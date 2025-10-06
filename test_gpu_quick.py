"""
快速测试GPU批处理 (无交互)
"""
import sys
import time

sys.path.insert(0, '.')

from visualization.parallel_executor import GPUParallelExecutor, calculate_optimal_workers
from visualization.rqa_pipeline_api import execute_full_pipeline_internal_gpu, generate_param_grid

if __name__ == '__main__':
    print("="*60)
    print("GPU Pipeline Quick Test")
    print("="*60)

    # 小规模测试配置: 2×2×2×1 = 8 组合
    batch_config = {
        "m_range": {"start": 2, "end": 3, "step": 1},  # 2 values: 2, 3
        "tau_range": {"start": 1, "end": 2, "step": 1},  # 2 values: 1, 2
        "eps_range": {"start": 0.05, "end": 0.06, "step": 0.01},  # 2 values
        "lmin_range": {"start": 2, "end": 2, "step": 1}  # 1 value
    }

    print("\nGenerating parameter grid...")
    param_combinations = generate_param_grid(
        batch_config['m_range'],
        batch_config['tau_range'],
        batch_config['eps_range'],
        batch_config['lmin_range']
    )

    print(f"Total combinations: {len(param_combinations)}")
    print(f"Expected time: ~{len(param_combinations) * 2}s (2s per combination)")

    # 计算最优worker数
    n_workers = calculate_optimal_workers()
    print(f"Workers: {n_workers}")

    print("\nStarting GPU parallel execution...")
    start_time = time.time()

    # 使用GPU并行执行器
    executor = GPUParallelExecutor(n_workers=n_workers, gpu_id=0)
    results = executor.execute_batch(param_combinations)

    elapsed = time.time() - start_time

    # 统计结果
    success = sum(1 for _, _, r in results if r.get('success') and not r.get('skipped'))
    skipped = sum(1 for _, _, r in results if r.get('skipped'))
    failed = sum(1 for _, _, r in results if not r.get('success'))

    print("\n" + "="*60)
    print("Test Results")
    print("="*60)
    print(f"Total:   {len(results)}")
    print(f"Success: {success}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")
    print(f"Time:    {elapsed:.2f}s ({elapsed/len(results):.2f}s per task)")
    print("="*60)

    if failed == 0:
        print("\n[OK] All tests passed!")
    else:
        print(f"\n[FAIL] {failed} tasks failed")
        for idx, params, result in results:
            if not result.get('success'):
                print(f"  Failed: {result.get('param_signature', params)}")
                print(f"    Error: {result.get('error', 'Unknown')}")
