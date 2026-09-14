# IntelliPrint Nexus — GPU Profiling Guide

---

## Overview

`profile_gpu.py` profiles the full inference path using:
- **torch.profiler** (when PyTorch is installed) — captures CPU and CUDA operator activity
- **cProfile** (always available) — captures Python-level overhead

---

## Quick Start

```bash
python profile_gpu.py
python profile_gpu.py --iters 20
python profile_gpu.py --output logs/my_trace.json
```

Output files:
- `logs/gpu_profile_<timestamp>.json` — Chrome trace (open in `chrome://tracing`)
- `logs/gpu_profile_<timestamp>_summary.txt` — human-readable operator table

---

## Chrome Trace Viewer

1. Open Google Chrome
2. Navigate to `chrome://tracing`
3. Click "Load" and select `logs/gpu_profile_*.json`
4. Look for:
   - **CPU row** — Python operators
   - **CUDA row** — GPU kernels (cuDNN conv_fwd, cudaMemcpy, etc.)
   - **Correlation arrows** — connecting CPU launch to CUDA kernel

---

## Reading the Operator Table

```
-------  ------------  --------  --------  --------  --------  --------
Name          CPU time    CUDA time  Calls    ...
-------  ------------  --------  --------  --------  --------  --------
aten::conv2d    0.5ms     3.2ms       20
aten::relu      0.1ms     0.8ms       20
cudaMemcpyAsync 0.2ms     1.1ms       20
-------  ------------  --------  --------  --------  --------  --------
```

**Key metrics:**
- `CUDA time_total` — time spent executing on GPU
- `CPU time_total` — Python dispatch overhead
- Ratio `CPU/CUDA << 1` means GPU is the bottleneck (good — GPU is being used)

---

## Using torch.profiler Directly

```python
import torch
from torch.profiler import profile, record_function, ProfilerActivity

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    record_shapes=True,
    profile_memory=True,
) as prof:
    with torch.inference_mode():
        with record_function("document_inference"):
            output = model(input_tensor)
    torch.cuda.synchronize()

# Print top operators by CUDA time
print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))

# Export for Chrome
prof.export_chrome_trace("trace.json")
```

---

## Memory Profiling

```python
import torch
torch.cuda.reset_peak_memory_stats()

# Before:
before = torch.cuda.memory_allocated() / 1024**2
print(f"Before: {before:.1f} MB")

with torch.inference_mode():
    _ = model(input_tensor)

# After:
after = torch.cuda.memory_allocated() / 1024**2
peak  = torch.cuda.max_memory_allocated() / 1024**2
print(f"After: {after:.1f} MB")
print(f"Peak:  {peak:.1f} MB")
```

This is exactly what `DeviceManager.get_memory_info()` records per inference.

---

## Interpreting Results

| Observation | Meaning | Action |
|---|---|---|
| CPU time >> CUDA time | Python dispatch overhead dominates | Use torch.compile or batch larger |
| CUDA time >> CPU time | GPU is the bottleneck | Use FP16, larger batch, or faster GPU |
| cudaMemcpy high | Host↔Device transfers dominate | Keep tensors on GPU between calls |
| OOM in profiler | Profiler overhead uses extra memory | Reduce batch or profiler scope |

---

## CPU-Only Profiling (cProfile)

When PyTorch is not installed, `profile_gpu.py` falls back to cProfile:

```bash
python profile_gpu.py
# Output: logs/gpu_profile_<timestamp>_cprofile.txt
```

This shows Python-level function call statistics for the NumPy workload path.
Useful for identifying preprocessing bottlenecks independent of the GPU.
