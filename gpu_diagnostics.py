"""
IntelliPrint Nexus — GPU Diagnostics CLI
=========================================
Comprehensive environment and GPU health diagnostic tool.

Shows:
  - Python, OS, CPU, RAM
  - CUDA version, GPU name, VRAM
  - TensorFlow GPU, PyTorch CUDA, OpenCV CUDA
  - DeviceManager health check
  - nvidia-smi output (if available)
  - Recent GPU telemetry summary
  - AI service health

Usage
-----
    python gpu_diagnostics.py
    python gpu_diagnostics.py --json          # machine-readable JSON output
    python gpu_diagnostics.py --report-only   # no nvidia-smi call
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np


def _header(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def collect_environment() -> dict:
    """Collect real environment data — no fabrication."""
    env: dict = {
        "python_version":   platform.python_version(),
        "python_impl":      platform.python_implementation(),
        "os":               platform.system(),
        "os_version":       platform.version(),
        "os_release":       platform.release(),
        "machine":          platform.machine(),
        "processor":        platform.processor(),
        "collected_at":     time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # CPU / RAM
    try:
        import psutil
        env["cpu_logical_cores"]  = psutil.cpu_count(logical=True)
        env["cpu_physical_cores"] = psutil.cpu_count(logical=False)
        env["cpu_freq_mhz"]       = round(psutil.cpu_freq().current, 1) if psutil.cpu_freq() else "N/A"
        mem = psutil.virtual_memory()
        env["ram_total_gb"]    = round(mem.total / (1024 ** 3), 1)
        env["ram_available_gb"]= round(mem.available / (1024 ** 3), 1)
        env["ram_percent"]     = mem.percent
    except ImportError:
        env["psutil"] = "not installed"

    return env


def check_numpy() -> dict:
    try:
        return {"version": np.__version__, "status": "installed"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def check_tensorflow() -> dict:
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        return {
            "version":        tf.__version__,
            "gpu_count":      len(gpus),
            "gpu_devices":    [g.name for g in gpus],
            "gpu_available":  len(gpus) > 0,
            "status":         "installed",
        }
    except ImportError:
        return {"status": "not_installed"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def check_pytorch() -> dict:
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        result: dict = {
            "version":         torch.__version__,
            "cuda_available":  cuda_ok,
            "cuda_version":    getattr(torch.version, "cuda", None),
            "device_count":    torch.cuda.device_count() if cuda_ok else 0,
            "status":          "installed",
        }
        if cuda_ok:
            result["device_name"]   = torch.cuda.get_device_name(0)
            result["device_cap"]    = ".".join(str(x) for x in torch.cuda.get_device_capability(0))
            result["cudnn_version"] = torch.backends.cudnn.version()
            props = torch.cuda.get_device_properties(0)
            result["vram_total_mb"] = props.total_memory // (1024 * 1024)
            result["vram_free_mb"]  = (props.total_memory - torch.cuda.memory_allocated()) // (1024 * 1024)
            result["bf16_supported"]= torch.cuda.is_bf16_supported()
        return result
    except ImportError:
        return {"status": "not_installed"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def check_opencv() -> dict:
    try:
        import cv2
        build = cv2.getBuildInformation()
        cuda_lines = [ln.strip() for ln in build.split("\n") if "CUDA" in ln]
        cuda_enabled = any("Enabled" in ln or "YES" in ln for ln in cuda_lines)
        return {
            "version":       cv2.__version__,
            "cuda_enabled":  cuda_enabled,
            "cuda_summary":  cuda_lines[:4],
            "status":        "installed",
        }
    except ImportError:
        return {"status": "not_installed"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def check_onnxruntime() -> dict:
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        return {
            "version":    ort.__version__,
            "providers":  providers,
            "cuda":       "CUDAExecutionProvider" in providers,
            "status":     "installed",
        }
    except ImportError:
        return {"status": "not_installed"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def run_nvidia_smi() -> dict:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,utilization.gpu,temperature.gpu,power.draw",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=8,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            gpus = []
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "name":           parts[0],
                        "memory_total":   parts[1] + " MiB",
                        "memory_free":    parts[2] + " MiB",
                        "utilization":    parts[3] + " %",
                        "temperature":    parts[4] + " °C",
                        "power_draw":     parts[5] + " W",
                    })
            return {"available": True, "gpus": gpus, "raw": result.stdout.strip()}
        return {"available": False, "error": result.stderr.strip()}
    except FileNotFoundError:
        return {"available": False, "error": "nvidia-smi not found (no NVIDIA driver)"}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def check_device_manager() -> dict:
    try:
        from smartcore.device_manager import device_manager
        health = device_manager.health_check()
        return {"available": True, "health": health}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def check_ai_service() -> dict:
    try:
        from smartai.document_quality import check_ai_health
        return {"available": True, "health": check_ai_health()}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def check_recent_telemetry() -> dict:
    try:
        from smartdb.crud_gpu import get_recent_telemetry, get_aggregate_stats
        rows  = get_recent_telemetry(5)
        stats = get_aggregate_stats()
        return {"available": True, "recent_jobs": rows, "aggregate": stats}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def run_quick_benchmark() -> dict:
    """Quick 100-iter NumPy benchmark — always runs."""
    n = 100
    size = 224
    a = np.random.rand(size, size).astype(np.float32)
    b = np.random.rand(size, size).astype(np.float32)

    # Warmup
    for _ in range(5):
        _ = np.dot(a, b)

    import time as _t
    latencies = []
    for _ in range(n):
        t0 = _t.perf_counter()
        _ = np.dot(a, b)
        latencies.append((_t.perf_counter() - t0) * 1000)

    arr = np.array(latencies)
    return {
        "device":     "cpu",
        "framework":  "NumPy",
        "workload":   f"matmul_{size}x{size}",
        "iters":      n,
        "mean_ms":    round(float(np.mean(arr)), 3),
        "p50_ms":     round(float(np.percentile(arr, 50)), 3),
        "p95_ms":     round(float(np.percentile(arr, 95)), 3),
        "p99_ms":     round(float(np.percentile(arr, 99)), 3),
        "throughput_rps": round(1000.0 / float(np.mean(arr)), 1),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="IntelliPrint Nexus GPU Diagnostics")
    parser.add_argument("--json",        action="store_true", help="Output JSON only")
    parser.add_argument("--report-only", action="store_true", help="Skip nvidia-smi subprocess")
    args = parser.parse_args()

    # Collect everything
    report = {
        "environment":     collect_environment(),
        "numpy":           check_numpy(),
        "tensorflow":      check_tensorflow(),
        "pytorch":         check_pytorch(),
        "opencv":          check_opencv(),
        "onnxruntime":     check_onnxruntime(),
        "nvidia_smi":      {} if args.report_only else run_nvidia_smi(),
        "device_manager":  check_device_manager(),
        "ai_service":      check_ai_service(),
        "telemetry":       check_recent_telemetry(),
        "quick_benchmark": run_quick_benchmark(),
    }

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return

    # Human-readable output
    print("=" * 60)
    print("  INTELLIPRINT NEXUS — GPU DIAGNOSTICS")
    print("=" * 60)

    env = report["environment"]
    _header("SYSTEM")
    print(f"  Python:     {env['python_version']} ({env['python_impl']})")
    print(f"  OS:         {env['os']} {env.get('os_release','')}")
    print(f"  CPU:        {env['processor']}")
    print(f"  CPU Cores:  {env.get('cpu_logical_cores','N/A')} logical / {env.get('cpu_physical_cores','N/A')} physical")
    print(f"  RAM:        {env.get('ram_total_gb','N/A')} GB total, {env.get('ram_available_gb','N/A')} GB free")

    _header("GPU / CUDA")
    smi = report["nvidia_smi"]
    if not args.report_only:
        if smi.get("available"):
            for g in smi["gpus"]:
                print(f"  GPU:        {g['name']}")
                print(f"  VRAM:       {g['memory_total']} total / {g['memory_free']} free")
                print(f"  Util:       {g['utilization']}")
                print(f"  Temp:       {g['temperature']}")
                print(f"  Power:      {g['power_draw']}")
        else:
            print(f"  nvidia-smi: ❌ {smi.get('error','N/A')}")
    else:
        print("  nvidia-smi: (skipped — --report-only)")

    _header("AI FRAMEWORKS")
    tf  = report["tensorflow"]
    pt  = report["pytorch"]
    cv  = report["opencv"]
    ort = report["onnxruntime"]
    print(f"  TensorFlow: {'✅ v' + tf['version'] if tf['status']=='installed' else '❌ ' + tf['status']}")
    if tf["status"] == "installed":
        print(f"             GPU count: {tf.get('gpu_count', 0)}")
    print(f"  PyTorch:    {'✅ v' + pt['version'] if pt['status']=='installed' else '❌ ' + pt['status']}")
    if pt["status"] == "installed":
        print(f"             CUDA: {'✅ ' + pt.get('device_name','') if pt.get('cuda_available') else '❌ Not available'}")
        if pt.get("cuda_available"):
            print(f"             VRAM: {pt.get('vram_total_mb','N/A')} MB total")
    print(f"  OpenCV:     {'✅ v' + cv['version'] if cv['status']=='installed' else '❌ ' + cv['status']}")
    if cv["status"] == "installed":
        print(f"             CUDA build: {'✅' if cv.get('cuda_enabled') else '❌ CPU-only'}")
    print(f"  ONNX RT:    {'✅ v' + ort['version'] if ort['status']=='installed' else '❌ ' + ort['status']}")
    if ort.get("status") == "installed":
        print(f"             CUDA EP: {'✅' if ort.get('cuda') else '❌'}")

    _header("DEVICE MANAGER")
    dm = report["device_manager"]
    if dm["available"]:
        h = dm["health"]
        print(f"  Status:     {h.get('status','N/A')}")
        print(f"  Device:     {h.get('device_str','N/A')}")
        print(f"  GPU:        {h.get('gpu_name','N/A')}")
        print(f"  Fallback:   {h.get('is_fallback','N/A')}")
        gov = h.get("governor", {})
        print(f"  Active jobs:{gov.get('active_jobs',0)} / {gov.get('max_concurrent',0)} max")
    else:
        print(f"  ❌ {dm.get('error','N/A')}")

    _header("AI SERVICE")
    ai = report["ai_service"]
    if ai["available"]:
        h = ai["health"]
        print(f"  Model loaded:  {h.get('model_loaded', False)}")
        print(f"  Model type:    {h.get('model_type','N/A')}")
        print(f"  Infer device:  {h.get('inference_device','N/A')}")
        print(f"  TF available:  {h.get('tf_available', False)}")
    else:
        print(f"  ❌ {ai.get('error','N/A')}")

    _header("QUICK BENCHMARK (CPU NumPy)")
    bm = report["quick_benchmark"]
    print(f"  Device:     {bm['device']} | {bm['framework']}")
    print(f"  Workload:   {bm['workload']} x {bm['iters']} iters")
    print(f"  Mean:       {bm['mean_ms']} ms")
    print(f"  P50:        {bm['p50_ms']} ms")
    print(f"  P95:        {bm['p95_ms']} ms")
    print(f"  P99:        {bm['p99_ms']} ms")
    print(f"  Throughput: {bm['throughput_rps']} ops/sec")

    _header("GPU TELEMETRY (Last 5 Jobs)")
    tel = report["telemetry"]
    if tel.get("available") and tel.get("recent_jobs"):
        agg = tel.get("aggregate", {})
        print(f"  Total jobs:  {agg.get('total_jobs', 0)}")
        print(f"  Successful:  {agg.get('success_jobs', 0)}")
        print(f"  Failed:      {agg.get('failed_jobs', 0)}")
        print(f"  Avg latency: {agg.get('avg_latency_ms', 0):.2f} ms")
        print(f"  P95 latency: {agg.get('p95_latency_ms', 0):.2f} ms")
        for job in tel["recent_jobs"][:3]:
            print(f"    [{job['id']}] {job['device']} | {job['precision']} | "
                  f"{job['latency_ms']:.1f}ms | {job['status']}")
    else:
        print("  No telemetry records yet (DB empty or unavailable)")

    print("\n" + "=" * 60)
    print("  Diagnostic complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
