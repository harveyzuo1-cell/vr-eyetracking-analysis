"""
模块10 Eye-Index 综合评估 - 核心工具函数
实现综合眼动系数 S_eye 计算、统计分析、报告生成
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
from sklearn.decomposition import PCA
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# 定义10个核心眼动特征（与用户规范一致）
EYE_FEATURES = [
    'game_duration', 'kw_roi_time', 'inst_roi_time', 'bg_roi_time',
    'rr_1d', 'det_1d', 'ent_1d', 'rr_2d', 'det_2d', 'ent_2d'
]

# MMSE子分数列名
MMSE_FEATURES = [
    'Q1_subscore', 'Q2_subscore', 'Q3_subscore', 'Q4_subscore', 'Q5_subscore'
]

def compute_s_eye(df, mode="equal", weights=None):
    """
    计算综合眼动系数 S_eye
    
    Args:
        df: 包含眼动特征的DataFrame
        mode: 计算模式 ("equal", "pca", "custom")
        weights: 自定义权重列表（仅在mode="custom"时使用）
    
    Returns:
        DataFrame: 添加了S_eye和S_eye_z列的数据框
    """
    
    # 检查必要特征是否存在
    available_features = []
    for feat in EYE_FEATURES:
        if feat in df.columns:
            available_features.append(feat)
    
    if len(available_features) == 0:
        raise ValueError("数据框中不包含任何眼动特征")
    
    print(f"📊 使用特征数量: {len(available_features)}/{len(EYE_FEATURES)}")
    print(f"📋 可用特征: {available_features}")
    
    # 提取特征矩阵（填充缺失值）
    feats = df[available_features].fillna(0).values
    
    if mode == "equal":
        # 等权平均
        s_eye = feats.mean(axis=1)
        print("🧮 计算模式: 等权平均")
        
    elif mode == "pca":
        # PCA第一主成分
        if feats.shape[1] < 2:
            print("⚠️ 特征数量不足，回退到等权平均")
            s_eye = feats.mean(axis=1)
        else:
            pca = PCA(n_components=1)
            pcs = pca.fit_transform(feats)
            # 归一化到[0,1]
            s_eye = (pcs.flatten() - pcs.min()) / (pcs.max() - pcs.min())
            print(f"🧮 计算模式: PCA第一主成分 (解释方差: {pca.explained_variance_ratio_[0]:.3f})")
            
    elif mode == "custom":
        # 自定义权重
        if weights is None or len(weights) != len(available_features):
            print("⚠️ 权重参数无效，回退到等权平均")
            s_eye = feats.mean(axis=1)
        else:
            w = np.asarray(weights, dtype=float)
            w = w / w.sum()  # 归一化权重
            s_eye = (feats * w).sum(axis=1)
            print(f"🧮 计算模式: 自定义权重 {w.round(3)}")
    else:
        raise ValueError(f"不支持的计算模式: {mode}")
    
    # 添加到数据框
    df = df.copy()
    df['S_eye'] = s_eye
    
    # 计算Z分数（标准化）
    if s_eye.std() > 0:
        df['S_eye_z'] = (s_eye - s_eye.mean()) / s_eye.std()
    else:
        df['S_eye_z'] = 0
    
    print(f"✅ S_eye计算完成: 范围 [{s_eye.min():.3f}, {s_eye.max():.3f}], 均值 {s_eye.mean():.3f}")
    
    return df

def generate_statistics(df):
    """生成S_eye的描述性统计"""
    s_eye = df['S_eye']
    
    stats = {
        'count': int(len(s_eye)),
        'mean': float(s_eye.mean()),
        'std': float(s_eye.std()),
        'min': float(s_eye.min()),
        'max': float(s_eye.max()),
        'q25': float(s_eye.quantile(0.25)),
        'q50': float(s_eye.quantile(0.50)),
        'q75': float(s_eye.quantile(0.75))
    }
    
    return stats

def generate_group_stats(df):
    """按组别生成统计"""
    group_stats = {}
    
    if 'Group_Type' in df.columns:
        for group in ['control', 'mci', 'ad']:
            group_data = df[df['Group_Type'] == group]
            if len(group_data) > 0:
                group_stats[group] = generate_statistics(group_data)
    
    return group_stats

def calculate_correlations(df):
    """计算S_eye与MMSE子分数的相关性"""
    correlations = {}
    
    if 'S_eye' not in df.columns:
        return correlations
    
    s_eye = df['S_eye']
    
    for mmse_feat in MMSE_FEATURES:
        if mmse_feat in df.columns:
            mmse_scores = df[mmse_feat].dropna()
            s_eye_aligned = s_eye[mmse_scores.index]
            
            if len(mmse_scores) > 1 and len(s_eye_aligned) > 1:
                try:
                    r, p = pearsonr(s_eye_aligned, mmse_scores)
                    correlations[mmse_feat] = {
                        'r': float(r),
                        'p': float(p),
                        'n': int(len(mmse_scores)),
                        'significant': p < 0.05
                    }
                except:
                    correlations[mmse_feat] = {
                        'r': 0.0,
                        'p': 1.0,
                        'n': 0,
                        'significant': False
                    }
    
    return correlations

def eye_index_report(df):
    """生成综合Eye-Index报告"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        'metadata': {
            'timestamp': timestamp,
            'total_subjects': int(len(df)),
            'eye_features_used': [feat for feat in EYE_FEATURES if feat in df.columns],
            'mmse_features_available': [feat for feat in MMSE_FEATURES if feat in df.columns]
        },
        'overall': {
            'stats': generate_statistics(df) if 'S_eye' in df.columns else {},
            'correlations': calculate_correlations(df)
        },
        'by_group': generate_group_stats(df) if 'S_eye' in df.columns else {},
        'interpretation': generate_interpretation(df) if 'S_eye' in df.columns else ""
    }
    
    return report

def generate_interpretation(df):
    """生成解释性文本"""
    
    if 'S_eye' not in df.columns:
        return "S_eye未计算"
    
    stats = generate_statistics(df)
    group_stats = generate_group_stats(df)
    correlations = calculate_correlations(df)
    
    interpretation = []
    
    # 整体分布解释
    interpretation.append(f"**综合眼动系数 (S_eye) 分析报告**")
    interpretation.append(f"")
    interpretation.append(f"**总体分布**：")
    interpretation.append(f"- 样本数量：{stats['count']} 名受试者")
    interpretation.append(f"- 均值±标准差：{stats['mean']:.3f} ± {stats['std']:.3f}")
    interpretation.append(f"- 中位数 [IQR]：{stats['q50']:.3f} [{stats['q25']:.3f}-{stats['q75']:.3f}]")
    interpretation.append(f"")
    
    # 组别对比
    if group_stats:
        interpretation.append(f"**组别对比**：")
        for group_name in ['control', 'mci', 'ad']:
            group_cn = {'control': '控制组', 'mci': 'MCI组', 'ad': 'AD组'}[group_name]
            if group_name in group_stats:
                gstats = group_stats[group_name]
                interpretation.append(f"- {group_cn}：{gstats['mean']:.3f} ± {gstats['std']:.3f} (n={gstats['count']})")
        interpretation.append(f"")
    
    # 相关性分析
    if correlations:
        interpretation.append(f"**与MMSE认知评估的相关性**：")
        for mmse_name, corr_data in correlations.items():
            task_cn = {
                'Q1_subscore': 'Q1(时间定向)',
                'Q2_subscore': 'Q2(空间定向)', 
                'Q3_subscore': 'Q3(即刻记忆)',
                'Q4_subscore': 'Q4(注意力计算)',
                'Q5_subscore': 'Q5(延迟回忆)'
            }.get(mmse_name, mmse_name)
            
            sig_mark = "**" if corr_data['significant'] else ""
            interpretation.append(f"- {task_cn}：r = {corr_data['r']:.3f}{sig_mark} (n={corr_data['n']})")
        interpretation.append(f"")
    
    # 临床意义解释
    interpretation.append(f"**临床意义**：")
    interpretation.append(f"S_eye 反映受试者在VR认知任务中的综合眼动表现。数值越高表示：")
    interpretation.append(f"- 游戏完成时间更短（效率更高）")
    interpretation.append(f"- ROI关注时间更合理（注意力更集中）")  
    interpretation.append(f"- RQA参数更优（眼动模式更稳定）")
    interpretation.append(f"")
    interpretation.append(f"可作为传统MMSE评估的客观补充指标，用于认知功能的量化评估。")
    
    return "\n".join(interpretation)

def save_dataset_with_s_eye(df, output_path):
    """保存带有S_eye的数据集"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"💾 数据集已保存: {output_path}")

def save_report(report, output_path):
    """保存JSON报告"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"📄 报告已保存: {output_path}")