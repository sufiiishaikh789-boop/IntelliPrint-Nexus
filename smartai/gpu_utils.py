"""
SmartPrint AI - NVIDIA GPU Utils
Detects and monitors GPU hardware acceleration (CUDA/cuDNN).
"""
import os
import subprocess
import re

def check_nvidia_gpu() -> dict:
    """Check if an NVIDIA GPU is available and return its stats."""
    gpu_stats = {
        "gpu_available": False,
        "gpu_name": "N/A",
        "cuda_version": "N/A",
        "memory_total_mb": 0,
        "memory_used_mb": 0,
        "utilization_percent": 0,
        "tf_gpu_available": False
    }
    
    try:
        # Check via nvidia-smi (structured query)
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[0].split(',')
                gpu_stats["gpu_available"] = True
                gpu_stats["gpu_name"] = parts[0].strip()
                gpu_stats["memory_total_mb"] = int(parts[1].strip())
                gpu_stats["memory_used_mb"] = int(parts[2].strip())
                gpu_stats["utilization_percent"] = int(parts[3].strip())
                
        # Query nvidia-smi standard table to extract CUDA Version
        table_result = subprocess.run(
            ['nvidia-smi'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if table_result.returncode == 0:
            cuda_match = re.search(r'CUDA Version:\s*([\d\.]+)', table_result.stdout)
            if cuda_match:
                gpu_stats["cuda_version"] = cuda_match.group(1)
                
    except (FileNotFoundError, Exception):
        pass
        
    # Check TensorFlow GPU support
    try:
        import tensorflow as tf
        physical_devices = tf.config.list_physical_devices('GPU')
        gpu_stats["tf_gpu_available"] = len(physical_devices) > 0
        if len(physical_devices) > 0:
            gpu_stats["gpu_available"] = True
            # Try to get the name of the GPU device from TF if nvidia-smi failed
            if gpu_stats["gpu_name"] == "N/A":
                try:
                    # e.g., 'PhysicalDevice(name="/physical_device:GPU:0", device_type="GPU")'
                    details = tf.config.experimental.get_device_details(physical_devices[0])
                    gpu_stats["gpu_name"] = details.get("device_name", "NVIDIA GPU")
                except Exception:
                    gpu_stats["gpu_name"] = "NVIDIA CUDA GPU"
    except ImportError:
        gpu_stats["tf_gpu_available"] = False
        
    return gpu_stats

# Alias for backward compatibility
get_gpu_info = check_nvidia_gpu
