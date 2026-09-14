# IntelliPrint Nexus — GPU Implementation
## Technical Documentation V2

---

## Overview

IntelliPrint Nexus uses GPU acceleration for AI-powered document quality analysis.
The system detects the best available compute device at startup and uses it for
all AI inference. When no GPU is present, it falls back to CPU seamlessly.

---

## Architecture

```
SmartPrint AI Application
│
├── smartcore/device_manager.py      ← Centralized DeviceManager (NEW V2)
├── smartcore/gpu_manager.py         ← GPU detection singleton (V1)
├── smartcore/gpu_inference_engine.py← Full inference pipeline (NEW V2)
├── smartcore/gpu_benchmark.py       ← Benchmark framework (NEW V2)
├── smartai/document_quality.py      ← CNN document analysis
├── smartai/computer_vision.py       ← OpenCV pipeline (20 metrics)
├── smartdb/models.py                ← GPUJobTelemetry table (NEW V2)
├── smartdb/crud_gpu.py              ← Telemetry CRUD (NEW V2)
├── smartviews/gpu_monitor.py        ← GPU Monitor admin page (V2)
│
├── gpu_diagnostics.py               ← CLI diagnostic tool (NEW V2)
├── profile_gpu.py                   ← GPU profiling tool (NEW V2)
└── gpu_check.py                     ← Quick CLI check (V1)
```

---

## Device Selection

The `DeviceManager` selects the inference device using this priority chain:

```
1. PyTorch CUDA (torch.cuda.is_available())     → "cuda:0"
2. TensorFlow GPU (list_physical_devices("GPU"))→ "tf-gpu:0"
3. CPU fallback                                 → "cpu"
```

**Key rule:** The actual execution device is always recorded in telemetry.
If the model runs on CPU, device is reported as "cpu" — never "cuda".

---

## Inference Pipeline

```python
from smartcore.gpu_inference_engine import run_inference

result, telemetry = run_inference(
    img_bytes,
    batch_size=1,
    precision="FP16",    # FP32 | FP16 | BF16
    print_job_id=42,
)
```

### Pipeline steps:

1. **Device detection** — `device_manager.detect_device()`
2. **Precision validation** — downgrade FP16→FP32 on CPU, check BF16 support
3. **Governor check** — reject if `MAX_CONCURRENT_GPU_JOBS` reached
4. **Image preprocessing** — decode → resize → normalize → (1, 3, 224, 224) float32
5. **Model load** — single load at startup, reused on every call
6. **Non-blocking transfer** — `.to(device, non_blocking=True)` for host→device
7. **AMP autocast** — `torch.amp.autocast("cuda", dtype=torch.float16)` on CUDA
8. **Inference mode** — `torch.inference_mode()` — zero gradient overhead
9. **CUDA synchronize** — accurate timing across CUDA stream
10. **Memory snapshot** — before/after/peak allocated MB
11. **Telemetry** — async DB write (never blocks inference)
12. **Result** — class, confidence, model_type, device, precision, latency_ms

---

## AMP (Automatic Mixed Precision)

On CUDA machines, FP16 inference uses:

```python
with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
    output = model(tensor)
```

BF16 is enabled only when `torch.cuda.is_bf16_supported()` returns True.
On CPU, autocast is not applied (returns FP32).

---

## OOM Recovery

```
CUDA OOM detected
    ↓
log error + clear_cache()
    ↓
halve batch_size (8 → 4)
    ↓
retry once
    ↓
if batch_size < 1:
    return CPU fallback result
```

---

## GPU Resource Governance

| Parameter | Default | Env Variable |
|---|---|---|
| MAX_CONCURRENT_GPU_JOBS | 4 | SMARTPRINT_MAX_GPU_JOBS |
| MAX_QUEUE_SIZE | 32 | SMARTPRINT_MAX_QUEUE_SIZE |
| GPU_MEMORY_THRESHOLD_MB | 512 | SMARTPRINT_GPU_MEM_THRESHOLD_MB |
| INFERENCE_TIMEOUT_S | 15.0 | SMARTPRINT_INFERENCE_TIMEOUT_S |
| WARMUP_ITERS | 3 | SMARTPRINT_WARMUP_ITERS |
| BENCHMARK_ITERS | 50 | SMARTPRINT_BENCHMARK_ITERS |
| PRECISION | FP32 | SMARTPRINT_PRECISION |

---

## Model

| Property | Value |
|---|---|
| Name | SmartPrintDocumentAnalyzer |
| Version | 1.0.0 |
| Architecture | MobileNetV2 (transfer learning) |
| Input | 224×224×3 RGB, ImageNet normalized |
| Output | 5-class softmax |
| Classes | Good Document, Blurry, Skewed, Low Quality, Damaged |
| Framework | PyTorch (primary) / TensorFlow (fallback) |
| Saved weight | models/document_quality_pytorch.pt |

---

## Security

- GPU endpoints (benchmarks, profiling, diagnostics) are admin-only
- No arbitrary command execution through request parameters
- No subprocess calls based on user input
- Students cannot trigger GPU workloads directly
- All subprocess calls use explicit argument lists (no shell=True)
