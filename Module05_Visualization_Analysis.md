# Module05 RQA可视化系统分析与改进建议

## 一、当前可视化系统解析

### 1.1 当前图片到底显示什么？

**重要理解：当前可视化图片是「聚合图」，不是单个任务的图**

当你在界面上选择一个参数组合（例如 m=2, tau=1, eps=0.05, lmin=2）后，生成的4张图显示的是：

```
数据范围：3组 × 20人 × 5任务 = 300条记录的聚合分析
- Control组：20人 × 5任务 = 100条数据
- MCI组：20人 × 5任务 = 100条数据
- AD组：20人 × 5任务 = 100条数据
```

**不是单个q的图，而是所有q1-q5混合在一起的统计分析！**

#### 图1: RQA指标箱线图 (`rqa_metrics_boxplot.png`)
```
目的：对比三组在核心RQA指标上的差异
- X轴：RR (递归率), DET (确定性), ENT (熵)
- Y轴：指标数值
- 每个指标显示3个箱子：Control, MCI, AD
- 数据来源：每组100条记录（20人×5任务）的混合

解读意义：
✓ 查看AD组的RR是否显著低于Control组（反映注视模式简化）
✓ 查看MCI组是否介于两者之间（渐进式认知退化）
✓ 箱体大小反映组内变异性
```

#### 图2: 相关性热力图 (`correlation_heatmap.png`)
```
目的：发现RQA特征之间的关联模式
- 显示所有RQA特征（x_RR, y_RR, combined_RR, x_DET等）的Pearson相关系数
- 数据来源：300条记录的全局相关性矩阵（不区分组别）

解读意义：
✓ 识别冗余特征（高度相关 r>0.9 的特征对）
✓ 发现独立特征（低相关特征更有价值）
✓ 指导特征选择和降维
```

#### 图3: 显著性特征 (`significant_features.png`)
```
目的：识别哪些RQA特征能显著区分三组
- Y轴：通过ANOVA检验的特征名称（p < 0.05）
- X轴：F统计量（值越大，组间差异越显著）
- 数据来源：对300条记录进行单因素ANOVA

解读意义：
✓ 找到最能区分Control/MCI/AD的特征
✓ 为机器学习特征选择提供依据
✓ 验证假设（例如：combined_DET应该显著，因为认知退化影响整体扫视模式）
```

#### 图4: 复杂度小提琴图 (`complexity_violin.png`)
```
目的：展示RQA复杂度指标的分布密度
- 显示特征：x_ENT, y_ENT, combined_ENT（或其他复杂度指标）
- 小提琴形状：宽=数据密集区域，窄=数据稀疏区域
- 数据来源：每组100条记录

解读意义：
✓ 查看分布形态（单峰/双峰/偏态）
✓ 识别异常值
✓ 对比组间分布差异（不仅是均值，还有形状）
```

---

### 1.2 当前系统的局限性

**问题1：任务混淆 (Task Confounding)**
```
❌ 当前问题：q1-q5的数据全部混在一起
   - q1可能是简单任务，RR值高
   - q5可能是复杂任务，RR值低
   - 混合分析会掩盖任务特异性模式

示例场景：
  Control组在q1的RR=0.8，q5的RR=0.4
  AD组在q1的RR=0.7，q5的RR=0.35
  → 混合后可能显示"无显著差异"，但分任务分析会发现显著差异
```

**问题2：RQA参数选择盲目**
```
❌ 当前问题：不知道哪个参数组合最优
   - 有3264种参数组合
   - 每种组合生成不同的RQA特征值
   - 缺乏系统化方法选择最佳参数

需要回答：
  ❓ 哪个eps值能最大化组间差异？
  ❓ m和tau如何影响分类性能？
  ❓ 不同任务是否需要不同参数？
```

**问题3：缺少ROI维度分析**
```
❌ 当前问题：没有利用ROI（兴趣区域）信息
   - Module02提供了ROI注视统计
   - Module04提供了事件特征（扫视、注视）
   - 但Module05的RQA分析是全局的，没有ROI粒度

潜在价值：
  ✓ 不同ROI的RQA模式可能不同（关键区域 vs 背景区域）
  ✓ AD患者可能在关键区域表现出更低的递归率
  ✓ ROI切换模式的RQA分析可能更有判别力
```

---

## 二、高级分析建议：ROI粒度的RQA分析

### 2.1 核心思路

**从全局RQA → 分层RQA**

```
Level 1: 全局RQA（当前实现）
  输入：完整眼动轨迹 (x, y, t)
  输出：整体递归模式

Level 2: 任务分层RQA（建议新增）
  输入：按任务q1-q5分别计算
  输出：每个任务的RQA特征 → 发现任务特异性模式

Level 3: ROI分层RQA（高级功能）
  输入：仅提取落在特定ROI内的注视点
  输出：每个ROI的RQA特征 → 发现区域特异性模式
```

---

### 2.2 具体实现方案

#### 方案A：任务分层可视化（优先级：高）

**实现步骤：**

1. **修改数据聚合逻辑**
   - 当前：`enriched_features.csv` 包含所有任务混合
   - 改进：生成 `enriched_features_q1.csv`, `enriched_features_q2.csv`, ...

2. **新增UI控件**
   ```jsx
   // 在VisualizationPanel.jsx中新增
   <Select placeholder="选择任务" onChange={setSelectedTask}>
     <Option value="all">全部任务（混合）</Option>
     <Option value="q1">任务1 (q1)</Option>
     <Option value="q2">任务2 (q2)</Option>
     <Option value="q3">任务3 (q3)</Option>
     <Option value="q4">任务4 (q4)</Option>
     <Option value="q5">任务5 (q5)</Option>
   </Select>
   ```

3. **动态生成统计图**
   - 当选择"q1"时，重新运行Step 4+5，仅使用q1数据（60条记录）
   - 生成 `rqa_metrics_boxplot_q1.png`
   - 生成 `significant_features_q1.png`

**分析价值：**
```
✓ 发现任务难度对RQA的影响
✓ 识别哪个任务最能区分AD/MCI/Control
✓ 为临床诊断选择最优任务
```

---

#### 方案B：ROI粒度RQA分析（优先级：中）

**实现步骤：**

1. **数据整合：从Module02获取ROI信息**
   ```python
   # 读取ROI配置（来自Module02）
   roi_config = load_roi_config(task_id='q1', version='v2')
   # 示例ROI：
   # - roi_1: 关键区域（指令区域）
   # - roi_2: 背景区域
   # - roi_3: 干扰区域
   ```

2. **注视点过滤：仅保留特定ROI内的点**
   ```python
   def filter_gaze_by_roi(gaze_data, roi_polygon):
       """
       过滤眼动数据，仅保留落在ROI内的注视点
       """
       filtered_points = []
       for point in gaze_data:
           if point_in_polygon(point['x'], point['y'], roi_polygon):
               filtered_points.append(point)
       return filtered_points
   ```

3. **分ROI计算RQA**
   ```python
   # 为每个ROI单独计算RQA
   for roi_id, roi_polygon in roi_config.items():
       roi_gaze = filter_gaze_by_roi(gaze_data, roi_polygon)
       roi_rqa = calculate_rqa(roi_gaze, params)

       # 保存为 subject_id_task_id_roi1_rqa.json
   ```

4. **新增可视化维度**
   ```
   箱线图：对比同一ROI在三组间的差异
   热力图：不同ROI的RQA特征相关性
   显著性分析：哪个ROI的RQA最能区分组别？
   ```

**分析价值：**
```
✓ 发现AD患者在关键区域的注视模式简化
✓ 验证假设：MCI患者在干扰区域停留更久（更高的RR）
✓ 为ROI设计提供反馈（哪些ROI最有判别力）
```

**挑战：**
```
⚠️ ROI内注视点可能很少（<10个点），RQA不稳定
⚠️ 需要设置最小点数阈值（例如：至少20个点才计算RQA）
⚠️ 计算量增加：300文件 × 5任务 × N个ROI × 3264参数
```

---

#### 方案C：参数优化分析（优先级：高）

**目的：从3264个参数组合中找到最优参数**

**实现步骤：**

1. **定义优化目标**
   ```python
   # 目标1：最大化组间F统计量（分类能力）
   def objective_function(params):
       rqa_features = load_rqa_results(params)
       f_stats = anova_analysis(rqa_features, groups=['control', 'mci', 'ad'])
       return np.mean(f_stats)  # 返回平均F值

   # 目标2：最大化显著特征数量
   def objective_function_v2(params):
       rqa_features = load_rqa_results(params)
       p_values = anova_analysis(rqa_features)
       return np.sum(p_values < 0.05)  # 返回显著特征数
   ```

2. **批量评估参数**
   ```python
   # 遍历所有3264个参数组合
   param_scores = []
   for params in all_param_combinations:
       score = objective_function(params)
       param_scores.append({
           'params': params,
           'f_stat_mean': score,
           'significant_count': objective_function_v2(params)
       })

   # 排序找到Top 10参数
   top_params = sorted(param_scores, key=lambda x: x['f_stat_mean'], reverse=True)[:10]
   ```

3. **可视化参数影响**
   ```
   图1：参数vs F统计量散点图
     - X轴：eps值，Y轴：平均F统计量，颜色：m值

   图2：参数组合排名表
     | Rank | m | tau | eps | lmin | Avg F-stat | Sig. Features |
     |------|---|-----|-----|------|------------|---------------|
     | 1    | 3 | 2   | 0.08| 2    | 45.6       | 12            |
     | 2    | 2 | 1   | 0.05| 2    | 42.3       | 10            |

   图3：参数敏感性分析
     - 显示哪个参数对结果影响最大
   ```

**分析价值：**
```
✓ 科学选择RQA参数（不再盲目）
✓ 发现参数-任务交互效应（q1最优参数 ≠ q5最优参数）
✓ 减少计算量（未来只需计算Top 10参数）
```

---

## 三、推荐实施路线图

### 阶段1：基础改进（1-2天）

**任务1.1：添加任务分层可视化**
- [ ] 修改Step 4统计分析，支持按task_id筛选
- [ ] 在VisualizationPanel添加任务选择下拉框
- [ ] 生成分任务的统计图（q1-q5 + all）

**任务1.2：参数优化分析**
- [ ] 实现参数评估脚本 `evaluate_params.py`
- [ ] 生成参数排名报告
- [ ] 在UI中高亮推荐参数

**预期成果：**
```
✓ 能回答："哪个任务最能区分AD？" → 答：q3的平均F统计量最高
✓ 能回答："最优参数是什么？" → 答：m=3, tau=2, eps=0.08, lmin=2
✓ 可视化更清晰（不再混淆任务）
```

---

### 阶段2：高级功能（3-5天）

**任务2.1：ROI粒度RQA分析**
- [ ] 整合Module02的ROI配置
- [ ] 实现ROI注视点过滤
- [ ] 计算分ROI的RQA特征
- [ ] 新增ROI维度可视化

**任务2.2：交互式参数探索**
- [ ] 实现参数vs性能的交互式图表（Plotly）
- [ ] 支持实时调整参数查看效果
- [ ] 添加参数推荐系统

**预期成果：**
```
✓ 能回答："AD患者在关键区域的RR比Control低多少？"
✓ 能回答："背景区域的RQA有判别力吗？"
✓ 找到最优ROI + 最优参数的组合
```

---

### 阶段3：机器学习集成（可选，5-7天）

**任务3.1：特征工程**
- [ ] 合并Module04事件特征 + Module05 RQA特征
- [ ] 添加ROI级别特征
- [ ] 特征标准化和降维

**任务3.2：分类模型训练**
- [ ] 实现Random Forest / SVM / XGBoost分类器
- [ ] 交叉验证评估
- [ ] 特征重要性分析

**任务3.3：诊断支持系统**
- [ ] 输入眼动数据 → 输出AD风险评分
- [ ] 可解释性报告（哪些特征贡献最大）

---

## 四、当前系统的正确使用姿势

### 4.1 如何解读现有可视化

**场景1：初步探索（当前状态）**
```
1. 在"批量执行"中提交任务，生成3264个参数的RQA结果
2. 在"结果查看"中选择一个参数组合（例如m=2, tau=1, eps=0.05）
3. 查看4张图：
   - 箱线图：哪个指标能区分三组？（如DET显著，RR不显著）
   - 热力图：哪些特征高度相关？（如x_RR vs y_RR = 0.85，可能冗余）
   - 显著性：哪些特征通过ANOVA？（假设combined_DET, x_ENT显著）
   - 小提琴图：分布是否正态？有无异常值？

4. 下载CSV文件：
   - `enriched_features.csv`：用于后续机器学习
   - `group_comparison.csv`：查看p值和效应量
```

**注意：这些图是300条记录的混合分析，包含所有q1-q5任务！**

---

**场景2：参数对比（手动方法）**
```
问题：m=2好还是m=3好？

步骤：
1. 选择参数组合1（m=2, tau=1, eps=0.05）
2. 查看显著性特征数量 → 假设10个显著特征
3. 下载 `group_comparison.csv`，记录平均F统计量 → 假设F_avg=35.2

4. 选择参数组合2（m=3, tau=1, eps=0.05）
5. 查看显著性特征数量 → 假设12个显著特征
6. 下载 `group_comparison.csv`，记录平均F统计量 → 假设F_avg=42.1

结论：m=3参数更优（更多显著特征，更高F统计量）
```

**问题：手动对比3264个参数太慢 → 需要自动化参数评估（方案C）**

---

### 4.2 数据文件说明

| 文件名 | 行数 | 列数 | 内容 |
|--------|------|------|------|
| `enriched_features.csv` | 300 | ~30 | 每行=一个受试者的一个任务<br>列=RQA特征 + Module04特征 + MMSE分数 |
| `descriptive_stats.csv` | 3 | ~30 | 每行=一个组别（Control/MCI/AD）<br>列=每个特征的均值、标准差、中位数 |
| `group_comparison.csv` | ~25 | 4 | 每行=一个RQA特征<br>列=F统计量、p值、效应量 |
| `correlation_matrix.csv` | ~25 | ~25 | RQA特征之间的相关系数矩阵 |

**enriched_features.csv 结构示例：**
```csv
subject_id,task_id,group,x_RR,y_RR,combined_RR,x_DET,y_DET,combined_DET,...,MMSE,fixation_count,saccade_velocity
control_1,q1,control,0.45,0.48,0.52,0.78,0.81,0.85,...,29,120,45.2
control_1,q2,control,0.42,0.46,0.50,0.75,0.79,0.82,...,29,135,48.7
...
ad_20,q5,ad,0.28,0.30,0.35,0.55,0.58,0.62,...,18,80,32.1
```

**每个受试者有5行（5个任务），共300行**

---

## 五、立即行动建议

### 优先级排序

**立即开始（今天）：**
1. ✅ **参数优化分析**
   - 创建 `src/modules/module05_rqa/utils/param_evaluator.py`
   - 实现参数评估和排名功能
   - 生成推荐参数报告

2. ✅ **任务分层可视化**
   - 修改 `statistical_analysis.py` 支持task_id过滤
   - 在UI添加任务选择器
   - 生成分任务统计图

**本周完成：**
3. 📊 **改进可视化说明**
   - 在每张图上添加标题说明数据范围（"基于300条记录，包含q1-q5"）
   - 添加Tooltip解释各指标含义

4. 📚 **生成分析报告模板**
   - 自动生成PDF报告，包含：
     - 参数选择依据
     - 主要发现（哪些特征显著）
     - 推荐的后续分析方向

**下周计划：**
5. 🎯 **ROI粒度分析（如果时间允许）**
   - 整合Module02 ROI数据
   - 实现分ROI的RQA计算

---

## 六、总结

### 当前系统做了什么
- ✅ 计算了3264种参数组合下的RQA特征（300文件 × 3264参数 = 979,200次计算）
- ✅ 为每个参数组合生成了4张统计图（基于300条混合数据）
- ✅ 提供了CSV数据供下载和二次分析

### 当前系统的不足
- ❌ 任务混淆：q1-q5数据混在一起，掩盖任务特异性
- ❌ 参数选择盲目：不知道哪个参数最优
- ❌ 缺少ROI维度：没有利用空间位置信息

### 下一步应该做什么
1. **短期（本周）**：添加任务分层 + 参数评估
2. **中期（2周内）**：ROI粒度分析
3. **长期（1个月）**：机器学习分类器

### 关键问题的答案

**Q: 当前的图是q几的图？**
A: 不是单个q的图，是q1-q5全部混合的聚合统计图（300条记录）

**Q: 可视化的目的是什么？**
A:
1. 发现哪些RQA特征能区分Control/MCI/AD
2. 识别冗余特征（高相关性）
3. 验证假设（AD患者的递归率更低）
4. 为后续机器学习提供特征选择依据

**Q: 如何分析不同ROI参数？**
A: 需要新增功能（方案B），当前系统不支持ROI粒度分析

---

**需要我立即开始实现哪个方案？**
- 推荐先做：**方案A（任务分层）+ 方案C（参数优化）**
- 因为这两个改进最直接，能快速提升分析深度
