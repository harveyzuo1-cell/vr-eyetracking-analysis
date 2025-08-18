# VR眼动数据分析系统 - 项目结构与开发指南

## 📁 项目目录结构

### 🎯 **核心数据目录**
```
data/
├── background_images/          # 📸 认知任务背景图片 (Q1-Q5.jpg)
│   ├── Q1.jpg                 # 任务1: 词汇识别
│   ├── Q2.jpg                 # 任务2: 语义理解  
│   ├── Q3.jpg                 # 任务3: 认知负荷
│   ├── Q4.jpg                 # 任务4: 执行功能
│   └── Q5.jpg                 # 任务5: 综合评估
├── control_raw/               # 🏥 健康对照组原始txt数据
├── control_processed/         # 🏥 健康对照组预处理csv数据
├── control_calibrated/        # 🏥 健康对照组校准csv数据（推荐使用）
├── mci_raw/                   # 🧠 轻度认知障碍组原始txt数据
├── mci_processed/             # 🧠 轻度认知障碍组预处理csv数据
├── mci_calibrated/            # 🧠 轻度认知障碍组校准csv数据（推荐使用）
├── ad_raw/                    # 🔬 阿尔茨海默症组原始txt数据
├── ad_processed/              # 🔬 阿尔茨海默症组预处理csv数据
├── ad_calibrated/             # 🔬 阿尔茨海默症组校准csv数据（推荐使用）
├── event_analysis_results/    # 📊 眼动事件分析结果
│   ├── All_Events.csv         # 所有眼动事件（注视、扫视）
│   └── All_ROI_Summary.csv    # ROI统计摘要
├── rqa_results/               # 🔄 RQA递归量化分析结果
│   └── [参数化目录结构]        # 基于分析参数的组织方式
└── rqa_pipeline_results/      # 🆕 第五模块：RQA参数化分析流程结果
    └── m{m}_tau{τ}_eps{ε}_lmin{l}/  # 参数签名目录
        ├── step1_rqa_calculation/    # 步骤1：RQA计算
        │   ├── RQA_1D2D_summary_control.csv
        │   ├── RQA_1D2D_summary_mci.csv
        │   └── RQA_1D2D_summary_ad.csv
        ├── step2_data_merging/       # 步骤2：数据合并
        │   └── All_Subjects_RQA_EyeMetrics.csv
        ├── step3_feature_enrichment/ # 步骤3：特征补充
        │   └── All_Subjects_RQA_EyeMetrics_Filled.csv
        ├── step4_statistical_analysis/ # 步骤4：统计分析
        │   ├── group_stats_output.csv
        │   └── multi_level_stats_output.csv
        ├── step5_visualization/      # 步骤5：可视化
        │   ├── bar_chart_RR_2D_xy.png
        │   ├── bar_chart_DET_2D_xy.png
        │   ├── bar_chart_ENT_2D_xy.png
        │   ├── trend_chart_RR_2D_xy.png
        │   ├── visualization_charts.json
        │   └── group_statistics.json
        └── metadata.json             # 参数元数据和流程状态
```

### 🔧 **核心功能模块**

#### 📊 **数据处理模块** (`data_processing/`)
- **主处理器**: `vr_eyetracking_processor.py`
  - 功能: 解析txt原始数据，计算速度和角度，过滤异常值
  - 输入: 原始txt眼动数据 
  - 输出: 预处理csv文件
  - 关键功能: 坐标转换、速度计算、异常值过滤

- **MCI数据提取器**: `extract_mci_data.py`
  - 功能: 专门处理轻度认知障碍组数据
  - 特点: 针对MCI组的特殊处理逻辑

- **AD数据提取器**: `extract_ad_data.py`
  - 功能: 专门处理阿尔茨海默症组数据
  - 特点: 针对AD组的特殊处理逻辑

#### 🎯 **校准系统** (`calibration/`)
- **基础校准器**: `basic_calibrator.py`
  - 功能: 提供基本的坐标校准功能
  - 用途: 应用固定偏移量校准眼动坐标

- **高级校准器**: `advanced_calibrator.py`
  - 功能: 个体化精确校准
  - 特点: 支持组级和文件级个性化参数
  - 配置: 基于`calibration_config.json`

- **就地校准器**: `inplace_calibrator.py`
  - 功能: 直接修改原文件的校准方式
  - 特点: 节省存储空间，支持题号过滤

#### 📈 **数据分析模块** (`analysis/`)
- **眼动分析器**: `eyetracking_analyzer.py`
  - 功能: 眼动轨迹分析、注视检测、扫视分析
  - 算法: IVT (速度阈值)算法
  - 分析: ROI区域统计、注视模式分析
  - 输出: 注视事件、扫视事件、ROI统计

- **RQA批量渲染器**: `rqa_batch_renderer.py` ⭐ **核心模块**
  - 功能: 递归量化分析(RQA)批量处理和可视化
  - 特点: 支持1D/2D信号、多种距离度量、参数化分析
  - 分析: 递归率(RR)、确定性(DET)、熵(ENT)指标
  - 输出: 轨迹图、幅度图、递归图、RQA指标

#### 🎨 **可视化模块** (`visualization/`)
- **Web可视化器**: `web_visualizer.py` → **enhanced_web_visualizer.py** ⭐ **主入口**
  - 功能: Flask Web服务器，提供在线可视化界面
  - 特点: 五大功能模块、三组数据对比、ROI标记、轨迹绘制
  - 接口: RESTful API，支持动态数据加载

- **RQA扩展API**: `rqa_api_extension.py`
  - 功能: RQA分析相关的API接口
  - 特点: 批量渲染、状态监控、结果获取
  - 接口: `/api/rqa-batch-render`, `/api/rqa-render-status`, `/api/rqa-rendered-results`

- **RQA分析流程API**: `rqa_pipeline_api.py` 🆕 **第五模块核心**
  - 功能: 完整的参数化RQA分析流程API
  - 特点: 五步骤流程、参数管理、结果对比、历史记录
  - 接口: 
    - `/api/rqa-pipeline/calculate` - RQA计算
    - `/api/rqa-pipeline/merge` - 数据合并
    - `/api/rqa-pipeline/enrich` - 特征补充
    - `/api/rqa-pipeline/analyze` - 统计分析
    - `/api/rqa-pipeline/visualize` - 可视化生成
    - `/api/rqa-pipeline/status` - 流程状态
    - `/api/rqa-pipeline/param-history` - 参数历史
    - `/api/rqa-pipeline/results/<signature>` - 获取结果
    - `/api/rqa-pipeline/delete/<signature>` - 删除结果

- **增强模板文件**: `templates/enhanced_index.html`
  - 功能: 五模块集成的Web界面HTML模板
  - 特点: 现代化UI、响应式设计、五个功能模块导航
  - 模块: 数据管理、校准系统、RQA分析、事件分析、**RQA分析流程**

- **静态资源**: `static/`
  - 功能: CSS样式、JavaScript脚本、图片资源

#### ⚙️ **配置管理** (`config/`)
- **基础配置**: `config.py`
  - 内容: 数据处理参数、路径配置、阈值设置
  - 用途: 全局基础配置管理

- **校准配置**: `calibration_config.json`
  - 内容: 校准参数、组级配置、文件级配置
  - 特点: 支持三组数据不同的默认参数

- **分析配置**: `eyetracking_analysis_config.json`
  - 内容: IVT算法参数、ROI区域定义、可视化设置
  - 特点: 详细的ROI坐标定义（Q1-Q5任务）

#### 🛠️ **工具辅助模块** (`utils/`)
- **目录优化工具**: `optimize_directory_naming.py`
  - 功能: 统一目录命名规范
  - 用途: 解决历史命名不一致问题

- **单文件测试工具**: `test_single_file.py`
  - 功能: 测试单个数据文件的处理流程
  - 用途: 开发调试、问题诊断

- **批处理脚本**: `run.bat`
  - 功能: Windows环境一键运行
  - 用途: 简化操作流程

### 🚀 **主入口脚本**

#### **主校准入口** (`calibrate.py`)
- 功能: 统一的校准入口，支持多种模式
- 命令行参数: 
  - `--control-only`: 仅校准对照组
  - `--mci-only`: 仅校准MCI组  
  - `--ad-only`: 仅校准AD组
  - `--inplace`: 就地覆盖校准
  - `--visualize`: 启动可视化界面

#### **可视化入口** (`visualize.py`)
- 功能: 专门的Web可视化启动器
- 特点: 快速启动Web服务器

#### **简单启动器** (`start_server.py`) ⭐ **推荐**
- 功能: 一键启动Web可视化服务器
- 特点: 最简单的启动方式，自动打开浏览器
- 使用: `python start_server.py`

#### **Windows启动器** (`启动服务器.bat`) ⭐ **最简单**
- 功能: Windows环境双击启动
- 特点: 无需命令行，最用户友好

## 🔄 数据流程

### 完整数据处理流程 (传统流程)
```
1. 原始数据 (txt) 
   ↓ [data_processing/vr_eyetracking_processor.py]
2. 预处理数据 (csv)
   ↓ [calibration/advanced_calibrator.py] 
3. 校准数据 (csv) ← 推荐使用
   ↓ [analysis/eyetracking_analyzer.py]
4. 分析结果 (统计+可视化)
   ↓ [visualization/enhanced_web_visualizer.py]
5. Web界面展示
```

### 🆕 RQA参数化分析流程 (第五模块)
```
1. 参数配置 (m, τ, ε, l_min)
   ↓ [rqa_pipeline_api.py - calculate]
2. RQA计算 → RQA_1D2D_summary_{group}.csv
   ↓ [rqa_pipeline_api.py - merge]
3. 数据合并 → All_Subjects_RQA_EyeMetrics.csv
   ↓ [rqa_pipeline_api.py - enrich]
4. 特征补充 → All_Subjects_RQA_EyeMetrics_Filled.csv
   ↓ [rqa_pipeline_api.py - analyze]
5. 统计分析 → group_stats_output.csv, multi_level_stats_output.csv
   ↓ [rqa_pipeline_api.py - visualize]
6. 可视化生成 → PNG图表 + JSON数据
   ↓ [enhanced_index.html]
7. 结果展示与管理 (参数历史、结果对比、删除管理)
```

### 参数化目录管理
```
data/rqa_pipeline_results/
├── m2_tau1_eps0.05_lmin2/     # 参数组合1
│   ├── step1_rqa_calculation/
│   ├── step2_data_merging/
│   ├── step3_feature_enrichment/
│   ├── step4_statistical_analysis/
│   └── step5_visualization/
├── m3_tau2_eps0.08_lmin3/     # 参数组合2
│   └── [同样的步骤结构]
└── m2_tau1_eps0.03_lmin2/     # 参数组合3
    └── [同样的步骤结构]
```

### 三组数据对比研究
- **Control Group (1-20)**: 健康基线数据
- **MCI Group**: 轻度认知障碍数据  
- **AD Group (3-22)**: 阿尔茨海默症数据
- **研究价值**: 健康→MCI→AD的疾病进展研究

## 🔧 开发指南

### 添加新功能
1. **新分析算法**: 在`analysis/`下创建新的分析器
2. **新可视化**: 在`visualization/`下扩展Web界面
3. **新校准方法**: 在`calibration/`下实现新校准器
4. **新数据格式**: 在`data_processing/`下添加解析器

### 配置管理
- **全局配置**: 修改`config/config.py`
- **校准参数**: 编辑`config/calibration_config.json`
- **ROI区域**: 编辑`config/eyetracking_analysis_config.json`

### 调试工具
- **单文件测试**: `python utils/test_single_file.py <文件路径>`
- **调试模式**: 在代码中设置`debug=True`参数
- **日志输出**: 查看控制台详细输出信息

### 部署建议
- **开发环境**: 使用`python start_server.py`
- **生产环境**: 使用`gunicorn`等专业WSGI服务器
- **依赖管理**: 确保安装`requirements.txt`中所有依赖

## 📝 维护要点

### 定期维护
1. **数据备份**: 定期备份校准后的数据
2. **配置更新**: 根据新需求调整ROI区域定义
3. **性能监控**: 监控大数据量处理性能
4. **依赖更新**: 定期更新Python依赖包

### 故障排除
1. **导入错误**: 检查Python路径和依赖安装
2. **数据错误**: 验证输入数据格式
3. **端口冲突**: 更改Web服务器端口
4. **内存不足**: 优化大数据量处理算法

### 扩展方向
1. **机器学习**: 集成ML模型进行疾病预测
2. **实时分析**: 支持实时眼动数据流处理
3. **云端部署**: 支持云服务器部署
4. **移动端**: 开发移动设备可视化界面
5. **🆕 RQA流程扩展**:
   - 更多RQA指标: LAM(层流性)、TREND(趋势性)、T1/T2(转移时间)
   - 参数优化: 自动寻找最优RQA参数组合
   - 对比分析: 多参数组合的自动对比报告
   - 导出功能: 支持Excel、PDF报告导出
   - 批量分析: 支持多数据集的批量处理 