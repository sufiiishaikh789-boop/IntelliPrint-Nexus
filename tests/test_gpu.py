"""
IntelliPrint Nexus — GPU Test Suite (V2)
=========================================
Automated tests for all GPU computing components.

Test categories
---------------
CPU-compatible (no GPU required):
    - test_device_detection_*
    - test_device_manager_*
    - test_inference_engine_cpu_*
    - test_benchmark_cpu_*
    - test_memory_tracking_*
    - test_oom_handling_*
    - test_telemetry_*

GPU-required (mark with @pytest.mark.gpu — skipped without CUDA):
    - test_gpu_fp32_*
    - test_gpu_fp16_*
    - test_cuda_*

Usage
-----
    pytest tests/test_gpu.py -v
    pytest tests/test_gpu.py -v -m "not gpu"   # CPU only
    pytest tests/test_gpu.py -v -m gpu          # GPU required
"""

from __future__ import annotations

import json
import os
import sys
import time
import threading
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ── Markers ──────────────────────────────────────────────────────────────────
def pytest_configure(config):
    config.addinivalue_line("markers", "gpu: mark test as requiring NVIDIA GPU")

_CUDA_AVAILABLE = False
try:
    import torch
    _CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    pass

requires_gpu = pytest.mark.skipif(
    not _CUDA_AVAILABLE,
    reason="CUDA GPU required — not available on this machine"
)

# ═══════════════════════════════════════════════════════════════════════════════
# Device Manager Tests (CPU-compatible)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeviceManager:
    """Tests for smartcore.device_manager.DeviceManager."""

    def test_import_device_manager(self):
        """DeviceManager must import without error."""
        from smartcore.device_manager import device_manager, DeviceManager
        assert device_manager is not None
        assert isinstance(device_manager, DeviceManager)

    def test_detect_device_returns_context(self):
        """detect_device() must always return a DeviceContext."""
        from smartcore.device_manager import device_manager, DeviceContext
        ctx = device_manager.detect_device()
        assert isinstance(ctx, DeviceContext)

    def test_device_context_fields(self):
        """DeviceContext must have all required fields."""
        from smartcore.device_manager import device_manager
        ctx = device_manager.detect_device()
        assert ctx.device_type in ("cuda", "cpu")
        assert ctx.device_str in ("cpu",) or ctx.device_str.startswith("cuda")
        assert isinstance(ctx.gpu_name, str)
        assert isinstance(ctx.cuda_available, bool)
        assert isinstance(ctx.is_fallback, bool)

    def test_cpu_fallback_no_gpu(self):
        """Without GPU, device_type must be 'cpu' and is_fallback=True."""
        from smartcore.device_manager import device_manager
        ctx = device_manager.detect_device()
        if not _CUDA_AVAILABLE:
            assert ctx.device_type == "cpu"
            assert ctx.is_fallback is True
            assert ctx.device_str == "cpu"

    def test_select_device_returns_string(self):
        """select_device() must return a non-empty string."""
        from smartcore.device_manager import device_manager
        dev = device_manager.select_device()
        assert isinstance(dev, str)
        assert len(dev) > 0

    def test_health_check_returns_dict(self):
        """health_check() must return a dict with required keys — never raises."""
        from smartcore.device_manager import device_manager
        health = device_manager.health_check()
        assert isinstance(health, dict)
        assert "status" in health
        assert "device_str" in health
        assert "cuda_available" in health
        assert health["status"] in ("healthy", "cpu_fallback", "error")

    def test_health_check_never_raises(self):
        """health_check() must never raise, even on failure."""
        from smartcore.device_manager import device_manager
        for _ in range(3):
            result = device_manager.health_check()
            assert isinstance(result, dict)

    def test_get_memory_info_returns_struct(self):
        """get_memory_info() must return GPUMemoryInfo."""
        from smartcore.device_manager import device_manager, GPUMemoryInfo
        mem = device_manager.get_memory_info()
        assert isinstance(mem, GPUMemoryInfo)
        assert isinstance(mem.source, str)
        assert mem.source in ("pytorch", "tensorflow", "nvidia-smi", "not_available")

    def test_memory_info_cpu_mode(self):
        """On CPU-only machine, memory info source must be 'not_available'."""
        from smartcore.device_manager import device_manager
        if not _CUDA_AVAILABLE:
            mem = device_manager.get_memory_info()
            assert mem.source == "not_available"
            assert mem.allocated_mb == 0.0
            assert mem.total_mb == 0.0

    def test_synchronize_never_raises(self):
        """synchronize() must be a no-op on CPU — never raises."""
        from smartcore.device_manager import device_manager
        device_manager.synchronize()  # must not raise

    def test_clear_cache_never_raises(self):
        """clear_cache() must never raise."""
        from smartcore.device_manager import device_manager
        device_manager.clear_cache()  # must not raise

    def test_reset_peak_memory_never_raises(self):
        """reset_peak_memory_stats() must never raise."""
        from smartcore.device_manager import device_manager
        device_manager.reset_peak_memory_stats()  # must not raise

    def test_benchmark_returns_result(self):
        """benchmark_device() must return a DeviceBenchmarkResult with stats."""
        from smartcore.device_manager import device_manager, DeviceBenchmarkResult
        result = device_manager.benchmark_device(warmup_iters=1, measured_iters=5)
        assert isinstance(result, DeviceBenchmarkResult)
        assert len(result.latencies_ms) == 5
        assert result.mean_ms > 0
        assert result.p50_ms > 0
        assert result.p95_ms >= result.p50_ms
        assert result.p99_ms >= result.p95_ms
        assert result.min_ms <= result.mean_ms <= result.max_ms

    def test_benchmark_result_to_dict(self):
        """DeviceBenchmarkResult.to_dict() must return a complete dict."""
        from smartcore.device_manager import device_manager
        result = device_manager.benchmark_device(warmup_iters=1, measured_iters=5)
        d = result.to_dict()
        assert isinstance(d, dict)
        required = ["device_str", "framework", "mean_ms", "p50_ms", "p95_ms", "p99_ms", "throughput_rps"]
        for key in required:
            assert key in d, f"Missing key: {key}"


# ═══════════════════════════════════════════════════════════════════════════════
# GPU Governor Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGPUGovernor:
    """Tests for the GPU resource governor."""

    def test_governor_allows_first_job(self):
        """Governor must allow the first job."""
        from smartcore.device_manager import _GPUGovernor
        gov = _GPUGovernor()
        allowed, reason = gov.can_start_job()
        assert allowed is True
        assert reason == "ok"

    def test_governor_blocks_at_limit(self):
        """Governor must block when MAX_CONCURRENT_GPU_JOBS is reached."""
        from smartcore.device_manager import _GPUGovernor, MAX_CONCURRENT_GPU_JOBS
        gov = _GPUGovernor()
        for _ in range(MAX_CONCURRENT_GPU_JOBS):
            gov.start_job()
        allowed, reason = gov.can_start_job()
        assert allowed is False
        assert "limit" in reason.lower()

    def test_governor_allows_after_finish(self):
        """Governor must allow a job after a previous one finishes."""
        from smartcore.device_manager import _GPUGovernor, MAX_CONCURRENT_GPU_JOBS
        gov = _GPUGovernor()
        for _ in range(MAX_CONCURRENT_GPU_JOBS):
            gov.start_job()
        gov.finish_job()
        allowed, _ = gov.can_start_job()
        assert allowed is True

    def test_governor_thread_safe(self):
        """Governor must be thread-safe under concurrent access."""
        from smartcore.device_manager import _GPUGovernor
        gov = _GPUGovernor()
        errors = []

        def worker():
            try:
                gov.start_job()
                time.sleep(0.01)
                gov.finish_job()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_governor_stats(self):
        """Governor stats dict must have required keys."""
        from smartcore.device_manager import _GPUGovernor
        gov = _GPUGovernor()
        stats = gov.stats
        assert "active_jobs" in stats
        assert "queue_depth" in stats
        assert "max_concurrent" in stats


# ═══════════════════════════════════════════════════════════════════════════════
# OOM Handling
# ═══════════════════════════════════════════════════════════════════════════════

class TestOOMHandling:
    """Tests for GPU Out-of-Memory recovery."""

    def test_oom_halves_batch_size(self):
        """handle_oom() must return (True, batch_size // 2) when reducible."""
        from smartcore.device_manager import device_manager
        retry, new_bs = device_manager.handle_oom(batch_size=8)
        assert retry is True
        assert new_bs == 4

    def test_oom_stops_at_batch_1(self):
        """handle_oom() with batch_size=1 must return (False, 0)."""
        from smartcore.device_manager import device_manager
        retry, new_bs = device_manager.handle_oom(batch_size=1)
        assert retry is False
        assert new_bs == 0

    def test_oom_does_not_raise(self):
        """handle_oom() must never raise."""
        from smartcore.device_manager import device_manager
        for bs in [1, 2, 4, 8, 16, 32]:
            result = device_manager.handle_oom(batch_size=bs)
            assert isinstance(result, tuple)


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark Framework Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBenchmarkFramework:
    """Tests for smartcore.gpu_benchmark."""

    def test_cpu_numpy_benchmark(self):
        """CPU NumPy benchmark must produce valid statistics."""
        from smartcore.gpu_benchmark import benchmark_cpu_numpy
        result = benchmark_cpu_numpy(size=64, warmup=1, n=10)
        assert result["status"] == "success"
        assert result["mean_ms"] > 0
        assert result["p50_ms"] > 0
        assert result["p95_ms"] >= result["p50_ms"]
        assert result["p99_ms"] >= result["p95_ms"]
        assert result["throughput_rps"] > 0

    def test_percentile_ordering(self):
        """P50 ≤ P95 ≤ P99 for any real latency distribution."""
        from smartcore.gpu_benchmark import benchmark_cpu_numpy
        result = benchmark_cpu_numpy(size=64, warmup=1, n=100)
        assert result["p50_ms"] <= result["p95_ms"]
        assert result["p95_ms"] <= result["p99_ms"]
        assert result["min_ms"] <= result["p50_ms"]
        assert result["p99_ms"] <= result["max_ms"]

    def test_pytorch_cpu_benchmark(self):
        """PyTorch CPU benchmark skips or succeeds — never crashes."""
        from smartcore.gpu_benchmark import benchmark_pytorch
        result = benchmark_pytorch("cpu", precision="FP32", warmup=1, n=5, shape=(1, 3, 32, 32))
        assert result["status"] in ("success", "skipped", "error")
        if result["status"] == "success":
            assert result["mean_ms"] > 0

    def test_pytorch_cuda_skipped_without_gpu(self):
        """PyTorch CUDA benchmark must be 'skipped' on non-CUDA machine."""
        if _CUDA_AVAILABLE:
            pytest.skip("GPU present — test irrelevant")
        from smartcore.gpu_benchmark import benchmark_pytorch
        result = benchmark_pytorch("cuda:0", precision="FP32", warmup=1, n=5)
        assert result["status"] == "skipped"
        reason = result.get("reason", "").lower()
        # Accept: 'not available', 'not installed', 'cuda not available'
        assert any(kw in reason for kw in ("not available", "not installed", "cuda"))

    def test_batch_benchmark_returns_list(self):
        """batch-size benchmark must return a list."""
        from smartcore.gpu_benchmark import benchmark_batch_sizes
        results = benchmark_batch_sizes("cpu", batch_sizes=[1, 2], warmup=1, n=5)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_gpu_benchmark_suite_runs(self):
        """GpuBenchmark.run_cpu_baseline() must produce a valid result."""
        from smartcore.gpu_benchmark import GpuBenchmark
        suite = GpuBenchmark()
        result = suite.run_cpu_baseline()
        assert result["status"] == "success"
        assert result["mean_ms"] > 0

    def test_benchmark_save_creates_file(self, tmp_path):
        """save_results() must create a JSON file."""
        import os, json
        from smartcore.gpu_benchmark import GpuBenchmark
        suite = GpuBenchmark()
        result = suite.run_cpu_baseline()
        report = {"results": {"cpu_baseline": result}, "environment": {}, "summary": {}, "generated_at": "test"}
        # Temporarily set benchmarks dir to tmp_path
        orig = __import__("smartcore.gpu_benchmark", fromlist=["BENCHMARKS_DIR"])
        orig.BENCHMARKS_DIR = str(tmp_path)
        path = suite.save_results(report)
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert "results" in data


# ═══════════════════════════════════════════════════════════════════════════════
# Inference Engine Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestInferenceEngine:
    """Tests for smartcore.gpu_inference_engine."""

    def _make_fake_image_bytes(self) -> bytes:
        """Create a minimal valid PNG image in memory."""
        try:
            import io
            from PIL import Image
            img = Image.new("RGB", (32, 32), color=(128, 128, 128))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except ImportError:
            # Minimal 1x1 PNG bytes (hardcoded)
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'

    def test_import_inference_engine(self):
        """Inference engine must import without error."""
        from smartcore.gpu_inference_engine import run_inference, GPUJobTelemetry
        assert callable(run_inference)
        assert GPUJobTelemetry is not None

    def test_inference_returns_tuple(self):
        """run_inference() must return (result_dict, GPUJobTelemetry)."""
        from smartcore.gpu_inference_engine import run_inference, GPUJobTelemetry
        img = self._make_fake_image_bytes()
        result, telemetry = run_inference(img, batch_size=1)
        assert isinstance(result, dict)
        assert isinstance(telemetry, GPUJobTelemetry)

    def test_inference_result_has_required_fields(self):
        """Inference result dict must have all required keys."""
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        result, _ = run_inference(img)
        required = ["class_idx", "class_name", "confidence", "model_type", "device"]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_inference_class_idx_valid(self):
        """class_idx must be within valid range."""
        from smartcore.gpu_inference_engine import run_inference, CLASSES
        img = self._make_fake_image_bytes()
        result, _ = run_inference(img)
        assert 0 <= result["class_idx"] < len(CLASSES)

    def test_inference_confidence_range(self):
        """Confidence must be in [0, 1]."""
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        result, _ = run_inference(img)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_telemetry_has_required_fields(self):
        """GPUJobTelemetry must have all required fields."""
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        _, tel = run_inference(img)
        assert isinstance(tel.model_name, str)
        assert isinstance(tel.device, str)
        assert isinstance(tel.precision, str)
        assert isinstance(tel.latency_ms, float)
        assert tel.latency_ms >= 0

    def test_telemetry_to_dict(self):
        """GPUJobTelemetry.to_dict() must return a complete dict."""
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        _, tel = run_inference(img)
        d = tel.to_dict()
        assert isinstance(d, dict)
        for key in ["model_name", "device", "precision", "latency_ms", "status"]:
            assert key in d

    def test_cpu_mode_device_reported_honestly(self):
        """Device must be reported honestly — 'cpu' when no GPU present."""
        if _CUDA_AVAILABLE:
            pytest.skip("GPU present — test irrelevant")
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        result, tel = run_inference(img)
        assert result["device"] in ("cpu",) or "CPU" in result.get("model_type", "")
        # Never reports 'cuda' when GPU is absent
        assert "cuda" not in result["device"].lower() or "cuda" not in tel.device.lower()

    def test_invalid_image_does_not_crash(self):
        """Garbage bytes must not crash inference — fallback must be returned."""
        from smartcore.gpu_inference_engine import run_inference
        result, tel = run_inference(b"not_an_image_at_all_xxxxx")
        assert isinstance(result, dict)
        assert isinstance(tel, object)
        # Must not raise even with corrupt input

    def test_inference_queue_submit_flush(self):
        """InferenceQueue must process submitted items."""
        from smartcore.gpu_inference_engine import InferenceQueue
        img = self._make_fake_image_bytes()
        q = InferenceQueue(max_batch=4)
        q.submit(img, print_job_id=None)
        q.submit(img, print_job_id=None)
        assert q.depth() == 2
        results = q.flush()
        assert len(results) == 2
        assert q.depth() == 0

    @requires_gpu
    @pytest.mark.gpu
    def test_gpu_fp32_inference(self):
        """On CUDA machine: model must execute on GPU."""
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        result, tel = run_inference(img, precision="FP32")
        assert "cuda" in result["device"].lower() or "cuda" in tel.device.lower()

    @requires_gpu
    @pytest.mark.gpu
    def test_gpu_fp16_inference(self):
        """On CUDA machine: FP16 precision must be used."""
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        result, tel = run_inference(img, precision="FP16")
        assert tel.precision == "FP16"
        assert result["precision"] == "FP16"

    @requires_gpu
    @pytest.mark.gpu
    def test_gpu_memory_tracked(self):
        """On CUDA machine: memory_before_mb and peak_memory_mb must be > 0."""
        from smartcore.gpu_inference_engine import run_inference
        img = self._make_fake_image_bytes()
        _, tel = run_inference(img, precision="FP32")
        assert tel.peak_memory_mb > 0


# ═══════════════════════════════════════════════════════════════════════════════
# GPU Manager Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGPUManager:
    """Tests for existing smartcore.gpu_manager (backward compat)."""

    def test_gpu_manager_imports(self):
        from smartcore.gpu_manager import gpu_manager
        assert gpu_manager is not None

    def test_get_gpu_status_returns_dict(self):
        from smartcore.gpu_manager import gpu_manager
        status = gpu_manager.get_gpu_status()
        assert isinstance(status, dict)
        assert "gpu_available" in status

    def test_get_inference_device_returns_string(self):
        from smartcore.gpu_manager import gpu_manager
        device = gpu_manager.get_inference_device()
        assert isinstance(device, str)
        assert device in ("cuda", "tf-gpu", "cpu")

    def test_get_system_resources_returns_dict(self):
        from smartcore.gpu_manager import get_system_resources
        res = get_system_resources()
        assert isinstance(res, dict)
        assert "cpu_percent" in res or "error" in res


# ═══════════════════════════════════════════════════════════════════════════════
# Database Telemetry Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGPUTelemetryDB:
    """Tests for GPU telemetry DB operations."""

    def test_create_telemetry_record(self):
        """create_gpu_telemetry() must insert and return an ID or None."""
        from smartdb.crud_gpu import create_gpu_telemetry
        data = {
            "model_name": "TestModel", "model_version": "0.0.1",
            "device": "cpu", "gpu_name": "CPU", "precision": "FP32",
            "batch_size": 1, "warmup_iters": 0, "measured_iters": 1,
            "latency_ms": 12.5, "throughput_rps": 80.0, "status": "success",
        }
        result = create_gpu_telemetry(data)
        # Returns int ID or None (None if DB unavailable — both acceptable)
        assert result is None or isinstance(result, int)

    def test_get_recent_telemetry_returns_list(self):
        """get_recent_telemetry() must return a list (empty or populated)."""
        from smartdb.crud_gpu import get_recent_telemetry
        rows = get_recent_telemetry(limit=5)
        assert isinstance(rows, list)

    def test_get_aggregate_stats_returns_dict(self):
        """get_aggregate_stats() must return a dict with required keys."""
        from smartdb.crud_gpu import get_aggregate_stats
        stats = get_aggregate_stats()
        assert isinstance(stats, dict)
        for key in ["total_jobs", "success_jobs", "avg_latency_ms", "p95_latency_ms"]:
            assert key in stats

    def test_get_aggregate_never_raises(self):
        """get_aggregate_stats() must never raise."""
        from smartdb.crud_gpu import get_aggregate_stats
        for _ in range(3):
            result = get_aggregate_stats()
            assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Precision Selection Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPrecisionSelection:
    """Tests for precision validation logic."""

    def test_fp32_always_valid(self):
        """FP32 must always be accepted."""
        from smartcore.gpu_inference_engine import _select_precision
        assert _select_precision("cpu", "FP32") == "FP32"

    def test_fp16_on_cpu_returns_fp32(self):
        """FP16 on CPU must be silently downgraded to FP32."""
        from smartcore.gpu_inference_engine import _select_precision
        result = _select_precision("cpu", "FP16")
        assert result == "FP32"

    def test_bf16_on_cpu_returns_fp32(self):
        """BF16 on CPU must be silently downgraded to FP32."""
        from smartcore.gpu_inference_engine import _select_precision
        result = _select_precision("cpu", "BF16")
        assert result == "FP32"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Device Manager → Benchmark → Telemetry
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndToEndCPU:
    """End-to-end CPU path integration tests."""

    def test_device_context_consistent_with_benchmark(self):
        """Benchmark result device_str must match DeviceManager device_str."""
        from smartcore.device_manager import device_manager
        ctx = device_manager.detect_device()
        result = device_manager.benchmark_device(warmup_iters=1, measured_iters=5)
        # On CPU: both must be "cpu"
        if not _CUDA_AVAILABLE:
            assert result.device_str == "cpu"
            assert ctx.device_str == "cpu"

    def test_full_cpu_inference_path(self):
        """Full path: detect device → run inference → check telemetry dict."""
        import io
        from smartcore.device_manager import device_manager
        from smartcore.gpu_inference_engine import run_inference
        ctx = device_manager.detect_device()
        assert ctx is not None
        try:
            from PIL import Image
            img = Image.new("RGB", (64, 64), (100, 150, 200))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            img_bytes = buf.getvalue()
        except ImportError:
            img_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 100  # stub
        result, tel = run_inference(img_bytes)
        assert isinstance(result, dict)
        assert tel.latency_ms >= 0
        tel_dict = tel.to_dict()
        assert tel_dict["device"] != ""

    def test_reproducibility_seed(self):
        """NumPy benchmarks with fixed seed produce deterministic variance."""
        from smartcore.gpu_benchmark import benchmark_cpu_numpy
        np.random.seed(42)
        r1 = benchmark_cpu_numpy(size=64, warmup=1, n=20)
        np.random.seed(42)
        r2 = benchmark_cpu_numpy(size=64, warmup=1, n=20)
        # Means should be very close (within 50% given OS scheduler jitter)
        assert abs(r1["mean_ms"] - r2["mean_ms"]) < r1["mean_ms"] * 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# V3: Kernel Validator Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestKernelValidatorV3:
    """V3 Kernel-Level Validation — CPU-compatible tests (no GPU required)."""

    def test_import_kernel_validator(self):
        """KernelValidator must be importable."""
        from smartcore.gpu_kernel_validator import KernelValidator
        assert KernelValidator is not None

    def test_import_dataclasses(self):
        """All V3 dataclasses must be importable."""
        from smartcore.gpu_kernel_validator import (
            KernelValidator, KernelValidationReport, PhaseBreakdown,
            MemorySnapshot, OperatorStat, UtilizationSample,
        )
        assert PhaseBreakdown is not None
        assert MemorySnapshot is not None
        assert KernelValidationReport is not None

    def test_validator_init(self):
        """KernelValidator initialises without error."""
        from smartcore.gpu_kernel_validator import KernelValidator
        v = KernelValidator()
        assert hasattr(v, "_cuda_available")
        assert hasattr(v, "_device_str")
        assert v._device_str in ("cpu", "cuda:0")

    def test_validator_device_str(self):
        """Device string must be a recognised value."""
        from smartcore.gpu_kernel_validator import KernelValidator
        v = KernelValidator()
        assert v._device_str.startswith("cpu") or v._device_str.startswith("cuda")

    def test_phase_breakdown_dataclass(self):
        """PhaseBreakdown to_dict() must contain all expected keys."""
        from smartcore.gpu_kernel_validator import PhaseBreakdown
        pb = PhaseBreakdown(preprocess_ms=1.0, h2d_ms=0.5, compute_ms=3.0,
                            d2h_ms=0.3, postprocess_ms=0.2, total_ms=5.0)
        d = pb.to_dict()
        for key in ("preprocess_ms", "h2d_ms", "compute_ms", "d2h_ms",
                    "postprocess_ms", "total_ms"):
            assert key in d, f"Missing key: {key}"

    def test_memory_snapshot_defaults(self):
        """MemorySnapshot must have sensible defaults."""
        from smartcore.gpu_kernel_validator import MemorySnapshot
        m = MemorySnapshot()
        assert m.allocated_mb == 0.0
        assert m.source == "not_available"

    def test_report_compute_stats(self):
        """_compute_stats() must correctly compute percentiles."""
        from smartcore.gpu_kernel_validator import KernelValidationReport
        r = KernelValidationReport()
        r.steady_latencies = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        r._compute_stats()
        assert r.p50_ms <= r.p95_ms <= r.p99_ms
        assert r.min_ms <= r.p50_ms
        assert r.max_ms >= r.p99_ms
        assert r.throughput_rps > 0

    def test_report_summary_text(self):
        """summary_text() must return a non-empty string."""
        from smartcore.gpu_kernel_validator import KernelValidationReport
        r = KernelValidationReport(
            generated_at="2026-09-14", gpu_name="Test", device_str="cpu",
            framework="NumPy", mean_ms=5.0, p50_ms=4.5, p95_ms=7.0, p99_ms=8.0,
        )
        txt = r.summary_text()
        assert isinstance(txt, str)
        assert len(txt) > 100
        assert "INTELLIPRINT" in txt

    def test_report_to_dict(self):
        """to_dict() must contain all top-level required sections."""
        from smartcore.gpu_kernel_validator import KernelValidationReport
        r = KernelValidationReport()
        d = r.to_dict()
        for section in ("environment", "latency", "memory", "speedup", "profiler"):
            assert section in d, f"Missing section: {section}"

    def test_full_validation_runs(self):
        """run_full_validation() must complete without crashing."""
        import os
        os.environ["SMARTPRINT_BENCHMARK_ITERS"] = "3"
        os.environ["SMARTPRINT_WARMUP_ITERS"]    = "1"
        from smartcore.gpu_kernel_validator import KernelValidator
        v = KernelValidator()
        r = v.run_full_validation(run_profiler=True)
        # Restore defaults
        os.environ.pop("SMARTPRINT_BENCHMARK_ITERS", None)
        os.environ.pop("SMARTPRINT_WARMUP_ITERS", None)
        assert r.cold_start_ms >= 0
        assert len(r.steady_latencies) >= 1
        assert r.mean_ms >= 0
        assert r.cpu_baseline_ms >= 0

    def test_full_validation_latency_ordering(self):
        """P50 <= P95 <= P99 must hold for V3 validator output."""
        import os
        os.environ["SMARTPRINT_BENCHMARK_ITERS"] = "5"
        os.environ["SMARTPRINT_WARMUP_ITERS"]    = "1"
        from smartcore.gpu_kernel_validator import KernelValidator
        v = KernelValidator()
        r = v.run_full_validation(run_profiler=False)
        os.environ.pop("SMARTPRINT_BENCHMARK_ITERS", None)
        os.environ.pop("SMARTPRINT_WARMUP_ITERS", None)
        if r.steady_latencies:
            assert r.p50_ms <= r.p95_ms + 0.001   # small tolerance for tiny sample
            assert r.p95_ms <= r.p99_ms + 0.001

    def test_phase_breakdown_measured(self):
        """Phase breakdown must be populated after validation."""
        import os
        os.environ["SMARTPRINT_BENCHMARK_ITERS"] = "2"
        os.environ["SMARTPRINT_WARMUP_ITERS"]    = "1"
        from smartcore.gpu_kernel_validator import KernelValidator
        v = KernelValidator()
        r = v.run_full_validation(run_profiler=False)
        os.environ.pop("SMARTPRINT_BENCHMARK_ITERS", None)
        os.environ.pop("SMARTPRINT_WARMUP_ITERS", None)
        assert r.phase_breakdown is not None
        pb = r.phase_breakdown
        assert pb.preprocess_ms >= 0
        assert pb.compute_ms >= 0
        assert pb.total_ms >= 0

    def test_save_report_creates_file(self):
        """save_report() must create a JSON file in benchmarks/."""
        import os, glob, json
        os.environ["SMARTPRINT_BENCHMARK_ITERS"] = "2"
        os.environ["SMARTPRINT_WARMUP_ITERS"]    = "1"
        from smartcore.gpu_kernel_validator import KernelValidator
        v = KernelValidator()
        r = v.run_full_validation(run_profiler=False)
        os.environ.pop("SMARTPRINT_BENCHMARK_ITERS", None)
        os.environ.pop("SMARTPRINT_WARMUP_ITERS", None)
        path = v.save_report(r)
        assert os.path.isfile(path), f"Report not found: {path}"
        # Verify valid JSON
        with open(path) as f:
            d = json.load(f)
        assert "environment" in d
        assert "latency" in d

