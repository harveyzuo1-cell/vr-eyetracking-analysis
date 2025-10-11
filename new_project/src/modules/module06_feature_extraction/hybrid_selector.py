"""
混合特征选择器 - 三阶段主控制器

集成Filter、Validation、Wrapper三个阶段
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from sklearn.model_selection import cross_val_score
from sklearn.neural_network import MLPRegressor

from src.utils.logger import setup_logger
from .filter_methods import FilterMethods
from .wrapper_methods import WrapperMethods
from .validation_utils import ValidationUtils

logger = setup_logger(__name__)


class HybridFeatureSelector:
    """
    混合特征选择器（三阶段）

    阶段1: Filter预筛选（ANOVA + F-regression + MI）
    阶段2: 回归验证（相关性 + VIF）
    阶段3: Wrapper精选（RFE + Lasso + RF）
    """

    def __init__(self, X: pd.DataFrame, y: pd.Series,
                 feature_names: List[str], groups: pd.Series = None):
        """
        初始化混合选择器

        Args:
            X: 特征矩阵 (n_samples, n_features)
            y: 目标变量（MMSE分数）
            feature_names: 特征名称列表
            groups: 分组标签（用于ANOVA）
        """
        self.X = X
        self.y = y
        self.feature_names = feature_names
        self.groups = groups

        self.filter = FilterMethods(X, y, feature_names, groups)
        self.wrapper = WrapperMethods(X, y, feature_names)
        self.validator = ValidationUtils(X, y, feature_names)

        # 存储每阶段结果
        self.stage1_results = None
        self.stage2_results = None
        self.stage3_results = None

        logger.info(f"HybridFeatureSelector初始化: {len(feature_names)}个特征, {len(X)}个样本")

    def run_stage1_filter(self, top_k: int = 15) -> Dict:
        """
        阶段1: Filter预筛选

        Returns:
            {
                'anova_scores': [...],
                'freg_scores': [...],
                'mi_scores': [...],
                'combined_ranks': [...],
                'top_features': [...],
                'execution_time': 60.5
            }
        """
        import time
        start_time = time.time()

        logger.info("=" * 50)
        logger.info("阶段1: Filter预筛选")
        logger.info("=" * 50)

        # 1. ANOVA敏感度分析
        anova_scores = self.filter.compute_anova_scores()

        # 2. F-regression
        freg_scores = self.filter.compute_f_regression_scores()

        # 3. Mutual Information
        mi_scores = self.filter.compute_mutual_info_scores()

        # 4. Borda Count投票
        combined_ranks = self.filter.combine_ranks(
            anova_scores, freg_scores, mi_scores
        )

        # 5. 选择Top-K
        top_features = self.filter.get_top_features(combined_ranks, top_k)

        self.stage1_results = {
            'anova_scores': anova_scores.tolist(),
            'freg_scores': freg_scores.tolist(),
            'mi_scores': mi_scores.tolist(),
            'combined_ranks': combined_ranks.tolist(),
            'top_features': top_features,
            'execution_time': time.time() - start_time
        }

        logger.info(f"阶段1完成 ({self.stage1_results['execution_time']:.1f}秒)")
        logger.info(f"选出Top-{top_k}特征: {top_features[:5]}...")

        return self.stage1_results

    def run_stage2_validation(self, threshold_corr: float = 0.25,
                              threshold_vif: float = 5.0) -> Dict:
        """
        阶段2: 回归验证

        Args:
            threshold_corr: 相关系数阈值
            threshold_vif: VIF阈值

        Returns:
            {
                'correlation_analysis': [...],
                'vif_analysis': [...],
                'filtered_features': [...],
                'removed_features': [...],
                'execution_time': 30.2
            }
        """
        if self.stage1_results is None:
            raise ValueError("请先运行阶段1")

        import time
        start_time = time.time()

        logger.info("=" * 50)
        logger.info("阶段2: 回归验证")
        logger.info("=" * 50)

        top_features = self.stage1_results['top_features']
        X_subset = self.X[top_features]

        # 1. 相关性分析
        corr_results = self.validator.compute_correlations(X_subset, self.y)

        # 过滤低相关特征
        features_after_corr = self.validator.filter_by_correlation(
            corr_results, threshold=threshold_corr
        )

        # 2. VIF分析
        X_after_corr = self.X[features_after_corr]
        vif_results = self.validator.compute_vif(X_after_corr)

        # 迭代移除高VIF特征
        features_final = self.validator.remove_high_vif_features(
            vif_results, threshold=threshold_vif
        )

        removed_features = list(set(top_features) - set(features_final))

        self.stage2_results = {
            'correlation_analysis': corr_results,
            'vif_analysis': vif_results,
            'filtered_features': features_final,
            'removed_features': removed_features,
            'execution_time': time.time() - start_time
        }

        logger.info(f"阶段2完成 ({self.stage2_results['execution_time']:.1f}秒)")
        logger.info(f"通过验证的特征: {len(features_final)}个")
        logger.info(f"移除的特征: {removed_features}")

        return self.stage2_results

    def run_stage3_wrapper(self, final_k: int = 10,
                          cv_folds: int = 5) -> Dict:
        """
        阶段3: Wrapper精选

        Args:
            final_k: 最终特征数量
            cv_folds: 交叉验证折数

        Returns:
            {
                'rfe_results': {...},
                'lasso_results': {...},
                'rf_results': {...},
                'best_method': 'RFE',
                'final_features': [...],
                'cv_scores': {...},
                'execution_time': 600.5
            }
        """
        if self.stage2_results is None:
            raise ValueError("请先运行阶段2")

        import time
        start_time = time.time()

        logger.info("=" * 50)
        logger.info("阶段3: Wrapper精选")
        logger.info("=" * 50)

        filtered_features = self.stage2_results['filtered_features']
        X_subset = self.X[filtered_features]

        # 1. RFE + MLP
        logger.info("运行RFE...")
        rfe_results = self.wrapper.run_rfe(X_subset, self.y, n_features=final_k)

        # 2. LassoCV
        logger.info("运行LassoCV...")
        lasso_results = self.wrapper.run_lasso(X_subset, self.y, n_features=final_k)

        # 3. Random Forest
        logger.info("运行Random Forest...")
        rf_results = self.wrapper.run_random_forest(X_subset, self.y, n_features=final_k)

        # 4. 交叉验证对比
        logger.info("交叉验证评估...")
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)

        cv_scores = {}
        for method_name, result in [('RFE', rfe_results),
                                     ('Lasso', lasso_results),
                                     ('RF', rf_results)]:
            selected_features = result['selected_features']
            X_selected = self.X[selected_features]

            scores = cross_val_score(
                mlp, X_selected, self.y,
                cv=cv_folds, scoring='r2'
            )

            cv_scores[method_name] = {
                'r2_mean': float(scores.mean()),
                'r2_std': float(scores.std()),
                'r2_scores': scores.tolist()
            }

            logger.info(f"{method_name}: R² = {scores.mean():.3f} ± {scores.std():.3f}")

        # 5. 选择最优方法
        best_method = max(cv_scores.items(), key=lambda x: x[1]['r2_mean'])[0]

        if best_method == 'RFE':
            final_features = rfe_results['selected_features']
        elif best_method == 'Lasso':
            final_features = lasso_results['selected_features']
        else:
            final_features = rf_results['selected_features']

        self.stage3_results = {
            'rfe_results': rfe_results,
            'lasso_results': lasso_results,
            'rf_results': rf_results,
            'best_method': best_method,
            'final_features': final_features,
            'cv_scores': cv_scores,
            'execution_time': time.time() - start_time
        }

        logger.info(f"阶段3完成 ({self.stage3_results['execution_time']:.1f}秒)")
        logger.info(f"最优方法: {best_method}")
        logger.info(f"最终特征: {final_features}")

        return self.stage3_results

    def generate_report(self) -> Dict:
        """
        生成完整报告

        Returns:
            {
                'stage1_filter': {...},
                'stage2_validation': {...},
                'stage3_wrapper': {...},
                'final_features': [...],
                'total_execution_time': 690.8
            }
        """
        if any(r is None for r in [self.stage1_results,
                                    self.stage2_results,
                                    self.stage3_results]):
            raise ValueError("请先完成全部三个阶段")

        logger.info("=" * 50)
        logger.info("生成完整报告")
        logger.info("=" * 50)

        total_time = sum([
            self.stage1_results['execution_time'],
            self.stage2_results['execution_time'],
            self.stage3_results['execution_time']
        ])

        report = {
            'stage1_filter': self.stage1_results,
            'stage2_validation': self.stage2_results,
            'stage3_wrapper': self.stage3_results,
            'final_features': self.stage3_results['final_features'],
            'total_execution_time': total_time
        }

        logger.info(f"混合特征选择完成，总耗时: {total_time:.1f}秒")
        logger.info(f"最终选出 {len(report['final_features'])} 个特征")

        return report
