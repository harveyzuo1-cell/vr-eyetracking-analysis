#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RQA分析流程API模块
完整的眼动数据递归量化分析流程，从数据处理到统计分析再到可视化
"""

import os
import math
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
from datetime import datetime
from flask import Blueprint, request, jsonify
import traceback

# 创建蓝图
rqa_pipeline_bp = Blueprint('rqa_pipeline', __name__)

# 全局配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 基础数据目录
BASE_DATA_DIR = 'data'
PIPELINE_RESULTS_DIR = os.path.join(BASE_DATA_DIR, 'rqa_pipeline_results')

# 确保目录存在
os.makedirs(PIPELINE_RESULTS_DIR, exist_ok=True)


###############################################################################
# 参数管理和目录结构
###############################################################################

def generate_param_signature(params):
    """生成参数签名"""
    m = params.get('m', 2)
    tau = params.get('tau', params.get('delay', 1))  # 兼容delay和tau
    eps = params.get('eps', 0.05)
    lmin = params.get('lmin', 2)
    return f"m{m}_tau{tau}_eps{eps}_lmin{lmin}"


def get_param_directory(params):
    """获取参数对应的目录路径"""
    signature = generate_param_signature(params)
    return os.path.join(PIPELINE_RESULTS_DIR, signature)


def get_step_directory(params, step_name):
    """获取特定步骤的目录路径"""
    param_dir = get_param_directory(params)
    step_dir = os.path.join(param_dir, step_name)
    os.makedirs(step_dir, exist_ok=True)
    return step_dir


def save_param_metadata(params, step_completed):
    """保存参数元数据"""
    param_dir = get_param_directory(params)
    os.makedirs(param_dir, exist_ok=True)
    
    metadata_file = os.path.join(param_dir, 'metadata.json')
    
    # 读取现有元数据
    metadata = {}
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except:
            pass
    
    # 更新元数据
    metadata.update({
        'signature': generate_param_signature(params),
        'parameters': params,
        'last_updated': datetime.now().isoformat(),
        f'step_{step_completed}_completed': True
    })
    
    # 保存元数据
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def get_param_history():
    """获取所有参数历史记录"""
    history = []
    
    if not os.path.exists(PIPELINE_RESULTS_DIR):
        return history
    
    for param_folder in os.listdir(PIPELINE_RESULTS_DIR):
        param_path = os.path.join(PIPELINE_RESULTS_DIR, param_folder)
        if os.path.isdir(param_path):
            metadata_file = os.path.join(param_path, 'metadata.json')
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # 计算完成步骤数
                    completed_steps = sum(1 for i in range(1, 6) 
                                        if metadata.get(f'step_{i}_completed', False))
                    
                    history.append({
                        'signature': metadata.get('signature', param_folder),
                        'params': metadata.get('parameters', {}),
                        'completed_steps': completed_steps,
                        'progress': (completed_steps / 5) * 100,
                        'last_updated': metadata.get('last_updated', '')
                    })
                except:
                    # 如果元数据损坏，尝试解析文件夹名
                    try:
                        # 解析文件夹名: m2_tau1_eps0.05_lmin2
                        parts = param_folder.split('_')
                        params = {}
                        for part in parts:
                            if part.startswith('m'):
                                params['m'] = int(part[1:])
                            elif part.startswith('tau'):
                                params['tau'] = int(part[3:])
                            elif part.startswith('eps'):
                                params['eps'] = float(part[3:])
                            elif part.startswith('lmin'):
                                params['lmin'] = int(part[4:])
                        
                        # 检查完成的步骤
                        step_dirs = ['step1_rqa_calculation', 'step2_data_merging', 
                                   'step3_feature_enrichment', 'step4_statistical_analysis', 
                                   'step5_visualization']
                        completed_steps = sum(1 for step_dir in step_dirs 
                                            if os.path.exists(os.path.join(param_path, step_dir)))
                        
                        history.append({
                            'signature': param_folder,
                            'params': params,
                            'completed_steps': completed_steps,
                            'progress': (completed_steps / 5) * 100,
                            'last_updated': ''
                        })
                    except:
                        pass
    
    # 按最后更新时间排序
    history.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
    return history


###############################################################################
# RQA计算模块 - 核心算法实现
###############################################################################

def load_xy_time_series(csv_path):
    """
    读取 CSV（需包含 'x','y' 列；可带 'milliseconds','ROI','SequenceID' 等），
    返回: x_, y_, t_, df
    """
    df = pd.read_csv(csv_path)
    if 'x' not in df.columns or 'y' not in df.columns:
        raise ValueError(f"{csv_path} 缺少 x 或 y 列!")
    
    x_ = df['x'].to_numpy()
    y_ = df['y'].to_numpy()
    if 'milliseconds' in df.columns:
        t_ = df['milliseconds'].to_numpy()
    else:
        t_ = np.arange(len(x_))
    return x_, y_, t_, df


def embed_seq_1d(x_, m=2, delay=1):
    """1D: 只用 x 序列 => shape=(N-(m-1)*delay, m)"""
    N = len(x_)
    rows = N - (m-1)*delay
    if rows <= 0:
        return np.empty((0, m))
    emb = []
    for i in range(rows):
        emb.append([x_[i+k*delay] for k in range(m)])
    return np.array(emb)


def embed_seq_2d(x_, y_, m=2, delay=1):
    """2D: 用 (x,y)，shape=(N-(m-1)*delay, 2*m)"""
    N = len(x_)
    if len(y_) != N:
        raise ValueError("x_ 和 y_ 长度不匹配!")
    rows = N - (m-1)*delay
    if rows <= 0:
        return np.empty((0, 2*m))
    emb = np.zeros((rows, 2*m), dtype=float)
    for i in range(rows):
        for k in range(m):
            emb[i, 2*k] = x_[i + k*delay]
            emb[i, 2*k+1] = y_[i + k*delay]
    return emb


def compute_rp_1dabs(emb_data, eps=0.05):
    """当只用 1D embedding 时，用绝对差之和 ≤ eps => 1"""
    M = emb_data.shape[0]
    m = emb_data.shape[1]
    RP = np.zeros((M, M), dtype=int)
    for i in range(M):
        for j in range(M):
            dist = sum(abs(emb_data[i, k] - emb_data[j, k]) for k in range(m))
            if dist <= eps:
                RP[i, j] = 1
    return RP


def compute_rp_euclid(emb_data, eps=0.05):
    """对 2D embedding 用欧几里得距离 ≤ eps => 1"""
    M = emb_data.shape[0]
    RP = np.zeros((M, M), dtype=int)
    for i in range(M):
        for j in range(M):
            dist = math.sqrt(np.sum((emb_data[i]-emb_data[j])**2))
            if dist <= eps:
                RP[i, j] = 1
    return RP


def extract_diag_lengths(RP):
    """统计对角线中 '1' 的连续段 => {长度:出现次数}"""
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


def compute_rqa_measures(RP, lmin=2):
    """返回 RR, DET, ENT"""
    N = RP.shape[0]
    sum_ones = RP.sum()
    RR = sum_ones/(N*N)
    
    length_dict = extract_diag_lengths(RP)
    denom_all = 0
    for l, c_ in length_dict.items():
        denom_all += l*c_
    
    numer_det = 0
    denom_ent = 0
    for l, c_ in length_dict.items():
        if l >= lmin:
            numer_det += l*c_
            denom_ent += c_
    
    DET = numer_det/denom_all if denom_all > 0 else 0
    
    ENT = 0
    if denom_ent > 0:
        sum_counts_lmin = sum(c_ for (ll, c_) in length_dict.items() if ll >= lmin)
        for l, c_ in length_dict.items():
            if l >= lmin:
                p_l = c_ / sum_counts_lmin
                if p_l > 1e-12:
                    ENT += - p_l * math.log2(p_l)
    return RR, DET, ENT


def process_single_rqa_file(csv_path, m=2, delay=1, eps=0.05, lmin=2):
    """处理单个文件的RQA计算"""
    try:
        x_, y_, t_, df = load_xy_time_series(csv_path)
        
        if len(x_) < 5:
            return None
        
        # 提取文件名中的folder和q信息
        filename = os.path.basename(csv_path)
        # 假设文件名格式: n3q1_preprocessed_calibrated.csv
        parts = filename.replace('_preprocessed_calibrated.csv', '').replace('.csv', '')
        
        result = {
            "filename": filename,
            "folder": None,
            "q": None,
            "RR-2D-xy": np.nan,
            "RR-1D-x": np.nan,
            "DET-2D-xy": np.nan,
            "DET-1D-x": np.nan,
            "ENT-2D-xy": np.nan,
            "ENT-1D-x": np.nan,
        }
        
        # 解析folder和q
        if parts.startswith('n') and 'q' in parts:
            # Control组: n3q1 -> folder=3, q=1
            folder_q = parts[1:]  # 去掉'n'
            if 'q' in folder_q:
                folder_str, q_str = folder_q.split('q')
                try:
                    result["folder"] = int(folder_str)
                    result["q"] = int(q_str)
                except:
                    pass
        elif parts.startswith('m') and 'q' in parts:
            # MCI组: m1q1 -> folder=1, q=1
            folder_q = parts[1:]  # 去掉'm'
            if 'q' in folder_q:
                folder_str, q_str = folder_q.split('q')
                try:
                    result["folder"] = int(folder_str)
                    result["q"] = int(q_str)
                except:
                    pass
        elif parts.startswith('ad') and 'q' in parts:
            # AD组: ad1q1 -> folder=1, q=1
            folder_q = parts[2:]  # 去掉'ad'
            if 'q' in folder_q:
                folder_str, q_str = folder_q.split('q')
                try:
                    result["folder"] = int(folder_str)
                    result["q"] = int(q_str)
                except:
                    pass
        
        # 2D-xy分析
        emb_2d = embed_seq_2d(x_, y_, m=m, delay=delay)
        if emb_2d.shape[0] >= 2:
            RP_2d = compute_rp_euclid(emb_2d, eps=eps)
            rr2d, det2d, ent2d = compute_rqa_measures(RP_2d, lmin=lmin)
            result["RR-2D-xy"] = rr2d
            result["DET-2D-xy"] = det2d
            result["ENT-2D-xy"] = ent2d
        
        # 1D-x分析
        emb_1d = embed_seq_1d(x_, m=m, delay=delay)
        if emb_1d.shape[0] >= 2:
            RP_1d = compute_rp_1dabs(emb_1d, eps=eps)
            rr1d, det1d, ent1d = compute_rqa_measures(RP_1d, lmin=lmin)
            result["RR-1D-x"] = rr1d
            result["DET-1D-x"] = det1d
            result["ENT-1D-x"] = ent1d
        
        return result
        
    except Exception as e:
        print(f"处理文件 {csv_path} 出错: {e}")
        return None


###############################################################################
# 数据处理函数
###############################################################################

def merge_group_data(control_csv, mci_csv, ad_csv=None):
    """合并三组数据"""
    try:
        all_data_list = []
        
        # 读取Control组
        if os.path.exists(control_csv):
            ctg = pd.read_csv(control_csv)
            ctg["Group"] = "Control"
            ctg["ID"] = ctg.apply(lambda row: f"n{row['folder']}q{row['q']}", axis=1)
            all_data_list.append(ctg)
        
        # 读取MCI组
        if os.path.exists(mci_csv):
            mci = pd.read_csv(mci_csv)
            mci["Group"] = "MCI"
            mci["ID"] = mci.apply(lambda row: f"m{row['folder']}q{row['q']}", axis=1)
            all_data_list.append(mci)
        
        # 读取AD组（如果提供）
        if ad_csv and os.path.exists(ad_csv):
            ad = pd.read_csv(ad_csv)
            ad["Group"] = "AD"
            ad["ID"] = ad.apply(lambda row: f"ad{row['folder']}q{row['q']}", axis=1)
            all_data_list.append(ad)
        
        if not all_data_list:
            raise ValueError("没有找到有效的数据文件")
        
        # 合并数据
        all_data = pd.concat(all_data_list, ignore_index=True)
        
        # 调整列顺序
        cols = [
            "ID", "Group", "folder", "q",
            "RR-2D-xy", "RR-1D-x", "DET-2D-xy", "DET-1D-x", "ENT-2D-xy", "ENT-1D-x"
        ]
        all_data = all_data[cols]
        
        return all_data
        
    except Exception as e:
        print(f"合并数据出错: {e}")
        raise


def build_event_aggregates(events_csv_path):
    """构造事件级聚合"""
    if not os.path.exists(events_csv_path):
        return pd.DataFrame()

    df_evt = pd.read_csv(events_csv_path)
    df_evt["EventType"] = df_evt["EventType"].astype(str).str.lower().str.strip()
    df_evt["ADQ_ID"] = df_evt["ADQ_ID"].astype(str)
    
    # 处理可能存在的列名，兼容不同的数据格式
    available_cols = df_evt.columns.tolist()
    
    # 映射列名（处理不同的命名约定）
    col_mapping = {
        'Duration_ms': ['Duration_ms', 'duration_ms', 'Duration'],
        'Amplitude': ['Amplitude_deg', 'SaccadeAmplitude', 'amplitude', 'Amplitude'],
        'MaxVel': ['MaxVel', 'SaccadeMaxVel', 'max_vel', 'MaxVelocity']
    }
    
    # 找到实际存在的列名
    actual_cols = {}
    for key, possible_names in col_mapping.items():
        for name in possible_names:
            if name in available_cols:
                actual_cols[key] = name
                break
        if key not in actual_cols:
            actual_cols[key] = None
    
    # 数值化处理存在的列
    for key, col_name in actual_cols.items():
        if col_name and col_name in df_evt.columns:
            df_evt[col_name] = pd.to_numeric(df_evt[col_name], errors="coerce")

    # fixation聚合
    fix_data = df_evt[df_evt["EventType"] == "fixation"].copy()
    if not fix_data.empty and actual_cols['Duration_ms']:
        fix_agg = fix_data.groupby("ADQ_ID").agg({actual_cols['Duration_ms']: "sum"})
        fix_agg["FixCount"] = fix_data.groupby("ADQ_ID")[actual_cols['Duration_ms']].count()
        fix_agg.rename(columns={actual_cols['Duration_ms']: "FixDurSum"}, inplace=True)
        fix_agg.reset_index(inplace=True)
    else:
        # 如果没有fixation数据或Duration列，创建空的聚合
        fix_agg = pd.DataFrame(columns=["ADQ_ID", "FixDurSum", "FixCount"])

    # saccade聚合
    sacc_data = df_evt[df_evt["EventType"] == "saccade"].copy()
    if not sacc_data.empty and actual_cols['Amplitude'] and actual_cols['MaxVel']:
        sacc_agg = sacc_data.groupby("ADQ_ID").agg({
            actual_cols['Amplitude']: "mean",
            actual_cols['MaxVel']: "max"
        })
        sacc_agg["SaccCount"] = sacc_data.groupby("ADQ_ID")[actual_cols['Amplitude']].count()
        sacc_agg.rename(columns={
            actual_cols['Amplitude']: "SaccAmpMean",
            actual_cols['MaxVel']: "SaccMaxVelPeak"
        }, inplace=True)
        sacc_agg.reset_index(inplace=True)
    else:
        # 如果没有saccade数据或相关列，创建空的聚合
        sacc_agg = pd.DataFrame(columns=["ADQ_ID", "SaccAmpMean", "SaccCount", "SaccMaxVelPeak"])

    # 合并
    if not fix_agg.empty and not sacc_agg.empty:
        df_evt_agg = pd.merge(fix_agg, sacc_agg, on="ADQ_ID", how="outer")
    elif not fix_agg.empty:
        df_evt_agg = fix_agg
        # 添加缺失的saccade列
        for col in ["SaccAmpMean", "SaccCount", "SaccMaxVelPeak"]:
            df_evt_agg[col] = 0
    elif not sacc_agg.empty:
        df_evt_agg = sacc_agg
        # 添加缺失的fixation列
        for col in ["FixDurSum", "FixCount"]:
            df_evt_agg[col] = 0
    else:
        # 如果都没有数据，返回空DataFrame
        return pd.DataFrame()
    
    # 填充缺失值
    for c in ["FixDurSum", "FixCount", "SaccAmpMean", "SaccCount", "SaccMaxVelPeak"]:
        if c in df_evt_agg.columns:
            df_evt_agg[c] = df_evt_agg[c].fillna(0)

    return df_evt_agg


def build_roi_aggregates(roi_csv_path):
    """构造ROI级聚合"""
    if not os.path.exists(roi_csv_path):
        return pd.DataFrame()

    df_roi = pd.read_csv(roi_csv_path)
    df_roi["ADQ_ID"] = df_roi["ADQ_ID"].astype(str)
    
    # 处理可能存在的列名，兼容不同的数据格式
    available_cols = df_roi.columns.tolist()
    
    col_mapping = {
        'RegressionCount': ['RegressionCount', 'regression_count', 'RegCount'],
        'FixationDuration': ['FixationDuration', 'FixTime', 'fixation_duration', 'FixDur']
    }
    
    # 找到实际存在的列名
    actual_cols = {}
    for key, possible_names in col_mapping.items():
        for name in possible_names:
            if name in available_cols:
                actual_cols[key] = name
                break
        if key not in actual_cols:
            actual_cols[key] = None

    # 数值化处理存在的列
    for key, col_name in actual_cols.items():
        if col_name and col_name in df_roi.columns:
            df_roi[col_name] = pd.to_numeric(df_roi[col_name], errors="coerce")

    # 执行聚合操作（如果相关列存在）
    agg_dict = {}
    if actual_cols['RegressionCount']:
        agg_dict[actual_cols['RegressionCount']] = "sum"
    if actual_cols['FixationDuration']:
        agg_dict[actual_cols['FixationDuration']] = "sum"

    if agg_dict:
        grp_agg = df_roi.groupby("ADQ_ID").agg(agg_dict)
        
        # 重命名列为标准化名称
        if actual_cols['RegressionCount'] and actual_cols['RegressionCount'] in grp_agg.columns:
            grp_agg.rename(columns={actual_cols['RegressionCount']: "RegCountSum"}, inplace=True)
        else:
            grp_agg["RegCountSum"] = 0 # 如果缺失则添加
            
        if actual_cols['FixationDuration'] and actual_cols['FixationDuration'] in grp_agg.columns:
            grp_agg.rename(columns={actual_cols['FixationDuration']: "ROIFixDurSum"}, inplace=True)
        else:
            grp_agg["ROIFixDurSum"] = 0 # 如果缺失则添加

        grp_agg.reset_index(inplace=True)
    else:
        # 如果没有相关列用于聚合，返回带有期望列的空DataFrame
        grp_agg = pd.DataFrame(columns=["ADQ_ID", "RegCountSum", "ROIFixDurSum"])

    # 填充任何剩余的NaN值为0
    for c in ["RegCountSum", "ROIFixDurSum"]:
        if c in grp_agg.columns:
            grp_agg[c] = grp_agg[c].fillna(0)

    return grp_agg


###############################################################################
# 可视化函数
###############################################################################

def create_group_bar_charts(df, metrics=["RR-2D-xy", "DET-2D-xy", "ENT-2D-xy"]):
    """创建组级条形图"""
    colors = {'Control': '#ADD8E6', 'MCI': '#FFB6A4', 'AD': '#98FB98'}
    charts = []
    
    for metric in metrics:
        if metric not in df.columns:
            continue
            
        try:
            plt.figure(figsize=(8, 6))
            
            # 移除NaN值
            df_clean = df.dropna(subset=[metric])
            if df_clean.empty:
                print(f"警告: {metric} 列中没有有效数据")
                continue
            
            # 计算组别统计
            group_stats = df_clean.groupby('Group')[metric].agg(['mean', 'std']).reset_index()
            
            # 处理NaN值
            group_stats['mean'] = group_stats['mean'].fillna(0)
            group_stats['std'] = group_stats['std'].fillna(0)
            
            # 绘制条形图
            bars = plt.bar(group_stats['Group'], group_stats['mean'], 
                          color=[colors.get(g, '#cccccc') for g in group_stats['Group']],
                          yerr=group_stats['std'], capsize=5, alpha=0.8)
            
            plt.title(f'Group-level {metric} (mean ± std)', fontsize=14, fontweight='bold')
            plt.xlabel('Group', fontsize=12, fontweight='bold')
            plt.ylabel(f'{metric} Value', fontsize=12, fontweight='bold')
            plt.grid(True, alpha=0.3)
            
            # 添加数值标签
            for i, (bar, mean_val, std_val) in enumerate(zip(bars, group_stats['mean'], group_stats['std'])):
                if not (np.isnan(mean_val) or np.isnan(std_val)):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + std_val + height*0.01,
                            f'{mean_val:.4f}', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            
            # 保存为base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            plt.close()
            
            charts.append({
                'title': f'{metric} 组别对比',
                'metric': metric,
                'image': image_base64
            })
            
        except Exception as e:
            print(f"生成 {metric} 条形图时出错: {e}")
            plt.close()  # 确保关闭图形
            continue
    
    return charts


def create_task_trend_chart(df, metric="RR-2D-xy"):
    """创建任务间变化折线图 - Average RR (2D-xy) across tasks by Group"""
    colors = {'Control': '#4472C4', 'MCI': '#E15759', 'AD': '#70AD47'}  # 更清晰的颜色
    
    try:
        print(f"📊 开始生成 {metric} 趋势图...")
        
        # 检查必要的列是否存在
        required_cols = [metric, 'Group', 'q']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ 缺少必要列: {missing_cols}")
            return None
        
        print(f"✅ 数据列检查通过，原始数据形状: {df.shape}")
        print(f"📈 包含的组: {df['Group'].unique()}")
        print(f"📊 包含的q值: {sorted(df['q'].unique())}")
        
        # 移除NaN值
        df_clean = df.dropna(subset=required_cols)
        print(f"🧹 清理后数据形状: {df_clean.shape}")
        
        if df_clean.empty:
            print(f"❌ 警告: 清理后的数据为空，无法生成趋势图")
            return None
        
        # 检查每个组的数据
        for group in ['Control', 'MCI', 'AD']:
            group_data = df_clean[df_clean['Group'] == group]
            print(f"👥 组 {group}: {len(group_data)} 条记录")
            if not group_data.empty:
                print(f"   - q值范围: {sorted(group_data['q'].unique())}")
                print(f"   - {metric}值范围: {group_data[metric].min():.6f} - {group_data[metric].max():.6f}")
        
        # 开始创建图表
        plt.figure(figsize=(12, 8))
        
        # 计算每个组在每个q值的统计
        print("📊 开始计算组级统计...")
        avg_by_group = df_clean.groupby(['Group', 'q'])[metric].agg(['mean', 'std', 'count']).reset_index()
        print(f"📋 聚合后数据形状: {avg_by_group.shape}")
        print(f"📋 聚合数据预览:\n{avg_by_group.head(10)}")
        
        # 处理NaN值
        avg_by_group['mean'] = avg_by_group['mean'].fillna(0)
        avg_by_group['std'] = avg_by_group['std'].fillna(0)
        
        lines_plotted = 0
        legend_labels = []
        
        # 为每个组画线
        for group in ['Control', 'MCI', 'AD']:
            if group not in avg_by_group['Group'].values:
                print(f"⚠️  跳过组 {group}：数据中不存在")
                continue
                
            group_data = avg_by_group[avg_by_group['Group'] == group].sort_values('q')
            if group_data.empty:
                print(f"⚠️  跳过组 {group}：无有效数据")
                continue
            
            # 计算总样本数（所有q值的平均）
            total_count = group_data['count'].mean()
            print(f"🎨 绘制组 {group}，数据点数: {len(group_data)}，平均样本数: {total_count:.1f}")
            
            # 绘制主线
            line = plt.plot(group_data['q'], group_data['mean'], 
                    marker='o', label=f'{group} (n≈{total_count:.0f})', 
                    color=colors[group], linewidth=3, markersize=8, 
                    markerfacecolor='white', markeredgewidth=2, markeredgecolor=colors[group])
            
            # 添加标准差区域
            plt.fill_between(group_data['q'],
                            group_data['mean'] - group_data['std'],
                            group_data['mean'] + group_data['std'],
                            color=colors[group], alpha=0.2)
            
            lines_plotted += 1
            legend_labels.append(f'{group} (n≈{total_count:.0f})')
            
            # 打印每个数据点的详细信息
            for _, row in group_data.iterrows():
                print(f"   Q{int(row['q'])}: mean={row['mean']:.6f}, std={row['std']:.6f}, count={row['count']}")
        
        if lines_plotted == 0:
            print(f"❌ 没有任何组的数据可以绘制")
            plt.close()
            return None
        
        print(f"✅ 成功绘制了 {lines_plotted} 个组的趋势线")
        
        # 设置图表样式
        plt.title(f"Average {metric} across tasks by Group", fontsize=16, fontweight='bold', pad=20)
        plt.xlabel("Task (Q)", fontsize=14, fontweight='bold')
        plt.ylabel(f"Mean {metric} Value", fontsize=14, fontweight='bold')
        
        # 设置x轴刻度
        all_q_values = sorted(df_clean['q'].unique())
        plt.xticks(all_q_values, [f'Q{int(q)}' for q in all_q_values])
        
        # 设置网格
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # 显示图例
        legend = plt.legend(title="Cognitive Groups", 
                          loc='best', frameon=True, fancybox=True, shadow=True)
        # 设置图例标题加粗
        legend.get_title().set_fontweight('bold')
        
        # 格式化y轴
        plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        
        plt.tight_layout()
        
        # 保存为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close()
        
        print(f"✅ 成功生成 {metric} 趋势图")
        return {
            'title': f'Average {metric} across tasks by Group',
            'metric': metric,
            'image': image_base64,
            'description': f'跨任务的平均{metric}变化趋势 (按认知组分组)'
        }
        
    except Exception as e:
        print(f"❌ 生成 {metric} 趋势图时出错: {e}")
        import traceback
        traceback.print_exc()
        plt.close()  # 确保关闭图形
        return None


###############################################################################
# API路由
###############################################################################

@rqa_pipeline_bp.route('/api/rqa-pipeline/calculate', methods=['POST'])
def rqa_calculate():
    """步骤1: RQA计算"""
    try:
        data = request.get_json()
        parameters = data.get('parameters', {})
        
        # 默认参数
        m = parameters.get('m', 2)
        delay = parameters.get('delay', parameters.get('tau', 1))  # 兼容tau和delay
        eps = parameters.get('eps', 0.05)
        lmin = parameters.get('lmin', 2)
        
        # 获取参数对应的目录
        step_dir = get_step_directory(parameters, 'step1_rqa_calculation')
        
        # 数据目录 - 需要根据实际情况调整
        data_dirs = [
            'data/control_calibrated',
            'data/mci_calibrated', 
            'data/ad_calibrated'
        ]
        
        results = []
        
        # 处理所有数据目录
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        if file.endswith('_calibrated.csv'):
                            csv_path = os.path.join(root, file)
                            result = process_single_rqa_file(csv_path, m, delay, eps, lmin)
                            if result:
                                results.append(result)
        
        # 根据组别保存结果到参数特定目录
        control_results = [r for r in results if r['filename'].startswith('n')]
        mci_results = [r for r in results if r['filename'].startswith('m')]
        ad_results = [r for r in results if r['filename'].startswith('ad')]
        
        # 保存到参数特定目录的CSV文件
        if control_results:
            control_df = pd.DataFrame(control_results)
            control_path = os.path.join(step_dir, 'RQA_1D2D_summary_control.csv')
            control_df.to_csv(control_path, index=False)
        
        if mci_results:
            mci_df = pd.DataFrame(mci_results)
            mci_path = os.path.join(step_dir, 'RQA_1D2D_summary_mci.csv')
            mci_df.to_csv(mci_path, index=False)
        
        if ad_results:
            ad_df = pd.DataFrame(ad_results)
            ad_path = os.path.join(step_dir, 'RQA_1D2D_summary_ad.csv')
            ad_df.to_csv(ad_path, index=False)
        
        # 保存参数元数据
        save_param_metadata(parameters, 1)
        
        return jsonify({
            'status': 'success',
            'message': 'RQA计算完成',
            'data': {
                'param_signature': generate_param_signature(parameters),
                'total_files': len(results),
                'control_files': len(control_results),
                'mci_files': len(mci_results),
                'ad_files': len(ad_results),
                'output_directory': step_dir
            }
        })
        
    except Exception as e:
        print(f"RQA计算错误: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'RQA计算失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/merge', methods=['POST'])
def data_merge():
    """步骤2: 数据合并"""
    try:
        data = request.get_json()
        parameters = data.get('parameters', {})
        
        # 获取参数对应的目录
        step1_dir = get_step_directory(parameters, 'step1_rqa_calculation')
        step2_dir = get_step_directory(parameters, 'step2_data_merging')
        
        # 从步骤1的结果读取数据
        control_path = os.path.join(step1_dir, 'RQA_1D2D_summary_control.csv')
        mci_path = os.path.join(step1_dir, 'RQA_1D2D_summary_mci.csv')
        ad_path = os.path.join(step1_dir, 'RQA_1D2D_summary_ad.csv')
        
        # 合并三组数据
        merged_data = merge_group_data(control_path, mci_path, ad_path)
        
        # 保存合并结果到步骤2目录
        output_path = os.path.join(step2_dir, 'All_Subjects_RQA_EyeMetrics.csv')
        merged_data.to_csv(output_path, index=False)
        
        # 保存参数元数据
        save_param_metadata(parameters, 2)
        
        return jsonify({
            'status': 'success',
            'message': '数据合并完成',
            'data': {
                'param_signature': generate_param_signature(parameters),
                'output_file': output_path,
                'total_records': len(merged_data),
                'groups': merged_data['Group'].value_counts().to_dict()
            }
        })
        
    except Exception as e:
        print(f"数据合并错误: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'数据合并失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/enrich', methods=['POST'])
def feature_enrichment():
    """步骤3: 特征补充"""
    try:
        data = request.get_json()
        parameters = data.get('parameters', {})
        
        # 获取参数对应的目录
        step2_dir = get_step_directory(parameters, 'step2_data_merging')
        step3_dir = get_step_directory(parameters, 'step3_feature_enrichment')
        
        # 读取基础RQA数据
        rqa_path = os.path.join(step2_dir, 'All_Subjects_RQA_EyeMetrics.csv')
        if not os.path.exists(rqa_path):
            raise FileNotFoundError("未找到RQA数据文件，请先执行数据合并步骤")
        
        df_rqa = pd.read_csv(rqa_path, dtype={"ID": str})
        df_rqa.rename(columns={"ID": "ADQ_ID"}, inplace=True)
        df_rqa["ADQ_ID"] = df_rqa["ADQ_ID"].str.replace(r"\.0$", "", regex=True)
        
        # 构建事件聚合
        events_path = 'data/event_analysis_results/All_Events.csv'
        df_evt_agg = build_event_aggregates(events_path)
        
        # 构建ROI聚合
        roi_path = 'data/event_analysis_results/All_ROI_Summary.csv'
        df_roi_agg = build_roi_aggregates(roi_path)
        
        # 合并特征
        if not df_evt_agg.empty and not df_roi_agg.empty:
            df_agg = pd.merge(df_evt_agg, df_roi_agg, on="ADQ_ID", how="outer")
        elif not df_evt_agg.empty:
            df_agg = df_evt_agg
        elif not df_roi_agg.empty:
            df_agg = df_roi_agg
        else:
            df_agg = pd.DataFrame()
        
        # 合并到RQA数据
        if not df_agg.empty:
            df_final = pd.merge(df_rqa, df_agg, on="ADQ_ID", how="left")
        else:
            df_final = df_rqa
        
        # 恢复ID列名
        df_final.rename(columns={"ADQ_ID": "ID"}, inplace=True)
        
        # 保存结果到步骤3目录
        output_path = os.path.join(step3_dir, 'All_Subjects_RQA_EyeMetrics_Filled.csv')
        df_final.to_csv(output_path, index=False)
        
        # 保存参数元数据
        save_param_metadata(parameters, 3)
        
        return jsonify({
            'status': 'success',
            'message': '特征补充完成',
            'data': {
                'param_signature': generate_param_signature(parameters),
                'output_file': output_path,
                'total_records': len(df_final),
                'added_features': list(df_agg.columns) if not df_agg.empty else []
            }
        })
        
    except Exception as e:
        print(f"特征补充错误: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'特征补充失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/analyze', methods=['POST'])
def statistical_analysis():
    """步骤4: 统计分析"""
    try:
        data = request.get_json()
        parameters = data.get('parameters', {})
        
        # 获取参数对应的目录
        step3_dir = get_step_directory(parameters, 'step3_feature_enrichment')
        step4_dir = get_step_directory(parameters, 'step4_statistical_analysis')
        
        # 读取填充后的数据
        filled_path = os.path.join(step3_dir, 'All_Subjects_RQA_EyeMetrics_Filled.csv')
        if not os.path.exists(filled_path):
            raise FileNotFoundError("未找到填充数据文件，请先执行特征补充步骤")
        
        df = pd.read_csv(filled_path)
        
        # RQA指标
        rqa_vars = ["RR-2D-xy", "DET-2D-xy", "ENT-2D-xy"]
        
        # 组级统计
        group_stats = df.groupby("Group")[rqa_vars].describe()
        group_stats_path = os.path.join(step4_dir, 'group_stats_output.csv')
        group_stats.to_csv(group_stats_path)
        
        # 多层次统计
        multi_level_stats = df.groupby(["Group", "folder", "q"])[rqa_vars].agg(["mean", "std"])
        multi_level_path = os.path.join(step4_dir, 'multi_level_stats_output.csv')
        multi_level_stats.to_csv(multi_level_path)
        
        # 准备返回数据
        group_summary = []
        for group in df['Group'].unique():
            group_data = df[df['Group'] == group]
            group_summary.append({
                'Group': group,
                'Count': len(group_data),
                'RR_mean': group_data['RR-2D-xy'].mean(),
                'RR_std': group_data['RR-2D-xy'].std(),
                'DET_mean': group_data['DET-2D-xy'].mean(),
                'DET_std': group_data['DET-2D-xy'].std(),
                'ENT_mean': group_data['ENT-2D-xy'].mean(),
                'ENT_std': group_data['ENT-2D-xy'].std(),
            })
        
        # 保存参数元数据
        save_param_metadata(parameters, 4)
        
        return jsonify({
            'status': 'success',
            'message': '统计分析完成',
            'data': {
                'param_signature': generate_param_signature(parameters),
                'group_stats_file': group_stats_path,
                'multi_level_stats_file': multi_level_path,
                'group_summary': group_summary
            }
        })
        
    except Exception as e:
        print(f"统计分析错误: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'统计分析失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/visualize', methods=['POST'])
def create_visualization():
    """步骤5: 可视化"""
    try:
        data = request.get_json()
        parameters = data.get('parameters', {})
        
        print(f"开始可视化步骤，参数: {parameters}")
        
        # 获取参数对应的目录
        step4_dir = get_step_directory(parameters, 'step4_statistical_analysis')
        step5_dir = get_step_directory(parameters, 'step5_visualization')
        
        print(f"可视化输出目录: {step5_dir}")
        
        # 读取填充后的数据（从步骤3目录）
        step3_dir = get_step_directory(parameters, 'step3_feature_enrichment')
        filled_path = os.path.join(step3_dir, 'All_Subjects_RQA_EyeMetrics_Filled.csv')
        if not os.path.exists(filled_path):
            raise FileNotFoundError("未找到填充数据文件，请先执行特征补充步骤")
        
        print(f"读取数据文件: {filled_path}")
        df = pd.read_csv(filled_path)
        print(f"数据形状: {df.shape}")
        print(f"数据列: {df.columns.tolist()}")
        print(f"数据组别: {df['Group'].value_counts()}")
        print(f"数据q值: {df['q'].value_counts()}")
        
        # 生成条形图
        print("\n=== 开始生成组级条形图 ===")
        bar_charts = create_group_bar_charts(df, ["RR-2D-xy", "DET-2D-xy", "ENT-2D-xy"])
        print(f"成功生成 {len(bar_charts)} 个条形图")
        
        # 保存条形图到文件
        for i, chart in enumerate(bar_charts):
            chart_filename = f"bar_chart_{chart['metric'].replace('-', '_')}.png"
            chart_path = os.path.join(step5_dir, chart_filename)
            
            # 解码base64并保存图片
            image_data = base64.b64decode(chart['image'])
            with open(chart_path, 'wb') as f:
                f.write(image_data)
            print(f"保存条形图: {chart_path}")
        
        # 生成折线图：Average RR (2D-xy) across tasks by Group
        print("\n=== 开始生成任务间变化趋势图 ===")
        trend_chart = create_task_trend_chart(df, "RR-2D-xy")
        
        # 组合所有图表
        all_charts = bar_charts[:]  # 复制条形图列表
        if trend_chart:  # 只有在成功生成时才添加
            all_charts.append(trend_chart)
            print("✅ 趋势图已成功添加到图表列表")
            
            # 保存趋势图到文件
            trend_filename = f"trend_chart_{trend_chart['metric'].replace('-', '_')}.png"
            trend_path = os.path.join(step5_dir, trend_filename)
            
            # 解码base64并保存图片
            image_data = base64.b64decode(trend_chart['image'])
            with open(trend_path, 'wb') as f:
                f.write(image_data)
            print(f"保存趋势图: {trend_path}")
        else:
            print("❌ 警告：趋势图生成失败，将跳过")
            print("检查数据是否包含必要的列和有效值...")
            print(f"RR-2D-xy列存在: {'RR-2D-xy' in df.columns}")
            print(f"Group列存在: {'Group' in df.columns}")
            print(f"q列存在: {'q' in df.columns}")
            if 'RR-2D-xy' in df.columns:
                print(f"RR-2D-xy非空值数量: {df['RR-2D-xy'].notna().sum()}")
                print(f"RR-2D-xy统计: {df['RR-2D-xy'].describe()}")
        
        print(f"\n=== 总共生成了 {len(all_charts)} 个图表 ===")
        
        # 保存图表列表到JSON文件
        charts_file = os.path.join(step5_dir, 'visualization_charts.json')
        with open(charts_file, 'w', encoding='utf-8') as f:
            json.dump(all_charts, f, indent=2, ensure_ascii=False)
        print(f"保存图表JSON: {charts_file}")
        
        # 准备组别统计数据
        print("\n=== 计算组别统计数据 ===")
        group_stats = []
        for group in df['Group'].unique():
            group_data = df[df['Group'] == group]
            print(f"组 {group}: {len(group_data)} 条记录")
            
            # 安全的统计计算，处理NaN值
            def safe_float(value):
                return float(value) if not np.isnan(value) else 0.0
            
            group_stats.append({
                'Group': group,
                'RR_mean': safe_float(group_data['RR-2D-xy'].mean()),
                'RR_std': safe_float(group_data['RR-2D-xy'].std()),
                'DET_mean': safe_float(group_data['DET-2D-xy'].mean()),
                'DET_std': safe_float(group_data['DET-2D-xy'].std()),
                'ENT_mean': safe_float(group_data['ENT-2D-xy'].mean()),
                'ENT_std': safe_float(group_data['ENT-2D-xy'].std()),
            })
        
        # 保存统计数据
        stats_file = os.path.join(step5_dir, 'group_statistics.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(group_stats, f, indent=2, ensure_ascii=False)
        print(f"保存统计数据: {stats_file}")
        
        # 列出生成的所有文件
        print(f"\n=== 生成的文件列表 ===")
        for file in os.listdir(step5_dir):
            file_path = os.path.join(step5_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"- {file} ({file_size} bytes)")
        
        # 保存参数元数据
        save_param_metadata(parameters, 5)
        
        return jsonify({
            'status': 'success',
            'message': '可视化生成完成',
            'data': {
                'param_signature': generate_param_signature(parameters),
                'charts': all_charts,
                'group_stats': group_stats,
                'total_charts': len(all_charts),
                'output_directory': step5_dir,
                'generated_files': os.listdir(step5_dir)
            }
        })
        
    except Exception as e:
        print(f"可视化错误: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'可视化失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/status', methods=['GET'])
def get_pipeline_status():
    """获取流程状态"""
    try:
        # 获取参数（如果提供）
        params = request.args.to_dict()
        
        if params:
            # 检查特定参数组合的状态
            param_dir = get_param_directory(params)
            step_dirs = ['step1_rqa_calculation', 'step2_data_merging', 
                        'step3_feature_enrichment', 'step4_statistical_analysis', 
                        'step5_visualization']
            
            status = {}
            for i, step_dir in enumerate(step_dirs, 1):
                step_path = os.path.join(param_dir, step_dir)
                status[f'step{i}'] = os.path.exists(step_path) and bool(os.listdir(step_path) if os.path.exists(step_path) else False)
        else:
            # 检查默认位置的状态（兼容旧版本）
            status = {
                'step1': os.path.exists('data/RQA_1D2D_summary_control.csv'),
                'step2': os.path.exists('data/All_Subjects_RQA_EyeMetrics.csv'),
                'step3': os.path.exists('data/All_Subjects_RQA_EyeMetrics_Filled.csv'),
                'step4': os.path.exists('data/group_stats_output.csv'),
                'step5': os.path.exists('data/multi_level_stats_output.csv'),
            }
        
        completed_steps = sum(status.values())
        progress = (completed_steps / 5) * 100
        
        return jsonify({
            'status': 'success',
            'data': {
                'step_status': status,
                'completed_steps': completed_steps,
                'total_steps': 5,
                'progress_percentage': progress,
                'param_signature': generate_param_signature(params) if params else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取状态失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/param-history', methods=['GET'])
def get_param_history_api():
    """获取参数历史记录"""
    try:
        history = get_param_history()
        
        return jsonify({
            'success': True,
            'history': history,
            'total_records': len(history)
        })
        
    except Exception as e:
        print(f"获取参数历史错误: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取参数历史失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/results/<signature>', methods=['GET'])
def get_param_results(signature):
    """获取指定参数组合的结果"""
    try:
        # 根据签名找到对应的目录
        param_path = os.path.join(PIPELINE_RESULTS_DIR, signature)
        
        if not os.path.exists(param_path):
            return jsonify({
                'status': 'error',
                'message': f'未找到参数组合 {signature} 的结果'
            }), 404
        
        # 检查哪些步骤已完成
        step_dirs = ['step1_rqa_calculation', 'step2_data_merging', 
                    'step3_feature_enrichment', 'step4_statistical_analysis', 
                    'step5_visualization']
        
        completed_steps = []
        results = {}
        
        for step_dir in step_dirs:
            step_path = os.path.join(param_path, step_dir)
            if os.path.exists(step_path) and os.listdir(step_path):
                completed_steps.append(step_dir)
        
        # 如果可视化步骤完成，返回图表数据
        if 'step5_visualization' in completed_steps:
            charts_file = os.path.join(param_path, 'step5_visualization', 'visualization_charts.json')
            stats_file = os.path.join(param_path, 'step5_visualization', 'group_statistics.json')
            
            if os.path.exists(charts_file):
                with open(charts_file, 'r', encoding='utf-8') as f:
                    results['charts'] = json.load(f)
                    
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    results['group_stats'] = json.load(f)
        
        # 读取元数据
        metadata_file = os.path.join(param_path, 'metadata.json')
        metadata = {}
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        
        return jsonify({
            'status': 'success',
            'data': {
                'signature': signature,
                'metadata': metadata,
                'completed_steps': completed_steps,
                'completed_count': len(completed_steps),
                'total_steps': 5,
                'results': results
            }
        })
        
    except Exception as e:
        print(f"获取结果错误: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取结果失败: {str(e)}'
        }), 500


@rqa_pipeline_bp.route('/api/rqa-pipeline/delete/<signature>', methods=['DELETE'])
def delete_param_results(signature):
    """删除指定参数组合的结果"""
    try:
        param_path = os.path.join(PIPELINE_RESULTS_DIR, signature)
        
        if not os.path.exists(param_path):
            return jsonify({
                'status': 'error',
                'message': f'未找到参数组合 {signature} 的结果'
            }), 404
        
        # 删除整个参数目录
        import shutil
        shutil.rmtree(param_path)
        
        return jsonify({
            'status': 'success',
            'message': f'已删除参数组合 {signature} 的所有结果'
        })
        
    except Exception as e:
        print(f"删除结果错误: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'删除结果失败: {str(e)}'
        }), 500 