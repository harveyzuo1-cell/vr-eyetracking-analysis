"""
Numba加速的RQA计算核心函数

使用JIT编译将Python代码编译成机器码,大幅提升计算性能
"""

import numpy as np
from numba import jit, prange
import math


@jit(nopython=True, parallel=True, cache=True)
def compute_distance_matrix_euclidean(embedded):
    """
    计算欧几里得距离矩阵 (Numba加速)

    Args:
        embedded: 嵌入矩阵, shape=(M, d)

    Returns:
        dist_matrix: 距离矩阵, shape=(M, M)
    """
    M = embedded.shape[0]
    d = embedded.shape[1]
    dist_matrix = np.zeros((M, M), dtype=np.float64)

    for i in prange(M):
        for j in range(i, M):  # 只计算上三角，利用对称性
            dist = 0.0
            for k in range(d):
                diff = embedded[i, k] - embedded[j, k]
                dist += diff * diff
            dist = math.sqrt(dist)
            dist_matrix[i, j] = dist
            dist_matrix[j, i] = dist  # 对称

    return dist_matrix


@jit(nopython=True, parallel=True, cache=True)
def compute_distance_matrix_cityblock(embedded):
    """
    计算曼哈顿距离矩阵 (Numba加速)

    Args:
        embedded: 嵌入矩阵, shape=(M, d)

    Returns:
        dist_matrix: 距离矩阵, shape=(M, M)
    """
    M = embedded.shape[0]
    d = embedded.shape[1]
    dist_matrix = np.zeros((M, M), dtype=np.float64)

    for i in prange(M):
        for j in range(i, M):
            dist = 0.0
            for k in range(d):
                dist += abs(embedded[i, k] - embedded[j, k])
            dist_matrix[i, j] = dist
            dist_matrix[j, i] = dist

    return dist_matrix


@jit(nopython=True, parallel=True, cache=True)
def compute_recurrence_matrix_fast(dist_matrix, eps):
    """
    根据距离矩阵生成递归矩阵 (Numba加速)

    Args:
        dist_matrix: 距离矩阵, shape=(M, M)
        eps: 递归阈值

    Returns:
        RP: 递归矩阵, shape=(M, M), 值为0或1
    """
    M = dist_matrix.shape[0]
    RP = np.zeros((M, M), dtype=np.int8)

    for i in prange(M):
        for j in range(M):
            if dist_matrix[i, j] <= eps:
                RP[i, j] = 1

    return RP


@jit(nopython=True)
def extract_diagonal_lengths_fast(RP):
    """
    提取对角线长度分布 (Numba加速)

    Args:
        RP: 递归矩阵, shape=(M, M)

    Returns:
        lengths: 对角线长度数组
    """
    M = RP.shape[0]

    # 预分配足够大的数组来存储所有可能的对角线长度
    # 最多有M条对角线，每条最长M
    max_diagonals = 2 * M - 1
    lengths = np.zeros(max_diagonals * M, dtype=np.int32)
    count = 0

    # 遍历所有对角线 (从左下到右上)
    for diag_offset in range(-(M-1), M):
        current_length = 0

        if diag_offset >= 0:
            # 主对角线及上方
            for i in range(M - diag_offset):
                j = i + diag_offset
                if RP[i, j] == 1:
                    current_length += 1
                else:
                    if current_length > 0:
                        lengths[count] = current_length
                        count += 1
                        current_length = 0
        else:
            # 主对角线下方
            for j in range(M + diag_offset):
                i = j - diag_offset
                if RP[i, j] == 1:
                    current_length += 1
                else:
                    if current_length > 0:
                        lengths[count] = current_length
                        count += 1
                        current_length = 0

        # 对角线结束时如果还有未记录的长度
        if current_length > 0:
            lengths[count] = current_length
            count += 1

    # 返回实际有效的长度
    return lengths[:count]


@jit(nopython=True)
def compute_rqa_metrics_fast(RP, lmin):
    """
    计算RQA指标 (Numba加速)

    Args:
        RP: 递归矩阵, shape=(M, M)
        lmin: 最小线长

    Returns:
        (RR, DET, ENT): 三个RQA指标
    """
    M = RP.shape[0]

    # 1. RR: 递归率
    total_points = M * M
    recurrence_points = 0
    for i in range(M):
        for j in range(M):
            recurrence_points += RP[i, j]

    RR = recurrence_points / total_points if total_points > 0 else 0.0

    # 2. 提取对角线长度
    lengths = extract_diagonal_lengths_fast(RP)

    if len(lengths) == 0:
        return RR, 0.0, 0.0

    # 3. 计算总长度和DET
    total_length = 0.0
    det_length = 0.0
    for length in lengths:
        total_length += length
        if length >= lmin:
            det_length += length

    DET = det_length / total_length if total_length > 0 else 0.0

    # 4. 计算ENT (熵)
    # 首先统计长度分布
    max_length = 0
    for length in lengths:
        if length > max_length:
            max_length = length

    # 创建长度计数数组
    length_counts = np.zeros(max_length + 1, dtype=np.int32)
    for length in lengths:
        if length >= lmin:
            length_counts[length] += 1

    # 计算总的>=lmin的对角线数
    total_lines_lmin = 0
    for count in length_counts:
        total_lines_lmin += count

    # 计算熵
    ENT = 0.0
    if total_lines_lmin > 0:
        for length in range(lmin, max_length + 1):
            count = length_counts[length]
            if count > 0:
                p_l = count / total_lines_lmin
                if p_l > 1e-12:
                    ENT += -p_l * math.log2(p_l)

    return RR, DET, ENT
