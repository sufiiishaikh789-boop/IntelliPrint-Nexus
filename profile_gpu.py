"""
IntelliPrint Nexus — GPU Profiling Script
==========================================
Runs a controlled profiling session on the active device.

On CUDA machines:
    - Uses torch.profiler to capture CPU + CUDA activity
    - Exports Chrome trace JSON for TensorBoard / chrome://tracing
    - Shows top GPU kernels by CUDA time

On CPU-only machines:
    - Uses cProfile for operator-level profiling
    - Still useful for identifying Python overhead

Usage
-----
    python profile_gpu.py
    python profile_gpu.py --iters 20 --output logs/my_trace.json

Output
------
    logs/gpu_profile_<timestamp>.json  (Chrome trace — open in chrome://tracing)
    logs/gpu_profile_<timestamp>_summary.txt
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import platform
import cProfile
import pstats
import io as _io
import logging

import numpy as np

log = logging.getLogger("smartprint.profiler")
logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")

LOGS_DIR = "logs"


def _ensure_dirs() -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs("models", exist_ok=True)


def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


# ── PyTorch profiler ──────────────────────────────────────────────────────────

def run_torch_profiler(iters: int = 10, output_path: str = "") -> str:
    """
    Run torch.profiler if PyTorch is available.
    Profiles CPU + CUDA operators.
    Returns path to the Chrome trace JSON.
    """
    try:
        import torch
        import torch.nn as nn
        from torch.profiler import profile, record_function, ProfilerActivity

        ts = _timestamp()
        trace_path = output_path or os.path.join(LOGS_DIR, f"gpu_profile_{ts}.json")
        summary_path = trace_path.replace(".json", "_summary.txt")

        is_cuda = torch.cuda.is_available()
        device  = "cuda" if is_cuda else "cpu"
        activities = [ProfilerActivity.CPU]
        if is_cuda:
            activities.append(ProfilerActivity.CUDA)

        log.info("Profiling on device: %s | CUDA: %s | Iterations: %d", device, is_cuda, iters)

        model = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((7, 7)),
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 5),
        ).to(device).eval()

        dummy = torch.randn(1, 3, 224, 224, device=device)

        with profile(
            activities=activities,
            record_shapes=True,
            profile_memory=True,
            with_stack=False,
        ) as prof:
            with torch.inference_mode():
                for i in range(iters):
                    with record_function(f"inference_iter_{i}"):
                        _ = model(dummy)
            if is_cuda:
                torch.cuda.synchronize()

        # Export Chrome trace
        prof.export_chrome_trace(trace_path)

        # Write text summary
        key_sort = "cuda_time_total" if is_cuda else "cpu_time_total"
        summary = prof.key_averages().table(sort_by=key_sort, row_limit=20)
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"PyTorch Profiler Summary\n")
            f.write(f"Device: {device} | CUDA: {is_cuda} | Iters: {iters}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(summary)

        log.info("Chrome trace → %s", trace_path)
        log.info("Summary      → %s", summary_path)
        print("\n" + summary)
        return trace_path

    except ImportError:
        log.warning("PyTorch not installed — falling back to cProfile")
        return run_cprofile(iters, output_path)
    except Exception as exc:
        log.error("Torch profiler error: %s", exc)
        return run_cprofile(iters, output_path)


# ── cProfile CPU fallback ────────────────────────────────────────────────────

def run_cprofile(iters: int = 10, output_path: str = "") -> str:
    """
    CPU profiling with cProfile — always available.
    Useful for identifying Python overhead in inference path.
    """
    ts = _timestamp()
    summary_path = output_path.replace(".json", "_cprofile.txt") if output_path \
        else os.path.join(LOGS_DIR, f"gpu_profile_{ts}_cprofile.txt")

    log.info("Running cProfile (CPU) for %d iterations...", iters)

    size = 224
    a = np.random.rand(size, size).astype(np.float32)
    b = np.random.rand(size, size).astype(np.float32)

    def workload():
        for _ in range(iters):
            _ = np.dot(a, b)

    pr = cProfile.Profile()
    pr.enable()
    workload()
    pr.disable()

    stream = _io.StringIO()
    ps = pstats.Stats(pr, stream=stream).sort_stats("cumulative")
    ps.print_stats(20)
    summary = stream.getvalue()

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"cProfile Summary (CPU fallback)\n")
        f.write(f"Workload: NumPy matmul {size}x{size} x {iters}\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(summary)

    log.info("cProfile summary → %s", summary_path)
    print("\n" + summary)
    return summary_path


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="IntelliPrint Nexus — GPU Profiler")
    parser.add_argument("--iters",  type=int,  default=10, help="Profiling iterations")
    parser.add_argument("--output", type=str,  default="", help="Output trace path")
    args = parser.parse_args()

    _ensure_dirs()

    print("=" * 60)
    print("  INTELLIPRINT NEXUS — GPU PROFILING SESSION")
    print("=" * 60)
    print(f"  Python:    {platform.python_version()}")
    print(f"  OS:        {platform.system()} {platform.release()}")
    print(f"  Iters:     {args.iters}")

    try:
        import torch
        print(f"  PyTorch:   {torch.__version__}")
        print(f"  CUDA:      {'Yes — ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No'}")
    except ImportError:
        print("  PyTorch:   Not installed (using cProfile)")
    print("-" * 60)

    output = run_torch_profiler(iters=args.iters, output_path=args.output)
    print(f"\n  ✅ Profile complete → {output}")
    print("  Open Chrome trace in: chrome://tracing (if .json)")
    print("=" * 60)


if __name__ == "__main__":
    main()
