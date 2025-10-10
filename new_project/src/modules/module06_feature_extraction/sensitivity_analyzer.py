"""
Module04 Feature Sensitivity Analyzer
Module04特征敏感度分析器

实现5种统计指标，计算综合敏感度得分，从9个特征中选出Top-4
"""

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind
from typing import Dict, List, Tuple
from itertools import combinations


class SensitivityAnalyzer:
    """
    Module04特征敏感度分析器

    分析9个特征（排除MMSE）在Control/MCI/AD三组间的敏感度
    使用5种统计指标计算综合敏感度得分
    """

    AVAILABLE_FEATURES = [
        "bg_ratio_frame",           # 背景区域占比
        "inst_ratio_frame",         # 指令区域占比
        "kw_ratio_frame",           # 关键词区域占比
        "total_fixation_time",      # 总注视时间
        "total_fixations",          # 注视次数
        "avg_fixation_duration",    # 平均注视时长
        "total_saccades",           # 扫视次数
        "avg_saccade_amplitude",    # 平均扫视幅度
        "task_total_time"           # 任务总时间
    ]

    GROUPS = ["control", "mci", "ad"]

    def __init__(self, features_df: pd.DataFrame):
        """
        初始化分析器

        Args:
            features_df: Module04特征数据
                必须包含列: subject_id, group, task_id, 以及9个特征列
        """
        self.df = features_df.copy()
        self._validate_data()

    def _validate_data(self):
        """验证输入数据格式"""
        required_cols = ["subject_id", "group", "task_id"] + self.AVAILABLE_FEATURES
        missing_cols = set(required_cols) - set(self.df.columns)

        if missing_cols:
            raise ValueError(f"缺少必需列: {missing_cols}")

        # 检查group值
        invalid_groups = set(self.df['group'].unique()) - set(self.GROUPS)
        if invalid_groups:
            raise ValueError(f"无效的分组: {invalid_groups}")

    def compute_all_features(self) -> pd.DataFrame:
        """
        计算所有9个特征的敏感度指标

        Returns:
            DataFrame: 包含所有敏感度指标和综合得分，按得分降序排序
                列: feature_name, f_statistic, p_value, eta_squared,
                    avg_cohens_d, avg_cv, sensitivity_score, rank
        """
        results = []

        for feature in self.AVAILABLE_FEATURES:
            # 计算5种统计指标
            f_stat, p_value = self._compute_f_statistic(feature)
            eta_squared = self._compute_eta_squared(feature, f_stat)
            pairwise_results = self._compute_pairwise(feature)
            avg_cohens_d = self._compute_avg_cohens_d(feature)
            avg_cv = self._compute_cv(feature)

            # 计算综合敏感度得分
            sensitivity_score = self._compute_score(
                f_stat, eta_squared, p_value, avg_cv
            )

            results.append({
                "feature_name": feature,
                "f_statistic": round(f_stat, 4),
                "p_value": round(p_value, 6),
                "eta_squared": round(eta_squared, 4),
                "avg_cohens_d": round(avg_cohens_d, 4),
                "avg_cv": round(avg_cv, 2),
                "sensitivity_score": round(sensitivity_score, 4),
                "pairwise_results": pairwise_results
            })

        # 转换为DataFrame并排序
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values("sensitivity_score", ascending=False)
        results_df["rank"] = range(1, len(results_df) + 1)

        return results_df

    def _compute_f_statistic(self, feature: str) -> Tuple[float, float]:
        """
        计算ANOVA F统计量和p值

        Args:
            feature: 特征名称

        Returns:
            (f_statistic, p_value)
        """
        groups_data = [
            self.df[self.df['group'] == group][feature].values
            for group in self.GROUPS
        ]

        f_stat, p_value = f_oneway(*groups_data)

        return f_stat, p_value

    def _compute_eta_squared(self, feature: str, f_stat: float) -> float:
        """
        计算Effect Size (Eta Squared)

        η² = SS_between / SS_total = SS_between / (SS_between + SS_within)

        通过F统计量计算:
        η² = (k-1) * F / ((k-1) * F + N - k)
        其中 k=3 (组数), N=总样本数

        Args:
            feature: 特征名称
            f_stat: F统计量

        Returns:
            eta_squared: 效应量 (0-1)
        """
        k = len(self.GROUPS)  # 组数 = 3
        N = len(self.df)      # 总样本数 = 300

        eta_squared = (k - 1) * f_stat / ((k - 1) * f_stat + N - k)

        return eta_squared

    def _compute_pairwise(self, feature: str) -> List[Dict]:
        """
        计算成对t检验 (Bonferroni校正)

        Args:
            feature: 特征名称

        Returns:
            List of dict: 每个组合的t检验结果
                {
                    'pair': 'control_vs_mci',
                    't_statistic': float,
                    'p_value': float,
                    'p_value_corrected': float,
                    'significant': bool
                }
        """
        pairs = list(combinations(self.GROUPS, 2))
        n_comparisons = len(pairs)  # 3 pairs
        alpha = 0.05
        bonferroni_alpha = alpha / n_comparisons  # 0.0167

        pairwise_results = []

        for group1, group2 in pairs:
            data1 = self.df[self.df['group'] == group1][feature].values
            data2 = self.df[self.df['group'] == group2][feature].values

            t_stat, p_value = ttest_ind(data1, data2)
            p_corrected = min(p_value * n_comparisons, 1.0)

            pairwise_results.append({
                'pair': f'{group1}_vs_{group2}',
                't_statistic': round(t_stat, 4),
                'p_value': round(p_value, 6),
                'p_value_corrected': round(p_corrected, 6),
                'significant': bool(p_corrected < alpha)
            })

        return pairwise_results

    def _compute_avg_cohens_d(self, feature: str) -> float:
        """
        计算平均Cohen's d (所有组合的平均)

        Cohen's d = (mean1 - mean2) / pooled_std

        Args:
            feature: 特征名称

        Returns:
            平均Cohen's d值
        """
        pairs = list(combinations(self.GROUPS, 2))
        cohens_d_values = []

        for group1, group2 in pairs:
            data1 = self.df[self.df['group'] == group1][feature].values
            data2 = self.df[self.df['group'] == group2][feature].values

            mean1, mean2 = np.mean(data1), np.mean(data2)
            std1, std2 = np.std(data1, ddof=1), np.std(data2, ddof=1)
            n1, n2 = len(data1), len(data2)

            # Pooled standard deviation
            pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

            cohens_d = abs(mean1 - mean2) / pooled_std if pooled_std > 0 else 0
            cohens_d_values.append(cohens_d)

        return np.mean(cohens_d_values)

    def _compute_cv(self, feature: str) -> float:
        """
        计算变异系数 (Coefficient of Variation)

        CV = (std / mean) × 100%
        返回三组CV的平均值

        Args:
            feature: 特征名称

        Returns:
            平均CV值 (百分比)
        """
        cv_values = []

        for group in self.GROUPS:
            data = self.df[self.df['group'] == group][feature].values
            mean_val = np.mean(data)
            std_val = np.std(data, ddof=1)

            cv = (std_val / mean_val * 100) if mean_val > 0 else 0
            cv_values.append(cv)

        return np.mean(cv_values)

    def _compute_score(self, f_stat: float, eta_squared: float,
                       p_value: float, avg_cv: float) -> float:
        """
        计算综合敏感度得分

        Score = (F × η²) / (1 + p_value) × (1 / (1 + CV/100))

        这个公式结合了:
        - 组间差异 (F统计量)
        - 效应量 (Eta Squared)
        - 统计显著性 (p值)
        - 稳定性 (变异系数)

        Args:
            f_stat: F统计量
            eta_squared: 效应量
            p_value: p值
            avg_cv: 平均变异系数

        Returns:
            综合敏感度得分
        """
        # 避免除零
        p_value = max(p_value, 1e-10)

        # 核心得分 (差异 × 效应)
        core_score = f_stat * eta_squared

        # 显著性因子 (p值越小越好)
        significance_factor = 1 / (1 + p_value)

        # 稳定性因子 (CV越小越好)
        stability_factor = 1 / (1 + avg_cv / 100)

        sensitivity_score = core_score * significance_factor * stability_factor

        return sensitivity_score

    def get_top_k_features(self, k: int = 4) -> List[str]:
        """
        获取Top-K敏感特征名称列表

        Args:
            k: 选择的特征数量，默认4

        Returns:
            特征名称列表
        """
        results_df = self.compute_all_features()
        return results_df.head(k)["feature_name"].tolist()

    def generate_report(self) -> Dict:
        """
        生成完整的敏感度分析报告

        Returns:
            {
                "summary": {...},
                "top_4_features": [...],
                "all_features": [...],
                "interpretation": {...}
            }
        """
        results_df = self.compute_all_features()
        top_4 = results_df.head(4)

        report = {
            "summary": {
                "total_features_analyzed": len(self.AVAILABLE_FEATURES),
                "top_k_selected": 4,
                "total_samples": len(self.df),
                "groups": self.GROUPS,
                "group_sizes": {
                    group: len(self.df[self.df['group'] == group])
                    for group in self.GROUPS
                }
            },
            "top_4_features": top_4.to_dict(orient="records"),
            "all_features": results_df.to_dict(orient="records"),
            "interpretation": {
                "eta_squared_threshold": {
                    "small": 0.01,
                    "medium": 0.06,
                    "large": 0.14
                },
                "cohens_d_threshold": {
                    "small": 0.2,
                    "medium": 0.5,
                    "large": 0.8
                },
                "significance_level": 0.05,
                "bonferroni_corrected_alpha": 0.0167
            }
        }

        return report
