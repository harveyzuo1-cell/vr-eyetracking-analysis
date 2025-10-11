# Module06 混合特征选择方案（方案C）设计文档

## 📋 目录
1. [设计目标](#1-设计目标)
2. [整体架构](#2-整体架构)
3. [技术原理](#3-技术原理)
4. [后端设计](#4-后端设计)
5. [前端设计](#5-前端设计)
6. [API接口设计](#6-api接口设计)
7. [数据流程](#7-数据流程)
8. [实施步骤](#8-实施步骤)
9. [测试验证](#9-测试验证)

---

## 1. 设计目标

### 1.1 当前问题
- **目标不一致**：敏感度分析优化"分组区分能力"，但最终任务是"MMSE回归预测"
- **单变量分析**：未考虑特征间交互和冗余
- **缺少验证**：未评估选出的特征在MLP任务中的实际性能

### 1.2 优化目标
- ✅ **三阶段混合方法**：Filter快速预筛选 → 回归验证 → Wrapper精选
- ✅ **针对回归任务优化**：使用与MMSE相关性、互信息、MLP性能作为评估指标
- ✅ **可视化对比**：展示不同方法的特征重要性和性能差异
- ✅ **用户可选**：支持"快速模式"（当前ANOVA）和"精确模式"（混合方法）

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Module06 混合特征选择                      │
└─────────────────────────────────────────────────────────────────┘

阶段1: Filter预筛选 (60秒)
┌──────────────────────────────────────────────────────┐
│  27个候选特征 (9个M04 + 18个M05)                      │
│  ↓                                                    │
│  方法1: ANOVA敏感度分析 (当前)                        │
│  方法2: F-regression (回归F统计量)                    │
│  方法3: Mutual Information (互信息)                   │
│  ↓                                                    │
│  三种方法投票 → 筛选到 Top-15 候选                    │
└──────────────────────────────────────────────────────┘
                        ↓
阶段2: 回归验证 (30秒)
┌──────────────────────────────────────────────────────┐
│  15个候选特征                                         │
│  ↓                                                    │
│  1. 计算与MMSE的Pearson/Spearman相关系数             │
│  2. 移除低相关特征 (|r| < 0.25)                      │
│  3. 检查多重共线性 (VIF < 5)                         │
│  ↓                                                    │
│  保留 12-13个特征                                     │
└──────────────────────────────────────────────────────┘
                        ↓
阶段3: Wrapper精选 (5-10分钟)
┌──────────────────────────────────────────────────────┐
│  12-13个候选特征                                      │
│  ↓                                                    │
│  方法A: RFE + MLP (递归特征消除)                      │
│  方法B: LassoCV (L1正则化)                            │
│  方法C: Random Forest Feature Importance              │
│  ↓                                                    │
│  交叉验证评估 → 选出 Top-10                           │
└──────────────────────────────────────────────────────┘
                        ↓
              最终特征集 (10维)
```

---

## 3. 技术原理

### 3.1 阶段1：Filter预筛选

#### **方法1: ANOVA F-statistic（当前）**
```python
# 组间差异检验
F = MS_between / MS_within
Score = (F × η²) / (1 + p) × (1 / (1 + CV/100))
```
- **优点**：快速、可解释性强
- **缺点**：针对分类任务优化

#### **方法2: F-regression**
```python
from sklearn.feature_selection import f_regression

# 回归F统计量（假设线性关系）
F_scores, p_values = f_regression(X_features, y_mmse)

# 计分公式
Score = F / (1 + p_value)
```
- **优点**：直接针对连续目标变量
- **假设**：特征与MMSE线性相关

#### **方法3: Mutual Information**
```python
from sklearn.feature_selection import mutual_info_regression

# 互信息（可捕捉非线性）
MI_scores = mutual_info_regression(X_features, y_mmse, random_state=42)
```
- **优点**：可捕捉非线性关系
- **缺点**：计算慢，需要调参

#### **投票策略**
```python
# 标准化三种方法的得分
rank_anova = rankdata(-scores_anova)
rank_freg = rankdata(-scores_freg)
rank_mi = rankdata(-scores_mi)

# Borda Count投票
combined_rank = rank_anova + rank_freg + rank_mi

# 选择Top-15
top_15_features = features[np.argsort(combined_rank)[:15]]
```

---

### 3.2 阶段2：回归验证

#### **相关性分析**
```python
from scipy.stats import pearsonr, spearmanr

for feature in top_15_features:
    r_pearson, p_pearson = pearsonr(X[feature], y_mmse)
    r_spearman, p_spearman = spearmanr(X[feature], y_mmse)

    # 过滤低相关特征
    if abs(r_pearson) < 0.25 and abs(r_spearman) < 0.25:
        remove_feature(feature)
```

**相关系数解释：**
- |r| ≥ 0.5：强相关 ⭐⭐⭐
- 0.3 ≤ |r| < 0.5：中等相关 ⭐⭐
- 0.1 ≤ |r| < 0.3：弱相关 ⭐
- |r| < 0.1：几乎无关 ❌

#### **多重共线性检查（VIF）**
```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

# 计算方差膨胀因子
vif_data = pd.DataFrame()
vif_data["feature"] = features
vif_data["VIF"] = [variance_inflation_factor(X.values, i)
                   for i in range(len(features))]

# 移除VIF > 5的特征（高共线性）
features_filtered = vif_data[vif_data["VIF"] < 5]["feature"].tolist()
```

**VIF解释：**
- VIF < 5：可接受 ✅
- 5 ≤ VIF < 10：中等共线性 ⚠️
- VIF ≥ 10：严重共线性，需移除 ❌

---

### 3.3 阶段3：Wrapper精选

#### **方法A: RFE + MLP**
```python
from sklearn.feature_selection import RFE
from sklearn.neural_network import MLPRegressor

mlp = MLPRegressor(
    hidden_layer_sizes=(64, 32, 16),
    activation='relu',
    max_iter=1000,
    random_state=42
)

# 递归特征消除
rfe = RFE(estimator=mlp, n_features_to_select=10, step=1)
rfe.fit(X_train, y_train)

selected_features = rfe.support_
```

**原理：**
1. 训练模型，计算特征重要性
2. 移除最不重要的特征
3. 重复直到剩余10个特征

#### **方法B: LassoCV**
```python
from sklearn.linear_model import LassoCV

lasso = LassoCV(cv=5, random_state=42, max_iter=10000)
lasso.fit(X_train, y_train)

# L1正则化自动特征选择
feature_importance = np.abs(lasso.coef_)
top_10_indices = np.argsort(feature_importance)[-10:]
```

**原理：** L1惩罚将不重要特征的系数压缩为0

#### **方法C: Random Forest**
```python
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
rf.fit(X_train, y_train)

feature_importance = rf.feature_importances_
top_10_indices = np.argsort(feature_importance)[-10:]
```

#### **交叉验证评估**
```python
from sklearn.model_selection import cross_val_score

# 对每个方法的特征子集进行5折交叉验证
for method in ['RFE', 'Lasso', 'RF']:
    features_subset = selected_features[method]

    scores = cross_val_score(
        mlp, X[:, features_subset], y_mmse,
        cv=5, scoring='r2'
    )

    print(f"{method}: R² = {scores.mean():.3f} ± {scores.std():.3f}")

# 选择R²最高的方法
best_method = max(methods, key=lambda m: m['r2_mean'])
```

---

## 4. 后端设计

### 4.1 新增模块结构

```
src/modules/module06_feature_extraction/
├── hybrid_selector.py           # 混合特征选择器（新增）
├── filter_methods.py            # Filter方法集合（新增）
├── wrapper_methods.py           # Wrapper方法集合（新增）
├── validation_utils.py          # 验证工具（新增）
├── service.py                   # 服务层（扩展）
└── api.py                       # API路由（扩展）
```

---

### 4.2 核心类设计

#### **4.2.1 HybridFeatureSelector（混合选择器）**

```python
# hybrid_selector.py

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.model_selection import cross_val_score
from sklearn.neural_network import MLPRegressor

from .filter_methods import FilterMethods
from .wrapper_methods import WrapperMethods
from .validation_utils import ValidationUtils


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
        top_indices = np.argsort(combined_ranks)[:top_k]
        top_features = [self.feature_names[i] for i in top_indices]

        self.stage1_results = {
            'anova_scores': anova_scores,
            'freg_scores': freg_scores,
            'mi_scores': mi_scores,
            'combined_ranks': combined_ranks,
            'top_features': top_features,
            'top_indices': top_indices,
            'execution_time': time.time() - start_time
        }

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

        top_features = self.stage1_results['top_features']
        X_subset = self.X[top_features]

        # 1. 相关性分析
        corr_results = self.validator.compute_correlations(X_subset, self.y)

        # 过滤低相关特征
        features_after_corr = [
            f['feature'] for f in corr_results
            if abs(f['pearson_r']) >= threshold_corr
            or abs(f['spearman_r']) >= threshold_corr
        ]

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

        filtered_features = self.stage2_results['filtered_features']
        X_subset = self.X[filtered_features]

        # 1. RFE + MLP
        rfe_results = self.wrapper.run_rfe(
            X_subset, self.y, n_features=final_k
        )

        # 2. LassoCV
        lasso_results = self.wrapper.run_lasso(
            X_subset, self.y, n_features=final_k
        )

        # 3. Random Forest
        rf_results = self.wrapper.run_random_forest(
            X_subset, self.y, n_features=final_k
        )

        # 4. 交叉验证对比
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000)

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

        return self.stage3_results

    def generate_report(self) -> Dict:
        """
        生成完整报告

        Returns:
            {
                'stage1': {...},
                'stage2': {...},
                'stage3': {...},
                'final_features': [...],
                'comparison_with_baseline': {...}
            }
        """
        if any(r is None for r in [self.stage1_results,
                                    self.stage2_results,
                                    self.stage3_results]):
            raise ValueError("请先完成全部三个阶段")

        # 对比baseline（当前ANOVA方法）
        baseline_comparison = self._compare_with_baseline()

        return {
            'stage1_filter': self.stage1_results,
            'stage2_validation': self.stage2_results,
            'stage3_wrapper': self.stage3_results,
            'final_features': self.stage3_results['final_features'],
            'comparison_with_baseline': baseline_comparison,
            'total_execution_time': sum([
                self.stage1_results['execution_time'],
                self.stage2_results['execution_time'],
                self.stage3_results['execution_time']
            ])
        }

    def _compare_with_baseline(self) -> Dict:
        """对比当前ANOVA方法（baseline）"""
        from .sensitivity_analyzer import SensitivityAnalyzer

        # Baseline: ANOVA方法
        analyzer = SensitivityAnalyzer(
            pd.DataFrame({
                **{f: self.X[f] for f in self.feature_names},
                'group': self.groups,
                'subject_id': range(len(self.X)),
                'task_id': ['q1'] * len(self.X)
            })
        )

        baseline_features = analyzer.get_top_k_features(k=10)

        # 交叉验证对比
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000)

        scores_baseline = cross_val_score(
            mlp, self.X[baseline_features], self.y, cv=5, scoring='r2'
        )

        scores_hybrid = cross_val_score(
            mlp, self.X[self.stage3_results['final_features']],
            self.y, cv=5, scoring='r2'
        )

        return {
            'baseline_method': 'ANOVA',
            'baseline_features': baseline_features,
            'baseline_r2': {
                'mean': float(scores_baseline.mean()),
                'std': float(scores_baseline.std())
            },
            'hybrid_method': self.stage3_results['best_method'],
            'hybrid_features': self.stage3_results['final_features'],
            'hybrid_r2': {
                'mean': float(scores_hybrid.mean()),
                'std': float(scores_hybrid.std())
            },
            'improvement': {
                'absolute': float(scores_hybrid.mean() - scores_baseline.mean()),
                'relative_pct': float((scores_hybrid.mean() - scores_baseline.mean())
                                     / scores_baseline.mean() * 100)
            }
        }
```

---

#### **4.2.2 FilterMethods（Filter方法集合）**

```python
# filter_methods.py

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, rankdata
from sklearn.feature_selection import f_regression, mutual_info_regression
from typing import Dict, List


class FilterMethods:
    """Filter特征选择方法集合"""

    def __init__(self, X: pd.DataFrame, y: pd.Series,
                 feature_names: List[str], groups: pd.Series = None):
        self.X = X
        self.y = y
        self.feature_names = feature_names
        self.groups = groups

    def compute_anova_scores(self) -> np.ndarray:
        """
        计算ANOVA敏感度得分

        Returns:
            scores: (n_features,) 每个特征的得分
        """
        from .sensitivity_analyzer import SensitivityAnalyzer

        # 构造适合SensitivityAnalyzer的数据格式
        df = pd.DataFrame(self.X, columns=self.feature_names)
        df['group'] = self.groups
        df['subject_id'] = range(len(self.X))
        df['task_id'] = ['q1'] * len(self.X)

        analyzer = SensitivityAnalyzer(df)
        results = analyzer.compute_all_features()

        # 返回sensitivity_score
        scores = results['sensitivity_score'].values
        return scores

    def compute_f_regression_scores(self) -> np.ndarray:
        """
        计算F-regression得分（针对回归任务）

        Returns:
            scores: (n_features,)
        """
        f_scores, p_values = f_regression(self.X, self.y)

        # 结合F值和p值
        # Score = F / (1 + p)
        scores = f_scores / (1 + p_values)

        return scores

    def compute_mutual_info_scores(self, random_state: int = 42) -> np.ndarray:
        """
        计算互信息得分（可捕捉非线性关系）

        Returns:
            scores: (n_features,)
        """
        mi_scores = mutual_info_regression(
            self.X, self.y,
            random_state=random_state,
            n_neighbors=5
        )

        return mi_scores

    def combine_ranks(self, *score_arrays) -> np.ndarray:
        """
        Borda Count投票

        Args:
            score_arrays: 多个得分数组

        Returns:
            combined_ranks: (n_features,) 综合排名（越小越好）
        """
        ranks = []
        for scores in score_arrays:
            # 得分越高排名越小（1, 2, 3, ...）
            rank = rankdata(-scores, method='average')
            ranks.append(rank)

        # 排名求和（Borda Count）
        combined_ranks = np.sum(ranks, axis=0)

        return combined_ranks
```

---

#### **4.2.3 WrapperMethods（Wrapper方法集合）**

```python
# wrapper_methods.py

import numpy as np
import pandas as pd
from typing import Dict, List
from sklearn.feature_selection import RFE
from sklearn.linear_model import LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor


class WrapperMethods:
    """Wrapper特征选择方法集合"""

    def __init__(self, X: pd.DataFrame, y: pd.Series, feature_names: List[str]):
        self.X = X
        self.y = y
        self.feature_names = feature_names

    def run_rfe(self, X_subset: pd.DataFrame, y: pd.Series,
                n_features: int = 10) -> Dict:
        """
        递归特征消除 (RFE) + MLP

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

        mlp = MLPRegressor(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            max_iter=1000,
            random_state=42,
            early_stopping=True
        )

        rfe = RFE(
            estimator=mlp,
            n_features_to_select=n_features,
            step=1,
            verbose=0
        )

        rfe.fit(X_subset, y)

        selected_indices = rfe.support_
        selected_features = X_subset.columns[selected_indices].tolist()

        return {
            'method': 'RFE',
            'selected_features': selected_features,
            'feature_ranking': rfe.ranking_.tolist(),
            'execution_time': time.time() - start_time
        }

    def run_lasso(self, X_subset: pd.DataFrame, y: pd.Series,
                  n_features: int = 10) -> Dict:
        """
        LassoCV (L1正则化)

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

        lasso = LassoCV(
            cv=5,
            random_state=42,
            max_iter=10000,
            n_alphas=100
        )

        lasso.fit(X_subset, y)

        # 选择系数绝对值最大的Top-K特征
        coef_abs = np.abs(lasso.coef_)
        top_indices = np.argsort(coef_abs)[-n_features:]

        selected_features = X_subset.columns[top_indices].tolist()

        return {
            'method': 'Lasso',
            'selected_features': selected_features,
            'coefficients': lasso.coef_.tolist(),
            'alpha': float(lasso.alpha_),
            'execution_time': time.time() - start_time
        }

    def run_random_forest(self, X_subset: pd.DataFrame, y: pd.Series,
                         n_features: int = 10) -> Dict:
        """
        Random Forest特征重要性

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

        rf = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        rf.fit(X_subset, y)

        # 选择重要性最高的Top-K特征
        importances = rf.feature_importances_
        top_indices = np.argsort(importances)[-n_features:]

        selected_features = X_subset.columns[top_indices].tolist()

        return {
            'method': 'RandomForest',
            'selected_features': selected_features,
            'feature_importances': importances.tolist(),
            'execution_time': time.time() - start_time
        }
```

---

#### **4.2.4 ValidationUtils（验证工具）**

```python
# validation_utils.py

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Dict, List


class ValidationUtils:
    """特征验证工具"""

    def __init__(self, X: pd.DataFrame, y: pd.Series, feature_names: List[str]):
        self.X = X
        self.y = y
        self.feature_names = feature_names

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
        results = []

        for feature in X_subset.columns:
            r_pearson, p_pearson = pearsonr(X_subset[feature], y)
            r_spearman, p_spearman = spearmanr(X_subset[feature], y)

            results.append({
                'feature': feature,
                'pearson_r': float(r_pearson),
                'pearson_p': float(p_pearson),
                'spearman_r': float(r_spearman),
                'spearman_p': float(p_spearman)
            })

        # 按Pearson相关系数绝对值降序排序
        results.sort(key=lambda x: abs(x['pearson_r']), reverse=True)

        return results

    def compute_vif(self, X_subset: pd.DataFrame) -> List[Dict]:
        """
        计算方差膨胀因子（VIF）

        Returns:
            [
                {'feature': 'total_saccades', 'vif': 2.3},
                {'feature': 'total_fixations', 'vif': 4.8},
                ...
            ]
        """
        vif_data = []

        for i, feature in enumerate(X_subset.columns):
            vif_value = variance_inflation_factor(X_subset.values, i)
            vif_data.append({
                'feature': feature,
                'vif': float(vif_value)
            })

        # 按VIF降序排序
        vif_data.sort(key=lambda x: x['vif'], reverse=True)

        return vif_data

    def remove_high_vif_features(self, vif_results: List[Dict],
                                 threshold: float = 5.0) -> List[str]:
        """
        迭代移除高VIF特征

        算法：
        1. 找到VIF最高的特征
        2. 如果VIF > threshold，移除该特征
        3. 重新计算剩余特征的VIF
        4. 重复直到所有VIF < threshold

        Returns:
            filtered_features: 过滤后的特征列表
        """
        current_features = [item['feature'] for item in vif_results]

        while True:
            X_current = self.X[current_features]
            vif_current = self.compute_vif(X_current)

            max_vif_item = max(vif_current, key=lambda x: x['vif'])

            if max_vif_item['vif'] < threshold:
                break

            # 移除VIF最高的特征
            current_features.remove(max_vif_item['feature'])

            if len(current_features) <= 1:
                break

        return current_features
```

---

### 4.3 扩展Service层

```python
# service.py (扩展现有类)

class FeatureExtractionService:
    # ... 现有代码 ...

    def compute_hybrid_selection(self, data_version: str = 'v1',
                                 mode: str = 'fast') -> Dict:
        """
        混合特征选择（方案C）

        Args:
            data_version: 数据版本
            mode: 'fast'（仅阶段1+2）或 'precise'（全部三阶段）

        Returns:
            完整报告
        """
        logger.info(f"开始混合特征选择 (mode={mode})")

        # 1. 加载所有候选特征
        X, y, groups, feature_names = self._load_all_features(data_version)

        # 2. 初始化混合选择器
        from .hybrid_selector import HybridFeatureSelector

        selector = HybridFeatureSelector(X, y, feature_names, groups)

        # 3. 运行阶段1
        stage1_results = selector.run_stage1_filter(top_k=15)
        logger.info(f"阶段1完成: {len(stage1_results['top_features'])} 候选特征")

        # 4. 运行阶段2
        stage2_results = selector.run_stage2_validation(
            threshold_corr=0.25,
            threshold_vif=5.0
        )
        logger.info(f"阶段2完成: {len(stage2_results['filtered_features'])} 特征通过验证")

        # 5. 根据mode决定是否运行阶段3
        if mode == 'precise':
            stage3_results = selector.run_stage3_wrapper(final_k=10, cv_folds=5)
            logger.info(f"阶段3完成: 最优方法 = {stage3_results['best_method']}")
        else:
            stage3_results = None
            logger.info("快速模式: 跳过阶段3")

        # 6. 生成报告
        report = selector.generate_report() if mode == 'precise' else {
            'stage1_filter': stage1_results,
            'stage2_validation': stage2_results,
            'mode': 'fast',
            'note': '快速模式仅完成Filter和验证，建议运行精确模式获得最优特征'
        }

        # 7. 缓存结果
        cache_file = self.cache_dir / f'hybrid_selection_{mode}_{data_version}.json'
        with open(cache_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    def _load_all_features(self, data_version: str) -> Tuple:
        """
        加载所有候选特征

        Returns:
            (X, y, groups, feature_names)
        """
        # Module04特征
        m04_features = self._load_m04_features(
            data_version=data_version,
            groups=['control', 'mci', 'ad'],
            velocity_threshold=40.0,
            min_fixation_duration=100
        )

        # Module05特征（假设已预计算）
        m05_file = self.base_dir / f"data/05_rqa_analysis/results/m1_tau1_eps0.051_lmin2/step3_feature_enrichment/enriched_features.csv"
        m05_features = pd.read_csv(m05_file)
        m05_features.columns = m05_features.columns.str.lower()

        # 合并（按subject_id）
        merged = m04_features.merge(
            m05_features,
            on=['subject_id', 'group'],
            how='inner'
        )

        # 提取特征矩阵和目标
        feature_cols = [c for c in merged.columns
                       if c not in ['subject_id', 'group', 'task_id']
                       and 'mmse' not in c.lower()]

        X = merged[feature_cols]
        y = merged['mmse_total_score']  # 假设已加载MMSE
        groups = merged['group']

        return X, y, groups, feature_cols
```

---

### 4.4 扩展API路由

```python
# api.py (扩展)

from flask import Blueprint, request, jsonify

m06_bp = Blueprint('module06', __name__, url_prefix='/api/m06')


@m06_bp.route('/hybrid/run', methods=['POST'])
def run_hybrid_selection():
    """
    运行混合特征选择

    Request Body:
    {
        "data_version": "v1",
        "mode": "fast" | "precise"
    }

    Response:
    {
        "success": true,
        "data": {
            "stage1_filter": {...},
            "stage2_validation": {...},
            "stage3_wrapper": {...},  // 仅precise模式
            "final_features": [...],
            "comparison_with_baseline": {...}
        }
    }
    """
    try:
        data = request.get_json()
        data_version = data.get('data_version', 'v1')
        mode = data.get('mode', 'fast')

        if mode not in ['fast', 'precise']:
            return jsonify({
                'success': False,
                'error': "mode必须是'fast'或'precise'"
            }), 400

        service = FeatureExtractionService()
        report = service.compute_hybrid_selection(
            data_version=data_version,
            mode=mode
        )

        return jsonify({
            'success': True,
            'data': report
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@m06_bp.route('/hybrid/compare', methods=['GET'])
def compare_methods():
    """
    对比不同特征选择方法

    Query Params:
    - data_version: v1/v2

    Response:
    {
        "success": true,
        "data": {
            "anova": {
                "features": [...],
                "r2_mean": 0.65,
                "r2_std": 0.08
            },
            "f_regression": {...},
            "mutual_info": {...},
            "hybrid": {...}
        }
    }
    """
    # 实现对比逻辑
    pass


@m06_bp.route('/hybrid/visualization', methods=['GET'])
def get_visualization_data():
    """
    获取可视化数据

    Response:
    {
        "success": true,
        "data": {
            "feature_importance_comparison": [...],
            "correlation_heatmap": [...],
            "cv_scores_boxplot": [...]
        }
    }
    """
    # 返回前端绘图所需数据
    pass
```

---

## 5. 前端设计

### 5.1 新增组件结构

```
frontend/src/components/Module06/
├── HybridSelectionPanel.jsx          # 混合选择主面板（新增）
├── Stage1FilterView.jsx              # 阶段1可视化（新增）
├── Stage2ValidationView.jsx          # 阶段2可视化（新增）
├── Stage3WrapperView.jsx             # 阶段3可视化（新增）
├── ComparisonView.jsx                # 方法对比视图（新增）
├── FeatureImportanceChart.jsx        # 特征重要性图表（新增）
└── ProgressTimeline.jsx              # 进度时间线（新增）
```

---

### 5.2 主面板UI设计

#### **HybridSelectionPanel.jsx**

```jsx
import React, { useState } from 'react';
import { Card, Steps, Button, Select, Space, Alert, Spin, Tabs } from 'antd';
import { PlayCircleOutlined, ExperimentOutlined, CompareOutlined } from '@ant-design/icons';
import axios from 'axios';

import Stage1FilterView from './Stage1FilterView';
import Stage2ValidationView from './Stage2ValidationView';
import Stage3WrapperView from './Stage3WrapperView';
import ComparisonView from './ComparisonView';

const { Step } = Steps;
const { Option } = Select;
const { TabPane } = Tabs;

const HybridSelectionPanel = () => {
  const [mode, setMode] = useState('fast'); // 'fast' | 'precise'
  const [dataVersion, setDataVersion] = useState('v1');
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [results, setResults] = useState(null);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setCurrentStep(0);

    try {
      const response = await axios.post('http://127.0.0.1:9090/api/m06/hybrid/run', {
        data_version: dataVersion,
        mode: mode
      });

      if (response.data.success) {
        setResults(response.data.data);
        setCurrentStep(mode === 'precise' ? 3 : 2);
        message.success(`${mode === 'precise' ? '精确' : '快速'}模式分析完成！`);
      }
    } catch (error) {
      message.error('分析失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 控制面板 */}
      <Card title="混合特征选择（方案C）">
        <Space size="large">
          <div>
            <label>数据版本: </label>
            <Select value={dataVersion} onChange={setDataVersion} style={{ width: 100 }}>
              <Option value="v1">V1</Option>
              <Option value="v2">V2</Option>
            </Select>
          </div>

          <div>
            <label>模式: </label>
            <Select value={mode} onChange={setMode} style={{ width: 150 }}>
              <Option value="fast">快速模式 (~2分钟)</Option>
              <Option value="precise">精确模式 (~10分钟)</Option>
            </Select>
          </div>

          <Button
            type="primary"
            icon={<ExperimentOutlined />}
            onClick={handleRunAnalysis}
            loading={loading}
            size="large"
          >
            运行分析
          </Button>
        </Space>

        <Alert
          message={mode === 'fast'
            ? '快速模式：仅运行阶段1（Filter）和阶段2（验证），适合初步探索'
            : '精确模式：完整运行三阶段，使用交叉验证选出最优特征子集'}
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </Card>

      {/* 进度指示 */}
      {loading && (
        <Card>
          <Steps current={currentStep}>
            <Step title="阶段1: Filter预筛选" description="ANOVA + F-regression + MI" />
            <Step title="阶段2: 回归验证" description="相关性 + VIF" />
            <Step title="阶段3: Wrapper精选" description="RFE + Lasso + RF" />
          </Steps>
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Spin size="large" tip={`正在执行${['阶段1', '阶段2', '阶段3'][currentStep]}...`} />
          </div>
        </Card>
      )}

      {/* 结果展示 */}
      {results && !loading && (
        <Tabs defaultActiveKey="stages" size="large">
          <TabPane tab="📊 分阶段结果" key="stages">
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Stage1FilterView data={results.stage1_filter} />
              <Stage2ValidationView data={results.stage2_validation} />
              {mode === 'precise' && (
                <Stage3WrapperView data={results.stage3_wrapper} />
              )}
            </Space>
          </TabPane>

          <TabPane tab="🔬 方法对比" key="comparison">
            <ComparisonView data={results.comparison_with_baseline} />
          </TabPane>

          <TabPane tab="✅ 最终特征" key="final">
            <Card title="最终选出的10个特征">
              <FinalFeaturesTable
                features={results.final_features}
                method={results.stage3_wrapper?.best_method || 'Stage2'}
              />
            </Card>
          </TabPane>
        </Tabs>
      )}
    </Space>
  );
};

export default HybridSelectionPanel;
```

---

### 5.3 阶段视图组件

#### **Stage1FilterView.jsx**

```jsx
import React from 'react';
import { Card, Table, Row, Col, Statistic } from 'antd';
import { Bar } from '@ant-design/charts';

const Stage1FilterView = ({ data }) => {
  if (!data) return null;

  // 准备柱状图数据
  const chartData = data.top_features.map((feature, index) => ({
    feature: feature,
    ANOVA: data.anova_scores[index],
    'F-regression': data.freg_scores[index],
    'Mutual Info': data.mi_scores[index]
  })).flatMap(item => [
    { feature: item.feature, method: 'ANOVA', score: item.ANOVA },
    { feature: item.feature, method: 'F-regression', score: item['F-regression'] },
    { feature: item.feature, method: 'Mutual Info', score: item['Mutual Info'] }
  ]);

  const config = {
    data: chartData,
    xField: 'score',
    yField: 'feature',
    seriesField: 'method',
    isGroup: true,
    legend: { position: 'top-right' }
  };

  return (
    <Card title="🔍 阶段1: Filter预筛选结果">
      <Row gutter={16}>
        <Col span={8}>
          <Statistic title="候选特征数" value={27} />
        </Col>
        <Col span={8}>
          <Statistic title="筛选出特征数" value={data.top_features.length} />
        </Col>
        <Col span={8}>
          <Statistic title="执行时间" value={data.execution_time.toFixed(1)} suffix="秒" />
        </Col>
      </Row>

      <div style={{ marginTop: 24 }}>
        <h4>三种方法得分对比</h4>
        <Bar {...config} />
      </div>
    </Card>
  );
};

export default Stage1FilterView;
```

#### **Stage2ValidationView.jsx**

```jsx
import React from 'react';
import { Card, Table, Tag, Tooltip } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

const Stage2ValidationView = ({ data }) => {
  if (!data) return null;

  const columns = [
    {
      title: '特征名称',
      dataIndex: 'feature',
      key: 'feature',
      fixed: 'left'
    },
    {
      title: 'Pearson r',
      dataIndex: 'pearson_r',
      key: 'pearson_r',
      render: (val) => {
        const color = Math.abs(val) >= 0.5 ? 'green' : Math.abs(val) >= 0.3 ? 'orange' : 'red';
        return <Tag color={color}>{val.toFixed(3)}</Tag>;
      },
      sorter: (a, b) => Math.abs(b.pearson_r) - Math.abs(a.pearson_r)
    },
    {
      title: 'Spearman r',
      dataIndex: 'spearman_r',
      key: 'spearman_r',
      render: (val) => val.toFixed(3)
    },
    {
      title: 'VIF',
      dataIndex: 'vif',
      key: 'vif',
      render: (val, record) => {
        const vif = data.vif_analysis.find(v => v.feature === record.feature)?.vif || 0;
        const color = vif < 5 ? 'green' : vif < 10 ? 'orange' : 'red';
        return <Tag color={color}>{vif.toFixed(2)}</Tag>;
      }
    },
    {
      title: '通过验证',
      key: 'passed',
      render: (_, record) => {
        const passed = data.filtered_features.includes(record.feature);
        return passed ?
          <CheckCircleOutlined style={{ color: 'green', fontSize: 20 }} /> :
          <CloseCircleOutlined style={{ color: 'red', fontSize: 20 }} />;
      }
    }
  ];

  const tableData = data.correlation_analysis;

  return (
    <Card title="✅ 阶段2: 回归验证结果">
      <div style={{ marginBottom: 16 }}>
        <Tag color="green">通过: {data.filtered_features.length}</Tag>
        <Tag color="red">移除: {data.removed_features.length}</Tag>
        <span style={{ marginLeft: 16, color: '#888' }}>
          移除原因：低相关性（|r| < 0.25）或高共线性（VIF > 5）
        </span>
      </div>

      <Table
        columns={columns}
        dataSource={tableData}
        rowKey="feature"
        pagination={{ pageSize: 15 }}
        scroll={{ x: 1000 }}
      />
    </Card>
  );
};

export default Stage2ValidationView;
```

#### **Stage3WrapperView.jsx**

```jsx
import React from 'react';
import { Card, Table, Row, Col, Statistic, Badge } from 'antd';
import { Column } from '@ant-design/charts';

const Stage3WrapperView = ({ data }) => {
  if (!data) return null;

  // 交叉验证得分对比
  const cvData = Object.entries(data.cv_scores).map(([method, scores]) => ({
    method: method,
    r2: scores.r2_mean
  }));

  const chartConfig = {
    data: cvData,
    xField: 'method',
    yField: 'r2',
    label: {
      position: 'top',
      formatter: (datum) => `R² = ${datum.r2.toFixed(3)}`
    },
    columnStyle: {
      fill: ({ method }) => {
        if (method === data.best_method) return '#52c41a';
        return '#1890ff';
      }
    }
  };

  return (
    <Card title="🏆 阶段3: Wrapper精选结果">
      <Row gutter={16}>
        <Col span={6}>
          <Statistic
            title="最优方法"
            value={data.best_method}
            prefix={<Badge status="success" />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="最优R²"
            value={data.cv_scores[data.best_method].r2_mean.toFixed(3)}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="标准差"
            value={data.cv_scores[data.best_method].r2_std.toFixed(3)}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="执行时间"
            value={data.execution_time.toFixed(1)}
            suffix="秒"
          />
        </Col>
      </Row>

      <div style={{ marginTop: 24 }}>
        <h4>三种Wrapper方法性能对比（5折交叉验证）</h4>
        <Column {...chartConfig} />
      </div>

      <div style={{ marginTop: 24 }}>
        <h4>最终选出的10个特征</h4>
        <div>
          {data.final_features.map((f, i) => (
            <Tag key={i} color="green" style={{ margin: 4 }}>{f}</Tag>
          ))}
        </div>
      </div>
    </Card>
  );
};

export default Stage3WrapperView;
```

---

### 5.4 对比视图

#### **ComparisonView.jsx**

```jsx
import React from 'react';
import { Card, Row, Col, Statistic, Table, Alert } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { Radar } from '@ant-design/charts';

const ComparisonView = ({ data }) => {
  if (!data) return null;

  const improvement = data.improvement.relative_pct;
  const isImproved = improvement > 0;

  const columns = [
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method'
    },
    {
      title: '选出的特征',
      dataIndex: 'features',
      key: 'features',
      render: (features) => features.join(', ')
    },
    {
      title: 'R² (均值)',
      dataIndex: 'r2_mean',
      key: 'r2_mean',
      sorter: (a, b) => a.r2_mean - b.r2_mean
    },
    {
      title: 'R² (标准差)',
      dataIndex: 'r2_std',
      key: 'r2_std'
    }
  ];

  const tableData = [
    {
      method: 'Baseline (ANOVA)',
      features: data.baseline_features,
      r2_mean: data.baseline_r2.mean.toFixed(3),
      r2_std: data.baseline_r2.std.toFixed(3)
    },
    {
      method: `Hybrid (${data.hybrid_method})`,
      features: data.hybrid_features,
      r2_mean: data.hybrid_r2.mean.toFixed(3),
      r2_std: data.hybrid_r2.std.toFixed(3)
    }
  ];

  return (
    <Card title="📈 方法对比: Baseline vs Hybrid">
      <Alert
        message={isImproved ? '性能提升 ✅' : '性能下降 ⚠️'}
        description={`混合方法相比Baseline ${isImproved ? '提升' : '降低'} ${Math.abs(improvement).toFixed(2)}%`}
        type={isImproved ? 'success' : 'warning'}
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="Baseline R²"
            value={data.baseline_r2.mean}
            precision={3}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Hybrid R²"
            value={data.hybrid_r2.mean}
            precision={3}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="改进幅度"
            value={Math.abs(improvement)}
            precision={2}
            suffix="%"
            prefix={isImproved ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            valueStyle={{ color: isImproved ? '#3f8600' : '#cf1322' }}
          />
        </Col>
      </Row>

      <Table
        columns={columns}
        dataSource={tableData}
        rowKey="method"
        pagination={false}
        style={{ marginTop: 24 }}
      />
    </Card>
  );
};

export default ComparisonView;
```

---

## 6. API接口设计

### 6.1 完整API列表

| 端点 | 方法 | 描述 | 预计耗时 |
|------|------|------|---------|
| `/api/m06/hybrid/run` | POST | 运行混合特征选择 | 2-10分钟 |
| `/api/m06/hybrid/status` | GET | 查询任务状态（如果异步） | <1秒 |
| `/api/m06/hybrid/compare` | GET | 对比不同方法 | <5秒 |
| `/api/m06/hybrid/visualization` | GET | 获取可视化数据 | <2秒 |
| `/api/m06/hybrid/export` | POST | 导出特征子集 | <5秒 |

### 6.2 详细接口规范

见上文API路由设计部分（4.4节）

---

## 7. 数据流程

```
用户操作
   ↓
前端: 选择模式（fast/precise）
   ↓
后端: HybridFeatureSelector.run_stage1_filter()
   ├─ FilterMethods.compute_anova_scores()
   ├─ FilterMethods.compute_f_regression_scores()
   └─ FilterMethods.compute_mutual_info_scores()
   ↓
   投票选出Top-15
   ↓
后端: HybridFeatureSelector.run_stage2_validation()
   ├─ ValidationUtils.compute_correlations()
   └─ ValidationUtils.compute_vif()
   ↓
   过滤到12-13个特征
   ↓
后端: HybridFeatureSelector.run_stage3_wrapper() [仅precise模式]
   ├─ WrapperMethods.run_rfe()
   ├─ WrapperMethods.run_lasso()
   └─ WrapperMethods.run_random_forest()
   ↓
   交叉验证选最优 → Top-10
   ↓
后端: 对比Baseline（ANOVA）
   ↓
前端: 展示三阶段结果 + 对比
   ↓
用户: 下载特征子集 / 导出报告
```

---

## 8. 实施步骤

### 第1天: 后端核心逻辑
- [ ] 实现`FilterMethods`类（3种Filter方法）
- [ ] 实现`ValidationUtils`类（相关性 + VIF）
- [ ] 单元测试：验证各方法输出正确性

### 第2天: Wrapper方法
- [ ] 实现`WrapperMethods`类（RFE + Lasso + RF）
- [ ] 实现交叉验证评估逻辑
- [ ] 测试：确保特征选择结果合理

### 第3天: 集成HybridSelector
- [ ] 实现`HybridFeatureSelector`主类
- [ ] 集成三阶段流程
- [ ] 实现Baseline对比逻辑

### 第4天: Service和API层
- [ ] 扩展`FeatureExtractionService`
- [ ] 添加API路由
- [ ] 测试API端到端

### 第5天: 前端UI
- [ ] 实现`HybridSelectionPanel`主面板
- [ ] 实现三个阶段视图组件
- [ ] 实现对比视图

### 第6天: 可视化优化
- [ ] 添加特征重要性图表
- [ ] 添加相关性热力图
- [ ] 优化交互体验

### 第7天: 测试与优化
- [ ] 端到端测试
- [ ] 性能优化（缓存、并行）
- [ ] 文档完善

---

## 9. 测试验证

### 9.1 功能测试

```python
# test_hybrid_selector.py

import pytest
import pandas as pd
import numpy as np
from src.modules.module06_feature_extraction.hybrid_selector import HybridFeatureSelector


def test_stage1_filter():
    """测试阶段1: Filter预筛选"""
    # 构造模拟数据
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(300, 27), columns=[f'feat_{i}' for i in range(27)])
    y = pd.Series(np.random.randint(20, 30, 300))
    groups = pd.Series(['control'] * 100 + ['mci'] * 100 + ['ad'] * 100)

    selector = HybridFeatureSelector(X, y, X.columns.tolist(), groups)
    results = selector.run_stage1_filter(top_k=15)

    assert len(results['top_features']) == 15
    assert 'anova_scores' in results
    assert 'freg_scores' in results
    assert 'mi_scores' in results


def test_stage2_validation():
    """测试阶段2: 回归验证"""
    # ... 类似测试逻辑


def test_stage3_wrapper():
    """测试阶段3: Wrapper精选"""
    # ... 类似测试逻辑


def test_end_to_end():
    """端到端测试"""
    # 使用真实数据测试完整流程
    pass
```

### 9.2 性能验证

**预期执行时间（300样本）：**
- 阶段1: 60秒
- 阶段2: 30秒
- 阶段3: 5-10分钟（取决于交叉验证）

**总耗时：**
- 快速模式: ~2分钟
- 精确模式: ~10分钟

---

## 10. 预期效果

### 10.1 性能提升预期

根据文献和经验，预期混合方法相比Baseline的提升：

| 指标 | Baseline (ANOVA) | Hybrid (预期) | 提升 |
|------|-----------------|--------------|------|
| R² | 0.60 - 0.70 | 0.65 - 0.75 | +5-10% |
| MAE | 2.5 - 3.0 | 2.2 - 2.8 | -8-12% |
| 特征冗余度 | 中等 | 低 | ✅ |
| 可解释性 | 高 | 中-高 | ⚠️ |

### 10.2 可解释性提升

- ✅ **三阶段透明度**：每阶段都有明确的评估指标
- ✅ **多方法对比**：用户可看到不同方法的特征重要性
- ✅ **统计验证**：相关性、VIF提供额外证据
- ✅ **交叉验证**：避免过拟合，结果更可靠

---

## 11. 文献参考

1. **Guyon & Elisseeff (2003).** *An Introduction to Variable and Feature Selection.* JMLR.
2. **Kohavi & John (1997).** *Wrappers for Feature Selection.* Artificial Intelligence.
3. **Saeys et al. (2007).** *A review of feature selection techniques in bioinformatics.* Bioinformatics.
4. **Bolón-Canedo et al. (2015).** *A review of microarray datasets and applied feature selection methods.* Information Sciences.

---

## 12. 附录：配置文件示例

```yaml
# config/module06_hybrid.yaml

hybrid_selection:
  stage1_filter:
    methods:
      - anova
      - f_regression
      - mutual_info
    top_k: 15
    voting_strategy: borda_count

  stage2_validation:
    correlation_threshold: 0.25
    vif_threshold: 5.0
    correlation_methods:
      - pearson
      - spearman

  stage3_wrapper:
    methods:
      - rfe
      - lasso
      - random_forest
    final_k: 10
    cv_folds: 5
    mlp_config:
      hidden_layers: [64, 32, 16]
      max_iter: 1000
      early_stopping: true
```

---

**文档版本**: 1.0
**创建日期**: 2025-10-12
**作者**: Claude
**状态**: 设计阶段
