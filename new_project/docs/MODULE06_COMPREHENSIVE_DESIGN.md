# Module06 智能特征提取与选择系统 - 综合设计文档

**文档版本**: v2.0
**创建日期**: 2025-10-10
**作者**: 系统架构团队
**模块名称**: Module06 - Intelligent Feature Extraction & Selection
**审核状态**: 待审核

---

## 📋 文档导航

### 第一部分: 需求与背景
1. [执行摘要](#1-执行摘要)
2. [问题分析](#2-问题分析)
3. [设计目标](#3-设计目标)

### 第二部分: 数据与特征分析
4. [Module04特征分析](#4-module04特征分析)
5. [Module05特征分析](#5-module05特征分析)
6. [特征空间维度灾难](#6-特征空间维度灾难)

### 第三部分: 核心设计
7. [双策略特征提取方案](#7-双策略特征提取方案)
8. [敏感度分析设计](#8-敏感度分析设计)
9. [特征选择算法](#9-特征选择算法)

### 第四部分: 系统架构
10. [系统架构设计](#10-系统架构设计)
11. [API接口设计](#11-api接口设计)
12. [数据流设计](#12-数据流设计)

### 第五部分: 实施与部署
13. [实施路线图](#13-实施路线图)
14. [测试策略](#14-测试策略)
15. [部署方案](#15-部署方案)

### 第六部分: 附录
16. [术语表](#16-术语表)
17. [参考文献](#17-参考文献)
18. [FAQ](#18-faq)

---

# 第一部分: 需求与背景

## 1. 执行摘要

### 1.1 项目背景

本项目旨在开发**Module06智能特征提取与选择系统**,作为眼动数据分析流水线的核心模块,连接上游的Module04(眼动事件分析)和Module05(RQA递归量化分析),为下游的机器学习建模提供高质量特征集。

### 1.2 核心挑战

当前系统面临**极端维度灾难**问题:

- **数据规模**: 300个样本 (60受试者 × 5任务)
  - Control组: 20人 × 5任务 = 100样本
  - MCI组: 20人 × 5任务 = 100样本
  - AD组: 20人 × 5任务 = 100样本

- **特征空间**: 潜在19,584维
  - Module04: 11维眼动特征
  - Module05: 3,264参数组合 × 6维RQA = 19,584维

- **维度灾难比**: 19,584维 / 300样本 = **65.3:1** ❌

### 1.3 解决方案

设计**双策略特征提取方案**:

| 策略 | 维度 | 样本比 | 适用场景 |
|------|------|--------|---------|
| **策略A (极简)** | 10维 | 30:1 ✅ | 临床快速筛查/移动端 |
| **策略B (综合)** | 69维 | 4.3:1 ✅ | 科研分析/模型优化 |

### 1.4 关键创新

1. **数据驱动的特征选择**: 基于敏感度分析,非人工经验
2. **双策略设计**: 兼顾效率与性能
3. **任务自适应**: 不同任务使用不同特征子集
4. **端到端自动化**: 从原始数据到标准化特征向量

---

## 2. 问题分析

### 2.1 维度灾难的危害

#### 2.1.1 过拟合风险

当特征维度远大于样本数时:

```
P(过拟合) ∝ (特征维度 / 样本数)²

当前: (19,584 / 300)² = 4,264 倍基线风险 ❌
```

**后果**:
- 训练集准确率: 99%
- 测试集准确率: 50% (随机猜测水平)
- 模型无法泛化

#### 2.1.2 计算成本

- **训练时间**: O(n × d²) = O(300 × 19,584²) = 1.15 × 10¹¹ 运算
- **内存占用**: 300 × 19,584 × 8 bytes = 46.9 MB (仅数据矩阵)
- **推理延迟**: 特征提取耗时 >> 模型推理耗时

#### 2.1.3 可解释性丧失

- 19,584个特征无法向临床医生解释
- 特征重要性分析困难
- 模型决策不透明

### 2.2 现有方案的不足

| 方法 | 优点 | 缺点 | 适用性 |
|------|------|------|--------|
| **全量特征** | 信息完整 | 严重过拟合 | ❌ |
| **随机选择** | 简单快速 | 丢失关键信息 | ❌ |
| **PCA降维** | 降维高效 | 丢失可解释性 | ⚠️ 部分适用 |
| **专家经验** | 可解释性强 | 主观性强,需验证 | ⚠️ 需数据验证 |
| **敏感度分析** | 数据驱动,客观 | 计算成本高 | ✅ 推荐 |

### 2.3 设计约束

1. **数据约束**: 60受试者,无法扩充
2. **标签约束**: MMSE分数不能作为特征(标签泄露)
3. **计算约束**: 特征提取延迟 < 1秒/样本
4. **可解释约束**: 临床应用需要特征可解释

---

## 3. 设计目标

### 3.1 功能目标

| 目标 | 优先级 | 成功标准 |
|------|--------|---------|
| **F1: 特征敏感度分析** | P0 | Module04: 9特征排序; Module05: 3264参数排序 |
| **F2: 自动特征选择** | P0 | 策略A: Top-10; 策略B: Top-69 |
| **F3: 特征标准化** | P0 | Z-score归一化,缺失值处理 |
| **F4: 任务自适应推荐** | P1 | 不同任务推荐不同特征子集 |
| **F5: 批量特征提取** | P1 | 支持300样本批量处理 |
| **F6: 可视化分析** | P2 | 特征分布、相关性热图 |

### 3.2 性能目标

| 指标 | 目标值 | 测量方法 |
|------|--------|---------|
| **特征提取延迟** | < 1s/样本 | 单样本处理时间 |
| **批量处理吞吐** | > 100样本/分钟 | 300样本总耗时 < 3分钟 |
| **敏感度分析耗时** | < 30分钟 | Module04: <5分钟; Module05: <30分钟 |
| **API响应时间** | < 500ms | 95th percentile |
| **内存占用** | < 2GB | 峰值内存 |

### 3.3 质量目标

| 维度 | 目标 | 验证方法 |
|------|------|---------|
| **准确性** | 敏感度计算结果可复现 | 单元测试 |
| **鲁棒性** | 处理缺失值、异常值 | 边界测试 |
| **可维护性** | 代码覆盖率 > 80% | pytest + coverage |
| **可扩展性** | 支持新增特征类型 | 架构评审 |
| **文档完整性** | API文档 + 使用示例 | 文档审查 |

---

# 第二部分: 数据与特征分析

## 4. Module04特征分析

### 4.1 数据源

**API端点**: `POST /api/m04/features`

**文件路径**: `data/04_features/cache/latest_analysis.json`

**数据结构**:
```python
{
    "success": true,
    "total_records": 300,
    "features": [
        {
            "subject_id": "control_legacy_1",
            "group": "control",
            "task_id": "q1",
            # ... 11维特征
        },
        ...
    ]
}
```

### 4.2 可用特征列表 (9维)

**排除MMSE标签后**:

```python
M04_AVAILABLE_FEATURES = {
    # ROI占比特征 (3维)
    "bg_ratio_frame": {
        "type": "float",
        "unit": "%",
        "range": [0, 100],
        "description": "背景区域注视时长占比",
        "clinical_meaning": "注意力分散程度"
    },
    "inst_ratio_frame": {
        "type": "float",
        "unit": "%",
        "range": [0, 100],
        "description": "指令区域注视时长占比",
        "clinical_meaning": "指令遵循能力"
    },
    "kw_ratio_frame": {
        "type": "float",
        "unit": "%",
        "range": [0, 100],
        "description": "关键词区域注视时长占比",
        "clinical_meaning": "关键信息捕获能力"
    },

    # 注视特征 (3维)
    "total_fixation_time": {
        "type": "float",
        "unit": "ms",
        "range": [0, 60000],
        "description": "总注视时长",
        "clinical_meaning": "视觉信息处理时间"
    },
    "total_fixations": {
        "type": "int",
        "unit": "count",
        "range": [0, 1000],
        "description": "总注视次数",
        "clinical_meaning": "视觉采样频率"
    },
    "avg_fixation_duration": {
        "type": "float",
        "unit": "ms",
        "range": [100, 1000],
        "description": "平均注视时长",
        "clinical_meaning": "注意力稳定性 (AD患者异常)"
    },

    # 扫视特征 (2维)
    "total_saccades": {
        "type": "int",
        "unit": "count",
        "range": [0, 1000],
        "description": "总扫视次数",
        "clinical_meaning": "视觉搜索活跃度"
    },
    "avg_saccade_amplitude": {
        "type": "float",
        "unit": "deg",
        "range": [0, 30],
        "description": "平均扫视幅度",
        "clinical_meaning": "视觉搜索范围 (AD患者减小)"
    },

    # 时间特征 (1维)
    "task_total_time": {
        "type": "float",
        "unit": "ms",
        "range": [0, 60000],
        "description": "任务总时长",
        "clinical_meaning": "任务完成效率"
    }
}
```

### 4.3 排除的特征 (2维)

```python
M04_EXCLUDED_FEATURES = {
    "mmse_total_score": "标签泄露 - MMSE总分是预测目标",
    "mmse_task_score": "标签泄露 - 任务相关MMSE分项分数"
}
```

### 4.4 特征分组

**按认知功能分类**:

```python
FEATURE_GROUPS = {
    "attention": [
        "kw_ratio_frame",       # 选择性注意
        "avg_fixation_duration", # 持续性注意
        "total_fixations"        # 注意力分配
    ],
    "executive_function": [
        "avg_saccade_amplitude", # 视觉搜索策略
        "total_saccades",        # 执行控制
        "task_total_time"        # 处理速度
    ],
    "spatial_processing": [
        "bg_ratio_frame",
        "inst_ratio_frame"
    ],
    "global_performance": [
        "total_fixation_time"
    ]
}
```

---

## 5. Module05特征分析

### 5.1 数据源

**API端点**: `POST /api/m05/sensitivity/compute-scores`

**文件路径**: `data/05_rqa_analysis/m{m}_tau{tau}_eps{eps}_lmin{lmin}/step3_enriched_features.csv`

**数据结构**:
```csv
subject_id,group,task_id,rr-1d-x,det-1d-x,ent-1d-x,rr-2d-xy,det-2d-xy,ent-2d-xy,...
control_legacy_1,control,q1,0.123,0.456,0.789,0.234,0.567,0.890,...
```

### 5.2 RQA特征列表 (~15-20维/参数组合)

```python
M05_RQA_FEATURES = {
    # 1D特征 - X坐标时间序列
    "rr-1d-x": {
        "full_name": "Recurrence Rate (1D-x)",
        "range": [0, 1],
        "meaning": "x坐标轨迹的规律性/重复性",
        "clinical": "水平眼动的刻板性"
    },
    "det-1d-x": {
        "full_name": "Determinism (1D-x)",
        "range": [0, 1],
        "meaning": "x坐标轨迹的可预测性",
        "clinical": "水平眼动的模式固定程度"
    },
    "ent-1d-x": {
        "full_name": "Entropy (1D-x)",
        "range": [0, +∞],
        "meaning": "x坐标轨迹的复杂度",
        "clinical": "水平眼动的不确定性"
    },
    "lam-1d-x": {
        "full_name": "Laminarity (1D-x)",
        "range": [0, 1],
        "meaning": "x坐标轨迹的层流性",
        "clinical": "水平眼动的停滞状态"
    },

    # 1D特征 - Y坐标时间序列
    "rr-1d-y": {...},
    "det-1d-y": {...},
    "ent-1d-y": {...},
    "lam-1d-y": {...},

    # 2D特征 - XY联合轨迹
    "rr-2d-xy": {
        "full_name": "Recurrence Rate (2D-xy)",
        "range": [0, 1],
        "meaning": "2D轨迹的整体重复性",
        "clinical": "眼动模式的全局刻板性"
    },
    "det-2d-xy": {...},
    "ent-2d-xy": {...},
    "lam-2d-xy": {...},

    # 派生特征
    "combined_rr": {
        "formula": "(rr-1d-x + rr-1d-y + rr-2d-xy) / 3",
        "meaning": "综合递归率"
    },
    "rqa_complexity_1d": {
        "formula": "f(ent-1d-x, ent-1d-y)",
        "meaning": "1D复杂度指数"
    },
    "rqa_complexity_2d": {
        "formula": "f(ent-2d-xy)",
        "meaning": "2D复杂度指数"
    },
    "x_y_symmetry": {
        "formula": "correlation(x_features, y_features)",
        "meaning": "X-Y对称性"
    }
}
```

### 5.3 参数空间

**完整参数组合**: 3,264个

```python
PARAMETER_SPACE = {
    "m": range(1, 11),          # Embedding dimension: 10种
    "tau": range(1, 11),        # Time delay: 10种
    "eps": [0.05 + i*0.005 for i in range(11)],  # Threshold: 11种 (0.05-0.10)
    "lmin": [2, 3]              # Min line length: 2种
}

# 总组合数 = 10 × 10 × 11 × 2 = 2,200 (理论)
# 实际分析: 3,264组合 (包含中间步长)
```

### 5.4 参数-特征空间

**总维度**: 3,264参数 × 15特征 = **49,056维**

**实际使用**:
- 策略A: 1参数 × 6特征 = 6维
- 策略B: 10参数 × 6特征 = 60维

---

## 6. 特征空间维度灾难

### 6.1 维度灾难量化

```python
# 原始特征空间
Total_Dimensions = M04 (11) + M05 (3264 × 15) = 11 + 48,960 = 48,971维
Sample_Count = 60 subjects × 5 tasks = 300样本

# 维度/样本比
Dimension_Ratio = 48,971 / 300 = 163.2 : 1 ❌❌❌

# Hughes现象临界点 (经验法则)
Safe_Ratio = 1 : 10 (线性模型)
Safe_Ratio = 1 : 5 (非线性模型)
Safe_Ratio = 1 : 1 (深度学习)

# 当前状态
Current_Ratio = 163.2 : 1  (超出安全比163倍!) ❌
```

### 6.2 过拟合风险评估

**理论分析**:

```
VC Dimension (线性分类器) ≈ d + 1 = 48,972
Generalization Error ∝ √(d / n) = √(48,971 / 300) = 12.78

解释: 泛化误差是基线的12.78倍 ❌
```

**实证研究** (文献[1]):

| 样本/维度比 | 测试集准确率 | 过拟合程度 |
|------------|------------|-----------|
| 10:1 | 85-90% | 低 ✅ |
| 5:1 | 75-85% | 中等 ⚠️ |
| 2:1 | 60-70% | 高 ❌ |
| 1:1 | 50-60% | 严重 ❌❌ |
| 0.5:1 | ~50% | 完全过拟合 ❌❌❌ |

**当前**: 300/48,971 = **0.006:1** → 预测准确率 ≈ 随机猜测

### 6.3 解决方案对比

| 方案 | 降维后维度 | 样本比 | 预期准确率 | 可解释性 |
|------|----------|--------|-----------|---------|
| **无降维** | 48,971 | 0.006:1 | ~33% | - |
| **PCA (保留95%方差)** | ~100 | 3:1 ✅ | 75-80% | 低 ❌ |
| **LASSO正则化** | ~50 | 6:1 ✅ | 78-83% | 中 ⚠️ |
| **策略A (敏感度Top-10)** | 10 | 30:1 ✅ | 75-82% | 高 ✅ |
| **策略B (敏感度Top-69)** | 69 | 4.3:1 ✅ | 80-88% | 中 ⚠️ |

**推荐**: 策略A (临床) + 策略B (科研)

---

# 第三部分: 核心设计

## 7. 双策略特征提取方案

### 7.1 策略概览

```
┌─────────────────────────────────────────────────────────────┐
│                   Module06 双策略设计                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐              ┌─────────────────┐        │
│  │   策略A: 极简    │              │   策略B: 综合    │        │
│  │   Top-10特征     │              │   Top-69特征     │        │
│  └─────────────────┘              └─────────────────┘        │
│         │                                  │                  │
│         ├─ Module04: 4维                   ├─ Module04: 9维  │
│         │   (敏感度Top-4)                  │   (全量核心)     │
│         │                                  │                  │
│         └─ Module05: 6维                   └─ Module05: 60维 │
│             (最优参数×6)                       (Top-10参数×6) │
│                                                               │
│  样本比: 30:1 ✅                    样本比: 4.3:1 ✅           │
│  适用: 临床/移动端                  适用: 科研/服务器          │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 策略A: Top-10极简策略

#### 7.2.1 设计理念

- **最小化维度**: 仅保留最敏感的10个特征
- **最大化样本比**: 30:1,远超安全线
- **极致可解释**: 每个特征都有明确临床意义
- **快速部署**: 特征提取 < 0.1s/样本

#### 7.2.2 特征选择流程

```python
def strategy_a_feature_selection():
    """策略A: Top-10特征选择"""

    # Step 1: Module04敏感度分析 (输入: 9个候选特征)
    m04_sensitivity = compute_module04_sensitivity()
    #   → 计算F-statistic, Effect Size, CV for 9 features
    #   → 输出: 按sensitivity_score排序

    # Step 2: 选择Top-4 Module04特征
    top4_m04 = m04_sensitivity.head(4)['feature_name'].tolist()
    # 预期结果 (待实际数据验证):
    # ['avg_fixation_duration', 'kw_ratio_frame',
    #  'avg_saccade_amplitude', 'total_fixations']

    # Step 3: Module05敏感度分析 (输入: 3264参数 × 15特征)
    m05_sensitivity = compute_module05_sensitivity()
    #   → 对每个(参数,特征)对计算overall_score
    #   → 跨参数聚合,选择Top-6特征

    # Step 4: 选择Top-6 Module05特征 (跨参数)
    top6_m05 = m05_sensitivity.groupby('feature').agg({
        'overall_score': 'mean'
    }).sort_values('overall_score', ascending=False).head(6).index.tolist()
    # 预期结果 (待实际数据验证):
    # ['rr-2d-xy', 'det-2d-xy', 'ent-1d-x',
    #  'rr-1d-x', 'det-1d-x', 'ent-2d-xy']

    # Step 5: 组合特征向量
    selected_features = {
        'module04': top4_m04,  # 4维
        'module05': top6_m05   # 6维
    }

    return selected_features  # Total: 10维
```

#### 7.2.3 特征向量结构

```python
StrategyA_FeatureVector = {
    # Module04 (4维)
    "m04_avg_fixation_duration": float,    # 平均注视时长
    "m04_kw_ratio_frame": float,           # 关键词占比
    "m04_avg_saccade_amplitude": float,    # 平均扫视幅度
    "m04_total_fixations": int,            # 总注视次数

    # Module05 (6维) - 跨参数最优特征
    "m05_rr_2d_xy": float,                 # 2D递归率
    "m05_det_2d_xy": float,                # 2D确定性
    "m05_ent_1d_x": float,                 # 1D-x熵
    "m05_rr_1d_x": float,                  # 1D-x递归率
    "m05_det_1d_x": float,                 # 1D-x确定性
    "m05_ent_2d_xy": float                 # 2D熵
}
# Total: 10维, 每维都有明确临床/认知意义
```

### 7.3 策略B: Top-69综合策略

#### 7.3.1 设计理念

- **信息完整性**: 保留Module04全量核心特征
- **参数多样性**: 从Top-10参数组合提取RQA特征
- **性能优先**: 追求最高分类准确率
- **科研导向**: 适合发表论文,特征探索

#### 7.3.2 特征选择流程

```python
def strategy_b_feature_selection():
    """策略B: Top-69特征选择"""

    # Step 1: Module04全量特征 (排除MMSE)
    m04_features = [
        'bg_ratio_frame', 'inst_ratio_frame', 'kw_ratio_frame',
        'total_fixation_time', 'total_fixations', 'avg_fixation_duration',
        'total_saccades', 'avg_saccade_amplitude', 'task_total_time'
    ]  # 9维

    # Step 2: Module05参数级敏感度分析
    m05_param_sensitivity = compute_module05_param_sensitivity()
    #   → 按参数组合聚合overall_score
    #   → 输出: 参数组合排序

    # Step 3: 选择Top-10参数组合
    top10_params = m05_param_sensitivity.head(10)['param_signature'].tolist()
    # 预期结果示例:
    # ['m2_tau1_eps0.050_lmin2', 'm3_tau2_eps0.055_lmin2', ...]

    # Step 4: 从每个参数提取6维核心RQA特征
    core_rqa_features = ['rr-1d-x', 'det-1d-x', 'ent-1d-x',
                         'rr-2d-xy', 'det-2d-xy', 'ent-2d-xy']

    m05_features = []
    for param in top10_params:
        for rqa_feat in core_rqa_features:
            m05_features.append(f"{param}_{rqa_feat}")
    # 10 params × 6 features = 60维

    # Step 5: 组合特征向量
    selected_features = {
        'module04': m04_features,  # 9维
        'module05': m05_features   # 60维
    }

    return selected_features  # Total: 69维
```

#### 7.3.3 特征向量结构

```python
StrategyB_FeatureVector = {
    # Module04 (9维)
    "m04_bg_ratio_frame": float,
    "m04_inst_ratio_frame": float,
    "m04_kw_ratio_frame": float,
    "m04_total_fixation_time": float,
    "m04_total_fixations": int,
    "m04_avg_fixation_duration": float,
    "m04_total_saccades": int,
    "m04_avg_saccade_amplitude": float,
    "m04_task_total_time": float,

    # Module05 (60维) - 10参数 × 6核心RQA特征
    "m05_m2_tau1_eps0.050_lmin2_rr_1d_x": float,
    "m05_m2_tau1_eps0.050_lmin2_det_1d_x": float,
    "m05_m2_tau1_eps0.050_lmin2_ent_1d_x": float,
    "m05_m2_tau1_eps0.050_lmin2_rr_2d_xy": float,
    "m05_m2_tau1_eps0.050_lmin2_det_2d_xy": float,
    "m05_m2_tau1_eps0.050_lmin2_ent_2d_xy": float,
    # ... 重复9次(其他9个参数组合)
}
# Total: 69维
```

### 7.4 策略对比

| 维度 | 策略A | 策略B | 说明 |
|------|-------|-------|------|
| **Module04特征数** | 4 | 9 | A选择Top-4,B全量 |
| **Module05参数数** | 跨参数 | 10 | A跨参数聚合,B保留10个 |
| **Module05特征数/参数** | 6 | 6 | 都使用6维核心RQA |
| **总维度** | 10 | 69 | A极简,B综合 |
| **样本比** | 30:1 | 4.3:1 | 都在安全范围 |
| **特征提取耗时** | ~0.1s | ~0.5s | A快5倍 |
| **可解释性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | A每维都可解释 |
| **预期准确率** | 75-82% | 80-88% | B高5-8% |
| **适用场景** | 临床/移动端 | 科研/服务器 |  |

---

## 8. 敏感度分析设计

### 8.1 Module04敏感度分析

#### 8.1.1 分析目标

从9个眼动特征中,基于**统计显著性**和**效应量**,选出区分Control/MCI/AD三组能力最强的Top-4特征。

#### 8.1.2 分析指标 (5个)

##### 指标1: ANOVA F-statistic

**公式**:
```
F = (组间均方 / 组内均方)
  = [Σ n_i(ȳ_i - ȳ)² / (k-1)] / [Σ Σ(y_ij - ȳ_i)² / (N-k)]

其中:
- k = 3 (组数: control/mci/ad)
- N = 300 (总样本数)
- n_i = 100 (每组样本数)
- ȳ_i = 组i的均值
- ȳ = 总均值
```

**解释**:
- F > 3.0: 组间差异显著
- p < 0.05: 拒绝零假设(三组均值相等)

**Python实现**:
```python
from scipy.stats import f_oneway

def compute_f_statistic(feature_name, df):
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

##### 指标2: Effect Size (Eta-squared)

**公式**:
```
η² = SS_between / SS_total
   = 组间平方和 / 总平方和

SS_between = Σ n_i(ȳ_i - ȳ)²
SS_total = Σ Σ(y_ij - ȳ)²
```

**解释** (Cohen's标准):
- η² < 0.01: 可忽略
- 0.01 ≤ η² < 0.06: 小效应
- 0.06 ≤ η² < 0.14: 中等效应
- η² ≥ 0.14: 大效应

**优势**: 不受样本量影响,量化实际效应大小

**Python实现**:
```python
def compute_effect_size(feature_name, df):
    grand_mean = df[feature_name].mean()

    # 组间平方和
    ss_between = 0
    for group in ['control', 'mci', 'ad']:
        group_data = df[df['group'] == group][feature_name].dropna()
        n = len(group_data)
        group_mean = group_data.mean()
        ss_between += n * (group_mean - grand_mean) ** 2

    # 总平方和
    ss_total = ((df[feature_name] - grand_mean) ** 2).sum()

    eta_squared = ss_between / ss_total if ss_total > 0 else 0

    # 分类
    if eta_squared < 0.01:
        label = "negligible"
    elif eta_squared < 0.06:
        label = "small"
    elif eta_squared < 0.14:
        label = "medium"
    else:
        label = "large"

    return {
        'eta_squared': eta_squared,
        'effect_size': label
    }
```

##### 指标3: Pairwise T-tests (Bonferroni校正)

**目的**: 确定哪些组对之间有显著差异

**方法**:
```
3个两两比较:
1. Control vs MCI
2. Control vs AD
3. MCI vs AD

Bonferroni校正: α_adjusted = 0.05 / 3 = 0.0167
```

**解释**:
- 如果只有Control vs AD显著 → 适合诊断AD,但不适合早期MCI检测
- 如果三对都显著 → 适合全疾病进程监测

**Python实现**:
```python
from scipy.stats import ttest_ind

def compute_pairwise_tests(feature_name, df):
    control = df[df['group'] == 'control'][feature_name].dropna()
    mci = df[df['group'] == 'mci'][feature_name].dropna()
    ad = df[df['group'] == 'ad'][feature_name].dropna()

    bonferroni_alpha = 0.05 / 3

    tests = {}
    for (name, g1, g2) in [
        ('control_vs_mci', control, mci),
        ('control_vs_ad', control, ad),
        ('mci_vs_ad', mci, ad)
    ]:
        t_stat, p_val = ttest_ind(g1, g2)
        tests[name] = {
            't_statistic': t_stat,
            'p_value': p_val,
            'significant': p_val < bonferroni_alpha
        }

    return tests
```

##### 指标4: Cohen's d

**公式**:
```
d = (μ₁ - μ₂) / s_pooled

s_pooled = √[((n₁-1)s₁² + (n₂-1)s₂²) / (n₁+n₂-2)]
```

**解释**:
- |d| < 0.2: 极小
- 0.2 ≤ |d| < 0.5: 小
- 0.5 ≤ |d| < 0.8: 中等
- |d| ≥ 0.8: 大

**Python实现**:
```python
def compute_cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()

    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    cohens_d = (group1.mean() - group2.mean()) / pooled_std if pooled_std > 0 else 0

    return cohens_d
```

##### 指标5: 变异系数 (CV)

**公式**:
```
CV = (σ / μ) × 100%
```

**目的**: 评估特征稳定性
- 低CV → 组内一致性高,特征可靠
- 高CV → 组内波动大,可能噪声多

**Python实现**:
```python
def compute_coefficient_of_variation(feature_name, df):
    cv_dict = {}
    for group in ['control', 'mci', 'ad']:
        group_data = df[df['group'] == group][feature_name].dropna()
        mean = group_data.mean()
        std = group_data.std()
        cv = (std / mean * 100) if mean != 0 else 0
        cv_dict[f'cv_{group}'] = cv

    cv_dict['avg_cv'] = np.mean(list(cv_dict.values()))
    return cv_dict
```

#### 8.1.3 综合敏感度得分

**公式**:
```python
sensitivity_score = (F × η²) / (1 + p_value) × (1 / (1 + CV/100))

设计理念:
1. F × η²: 核心得分 (显著性 × 效应量)
2. / (1 + p_value): p值惩罚 (p越小,得分越高)
3. × (1 / (1 + CV/100)): 稳定性奖励 (CV越低,得分越高)
```

**示例**:
```
特征A: F=50, η²=0.3, p=0.001, CV=15
  → score = (50 × 0.3) / (1 + 0.001) × (1 / (1 + 0.15))
          = 15 / 1.001 × 0.87 = 13.03

特征B: F=40, η²=0.25, p=0.01, CV=25
  → score = (40 × 0.25) / (1 + 0.01) × (1 / (1 + 0.25))
          = 10 / 1.01 × 0.80 = 7.92

特征A得分更高 (更稳定,p值更小)
```

#### 8.1.4 API设计

**端点1: 计算全局敏感度**
```
GET /api/m04/sensitivity/compute-features
Query Parameters:
  - data_version: v1 (默认)
  - sort_by: sensitivity_score (默认)

Response:
{
    "success": true,
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
            "sensitivity_score": 13.045,
            "group_means": {
                "control": 245.67,
                "mci": 268.34,
                "ad": 289.12
            }
        },
        ...
    ],
    "summary": {
        "top_4_features": ["avg_fixation_duration", "kw_ratio_frame", "avg_saccade_amplitude", "total_fixations"]
    }
}
```

**端点2: 任务级敏感度**
```
GET /api/m04/sensitivity/compute-features-by-task?task_id=q1

Response:
{
    "success": true,
    "tasks": {
        "q1": {
            "total_samples": 60,
            "features": [...],
            "top_4_features": ["kw_ratio_frame", "inst_ratio_frame", ...]
        }
    }
}
```

### 8.2 Module05敏感度分析

#### 8.2.1 已实现功能

✅ **Module05已有完整敏感度分析**: `parameter_sensitivity_analyzer.py`

**核心类**: `ParameterSensitivityAnalyzer`

**分析指标** (5个):
1. **F-statistic**: 跨任务(q1-q5)平均
2. **P-value**: 统计显著性
3. **Effect Size (η²)**: 效应量
4. **Task Consistency**: 跨任务稳定性 (F值的CV倒数)
5. **Overall Score**: 综合得分

**公式**:
```python
overall_score = (
    0.4 × min(F/100, 1.0) +      # F统计量权重40%
    0.3 × eta_squared +           # 效应量权重30%
    0.2 × task_consistency -      # 一致性权重20%
    0.1 × p_value                 # p值惩罚10%
)
```

#### 8.2.2 API端点

**端点1: 扫描RQA结果**
```
GET /api/m05/sensitivity/scan-results

Response:
{
    "success": true,
    "results": [
        {
            "params": {"m": 2, "tau": 1, "eps": 0.050, "lmin": 2},
            "enriched_features_path": "data/05_rqa_analysis/.../step3_enriched_features.csv"
        },
        ...
    ],
    "total": 3264
}
```

**端点2: 计算敏感度 (异步)**
```
POST /api/m05/sensitivity/compute-scores
{
    "params_filter": {
        "m_range": [1, 10],
        "tau_range": [1, 10]
    }
}

Response:
{
    "success": true,
    "task_id": "sensitivity_task_20251010_143052"
}
```

**端点3: 查询任务状态**
```
GET /api/m05/sensitivity/status/<task_id>

Response:
{
    "success": true,
    "data": {
        "task": {
            "status": "completed",
            "result_file": "data/05_rqa_analysis/sensitivity_scores.csv"
        }
    }
}
```

#### 8.2.3 特征选择策略

**策略1: 跨参数Top-6特征** (推荐用于策略A)

```python
# 读取敏感度评分
sensitivity_df = pd.read_csv('sensitivity_scores.csv')

# 按特征聚合(忽略参数差异)
feature_scores = sensitivity_df.groupby('feature').agg({
    'overall_score': 'mean',
    'f_statistic': 'mean',
    'effect_size': 'mean',
    'task_consistency': 'mean'
}).sort_values('overall_score', ascending=False)

# 选择Top-6
top6_features = feature_scores.head(6).index.tolist()

# 预期结果 (待实际数据验证):
# ['rr-2d-xy', 'det-2d-xy', 'ent-1d-x', 'rr-1d-x', 'det-1d-x', 'ent-2d-xy']
```

**优势**:
- 特征多样性高
- 不局限于单一参数组合
- 鲁棒性强

**策略2: Top-10参数 × 6核心特征** (推荐用于策略B)

```python
# 按参数组合聚合
param_scores = sensitivity_df.groupby('param_signature').agg({
    'overall_score': 'mean'
}).sort_values('overall_score', ascending=False)

# 选择Top-10参数
top10_params = param_scores.head(10).index.tolist()

# 从每个参数提取6维核心RQA
core_rqa = ['rr-1d-x', 'det-1d-x', 'ent-1d-x',
            'rr-2d-xy', 'det-2d-xy', 'ent-2d-xy']

# 总计: 10 × 6 = 60维
```

**优势**:
- 保留参数多样性(低复杂度 → 高复杂度)
- 特征完整性高
- 适合ensemble模型

---

## 9. 特征选择算法

### 9.1 算法流程图

```
┌─────────────────────────────────────────────────────────────┐
│           Module06 特征选择算法 (策略A)                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ 输入: 原始特征空间                │
        │ - Module04: 9维候选特征          │
        │ - Module05: 3264参数 × 15特征    │
        └──────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ Phase 1: Module04敏感度分析      │
        │                                  │
        │ For each of 9 features:          │
        │   1. Compute F-statistic         │
        │   2. Compute Effect Size (η²)    │
        │   3. Compute Pairwise t-tests    │
        │   4. Compute Cohen's d           │
        │   5. Compute CV                  │
        │   6. Compute sensitivity_score   │
        └──────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ Rank & Select: Top-4 M04 features│
        │                                  │
        │ Sort by sensitivity_score DESC   │
        │ Output: ['avg_fixation_duration',│
        │          'kw_ratio_frame',       │
        │          'avg_saccade_amplitude',│
        │          'total_fixations']      │
        └──────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ Phase 2: Module05敏感度分析      │
        │                                  │
        │ For each (param, feature) pair:  │
        │   1. Compute F-stat (per task)   │
        │   2. Compute Effect Size         │
        │   3. Compute Task Consistency    │
        │   4. Compute overall_score       │
        └──────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ Aggregate: 跨参数聚合特征敏感度   │
        │                                  │
        │ Group by 'feature'               │
        │ Aggregate: mean(overall_score)   │
        └──────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ Rank & Select: Top-6 M05 features│
        │                                  │
        │ Sort by mean_score DESC          │
        │ Output: ['rr-2d-xy',             │
        │          'det-2d-xy',            │
        │          'ent-1d-x',             │
        │          'rr-1d-x',              │
        │          'det-1d-x',             │
        │          'ent-2d-xy']            │
        └──────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ Phase 3: 特征向量构建            │
        │                                  │
        │ For each sample:                 │
        │   1. Extract 4 M04 features      │
        │   2. Extract 6 M05 features      │
        │   3. Concatenate → 10D vector    │
        │   4. Z-score normalization       │
        └──────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ Output: 10维标准化特征向量        │
        │                                  │
        │ Shape: (300, 10)                 │
        │ Sample:Feature Ratio = 30:1 ✅   │
        └──────────────────────────────────┘
```

### 9.2 伪代码

```python
class FeatureSelectionPipeline:
    """Module06特征选择流水线"""

    def __init__(self, strategy='A'):
        self.strategy = strategy

    def execute(self, data_version='v1'):
        """执行特征选择"""

        if self.strategy == 'A':
            return self._strategy_a(data_version)
        elif self.strategy == 'B':
            return self._strategy_b(data_version)

    def _strategy_a(self, data_version):
        """策略A: Top-10特征"""

        # Phase 1: Module04敏感度分析
        m04_features_df = self.load_module04_features(data_version)
        m04_sensitivity = self.compute_module04_sensitivity(m04_features_df)

        # 选择Top-4
        top4_m04 = m04_sensitivity.head(4)['feature_name'].tolist()

        # Phase 2: Module05敏感度分析
        m05_results = self.scan_module05_results()
        m05_sensitivity = self.compute_module05_sensitivity(m05_results)

        # 跨参数聚合,选择Top-6特征
        m05_feature_agg = m05_sensitivity.groupby('feature').agg({
            'overall_score': 'mean'
        }).sort_values('overall_score', ascending=False)

        top6_m05 = m05_feature_agg.head(6).index.tolist()

        # Phase 3: 构建特征向量
        feature_vectors = []
        for sample in self.iter_samples():
            vector = {}

            # 提取Module04特征
            for feat in top4_m04:
                vector[f"m04_{feat}"] = sample.get_module04_value(feat)

            # 提取Module05特征 (从最优参数组合)
            best_param = self.get_best_param_for_features(top6_m05, m05_sensitivity)
            for feat in top6_m05:
                vector[f"m05_{feat}"] = sample.get_module05_value(best_param, feat)

            feature_vectors.append(vector)

        # Phase 4: 标准化
        normalized = self.normalize(feature_vectors, method='zscore')

        return {
            'strategy': 'A',
            'dimensions': 10,
            'features': feature_vectors,
            'normalized': normalized,
            'metadata': {
                'top4_m04': top4_m04,
                'top6_m05': top6_m05,
                'sample_ratio': 30.0
            }
        }

    def _strategy_b(self, data_version):
        """策略B: Top-69特征"""

        # Phase 1: Module04全量特征
        m04_features = [
            'bg_ratio_frame', 'inst_ratio_frame', 'kw_ratio_frame',
            'total_fixation_time', 'total_fixations', 'avg_fixation_duration',
            'total_saccades', 'avg_saccade_amplitude', 'task_total_time'
        ]  # 9维

        # Phase 2: Module05参数敏感度分析
        m05_results = self.scan_module05_results()
        m05_sensitivity = self.compute_module05_sensitivity(m05_results)

        # 按参数聚合,选择Top-10参数
        m05_param_agg = m05_sensitivity.groupby('param_signature').agg({
            'overall_score': 'mean'
        }).sort_values('overall_score', ascending=False)

        top10_params = m05_param_agg.head(10).index.tolist()

        # 从每个参数提取6维核心RQA
        core_rqa = ['rr-1d-x', 'det-1d-x', 'ent-1d-x',
                    'rr-2d-xy', 'det-2d-xy', 'ent-2d-xy']

        # Phase 3: 构建特征向量
        feature_vectors = []
        for sample in self.iter_samples():
            vector = {}

            # Module04: 9维
            for feat in m04_features:
                vector[f"m04_{feat}"] = sample.get_module04_value(feat)

            # Module05: 10参数 × 6特征 = 60维
            for param in top10_params:
                for rqa_feat in core_rqa:
                    key = f"m05_{param}_{rqa_feat}"
                    vector[key] = sample.get_module05_value(param, rqa_feat)

            feature_vectors.append(vector)

        # Phase 4: 标准化
        normalized = self.normalize(feature_vectors, method='zscore')

        return {
            'strategy': 'B',
            'dimensions': 69,
            'features': feature_vectors,
            'normalized': normalized,
            'metadata': {
                'm04_features': m04_features,
                'top10_params': top10_params,
                'core_rqa': core_rqa,
                'sample_ratio': 4.35
            }
        }

    def compute_module04_sensitivity(self, df):
        """计算Module04敏感度"""
        from scipy.stats import f_oneway, ttest_ind

        results = []
        for feature in self.get_m04_candidate_features():
            # 提取三组数据
            control = df[df['group']=='control'][feature].dropna()
            mci = df[df['group']=='mci'][feature].dropna()
            ad = df[df['group']=='ad'][feature].dropna()

            # 指标1: ANOVA
            f_stat, p_value = f_oneway(control, mci, ad)

            # 指标2: Effect Size
            eta_squared = self._compute_eta_squared(df, feature)

            # 指标3: Pairwise tests
            pairwise = self._compute_pairwise(control, mci, ad)

            # 指标4: Cohen's d
            cohens_d = self._compute_cohens_d(control, mci, ad)

            # 指标5: CV
            cv_stats = self._compute_cv(control, mci, ad)

            # 综合得分
            sensitivity_score = (f_stat * eta_squared) / (1 + p_value) * (1 / (1 + cv_stats['avg_cv']/100))

            results.append({
                'feature_name': feature,
                'f_statistic': f_stat,
                'p_value': p_value,
                'eta_squared': eta_squared,
                'sensitivity_score': sensitivity_score,
                **pairwise,
                **cohens_d,
                **cv_stats
            })

        return pd.DataFrame(results).sort_values('sensitivity_score', ascending=False)

    def compute_module05_sensitivity(self, results_by_params):
        """计算Module05敏感度 (调用已实现的ParameterSensitivityAnalyzer)"""
        from src.modules.module05_rqa_analysis.parameter_sensitivity_analyzer import ParameterSensitivityAnalyzer

        analyzer = ParameterSensitivityAnalyzer()
        sensitivity_df = analyzer.compute_parameter_sensitivity_scores(results_by_params)

        return sensitivity_df

    def normalize(self, feature_vectors, method='zscore'):
        """特征标准化"""
        from sklearn.preprocessing import StandardScaler

        # 转DataFrame
        df = pd.DataFrame(feature_vectors)

        if method == 'zscore':
            scaler = StandardScaler()
            normalized_values = scaler.fit_transform(df.values)
            normalized_df = pd.DataFrame(normalized_values, columns=df.columns)

        return normalized_df
```

---

# 第四部分: 系统架构

## 10. 系统架构设计

### 10.1 整体架构

```
┌────────────────────────────────────────────────────────────────┐
│                     Module06 System Architecture                │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Frontend Layer (React)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │FeatureSelection  │  │ Sensitivity      │  │ Feature        ││
│  │Panel             │  │ Visualization    │  │ Statistics     ││
│  └──────────────────┘  └──────────────────┘  └────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                             │  HTTP/JSON
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer (Flask)                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /api/m06/extract/strategy-a                              │  │
│  │ /api/m06/extract/strategy-b                              │  │
│  │ /api/m06/extract/batch                                   │  │
│  │ /api/m06/sensitivity/m04-features                        │  │
│  │ /api/m06/sensitivity/feature-comparison                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer (Business Logic)               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ FeatureExtractionService                                │   │
│  │  ├─ extract_strategy_a()                                │   │
│  │  ├─ extract_strategy_b()                                │   │
│  │  ├─ extract_batch()                                     │   │
│  │  └─ normalize_features()                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ SensitivityAnalysisService                              │   │
│  │  ├─ compute_m04_sensitivity()                           │   │
│  │  ├─ compute_m05_sensitivity()                           │   │
│  │  └─ get_feature_rankings()                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Integration Layer (Module Clients)               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │ Module04Client   │           │ Module05Client   │           │
│  │ ┌──────────────┐ │           │ ┌──────────────┐ │           │
│  │ │GET /features │ │           │ │GET /results  │ │           │
│  │ │POST /        │ │           │ │POST /        │ │           │
│  │ │sensitivity   │ │           │ │sensitivity   │ │           │
│  │ └──────────────┘ │           │ └──────────────┘ │           │
│  └──────────────────┘           └──────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Access Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ FeatureRepository                                       │   │
│  │  ├─ save_features(df, strategy)                         │   │
│  │  ├─ load_features(strategy, data_version)               │   │
│  │  └─ load_sensitivity_scores()                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ File System                                              │  │
│  │  ├─ data/06_features/                                    │  │
│  │  │   ├─ strategy_a/                                      │  │
│  │  │   │   └─ features_v1_20251010.csv                     │  │
│  │  │   ├─ strategy_b/                                      │  │
│  │  │   └─ sensitivity_scores/                              │  │
│  │  │       ├─ m04_sensitivity.csv                          │  │
│  │  │       └─ m05_sensitivity.csv                          │  │
│  │  ├─ 04_features/cache/latest_analysis.json               │  │
│  │  └─ 05_rqa_analysis/m*_tau*/step3_enriched_features.csv │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 模块目录结构

```
new_project/
├── src/
│   └── modules/
│       └── module06_feature_extraction/
│           ├── __init__.py
│           ├── api.py                          # Flask API路由
│           ├── service.py                      # 特征提取服务
│           ├── sensitivity_analyzer.py         # Module04敏感度分析
│           ├── feature_selector.py             # 特征选择器
│           ├── normalizer.py                   # 特征标准化
│           ├── repository.py                   # 数据访问层
│           ├── clients/
│           │   ├── module04_client.py          # Module04 API客户端
│           │   └── module05_client.py          # Module05 API客户端
│           └── utils.py                        # 工具函数
│
├── data/
│   └── 06_features/
│       ├── strategy_a/
│       ├── strategy_b/
│       └── sensitivity_scores/
│
├── frontend/
│   └── src/
│       └── components/
│           └── Module06/
│               ├── FeatureSelectionPanel.jsx   # 特征选择界面
│               ├── SensitivityDashboard.jsx    # 敏感度分析仪表板
│               └── FeatureStatistics.jsx       # 特征统计可视化
│
├── docs/
│   ├── MODULE06_COMPREHENSIVE_DESIGN.md        # (本文档)
│   ├── MODULE04_SENSITIVITY_ANALYSIS_DESIGN.md
│   └── MODULE05_SENSITIVITY_ANALYSIS_REPORT.md
│
└── tests/
    └── test_module06/
        ├── test_sensitivity_analyzer.py
        ├── test_feature_selector.py
        └── test_service.py
```

---

## 11. API接口设计

### 11.1 特征提取API

#### API #1: 策略A特征提取
```
POST /api/m06/extract/strategy-a

Request Body:
{
    "subject_id": "control_legacy_1",
    "group": "control",
    "task_id": "q1",
    "data_version": "v1"
}

Response:
{
    "success": true,
    "strategy": "A",
    "dimensions": 10,
    "features": {
        "m04_avg_fixation_duration": 245.67,
        "m04_kw_ratio_frame": 35.2,
        "m04_avg_saccade_amplitude": 4.87,
        "m04_total_fixations": 128,
        "m05_rr_2d_xy": 0.234,
        "m05_det_2d_xy": 0.567,
        "m05_ent_1d_x": 1.234,
        "m05_rr_1d_x": 0.189,
        "m05_det_1d_x": 0.456,
        "m05_ent_2d_xy": 1.567
    },
    "normalized": [0.23, -0.45, 0.78, -0.12, 0.56, -0.34, 0.89, -0.67, 0.23, 0.45],
    "metadata": {
        "extraction_time_ms": 87,
        "m04_source": "/api/m04/features",
        "m05_best_param": "m2_tau1_eps0.050_lmin2"
    }
}
```

#### API #2: 策略B特征提取
```
POST /api/m06/extract/strategy-b

Request Body:
{
    "subject_id": "control_legacy_1",
    "group": "control",
    "task_id": "q1",
    "data_version": "v1"
}

Response:
{
    "success": true,
    "strategy": "B",
    "dimensions": 69,
    "features": {
        "m04_bg_ratio_frame": 45.2,
        "m04_inst_ratio_frame": 20.3,
        ... (9 Module04 features)
        "m05_m2_tau1_eps0.050_lmin2_rr_1d_x": 0.234,
        ... (60 Module05 features)
    },
    "normalized": [...],  // 69维数组
    "metadata": {
        "extraction_time_ms": 423,
        "top10_params": ["m2_tau1_eps0.050_lmin2", ...]
    }
}
```

#### API #3: 批量特征提取
```
POST /api/m06/extract/batch

Request Body:
{
    "strategy": "A",  // or "B"
    "groups": ["control", "mci", "ad"],
    "data_version": "v1",
    "output_format": "csv"  // or "json"
}

Response:
{
    "success": true,
    "task_id": "batch_extraction_20251010_150030",
    "estimated_time_seconds": 180
}

# 查询任务状态
GET /api/m06/extract/batch/status/<task_id>

Response (completed):
{
    "success": true,
    "status": "completed",
    "result_file": "data/06_features/strategy_a/features_v1_20251010_150030.csv",
    "download_url": "/api/m06/download/<task_id>",
    "total_samples": 300,
    "total_time_seconds": 176
}
```

### 11.2 敏感度分析API

#### API #4: Module04敏感度分析
```
GET /api/m06/sensitivity/m04-features?data_version=v1

Response:
{
    "success": true,
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
            "pairwise_tests": {...},
            "cohens_d": {...},
            "variability": {...},
            "sensitivity_score": 13.045
        },
        ...
    ],
    "summary": {
        "top_4_features": ["avg_fixation_duration", "kw_ratio_frame", "avg_saccade_amplitude", "total_fixations"],
        "highly_significant_count": 6
    }
}
```

#### API #5: 特征对比可视化
```
GET /api/m06/sensitivity/feature-comparison?features=avg_fixation_duration,kw_ratio_frame

Response:
{
    "success": true,
    "features": {
        "avg_fixation_duration": {
            "control": [245.3, 250.1, ...],  // 100个数据点
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

### 11.3 工具API

#### API #6: 特征元数据
```
GET /api/m06/metadata/features

Response:
{
    "success": true,
    "module04_features": {
        "avg_fixation_duration": {
            "type": "float",
            "unit": "ms",
            "range": [100, 1000],
            "description": "平均注视时长",
            "clinical_meaning": "注意力稳定性"
        },
        ...
    },
    "module05_features": {
        "rr-1d-x": {
            "type": "float",
            "range": [0, 1],
            "description": "1D-x递归率",
            "clinical_meaning": "水平眼动刻板性"
        },
        ...
    }
}
```

---

## 12. 数据流设计

### 12.1 策略A数据流

```
User Request (POST /api/m06/extract/strategy-a)
  │
  ▼
API Layer (api.py: extract_strategy_a())
  │
  ├─ Validate Request
  │   ├─ subject_id exists?
  │   ├─ group in [control, mci, ad]?
  │   └─ task_id in [q1, q2, q3, q4, q5]?
  │
  ▼
Service Layer (service.py: FeatureExtractionService.extract_strategy_a())
  │
  ├─ Step 1: Load Sensitivity Scores (cached)
  │   ├─ Check cache: data/06_features/sensitivity_scores/m04_sensitivity.csv
  │   └─ If not exist → Trigger sensitivity analysis
  │
  ├─ Step 2: Get Top-4 M04 Features
  │   ├─ Read m04_sensitivity.csv
  │   └─ Select top 4 by sensitivity_score
  │
  ├─ Step 3: Get Top-6 M05 Features
  │   ├─ Read m05_sensitivity.csv
  │   ├─ Group by 'feature'
  │   └─ Select top 6 by mean(overall_score)
  │
  ▼
Integration Layer (clients/)
  │
  ├─ Module04Client.get_features(subject_id, group, task_id)
  │   │
  │   ├─ HTTP GET /api/m04/features
  │   │
  │   └─ Extract: {
  │         'avg_fixation_duration': 245.67,
  │         'kw_ratio_frame': 35.2,
  │         'avg_saccade_amplitude': 4.87,
  │         'total_fixations': 128
  │       }
  │
  └─ Module05Client.get_rqa_features(subject_id, task_id, best_param)
      │
      ├─ Determine best_param from sensitivity analysis
      │   (e.g., m=2, tau=1, eps=0.05, lmin=2)
      │
      ├─ Read CSV: data/05_rqa_analysis/m2_tau1_eps0.050_lmin2/step3_enriched_features.csv
      │
      └─ Extract: {
            'rr-2d-xy': 0.234,
            'det-2d-xy': 0.567,
            'ent-1d-x': 1.234,
            'rr-1d-x': 0.189,
            'det-1d-x': 0.456,
            'ent-2d-xy': 1.567
          }
  │
  ▼
Service Layer (normalizer.py: normalize())
  │
  ├─ Concatenate M04 + M05 features → 10D vector
  │
  ├─ Z-score normalization:
  │   z_i = (x_i - μ_i) / σ_i
  │   (使用全局统计量,从缓存加载)
  │
  └─ Return: {
        'features': {...},
        'normalized': [0.23, -0.45, ...]
      }
  │
  ▼
Data Access Layer (repository.py: save_features())
  │
  ├─ Optional: Cache feature vector
  │
  └─ Save to: data/06_features/strategy_a/cache/
  │
  ▼
API Response (JSON)
  │
  └─ Return to client
```

### 12.2 敏感度分析数据流

```
User Request (GET /api/m06/sensitivity/m04-features)
  │
  ▼
API Layer (api.py: get_m04_sensitivity())
  │
  ├─ Check cache: data/06_features/sensitivity_scores/m04_sensitivity.csv
  │
  ├─ If cached → Return cached results
  │
  └─ If not cached → Trigger analysis
  │
  ▼
Service Layer (sensitivity_analyzer.py: SensitivityAnalyzer.compute_all())
  │
  ├─ Step 1: Load Module04 Features
  │   └─ Module04Client.get_all_features(data_version='v1')
  │       → 返回300样本 × 11特征的DataFrame
  │
  ├─ Step 2: Filter out MMSE features
  │   └─ 排除 'mmse_total_score', 'mmse_task_score'
  │       → 剩余9个候选特征
  │
  ├─ Step 3: For each of 9 features
  │   │
  │   ├─ Extract 3 groups
  │   │   ├─ control = df[df['group']=='control'][feature]
  │   │   ├─ mci = df[df['group']=='mci'][feature]
  │   │   └─ ad = df[df['group']=='ad'][feature]
  │   │
  │   ├─ Compute Metrics
  │   │   ├─ F-statistic: f_oneway(control, mci, ad)
  │   │   ├─ Effect Size: eta_squared
  │   │   ├─ Pairwise t-tests: ttest_ind() × 3
  │   │   ├─ Cohen's d × 3
  │   │   └─ CV × 3
  │   │
  │   └─ Compute sensitivity_score
  │       = (F × η²) / (1 + p) × (1 / (1 + CV/100))
  │
  ├─ Step 4: Sort by sensitivity_score DESC
  │
  └─ Step 5: Cache results
      └─ Save to: data/06_features/sensitivity_scores/m04_sensitivity.csv
  │
  ▼
API Response (JSON)
  │
  └─ Return ranked features + summary
```

---

# 第五部分: 实施与部署

## 13. 实施路线图

### 13.1 总体时间线

**总工期**: 6周 (Week 1 - Week 6)

```
Week 1-2: 敏感度分析实施
Week 3-4: 特征提取服务开发
Week 5:   API & Frontend集成
Week 6:   测试与部署
```

### 13.2 详细任务分解

#### Phase 1: 敏感度分析 (Week 1-2)

| 任务 | 优先级 | 工期 | 负责人 | 产出 |
|------|--------|------|--------|------|
| **Week 1.1**: Module04敏感度分析器开发 | P0 | 3天 | Backend | `sensitivity_analyzer.py` |
| - 实现`SensitivityAnalyzer`类 | P0 | 1天 | | 5个指标计算函数 |
| - 实现综合评分算法 | P0 | 0.5天 | | `compute_sensitivity_score()` |
| - 单元测试 | P0 | 1天 | | 测试覆盖率 > 80% |
| - 模拟数据验证 | P1 | 0.5天 | | 验证报告 |
| **Week 1.2**: Module04敏感度API | P0 | 2天 | Backend | API端点 |
| - 添加3个API端点 | P0 | 1天 | | `/compute-features`, `/by-task`, `/comparison` |
| - API集成测试 | P0 | 1天 | | Postman测试集 |
| **Week 2.1**: 运行Module05敏感度分析 | P0 | 2天 | Data | 敏感度评分文件 |
| - 调用`/api/m05/sensitivity/compute-scores` | P0 | 0.5天 | | 提交任务 |
| - 监控执行(10-30分钟) | P0 | 0.5天 | | 等待完成 |
| - 分析结果,生成报告 | P0 | 1天 | | Top-10参数, Top-6特征 |
| **Week 2.2**: 敏感度结果验证 | P1 | 3天 | All | 验证报告 |
| - 与文献对比 | P1 | 1天 | Research | 文献调研 |
| - 跨任务一致性检查 | P1 | 1天 | Data | 一致性分析 |
| - 临床专家评审 | P2 | 1天 | Clinical | 专家意见 |

#### Phase 2: 特征提取服务 (Week 3-4)

| 任务 | 优先级 | 工期 | 负责人 | 产出 |
|------|--------|------|--------|------|
| **Week 3.1**: 核心服务类开发 | P0 | 3天 | Backend | `service.py` |
| - `FeatureExtractionService`类 | P0 | 1天 | | 服务类骨架 |
| - `extract_strategy_a()` | P0 | 1天 | | 策略A实现 |
| - `extract_strategy_b()` | P0 | 1天 | | 策略B实现 |
| **Week 3.2**: Module客户端开发 | P0 | 2天 | Backend | `clients/` |
| - `Module04Client` | P0 | 1天 | | HTTP客户端 |
| - `Module05Client` | P0 | 1天 | | 文件读取客户端 |
| **Week 4.1**: 特征标准化 | P0 | 2天 | Backend | `normalizer.py` |
| - Z-score归一化 | P0 | 1天 | | `ZScoreNormalizer`类 |
| - 缺失值处理 | P0 | 0.5天 | | Imputation策略 |
| - 异常值检测 | P1 | 0.5天 | | IQR方法 |
| **Week 4.2**: 数据访问层 | P0 | 2天 | Backend | `repository.py` |
| - `FeatureRepository`类 | P0 | 1天 | | CRUD操作 |
| - CSV读写 | P0 | 0.5天 | | Pandas集成 |
| - 缓存机制 | P1 | 0.5天 | | LRU缓存 |
| **Week 4.3**: 单元测试 | P0 | 2天 | Backend | `tests/test_module06/` |
| - Service层测试 | P0 | 1天 | | Pytest测试集 |
| - 集成测试 | P0 | 1天 | | End-to-end测试 |

#### Phase 3: API & Frontend (Week 5)

| 任务 | 优先级 | 工期 | 负责人 | 产出 |
|------|--------|------|--------|------|
| **Week 5.1**: API端点实现 | P0 | 2天 | Backend | `api.py` |
| - `/extract/strategy-a` | P0 | 0.5天 | | API端点 |
| - `/extract/strategy-b` | P0 | 0.5天 | | API端点 |
| - `/extract/batch` | P0 | 0.5天 | | 异步任务 |
| - `/metadata/features` | P1 | 0.5天 | | 元数据API |
| **Week 5.2**: Frontend组件开发 | P1 | 3天 | Frontend | React组件 |
| - `FeatureSelectionPanel.jsx` | P1 | 1天 | | 特征选择UI |
| - `SensitivityDashboard.jsx` | P1 | 1天 | | 敏感度可视化 |
| - `FeatureStatistics.jsx` | P2 | 1天 | | 统计图表 |

#### Phase 4: 测试与部署 (Week 6)

| 任务 | 优先级 | 工期 | 负责人 | 产出 |
|------|--------|------|--------|------|
| **Week 6.1**: 集成测试 | P0 | 2天 | QA | 测试报告 |
| - API功能测试 | P0 | 1天 | | Postman测试集 |
| - 性能测试 | P0 | 1天 | | 性能基准 |
| **Week 6.2**: 批量特征提取 | P0 | 1天 | Data | 特征文件 |
| - 提取300样本 × 2策略 | P0 | 0.5天 | | CSV文件 |
| - 验证特征质量 | P0 | 0.5天 | | 验证报告 |
| **Week 6.3**: 文档与部署 | P0 | 2天 | All | 部署完成 |
| - API文档补充 | P0 | 0.5天 | | Swagger文档 |
| - 使用手册 | P1 | 0.5天 | | 用户手册 |
| - 生产环境部署 | P0 | 1天 | DevOps | 部署完成 |

### 13.3 里程碑

| 里程碑 | 日期 | 交付物 | 验收标准 |
|--------|------|--------|---------|
| **M1: 敏感度分析完成** | Week 2 End | m04_sensitivity.csv + m05_sensitivity.csv | Top-4和Top-6特征确定 |
| **M2: 核心服务完成** | Week 4 End | FeatureExtractionService可用 | 单元测试通过率 > 80% |
| **M3: API集成完成** | Week 5 End | 6个API端点可用 | API响应时间 < 500ms |
| **M4: 生产部署完成** | Week 6 End | Module06上线 | 300样本特征提取完成 |

---

## 14. 测试策略

### 14.1 测试金字塔

```
           ┌──────────────┐
           │  E2E Tests   │  (10%) - 端到端测试
           │   ~5 cases   │
           └──────────────┘
         ┌────────────────────┐
         │ Integration Tests  │  (30%) - 集成测试
         │    ~15 cases       │
         └────────────────────┘
    ┌───────────────────────────────┐
    │      Unit Tests               │  (60%) - 单元测试
    │       ~30 cases               │
    └───────────────────────────────┘
```

### 14.2 单元测试 (60%)

**目标**: 测试覆盖率 > 80%

**测试文件**: `tests/test_module06/test_sensitivity_analyzer.py`

```python
import pytest
import pandas as pd
import numpy as np
from src.modules.module06_feature_extraction.sensitivity_analyzer import SensitivityAnalyzer

class TestSensitivityAnalyzer:
    """SensitivityAnalyzer单元测试"""

    @pytest.fixture
    def sample_data(self):
        """生成模拟数据"""
        np.random.seed(42)
        data = []
        for group in ['control', 'mci', 'ad']:
            for i in range(100):
                data.append({
                    'subject_id': f'{group}_sub_{i}',
                    'group': group,
                    'task_id': 'q1',
                    'avg_fixation_duration': np.random.normal(250 + (group=='ad')*50, 30),
                    'kw_ratio_frame': np.random.normal(35 - (group=='ad')*10, 5),
                    'total_fixations': np.random.randint(80, 200)
                })
        return pd.DataFrame(data)

    def test_compute_f_statistic(self, sample_data):
        """测试F统计量计算"""
        analyzer = SensitivityAnalyzer(sample_data)
        result = analyzer._compute_f_statistic('avg_fixation_duration')

        assert 'f_statistic' in result
        assert 'p_value' in result
        assert result['f_statistic'] > 0
        assert 0 <= result['p_value'] <= 1

    def test_compute_effect_size(self, sample_data):
        """测试效应量计算"""
        analyzer = SensitivityAnalyzer(sample_data)
        result = analyzer._compute_eta_squared('avg_fixation_duration')

        assert 0 <= result <= 1  # Eta-squared范围[0,1]

    def test_sensitivity_score_ranking(self, sample_data):
        """测试敏感度排序"""
        analyzer = SensitivityAnalyzer(sample_data)
        results = analyzer.compute_all_features()

        # 检查排序
        scores = results['sensitivity_score'].tolist()
        assert scores == sorted(scores, reverse=True)

        # 检查Top-4
        top4 = results.head(4)['feature_name'].tolist()
        assert len(top4) == 4

    def test_pairwise_tests_bonferroni(self, sample_data):
        """测试Bonferroni校正"""
        analyzer = SensitivityAnalyzer(sample_data)
        control = sample_data[sample_data['group']=='control']['avg_fixation_duration']
        mci = sample_data[sample_data['group']=='mci']['avg_fixation_duration']
        ad = sample_data[sample_data['group']=='ad']['avg_fixation_duration']

        result = analyzer._compute_pairwise(control, mci, ad)

        # 检查Bonferroni阈值: 0.05/3 = 0.0167
        for pair in result.values():
            if pair['significant']:
                assert pair['p_value'] < 0.0167

    def test_cv_computation(self, sample_data):
        """测试变异系数计算"""
        analyzer = SensitivityAnalyzer(sample_data)
        control = sample_data[sample_data['group']=='control']['avg_fixation_duration']
        mci = sample_data[sample_data['group']=='mci']['avg_fixation_duration']
        ad = sample_data[sample_data['group']=='ad']['avg_fixation_duration']

        result = analyzer._compute_cv(control, mci, ad)

        assert all(cv >= 0 for cv in result.values())
        assert 'avg_cv' in result
```

### 14.3 集成测试 (30%)

**测试文件**: `tests/test_module06/test_integration.py`

```python
class TestFeatureExtractionIntegration:
    """特征提取集成测试"""

    def test_strategy_a_end_to_end(self):
        """策略A端到端测试"""
        # Step 1: 调用敏感度分析
        response = requests.get('http://localhost:9090/api/m06/sensitivity/m04-features')
        assert response.status_code == 200
        sensitivity = response.json()
        assert 'top_4_features' in sensitivity['summary']

        # Step 2: 提取特征
        response = requests.post('http://localhost:9090/api/m06/extract/strategy-a', json={
            'subject_id': 'control_legacy_1',
            'group': 'control',
            'task_id': 'q1',
            'data_version': 'v1'
        })
        assert response.status_code == 200
        result = response.json()

        # Step 3: 验证特征向量
        assert result['dimensions'] == 10
        assert len(result['features']) == 10
        assert len(result['normalized']) == 10

    def test_module04_client_integration(self):
        """Module04客户端集成测试"""
        from src.modules.module06_feature_extraction.clients.module04_client import Module04Client

        client = Module04Client()
        features = client.get_features('control_legacy_1', 'control', 'q1', 'v1')

        assert 'avg_fixation_duration' in features
        assert isinstance(features['avg_fixation_duration'], (int, float))

    def test_module05_client_integration(self):
        """Module05客户端集成测试"""
        from src.modules.module06_feature_extraction.clients.module05_client import Module05Client

        client = Module05Client()
        features = client.get_rqa_features(
            'control_legacy_1', 'q1',
            params={'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}
        )

        assert 'rr-1d-x' in features
        assert 0 <= features['rr-1d-x'] <= 1  # RQA特征范围[0,1]
```

### 14.4 性能测试

**测试用例**: `tests/test_module06/test_performance.py`

```python
import time

class TestPerformance:
    """性能测试"""

    def test_single_sample_latency(self):
        """单样本延迟测试 (目标: < 1s)"""
        start = time.time()

        response = requests.post('http://localhost:9090/api/m06/extract/strategy-a', json={
            'subject_id': 'control_legacy_1',
            'group': 'control',
            'task_id': 'q1'
        })

        latency = time.time() - start

        assert response.status_code == 200
        assert latency < 1.0  # 必须 < 1秒

    def test_batch_throughput(self):
        """批量吞吐量测试 (目标: > 100样本/分钟)"""
        start = time.time()

        response = requests.post('http://localhost:9090/api/m06/extract/batch', json={
            'strategy': 'A',
            'groups': ['control'],
            'data_version': 'v1'
        })

        task_id = response.json()['task_id']

        # 等待完成
        while True:
            status = requests.get(f'http://localhost:9090/api/m06/extract/batch/status/{task_id}').json()
            if status['status'] == 'completed':
                break
            time.sleep(1)

        total_time = time.time() - start
        total_samples = status['total_samples']  # 100 (control组)

        throughput = total_samples / (total_time / 60)  # 样本/分钟

        assert throughput > 100  # 必须 > 100样本/分钟
```

---

## 15. 部署方案

### 15.1 环境配置

**生产环境要求**:
- Python 3.8+
- NumPy 1.20+, Pandas 1.3+, SciPy 1.7+
- Flask 2.0+
- 内存: 4GB+
- 磁盘: 10GB+ (存储特征文件)

**环境变量**:
```bash
# .env
MODULE06_DATA_ROOT=data/06_features
MODULE06_CACHE_ENABLED=true
MODULE06_CACHE_TTL=3600  # 1小时
MODULE04_API_URL=http://localhost:9090/api/m04
MODULE05_DATA_ROOT=data/05_rqa_analysis
```

### 15.2 部署步骤

**Step 1: 依赖安装**
```bash
cd new_project
pip install -r requirements.txt
```

**Step 2: 运行敏感度分析 (首次部署)**
```bash
# Module04敏感度分析
curl -X GET http://localhost:9090/api/m06/sensitivity/m04-features

# Module05敏感度分析 (如果未运行)
curl -X POST http://localhost:9090/api/m05/sensitivity/compute-scores

# 等待完成,查询状态
curl -X GET http://localhost:9090/api/m05/sensitivity/status/<task_id>
```

**Step 3: 批量提取特征**
```bash
# 策略A: 提取300样本
curl -X POST http://localhost:9090/api/m06/extract/batch \
  -H "Content-Type: application/json" \
  -d '{"strategy": "A", "groups": ["control", "mci", "ad"], "data_version": "v1"}'

# 策略B: 提取300样本
curl -X POST http://localhost:9090/api/m06/extract/batch \
  -H "Content-Type: application/json" \
  -d '{"strategy": "B", "groups": ["control", "mci", "ad"], "data_version": "v1"}'
```

**Step 4: 验证部署**
```bash
# 健康检查
curl http://localhost:9090/api/m06/health

# 提取单样本测试
curl -X POST http://localhost:9090/api/m06/extract/strategy-a \
  -H "Content-Type: application/json" \
  -d '{"subject_id": "control_legacy_1", "group": "control", "task_id": "q1"}'
```

### 15.3 监控指标

**关键指标**:
1. API响应时间 (P50, P95, P99)
2. 特征提取延迟 (单样本)
3. 批量处理吞吐量
4. 错误率
5. 缓存命中率

**监控工具**: Prometheus + Grafana

**告警阈值**:
- API P95延迟 > 500ms → 警告
- API P99延迟 > 1s → 严重
- 错误率 > 1% → 警告
- 错误率 > 5% → 严重

---

# 第六部分: 附录

## 16. 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| **维度灾难** | Curse of Dimensionality | 当特征维度远大于样本数时,导致过拟合和泛化能力下降 |
| **效应量** | Effect Size | 量化组间差异大小,不受样本量影响 (Eta-squared, Cohen's d) |
| **Bonferroni校正** | Bonferroni Correction | 多重比较校正方法,调整显著性阈值 α' = α / k |
| **变异系数** | Coefficient of Variation (CV) | 标准差与均值的比值,衡量相对变异程度 |
| **敏感度** | Sensitivity | 特征区分不同组别的能力 |
| **Z-score归一化** | Z-score Normalization | (x - μ) / σ,使特征均值为0,标准差为1 |
| **RQA** | Recurrence Quantification Analysis | 递归量化分析,非线性时间序列分析方法 |
| **IVT** | I-VT Algorithm | 基于速度阈值的注视/扫视分类算法 |
| **ROI** | Region of Interest | 兴趣区域,眼动研究中的关键区域 |

## 17. 参考文献

[1] Hughes, G. (1968). On the mean accuracy of statistical pattern recognizers. *IEEE Transactions on Information Theory*, 14(1), 55-63.

[2] Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.

[3] Salvucci, D. D., & Goldberg, J. H. (2000). Identifying fixations and saccades in eye-tracking protocols. *Proceedings of the Eye Tracking Research and Applications Symposium*, 71-78.

[4] Webber, C. L., & Zbilut, J. P. (2005). Recurrence quantification analysis of nonlinear dynamical systems. *Tutorials in Contemporary Nonlinear Methods for the Behavioral Sciences*, 26-94.

[5] Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning* (2nd ed.). Springer.

## 18. FAQ

### Q1: 为什么选择10维和69维,而不是其他维度?

**A**:
- **10维**: 样本比30:1,满足线性/非线性模型安全阈值(10:1和5:1)
- **69维**: 样本比4.3:1,接近非线性模型阈值,平衡性能与过拟合风险
- 两个策略都在**经验法则的安全范围**内

### Q2: 如果实际敏感度分析结果与文献推荐不同怎么办?

**A**: **以实际数据为准**!文献推荐仅作参考。Module06设计的核心优势就是**数据驱动**,避免人为主观性。

### Q3: 策略A使用单个参数还是跨参数聚合?

**A**: **推荐跨参数聚合** (策略2),原因:
- 不同参数组合可能在不同特征上表现最佳
- 跨参数选择Top-6特征,多样性更高
- 鲁棒性更强,不依赖单一参数组合

### Q4: 如果Module05敏感度分析耗时超过30分钟怎么办?

**A**:
1. **并行化**: 修改`compute_parameter_sensitivity_scores()`使用多进程
2. **采样**: 先分析部分参数组合(如m≤5),再扩展
3. **缓存**: 敏感度结果长期有效,只需计算一次

### Q5: 如何处理缺失值?

**A**:
- **Module04**: 使用`.dropna()`忽略缺失值
- **Module05**: RQA分析失败的样本用0填充(表示无有效轨迹)
- **Module06**: 提供可选Imputation策略(均值/中位数/KNN)

### Q6: 特征提取速度慢怎么优化?

**A**:
1. **缓存**: 敏感度评分、全局统计量缓存
2. **批量查询**: Module04/05 API支持批量查询
3. **异步处理**: 批量提取使用后台任务
4. **数据预加载**: 启动时预加载敏感度评分

---

**文档状态**: ✅ v2.0完成
**最后更新**: 2025-10-10
**审核人**: 待定
**版本控制**: Git - docs/MODULE06_COMPREHENSIVE_DESIGN.md

**变更记录**:
- v1.0 (2025-10-10): 初版,包含双策略设计
- v2.0 (2025-10-10): 重构为综合设计文档,新增系统架构、实施路线图、测试策略

---

## 📌 快速导航

**开发人员快速入口**:
- [系统架构](#10-系统架构设计) → 了解模块结构
- [API接口设计](#11-api接口设计) → 开发API
- [实施路线图](#13-实施路线图) → 查看任务分配

**数据科学家快速入口**:
- [特征空间分析](#6-特征空间维度灾难) → 理解维度灾难
- [敏感度分析设计](#8-敏感度分析设计) → 了解统计方法
- [特征选择算法](#9-特征选择算法) → 查看算法流程

**项目管理快速入口**:
- [执行摘要](#1-执行摘要) → 了解项目背景
- [实施路线图](#13-实施路线图) → 查看工期和里程碑
- [测试策略](#14-测试策略) → 了解质量保证

**使用者快速入口**:
- [双策略对比](#7-双策略特征提取方案) → 选择合适策略
- [API接口设计](#11-api接口设计) → 调用API
- [FAQ](#18-faq) → 常见问题
