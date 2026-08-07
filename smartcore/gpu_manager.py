"""
IntelliPrint Nexus — GPU Manager (Enterprise Singleton)
==================================================
Centralised GPU state manager with automatic detection, caching,
memory configuration, and CPU fallback.

Features:
- Detects NVIDIA CUDA, TensorFlow GPU, and PyTorch GPU
- Caches detection results (TTL: 30 seconds by default)
- Configures TensorFlow memory growth to prevent OOM
- Returns inference device string: "cuda", "tf-gpu", or "cpu"
- Thread-safe singleton
- Never crashes — all exceptions caught and logged

Usage::

    from smartcore.gpu_manager import gpu_manager
    device = gpu_manager.get_inference_device()    # "cuda" / "tf-gpu" / "cpu"
    status = gpu_manager.get_gpu_status()          # full metrics dict
"""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Any, Dict, Optional

try:
    from smartcore.config import cfg as _cfg
    _ENABLE_GPU        = _cfg.GPU.ENABLE_GPU
    _STATS_TTL         = _cfg.GPU.STATS_CACHE_TTL_S
    _SMI_TIMEOUT       = _cfg.GPU.NVIDIA_SMI_TIMEOUT_S
    _TF_MEM_GROWTH     = _cfg.GPU.TF_MEMORY_GROWTH
    _TF_MEM_FRACTION   = _cfg.GPU.TF_PER_PROCESS_MEMORY_FRACTION
    _MIN_FREE_VRAM_MB  = _cfg.GPU.MIN_FREE_VRAM_MB
except ImportError:
    _ENABLE_GPU = True
    _STATS_TTL = 30
    _SMI_TIMEOUT = 5
    _TF_MEM_GROWTH = True
    _TF_MEM_FRACTION = 0.4
    _MIN_FREE_VRAM_MB = 512

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("ai")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.gpu")


class GPUManager:
    """
    Singleton GPU state manager.

    Do not instantiate directly — use the module-level ``gpu_manager`` instance.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0.0
        self._tf_configured: bool = False
        self._device: Optional[str] = None

    # ── Public API ─────────────────────────────────────────────────────────

    def get_inference_device(self) -> str:
        """
        Return the best available inference device.

        Returns
        -------
        str
            One of ``"tf-gpu"``, ``"cuda"``, or ``"cpu"``.
        """
        if not _ENABLE_GPU:
            return "cpu"
        status = self.get_gpu_status()
        if status.get("tf_gpu_available"):
            return "tf-gpu"
        if status.get("gpu_available"):
            return "cuda"
        return "cpu"

    def get_gpu_status(self) -> Dict[str, Any]:
        """
        Return cached GPU metrics.  Re-queries after TTL expires.

        Returns a dict with at minimum:
            gpu_available, gpu_name, cuda_version, memory_total_mb,
            memory_used_mb, memory_free_mb, utilization_percent,
            tf_gpu_available, temperature_c, power_draw_w
        """
        with self._lock:
            now = time.monotonic()
            if self._cache is not None and (now - self._cache_time) < _STATS_TTL:
                return self._cache

            fresh = self._detect_gpu()
            self._cache = fresh
            self._cache_time = now
            return fresh

    def configure_tensorflow(self) -> bool:
        """
        Configure TensorFlow GPU memory settings.
        Should be called once, early in application startup.

        Returns True if GPU was configured, False if CPU-only.
        """
        with self._lock:
            if self._tf_configured:
                return self._device == "tf-gpu"
            result = self._setup_tf_gpu()
            self._tf_configured = True
            return result

    def invalidate_cache(self) -> None:
        """Force the next ``get_gpu_status()`` call to re-detect hardware."""
        with self._lock:
            self._cache = None
            self._cache_time = 0.0

    # ── Internal detection ─────────────────────────────────────────────────

    def _detect_gpu(self) -> Dict[str, Any]:
        """Run full GPU detection (may be slow — always called from cached path)."""
        stats: Dict[str, Any] = {
            "gpu_available":      False,
            "gpu_name":           "N/A",
            "cuda_version":       "N/A",
            "memory_total_mb":    0,
            "memory_used_mb":     0,
            "memory_free_mb":     0,
            "utilization_percent": 0,
            "temperature_c":      "N/A",
            "power_draw_w":       "N/A",
            "fan_speed_pct":      "N/A",
            "tf_gpu_available":   False,
            "torch_gpu_available": False,
            "device":             "cpu",
        }

        # ── nvidia-smi query ───────────────────────────────────────────────
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.used,memory.free,"
                    "utilization.gpu,temperature.gpu,power.draw,fan.speed",
                    "--format=csv,noheader,nounits",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=_SMI_TIMEOUT,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines:
                    parts = [p.strip() for p in lines[0].split(",")]
                    stats["gpu_available"]      = True
                    stats["gpu_name"]           = parts[0] if len(parts) > 0 else "N/A"
                    stats["memory_total_mb"]    = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    stats["memory_used_mb"]     = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                    stats["memory_free_mb"]     = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                    stats["utilization_percent"] = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                    try:
                        stats["temperature_c"] = int(parts[5]) if len(parts) > 5 else "N/A"
                    except (ValueError, TypeError):
                        pass
                    try:
                        stats["power_draw_w"]  = float(parts[6]) if len(parts) > 6 else "N/A"
                    except (ValueError, TypeError):
                        pass
                    try:
                        stats["fan_speed_pct"] = int(parts[7]) if len(parts) > 7 else "N/A"
                    except (ValueError, TypeError):
                        pass

            # Extract CUDA version
            table = subprocess.run(
                ["nvidia-smi"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=_SMI_TIMEOUT,
            )
            if table.returncode == 0:
                import re
                m = re.search(r"CUDA Version:\s*([\d\.]+)", table.stdout)
                if m:
                    stats["cuda_version"] = m.group(1)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as exc:
            _log.debug("nvidia-smi query failed: %s", exc)

        # ── TensorFlow GPU ─────────────────────────────────────────────────
        try:
            import tensorflow as tf
            devices = tf.config.list_physical_devices("GPU")
            if devices:
                stats["tf_gpu_available"] = True
                stats["gpu_available"]    = True
                stats["device"]           = "tf-gpu"
                if stats["gpu_name"] == "N/A":
                    try:
                        details = tf.config.experimental.get_device_details(devices[0])
                        stats["gpu_name"] = details.get("device_name", "TF GPU")
                    except Exception:
                        stats["gpu_name"] = "TF GPU"
        except ImportError:
            pass
        except Exception as exc:
            _log.debug("TF GPU detection error: %s", exc)

        # ── PyTorch GPU ────────────────────────────────────────────────────
        try:
            import torch
            if torch.cuda.is_available():
                stats["torch_gpu_available"] = True
                stats["gpu_available"]       = True
                if stats["device"] == "cpu":
                    stats["device"] = "cuda"
                if stats["gpu_name"] == "N/A":
                    stats["gpu_name"] = torch.cuda.get_device_name(0)
        except ImportError:
            pass
        except Exception as exc:
            _log.debug("PyTorch GPU detection error: %s", exc)

        if stats["device"] == "cpu":
            stats["device"] = "tf-gpu" if stats["tf_gpu_available"] else (
                "cuda" if stats["gpu_available"] else "cpu"
            )

        return stats

    def _setup_tf_gpu(self) -> bool:
        """Configure TensorFlow GPU memory settings. Returns True on success."""
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices("GPU")
            if not gpus:
                self._device = "cpu"
                return False

            if _TF_MEM_GROWTH:
                for gpu in gpus:
                    try:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    except RuntimeError:
                        # Memory growth must be set before GPUs have been initialized
                        pass

            self._device = "tf-gpu"
            _log.info("TensorFlow GPU configured: %d device(s), memory_growth=%s", len(gpus), _TF_MEM_GROWTH)
            return True

        except ImportError:
            self._device = "cpu"
            return False
        except Exception as exc:
            _log.warning("TF GPU setup failed: %s — using CPU", exc)
            self._device = "cpu"
            return False


# ── Module-level singleton ──────────────────────────────────────────────────
gpu_manager = GPUManager()


# ── Backward-compatible helpers (used by existing code) ────────────────────

def check_nvidia_gpu() -> Dict[str, Any]:
    """Backward-compatible wrapper — returns cached GPU status dict."""
    return gpu_manager.get_gpu_status()


def get_gpu_info() -> Dict[str, Any]:
    """Alias for check_nvidia_gpu."""
    return gpu_manager.get_gpu_status()


def get_gpu_extended_stats() -> Dict[str, Any]:
    """Return extended GPU stats (temperature, power, fan)."""
    s = gpu_manager.get_gpu_status()
    return {
        "temperature_c": s.get("temperature_c", "N/A"),
        "power_draw_w":  s.get("power_draw_w",  "N/A"),
        "fan_speed_pct": s.get("fan_speed_pct", "N/A"),
    }


def get_system_resources() -> Dict[str, Any]:
    """
    Get real-time system resource usage using psutil.
    Returns dict with cpu_percent, ram_*, disk_* fields.
    All values are 'N/A' if psutil is unavailable.
    """
    result: Dict[str, Any] = {
        "cpu_percent":  "N/A",
        "cpu_count":    "N/A",
        "cpu_freq_mhz": "N/A",
        "ram_used_gb":  "N/A",
        "ram_total_gb": "N/A",
        "ram_percent":  "N/A",
        "disk_used_gb": "N/A",
        "disk_total_gb": "N/A",
        "disk_percent": "N/A",
    }
    try:
        import psutil
        result["cpu_percent"] = round(psutil.cpu_percent(interval=0.2), 1)
        result["cpu_count"]   = psutil.cpu_count(logical=True)
        try:
            freq = psutil.cpu_freq()
            result["cpu_freq_mhz"] = round(freq.current) if freq else "N/A"
        except Exception:
            pass
        mem = psutil.virtual_memory()
        result["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)
        result["ram_used_gb"]  = round(mem.used  / (1024 ** 3), 1)
        result["ram_percent"]  = mem.percent
        disk = psutil.disk_usage("/")
        result["disk_total_gb"] = round(disk.total / (1024 ** 3), 1)
        result["disk_used_gb"]  = round(disk.used  / (1024 ** 3), 1)
        result["disk_percent"]  = disk.percent
    except ImportError:
        pass
    except Exception as exc:
        _log.debug("psutil error: %s", exc)
    return result
