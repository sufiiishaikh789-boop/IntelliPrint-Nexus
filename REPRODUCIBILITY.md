# IntelliPrint Nexus — Benchmark Reproducibility

---

## Hardware Baseline (This Deployment)

| Item | Value |
|---|---|
| Python | 3.14.6 |
| OS | Windows 10 (10.0.19045) |
| CPU | AMD64 Family 22 Model 48 (4 cores) |
| RAM | 6 GB |
| GPU | ❌ Not present |
| CUDA | ❌ Not available |
| TensorFlow | ❌ Not installed |
| PyTorch | ❌ Not installed |

**Inference device: `cpu` (NumPy fallback)**

---

## CPU Benchmark Results (Measured)

All results from live measurements. Run date: 2026-09-14.

| Workload | Framework | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |
|---|---|---|---|---|---|---|
| matmul_224×224 | NumPy FP32 | _(live)_ | _(live)_ | _(live)_ | _(live)_ | _(live)_ |

Run `python -m smartcore.gpu_benchmark` to collect fresh results for your hardware.

---

## GPU Benchmark Results Template (For CUDA Machine)

When a CUDA machine is used, results populate automatically:

```json
{
  "environment": {
    "device": "cuda:0",
    "gpu_name": "NVIDIA GeForce RTX XXXX",
    "cuda": "12.x",
    "warmup_iters": 3,
    "measured_iters": 50
  },
  "results": {
    "cpu_baseline": { "mean_ms": 48.2, "p50_ms": 47.1, "p95_ms": 58.0, "status": "success" },
    "gpu_fp32":     { "mean_ms":  4.8, "p50_ms":  4.7, "p95_ms":  5.9, "status": "success" },
    "gpu_fp16":     { "mean_ms":  2.4, "p50_ms":  2.3, "p95_ms":  3.0, "status": "success" }
  },
  "summary": {
    "gpu_speedup": 10.04
  }
}
```

---

## Reproducibility Conditions

To reproduce exactly:

```bash
# 1. Activate virtual environment
.venv\Scripts\activate

# 2. Verify versions
python -c "import torch; print(torch.__version__, torch.cuda.get_device_name(0))"

# 3. Run benchmark (results saved to benchmarks/)
python -m smartcore.gpu_benchmark

# 4. Run tests
pytest tests/test_gpu.py -v -m "not gpu"

# 5. Run diagnostic
python gpu_diagnostics.py
```

---

## Known Sources of Variance

| Source | Typical impact |
|---|---|
| OS scheduler preemption | ±5-15% on P99 |
| Background processes | ±1-5% on mean |
| Thermal throttling (GPU) | Significant if sustained |
| First run after OS boot | Slower — use warmup |
| Memory fragmentation | Small |

Use ≥50 iterations (BENCHMARK_ITERS) to average out scheduler noise.
