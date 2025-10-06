"""
GPU多进程并行执行器

支持多个worker同时在GPU上执行RQA分析任务
关键特性:
1. 多进程并行 (ProcessPoolExecutor)
2. GPU显存管理
3. 进度回调
4. 错误处理与重试
"""

import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Callable, Any, Tuple
import time


class GPUParallelExecutor:
    """GPU多进程并行执行器"""

    def __init__(self, n_workers=4, gpu_id=0):
        """
        Args:
            n_workers: 并行worker数量 (建议4-6)
            gpu_id: 使用的GPU编号
        """
        self.n_workers = n_workers
        self.gpu_id = gpu_id

        print(f"[Parallel Executor] Initialized with {n_workers} workers on GPU {gpu_id}")

    def execute_batch(self, param_combinations: List[Dict],
                      callback: Callable = None) -> List[Tuple[int, Dict, Dict]]:
        """
        并行执行批量任务

        Args:
            param_combinations: 参数组合列表
            callback: 进度回调函数 callback(index, params, result)

        Returns:
            [(index, params, result), ...]
        """
        total_count = len(param_combinations)
        results = []

        print(f"[Parallel Executor] Starting batch execution: {total_count} tasks")

        with ProcessPoolExecutor(
            max_workers=self.n_workers,
            mp_context=mp.get_context('spawn')  # Windows必须用spawn
        ) as executor:
            # 提交所有任务
            future_to_params = {
                executor.submit(
                    self._worker_task,
                    params,
                    self.gpu_id
                ): (i, params)
                for i, params in enumerate(param_combinations)
            }

            # 收集结果
            completed_count = 0
            for future in as_completed(future_to_params):
                idx, params = future_to_params[future]
                completed_count += 1

                try:
                    result = future.result()
                    results.append((idx, params, result))

                    # 进度回调
                    if callback:
                        callback(idx, params, result)

                    # 打印进度
                    if completed_count % 10 == 0 or completed_count == total_count:
                        progress = (completed_count / total_count) * 100
                        print(f"[Progress] {completed_count}/{total_count} ({progress:.1f}%)")

                except Exception as e:
                    print(f"[Error] Task {idx} failed: {e}")
                    results.append((idx, params, {'success': False, 'error': str(e)}))

        # 按原顺序排序
        results.sort(key=lambda x: x[0])

        print(f"[Parallel Executor] Batch execution completed")
        return results

    @staticmethod
    def _worker_task(params: Dict, gpu_id: int) -> Dict:
        """
        Worker任务函数 (在子进程中执行)

        Args:
            params: RQA参数 {'m', 'tau', 'eps', 'lmin'}
            gpu_id: GPU设备ID

        Returns:
            执行结果字典
        """
        import cupy as cp
        import sys
        import os

        # 添加项目根目录到路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            # 设置GPU设备
            cp.cuda.Device(gpu_id).use()

            # 导入并执行完整pipeline
            from visualization.rqa_pipeline_api import execute_full_pipeline_internal_gpu

            result = execute_full_pipeline_internal_gpu(params)
            return result

        except Exception as e:
            return {
                'success': False,
                'error': f"Worker error: {str(e)}"
            }
        finally:
            # 清理GPU缓存
            try:
                cp.get_default_memory_pool().free_all_blocks()
            except:
                pass


def calculate_optimal_workers(gpu_mem_gb=16, single_task_mem_gb=2.5, max_workers=6) -> int:
    """
    计算最优worker数量

    Args:
        gpu_mem_gb: GPU显存容量 (GB)
        single_task_mem_gb: 单任务平均显存占用 (GB)
        max_workers: 最大worker数量

    Returns:
        最优worker数量
    """
    # 保留20%显存buffer
    usable_mem = gpu_mem_gb * 0.8

    # 理论最大worker数
    max_workers_mem = int(usable_mem / single_task_mem_gb)

    # CPU核心数限制
    cpu_cores = os.cpu_count() or 4

    # 取较小值
    optimal = min(max_workers_mem, cpu_cores // 2, max_workers)

    return max(optimal, 1)


# 简单测试
if __name__ == '__main__':
    print("="*60)
    print("GPU Parallel Executor Test")
    print("="*60)

    # 生成测试参数
    test_params = [
        {'m': m, 'tau': 1, 'eps': 0.06, 'lmin': 2}
        for m in range(2, 7)  # 5个任务
    ]

    print(f"\nTest parameters: {len(test_params)} tasks")
    print(f"Optimal workers: {calculate_optimal_workers()}")

    # 定义回调函数
    def progress_callback(idx, params, result):
        if result.get('success'):
            status = "SKIPPED" if result.get('skipped') else "SUCCESS"
        else:
            status = "FAILED"
        print(f"  Task {idx+1}: m={params['m']} -> {status}")

    # 执行并行任务
    executor = GPUParallelExecutor(n_workers=2)

    start = time.time()
    results = executor.execute_batch(test_params, callback=progress_callback)
    elapsed = time.time() - start

    # 统计结果
    success_count = sum(1 for _, _, r in results if r.get('success'))
    failed_count = len(results) - success_count

    print(f"\n{'='*60}")
    print(f"Total time: {elapsed:.1f}s")
    print(f"Success: {success_count}, Failed: {failed_count}")
    print(f"Average time per task: {elapsed/len(results):.1f}s")
    print("="*60)
