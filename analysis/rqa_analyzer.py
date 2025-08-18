"""
RQA (Recurrence Quantification Analysis) 分析模块 - 增强版

基于用户需求改进，支持：
1. 1D信号分析（使用x坐标）
2. ROI信息集成和颜色编码
3. 改进的可视化效果
4. 更准确的RQA指标计算
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from scipy.stats import zscore
import base64
import io
import math
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class RQAAnalyzer:
    """增强版RQA分析器"""
    
    def __init__(self):
        self.default_params = {
            'embedding_dimension': 2,
            'time_delay': 1,
            'recurrence_threshold': 0.05,
            'min_line_length': 2,
            'analysis_mode': '1d_x',  # '1d_x', '1d_amplitude', '2d_xy'
            'distance_metric': '1d_abs'  # '1d_abs', 'euclidean'
        }
        
        # ROI颜色映射（基于用户代码逻辑）
        self.roi_colors = {}
        
    def analyze_data(self, data_file: str, parameters: Dict = None) -> Dict:
        """
        对眼动数据进行RQA分析（增强版）
        
        Args:
            data_file: 数据文件路径
            parameters: RQA参数
            
        Returns:
            分析结果字典
        """
        try:
            # 使用默认参数并更新用户参数
            params = self.default_params.copy()
            if parameters:
                params.update(parameters)
            
            # 加载数据
            df = pd.read_csv(data_file)
            
            # 数据预处理
            signal_data, roi_info = self._preprocess_data_enhanced(df, params['analysis_mode'])
            
            # 构建嵌入空间
            embedded_data = self._embed_signal(signal_data, 
                                             params['embedding_dimension'], 
                                             params['time_delay'])
            
            # 计算递归矩阵
            recurrence_matrix = self._compute_recurrence_matrix_enhanced(
                embedded_data, 
                params['recurrence_threshold'],
                params['distance_metric']
            )
            
            # 生成递归图（增强版，包含ROI信息）
            recurrence_plot = self._create_enhanced_recurrence_plot(
                recurrence_matrix, df, roi_info, params
            )
            
            # 计算RQA指标
            metrics = self._compute_rqa_metrics_enhanced(
                recurrence_matrix, 
                params['min_line_length']
            )
            
            # 生成时间序列图
            time_series_plot = self._create_time_series_plot(
                signal_data, df, roi_info, params
            )
            
            return {
                'success': True,
                'recurrence_plot': recurrence_plot,
                'time_series_plot': time_series_plot,
                'metrics': metrics,
                'parameters': params,
                'analysis_info': {
                    'data_points': int(len(df)),
                    'embedding_points': int(len(embedded_data)),
                    'analysis_mode': str(params['analysis_mode']),
                    'roi_count': int(len(roi_info['unique_rois']) if roi_info else 0)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _preprocess_data_enhanced(self, df: pd.DataFrame, analysis_mode: str) -> Tuple[np.ndarray, Dict]:
        """增强数据预处理"""
        # 检查必要的列
        required_cols = ['x']
        if analysis_mode == '2d_xy':
            required_cols.append('y')
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"数据文件缺少列: {missing_cols}")
        
        # 提取信号数据
        if analysis_mode == '1d_x':
            # 使用x坐标作为1D信号
            signal_data = df['x'].values
        elif analysis_mode == '1d_amplitude':
            # 使用幅度 sqrt(x^2 + y^2)
            x_vals = df['x'].values
            y_vals = df['y'].values if 'y' in df.columns else np.zeros_like(x_vals)
            signal_data = np.sqrt(x_vals**2 + y_vals**2)
        elif analysis_mode == '2d_xy':
            # 使用x,y坐标
            signal_data = np.column_stack([df['x'].values, df['y'].values])
        else:
            raise ValueError(f"不支持的分析模式: {analysis_mode}")
        
        # 处理ROI信息
        roi_info = self._extract_roi_info(df)
        
        # 去除无效值
        if signal_data.ndim == 1:
            valid_mask = ~np.isnan(signal_data)
            signal_data = signal_data[valid_mask]
        else:
            valid_mask = ~(np.isnan(signal_data).any(axis=1))
            signal_data = signal_data[valid_mask]
        
        return signal_data, roi_info
    
    def _extract_roi_info(self, df: pd.DataFrame) -> Dict:
        """提取ROI信息"""
        roi_info = {
            'rois': [],
            'sequences': [],
            'unique_rois': [],
            'roi_colors': {}
        }
        
        if 'ROI' in df.columns and 'SequenceID' in df.columns:
            # 清理ROI名称（去除n2前缀）
            df_roi = df['ROI'].fillna('Unknown').astype(str)
            df_roi_cleaned = df_roi.str.replace('n2', '', regex=False)
            
            roi_info['rois'] = df_roi_cleaned.values
            roi_info['sequences'] = df['SequenceID'].values
            roi_info['unique_rois'] = sorted(df_roi_cleaned.unique())
            
            # 分配颜色
            cmap = plt.cm.get_cmap('tab20', len(roi_info['unique_rois']))
            for i, roi in enumerate(roi_info['unique_rois']):
                roi_info['roi_colors'][roi] = cmap(i)
        else:
            # 为缺少ROI/SequenceID信息的数据生成默认值
            print("警告: 数据中缺少ROI或SequenceID列，使用默认值")
            n_points = len(df)
            roi_info['rois'] = ['background'] * n_points
            roi_info['sequences'] = [0] * n_points
            roi_info['unique_rois'] = ['background']
            roi_info['roi_colors'] = {'background': plt.cm.tab20(0)}
        
        return roi_info
    
    def _embed_signal(self, signal_data: np.ndarray, m: int, delay: int) -> np.ndarray:
        """信号嵌入"""
        if signal_data.ndim == 1:
            # 1D信号嵌入
            N = len(signal_data)
            rows = N - (m-1)*delay
            if rows <= 0:
                return np.empty((0, m))
            
            embedded = np.zeros((rows, m))
            for i in range(rows):
                for j in range(m):
                    embedded[i, j] = signal_data[i + j*delay]
            return embedded
        else:
            # 2D信号嵌入
            N = signal_data.shape[0]
            rows = N - (m-1)*delay
            if rows <= 0:
                return np.empty((0, m*2))
            
            embedded = np.zeros((rows, m*2))
            for i in range(rows):
                for j in range(m):
                    embedded[i, j*2] = signal_data[i + j*delay, 0]
                    embedded[i, j*2+1] = signal_data[i + j*delay, 1]
            return embedded
    
    def _compute_recurrence_matrix_enhanced(self, embedded_data: np.ndarray, 
                                          threshold: float, metric: str) -> np.ndarray:
        """计算递归矩阵（增强版）"""
        M = embedded_data.shape[0]
        RP = np.zeros((M, M), dtype=int)
        
        for i in range(M):
            for j in range(M):
                if metric == '1d_abs':
                    # 1D绝对差距离
                    dist = np.sum(np.abs(embedded_data[i] - embedded_data[j]))
                elif metric == 'euclidean':
                    # 欧几里得距离
                    dist = np.sqrt(np.sum((embedded_data[i] - embedded_data[j])**2))
                else:
                    dist = 0
                
                if dist <= threshold:
                    RP[i, j] = 1
        
        return RP
    
    def _create_enhanced_recurrence_plot(self, recurrence_matrix: np.ndarray, 
                                       df: pd.DataFrame, roi_info: Dict, 
                                       params: Dict) -> str:
        """创建增强递归图"""
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # 显示递归矩阵
        ax.imshow(recurrence_matrix, cmap='binary', origin='lower')
        ax.set_title(f'递归图 (Recurrence Plot) - {params["analysis_mode"]}', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('时间索引', fontsize=12)
        ax.set_ylabel('时间索引', fontsize=12)
        
        # 添加ROI信息（如果有）
        if roi_info and 'sequences' in roi_info:
            self._add_roi_rectangles_to_rp(ax, df, roi_info, recurrence_matrix.shape[0])
        
        # 保存为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return plot_data
    
    def _add_roi_rectangles_to_rp(self, ax, df: pd.DataFrame, roi_info: Dict, matrix_size: int):
        """在递归图上添加ROI矩形"""
        from matplotlib.patches import Rectangle
        
        # 检查是否有SequenceID列
        if 'SequenceID' not in df.columns:
            # 如果没有SequenceID列，直接返回，不添加ROI矩形
            return
        
        # 获取序列信息
        seq_vals = df['SequenceID'].unique()
        
        for sid in sorted(seq_vals):
            if sid <= 0:
                continue
            
            # 找到该序列的索引范围
            inds = df.index[df['SequenceID'] == sid].to_numpy()
            if len(inds) < 2:
                continue
            
            st_i = inds[0]
            ed_i = inds[-1]
            
            # 确保索引在矩阵范围内
            if st_i >= matrix_size:
                continue
            if ed_i >= matrix_size:
                ed_i = matrix_size - 1
            
            w = ed_i - st_i + 1
            if w < 1:
                continue
            
            # 获取ROI信息
            roi_name = roi_info['rois'][st_i] if st_i < len(roi_info['rois']) else 'Unknown'
            color = roi_info['roi_colors'].get(roi_name, 'gray')
            
            # 在对角线位置绘制矩形
            rect = Rectangle((st_i, st_i), w, w,
                           fill=True, alpha=0.3, color=color, linewidth=1)
            ax.add_patch(rect)
            
            # 添加标签
            cx = st_i + w/2
            ax.text(cx, cx, f'S{sid}({roi_name})', 
                   color='black', fontsize=8, ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.7))
    
    def _create_time_series_plot(self, signal_data: np.ndarray, 
                               df: pd.DataFrame, roi_info: Dict, 
                               params: Dict) -> str:
        """创建时间序列图"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 时间轴
        if 'milliseconds' in df.columns:
            time_vals = df['milliseconds'].values[:len(signal_data)]
            ax.set_xlabel('时间 (ms)', fontsize=12)
        else:
            time_vals = np.arange(len(signal_data))
            ax.set_xlabel('时间索引', fontsize=12)
        
        # 绘制信号
        if signal_data.ndim == 1:
            ax.plot(time_vals, signal_data, color='blue', linewidth=1.2, alpha=0.8)
            ax.set_ylabel(f'信号值 ({params["analysis_mode"]})', fontsize=12)
        else:
            ax.plot(time_vals, signal_data[:, 0], label='X', color='blue', linewidth=1.2)
            ax.plot(time_vals, signal_data[:, 1], label='Y', color='red', linewidth=1.2)
            ax.legend()
            ax.set_ylabel('坐标值', fontsize=12)
        
        # 添加ROI颜色填充
        if roi_info and 'sequences' in roi_info:
            self._add_roi_coloring_to_timeseries(ax, df, roi_info, time_vals, signal_data)
        
        ax.set_title(f'时间序列 - {params["analysis_mode"]}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 保存为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return plot_data
    
    def _add_roi_coloring_to_timeseries(self, ax, df: pd.DataFrame, roi_info: Dict, 
                                      time_vals: np.ndarray, signal_data: np.ndarray):
        """为时间序列添加ROI颜色"""
        # 检查是否有SequenceID列
        if 'SequenceID' not in df.columns:
            # 如果没有SequenceID列，直接返回，不添加ROI颜色
            return
            
        seq_vals = df['SequenceID'].unique()
        
        for sid in sorted(seq_vals):
            if sid <= 0:
                continue
            
            inds = df.index[df['SequenceID'] == sid].to_numpy()
            if len(inds) < 2:
                continue
            
            st_i = inds[0]
            ed_i = min(inds[-1], len(signal_data) - 1)
            
            if st_i >= len(signal_data):
                continue
            
            # 获取该段的时间和信号值
            seg_time = time_vals[st_i:ed_i+1]
            
            if signal_data.ndim == 1:
                seg_signal = signal_data[st_i:ed_i+1]
                roi_name = roi_info['rois'][st_i] if st_i < len(roi_info['rois']) else 'Unknown'
                color = roi_info['roi_colors'].get(roi_name, 'gray')
                
                # 填充到0线
                ax.fill_between(seg_time, seg_signal, 0, color=color, alpha=0.3)
                
                # 添加ROI标签
                if len(seg_time) > 0 and len(seg_signal) > 0:
                    ax.text(seg_time[0], seg_signal[0], f'S{sid}({roi_name})',
                           color=color, fontsize=8, ha='right', va='top',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.7))
    
    def _compute_rqa_metrics_enhanced(self, recurrence_matrix: np.ndarray, 
                                    min_line_length: int) -> Dict:
        """计算RQA指标（增强版）"""
        N = recurrence_matrix.shape[0]
        
        # 递归率 (Recurrence Rate, RR)
        total_points = N * N
        recurrent_points = np.sum(recurrence_matrix)
        RR = recurrent_points / total_points
        
        # 提取对角线段长度
        diag_lengths = self._extract_diagonal_lengths_enhanced(recurrence_matrix)
        
        # 确定性 (Determinism, DET)
        total_diag_points = sum(length * count for length, count in diag_lengths.items())
        long_diag_points = sum(length * count for length, count in diag_lengths.items() 
                              if length >= min_line_length)
        DET = long_diag_points / total_diag_points if total_diag_points > 0 else 0
        
        # 平均对角线长度 (L)
        if long_diag_points > 0:
            weighted_lengths = [length for length, count in diag_lengths.items() 
                              if length >= min_line_length for _ in range(count)]
            L = np.mean(weighted_lengths) if weighted_lengths else 0
        else:
            L = 0
        
        # 最大对角线长度 (Lmax)
        long_lengths = [length for length in diag_lengths.keys() if length >= min_line_length]
        Lmax = max(long_lengths) if long_lengths else 0
        
        # 发散性 (Divergence, DIV)
        DIV = 1.0 / Lmax if Lmax > 0 else 0
        
        # 层流性 (Laminarity, LAM) - 基于垂直线结构
        vert_lengths = self._extract_vertical_lengths_enhanced(recurrence_matrix)
        total_vert_points = sum(length * count for length, count in vert_lengths.items())
        long_vert_points = sum(length * count for length, count in vert_lengths.items() 
                              if length >= min_line_length)
        LAM = long_vert_points / total_vert_points if total_vert_points > 0 else 0
        
        # 平均垂直线长度 (TT)
        if long_vert_points > 0:
            weighted_vert_lengths = [length for length, count in vert_lengths.items() 
                                   if length >= min_line_length for _ in range(count)]
            TT = np.mean(weighted_vert_lengths) if weighted_vert_lengths else 0
        else:
            TT = 0
        
        # 最大垂直线长度 (Vmax)
        long_vert_lengths = [length for length in vert_lengths.keys() if length >= min_line_length]
        Vmax = max(long_vert_lengths) if long_vert_lengths else 0
        
        # 熵 (Entropy, ENTR)
        ENTR = self._compute_shannon_entropy(diag_lengths, min_line_length)
        
        # 确保所有值都是JSON可序列化的Python原生类型
        return {
            'RR': float(round(RR, 6)),
            'DET': float(round(DET, 6)),
            'LAM': float(round(LAM, 6)),
            'L': float(round(L, 4)),
            'Lmax': int(Lmax),
            'DIV': float(round(DIV, 6)),
            'TT': float(round(TT, 4)),
            'Vmax': int(Vmax),
            'ENTR': float(round(ENTR, 6))
        }
    
    def _extract_diagonal_lengths_enhanced(self, matrix: np.ndarray) -> Dict[int, int]:
        """提取对角线长度（增强版）"""
        lengths = {}
        N = matrix.shape[0]
        
        # 遍历所有对角线（主对角线及其平行线）
        for offset in range(-(N-1), N):
            diagonal = np.diagonal(matrix, offset=offset)
            current_length = 0
            
            for point in diagonal:
                if point == 1:
                    current_length += 1
                else:
                    if current_length > 0:
                        lengths[current_length] = lengths.get(current_length, 0) + 1
                    current_length = 0
            
            # 处理对角线末尾
            if current_length > 0:
                lengths[current_length] = lengths.get(current_length, 0) + 1
        
        return lengths
    
    def _extract_vertical_lengths_enhanced(self, matrix: np.ndarray) -> Dict[int, int]:
        """提取垂直线长度（增强版）"""
        lengths = {}
        N = matrix.shape[0]
        
        # 遍历所有列
        for col in range(N):
            current_length = 0
            
            for row in range(N):
                if matrix[row, col] == 1:
                    current_length += 1
                else:
                    if current_length > 0:
                        lengths[current_length] = lengths.get(current_length, 0) + 1
                    current_length = 0
            
            # 处理列末尾
            if current_length > 0:
                lengths[current_length] = lengths.get(current_length, 0) + 1
        
        return lengths
    
    def _compute_shannon_entropy(self, length_dict: Dict[int, int], min_length: int) -> float:
        """计算Shannon熵"""
        # 只考虑长度 >= min_length 的线段
        relevant_lengths = {length: count for length, count in length_dict.items() 
                          if length >= min_length}
        
        if not relevant_lengths:
            return 0.0
        
        total_count = sum(relevant_lengths.values())
        if total_count == 0:
            return 0.0
        
        entropy = 0.0
        for count in relevant_lengths.values():
            probability = count / total_count
            if probability > 1e-12:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def compare_groups(self, results_list: List[Dict]) -> Dict:
        """比较多组RQA结果"""
        if len(results_list) < 2:
            return {'error': '需要至少两组数据进行比较'}
        
        # 提取指标
        metrics_names = ['RR', 'DET', 'LAM', 'L', 'Lmax', 'DIV', 'TT', 'Vmax', 'ENTR']
        comparison = {}
        
        for metric in metrics_names:
            values = [result['metrics'][metric] for result in results_list 
                     if 'metrics' in result and metric in result['metrics']]
            
            if values:
                # 确保所有统计值都是JSON可序列化的Python原生类型
                comparison[metric] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'values': [float(v) if isinstance(v, (np.integer, np.floating)) else v for v in values]
                }
        
        return comparison


def create_rqa_analyzer():
    """创建RQA分析器实例"""
    return RQAAnalyzer()


# 测试函数
if __name__ == "__main__":
    analyzer = create_rqa_analyzer()
    
    # 创建测试数据（模拟眼动数据）
    np.random.seed(42)
    n_points = 500
    
    # 模拟x坐标数据（带有一些周期性模式）
    t = np.linspace(0, 10, n_points)
    x = 5 * np.sin(0.5 * t) + 2 * np.cos(2 * t) + 0.5 * np.random.randn(n_points)
    y = 3 * np.cos(0.3 * t) + 1.5 * np.sin(1.5 * t) + 0.5 * np.random.randn(n_points)
    
    # 模拟ROI和序列信息
    roi_names = ['ROI_A', 'ROI_B', 'ROI_C'] * (n_points // 100 + 1)
    sequence_ids = np.repeat(range(1, n_points // 100 + 2), 100)[:n_points]
    
    test_df = pd.DataFrame({
        'x': x,
        'y': y,
        'ROI': roi_names[:n_points],
        'SequenceID': sequence_ids,
        'milliseconds': np.arange(n_points) * 16.67  # 模拟60Hz采样
    })
    
    # 保存测试数据
    test_file = 'test_rqa_enhanced_data.csv'
    test_df.to_csv(test_file, index=False)
    
    # 运行分析
    params = {
        'analysis_mode': '1d_x',
        'embedding_dimension': 2,
        'time_delay': 1,
        'recurrence_threshold': 0.1,
        'min_line_length': 2,
        'distance_metric': '1d_abs'
    }
    
    result = analyzer.analyze_data(test_file, params)
    
    if result['success']:
        print("🎉 RQA分析成功!")
        print("📊 指标:")
        for key, value in result['metrics'].items():
            print(f"  {key}: {value}")
        print(f"\n📈 数据信息:")
        for key, value in result['data_info'].items():
            print(f"  {key}: {value}")
    else:
        print(f"❌ 分析失败: {result['error']}") 