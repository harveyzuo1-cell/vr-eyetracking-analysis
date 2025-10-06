# VR眼动数据预处理技术规范

## 文档信息
- **版本**: 2.0
- **日期**: 2025-10-06
- **状态**: 基于最新学术文献修订

---

## 目录
1. [眼动数据特性分析](#1-眼动数据特性分析)
2. [IVT算法详解](#2-ivt算法详解)
3. [当前预处理方案问题分析](#3-当前预处理方案问题分析)
4. [新预处理方案设计](#4-新预处理方案设计)
5. [风险评估与缓解策略](#5-风险评估与缓解策略)
6. [实施建议](#6-实施建议)

---

## 1. 眼动数据特性分析

### 1.1 VR眼动数据的独特性

VR眼动追踪与传统屏幕眼动追踪存在本质差异:

| 特征 | 传统2D屏幕 | VR环境 |
|------|-----------|--------|
| **坐标系统** | 2D屏幕坐标(x, y) | 3D世界坐标 + 注视方向向量 |
| **头部运动** | 固定/有限 | 完全自由(6-DOF) |
| **采样率** | 60-1000Hz | 通常60-120Hz |
| **数据质量** | 相对稳定 | 受头显移动影响 |
| **眨眼模式** | 清晰可辨 | 可能被头部运动混淆 |

### 1.2 数据缺失的主要来源

**文献依据**: Uncovering and Addressing Blink-Related Challenges in Using Eye Tracking for Interactive Systems (CHI 2024)

1. **生理性眨眼**
   - 频率: 约15-20次/分钟
   - 持续时间: 100-400ms
   - 特征: 数据丢失前后有瞳孔面积急剧变化

2. **追踪丢失**
   - 原因: 头显移位、强光反射、极端注视角度
   - 特征: 持续时间不定,无规律模式

3. **系统噪声**
   - 来源: 传感器噪声、校准误差
   - 特征: 高频随机波动(>75Hz)

### 1.3 关键观察

**⚠️ 重要发现**:
- **VR数据集通常会主动避免眨眼和错误检测** (VR Eye Tracking Survey 2024)
- **眨眼期间眼球位置变化不可预测,不应插值注视位置** (MNE Preprocessing Documentation)
- **只有瞳孔直径可以安全插值,注视坐标不应插值** (Best Practices 2024)

---

## 2. IVT算法详解

### 2.1 算法原理

**IVT (Identification by Velocity Threshold)** 是基于速度阈值的注视点检测算法。

#### 核心思想
根据眼动速度将数据分类为:
- **注视(Fixation)**: 速度 < 阈值 → 信息提取阶段
- **扫视(Saccade)**: 速度 ≥ 阈值 → 快速眼动

### 2.2 数学公式

#### 2.2.1 点对点速度计算

对于连续两个采样点 $P_i(x_i, y_i, t_i)$ 和 $P_{i+1}(x_{i+1}, y_{i+1}, t_{i+1})$:

**欧氏距离(像素)**:
```
d_pixel = √[(x_{i+1} - x_i)² + (y_{i+1} - y_i)²]
```

**转换为视角(度)**:
```
d_degree = 2 × arctan(d_pixel / (2 × viewing_distance))
```

对于VR,使用角度直接计算:
```
angular_distance = arccos(cos(θ₁)cos(θ₂)cos(φ₁-φ₂) + sin(θ₁)sin(θ₂))
```
其中 $(θ, φ)$ 是球面坐标

**速度(度/秒)**:
```
velocity = angular_distance / (t_{i+1} - t_i)
```

#### 2.2.2 注视/扫视分类

```python
if velocity < threshold:
    event_type = "fixation"
else:
    event_type = "saccade"
```

### 2.3 标准参数(基于Tobii I-VT Filter)

| 参数 | 推荐值 | 范围 | 说明 |
|------|--------|------|------|
| **速度阈值** | 30-35 °/s | 20-100 °/s | 核心参数,区分注视/扫视 |
| **最小注视时长** | 60-100 ms | 40-200 ms | 过滤微扫视 |
| **合并距离阈值** | 0.5-1.0° | 0.3-2.0° | 合并相邻注视点 |
| **合并时间窗口** | 75 ms | 50-100 ms | 时间上的注视合并 |
| **最小扫视时长** | 10-20 ms | 5-50 ms | 过滤噪声 |

### 2.4 预处理中的噪声降低(可选)

**文献依据**: The Tobii I-VT Fixation Filter

IVT可选噪声降低方法:

#### 方法1: 移动平均(Moving Average)
```
x_smooth[i] = (1/w) × Σ(x[i-k] to x[i+k])
```
- 窗口大小 `w = 3-5` 个样本
- 优点: 简单快速
- 缺点: 延迟,边缘效应

#### 方法2: 中值滤波(Median Filter)
```
x_smooth[i] = median(x[i-k], ..., x[i], ..., x[i+k])
```
- 窗口大小 `w = 3-5` 个样本
- 优点: 保留边缘,抗离群值
- 缺点: 计算稍慢

**⚠️ 重要**: IVT本身具有抗噪能力,**不强制要求预滤波**

---

## 3. 当前预处理方案问题分析

### 3.1 当前配置审查

```python
# 现有默认配置
config = {
    'cleaning_config': {
        'missing_method': 'interpolate',      # ❌ 问题!
        'outlier_method': '3sigma',
        'outlier_threshold': 3.0,
        'outlier_action': 'interpolate',      # ❌ 问题!
        'clip_range': True,
        'x_range': [0, 1],
        'y_range': [0, 1],
        'resample': False,
        'target_rate': 60
    },
    'smoothing_config': {
        'method': 'gaussian',                 # ⚠️ 存疑!
        'window_size': 5,
        'sigma': 1.5,
        'smooth_x': True,                     # ⚠️ 存疑!
        'smooth_y': True                      # ⚠️ 存疑!
    }
}
```

### 3.2 问题详解

#### 问题1: 注视位置插值 ❌

**现状**: 对缺失的注视坐标进行线性插值

**为什么错误**:
- 眨眼时眼球位置不可预测(文献明确指出)
- 线性插值会创造"虚假注视路径"
- 破坏后续注视检测算法的准确性

**影响**:
```
真实情况: [fix1] → [眨眼,位置未知] → [fix2在不同位置]
错误插值: [fix1] → [人工路径] → [fix2]  # 创造了不存在的扫视!
```

#### 问题2: 异常值插值 ❌

**现状**: 将异常值替换为插值

**为什么错误**:
- 真实的快速扫视可能被误判为异常值
- 插值会"平滑掉"真实的眼动事件
- 扭曲速度曲线,影响IVT分类

#### 问题3: 平滑滤波的争议 ⚠️

**现状**: 对x,y坐标应用高斯滤波(sigma=1.5, window=5)

**文献观点对比**:

✅ **支持平滑的观点**:
- Tobii I-VT Filter: 提供可选的噪声降低(移动平均/中值)
- 原因: 降低高频噪声(>75Hz)可提高注视检测准确性

❌ **反对平滑的观点**:
- Filtering Eye-Tracking Data (2024): 低通滤波会显著扭曲扫视速度
- 建议: 收集原始数据,必要时使用FIR滤波而非高斯滤波
- Savitzky-Golay比较研究: 大窗口会拉伸信号,产生振铃效应

**关键问题**:
- 当前高斯滤波(sigma=1.5, window=5) **可能过度平滑**
- 没有考虑采样率和信号频率特性
- 应该**在IVT检测前**而非数据清洗阶段进行(如果需要)

---

## 4. 新预处理方案设计

### 4.1 设计原则

1. **最小干预原则**: 尽量保留原始眼动特征
2. **分阶段处理**: 区分"数据质量控制"和"特征提取准备"
3. **可追溯性**: 记录所有处理步骤,保留原始数据
4. **特定场景优化**: 针对VR和认知评估任务

### 4.2 新方案流程图

```
原始数据
    ↓
[阶段1: 数据质量评估]
    ├─ 采样率检查
    ├─ 有效数据率计算
    └─ 眨眼检测与标记
    ↓
[阶段2: 数据清理(保守)]
    ├─ 范围裁剪(硬件限制)
    ├─ 明显错误值移除(validity=0)
    └─ 眨眼片段标记(不插值!)
    ↓
[阶段3: 可选噪声降低]
    ├─ IF: 数据噪声>阈值
    │   └─ 中值滤波(window=3)
    └─ ELSE: 跳过
    ↓
[阶段4: IVT事件检测]
    ├─ 速度计算
    ├─ 注视/扫视分类
    └─ 注视点提取
    ↓
处理后的事件数据
```

### 4.3 详细参数配置

#### 4.3.1 阶段1: 质量评估

```python
quality_assessment_config = {
    # 采样率检查
    'expected_sampling_rate': 60,  # Hz
    'sampling_rate_tolerance': 10,  # ±10 Hz

    # 数据完整性
    'min_valid_data_rate': 0.75,  # 至少75%有效数据

    # 眨眼检测参数
    'blink_detection': {
        'method': 'pupil_based',  # 基于瞳孔面积变化
        'pupil_threshold': 0.5,   # 瞳孔面积变化阈值
        'min_blink_duration': 50,  # ms
        'max_blink_duration': 500, # ms
        'pre_blink_buffer': 50,    # 眨眼前保留ms
        'post_blink_buffer': 50    # 眨眼后保留ms
    }
}
```

**眨眼检测公式**:
```python
# 瞳孔面积变化率
pupil_change_rate = |pupil[i+1] - pupil[i]| / pupil[i]

# 检测眨眼开始
if pupil_change_rate > threshold and pupil[i+1] < pupil[i]:
    blink_start = i

# 检测眨眼结束
if pupil[i] == 0 and pupil[i+1] > 0:
    blink_end = i + 1
```

#### 4.3.2 阶段2: 数据清理

```python
cleaning_config = {
    # 范围裁剪(基于硬件物理限制)
    'clip_range': True,
    'x_range': [0, 1],  # 或实际FOV
    'y_range': [0, 1],

    # 明显错误值处理
    'remove_invalid_samples': True,  # validity字段=0的样本

    # 缺失值处理: 标记而非插值!
    'missing_value_strategy': 'mark_only',  # 'mark_only' | 'remove'

    # 眨眼处理: 标记而非插值!
    'blink_strategy': 'mark_segment',  # 标记整个眨眼片段

    # 极端异常值(非眼动事件)
    'extreme_outlier_removal': {
        'enabled': True,
        'method': 'velocity_based',
        'max_velocity_threshold': 1000,  # °/s (生理极限~900°/s)
        'action': 'mark'  # 标记而非删除或插值
    }
}
```

**重要**: 所有"异常"数据仅标记,不修改原始值!

#### 4.3.3 阶段3: 可选噪声降低

```python
noise_reduction_config = {
    'enabled': False,  # 默认关闭!

    # 自动启用条件
    'auto_enable_if': {
        'noise_level': 0.1,  # 位置噪声 > 0.1°
        'or': {
            'sampling_jitter': 5  # 采样抖动 > 5ms
        }
    },

    # 滤波方法
    'method': 'median',  # median | savgol | none

    # 中值滤波参数(推荐)
    'median_filter': {
        'window_size': 3,  # 小窗口保留瞬态
        'apply_to': ['x', 'y'],  # 不处理瞳孔!
    },

    # Savgol滤波参数(备选)
    'savgol_filter': {
        'window_size': 5,
        'polyorder': 2,
        'apply_to': ['x', 'y']
    },

    # 绝对禁止
    'gaussian_filter': {
        'enabled': False,  # ❌ 不使用高斯滤波!
        'reason': '会严重扭曲扫视速度特征'
    }
}
```

**滤波公式**:

**中值滤波**:
```
x_filtered[i] = median(x[i-1], x[i], x[i+1])
```

**Savitzky-Golay**:
```
x_filtered[i] = Σ(c_k × x[i+k])  # k from -m to m
# c_k为预计算系数,取决于window_size和polyorder
```

#### 4.3.4 阶段4: IVT参数

```python
ivt_config = {
    # 核心速度阈值
    'velocity_threshold': 30,  # °/s (Tobii标准: 30-35)

    # 速度计算方法
    'velocity_calculation': {
        'method': 'point_to_point',  # 逐点计算
        'use_degrees': True,         # 使用角度而非像素
        'sampling_aware': True       # 考虑实际采样间隔
    },

    # 注视过滤
    'fixation_filter': {
        'min_duration': 60,      # ms (Tobii: 60-100)
        'merge_distance': 0.5,   # ° (Tobii: 0.5-1.0)
        'merge_time_window': 75  # ms (Tobii: 75)
    },

    # 扫视过滤
    'saccade_filter': {
        'min_duration': 10,      # ms (Tobii: 10-20)
        'min_amplitude': 0.5     # ° 最小扫视幅度
    },

    # 眨眼处理
    'handle_blinks': {
        'action': 'create_event',  # 标记为单独事件类型
        'merge_adjacent_fixations': True  # 眨眼前后的注视可合并
    }
}
```

**速度计算公式(考虑采样率)**:
```python
def calculate_velocity(p1, p2, actual_dt):
    """
    p1, p2: (x, y, timestamp)
    actual_dt: 实际时间间隔(s)
    """
    # 角距离
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angular_distance = np.sqrt(dx**2 + dy**2)  # 假设已是角度

    # 速度
    velocity = angular_distance / actual_dt  # °/s

    return velocity
```

### 4.4 配置对比总结

| 项目 | 旧方案 | 新方案 | 变更理由 |
|------|--------|--------|----------|
| **缺失值处理** | 线性插值 | 仅标记 | 避免创造虚假数据 |
| **异常值处理** | 插值替换 | 标记保留 | 保留真实扫视事件 |
| **平滑滤波** | 强制高斯(σ=1.5) | 条件中值(w=3) | 减少速度扭曲 |
| **眨眼处理** | 插值 | 独立事件 | 符合生理特性 |
| **数据完整性** | 无检查 | 质量评分 | 可追溯性 |

---

## 5. 风险评估与缓解策略

### 5.1 主要风险

#### 风险1: 数据可用性降低 🔴 高风险

**问题**: 不插值缺失值可能导致可分析数据减少

**量化影响**:
- 假设眨眼率: 15次/分钟,每次200ms
- 测试时长: 5分钟
- 数据丢失: 15 × 5 × 0.2 = 15秒 = 5%

**缓解措施**:
1. **事前**: 改进实验设计
   - 任务说明中提醒减少眨眼
   - 任务间隔允许自由眨眼
   - VR场景优化减少视疲劳

2. **事中**: 质量监控
   - 实时显示有效数据率
   - 低于阈值时提示重新校准

3. **事后**: 智能分析
   - 分段分析(跳过眨眼段)
   - 使用注视事件而非原始样本
   - 统计时标注数据质量

#### 风险2: 参数敏感性 🟡 中风险

**问题**: IVT速度阈值30°/s可能不适合所有场景

**场景差异**:
- 阅读任务: 需要更低阈值(20-25°/s)
- 探索任务: 可用更高阈值(35-40°/s)
- 老年群体: 扫视速度变慢,可能需调低

**缓解措施**:
1. **自适应阈值**:
```python
def adaptive_threshold(age, task_type):
    base_threshold = 30  # °/s

    # 年龄调整
    if age > 65:
        base_threshold *= 0.85  # -15%

    # 任务调整
    if task_type == 'reading':
        base_threshold *= 0.8
    elif task_type == 'exploration':
        base_threshold *= 1.15

    return base_threshold
```

2. **多阈值验证**:
   - 并行运行多个阈值(25, 30, 35°/s)
   - 对比结果一致性
   - 选择最稳定参数

#### 风险3: 计算复杂度增加 🟢 低风险

**问题**: 不插值导致后续分析需处理不规则时间序列

**影响评估**:
- RQA分析需要等间隔时间序列
- 可能需要额外的时间对齐步骤

**缓解措施**:
1. **事件级分析**:
   - 直接使用IVT检测的注视事件
   - 注视序列本身就是离散的,不需要等间隔

2. **智能重采样**:
   - 仅在必要时重采样(如RQA)
   - 基于注视事件而非原始样本
   ```python
   # 伪代码
   fixation_sequence = extract_fixations(raw_data, ivt_config)
   regular_series = resample_fixations(fixation_sequence, target_rate=10)  # 10 fixations/s
   ```

#### 风险4: 向后兼容性 🟡 中风险

**问题**: 新方案可能导致与现有分析结果不一致

**影响**:
- 已发表结果基于旧处理方式
- 无法直接对比新旧数据

**缓解措施**:
1. **过渡期策略**:
   - 同时提供新旧两种处理模式
   - 对比分析报告差异

2. **版本管理**:
   ```python
   preprocessing_version = "v2.0"
   config['preprocessing_version'] = preprocessing_version
   # 保存到元数据,确保可追溯
   ```

3. **验证研究**:
   - 选取代表性样本
   - 新旧方法对比
   - 量化差异并评估影响

### 5.2 风险优先级矩阵

| 风险 | 可能性 | 影响 | 优先级 | 行动 |
|------|--------|------|--------|------|
| 数据可用性降低 | 中 | 高 | 🔴 高 | 立即实施缓解措施 |
| 参数敏感性 | 高 | 中 | 🟡 中 | 建立自适应机制 |
| 计算复杂度 | 低 | 低 | 🟢 低 | 监控即可 |
| 向后兼容性 | 高 | 中 | 🟡 中 | 建立过渡方案 |

---

## 6. 实施建议

### 6.1 分阶段实施路线图

#### 第一阶段: 验证研究(2周)
- [ ] 选取10个代表性样本(各组平衡)
- [ ] 实施新旧方案对比
- [ ] 量化关键指标差异:
  - 注视点数量
  - 扫视幅度分布
  - 数据可用率
- [ ] 评审会议决定是否继续

#### 第二阶段: 并行运行(4周)
- [ ] 实现配置切换功能
- [ ] 新数据同时生成新旧两种结果
- [ ] 建立质量监控Dashboard
- [ ] 收集用户反馈

#### 第三阶段: 全面切换(2周)
- [ ] 更新默认配置为新方案
- [ ] 保留旧方案作为可选项
- [ ] 更新文档和培训材料
- [ ] 建立问题反馈机制

### 6.2 关键成功因素

1. **文档完备**:
   - 每个参数的含义和影响
   - 决策过程和文献依据
   - 故障排查指南

2. **可解释性**:
   - 可视化对比工具
   - 处理日志详细记录
   - 质量报告自动生成

3. **灵活性**:
   - 参数可调节
   - 方案可切换
   - 扩展性预留

### 6.3 推荐配置模板

```python
# 保守模式(推荐用于新研究)
CONSERVATIVE_CONFIG = {
    'quality_assessment': quality_assessment_config,
    'cleaning': {
        **cleaning_config,
        'missing_value_strategy': 'mark_only',
        'blink_strategy': 'mark_segment'
    },
    'noise_reduction': {
        'enabled': False  # 默认关闭
    },
    'ivt': ivt_config
}

# 兼容模式(用于对比研究)
COMPATIBILITY_CONFIG = {
    # 旧配置,保持向后兼容
    'cleaning': {
        'missing_method': 'interpolate',
        'outlier_method': '3sigma',
        'outlier_action': 'interpolate'
    },
    'smoothing': {
        'method': 'gaussian',
        'window_size': 5,
        'sigma': 1.5
    }
}

# 高质量模式(噪声数据)
HIGH_QUALITY_CONFIG = {
    **CONSERVATIVE_CONFIG,
    'noise_reduction': {
        'enabled': True,
        'method': 'median',
        'window_size': 3
    }
}
```

---

## 7. 参考文献

1. **Andersson, R., Larsson, L., Holmqvist, K., et al.** (2017). "One algorithm to rule them all? An evaluation and discussion of ten eye movement event-detection algorithms." *Behavior Research Methods*, 49(2), 616-637.

2. **Startsev, M., Zemblys, R.** (2023). "Filtering Eye-Tracking Data From an EyeLink 1000: Comparing Heuristic, Savitzky-Golay, IIR and FIR Digital Filters." *arXiv:2303.02134*

3. **Tobii Technology** (2012). "The Tobii I-VT Fixation Filter Algorithm Description."

4. **Hessels, R. S., Niehorster, D. C., et al.** (2024). "Uncovering and Addressing Blink-Related Challenges in Using Eye Tracking for Interactive Systems." *CHI Conference on Human Factors in Computing Systems*

5. **Krassanakis, V., Filippakopoulou, V., Nakos, B.** (2014). "EyeMMV toolbox: An eye movement post-analysis tool based on a two-step spatial dispersion threshold for fixation identification." *Journal of Eye Movement Research*, 7(1).

6. **Salvucci, D. D., & Goldberg, J. H.** (2000). "Identifying fixations and saccades in eye-tracking protocols." *Proceedings of the symposium on Eye tracking research & applications*, 71-78.

7. **Clay, V., König, P., König, S.** (2019). "Eye Tracking in Virtual Reality." *Journal of Eye Movement Research*, 12(1).

---

## 附录A: 快速决策树

```
开始预处理
    │
    ├─ 数据采样率 < 60Hz?
    │   ├─ 是 → ⚠️ 警告: 可能影响注视检测
    │   └─ 否 → 继续
    │
    ├─ 有效数据率 < 75%?
    │   ├─ 是 → ⚠️ 建议重新采集
    │   └─ 否 → 继续
    │
    ├─ 数据噪声 > 0.1°?
    │   ├─ 是 → 启用中值滤波(w=3)
    │   └─ 否 → 跳过滤波
    │
    ├─ 任务类型?
    │   ├─ 阅读 → IVT阈值 = 25°/s
    │   ├─ 探索 → IVT阈值 = 35°/s
    │   └─ 默认 → IVT阈值 = 30°/s
    │
    └─ 执行IVT检测
```

---

## 附录B: 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 注视 | Fixation | 眼球相对静止,信息提取阶段(典型50-600ms) |
| 扫视 | Saccade | 快速眼动,视觉抑制阶段(典型20-200ms,速度可达900°/s) |
| IVT | I-VT | Identification by Velocity Threshold,基于速度阈值的事件检测 |
| 视角 | Visual Degree | 角度单位,用于测量视网膜上的角距离 |
| 采样率 | Sampling Rate | 每秒采集数据点数(Hz) |
| 插值 | Interpolation | 根据已知数据点估算中间值的方法 |
| 低通滤波 | Low-pass Filter | 保留低频信号,去除高频噪声的滤波器 |

---

**文档结束**

*如有疑问或需要进一步说明,请联系技术团队*
