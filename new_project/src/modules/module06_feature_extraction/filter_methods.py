"""
Filter特征选择方法集合

实现三种Filter方法：
1. ANOVA敏感度分析（当前方法）
2. F-regression（针对回归任务）
3. Mutual Information（捕捉非线性关系）
"""

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.feature_selection import f_regression, mutual_info_regression
from typing import List

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class FilterMethods:
    """Filter特征选择方法集合"""

    def __init__(self, X: pd.DataFrame, y: pd.Series,
                 feature_names: List[str], groups: pd.Series = None):
        """
        初始化Filter方法

        Args:
            X: 特征矩阵 (n_samples, n_features)
            y: 目标变量（MMSE分数）
            feature_names: 特征名称列表
            groups: 分组标签（用于ANOVA，可选）
        """
        self.X = X
        self.y = y
        self.feature_names = feature_names
        self.groups = groups

        logger.info(f"FilterMethods初始化: {len(feature_names)}个特征, {len(X)}个样本")

    def compute_anova_scores(self) -> np.ndarray:
        """
        计算ANOVA敏感度得分（复用现有SensitivityAnalyzer）

        Returns:
            scores: (n_features,) 每个特征的敏感度得分
        """
        if self.groups is None:
            logger.warning("未提供分组信息，ANOVA得分将全部设为0")
            return np.zeros(len(self.feature_names))

        from .sensitivity_analyzer import SensitivityAnalyzer

        logger.info("计算ANOVA敏感度得分...")

        # 构造适合SensitivityAnalyzer的数据格式
        df = pd.DataFrame(self.X, columns=self.feature_names)
        df['group'] = self.groups.values
        df['subject_id'] = range(len(self.X))
        df['task_id'] = ['q1'] * len(self.X)

        try:
            analyzer = SensitivityAnalyzer(df)
            results = analyzer.compute_all_features()

            # 提取sensitivity_score
            scores = results['sensitivity_score'].values

            logger.info(f"ANOVA得分计算完成，得分范围: [{scores.min():.2f}, {scores.max():.2f}]")
            return scores

        except Exception as e:
            logger.error(f"ANOVA计算失败: {e}")
            return np.zeros(len(self.feature_names))

    def compute_f_regression_scores(self) -> np.ndarray:
        """
        计算F-regression得分（针对回归任务）

        公式: Score = F / (1 + p_value)

        Returns:
            scores: (n_features,)
        """
        logger.info("计算F-regression得分...")

        try:
            # sklearn的f_regression返回F值和p值
            f_scores, p_values = f_regression(self.X, self.y)

            # 结合F值和p值
            # Score = F / (1 + p)，p值越小得分越高
            scores = f_scores / (1 + p_values)

            logger.info(f"F-regression得分计算完成，得分范围: [{scores.min():.2f}, {scores.max():.2f}]")
            return scores

        except Exception as e:
            logger.error(f"F-regression计算失败: {e}")
            return np.zeros(len(self.feature_names))

    def compute_mutual_info_scores(self, random_state: int = 42) -> np.ndarray:
        """
        计算互信息得分（可捕捉非线性关系）

        Args:
            random_state: 随机种子

        Returns:
            scores: (n_features,)
        """
        logger.info("计算Mutual Information得分...")

        try:
            mi_scores = mutual_info_regression(
                self.X, self.y,
                random_state=random_state,
                n_neighbors=5
            )

            logger.info(f"MI得分计算完成，得分范围: [{mi_scores.min():.4f}, {mi_scores.max():.4f}]")
            return mi_scores

        except Exception as e:
            logger.error(f"Mutual Information计算失败: {e}")
            return np.zeros(len(self.feature_names))

    def combine_ranks(self, *score_arrays) -> np.ndarray:
        """
        Borda Count投票：将多个得分数组的排名相加

        Args:
            score_arrays: 多个得分数组（得分越高越好）

        Returns:
            combined_ranks: (n_features,) 综合排名（数值越小排名越高）
        """
        logger.info(f"使用Borda Count投票融合 {len(score_arrays)} 种方法的排名...")

        ranks = []
        for i, scores in enumerate(score_arrays):
            # 得分越高排名越小（1, 2, 3, ...）
            # 使用负号使得高分特征排名靠前
            rank = rankdata(-scores, method='average')
            ranks.append(rank)

            logger.debug(f"方法{i+1} - 排名范围: [{rank.min():.1f}, {rank.max():.1f}]")

        # 排名求和（Borda Count）
        combined_ranks = np.sum(ranks, axis=0)

        logger.info(f"Borda Count投票完成，综合排名范围: [{combined_ranks.min():.1f}, {combined_ranks.max():.1f}]")

        return combined_ranks

    def get_top_features(self, combined_ranks: np.ndarray, top_k: int = 15) -> List[str]:
        """
        根据综合排名选择Top-K特征

        Args:
            combined_ranks: 综合排名
            top_k: 选择的特征数量

        Returns:
            top_features: Top-K特征名称列表
        """
        # 排名越小越好，选择排名最小的K个
        top_indices = np.argsort(combined_ranks)[:top_k]
        top_features = [self.feature_names[i] for i in top_indices]

        logger.info(f"选出Top-{top_k}特征: {top_features[:5]}...")

        return top_features
