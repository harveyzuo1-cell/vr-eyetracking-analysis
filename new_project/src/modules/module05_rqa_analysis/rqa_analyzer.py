"""
RQA分析器 - 核心算法实现

实现递归量化分析（Recurrence Quantification Analysis）的核心算法：
1. 时间延迟嵌入（Time Delay Embedding）
2. 递归矩阵计算（Recurrence Matrix）
3. RQA指标计算（RR, DET, ENT）
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from pathlib import Path
import math

from src.utils.logger import setup_logger
from src.modules.module05_rqa_analysis.rqa_fast import (
    compute_distance_matrix_euclidean,
    compute_distance_matrix_cityblock,
    compute_recurrence_matrix_fast,
    compute_rqa_metrics_fast
)

logger = setup_logger(__name__)


class RQAAnalyzer:
    """RQA分析器"""

    def __init__(self):
        """初始化RQA分析器"""
        self.default_params = {
            'm': 2,      # 嵌入维度
            'tau': 1,    # 时间延迟
            'eps': 0.05, # 递归阈值
            'lmin': 2    # 最小线长
        }

    def analyze_single_file(self, csv_path: str, params: Dict) -> Dict:
        """
        分析单个CSV文件

        Args:
            csv_path: 校准后CSV文件路径
            params: RQA参数 {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}

        Returns:
            结果字典，包含6个RQA指标
        """
        try:
            # 加载数据
            x, y, df = self._load_csv_data(csv_path)

            if len(x) < 5:
                logger.warning(f"信号太短: {csv_path}, length={len(x)}")
                return self._empty_result()

            # 提取参数
            m = params.get('m', self.default_params['m'])
            tau = params.get('tau', self.default_params['tau'])
            eps = params.get('eps', self.default_params['eps'])
            lmin = params.get('lmin', self.default_params['lmin'])

            # 初始化结果
            result = self._empty_result()

            # 1D-x 分析
            try:
                embedded_1d = self.embed_signal_1d(x, m, tau)
                if embedded_1d.shape[0] >= 2:
                    rp_1d = self.compute_recurrence_matrix(embedded_1d, eps, metric='1d_abs')
                    metrics_1d = self.compute_rqa_metrics(rp_1d, lmin)

                    result['RR-1D-x'] = metrics_1d['RR']
                    result['DET-1D-x'] = metrics_1d['DET']
                    result['ENT-1D-x'] = metrics_1d['ENT']
            except Exception as e:
                logger.error(f"1D分析失败: {csv_path} - {e}")

            # 2D-xy 分析
            try:
                embedded_2d = self.embed_signal_2d(x, y, m, tau)
                if embedded_2d.shape[0] >= 2:
                    rp_2d = self.compute_recurrence_matrix(embedded_2d, eps, metric='euclidean')
                    metrics_2d = self.compute_rqa_metrics(rp_2d, lmin)

                    result['RR-2D-xy'] = metrics_2d['RR']
                    result['DET-2D-xy'] = metrics_2d['DET']
                    result['ENT-2D-xy'] = metrics_2d['ENT']
            except Exception as e:
                logger.error(f"2D分析失败: {csv_path} - {e}")

            return result

        except Exception as e:
            logger.error(f"分析文件失败: {csv_path} - {e}", exc_info=True)
            return self._empty_result()

    def _load_csv_data(self, csv_path: str) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        加载CSV数据

        Args:
            csv_path: CSV文件路径

        Returns:
            (x, y, df)
        """
        df = pd.read_csv(csv_path)

        # 支持多种列名格式
        if 'x' in df.columns and 'y' in df.columns:
            x = df['x'].values
            y = df['y'].values
        elif 'GazePointX_normalized' in df.columns and 'GazePointY_normalized' in df.columns:
            x = df['GazePointX_normalized'].values
            y = df['GazePointY_normalized'].values
        else:
            raise ValueError(f"CSV文件缺少x/y列: {csv_path}")

        return x, y, df

    def _empty_result(self) -> Dict:
        """返回空结果（所有指标为NaN）"""
        return {
            'RR-1D-x': np.nan,
            'DET-1D-x': np.nan,
            'ENT-1D-x': np.nan,
            'RR-2D-xy': np.nan,
            'DET-2D-xy': np.nan,
            'ENT-2D-xy': np.nan
        }

    def embed_signal_1d(self, x: np.ndarray, m: int, tau: int) -> np.ndarray:
        """
        1D时间延迟嵌入

        Args:
            x: 1D信号，shape=(N,)
            m: 嵌入维度
            tau: 时间延迟

        Returns:
            嵌入矩阵，shape=(N-(m-1)*tau, m)

        Example:
            x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            m = 3, tau = 2

            embedded = [
                [0, 2, 4],  # i=0: x[0], x[2], x[4]
                [1, 3, 5],  # i=1: x[1], x[3], x[5]
                [2, 4, 6],  # i=2: x[2], x[4], x[6]
                [3, 5, 7],  # i=3: x[3], x[5], x[7]
                [4, 6, 8],  # i=4: x[4], x[6], x[8]
                [5, 7, 9],  # i=5: x[5], x[7], x[9]
            ]
        """
        N = len(x)
        rows = N - (m - 1) * tau

        if rows <= 0:
            raise ValueError(f"信号太短：N={N}, m={m}, tau={tau}, 需要至少{(m-1)*tau + 1}个数据点")

        embedded = np.zeros((rows, m))
        for i in range(rows):
            for j in range(m):
                embedded[i, j] = x[i + j * tau]

        return embedded

    def embed_signal_2d(self, x: np.ndarray, y: np.ndarray, m: int, tau: int) -> np.ndarray:
        """
        2D时间延迟嵌入

        Args:
            x, y: 2D轨迹，shape=(N,)
            m: 嵌入维度
            tau: 时间延迟

        Returns:
            嵌入矩阵，shape=(N-(m-1)*tau, 2*m)

        Example:
            x = [0, 1, 2, 3, 4]
            y = [5, 6, 7, 8, 9]
            m = 2, tau = 1

            embedded = [
                [0, 5, 1, 6],  # i=0: (x[0],y[0]), (x[1],y[1])
                [1, 6, 2, 7],  # i=1: (x[1],y[1]), (x[2],y[2])
                [2, 7, 3, 8],  # i=2: (x[2],y[2]), (x[3],y[3])
                [3, 8, 4, 9],  # i=3: (x[3],y[3]), (x[4],y[4])
            ]
        """
        N = len(x)
        if len(y) != N:
            raise ValueError("x和y长度必须相同")

        rows = N - (m - 1) * tau
        if rows <= 0:
            raise ValueError(f"信号太短：N={N}, m={m}, tau={tau}")

        embedded = np.zeros((rows, 2 * m))
        for i in range(rows):
            for j in range(m):
                embedded[i, 2*j] = x[i + j * tau]
                embedded[i, 2*j + 1] = y[i + j * tau]

        return embedded

    def compute_recurrence_matrix(self, embedded: np.ndarray, eps: float,
                                  metric: str = 'euclidean') -> np.ndarray:
        """
        计算递归矩阵 (使用Numba加速)

        Args:
            embedded: 嵌入矩阵，shape=(M, d)
            eps: 递归阈值
            metric: 距离度量 ('1d_abs' 或 'euclidean')

        Returns:
            递归矩阵 RP，shape=(M, M)，值为0或1

        Definition:
            RP[i,j] = 1 if dist(embedded[i], embedded[j]) <= eps
                      0 otherwise
        """
        # 使用Numba加速的距离矩阵计算
        if metric == '1d_abs':
            # 曼哈顿距离（L1范数）
            dist_matrix = compute_distance_matrix_cityblock(embedded)
        elif metric == 'euclidean':
            # 欧几里得距离（L2范数）
            dist_matrix = compute_distance_matrix_euclidean(embedded)
        else:
            raise ValueError(f"不支持的距离度量: {metric}")

        # 使用Numba加速的递归矩阵生成
        RP = compute_recurrence_matrix_fast(dist_matrix, eps)

        return RP

    def compute_rqa_metrics(self, RP: np.ndarray, lmin: int = 2) -> Dict[str, float]:
        """
        计算RQA指标 (使用Numba加速)

        Args:
            RP: 递归矩阵，shape=(M, M)
            lmin: 最小线长

        Returns:
            {
                'RR': float,   # Recurrence Rate (递归率)
                'DET': float,  # Determinism (确定性)
                'ENT': float   # Entropy (熵)
            }
        """
        # 使用Numba加速的RQA指标计算
        RR, DET, ENT = compute_rqa_metrics_fast(RP, lmin)

        return {
            'RR': float(RR),
            'DET': float(DET),
            'ENT': float(ENT)
        }

    def _extract_diagonal_lengths(self, RP: np.ndarray) -> Dict[int, int]:
        """
        提取对角线中连续1的长度分布

        Args:
            RP: 递归矩阵，shape=(M, M)

        Returns:
            {长度: 出现次数}

        Example:
            RP = [
                [1, 1, 0, 0],
                [1, 1, 1, 0],
                [0, 1, 1, 1],
                [0, 0, 1, 1]
            ]

            对角线d=-3: [0]           -> 无连续段
            对角线d=-2: [0, 0]         -> 无连续段
            对角线d=-1: [1, 1, 1]      -> 一段长度3
            对角线d=0:  [1, 1, 1, 1]   -> 一段长度4
            对角线d=1:  [1, 1, 1]      -> 一段长度3
            对角线d=2:  [0, 0]         -> 无连续段
            对角线d=3:  [0]            -> 无连续段

            结果: {3: 2, 4: 1}  # 长度3出现2次，长度4出现1次
        """
        M = RP.shape[0]
        length_counts = {}

        # 遍历所有对角线
        for d in range(-(M-1), M):
            diagonal = []
            for i in range(M):
                j = i + d
                if 0 <= j < M:
                    diagonal.append(RP[i, j])

            # 提取连续1的长度
            idx = 0
            while idx < len(diagonal):
                if diagonal[idx] == 1:
                    length = 1
                    idx += 1
                    while idx < len(diagonal) and diagonal[idx] == 1:
                        length += 1
                        idx += 1
                    length_counts[length] = length_counts.get(length, 0) + 1
                else:
                    idx += 1

        return length_counts

    def create_recurrence_plot(self, RP: np.ndarray, title: str = "Recurrence Plot") -> bytes:
        """
        创建递归图的PNG图像

        Args:
            RP: 递归矩阵
            title: 图表标题

        Returns:
            PNG图像的字节数据
        """
        import matplotlib.pyplot as plt
        import io

        fig, ax = plt.subplots(figsize=(10, 10))

        # 显示递归矩阵
        ax.imshow(RP, cmap='binary', origin='lower', interpolation='nearest')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Time Index', fontsize=12)
        ax.set_ylabel('Time Index', fontsize=12)

        # 保存为字节流
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        plt.close(fig)

        return image_bytes
