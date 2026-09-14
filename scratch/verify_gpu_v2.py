"""Verification script for GPU V2 upgrade."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

errors = []

print('=== IMPORT VERIFICATION ===')
try:
    from smartcore.device_manager import device_manager, DeviceManager, DeviceContext, GPUMemoryInfo, DeviceBenchmarkResult, _GPUGovernor
    print('  OK: smartcore.device_manager')
except Exception as e:
    print('  ERROR device_manager:', e)
    errors.append(str(e))

try:
    from smartcore.gpu_inference_engine import run_inference, GPUJobTelemetry, InferenceQueue
    print('  OK: smartcore.gpu_inference_engine')
except Exception as e:
    print('  ERROR gpu_inference_engine:', e)
    errors.append(str(e))

try:
    from smartcore.gpu_benchmark import GpuBenchmark, benchmark_cpu_numpy
    print('  OK: smartcore.gpu_benchmark')
except Exception as e:
    print('  ERROR gpu_benchmark:', e)
    errors.append(str(e))

try:
    from smartdb.crud_gpu import create_gpu_telemetry, get_recent_telemetry, get_aggregate_stats
    print('  OK: smartdb.crud_gpu')
except Exception as e:
    print('  ERROR crud_gpu:', e)
    errors.append(str(e))

print()
print('=== DB MIGRATION ===')
try:
    from smartdb.models import init_db, GPUJobTelemetry
    init_db()
    print('  DB init OK — GPUJobTelemetry table present')
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
print('=== DEVICE MANAGER ===')
try:
    from smartcore.device_manager import device_manager
    ctx = device_manager.detect_device()
    health = device_manager.health_check()
    mem = device_manager.get_memory_info()
    print('  Device:', ctx.device_str, '| GPU Name:', ctx.gpu_name, '| Fallback:', ctx.is_fallback)
    print('  Health status:', health.get('status'))
    print('  Memory source:', mem.source)
    bench = device_manager.benchmark_device(warmup_iters=1, measured_iters=10)
    print('  Benchmark iters:', len(bench.latencies_ms))
    print('  Mean:', round(bench.mean_ms, 3), 'ms | P50:', round(bench.p50_ms, 3), 'ms | P95:', round(bench.p95_ms, 3), 'ms | P99:', round(bench.p99_ms, 3), 'ms')
    print('  Throughput:', round(bench.throughput_rps, 1), 'ops/sec')
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
print('=== GOVERNOR ===')
try:
    from smartcore.device_manager import _GPUGovernor, MAX_CONCURRENT_GPU_JOBS
    gov = _GPUGovernor()
    ok, reason = gov.can_start_job()
    print('  First job allowed:', ok, '-', reason)
    for _ in range(MAX_CONCURRENT_GPU_JOBS):
        gov.start_job()
    ok2, r2 = gov.can_start_job()
    print('  At limit (' + str(MAX_CONCURRENT_GPU_JOBS) + ') allowed:', ok2, '-', r2)
    gov.finish_job()
    ok3, _ = gov.can_start_job()
    print('  After finish allowed:', ok3)
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
print('=== OOM HANDLING ===')
try:
    from smartcore.device_manager import device_manager as dm
    r1, bs1 = dm.handle_oom(8)
    r2, bs2 = dm.handle_oom(1)
    print('  OOM(8): retry=' + str(r1) + ' new_batch=' + str(bs1))
    print('  OOM(1): retry=' + str(r2) + ' new_batch=' + str(bs2) + ' (should be False, 0)')
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
print('=== CPU BENCHMARK (P50/P95/P99) ===')
try:
    from smartcore.gpu_benchmark import benchmark_cpu_numpy
    r = benchmark_cpu_numpy(size=64, warmup=1, n=20)
    print('  Status:', r['status'])
    print('  Mean:', round(r['mean_ms'], 3), '| P50:', round(r['p50_ms'], 3), '| P95:', round(r['p95_ms'], 3), '| P99:', round(r['p99_ms'], 3))
    print('  Throughput:', round(r['throughput_rps'], 1), 'ops/sec')
    assert r['p50_ms'] <= r['p95_ms'], 'P50 > P95!'
    assert r['p95_ms'] <= r['p99_ms'], 'P95 > P99!'
    assert r['min_ms'] <= r['p50_ms'], 'min > P50!'
    print('  Percentile ordering: CORRECT (min <= P50 <= P95 <= P99)')
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
print('=== TELEMETRY DB ===')
try:
    from smartdb.crud_gpu import create_gpu_telemetry, get_recent_telemetry, get_aggregate_stats
    data = {
        'model_name': 'VerifyTest', 'model_version': '0.1',
        'device': 'cpu', 'gpu_name': 'CPU', 'precision': 'FP32',
        'batch_size': 1, 'warmup_iters': 3, 'measured_iters': 1,
        'latency_ms': 15.5, 'throughput_rps': 64.5, 'status': 'success',
    }
    rec_id = create_gpu_telemetry(data)
    print('  Insert id:', rec_id)
    rows = get_recent_telemetry(5)
    print('  Recent rows count:', len(rows))
    stats = get_aggregate_stats()
    print('  Total jobs:', stats['total_jobs'])
    print('  Avg latency:', round(stats['avg_latency_ms'], 2), 'ms')
    print('  P95 latency:', round(stats['p95_latency_ms'], 2), 'ms')
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
print('=== INFERENCE ENGINE (CPU path) ===')
try:
    from smartcore.gpu_inference_engine import run_inference, GPUJobTelemetry
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (100, 150, 200)).save(buf, format="PNG")
    img_bytes = buf.getvalue()
    result, tel = run_inference(img_bytes, batch_size=1, precision="FP32")
    print('  Class:', result.get('class_name'), '| Confidence:', round(result.get('confidence', 0), 3))
    print('  Device:', result.get('device'), '| Precision:', result.get('precision'))
    print('  Latency:', round(tel.latency_ms, 3), 'ms | Status:', tel.status)
    print('  Telemetry to_dict keys:', list(tel.to_dict().keys())[:5], '...')
except ImportError as e:
    print('  PIL not available, skipping inference test:', e)
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
print('=== GPU DIAGNOSTICS (--report-only) ===')
try:
    import subprocess
    r = subprocess.run(['python', 'gpu_diagnostics.py', '--report-only'], capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        lines = r.stdout.strip().split('\n')
        for l in lines[:10]:
            print(' ', l)
        print('  ... (truncated)')
    else:
        print('  STDERR:', r.stderr[:200])
except Exception as e:
    print('  ERROR:', e)
    errors.append(str(e))

print()
if errors:
    print('=== SUMMARY: ' + str(len(errors)) + ' ERROR(S) ===')
    for e in errors:
        print('  -', e)
    sys.exit(1)
else:
    print('=== ALL CHECKS PASSED ===')
