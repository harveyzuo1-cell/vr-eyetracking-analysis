import os
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import json
from pathlib import Path
import base64
from io import BytesIO
import gc  # 垃圾回收
import time
from datetime import datetime # Added for datetime import

class RQABatchRenderer:
    """RQA批量渲染器 - 从校准后数据生成递归图并按参数结构存储"""
    
    def __init__(self, data_root="data"):
        self.data_root = data_root
        self.rqa_results_dir = os.path.join(data_root, "rqa_results")
        self.ensure_directories()
        
        # 默认参数
        self.default_params = {
            "analysis_mode": "1d_x",  # 1d_x, 1d_amplitude, 2d_xy
            "distance_metric": "1d_abs",  # 1d_abs, euclidean
            "embedding_dimension": 2,
            "time_delay": 1,
            "recurrence_threshold": 0.05,
            "min_line_length": 2
        }
        
        # 默认颜色主题
        self.default_color_theme = "green_gradient"
        
        # 颜色主题
        self.color_themes = {
            "grayscale": "gray",
            "green_gradient": "Greens"
        }
        
        # 批处理设置
        self.batch_size = 5  # 减少批处理大小
        self.max_memory_mb = 400  # 减少内存限制
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.rqa_results_dir, exist_ok=True)
    
    def get_param_signature(self, params, color_theme):
        """生成参数组合的唯一标识"""
        return f"mode_{params['analysis_mode']}_dist_{params['distance_metric']}_m{params['embedding_dimension']}_tau{params['time_delay']}_eps{params['recurrence_threshold']:.3f}_lmin{params['min_line_length']}_color_{color_theme}"
    
    def get_results_directory(self, params, color_theme):
        """根据参数组合生成结果目录路径"""
        param_signature = self.get_param_signature(params, color_theme)
        return os.path.join(self.rqa_results_dir, param_signature)
    
    def find_calibrated_data_files(self):
        """查找校准后的数据文件"""
        data_files = []
        
        # 查找各组的校准后数据
        for group_type in ["control", "mci", "ad"]:
            calibrated_dir = os.path.join(self.data_root, f"{group_type}_calibrated")
            
            if not os.path.exists(calibrated_dir):
                print(f"警告: 未找到 {calibrated_dir}")
                continue
            
            # 遍历组内的所有子目录和文件
            for root, dirs, files in os.walk(calibrated_dir):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(root, file)
                        
                        # 解析文件信息
                        rel_path = os.path.relpath(file_path, calibrated_dir)
                        path_parts = rel_path.split(os.sep)
                        
                        # 确定问题编号
                        question = self.extract_question_from_path(rel_path, file)
                        if question:
                            # 确定数据ID
                            data_id = os.path.splitext(file)[0]
                            
                            data_files.append({
                                'group': group_type,
                                'question': question,
                                'data_id': data_id,
                                'file_path': file_path,
                                'relative_path': rel_path
                            })
        
        print(f"找到 {len(data_files)} 个校准后数据文件")
        return data_files
    
    def extract_question_from_path(self, rel_path, filename):
        """从路径和文件名中提取问题编号"""
        # 方法1: 从文件名提取 (如 n1q1.csv -> 1)
        import re
        match = re.search(r'q(\d+)', filename.lower())
        if match:
            return int(match.group(1))
        
        # 方法2: 从路径提取
        for part in rel_path.split(os.sep):
            match = re.search(r'q(\d+)', part.lower())
            if match:
                return int(match.group(1))
        
        # 方法3: 从组目录名提取 (如 control_group_1 -> 检查是否有问题模式)
        for i in range(1, 6):  # Q1-Q5
            if f'q{i}' in rel_path.lower():
                return i
        
        # 默认返回None，需要进一步分析
        return None
    
    def load_and_validate_data(self, file_path):
        """加载并验证眼动数据"""
        try:
            df = pd.read_csv(file_path)
            
            # 检查基本坐标列
            if 'x' not in df.columns or 'y' not in df.columns:
                print(f"警告: {file_path} 缺少必需的x/y坐标列")
                return None
            
            # 检查时间列，支持多种格式
            time_col = None
            for possible_time_col in ['timestamp', 'milliseconds', 'time', 'abs_datetime']:
                if possible_time_col in df.columns:
                    time_col = possible_time_col
                    break
            
            if time_col is None:
                print(f"警告: {file_path} 没有找到时间列，使用索引作为时间")
                df['timestamp'] = range(len(df))
                time_col = 'timestamp'
            else:
                # 重命名为标准的timestamp列
                if time_col != 'timestamp':
                    df['timestamp'] = df[time_col]
            
            # 过滤有效数据
            df = df.dropna(subset=['x', 'y'])
            
            if len(df) < 10:  # 至少需要10个数据点
                print(f"警告: {file_path} 数据点太少: {len(df)}")
                return None
            
            # 确保包含基本列，如果有ROI信息就保留
            result_cols = ['timestamp', 'x', 'y']
            if 'ROI' in df.columns:
                result_cols.append('ROI')
            if 'SequenceID' in df.columns:
                result_cols.append('SequenceID')
            
            available_cols = [col for col in result_cols if col in df.columns]
            return df[available_cols].reset_index(drop=True)
            
        except Exception as e:
            print(f"错误: 无法加载 {file_path}: {str(e)}")
            return None
    
    def strip_n2_prefix(self, roi_name):
        """
        Remove 'n2' prefix from ROI names (like reference code)
        Example: "INST_n2q5_1c" => "INST_q5_1c"
        """
        if not isinstance(roi_name, str):
            return roi_name
        return roi_name.replace("n2", "")
    
    def _fig_to_base64(self, fig):
        """将matplotlib图形转换为base64字符串"""
        try:
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            
            # 转换为base64
            graphic = base64.b64encode(image_png)
            return graphic.decode('utf-8')
        except Exception as e:
            print(f"图形转换base64失败: {e}")
            return ""
    
    def embed_signal(self, signal, m=2, delay=1, mode="1d"):
        """信号嵌入"""
        try:
            if mode == "1d":
                return self._embed_1d(signal, m, delay)
            elif mode == "2d":
                # 修复解包错误：从2D数组中提取x和y列
                if signal.ndim == 2 and signal.shape[1] >= 2:
                    x_ = signal[:, 0]  # 第一列是x
                    y_ = signal[:, 1]  # 第二列是y
                else:
                    raise ValueError(f"2D模式需要形状为(n, 2)的信号数据，得到形状: {signal.shape}")
                return self._embed_2d(x_, y_, m, delay)
            else:
                raise ValueError(f"不支持的嵌入模式: {mode}")
        except Exception as e:
            print(f"信号嵌入失败: {e}")
            raise
        finally:
            gc.collect()
    
    def _embed_1d(self, signal, m=2, delay=1):
        """1D信号嵌入"""
        N = len(signal)
        rows = N - (m-1)*delay
        if rows <= 0:
            return np.empty((0, m))
        
        emb = []
        for i in range(rows):
            emb.append([signal[i + k*delay] for k in range(m)])
        return np.array(emb)
    
    def _embed_2d(self, x_, y_, m=2, delay=1):
        """2D信号嵌入"""
        N = len(x_)
        if len(y_) != N:
            raise ValueError("x_ 和 y_ 长度必须相等!")
        
        rows = N - (m-1)*delay
        if rows <= 0:
            return np.empty((0, 2*m))
        
        emb = np.zeros((rows, 2*m), dtype=float)
        for i in range(rows):
            for k in range(m):
                emb[i, 2*k] = x_[i + k*delay]
                emb[i, 2*k+1] = y_[i + k*delay]
        
        return emb
    
    def extract_diag_lengths(self, RP):
        """
        Extract diagonal line lengths from RP matrix
        Returns a dict: {line_length: count}
        """
        N = RP.shape[0]
        length_counts = {}
        
        # Iterate through all diagonals (main + parallel)
        for d in range(-(N-1), N):
            line_vals = []
            # Collect values along diagonal d
            for i in range(N):
                j = i + d
                if 0 <= j < N:
                    line_vals.append(RP[i, j])
            
            # Count consecutive '1' segments in this diagonal
            idx = 0
            L = len(line_vals)
            while idx < L:
                if line_vals[idx] == 1:
                    seg_len = 1
                    idx2 = idx + 1
                    while idx2 < L and line_vals[idx2] == 1:
                        seg_len += 1
                        idx2 += 1
                    length_counts[seg_len] = length_counts.get(seg_len, 0) + 1
                    idx = idx2
                else:
                    idx += 1
        
        return length_counts
    
    def compute_rqa_measures(self, RP, lmin=2):
        """
        Compute RQA measures: RR, DET, ENT
        Based on reference implementation
        """
        try:
            N = RP.shape[0]
            sum_ones = RP.sum()
            
            # RR: Recurrence Rate
            RR = float(sum_ones) / (N * N) if N > 0 else 0.0
            
            # Extract diagonal lengths
            length_dict = self.extract_diag_lengths(RP)
            
            # Calculate total diagonal points
            denom_all = 0
            for l, c in length_dict.items():
                denom_all += l * c
            
            # Calculate numerators for DET and ENT
            numer_det = 0
            denom_ent = 0
            for l, c in length_dict.items():
                if l >= lmin:
                    numer_det += l * c
                    denom_ent += c
            
            # DET: Determinism
            DET = float(numer_det) / denom_all if denom_all > 0 else 0.0
            
            # ENT: Entropy
            ENT = 0.0
            if denom_ent > 0:
                sum_counts_lmin = sum(c for (ll, c) in length_dict.items() if ll >= lmin)
                if sum_counts_lmin > 0:
                    for l, c in length_dict.items():
                        if l >= lmin:
                            p_l = float(c) / sum_counts_lmin
                            if p_l > 1e-12:
                                ENT += -p_l * math.log2(p_l)
            
            return {
                'RR': RR,
                'DET': DET, 
                'ENT': ENT
            }
            
        except Exception as e:
            print(f"RQA calculation error: {e}")
            # Return default values to avoid crashes
            return {
                'RR': 0.0,
                'DET': 0.0,
                'ENT': 0.0
            }

    def compute_recurrence_matrix(self, emb_data, eps=0.05, metric="1d_abs"):
        """Compute recurrence matrix with proper distance metrics"""
        try:
            M = emb_data.shape[0]
            RP = np.zeros((M, M), dtype=int)
            
            for i in range(M):
                for j in range(M):
                    if metric == "1d_abs":
                        # 1D absolute difference (sum of absolute differences)
                        dist = np.sum(np.abs(emb_data[i] - emb_data[j]))
                    elif metric == "euclidean":
                        # Euclidean distance
                        dist = np.sqrt(np.sum((emb_data[i] - emb_data[j])**2))
                    else:
                        raise ValueError(f"Unsupported distance metric: {metric}")
                    
                    if dist <= eps:
                        RP[i, j] = 1
            
            return RP
            
        except Exception as e:
            print(f"Recurrence matrix computation error: {e}")
            return np.zeros((1, 1), dtype=int)
    
    def compute_rqa_metrics(self, RP, lmin=2):
        """计算RQA指标"""
        N = RP.shape[0]
        sum_ones = RP.sum()
        RR = float(sum_ones / (N * N))  # Recurrence Rate
        
        # 提取对角线长度
        length_dict = self._extract_diagonal_lengths(RP)
        
        denom_all = sum(l * c for l, c in length_dict.items())
        numer_det = sum(l * c for l, c in length_dict.items() if l >= lmin)
        
        DET = float(numer_det / denom_all) if denom_all > 0 else 0.0
        
        # 计算熵
        denom_ent = sum(c for l, c in length_dict.items() if l >= lmin)
        ENT = 0.0
        if denom_ent > 0:
            for l, c in length_dict.items():
                if l >= lmin:
                    p_l = c / denom_ent
                    if p_l > 1e-12:
                        ENT += -p_l * math.log2(p_l)
        
        return {
            "RR": RR,
            "DET": DET,
            "ENT": float(ENT)
        }
    
    def _extract_diagonal_lengths(self, RP):
        """提取对角线长度"""
        N = RP.shape[0]
        length_counts = {}
        
        for d in range(-(N-1), N):
            line_vals = []
            for i in range(N):
                j = i + d
                if 0 <= j < N:
                    line_vals.append(RP[i, j])
            
            idx = 0
            L = len(line_vals)
            while idx < L:
                if line_vals[idx] == 1:
                    seg_len = 1
                    idx2 = idx + 1
                    while idx2 < L and line_vals[idx2] == 1:
                        seg_len += 1
                        idx2 += 1
                    length_counts[seg_len] = length_counts.get(seg_len, 0) + 1
                    idx = idx2
                else:
                    idx += 1
        
        return length_counts
    
    def load_all_events_data(self):
        """
        Load ROI information from All_Events.csv
        """
        try:
            events_file = "data/event_analysis_results/All_Events.csv"
            if not os.path.exists(events_file):
                print(f"All_Events.csv not found: {events_file}")
                return {}
            
            df = pd.read_csv(events_file)
            print(f"Loaded All_Events.csv with {len(df)} records")
            
            # Group events by ADQ_ID for quick lookup
            events_dict = {}
            for _, row in df.iterrows():
                adq_id = row['ADQ_ID']
                if adq_id not in events_dict:
                    events_dict[adq_id] = []
                
                events_dict[adq_id].append({
                    'roi': self.strip_n2_prefix(row['ROI']),
                    'start_idx': int(row['StartIndex']),
                    'end_idx': int(row['EndIndex']),
                    'group': row['Group']
                })
            
            print(f"Processed events for {len(events_dict)} ADQ_IDs")
            return events_dict
            
        except Exception as e:
            print(f"Failed to load All_Events.csv: {e}")
            return {}

    def create_roi_color_mapping_enhanced(self, all_rois):
        """
        Create enhanced ROI color mapping with dark green gradient
        Based on user's optimization suggestions
        """
        try:
            roi_list = sorted(list(all_rois))
            if not roi_list:
                return {}
            
            # ROI priority function - INST highest, then KW, then BG
            def roi_priority(roi_name):
                roi_upper = roi_name.upper()
                if roi_upper.startswith('INST'):
                    return 0  # Highest priority - darkest green
                elif roi_upper.startswith('KW'):
                    return 1  # Medium priority
                elif roi_upper.startswith('BG'):
                    return 2  # Lower priority - lighter green
                else:
                    return 3  # Lowest priority
            
            # Sort ROI list by priority
            roi_list_sorted = sorted(roi_list, key=roi_priority)
            
            # Dark green gradient colors (hex format)
            dark_green_colors = [
                '#0A3A2A',  # Darkest - for INST
                '#0D4F3C',  
                '#156651',  # Medium dark - for KW  
                '#1E7E67',
                '#2A967F',
                '#3AAE98',  # Medium - for BG
                '#4FC7B2',
                '#67DFCC'   # Lightest
            ]
            
            # Convert hex to RGB tuples
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
            
            rgb_colors = [hex_to_rgb(color) for color in dark_green_colors]
            
            # Assign colors based on ROI priority and count
            roi_color_dict = {}
            n_colors = len(rgb_colors)
            n_rois = len(roi_list_sorted)
            
            for i, roi in enumerate(roi_list_sorted):
                if n_rois == 1:
                    color_idx = 2  # Middle green for single ROI
                else:
                    # Distribute colors across the gradient
                    color_idx = int(i * (n_colors - 1) / max(n_rois - 1, 1))
                    color_idx = min(color_idx, n_colors - 1)
                
                roi_color_dict[roi] = rgb_colors[color_idx]
            
            print(f"Created enhanced dark green ROI mapping with {len(roi_color_dict)} ROIs")
            print(f"ROI priorities: {[(roi, roi_priority(roi)) for roi in roi_list_sorted[:5]]}")
            
            return roi_color_dict
            
        except Exception as e:
            print(f"Enhanced ROI color mapping creation failed: {e}")
            return {}

    def create_roi_color_mapping(self, all_rois, color_theme="green_gradient"):
        """
        Fallback method for backward compatibility
        """
        return self.create_roi_color_mapping_enhanced(all_rois)

    def get_roi_events_for_data_id(self, data_id, events_dict):
        """
        Get ROI events for a specific data_id from All_Events.csv data
        """
        # Extract base ADQ_ID from data_id (remove _preprocessed_calibrated suffix)
        adq_id = data_id.replace('_preprocessed_calibrated', '')
        
        if adq_id in events_dict:
            return events_dict[adq_id]
        else:
            print(f"No ROI events found for {adq_id} in All_Events.csv")
            return []

    def prepare_signal_data(self, df, analysis_mode):
        """根据分析模式准备信号数据 - 基于参考代码优化"""
        try:
            if analysis_mode == "1d_x":
                # 使用x坐标作为1D信号（参考代码中的做法）
                signal_data = df['x'].values
                return signal_data, df['timestamp'].values
            elif analysis_mode == "1d_amplitude":
                # 计算幅度 r = sqrt(x^2 + y^2)
                amplitude = np.sqrt(df['x'].values**2 + df['y'].values**2)
                return amplitude, df['timestamp'].values
            elif analysis_mode == "2d_xy":
                # 2D信号使用x,y坐标
                return df[['x', 'y']].values, df['timestamp'].values
            else:
                raise ValueError(f"不支持的分析模式: {analysis_mode}")
        except Exception as e:
            print(f"信号数据准备失败: {e}")
            return None, None

    def plot_amplitude_with_roi_enhanced(self, data_id, signal_data, t_, df, roi_color_dict, 
                                       params, save_path, events_dict):
        """Enhanced amplitude plot - 基本图用原始数据，ROI着色用All_Events.csv"""
        fig = None
        try:
            # Create 1:1 square figure  
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # Process signal based on analysis mode (使用原始数据)
            if params["analysis_mode"] == "1d_amplitude":
                y_signal = signal_data
                ax.set_ylabel('Amplitude', fontsize=16, fontweight='bold')  # 只改字体
                title_suffix = "amplitude"
            elif params["analysis_mode"] == "1d_x":
                y_signal = signal_data
                ax.set_ylabel('X Coordinate', fontsize=16, fontweight='bold')  # 只改字体
                title_suffix = "X Signal"
            else:  # 2d_xy
                # Calculate amplitude for 2D data
                y_signal = np.sqrt(signal_data[:, 0]**2 + signal_data[:, 1]**2)
                ax.set_ylabel('Amplitude', fontsize=16, fontweight='bold')  # 只改字体
                title_suffix = "amplitude"
            
            # Plot main signal line in blue (使用原始数据绘制基本图形)
            ax.plot(t_, y_signal, color='blue', lw=1.2)
            ax.set_title(f"{data_id} {title_suffix}", fontsize=20, fontweight='bold')  # 只改字体
            
            # 恢复原始的ROI着色逻辑（先尝试原始方法，再尝试All_Events.csv）
            roi_added = False
            
            # 首先使用原始的SequenceID方法进行ROI着色（恢复原样）
            if "ROI" in df.columns and "SequenceID" in df.columns:
                seq_vals = df["SequenceID"].unique()
                for sid in sorted(seq_vals):
                    if sid <= 0:
                        continue
                    inds = df.index[df["SequenceID"] == sid].to_numpy()
                    if len(inds) < 2:
                        continue
                    
                    st_i = inds[0]
                    ed_i = inds[-1]
                    if st_i >= len(t_) or ed_i >= len(t_):
                        continue
                        
                    seg_t = t_[st_i : ed_i+1]
                    seg_r = y_signal[st_i : ed_i+1]
                    
                    # Get ROI and clean name
                    roi_raw = df.at[st_i, "ROI"] if "ROI" in df.columns else ""
                    if pd.isna(roi_raw): 
                        roi_raw = "?"
                    roi_ = self.strip_n2_prefix(roi_raw)
                    
                    color_ = roi_color_dict.get(roi_, (0.5, 0.7, 0.5))  # default green
                    
                    # Fill between signal and y=0 (ROI着色，保持原样)
                    ax.fill_between(seg_t, seg_r, 0, color=color_, alpha=0.3)
                    
                    # Add ROI label at beginning of segment (只改字体大小)
                    ax.text(seg_t[0], seg_r[0], f"S{sid}({roi_})",
                            color=color_, fontsize=16, ha="right", va="top",
                            fontweight='bold')
                    roi_added = True
            
            # 如果原始方法没有ROI数据，才尝试All_Events.csv
            if not roi_added:
                roi_events = self.get_roi_events_for_data_id(data_id, events_dict)
                if roi_events:
                    # Add ROI background regions with green fill_between
                    for i, event in enumerate(roi_events):
                        start_idx = event['start_idx']
                        end_idx = event['end_idx']
                        roi_name = event['roi']
                        
                        # Ensure indices are within signal range
                        if start_idx >= len(t_) or end_idx >= len(t_) or start_idx < 0:
                            continue
                        
                        end_idx = min(end_idx, len(t_) - 1)
                        
                        seg_t = t_[start_idx:end_idx+1]
                        seg_r = y_signal[start_idx:end_idx+1]
                        
                        if len(seg_t) > 0:
                            color_ = roi_color_dict.get(roi_name, (0.5, 0.7, 0.5))
                            
                            # Fill between signal and y=0 (ROI着色)
                            ax.fill_between(seg_t, seg_r, 0, color=color_, alpha=0.3)
                            
                            # Add ROI label at beginning of segment (只改字体大小)
                            sequence_id = i + 1
                            ax.text(seg_t[0], seg_r[0], f"S{sequence_id}({roi_name})",
                                    color=color_, fontsize=16, ha="right", va="top",
                                    fontweight='bold')
            
            # Chart styling with English labels - 只改字体大小
            ax.set_xlabel('Time(ms)', fontsize=16, fontweight='bold')
            
            # 加粗轴刻度标签（只改字体）
            ax.tick_params(axis='both', which='major', labelsize=14, labelcolor='black')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontweight('bold')
            
            plt.tight_layout()
            
            # Save image
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            
            return f"data:image/png;base64,{self._fig_to_base64(fig)}"
            
        except Exception as e:
            print(f"Enhanced amplitude plot rendering failed {data_id}: {e}")
            return None
        finally:
            if fig:
                plt.close(fig)
            plt.close('all')
            gc.collect()

    def plot_amplitude_with_roi(self, data_id, signal_data, t_, df, roi_color_dict, params, save_path):
        """
        Fallback method - use enhanced version with empty events_dict
        """
        return self.plot_amplitude_with_roi_enhanced(data_id, signal_data, t_, df, roi_color_dict, 
                                                   params, save_path, {})

    def plot_trajectory_2d(self, data_id, signal_data, df, roi_color_dict, params, save_path):
        """Plot 2D trajectory with ROI coloring (consistent green theme) - 放大文字2倍并加粗"""
        fig = None
        try:
            # Create 1:1 square figure
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # Extract x, y coordinates from 2D signal data
            if signal_data.ndim == 2 and signal_data.shape[1] >= 2:
                x_coords = signal_data[:, 0]
                y_coords = signal_data[:, 1]
            else:
                print(f"Warning: Invalid 2D signal data shape for trajectory plot: {signal_data.shape}")
                return None
            
            # Plot main trajectory line in blue
            ax.plot(x_coords, y_coords, color='blue', lw=1.2, alpha=0.8)
            ax.set_title(f"{data_id} - 2D Trajectory", fontsize=20, fontweight='bold')  # 放大2倍并加粗
            
            # Add ROI scatter points with green coloring (consistent with reference)
            if "ROI" in df.columns and "SequenceID" in df.columns:
                seq_vals = df["SequenceID"].unique()
                for sid in sorted(seq_vals):
                    if sid <= 0:
                        continue
                    inds = df.index[df["SequenceID"] == sid].to_numpy()
                    if len(inds) < 2:
                        continue
                    
                    st_i = inds[0]
                    ed_i = inds[-1]
                    if st_i >= len(x_coords) or ed_i >= len(x_coords):
                        continue
                        
                    seg_x = x_coords[st_i : ed_i+1]
                    seg_y = y_coords[st_i : ed_i+1]
                    
                    # Get ROI and clean name
                    roi_raw = df.at[st_i, "ROI"] if "ROI" in df.columns else ""
                    if pd.isna(roi_raw): 
                        roi_raw = "?"
                    roi_ = self.strip_n2_prefix(roi_raw)
                    
                    color_ = roi_color_dict.get(roi_, (0.5, 0.7, 0.5))  # default green
                    
                    # Scatter plot for ROI segments (green points)
                    ax.scatter(seg_x, seg_y, color=color_, alpha=0.7, s=20)
                    
                    # Add ROI label at beginning of segment
                    ax.text(seg_x[0], seg_y[0], f"S{sid}({roi_})",
                            color=color_, fontsize=16, ha="left", va="bottom",  # 放大2倍并加粗
                            fontweight='bold')
            
            # Mark start and end points
            ax.scatter(x_coords[0], y_coords[0], color='darkgreen', s=80, marker='o', 
                      label='Start', zorder=5)
            ax.scatter(x_coords[-1], y_coords[-1], color='darkred', s=80, marker='s', 
                      label='End', zorder=5)
            
            # Chart styling with English labels - 放大并加粗
            ax.set_xlabel('X Coordinate', fontsize=16, fontweight='bold')  # 放大2倍并加粗
            ax.set_ylabel('Y Coordinate', fontsize=16, fontweight='bold')  # 放大2倍并加粗
            ax.legend(fontsize=14, frameon=True, fancybox=True, shadow=True, loc='best')  # 放大图例
            
            # 加粗轴刻度标签
            ax.tick_params(axis='both', which='major', labelsize=14, labelcolor='black')  # 放大刻度标签
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontweight('bold')
            
            ax.set_aspect('equal')  # Keep 1:1 aspect ratio
            plt.tight_layout()
            
            # Save image
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            
            return f"data:image/png;base64,{self._fig_to_base64(fig)}"
            
        except Exception as e:
            print(f"Trajectory plot rendering failed {data_id}: {e}")
            return None
        finally:
            if fig:
                plt.close(fig)
            plt.close('all')
            gc.collect()

    def add_roi_background_to_plot(self, ax, df, roi_color_dict, t_, y_signal):
        """Add ROI background regions with green fill_between style (for compatibility)"""
        try:
            # This method is kept for compatibility but main logic moved to plot_amplitude_with_roi
            pass
        except Exception as e:
            print(f"ROI background rendering failed: {e}")

    def add_roi_scatter_to_plot(self, ax, df, roi_color_dict, x_coords, y_coords):
        """Add ROI scatter coloring for trajectory plots (compatibility method)"""
        try:
            # This method is kept for compatibility but main logic moved to plot_trajectory_2d
            pass
        except Exception as e:
            print(f"ROI scatter rendering failed: {e}")
    
    def plot_recurrence_plot_enhanced(self, data_id, RP, df, roi_color_dict, rqa_metrics,
                                    params, save_path, events_dict):
        """Enhanced recurrence plot - 基本图用原始数据，ROI着色用All_Events.csv - 放大文字2倍并加粗"""
        try:
            # Create 1:1 square figure
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            
            # Plot recurrence matrix in black/white (使用原始数据的RP矩阵)
            ax.imshow(RP, cmap='binary', origin='lower', aspect='equal')
            ax.set_title(f"{data_id} - Recurrence Plot", fontsize=20, fontweight='bold')  # 放大2倍并加粗
            ax.set_xlabel("Index(Embedded)", fontsize=16, fontweight='bold')  # 放大2倍并加粗
            ax.set_ylabel("Index(Embedded)", fontsize=16, fontweight='bold')  # 放大2倍并加粗
            
            # 叠加ROI着色和标记（使用All_Events.csv）
            roi_events = self.get_roi_events_for_data_id(data_id, events_dict)
            M = RP.shape[0]
            
            if roi_events:
                # Add green ROI rectangles on diagonal (基于All_Events.csv)
                for i, event in enumerate(roi_events):
                    start_idx = event['start_idx']
                    end_idx = event['end_idx']
                    roi_name = event['roi']
                    
                    # Ensure indices are within RP matrix range
                    if start_idx >= M or start_idx < 0:
                        continue
                    if end_idx >= M:
                        end_idx = M - 1
                    
                    w = end_idx - start_idx + 1
                    if w < 1:
                        continue
                    
                    color_ = roi_color_dict.get(roi_name, (0.5, 0.7, 0.5))
                    
                    # Add semi-transparent green rectangle on diagonal (ROI着色)
                    rect = Rectangle((start_idx, start_idx), w, w,
                                   fill=True, alpha=0.3, color=color_, lw=1)
                    ax.add_patch(rect)
                    
                    # Add ROI label in center (ROI标记)
                    cx = start_idx + w/2
                    cy = start_idx + w/2
                    sequence_id = i + 1
                    ax.text(cx, cy, f"S{sequence_id}({roi_name})", color='black', fontsize=16,  # 放大2倍并加粗
                           ha="center", va="center", fontweight='bold')
            else:
                # 如果没有All_Events.csv数据，使用原始方法进行ROI着色
                if "SequenceID" in df.columns and "ROI" in df.columns:
                    seq_vals = df["SequenceID"].unique()
                    
                    for sid in sorted(seq_vals):
                        if sid <= 0:
                            continue
                        inds = df.index[df["SequenceID"] == sid].to_numpy()
                        if len(inds) < 2:
                            continue
                        
                        st_i = inds[0]
                        ed_i = inds[-1]
                        if st_i >= M:
                            continue
                        if ed_i >= M:
                            ed_i = M - 1
                        
                        w = ed_i - st_i + 1
                        if w < 1:
                            continue
                        
                        # Get ROI and clean name
                        roi_raw = df.at[st_i, "ROI"] if not pd.isna(df.at[st_i, "ROI"]) else "?"
                        roi_ = self.strip_n2_prefix(roi_raw)
                        color_ = roi_color_dict.get(roi_, (0.5, 0.7, 0.5))  # default green
                        
                        # Add semi-transparent green rectangle (ROI着色)
                        rect = Rectangle((st_i, st_i), w, w,
                                        fill=True, alpha=0.3, color=color_, lw=1)
                        ax.add_patch(rect)
                        
                        # Add ROI label in center (ROI标记)
                        cx = st_i + w/2
                        cy = st_i + w/2
                        ax.text(cx, cy, f"S{sid}({roi_})", color='black', fontsize=16,  # 放大2倍并加粗
                               ha="center", va="center", fontweight='bold')
            
            # Add RQA metrics in top-left corner - 放大并加粗
            metrics_text = f"RR={rqa_metrics['RR']:.2f}\nDET={rqa_metrics['DET']:.2f}\nENT={rqa_metrics['ENT']:.2f}"
            ax.text(0.05, 0.95, metrics_text, transform=ax.transAxes,
                   fontsize=14, va="top", ha="left", fontweight='bold',  # 放大2倍并加粗
                   bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.8))
            
            # 加粗轴刻度标签
            ax.tick_params(axis='both', which='major', labelsize=14, labelcolor='black')  # 放大刻度标签
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontweight('bold')
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            base64_data = self._fig_to_base64(fig)
            plt.close(fig)
            
            return base64_data
        except Exception as e:
            print(f"Enhanced recurrence plot rendering failed {data_id}: {e}")
            return None
        finally:
            plt.close('all')
            gc.collect()
    
    def plot_recurrence_plot(self, data_id, RP, df, roi_color_dict, rqa_metrics, params, save_path):
        """
        Fallback method - use enhanced version with empty events_dict
        """
        return self.plot_recurrence_plot_enhanced(data_id, RP, df, roi_color_dict, rqa_metrics,
                                                params, save_path, {})

    def plot_combined_rqa(self, data_id, signal_data, t_, df, emb_data, RP, 
                         rqa_metrics, roi_color_dict, params, save_path):
        """绘制组合的RQA图（时间序列+递归图）"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 左侧：时间序列图
            self._plot_time_series(ax1, signal_data, t_, df, roi_color_dict, 
                                  data_id, params["analysis_mode"])
            
            # 右侧：递归图
            self._plot_recurrence_plot(ax2, RP, df, roi_color_dict, data_id, params)
            
            # 添加RQA指标文本
            metrics_text = f"RR={rqa_metrics['RR']:.3f}\nDET={rqa_metrics['DET']:.3f}\nENT={rqa_metrics['ENT']:.3f}"
            ax1.text(0.02, 0.98, metrics_text, transform=ax1.transAxes,
                    fontsize=9, va="top", ha="left",
                    bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            base64_data = self._fig_to_base64(fig)
            plt.close(fig)
            
            return base64_data
        except Exception as e:
            print(f"绘制组合图失败 {data_id}: {e}")
            return None
        finally:
            plt.close('all')
            gc.collect()
    
    def _plot_time_series(self, ax, signal_data, t_, df, roi_color_dict, 
                         data_id, analysis_mode):
        """绘制时间序列图"""
        if analysis_mode == "2d_xy":
            # 对于2D数据，绘制轨迹
            x_, y_ = signal_data
            ax.plot(x_, y_, color='blue', lw=1.0, alpha=0.7)
            ax.set_xlabel("X coordinate")
            ax.set_ylabel("Y coordinate")
            ax.set_title(f"{data_id} - 2D Trajectory")
        else:
            # 对于1D数据，绘制时间序列
            r_ = signal_data
            ax.plot(t_, r_, color='blue', lw=1.2)
            
            # 添加ROI分段着色
            if "SequenceID" in df.columns and "ROI" in df.columns:
                seq_vals = df["SequenceID"].unique()
                for sid in sorted(seq_vals):
                    if sid <= 0:
                        continue
                    inds = df.index[df["SequenceID"] == sid].to_numpy()
                    if len(inds) < 2:
                        continue
                    
                    st_i = inds[0]
                    ed_i = inds[-1]
                    if st_i >= len(t_) or ed_i >= len(t_):
                        continue
                    
                    seg_t = t_[st_i:ed_i+1]
                    seg_r = r_[st_i:ed_i+1]
                    
                    roi_raw = df.at[st_i, "ROI"] if not pd.isna(df.at[st_i, "ROI"]) else "?"
                    roi_ = self.strip_n2_prefix(roi_raw)
                    color_ = roi_color_dict.get(roi_, "gray")
                    
                    ax.fill_between(seg_t, seg_r, 0, color=color_, alpha=0.3)
            
            ax.set_xlabel("Time (ms)")
            signal_label = "X coordinate" if analysis_mode == "1d_x" else "Amplitude"
            ax.set_ylabel(signal_label)
            ax.set_title(f"{data_id} - {signal_label}")
    
    def _plot_recurrence_plot(self, ax, RP, df, roi_color_dict, data_id, params):
        """绘制递归图"""
        ax.imshow(RP, cmap='binary', origin='lower')
        ax.set_title(f"{data_id} - Recurrence Plot")
        ax.set_xlabel("Time Index")
        ax.set_ylabel("Time Index")
        
        # 添加ROI矩形框
        if "SequenceID" in df.columns and "ROI" in df.columns:
            M = RP.shape[0]
            seq_vals = df["SequenceID"].unique()
            
            for sid in sorted(seq_vals):
                if sid <= 0:
                    continue
                inds = df.index[df["SequenceID"] == sid].to_numpy()
                if len(inds) < 2:
                    continue
                
                st_i = inds[0]
                ed_i = inds[-1]
                if st_i >= M:
                    continue
                if ed_i >= M:
                    ed_i = M - 1
                
                w = ed_i - st_i + 1
                if w < 1:
                    continue
                
                roi_raw = df.at[st_i, "ROI"] if not pd.isna(df.at[st_i, "ROI"]) else "?"
                roi_ = self.strip_n2_prefix(roi_raw)
                color_ = roi_color_dict.get(roi_, "gray")
                
                rect = Rectangle((st_i, st_i), w, w,
                               fill=True, alpha=0.3, color=color_, lw=1)
                ax.add_patch(rect)
    
    def _fig_to_base64(self, fig):
        """将matplotlib图形转换为base64字符串"""
        try:
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            print(f"转换图形为base64失败: {e}")
            return None
    
    def batch_render_all_groups(self, params=None, color_theme="green_gradient", progress_callback=None):
        """批量渲染所有组的RQA图"""
        
        # 使用默认参数
        if params is None:
            params = self.default_params.copy()
        
        results = {}
        processed_files = 0
        
        try:
            # 查找所有校准后的数据文件
            data_files_info = self.find_calibrated_data_files()
            total_files = len(data_files_info) * 3  # 每个CSV生成3张图
            
            print(f"开始批量渲染，总共 {len(data_files_info)} 个文件，预期生成 {total_files} 张图片")
            
            if progress_callback:
                progress_callback(0, f"开始处理 {len(data_files_info)} 个数据文件")
            
            # 收集所有ROI用于颜色映射
            all_rois = set()
            for file_info in data_files_info:
                try:
                    df = self.load_and_validate_data(file_info['file_path'])
                    if df is not None and "ROI" in df.columns:
                        rois = df["ROI"].dropna().apply(self.strip_n2_prefix).unique()
                        all_rois.update(rois)
                    del df  # 立即释放内存
                except Exception as e:
                    print(f"读取文件出错 {file_info['file_path']}: {e}")
            
            # 创建ROI颜色映射
            roi_color_dict = self.create_roi_color_mapping_enhanced(all_rois)
            
            # 加载All_Events.csv数据
            events_dict = self.load_all_events_data()
            
            # 获取参数目录
            results_dir = self.get_results_directory(params, color_theme)
            os.makedirs(results_dir, exist_ok=True)
            
            # 分批处理文件
            for i, file_info in enumerate(data_files_info):
                try:
                    if file_info['group'] not in results:
                        results[file_info['group']] = {}
                    
                    # 解析数据ID
                    data_id = file_info['data_id']
                    q_idx = file_info['question']
                    
                    if q_idx is None:
                        continue
                    
                    print(f"处理文件 {i+1}/{len(data_files_info)}: {data_id}")
                    
                    # 加载和验证数据
                    df = self.load_and_validate_data(file_info['file_path'])
                    if df is None:
                        processed_files += 3  # 计数但跳过
                        continue
                    
                    # 准备信号数据
                    signal_data, t_ = self.prepare_signal_data(df, params["analysis_mode"])
                    if signal_data is None:
                        processed_files += 3
                        continue
                    
                    # 信号嵌入
                    if params["analysis_mode"] == "2d_xy":
                        emb_data = self.embed_signal(signal_data, 
                                                   params["embedding_dimension"],
                                                   params["time_delay"], "2d")
                    else:
                        emb_data = self.embed_signal(signal_data,
                                                   params["embedding_dimension"],
                                                   params["time_delay"], "1d")
                    
                                        # 计算递归矩阵
                    RP = self.compute_recurrence_matrix(emb_data, params["recurrence_threshold"], params["distance_metric"])
                    
                    # 计算RQA指标
                    rqa_metrics = self.compute_rqa_measures(RP, params["min_line_length"])
                    
                    # 保存路径 - 使用新的参数化目录结构
                    save_dir = os.path.join(results_dir, file_info['group'], f"q{q_idx}")
                    os.makedirs(save_dir, exist_ok=True)
                    
                    amplitude_path = os.path.join(save_dir, f"{data_id}_amplitude.png")
                    trajectory_path = os.path.join(save_dir, f"{data_id}_trajectory.png") 
                    recurrence_path = os.path.join(save_dir, f"{data_id}_recurrence.png")
                    
                    # 绘制并保存三张图
                    amplitude_base64 = self.plot_amplitude_with_roi_enhanced(data_id, signal_data, t_, df,
                                                                  roi_color_dict, params, amplitude_path, events_dict)
                    trajectory_base64 = self.plot_trajectory_2d(data_id, signal_data, df,
                                                              roi_color_dict, params, trajectory_path)
                    recurrence_base64 = self.plot_recurrence_plot_enhanced(data_id, RP, df, roi_color_dict,
                                                                 rqa_metrics, params, recurrence_path, events_dict)
                    
                    # 存储结果
                    if f"q{q_idx}" not in results[file_info['group']]:
                        results[file_info['group']][f"q{q_idx}"] = []
                    
                    # 计算相对路径用于API访问
                    rel_amplitude = os.path.relpath(amplitude_path, self.rqa_results_dir)
                    rel_trajectory = os.path.relpath(trajectory_path, self.rqa_results_dir)
                    rel_recurrence = os.path.relpath(recurrence_path, self.rqa_results_dir)
                    
                    results[file_info['group']][f"q{q_idx}"].append({
                        "data_id": data_id,
                        "amplitude_path": rel_amplitude.replace('\\', '/'),
                        "trajectory_path": rel_trajectory.replace('\\', '/'),
                        "recurrence_path": rel_recurrence.replace('\\', '/'),
                        "relative_path": rel_amplitude.replace('\\', '/'),  # 兼容性
                        "rqa_metrics": rqa_metrics,
                        # 添加渲染参数信息
                        "render_params": params,
                        "color_theme": color_theme,
                        "param_signature": self.get_param_signature(params, color_theme)
                    })
                    
                    # 更新进度
                    processed_files += 3
                    progress = (processed_files / total_files) * 100
                    
                    if progress_callback:
                        progress_callback(progress, f"已处理 {data_id}")
                    
                    # 释放内存
                    del df, signal_data, emb_data, RP
                    
                    # 每处理一定数量的文件后进行垃圾回收
                    if (i + 1) % self.batch_size == 0:
                        plt.close('all')
                        gc.collect()
                        time.sleep(0.1)  # 短暂暂停让系统回收内存
                        
                        if progress_callback:
                            progress_callback(progress, f"内存清理完成，继续处理...")
                
                except Exception as e:
                    print(f"处理文件出错 {file_info['file_path']}: {e}")
                    processed_files += 3  # 仍然计数，避免进度卡住
                    continue
            
            # 保存渲染结果索引
            self._save_render_results(results, params, color_theme)
            
            if progress_callback:
                progress_callback(100, f"批量渲染完成！共生成 {processed_files} 张图片")
            
            print(f"批量渲染完成！共处理 {len(data_files_info)} 个文件，生成 {processed_files} 张图片")
            
            return {
                "success": True, 
                "message": f"成功渲染 {processed_files} 张图片", 
                "results": results,
                "param_signature": self.get_param_signature(params, color_theme)
            }
            
        except Exception as e:
            error_msg = f"批量渲染失败: {str(e)}"
            print(error_msg)
            if progress_callback:
                progress_callback(0, error_msg)
            return {"success": False, "message": error_msg}
        finally:
            # 最终清理
            plt.close('all')
            gc.collect()

    def _save_render_results(self, results, params, color_theme):
        """Save render results index with English labels"""
        try:
            param_signature = self.get_param_signature(params, color_theme)
            results_dir = self.get_results_directory(params, color_theme)
            
            index_file = os.path.join(results_dir, "render_index.json")
            
            # Calculate summary statistics
            total_files = 0
            for group_data in results.values():
                for question_data in group_data.values():
                    total_files += len(question_data)
            
            index_data = {
                "params": params,
                "color_theme": color_theme,
                "param_signature": param_signature,
                "render_time": datetime.now().isoformat(),
                "params_display": {
                    "analysis_mode_display": {
                        "1d_x": "1D Signal (X Coordinate)",
                        "1d_amplitude": "1D Signal (Amplitude)", 
                        "2d_xy": "2D Signal (X,Y Coordinates)"
                    }.get(params['analysis_mode'], params['analysis_mode']),
                    "distance_metric_display": {
                        "1d_abs": "1D Absolute Difference",
                        "euclidean": "Euclidean Distance"
                    }.get(params['distance_metric'], params['distance_metric']),
                    "color_theme_display": {
                        "grayscale": "Grayscale Theme",
                        "green_gradient": "Green Gradient"
                    }.get(color_theme, color_theme)
                },
                "results_summary": {
                    "total_files": total_files,
                    "groups": ["control", "mci", "ad"],
                    "questions": ["q1", "q2", "q3", "q4", "q5"],
                    **results
                }
            }
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            print(f"Render index saved: {index_file}")
            
        except Exception as e:
            print(f"Failed to save render index: {e}")
    
    def get_rendered_results(self, group_type=None, question=None, param_signature=None):
        """获取已渲染的结果 - 支持参数化筛选"""
        results = []
        
        try:
            # 如果指定了参数签名，只查找对应的目录
            if param_signature:
                search_dirs = [os.path.join(self.rqa_results_dir, param_signature)]
            else:
                # 查找所有参数目录
                search_dirs = []
                for item in os.listdir(self.rqa_results_dir):
                    item_path = os.path.join(self.rqa_results_dir, item)
                    if os.path.isdir(item_path) and item.startswith('mode_'):
                        search_dirs.append(item_path)
            
            for param_dir in search_dirs:
                if not os.path.exists(param_dir):
                    continue
                
                # 读取参数信息
                index_file = os.path.join(param_dir, "render_index.json")
                index_data = {}
                if os.path.exists(index_file):
                    try:
                        with open(index_file, 'r', encoding='utf-8') as f:
                            index_data = json.load(f)
                    except Exception as e:
                        print(f"读取索引文件失败 {index_file}: {e}")
                
                # 遍历组目录
                for group in ["control", "mci", "ad"]:
                    if group_type and group != group_type:
                        continue
                    
                    group_dir = os.path.join(param_dir, group)
                    if not os.path.exists(group_dir):
                        continue
                    
                    # 遍历问题目录 
                    for q_idx in range(1, 6):
                        if question and q_idx != question:
                            continue
                        
                        q_dir = os.path.join(group_dir, f"q{q_idx}")
                        if not os.path.exists(q_dir):
                            continue
                        
                        # 查找图片文件
                        for file in os.listdir(q_dir):
                            if file.endswith('_amplitude.png'):
                                data_id = file.replace('_amplitude.png', '')
                                
                                # 检查是否有完整的三张图
                                amplitude_file = os.path.join(q_dir, f"{data_id}_amplitude.png")
                                trajectory_file = os.path.join(q_dir, f"{data_id}_trajectory.png")
                                recurrence_file = os.path.join(q_dir, f"{data_id}_recurrence.png")
                                
                                if (os.path.exists(amplitude_file) and 
                                    os.path.exists(trajectory_file) and 
                                    os.path.exists(recurrence_file)):
                                    
                                    # 计算相对路径
                                    rel_param_dir = os.path.relpath(param_dir, self.rqa_results_dir)
                                    amplitude_path = f"{rel_param_dir}/{group}/q{q_idx}/{data_id}_amplitude.png".replace('\\', '/')
                                    trajectory_path = f"{rel_param_dir}/{group}/q{q_idx}/{data_id}_trajectory.png".replace('\\', '/')
                                    recurrence_path = f"{rel_param_dir}/{group}/q{q_idx}/{data_id}_recurrence.png".replace('\\', '/')
                                    
                                    results.append({
                                        "group": group,
                                        "question": q_idx,
                                        "data_id": data_id,
                                        "amplitude_path": amplitude_path,
                                        "trajectory_path": trajectory_path,
                                        "recurrence_path": recurrence_path,
                                        "relative_path": amplitude_path,  # 兼容性
                                        # 添加渲染参数信息
                                        "render_params": index_data.get("params", {}),
                                        "render_params_display": index_data.get("params_display", {}),
                                        "param_signature": index_data.get("param_signature", ""),
                                        "render_time": index_data.get("render_time", ""),
                                        "color_theme": index_data.get("color_theme", "")
                                    })
            
            print(f"找到 {len(results)} 个渲染结果")
            return results
            
        except Exception as e:
            print(f"获取渲染结果失败: {e}")
            return []


def create_rqa_batch_renderer(data_root="data"):
    """创建RQA批量渲染器实例"""
    return RQABatchRenderer(data_root)


if __name__ == "__main__":
    # 测试
    renderer = create_rqa_batch_renderer()
    
    def progress_callback(progress, message):
        print(f"进度: {progress:.1f}% - {message}")
    
    # 批量渲染
    results = renderer.batch_render_all_groups(
        color_theme="green_gradient",
        progress_callback=progress_callback
    )
    
    print(f"渲染完成: {results['processed_files']}/{results['total_files']} 个文件") 