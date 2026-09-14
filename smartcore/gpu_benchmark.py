"""
IntelliPrint Nexus — GPU Benchmark Framework (V2)
==================================================
Comprehensive, reproducible benchmark suite for CPU vs GPU,
precision comparison (FP32/FP16/BF16), and batch-size scaling.

All values are measured — never hardcoded.

Usage
-----
    from smartcore.gpu_benchmark import GpuBenchmark
    suite = GpuBenchmark()
    report = suite.run_full_suite()
    suite.save_results(report)

Or from CLI:
    python -m smartcore.gpu_benchmark
"""

from __future__ import annotations

import json
import os
import time
import platform
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("gpu_benchmark")
except ImportError:
    _log = logging.getLogger("smartprint.gpu_benchmark")

try:
    from smartcore.device_manager import device_manager, DeviceBenchmarkResult
except ImportError:
    device_manager = None  # type: ignore[assignment]
    DeviceBenchmarkResult = None  # type: ignore[assignment]

BENCHMARKS_DIR = "benchmarks"
WARMUP_ITERS   = int(os.environ.get("SMARTPRINT_WARMUP_ITERS", "3"))
BENCH_ITERS    = int(os.environ.get("SMARTPRINT_BENCHMARK_ITERS", "50"))
INPUT_SHAPE    = (1, 3, 224, 224)   # standard CNN input


# ═══════════════════════════════════════════════════════════════════════════════
# Individual Benchmark Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _percentile_stats(latencies: List[float]) -> Dict[str, float]:
    if not latencies:
        return {}
    arr = np.array(latencies, dtype=np.float64)
    return {
        "mean_ms":   round(float(np.mean(arr)), 3),
        "median_ms": round(float(np.median(arr)), 3),
        "p50_ms":    round(float(np.percentile(arr, 50)), 3),
        "p95_ms":    round(float(np.percentile(arr, 95)), 3),
        "p99_ms":    round(float(np.percentile(arr, 99)), 3),
        "min_ms":    round(float(np.min(arr)), 3),
        "max_ms":    round(float(np.max(arr)), 3),
        "throughput_rps": round(1000.0 / float(np.mean(arr)), 2) if np.mean(arr) > 0 else 0.0,
    }


def benchmark_cpu_numpy(
    size: int = 224,
    warmup: int = WARMUP_ITERS,
    n: int = BENCH_ITERS,
) -> Dict[str, Any]:
    """CPU NumPy matrix multiply benchmark — always available."""
    a = np.random.rand(size, size).astype(np.float32)
    b = np.random.rand(size, size).astype(np.float32)

    for _ in range(warmup):
        _ = np.dot(a, b)

    latencies = []
    for _ in range(n):
        t0 = time.perf_counter()
        _ = np.dot(a, b)
        latencies.append((time.perf_counter() - t0) * 1000)

    stats = _percentile_stats(latencies)
    return {
        "backend":      "cpu_numpy",
        "device":       "cpu",
        "framework":    "NumPy",
        "precision":    "FP32",
        "workload":     f"matmul_{size}x{size}",
        "warmup_iters": warmup,
        "measured_iters": n,
        **stats,
        "status":       "success",
    }


def benchmark_pytorch(
    device_str: str,
    precision: str = "FP32",
    warmup: int = WARMUP_ITERS,
    n: int = BENCH_ITERS,
    shape: tuple = INPUT_SHAPE,
) -> Dict[str, Any]:
    """
    PyTorch Conv2D benchmark on specified device and precision.
    Warms up first — compilation/JIT time is NOT included in results.
    """
    result_base: Dict[str, Any] = {
        "backend":        f"pytorch_{device_str}_{precision.lower()}",
        "device":         device_str,
        "framework":      "PyTorch",
        "precision":      precision,
        "workload":       f"Conv2D_{'x'.join(str(d) for d in shape)}",
        "warmup_iters":   warmup,
        "measured_iters": n,
    }

    try:
        import torch
        import torch.nn as nn
        import contextlib

        if not torch.cuda.is_available() and "cuda" in device_str:
            return {**result_base, "status": "skipped", "reason": "CUDA not available"}

        conv = nn.Conv2d(shape[1], 64, kernel_size=3, padding=1).to(device_str)
        conv.eval()
        dummy = torch.randn(*shape).to(device_str, non_blocking=True)

        # AMP context selection
        is_cuda = "cuda" in device_str
        if precision == "FP16" and is_cuda:
            amp_ctx = torch.amp.autocast(device_type="cuda", dtype=torch.float16)
        elif precision == "BF16" and is_cuda:
            if torch.cuda.is_bf16_supported():
                amp_ctx = torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16)
            else:
                return {**result_base, "status": "skipped", "reason": "BF16 not supported on this GPU"}
        else:
            amp_ctx = contextlib.nullcontext()

        def _sync():
            if is_cuda:
                torch.cuda.synchronize()

        # Memory before
        if is_cuda:
            torch.cuda.reset_peak_memory_stats()
            mem_before_mb = torch.cuda.memory_allocated() / (1024 * 1024)
        else:
            mem_before_mb = 0.0

        with torch.inference_mode():
            # Warmup — NOT timed
            for _ in range(warmup):
                with amp_ctx:
                    _ = conv(dummy)
            _sync()

            # Measurement
            latencies = []
            for _ in range(n):
                _sync()
                t0 = time.perf_counter()
                with amp_ctx:
                    _ = conv(dummy)
                _sync()
                latencies.append((time.perf_counter() - t0) * 1000)

        if is_cuda:
            peak_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
            mem_after_mb = torch.cuda.memory_allocated() / (1024 * 1024)
        else:
            peak_mb = mem_after_mb = 0.0

        stats = _percentile_stats(latencies)
        return {
            **result_base,
            **stats,
            "memory_before_mb": round(mem_before_mb, 1),
            "memory_after_mb":  round(mem_after_mb, 1),
            "peak_memory_mb":   round(peak_mb, 1),
            "status":           "success",
        }

    except ImportError:
        return {**result_base, "status": "skipped", "reason": "PyTorch not installed"}
    except Exception as exc:
        return {**result_base, "status": "error", "error": str(exc)[:200]}


def benchmark_torch_compile(
    device_str: str,
    warmup: int = WARMUP_ITERS,
    n: int = BENCH_ITERS,
    shape: tuple = INPUT_SHAPE,
) -> Dict[str, Any]:
    """
    Benchmark torch.compile() vs normal PyTorch.
    Compile overhead is separated from steady-state inference.
    First-run time (compilation) is reported separately.
    """
    base: Dict[str, Any] = {
        "backend":      "torch_compile",
        "device":       device_str,
        "framework":    "PyTorch (compiled)",
        "precision":    "FP32",
        "workload":     f"compiled_conv2d_{'x'.join(str(d) for d in shape)}",
        "warmup_iters": warmup,
        "measured_iters": n,
    }

    try:
        import torch
        import torch.nn as nn

        if not hasattr(torch, "compile"):
            return {**base, "status": "skipped", "reason": "torch.compile not available (torch < 2.0)"}

        if not torch.cuda.is_available() and "cuda" in device_str:
            return {**base, "status": "skipped", "reason": "CUDA not available"}

        conv = nn.Conv2d(shape[1], 64, kernel_size=3, padding=1).to(device_str)
        conv.eval()

        # Measure compile time
        t_compile_start = time.perf_counter()
        compiled_conv = torch.compile(conv, mode="reduce-overhead")
        dummy = torch.randn(*shape).to(device_str)

        def _sync():
            if "cuda" in device_str:
                torch.cuda.synchronize()

        with torch.inference_mode():
            # First run — compilation happens here
            _sync()
            t0 = time.perf_counter()
            _ = compiled_conv(dummy)
            _sync()
            first_run_ms = (time.perf_counter() - t0) * 1000
            compile_overhead_ms = (time.perf_counter() - t_compile_start) * 1000

            # Warmup (after compilation)
            for _ in range(warmup):
                _ = compiled_conv(dummy)
            _sync()

            # Steady-state measurement
            latencies = []
            for _ in range(n):
                _sync()
                t0 = time.perf_counter()
                _ = compiled_conv(dummy)
                _sync()
                latencies.append((time.perf_counter() - t0) * 1000)

        stats = _percentile_stats(latencies)
        return {
            **base, **stats,
            "first_run_ms":        round(first_run_ms, 3),
            "compile_overhead_ms": round(compile_overhead_ms, 3),
            "status":              "success",
        }

    except ImportError:
        return {**base, "status": "skipped", "reason": "PyTorch not installed"}
    except Exception as exc:
        return {**base, "status": "error", "error": str(exc)[:200]}


def benchmark_onnx_cuda(
    warmup: int = WARMUP_ITERS,
    n: int = BENCH_ITERS,
    shape: tuple = INPUT_SHAPE,
) -> Dict[str, Any]:
    """
    ONNX Runtime with CUDAExecutionProvider.
    Only claims CUDA if CUDAExecutionProvider is actually active — not faked.
    """
    base: Dict[str, Any] = {
        "backend":      "onnx_cuda",
        "framework":    "ONNX Runtime",
        "precision":    "FP32",
        "workload":     f"conv2d_{'x'.join(str(d) for d in shape)}",
        "warmup_iters": warmup,
        "measured_iters": n,
    }

    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()

        if "CUDAExecutionProvider" in providers:
            ep = "CUDAExecutionProvider"
        elif "CPUExecutionProvider" in providers:
            ep = "CPUExecutionProvider"
        else:
            return {**base, "device": "unknown", "status": "skipped", "reason": "No ONNX providers found"}

        # We'd need an actual ONNX model file; create a dummy one
        onnx_path = "models/benchmark_conv.onnx"
        if not os.path.exists(onnx_path):
            try:
                import torch
                import torch.nn as nn
                conv = nn.Conv2d(shape[1], 64, kernel_size=3, padding=1)
                conv.eval()
                dummy = torch.randn(*shape)
                os.makedirs("models", exist_ok=True)
                with torch.inference_mode():
                    torch.onnx.export(
                        conv, dummy, onnx_path,
                        input_names=["input"], output_names=["output"],
                        dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
                        opset_version=17,
                    )
            except Exception as e:
                return {**base, "device": ep, "status": "skipped", "reason": f"ONNX export failed: {e}"}

        sess = ort.InferenceSession(onnx_path, providers=[ep])
        actual_provider = sess.get_providers()[0]
        dummy_np = np.random.rand(*shape).astype(np.float32)
        inp_name = sess.get_inputs()[0].name

        for _ in range(warmup):
            _ = sess.run(None, {inp_name: dummy_np})

        latencies = []
        for _ in range(n):
            t0 = time.perf_counter()
            _ = sess.run(None, {inp_name: dummy_np})
            latencies.append((time.perf_counter() - t0) * 1000)

        stats = _percentile_stats(latencies)
        return {
            **base,
            "device":           actual_provider.replace("ExecutionProvider", ""),
            "actual_provider":  actual_provider,
            **stats,
            "status":           "success",
        }

    except ImportError:
        return {**base, "device": "N/A", "status": "skipped", "reason": "onnxruntime not installed"}
    except Exception as exc:
        return {**base, "device": "N/A", "status": "error", "error": str(exc)[:200]}


def benchmark_batch_sizes(
    device_str: str,
    batch_sizes: List[int] = [1, 4, 8, 16],
    precision: str = "FP32",
    warmup: int = WARMUP_ITERS,
    n: int = BENCH_ITERS,
) -> List[Dict[str, Any]]:
    """
    Benchmark across multiple batch sizes on the given device.
    Automatically stops if VRAM would be exhausted.
    """
    results = []
    for bs in batch_sizes:
        # Check available VRAM before large batches
        if device_manager and "cuda" in device_str:
            mem = device_manager.get_memory_info()
            if mem.free_mb < 256 * bs:
                results.append({
                    "batch_size": bs, "device": device_str, "precision": precision,
                    "status": "skipped", "reason": f"Insufficient VRAM (free: {mem.free_mb:.0f} MB)",
                })
                continue

        shape = (bs, 3, 224, 224)
        r = benchmark_pytorch(device_str, precision=precision, warmup=warmup, n=n, shape=shape)
        r["batch_size"] = bs
        results.append(r)

        # If OOM occurred, stop trying larger batches
        if r.get("status") == "error" and "memory" in str(r.get("error", "")).lower():
            break

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Full Suite Runner
# ═══════════════════════════════════════════════════════════════════════════════

class GpuBenchmark:
    """Orchestrates the full benchmark suite and saves structured JSON results."""

    def __init__(self) -> None:
        self.ctx = device_manager.detect_device() if device_manager else None
        self.device_str = self.ctx.device_str if self.ctx else "cpu"

    def run_cpu_baseline(self) -> Dict[str, Any]:
        _log.info("Running CPU NumPy baseline benchmark...")
        return benchmark_cpu_numpy(warmup=WARMUP_ITERS, n=BENCH_ITERS)

    def run_gpu_fp32(self) -> Dict[str, Any]:
        _log.info("Running GPU FP32 benchmark...")
        return benchmark_pytorch(self.device_str, precision="FP32", warmup=WARMUP_ITERS, n=BENCH_ITERS)

    def run_gpu_fp16(self) -> Dict[str, Any]:
        _log.info("Running GPU FP16 benchmark...")
        return benchmark_pytorch(self.device_str, precision="FP16", warmup=WARMUP_ITERS, n=BENCH_ITERS)

    def run_gpu_bf16(self) -> Dict[str, Any]:
        _log.info("Running GPU BF16 benchmark...")
        return benchmark_pytorch(self.device_str, precision="BF16", warmup=WARMUP_ITERS, n=BENCH_ITERS)

    def run_torch_compile(self) -> Dict[str, Any]:
        _log.info("Running torch.compile benchmark...")
        return benchmark_torch_compile(self.device_str, warmup=WARMUP_ITERS, n=BENCH_ITERS)

    def run_onnx(self) -> Dict[str, Any]:
        _log.info("Running ONNX Runtime benchmark...")
        return benchmark_onnx_cuda(warmup=WARMUP_ITERS, n=BENCH_ITERS)

    def run_batch_comparison(self) -> List[Dict[str, Any]]:
        _log.info("Running batch-size comparison benchmark...")
        return benchmark_batch_sizes(self.device_str, batch_sizes=[1, 4, 8, 16])

    def run_full_suite(self) -> Dict[str, Any]:
        """Run all benchmarks and return structured report."""
        started = time.strftime("%Y-%m-%d %H:%M:%S")
        _log.info("Starting full GPU benchmark suite...")

        cpu       = self.run_cpu_baseline()
        gpu_fp32  = self.run_gpu_fp32()
        gpu_fp16  = self.run_gpu_fp16()
        gpu_bf16  = self.run_gpu_bf16()
        compiled  = self.run_torch_compile()
        onnx      = self.run_onnx()
        batch_cmp = self.run_batch_comparison()

        # Calculate speedup (CPU numpy mean / GPU FP32 mean)
        speedup = 0.0
        cpu_mean  = cpu.get("mean_ms", 0)
        gpu_mean  = gpu_fp32.get("mean_ms", 0)
        if cpu_mean > 0 and gpu_mean > 0 and gpu_fp32.get("status") == "success":
            speedup = round(cpu_mean / gpu_mean, 2)

        report = {
            "generated_at":   started,
            "environment": {
                "python":   platform.python_version(),
                "os":       platform.system(),
                "cpu":      platform.processor(),
                "device":   self.device_str,
                "gpu_name": self.ctx.gpu_name if self.ctx else "CPU",
                "cuda":     self.ctx.cuda_version if self.ctx else None,
                "warmup_iters":   WARMUP_ITERS,
                "measured_iters": BENCH_ITERS,
                "model_version":  "1.0.0",
            },
            "results": {
                "cpu_baseline":      cpu,
                "gpu_fp32":          gpu_fp32,
                "gpu_fp16":          gpu_fp16,
                "gpu_bf16":          gpu_bf16,
                "torch_compile":     compiled,
                "onnx_cuda":         onnx,
                "batch_comparison":  batch_cmp,
            },
            "summary": {
                "cpu_mean_ms":   cpu.get("mean_ms"),
                "gpu_fp32_mean_ms": gpu_fp32.get("mean_ms"),
                "gpu_fp16_mean_ms": gpu_fp16.get("mean_ms"),
                "gpu_speedup":   speedup,
                "best_device":   self.device_str,
            },
        }
        _log.info("Benchmark suite complete. GPU speedup=%.2fx", speedup)
        return report

    def save_results(self, report: Dict[str, Any]) -> str:
        """Save benchmark results to benchmarks/ directory."""
        os.makedirs(BENCHMARKS_DIR, exist_ok=True)
        ts   = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(BENCHMARKS_DIR, f"benchmark_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        _log.info("Benchmark results saved to %s", path)
        return path


# ── CLI entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    suite  = GpuBenchmark()
    report = suite.run_full_suite()
    path   = suite.save_results(report)

    print("\n" + "=" * 60)
    print("  INTELLIPRINT NEXUS — GPU BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Device:        {report['environment']['device']}")
    print(f"  GPU:           {report['environment']['gpu_name']}")
    print(f"  CUDA:          {report['environment']['cuda'] or 'N/A'}")
    print("-" * 60)
    cpu = report["results"]["cpu_baseline"]
    g32 = report["results"]["gpu_fp32"]
    g16 = report["results"]["gpu_fp16"]
    print(f"  CPU Baseline:  {cpu.get('mean_ms', 'N/A'):.3f} ms (mean)")
    print(f"  GPU FP32:      {g32.get('mean_ms', 'N/A')} ms (mean) [{g32.get('status')}]")
    print(f"  GPU FP16:      {g16.get('mean_ms', 'N/A')} ms (mean) [{g16.get('status')}]")
    print(f"  GPU Speedup:   {report['summary']['gpu_speedup']}x")
    print("-" * 60)
    cpu_p = cpu.get
    print(f"  CPU P50:  {cpu_p('p50_ms','N/A')} ms  P95: {cpu_p('p95_ms','N/A')} ms  P99: {cpu_p('p99_ms','N/A')} ms")
    print(f"  Results saved → {path}")
    print("=" * 60)
