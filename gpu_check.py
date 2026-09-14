"""
GPU Check Utility — CLI Demonstration Script
Demonstrates NVIDIA GPU utilization for IntelliPrint Nexus.

Run:  python gpu_check.py
"""
import sys

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    print("=" * 60)
    print("   INTELLIPRINT NEXUS — GPU ACCELERATION CHECK")
    print("=" * 60)

    # Use the enterprise GPU manager singleton
    from smartcore.gpu_manager import gpu_manager, get_system_resources

    stats = gpu_manager.get_gpu_status()
    device = gpu_manager.get_inference_device()

    print()
    if stats["gpu_available"]:
        print("  ✅ NVIDIA GPU Detected")
        print(f"     GPU Name       : {stats['gpu_name']}")
        print(f"     CUDA Version   : {stats['cuda_version']}")
        print(f"     Total VRAM     : {stats['memory_total_mb']} MB")
        print(f"     Used VRAM      : {stats['memory_used_mb']} MB")
        print(f"     Free VRAM      : {stats['memory_free_mb']} MB")
        print(f"     Utilisation    : {stats['utilization_percent']}%")
        print(f"     Temperature    : {stats.get('temperature_c', 'N/A')}°C")
        print(f"     Power Draw     : {stats.get('power_draw_w', 'N/A')} W")
        print(f"     Fan Speed      : {stats.get('fan_speed_pct', 'N/A')}%")
    else:
        print("  ❌ No NVIDIA GPU detected — running in CPU fallback mode")

    print()
    print("-" * 60)
    print(f"  TensorFlow GPU    : {'✅ YES' if stats.get('tf_gpu_available') else '❌ NO'}")
    print(f"  PyTorch CUDA      : {'✅ YES' if stats.get('torch_gpu_available') else '❌ NO'}")
    print(f"  Inference Device  : {device.upper()}")

    # System resources
    print("-" * 60)
    sysres = get_system_resources()
    print(f"  CPU Usage         : {sysres.get('cpu_percent', 'N/A')}%")
    print(f"  CPU Cores         : {sysres.get('cpu_count', 'N/A')}")
    print(f"  RAM               : {sysres.get('ram_used_gb', 'N/A')} / {sysres.get('ram_total_gb', 'N/A')} GB")
    print(f"  Disk Usage        : {sysres.get('disk_percent', 'N/A')}%")

    # Quick benchmark
    print("-" * 60)
    print("  Running quick benchmark...")
    import time, numpy as np
    n = 500
    a = np.random.rand(224, 224).astype("float32")
    b = np.random.rand(224, 224).astype("float32")
    t0 = time.perf_counter()
    for _ in range(n):
        _ = np.dot(a, b)
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"  NumPy 224×224 matmul × {n}: {elapsed:.1f} ms ({elapsed/n:.2f} ms/iter)")
    print(f"  Throughput: {n / (elapsed / 1000):.0f} ops/sec")

    print("=" * 60)
    print("  GPU check complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
