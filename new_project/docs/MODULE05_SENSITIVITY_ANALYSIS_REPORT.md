# Module05 RQA参数敏感度分析 - 功能报告

**文档版本**: v1.0
**创建日期**: 2025-10-10
**目的**: 为Module06特征选择提供Module05敏感度分析功能说明

---

## 📋 执行摘要

✅ **好消息**: Module05**已经实现了完整的参数敏感度分析功能**!

核心能力:
- ✅ 计算3264个参数组合的敏感性评分
- ✅ 基于ANOVA F-test评估组间差异
- ✅ 计算效应量(Eta-squared)
- ✅ 评估任务一致性
- ✅ 生成综合敏感度得分
- ✅ 提供完整的API接口和可视化

---

## 1. 已实现的敏感度分析功能

### 1.1 核心分析器

**文件**: `parameter_sensitivity_analyzer.py`

**功能**: 计算每个RQA参数组合在区分Control/MCI/AD三组间的能力

### 1.2 分析指标 (5个)

Module05的敏感度分析使用**5个互补指标**:

#### 指标1: F-statistic (ANOVA)
```python
# 对每个任务(q1-q5)分别计算ANOVA F统计量
for task in ['q1', 'q2', 'q3', 'q4', 'q5']:
    control = df[df['group'] == 'control'][feature]
    mci = df[df['group'] == 'mci'][feature]
    ad = df[df['group'] == 'ad'][feature]

    f_stat, p_val = stats.f_oneway(control, mci, ad)
```
**含义**: 组间差异 vs 组内差异比值,越大越好

#### 指标2: P-value
```python
# ANOVA返回的显著性p值
# p < 0.05 表示统计显著
```
**含义**: 统计显著性,越小越好

#### 指标3: Effect Size (Eta-squared)
```python
# 计算效应量
eta_squared = SS_between / SS_total
```
**含义**: 组别因素解释的方差比例 (0-1),越大效应越强
- 0.01-0.06: 小效应
- 0.06-0.14: 中等效应
- 0.14+: 大效应

#### 指标4: Task Consistency (任务一致性)
```python
# 跨任务的F统计量变异系数
cv = std(f_stats) / mean(f_stats)
task_consistency = 1 / (1 + cv)  # 归一化到[0,1]
```
**含义**: 参数在不同任务上表现的稳定性,越高越好

#### 指标5: Overall Score (综合评分)
```python
overall_score = (
    0.4 * min(f_stat_mean / 100, 1.0) +  # F统计量权重40%
    0.3 * effect_size_mean +              # 效应量权重30%
    0.2 * task_consistency -              # 一致性权重20%
    0.1 * p_val_mean                      # p值惩罚10%
)
```
**含义**: 加权综合得分,用于排序

---

## 2. API接口

### 2.1 核心API端点

#### API #1: 扫描RQA结果
```
GET /api/m05/sensitivity/scan-results
```
**功能**: 扫描磁盘上所有已完成的RQA分析结果

**响应示例**:
```json
{
    "success": true,
    "results": [
        {
            "params": {"m": 2, "tau": 1, "eps": 0.050, "lmin": 2},
            "enriched_features_path": "data/05_rqa_analysis/m2_tau1_eps0.050_lmin2/step3_enriched_features.csv"
        },
        ...
    ],
    "total": 3264
}
```

#### API #2: 计算敏感度评分 (异步任务)
```
POST /api/m05/sensitivity/compute-scores
{
    "params_filter": {
        "m_range": [1, 10],
        "tau_range": [1, 10]
    }
}
```
**功能**: 提交敏感度分析任务(异步执行,避免阻塞)

**响应**:
```json
{
    "success": true,
    "task_id": "sensitivity_task_20251010_143052",
    "message": "参数敏感性分析任务已提交"
}
```

#### API #3: 查询任务状态
```
GET /api/m05/sensitivity/status/<task_id>
```
**响应示例**:
```json
{
    "success": true,
    "data": {
        "task": {
            "task_id": "sensitivity_task_20251010_143052",
            "status": "completed",  // pending, running, completed, failed
            "progress": 100,
            "total_params": 3264,
            "processed_params": 3264,
            "result_file": "data/05_rqa_analysis/sensitivity_scores_20251010_143052.csv"
        }
    }
}
```

#### API #4: 3D参数空间可视化
```
POST /api/m05/sensitivity/plot-3d-space
{
    "feature": "rr-1d-x",
    "sensitivity_scores_file": "sensitivity_scores.csv"
}
```
**功能**: 生成交互式3D散点图(Plotly)

#### API #5: 参数-特征热图
```
POST /api/m05/sensitivity/plot-heatmap
{
    "sensitivity_scores_file": "sensitivity_scores.csv",
    "metric": "overall_score"
}
```
**功能**: 生成参数组合 × RQA特征热图

---

## 3. RQA特征维度

### 3.1 动态特征识别

Module05使用`_identify_rqa_features()`自动识别RQA特征列:

**识别模式**:
```python
rqa_prefixes = ['rr-', 'det-', 'ent-', 'lam-', 'x_', 'y_', 'combined_', 'rqa_']
rqa_keywords = ['symmetry', 'diff', 'complexity']
```

**实际特征列** (基于step3_enriched_features.csv):
```
1D特征 (x坐标):
- rr-1d-x       # 递归率
- det-1d-x      # 确定性
- ent-1d-x      # 熵
- lam-1d-x      # Laminarity

1D特征 (y坐标):
- rr-1d-y
- det-1d-y
- ent-1d-y
- lam-1d-y

2D特征 (xy轨迹):
- rr-2d-xy
- det-2d-xy
- ent-2d-xy
- lam-2d-xy

派生特征:
- combined_rr
- rqa_complexity_1d
- rqa_complexity_2d
- x_y_symmetry
- rr_xy_diff
- det_xy_diff
...
```

**总计**: 约**15-20个RQA特征** (取决于step3增强逻辑)

---

## 4. Module06集成方案

### 4.1 策略A: 选择Top-6 RQA特征

**方法1**: 基于单个最优参数
```python
# Step 1: 获取敏感度评分
response = requests.get('/api/m05/sensitivity/compute-scores')
task_id = response.json()['task_id']

# Step 2: 等待完成
while True:
    status = requests.get(f'/api/m05/sensitivity/status/{task_id}').json()
    if status['data']['task']['status'] == 'completed':
        break

# Step 3: 读取结果
result_file = status['data']['task']['result_file']
sensitivity_df = pd.read_csv(result_file)

# Step 4: 选择overall_score最高的参数组合
best_param = sensitivity_df.groupby('param_signature').agg({
    'overall_score': 'mean'
}).idxmax()

# Step 5: 提取该参数下Top-6 RQA特征
param_features = sensitivity_df[
    sensitivity_df['param_signature'] == best_param
].sort_values('overall_score', ascending=False).head(6)

top6_features = param_features['feature'].tolist()
# 例如: ['rr-2d-xy', 'det-2d-xy', 'ent-1d-x', 'rr-1d-x', 'det-1d-x', 'ent-2d-xy']
```

**方法2**: 跨参数选择Top-6特征 (推荐)
```python
# 对所有参数组合,按特征聚合敏感度
feature_scores = sensitivity_df.groupby('feature').agg({
    'overall_score': 'mean',
    'f_statistic': 'mean',
    'effect_size': 'mean'
}).sort_values('overall_score', ascending=False)

top6_features = feature_scores.head(6).index.tolist()
```

### 4.2 策略B: 选择Top-10参数组合

```python
# 按参数组合聚合
param_scores = sensitivity_df.groupby('param_signature').agg({
    'overall_score': 'mean',
    'f_statistic': 'mean',
    'effect_size': 'mean',
    'task_consistency': 'mean'
}).sort_values('overall_score', ascending=False)

top10_params = param_scores.head(10).index.tolist()

# 每个参数提取6维RQA特征
# 总计: 10 × 6 = 60维
```

---

## 5. 关键问题分析

### 5.1 ✅ Module05已经找出最敏感的特征吗?

**答**: **部分完成,但需要运行计算**

- ✅ **敏感度分析功能已实现**: `ParameterSensitivityAnalyzer`类完整实现
- ✅ **API端点可用**: `/api/m05/sensitivity/compute-scores`
- ❓ **是否已运行过**: 需要检查是否有缓存的敏感度评分文件

让我检查是否有缓存结果:

```bash
# 检查是否有敏感度评分文件
ls data/05_rqa_analysis/sensitivity_scores_*.csv
```

### 5.2 敏感度分析的计算成本

**输入**: 3264个参数组合 × 5个任务 × ~15个RQA特征 = **约245,000次ANOVA计算**

**预计时间**:
- CPU密集型计算
- 预计耗时: 10-30分钟 (取决于CPU性能)
- 内存需求: ~2GB

**建议**:
- 提交异步任务,不要阻塞主线程
- 结果缓存到CSV,避免重复计算

---

## 6. Module06使用建议

### 6.1 策略A实施步骤

**Step 1**: 运行Module05敏感度分析(如果未运行)
```bash
curl -X POST http://127.0.0.1:9090/api/m05/sensitivity/compute-scores
```

**Step 2**: 等待完成,获取结果
```bash
curl http://127.0.0.1:9090/api/m05/sensitivity/status/<task_id>
```

**Step 3**: 从结果中选择Top-6 RQA特征
```python
# 方法1: 单个最优参数的6维
# 方法2: 跨参数Top-6特征
```

**Step 4**: Module04选择Top-4,Module05选择Top-6
```python
# 总计: 4 + 6 = 10维
# 样本比: 300 / 10 = 30:1 ✅
```

### 6.2 特征选择方法对比

| 方法 | Module04 | Module05 | 总维度 | 样本比 | 优势 |
|------|----------|----------|--------|--------|------|
| **A1** | Top-4特征 | 单参数6维RQA | 10维 | 30:1 | 极简,可解释性强 |
| **A2** | Top-4特征 | 跨参数Top-6特征 | 10维 | 30:1 | 特征多样性高 |
| **B** | 全量9维 | Top-10参数×6 | 69维 | 4.3:1 | 特征完整,性能高 |

**推荐**: **方法A2** - 跨参数选择Top-6 RQA特征
- 原因: 不同参数组合可能在不同特征上表现最佳,跨参数选择避免局限于单一参数组合

---

## 7. 待办事项

**Module05侧**:
- [ ] 运行敏感度分析(如果未运行)
- [ ] 确认缓存结果可用
- [ ] 可选: 添加API返回Top-K特征直接查询接口

**Module06侧**:
- [ ] 集成Module05敏感度API
- [ ] 实现Top-6特征选择逻辑
- [ ] 与Module04 Top-4特征融合
- [ ] 生成10维特征向量

---

## 8. 总结

### ✅ Module05已具备的能力

1. **完整的参数敏感度分析器**: 5个互补指标
2. **API接口**: 异步任务提交、状态查询
3. **可视化支持**: 3D参数空间、热图
4. **动态特征识别**: 自适应RQA特征列

### ⚠️ 需要确认的事项

1. **是否已运行过敏感度分析**: 检查缓存文件
2. **RQA特征实际数量**: 取决于step3增强逻辑
3. **最优参数组合**: 需要查看实际评分结果

### 🎯 下一步行动

**优先级1**: 检查是否有敏感度评分缓存
```bash
ls -lh data/05_rqa_analysis/sensitivity_scores_*.csv
```

**优先级2**: 如果没有,运行敏感度分析
```bash
curl -X POST http://127.0.0.1:9090/api/m05/sensitivity/compute-scores
```

**优先级3**: 查看Top-10参数和Top-6特征
```python
sensitivity_df = pd.read_csv('sensitivity_scores.csv')
print(sensitivity_df.groupby('param_signature')['overall_score'].mean().sort_values(ascending=False).head(10))
print(sensitivity_df.groupby('feature')['overall_score'].mean().sort_values(ascending=False).head(6))
```

---

**文档状态**: ✅ 完成
**审核状态**: 待验证缓存文件
**下一步**: 运行敏感度分析或查看缓存结果
