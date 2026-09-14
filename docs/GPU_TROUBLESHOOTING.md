# IntelliPrint Nexus — GPU Troubleshooting

---

## Common Issues

### Issue: nvidia-smi not found

```
nvidia-smi : The term 'nvidia-smi' is not recognized...
```

**Cause:** No NVIDIA driver installed, or GPU not present.

**Resolution:**
1. Verify GPU is physically present
2. Download driver from https://www.nvidia.com/drivers
3. For WSL2: Install CUDA Toolkit for WSL

---

### Issue: PyTorch not installed

```
PyTorch NOT installed: No module named 'torch'
```

**Resolution:**
```powershell
# For CUDA 12.1:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# For CPU only:
pip install torch torchvision
```

After install, verify:
```python
import torch
print(torch.cuda.is_available())
```

---

### Issue: CUDA available but wrong device selected

**Cause:** `device_manager._detect_fresh()` tries PyTorch CUDA first. If PyTorch is not installed,
it falls through to TensorFlow GPU, then CPU.

**Fix:** Install PyTorch with CUDA support (see above).

---

### Issue: CUDA Out of Memory (OOM)

```
RuntimeError: CUDA out of memory. Tried to allocate XXX MB
```

**Automatic recovery:** The inference engine halves batch size and retries.

**Manual fix:**
```python
# Check available memory:
import torch
print(torch.cuda.memory_summary())
print(f"Free: {torch.cuda.mem_get_info()[0] / 1024**2:.0f} MB")

# Clear cache:
torch.cuda.empty_cache()
```

**Prevent OOM:** Reduce `MAX_BATCH_SIZE` env variable:
```powershell
$env:SMARTPRINT_MAX_BATCH_SIZE = "4"
```

---

### Issue: GPU detected but inference runs on CPU

**Cause:** Governor blocked the job (too many concurrent GPU jobs).

**Check:**
```python
from smartcore.device_manager import device_manager
health = device_manager.health_check()
print(health["governor"])
# → {"active_jobs": 4, "max_concurrent": 4, ...}
```

**Fix:** Increase limit:
```powershell
$env:SMARTPRINT_MAX_GPU_JOBS = "8"
```

---

### Issue: FP16 causes NaN outputs

**Cause:** Model weights have large magnitude values that overflow float16.

**Fix:** Use FP32:
```powershell
$env:SMARTPRINT_PRECISION = "FP32"
```

Or use BF16 which has the same dynamic range as FP32:
```powershell
$env:SMARTPRINT_PRECISION = "BF16"
```

---

### Issue: torch.compile fails

```
torch._dynamo.exc.Unsupported: ...
```

**Cause:** Some operations are not compilable on the current PyTorch version.

**Fix:** The benchmark framework automatically marks it as "skipped" and continues.
torch.compile is not required for correct inference.

---

### Issue: ONNX export fails

**Cause:** Custom layers not supported by ONNX opset.

**Fix:** The benchmark marks this as "error" and continues.
ONNX export requires: `pip install onnx onnxruntime[-gpu]`

---

### Issue: DB telemetry not saving

```
create_gpu_telemetry failed: ...
```

**Cause:** DB migration hasn't run yet.

**Fix:** Start the app once (calls `init_db()` → creates `gpu_job_telemetry` table).

Or manually:
```python
from smartdb.models import init_db
init_db()
```

---

### Issue: GPU Monitor page not loading

**Check:** `app.py` must have the GPU monitor route registered.

```python
# Should be in app.py:
elif page == "gpu_monitor":
    from smartviews.gpu_monitor import show_gpu_monitor
    show_gpu_monitor()
```

---

## Environment Variables Reference

| Variable | Default | Effect |
|---|---|---|
| SMARTPRINT_MAX_GPU_JOBS | 4 | Max concurrent GPU inference jobs |
| SMARTPRINT_MAX_QUEUE_SIZE | 32 | Max items in inference queue |
| SMARTPRINT_GPU_MEM_THRESHOLD_MB | 512 | Min free VRAM required |
| SMARTPRINT_PRECISION | FP32 | Default precision (FP32/FP16/BF16) |
| SMARTPRINT_WARMUP_ITERS | 3 | Warmup iterations (discarded from stats) |
| SMARTPRINT_BENCHMARK_ITERS | 50 | Measured iterations for benchmarks |
| SMARTPRINT_INFERENCE_TIMEOUT_S | 15.0 | Inference timeout |
| TF_CPP_MIN_LOG_LEVEL | — | Set to 2 to suppress TF logs |

---

## Diagnostic Commands

```bash
# Full diagnostic
python gpu_diagnostics.py

# JSON diagnostic (machine-readable)
python gpu_diagnostics.py --json

# Quick GPU check
python gpu_check.py

# Run benchmark
python -m smartcore.gpu_benchmark

# Run profiler
python profile_gpu.py

# Run tests (CPU-only, no GPU required)
pytest tests/test_gpu.py -v -m "not gpu"
```
