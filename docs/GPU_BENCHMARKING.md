# IntelliPrint Nexus — GPU Benchmarking Guide

---

## Overview

The benchmark framework in `smartcore/gpu_benchmark.py` measures real inference latency
and compute throughput. It uses proper statistical methodology with warmup separation,
multiple iterations, and percentile reporting (P50/P95/P99).

---

## Methodology

### Why warmup matters

The first 1-3 iterations of any GPU workload are slower due to:
- CUDA kernel compilation (especially with torch.compile)
- Memory page allocation
- Framework initialization overhead

**SmartPrint always discards warmup iterations** and only measures steady-state latency.

```python
# Warmup — NOT included in statistics
for _ in range(WARMUP_ITERS):   # default: 3
    _ = model(dummy)
synchronize()

# Measurement — these are the real numbers
for _ in range(BENCHMARK_ITERS):   # default: 50
    synchronize()          # barrier before timing
    t0 = perf_counter()
    _ = model(dummy)
    synchronize()          # barrier after (CUDA async)
    latencies.append((perf_counter() - t0) * 1000)
```

### Why synchronize() is required

CUDA execution is asynchronous. Without `torch.cuda.synchronize()`,
`perf_counter()` measures the time to *enqueue* the kernel, not execute it.
SmartPrint always synchronizes before and after each timing measurement.

---

## Statistical Reporting

| Metric | Meaning |
|---|---|
| mean_ms | Average latency — affected by outliers |
| median_ms | Middle value — more robust than mean |
| P50 | 50th percentile — half of requests faster than this |
| P95 | 95th percentile — 95% of requests faster than this |
| P99 | 99th percentile — 99% of requests faster than this |
| min_ms | Best-case latency |
| max_ms | Worst-case latency |
| throughput_rps | 1000 / mean_ms = requests per second |

**SLO recommendation:** Use P95 as your latency target. P99 catches tail latency.

---

## Running the Full Benchmark Suite

```bash
python -m smartcore.gpu_benchmark
```

Output saved to `benchmarks/benchmark_<timestamp>.json`.

Example output on a GPU machine:
```
============================================================
  INTELLIPRINT NEXUS — GPU BENCHMARK RESULTS
============================================================
  Device:        cuda:0
  GPU:           NVIDIA GeForce RTX 3060
  CUDA:          12.1
------------------------------------------------------------
  CPU Baseline:  48.230 ms (mean)
  GPU FP32:       4.820 ms (mean) [success]
  GPU FP16:       2.410 ms (mean) [success]
  GPU Speedup:   10.01x
------------------------------------------------------------
  CPU P50:  47.200 ms  P95: 58.100 ms  P99: 65.400 ms
  Results saved → benchmarks/benchmark_20261014_120000.json
============================================================
```

---

## Running Partial Benchmarks

```python
from smartcore.gpu_benchmark import GpuBenchmark, benchmark_cpu_numpy, benchmark_pytorch

# CPU only
result = benchmark_cpu_numpy(size=224, warmup=3, n=100)
print(result)

# GPU FP32 (if CUDA available)
result = benchmark_pytorch("cuda:0", precision="FP32", warmup=3, n=100)
print(result)

# Batch comparison
from smartcore.gpu_benchmark import benchmark_batch_sizes
results = benchmark_batch_sizes("cuda:0", batch_sizes=[1, 4, 8, 16])
```

---

## Precision Comparison

| Precision | Activation condition | Typical speedup |
|---|---|---|
| FP32 | Always | Baseline |
| FP16 | CUDA + torch >= 1.6 | ~2x vs FP32 |
| BF16 | CUDA + `is_bf16_supported()` | ~2x vs FP32 |

FP16/BF16 require hardware with Tensor Cores (Volta/Turing/Ampere+).

---

## torch.compile Benchmark

The `benchmark_torch_compile()` function separately reports:

- `first_run_ms` — includes compilation overhead
- `compile_overhead_ms` — total time to trace and compile the model
- `mean_ms` / `p95_ms` — steady-state **after** compilation

```
torch.compile(mode="reduce-overhead") — fuses operators, removes dispatch overhead
First run: 1500 ms (compilation)
Steady:    3.1 ms/inference
```

---

## ONNX Runtime Benchmark

```python
from smartcore.gpu_benchmark import benchmark_onnx_cuda
result = benchmark_onnx_cuda(warmup=3, n=50)
print(result["actual_provider"])   # "CUDAExecutionProvider" or "CPUExecutionProvider"
```

The result honestly reports which provider is active — never claims CUDA if CPUExecutionProvider is used.

---

## Reproducibility

Results are reproducible within normal OS scheduler jitter (~5-15% variance).
To reduce variance:
1. Close other applications
2. Use `sudo nvidia-smi -pm 1` (Persistent Mode) on Linux
3. Lock GPU clock: `sudo nvidia-smi -lgc <max_freq>`
4. Use `--benchmark-iters 200` for smaller standard deviation

The `benchmarks/` directory stores all results with timestamps.
