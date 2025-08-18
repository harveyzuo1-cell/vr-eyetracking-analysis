# 眼动数据归一化数据库设计文档

## 📋 设计原则

本设计严格遵循数据库三大范式，确保数据的一致性、减少冗余、避免异常。

### 🔧 三大范式遵循

#### 第一范式（1NF）
- ✅ 每个表格的每个字段都是原子性的，不可再分
- ✅ 每个表格都有主键
- ✅ 字段值不重复

#### 第二范式（2NF）  
- ✅ 满足1NF
- ✅ 非主键字段完全函数依赖于主键
- ✅ 消除部分函数依赖

#### 第三范式（3NF）
- ✅ 满足2NF
- ✅ 非主键字段不传递依赖于主键
- ✅ 消除传递函数依赖

---

## 📊 数据库表结构设计

### 1. 受试者基本信息表 (subjects)

**表名**: `subjects.csv`  
**主键**: `subject_id`

| 字段名 | 数据类型 | 描述 | 示例 | 约束 |
|--------|----------|------|------|------|
| subject_id | String | 受试者唯一标识 | ad01, m01, n01 | 主键，非空 |
| group_type | String | 实验组类型 | ad, mci, control | 非空 |
| group_number | Integer | 组内编号 | 1, 2, 3... | 非空 |
| original_id | String | 原始ID | ad01, M01, n01 | 非空 |

### 2. 任务信息表 (tasks)

**表名**: `tasks.csv`  
**主键**: `task_id`

| 字段名 | 数据类型 | 描述 | 示例 | 约束 |
|--------|----------|------|------|------|
| task_id | String | 任务唯一标识 | Q1, Q2, Q3, Q4, Q5 | 主键，非空 |
| task_name | String | 任务名称 | 第一题, 第二题... | 非空 |
| max_duration_seconds | Float | 最大时长(秒) | 180.0 | 非空 |
| description | String | 任务描述 | VR-MMSE任务1 | 可空 |

### 3. MMSE评分表 (mmse_scores)

**表名**: `mmse_scores.csv`  
**主键**: `subject_id`  
**外键**: `subject_id` → `subjects.subject_id`

| 字段名 | 数据类型 | 描述 | 取值范围 | 约束 |
|--------|----------|------|----------|------|
| subject_id | String | 受试者ID | ad01, m01, n01 | 主键，外键 |
| vr_mmse_score | Integer | VR-MMSE总分 | 0-21 | 非空 |
| standard_mmse_score | Float | 标准MMSE分数 | 0-30 | 计算字段 |
| orientation_time | Integer | 时间定向 | 0-5 | 非空 |
| orientation_place | Integer | 地点定向 | 0-5 | 非空 |
| immediate_memory | Integer | 即刻记忆 | 0-3 | 非空 |
| attention_calculation | Integer | 注意力计算 | 0-5 | 非空 |
| delayed_recall | Integer | 延迟回忆 | 0-3 | 非空 |

### 4. 游戏会话表 (game_sessions)

**表名**: `game_sessions.csv`  
**主键**: `session_id`  
**外键**: `subject_id` → `subjects.subject_id`, `task_id` → `tasks.task_id`

| 字段名 | 数据类型 | 描述 | 示例 | 约束 |
|--------|----------|------|------|------|
| session_id | String | 会话唯一标识 | ad01q1, m01q1, n01q1 | 主键，非空 |
| subject_id | String | 受试者ID | ad01, m01, n01 | 外键，非空 |
| task_id | String | 任务ID | Q1, Q2, Q3, Q4, Q5 | 外键，非空 |
| game_duration_seconds | Float | 实际游戏时长(秒) | 24.2, 35.8, 90.2 | 非空 |
| game_duration_normalized | Float | 归一化游戏时长 | 0.0-1.0 | 非空 |
| data_points_count | Integer | 数据点总数 | 446, 523, 892 | 非空 |
| file_path | String | 原始数据文件路径 | data/ad_calibrated/... | 非空 |

### 5. ROI特征表 (roi_features)

**表名**: `roi_features.csv`  
**主键**: `session_id` + `roi_type`  
**外键**: `session_id` → `game_sessions.session_id`

| 字段名 | 数据类型 | 描述 | 示例 | 约束 |
|--------|----------|------|------|------|
| session_id | String | 会话ID | ad01q1, m01q1 | 主键组合，外键 |
| roi_type | String | ROI类型 | KW, INST, BG | 主键组合，非空 |
| total_fixation_time_seconds | Float | ROI总注视时间(秒) | 2.569, 4.350 | 非空，>=0 |
| total_fixation_time_normalized | Float | 归一化总注视时间 | 0.0-1.0 | 非空 |
| fixation_time_percentage | Float | 注视时间占比 | 0.0-1.0 | 非空 |
| fixation_time_percentage_normalized | Float | 归一化占比 | 0.0-1.0 | 非空 |
| enter_count | Integer | 进入次数 | 4, 1, 7 | 非空，>=0 |
| regression_count | Integer | 回视次数 | 3, 0, 6 | 非空，>=0 |

### 6. RQA特征表 (rqa_features)

**表名**: `rqa_features.csv`  
**主键**: `session_id`  
**外键**: `session_id` → `game_sessions.session_id`

| 字段名 | 数据类型 | 描述 | 取值范围 | 约束 |
|--------|----------|------|----------|------|
| session_id | String | 会话ID | ad01q1, m01q1 | 主键，外键 |
| rr_2d_xy | Float | 2D递归率原始值 | 0.0096-0.2422 | 非空 |
| rr_2d_xy_normalized | Float | 2D递归率归一化 | 0.0-1.0 | 非空 |
| rr_1d_x | Float | 1D递归率原始值 | 0.0298-0.2870 | 非空 |
| rr_1d_x_normalized | Float | 1D递归率归一化 | 0.0-1.0 | 非空 |
| det_2d_xy | Float | 2D确定性原始值 | 0.5808-0.9655 | 非空 |
| det_2d_xy_normalized | Float | 2D确定性归一化 | 0.0-1.0 | 非空 |
| det_1d_x | Float | 1D确定性原始值 | 0.5319-0.9556 | 非空 |
| det_1d_x_normalized | Float | 1D确定性归一化 | 0.0-1.0 | 非空 |
| ent_2d_xy | Float | 2D熵原始值 | 0.7219-3.8210 | 非空 |
| ent_2d_xy_normalized | Float | 2D熵归一化 | 0.0-1.0 | 非空 |
| ent_1d_x | Float | 1D熵原始值 | 0.8879-3.5615 | 非空 |
| ent_1d_x_normalized | Float | 1D熵归一化 | 0.0-1.0 | 非空 |

### 7. 归一化特征汇总表 (normalized_features_summary)

**表名**: `normalized_features_summary.csv`  
**主键**: `session_id`  
**外键**: `session_id` → `game_sessions.session_id`

| 字段名 | 数据类型 | 描述 | 取值范围 | 约束 |
|--------|----------|------|----------|------|
| session_id | String | 会话ID | ad01q1, m01q1 | 主键，外键 |
| subject_id | String | 受试者ID | ad01, m01, n01 | 非空 |
| task_id | String | 任务ID | Q1, Q2, Q3, Q4, Q5 | 非空 |
| group_type | String | 实验组 | ad, mci, control | 非空 |
| game_duration_norm | Float | 归一化游戏时长 | 0.0-1.0 | 非空 |
| roi_kw_time_norm | Float | 归一化KW ROI时间 | 0.0-1.0 | 非空 |
| roi_inst_time_norm | Float | 归一化INST ROI时间 | 0.0-1.0 | 非空 |
| roi_bg_time_norm | Float | 归一化BG ROI时间 | 0.0-1.0 | 非空 |
| roi_kw_percentage_norm | Float | 归一化KW时间占比 | 0.0-1.0 | 非空 |
| roi_inst_percentage_norm | Float | 归一化INST时间占比 | 0.0-1.0 | 非空 |
| roi_bg_percentage_norm | Float | 归一化BG时间占比 | 0.0-1.0 | 非空 |
| rr_2d_norm | Float | 归一化2D递归率 | 0.0-1.0 | 非空 |
| rr_1d_norm | Float | 归一化1D递归率 | 0.0-1.0 | 非空 |
| det_2d_norm | Float | 归一化2D确定性 | 0.0-1.0 | 非空 |
| det_1d_norm | Float | 归一化1D确定性 | 0.0-1.0 | 非空 |
| ent_2d_norm | Float | 归一化2D熵 | 0.0-1.0 | 非空 |
| ent_1d_norm | Float | 归一化1D熵 | 0.0-1.0 | 非空 |

---

## 🔢 归一化公式

### 1. 游戏总时长归一化

**公式**: 
```
game_duration_normalized = min(game_duration_seconds / 180.0, 1.0)
```

**说明**: 最大时长3分钟(180秒)，超过则截断为1.0

### 2. ROI注视时间归一化

**公式**:
```
total_fixation_time_normalized = min(total_fixation_time_seconds / 67.23, 1.0)
```

**说明**: 使用实际最大值67.23秒作为上限，超过则截断为1.0

### 3. ROI时间占比归一化

**公式**:
```
fixation_time_percentage = total_fixation_time_seconds / game_duration_seconds
fixation_time_percentage_normalized = fixation_time_percentage  // 已经是0-1范围
```

**说明**: 占比本身就在0-1范围内，无需额外归一化

### 4. RQA指标归一化

**递归率 (RR) 归一化**:
```
rr_2d_xy_normalized = (rr_2d_xy - 0.0096) / (0.2422 - 0.0096)
rr_1d_x_normalized = (rr_1d_x - 0.0298) / (0.2870 - 0.0298)
```

**确定性 (DET) 归一化**:
```
det_2d_xy_normalized = (det_2d_xy - 0.5808) / (0.9655 - 0.5808)
det_1d_x_normalized = (det_1d_x - 0.5319) / (0.9556 - 0.5319)
```

**熵 (ENT) 归一化**:
```
ent_2d_xy_normalized = (ent_2d_xy - 0.7219) / (3.8210 - 0.7219)
ent_1d_x_normalized = (ent_1d_x - 0.8879) / (3.5615 - 0.8879)
```

---

## 🔗 表关系图

```
subjects (1) ----< game_sessions (N)
    |                    |
    |                    |----< roi_features (N)
    |                    |
    |                    |----< rqa_features (1)
    |                    |
    |                    |----< normalized_features_summary (1)
    |
    |----< mmse_scores (1)

tasks (1) ----< game_sessions (N)
```

### 关系说明

1. **subjects → game_sessions**: 一对多 (一个受试者多个会话)
2. **tasks → game_sessions**: 一对多 (一个任务多个会话)
3. **subjects → mmse_scores**: 一对一 (一个受试者一个MMSE分数)
4. **game_sessions → roi_features**: 一对多 (一个会话多个ROI特征)
5. **game_sessions → rqa_features**: 一对一 (一个会话一个RQA特征组)
6. **game_sessions → normalized_features_summary**: 一对一 (一个会话一个汇总)

---

## 📝 数据一致性约束

### 完整性约束

1. **实体完整性**: 每个表都有主键，主键不能为空
2. **参照完整性**: 外键必须引用存在的主键值
3. **域完整性**: 字段值必须符合定义的数据类型和取值范围

### 业务规则约束

1. **游戏时长**: `game_duration_seconds >= 0`
2. **归一化值**: 所有`*_normalized`字段值在[0,1]范围内
3. **ROI时间**: `total_fixation_time_seconds >= 0`
4. **占比逻辑**: `fixation_time_percentage <= 1.0`
5. **会话唯一性**: `session_id`格式为`{subject_id}q{task_number}`

### 数据质量检查

```sql
-- 检查归一化值范围
SELECT * FROM normalized_features_summary 
WHERE game_duration_norm < 0 OR game_duration_norm > 1;

-- 检查ROI时间逻辑
SELECT session_id, roi_type, fixation_time_percentage 
FROM roi_features 
WHERE fixation_time_percentage > 1.0;

-- 检查会话完整性
SELECT g.session_id 
FROM game_sessions g
LEFT JOIN rqa_features r ON g.session_id = r.session_id
WHERE r.session_id IS NULL;
```

---

## 🚀 实现策略

### 数据迁移流程

1. **提取基础数据**: 从MMSE文件和校准数据中提取受试者信息
2. **计算会话特征**: 分析每个会话的游戏时长和数据点数
3. **聚合ROI特征**: 从事件分析结果中聚合ROI相关特征
4. **整合RQA特征**: 从RQA结果中提取并归一化指标
5. **生成汇总表**: 将所有归一化特征整合到汇总表中

### 数据处理脚本

- `extract_subjects.py`: 提取受试者基础信息
- `calculate_game_sessions.py`: 计算游戏会话特征
- `aggregate_roi_features.py`: 聚合ROI特征
- `normalize_rqa_features.py`: 归一化RQA特征
- `generate_summary.py`: 生成最终汇总表

---

## 📊 使用示例

### 按任务分组分析

```python
# 按任务分组分析归一化特征
summary_df = pd.read_csv('normalized_features_summary.csv')
task_analysis = summary_df.groupby('task_id').agg({
    'game_duration_norm': ['mean', 'std'],
    'rr_2d_norm': ['mean', 'std'],
    'det_2d_norm': ['mean', 'std']
}).round(4)
```

### 组间差异分析

```python
# 比较不同实验组的特征差异
group_comparison = summary_df.groupby('group_type').agg({
    'roi_kw_time_norm': 'mean',
    'roi_inst_time_norm': 'mean', 
    'rr_2d_norm': 'mean',
    'det_2d_norm': 'mean'
}).round(4)
```

---

## ⚠️ 注意事项

### 数据处理注意点

1. **缺失值处理**: ROI特征可能存在缺失值，需要合理填充或标记
2. **异常值检测**: 归一化前需要检测和处理异常值
3. **精度保持**: 浮点数计算需要保持足够精度
4. **版本控制**: 归一化参数变更需要版本化管理

### 性能考虑

1. **索引优化**: 在主键和外键上建立索引
2. **批量处理**: 大量数据处理时使用批量操作
3. **内存管理**: 处理大文件时注意内存使用
4. **并行计算**: RQA特征计算可以并行化

---

**文档版本**: 1.0  
**创建日期**: 2025年7月31日  
**更新日期**: 2025年7月31日  
**设计者**: AI Assistant