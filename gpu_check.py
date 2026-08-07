"""
GPU Check Utility
Demonstrates NVIDIA GPU utilization for IntelliPrint Nexus.
"""
import sys
from smartai.gpu_utils import check_nvidia_gpu

def main():
    # Reconfigure stdout to support emojis on Windows command prompt
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    print("=" * 50)
    print("NVIDIA GPU ACCELERATION CHECK")
    print("=" * 50)
    
    stats = check_nvidia_gpu()
    
    if stats["gpu_available"]:
        print("✅ NVIDIA GPU Detected")
        print(f"GPU Name: {stats['gpu_name']}")
        print(f"CUDA Version: {stats['cuda_version']}")
        print(f"Total VRAM: {stats['memory_total_mb']} MB")
        print(f"Used VRAM: {stats['memory_used_mb']} MB")
        print(f"Utilization: {stats['utilization_percent']}%")
    else:
        print("❌ No NVIDIA GPU detected via nvidia-smi / TensorFlow config.")
        
    print("-" * 50)
    print(f"TensorFlow GPU Support: {'✅ YES' if stats.get('tf_gpu_available', False) else '❌ NO'}")
    print("=" * 50)

if __name__ == "__main__":
    main()
