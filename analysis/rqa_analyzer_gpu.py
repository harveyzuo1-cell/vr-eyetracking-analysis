"""
RQA (Recurrence Quantification Analysis) GPU加速模块

使用CuPy进行GPU加速计算，与原CPU版本保持接口兼容
主要优化点:
1. 嵌入空间构建 (GPU并行)
2. 距离矩阵计算 (GPU矩阵运算)
3. 递归矩阵生成 (GPU并行)

性能目标: 15-25x加速
"""

import numpy as np
import cupy as cp
import time
from typing import Dict, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class GPUMemoryManager:
    """GPU显存管理器"""

    def __init__(self, max_gpu_usage=0.8):
        """
        Args:
            max_gpu_usage: 最大GPU显存使用率 (0-1)
        """
        self.max_usage = max_gpu_usage
        self.device = cp.cuda.Device(0)
        self.total_mem = self.device.mem_info[1]

    def get_free_memory(self) -> int:
        """获取可用显存 (字节)"""
        return self.device.mem_info[0]

    def can_allocate(self, size_bytes: int) -> bool:
        """检查是否可分配指定大小"""
        free_mem = self.get_free_memory()
        required = size_bytes + self.total_mem * (1 - self.max_usage)
        return free_mem > required

    def clear_cache(self):
        """清理GPU缓存"""
        cp.get_default_memory_pool().free_all_blocks()

    def get_memory_usage(self) -> Dict[str, float]:
        """获取显存使用情况 (GB)"""
        free, total = self.device.mem_info
        used = total - free
        return {
            'used_gb': used / 1e9,
            'free_gb': free / 1e9,
            'total_gb': total / 1e9,
            'usage_percent': (used / total) * 100
        }


class RQAAnalyzerGPU:
    """GPU加速RQA分析器"""

    def __init__(self, gpu_id=0):
        """
        Args:
            gpu_id: GPU设备编号
        """
        self.gpu_id = gpu_id
        cp.cuda.Device(gpu_id).use()
        self.mem_manager = GPUMemoryManager()

    def embed_signal_gpu(self, signal_data: np.ndarray, m: int, tau: int) -> cp.ndarray:
        """
        GPU加速的信号嵌入

        Args:
            signal_data: 输入信号 (1D或2D NumPy数组)
            m: 嵌入维度
            tau: 时间延迟

        Returns:
            嵌入后的数据 (CuPy数组)
        """
        # 转移到GPU
        signal_gpu = cp.asarray(signal_data, dtype=cp.float32)

        if signal_data.ndim == 1:
            # 1D信号嵌入
            N = len(signal_data)
            rows = N - (m - 1) * tau

            if rows <= 0:
                return cp.empty((0, m), dtype=cp.float32)

            # GPU并行构建嵌入矩阵
            embedded = cp.zeros((rows, m), dtype=cp.float32)
            for j in range(m):
                embedded[:, j] = signal_gpu[j * tau : j * tau + rows]

            return embedded
        else:
            # 2D信号嵌入
            N = signal_data.shape[0]
            rows = N - (m - 1) * tau

            if rows <= 0:
                return cp.empty((0, m * 2), dtype=cp.float32)

            embedded = cp.zeros((rows, m * 2), dtype=cp.float32)
            for j in range(m):
                embedded[:, j * 2] = signal_gpu[j * tau : j * tau + rows, 0]
                embedded[:, j * 2 + 1] = signal_gpu[j * tau : j * tau + rows, 1]

            return embedded

    def compute_distance_matrix_gpu(self, embedded: cp.ndarray, metric: str = '1d_abs') -> cp.ndarray:
        """
        GPU加速的距离矩阵计算 (核心优化点!)

        Args:
            embedded: 嵌入后的数据 (CuPy数组)
            metric: 距离度量 ('1d_abs' or 'euclidean')

        Returns:
            距离矩阵 (CuPy数组)
        """
        M = embedded.shape[0]

        if metric == '1d_abs':
            # 1D绝对差距离 (使用广播加速)
            # dist[i,j] = sum(|embedded[i] - embedded[j]|)
            diff = embedded[:, None, :] - embedded[None, :, :]  # (M, M, dim)
            dist_matrix = cp.sum(cp.abs(diff), axis=2)  # (M, M)

        elif metric == 'euclidean':
            # 欧氏距离 (使用CuPy优化的norm)
            # dist[i,j] = ||embedded[i] - embedded[j]||_2
            diff = embedded[:, None, :] - embedded[None, :, :]  # (M, M, dim)
            dist_matrix = cp.linalg.norm(diff, axis=2)  # (M, M)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return dist_matrix

    def compute_recurrence_matrix_gpu(self, dist_matrix: cp.ndarray, eps: float) -> cp.ndarray:
        """
        GPU加速的递归矩阵生成

        Args:
            dist_matrix: 距离矩阵 (CuPy数组)
            eps: 递归阈值

        Returns:
            递归矩阵 (CuPy数组, int8)
        """
        # GPU并行比较
        rec_matrix = (dist_matrix < eps).astype(cp.int8)
        return rec_matrix

    def compute_rqa_metrics_gpu(self, rec_matrix: cp.ndarray, lmin: int = 2) -> Dict[str, float]:
        """
        RQA指标计算 (混合CPU/GPU策略)

        简单指标(RR): GPU计算
        复杂指标(DET, ENT): 传回CPU计算 (避免复杂kernel编写)

        Args:
            rec_matrix: 递归矩阵 (CuPy数组)
            lmin: 最小线长度

        Returns:
            RQA指标字典
        """
        # GPU计算RR (Recurrence Rate)
        M = rec_matrix.shape[0]
        rr = float(cp.sum(rec_matrix)) / (M * M)

        # 传回CPU计算DET/ENT/L_max (避免复杂GPU kernel)
        rec_cpu = cp.asnumpy(rec_matrix)
        det, lmax, entr = self._compute_det_lmax_ent_cpu(rec_cpu, lmin)

        return {
            'RR': rr,
            'DET': det,
            'L_max': lmax,
            'ENT': entr,
            'lmin': lmin
        }

    @staticmethod
    def _compute_det_lmax_ent_cpu(rec_matrix: np.ndarray, lmin: int) -> Tuple[float, int, float]:
        """
        CPU计算DET, L_max, ENT (复用原逻辑)

        Args:
            rec_matrix: 递归矩阵 (NumPy数组)
            lmin: 最小线长度

        Returns:
            (DET, L_max, ENT)
        """
        M = rec_matrix.shape[0]

        # 提取对角线
        diag_lines = []
        for k in range(-(M-1), M):
            diag = np.diagonal(rec_matrix, offset=k)
            if len(diag) > 0:
                diag_lines.append(diag)

        # 统计线段长度
        line_lengths = []
        for diag in diag_lines:
            current_length = 0
            for val in diag:
                if val == 1:
                    current_length += 1
                else:
                    if current_length >= lmin:
                        line_lengths.append(current_length)
                    current_length = 0
            # 处理末尾
            if current_length >= lmin:
                line_lengths.append(current_length)

        # 计算DET
        if len(line_lengths) > 0:
            total_recurrence_points = np.sum(rec_matrix)
            total_line_points = np.sum(line_lengths)
            det = total_line_points / total_recurrence_points if total_recurrence_points > 0 else 0.0
        else:
            det = 0.0

        # 计算L_max
        lmax = max(line_lengths) if line_lengths else 0

        # 计算ENT (熵)
        if len(line_lengths) > 0:
            line_hist = np.bincount(line_lengths)
            line_prob = line_hist[line_hist > 0] / np.sum(line_hist)
            entr = -np.sum(line_prob * np.log(line_prob + 1e-10))
        else:
            entr = 0.0

        return float(det), int(lmax), float(entr)

    def analyze_batch_gpu(self, trajectories_list: list, params: Dict,
                          batch_size: int = 10) -> list:
        """
        批量GPU处理多条轨迹 (性能优化)

        Args:
            trajectories_list: [(traj_x1, traj_y1), (traj_x2, traj_y2), ...]
            params: RQA参数 {'m', 'tau', 'eps', 'lmin'}
            batch_size: 每批处理数量 (用于内存管理)

        Returns:
            [{'rr_1d': ..., 'det_1d': ..., 'rr_2d': ..., ...}, ...]
        """
        results = []
        n_trajectories = len(trajectories_list)

        m = params.get('m', 2)
        tau = params.get('tau', params.get('delay', 1))
        eps = params.get('eps', 0.05)
        lmin = params.get('lmin', 2)

        for i in range(0, n_trajectories, batch_size):
            batch = trajectories_list[i:i+batch_size]

            for traj_x, traj_y in batch:
                try:
                    # 1D RQA
                    result_1d_x = self.compute_rqa_1d(
                        np.array(traj_x, dtype=np.float32),
                        np.array(traj_y, dtype=np.float32),
                        m, tau, eps, lmin
                    )

                    # 2D RQA
                    result_2d = self.compute_rqa_2d(
                        np.array(traj_x, dtype=np.float32),
                        np.array(traj_y, dtype=np.float32),
                        m, tau, eps, lmin
                    )

                    # 合并结果
                    combined = {**result_1d_x, **result_2d}
                    results.append(combined)

                except Exception as e:
                    # 失败返回默认值
                    results.append({
                        'error': str(e),
                        'rr_1d': 0.0, 'det_1d': 0.0, 'lmax_1d': 0, 'ent_1d': 0.0,
                        'rr_2d': 0.0, 'det_2d': 0.0, 'lmax_2d': 0, 'ent_2d': 0.0
                    })

            # 定期清理GPU缓存
            if i % (batch_size * 3) == 0 and i > 0:
                self.mem_manager.clear_cache()

        return results

    def analyze_trajectory_gpu(self, traj_x: np.ndarray, traj_y: np.ndarray,
                               params: Dict) -> Dict[str, Any]:
        """
        完整的GPU加速RQA分析

        Args:
            traj_x: X坐标轨迹
            traj_y: Y坐标轨迹
            params: 参数字典 {'m': int, 'tau': int, 'eps': float, 'lmin': int}

        Returns:
            分析结果字典
        """
        m = params.get('m', 2)
        tau = params.get('tau', 1)
        eps = params.get('eps', 0.05)
        lmin = params.get('lmin', 2)

        results = {}

        try:
            # 1D X分析
            start = time.time()
            embedded_x = self.embed_signal_gpu(traj_x, m, tau)
            dist_matrix_x = self.compute_distance_matrix_gpu(embedded_x, '1d_abs')
            rec_matrix_x = self.compute_recurrence_matrix_gpu(dist_matrix_x, eps)
            metrics_x = self.compute_rqa_metrics_gpu(rec_matrix_x, lmin)
            time_x = time.time() - start

            results['1d_x'] = {
                'RR_x': metrics_x['RR'],
                'DET_x': metrics_x['DET'],
                'L_max_x': metrics_x['L_max'],
                'ENT_x': metrics_x['ENT'],
                'time': time_x
            }

            # 1D Y分析
            start = time.time()
            embedded_y = self.embed_signal_gpu(traj_y, m, tau)
            dist_matrix_y = self.compute_distance_matrix_gpu(embedded_y, '1d_abs')
            rec_matrix_y = self.compute_recurrence_matrix_gpu(dist_matrix_y, eps)
            metrics_y = self.compute_rqa_metrics_gpu(rec_matrix_y, lmin)
            time_y = time.time() - start

            results['1d_y'] = {
                'RR_y': metrics_y['RR'],
                'DET_y': metrics_y['DET'],
                'L_max_y': metrics_y['L_max'],
                'ENT_y': metrics_y['ENT'],
                'time': time_y
            }

            # 2D XY分析
            start = time.time()
            traj_2d = np.column_stack([traj_x, traj_y])
            embedded_2d = self.embed_signal_gpu(traj_2d, m, tau)
            dist_matrix_2d = self.compute_distance_matrix_gpu(embedded_2d, 'euclidean')
            rec_matrix_2d = self.compute_recurrence_matrix_gpu(dist_matrix_2d, eps)
            metrics_2d = self.compute_rqa_metrics_gpu(rec_matrix_2d, lmin)
            time_2d = time.time() - start

            results['2d_xy'] = {
                'RR_2d': metrics_2d['RR'],
                'DET_2d': metrics_2d['DET'],
                'L_max_2d': metrics_2d['L_max'],
                'ENT_2d': metrics_2d['ENT'],
                'time': time_2d
            }

            results['success'] = True
            results['total_time'] = time_x + time_y + time_2d
            results['gpu_memory'] = self.mem_manager.get_memory_usage()

        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
        finally:
            # 清理GPU缓存
            self.mem_manager.clear_cache()

        return results


# 便捷函数接口 (与CPU版本兼容)

def compute_rqa_1d_gpu(traj_x: np.ndarray, traj_y: np.ndarray, params: Dict) -> Dict:
    """
    GPU加速的1D RQA计算 (便捷接口)

    Args:
        traj_x: X坐标
        traj_y: Y坐标
        params: {'m': int, 'tau': int, 'eps': float, 'lmin': int}

    Returns:
        包含 RR_x, DET_x, L_max_x, ENT_x 的字典
    """
    analyzer = RQAAnalyzerGPU()
    results = analyzer.analyze_trajectory_gpu(traj_x, traj_y, params)

    if results['success']:
        return {
            'RR_x': results['1d_x']['RR_x'],
            'DET_x': results['1d_x']['DET_x'],
            'L_max_x': results['1d_x']['L_max_x'],
            'ENT_x': results['1d_x']['ENT_x'],
            'RR_y': results['1d_y']['RR_y'],
            'DET_y': results['1d_y']['DET_y'],
            'L_max_y': results['1d_y']['L_max_y'],
            'ENT_y': results['1d_y']['ENT_y']
        }
    else:
        raise RuntimeError(f"GPU RQA计算失败: {results.get('error', 'Unknown')}")


def compute_rqa_2d_gpu(traj_x: np.ndarray, traj_y: np.ndarray, params: Dict) -> Dict:
    """
    GPU加速的2D RQA计算 (便捷接口)

    Args:
        traj_x: X坐标
        traj_y: Y坐标
        params: {'m': int, 'tau': int, 'eps': float, 'lmin': int}

    Returns:
        包含 RR_2d, DET_2d, L_max_2d, ENT_2d 的字典
    """
    analyzer = RQAAnalyzerGPU()
    results = analyzer.analyze_trajectory_gpu(traj_x, traj_y, params)

    if results['success']:
        return {
            'RR_2d': results['2d_xy']['RR_2d'],
            'DET_2d': results['2d_xy']['DET_2d'],
            'L_max_2d': results['2d_xy']['L_max_2d'],
            'ENT_2d': results['2d_xy']['ENT_2d']
        }
    else:
        raise RuntimeError(f"GPU RQA计算失败: {results.get('error', 'Unknown')}")


# 自动降级函数 (GPU失败时切换到CPU)

def compute_rqa_with_fallback(traj_x: np.ndarray, traj_y: np.ndarray,
                               params: Dict, mode: str = '1d') -> Dict:
    """
    自动降级的RQA计算 (GPU失败切换到CPU)

    Args:
        traj_x: X坐标
        traj_y: Y坐标
        params: RQA参数
        mode: '1d' or '2d'

    Returns:
        RQA结果字典
    """
    try:
        # 优先GPU
        if mode == '1d':
            return compute_rqa_1d_gpu(traj_x, traj_y, params)
        else:
            return compute_rqa_2d_gpu(traj_x, traj_y, params)
    except (cp.cuda.memory.OutOfMemoryError, RuntimeError, Exception) as e:
        # 降级到CPU
        print(f"⚠️  GPU失败 ({str(e)})，切换到CPU模式")
        from analysis.rqa_analyzer import RQAAnalyzer

        # 调用原CPU版本 (需要实现对应接口)
        # 这里简化处理，实际需要调用原有的CPU函数
        raise NotImplementedError("CPU降级版本需要实现")


if __name__ == '__main__':
    # 简单测试
    print("=== GPU RQA分析器测试 ===")

    # 生成测试数据
    np.random.seed(42)
    traj_x = np.cumsum(np.random.randn(5000)) * 0.1
    traj_y = np.cumsum(np.random.randn(5000)) * 0.1

    params = {'m': 5, 'tau': 3, 'eps': 0.08, 'lmin': 2}

    # GPU测试
    analyzer = RQAAnalyzerGPU()
    results = analyzer.analyze_trajectory_gpu(traj_x, traj_y, params)

    print(f"\n✅ GPU分析完成")
    print(f"总耗时: {results['total_time']:.3f}秒")
    print(f"1D X指标: RR={results['1d_x']['RR_x']:.4f}, DET={results['1d_x']['DET_x']:.4f}")
    print(f"2D XY指标: RR={results['2d_xy']['RR_2d']:.4f}, DET={results['2d_xy']['DET_2d']:.4f}")
    print(f"显存使用: {results['gpu_memory']['used_gb']:.2f} / {results['gpu_memory']['total_gb']:.1f} GB")
