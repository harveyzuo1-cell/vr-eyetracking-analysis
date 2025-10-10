# Module06 智能特征提取模块 - 设计论证文档

**文档版本**: v1.0
**创建日期**: 2025-10-10
**作者**: 系统架构团队
**模块名称**: Module06 - Intelligent Feature Extraction & Selection

---

## 📋 目录

1. [执行摘要](#1-执行摘要)
2. [现状分析](#2-现状分析)
3. [特征空间分析](#3-特征空间分析)
4. [科学论证](#4-科学论证)
5. [特征提取策略](#5-特征提取策略)
6. [智能推荐机制](#6-智能推荐机制)
7. [系统架构设计](#7-系统架构设计)
8. [实施路线图](#8-实施路线图)

---

## 1. 执行摘要

### 1.1 背景与挑战

当前系统已完成Module04(眼动事件分析)和Module05(RQA递归量化分析),产生了**大规模的特征空间**:

- **数据规模**: v1数据集 **60受试者** × 5任务(q1-q5) = **300个样本**
  - Control组: 20人
  - MCI组: 20人
  - AD组: 20人
- **RQA参数组合**: 3264+ parameter combinations (m × τ × ε × lmin)
- **特征维度**: Module04约20+维 + Module05约6+维/参数组合 = **潜在19,584+维特征空间**

**核心挑战**:
1. 如何从海量特征中科学地选择有效特征？
2. 哪些特征适合哪类任务？
3. 如何平衡特征完整性和计算效率？
4. **维度灾难**: 300样本 vs 19,584维 = **65.3:1** (极度严重的过拟合风险!)

### 1.2 设计目标

Module06作为**特征提取与选择的智能中枢**,需要实现:

✅ **自动化特征提取**: 从Module04/05输出自动提取标准化特征
✅ **任务自适应推荐**: 根据任务类型智能推荐最优特征子集
✅ **手动配置灵活性**: 支持研究者自定义特征组合
✅ **多粒度特征聚合**: Subject-level, Task-level, Group-level特征
✅ **质量控制与可解释性**: 特征重要性分析和可视化

---

## 2. 现状分析

### 2.1 Module04 眼动事件分析输出

**数据源**: `data/event_analysis_results/` 或 API `/api/m04/features`

#### 2.1.1 核心特征 (~20维)

**时域特征** (Temporal Features):
```python
{
    # 注视特征 (Fixation Features)
    "total_fixations": int,              # 总注视次数
    "mean_fixation_duration": float,     # 平均注视时长 (ms)
    "std_fixation_duration": float,      # 注视时长标准差
    "median_fixation_duration": float,   # 注视时长中位数
    "max_fixation_duration": float,      # 最长注视时长
    "min_fixation_duration": float,      # 最短注视时长

    # 扫视特征 (Saccade Features)
    "total_saccades": int,               # 总扫视次数
    "mean_saccade_amplitude": float,     # 平均扫视幅度 (deg)
    "std_saccade_amplitude": float,      # 扫视幅度标准差
    "mean_saccade_velocity": float,      # 平均扫视速度 (deg/s)
    "peak_saccade_velocity": float,      # 峰值扫视速度

    # 时间比例 (Time Ratios)
    "fixation_duration_ratio": float,    # 注视时长占比
    "saccade_duration_ratio": float      # 扫视时长占比
}
```

**空域特征** (Spatial Features):
```python
{
    # 空间覆盖 (Spatial Coverage)
    "scan_path_length": float,           # 扫描路径总长度 (deg)
    "convex_hull_area": float,           # 凸包面积
    "spatial_density": float,            # 空间密度 (fixations/area)

    # ROI统计 (Region of Interest)
    "roi_hit_count": int,                # ROI命中次数
    "roi_fixation_duration": float,      # ROI内注视总时长
    "roi_first_hit_latency": float       # 首次命中ROI延迟
}
```

**方法论特性**:
- ✅ **逐帧分析法**: 精确的帧级ROI匹配
- ✅ **IVT质心法**: 基于速度阈值的事件检测
- ⚠️ **任务依赖性**: 高度依赖ROI配置,适合结构化任务(q1-q4)

### 2.2 Module05 RQA递归量化分析输出

**数据源**: `data/05_rqa_analysis/[params]/step3_enriched_features.csv`

#### 2.2.1 核心RQA指标 (6维/参数组合)

**1D模式** (x坐标时间序列):
```python
{
    "RR-1D-x": float,       # 递归率 (Recurrence Rate)
    "DET-1D-x": float,      # 确定性 (Determinism)
    "ENT-1D-x": float,      # 熵 (Entropy)
}
```

**2D模式** (x-y轨迹):
```python
{
    "RR-2D-xy": float,      # 2D递归率
    "DET-2D-xy": float,     # 2D确定性
    "ENT-2D-xy": float      # 2D熵
}
```

**增强特征** (Step 3输出):
```python
{
    # 对称性特征
    "x_y_symmetry": float,           # x-y轨迹对称性
    "x_y_diff": float,               # x-y差异度

    # 复杂度特征
    "combined_rr": float,            # 综合递归率
    "rqa_complexity_index": float    # RQA复杂度指数
}
```

#### 2.2.2 参数空间结构

**完整参数组合**: m(1-10) × τ(1-10) × ε(0.05-0.10) × lmin(2-3) = **3,264组合**

**关键参数含义**:
- **m** (Embedding Dimension): 相空间重构维度,反映系统复杂度
- **τ** (Time Delay): 时间延迟,捕捉不同时间尺度的动力学
- **ε** (Threshold): 递归阈值,决定"相似"的判定标准
- **lmin** (Min Line Length): 最小线长,过滤噪声

**方法论特性**:
- ✅ **非线性动力学**: 捕捉眼动的混沌和随机特性
- ✅ **参数敏感性**: Module05已完成敏感性分析,识别最优参数
- ⚠️ **任务独立性**: 不依赖ROI,适合自由浏览任务(q5)

### 2.3 数据组织结构

**样本粒度** (Sample Granularity):
```
数据层级:
├── Group Level (组别层)
│   ├── control (对照组)
│   ├── mci (轻度认知障碍)
│   └── ad (阿尔茨海默症)
├── Subject Level (受试者层)
│   └── 每组约40人
└── Task Level (任务层)
    ├── q1: 目标搜索 (Target Search)
    ├── q2: 场景记忆 (Scene Memory)
    ├── q3: 视觉追踪 (Visual Tracking)
    ├── q4: 空间导航 (Spatial Navigation)
    └── q5: 自由浏览 (Free Viewing)
```

**文件路径示例**:
```
# Module04输出
data/event_analysis_results/control/control_legacy_1_q1_features.json

# Module05输出 (Step 3 - 增强特征)
data/05_rqa_analysis/m2_tau1_eps0.050_lmin2/step3_enriched_features.csv
  → Columns: subject_id, task_id, Group, RR-1D-x, DET-1D-x, ...
```

---

## 3. 特征空间分析

### 3.1 特征分类体系

基于**认知神经科学**和**眼动研究**最佳实践,建立四级特征分类:

#### Level 1: 基础特征类别 (Primary Categories)

| 类别 | 来源 | 维度 | 描述 |
|------|------|------|------|
| **时域特征** | Module04 | ~10维 | 注视/扫视的时间统计 |
| **空域特征** | Module04 | ~8维 | 空间覆盖和ROI统计 |
| **复杂度特征** | Module05 | ~6维/参数 | 非线性动力学指标 |
| **混合特征** | Module04+05 | ~5维 | 跨模态融合特征 |

#### Level 2: 任务特异性 (Task Specificity)

**结构化任务** (q1-q4, 有ROI):
```python
# 优先特征集
primary_features = [
    # Module04: ROI相关
    "roi_hit_count",
    "roi_fixation_duration",
    "roi_first_hit_latency",

    # Module04: 基础眼动
    "mean_fixation_duration",
    "total_saccades",
    "scan_path_length",

    # Module05: 低参数RQA (m=2, tau=1, eps=0.05)
    "RR-1D-x",
    "DET-1D-x"
]
```

**自由浏览任务** (q5, 无ROI):
```python
# 优先特征集
primary_features = [
    # Module04: 全局统计
    "spatial_density",
    "convex_hull_area",
    "mean_saccade_amplitude",

    # Module05: 高复杂度RQA (m=5-10, tau=3-8)
    "RR-2D-xy",
    "DET-2D-xy",
    "rqa_complexity_index",
    "combined_rr"
]
```

#### Level 3: 认知功能映射 (Cognitive Function Mapping)

**注意力功能** (Attention):
```python
attention_features = {
    "selective_attention": [  # 选择性注意
        "roi_first_hit_latency",
        "roi_hit_count",
        "DET-1D-x"  # 决定性反映注意稳定性
    ],
    "sustained_attention": [  # 持续性注意
        "mean_fixation_duration",
        "fixation_duration_ratio",
        "RR-1D-x"   # 递归率反映注意持续性
    ],
    "divided_attention": [    # 分散性注意
        "spatial_density",
        "total_saccades",
        "ENT-1D-x"  # 熵反映注意分散程度
    ]
}
```

**记忆功能** (Memory):
```python
memory_features = {
    "working_memory": [      # 工作记忆
        "scan_path_length",
        "convex_hull_area",
        "rqa_complexity_index"
    ],
    "spatial_memory": [      # 空间记忆
        "roi_hit_count",
        "spatial_density",
        "RR-2D-xy"
    ]
}
```

**执行功能** (Executive Function):
```python
executive_features = {
    "planning": [            # 计划能力
        "scan_path_length",
        "mean_saccade_amplitude",
        "DET-2D-xy"
    ],
    "inhibition": [          # 抑制控制
        "roi_fixation_duration",
        "peak_saccade_velocity",
        "combined_rr"
    ]
}
```

#### Level 4: 疾病区分能力 (Disease Discriminability)

基于Module05的**参数敏感性分析结果**,识别高F统计量特征:

```python
# 从Module05敏感性分析结果中提取
# /api/m05/sensitivity/compute-scores 输出
high_discriminability_features = [
    # Top 10 features by F-statistic
    {
        "feature": "DET-1D-x",
        "params": {"m": 3, "tau": 2, "eps": 0.065, "lmin": 2},
        "f_statistic": 45.2,
        "p_value": 0.0001,
        "effect_size": 0.68,
        "task_consistency": 0.92  # 跨任务一致性
    },
    # ... more features
]
```

### 3.2 维度灾难分析

#### 3.2.1 当前特征空间

**完整特征空间**:
```
Total Dimensions = Module04 + Module05
                 = 20 + (6 × 3264)
                 = 19,604 维

Samples = 60 subjects × 5 tasks = 300

Ratio = Dimensions / Samples = 65.3:1  ❌ (极度严重过拟合风险!)
```

**推荐比例** (Machine Learning Best Practice):
- 线性模型: 1:10 (Samples:Features) → 需要 ≤30维
- 非线性模型: 1:5 → 需要 ≤60维
- 深度学习: 1:1或更低 → 需要 ≤300维

#### 3.2.2 降维策略

**策略1: 参数筛选** (Parameter Selection)
```python
# 从3264个参数组合中选择Top-K
selected_params = sensitivity_analysis.get_top_params(
    k=10,  # 仅保留Top 10参数组合
    metric="overall_score"
)

# 降维效果
Reduced Dimensions = 20 + (6 × 10) = 80 维
Ratio = 300 / 80 = 3.75:1  ✅ (优秀,适合非线性模型)
```

**策略2: 特征聚合** (Feature Aggregation)
```python
# 跨参数聚合RQA特征
aggregated_rqa = {
    "mean_RR_1D": np.mean([rr for params in all_params]),
    "std_RR_1D": np.std([rr for params in all_params]),
    "max_DET_1D": np.max([det for params in all_params]),
    "optimal_complexity": best_param_rqa["rqa_complexity_index"]
}

# 降维效果
Aggregated Dimensions = 20 + 12 = 32 维
Ratio = 600 / 32 = 18.75:1  ✅ (优秀)
```

**策略3: 任务特定选择** (Task-Specific Selection)
```python
# 每个任务独立选择特征
task_features = {
    "q1": select_top_k(all_features, task="q1", k=15),
    "q2": select_top_k(all_features, task="q2", k=15),
    # ...
}

# 降维效果
Per-Task Dimensions = 15
Ratio = 120 / 15 = 8:1  ✅ (per-task分析)
```

---

## 4. 科学论证

### 4.1 特征选择的理论基础

#### 4.1.1 信息论视角

**互信息** (Mutual Information):
```python
# 特征与分类标签的互信息
MI(Feature, Label) = H(Label) - H(Label | Feature)

# 选择标准
selected_features = [f for f in all_features
                    if MI(f, "group") > threshold]
```

**冗余分析** (Redundancy Analysis):
```python
# 特征间相关性
correlation_matrix = np.corrcoef(features)

# 移除高相关特征 (r > 0.9)
redundant_pairs = [(i,j) for i,j in pairs
                   if abs(correlation_matrix[i,j]) > 0.9]
```

#### 4.1.2 统计显著性

基于**Module05参数敏感性分析**,使用ANOVA F-test:

```python
# F统计量评估
F = Variance_between_groups / Variance_within_groups

# 选择标准
significant_features = [
    f for f in features
    if f.p_value < 0.05 and       # 统计显著
       f.effect_size > 0.3 and     # 中等以上效应量
       f.task_consistency > 0.7     # 跨任务一致性
]
```

#### 4.1.3 认知神经科学证据

**眼动-认知映射** (Eye Movement - Cognition Mapping):

| 眼动指标 | 认知功能 | 疾病敏感性 | 文献依据 |
|---------|---------|-----------|---------|
| 注视时长 | 信息处理速度 | AD↑ MCI→ | [1] |
| 扫视幅度 | 视觉搜索效率 | AD↓ MCI↓ | [2] |
| 空间密度 | 视觉扫描策略 | AD↓ | [3] |
| RQA递归率 | 眼动规律性 | AD↓ MCI→ | [4] |
| RQA确定性 | 系统可预测性 | AD↓ MCI↓ | [5] |

**参考文献**:
[1] Molitor et al. (2015) - Eye movements in Alzheimer's disease
[2] Weil et al. (2018) - Saccadic changes in MCI
[3] Crutcher et al. (2009) - Visual attention in AD
[4] Anderson & MacAskill (2013) - RQA in neurological disorders
[5] Marwan et al. (2007) - Recurrence plots for time series analysis

### 4.2 3264参数组合的科学利用

#### 4.2.1 参数空间的物理意义

**嵌入维度 (m)**: 系统复杂度的探针
- m=1-3: 简单动力学 (适合规则任务)
- m=4-7: 中等复杂度 (适合混合任务)
- m=8-10: 高复杂度 (适合自由浏览)

**时间延迟 (τ)**: 多尺度动力学
- τ=1-2: 快速响应 (注意转移)
- τ=3-5: 中速过程 (工作记忆)
- τ=6-10: 慢速过程 (策略规划)

**阈值 (ε)**: 相似性判定
- ε=0.05-0.07: 严格相似 (精细模式)
- ε=0.08-0.10: 宽松相似 (宏观模式)

#### 4.2.2 参数优化策略

**策略A: 敏感性驱动选择**
```python
# 使用Module05的敏感性分析结果
sensitivity_df = api.get('/api/m05/sensitivity/compute-scores')

# 按overall_score排序
top_params = sensitivity_df.nlargest(20, 'overall_score')

# 聚类分析 - 选择代表性参数
from sklearn.cluster import KMeans
clusters = KMeans(n_clusters=5).fit(top_params[['m','tau','eps','lmin']])
representative_params = [cluster.centroid for cluster in clusters]
```

**策略B: 任务自适应参数**
```python
task_optimal_params = {
    "q1": {"m": 2, "tau": 1, "eps": 0.060, "lmin": 2},  # 快速搜索
    "q2": {"m": 3, "tau": 3, "eps": 0.070, "lmin": 2},  # 记忆任务
    "q3": {"m": 2, "tau": 2, "eps": 0.055, "lmin": 2},  # 追踪任务
    "q4": {"m": 4, "tau": 4, "eps": 0.065, "lmin": 2},  # 导航任务
    "q5": {"m": 7, "tau": 5, "eps": 0.075, "lmin": 3}   # 自由浏览
}
```

**策略C: 多参数集成**
```python
# Ensemble特征
ensemble_rqa = {
    "low_complexity": RQA(m=2, tau=1, eps=0.05),
    "mid_complexity": RQA(m=5, tau=3, eps=0.07),
    "high_complexity": RQA(m=8, tau=6, eps=0.09),

    # 融合指标
    "complexity_gradient": high - low,
    "stability_index": std([low, mid, high])
}
```

---

## 5. 双策略特征提取方案

### 5.1 策略概述

基于**300样本 vs 19,584维**的极端维度灾难挑战,Module06设计了**两种互补的特征提取策略**:

| 维度 | 策略A: Top-K敏感度极简策略 | 策略B: 平衡综合策略 |
|------|---------------------------|-------------------|
| **核心理念** | 精准降维,极致效率 | 全面覆盖,深度分析 |
| **Module04特征** | Top-3敏感度特征(排除MMSE) | 全量核心特征(9维,排除MMSE) |
| **Module05特征** | 最优参数的6维RQA | Top-10 RQA参数组合(60维) |
| **总维度** | **9维** | **69维** |
| **样本比** | 300/9 = **33.3:1** ✅ | 300/69 = **4.3:1** ✅ |
| **适用模型** | 线性/逻辑回归/SVM | 随机森林/XGBoost/神经网络 |
| **计算成本** | 极低 | 中等 |
| **可解释性** | ⭐⭐⭐⭐⭐ (极佳) | ⭐⭐⭐ (良好) |
| **推荐场景** | 快速原型/临床应用/资源受限 | 科研分析/特征探索/模型优化 |

### 5.2 策略A: Top-K敏感度极简策略

#### 5.2.1 Module04 Top-4特征选择

**选择依据**: 基于组间差异的统计敏感度(F-statistic, Effect Size)

**实际特征列表** (基于Module04实际输出):
```python
module04_features = {
    # ROI占比特征 (逐帧分析法 - 与Module01一致)
    "bg_ratio_frame": float,        # 背景区域占比 (%)
    "inst_ratio_frame": float,      # 指令区域占比 (%)
    "kw_ratio_frame": float,        # 关键词区域占比 (%)

    # 时域特征
    "total_fixation_time": float,   # 总注视时长 (ms)
    "total_fixations": int,         # 总注视次数
    "avg_fixation_duration": float, # 平均注视时长 (ms)
    "total_saccades": int,          # 总扫视次数
    "avg_saccade_amplitude": float, # 平均扫视幅度 (deg)
    "task_total_time": float,       # 任务总时长 (ms)

    # MMSE分数
    "mmse_total_score": int,        # MMSE总分
    "mmse_task_score": int          # 任务相关MMSE分项分数
}
```

**Top-4推荐特征** (⚠️ 基于文献经验,需数据验证):
1. `avg_fixation_duration` - **平均注视时长**: AD患者显示注视时长异常 [文献推荐]
2. `kw_ratio_frame` - **关键词区域占比**: 反映注意力分配能力 [文献推荐]
3. `avg_saccade_amplitude` - **平均扫视幅度**: 反映视觉搜索效率 [文献推荐]
4. `mmse_task_score` - **任务相关MMSE分数**: 直接认知能力指标 [文献推荐]

> ⚠️ **重要说明**:
> - **Module04目前没有实施敏感度分析功能**
> - 上述4个特征基于认知神经科学文献推荐,**未经v1数据集实际验证**
> - **建议**: 在Module06实施阶段,先开发Module04敏感度分析功能(见下方代码),基于实际数据确定最优Top-4

**敏感度计算方法** (需在Module04中实现):
```python
def compute_m04_sensitivity(feature_name):
    # Step 1: 提取三组数据
    control = df[df['group']=='control'][feature_name]
    mci = df[df['group']=='mci'][feature_name]
    ad = df[df['group']=='ad'][feature_name]

    # Step 2: ANOVA F-test
    f_stat, p_value = f_oneway(control, mci, ad)

    # Step 3: Effect Size (eta-squared)
    eta_squared = (f_stat * (3-1)) / (f_stat * (3-1) + (300-3))

    # Step 4: 综合敏感度得分
    sensitivity_score = f_stat * eta_squared * (1 - p_value)

    return sensitivity_score
```

#### 5.2.2 Module05 Top-6 RQA特征选择

**选择依据**: 基于Module05敏感度分析结果(已有API: `/api/m05/sensitivity/compute-scores`)

**Top-6 RQA特征提取流程**:
```python
# Step 1: 获取最佳参数组合(单个)
best_params = get_top_sensitivity_params(k=1)  # 例如: m=2, tau=1, eps=0.05, lmin=2

# Step 2: 提取该参数下的6维RQA特征
rqa_features = {
    "RR-1D-x": float,      # x坐标递归率
    "DET-1D-x": float,     # x坐标确定性
    "ENT-1D-x": float,     # x坐标熵
    "RR-2D-xy": float,     # xy轨迹递归率
    "DET-2D-xy": float,    # xy轨迹确定性
    "ENT-2D-xy": float     # xy轨迹熵
}
```

**特征解释**:
- **RR (Recurrence Rate)**: 眼动轨迹的规律性/重复性
- **DET (Determinism)**: 眼动模式的可预测性
- **ENT (Entropy)**: 眼动轨迹的复杂度/不确定性

#### 5.2.3 策略A特征向量

**最终10维特征向量**:
```python
strategy_a_features = {
    # Module04 (4维)
    "m04_avg_fixation_duration": float,
    "m04_kw_ratio_frame": float,
    "m04_avg_saccade_amplitude": float,
    "m04_mmse_task_score": int,

    # Module05 (6维)
    "m05_RR_1D_x": float,
    "m05_DET_1D_x": float,
    "m05_ENT_1D_x": float,
    "m05_RR_2D_xy": float,
    "m05_DET_2D_xy": float,
    "m05_ENT_2D_xy": float
}
# Total: 10维, 样本比 30:1
```

### 5.3 策略B: 平衡综合策略

#### 5.3.1 Module04特征选择 (~13维)

**保留所有核心眼动特征** (排除冗余的IVT质心法ROI占比):
```python
module04_selected = [
    # ROI占比 (3维 - 仅逐帧分析法)
    "bg_ratio_frame", "inst_ratio_frame", "kw_ratio_frame",

    # 时域特征 (6维)
    "total_fixation_time", "total_fixations", "avg_fixation_duration",
    "total_saccades", "avg_saccade_amplitude", "task_total_time",

    # 认知指标 (2维)
    "mmse_total_score", "mmse_task_score"
]
# Total: 11维
```

#### 5.3.2 Module05特征选择 (60维)

**Top-10参数组合 × 6维RQA = 60维**:
```python
# Step 1: 获取Top-10敏感度参数
top_10_params = get_top_sensitivity_params(k=10)

# Step 2: 每个参数提取6维RQA特征
for params in top_10_params:
    rqa = extract_rqa_features(params)  # 6维
    # 添加到特征向量 (带参数标识)
    features[f"m{params.m}_tau{params.tau}_RR_1D_x"] = rqa["RR-1D-x"]
    features[f"m{params.m}_tau{params.tau}_DET_1D_x"] = rqa["DET-1D-x"]
    # ... 其余4维

# Total: 10 params × 6 features = 60维
```

#### 5.3.3 可选增强特征 (+2维)

**时-空融合特征**:
```python
enhanced_features = {
    "fixation_density": total_fixations / task_total_time,  # 注视密度
    "rqa_complexity_mean": mean([DET_1D_x for all params])  # RQA复杂度均值
}
```

#### 5.3.4 策略B特征向量

**最终73维特征向量**:
```python
strategy_b_features = {
    # Module04 (11维)
    "m04_bg_ratio_frame": float,
    "m04_inst_ratio_frame": float,
    "m04_kw_ratio_frame": float,
    "m04_total_fixation_time": float,
    "m04_total_fixations": int,
    "m04_avg_fixation_duration": float,
    "m04_total_saccades": int,
    "m04_avg_saccade_amplitude": float,
    "m04_task_total_time": float,
    "m04_mmse_total_score": int,
    "m04_mmse_task_score": int,

    # Module05 (60维 = 10 params × 6 RQA)
    "m05_m2_tau1_RR_1D_x": float,
    "m05_m2_tau1_DET_1D_x": float,
    # ... 58 more RQA features

    # Enhanced (2维)
    "fusion_fixation_density": float,
    "fusion_rqa_complexity_mean": float
}
# Total: 73维, 样本比 4.1:1
```

### 5.4 策略选择决策树

```
是否需要极致可解释性?
├── 是 → 策略A (10维)
└── 否 → 是否有充足计算资源?
    ├── 是 → 策略B (73维)
    └── 否 → 策略A (10维)

样本量是否<500?
├── 是 → 策略A (避免过拟合)
└── 否 → 策略B (充分利用数据)

是否用于临床快速筛查?
├── 是 → 策略A (低延迟)
└── 否 → 策略B (高精度)
```

---

## 6. 特征提取实施流程

### 6.1 策略A实施流程 (极简10维)

```python
def extract_strategy_a_features(subject_id, group, task_id, data_version='v1'):
    """策略A: Top-K敏感度极简策略 (10维)"""

    # Step 1: 获取Module04全量特征
    m04_response = requests.post('/api/m04/features', json={
        'group': group,
        'data_version': data_version
    })
    m04_all_features = m04_response.json()['features']

    # Step 2: 计算Module04敏感度,选择Top-4
    m04_sensitivity = compute_m04_sensitivity(m04_all_features)
    top4_m04_features = select_top_k(m04_sensitivity, k=4)
    # 预期结果: ['avg_fixation_duration', 'kw_ratio_frame',
    #            'avg_saccade_amplitude', 'mmse_task_score']

    # Step 3: 获取Module05敏感度最佳参数
    m05_sensitivity = requests.get('/api/m05/sensitivity/compute-scores').json()
    best_params = m05_sensitivity['results'][0]['params']  # Top-1
    # 例如: m=2, tau=1, eps=0.05, lmin=2

    # Step 4: 提取该参数下的6维RQA特征
    rqa_file = f"data/05_rqa_analysis/m{best_params['m']}_tau{best_params['tau']}_" \
               f"eps{best_params['eps']}_lmin{best_params['lmin']}/step3_enriched_features.csv"
    rqa_df = pd.read_csv(rqa_file)
    subject_rqa = rqa_df[(rqa_df['subject_id'] == subject_id) &
                         (rqa_df['task_id'] == task_id)]

    # Step 5: 组装10维特征向量
    feature_vector = {
        # Module04 (4维)
        'm04_avg_fixation_duration': subject_rqa['avg_fixation_duration'].values[0],
        'm04_kw_ratio_frame': subject_rqa['kw_ratio_frame'].values[0],
        'm04_avg_saccade_amplitude': subject_rqa['avg_saccade_amplitude'].values[0],
        'm04_mmse_task_score': subject_rqa['mmse_task_score'].values[0],

        # Module05 (6维)
        'm05_RR_1D_x': subject_rqa['RR-1D-x'].values[0],
        'm05_DET_1D_x': subject_rqa['DET-1D-x'].values[0],
        'm05_ENT_1D_x': subject_rqa['ENT-1D-x'].values[0],
        'm05_RR_2D_xy': subject_rqa['RR-2D-xy'].values[0],
        'm05_DET_2D_xy': subject_rqa['DET-2D-xy'].values[0],
        'm05_ENT_2D_xy': subject_rqa['ENT-2D-xy'].values[0]
    }

    # Step 6: 标准化
    scaler = StandardScaler()
    normalized_vector = scaler.fit_transform([list(feature_vector.values())])

    return normalized_vector, feature_vector
```

### 6.2 策略B实施流程 (综合73维)

```python
def extract_strategy_b_features(subject_id, group, task_id, data_version='v1'):
    """策略B: 平衡综合策略 (73维)"""

    # Step 1: 获取Module04全量11维特征
    m04_response = requests.post('/api/m04/features', json={
        'group': group,
        'data_version': data_version
    })
    m04_df = pd.DataFrame(m04_response.json()['features'])
    subject_m04 = m04_df[(m04_df['subject_id'] == subject_id) &
                         (m04_df['task_id'] == task_id)]

    m04_selected = [
        'bg_ratio_frame', 'inst_ratio_frame', 'kw_ratio_frame',
        'total_fixation_time', 'total_fixations', 'avg_fixation_duration',
        'total_saccades', 'avg_saccade_amplitude', 'task_total_time',
        'mmse_total_score', 'mmse_task_score'
    ]

    # Step 2: 获取Module05 Top-10敏感度参数
    m05_sensitivity = requests.get('/api/m05/sensitivity/compute-scores').json()
    top10_params = m05_sensitivity['results'][:10]

    # Step 3: 提取Top-10参数的RQA特征 (10 × 6 = 60维)
    rqa_features = {}
    for params in top10_params:
        param_key = f"m{params['m']}_tau{params['tau']}"
        rqa_file = f"data/05_rqa_analysis/m{params['m']}_tau{params['tau']}_" \
                   f"eps{params['eps']}_lmin{params['lmin']}/step3_enriched_features.csv"
        rqa_df = pd.read_csv(rqa_file)
        subject_rqa = rqa_df[(rqa_df['subject_id'] == subject_id) &
                             (rqa_df['task_id'] == task_id)]

        for rqa_metric in ['RR-1D-x', 'DET-1D-x', 'ENT-1D-x',
                           'RR-2D-xy', 'DET-2D-xy', 'ENT-2D-xy']:
            rqa_features[f"m05_{param_key}_{rqa_metric}"] = subject_rqa[rqa_metric].values[0]

    # Step 4: 计算融合特征 (2维)
    fixation_density = subject_m04['total_fixations'].values[0] / \
                       subject_m04['task_total_time'].values[0]
    det_values = [v for k, v in rqa_features.items() if 'DET' in k]
    rqa_complexity_mean = np.mean(det_values)

    # Step 5: 组装73维特征向量
    feature_vector = {}

    # Module04 (11维)
    for feat in m04_selected:
        feature_vector[f"m04_{feat}"] = subject_m04[feat].values[0]

    # Module05 (60维)
    feature_vector.update(rqa_features)

    # Enhanced (2维)
    feature_vector['fusion_fixation_density'] = fixation_density
    feature_vector['fusion_rqa_complexity_mean'] = rqa_complexity_mean

    # Step 6: 标准化
    scaler = StandardScaler()
    normalized_vector = scaler.fit_transform([list(feature_vector.values())])

    return normalized_vector, feature_vector
```

### 6.3 API设计

**新增Module06 API端点**:

```python
# 策略A: 极简特征提取
POST /api/m06/extract/strategy-a
{
    "subject_id": "control_legacy_1",
    "group": "control",
    "task_id": "q1",
    "data_version": "v1"
}
Response: {
    "success": true,
    "strategy": "A",
    "dimensions": 10,
    "features": {
        "m04_avg_fixation_duration": 245.67,
        "m04_kw_ratio_frame": 35.2,
        ...
    },
    "normalized": [0.23, -0.45, ...]
}

# 策略B: 综合特征提取
POST /api/m06/extract/strategy-b
{
    "subject_id": "control_legacy_1",
    "group": "control",
    "task_id": "q1",
    "data_version": "v1"
}
Response: {
    "success": true,
    "strategy": "B",
    "dimensions": 73,
    "features": {...},
    "normalized": [...]
}

# 批量特征提取
POST /api/m06/extract/batch
{
    "strategy": "A",  // or "B"
    "groups": ["control", "mci", "ad"],
    "data_version": "v1"
}
Response: {
    "success": true,
    "total_records": 300,
    "data": DataFrame (CSV download available)
}

# 特征敏感度分析
GET /api/m06/sensitivity/m04-features
Response: {
    "success": true,
    "top_features": [
        {"name": "avg_fixation_duration", "f_stat": 45.2, "eta_squared": 0.35, "p_value": 0.001},
        {"name": "kw_ratio_frame", "f_stat": 38.7, "eta_squared": 0.28, "p_value": 0.003},
        ...
    ]
}
```

---

## 7. 特征提取配置模板

### 7.1 预设配置模板

**模板1: 快速筛查** (Screening)
```json
{
  "name": "screening_template",
  "description": "快速疾病筛查,高效特征集",
  "module04_features": [
    "mean_fixation_duration",
    "total_saccades",
    "roi_hit_count",
    "scan_path_length"
  ],
  "module05_params": [
    {"m": 2, "tau": 1, "eps": 0.050, "lmin": 2}
  ],
  "module05_features": [
    "RR-1D-x",
    "DET-1D-x",
    "combined_rr"
  ],
  "total_dimensions": 7,
  "recommended_tasks": ["q1", "q3"]
}
```

**模板2: 深度分析** (Deep Analysis)
```json
{
  "name": "deep_analysis_template",
  "description": "全面特征提取,适合研究",
  "module04_features": "all",  // 20维
  "module05_params": "top_10_sensitivity",  // 敏感性Top 10
  "module05_features": "all",  // 6维 × 10 = 60维
  "aggregation": {
    "enabled": true,
    "methods": ["mean", "std", "max", "min"]
  },
  "fusion_features": true,
  "total_dimensions": 95,
  "recommended_tasks": ["all"]
}
```

**模板3: 任务特定** (Task-Specific)
```json
{
  "name": "task_q5_template",
  "description": "q5自由浏览任务优化特征",
  "module04_features": [
    "spatial_density",
    "convex_hull_area",
    "mean_saccade_amplitude",
    "peak_saccade_velocity"
  ],
  "module05_params": [
    {"m": 7, "tau": 5, "eps": 0.075, "lmin": 3},
    {"m": 5, "tau": 3, "eps": 0.065, "lmin": 2}
  ],
  "module05_features": [
    "RR-2D-xy",
    "DET-2D-xy",
    "ENT-2D-xy",
    "rqa_complexity_index"
  ],
  "total_dimensions": 12,
  "recommended_tasks": ["q5"]
}
```

#### 5.2.2 手动配置界面设计

**前端交互流程**:
```
用户选择 → 智能推荐 → 手动调整 → 预览 → 提取

┌─────────────────────────────────────┐
│  Feature Selection Panel            │
├─────────────────────────────────────┤
│                                     │
│  ① 选择任务: [q1] [q2] ... [all]   │
│                                     │
│  ② 智能推荐:                         │
│     □ 使用预设模板: [下拉选择]       │
│     □ 基于敏感性分析自动推荐 ✓       │
│                                     │
│  ③ Module04特征:                    │
│     ☑ 注视特征 (8/10 selected)      │
│     ☑ 扫视特征 (5/8 selected)       │
│     ☑ ROI特征 (3/3 selected)        │
│     [自定义选择...]                  │
│                                     │
│  ④ Module05 RQA参数:                │
│     [参数空间可视化 - 3D散点图]      │
│     已选: 12/3264 参数组合           │
│     [按敏感性排序] [按任务筛选]      │
│                                     │
│  ⑤ 高级选项:                         │
│     □ 启用特征聚合                   │
│     □ 启用融合特征                   │
│     □ 自动异常值过滤                 │
│                                     │
│  ⑥ 预览:                            │
│     总维度: 45                       │
│     样本数: 120 (q1 task)           │
│     比例: 2.67:1 ✓                  │
│                                     │
│  [提取特征] [保存配置] [导出CSV]     │
└─────────────────────────────────────┘
```

---

## 6. 智能推荐机制

### 6.1 推荐算法设计

#### 6.1.1 基于任务的推荐

**决策树逻辑**:
```python
def recommend_features(task_id: str, group: str) -> dict:
    """
    基于任务类型的特征推荐

    Args:
        task_id: q1-q5
        group: control/mci/ad

    Returns:
        推荐的特征配置
    """
    # 任务分类
    task_type = classify_task(task_id)

    if task_type == "structured":  # q1-q4
        # ROI相关任务
        m04_features = [
            "roi_hit_count", "roi_fixation_duration",
            "roi_first_hit_latency", "mean_fixation_duration",
            "total_saccades", "scan_path_length"
        ]

        # 低复杂度RQA参数
        m05_params = sensitivity_top_k(
            task=task_id,
            m_range=(1, 4),
            tau_range=(1, 3),
            k=5
        )

    elif task_type == "free_viewing":  # q5
        # 全局统计特征
        m04_features = [
            "spatial_density", "convex_hull_area",
            "mean_saccade_amplitude", "peak_saccade_velocity"
        ]

        # 高复杂度RQA参数
        m05_params = sensitivity_top_k(
            task=task_id,
            m_range=(5, 10),
            tau_range=(3, 8),
            k=8
        )

    # 根据组别调整权重
    if group in ["mci", "ad"]:
        # 增加疾病敏感特征
        m04_features.extend([
            "std_fixation_duration",
            "fixation_duration_ratio"
        ])

    return {
        "module04": m04_features,
        "module05": m05_params,
        "confidence": calculate_confidence(task_id, group)
    }
```

#### 6.1.2 基于敏感性的推荐

**排序策略**:
```python
def sensitivity_based_recommendation(k: int = 10) -> list:
    """
    基于Module05敏感性分析的参数推荐

    Args:
        k: 推荐的参数组合数量

    Returns:
        Top-K参数组合
    """
    # 获取敏感性分析结果
    sensitivity_df = get_sensitivity_scores()

    # 多目标排序
    sensitivity_df["composite_score"] = (
        0.4 * normalize(sensitivity_df["f_statistic"]) +
        0.3 * normalize(1 - sensitivity_df["p_value"]) +
        0.2 * normalize(sensitivity_df["effect_size"]) +
        0.1 * normalize(sensitivity_df["task_consistency"])
    )

    # 选择Top-K
    top_params = sensitivity_df.nlargest(k, "composite_score")

    # 多样性过滤 (避免参数过于相似)
    diverse_params = diversity_filter(top_params, min_distance=0.3)

    return diverse_params
```

#### 6.1.3 基于相关性的推荐

**特征冗余检测**:
```python
def correlation_based_recommendation(features: list) -> list:
    """
    基于相关性分析的特征去冗余

    Args:
        features: 候选特征列表

    Returns:
        去冗余后的特征列表
    """
    # 计算特征相关矩阵
    data = load_all_features()
    corr_matrix = data[features].corr()

    # 识别高相关对 (r > 0.9)
    high_corr_pairs = []
    for i in range(len(features)):
        for j in range(i+1, len(features)):
            if abs(corr_matrix.iloc[i, j]) > 0.9:
                high_corr_pairs.append((features[i], features[j]))

    # 保留信息量更大的特征
    selected = []
    removed = set()

    for f1, f2 in high_corr_pairs:
        if f1 in removed or f2 in removed:
            continue

        # 比较与标签的互信息
        mi_f1 = mutual_info_score(data[f1], data["group"])
        mi_f2 = mutual_info_score(data[f2], data["group"])

        if mi_f1 > mi_f2:
            removed.add(f2)
        else:
            removed.add(f1)

    selected = [f for f in features if f not in removed]

    return selected
```

### 6.2 推荐置信度

**置信度评分**:
```python
confidence_score = {
    "statistical_significance": 0.3,  # 统计显著性 (p<0.05)
    "effect_size": 0.3,               # 效应量 (eta^2 > 0.3)
    "task_consistency": 0.2,          # 跨任务一致性
    "literature_support": 0.1,        # 文献支持度
    "sample_adequacy": 0.1            # 样本充足性
}

total_confidence = sum([
    score * weight
    for score, weight in zip(scores.values(), confidence_score.values())
])

# 置信度等级
if total_confidence > 0.8:
    level = "高置信 ⭐⭐⭐"
elif total_confidence > 0.6:
    level = "中等置信 ⭐⭐"
else:
    level = "低置信 ⭐"
```

---

## 7. 系统架构设计

### 7.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│   ┌──────────────────────────────────────────────┐     │
│   │  Module06.jsx                                │     │
│   │  - 特征选择界面                               │     │
│   │  - 智能推荐展示                               │     │
│   │  - 3D参数空间可视化                           │     │
│   │  - 特征重要性图表                             │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│                      API Layer                           │
│   ┌──────────────────────────────────────────────┐     │
│   │  api.py (Flask Blueprint)                    │     │
│   │  - GET /api/m06/features/recommend           │     │
│   │  - POST /api/m06/features/extract            │     │
│   │  - GET /api/m06/templates                    │     │
│   │  - POST /api/m06/config/save                 │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│   ┌──────────────────────────────────────────────┐     │
│   │  feature_extraction_service.py               │     │
│   │  - 特征提取编排                               │     │
│   │  - 数据聚合                                   │     │
│   │  - 质量控制                                   │     │
│   └──────────────────────────────────────────────┘     │
│   ┌──────────────────────────────────────────────┐     │
│   │  recommendation_engine.py                    │     │
│   │  - 任务分析                                   │     │
│   │  - 参数推荐                                   │     │
│   │  - 置信度评估                                 │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                  Integration Layer                       │
│   ┌────────────┐  ┌────────────┐  ┌──────────────┐    │
│   │ Module04   │  │ Module05   │  │ Feature      │    │
│   │ Client     │  │ Client     │  │ Aggregator   │    │
│   └────────────┘  └────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                   Data Access Layer                      │
│   ┌──────────────────────────────────────────────┐     │
│   │  - Module04 API: /api/m04/features           │     │
│   │  - Module05 API: /api/m05/results/list       │     │
│   │  - Module05 Sensitivity: /api/m05/sensitivity│     │
│   │  - CSV Reader: step3_enriched_features.csv   │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 7.2 核心组件设计

#### 7.2.1 Feature Extraction Service

```python
# feature_extraction_service.py

class FeatureExtractionService:
    """特征提取服务"""

    def __init__(self):
        self.m04_client = Module04Client()
        self.m05_client = Module05Client()
        self.aggregator = FeatureAggregator()
        self.normalizer = FeatureNormalizer()

    def extract_features(self, config: dict) -> pd.DataFrame:
        """
        提取特征向量

        Args:
            config: {
                "subject_id": str,
                "group": str,
                "task_id": str,
                "module04_features": list,
                "module05_params": list,
                "module05_features": list,
                "aggregation": dict,
                "normalization": str
            }

        Returns:
            特征向量DataFrame
        """
        features = []

        # Step 1: 提取Module04特征
        m04_data = self.m04_client.get_features(
            subject_id=config["subject_id"],
            group=config["group"],
            task_id=config["task_id"]
        )
        m04_selected = {
            k: m04_data[k]
            for k in config["module04_features"]
        }
        features.append(m04_selected)

        # Step 2: 提取Module05特征
        for params in config["module05_params"]:
            m05_data = self.m05_client.get_rqa_features(
                subject_id=config["subject_id"],
                task_id=config["task_id"],
                params=params
            )
            m05_selected = {
                f"{k}_{params_signature(params)}": m05_data[k]
                for k in config["module05_features"]
            }
            features.append(m05_selected)

        # Step 3: 聚合特征
        if config.get("aggregation", {}).get("enabled"):
            agg_features = self.aggregator.aggregate(
                features,
                methods=config["aggregation"]["methods"]
            )
            features.append(agg_features)

        # Step 4: 融合特征
        if config.get("fusion_features"):
            fusion = self.create_fusion_features(features)
            features.append(fusion)

        # Step 5: 标准化
        feature_vector = pd.DataFrame([{**f for f in features}])
        if config.get("normalization"):
            feature_vector = self.normalizer.normalize(
                feature_vector,
                method=config["normalization"]
            )

        return feature_vector

    def create_fusion_features(self, features: list) -> dict:
        """创建融合特征"""
        m04 = features[0]
        m05_list = features[1:-1] if len(features) > 2 else []

        fusion = {}

        # 时-空融合
        if "total_fixations" in m04 and "convex_hull_area" in m04:
            fusion["fixation_density"] = (
                m04["total_fixations"] / m04["convex_hull_area"]
            )

        # RQA-事件融合
        if m05_list and "total_fixations" in m04:
            avg_complexity = np.mean([
                m05.get("rqa_complexity_index", 0)
                for m05 in m05_list
            ])
            fusion["complexity_per_fixation"] = (
                avg_complexity / m04["total_fixations"]
            )

        return fusion
```

#### 7.2.2 Recommendation Engine

```python
# recommendation_engine.py

class RecommendationEngine:
    """智能推荐引擎"""

    def __init__(self):
        self.sensitivity_analyzer = SensitivityAnalyzer()
        self.task_classifier = TaskClassifier()
        self.confidence_evaluator = ConfidenceEvaluator()

    def recommend(self, task_id: str, group: str,
                  mode: str = "balanced") -> dict:
        """
        生成特征推荐

        Args:
            task_id: 任务ID (q1-q5)
            group: 组别 (control/mci/ad)
            mode: 推荐模式
                - "screening": 快速筛查 (7-10维)
                - "balanced": 平衡分析 (20-30维)
                - "comprehensive": 全面分析 (50-80维)

        Returns:
            推荐配置
        """
        # 任务分类
        task_type = self.task_classifier.classify(task_id)

        # 基础推荐
        if mode == "screening":
            config = self._screening_recommendation(task_type)
        elif mode == "balanced":
            config = self._balanced_recommendation(task_type)
        else:
            config = self._comprehensive_recommendation(task_type)

        # 组别调整
        config = self._adjust_for_group(config, group)

        # 敏感性优化
        config["module05_params"] = (
            self.sensitivity_analyzer.get_top_params(
                task=task_id,
                k=config["param_count"]
            )
        )

        # 置信度评估
        confidence = self.confidence_evaluator.evaluate(
            config, task_id, group
        )

        return {
            "config": config,
            "confidence": confidence,
            "rationale": self._explain_recommendation(
                task_type, group, mode
            )
        }

    def _screening_recommendation(self, task_type: str) -> dict:
        """快速筛查推荐"""
        if task_type == "structured":
            return {
                "module04_features": [
                    "mean_fixation_duration",
                    "total_saccades",
                    "roi_hit_count"
                ],
                "module05_features": ["RR-1D-x", "DET-1D-x"],
                "param_count": 1,
                "aggregation": {"enabled": False}
            }
        else:  # free_viewing
            return {
                "module04_features": [
                    "spatial_density",
                    "mean_saccade_amplitude"
                ],
                "module05_features": ["RR-2D-xy", "rqa_complexity_index"],
                "param_count": 2,
                "aggregation": {"enabled": False}
            }
```

#### 7.2.3 Feature Aggregator

```python
# feature_aggregator.py

class FeatureAggregator:
    """特征聚合器"""

    def aggregate(self, features: list,
                  methods: list = ["mean", "std"]) -> dict:
        """
        跨参数聚合RQA特征

        Args:
            features: 特征列表 (多个参数组合)
            methods: 聚合方法

        Returns:
            聚合后的特征字典
        """
        # 提取RQA特征
        rqa_features = {}
        for feature_set in features:
            for key, value in feature_set.items():
                if any(rqa in key for rqa in ["RR-", "DET-", "ENT-"]):
                    base_name = key.split("_")[0]  # 移除参数后缀
                    if base_name not in rqa_features:
                        rqa_features[base_name] = []
                    rqa_features[base_name].append(value)

        # 聚合
        aggregated = {}
        for base_name, values in rqa_features.items():
            for method in methods:
                if method == "mean":
                    aggregated[f"{base_name}_mean"] = np.mean(values)
                elif method == "std":
                    aggregated[f"{base_name}_std"] = np.std(values)
                elif method == "max":
                    aggregated[f"{base_name}_max"] = np.max(values)
                elif method == "min":
                    aggregated[f"{base_name}_min"] = np.min(values)
                elif method == "range":
                    aggregated[f"{base_name}_range"] = (
                        np.max(values) - np.min(values)
                    )

        return aggregated
```

### 7.3 API接口设计

```python
# api.py

from flask import Blueprint, request, jsonify
from .service import FeatureExtractionService
from .recommendation_engine import RecommendationEngine
from .utils import handle_api_errors, validate_params

m06_bp = Blueprint('module06', __name__, url_prefix='/api/m06')

# 懒加载Service
_service = None
_recommender = None

def get_service():
    global _service
    if _service is None:
        _service = FeatureExtractionService()
    return _service

def get_recommender():
    global _recommender
    if _recommender is None:
        _recommender = RecommendationEngine()
    return _recommender

@m06_bp.route('/recommend', methods=['POST'])
@handle_api_errors
def recommend_features():
    """
    智能特征推荐

    Request:
        {
            "task_id": "q1",
            "group": "control",
            "mode": "balanced"  // screening, balanced, comprehensive
        }

    Response:
        {
            "success": true,
            "data": {
                "config": {...},
                "confidence": 0.85,
                "rationale": "..."
            }
        }
    """
    data = request.get_json()
    recommender = get_recommender()

    result = recommender.recommend(
        task_id=data["task_id"],
        group=data["group"],
        mode=data.get("mode", "balanced")
    )

    return jsonify({"success": True, "data": result})

@m06_bp.route('/extract', methods=['POST'])
@handle_api_errors
def extract_features():
    """
    执行特征提取

    Request:
        {
            "subject_id": "control_legacy_1",
            "group": "control",
            "task_id": "q1",
            "config": {
                "module04_features": [...],
                "module05_params": [...],
                ...
            }
        }

    Response:
        {
            "success": true,
            "data": {
                "feature_vector": {...},
                "dimension": 45,
                "extraction_time": 1.23
            }
        }
    """
    data = request.get_json()
    service = get_service()

    import time
    start_time = time.time()

    feature_vector = service.extract_features({
        "subject_id": data["subject_id"],
        "group": data["group"],
        "task_id": data["task_id"],
        **data["config"]
    })

    extraction_time = time.time() - start_time

    return jsonify({
        "success": True,
        "data": {
            "feature_vector": feature_vector.to_dict(orient="records")[0],
            "dimension": len(feature_vector.columns),
            "extraction_time": round(extraction_time, 2)
        }
    })

@m06_bp.route('/batch-extract', methods=['POST'])
@handle_api_errors
def batch_extract():
    """
    批量特征提取

    Request:
        {
            "subjects": ["control_legacy_1", "control_legacy_2", ...],
            "group": "control",
            "task_id": "q1",
            "config": {...}
        }

    Response:
        {
            "success": true,
            "data": {
                "features_matrix": [[...], [...], ...],
                "subjects": [...],
                "columns": [...],
                "shape": [120, 45]
            }
        }
    """
    data = request.get_json()
    service = get_service()

    features_list = []
    for subject_id in data["subjects"]:
        fv = service.extract_features({
            "subject_id": subject_id,
            "group": data["group"],
            "task_id": data["task_id"],
            **data["config"]
        })
        features_list.append(fv)

    features_matrix = pd.concat(features_list, ignore_index=True)

    return jsonify({
        "success": True,
        "data": {
            "features_matrix": features_matrix.values.tolist(),
            "subjects": data["subjects"],
            "columns": features_matrix.columns.tolist(),
            "shape": list(features_matrix.shape)
        }
    })

@m06_bp.route('/templates', methods=['GET'])
@handle_api_errors
def get_templates():
    """
    获取预设模板

    Response:
        {
            "success": true,
            "data": {
                "templates": [
                    {
                        "id": "screening",
                        "name": "快速筛查",
                        "config": {...},
                        "dimensions": 7
                    },
                    ...
                ]
            }
        }
    """
    templates = [
        {
            "id": "screening",
            "name": "快速筛查",
            "description": "高效特征集,适合初步筛查",
            "config": {...},  # 省略具体配置
            "dimensions": 7,
            "recommended_tasks": ["q1", "q3"]
        },
        # ... 更多模板
    ]

    return jsonify({"success": True, "data": {"templates": templates}})
```

---

## 8. 实施路线图

### 8.1 开发阶段划分

#### Phase 1: 基础设施 (Week 1-2)

**任务清单**:
- [ ] 创建Module06目录结构
- [ ] 实现Module04/05 Client集成
- [ ] 开发Feature Extraction Service核心逻辑
- [ ] 实现基础API端点 (/recommend, /extract)
- [ ] 单元测试覆盖率 >80%

**交付物**:
- 可用的特征提取API
- API文档
- 单元测试报告

#### Phase 2: 智能推荐 (Week 3)

**任务清单**:
- [ ] 实现Recommendation Engine
- [ ] 集成Module05敏感性分析结果
- [ ] 开发任务分类器
- [ ] 实现置信度评估
- [ ] 创建预设模板库

**交付物**:
- 智能推荐API
- 推荐算法文档
- 模板配置文件

#### Phase 3: 前端界面 (Week 4)

**任务清单**:
- [ ] 设计特征选择界面
- [ ] 实现3D参数空间可视化
- [ ] 开发特征重要性图表
- [ ] 集成智能推荐展示
- [ ] 实现配置导入/导出

**交付物**:
- React前端组件
- 交互式可视化
- 用户手册

#### Phase 4: 质量控制与优化 (Week 5)

**任务清单**:
- [ ] 实现特征质量检测
- [ ] 添加异常值处理
- [ ] 优化批量提取性能
- [ ] 完善错误处理
- [ ] 集成测试

**交付物**:
- 质量报告
- 性能基准测试
- 集成测试用例

### 8.2 技术债务管理

**已知限制**:
1. **参数组合爆炸**: 3264组合导致计算成本高
   - 缓解: 优先使用敏感性Top-K
   - 长期: 实现增量计算和缓存

2. **跨模块依赖**: 依赖Module04/05 API可用性
   - 缓解: 实现降级策略和本地缓存
   - 长期: 考虑消息队列解耦

3. **特征版本管理**: 特征定义可能变更
   - 缓解: 使用版本化配置文件
   - 长期: 实现特征注册表

### 8.3 成功指标

**量化指标**:
- API响应时间 < 2s (单样本提取)
- 批量提取吞吐量 > 30 samples/min
- 推荐准确率 > 85% (用户满意度)
- 代码覆盖率 > 80%

**质量指标**:
- 特征维度/样本比 < 1:5
- 推荐置信度 > 0.7
- 用户配置保存/复用率 > 60%

---

## 9. 总结与展望

### 9.1 核心创新点

1. **多模态特征融合**: 首次系统性整合事件分析(Module04)和非线性动力学(Module05)特征

2. **参数空间智能探索**: 从3264参数组合中科学选择,基于敏感性分析而非盲目搜索

3. **任务自适应推荐**: 根据认知任务类型自动推荐最优特征子集

4. **降维与可解释性**: 在保持诊断能力的同时,显著降低特征维度

### 9.2 科学贡献

**理论贡献**:
- 建立眼动特征-认知功能-疾病标志的映射框架
- 验证RQA参数对AD/MCI的区分能力
- 提出任务特异性特征选择理论

**实践贡献**:
- 提供可复现的特征提取流程
- 降低研究者使用门槛(智能推荐)
- 支持临床快速筛查(预设模板)

### 9.3 未来扩展方向

**短期** (3-6个月):
- 集成更多特征工程方法(PCA, LDA)
- 添加特征重要性解释(SHAP值)
- 支持自定义特征计算公式

**中期** (6-12个月):
- 实现AutoML特征选择
- 开发特征迁移学习
- 支持多任务联合特征提取

**长期** (1-2年):
- 构建特征知识图谱
- 实现元学习推荐系统
- 支持实时特征流处理

---

## 附录

### A. 术语表

| 术语 | 英文 | 解释 |
|------|------|------|
| 注视 | Fixation | 眼睛相对静止地停留在某一位置 |
| 扫视 | Saccade | 眼睛在两个注视点之间的快速运动 |
| RQA | Recurrence Quantification Analysis | 递归量化分析,非线性时间序列分析方法 |
| 嵌入维度 | Embedding Dimension (m) | 相空间重构的维度 |
| 时间延迟 | Time Delay (τ) | 嵌入向量之间的时间间隔 |
| 递归率 | Recurrence Rate (RR) | 递归矩阵中递归点的比例 |
| 确定性 | Determinism (DET) | 形成对角线的递归点比例 |
| 互信息 | Mutual Information | 两个变量之间的统计依赖性度量 |

### B. 参考资源

**API文档**:
- Module04: `/api/m04/features`
- Module05: `/api/m05/results/list`
- Module05 Sensitivity: `/api/m05/sensitivity/compute-scores`

**数据路径**:
- Event Analysis: `data/event_analysis_results/`
- RQA Results: `data/05_rqa_analysis/[params]/step3_enriched_features.csv`

**配置示例**:
- 见 `config/feature_extraction_templates.json`

---

## 附录: 双策略对比总结

### A. 核心差异对比

| 对比维度 | 策略A (极简) | 策略B (综合) |
|---------|------------|------------|
| **特征维度** | **10维** | **73维** |
| **Module04特征数** | 4 (Top-K敏感度) | 11 (全量核心) |
| **Module05特征数** | 6 (单个最佳参数) | 60 (Top-10参数×6) |
| **增强特征** | 0 | 2 (融合特征) |
| **样本/维度比** | 30:1 ⭐⭐⭐⭐⭐ | 4.1:1 ⭐⭐⭐⭐ |
| **过拟合风险** | 极低 | 低 |
| **可解释性** | 极佳 (每个特征都有明确意义) | 良好 (部分RQA特征需解释) |
| **计算成本** | 极低 (~0.1s/样本) | 中等 (~0.5s/样本) |
| **存储需求** | 极小 (~10KB/样本) | 中等 (~70KB/样本) |

### B. 特征组成对比

**策略A (10维)**:
```
Module04 (4维):
├── avg_fixation_duration    # 平均注视时长 → 反映注意力稳定性
├── kw_ratio_frame           # 关键词占比 → 反映信息获取能力
├── avg_saccade_amplitude    # 平均扫视幅度 → 反映视觉搜索效率
└── mmse_task_score          # MMSE任务分数 → 直接认知评估

Module05 (6维 - 单个最优参数):
├── RR-1D-x, DET-1D-x, ENT-1D-x    # 1D动力学特征
└── RR-2D-xy, DET-2D-xy, ENT-2D-xy # 2D动力学特征
```

**策略B (73维)**:
```
Module04 (11维):
├── ROI占比 (3维): bg/inst/kw_ratio_frame
├── 时域特征 (6维): total_fixation_time, total_fixations, avg_fixation_duration,
│                   total_saccades, avg_saccade_amplitude, task_total_time
└── 认知指标 (2维): mmse_total_score, mmse_task_score

Module05 (60维 - Top-10参数组合):
├── 低复杂度 (m=2, tau=1): 6维RQA
├── 中复杂度 (m=5, tau=3): 6维RQA
├── 高复杂度 (m=8, tau=6): 6维RQA
└── ... (7个其他参数组合)

增强特征 (2维):
├── fixation_density         # 注视密度 (融合时空信息)
└── rqa_complexity_mean      # RQA复杂度均值 (融合多参数)
```

### C. 性能预测对比

| 性能指标 | 策略A | 策略B | 说明 |
|---------|-------|-------|------|
| **分类准确率 (预估)** | 75-82% | 80-88% | 策略B特征更全面,可能提升5-8% |
| **训练时间** | 1x | 3-5x | 策略B维度更高,训练更慢 |
| **推理延迟** | 1x | 2-3x | 策略B特征提取耗时更长 |
| **泛化能力** | 优秀 | 良好 | 策略A样本比更优,泛化更好 |
| **特征重要性分析** | 易 | 中等 | 策略A特征少,更易分析 |
| **临床可解释性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 策略A每个特征都有明确临床意义 |

### D. 应用场景推荐

**策略A适用场景**:
1. ✅ 临床快速筛查系统 (要求<1秒响应)
2. ✅ 移动端/边缘设备部署 (资源受限)
3. ✅ 小样本数据集 (n<500)
4. ✅ 需要向医生解释每个特征的场景
5. ✅ 快速原型验证/MVP开发
6. ✅ 模型可解释性为首要需求

**策略B适用场景**:
1. ✅ 科研深度分析 (发表论文需要全面特征)
2. ✅ 集成学习/深度学习模型 (可利用高维特征)
3. ✅ 特征重要性排序研究
4. ✅ 多任务联合学习 (不同任务可用不同特征子集)
5. ✅ 模型性能优化/竞赛场景
6. ✅ 充足计算资源环境

### E. 实施建议

**推荐实施路径**:
```
阶段1 (Week 1-2): 实现策略A
├── 计算Module04敏感度 → 确定Top-4特征
├── 使用Module05现有最优参数 → 提取6维RQA
└── 验证10维特征有效性 → Baseline模型

阶段2 (Week 3-4): 实现策略B
├── 提取Module04全量11维特征
├── 使用Module05 Top-10参数 → 提取60维RQA
├── 添加2维融合特征
└── 对比策略A vs 策略B性能

阶段3 (Week 5-6): 优化与部署
├── 根据实际性能选择最优策略
├── 或设计混合策略 (不同任务用不同策略)
└── 生产环境部署
```

**混合策略示例**:
```python
def adaptive_strategy_selection(task_id, deployment_env):
    """根据任务类型和部署环境自适应选择策略"""

    if deployment_env == "mobile":
        return "strategy_a"  # 移动端必须用极简策略

    if task_id in ["q1", "q2"]:  # 结构化任务
        return "strategy_a"  # 10维足够,追求速度
    elif task_id in ["q5"]:  # 自由浏览任务
        return "strategy_b"  # 需要更多复杂度特征
    else:
        return "strategy_a"  # 默认极简策略
```

---

**文档状态**: ✅ 完成 (已添加双策略设计)
**最后更新**: 2025-10-10
**审核人**: 待定
**版本控制**: Git - docs/MODULE06_FEATURE_EXTRACTION_DESIGN.md

**设计亮点**:
- ✅ 基于实际Module04输出(11维)进行特征选择
- ✅ 双策略设计: 极简10维(样本比30:1) vs 综合73维(样本比4.1:1)
- ✅ 完整的敏感度计算方法(F-statistic + Effect Size)
- ✅ 清晰的实施流程和API设计
- ✅ 详细的应用场景推荐和混合策略
