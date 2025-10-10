# Module04 特征敏感度分析设计文档

**文档版本**: v1.0
**创建日期**: 2025-10-10
**目的**: 为Module06特征选择提供数据驱动的敏感度分析

---

## 1. 设计目标

### 1.1 核心需求
- 分析Module04的**9个眼动特征**(排除MMSE分数)在Control/MCI/AD三组间的区分能力
- 提供**多维度敏感度指标**,不仅仅是单一的F-statistic
- 支持**任务级别**和**全局级别**的敏感度分析
- 输出排序结果,供Module06策略A选择**Top-4特征**

### 1.2 可用特征列表 (9维)

基于Module04实际输出,**排除标签相关特征**:

```python
AVAILABLE_FEATURES = [
    # ROI占比特征 (3维)
    "bg_ratio_frame",           # 背景区域占比 (%)
    "inst_ratio_frame",         # 指令区域占比 (%)
    "kw_ratio_frame",           # 关键词区域占比 (%)

    # 注视特征 (3维)
    "total_fixation_time",      # 总注视时长 (ms)
    "total_fixations",          # 总注视次数 (count)
    "avg_fixation_duration",    # 平均注视时长 (ms)

    # 扫视特征 (2维)
    "total_saccades",           # 总扫视次数 (count)
    "avg_saccade_amplitude",    # 平均扫视幅度 (deg)

    # 时间特征 (1维)
    "task_total_time"           # 任务总时长 (ms)
]

# 排除的特征 (标签相关)
EXCLUDED_FEATURES = [
    "mmse_total_score",   # 总分 - 直接标签
    "mmse_task_score"     # 任务分数 - 直接标签
]
```

---

## 2. 敏感度分析方法

### 2.1 多维度评估指标

为了全面评估特征的区分能力,采用**5个互补的统计指标**:

#### 指标1: One-Way ANOVA F-statistic
**目的**: 检验三组均值是否有显著差异

```python
from scipy.stats import f_oneway

def compute_f_statistic(feature_name, df):
    """
    计算单因素方差分析F统计量

    H0: μ_control = μ_mci = μ_ad (三组均值相等)
    H1: 至少有一组均值不同
    """
    control = df[df['group'] == 'control'][feature_name].dropna()
    mci = df[df['group'] == 'mci'][feature_name].dropna()
    ad = df[df['group'] == 'ad'][feature_name].dropna()

    f_stat, p_value = f_oneway(control, mci, ad)

    return {
        'f_statistic': f_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
```

**解释**:
- F值越大,组间差异越显著
- p < 0.05 表示统计显著

#### 指标2: Effect Size (Eta-Squared)
**目的**: 量化效应大小,不受样本量影响

```python
def compute_effect_size(feature_name, df):
    """
    计算效应量 (Eta-squared)

    η² = SS_between / SS_total
    表示组别因素解释的方差比例

    解释标准 (Cohen's):
    - 0.01 - 0.06: 小效应
    - 0.06 - 0.14: 中等效应
    - 0.14+:        大效应
    """
    control = df[df['group'] == 'control'][feature_name].dropna()
    mci = df[df['group'] == 'mci'][feature_name].dropna()
    ad = df[df['group'] == 'ad'][feature_name].dropna()

    # 总均值
    grand_mean = df[feature_name].mean()

    # 组间平方和 (SS_between)
    n_control, n_mci, n_ad = len(control), len(mci), len(ad)
    ss_between = (
        n_control * (control.mean() - grand_mean) ** 2 +
        n_mci * (mci.mean() - grand_mean) ** 2 +
        n_ad * (ad.mean() - grand_mean) ** 2
    )

    # 总平方和 (SS_total)
    ss_total = ((df[feature_name] - grand_mean) ** 2).sum()

    eta_squared = ss_between / ss_total if ss_total > 0 else 0

    # 效应大小分类
    if eta_squared < 0.01:
        effect_label = "negligible"
    elif eta_squared < 0.06:
        effect_label = "small"
    elif eta_squared < 0.14:
        effect_label = "medium"
    else:
        effect_label = "large"

    return {
        'eta_squared': eta_squared,
        'effect_size': effect_label
    }
```

#### 指标3: Pairwise T-tests (两两比较)
**目的**: 确定哪些组对之间有显著差异

```python
from scipy.stats import ttest_ind

def compute_pairwise_tests(feature_name, df):
    """
    执行两两t检验 (Bonferroni校正)

    比较:
    - Control vs MCI
    - Control vs AD
    - MCI vs AD
    """
    control = df[df['group'] == 'control'][feature_name].dropna()
    mci = df[df['group'] == 'mci'][feature_name].dropna()
    ad = df[df['group'] == 'ad'][feature_name].dropna()

    # 两两t检验
    t_control_mci, p_control_mci = ttest_ind(control, mci)
    t_control_ad, p_control_ad = ttest_ind(control, ad)
    t_mci_ad, p_mci_ad = ttest_ind(mci, ad)

    # Bonferroni校正 (3次比较,显著性阈值 = 0.05/3 = 0.0167)
    bonferroni_alpha = 0.05 / 3

    return {
        'control_vs_mci': {
            't_stat': t_control_mci,
            'p_value': p_control_mci,
            'significant': p_control_mci < bonferroni_alpha
        },
        'control_vs_ad': {
            't_stat': t_control_ad,
            'p_value': p_control_ad,
            'significant': p_control_ad < bonferroni_alpha
        },
        'mci_vs_ad': {
            't_stat': t_mci_ad,
            'p_value': p_mci_ad,
            'significant': p_mci_ad < bonferroni_alpha
        }
    }
```

**解释**:
- 有助于理解特征在疾病进展不同阶段的表现
- 例如: 某特征在Control vs AD显著,但MCI vs AD不显著 → 早期诊断能力差

#### 指标4: Cohen's d (标准化均值差)
**目的**: 量化两组间的实际差异大小

```python
def compute_cohens_d(group1, group2):
    """
    计算Cohen's d

    d = (μ1 - μ2) / s_pooled

    解释标准:
    - |d| < 0.2: 极小差异
    - 0.2 ≤ |d| < 0.5: 小差异
    - 0.5 ≤ |d| < 0.8: 中等差异
    - |d| ≥ 0.8: 大差异
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()

    # 合并标准差
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    cohens_d = (group1.mean() - group2.mean()) / pooled_std if pooled_std > 0 else 0

    return cohens_d
```

#### 指标5: 组内变异系数 (CV)
**目的**: 评估特征稳定性,低CV意味着组内一致性高

```python
def compute_coefficient_of_variation(feature_name, df):
    """
    计算各组的变异系数 (CV)

    CV = σ / μ × 100%

    低CV → 特征稳定,组内一致性高
    高CV → 特征波动大,可能噪声多
    """
    control = df[df['group'] == 'control'][feature_name].dropna()
    mci = df[df['group'] == 'mci'][feature_name].dropna()
    ad = df[df['group'] == 'ad'][feature_name].dropna()

    cv_control = (control.std() / control.mean() * 100) if control.mean() != 0 else 0
    cv_mci = (mci.std() / mci.mean() * 100) if mci.mean() != 0 else 0
    cv_ad = (ad.std() / ad.mean() * 100) if ad.mean() != 0 else 0

    return {
        'cv_control': cv_control,
        'cv_mci': cv_mci,
        'cv_ad': cv_ad,
        'avg_cv': (cv_control + cv_mci + cv_ad) / 3
    }
```

### 2.2 综合敏感度得分

**融合5个指标为单一得分**,用于排序:

```python
def compute_sensitivity_score(f_stat, eta_squared, p_value, avg_cv):
    """
    综合敏感度得分计算

    Score = (F × η²) / (1 + p_value) × (1 / (1 + CV/100))

    设计理念:
    - F统计量和效应量越大越好
    - p值越小越好
    - 变异系数越小越好 (稳定性高)
    """
    # 防止除零
    p_value = max(p_value, 1e-10)

    # 核心得分: F统计量 × 效应量
    core_score = f_stat * eta_squared

    # p值惩罚因子
    significance_factor = 1 / (1 + p_value)

    # 稳定性奖励因子 (CV越低,因子越高)
    stability_factor = 1 / (1 + avg_cv / 100)

    sensitivity_score = core_score * significance_factor * stability_factor

    return sensitivity_score
```

---

## 3. API设计

### 3.1 端点1: 全局敏感度分析

**路径**: `GET /api/m04/sensitivity/compute-features`

**功能**: 计算所有9个特征在全部300个样本上的敏感度

**查询参数**:
```python
{
    "data_version": "v1",  # 可选,默认v1
    "sort_by": "sensitivity_score",  # 可选: sensitivity_score, f_statistic, eta_squared
    "order": "desc"  # 可选: asc, desc
}
```

**响应示例**:
```json
{
    "success": true,
    "data_version": "v1",
    "total_samples": 300,
    "features": [
        {
            "feature_name": "avg_fixation_duration",
            "rank": 1,
            "statistics": {
                "f_statistic": 45.23,
                "p_value": 0.00012,
                "eta_squared": 0.234,
                "effect_size": "large"
            },
            "pairwise_tests": {
                "control_vs_mci": {"t_stat": 3.45, "p_value": 0.001, "significant": true},
                "control_vs_ad": {"t_stat": 6.78, "p_value": 0.00001, "significant": true},
                "mci_vs_ad": {"t_stat": 2.89, "p_value": 0.005, "significant": true}
            },
            "cohens_d": {
                "control_vs_mci": 0.45,
                "control_vs_ad": 0.89,
                "mci_vs_ad": 0.38
            },
            "variability": {
                "cv_control": 12.5,
                "cv_mci": 15.3,
                "cv_ad": 18.7,
                "avg_cv": 15.5
            },
            "sensitivity_score": 8.345,
            "group_means": {
                "control": 245.67,
                "mci": 268.34,
                "ad": 289.12
            },
            "group_stds": {
                "control": 30.7,
                "mci": 41.0,
                "ad": 54.1
            }
        },
        {
            "feature_name": "kw_ratio_frame",
            "rank": 2,
            "statistics": {...},
            ...
        },
        ...
    ],
    "summary": {
        "top_3_features": ["avg_fixation_duration", "kw_ratio_frame", "avg_saccade_amplitude"],
        "highly_significant_count": 6,  # p < 0.01
        "large_effect_count": 4  # eta_squared > 0.14
    }
}
```

### 3.2 端点2: 任务级敏感度分析

**路径**: `GET /api/m04/sensitivity/compute-features-by-task`

**功能**: 分别计算每个任务(q1-q5)上的特征敏感度

**查询参数**:
```python
{
    "data_version": "v1",
    "task_id": "q1"  # 可选,不提供则返回所有任务
}
```

**响应示例**:
```json
{
    "success": true,
    "data_version": "v1",
    "tasks": {
        "q1": {
            "total_samples": 60,
            "features": [
                {
                    "feature_name": "kw_ratio_frame",
                    "rank": 1,
                    "sensitivity_score": 4.567,
                    ...
                },
                ...
            ],
            "top_3_features": ["kw_ratio_frame", "inst_ratio_frame", "avg_fixation_duration"]
        },
        "q2": {...},
        "q3": {...},
        "q4": {...},
        "q5": {...}
    },
    "task_consistency": {
        "avg_fixation_duration": {
            "appears_in_top3": ["q1", "q2", "q3", "q5"],
            "consistency_score": 0.8  # 4/5 = 80%
        },
        ...
    }
}
```

### 3.3 端点3: 特征对比可视化数据

**路径**: `GET /api/m04/sensitivity/feature-comparison`

**功能**: 提供箱线图、小提琴图数据

**查询参数**:
```python
{
    "feature_names": ["avg_fixation_duration", "kw_ratio_frame"],
    "data_version": "v1"
}
```

**响应示例**:
```json
{
    "success": true,
    "features": {
        "avg_fixation_duration": {
            "control": [245.3, 250.1, 239.8, ...],  // 100个数据点
            "mci": [268.5, 271.2, ...],
            "ad": [289.3, 295.1, ...]
        },
        "kw_ratio_frame": {
            "control": [35.2, 38.5, ...],
            "mci": [28.9, 25.3, ...],
            "ad": [18.7, 15.2, ...]
        }
    }
}
```

---

## 4. 实施架构

### 4.1 新增模块文件

```
src/modules/module04_event_analysis/
├── sensitivity_analyzer.py    # 新增: 敏感度分析核心逻辑
└── api.py                      # 修改: 添加3个新端点
```

### 4.2 sensitivity_analyzer.py 实现

```python
"""
Module04 特征敏感度分析器
"""
import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind
from typing import Dict, List

class SensitivityAnalyzer:
    """特征敏感度分析器"""

    AVAILABLE_FEATURES = [
        "bg_ratio_frame", "inst_ratio_frame", "kw_ratio_frame",
        "total_fixation_time", "total_fixations", "avg_fixation_duration",
        "total_saccades", "avg_saccade_amplitude", "task_total_time"
    ]

    def __init__(self, features_df: pd.DataFrame):
        """
        初始化

        Args:
            features_df: Module04特征数据 (包含subject_id, group, task_id, features)
        """
        self.df = features_df
        self.results = {}

    def compute_all_features(self, sort_by='sensitivity_score') -> Dict:
        """计算所有特征的敏感度"""
        results = []

        for feature_name in self.AVAILABLE_FEATURES:
            feature_result = self._analyze_single_feature(feature_name)
            results.append(feature_result)

        # 按敏感度得分排序
        results = sorted(results, key=lambda x: x[sort_by], reverse=True)

        # 添加排名
        for rank, result in enumerate(results, 1):
            result['rank'] = rank

        return {
            'features': results,
            'summary': self._generate_summary(results)
        }

    def _analyze_single_feature(self, feature_name: str) -> Dict:
        """分析单个特征"""
        # 提取三组数据
        control = self.df[self.df['group'] == 'control'][feature_name].dropna()
        mci = self.df[self.df['group'] == 'mci'][feature_name].dropna()
        ad = self.df[self.df['group'] == 'ad'][feature_name].dropna()

        # 指标1: ANOVA
        f_stat, p_value = f_oneway(control, mci, ad)

        # 指标2: Effect Size
        eta_squared = self._compute_eta_squared(feature_name)

        # 指标3: Pairwise tests
        pairwise = self._compute_pairwise(control, mci, ad)

        # 指标4: Cohen's d
        cohens_d = self._compute_all_cohens_d(control, mci, ad)

        # 指标5: CV
        cv_stats = self._compute_cv(control, mci, ad)

        # 综合得分
        sensitivity_score = self._compute_score(
            f_stat, eta_squared, p_value, cv_stats['avg_cv']
        )

        return {
            'feature_name': feature_name,
            'statistics': {
                'f_statistic': round(f_stat, 4),
                'p_value': round(p_value, 6),
                'eta_squared': round(eta_squared, 4),
                'effect_size': self._classify_effect(eta_squared)
            },
            'pairwise_tests': pairwise,
            'cohens_d': cohens_d,
            'variability': cv_stats,
            'sensitivity_score': round(sensitivity_score, 4),
            'group_means': {
                'control': round(control.mean(), 2),
                'mci': round(mci.mean(), 2),
                'ad': round(ad.mean(), 2)
            },
            'group_stds': {
                'control': round(control.std(), 2),
                'mci': round(mci.std(), 2),
                'ad': round(ad.std(), 2)
            }
        }

    def _compute_eta_squared(self, feature_name: str) -> float:
        """计算Eta-squared"""
        grand_mean = self.df[feature_name].mean()

        ss_between = 0
        for group in ['control', 'mci', 'ad']:
            group_data = self.df[self.df['group'] == group][feature_name].dropna()
            n = len(group_data)
            ss_between += n * (group_data.mean() - grand_mean) ** 2

        ss_total = ((self.df[feature_name] - grand_mean) ** 2).sum()

        return ss_between / ss_total if ss_total > 0 else 0

    def _compute_pairwise(self, control, mci, ad) -> Dict:
        """两两t检验"""
        bonferroni_alpha = 0.05 / 3

        t_cm, p_cm = ttest_ind(control, mci)
        t_ca, p_ca = ttest_ind(control, ad)
        t_ma, p_ma = ttest_ind(mci, ad)

        return {
            'control_vs_mci': {
                't_stat': round(t_cm, 4),
                'p_value': round(p_cm, 6),
                'significant': p_cm < bonferroni_alpha
            },
            'control_vs_ad': {
                't_stat': round(t_ca, 4),
                'p_value': round(p_ca, 6),
                'significant': p_ca < bonferroni_alpha
            },
            'mci_vs_ad': {
                't_stat': round(t_ma, 4),
                'p_value': round(p_ma, 6),
                'significant': p_ma < bonferroni_alpha
            }
        }

    def _compute_all_cohens_d(self, control, mci, ad) -> Dict:
        """计算所有Cohen's d"""
        def cohens_d(g1, g2):
            n1, n2 = len(g1), len(g2)
            var1, var2 = g1.var(), g2.var()
            pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
            return (g1.mean() - g2.mean()) / pooled_std if pooled_std > 0 else 0

        return {
            'control_vs_mci': round(cohens_d(control, mci), 3),
            'control_vs_ad': round(cohens_d(control, ad), 3),
            'mci_vs_ad': round(cohens_d(mci, ad), 3)
        }

    def _compute_cv(self, control, mci, ad) -> Dict:
        """计算变异系数"""
        def cv(group):
            return (group.std() / group.mean() * 100) if group.mean() != 0 else 0

        cv_c, cv_m, cv_a = cv(control), cv(mci), cv(ad)

        return {
            'cv_control': round(cv_c, 2),
            'cv_mci': round(cv_m, 2),
            'cv_ad': round(cv_a, 2),
            'avg_cv': round((cv_c + cv_m + cv_a) / 3, 2)
        }

    def _compute_score(self, f_stat, eta_squared, p_value, avg_cv) -> float:
        """计算综合敏感度得分"""
        p_value = max(p_value, 1e-10)
        core_score = f_stat * eta_squared
        significance_factor = 1 / (1 + p_value)
        stability_factor = 1 / (1 + avg_cv / 100)
        return core_score * significance_factor * stability_factor

    def _classify_effect(self, eta_squared) -> str:
        """效应量分类"""
        if eta_squared < 0.01:
            return "negligible"
        elif eta_squared < 0.06:
            return "small"
        elif eta_squared < 0.14:
            return "medium"
        else:
            return "large"

    def _generate_summary(self, results: List[Dict]) -> Dict:
        """生成汇总统计"""
        return {
            'top_3_features': [r['feature_name'] for r in results[:3]],
            'highly_significant_count': sum(1 for r in results if r['statistics']['p_value'] < 0.01),
            'large_effect_count': sum(1 for r in results if r['statistics']['effect_size'] == 'large')
        }
```

---

## 5. Module06集成

### 5.1 策略A更新

基于敏感度分析结果,**动态选择Top-3特征**:

```python
# 策略A: 从敏感度分析选择Top-3 (不含MMSE)
response = requests.get('/api/m04/sensitivity/compute-features')
top_features = response.json()['summary']['top_3_features']

# 例如可能得到: ['avg_fixation_duration', 'kw_ratio_frame', 'total_saccades']

# 然后从Module05选择最优参数的6维RQA
# 最终: 3 + 6 = 9维特征向量
# 样本比: 300 / 9 = 33.3:1 ✅
```

---

## 6. 实施计划

**Week 1**:
- [ ] 实现 `SensitivityAnalyzer` 类
- [ ] 单元测试 (模拟数据)

**Week 2**:
- [ ] 集成到Module04 API
- [ ] 使用v1真实数据验证
- [ ] 输出特征排序报告

**Week 3**:
- [ ] 更新Module06设计文档
- [ ] 基于实际结果调整策略A特征选择

---

**文档状态**: ✅ 设计完成
**待审核**: 统计方法是否科学合理
**下一步**: 实施 `SensitivityAnalyzer` 类
