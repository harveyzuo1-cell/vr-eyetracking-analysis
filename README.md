# VR Eye-tracking Data Analysis Platform

[English](#english) | [中文](#chinese)

<a name="english"></a>
## 📋 Project Overview

This is a Python + Flask based eye-tracking data analysis platform specifically designed for processing and analyzing VR eye-tracking experimental data. The system supports multiple analysis modes including Recurrence Quantification Analysis (RQA), trajectory visualization, and Region of Interest (ROI) analysis.

### 🎯 Key Features
- ✅ **Eye-tracking Data Preprocessing** - Time calibration, noise filtering, data normalization
- ✅ **Recurrence Quantification Analysis (RQA)** - 1D/2D signal analysis, recurrence plot generation, quantitative metrics calculation
- ✅ **Visual Analysis** - Trajectory plots, heatmaps, amplitude plots, recurrence plots
- ✅ **ROI Region Analysis** - Precise ROI coloring and annotation based on All_Events.csv
- ✅ **Web Interface** - Modern responsive interface with parameter configuration and result viewing
- 🆕 **RQA Parameterized Analysis Pipeline** - Complete five-step automated analysis workflow with parameter management and result comparison
- 🆕 **Eye Movement Coefficient vs MMSE Comparison Analysis** - Cognitive assessment comparison based on eye movement features, supporting multi-dimensional correlation studies

## 🏗️ System Architecture

### Core Module Architecture
```
VR Eye-tracking Data Analysis System
├── 📊 Data Processing Module
│   ├── Time Calibration
│   ├── Data Preprocessing
│   └── Data Validation
├── 🔬 RQA Analysis Module
│   ├── Signal Embedding
│   ├── Recurrence Matrix Calculation
│   ├── RQA Measures Extraction
│   └── Visualization Rendering
├── 🎨 Visualization Module
│   ├── Trajectory Plots
│   ├── Heatmaps
│   ├── ROI Analysis Plots
│   └── Recurrence Plots
├── 🔄 RQA Analysis Pipeline Module 🆕
│   ├── RQA Calculation
│   ├── Data Merging
│   ├── Feature Enrichment
│   ├── Statistical Analysis
│   ├── Visualization Generation
│   └── Parameter Management
├── 📊 Data Integration Module (Module 7) 🆕
│   ├── Multi-source Data Loading
│   ├── Feature Extraction & Integration
│   ├── 10-Feature Normalization
│   ├── Intelligent Outlier Handling
│   ├── RQA Parameter Management
│   └── Structured Data Storage
├── 🧠 Eye Movement vs MMSE Comparison Module (Module 8) 🆕
│   ├── Eye Movement Data Processing
│   ├── Eye Movement Coefficient Calculation
│   ├── MMSE Data Loading
│   ├── Multi-dimensional Comparison
│   ├── Sub-question Analysis
│   ├── 5-Chart Visualization
│   ├── Correlation Analysis
│   └── Auto CSV Export
└── 🌐 Web Interface Module
    ├── Data Management Interface
    ├── Analysis Configuration Interface
    ├── Result Display Interface
    ├── 🆕 RQA Pipeline Interface
    ├── 🆕 Data Integration Interface (Module 7)
    ├── 🆕 Eye Movement vs MMSE Interface (Module 8)
    └── API Endpoints
```

### Technology Stack
- **Backend**: Python 3.8+, Flask, NumPy, Pandas, Matplotlib
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap
- **Data Processing**: SciPy, scikit-learn
- **Visualization**: Matplotlib, Seaborn
- **API**: RESTful API, JSON data exchange

## 📁 Project Structure

```
vr-eyetracking-analysis/
├── 📂 analysis/                    # Core analysis modules
│   ├── rqa_batch_renderer.py      # RQA batch renderer (core class)
│   ├── time_calibration.py        # Time calibration module
│   └── data_processor.py          # Data preprocessor
├── 📂 visualization/               # Visualization modules
│   ├── rqa_api_extension.py       # RQA API extension
│   ├── rqa_pipeline_api.py        # 🆕 RQA pipeline API
│   ├── mmse_api_extension.py      # 🆕 MMSE data API extension
│   ├── real_data_integration_api.py # 🆕 Real data integration API
│   ├── web_api.py                 # Web API interface
│   └── templates/
│       └── enhanced_index.html    # Main interface template
├── 📂 data/                       # Data directory
│   ├── calibrated/                # Eye-tracking calibrated data
│   ├── MMSE_Score/                # 🆕 MMSE cognitive assessment data
│   ├── event_analysis_results/    # ROI event analysis results
│   ├── normalized_features/       # 🆕 Normalized feature data
│   ├── module7_integrated_results/ # 🆕 Module 7 integration results
│   ├── module8_analysis_results/  # 🆕 Module 8 analysis results
│   └── rqa_pipeline_results/      # 🆕 RQA pipeline results
├── 📂 static/                     # Static resources
├── start_server.py                # Server startup script
└── README.md                      # Project documentation
```

## 🚀 Quick Start

### Environment Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install flask numpy pandas matplotlib scipy scikit-learn

# 3. Start server
python start_server.py
```

### Access the System

```bash
# Start web server
python start_server.py

# Access interface
http://localhost:8080
```

## 📊 Usage Guide

### Data Preparation

1. **Data Format Requirements**:
```csv
timestamp,x,y,milliseconds,ROI,SequenceID
1641024000000,500.2,300.1,0,BG,0
1641024000016,502.1,301.5,16,INST,1
...
```

2. **File Naming Convention**:
```
{group}{id}q{question}_preprocessed_calibrated.csv
Example: n1q1_preprocessed_calibrated.csv (Control group 1, Q1)
        m1q1_preprocessed_calibrated.csv (MCI group 1, Q1)
```

### Running Analysis

#### Traditional RQA Analysis
1. Start system: `python start_server.py`
2. Access interface: http://localhost:8080
3. Select RQA Analysis tab
4. Configure parameters:
   - Analysis mode: 1D signal (X coordinate)/1D signal (amplitude)/2D signal (X,Y coordinates)
   - Distance metric: 1D absolute difference/Euclidean distance
   - Embedding dimension: typically 2-10
   - Time delay: typically 1
   - Recurrence threshold: 0.01-0.1 range
   - Minimum line length: 2-5
5. Start rendering: Click "Start RQA Rendering"
6. View results in the results area

#### 🆕 RQA Analysis Pipeline (Recommended)
1. Start system and access interface
2. Select "RQA Analysis Pipeline" tab
3. Configure RQA parameters:
   - Embedding dimension (m): 2 (default)
   - Time delay (τ): 1 (default)
   - Recurrence threshold (ε): 0.05 (default)
   - Minimum line length (l_min): 2 (default)
4. View parameter signature: System auto-generates `m2_tau1_eps0.05_lmin2`
5. Execute analysis workflow:
   - Click "Step 1: RQA Calculation" or
   - Click "Complete Pipeline" (one-click execution)
6. Monitor progress with five-step progress indicator
7. View results in visualization area
8. Manage history using "Parameter History" feature

#### 🆕 Module 7: Data Integration
1. Select "Module 7 - Data Integration" tab
2. Choose RQA parameter configuration from dropdown
3. View real-time statistics:
   - Total subjects: dynamically calculated
   - Game sessions: real-time updates
   - VR-MMSE tasks: task type statistics
   - Normalized features: feature count statistics
4. Execute data integration
5. View standardization details
6. Generate visualizations
7. Export integrated data

#### 🆕 Module 8: Eye Movement vs MMSE Analysis
1. Select "Module 8 - MMSE Comparison" tab
2. Select data source from Module 7
3. Load eye movement data
4. Calculate eye movement coefficients
5. Perform MMSE comparison analysis
6. View multi-dimensional results:
   - Individual view: detailed comparison per subject
   - Group view: statistics by group with correlation analysis
   - Main task mode: Q1-Q5 task-level analysis
   - Sub-question mode: detailed analysis of 17 specific sub-questions
7. Smart visualization:
   - Q1-Q5 separated scatter plots
   - Three-color grouping: Blue=Control, Orange=MCI, Red=AD
   - Completion rate axis: Y-axis shows MMSE completion rate (0-100%)
8. Export analysis reports

## 🔬 Module Details

### Data Processing Module
**Function**: Eye-tracking data preprocessing and standardization
**Core Features**:
- ⏰ Time calibration: millisecond-level timestamp standardization
- 🔧 Data cleaning: anomaly detection and filtering
- 📊 Format conversion: multiple data format support
- ✅ Data validation: completeness and consistency checks

### RQA Analysis Module
**Function**: Complete implementation of Recurrence Quantification Analysis
**Analysis Modes**:
- 🔢 1D signal (X coordinate): `1d_x`
- 📈 1D signal (amplitude): `1d_amplitude`
- 📊 2D signal (X,Y coordinates): `2d_xy`

**Parameters**:
```python
{
    "analysis_mode": "2d_xy",
    "distance_metric": "euclidean",
    "embedding_dimension": 2,        # m
    "time_delay": 1,                 # τ
    "recurrence_threshold": 0.05,    # ε
    "min_line_length": 2,            # l_min
    "color_theme": "green_gradient"
}
```

### Module 7: Data Integration 🆕
**Core Features**:
- 🔗 Multi-source data integration
- 📊 Intelligent data standardization
- 🎯 RQA parameterized configuration
- 💾 Result caching mechanism
- 📈 Real-time statistics updates

**10 Normalized Features**:
- `game_duration`: Game duration
- `roi_kw_time`: KW-ROI time
- `roi_inst_time`: INST-ROI time
- `roi_bg_time`: BG-ROI time
- `rr_1d`, `det_1d`, `ent_1d`: 1D RQA metrics
- `rr_2d`, `det_2d`, `ent_2d`: 2D RQA metrics

### Module 8: Eye Movement vs MMSE Analysis 🆕
**Core Features**:
- 🧠 MMSE data integration
- 📊 Eye movement coefficient calculation
- 🔍 Multi-dimensional comparison
- 📈 5-chart visualization
- 🔗 Correlation analysis
- 📁 Auto CSV export

**Eye Movement Coefficient Calculation**:
```javascript
Eye_Movement_Coefficient = mean(
  inverted(game_duration, roi_times) + 
  direct(rqa_metrics)
) / 10
```

## 🔧 Technical Details

### RQA Algorithm Implementation

```python
# 1. Signal embedding (Phase Space Reconstruction)
embedded = embed_signal(signal, m=2, tau=1)

# 2. Distance matrix calculation
distances = compute_distance_matrix(embedded, metric='euclidean')

# 3. Recurrence matrix generation
recurrence_matrix = distances < threshold

# 4. RQA metrics calculation
RR = np.sum(recurrence_matrix) / (N * N)
DET = calculate_determinism(recurrence_matrix)
ENT = calculate_entropy(recurrence_matrix)
```

### Performance Optimization
- ⚡ **Batch Processing**: Parallel processing of multiple data files
- 💾 **Memory Management**: Timely release of graphics objects and memory
- 🔄 **Incremental Rendering**: Support for incremental updates
- 📁 **Result Caching**: Results organized by parameter signatures

## 🐛 FAQ

### Q: Rendering failed?
A: Check data format, file paths, and parameter settings. Check server logs for detailed error information.

### Q: Module 7 data integration failed?
A: 
- Check if `data/calibrated` directory contains calibrated data
- Confirm `data/event_analysis_results/All_ROI_Summary.csv` exists
- Verify RQA results in `data/rqa_pipeline_results`
- Check server logs for details

### Q: Module 8 MMSE data loading error?
A:
- Confirm `data/MMSE_Score` directory contains three group CSV files
- Check CSV file column name format
- Verify subject ID format matching
- Ensure Module 7 data is generated first

## 📞 Support

For issues or suggestions:
- 📧 Create an Issue
- 📝 Check project Wiki
- 🔧 Submit Pull Requests

---

<a name="chinese"></a>
# 眼动数据分析系统 (中文版)

## 📋 项目概述

这是一个基于Python + Flask的眼动数据分析平台，专门用于处理和分析眼球追踪实验数据。系统支持多种分析模式，包括递归量化分析(RQA)、轨迹可视化、ROI(感兴趣区域)分析等功能。

### 🎯 主要功能
- ✅ **眼动数据预处理** - 时间校准、噪声过滤、数据标准化
- ✅ **递归量化分析(RQA)** - 1D/2D信号分析、递归图生成、量化指标计算
- ✅ **可视化分析** - 轨迹图、热力图、amplitude图、递归图
- ✅ **ROI区域分析** - 基于All_Events.csv的精确ROI着色和标注
- ✅ **Web界面** - 现代化响应式界面，支持参数配置和结果查看
- 🆕 **RQA参数化分析流程** - 完整的五步骤自动化分析流程，支持参数管理和结果对比
- 🆕 **眼动系数与MMSE对比分析** - 基于眼动特征的认知评估对比分析，支持多维度相关性研究

## 🏗️ 系统架构

### 核心模块架构
```
眼动数据分析系统
├── 📊 数据处理模块 (Data Processing)
│   ├── 时间校准 (Time Calibration)
│   ├── 数据预处理 (Preprocessing) 
│   └── 数据验证 (Validation)
├── 🔬 RQA分析模块 (RQA Analysis)
│   ├── 信号嵌入 (Signal Embedding)
│   ├── 递归矩阵计算 (Recurrence Matrix)
│   ├── 量化指标提取 (RQA Measures)
│   └── 可视化渲染 (Visualization)
├── 🎨 可视化模块 (Visualization)
│   ├── 轨迹图 (Trajectory Plots)
│   ├── 热力图 (Heatmaps)
│   ├── ROI分析图 (ROI Analysis)
│   └── 递归图 (Recurrence Plots)
├── 🔄 RQA分析流程模块 (RQA Pipeline) 🆕
│   ├── RQA计算 (RQA Calculation)
│   ├── 数据合并 (Data Merging)
│   ├── 特征补充 (Feature Enrichment)
│   ├── 统计分析 (Statistical Analysis)
│   ├── 可视化生成 (Visualization Generation)
│   └── 参数管理 (Parameter Management)
├── 📊 数据整合模块 (Module 7) 🆕
│   ├── 多源数据加载 (Multi-source Data Loading)
│   ├── 特征抽取整合 (Feature Extraction & Integration)
│   ├── 十属性归一化 (10-Feature Normalization)
│   ├── 智能异常值处理 (Intelligent Outlier Handling)
│   ├── RQA参数化管理 (RQA Parameter Management)
│   └── 结构化数据存储 (Structured Data Storage)
├── 🧠 眼动系数与MMSE对比分析模块 (Module 8) 🆕
│   ├── 眼动数据处理 (Eye Movement Data Processing)
│   ├── 眼动系数计算 (Eye Movement Coefficient Calculation)
│   ├── MMSE数据加载 (MMSE Data Loading)
│   ├── 多维度对比分析 (Multi-dimensional Comparison)
│   ├── 子问题详细分析 (Sub-question Analysis)
│   ├── 5图表可视化 (5-Chart Visualization)
│   ├── 相关性分析 (Correlation Analysis)
│   └── 自动CSV导出 (Auto CSV Export)
└── 🌐 Web界面模块 (Web Interface)
    ├── 数据管理界面
    ├── 分析配置界面
    ├── 结果展示界面
    ├── 🆕 RQA分析流程界面
    ├── 🆕 数据整合界面 (模块7)
    ├── 🆕 眼动系数与MMSE对比界面 (模块8)
    └── API接口
```

### 技术栈
- **后端**: Python 3.8+, Flask, NumPy, Pandas, Matplotlib
- **前端**: HTML5, CSS3, JavaScript (ES6+), Bootstrap
- **数据处理**: SciPy, scikit-learn
- **可视化**: Matplotlib, Seaborn
- **API**: RESTful API, JSON数据交换

## 📁 项目文件结构

```
az/
├── 📂 analysis/                    # 核心分析模块
│   ├── rqa_batch_renderer.py      # RQA批量渲染器 (核心类)
│   ├── time_calibration.py        # 时间校准模块
│   └── data_processor.py          # 数据预处理器
├── 📂 visualization/               # 可视化模块  
│   ├── rqa_api_extension.py       # RQA API扩展
│   ├── rqa_pipeline_api.py        # 🆕 RQA分析流程API
│   ├── mmse_api_extension.py      # 🆕 MMSE数据API扩展
│   ├── real_data_integration_api.py # 🆕 真实数据整合API
│   ├── web_api.py                 # Web API接口
│   └── templates/
│       └── enhanced_index.html    # 主界面模板(含模块7-8)
├── 📂 data/                       # 数据目录
│   ├── calibrated/                # 眼动校准数据(按组别目录)
│   ├── MMSE_Score/                # 🆕 MMSE认知评估数据
│   ├── event_analysis_results/    # ROI事件分析结果
│   ├── normalized_features/       # 🆕 标准化特征数据(模块7)
│   ├── module7_integrated_results/ # 🆕 模块7数据整合结果
│   ├── module8_analysis_results/  # 🆕 模块8分析结果
│   └── rqa_pipeline_results/      # 🆕 RQA分析流程结果
├── 📂 static/                     # 静态资源
├── start_server.py                # 服务器启动脚本
└── README.md                      # 项目文档
```

## 🚀 开发指南

### 环境配置

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install flask numpy pandas matplotlib scipy scikit-learn

# 3. 启动服务
python start_server.py
```

### 启动系统

```bash
# 启动Web服务器
python start_server.py

# 访问界面
http://localhost:8080
```

## 📊 使用说明

### 数据准备

1. **数据格式要求**:
```csv
timestamp,x,y,milliseconds,ROI,SequenceID
1641024000000,500.2,300.1,0,BG,0
1641024000016,502.1,301.5,16,INST,1
...
```

2. **文件命名规范**:
```
{group}{id}q{question}_preprocessed_calibrated.csv
例如: n1q1_preprocessed_calibrated.csv (对照组1号Q1)
     m1q1_preprocessed_calibrated.csv (MCI组1号Q1)
```

### 运行分析

#### 传统RQA分析
1. **启动系统**: `python start_server.py`
2. **访问界面**: http://localhost:8080
3. **选择RQA分析选项卡**
4. **配置参数**:
   - 分析模式: 1D信号(X坐标)/1D信号(幅度)/2D信号(X,Y坐标)
   - 距离度量: 1D绝对差/欧几里得距离
   - 嵌入维度: 通常为2-10
   - 时间延迟: 通常为1
   - 递归阈值: 0.01-0.1范围
   - 最小线长: 2-5
5. **启动渲染**: 点击"开始RQA渲染"
6. **查看结果**: 渲染完成后在结果区域查看

#### 🆕 RQA分析流程 (推荐)
1. **启动系统**: `python start_server.py`
2. **访问界面**: http://localhost:8080
3. **选择"RQA分析流程"选项卡**
4. **配置RQA参数**:
   - 嵌入维度(m): 2 (默认)
   - 时间延迟(τ): 1 (默认)
   - 递归阈值(ε): 0.05 (默认)
   - 最小线长(l_min): 2 (默认)
5. **查看参数签名**: 系统自动生成 `m2_tau1_eps0.05_lmin2`
6. **执行分析流程**:
   - 点击"步骤1: RQA计算" 或
   - 点击"完整流程" (一键执行所有步骤)
7. **监控进度**: 观察五步骤进度指示器
8. **查看结果**: 在可视化区域查看生成的图表
9. **管理历史**: 使用"历史参数"功能管理和对比不同参数的结果

#### 🆕 模块7: 数据整合分析
1. **选择"模块7-数据整合"选项卡**
2. **选择RQA参数配置**
3. **查看实时统计**:
   - 受试者总数: 动态计算
   - 游戏会话数: 实时更新
   - VR-MMSE任务: 任务类型统计
   - 归一化特征: 特征数量统计
4. **执行数据整合**
5. **查看标准化说明**
6. **可视化分析**
7. **数据导出**

#### 🆕 模块8: 眼动系数与MMSE对比分析
1. **选择"模块8-MMSE对比分析"选项卡**
2. **选择数据源**
3. **加载眼动数据**
4. **计算眼动系数**
5. **MMSE对比分析**
6. **多维度分析结果**:
   - **个人视图**: 每个受试者的详细对比数据
   - **群体视图**: 按组别统计的平均值和相关性分析
   - **主问题模式**: Q1-Q5任务级别分析
   - **子问题模式**: 17个具体子问题的精细分析
7. **智能可视化**:
   - **Q1-Q5分离式散点图**: 任务特异性相关性展示
   - **三色分组**: 蓝色=Control, 橙色=MCI, 红色=AD
   - **完成率轴**: Y轴显示MMSE完成率(0-100%)
8. **智能数据导出**

## 🔬 模块详解

### 数据处理模块
**功能**: 眼动数据的预处理和标准化
**核心功能**:
- ⏰ **时间校准**: 毫秒级时间戳标准化
- 🔧 **数据清洗**: 异常值检测和过滤
- 📊 **格式转换**: 多种数据格式支持
- ✅ **数据验证**: 完整性和一致性检查

### RQA分析模块
**功能**: 递归量化分析的完整实现
**分析模式**:
- 🔢 **1D信号(X坐标)**: `1d_x`
- 📈 **1D信号(幅度)**: `1d_amplitude`
- 📊 **2D信号(X,Y坐标)**: `2d_xy`

**参数设置**:
```python
{
    "analysis_mode": "2d_xy",           # 分析模式
    "distance_metric": "euclidean",     # 距离度量
    "embedding_dimension": 2,           # 嵌入维度(m)
    "time_delay": 1,                    # 时间延迟(τ)
    "recurrence_threshold": 0.05,       # 递归阈值(ε)
    "min_line_length": 2,               # 最小线长(l_min)
    "color_theme": "green_gradient"     # 渲染主题
}
```

### 模块7: 数据整合 🆕
**核心特性**:
- 🔗 **多源数据整合**: 自动整合校准数据、ROI分析结果、RQA计算结果
- 📊 **智能数据标准化**: 支持百分位截断和Min-Max标准化策略
- 🎯 **RQA参数化配置**: 动态检测和选择不同RQA参数组合
- 💾 **结果缓存机制**: 基于RQA参数的智能缓存和增量更新
- 📈 **实时统计更新**: 动态计算受试者、会话、特征数量

**10个标准化特征**:
- `game_duration`: 游戏时长
- `roi_kw_time`: KW-ROI时间
- `roi_inst_time`: INST-ROI时间
- `roi_bg_time`: BG-ROI时间
- `rr_1d`, `det_1d`, `ent_1d`: 1D RQA指标
- `rr_2d`, `det_2d`, `ent_2d`: 2D RQA指标

### 模块8: 眼动系数与MMSE对比分析 🆕
**核心特性**:
- 🧠 **MMSE数据整合**: 自动加载对照组、MCI组、AD组认知评估数据
- 📊 **眼动系数计算**: 基于10个标准化特征的综合眼动表现系数
- 🔍 **多维度对比**: 个人级、群体级、子问题级三种分析维度
- 📈 **5图表可视化**: Q1-Q5任务的分离式散点图展示
- 🔗 **相关性分析**: Pearson相关系数和标准差统计
- 📁 **自动CSV导出**: 所有分析结果自动保存为CSV格式

**眼动系数计算**:
```javascript
眼动系数 = mean(
  反转(游戏时长, ROI时间) + 
  直接(RQA指标)
) / 10
```

## 🔧 技术细节

### RQA算法实现

```python
# 1. 信号嵌入 (Phase Space Reconstruction)
embedded = embed_signal(signal, m=2, tau=1)

# 2. 距离矩阵计算
distances = compute_distance_matrix(embedded, metric='euclidean')

# 3. 递归矩阵生成
recurrence_matrix = distances < threshold

# 4. RQA指标计算
RR = np.sum(recurrence_matrix) / (N * N)
DET = calculate_determinism(recurrence_matrix)
ENT = calculate_entropy(recurrence_matrix)
```

### 性能优化
- ⚡ **批量处理**: 并行处理多个数据文件
- 💾 **内存管理**: 及时释放图形对象和内存
- 🔄 **增量渲染**: 支持参数变更时的增量更新
- 📁 **结果缓存**: 按参数签名组织结果文件

## 🐛 常见问题

### Q: 渲染失败怎么办？
A: 检查数据格式、文件路径和参数设置，查看服务器日志获取详细错误信息。

### Q: 模块7数据整合失败？
A: 
- 检查`data/calibrated`目录是否包含校准数据
- 确认`data/event_analysis_results/All_ROI_Summary.csv`文件存在
- 验证`data/rqa_pipeline_results`中有对应RQA参数的结果
- 查看服务器日志获取详细错误信息

### Q: 模块8 MMSE数据加载异常？
A:
- 确认`data/MMSE_Score`目录包含三个组别的CSV文件
- 检查CSV文件的列名格式(受试者/试者列名不一致)
- 验证受试者ID格式匹配(如`n01` vs `n1q`)
- 确保先在模块7中生成对应RQA配置的数据

## 📞 技术支持

如有问题或建议，请通过以下方式联系：
- 📧 创建Issue描述问题
- 📝 查看项目Wiki获取更多信息
- 🔧 提交Pull Request参与开发

---

**版本**: v1.3.0  
**最后更新**: 2025年8月5日  
**开发状态**: 活跃开发中 🚀