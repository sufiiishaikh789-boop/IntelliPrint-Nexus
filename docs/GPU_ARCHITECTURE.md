# IntelliPrint Nexus — GPU Architecture

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SmartPrint AI Application                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Admin Dashboard                         │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐  │   │
│  │  │ GPU Status  │  │  Benchmark   │  │ Telemetry Table │  │   │
│  │  │   Panel     │  │  Panel       │  │   (Per-Job)     │  │   │
│  │  └─────┬───────┘  └──────┬───────┘  └────────┬────────┘  │   │
│  └────────┼─────────────────┼──────────────────┼───────────┘   │
│           │                 │                  │               │
│  ┌────────▼─────────────────▼──────────────────▼───────────┐   │
│  │                    smartcore/                             │   │
│  │                                                           │   │
│  │  ┌─────────────────┐  ┌───────────────────────────────┐  │   │
│  │  │  DeviceManager  │  │      GPUInferenceEngine        │  │   │
│  │  │  (singleton)    │  │                               │  │   │
│  │  │                 │  │  preprocess → transfer →       │  │   │
│  │  │ detect_device() │  │  autocast → inference_mode()→  │  │   │
│  │  │ health_check()  │◄─┤  model(tensor) → postprocess   │  │   │
│  │  │ benchmark()     │  │              ↓                │  │   │
│  │  │ get_memory()    │  │        GPUJobTelemetry         │  │   │
│  │  │ synchronize()   │  │        (async DB write)        │  │   │
│  │  │ handle_oom()    │  └───────────────────────────────┘  │   │
│  │  └────────┬────────┘                                      │   │
│  │           │                                               │   │
│  │  ┌────────▼────────┐  ┌───────────────┐                  │   │
│  │  │  GPUGovernor    │  │ GpuBenchmark  │                  │   │
│  │  │  (resource      │  │               │                  │   │
│  │  │   limits)       │  │ CPU/GPU/FP16  │                  │   │
│  │  │                 │  │ P50/P95/P99   │                  │   │
│  │  └─────────────────┘  │ JSON results  │                  │   │
│  │                        └───────────────┘                  │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      smartdb/                              │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │  gpu_job_telemetry table                           │   │  │
│  │  │  id, device, precision, latency_ms, peak_memory_mb │   │  │
│  │  │  status, model_name, batch_size, started_at        │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
Student uploads document
        ↓
    upload.py
        ↓
    computer_vision.py (OpenCV pipeline — 20 metrics)
        ↓
    gpu_inference_engine.run_inference()
        │
        ├── device_manager.detect_device()  → DeviceContext
        ├── device_manager.governor.can_start_job()
        ├── _preprocess_image()             → (1,3,224,224) tensor
        ├── tensor.to(device, non_blocking=True)
        ├── torch.amp.autocast("cuda", dtype=torch.float16)
        ├── torch.inference_mode()
        │       model(tensor)
        ├── synchronize()
        ├── device_manager.get_memory_info()  → peak_memory_mb
        └── _save_telemetry_async()          → gpu_job_telemetry
                ↓
        result dict (class, confidence, latency_ms, device, precision)
                ↓
        document_quality.py blends CNN result into quality score
                ↓
        Admin can see telemetry in GPU Monitor page
```

---

## Key Design Decisions

### 1. Singleton DeviceManager (not scattered .to("cuda"))

**Problem:** Previous code had scattered `.to("cuda")` calls with no centralized tracking.

**Solution:** All device selection, memory tracking, and governance goes through `device_manager`.
Every AI job receives a `DeviceContext` and every result produces a `GPUJobTelemetry`.

### 2. torch.inference_mode() not just .eval()

`model.eval()` disables BatchNorm tracking but still builds the autograd graph.
`torch.inference_mode()` additionally:
- Disables gradient computation and storage entirely
- Reduces memory by ~30% compared to `torch.no_grad()`
- Cannot create tensors that participate in autograd

### 3. AMP with explicit dtype

Using `torch.amp.autocast(device_type="cuda", dtype=torch.float16)` explicitly.
The `device_type` argument was added in PyTorch 2.0 to replace the deprecated
`torch.cuda.amp.autocast()`. This ensures correct behavior on CPU (no-op) and
on CUDA (FP16 kernel dispatch).

### 4. Non-blocking transfers

`.to(device, non_blocking=True)` allows CUDA copy to overlap with other CPU work.
The `synchronize()` before timing ensures the transfer is complete before we measure.

### 5. Telemetry is async and non-blocking

DB writes use a daemon thread — they never delay the inference response.
If the DB is unavailable or overloaded, telemetry is silently dropped (warning only).

### 6. OOM recovery is automatic

If CUDA OOM occurs:
1. Cache is cleared (justified — recover from OOM)
2. Batch size is halved
3. Retry once at the smaller batch
4. If still OOM, fall back to CPU gracefully
