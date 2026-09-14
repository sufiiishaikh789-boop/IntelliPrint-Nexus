"""
IntelliPrint Nexus — Centralized GPU Device Manager (V2)
=========================================================
Replaces scattered `.to("cuda")` calls with a single,
auditable device management layer.

Architecture
------------
DeviceManager (singleton)
│
├── detect_device()        → DeviceContext dataclass
├── get_memory_info()      → GPUMemoryInfo dataclass
├── health_check()         → Dict[str, Any]
├── benchmark_device()     → DeviceBenchmarkResult
├── select_device()        → str   ("cuda:0" / "cpu")
├── synchronize()          → None  (CUDA sync or no-op)
├── clear_cache()          → None  (only when justified)
└── resource_governor      → enforces MAX_CONCURRENT_GPU_JOBS

Every AI job records:
    device_type, device_index, gpu_name, framework, model_name

Usage
-----
    from smartcore.device_manager import device_manager, DeviceContext
    ctx = device_manager.detect_device()
    print(ctx.device_str)   # e.g. "cuda:0" or "cpu"
"""

from __future__ import annotations

import os
import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("device_manager")
except ImportError:
    _log = logging.getLogger("smartprint.device_manager")

# ── Configuration constants (override via environment variables) ────────────
MAX_CONCURRENT_GPU_JOBS: int = int(os.environ.get("SMARTPRINT_MAX_GPU_JOBS", "4"))
MAX_QUEUE_SIZE: int = int(os.environ.get("SMARTPRINT_MAX_QUEUE_SIZE", "32"))
GPU_MEMORY_THRESHOLD_MB: int = int(os.environ.get("SMARTPRINT_GPU_MEM_THRESHOLD_MB", "512"))
REQUEST_TIMEOUT_S: float = float(os.environ.get("SMARTPRINT_REQUEST_TIMEOUT_S", "60.0"))
INFERENCE_TIMEOUT_S: float = float(os.environ.get("SMARTPRINT_INFERENCE_TIMEOUT_S", "15.0"))
WARMUP_ITERS: int = int(os.environ.get("SMARTPRINT_WARMUP_ITERS", "3"))
BENCHMARK_ITERS: int = int(os.environ.get("SMARTPRINT_BENCHMARK_ITERS", "50"))


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DeviceContext:
    """
    Fully-described execution device returned by detect_device().
    Every AI job must receive and record one of these.
    """
    device_type: str          # "cuda" | "cpu"
    device_index: int         # 0, 1, … (always 0 for CPU)
    device_str: str           # "cuda:0" | "cpu"
    gpu_name: str             # "NVIDIA RTX 4090" | "CPU"
    framework: str            # "pytorch" | "tensorflow" | "cpu"
    cuda_available: bool
    cuda_version: Optional[str]
    vram_total_mb: int
    vram_free_mb: int
    is_fallback: bool         # True when GPU was requested but CPU was used


@dataclass
class GPUMemoryInfo:
    """
    Snapshot of GPU memory state.
    On CPU machines, all values are 0 and source is "not_available".
    """
    allocated_mb: float
    reserved_mb: float
    peak_allocated_mb: float
    peak_reserved_mb: float
    free_mb: float
    total_mb: float
    utilization_pct: float
    source: str               # "pytorch" | "tensorflow" | "nvidia-smi" | "not_available"


@dataclass
class DeviceBenchmarkResult:
    """
    Result of benchmark_device() — real measured values only.
    """
    device_str: str
    framework: str
    workload: str             # description of what was benchmarked
    warmup_iters: int
    measured_iters: int
    latencies_ms: List[float] = field(default_factory=list)

    # Computed statistics (filled by _compute_stats)
    mean_ms: float = 0.0
    median_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    throughput_rps: float = 0.0
    memory_before_mb: float = 0.0
    memory_after_mb: float = 0.0
    peak_memory_mb: float = 0.0
    precision: str = "FP32"
    error: Optional[str] = None

    def compute_stats(self) -> None:
        """Compute all statistics from self.latencies_ms in-place."""
        import numpy as np
        if not self.latencies_ms:
            return
        arr = np.array(self.latencies_ms, dtype=np.float64)
        self.mean_ms   = float(np.mean(arr))
        self.median_ms = float(np.median(arr))
        self.p50_ms    = float(np.percentile(arr, 50))
        self.p95_ms    = float(np.percentile(arr, 95))
        self.p99_ms    = float(np.percentile(arr, 99))
        self.min_ms    = float(np.min(arr))
        self.max_ms    = float(np.max(arr))
        if self.mean_ms > 0:
            self.throughput_rps = round(1000.0 / self.mean_ms, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_str":       self.device_str,
            "framework":        self.framework,
            "workload":         self.workload,
            "precision":        self.precision,
            "warmup_iters":     self.warmup_iters,
            "measured_iters":   self.measured_iters,
            "mean_ms":          round(self.mean_ms, 3),
            "median_ms":        round(self.median_ms, 3),
            "p50_ms":           round(self.p50_ms, 3),
            "p95_ms":           round(self.p95_ms, 3),
            "p99_ms":           round(self.p99_ms, 3),
            "min_ms":           round(self.min_ms, 3),
            "max_ms":           round(self.max_ms, 3),
            "throughput_rps":   self.throughput_rps,
            "memory_before_mb": round(self.memory_before_mb, 1),
            "memory_after_mb":  round(self.memory_after_mb, 1),
            "peak_memory_mb":   round(self.peak_memory_mb, 1),
            "error":            self.error,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# GPU Resource Governor
# ═══════════════════════════════════════════════════════════════════════════════

class _GPUGovernor:
    """
    Thread-safe resource governor.
    Prevents unlimited concurrent GPU workloads from exhausting VRAM.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_jobs: int = 0
        self._queue_depth: int = 0

    def can_start_job(self) -> Tuple[bool, str]:
        """Return (allowed, reason) before starting a GPU job."""
        with self._lock:
            if self._active_jobs >= MAX_CONCURRENT_GPU_JOBS:
                return False, f"GPU job limit reached ({MAX_CONCURRENT_GPU_JOBS} concurrent)"
            if self._queue_depth >= MAX_QUEUE_SIZE:
                return False, f"Queue full ({MAX_QUEUE_SIZE} items)"
            return True, "ok"

    def start_job(self) -> None:
        with self._lock:
            self._active_jobs += 1

    def finish_job(self) -> None:
        with self._lock:
            self._active_jobs = max(0, self._active_jobs - 1)

    def enqueue(self) -> None:
        with self._lock:
            self._queue_depth += 1

    def dequeue(self) -> None:
        with self._lock:
            self._queue_depth = max(0, self._queue_depth - 1)

    @property
    def stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "active_jobs":        self._active_jobs,
                "queue_depth":        self._queue_depth,
                "max_concurrent":     MAX_CONCURRENT_GPU_JOBS,
                "max_queue":          MAX_QUEUE_SIZE,
            }


# ═══════════════════════════════════════════════════════════════════════════════
# DeviceManager — Main Class
# ═══════════════════════════════════════════════════════════════════════════════

class DeviceManager:
    """
    Centralized, thread-safe GPU device management.

    Single instance via module-level ``device_manager`` singleton.
    Uses the existing gpu_manager for raw detection;
    adds DeviceContext, GPUMemoryInfo, benchmarking, and governance.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ctx: Optional[DeviceContext] = None
        self._ctx_timestamp: float = 0.0
        self._ctx_ttl: float = 30.0          # re-detect every 30 s
        self.governor = _GPUGovernor()

    # ── Device detection ────────────────────────────────────────────────────

    def detect_device(self, force: bool = False) -> DeviceContext:
        """
        Return the best available execution device.
        Result is cached for _ctx_ttl seconds.
        """
        now = time.monotonic()
        with self._lock:
            if not force and self._ctx and (now - self._ctx_timestamp) < self._ctx_ttl:
                return self._ctx
            ctx = self._detect_fresh()
            self._ctx = ctx
            self._ctx_timestamp = now
            return ctx

    def _detect_fresh(self) -> DeviceContext:
        """Probe all available frameworks and build a DeviceContext."""
        # 1. Try PyTorch CUDA
        try:
            import torch
            if torch.cuda.is_available():
                idx = 0
                name = torch.cuda.get_device_name(idx)
                total = torch.cuda.get_device_properties(idx).total_memory // (1024 * 1024)
                free  = (torch.cuda.get_device_properties(idx).total_memory
                         - torch.cuda.memory_allocated(idx)) // (1024 * 1024)
                cuda_ver = getattr(torch.version, "cuda", None)
                _log.info("DeviceManager: PyTorch CUDA selected — %s", name)
                return DeviceContext(
                    device_type="cuda", device_index=idx, device_str=f"cuda:{idx}",
                    gpu_name=name, framework="pytorch",
                    cuda_available=True, cuda_version=cuda_ver,
                    vram_total_mb=total, vram_free_mb=free, is_fallback=False,
                )
        except ImportError:
            pass
        except Exception as exc:
            _log.warning("PyTorch CUDA probe failed: %s", exc)

        # 2. Try TensorFlow GPU
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                _log.info("DeviceManager: TensorFlow GPU selected — %s", gpus[0].name)
                return DeviceContext(
                    device_type="cuda", device_index=0, device_str="tf-gpu:0",
                    gpu_name=str(gpus[0].name), framework="tensorflow",
                    cuda_available=True, cuda_version=None,
                    vram_total_mb=0, vram_free_mb=0, is_fallback=False,
                )
        except ImportError:
            pass
        except Exception as exc:
            _log.warning("TF GPU probe failed: %s", exc)

        # 3. CPU fallback
        _log.info("DeviceManager: CPU fallback selected")
        return DeviceContext(
            device_type="cpu", device_index=0, device_str="cpu",
            gpu_name="CPU", framework="cpu",
            cuda_available=False, cuda_version=None,
            vram_total_mb=0, vram_free_mb=0, is_fallback=True,
        )

    def select_device(self, prefer_gpu: bool = True) -> str:
        """Return device string — 'cuda:0' or 'cpu'."""
        ctx = self.detect_device()
        if prefer_gpu:
            return ctx.device_str
        return "cpu"

    # ── Memory info ─────────────────────────────────────────────────────────

    def get_memory_info(self) -> GPUMemoryInfo:
        """Return structured GPU memory snapshot."""
        ctx = self.detect_device()

        if ctx.framework == "pytorch":
            try:
                import torch
                idx = ctx.device_index
                props = torch.cuda.get_device_properties(idx)
                total = props.total_memory / (1024 * 1024)
                alloc = torch.cuda.memory_allocated(idx) / (1024 * 1024)
                reserv = torch.cuda.memory_reserved(idx) / (1024 * 1024)
                peak_a = torch.cuda.max_memory_allocated(idx) / (1024 * 1024)
                peak_r = torch.cuda.max_memory_reserved(idx) / (1024 * 1024)
                free   = total - alloc
                util   = (alloc / total * 100) if total > 0 else 0.0
                return GPUMemoryInfo(
                    allocated_mb=round(alloc, 1), reserved_mb=round(reserv, 1),
                    peak_allocated_mb=round(peak_a, 1), peak_reserved_mb=round(peak_r, 1),
                    free_mb=round(free, 1), total_mb=round(total, 1),
                    utilization_pct=round(util, 1), source="pytorch",
                )
            except Exception as exc:
                _log.debug("PyTorch memory info failed: %s", exc)

        # CPU-mode or unavailable
        return GPUMemoryInfo(
            allocated_mb=0.0, reserved_mb=0.0, peak_allocated_mb=0.0,
            peak_reserved_mb=0.0, free_mb=0.0, total_mb=0.0,
            utilization_pct=0.0, source="not_available",
        )

    def reset_peak_memory_stats(self) -> None:
        """Reset PyTorch peak memory stats before a benchmark/inference run."""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
        except Exception:
            pass

    def synchronize(self) -> None:
        """
        Synchronize CUDA stream (blocking) so timing is accurate.
        No-op on CPU.
        """
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.synchronize()
        except Exception:
            pass

    def clear_cache(self) -> None:
        """
        Clear GPU memory cache.
        ONLY call this when technically justified (e.g., after OOM recovery).
        Do NOT call this as a fake optimization.
        """
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                _log.debug("GPU cache cleared")
        except Exception:
            pass

    # ── Health check ────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """
        Return a structured health dict suitable for admin dashboards.
        Never raises.
        """
        try:
            ctx = self.detect_device(force=True)
            mem = self.get_memory_info()
            gov = self.governor.stats

            # Try to get GPU utilization from gpu_manager
            util_pct: Any = "N/A"
            temp: Any = "N/A"
            power: Any = "N/A"
            try:
                from smartcore.gpu_manager import gpu_manager
                s = gpu_manager.get_gpu_status()
                util_pct = s.get("utilization_percent", "N/A")
                temp     = s.get("temperature_c", "N/A")
                power    = s.get("power_draw_w", "N/A")
            except Exception:
                pass

            return {
                "status":             "healthy" if ctx.cuda_available else "cpu_fallback",
                "device_str":         ctx.device_str,
                "device_type":        ctx.device_type,
                "gpu_name":           ctx.gpu_name,
                "framework":          ctx.framework,
                "cuda_available":     ctx.cuda_available,
                "cuda_version":       ctx.cuda_version,
                "is_fallback":        ctx.is_fallback,
                "vram_total_mb":      ctx.vram_total_mb,
                "vram_free_mb":       ctx.vram_free_mb,
                "memory_allocated_mb": mem.allocated_mb,
                "memory_reserved_mb":  mem.reserved_mb,
                "peak_memory_mb":      mem.peak_allocated_mb,
                "utilization_pct":    util_pct,
                "temperature_c":      temp,
                "power_draw_w":       power,
                "governor":           gov,
                "checked_at":         time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as exc:
            _log.error("Device health check failed: %s", exc)
            return {
                "status":  "error",
                "error":   str(exc),
                "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

    # ── Benchmarking ────────────────────────────────────────────────────────

    def benchmark_device(
        self,
        input_shape: Tuple[int, ...] = (1, 3, 224, 224),
        warmup_iters: int = WARMUP_ITERS,
        measured_iters: int = BENCHMARK_ITERS,
        precision: str = "FP32",
    ) -> DeviceBenchmarkResult:
        """
        Run a controlled micro-benchmark on the current device.
        Separate warmup from measurement — never report compile/warmup as inference.
        Returns a DeviceBenchmarkResult with real P50/P95/P99 statistics.
        """
        ctx = self.detect_device()
        result = DeviceBenchmarkResult(
            device_str=ctx.device_str,
            framework=ctx.framework,
            workload=f"matrix_multiply_{input_shape}",
            warmup_iters=warmup_iters,
            measured_iters=measured_iters,
            precision=precision,
        )

        # PyTorch path
        if ctx.framework == "pytorch":
            try:
                import torch
                result = self._benchmark_pytorch(ctx, input_shape, warmup_iters, measured_iters, precision)
                return result
            except Exception as exc:
                result.error = str(exc)
                _log.warning("PyTorch benchmark failed: %s — falling back to NumPy", exc)

        # NumPy CPU path (always available)
        result = self._benchmark_numpy(ctx, input_shape, warmup_iters, measured_iters)
        return result

    def _benchmark_pytorch(
        self, ctx: DeviceContext,
        shape: Tuple[int, ...], warmup: int, n: int, precision: str
    ) -> DeviceBenchmarkResult:
        import torch
        dev = ctx.device_str
        res = DeviceBenchmarkResult(
            device_str=dev, framework="pytorch",
            workload=f"conv2d_{shape}", warmup_iters=warmup, measured_iters=n, precision=precision,
        )
        # Create a small conv layer as workload (representative of CNN inference)
        in_ch = shape[1] if len(shape) >= 2 else 3
        model = torch.nn.Conv2d(in_ch, 64, kernel_size=3, padding=1).to(dev)
        model.eval()

        # AMP context
        use_amp = (precision == "FP16") and ctx.cuda_available
        amp_ctx = torch.amp.autocast(device_type=ctx.device_type) if use_amp else __import__("contextlib").nullcontext()

        dummy = torch.randn(*shape).to(dev)
        self.reset_peak_memory_stats()
        mem_before = self.get_memory_info()

        with torch.inference_mode():
            # Warmup — discard timing
            for _ in range(warmup):
                with amp_ctx:
                    _ = model(dummy)
            self.synchronize()

            # Measurement
            latencies = []
            for _ in range(n):
                self.synchronize()
                t0 = time.perf_counter()
                with amp_ctx:
                    _ = model(dummy)
                self.synchronize()
                latencies.append((time.perf_counter() - t0) * 1000)

        mem_after = self.get_memory_info()
        peak_mem  = self.get_memory_info()  # reads peak_allocated_mb

        res.latencies_ms      = latencies
        res.memory_before_mb  = mem_before.allocated_mb
        res.memory_after_mb   = mem_after.allocated_mb
        res.peak_memory_mb    = peak_mem.peak_allocated_mb
        res.compute_stats()
        return res

    def _benchmark_numpy(
        self, ctx: DeviceContext,
        shape: Tuple[int, ...], warmup: int, n: int
    ) -> DeviceBenchmarkResult:
        import numpy as np
        size = shape[-1] if shape else 224
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)

        res = DeviceBenchmarkResult(
            device_str="cpu", framework="numpy",
            workload=f"matmul_{size}x{size}", warmup_iters=warmup, measured_iters=n, precision="FP32",
        )

        # Warmup
        for _ in range(warmup):
            _ = np.dot(a, b)

        # Measure
        latencies = []
        for _ in range(n):
            t0 = time.perf_counter()
            _ = np.dot(a, b)
            latencies.append((time.perf_counter() - t0) * 1000)

        res.latencies_ms = latencies
        res.compute_stats()
        return res

    # ── OOM handling ─────────────────────────────────────────────────────────

    def handle_oom(self, batch_size: int) -> Tuple[bool, int]:
        """
        Called when a CUDA OOM error occurs.
        Returns (should_retry, new_batch_size).
        Halves batch size once, then signals no retry.
        """
        _log.error("CUDA OOM detected — clearing cache, halving batch size from %d", batch_size)
        self.clear_cache()
        new_size = batch_size // 2
        if new_size < 1:
            _log.error("Batch size would be <1 after halving — giving up GPU execution")
            return False, 0
        _log.warning("Retrying with batch_size=%d", new_size)
        return True, new_size


# ── Module-level singleton ──────────────────────────────────────────────────
device_manager = DeviceManager()
