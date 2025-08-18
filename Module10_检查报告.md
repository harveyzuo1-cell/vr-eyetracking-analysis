# Module 10 数据预处理和模型训练检查报告

## 执行摘要

本报告对Module 10（Eye-Index综合评估模块）及其子模块A、B、C、D的数据预处理、标签处理、归一化/标准化和数据泄露问题进行了全面检查。

**检查结果概览：**
- ✅ 无明显的标签错误
- ⚠️ 存在归一化处理不一致的风险
- ⚠️ 存在潜在的数据泄露风险
- ⚠️ 受试者ID映射可能导致数据对齐问题

---

## 1. 模块架构概览

### 1.1 模块结构
```
Module 10 (Eye-Index综合评估)
├── Module 10-A: 数据预处理 (m10_data_prep)
│   ├── builder.py - 特征构建器
│   ├── schema.py - 数据验证
│   └── settings.py - 配置管理
├── Module 10-B: 训练核心 (m10_training)
│   ├── dataset.py - 数据加载
│   ├── model.py - 模型定义
│   └── trainer.py - 训练流程
├── Module 10-C: 服务API (m10_service)
│   ├── predict.py - 预测接口
│   └── loader.py - 模型管理
└── Module 10-D: 评估可视化 (m10_evaluation)
    └── evaluator.py - 性能评估
```

### 1.2 数据流向
1. **Module 7输出** → Module 10-A (数据预处理)
2. Module 10-A → **NPZ数据集** (按任务Q1-Q5分割)
3. NPZ数据集 → Module 10-B (模型训练)
4. 训练好的模型 → Module 10-C (服务API)
5. 模型+数据 → Module 10-D (性能评估)

---

## 2. 标签处理检查

### 2.1 MMSE子分数计算 ✅ 正确
**位置：** `builder.py` 第273-294行

```python
# Q1: 时间定向（5分）
df['Q1_subscore'] = (年份 + 季节 + 月份 + 星期).fillna(0)

# Q2: 地点定向（5分）
df['Q2_subscore'] = (省市区 + 街道 + 建筑 + 楼层).fillna(0)

# Q3: 即刻记忆（3分）
df['Q3_subscore'] = 即刻记忆.fillna(0)

# Q4: 注意力和计算（5分）
df['Q4_subscore'] = (100-7 + 93-7 + 86-7 + 79-7 + 72-7).fillna(0)

# Q5: 延迟回忆（3分）
df['Q5_subscore'] = (词1 + 词2 + 词3).fillna(0)
```

**评估：** 标签计算逻辑正确，符合MMSE评分标准。

### 2.2 标签归一化 ✅ 正确
**位置：** `builder.py` 第296-298行

```python
max_scores = {'Q1': 5, 'Q2': 5, 'Q3': 3, 'Q4': 5, 'Q5': 3}
for task_id, max_score in max_scores.items():
    df[f'{task_id}_subscore_norm'] = df[f'{task_id}_subscore'] / max_score
```

**评估：** 正确地将各子任务分数归一化到[0,1]范围。

### 2.3 受试者ID映射问题 ⚠️ 警告
**位置：** `builder.py` 第364-367行

```python
# AD组特殊映射: ad3-ad22 映射到 ad01-ad20
if prefix == 'ad' and 3 <= number_int <= 22:
    mapped_number = number_int - 2
    return f"ad{mapped_number:02d}"
```

**问题：** 
- AD组的受试者ID存在特殊映射规则（ad3→ad01, ad4→ad02...）
- 这种映射可能导致数据对齐错误，特别是当MMSE数据和眼动数据使用不同编号体系时

**建议：**
1. 验证MMSE数据文件中AD组的实际编号体系
2. 考虑在数据源头统一编号，而非在预处理中进行映射
3. 添加映射日志以便追踪和调试

---

## 3. 归一化/标准化检查

### 3.1 特征归一化 ⚠️ 存在风险
**位置：** `builder.py` 第144-157行

```python
# 动态映射归一化列
for col in FEATURE_NAMES:
    norm_col = FEATURE_ALIAS[col]  # col + "_norm"
    if norm_col in combined_df.columns:
        combined_df[col] = combined_df[norm_col]  # 覆盖为归一化值
```

**问题：**
1. **依赖上游归一化：** 假设Module 7已经完成归一化，但未验证
2. **缺少范围检查：** 未验证归一化后的值是否在[0,1]范围内
3. **回退机制不明确：** 如果没有`_norm`列，使用原始值可能导致尺度不一致

### 3.2 目标值二次归一化 ⚠️ 潜在问题
**位置：** `dataset.py` 第56-62行

```python
if normalize_targets:
    if self.y.min() < 0 or self.y.max() > 1:
        logger.warning(f"目标值可能未正确归一化")
        # 强制归一化到[0,1]
        self.y = (self.y - self.y.min()) / (self.y.max() - self.y.min() + 1e-8)
```

**问题：**
1. **二次归一化风险：** 如果目标值已经归一化，再次归一化会改变分布
2. **使用全局统计：** 使用整个数据集的min/max进行归一化可能导致数据泄露

**建议：**
1. 在Module 10-A中确保归一化完成，避免在数据加载时再次处理
2. 记录归一化参数（min, max, mean, std）用于推理时的一致性

---

## 4. 数据泄露检查

### 4.1 训练/验证集分割 ✅ 正确
**位置：** `dataset.py` 第150-153行

```python
generator = torch.Generator().manual_seed(seed)
train_dataset, val_dataset = random_split(
    dataset, [n_train, n_val], generator=generator
)
```

**评估：** 使用固定随机种子进行分割，保证可重现性。

### 4.2 潜在的数据泄露风险 ⚠️

#### 风险1：特征归一化使用全局统计
**问题：** Module 7可能使用整个数据集（包括验证集）的统计信息进行归一化

**影响：** 验证集信息泄露到训练集的预处理中

**建议：**
```python
# 正确做法：只使用训练集统计
train_mean = X_train.mean()
train_std = X_train.std()
X_train_norm = (X_train - train_mean) / train_std
X_val_norm = (X_val - train_mean) / train_std  # 使用训练集的统计
```

#### 风险2：受试者级别的数据混合
**位置：** `builder.py` 第202-203行

```python
# 按受试者分组并取均值
subject_grouped = task_data.groupby("subject_id")[FEATURE_NAMES].mean()
```

**问题：** 同一受试者的多条记录被平均，但未确保同一受试者的数据不会同时出现在训练集和验证集中

**建议：** 实现受试者级别的分割，确保同一受试者的所有数据只在训练集或验证集中

#### 风险3：时间序列数据的处理
**问题：** 眼动数据具有时间序列特性，随机分割可能破坏时间依赖性

**建议：** 考虑按时间或会话进行分割，而非随机分割

---

## 5. 其他发现

### 5.1 模型架构一致性 ✅
- 输入维度：10个特征（正确）
- 输出维度：1个回归值（正确）
- 激活函数：最后一层使用Sigmoid，限制输出在[0,1]（适合归一化目标）

### 5.2 损失函数选择 ✅
- 使用MSE损失函数，适合回归任务
- 配合归一化的目标值，损失值易于解释

### 5.3 数据验证不足 ⚠️
**位置：** `schema.py` 验证器

**问题：**
- 缺少对特征值分布的详细验证
- 未检查异常值和离群点
- 未验证特征之间的相关性

---

## 6. 改进建议

### 6.1 立即需要修复
1. **添加归一化验证：** 在Module 10-A中验证所有特征和标签都在[0,1]范围内
2. **修复ID映射：** 统一AD组的受试者编号体系，避免混淆
3. **实现受试者级分割：** 确保同一受试者不会跨越训练/验证集

### 6.2 建议改进
1. **记录预处理参数：** 保存归一化使用的统计信息（mean, std, min, max）
2. **添加数据质量报告：** 生成详细的数据分布和异常值报告
3. **实现增量训练：** 支持新数据的持续学习，但需注意归一化参数的一致性

### 6.3 长期优化
1. **实现交叉验证：** 使用k-fold验证评估模型稳定性
2. **添加特征工程：** 探索特征组合和转换
3. **集成学习：** 训练多个模型并集成，提高预测稳定性

---

## 7. 代码示例：修复数据泄露

```python
# 建议的受试者级别分割实现
def split_by_subject(df, val_ratio=0.2, seed=42):
    """按受试者分割，避免数据泄露"""
    np.random.seed(seed)
    
    # 获取唯一受试者列表
    subjects = df['subject_id'].unique()
    np.random.shuffle(subjects)
    
    # 分割受试者
    n_val = int(len(subjects) * val_ratio)
    val_subjects = subjects[:n_val]
    train_subjects = subjects[n_val:]
    
    # 分割数据
    train_df = df[df['subject_id'].isin(train_subjects)]
    val_df = df[df['subject_id'].isin(val_subjects)]
    
    return train_df, val_df

# 建议的归一化实现
def normalize_features(X_train, X_val=None):
    """使用训练集统计进行归一化"""
    # 计算训练集统计
    train_mean = X_train.mean(axis=0)
    train_std = X_train.std(axis=0) + 1e-8
    
    # 归一化
    X_train_norm = (X_train - train_mean) / train_std
    
    if X_val is not None:
        # 使用训练集统计归一化验证集
        X_val_norm = (X_val - train_mean) / train_std
        return X_train_norm, X_val_norm, {'mean': train_mean, 'std': train_std}
    
    return X_train_norm, {'mean': train_mean, 'std': train_std}
```

---

## 8. 结论

Module 10的整体架构设计合理，代码质量较高。主要风险点在于：

1. **数据预处理的一致性：** 需要确保训练和推理时使用相同的归一化参数
2. **数据泄露预防：** 需要实施更严格的数据分割策略
3. **受试者ID管理：** 需要统一和规范化ID体系

建议优先处理数据泄露风险和归一化一致性问题，这些问题可能直接影响模型的泛化性能和评估的可靠性。

---

**报告生成时间：** 2024年
**检查人员：** AI Assistant
**版本：** v1.0