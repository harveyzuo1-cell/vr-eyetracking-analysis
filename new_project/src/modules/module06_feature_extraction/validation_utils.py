"""
特征验证工具

实现：
1. Pearson/Spearman相关性分析
2. VIF（方差膨胀因子）多重共线性检查
"""

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from typing import Dict, List

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ValidationUtils:
    """特征验证工具"""

    def __init__(self, X: pd.DataFrame, y: pd.Series, feature_names: List[str]):
        """
        初始化验证工具

        Args:
            X: 特征矩阵
            y: 目标变量（MMSE分数）
            feature_names: 特征名称列表
        """
        self.X = X
        self.y = y
        self.feature_names = feature_names

        logger.info(f"ValidationUtils初始化: {len(feature_names)}个特征")

    def compute_correlations(self, X_subset: pd.DataFrame,
                            y: pd.Series) -> List[Dict]:
        """
        计算特征与目标的相关系数

        Returns:
            [
                {
                    'feature': 'total_saccades',
                    'pearson_r': 0.45,
                    'pearson_p': 0.001,
                    'spearman_r': 0.42,
                    'spearman_p': 0.002
                },
                ...
            ]
        """
        logger.info(f"计算 {len(X_subset.columns)} 个特征与MMSE的相关性...")

        results = []

        for feature in X_subset.columns:
            try:
                # Pearson相关系数（线性关系）
                r_pearson, p_pearson = pearsonr(X_subset[feature], y)

                # Spearman相关系数（单调关系，对异常值鲁棒）
                r_spearman, p_spearman = spearmanr(X_subset[feature], y)

                results.append({
                    'feature': feature,
                    'pearson_r': float(r_pearson),
                    'pearson_p': float(p_pearson),
                    'spearman_r': float(r_spearman),
                    'spearman_p': float(p_spearman)
                })

            except Exception as e:
                logger.warning(f"特征 {feature} 相关性计算失败: {e}")
                results.append({
                    'feature': feature,
                    'pearson_r': 0.0,
                    'pearson_p': 1.0,
                    'spearman_r': 0.0,
                    'spearman_p': 1.0
                })

        # 按Pearson相关系数绝对值降序排序
        results.sort(key=lambda x: abs(x['pearson_r']), reverse=True)

        logger.info(f"相关性分析完成，Top-3特征: {[r['feature'] for r in results[:3]]}")

        return results

    def compute_vif(self, X_subset: pd.DataFrame) -> List[Dict]:
        """
        计算方差膨胀因子（VIF）

        VIF = 1 / (1 - R²_i)
        其中R²_i是用其他特征预测第i个特征的R²

        Returns:
            [
                {'feature': 'total_saccades', 'vif': 2.3},
                {'feature': 'total_fixations', 'vif': 4.8},
                ...
            ]
        """
        logger.info(f"计算 {len(X_subset.columns)} 个特征的VIF...")

        try:
            from statsmodels.stats.outliers_influence import variance_inflation_factor

            vif_data = []

            for i, feature in enumerate(X_subset.columns):
                try:
                    vif_value = variance_inflation_factor(X_subset.values, i)

                    # VIF可能是inf或nan，需要处理
                    if np.isinf(vif_value) or np.isnan(vif_value):
                        vif_value = 999.0  # 设置为大值表示严重共线性

                    vif_data.append({
                        'feature': feature,
                        'vif': float(vif_value)
                    })

                except Exception as e:
                    logger.warning(f"特征 {feature} VIF计算失败: {e}")
                    vif_data.append({
                        'feature': feature,
                        'vif': 999.0
                    })

            # 按VIF降序排序
            vif_data.sort(key=lambda x: x['vif'], reverse=True)

            logger.info(f"VIF分析完成，最高VIF: {vif_data[0]['feature']}={vif_data[0]['vif']:.2f}")

            return vif_data

        except ImportError:
            logger.error("未安装statsmodels库，无法计算VIF")
            return [{'feature': f, 'vif': 1.0} for f in X_subset.columns]

    def remove_high_vif_features(self, vif_results: List[Dict],
                                 threshold: float = 5.0) -> List[str]:
        """
        迭代移除高VIF特征

        算法：
        1. 找到VIF最高的特征
        2. 如果VIF > threshold，移除该特征
        3. 重新计算剩余特征的VIF
        4. 重复直到所有VIF < threshold

        Args:
            vif_results: VIF分析结果
            threshold: VIF阈值

        Returns:
            filtered_features: 过滤后的特征列表
        """
        logger.info(f"移除VIF > {threshold} 的特征...")

        current_features = [item['feature'] for item in vif_results]
        removed_features = []

        iteration = 0
        max_iterations = len(current_features)  # 防止无限循环

        while iteration < max_iterations:
            iteration += 1

            # 重新计算当前特征的VIF
            X_current = self.X[current_features]
            vif_current = self.compute_vif(X_current)

            # 找到VIF最高的特征
            max_vif_item = max(vif_current, key=lambda x: x['vif'])

            if max_vif_item['vif'] < threshold:
                logger.info(f"所有特征VIF < {threshold}，停止移除")
                break

            # 移除VIF最高的特征
            removed_feature = max_vif_item['feature']
            current_features.remove(removed_feature)
            removed_features.append(removed_feature)

            logger.info(f"移除特征 {removed_feature} (VIF={max_vif_item['vif']:.2f}), "
                       f"剩余 {len(current_features)} 个特征")

            if len(current_features) <= 1:
                logger.warning("只剩1个特征，停止移除")
                break

        logger.info(f"VIF过滤完成，移除了 {len(removed_features)} 个特征: {removed_features}")

        return current_features

    def filter_by_correlation(self, corr_results: List[Dict],
                             threshold: float = 0.25) -> List[str]:
        """
        根据相关性阈值过滤特征

        Args:
            corr_results: 相关性分析结果
            threshold: 相关系数阈值（保留 |r| >= threshold 的特征）

        Returns:
            filtered_features: 过滤后的特征列表
        """
        logger.info(f"过滤相关性 < {threshold} 的特征...")

        filtered_features = [
            item['feature'] for item in corr_results
            if abs(item['pearson_r']) >= threshold
            or abs(item['spearman_r']) >= threshold
        ]

        removed_count = len(corr_results) - len(filtered_features)

        logger.info(f"相关性过滤完成，保留 {len(filtered_features)} 个特征，"
                   f"移除 {removed_count} 个低相关特征")

        return filtered_features
