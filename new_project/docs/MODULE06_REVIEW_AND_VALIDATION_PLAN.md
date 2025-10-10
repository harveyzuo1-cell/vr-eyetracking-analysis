# Module06 审核与数据验证计划

**文档版本**: v1.0
**创建日期**: 2025-10-10
**目的**: 在正式开发前,对设计方案进行技术审核、业务审核和数据验证
**优先级**: P0 (必须在开发前完成)

---

## 📋 目录

1. [审核目标](#1-审核目标)
2. [技术审核](#2-技术审核)
3. [业务审核](#3-业务审核)
4. [数据验证](#4-数据验证)
5. [审核流程](#5-审核流程)
6. [审核检查清单](#6-审核检查清单)
7. [数据验证实验](#7-数据验证实验)
8. [审核报告模板](#8-审核报告模板)

---

## 1. 审核目标

### 1.1 核心目标

在正式开发Module06之前,通过**三重审核**确保设计方案的科学性、合理性和可行性:

```
┌────────────────────────────────────────────────────────┐
│            Module06 三重审核体系                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ 技术审核     │  │ 业务审核     │  │ 数据验证     │   │
│  │             │  │             │  │             │   │
│  │ • 统计方法   │  │ • 临床意义   │  │ • 真实数据   │   │
│  │ • 算法设计   │  │ • 特征解释   │  │ • 实验验证   │   │
│  │ • 架构合理性 │  │ • 应用场景   │  │ • 推荐调整   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│         │                │                │            │
│         └────────────────┴────────────────┘            │
│                          │                             │
│                  ┌───────▼────────┐                    │
│                  │ 审核报告 + 改进  │                    │
│                  │    建议          │                    │
│                  └─────────────────┘                    │
└────────────────────────────────────────────────────────┘
```

### 1.2 审核范围

| 审核类型 | 审核对象 | 审核人 | 工期 | 优先级 |
|---------|---------|--------|------|--------|
| **技术审核** | 统计方法、算法设计、系统架构 | 数据科学家/算法工程师 | 2天 | P0 |
| **业务审核** | 临床意义、特征解释、应用场景 | 临床专家/认知神经科学家 | 2天 | P0 |
| **数据验证** | 实际数据特征选择、推荐调整 | 数据分析师 | 3天 | P0 |

### 1.3 成功标准

- ✅ 技术审核通过率 > 90%
- ✅ 业务审核专家认可度 > 80%
- ✅ 数据验证与文献推荐一致性 > 70%
- ✅ 所有P0问题解决
- ✅ 生成改进建议清单

---

## 2. 技术审核

### 2.1 统计方法审核

#### 2.1.1 审核要点

**审核对象**: Module04敏感度分析的5个统计指标

| 指标 | 审核问题 | 参考标准 |
|------|---------|---------|
| **ANOVA F-test** | • 数据是否满足正态性假设?<br>• 方差齐性是否检验?<br>• 样本量是否足够? | • Shapiro-Wilk检验<br>• Levene检验<br>• 每组n≥30 |
| **Effect Size (η²)** | • 公式是否正确?<br>• 解释标准是否合理? | • Cohen (1988)标准<br>• η² = SS_between / SS_total |
| **Pairwise T-tests** | • Bonferroni校正是否合理?<br>• 是否应考虑其他校正方法? | • α' = 0.05 / 3<br>• 或考虑FDR校正 |
| **Cohen's d** | • 合并标准差计算是否正确?<br>• 解释标准是否合理? | • Cohen (1988)标准<br>• s_pooled公式验证 |
| **变异系数 (CV)** | • 是否适用于所有特征?<br>• 对均值接近0的特征如何处理? | • CV仅适用于比率数据<br>• 添加阈值保护 |

#### 2.1.2 审核任务

**任务1: 正态性检验**
```python
# 审核脚本: check_normality.py
from scipy.stats import shapiro

def check_normality_assumptions(df, features):
    """检查各组各特征的正态性"""
    results = []

    for feature in features:
        for group in ['control', 'mci', 'ad']:
            data = df[df['group'] == group][feature].dropna()

            # Shapiro-Wilk检验
            stat, p_value = shapiro(data)

            results.append({
                'feature': feature,
                'group': group,
                'shapiro_statistic': stat,
                'p_value': p_value,
                'is_normal': p_value > 0.05,
                'sample_size': len(data)
            })

    results_df = pd.DataFrame(results)

    # 汇总: 哪些特征违反正态性假设
    violations = results_df[results_df['is_normal'] == False]

    return {
        'results': results_df,
        'violations': violations,
        'violation_rate': len(violations) / len(results_df)
    }

# 执行
normality_check = check_normality_assumptions(m04_features_df, M04_FEATURES)

# 报告
print(f"正态性违反率: {normality_check['violation_rate']:.1%}")
if normality_check['violation_rate'] > 0.3:
    print("⚠️ 警告: >30%的特征-组合违反正态性假设")
    print("建议: 考虑使用Kruskal-Wallis非参数检验替代ANOVA")
```

**任务2: 方差齐性检验**
```python
# 审核脚本: check_homogeneity.py
from scipy.stats import levene

def check_variance_homogeneity(df, features):
    """检查方差齐性 (Levene检验)"""
    results = []

    for feature in features:
        control = df[df['group'] == 'control'][feature].dropna()
        mci = df[df['group'] == 'mci'][feature].dropna()
        ad = df[df['group'] == 'ad'][feature].dropna()

        # Levene检验
        stat, p_value = levene(control, mci, ad)

        results.append({
            'feature': feature,
            'levene_statistic': stat,
            'p_value': p_value,
            'is_homogeneous': p_value > 0.05
        })

    results_df = pd.DataFrame(results)
    violations = results_df[results_df['is_homogeneous'] == False]

    return {
        'results': results_df,
        'violations': violations,
        'violation_rate': len(violations) / len(results_df)
    }
```

**任务3: 多重比较校正方法对比**
```python
# 审核脚本: compare_corrections.py
from statsmodels.stats.multitest import multipletests

def compare_correction_methods(p_values):
    """对比不同多重比较校正方法"""
    methods = ['bonferroni', 'holm', 'fdr_bh']

    results = {}
    for method in methods:
        rejected, p_adjusted, _, _ = multipletests(p_values, method=method)
        results[method] = {
            'rejected_count': rejected.sum(),
            'p_adjusted': p_adjusted
        }

    return results

# 分析
print("多重比较校正方法对比:")
print("Bonferroni: 最保守,控制FWER")
print("Holm: 比Bonferroni宽松,仍控制FWER")
print("FDR (Benjamini-Hochberg): 控制FDR,更宽松")
print("\n推荐: 使用Bonferroni (保守,适合临床应用)")
```

#### 2.1.3 审核决策

**决策树**:
```
正态性检验通过率 > 70%?
├── 是 → 使用ANOVA F-test ✅
└── 否 → 是否可用非参数检验?
    ├── 是 → 使用Kruskal-Wallis检验 ⚠️
    └── 否 → 考虑数据转换 (log, sqrt)

方差齐性检验通过率 > 70%?
├── 是 → 使用标准ANOVA ✅
└── 否 → 使用Welch's ANOVA (不假设方差齐性) ⚠️

多重比较校正方法?
├── 临床应用 → Bonferroni (保守) ✅
└── 科研探索 → FDR (宽松) ⚠️
```

### 2.2 算法设计审核

#### 2.2.1 综合敏感度得分公式审核

**当前公式**:
```python
sensitivity_score = (F × η²) / (1 + p_value) × (1 / (1 + CV/100))
```

**审核问题**:

| 问题 | 审核点 | 建议 |
|------|--------|------|
| **权重合理性** | 为什么不使用显式权重? | 考虑改为加权和:<br>`w1×F + w2×η² - w3×p + w4/CV` |
| **归一化** | F统计量未归一化,范围[0, +∞] | 添加归一化: `min(F/100, 1.0)` |
| **p值处理** | `1/(1+p)`是否合理? | 考虑`-log10(p)`或`1-p` |
| **CV异常值** | CV接近0时,得分爆炸 | 添加下界: `max(CV, 1.0)` |

**改进建议**:
```python
def compute_sensitivity_score_v2(f_stat, eta_squared, p_value, avg_cv):
    """
    改进版敏感度得分

    Score = w1 × F_norm + w2 × η² + w3 × (1 - p) + w4 × (1 / CV_safe)

    权重:
    - w1 = 0.3: F统计量 (显著性)
    - w2 = 0.3: 效应量 (实际差异大小)
    - w3 = 0.2: p值 (统计可信度)
    - w4 = 0.2: 稳定性 (低CV更好)
    """
    # 归一化F统计量 (假设F > 100为极端值)
    f_norm = min(f_stat / 100.0, 1.0)

    # 归一化p值
    p_norm = 1 - p_value

    # 安全的CV (避免除零)
    cv_safe = max(avg_cv, 1.0)
    cv_score = 1 / (cv_safe / 100)  # CV=10% → 10分, CV=100% → 1分

    # 加权和
    score = (
        0.3 * f_norm +
        0.3 * eta_squared +
        0.2 * p_norm +
        0.2 * min(cv_score, 1.0)  # CV得分也归一化到[0,1]
    )

    return score
```

#### 2.2.2 特征选择策略审核

**审核问题**: 策略A使用"跨参数Top-6特征"是否合理?

**备选方案**:

| 方案 | 优势 | 劣势 | 推荐度 |
|------|------|------|--------|
| **方案A: 跨参数Top-6** | 特征多样性高 | 可能丢失参数信息 | ⭐⭐⭐⭐ |
| **方案B: 单参数Top-6** | 保留参数一致性 | 局限于单一参数组合 | ⭐⭐⭐ |
| **方案C: 分层选择** | 从低/中/高复杂度各选2个 | 可能不是全局最优 | ⭐⭐⭐⭐ |
| **方案D: 聚类后选择** | 避免冗余特征 | 计算复杂度高 | ⭐⭐⭐ |

**推荐**: 方案A (跨参数) + 方案C (分层) 结合

```python
def select_top6_rqa_features_hybrid(sensitivity_df):
    """
    混合策略: 跨参数 + 分层选择

    Step 1: 将参数分为3个复杂度层级
      - Low: m ∈ [1,3], tau ∈ [1,3]
      - Mid: m ∈ [4,6], tau ∈ [4,6]
      - High: m ∈ [7,10], tau ∈ [7,10]

    Step 2: 从每层选择Top-2特征

    Step 3: 确保6个特征不重复
    """
    # 定义复杂度层级
    low_params = sensitivity_df[(sensitivity_df['m'] <= 3) & (sensitivity_df['tau'] <= 3)]
    mid_params = sensitivity_df[(sensitivity_df['m'].between(4, 6)) & (sensitivity_df['tau'].between(4, 6))]
    high_params = sensitivity_df[(sensitivity_df['m'] >= 7) & (sensitivity_df['tau'] >= 7)]

    # 从每层选Top-2
    top2_low = low_params.groupby('feature')['overall_score'].mean().sort_values(ascending=False).head(2)
    top2_mid = mid_params.groupby('feature')['overall_score'].mean().sort_values(ascending=False).head(2)
    top2_high = high_params.groupby('feature')['overall_score'].mean().sort_values(ascending=False).head(2)

    # 合并 (去重)
    all_features = set(top2_low.index) | set(top2_mid.index) | set(top2_high.index)

    # 如果不足6个,从全局Top-6补充
    if len(all_features) < 6:
        global_top6 = sensitivity_df.groupby('feature')['overall_score'].mean().sort_values(ascending=False).head(6)
        all_features = all_features | set(global_top6.index)

    return list(all_features)[:6]
```

### 2.3 系统架构审核

#### 2.3.1 审核要点

| 架构组件 | 审核问题 | 审核标准 |
|---------|---------|---------|
| **5层架构** | 层级划分是否清晰?<br>依赖方向是否合理? | • 单向依赖<br>• 无循环依赖 |
| **Module客户端** | HTTP调用 vs 直接文件读取? | • 性能对比<br>• 缓存策略 |
| **缓存设计** | 缓存粒度?过期策略? | • 敏感度评分长期缓存<br>• 特征向量短期缓存 |
| **异步任务** | 批量提取是否需要队列? | • 样本数 > 100 → 异步 |
| **错误处理** | 缺失值、异常值如何处理? | • Graceful degradation<br>• 日志记录 |

#### 2.3.2 性能审核

**基准测试计划**:

```python
# 审核脚本: benchmark.py
import time

def benchmark_feature_extraction():
    """特征提取性能基准测试"""

    # Test 1: 单样本延迟
    start = time.time()
    extract_strategy_a('control_legacy_1', 'control', 'q1')
    latency_single = time.time() - start

    assert latency_single < 1.0, f"单样本延迟超标: {latency_single:.2f}s > 1s"

    # Test 2: 批量吞吐量
    start = time.time()
    extract_batch_strategy_a(sample_count=100)
    time_100_samples = time.time() - start

    throughput = 100 / (time_100_samples / 60)  # 样本/分钟
    assert throughput > 100, f"吞吐量不足: {throughput:.1f} < 100样本/分钟"

    # Test 3: 内存占用
    import psutil
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB

    extract_batch_strategy_b(sample_count=300)

    mem_after = process.memory_info().rss / 1024 / 1024
    mem_usage = mem_after - mem_before

    assert mem_usage < 2048, f"内存占用超标: {mem_usage:.1f}MB > 2GB"

    print("✅ 性能基准测试通过")
    print(f"  - 单样本延迟: {latency_single:.3f}s")
    print(f"  - 批量吞吐量: {throughput:.1f}样本/分钟")
    print(f"  - 内存占用: {mem_usage:.1f}MB")
```

---

## 3. 业务审核

### 3.1 临床意义审核

#### 3.1.1 特征临床解释审核

**审核对象**: Module04的9个特征是否有临床意义

| 特征 | 当前临床解释 | 审核问题 | 文献支持 |
|------|------------|---------|---------|
| **avg_fixation_duration** | 注意力稳定性<br>AD患者异常 | • AD患者是增加还是减少?<br>• MCI阶段是否有变化? | [需文献] |
| **kw_ratio_frame** | 关键信息捕获能力 | • 是否所有任务都适用?<br>• q5无ROI如何解释? | [需文献] |
| **avg_saccade_amplitude** | 视觉搜索效率<br>AD患者减小 | • 减小程度有多大?<br>• 是否有量化标准? | [需文献] |
| **total_fixations** | 视觉采样频率 | • 频率高是好是坏?<br>• 与认知功能的关系? | [需文献] |
| **bg_ratio_frame** | 注意力分散程度 | • 背景占比高 = 注意力差?<br>• 是否有混淆因素? | [需文献] |
| **inst_ratio_frame** | 指令遵循能力 | • 指令占比与执行功能关系? | [需文献] |
| **total_saccades** | 视觉搜索活跃度 | • 活跃度与认知的关系? | [需文献] |
| **task_total_time** | 任务完成效率 | • 时间长 = 认知慢?<br>• 是否排除焦虑等混淆? | [需文献] |
| **total_fixation_time** | 视觉信息处理时间 | • 与task_total_time区别? | [需文献] |

#### 3.1.2 审核任务

**任务1: 文献调研** (2天)

```markdown
# 文献调研计划

## 目标
为9个Module04特征寻找认知神经科学/临床神经学文献支持

## 数据库
- PubMed
- Google Scholar
- Web of Science

## 检索关键词
- "eye tracking AND Alzheimer's disease"
- "fixation duration AND mild cognitive impairment"
- "saccade amplitude AND dementia"
- "visual attention AND AD"

## 输出
每个特征至少找到2篇文献支持,记录:
1. 文献标题
2. 作者 + 年份
3. 核心发现 (AD患者该特征的变化方向和程度)
4. 样本量和置信度
```

**任务2: 临床专家访谈** (1天)

```markdown
# 专家访谈问题清单

## 受访专家
- 神经科医生 (AD诊断经验 > 5年)
- 认知神经心理学家

## 访谈问题

### 特征解释验证
1. "平均注视时长"在AD患者中通常是增加还是减少?
2. "关键词区域占比"是否能反映注意力选择性?
3. 哪些特征在MCI早期阶段最敏感?

### 特征重要性排序
4. 如果只能选4个眼动特征用于临床筛查,您会选哪4个?
5. 为什么?

### 混淆因素
6. 除了认知功能,还有哪些因素会影响眼动指标?
   (年龄、教育程度、视力、焦虑等)
7. 如何控制这些混淆因素?

### 临床应用
8. 10维特征向量对于临床医生是否可解释?
9. 是否需要提供特征重要性排序?
```

#### 3.1.3 审核输出

**文献支持表** (示例):

| 特征 | 文献1 | 文献2 | 一致性结论 |
|------|-------|-------|-----------|
| avg_fixation_duration | Smith et al. (2018)<br>AD患者↑ 15-20% | Jones et al. (2020)<br>AD患者↑ 18% | ✅ 一致:<br>AD患者注视时长增加 |
| avg_saccade_amplitude | Lee et al. (2019)<br>AD患者↓ 25% | Wang et al. (2021)<br>AD患者↓ 30% | ✅ 一致:<br>AD患者扫视幅度减小 |
| kw_ratio_frame | [无文献] | [无文献] | ⚠️ 缺乏文献支持<br>需要数据验证 |

**专家意见汇总**:

```markdown
## 专家反馈 (2位神经科医生 + 1位神经心理学家)

### 一致意见
✅ avg_fixation_duration 和 avg_saccade_amplitude 是最有临床价值的特征
✅ total_fixations 可反映视觉搜索策略变化
✅ 10维特征对临床医生来说是可接受的 (如果有解释)

### 分歧意见
⚠️ kw_ratio_frame: 2位认为有价值, 1位认为依赖ROI定义,可靠性存疑
⚠️ task_total_time: 可能受焦虑、动机等非认知因素影响

### 建议
💡 添加年龄、教育程度作为协变量控制
💡 考虑按任务类型分别分析 (结构化 vs 自由浏览)
💡 提供特征重要性可视化 (SHAP值)
```

### 3.2 应用场景审核

#### 3.2.1 策略A vs 策略B适用性

**审核问题**: 双策略设计是否覆盖主要应用场景?

**应用场景分析**:

| 场景 | 需求 | 推荐策略 | 理由 |
|------|------|---------|------|
| **社区筛查** | 快速、低成本、移动端 | 策略A (10维) | 延迟<0.1s,可部署到平板 |
| **医院门诊** | 准确、可解释 | 策略A (10维) | 医生可理解每个特征 |
| **科研数据库** | 全面、高精度 | 策略B (69维) | 用于发表论文,特征完整 |
| **药物试验** | 敏感、可追踪 | 策略B (69维) | 检测微小变化 |
| **远程医疗** | 轻量、实时 | 策略A (10维) | 网络传输小,响应快 |
| **多中心研究** | 标准化、可复现 | 策略A (10维) | 统一标准,易于推广 |

**审核结论**: ✅ 双策略设计覆盖主要场景,但需补充:

- **策略C (中等)**: 20-30维,平衡性能与效率
  - 适用场景: 大型医院精准诊断
  - 特征选择: Module04全量9维 + Module05 Top-3参数×6 = 27维

---

## 4. 数据验证

### 4.1 验证目标

使用**v1真实数据**(300样本)验证:
1. 文献推荐的Top-4 Module04特征是否实际最敏感
2. Module05的Top-6 RQA特征是什么
3. 是否需要调整特征选择策略

### 4.2 验证实验设计

#### 实验1: Module04特征敏感度验证

**实验目的**: 计算9个特征的实际敏感度,验证文献推荐

**实验步骤**:

```python
# 实验脚本: experiment_m04_sensitivity.py

# Step 1: 加载v1数据
m04_features = load_module04_features(data_version='v1')
print(f"加载样本数: {len(m04_features)}")

# Step 2: 计算敏感度
analyzer = SensitivityAnalyzer(m04_features)
sensitivity_results = analyzer.compute_all_features()

# Step 3: 与文献推荐对比
literature_top4 = ['avg_fixation_duration', 'kw_ratio_frame',
                   'avg_saccade_amplitude', 'total_fixations']

actual_top4 = sensitivity_results.head(4)['feature_name'].tolist()

# Step 4: 计算一致性
overlap = set(literature_top4) & set(actual_top4)
consistency = len(overlap) / 4

print(f"\n文献推荐Top-4: {literature_top4}")
print(f"实际数据Top-4: {actual_top4}")
print(f"一致性: {consistency:.0%} ({len(overlap)}/4)")

# Step 5: 详细对比
comparison = sensitivity_results[['feature_name', 'rank', 'sensitivity_score']].copy()
comparison['literature_recommended'] = comparison['feature_name'].isin(literature_top4)

print("\n详细对比:")
print(comparison)

# Step 6: 生成报告
report = {
    'date': datetime.now().isoformat(),
    'literature_top4': literature_top4,
    'actual_top4': actual_top4,
    'consistency': consistency,
    'full_results': sensitivity_results.to_dict('records'),
    'recommendation': 'Use actual_top4' if consistency < 0.75 else 'Use literature_top4'
}

# 保存
with open('data/06_features/validation/m04_sensitivity_validation.json', 'w') as f:
    json.dump(report, f, indent=2)
```

**预期输出**:

```json
{
  "date": "2025-10-10T15:30:00",
  "literature_top4": [
    "avg_fixation_duration",
    "kw_ratio_frame",
    "avg_saccade_amplitude",
    "total_fixations"
  ],
  "actual_top4": [
    "avg_fixation_duration",  // Rank 1
    "avg_saccade_amplitude",  // Rank 2
    "kw_ratio_frame",         // Rank 3
    "total_saccades"          // Rank 4 (不同!)
  ],
  "consistency": 0.75,
  "recommendation": "Use actual_top4 (3/4一致,但total_saccades替代total_fixations)"
}
```

#### 实验2: Module05特征敏感度验证

**实验目的**: 运行Module05敏感度分析,获取实际Top-6 RQA特征

**实验步骤**:

```python
# 实验脚本: experiment_m05_sensitivity.py

# Step 1: 调用Module05敏感度分析API
response = requests.post('http://localhost:9090/api/m05/sensitivity/compute-scores', json={
    'params_filter': {
        'm_range': [1, 10],
        'tau_range': [1, 10]
    }
})

task_id = response.json()['task_id']
print(f"任务ID: {task_id}")

# Step 2: 等待完成 (估计10-30分钟)
import time
while True:
    status_resp = requests.get(f'http://localhost:9090/api/m05/sensitivity/status/{task_id}')
    status = status_resp.json()['data']['task']['status']
    progress = status_resp.json()['data']['task'].get('progress', 0)

    print(f"进度: {progress}% - {status}")

    if status == 'completed':
        break
    elif status == 'failed':
        raise Exception("敏感度分析失败")

    time.sleep(30)  # 每30秒查询一次

# Step 3: 读取结果
result_file = status_resp.json()['data']['task']['result_file']
sensitivity_df = pd.read_csv(result_file)

print(f"总记录数: {len(sensitivity_df)}")
print(f"参数组合数: {sensitivity_df['param_signature'].nunique()}")
print(f"特征数: {sensitivity_df['feature'].nunique()}")

# Step 4: 跨参数聚合,选择Top-6特征
feature_scores = sensitivity_df.groupby('feature').agg({
    'overall_score': 'mean',
    'f_statistic': 'mean',
    'effect_size': 'mean',
    'task_consistency': 'mean'
}).sort_values('overall_score', ascending=False)

top6_features = feature_scores.head(6)

print("\nTop-6 RQA特征 (跨参数聚合):")
print(top6_features)

# Step 5: 分析特征分布
print("\n特征类型分布:")
feature_types = {
    '1D-x': [f for f in top6_features.index if '1d-x' in f.lower()],
    '1D-y': [f for f in top6_features.index if '1d-y' in f.lower()],
    '2D-xy': [f for f in top6_features.index if '2d' in f.lower()]
}

for ftype, features in feature_types.items():
    print(f"  {ftype}: {len(features)}个 - {features}")

# Step 6: 生成报告
report = {
    'date': datetime.now().isoformat(),
    'task_id': task_id,
    'top6_features': top6_features.index.tolist(),
    'top6_scores': top6_features['overall_score'].tolist(),
    'feature_type_distribution': {k: len(v) for k, v in feature_types.items()},
    'recommendation': 'Use these Top-6 features for Strategy A'
}

with open('data/06_features/validation/m05_sensitivity_validation.json', 'w') as f:
    json.dump(report, f, indent=2)
```

**预期输出** (示例):

```json
{
  "date": "2025-10-10T16:45:00",
  "task_id": "sensitivity_task_20251010_153000",
  "top6_features": [
    "det-2d-xy",      // Rank 1: 2D确定性
    "rr-2d-xy",       // Rank 2: 2D递归率
    "ent-1d-x",       // Rank 3: 1D-x熵
    "det-1d-x",       // Rank 4: 1D-x确定性
    "ent-2d-xy",      // Rank 5: 2D熵
    "rr-1d-y"         // Rank 6: 1D-y递归率
  ],
  "top6_scores": [0.678, 0.654, 0.632, 0.621, 0.598, 0.576],
  "feature_type_distribution": {
    "1D-x": 2,
    "1D-y": 1,
    "2D-xy": 3
  },
  "recommendation": "Use these Top-6 features for Strategy A"
}
```

#### 实验3: 特征组合性能验证

**实验目的**: 对比不同特征组合的分类性能

**实验设计**:

```python
# 实验脚本: experiment_feature_combination.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

# 准备数据
X_full = m04_features_df[M04_FEATURES]  # 9维全量
y = m04_features_df['group']  # 标签: control/mci/ad

# 定义特征组合
combinations = {
    'Literature_Top4': ['avg_fixation_duration', 'kw_ratio_frame',
                        'avg_saccade_amplitude', 'total_fixations'],
    'Actual_Top4': actual_top4,  # 从实验1获得
    'Random_4': random.sample(M04_FEATURES, 4),
    'Full_9': M04_FEATURES
}

# 对比实验
results = []
for comb_name, features in combinations.items():
    X = m04_features_df[features]

    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 5折交叉验证
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    scores = cross_val_score(clf, X_scaled, y, cv=5, scoring='accuracy')

    results.append({
        'combination': comb_name,
        'features': features,
        'dimensions': len(features),
        'mean_accuracy': scores.mean(),
        'std_accuracy': scores.std(),
        'scores': scores.tolist()
    })

    print(f"{comb_name}: {scores.mean():.3f} ± {scores.std():.3f}")

# 排序
results_df = pd.DataFrame(results).sort_values('mean_accuracy', ascending=False)

# 统计检验: Actual vs Literature
from scipy.stats import ttest_rel
actual_scores = results_df[results_df['combination']=='Actual_Top4']['scores'].values[0]
lit_scores = results_df[results_df['combination']=='Literature_Top4']['scores'].values[0]

t_stat, p_value = ttest_rel(actual_scores, lit_scores)

print(f"\nActual vs Literature t-test:")
print(f"  t = {t_stat:.3f}, p = {p_value:.4f}")
print(f"  结论: {'显著差异' if p_value < 0.05 else '无显著差异'}")

# 保存报告
report = {
    'date': datetime.now().isoformat(),
    'results': results,
    'best_combination': results_df.iloc[0]['combination'],
    'statistical_test': {
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    },
    'recommendation': results_df.iloc[0]['features']
}

with open('data/06_features/validation/feature_combination_validation.json', 'w') as f:
    json.dump(report, f, indent=2)
```

### 4.3 验证决策矩阵

**决策规则**:

| 条件 | 决策 |
|------|------|
| 文献Top-4与实际Top-4一致性 ≥ 75% | ✅ 使用文献Top-4 |
| 文献Top-4与实际Top-4一致性 < 75% | ⚠️ 使用实际Top-4,更新设计文档 |
| 实际Top-4性能显著优于文献Top-4 (p<0.05) | ✅ 使用实际Top-4 |
| Module05 Top-6中2D特征 > 4个 | ⚠️ 考虑平衡1D和2D特征 |
| 某个特征在所有实验中都表现差 | ❌ 从候选中移除 |

---

## 5. 审核流程

### 5.1 流程图

```
┌────────────────────────────────────────────────────────┐
│              Module06 审核流程 (7天)                     │
└────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼────┐                    ┌────▼────┐
    │ Day 1-2 │                    │ Day 3-4 │
    │技术审核  │                    │业务审核  │
    └────┬────┘                    └────┬────┘
         │                               │
         │  ┌──────────────┐            │
         │  │ 正态性检验    │            │
         │  │ 方差齐性检验  │            │
         │  │ 公式验证      │            │
         │  └──────────────┘            │
         │                        ┌─────▼─────┐
         │                        │文献调研    │
         │                        │专家访谈    │
         │                        │临床解释    │
         │                        └───────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                    ┌────▼────┐
                    │ Day 5-7 │
                    │数据验证  │
                    └────┬────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         ┌────▼────┐          ┌────▼────┐
         │实验1:    │          │实验2:    │
         │M04敏感度 │          │M05敏感度 │
         └────┬────┘          └────┬────┘
              │                     │
              └──────────┬──────────┘
                         │
                    ┌────▼────┐
                    │实验3:    │
                    │性能对比  │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │审核报告  │
                    │+ 改进建议│
                    └─────────┘
```

### 5.2 时间安排

| 日期 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| **Day 1** | 技术审核 - 统计方法验证 | 数据科学家 | 正态性/方差齐性检验报告 |
| **Day 2** | 技术审核 - 算法&架构 | 算法工程师 | 公式优化建议,架构审查报告 |
| **Day 3** | 业务审核 - 文献调研 | Research Analyst | 文献支持表 |
| **Day 4** | 业务审核 - 专家访谈 | Clinical Lead | 专家意见汇总 |
| **Day 5** | 数据验证 - 实验1 | Data Analyst | M04敏感度验证报告 |
| **Day 6** | 数据验证 - 实验2 | Data Analyst | M05敏感度验证报告 |
| **Day 7** | 数据验证 - 实验3 + 报告 | All | 综合审核报告 |

---

## 6. 审核检查清单

### 6.1 技术审核检查清单

- [ ] **统计方法**
  - [ ] 正态性检验通过率 > 70%
  - [ ] 方差齐性检验通过率 > 70%
  - [ ] Bonferroni校正合理性确认
  - [ ] Effect Size计算公式验证
  - [ ] CV异常值处理策略确认

- [ ] **算法设计**
  - [ ] 敏感度得分公式权重合理性
  - [ ] 归一化方法正确性
  - [ ] 特征选择策略科学性
  - [ ] 边界条件处理 (缺失值、异常值)

- [ ] **系统架构**
  - [ ] 5层架构依赖方向检查
  - [ ] 缓存策略合理性
  - [ ] 错误处理完备性
  - [ ] 性能基准达标 (延迟<1s, 吞吐>100/min, 内存<2GB)

### 6.2 业务审核检查清单

- [ ] **临床意义**
  - [ ] 9个Module04特征文献支持 (每个≥2篇)
  - [ ] AD/MCI变化方向确认
  - [ ] 混淆因素识别
  - [ ] 专家访谈完成 (≥2位临床专家)

- [ ] **应用场景**
  - [ ] 策略A适用场景明确
  - [ ] 策略B适用场景明确
  - [ ] 是否需要第3种策略
  - [ ] 临床可解释性验证

### 6.3 数据验证检查清单

- [ ] **实验执行**
  - [ ] 实验1: M04敏感度计算完成
  - [ ] 实验2: M05敏感度计算完成
  - [ ] 实验3: 特征组合性能对比完成

- [ ] **结果分析**
  - [ ] 文献推荐 vs 实际Top-4一致性 > 70%
  - [ ] Top-6 RQA特征确定
  - [ ] 特征类型分布合理 (1D vs 2D)
  - [ ] 性能提升显著性检验 (p<0.05)

- [ ] **文档更新**
  - [ ] MODULE06设计文档更新 (如有调整)
  - [ ] 验证报告归档
  - [ ] 审核结论记录

---

## 7. 数据验证实验

### 7.1 实验环境准备

```bash
# 创建验证目录
mkdir -p data/06_features/validation

# 检查数据完整性
python -c "
from pathlib import Path
import pandas as pd

# 检查Module04数据
m04_cache = Path('data/04_features/cache/latest_analysis.json')
if m04_cache.exists():
    print('✅ Module04缓存存在')
else:
    print('❌ Module04缓存缺失,请先运行Module04分析')

# 检查Module05数据
m05_dir = Path('data/05_rqa_analysis')
if m05_dir.exists():
    param_dirs = list(m05_dir.glob('m*_tau*'))
    print(f'✅ Module05数据: {len(param_dirs)}个参数组合')
else:
    print('❌ Module05数据缺失')
"
```

### 7.2 实验执行脚本

**主实验脚本**: `scripts/validation/run_all_experiments.py`

```python
"""
Module06 数据验证实验主脚本
执行全部3个实验,生成综合报告
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

def run_experiment_1():
    """实验1: Module04敏感度验证"""
    print("=" * 60)
    print("实验1: Module04特征敏感度验证")
    print("=" * 60)

    from scripts.validation.experiment_m04_sensitivity import main as exp1_main
    result = exp1_main()

    print(f"\n✅ 实验1完成")
    print(f"  一致性: {result['consistency']:.0%}")
    print(f"  文献Top-4: {result['literature_top4']}")
    print(f"  实际Top-4: {result['actual_top4']}")

    return result

def run_experiment_2():
    """实验2: Module05敏感度验证"""
    print("\n" + "=" * 60)
    print("实验2: Module05 RQA特征敏感度验证")
    print("=" * 60)

    from scripts.validation.experiment_m05_sensitivity import main as exp2_main
    result = exp2_main()

    print(f"\n✅ 实验2完成")
    print(f"  Top-6特征: {result['top6_features']}")
    print(f"  特征类型分布: {result['feature_type_distribution']}")

    return result

def run_experiment_3(m04_result):
    """实验3: 特征组合性能验证"""
    print("\n" + "=" * 60)
    print("实验3: 特征组合分类性能对比")
    print("=" * 60)

    from scripts.validation.experiment_feature_combination import main as exp3_main
    result = exp3_main(actual_top4=m04_result['actual_top4'])

    print(f"\n✅ 实验3完成")
    print(f"  最佳组合: {result['best_combination']}")
    print(f"  准确率: {result['results'][0]['mean_accuracy']:.3f}")

    return result

def generate_comprehensive_report(exp1_result, exp2_result, exp3_result):
    """生成综合审核报告"""
    report = {
        'meta': {
            'date': datetime.now().isoformat(),
            'version': 'v1.0',
            'status': 'completed'
        },
        'experiment_1_m04_sensitivity': exp1_result,
        'experiment_2_m05_sensitivity': exp2_result,
        'experiment_3_performance': exp3_result,
        'recommendations': {
            'module04_features': exp1_result.get('recommendation'),
            'module05_features': exp2_result['top6_features'],
            'strategy_a_dimensions': 4 + 6,  # M04 Top-4 + M05 Top-6
            'update_design_doc': exp1_result['consistency'] < 0.75
        },
        'next_steps': [
            '更新MODULE06_COMPREHENSIVE_DESIGN.md (如有调整)',
            '将实际Top-4/Top-6写入配置文件',
            '开始Phase 1开发: 敏感度分析实现'
        ]
    }

    # 保存
    output_file = Path('data/06_features/validation/comprehensive_report.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("综合审核报告")
    print("=" * 60)
    print(json.dumps(report['recommendations'], indent=2, ensure_ascii=False))
    print(f"\n报告已保存: {output_file}")

    return report

if __name__ == '__main__':
    print("Module06 数据验证实验套件")
    print("预计耗时: 30-60分钟 (取决于Module05敏感度分析)")
    print()

    # 执行实验
    exp1_result = run_experiment_1()
    exp2_result = run_experiment_2()
    exp3_result = run_experiment_3(exp1_result)

    # 生成报告
    report = generate_comprehensive_report(exp1_result, exp2_result, exp3_result)

    print("\n✅ 所有实验完成!")
```

---

## 8. 审核报告模板

### 8.1 综合审核报告结构

```markdown
# Module06 设计方案审核报告

**报告日期**: 2025-10-XX
**审核版本**: MODULE06_COMPREHENSIVE_DESIGN v2.0
**审核人员**:
  - 技术审核: [姓名], 数据科学家
  - 业务审核: [姓名], 临床专家
  - 数据验证: [姓名], 数据分析师

---

## 1. 审核摘要

| 审核维度 | 通过率 | 状态 | 关键问题数 |
|---------|-------|------|-----------|
| 技术审核 | 92% | ✅ 通过 | 2个P1问题 |
| 业务审核 | 85% | ✅ 通过 | 3个P2问题 |
| 数据验证 | 78% | ⚠️ 有调整 | 1个P0问题 |

**总体结论**: ✅ **方案可行,需小幅调整后进入开发**

---

## 2. 技术审核结果

### 2.1 统计方法

✅ **通过项**:
- 正态性检验通过率: 73% (≥70%阈值)
- 方差齐性检验通过率: 81%
- Effect Size计算公式验证正确

⚠️ **待改进项**:
1. **P1**: CV异常值处理 - 需添加下界保护 `max(CV, 1.0)`
2. **P1**: 综合评分公式 - 建议改为显式加权和

**改进建议**:
```python
# 原公式
score = (F × η²) / (1 + p) × (1 / (1 + CV/100))

# 改进公式
score = 0.3×F_norm + 0.3×η² + 0.2×(1-p) + 0.2×(1/CV_safe)
```

### 2.2 算法设计

✅ **通过项**:
- 双策略设计合理
- 特征选择流程清晰

⚠️ **待改进项**:
1. **P2**: 跨参数Top-6 RQA特征 - 建议添加分层选择确保特征多样性

### 2.3 系统架构

✅ **通过项**:
- 5层架构设计合理
- API接口设计完善

---

## 3. 业务审核结果

### 3.1 临床意义

✅ **文献支持**:
- avg_fixation_duration: 3篇文献,一致结论AD患者↑
- avg_saccade_amplitude: 2篇文献,一致结论AD患者↓

⚠️ **文献缺失**:
- kw_ratio_frame: 无直接文献支持,依赖数据验证

**专家意见** (2位神经科医生):
- ✅ avg_fixation_duration 和 avg_saccade_amplitude 临床价值高
- ⚠️ kw_ratio_frame 依赖ROI定义,可靠性待验证

### 3.2 应用场景

✅ 双策略覆盖主要场景

💡 **新增建议**: 考虑策略C (27维) 用于大型医院

---

## 4. 数据验证结果

### 4.1 实验1: Module04敏感度

**文献推荐Top-4**:
1. avg_fixation_duration
2. kw_ratio_frame
3. avg_saccade_amplitude
4. total_fixations

**实际数据Top-4**:
1. avg_fixation_duration (一致✅)
2. avg_saccade_amplitude (一致✅)
3. kw_ratio_frame (一致✅)
4. **total_saccades** (不一致❌)

**一致性**: 75% (3/4)

**决策**: ✅ **采用实际Top-4**

### 4.2 实验2: Module05敏感度

**实际Top-6 RQA特征**:
1. det-2d-xy (2D确定性)
2. rr-2d-xy (2D递归率)
3. ent-1d-x (1D-x熵)
4. det-1d-x (1D-x确定性)
5. ent-2d-xy (2D熵)
6. rr-1d-y (1D-y递归率)

**特征类型分布**:
- 1D-x: 2个
- 1D-y: 1个
- 2D-xy: 3个

**决策**: ✅ **采用实际Top-6**

### 4.3 实验3: 性能对比

| 组合 | 准确率 | 标准差 |
|------|--------|--------|
| Actual_Top4 | 0.782 | 0.023 |
| Literature_Top4 | 0.768 | 0.031 |
| Full_9 | 0.791 | 0.019 |

**t检验**: Actual vs Literature, p = 0.12 (无显著差异)

**决策**: ✅ 使用Actual_Top4 (略优且数据驱动)

---

## 5. 改进建议清单

| ID | 优先级 | 类别 | 问题描述 | 改进建议 | 负责人 |
|----|--------|------|---------|---------|--------|
| R1 | P0 | 数据验证 | 文献Top-4与实际不一致 | 更新设计文档,使用实际Top-4 | Tech Lead |
| R2 | P1 | 技术审核 | CV异常值处理缺失 | 添加`max(CV, 1.0)`保护 | Data Scientist |
| R3 | P1 | 技术审核 | 敏感度得分公式不直观 | 改为显式加权和 | Data Scientist |
| R4 | P2 | 业务审核 | kw_ratio_frame文献缺失 | 补充实际数据分析报告 | Research Analyst |
| R5 | P2 | 算法设计 | RQA特征选择单一策略 | 添加分层选择备选方案 | Algorithm Engineer |

---

## 6. 下一步行动

### 立即执行 (本周)
- [ ] **R1**: 更新MODULE06设计文档,替换文献Top-4为实际Top-4
- [ ] **R2**: 修改敏感度得分公式,添加CV保护
- [ ] **R3**: 重构公式为显式加权和

### 短期执行 (下周)
- [ ] **R4**: 补充kw_ratio_frame的数据分析报告
- [ ] **R5**: 设计RQA特征分层选择算法

### 长期跟踪
- [ ] 在Phase 1开发中验证改进方案
- [ ] 收集实际使用反馈,持续优化

---

## 7. 审核批准

| 角色 | 姓名 | 签名 | 日期 |
|------|------|------|------|
| 技术负责人 | [姓名] | _______ | 2025-10-XX |
| 业务负责人 | [姓名] | _______ | 2025-10-XX |
| 项目经理 | [姓名] | _______ | 2025-10-XX |

**批准意见**: ✅ **方案通过审核,批准进入开发阶段**
```

---

## 附录A: 审核工具清单

| 工具 | 用途 | 脚本路径 |
|------|------|---------|
| `check_normality.py` | 正态性检验 | `scripts/validation/` |
| `check_homogeneity.py` | 方差齐性检验 | `scripts/validation/` |
| `compare_corrections.py` | 多重比较校正对比 | `scripts/validation/` |
| `experiment_m04_sensitivity.py` | 实验1主脚本 | `scripts/validation/` |
| `experiment_m05_sensitivity.py` | 实验2主脚本 | `scripts/validation/` |
| `experiment_feature_combination.py` | 实验3主脚本 | `scripts/validation/` |
| `run_all_experiments.py` | 实验套件入口 | `scripts/validation/` |

---

**文档状态**: ✅ 完成
**最后更新**: 2025-10-10
**版本控制**: Git - docs/MODULE06_REVIEW_AND_VALIDATION_PLAN.md
