"""
IntelliPrint Nexus — Centralized Hardware Telemetry Service
============================================================
Single source of truth for ALL hardware telemetry on the admin dashboard.

Design principles
-----------------
- NEVER fabricates values. All metrics come from actual system APIs.
- Returns "N/A" / None for any metric that cannot be obtained.
- Cross-platform: Windows (C:\\) and Linux (/) disk paths both work.
- Multi-GPU aware: enumerates all CUDA/NVIDIA devices, not just index 0.
- Never raises — every method is wrapped in try/except.
- Thread-safe singleton with configurable TTL cache.
- Force-refresh method bypasses cache immediately.

Detection hierarchy
-------------------
  HardwareTelemetryService
      |
      +-- CPU (psutil)
      |       cpu_percent, cpu_count_logical, cpu_count_physical,
      |       cpu_freq_mhz, cpu_model (platform / registry)
      |
      +-- Memory (psutil.virtual_memory)
      |       total_bytes, used_bytes, available_bytes, percent
      |
      +-- Disk (psutil.disk_usage — Windows AND Linux aware)
      |       total_bytes, used_bytes, free_bytes, percent
      |
      +-- NVIDIA GPU (nvidia-smi, PyTorch, TF)
              gpu_available, vendor, model, device_index
              cuda_available, cuda_version, driver_version
              utilization_percent, temperature_c, power_watts
              vram_total_mb, vram_used_mb, vram_free_mb, vram_percent
              fan_speed_pct

Usage
-----
    from smartcore.hardware_telemetry import hardware_telemetry
    tel = hardware_telemetry.get()          # returns cached HardwareTelemetry
    tel = hardware_telemetry.get(force=True) # bypass cache
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("hw_telemetry")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.hw_telemetry")

# ── Configuration ─────────────────────────────────────────────────────────────
_CACHE_TTL_S:    float = float(os.environ.get("SMARTPRINT_HW_TELEMETRY_TTL", "5"))
_SMI_TIMEOUT_S:  float = float(os.environ.get("SMARTPRINT_SMI_TIMEOUT", "4"))
_CPU_INTERVAL_S: float = 0.3   # psutil cpu_percent sampling window


# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses (normalized telemetry contract)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CpuInfo:
    utilization_pct:    float   = 0.0
    count_logical:      int     = 0
    count_physical:     int     = 0
    freq_mhz:           float   = 0.0
    model:              str     = "N/A"
    available:          bool    = False


@dataclass
class MemInfo:
    total_bytes:        int     = 0
    used_bytes:         int     = 0
    available_bytes:    int     = 0
    utilization_pct:    float   = 0.0
    total_gb:           float   = 0.0
    used_gb:            float   = 0.0
    available_gb:       float   = 0.0
    available:          bool    = False


@dataclass
class DiskInfo:
    total_bytes:        int     = 0
    used_bytes:         int     = 0
    free_bytes:         int     = 0
    utilization_pct:    float   = 0.0
    total_gb:           float   = 0.0
    used_gb:            float   = 0.0
    free_gb:            float   = 0.0
    mount_path:         str     = "N/A"
    available:          bool    = False


@dataclass
class GpuDeviceInfo:
    """One GPU device's telemetry."""
    device_index:       int     = 0
    name:               str     = "N/A"
    vendor:             str     = "N/A"          # "NVIDIA" | "AMD" | "Intel" | "N/A"
    cuda_device_index:  Optional[int] = None     # None if not a CUDA device
    vram_total_mb:      int     = 0
    vram_used_mb:       int     = 0
    vram_free_mb:       int     = 0
    vram_pct:           float   = 0.0
    utilization_pct:    float   = 0.0
    temperature_c:      Any     = None           # int or None
    power_watts:        Any     = None           # float or None
    fan_speed_pct:      Any     = None           # int or None


@dataclass
class GpuInfo:
    available:          bool    = False
    nvidia_available:   bool    = False
    cuda_available:     bool    = False
    tf_gpu_available:   bool    = False
    torch_gpu_available: bool   = False
    cuda_version:       str     = "N/A"
    driver_version:     str     = "N/A"
    device_count:       int     = 0
    primary_device:     Optional[GpuDeviceInfo] = None    # first/best device
    all_devices:        List[GpuDeviceInfo] = field(default_factory=list)
    mode:               str     = "CPU"          # "CUDA_GPU" | "TF_GPU" | "CPU"
    fallback_reason:    str     = ""


@dataclass
class HardwareTelemetry:
    """Complete normalized hardware telemetry snapshot."""
    timestamp:          str     = ""
    status:             str     = "unavailable"  # "live" | "cpu_fallback" | "unavailable"
    mode:               str     = "CPU"          # "CUDA_GPU" | "TF_GPU" | "CPU"
    cpu:                CpuInfo = field(default_factory=CpuInfo)
    memory:             MemInfo = field(default_factory=MemInfo)
    disk:               DiskInfo = field(default_factory=DiskInfo)
    gpu:                GpuInfo = field(default_factory=GpuInfo)
    errors:             List[str] = field(default_factory=list)
    warnings:           List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a flat dict for easy dashboard rendering."""
        g = self.gpu
        pd = g.primary_device
        return {
            "timestamp":            self.timestamp,
            "status":               self.status,
            "mode":                 self.mode,
            # CPU
            "cpu_utilization_pct":  self.cpu.utilization_pct,
            "cpu_model":            self.cpu.model,
            "cpu_cores_logical":    self.cpu.count_logical,
            "cpu_cores_physical":   self.cpu.count_physical,
            "cpu_freq_mhz":         self.cpu.freq_mhz,
            # Memory
            "ram_total_gb":         self.memory.total_gb,
            "ram_used_gb":          self.memory.used_gb,
            "ram_available_gb":     self.memory.available_gb,
            "ram_utilization_pct":  self.memory.utilization_pct,
            # Disk
            "disk_total_gb":        self.disk.total_gb,
            "disk_used_gb":         self.disk.used_gb,
            "disk_free_gb":         self.disk.free_gb,
            "disk_utilization_pct": self.disk.utilization_pct,
            "disk_mount":           self.disk.mount_path,
            # GPU
            "gpu_available":        g.available,
            "gpu_nvidia":           g.nvidia_available,
            "gpu_cuda":             g.cuda_available,
            "gpu_tf":               g.tf_gpu_available,
            "gpu_torch":            g.torch_gpu_available,
            "gpu_cuda_version":     g.cuda_version,
            "gpu_driver_version":   g.driver_version,
            "gpu_mode":             g.mode,
            "gpu_fallback_reason":  g.fallback_reason,
            "gpu_device_count":     g.device_count,
            # Primary GPU device
            "gpu_name":             pd.name if pd else "N/A",
            "gpu_vendor":           pd.vendor if pd else "N/A",
            "gpu_device_index":     pd.device_index if pd else 0,
            "gpu_cuda_index":       pd.cuda_device_index if pd else None,
            "gpu_vram_total_mb":    pd.vram_total_mb if pd else 0,
            "gpu_vram_used_mb":     pd.vram_used_mb if pd else 0,
            "gpu_vram_free_mb":     pd.vram_free_mb if pd else 0,
            "gpu_vram_pct":         pd.vram_pct if pd else 0.0,
            "gpu_utilization_pct":  pd.utilization_pct if pd else 0.0,
            "gpu_temperature_c":    pd.temperature_c if pd else None,
            "gpu_power_watts":      pd.power_watts if pd else None,
            "gpu_fan_pct":          pd.fan_speed_pct if pd else None,
            # Errors
            "errors":               self.errors,
            "warnings":             self.warnings,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Hardware Telemetry Service
# ═══════════════════════════════════════════════════════════════════════════════

class HardwareTelemetryService:
    """
    Singleton service for collecting hardware telemetry.
    Thread-safe, never raises, always returns a valid HardwareTelemetry object.
    """

    def __init__(self) -> None:
        self._lock       = threading.Lock()
        self._cache:     Optional[HardwareTelemetry] = None
        self._cache_ts:  float = 0.0

    # ── Public API ─────────────────────────────────────────────────────────

    def get(self, force: bool = False) -> HardwareTelemetry:
        """
        Return hardware telemetry. Uses cached result within TTL.
        Pass force=True to bypass cache and re-query immediately.
        """
        with self._lock:
            now = time.monotonic()
            if not force and self._cache is not None and (now - self._cache_ts) < _CACHE_TTL_S:
                return self._cache
            fresh = self._collect()
            self._cache    = fresh
            self._cache_ts = now
            return fresh

    def force_refresh(self) -> HardwareTelemetry:
        """Force immediate re-collection, bypassing TTL cache."""
        return self.get(force=True)

    def invalidate(self) -> None:
        """Invalidate cache so next get() re-collects."""
        with self._lock:
            self._cache    = None
            self._cache_ts = 0.0

    # ── Internal collection ────────────────────────────────────────────────

    def _collect(self) -> HardwareTelemetry:
        """Collect all telemetry. Never raises."""
        tel = HardwareTelemetry(timestamp=datetime.now().strftime("%H:%M:%S"))
        _log.debug("HARDWARE_REFRESH_STARTED")

        tel.cpu    = self._collect_cpu(tel)
        tel.memory = self._collect_memory(tel)
        tel.disk   = self._collect_disk(tel)
        tel.gpu    = self._collect_gpu(tel)

        # Determine overall mode/status
        if tel.gpu.cuda_available:
            tel.mode   = "CUDA_GPU"
            tel.status = "live"
        elif tel.gpu.tf_gpu_available:
            tel.mode   = "TF_GPU"
            tel.status = "live"
        elif tel.cpu.available:
            tel.mode   = "CPU"
            tel.status = "cpu_fallback"
        else:
            tel.status = "unavailable"

        _log.debug("HARDWARE_REFRESH_COMPLETED — mode=%s status=%s", tel.mode, tel.status)
        return tel

    # ── CPU ────────────────────────────────────────────────────────────────

    def _collect_cpu(self, tel: HardwareTelemetry) -> CpuInfo:
        info = CpuInfo()
        try:
            import psutil
            info.utilization_pct = round(psutil.cpu_percent(interval=_CPU_INTERVAL_S), 1)
            info.count_logical   = psutil.cpu_count(logical=True) or 0
            info.count_physical  = psutil.cpu_count(logical=False) or 0
            try:
                freq = psutil.cpu_freq()
                info.freq_mhz = round(freq.current, 1) if freq else 0.0
            except Exception:
                pass
            info.model     = self._cpu_model_name()
            info.available = True
            _log.debug("CPU: %.1f%% (%d logical cores)", info.utilization_pct, info.count_logical)
        except ImportError:
            tel.errors.append("psutil not installed — CPU telemetry unavailable")
        except Exception as exc:
            tel.errors.append(f"CPU telemetry error: {exc}")
            _log.warning("CPU telemetry error: %s", exc)
        return info

    def _cpu_model_name(self) -> str:
        """Get CPU model name — cross-platform."""
        try:
            if platform.system() == "Windows":
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
                )
                name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
                winreg.CloseKey(key)
                return name
        except Exception:
            pass
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":")[1].strip()
        except Exception:
            pass
        try:
            return platform.processor() or "N/A"
        except Exception:
            return "N/A"

    # ── Memory ─────────────────────────────────────────────────────────────

    def _collect_memory(self, tel: HardwareTelemetry) -> MemInfo:
        info = MemInfo()
        try:
            import psutil
            mem = psutil.virtual_memory()
            info.total_bytes      = mem.total
            info.used_bytes       = mem.used
            info.available_bytes  = mem.available
            info.utilization_pct  = round(mem.percent, 1)
            info.total_gb         = round(mem.total     / (1024 ** 3), 2)
            info.used_gb          = round(mem.used      / (1024 ** 3), 2)
            info.available_gb     = round(mem.available / (1024 ** 3), 2)
            info.available        = True
        except ImportError:
            tel.errors.append("psutil not installed — RAM telemetry unavailable")
        except Exception as exc:
            tel.errors.append(f"RAM telemetry error: {exc}")
            _log.warning("RAM telemetry error: %s", exc)
        return info

    # ── Disk ───────────────────────────────────────────────────────────────

    def _collect_disk(self, tel: HardwareTelemetry) -> DiskInfo:
        info = DiskInfo()
        # Try multiple mount paths — Windows first, then Linux
        candidates = []
        if platform.system() == "Windows":
            # Prefer the drive where the app lives
            app_drive = os.path.splitdrive(os.path.abspath(__file__))[0] + "\\"
            candidates = [app_drive, "C:\\", "/"]
        else:
            candidates = ["/", "/home"]
        try:
            import psutil
            for path in candidates:
                try:
                    disk = psutil.disk_usage(path)
                    info.total_bytes    = disk.total
                    info.used_bytes     = disk.used
                    info.free_bytes     = disk.free
                    info.utilization_pct = round(disk.percent, 1)
                    info.total_gb       = round(disk.total / (1024 ** 3), 1)
                    info.used_gb        = round(disk.used  / (1024 ** 3), 1)
                    info.free_gb        = round(disk.free  / (1024 ** 3), 1)
                    info.mount_path     = path
                    info.available      = True
                    break
                except Exception:
                    continue
        except ImportError:
            tel.errors.append("psutil not installed — Disk telemetry unavailable")
        except Exception as exc:
            tel.errors.append(f"Disk telemetry error: {exc}")
        return info

    # ── GPU ────────────────────────────────────────────────────────────────

    def _collect_gpu(self, tel: HardwareTelemetry) -> GpuInfo:
        info = GpuInfo()

        # ── Step 1: nvidia-smi multi-GPU enumeration ───────────────────────
        smi_devices = self._query_nvidia_smi()
        if smi_devices:
            info.nvidia_available = True
            info.available        = True
            info.all_devices      = smi_devices
            info.primary_device   = smi_devices[0]
            info.device_count     = len(smi_devices)
            _log.info("CUDA_AVAILABLE — %d NVIDIA GPU(s) via nvidia-smi", len(smi_devices))

        # ── Step 2: CUDA version + driver from nvidia-smi header ───────────
        cuda_v, driver_v = self._query_smi_header()
        if cuda_v:
            info.cuda_version     = cuda_v
            info.driver_version   = driver_v
            info.cuda_available   = True
            if info.available:
                info.mode         = "CUDA_GPU"

        # ── Step 3: PyTorch CUDA ───────────────────────────────────────────
        info = self._enrich_pytorch(info, tel)

        # ── Step 4: TensorFlow GPU ─────────────────────────────────────────
        info = self._enrich_tensorflow(info, tel)

        # ── Step 5: determine mode and fallback reason ─────────────────────
        if info.cuda_available or info.torch_gpu_available:
            info.mode           = "CUDA_GPU"
            info.available      = True
        elif info.tf_gpu_available:
            info.mode           = "TF_GPU"
            info.available      = True
        else:
            info.mode           = "CPU"
            reason_parts        = []
            if not info.nvidia_available:
                reason_parts.append("No NVIDIA GPU detected")
            if not info.cuda_available:
                reason_parts.append("CUDA unavailable")
            info.fallback_reason = " — ".join(reason_parts) if reason_parts else "CPU fallback active"
            if not info.available:
                _log.info("CPU_FALLBACK_ACTIVE — %s", info.fallback_reason)

        return info

    def _query_nvidia_smi(self) -> List[GpuDeviceInfo]:
        """Query nvidia-smi for all GPU devices. Returns [] if unavailable."""
        devices: List[GpuDeviceInfo] = []
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.total,memory.used,memory.free,"
                    "utilization.gpu,temperature.gpu,power.draw,fan.speed",
                    "--format=csv,noheader,nounits",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=_SMI_TIMEOUT_S,
            )
            if result.returncode != 0:
                return []

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 2:
                    continue
                dev = GpuDeviceInfo()
                dev.device_index = int(parts[0]) if parts[0].isdigit() else 0
                dev.name         = parts[1] if len(parts) > 1 else "NVIDIA GPU"
                dev.vendor       = "NVIDIA"

                def _safe_int(s: str) -> Optional[int]:
                    try: return int(float(s))
                    except Exception: return None

                def _safe_float(s: str) -> Optional[float]:
                    try: return round(float(s), 1)
                    except Exception: return None

                if len(parts) > 2: dev.vram_total_mb   = _safe_int(parts[2]) or 0
                if len(parts) > 3: dev.vram_used_mb    = _safe_int(parts[3]) or 0
                if len(parts) > 4: dev.vram_free_mb    = _safe_int(parts[4]) or 0
                if len(parts) > 5: dev.utilization_pct = float(_safe_int(parts[5]) or 0)
                if len(parts) > 6: dev.temperature_c   = _safe_int(parts[6])
                if len(parts) > 7: dev.power_watts     = _safe_float(parts[7])
                if len(parts) > 8: dev.fan_speed_pct   = _safe_int(parts[8])

                if dev.vram_total_mb > 0:
                    dev.vram_pct = round(dev.vram_used_mb / dev.vram_total_mb * 100, 1)

                devices.append(dev)
                _log.info("GPU_TELEMETRY_UPDATED — index=%d name=%s util=%s%%",
                          dev.device_index, dev.name, dev.utilization_pct)

        except FileNotFoundError:
            _log.debug("nvidia-smi not found — NVIDIA telemetry unavailable")
        except subprocess.TimeoutExpired:
            _log.warning("nvidia-smi timed out after %.1fs", _SMI_TIMEOUT_S)
        except Exception as exc:
            _log.debug("nvidia-smi error: %s", exc)
        return devices

    def _query_smi_header(self):
        """Extract CUDA Version and Driver Version from nvidia-smi header table."""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=_SMI_TIMEOUT_S,
            )
            if result.returncode == 0:
                cuda_m   = re.search(r"CUDA Version:\s*([\d\.]+)", result.stdout)
                driver_m = re.search(r"Driver Version:\s*([\d\.]+)", result.stdout)
                cuda_v   = cuda_m.group(1)   if cuda_m   else None
                driver_v = driver_m.group(1) if driver_m else None
                return cuda_v, driver_v
        except Exception:
            pass
        return None, None

    def _enrich_pytorch(self, info: GpuInfo, tel: HardwareTelemetry) -> GpuInfo:
        """Add PyTorch CUDA information."""
        try:
            import torch
            if torch.cuda.is_available():
                info.torch_gpu_available = True
                info.cuda_available      = True
                info.available           = True
                device_count             = torch.cuda.device_count()
                if info.cuda_version == "N/A" and torch.version.cuda:
                    info.cuda_version    = torch.version.cuda

                # Map CUDA device indices to GpuDeviceInfo
                for cuda_idx in range(device_count):
                    name = torch.cuda.get_device_name(cuda_idx)
                    # Try to match with existing nvidia-smi device
                    matched = next(
                        (d for d in info.all_devices if d.name == name), None
                    )
                    if matched:
                        matched.cuda_device_index = cuda_idx
                    else:
                        # nvidia-smi wasn't available — create from PyTorch data
                        props = torch.cuda.get_device_properties(cuda_idx)
                        dev = GpuDeviceInfo(
                            device_index      = cuda_idx,
                            cuda_device_index = cuda_idx,
                            name              = name,
                            vendor            = "NVIDIA",
                            vram_total_mb     = props.total_memory // (1024 ** 2),
                        )
                        try:
                            dev.vram_used_mb  = torch.cuda.memory_allocated(cuda_idx) // (1024 ** 2)
                            dev.vram_free_mb  = dev.vram_total_mb - dev.vram_used_mb
                            if dev.vram_total_mb > 0:
                                dev.vram_pct  = round(dev.vram_used_mb / dev.vram_total_mb * 100, 1)
                        except Exception:
                            pass
                        info.all_devices.append(dev)
                        if info.primary_device is None:
                            info.primary_device = dev

                info.device_count = max(device_count, len(info.all_devices))
                _log.info("CUDA_AVAILABLE — PyTorch: %d device(s)", device_count)
            else:
                _log.debug("PyTorch installed but CUDA unavailable")
        except ImportError:
            _log.debug("PyTorch not installed")
        except Exception as exc:
            tel.warnings.append(f"PyTorch GPU detection: {exc}")
        return info

    def _enrich_tensorflow(self, info: GpuInfo, tel: HardwareTelemetry) -> GpuInfo:
        """Add TensorFlow GPU information."""
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                info.tf_gpu_available = True
                info.available        = True
                for i, gpu in enumerate(gpus):
                    try:
                        details = tf.config.experimental.get_device_details(gpu)
                        name    = details.get("device_name", f"TF GPU {i}")
                    except Exception:
                        name    = f"TF GPU {i}"
                    # Only add if not already captured by nvidia-smi
                    already = any(d.name == name for d in info.all_devices)
                    if not already:
                        dev = GpuDeviceInfo(device_index=i, name=name, vendor="NVIDIA")
                        info.all_devices.append(dev)
                        if info.primary_device is None:
                            info.primary_device = dev
                info.device_count = max(len(gpus), len(info.all_devices))
                _log.info("TF GPU available: %d device(s)", len(gpus))
        except ImportError:
            pass
        except Exception as exc:
            tel.warnings.append(f"TensorFlow GPU detection: {exc}")
        return info


# ── Module-level singleton ─────────────────────────────────────────────────────
hardware_telemetry = HardwareTelemetryService()
