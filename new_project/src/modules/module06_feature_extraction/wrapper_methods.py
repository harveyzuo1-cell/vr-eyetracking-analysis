"""
Wrapper特征选择方法集合

实现三种Wrapper方法：
1. RFE (Recursive Feature Elimination) + MLP
2. LassoCV (L1正则化)
3. Random Forest特征重要性
"""

import numpy as np
import pandas as pd
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class WrapperMethods:
    """Wrapper特征选择方法集合"""

    def __init__(self, X: pd.DataFrame, y: pd.Series, feature_names: List[str]):
        """
        初始化Wrapper方法

        Args:
            X: 特征矩阵
            y: 目标变量（MMSE分数）
            feature_names: 特征名称列表
        """
        self.X = X
        self.y = y
        self.feature_names = feature_names

        logger.info(f"WrapperMethods初始化: {len(feature_names)}个特征, {len(X)}个样本")

    def run_rfe(self, X_subset: pd.DataFrame, y: pd.Series,
                n_features: int = 10) -> Dict:
        """
        递归特征消除 (RFE) + MLP

        算法流程：
        1. 训练MLP模型
        2. 计算特征重要性（通过权重或置换）
        3. 移除最不重要的特征
        4. 重复直到剩余n_features个特征

        Args:
            X_subset: 候选特征子集
            y: 目标变量
            n_features: 最终保留的特征数

        Returns:
            {
                'method': 'RFE',
                'selected_features': [...],
                'feature_ranking': [...],
                'execution_time': 120.5
            }
        """
        import time
        start_time = time.time()

        logger.info(f"运行RFE，从 {len(X_subset.columns)} 个特征选出 {n_features} 个...")

        try:
            from sklearn.feature_selection import RFE
            from sklearn.neural_network import MLPRegressor

            # MLP配置
            mlp = MLPRegressor(
                hidden_layer_sizes=(64, 32, 16),
                activation='relu',
                max_iter=1000,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1,
                n_iter_no_change=20,
                verbose=False
            )

            # RFE
            rfe = RFE(
                estimator=mlp,
                n_features_to_select=n_features,
                step=1,  # 每次移除1个特征
                verbose=0
            )

            rfe.fit(X_subset, y)

            # 提取选中的特征
            selected_indices = rfe.support_
            selected_features = X_subset.columns[selected_indices].tolist()

            logger.info(f"RFE完成，选出特征: {selected_features[:5]}...")

            return {
                'method': 'RFE',
                'selected_features': selected_features,
                'feature_ranking': rfe.ranking_.tolist(),
                'n_features_selected': len(selected_features),
                'execution_time': time.time() - start_time
            }

        except Exception as e:
            logger.error(f"RFE执行失败: {e}")
            # 降级方案：返回前n个特征
            return {
                'method': 'RFE',
                'selected_features': X_subset.columns[:n_features].tolist(),
                'feature_ranking': list(range(1, len(X_subset.columns) + 1)),
                'n_features_selected': n_features,
                'execution_time': time.time() - start_time,
                'error': str(e)
            }

    def run_lasso(self, X_subset: pd.DataFrame, y: pd.Series,
                  n_features: int = 10) -> Dict:
        """
        LassoCV (L1正则化自动特征选择)

        L1正则化会将不重要特征的系数压缩为0

        Args:
            X_subset: 候选特征子集
            y: 目标变量
            n_features: 最终保留的特征数

        Returns:
            {
                'method': 'Lasso',
                'selected_features': [...],
                'coefficients': [...],
                'alpha': 0.05,
                'execution_time': 60.2
            }
        """
        import time
        start_time = time.time()

        logger.info(f"运行LassoCV，从 {len(X_subset.columns)} 个特征选出 {n_features} 个...")

        try:
            from sklearn.linear_model import LassoCV
            from sklearn.preprocessing import StandardScaler

            # 标准化（Lasso对尺度敏感）
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_subset)

            # LassoCV自动选择最优alpha
            lasso = LassoCV(
                cv=5,
                random_state=42,
                max_iter=10000,
                n_alphas=100,
                verbose=False
            )

            lasso.fit(X_scaled, y)

            # 选择系数绝对值最大的Top-K特征
            coef_abs = np.abs(lasso.coef_)
            top_indices = np.argsort(coef_abs)[-n_features:]

            selected_features = X_subset.columns[top_indices].tolist()

            logger.info(f"LassoCV完成 (alpha={lasso.alpha_:.4f})，选出特征: {selected_features[:5]}...")

            return {
                'method': 'Lasso',
                'selected_features': selected_features,
                'coefficients': lasso.coef_.tolist(),
                'alpha': float(lasso.alpha_),
                'n_features_selected': len(selected_features),
                'execution_time': time.time() - start_time
            }

        except Exception as e:
            logger.error(f"LassoCV执行失败: {e}")
            return {
                'method': 'Lasso',
                'selected_features': X_subset.columns[:n_features].tolist(),
                'coefficients': [0.0] * len(X_subset.columns),
                'alpha': 1.0,
                'n_features_selected': n_features,
                'execution_time': time.time() - start_time,
                'error': str(e)
            }

    def run_random_forest(self, X_subset: pd.DataFrame, y: pd.Series,
                         n_features: int = 10) -> Dict:
        """
        Random Forest特征重要性

        基于基尼不纯度或均方误差的下降计算特征重要性

        Args:
            X_subset: 候选特征子集
            y: 目标变量
            n_features: 最终保留的特征数

        Returns:
            {
                'method': 'RandomForest',
                'selected_features': [...],
                'feature_importances': [...],
                'execution_time': 45.8
            }
        """
        import time
        start_time = time.time()

        logger.info(f"运行Random Forest，从 {len(X_subset.columns)} 个特征选出 {n_features} 个...")

        try:
            from sklearn.ensemble import RandomForestRegressor

            # Random Forest配置
            rf = RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,  # 并行加速
                verbose=0
            )

            rf.fit(X_subset, y)

            # 获取特征重要性
            importances = rf.feature_importances_

            # 选择重要性最高的Top-K特征
            top_indices = np.argsort(importances)[-n_features:]

            selected_features = X_subset.columns[top_indices].tolist()

            logger.info(f"Random Forest完成，选出特征: {selected_features[:5]}...")

            return {
                'method': 'RandomForest',
                'selected_features': selected_features,
                'feature_importances': importances.tolist(),
                'n_features_selected': len(selected_features),
                'execution_time': time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Random Forest执行失败: {e}")
            return {
                'method': 'RandomForest',
                'selected_features': X_subset.columns[:n_features].tolist(),
                'feature_importances': [1.0 / len(X_subset.columns)] * len(X_subset.columns),
                'n_features_selected': n_features,
                'execution_time': time.time() - start_time,
                'error': str(e)
            }
