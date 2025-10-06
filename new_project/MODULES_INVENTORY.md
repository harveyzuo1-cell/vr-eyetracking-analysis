# 模块功能清单 - 详细分析

## 模块1: 数据可视化 (Module 1: Visualization)

### 当前实现位置
- **前端**: `visualization/static/modules/module1_visualization.html` (296行)
- **后端**: `visualization/enhanced_web_visualizer.py` 中的部分功能
- **主HTML**: `visualization/templates/enhanced_index.html` (8000-11500行)

### 核心功能
1. **眼动轨迹可视化**
   - 绘制注视点、扫视路径
   - ROI (兴趣区域) 叠加显示
   - 轨迹参数调节（粗细、颜色、样式）

2. **数据浏览**
   - 三组数据切换（Control/MCI/AD）
   - 受试者列表展示
   - 任务(Q1-Q5)切换

3. **MMSE分数显示**
   - 关联MMSE评分
   - 子问题得分明细
   - 认知水平标注

4. **交互功能**
   - 数据筛选（按组别、任务）
   - 参数实时调整
   - 图表导出

### 数据依赖
- **输入数据**:
  - `data/*/calibrated/*_calibrated.csv` (校准后眼动数据)
  - `data/MMSE_Score/*.csv` (MMSE评分)
  - `data/background_images/*.jpg` (背景图片)

- **输出数据**:
  - 实时生成的可视化图表（base64图片）

### API端点
```python
GET /api/visualize/<group>/<data_id>
GET /api/groups
GET /api/group/<group>/data
GET /api/mmse-scores/<group>
```

### 重构建议
- **前端**: 300行HTML + 独立JS模块
- **后端**: 拆分为3个文件
  - `api.py` (路由，50行)
  - `service.py` (业务逻辑，150行)
  - `renderer.py` (图表渲染，100行)

---

## 模块2: 数据导入 (Module 2: Data Import)

### 当前实现位置
- **前端**: `visualization/static/modules/module2_data_import.html` (219行)
- **后端**: `visualization/enhanced_web_visualizer.py` 中的上传功能

### 核心功能
1. **文件上传**
   - CSV文件上传
   - 格式验证
   - 批量上传

2. **数据预处理**
   - 列名标准化
   - 缺失值处理
   - 异常值检测

3. **数据保存**
   - 存储到指定目录
   - 自动分类（按组别）
   - 备份管理

### 数据流
```
原始CSV → 验证 → 预处理 → data/02_preprocessed/ → data/03_calibrated/
```

### 重构建议
- **前端**: 保持219行，简化UI
- **后端**: 3个文件
  - `api.py` (上传接口，50行)
  - `service.py` (处理逻辑，100行)
  - `preprocessor.py` (数据处理，150行)

---

## 模块3: RQA分析 (Module 3: RQA Analysis)

### 当前实现位置
- **前端**: `visualization/static/modules/module3_rqa_analysis.html` (210行)
- **后端**: `visualization/rqa_api_extension.py` (407行)
- **分析器**: `analysis/rqa_analyzer.py`

### 核心功能
1. **参数配置**
   - m (嵌入维度)
   - tau (时间延迟)
   - eps (距离阈值)
   - lmin (最小线长)

2. **RQA指标计算**
   - RR (递归率)
   - DET (确定性)
   - LAM (层流性)
   - ENTR (熵)
   - L_mean, L_max (线长统计)

3. **结果展示**
   - RQA指标表格
   - 递归图可视化
   - 结果保存

### 数据依赖
- **输入**: `data/03_calibrated/` 校准数据
- **输出**: `data/04_features/rqa/` RQA特征

### API端点
```python
POST /api/rqa-analysis/analyze
GET /api/rqa-analysis/results/<result_id>
```

### 重构建议
- **后端**: 拆分为4个文件
  - `api.py` (50行)
  - `service.py` (120行)
  - `rqa_calculator.py` (200行，核心算法)
  - `rqa_calculator_gpu.py` (200行，GPU优化版本)

---

## 模块4: 事件分析 (Module 4: Event Analysis)

### 当前实现位置
- **前端**: `visualization/static/modules/module4_event_analysis.html` (114行)
- **后端**: `visualization/event_api_extension.py` (250行)
- **分析器**: `analysis/event_analyzer.py`

### 核心功能
1. **事件检测**
   - 注视 (Fixation)
   - 扫视 (Saccade)
   - 使用IVT算法（速度阈值）

2. **事件统计**
   - 注视时长、次数
   - 扫视幅度、速度
   - ROI访问统计

3. **结果查看**
   - 事件序列表格
   - 统计图表
   - 按组别对比

### 数据流
```
校准数据 → 计算速度 → IVT分类 → 事件序列 → 统计分析
```

### 重构建议
- **后端**: 3个文件
  - `api.py` (50行)
  - `service.py` (100行)
  - `detector.py` (150行，事件检测算法)

---

## 模块5: RQA批处理 (Module 5: RQA Pipeline)

### 当前实现位置
- **前端**: `visualization/static/modules/module5_rqa_pipeline.html` (422行)
- **后端**: `visualization/rqa_pipeline_api.py` (2017行！！！)
- **GPU实现**: 集成在同一文件中

### 核心功能
1. **参数网格生成**
   - m: [2, 3, 4, ...]
   - tau: [1, 2, 3, ...]
   - eps: [0.05, 0.06, ...]
   - lmin: [2, 3, 4, ...]
   - 组合总数可达数千

2. **批量执行**
   - 所有参数组合的RQA分析
   - 进度跟踪
   - 结果存储

3. **GPU并行加速**
   - CuPy实现
   - 批处理优化
   - 从142小时 → 约6小时

4. **结果管理**
   - 参数历史记录
   - 结果可视化
   - 导出功能

### 数据流
```
参数网格 → 加载所有数据 → GPU并行计算 → 保存结果 → 生成元数据
```

### 重构建议（重点！）
- **后端**: 必须拆分为至少5个文件
  - `api.py` (100行，路由)
  - `service.py` (150行，业务逻辑)
  - `batch_processor.py` (250行，批处理逻辑)
  - `gpu_executor.py` (300行，GPU并行执行)
  - `result_manager.py` (150行，结果管理)

---

## 模块6: 综合特征提取 (Module 6: Comprehensive Feature Extraction)

### 当前实现位置
- **前端**: `visualization/static/modules/module6_comprehensive_feature.html` (229行)
- **后端**: `visualization/feature_extraction_api.py` (623行)

### 核心功能
1. **多源特征整合**
   - RQA特征
   - 事件分析特征
   - 统计特征

2. **特征归一化**
   - Min-Max归一化
   - Z-score标准化

3. **特征导出**
   - CSV格式
   - 包含元数据

### 重构建议
- **后端**: 4个文件
  - `api.py` (50行)
  - `service.py` (120行)
  - `extractors/` (子目录)
    - `rqa_features.py` (100行)
    - `event_features.py` (100行)
    - `statistical_features.py` (80行)

---

## 模块7: 真实数据整合 (Module 7: Real Data Integration)

### 当前实现位置
- **后端**: `visualization/real_data_integration_api.py` (586行)

### 核心功能
1. **数据源整合**
   - 眼动数据
   - MMSE分数
   - 受试者信息

2. **数据关联**
   - 按subject_id关联
   - 时间序列对齐

3. **导出功能**
   - 整合后的完整数据集

### 重构建议
- **后端**: 3个文件
  - `api.py` (50行)
  - `service.py` (150行)
  - `data_merger.py` (150行)

---

## 模块8: MMSE对比分析 (Module 8: MMSE Analysis)

### 当前实现位置
- **后端**: `visualization/mmse_api_extension.py` (214行)

### 核心功能
1. **MMSE数据加载**
   - 三组数据 (Control/MCI/AD)
   - 子问题分数详情

2. **分数计算**
   - 各题目得分
   - 总分计算
   - 认知水平评估

3. **对比分析**
   - 组间比较
   - 任务间比较

### 数据源
- `data/MMSE_Score/控制组.csv`
- `data/MMSE_Score/轻度认知障碍组.csv`
- `data/MMSE_Score/阿尔兹海默症组.csv`

### 重构建议
- **数据格式统一**: 合并为单个 `mmse_scores.csv`
- **后端**: 3个文件
  - `api.py` (50行)
  - `service.py` (80行)
  - `mmse_loader.py` (80行)

---

## 模块9: 机器学习预测 (Module 9: ML Prediction)

### 当前实现位置
- **后端**: `visualization/ml_prediction_api.py` (2021行！！！)

### 核心功能
1. **模型加载**
   - MLP分类器
   - 预训练权重加载

2. **特征预处理**
   - 特征选择
   - 归一化

3. **预测**
   - 认知状态分类 (Control/MCI/AD)
   - 置信度输出

4. **可视化**
   - 混淆矩阵
   - 特征重要性

### 重构建议
- **后端**: 拆分为6个文件
  - `api.py` (100行)
  - `service.py` (150行)
  - `models/mlp_model.py` (200行)
  - `models/model_loader.py` (100行)
  - `preprocessor.py` (150行)
  - `visualizer.py` (100行)

---

## 模块10: Eye-Index综合评估 (Module 10: Eye-Index)

### 当前实现位置
- **后端API**: `visualization/module10_eye_index/api.py` (452行)
- **后端训练**: `backend/m10_training/` (多个文件)
- **后端服务**: `backend/m10_service/` (多个文件)
- **数据准备**: `backend/m10_data_prep/`
- **评估**: `backend/m10_evaluation/`
- **关联分析**: `backend/m10e_correlation/`

### 子模块结构

#### 10A: 数据准备
- **功能**: 准备Eye-Index训练数据
- **文件**: `backend/m10_data_prep/`

#### 10B: 模型训练
- **功能**: MLP模型训练
- **文件**: `backend/m10_training/`
- **组件**:
  - `trainer.py` - 训练器
  - `model.py` - 模型定义
  - `dataset.py` - 数据集
  - `callbacks.py` - 训练回调

#### 10C: 模型服务
- **功能**: 模型推理服务
- **文件**: `backend/m10_service/`
- **组件**:
  - `predict.py` - 预测逻辑
  - `loader.py` - 模型加载
  - `metrics.py` - 评估指标

#### 10D: 性能评估
- **功能**: 模型性能分析
- **文件**: `backend/m10_evaluation/`

#### 10E: 关联性可视化
- **功能**: 特征-认知关联分析
- **文件**: `backend/m10e_correlation/`

### 重构建议
保持当前的子模块结构，但统一到新项目中：
```
src/modules/module10_eye_index/
├── api.py (100行)
├── service.py (150行)
└── submodules/
    ├── data_preparation.py
    ├── model_training.py
    ├── model_service.py
    ├── performance_eval.py
    └── correlation_viz.py
```

---

## 数据流总览

```
原始CSV数据
    ↓
[模块2] 数据导入 → 预处理数据
    ↓
校准 → 校准数据
    ↓
├─[模块1] 可视化查看
├─[模块3] RQA分析 → RQA特征
├─[模块4] 事件分析 → 事件特征
├─[模块5] RQA批处理 → 大量RQA结果
└─[模块8] MMSE关联
    ↓
[模块6] 特征提取 → 综合特征集
    ↓
[模块7] 数据整合 → 完整数据集
    ↓
[模块9] ML预测 → 分类结果
    ↓
[模块10] Eye-Index → 综合评估指标
```

---

## 技术债务清单

### 高优先级
1. ❌ **单文件过大**: `enhanced_index.html` 19,504行
2. ❌ **API文件过大**: `rqa_pipeline_api.py` 2,017行
3. ❌ **ML API过大**: `ml_prediction_api.py` 2,021行
4. ❌ **数据命名不统一**: ad3q1, n1q1, m6q1

### 中优先级
5. ❌ **MMSE数据分散**: 3个中文文件名
6. ❌ **配置硬编码**: 路径写死在代码中
7. ❌ **缺少测试**: 无单元测试
8. ❌ **日志不规范**: print调试信息

### 低优先级
9. ❌ **文档过时**: 部分MD文档不同步
10. ❌ **版本控制**: 无数据版本管理

---

## 下一步行动计划

### 第1步: 立即行动（今天）
1. ✅ 创建重构方案文档
2. ✅ 创建模块清单文档
3. ⬜ 创建数据迁移计划
4. ⬜ 设计配置文件结构

### 第2步: 本周完成
1. ⬜ 搭建新项目基础架构
2. ⬜ 实现核心工具类
3. ⬜ 编写数据迁移脚本
4. ⬜ 开始模块1迁移

### 第3步: 两周内完成
1. ⬜ 完成模块1-3迁移
2. ⬜ 编写单元测试
3. ⬜ 文档同步更新
