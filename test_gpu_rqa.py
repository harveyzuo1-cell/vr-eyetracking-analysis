"""
GPU RQA分析器性能测试脚本
"""
import numpy as np
import time
from analysis.rqa_analyzer_gpu import RQAAnalyzerGPU

print("=" * 60)
print("GPU RQA Analysis Test")
print("=" * 60)

# 生成测试数据
np.random.seed(42)
traj_x = np.cumsum(np.random.randn(5000)) * 0.1
traj_y = np.cumsum(np.random.randn(5000)) * 0.1

params = {'m': 5, 'tau': 3, 'eps': 0.08, 'lmin': 2}

print(f"\nTest Parameters:")
print(f"  Data points: {len(traj_x)}")
print(f"  m={params['m']}, tau={params['tau']}, eps={params['eps']}, lmin={params['lmin']}")

# GPU测试
print("\n[GPU Test]")
analyzer = RQAAnalyzerGPU()

start_total = time.time()
results = analyzer.analyze_trajectory_gpu(traj_x, traj_y, params)
total_time = time.time() - start_total

if results['success']:
    print(f"SUCCESS - Total time: {total_time:.3f}s")
    print(f"\n1D X Metrics:")
    print(f"  RR_x  = {results['1d_x']['RR_x']:.4f}")
    print(f"  DET_x = {results['1d_x']['DET_x']:.4f}")
    print(f"  L_max_x = {results['1d_x']['L_max_x']}")
    print(f"  ENT_x = {results['1d_x']['ENT_x']:.4f}")
    print(f"  Time: {results['1d_x']['time']:.3f}s")

    print(f"\n1D Y Metrics:")
    print(f"  RR_y  = {results['1d_y']['RR_y']:.4f}")
    print(f"  DET_y = {results['1d_y']['DET_y']:.4f}")
    print(f"  L_max_y = {results['1d_y']['L_max_y']}")
    print(f"  ENT_y = {results['1d_y']['ENT_y']:.4f}")
    print(f"  Time: {results['1d_y']['time']:.3f}s")

    print(f"\n2D XY Metrics:")
    print(f"  RR_2d  = {results['2d_xy']['RR_2d']:.4f}")
    print(f"  DET_2d = {results['2d_xy']['DET_2d']:.4f}")
    print(f"  L_max_2d = {results['2d_xy']['L_max_2d']}")
    print(f"  ENT_2d = {results['2d_xy']['ENT_2d']:.4f}")
    print(f"  Time: {results['2d_xy']['time']:.3f}s")

    print(f"\nGPU Memory:")
    mem = results['gpu_memory']
    print(f"  Used: {mem['used_gb']:.2f} GB / {mem['total_gb']:.1f} GB ({mem['usage_percent']:.1f}%)")

else:
    print(f"FAILED - {results.get('error', 'Unknown error')}")

print("\n" + "=" * 60)
