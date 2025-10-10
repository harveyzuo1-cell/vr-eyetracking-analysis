"""
Module05 RQA特征聚合器

用于从Module05敏感度分析结果中提取Top-K RQA特征
支持两种聚合策略:
1. cross_param: 跨参数聚合,选择6个核心RQA指标
2. single_param: 基于单参数,选择Top参数的RQA特征
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class M05FeatureAggregator:
    """Module05 RQA特征聚合器"""

    # Module05 RQA特征分类
    # 1D特征: 基于x轴(水平方向)的递归
    RQA_FEATURES_1D_X = ['rr-1d-x', 'det-1d-x', 'ent-1d-x', 'lam-1d-x', 'l_mean-1d-x']

    # 2D特征: 基于xy二维空间的递归
    RQA_FEATURES_2D_XY = ['rr-2d-xy', 'det-2d-xy', 'ent-2d-xy', 'lam-2d-xy', 'l_mean-2d-xy']

    # 所有RQA核心特征
    ALL_RQA_FEATURES = RQA_FEATURES_1D_X + RQA_FEATURES_2D_XY

    def __init__(self):
        """初始化聚合器"""
        logger.info("M05FeatureAggregator initialized")

    def aggregate_cross_param(self, sensitivity_df: pd.DataFrame,
                             top_k: int = 6) -> List[Dict]:
        """
        跨参数聚合: 选择Top-K个RQA核心指标

        对每个RQA特征,在所有参数组合中取平均敏感度得分,
        然后选择得分最高的K个特征

        Args:
            sensitivity_df: Module05敏感度分析结果DataFrame
                必须包含列: feature, overall_score, f_statistic, effect_size
            top_k: 选择的特征数量

        Returns:
            Top-K RQA特征列表
            [{
                'feature': 'RR-2D-xy',
                'avg_score': 0.85,
                'avg_f_stat': 45.2,
                'avg_effect_size': 0.32,
                'param_count': 3264,  # 该特征在多少个参数组合中出现
                'rank': 1
            }, ...]
        """
        logger.info(f"跨参数聚合: 从 {len(sensitivity_df)} 条记录中选择 Top-{top_k} RQA特征")

        # 标准化feature列名(转小写,处理各种格式)
        sensitivity_df = sensitivity_df.copy()
        sensitivity_df['feature'] = sensitivity_df['feature'].str.lower().str.strip()

        # 按feature分组,计算平均指标
        aggregated = sensitivity_df.groupby('feature').agg({
            'overall_score': 'mean',
            'f_statistic': 'mean',
            'effect_size': 'mean',
            'p_value': 'mean',
            'task_consistency': 'mean'
        }).reset_index()

        # 添加参数组合计数
        param_counts = sensitivity_df.groupby('feature').size().reset_index(name='param_count')
        aggregated = aggregated.merge(param_counts, on='feature')

        # 按平均综合得分排序
        aggregated = aggregated.sort_values('overall_score', ascending=False)

        # 选择Top-K
        top_features = aggregated.head(top_k)

        # 格式化结果
        result = []
        for rank, (idx, row) in enumerate(top_features.iterrows(), 1):
            result.append({
                'feature': row['feature'].upper(),  # 转回大写显示
                'avg_score': round(row['overall_score'], 4),
                'avg_f_stat': round(row['f_statistic'], 4),
                'avg_effect_size': round(row['effect_size'], 4),
                'avg_p_value': round(row['p_value'], 6),
                'avg_task_consistency': round(row['task_consistency'], 4),
                'param_count': int(row['param_count']),
                'rank': rank
            })

        logger.info(f"跨参数聚合完成: Top-{top_k} = {[f['feature'] for f in result]}")

        return result

    def aggregate_by_top_params(self, sensitivity_df: pd.DataFrame,
                                top_k_params: int = 10,
                                features_per_param: int = 6) -> List[Dict]:
        """
        基于Top参数聚合: 选择Top-K参数组合,每个参数选择N个最佳RQA特征

        Strategy B使用此方法: Top-10参数 × 6特征 = 60维

        Args:
            sensitivity_df: Module05敏感度分析结果DataFrame
            top_k_params: 选择Top-K个参数组合
            features_per_param: 每个参数组合选择N个特征

        Returns:
            选定的RQA特征列表
        """
        logger.info(f"Top参数聚合: Top-{top_k_params}参数 × {features_per_param}特征")

        # 标准化列名
        sensitivity_df = sensitivity_df.copy()
        sensitivity_df['feature'] = sensitivity_df['feature'].str.lower()

        # 为每个参数组合计算平均敏感度(跨所有特征)
        param_scores = sensitivity_df.groupby('param_signature').agg({
            'overall_score': 'mean',
            'f_statistic': 'mean',
            'effect_size': 'mean'
        }).reset_index()

        # 选择Top-K参数组合
        param_scores = param_scores.sort_values('overall_score', ascending=False)
        top_params = param_scores.head(top_k_params)['param_signature'].tolist()

        logger.info(f"Top-{top_k_params}参数: {top_params[:3]}...")

        # 对每个Top参数,选择最佳N个特征
        result = []
        rank = 1

        for param_sig in top_params:
            param_df = sensitivity_df[sensitivity_df['param_signature'] == param_sig]
            param_df = param_df.sort_values('overall_score', ascending=False)
            top_features = param_df.head(features_per_param)

            for _, row in top_features.iterrows():
                result.append({
                    'feature': f"{param_sig}_{row['feature']}".upper(),
                    'param_signature': param_sig,
                    'rqa_feature': row['feature'].upper(),
                    'score': round(row['overall_score'], 4),
                    'f_stat': round(row['f_statistic'], 4),
                    'effect_size': round(row['effect_size'], 4),
                    'rank': rank
                })
                rank += 1

        logger.info(f"Top参数聚合完成: 共 {len(result)} 个特征")

        return result

    def get_top_params_summary(self, sensitivity_df: pd.DataFrame,
                              top_k: int = 10) -> List[Dict]:
        """
        获取Top-K参数组合摘要

        Args:
            sensitivity_df: 敏感度分析结果
            top_k: Top-K个参数

        Returns:
            参数摘要列表
        """
        # 计算每个参数的平均得分
        param_summary = sensitivity_df.groupby('param_signature').agg({
            'm': 'first',
            'tau': 'first',
            'eps': 'first',
            'lmin': 'first',
            'overall_score': 'mean',
            'f_statistic': 'mean',
            'effect_size': 'mean'
        }).reset_index()

        # 排序并选择Top-K
        param_summary = param_summary.sort_values('overall_score', ascending=False)
        top_params = param_summary.head(top_k)

        result = []
        for rank, (_, row) in enumerate(top_params.iterrows(), 1):
            result.append({
                'rank': rank,
                'param_signature': row['param_signature'],
                'm': int(row['m']),
                'tau': int(row['tau']),
                'eps': round(row['eps'], 3),
                'lmin': int(row['lmin']),
                'avg_score': round(row['overall_score'], 4),
                'avg_f_stat': round(row['f_statistic'], 4),
                'avg_effect_size': round(row['effect_size'], 4)
            })

        return result

    def validate_sensitivity_data(self, sensitivity_df: pd.DataFrame) -> Dict:
        """
        验证敏感度分析数据质量

        Returns:
            验证结果摘要
        """
        required_cols = ['param_signature', 'feature', 'overall_score',
                        'f_statistic', 'effect_size']
        missing_cols = set(required_cols) - set(sensitivity_df.columns)

        if missing_cols:
            raise ValueError(f"敏感度数据缺少必需列: {missing_cols}")

        validation = {
            'total_records': len(sensitivity_df),
            'unique_params': sensitivity_df['param_signature'].nunique(),
            'unique_features': sensitivity_df['feature'].nunique(),
            'score_range': (
                float(sensitivity_df['overall_score'].min()),
                float(sensitivity_df['overall_score'].max())
            ),
            'missing_values': sensitivity_df.isnull().sum().to_dict(),
            'valid': True
        }

        logger.info(f"数据验证通过: {validation['unique_params']}个参数, "
                   f"{validation['unique_features']}个特征")

        return validation
