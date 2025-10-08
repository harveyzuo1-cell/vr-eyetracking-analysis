# Module05 RQA分析模块设计文档

**文档版本**: v1.0
**创建日期**: 2025-10-07
**作者**: 系统架构团队
**模块名称**: Module05 - 递归量化分析 (Recurrence Quantification Analysis)

---

## 📋 目录

1. [执行摘要](#1-执行摘要)
2. [需求分析](#2-需求分析)
3. [系统架构设计](#3-系统架构设计)
4. [核心功能设计](#4-核心功能设计)
5. [数据流设计](#5-数据流设计)
6. [API接口设计](#6-api接口设计)
7. [并行处理设计](#7-并行处理设计)
8. [数据持久化设计](#8-数据持久化设计)
9. [前端交互设计](#9-前端交互设计)
10. [性能优化策略](#10-性能优化策略)
11. [实施计划](#11-实施计划)

---

## 1. 执行摘要

### 1.1 模块概述

Module05 RQA分析模块是眼动数据分析平台的核心分析组件，负责对校准后的眼动轨迹数据进行递归量化分析（RQA），提取非线性动力学特征，用于认知功能评估和疾病诊断。

### 1.2 核心价值

- **大规模参数空间探索**: 支持10,200+参数组合的批量分析
- **CPU多线程优化**: 充分利用CPU多核资源，避免GPU依赖
- **完整分析流程**: 从RQA计算到统计分析的5步完整流程
- **架构最佳实践**: 遵循Module04的卓越架构模式

### 1.3 关键特性

| 特性 | 说明 |
|------|------|
| **批量参数生成** | 自动生成m×τ×ε×lmin参数组合空间 |
| **双模式分析** | 支持1D-x和2D-xy两种嵌入模式 |
| **并行计算** | CPU多线程池处理，可配置线程数 |
| **增量缓存** | 已完成参数组合可复用，支持断点续传 |
| **进度追踪** | 实时进度反馈，支持任务取消 |
| **结果可视化** | 递归图、时间序列图、统计图表 |

---

## 2. 需求分析

### 2.1 功能需求

#### 2.1.1 RQA参数配置

**嵌入维度 (m - Embedding Dimension)**
- 范围: 1-10
- 步长: 1
- 默认: 2
- 说明: 相空间重构的维度

**时间延迟 (τ - Time Delay)**
- 范围: 1-10
- 步长: 1
- 默认: 1
- 说明: 嵌入向量之间的时间间隔

**递归阈值 (ε - Recurrence Threshold)**
- 范围: 0.05-0.1
- 步长: 0.001
- 默认: 0.05
- 说明: 判定两点为递归点的距离阈值

**最小线长 (lmin - Minimum Line Length)**
- 范围: 2-3
- 步长: 1
- 默认: 2
- 说明: 计算DET和ENT时的最小对角线长度

#### 2.1.2 批量执行配置

```python
# 预计生成的参数组合数
total_combinations = (
    (m_end - m_start) / m_step + 1 *
    (tau_end - tau_start) / tau_step + 1 *
    (eps_end - eps_start) / eps_step + 1 *
    (lmin_end - lmin_start) / lmin_step + 1
)
# 默认配置: 10 * 10 * 51 * 2 = 10,200 组合
```

#### 2.1.3 RQA指标计算

**核心指标 (两种模式)**
- **RR (Recurrence Rate)**: 递归率
- **DET (Determinism)**: 确定性
- **ENT (Entropy)**: 熵

**分析模式**
- **1D-x**: 仅使用x坐标的1D时间序列分析
- **2D-xy**: 使用(x,y)坐标的2D轨迹分析

每个参数组合产生6个指标:
- RR-1D-x, DET-1D-x, ENT-1D-x
- RR-2D-xy, DET-2D-xy, ENT-2D-xy

### 2.2 非功能需求

#### 2.2.1 性能要求

| 指标 | 要求 | 实现策略 |
|------|------|----------|
| **单文件处理时间** | <2秒/参数组合 | CPU多线程 |
| **批量处理吞吐量** | >50文件/分钟 | 线程池并行 |
| **内存占用** | <4GB (峰值) | 流式处理，及时释放 |
| **CPU利用率** | >80% (多核) | 动态线程池调整 |
| **任务响应时间** | <500ms (启动) | 异步任务队列 |

#### 2.2.2 可靠性要求

- **容错能力**: 单文件失败不影响整体流程
- **断点续传**: 已完成的参数组合可跳过
- **数据完整性**: 所有结果带时间戳和校验信息
- **错误追踪**: 详细错误日志，支持调试

#### 2.2.3 可用性要求

- **进度可视化**: 实时显示已完成/总数
- **任务管理**: 支持暂停、取消、重启
- **结果查询**: 按参数、按受试者快速检索
- **导出功能**: CSV、Excel、JSON多格式导出

---

## 3. 系统架构设计

### 3.1 整体架构

遵循Module04的卓越架构模式，采用三层分层架构：

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│   ┌──────────────────────────────────────────────┐     │
│   │  Module05.jsx (React Component)              │     │
│   │  - 参数配置界面                               │     │
│   │  - 进度监控面板                               │     │
│   │  - 结果可视化                                 │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│                      API Layer                           │
│   ┌──────────────────────────────────────────────┐     │
│   │  api.py (Flask Blueprint)                    │     │
│   │  - RESTful API endpoints                     │     │
│   │  - 参数验证装饰器                            │     │
│   │  - 统一错误处理                              │     │
│   └──────────────────────────────────────────────┘     │
│   ┌──────────────────────────────────────────────┐     │
│   │  utils.py (Decorators & Validators)          │     │
│   │  - @handle_api_errors                        │     │
│   │  - @validate_params                          │     │
│   │  - @monitor_performance                      │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│   ┌──────────────────────────────────────────────┐     │
│   │  service.py (RQAAnalysisService)             │     │
│   │  - 参数组合生成                              │     │
│   │  - 任务调度管理                              │     │
│   │  - 结果聚合                                  │     │
│   │  - 缓存管理                                  │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                    │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│   │rqa_analyzer.py│  │task_executor.py│  │visualizer.py│ │
│   │- RQA核心算法 │  │- 多线程调度   │  │- 图表生成   │ │
│   │- 嵌入重构    │  │- 进度追踪     │  │- 递归图     │ │
│   │- 递归矩阵    │  │- 任务队列     │  │- 统计图     │ │
│   │- 指标计算    │  │- 错误恢复     │  │              │ │
│   └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                   Data Access Layer                      │
│   ┌──────────────────────────────────────────────┐     │
│   │  data_loader.py                              │     │
│   │  - 读取校准后数据 (02_processed)             │     │
│   │  - ROI配置加载                               │     │
│   │  - 受试者信息                                │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                   Data Persistence                       │
│   data/05_rqa_analysis/                                 │
│   ├── cache/                                            │
│   │   └── param_combinations.json                      │
│   ├── results/                                          │
│   │   ├── m{m}_tau{tau}_eps{eps}_lmin{lmin}/          │
│   │   │   ├── step1_rqa_calculation/                   │
│   │   │   │   ├── control_rqa_results.csv             │
│   │   │   │   ├── mci_rqa_results.csv                 │
│   │   │   │   └── ad_rqa_results.csv                  │
│   │   │   ├── step2_data_merging/                      │
│   │   │   │   └── merged_data.csv                     │
│   │   │   ├── step3_feature_enrichment/                │
│   │   │   │   └── enriched_features.csv               │
│   │   │   ├── step4_statistical_analysis/              │
│   │   │   │   ├── descriptive_stats.csv               │
│   │   │   │   └── group_comparison.csv                │
│   │   │   ├── step5_visualization/                     │
│   │   │   │   ├── recurrence_plots/                   │
│   │   │   │   ├── time_series_plots/                  │
│   │   │   │   └── statistical_plots/                  │
│   │   │   └── metadata.json                           │
│   └── exports/                                         │
│       └── rqa_results_{timestamp}.xlsx                 │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

#### 3.2.1 Service层 - RQAAnalysisService

```python
class RQAAnalysisService:
    """RQA分析服务 - 核心调度器"""

    def __init__(self):
        self.data_root = Path(Config.DATA_ROOT)
        self.processed_dir = self.data_root / '02_processed'
        self.results_dir = self.data_root / '05_rqa_analysis' / 'results'
        self.cache_dir = self.data_root / '05_rqa_analysis' / 'cache'

        # 任务执行器（CPU多线程）
        self.task_executor = RQATaskExecutor(max_workers=cpu_count())

        # RQA分析器
        self.rqa_analyzer = RQAAnalyzer()

        # 进度追踪
        self.progress_tracker = ProgressTracker()

    def generate_param_combinations(self, param_ranges: Dict) -> List[Dict]:
        """生成参数组合空间"""

    def analyze_batch(self, param_combinations: List[Dict],
                     groups: List[str]) -> Dict:
        """批量RQA分析（5步流程）"""

    def get_analysis_status(self, param_signature: str) -> Dict:
        """获取分析状态"""

    def cancel_analysis(self, task_id: str) -> bool:
        """取消分析任务"""
```

#### 3.2.2 业务逻辑层 - RQAAnalyzer

```python
class RQAAnalyzer:
    """RQA核心算法实现"""

    def analyze_single_file(self, csv_path: str, params: Dict) -> Dict:
        """
        单文件RQA分析

        Args:
            csv_path: 校准后CSV文件路径
            params: {m, tau, eps, lmin}

        Returns:
            {
                'RR-1D-x': float,
                'DET-1D-x': float,
                'ENT-1D-x': float,
                'RR-2D-xy': float,
                'DET-2D-xy': float,
                'ENT-2D-xy': float,
                'metadata': {...}
            }
        """

    def embed_signal_1d(self, x: np.ndarray, m: int, tau: int) -> np.ndarray:
        """1D信号嵌入重构"""

    def embed_signal_2d(self, x: np.ndarray, y: np.ndarray,
                       m: int, tau: int) -> np.ndarray:
        """2D信号嵌入重构"""

    def compute_recurrence_matrix(self, embedded: np.ndarray,
                                  eps: float, metric: str) -> np.ndarray:
        """计算递归矩阵"""

    def compute_rqa_metrics(self, rp: np.ndarray, lmin: int) -> Dict:
        """计算RQA指标 (RR, DET, ENT)"""

    def extract_diagonal_lengths(self, rp: np.ndarray) -> Dict[int, int]:
        """提取对角线长度分布"""
```

#### 3.2.3 任务执行器 - RQATaskExecutor

```python
class RQATaskExecutor:
    """CPU多线程任务执行器"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or cpu_count()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.active_tasks = {}
        self.task_results = {}

    def submit_batch_task(self, task_id: str, files: List[str],
                         params: Dict, callback: Callable) -> Future:
        """提交批量分析任务"""

    def get_task_progress(self, task_id: str) -> Dict:
        """获取任务进度"""

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""

    def _process_file_batch(self, files: List[str], params: Dict) -> List[Dict]:
        """批量处理文件（线程池并行）"""
```

---

## 4. 核心功能设计

### 4.1 五步RQA分析流程

#### Step 1: RQA计算 (RQA Calculation)

**输入**:
- 校准后眼动数据: `data/02_processed/{group}/{subject_id}_{task_id}_calibrated.csv`
- RQA参数: `{m, tau, eps, lmin}`

**处理**:
```python
def step1_rqa_calculation(params: Dict, groups: List[str]) -> Dict:
    """
    对所有受试者的所有任务进行RQA计算

    流程:
    1. 扫描数据目录，获取所有CSV文件
    2. 生成文件列表 (control, mci, ad)
    3. 多线程并行处理每个文件
    4. 保存结果到CSV

    输出:
    - control_rqa_results.csv
    - mci_rqa_results.csv
    - ad_rqa_results.csv

    CSV格式:
    | subject_id | task_id | RR-1D-x | DET-1D-x | ENT-1D-x | RR-2D-xy | DET-2D-xy | ENT-2D-xy |
    """
    results = {'control': [], 'mci': [], 'ad': []}

    for group in groups:
        csv_files = scan_calibrated_files(group)

        # 多线程处理
        with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
            futures = [
                executor.submit(rqa_analyzer.analyze_single_file, file, params)
                for file in csv_files
            ]

            for future in as_completed(futures):
                result = future.result()
                results[group].append(result)

        # 保存结果
        df = pd.DataFrame(results[group])
        output_path = get_step_directory(params, 'step1_rqa_calculation')
        df.to_csv(output_path / f'{group}_rqa_results.csv', index=False)

    return {
        'success': True,
        'total_files_processed': sum(len(r) for r in results.values()),
        'output_files': [...]
    }
```

#### Step 2: 数据合并 (Data Merging)

**输入**:
- Step1的三个CSV文件

**处理**:
```python
def step2_data_merging(params: Dict) -> Dict:
    """
    合并三组数据，添加分组标签

    输出:
    - merged_data.csv

    CSV格式:
    | ID | Group | subject_id | task_id | RR-1D-x | ... | ENT-2D-xy |
    """
    step1_dir = get_step_directory(params, 'step1_rqa_calculation')

    # 读取三组数据
    control = pd.read_csv(step1_dir / 'control_rqa_results.csv')
    mci = pd.read_csv(step1_dir / 'mci_rqa_results.csv')
    ad = pd.read_csv(step1_dir / 'ad_rqa_results.csv')

    # 添加分组标签
    control['Group'] = 'Control'
    mci['Group'] = 'MCI'
    ad['Group'] = 'AD'

    # 生成ID
    control['ID'] = control['subject_id'] + '_' + control['task_id']
    mci['ID'] = mci['subject_id'] + '_' + mci['task_id']
    ad['ID'] = ad['subject_id'] + '_' + ad['task_id']

    # 合并
    merged = pd.concat([control, mci, ad], ignore_index=True)

    # 保存
    step2_dir = get_step_directory(params, 'step2_data_merging')
    merged.to_csv(step2_dir / 'merged_data.csv', index=False)

    return {'success': True, 'total_records': len(merged)}
```

#### Step 3: 特征增强 (Feature Enrichment)

**输入**:
- Step2的merged_data.csv
- Module04的事件分析结果
- 受试者MMSE信息

**处理**:
```python
def step3_feature_enrichment(params: Dict) -> Dict:
    """
    增强特征：合并事件分析数据和受试者信息

    输出:
    - enriched_features.csv

    增加的列:
    - fixation_count, saccade_count (来自Module04)
    - avg_fixation_duration, avg_saccade_amplitude
    - roi_bg_ratio, roi_inst_ratio, roi_kw_ratio
    - mmse_total_score, mmse_orientation, mmse_memory, etc.
    - age, education_level
    """
    step2_dir = get_step_directory(params, 'step2_data_merging')
    merged = pd.read_csv(step2_dir / 'merged_data.csv')

    # 1. 合并Module04事件数据
    event_features = load_event_features()  # 从Module04缓存加载
    enriched = merged.merge(event_features,
                           on=['subject_id', 'task_id'],
                           how='left')

    # 2. 合并MMSE数据
    mmse_data = load_mmse_data()  # 从SubjectManager加载
    enriched = enriched.merge(mmse_data,
                             on='subject_id',
                             how='left')

    # 3. 计算衍生特征
    enriched['rqa_complexity_1d'] = (
        enriched['DET-1D-x'] * enriched['ENT-1D-x']
    )
    enriched['rqa_complexity_2d'] = (
        enriched['DET-2D-xy'] * enriched['ENT-2D-xy']
    )

    # 保存
    step3_dir = get_step_directory(params, 'step3_feature_enrichment')
    enriched.to_csv(step3_dir / 'enriched_features.csv', index=False)

    return {'success': True, 'features_count': len(enriched.columns)}
```

#### Step 4: 统计分析 (Statistical Analysis)

**输入**:
- Step3的enriched_features.csv

**处理**:
```python
def step4_statistical_analysis(params: Dict) -> Dict:
    """
    统计分析：描述性统计 + 组间比较

    输出:
    - descriptive_stats.csv (各组均值、标准差)
    - group_comparison.csv (ANOVA/t-test结果)
    - correlation_matrix.csv (特征相关性)
    """
    step3_dir = get_step_directory(params, 'step3_feature_enrichment')
    data = pd.read_csv(step3_dir / 'enriched_features.csv')

    # 1. 描述性统计
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    desc_stats = data.groupby('Group')[numeric_cols].agg(['mean', 'std', 'min', 'max'])

    # 2. 组间比较（ANOVA）
    from scipy.stats import f_oneway
    comparison_results = []

    for col in numeric_cols:
        control_vals = data[data['Group'] == 'Control'][col].dropna()
        mci_vals = data[data['Group'] == 'MCI'][col].dropna()
        ad_vals = data[data['Group'] == 'AD'][col].dropna()

        if len(control_vals) > 0 and len(mci_vals) > 0 and len(ad_vals) > 0:
            f_stat, p_value = f_oneway(control_vals, mci_vals, ad_vals)
            comparison_results.append({
                'feature': col,
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            })

    # 3. 相关性矩阵
    corr_matrix = data[numeric_cols].corr()

    # 保存
    step4_dir = get_step_directory(params, 'step4_statistical_analysis')
    desc_stats.to_csv(step4_dir / 'descriptive_stats.csv')
    pd.DataFrame(comparison_results).to_csv(step4_dir / 'group_comparison.csv', index=False)
    corr_matrix.to_csv(step4_dir / 'correlation_matrix.csv')

    return {
        'success': True,
        'significant_features': sum(r['significant'] for r in comparison_results)
    }
```

#### Step 5: 可视化 (Visualization)

**输入**:
- 前4步的所有数据

**处理**:
```python
def step5_visualization(params: Dict) -> Dict:
    """
    生成可视化图表

    输出:
    - recurrence_plots/ (递归图，每个受试者-任务一张)
    - time_series_plots/ (时间序列图)
    - statistical_plots/
      - group_comparison_boxplot.png
      - rqa_metrics_heatmap.png
      - correlation_matrix_heatmap.png
      - feature_distribution_violin.png
    """
    visualizer = RQAVisualizer()

    # 1. 递归图（抽样展示）
    sample_files = select_representative_samples(data, n=20)
    for file in sample_files:
        rp = compute_recurrence_matrix(file, params)
        plot = visualizer.plot_recurrence_matrix(rp, file)
        save_plot(plot, 'recurrence_plots', f'{file.stem}.png')

    # 2. 统计图表
    step4_dir = get_step_directory(params, 'step4_statistical_analysis')
    enriched_data = pd.read_csv(step3_dir / 'enriched_features.csv')

    # 组间比较箱线图
    visualizer.plot_group_comparison_boxplot(
        enriched_data,
        features=['RR-1D-x', 'DET-1D-x', 'ENT-1D-x']
    )

    # RQA指标热力图
    visualizer.plot_rqa_heatmap(enriched_data)

    # 相关性矩阵
    corr_matrix = pd.read_csv(step4_dir / 'correlation_matrix.csv', index_col=0)
    visualizer.plot_correlation_heatmap(corr_matrix)

    return {
        'success': True,
        'plots_generated': count_generated_plots()
    }
```

### 4.2 RQA核心算法

#### 4.2.1 相空间重构 (Phase Space Reconstruction)

**1D嵌入**:
```python
def embed_signal_1d(x: np.ndarray, m: int, tau: int) -> np.ndarray:
    """
    1D时间延迟嵌入

    Args:
        x: 1D信号，shape=(N,)
        m: 嵌入维度
        tau: 时间延迟

    Returns:
        嵌入矩阵，shape=(N-(m-1)*tau, m)

    Example:
        x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = 3, tau = 2

        embedded = [
            [0, 2, 4],  # i=0: x[0], x[2], x[4]
            [1, 3, 5],  # i=1: x[1], x[3], x[5]
            [2, 4, 6],  # i=2: x[2], x[4], x[6]
            [3, 5, 7],  # i=3: x[3], x[5], x[7]
            [4, 6, 8],  # i=4: x[4], x[6], x[8]
            [5, 7, 9],  # i=5: x[5], x[7], x[9]
        ]
    """
    N = len(x)
    rows = N - (m - 1) * tau

    if rows <= 0:
        raise ValueError(f"信号太短：N={N}, m={m}, tau={tau}")

    embedded = np.zeros((rows, m))
    for i in range(rows):
        for j in range(m):
            embedded[i, j] = x[i + j * tau]

    return embedded
```

**2D嵌入**:
```python
def embed_signal_2d(x: np.ndarray, y: np.ndarray,
                   m: int, tau: int) -> np.ndarray:
    """
    2D时间延迟嵌入

    Args:
        x, y: 2D轨迹，shape=(N,)
        m: 嵌入维度
        tau: 时间延迟

    Returns:
        嵌入矩阵，shape=(N-(m-1)*tau, 2*m)

    Example:
        x = [0, 1, 2, 3, 4]
        y = [5, 6, 7, 8, 9]
        m = 2, tau = 1

        embedded = [
            [0, 5, 1, 6],  # i=0: (x[0],y[0]), (x[1],y[1])
            [1, 6, 2, 7],  # i=1: (x[1],y[1]), (x[2],y[2])
            [2, 7, 3, 8],  # i=2: (x[2],y[2]), (x[3],y[3])
            [3, 8, 4, 9],  # i=3: (x[3],y[3]), (x[4],y[4])
        ]
    """
    N = len(x)
    if len(y) != N:
        raise ValueError("x和y长度必须相同")

    rows = N - (m - 1) * tau
    if rows <= 0:
        raise ValueError(f"信号太短：N={N}, m={m}, tau={tau}")

    embedded = np.zeros((rows, 2 * m))
    for i in range(rows):
        for j in range(m):
            embedded[i, 2*j] = x[i + j * tau]
            embedded[i, 2*j + 1] = y[i + j * tau]

    return embedded
```

#### 4.2.2 递归矩阵计算 (Recurrence Matrix)

```python
def compute_recurrence_matrix(embedded: np.ndarray,
                             eps: float,
                             metric: str = '1d_abs') -> np.ndarray:
    """
    计算递归矩阵

    Args:
        embedded: 嵌入矩阵，shape=(M, d)
        eps: 递归阈值
        metric: 距离度量 ('1d_abs' 或 'euclidean')

    Returns:
        递归矩阵 RP，shape=(M, M)，值为0或1

    Definition:
        RP[i,j] = 1 if dist(embedded[i], embedded[j]) <= eps
                  0 otherwise
    """
    M = embedded.shape[0]
    RP = np.zeros((M, M), dtype=np.int8)

    if metric == '1d_abs':
        # 1D：绝对差之和
        for i in range(M):
            for j in range(M):
                dist = np.sum(np.abs(embedded[i] - embedded[j]))
                if dist <= eps:
                    RP[i, j] = 1

    elif metric == 'euclidean':
        # 欧几里得距离
        for i in range(M):
            for j in range(M):
                dist = np.sqrt(np.sum((embedded[i] - embedded[j])**2))
                if dist <= eps:
                    RP[i, j] = 1

    return RP
```

**优化版本（向量化）**:
```python
def compute_recurrence_matrix_vectorized(embedded: np.ndarray,
                                        eps: float,
                                        metric: str = 'euclidean') -> np.ndarray:
    """
    向量化版本（更快）

    使用scipy.spatial.distance.pdist + squareform
    """
    from scipy.spatial.distance import pdist, squareform

    if metric == '1d_abs':
        # 曼哈顿距离（L1范数）
        dist_matrix = squareform(pdist(embedded, metric='cityblock'))
    else:
        # 欧几里得距离（L2范数）
        dist_matrix = squareform(pdist(embedded, metric='euclidean'))

    RP = (dist_matrix <= eps).astype(np.int8)
    return RP
```

#### 4.2.3 RQA指标计算

**对角线提取**:
```python
def extract_diagonal_lengths(RP: np.ndarray) -> Dict[int, int]:
    """
    提取对角线中连续1的长度分布

    Args:
        RP: 递归矩阵，shape=(M, M)

    Returns:
        {长度: 出现次数}

    Example:
        RP = [
            [1, 1, 0, 0],
            [1, 1, 1, 0],
            [0, 1, 1, 1],
            [0, 0, 1, 1]
        ]

        对角线d=-3: [0]           -> 无连续段
        对角线d=-2: [0, 0]         -> 无连续段
        对角线d=-1: [1, 1, 1]      -> 一段长度3
        对角线d=0:  [1, 1, 1, 1]   -> 一段长度4
        对角线d=1:  [1, 1, 1]      -> 一段长度3
        对角线d=2:  [0, 0]         -> 无连续段
        对角线d=3:  [0]            -> 无连续段

        结果: {3: 2, 4: 1}  # 长度3出现2次，长度4出现1次
    """
    M = RP.shape[0]
    length_counts = {}

    # 遍历所有对角线
    for d in range(-(M-1), M):
        diagonal = []
        for i in range(M):
            j = i + d
            if 0 <= j < M:
                diagonal.append(RP[i, j])

        # 提取连续1的长度
        idx = 0
        while idx < len(diagonal):
            if diagonal[idx] == 1:
                length = 1
                idx += 1
                while idx < len(diagonal) and diagonal[idx] == 1:
                    length += 1
                    idx += 1
                length_counts[length] = length_counts.get(length, 0) + 1
            else:
                idx += 1

    return length_counts
```

**RQA指标**:
```python
def compute_rqa_metrics(RP: np.ndarray, lmin: int = 2) -> Dict[str, float]:
    """
    计算RQA指标

    Args:
        RP: 递归矩阵
        lmin: 最小线长

    Returns:
        {
            'RR': float,   # Recurrence Rate
            'DET': float,  # Determinism
            'ENT': float   # Entropy
        }
    """
    M = RP.shape[0]

    # 1. RR: 递归率 = 递归点数量 / 总点数
    total_points = M * M
    recurrence_points = np.sum(RP)
    RR = recurrence_points / total_points

    # 2. 提取对角线长度分布
    length_counts = extract_diagonal_lengths(RP)

    # 计算总长度
    total_length = sum(length * count for length, count in length_counts.items())

    # 3. DET: 确定性 = (长度>=lmin的对角线长度之和) / (所有对角线长度之和)
    det_length = sum(
        length * count
        for length, count in length_counts.items()
        if length >= lmin
    )
    DET = det_length / total_length if total_length > 0 else 0.0

    # 4. ENT: 熵 = -Σ p(l) * log2(p(l))  (对于l >= lmin)
    # p(l) = 长度为l的对角线段数 / 长度>=lmin的对角线段总数
    total_lines_lmin = sum(
        count
        for length, count in length_counts.items()
        if length >= lmin
    )

    ENT = 0.0
    if total_lines_lmin > 0:
        for length, count in length_counts.items():
            if length >= lmin:
                p_l = count / total_lines_lmin
                if p_l > 1e-12:  # 避免log(0)
                    ENT += -p_l * np.log2(p_l)

    return {
        'RR': RR,
        'DET': DET,
        'ENT': ENT
    }
```

---

## 5. 数据流设计

### 5.1 数据流转图

```
┌────────────────────────────────────────────────────────────┐
│  用户输入参数                                               │
│  - m: [1, 10, 1]                                           │
│  - tau: [1, 10, 1]                                         │
│  - eps: [0.05, 0.1, 0.001]                                 │
│  - lmin: [2, 3, 1]                                         │
└────────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  参数组合生成器                                             │
│  - 生成10,200个参数组合                                     │
│  - 检查缓存，跳过已完成的组合                               │
└────────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  任务调度器                                                 │
│  - 创建任务队列                                             │
│  - 分配给线程池                                             │
│  - 监控进度                                                 │
└────────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────┐              ┌──────────────┐
│ 线程1        │  ...         │ 线程N        │
│ - 参数组合1  │              │ - 参数组合N  │
└──────────────┘              └──────────────┘
        ↓                               ↓
        └───────────────┬───────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  单个参数组合处理                                           │
│  For params in param_combinations:                         │
│    1. 加载校准后数据                                        │
│    2. 1D嵌入 + 递归矩阵 + RQA指标                          │
│    3. 2D嵌入 + 递归矩阵 + RQA指标                          │
│    4. 保存结果                                              │
└────────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  结果聚合                                                   │
│  - 收集所有线程结果                                         │
│  - 生成CSV文件                                              │
│  - 更新进度                                                 │
└────────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  5步流程执行                                                │
│  Step 1: RQA计算 → CSV                                     │
│  Step 2: 数据合并 → CSV                                    │
│  Step 3: 特征增强 → CSV                                    │
│  Step 4: 统计分析 → CSV + 图表                             │
│  Step 5: 可视化 → 图片                                     │
└────────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────────┐
│  结果返回                                                   │
│  - 任务ID                                                  │
│  - 完成进度                                                 │
│  - 结果路径                                                 │
│  - 预览图表                                                 │
└────────────────────────────────────────────────────────────┘
```

### 5.2 数据结构定义

#### 5.2.1 参数组合

```python
@dataclass
class RQAParams:
    """RQA参数"""
    m: int              # 嵌入维度
    tau: int            # 时间延迟
    eps: float          # 递归阈值
    lmin: int           # 最小线长

    def to_dict(self) -> Dict:
        return {
            'm': self.m,
            'tau': self.tau,
            'eps': self.eps,
            'lmin': self.lmin
        }

    def signature(self) -> str:
        """生成唯一签名"""
        return f"m{self.m}_tau{self.tau}_eps{self.eps}_lmin{self.lmin}"
```

#### 5.2.2 分析结果

```python
@dataclass
class RQAResult:
    """单文件RQA结果"""
    subject_id: str
    task_id: str
    group: str

    # 1D指标
    rr_1d: float
    det_1d: float
    ent_1d: float

    # 2D指标
    rr_2d: float
    det_2d: float
    ent_2d: float

    # 元数据
    params: RQAParams
    processing_time: float
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            'subject_id': self.subject_id,
            'task_id': self.task_id,
            'group': self.group,
            'RR-1D-x': self.rr_1d,
            'DET-1D-x': self.det_1d,
            'ENT-1D-x': self.ent_1d,
            'RR-2D-xy': self.rr_2d,
            'DET-2D-xy': self.det_2d,
            'ENT-2D-xy': self.ent_2d,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp
        }
```

#### 5.2.3 任务状态

```python
@dataclass
class TaskStatus:
    """批量任务状态"""
    task_id: str
    params: RQAParams
    total_files: int
    processed_files: int
    failed_files: int
    current_step: int  # 1-5
    status: str  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    start_time: datetime
    end_time: Optional[datetime]
    error_message: Optional[str]

    @property
    def progress(self) -> float:
        """进度百分比"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

    @property
    def eta(self) -> Optional[timedelta]:
        """预计剩余时间"""
        if self.processed_files == 0:
            return None

        elapsed = (datetime.now() - self.start_time).total_seconds()
        avg_time_per_file = elapsed / self.processed_files
        remaining_files = self.total_files - self.processed_files

        return timedelta(seconds=avg_time_per_file * remaining_files)
```

---

## 6. API接口设计

### 6.1 API端点列表

| 端点 | 方法 | 功能 | 装饰器 |
|------|------|------|--------|
| `/api/m05/health` | GET | 健康检查 | - |
| `/api/m05/params/generate` | POST | 生成参数组合 | `@validate_params`, `@handle_api_errors` |
| `/api/m05/params/history` | GET | 获取参数历史 | `@handle_api_errors` |
| `/api/m05/analyze/batch` | POST | 批量RQA分析 | `@validate_params`, `@handle_api_errors` |
| `/api/m05/analyze/status` | GET | 查询任务状态 | `@validate_params`, `@handle_api_errors` |
| `/api/m05/analyze/cancel` | POST | 取消任务 | `@validate_params`, `@handle_api_errors` |
| `/api/m05/results/list` | GET | 列出结果 | `@handle_api_errors` |
| `/api/m05/results/download` | GET | 下载结果 | `@validate_params`, `@handle_api_errors` |
| `/api/m05/results/preview` | GET | 预览结果 | `@validate_params`, `@handle_api_errors` |
| `/api/m05/visualize/recurrence-plot` | POST | 生成递归图 | `@validate_params`, `@handle_api_errors` |
| `/api/m05/visualize/statistics` | GET | 统计图表 | `@validate_params`, `@handle_api_errors` |

### 6.2 详细接口规范

#### 6.2.1 生成参数组合

```python
@m05_bp.route('/params/generate', methods=['POST'])
@validate_params('m_range', 'tau_range', 'eps_range', 'lmin_range')
@handle_api_errors
def generate_param_combinations():
    """
    生成参数组合空间

    Request Body:
    {
        "m_range": {
            "start": 1,
            "end": 10,
            "step": 1
        },
        "tau_range": {
            "start": 1,
            "end": 10,
            "step": 1
        },
        "eps_range": {
            "start": 0.05,
            "end": 0.1,
            "step": 0.001
        },
        "lmin_range": {
            "start": 2,
            "end": 3,
            "step": 1
        }
    }

    Response:
    {
        "success": true,
        "total_combinations": 10200,
        "combinations": [
            {"m": 1, "tau": 1, "eps": 0.05, "lmin": 2},
            {"m": 1, "tau": 1, "eps": 0.051, "lmin": 2},
            ...
        ],
        "estimated_time_minutes": 340
    }
    """
    data = request.get_json()

    service = get_service()
    result = service.generate_param_combinations(
        m_range=data['m_range'],
        tau_range=data['tau_range'],
        eps_range=data['eps_range'],
        lmin_range=data['lmin_range']
    )

    return jsonify(result)
```

#### 6.2.2 批量RQA分析

```python
@m05_bp.route('/analyze/batch', methods=['POST'])
@validate_params('param_combinations', 'groups')
@handle_api_errors
@monitor_performance  # 新增性能监控装饰器
def analyze_batch():
    """
    批量RQA分析（异步）

    Request Body:
    {
        "param_combinations": [
            {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
            ...
        ],
        "groups": ["control", "mci", "ad"],
        "execute_steps": [1, 2, 3, 4, 5],  // 可选：指定执行哪些步骤
        "max_workers": 8  // 可选：最大线程数
    }

    Response:
    {
        "success": true,
        "task_id": "rqa_20251007_153045_abc123",
        "total_combinations": 10200,
        "estimated_time_minutes": 340,
        "message": "任务已启动，请使用task_id查询进度"
    }
    """
    data = request.get_json()

    service = get_service()
    result = service.analyze_batch(
        param_combinations=data['param_combinations'],
        groups=data['groups'],
        execute_steps=data.get('execute_steps', [1, 2, 3, 4, 5]),
        max_workers=data.get('max_workers')
    )

    return jsonify(result)
```

#### 6.2.3 查询任务状态

```python
@m05_bp.route('/analyze/status', methods=['GET'])
@validate_params('task_id')
@handle_api_errors
def get_task_status():
    """
    查询任务状态

    Query Parameters:
        task_id: 任务ID

    Response:
    {
        "success": true,
        "task_id": "rqa_20251007_153045_abc123",
        "status": "running",  // pending, running, completed, failed, cancelled
        "progress": 45.2,  // 百分比
        "current_step": 1,
        "total_files": 500,
        "processed_files": 226,
        "failed_files": 3,
        "start_time": "2025-10-07T15:30:45",
        "elapsed_time_seconds": 1234,
        "eta_seconds": 1500,
        "current_param": {"m": 2, "tau": 3, "eps": 0.056, "lmin": 2},
        "errors": [
            {"file": "control_legacy_10_q4_calibrated.csv", "error": "..."}
        ]
    }
    """
    task_id = request.args.get('task_id')

    service = get_service()
    status = service.get_task_status(task_id)

    return jsonify(status)
```

#### 6.2.4 生成递归图

```python
@m05_bp.route('/visualize/recurrence-plot', methods=['POST'])
@validate_params('subject_id', 'task_id', 'params')
@handle_api_errors
def generate_recurrence_plot():
    """
    生成单个受试者-任务的递归图

    Request Body:
    {
        "subject_id": "control_legacy_1",
        "task_id": "q1",
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "mode": "1d"  // '1d' or '2d'
    }

    Response:
    {
        "success": true,
        "plot_base64": "iVBORw0KGgoAAAANSUh...",  // PNG图片的base64编码
        "metrics": {
            "RR": 0.234,
            "DET": 0.876,
            "ENT": 2.345
        },
        "embedding_info": {
            "original_length": 500,
            "embedded_length": 498,
            "embedding_dim": 2
        }
    }
    """
    data = request.get_json()

    service = get_service()
    result = service.generate_recurrence_plot(
        subject_id=data['subject_id'],
        task_id=data['task_id'],
        params=data['params'],
        mode=data.get('mode', '1d')
    )

    return jsonify(result)
```

---

## 7. 并行处理设计

### 7.1 多线程架构

```python
class RQATaskExecutor:
    """CPU多线程任务执行器"""

    def __init__(self, max_workers: int = None):
        """
        初始化执行器

        Args:
            max_workers: 最大线程数，默认为CPU核心数
        """
        from multiprocessing import cpu_count

        self.max_workers = max_workers or cpu_count()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # 任务管理
        self.active_tasks = {}  # {task_id: Future}
        self.task_status = {}   # {task_id: TaskStatus}

        # 线程安全的进度计数器
        self.progress_lock = threading.Lock()

        logger.info(f"RQATaskExecutor initialized: max_workers={self.max_workers}")

    def submit_batch_task(self, task_id: str,
                         param_combinations: List[Dict],
                         groups: List[str],
                         callback: Callable = None) -> str:
        """
        提交批量任务

        Args:
            task_id: 任务ID
            param_combinations: 参数组合列表
            groups: 分组列表
            callback: 完成回调函数

        Returns:
            task_id
        """
        # 初始化任务状态
        total_files = self._count_total_files(groups)
        self.task_status[task_id] = TaskStatus(
            task_id=task_id,
            params=param_combinations[0],  # 第一个参数组合
            total_files=total_files * len(param_combinations),
            processed_files=0,
            failed_files=0,
            current_step=1,
            status='pending',
            start_time=datetime.now(),
            end_time=None,
            error_message=None
        )

        # 提交到线程池
        future = self.executor.submit(
            self._execute_batch_task,
            task_id,
            param_combinations,
            groups
        )

        # 添加完成回调
        if callback:
            future.add_done_callback(callback)

        self.active_tasks[task_id] = future
        self.task_status[task_id].status = 'running'

        return task_id

    def _execute_batch_task(self, task_id: str,
                           param_combinations: List[Dict],
                           groups: List[str]):
        """
        执行批量任务（在线程中运行）

        流程:
        1. 遍历所有参数组合
        2. 对每个组合，并行处理所有文件
        3. 更新进度
        4. 执行5步流程
        """
        try:
            for param_idx, params in enumerate(param_combinations):
                logger.info(f"Task {task_id}: Processing param {param_idx+1}/{len(param_combinations)}")

                # 更新当前参数
                self.task_status[task_id].current_param = params

                # Step 1: RQA计算（并行处理文件）
                self._execute_step1_parallel(task_id, params, groups)

                # Step 2-5: 数据处理（串行）
                self._execute_step2(task_id, params)
                self._execute_step3(task_id, params)
                self._execute_step4(task_id, params)
                self._execute_step5(task_id, params)

            # 标记完成
            self.task_status[task_id].status = 'completed'
            self.task_status[task_id].end_time = datetime.now()

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            self.task_status[task_id].status = 'failed'
            self.task_status[task_id].error_message = str(e)
            self.task_status[task_id].end_time = datetime.now()

    def _execute_step1_parallel(self, task_id: str, params: Dict, groups: List[str]):
        """
        Step 1: 并行RQA计算

        策略:
        - 将所有CSV文件分成batch
        - 每个batch提交给线程池
        - 等待所有batch完成
        """
        from concurrent.futures import as_completed

        results = {group: [] for group in groups}

        for group in groups:
            # 扫描文件
            csv_files = self._scan_calibrated_files(group)
            logger.info(f"Task {task_id}: Found {len(csv_files)} files for group {group}")

            # 批量提交到线程池
            batch_size = 10  # 每次提交10个文件
            futures = []

            for i in range(0, len(csv_files), batch_size):
                batch = csv_files[i:i+batch_size]
                future = self.executor.submit(
                    self._process_file_batch,
                    task_id,
                    batch,
                    params
                )
                futures.append(future)

            # 收集结果
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results[group].extend(batch_results)

                    # 更新进度
                    with self.progress_lock:
                        self.task_status[task_id].processed_files += len(batch_results)

                except Exception as e:
                    logger.error(f"Batch processing failed: {e}")
                    with self.progress_lock:
                        self.task_status[task_id].failed_files += batch_size

            # 保存该组结果
            df = pd.DataFrame(results[group])
            output_dir = get_step_directory(params, 'step1_rqa_calculation')
            df.to_csv(output_dir / f'{group}_rqa_results.csv', index=False)
            logger.info(f"Task {task_id}: Saved {len(results[group])} results for group {group}")

    def _process_file_batch(self, task_id: str,
                           files: List[Path],
                           params: Dict) -> List[Dict]:
        """
        处理一批文件（在单个线程中）

        Args:
            task_id: 任务ID
            files: 文件路径列表
            params: RQA参数

        Returns:
            结果列表
        """
        from .rqa_analyzer import RQAAnalyzer

        analyzer = RQAAnalyzer()
        results = []

        for file_path in files:
            try:
                result = analyzer.analyze_single_file(str(file_path), params)
                results.append(result)

            except Exception as e:
                logger.error(f"File {file_path} analysis failed: {e}")
                # 继续处理下一个文件，不中断整个batch

        return results

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        注意: 已经在运行的线程无法立即取消，
        但会设置标志位，线程会在下一个检查点退出
        """
        if task_id in self.active_tasks:
            future = self.active_tasks[task_id]
            cancelled = future.cancel()

            if cancelled or self.task_status[task_id].status == 'running':
                self.task_status[task_id].status = 'cancelled'
                self.task_status[task_id].end_time = datetime.now()
                return True

        return False
```

### 7.2 性能优化策略

#### 7.2.1 批处理策略

```python
# 策略1: 动态batch大小
def calculate_optimal_batch_size(file_count: int,
                                 max_workers: int) -> int:
    """
    根据文件数量和线程数计算最优batch大小

    原则:
    - batch太小: 提交开销大
    - batch太大: 负载不均衡
    - 最优: batch_count = 2-4 * max_workers
    """
    target_batches = max_workers * 3
    batch_size = max(1, file_count // target_batches)
    return batch_size

# 策略2: 优先级队列
class PriorityTaskQueue:
    """优先级任务队列"""

    def __init__(self):
        self.queue = PriorityQueue()

    def add_task(self, file_path: Path, priority: int = 0):
        """
        添加任务

        优先级规则:
        - 小文件优先 (处理快，提升响应速度)
        - 失败过的文件延后
        """
        file_size = file_path.stat().st_size
        # 小文件 = 高优先级 (数值越小越优先)
        adjusted_priority = priority + (file_size // 1024)

        self.queue.put((adjusted_priority, file_path))

    def get_batch(self, batch_size: int) -> List[Path]:
        """获取一批任务"""
        batch = []
        for _ in range(batch_size):
            if not self.queue.empty():
                _, file_path = self.queue.get()
                batch.append(file_path)
        return batch
```

#### 7.2.2 内存优化

```python
# 策略1: 流式处理
def analyze_file_streaming(csv_path: str, params: Dict) -> Dict:
    """
    流式处理大文件

    策略:
    - 使用pandas chunksize读取
    - 逐块计算嵌入
    - 增量构建递归矩阵
    """
    chunk_size = 10000
    all_embedded = []

    for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
        x = chunk['x'].values
        y = chunk['y'].values

        # 嵌入
        embedded = embed_signal_2d(x, y, params['m'], params['tau'])
        all_embedded.append(embedded)

        # 释放chunk内存
        del chunk, x, y

    # 合并嵌入
    final_embedded = np.vstack(all_embedded)
    del all_embedded

    # 计算递归矩阵（分块计算）
    rp = compute_recurrence_matrix_chunked(final_embedded, params['eps'])

    return compute_rqa_metrics(rp, params['lmin'])

# 策略2: 显式内存释放
import gc

def process_param_combination(params: Dict, files: List[Path]):
    """处理单个参数组合"""
    results = []

    for file_path in files:
        result = analyze_single_file(file_path, params)
        results.append(result)

        # 每处理10个文件，强制垃圾回收
        if len(results) % 10 == 0:
            gc.collect()

    return results
```

#### 7.2.3 CPU亲和性优化

```python
import os
import psutil

def set_cpu_affinity(worker_id: int, max_workers: int):
    """
    设置CPU亲和性，避免线程迁移

    策略:
    - 将线程绑定到特定CPU核心
    - 减少上下文切换
    - 提升缓存命中率
    """
    cpu_count = psutil.cpu_count(logical=True)

    # 为每个worker分配专属CPU核心
    assigned_cpus = [(worker_id * cpu_count) // max_workers]

    try:
        p = psutil.Process(os.getpid())
        p.cpu_affinity(assigned_cpus)
        logger.debug(f"Worker {worker_id} bound to CPU {assigned_cpus}")
    except Exception as e:
        logger.warning(f"Failed to set CPU affinity: {e}")
```

---

## 8. 数据持久化设计

### 8.1 目录结构

```
data/05_rqa_analysis/
├── cache/
│   ├── param_combinations.json          # 所有生成的参数组合
│   ├── task_history.json                # 任务历史记录
│   └── last_analysis.json               # 最近一次分析的缓存
│
├── results/
│   ├── m2_tau1_eps0.05_lmin2/           # 参数组合目录
│   │   ├── metadata.json                # 元数据
│   │   ├── step1_rqa_calculation/
│   │   │   ├── control_rqa_results.csv
│   │   │   ├── mci_rqa_results.csv
│   │   │   └── ad_rqa_results.csv
│   │   ├── step2_data_merging/
│   │   │   └── merged_data.csv
│   │   ├── step3_feature_enrichment/
│   │   │   └── enriched_features.csv
│   │   ├── step4_statistical_analysis/
│   │   │   ├── descriptive_stats.csv
│   │   │   ├── group_comparison.csv
│   │   │   └── correlation_matrix.csv
│   │   └── step5_visualization/
│   │       ├── recurrence_plots/
│   │       │   ├── control_legacy_1_q1.png
│   │       │   └── ...
│   │       ├── time_series_plots/
│   │       └── statistical_plots/
│   │           ├── group_comparison_boxplot.png
│   │           ├── rqa_heatmap.png
│   │           └── correlation_heatmap.png
│   │
│   ├── m2_tau1_eps0.051_lmin2/
│   └── ...
│
└── exports/
    ├── rqa_analysis_20251007_153045.xlsx  # 完整导出
    ├── rqa_analysis_20251007_153045.zip   # 打包下载
    └── summary_report_20251007.pdf        # 分析报告
```

### 8.2 元数据格式

```json
{
  "signature": "m2_tau1_eps0.05_lmin2",
  "parameters": {
    "m": 2,
    "tau": 1,
    "eps": 0.05,
    "lmin": 2
  },
  "creation_time": "2025-10-07T15:30:45",
  "last_updated": "2025-10-07T16:45:22",
  "steps_completed": {
    "step1_rqa_calculation": {
      "completed": true,
      "timestamp": "2025-10-07T15:45:12",
      "files_processed": 500,
      "files_failed": 3
    },
    "step2_data_merging": {
      "completed": true,
      "timestamp": "2025-10-07T15:46:00",
      "total_records": 497
    },
    "step3_feature_enrichment": {
      "completed": true,
      "timestamp": "2025-10-07T15:50:30",
      "features_added": 15
    },
    "step4_statistical_analysis": {
      "completed": true,
      "timestamp": "2025-10-07T16:00:00",
      "significant_features": 8
    },
    "step5_visualization": {
      "completed": true,
      "timestamp": "2025-10-07T16:45:22",
      "plots_generated": 45
    }
  },
  "statistics": {
    "total_processing_time_seconds": 4537,
    "avg_time_per_file_seconds": 2.1,
    "memory_peak_mb": 1024
  },
  "errors": [
    {
      "step": 1,
      "file": "control_legacy_10_q4_calibrated.csv",
      "error": "Signal too short for embedding",
      "timestamp": "2025-10-07T15:35:12"
    }
  ]
}
```

### 8.3 增量缓存策略

```python
class RQACache:
    """RQA结果缓存管理器"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.param_cache_file = cache_dir / 'param_combinations.json'
        self.task_history_file = cache_dir / 'task_history.json'

    def is_param_completed(self, params: Dict, step: int = 5) -> bool:
        """
        检查参数组合是否已完成指定步骤

        Args:
            params: RQA参数
            step: 步骤编号 (1-5)

        Returns:
            是否已完成
        """
        signature = generate_param_signature(params)
        param_dir = get_param_directory(params)
        metadata_file = param_dir / 'metadata.json'

        if not metadata_file.exists():
            return False

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        step_key = f'step{step}_{"_".join(["rqa_calculation", "data_merging", "feature_enrichment", "statistical_analysis", "visualization"][step-1].split())}'
        return metadata.get('steps_completed', {}).get(step_key, {}).get('completed', False)

    def get_completed_params(self, all_params: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        分离已完成和未完成的参数组合

        Args:
            all_params: 所有参数组合

        Returns:
            (completed, pending)
        """
        completed = []
        pending = []

        for params in all_params:
            if self.is_param_completed(params, step=5):
                completed.append(params)
            else:
                pending.append(params)

        return completed, pending

    def save_partial_result(self, params: Dict, step: int, data: Dict):
        """
        保存部分结果（断点续传）

        Args:
            params: RQA参数
            step: 当前步骤
            data: 结果数据
        """
        param_dir = get_param_directory(params)
        partial_file = param_dir / f'step{step}_partial.json'

        with open(partial_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved partial result for step {step}: {partial_file}")

    def load_partial_result(self, params: Dict, step: int) -> Optional[Dict]:
        """加载部分结果"""
        param_dir = get_param_directory(params)
        partial_file = param_dir / f'step{step}_partial.json'

        if not partial_file.exists():
            return None

        with open(partial_file, 'r', encoding='utf-8') as f:
            return json.load(f)
```

---

## 9. 前端交互设计

### 9.1 页面布局

```jsx
// Module05.jsx
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Tabs, Button, Progress, message } from 'antd';

const Module05 = () => {
  return (
    <div className="module05-container">
      <Tabs defaultActiveKey="1">
        {/* Tab 1: 参数配置 */}
        <Tabs.TabPane tab="参数配置" key="1">
          <ParamConfigPanel />
        </Tabs.TabPane>

        {/* Tab 2: 批量执行 */}
        <Tabs.TabPane tab="批量执行" key="2">
          <BatchExecutionPanel />
        </Tabs.TabPane>

        {/* Tab 3: 结果查看 */}
        <Tabs.TabPane tab="结果查看" key="3">
          <ResultsViewer />
        </Tabs.TabPane>

        {/* Tab 4: 可视化 */}
        <Tabs.TabPane tab="可视化分析" key="4">
          <VisualizationPanel />
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
};
```

### 9.2 参数配置组件

```jsx
const ParamConfigPanel = () => {
  const [paramRanges, setParamRanges] = useState({
    m: { start: 1, end: 10, step: 1 },
    tau: { start: 1, end: 10, step: 1 },
    eps: { start: 0.05, end: 0.1, step: 0.001 },
    lmin: { start: 2, end: 3, step: 1 }
  });

  const [totalCombinations, setTotalCombinations] = useState(0);

  useEffect(() => {
    calculateTotalCombinations();
  }, [paramRanges]);

  const calculateTotalCombinations = () => {
    const { m, tau, eps, lmin } = paramRanges;
    const total =
      Math.floor((m.end - m.start) / m.step + 1) *
      Math.floor((tau.end - tau.start) / tau.step + 1) *
      Math.floor((eps.end - eps.start) / eps.step + 1) *
      Math.floor((lmin.end - lmin.start) / lmin.step + 1);

    setTotalCombinations(total);
  };

  const handleGenerate = async () => {
    try {
      const response = await axios.post('/api/m05/params/generate', {
        m_range: paramRanges.m,
        tau_range: paramRanges.tau,
        eps_range: paramRanges.eps,
        lmin_range: paramRanges.lmin
      });

      if (response.data.success) {
        message.success(`成功生成 ${response.data.total_combinations} 个参数组合`);
      }
    } catch (error) {
      message.error('生成参数组合失败');
    }
  };

  return (
    <Card title="RQA参数配置">
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <ParamRangeInput
            label="嵌入维度 (m)"
            value={paramRanges.m}
            onChange={(val) => setParamRanges({...paramRanges, m: val})}
          />
        </Col>
        <Col span={6}>
          <ParamRangeInput
            label="时间延迟 (τ)"
            value={paramRanges.tau}
            onChange={(val) => setParamRanges({...paramRanges, tau: val})}
          />
        </Col>
        <Col span={6}>
          <ParamRangeInput
            label="递归阈值 (ε)"
            value={paramRanges.eps}
            onChange={(val) => setParamRanges({...paramRanges, eps: val})}
            step={0.001}
          />
        </Col>
        <Col span={6}>
          <ParamRangeInput
            label="最小线长 (lmin)"
            value={paramRanges.lmin}
            onChange={(val) => setParamRanges({...paramRanges, lmin: val})}
          />
        </Col>
      </Row>

      <div style={{marginTop: 24, textAlign: 'center'}}>
        <h3>预计生成: <span style={{color: '#1890ff', fontSize: 32}}>{totalCombinations.toLocaleString()}</span> 个参数组合</h3>
        <Button type="primary" size="large" onClick={handleGenerate}>
          生成参数组合
        </Button>
      </div>
    </Card>
  );
};
```

### 9.3 批量执行面板

```jsx
const BatchExecutionPanel = () => {
  const [taskStatus, setTaskStatus] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  // 轮询任务状态
  useEffect(() => {
    let interval;
    if (isRunning && taskStatus?.task_id) {
      interval = setInterval(async () => {
        const response = await axios.get('/api/m05/analyze/status', {
          params: { task_id: taskStatus.task_id }
        });

        setTaskStatus(response.data);

        if (response.data.status === 'completed' ||
            response.data.status === 'failed') {
          setIsRunning(false);
          clearInterval(interval);
        }
      }, 2000);  // 每2秒更新一次
    }

    return () => clearInterval(interval);
  }, [isRunning, taskStatus?.task_id]);

  const handleStartAnalysis = async () => {
    try {
      const response = await axios.post('/api/m05/analyze/batch', {
        param_combinations: [...],  // 从状态获取
        groups: ['control', 'mci', 'ad'],
        execute_steps: [1, 2, 3, 4, 5]
      });

      if (response.data.success) {
        setTaskStatus(response.data);
        setIsRunning(true);
        message.success('分析任务已启动');
      }
    } catch (error) {
      message.error('启动分析失败');
    }
  };

  const handleCancelAnalysis = async () => {
    try {
      await axios.post('/api/m05/analyze/cancel', {
        task_id: taskStatus.task_id
      });

      setIsRunning(false);
      message.info('任务已取消');
    } catch (error) {
      message.error('取消任务失败');
    }
  };

  return (
    <Card title="批量执行">
      {!isRunning ? (
        <Button type="primary" size="large" onClick={handleStartAnalysis}>
          开始批量分析
        </Button>
      ) : (
        <div>
          <h3>任务进度</h3>
          <Progress
            percent={taskStatus?.progress || 0}
            status={taskStatus?.status === 'failed' ? 'exception' : 'active'}
          />

          <Row gutter={[16, 16]} style={{marginTop: 16}}>
            <Col span={8}>
              <Statistic
                title="已处理文件"
                value={taskStatus?.processed_files || 0}
                suffix={`/ ${taskStatus?.total_files || 0}`}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="当前步骤"
                value={`Step ${taskStatus?.current_step || 1}`}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="预计剩余时间"
                value={formatETA(taskStatus?.eta_seconds)}
              />
            </Col>
          </Row>

          <div style={{marginTop: 16}}>
            <Button danger onClick={handleCancelAnalysis}>
              取消任务
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
};
```

---

## 10. 性能优化策略

### 10.1 计算优化

| 优化项 | 策略 | 预期提升 |
|--------|------|----------|
| **向量化计算** | 使用NumPy向量化代替Python循环 | 10-50x |
| **距离矩阵计算** | 使用scipy.spatial.distance.pdist | 5-10x |
| **内存对齐** | 使用np.ascontiguousarray | 1.2-1.5x |
| **数据类型优化** | RP矩阵使用int8而非int32/int64 | 减少75%内存 |
| **稀疏矩阵** | 对于低RR矩阵使用scipy.sparse | 减少50-90%内存 |

### 10.2 I/O优化

```python
# 策略1: 批量读取
def load_files_batch(file_paths: List[Path],
                    columns: List[str] = None) -> Dict[Path, pd.DataFrame]:
    """
    批量读取CSV文件

    优势:
    - 减少磁盘I/O次数
    - 利用操作系统预读缓存
    """
    data = {}
    for path in file_paths:
        df = pd.read_csv(path, usecols=columns)  # 只读取需要的列
        data[path] = df
    return data

# 策略2: 列选择
# 只读取x, y列，忽略其他列
df = pd.read_csv(csv_path, usecols=['x', 'y', 'milliseconds'])

# 策略3: 压缩保存
df.to_csv(output_path, compression='gzip')  # 减少50-70%磁盘空间
```

### 10.3 并行度调优

```python
def get_optimal_workers(task_type: str) -> int:
    """
    根据任务类型确定最优线程数

    Args:
        task_type: 'cpu_bound' 或 'io_bound'

    Returns:
        最优线程数
    """
    from multiprocessing import cpu_count

    if task_type == 'cpu_bound':
        # CPU密集型：线程数 = CPU核心数
        return cpu_count()

    elif task_type == 'io_bound':
        # I/O密集型：线程数 = 2-4 * CPU核心数
        return cpu_count() * 2

    return cpu_count()

# RQA分析是CPU密集型
max_workers = get_optimal_workers('cpu_bound')
```

---

## 11. 实施计划

### 11.1 开发阶段（3周）

**Week 1: 核心功能开发**
- Day 1-2: 项目结构搭建
  - 创建目录结构
  - 配置文件和常量定义
  - 基础工具函数

- Day 3-4: RQA核心算法
  - 嵌入重构函数
  - 递归矩阵计算
  - RQA指标计算
  - 单元测试

- Day 5-7: Service层和API层
  - RQAAnalysisService实现
  - API端点开发
  - 装饰器实现
  - 集成测试

**Week 2: 并行处理和优化**
- Day 8-10: 多线程执行器
  - RQATaskExecutor实现
  - 任务调度逻辑
  - 进度追踪
  - 错误恢复

- Day 11-12: 性能优化
  - 向量化计算
  - 内存优化
  - I/O优化
  - 性能测试

- Day 13-14: 5步流程实现
  - Step 1: RQA计算
  - Step 2: 数据合并
  - Step 3: 特征增强
  - Step 4: 统计分析
  - Step 5: 可视化

**Week 3: 前端开发和集成**
- Day 15-17: 前端组件
  - Module05.jsx主页面
  - 参数配置面板
  - 批量执行面板
  - 结果查看器

- Day 18-19: 可视化
  - 递归图生成
  - 统计图表
  - 交互功能

- Day 20-21: 集成测试和优化
  - 端到端测试
  - 性能测试
  - Bug修复
  - 文档完善

### 11.2 工作量估算

| 任务 | 工时(小时) | 优先级 |
|------|-----------|--------|
| 项目结构搭建 | 4 | P0 |
| RQA核心算法 | 16 | P0 |
| Service层 | 12 | P0 |
| API层 | 10 | P0 |
| 多线程执行器 | 16 | P0 |
| 5步流程 | 20 | P0 |
| 前端UI | 20 | P1 |
| 可视化 | 12 | P1 |
| 性能优化 | 16 | P1 |
| 测试 | 20 | P0 |
| 文档 | 8 | P2 |
| **总计** | **154小时** | - |

**人力配置**: 2人 × 3周 = 240小时 (含buffer)

### 11.3 里程碑

| 里程碑 | 日期 | 交付物 |
|--------|------|--------|
| M1: 核心算法完成 | Week 1 End | RQA算法单元测试通过 |
| M2: 后端完成 | Week 2 End | API全部端点可用 |
| M3: MVP完成 | Week 3 Mid | 前后端基本功能可用 |
| M4: 正式发布 | Week 3 End | 完整功能 + 文档 |

---

## 附录

### A. 技术栈

**后端**:
- Python 3.8+
- Flask (Web框架)
- NumPy (数值计算)
- Pandas (数据处理)
- SciPy (科学计算)
- Matplotlib/Seaborn (可视化)
- ThreadPoolExecutor (并行处理)

**前端**:
- React 18
- Ant Design 5
- Axios (HTTP客户端)
- ECharts (图表库)

**架构模式**:
- 三层架构 (API - Service - Business Logic)
- 装饰器模式 (错误处理、参数验证)
- 单例模式 (Service懒加载)
- 工厂模式 (参数组合生成)

### B. 参考文献

1. Marwan, N., et al. (2007). "Recurrence plots for the analysis of complex systems." *Physics Reports*, 438(5-6), 237-329.

2. Zbilut, J. P., & Webber Jr, C. L. (1992). "Embeddings and delays as derived from quantification of recurrence plots." *Physics Letters A*, 171(3-4), 199-203.

3. Anderson, N. C., et al. (2013). "Eye tracking in human-computer interaction and usability research." *Psychological Methods*, 18(3), 338-356.

### C. 词汇表

| 术语 | 英文 | 说明 |
|------|------|------|
| 递归量化分析 | Recurrence Quantification Analysis (RQA) | 非线性时间序列分析方法 |
| 嵌入维度 | Embedding Dimension (m) | 相空间重构的维度 |
| 时间延迟 | Time Delay (τ) | 嵌入向量间的时间间隔 |
| 递归阈值 | Recurrence Threshold (ε) | 判定递归点的距离阈值 |
| 递归率 | Recurrence Rate (RR) | 递归点占总点数的比例 |
| 确定性 | Determinism (DET) | 形成对角线结构的递归点比例 |
| 熵 | Entropy (ENT) | 对角线长度分布的香农熵 |

---

**文档结束**
