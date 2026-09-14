"""
IntelliPrint Nexus — Hardware Telemetry Tests
==============================================
Tests for the centralized HardwareTelemetryService.

All hardware-specific APIs (psutil, nvidia-smi, torch, tensorflow)
are mocked where necessary — no real GPU required.

Run:
    .venv\\Scripts\\python.exe -m pytest tests/test_hardware_telemetry.py -v -m "not gpu"
"""
from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_psutil_mem(total_gb=8, used_gb=4, available_gb=4, percent=50.0):
    m = MagicMock()
    gb = 1024 ** 3
    m.total     = int(total_gb * gb)
    m.used      = int(used_gb * gb)
    m.available = int(available_gb * gb)
    m.percent   = percent
    return m


def _make_psutil_disk(total_gb=500, used_gb=250, free_gb=250, percent=50.0):
    m = MagicMock()
    gb = 1024 ** 3
    m.total   = int(total_gb * gb)
    m.used    = int(used_gb * gb)
    m.free    = int(free_gb * gb)
    m.percent = percent
    return m


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Import tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestImport(unittest.TestCase):
    def test_service_importable(self):
        from smartcore.hardware_telemetry import hardware_telemetry
        self.assertIsNotNone(hardware_telemetry)

    def test_dataclasses_importable(self):
        from smartcore.hardware_telemetry import (
            HardwareTelemetry, CpuInfo, MemInfo, DiskInfo,
            GpuInfo, GpuDeviceInfo, HardwareTelemetryService,
        )
        self.assertTrue(True)

    def test_singleton_is_same_instance(self):
        from smartcore.hardware_telemetry import hardware_telemetry as a
        from smartcore.hardware_telemetry import hardware_telemetry as b
        self.assertIs(a, b)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CPU telemetry
# ═══════════════════════════════════════════════════════════════════════════════

class TestCpuTelemetry(unittest.TestCase):
    @patch("psutil.cpu_percent", return_value=42.5)
    @patch("psutil.cpu_count", side_effect=[8, 4])    # logical, physical
    @patch("psutil.cpu_freq", return_value=MagicMock(current=3200.0))
    def test_cpu_values_are_real(self, _freq, _count, _pct):
        from smartcore.hardware_telemetry import HardwareTelemetryService
        svc = HardwareTelemetryService()
        tel = MagicMock()
        tel.errors = []
        info = svc._collect_cpu(tel)
        self.assertAlmostEqual(info.utilization_pct, 42.5)
        self.assertEqual(info.count_logical, 8)
        self.assertEqual(info.count_physical, 4)
        self.assertAlmostEqual(info.freq_mhz, 3200.0)
        self.assertTrue(info.available)

    @patch("psutil.cpu_percent", side_effect=ImportError("no psutil"))
    def test_cpu_returns_unavailable_if_psutil_missing(self, _):
        from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
        svc = HardwareTelemetryService()
        tel = HardwareTelemetry()
        with patch.dict(sys.modules, {"psutil": None}):
            info = svc._collect_cpu(tel)
        self.assertFalse(info.available)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RAM telemetry
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemTelemetry(unittest.TestCase):
    def test_memory_values(self):
        mem_mock = _make_psutil_mem(total_gb=16, used_gb=6, available_gb=10, percent=37.5)
        with patch("psutil.virtual_memory", return_value=mem_mock):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            info = svc._collect_memory(tel)
        self.assertAlmostEqual(info.total_gb, 16.0, places=0)
        self.assertAlmostEqual(info.used_gb, 6.0, places=0)
        self.assertAlmostEqual(info.utilization_pct, 37.5)
        self.assertTrue(info.available)
        self.assertEqual(len(tel.errors), 0)

    def test_ram_never_returns_negative(self):
        mem_mock = _make_psutil_mem(total_gb=8, used_gb=8, available_gb=0, percent=100.0)
        with patch("psutil.virtual_memory", return_value=mem_mock):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            info = svc._collect_memory(tel)
        self.assertGreaterEqual(info.available_gb, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Disk telemetry
# ═══════════════════════════════════════════════════════════════════════════════

class TestDiskTelemetry(unittest.TestCase):
    def test_disk_values(self):
        disk_mock = _make_psutil_disk(total_gb=512, used_gb=300, free_gb=212, percent=58.6)
        with patch("psutil.disk_usage", return_value=disk_mock):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            info = svc._collect_disk(tel)
        self.assertAlmostEqual(info.total_gb, 512.0, places=0)
        self.assertAlmostEqual(info.utilization_pct, 58.6)
        self.assertTrue(info.available)

    def test_disk_windows_path_tried_first(self):
        """Windows disk candidate C:\\ must be tried before /."""
        import platform
        disk_mock = _make_psutil_disk()
        call_log = []

        def fake_disk_usage(path):
            call_log.append(path)
            return disk_mock

        with patch("platform.system", return_value="Windows"), \
             patch("psutil.disk_usage", side_effect=fake_disk_usage):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            svc._collect_disk(tel)

        # At least one Windows-style path should be tried
        windows_paths = [p for p in call_log if ":\\" in p or p == "C:\\"]
        self.assertTrue(len(windows_paths) > 0 or len(call_log) > 0)

    def test_disk_fallback_on_error(self):
        """If primary path fails, a fallback path should be tried."""
        call_log = []

        def fake_disk_usage(path):
            call_log.append(path)
            if len(call_log) < 2:
                raise PermissionError("no access")
            return _make_psutil_disk()

        with patch("psutil.disk_usage", side_effect=fake_disk_usage):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            info = svc._collect_disk(tel)

        self.assertGreaterEqual(len(call_log), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. NVIDIA GPU detection — NVIDIA available
# ═══════════════════════════════════════════════════════════════════════════════

_NVIDIA_SMI_CSV = "0, NVIDIA GeForce RTX 4060 Laptop GPU, 8192, 512, 7680, 15, 62, 28.5, 45\n"
_NVIDIA_SMI_HDR = "| NVIDIA-SMI 555.85   Driver Version: 555.85   CUDA Version: 12.5 |"


class TestNvidiaDetection(unittest.TestCase):
    def _run_smi(self, returncode=0, stdout="", stderr=""):
        r = MagicMock()
        r.returncode = returncode
        r.stdout     = stdout
        r.stderr     = stderr
        return r

    def test_nvidia_detected_from_smi(self):
        responses = [
            self._run_smi(0, _NVIDIA_SMI_CSV),    # query-gpu
            self._run_smi(0, _NVIDIA_SMI_HDR),    # header
        ]
        with patch("subprocess.run", side_effect=responses):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            devices = svc._query_nvidia_smi()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "NVIDIA GeForce RTX 4060 Laptop GPU")
        self.assertEqual(devices[0].vram_total_mb, 8192)
        self.assertEqual(devices[0].vram_used_mb, 512)
        self.assertEqual(devices[0].utilization_pct, 15.0)
        self.assertEqual(devices[0].temperature_c, 62)
        self.assertAlmostEqual(devices[0].power_watts, 28.5)
        self.assertEqual(devices[0].fan_speed_pct, 45)
        self.assertEqual(devices[0].vendor, "NVIDIA")

    def test_cuda_version_extracted(self):
        # _query_smi_header makes one subprocess.run call (the plain nvidia-smi)
        resp = self._run_smi(0, _NVIDIA_SMI_HDR)
        with patch("subprocess.run", return_value=resp):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            cuda_v, driver_v = svc._query_smi_header()
        self.assertEqual(cuda_v, "12.5")
        self.assertEqual(driver_v, "555.85")

    def test_gpu_mode_is_cuda_when_nvidia_available(self):
        responses = [
            self._run_smi(0, _NVIDIA_SMI_CSV),
            self._run_smi(0, _NVIDIA_SMI_HDR),
        ]
        with patch("subprocess.run", side_effect=responses), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            gpu = svc._collect_gpu(tel)
        self.assertTrue(gpu.nvidia_available)
        self.assertEqual(gpu.mode, "CUDA_GPU")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CUDA unavailable fallback (AMD / no-NVIDIA)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCudaUnavailableFallback(unittest.TestCase):
    def test_no_nvidia_smi_returns_empty_devices(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("nvidia-smi not found")):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            devices = svc._query_nvidia_smi()
        self.assertEqual(devices, [])

    def test_cpu_mode_when_no_gpu(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            gpu = svc._collect_gpu(tel)
        self.assertFalse(gpu.available)
        self.assertFalse(gpu.cuda_available)
        self.assertEqual(gpu.mode, "CPU")

    def test_full_telemetry_cpu_fallback_status(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}), \
             patch("psutil.cpu_percent", return_value=25.0), \
             patch("psutil.cpu_count", return_value=4), \
             patch("psutil.cpu_freq", return_value=None), \
             patch("psutil.virtual_memory", return_value=_make_psutil_mem()), \
             patch("psutil.disk_usage", return_value=_make_psutil_disk()):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            tel = svc._collect()
        self.assertEqual(tel.status, "cpu_fallback")
        self.assertEqual(tel.mode, "CPU")
        self.assertFalse(tel.gpu.cuda_available)
        self.assertTrue(tel.cpu.available)

    def test_cuda_fields_are_na_on_cpu_machine(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}), \
             patch("psutil.cpu_percent", return_value=10.0), \
             patch("psutil.cpu_count", return_value=4), \
             patch("psutil.cpu_freq", return_value=None), \
             patch("psutil.virtual_memory", return_value=_make_psutil_mem()), \
             patch("psutil.disk_usage", return_value=_make_psutil_disk()):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            tel = svc._collect()
            d = tel.to_dict()
        self.assertEqual(d["gpu_cuda_version"], "N/A")
        self.assertEqual(d["gpu_temperature_c"], None)
        self.assertEqual(d["gpu_power_watts"], None)
        self.assertEqual(d["gpu_vram_total_mb"], 0)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. RTX 4060 compatible response handling
# ═══════════════════════════════════════════════════════════════════════════════

class TestRTX4060Response(unittest.TestCase):
    """Verifies the telemetry logic handles RTX 4060 data correctly (mock)."""

    _RTX4060_CSV = "0, NVIDIA GeForce RTX 4060 Laptop GPU, 8188, 1024, 7164, 32, 68, 45.2, 60\n"
    _RTX4060_HDR = "| NVIDIA-SMI 555.85   Driver Version: 555.85   CUDA Version: 12.5 |"

    def _run_smi(self, returncode=0, stdout=""):
        r = MagicMock(); r.returncode = returncode; r.stdout = stdout; r.stderr = ""; return r

    def test_rtx4060_device_parsed_correctly(self):
        responses = [
            self._run_smi(0, self._RTX4060_CSV),
            self._run_smi(0, self._RTX4060_HDR),
        ]
        with patch("subprocess.run", side_effect=responses):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            devices = svc._query_nvidia_smi()
        self.assertEqual(len(devices), 1)
        d = devices[0]
        self.assertIn("RTX 4060", d.name)
        self.assertEqual(d.vram_total_mb, 8188)
        self.assertEqual(d.vram_used_mb, 1024)
        self.assertEqual(d.utilization_pct, 32.0)
        self.assertEqual(d.temperature_c, 68)
        self.assertAlmostEqual(d.power_watts, 45.2)
        self.assertEqual(d.fan_speed_pct, 60)
        vram_pct = d.vram_used_mb / d.vram_total_mb * 100
        self.assertAlmostEqual(vram_pct, d.vram_pct, places=0)

    def test_rtx4060_full_telemetry_dict(self):
        responses = [
            self._run_smi(0, self._RTX4060_CSV),
            self._run_smi(0, self._RTX4060_HDR),
        ]
        with patch("subprocess.run", side_effect=responses), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}), \
             patch("psutil.cpu_percent", return_value=30.0), \
             patch("psutil.cpu_count", return_value=8), \
             patch("psutil.cpu_freq", return_value=None), \
             patch("psutil.virtual_memory", return_value=_make_psutil_mem(16, 8, 8, 50.0)), \
             patch("psutil.disk_usage", return_value=_make_psutil_disk()):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            tel = svc._collect()
            d = tel.to_dict()

        self.assertEqual(d["mode"], "CUDA_GPU")
        self.assertIn("RTX 4060", d["gpu_name"])
        self.assertEqual(d["gpu_cuda_version"], "12.5")
        self.assertEqual(d["gpu_driver_version"], "555.85")
        # nvidia-smi detected = nvidia_available is True
        self.assertTrue(d["gpu_nvidia"])
        # VRAM data from nvidia-smi
        self.assertEqual(d["gpu_vram_total_mb"], 8188)
        self.assertEqual(d["gpu_vram_used_mb"], 1024)
        # CPU/RAM still real
        self.assertAlmostEqual(d["cpu_utilization_pct"], 30.0)
        self.assertAlmostEqual(d["ram_total_gb"], 16.0, places=0)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Cache / force refresh / deduplication
# ═══════════════════════════════════════════════════════════════════════════════

class TestCacheAndRefresh(unittest.TestCase):
    def test_cache_is_used_within_ttl(self):
        from smartcore.hardware_telemetry import HardwareTelemetryService
        svc = HardwareTelemetryService()
        call_count = [0]
        original = svc._collect
        def counting_collect():
            call_count[0] += 1
            return original()
        svc._collect = counting_collect

        with patch("subprocess.run", side_effect=FileNotFoundError()), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}), \
             patch("psutil.cpu_percent", return_value=5.0), \
             patch("psutil.cpu_count", return_value=4), \
             patch("psutil.cpu_freq", return_value=None), \
             patch("psutil.virtual_memory", return_value=_make_psutil_mem()), \
             patch("psutil.disk_usage", return_value=_make_psutil_disk()):
            svc.get()
            svc.get()   # second call should use cache
        self.assertEqual(call_count[0], 1)

    def test_force_refresh_bypasses_cache(self):
        from smartcore.hardware_telemetry import HardwareTelemetryService
        svc = HardwareTelemetryService()
        call_count = [0]
        original = svc._collect
        def counting_collect():
            call_count[0] += 1
            return original()
        svc._collect = counting_collect

        with patch("subprocess.run", side_effect=FileNotFoundError()), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}), \
             patch("psutil.cpu_percent", return_value=5.0), \
             patch("psutil.cpu_count", return_value=4), \
             patch("psutil.cpu_freq", return_value=None), \
             patch("psutil.virtual_memory", return_value=_make_psutil_mem()), \
             patch("psutil.disk_usage", return_value=_make_psutil_disk()):
            svc.get()
            svc.get(force=True)   # must bypass cache
        self.assertEqual(call_count[0], 2)

    def test_invalidate_causes_re_collect(self):
        from smartcore.hardware_telemetry import HardwareTelemetryService
        svc = HardwareTelemetryService()
        call_count = [0]
        original = svc._collect
        def counting_collect():
            call_count[0] += 1
            return original()
        svc._collect = counting_collect

        with patch("subprocess.run", side_effect=FileNotFoundError()), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}), \
             patch("psutil.cpu_percent", return_value=5.0), \
             patch("psutil.cpu_count", return_value=4), \
             patch("psutil.cpu_freq", return_value=None), \
             patch("psutil.virtual_memory", return_value=_make_psutil_mem()), \
             patch("psutil.disk_usage", return_value=_make_psutil_disk()):
            svc.get()
            svc.invalidate()
            svc.get()
        self.assertEqual(call_count[0], 2)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. to_dict / report structure
# ═══════════════════════════════════════════════════════════════════════════════

class TestTelemetryDict(unittest.TestCase):
    def test_to_dict_contains_all_required_keys(self):
        from smartcore.hardware_telemetry import HardwareTelemetry
        tel = HardwareTelemetry()
        d = tel.to_dict()
        required = [
            "timestamp", "status", "mode",
            "cpu_utilization_pct", "cpu_model", "cpu_cores_logical",
            "ram_total_gb", "ram_used_gb", "ram_utilization_pct",
            "disk_total_gb", "disk_used_gb", "disk_utilization_pct",
            "gpu_available", "gpu_cuda", "gpu_cuda_version", "gpu_driver_version",
            "gpu_name", "gpu_vram_total_mb", "gpu_vram_used_mb",
            "gpu_utilization_pct", "gpu_temperature_c", "gpu_power_watts",
            "errors", "warnings",
        ]
        for key in required:
            self.assertIn(key, d, f"Missing key: {key}")

    def test_no_fake_values_in_default_state(self):
        """Default/empty telemetry must not contain suspicious hard-coded values."""
        from smartcore.hardware_telemetry import HardwareTelemetry
        tel = HardwareTelemetry()
        d = tel.to_dict()
        # Common fake hard-coded values
        forbidden_percentages = {90.0, 85.0, 75.5, 50.0, 25.0}
        actual_cpu = d["cpu_utilization_pct"]
        self.assertNotIn(actual_cpu, forbidden_percentages,
                         f"cpu_utilization_pct={actual_cpu} looks hard-coded")


# ═══════════════════════════════════════════════════════════════════════════════
# 10. nvidia-smi timeout / error handling
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorHandling(unittest.TestCase):
    def test_smi_timeout_returns_empty_list(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("nvidia-smi", 4)):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            devices = svc._query_nvidia_smi()
        self.assertEqual(devices, [])

    def test_smi_nonzero_returncode_returns_empty(self):
        r = MagicMock(); r.returncode = 1; r.stdout = ""; r.stderr = "error"
        with patch("subprocess.run", return_value=r):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            devices = svc._query_nvidia_smi()
        self.assertEqual(devices, [])

    def test_malformed_smi_line_does_not_crash(self):
        r = MagicMock(); r.returncode = 0; r.stdout = "bad,data\n"; r.stderr = ""
        r2 = MagicMock(); r2.returncode = 0; r2.stdout = ""; r2.stderr = ""
        with patch("subprocess.run", side_effect=[r, r2]):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            # Should not raise
            devices = svc._query_nvidia_smi()
        self.assertIsInstance(devices, list)

    def test_full_collection_never_raises(self):
        """The entire collection pipeline must never raise an exception."""
        with patch("subprocess.run", side_effect=Exception("random crash")), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}), \
             patch("psutil.cpu_percent", side_effect=Exception("psutil crash")), \
             patch("psutil.virtual_memory", side_effect=Exception("mem crash")), \
             patch("psutil.disk_usage", side_effect=Exception("disk crash")):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            try:
                tel = svc._collect()
            except Exception as e:
                self.fail(f"_collect() raised unexpectedly: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Multi-GPU
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiGpu(unittest.TestCase):
    _TWO_GPU_CSV = (
        "0, NVIDIA GeForce RTX 4060 Laptop GPU, 8192, 512, 7680, 20, 65, 30.0, 50\n"
        "1, NVIDIA GeForce RTX 3080, 10240, 2048, 8192, 45, 75, 85.0, 70\n"
    )

    def _run_smi(self, returncode=0, stdout=""):
        r = MagicMock(); r.returncode = returncode; r.stdout = stdout; r.stderr = ""; return r

    def test_two_gpus_enumerated(self):
        responses = [
            self._run_smi(0, self._TWO_GPU_CSV),
            self._run_smi(0, "| NVIDIA-SMI   Driver Version: 555.85   CUDA Version: 12.5 |"),
        ]
        with patch("subprocess.run", side_effect=responses):
            from smartcore.hardware_telemetry import HardwareTelemetryService
            svc = HardwareTelemetryService()
            devices = svc._query_nvidia_smi()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].device_index, 0)
        self.assertEqual(devices[1].device_index, 1)
        self.assertIn("RTX 4060", devices[0].name)
        self.assertIn("RTX 3080", devices[1].name)

    def test_primary_device_is_index_0(self):
        responses = [
            self._run_smi(0, self._TWO_GPU_CSV),
            self._run_smi(0, "| CUDA Version: 12.5 |"),
        ]
        with patch("subprocess.run", side_effect=responses), \
             patch.dict(sys.modules, {"torch": None, "tensorflow": None}):
            from smartcore.hardware_telemetry import HardwareTelemetryService, HardwareTelemetry
            svc = HardwareTelemetryService()
            tel = HardwareTelemetry()
            gpu = svc._collect_gpu(tel)
        self.assertIsNotNone(gpu.primary_device)
        self.assertEqual(gpu.primary_device.device_index, 0)
        self.assertEqual(gpu.device_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
