"""
IntelliPrint Nexus — GPU Utils (Enterprise Edition)
==============================================
Backward-compatible wrapper that delegates to the smartcore.gpu_manager
singleton. All logic has been moved to smartcore/gpu_manager.py.

This file is preserved for import compatibility with any module that does:
    from smartai.gpu_utils import check_nvidia_gpu, get_system_resources
"""

from __future__ import annotations

# Delegate everything to the enterprise GPU manager singleton
from smartcore.gpu_manager import (
    check_nvidia_gpu,
    get_gpu_info,
    get_gpu_extended_stats,
    get_system_resources,
    gpu_manager,
)

__all__ = [
    "check_nvidia_gpu",
    "get_gpu_info",
    "get_gpu_extended_stats",
    "get_system_resources",
    "gpu_manager",
]
