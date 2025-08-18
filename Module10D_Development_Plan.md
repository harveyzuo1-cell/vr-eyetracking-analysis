# 模块10-D开发规划：模型性能评估与差异可视化

## 项目概述

模块10-D是Eye-Index综合评估系统的最后一环，专注于对训练完成的模型进行深度性能分析和可视化展示。该模块通过多维度的残差分析、任务级误差对比和分组性能评估，为研究者提供全面的模型验证工具，完成从"数据→训练→结果→评估"的完整科研闭环。

## 系统架构更新

```
模块10 - Eye-Index 综合评估
├── 模块10-A: 数据准备与特征提取  
├── 模块10-B: PyTorch训练引擎  
├── 模块10-C: 训练数据查看器  
└── 模块10-D: 模型性能评估与差异可视化 🚀（新增）
```

## 核心功能特性

### 1. 模型选择与批量评估
- **多模型加载**: 支持选择特定RQA配置下的完整模型组（Q1-Q5）
- **批量性能计算**: 自动加载所有子任务模型并进行性能验证
- **指标对比**: 提供R²、RMSE、MAE等关键指标的任务间对比

### 2. 个体残差分析
- **五维误差指纹**: 为每位受试者生成Q1-Q5任务的预测误差曲线
- **个体差异识别**: 通过折线图展示不同受试者的误差模式
- **异常值检测**: 识别预测误差异常的样本和任务组合

### 3. 任务级性能对比
- **平均误差分析**: 计算并可视化每个任务的平均预测误差
- **真实得分对比**: 展示任务难度与预测误差的关系
- **系统性偏差检测**: 识别模型在特定任务上的高估/低估倾向

### 4. 分组差异分析
- **认知组别对比**: 按Control/MCI/AD组别分析模型性能差异
- **组别平均曲线**: 生成各组在Q1-Q5任务上的平均误差曲线
- **临床意义解读**: 评估模型在不同认知状态人群中的适用性

### 5. 交互式可视化
- **多图综合展示**: 在单一页面同时呈现多个分析图表
- **动态图例控制**: 支持点击显示/隐藏特定数据系列
- **悬停详情提示**: 鼠标悬停显示具体数值和样本信息

### 6. 结果导出功能
- **图表导出**: 支持PNG格式的高质量图表导出
- **数据导出**: 提供CSV格式的原始数据导出
- **报告生成**: 自动生成包含关键指标的性能报告

---

## 详细开发计划

### 阶段一：后端架构搭建 (2-3天)

#### 1.1 创建模块目录结构
```
backend/m10_evaluation/
├── __init__.py              # 模块初始化
├── evaluator.py            # 核心评估逻辑
├── api.py                  # Flask API路由
├── config.py               # 配置管理
└── utils/
    ├── __init__.py
    ├── metrics.py          # 评估指标计算
    └── data_loader.py      # 数据加载工具
```

#### 1.2 实现ModelEvaluator核心类
```python
class ModelEvaluator:
    """模型性能评估器"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_cache = {}  # 模型缓存
        
    def evaluate_model_set(self, rqa_sig, include_groups=False):
        """
        批量评估指定配置下的所有任务模型
        
        Args:
            rqa_sig: RQA配置签名
            include_groups: 是否包含分组分析
            
        Returns:
            完整的性能分析结果
        """
        
    def _load_model(self, model_path):
        """加载并缓存模型"""
        
    def _calculate_residuals(self, y_true, y_pred):
        """计算残差数据"""
        
    def _group_analysis(self, errors_matrix, sample_ids):
        """按组别分析误差"""
```

#### 1.3 设计API接口规范
```python
# 主要性能分析API
GET /api/m10d/performance?config=<rqa_sig>&include_groups=<bool>

# 可用模型配置列表
GET /api/m10d/configs

# 特定任务详细分析
GET /api/m10d/task-analysis/<task>?config=<rqa_sig>

# 导出功能
GET /api/m10d/export/data?config=<rqa_sig>&format=<csv|json>
```

### 阶段二：数据处理与分析逻辑 (3-4天)

#### 2.1 实现批量模型加载
- **智能缓存机制**: 缓存最近使用的5组模型，避免重复加载
- **GPU内存管理**: 合理分配GPU内存，支持批量推理加速
- **错误处理**: 优雅处理模型文件缺失或损坏的情况

#### 2.2 实现残差计算逻辑
```python
def calculate_comprehensive_metrics(self, rqa_sig):
    """计算全面的性能指标"""
    tasks = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    results = {
        "task_metrics": {},
        "residual_matrix": [],  # [n_samples, 5]
        "avg_errors": [],
        "avg_actuals": [],
        "group_analysis": {}
    }
    
    for task in tasks:
        # 1. 加载模型和数据
        model = self._load_model(f"models/{rqa_sig}/{task}_best.pt")
        data = self._load_data(f"data/module10_datasets/{rqa_sig}/{task}.npz")
        
        # 2. 执行预测
        predictions = self._predict_batch(model, data['X'])
        
        # 3. 计算指标和残差
        metrics = calculate_metrics(data['y'], predictions)
        residuals = predictions - data['y']
        
        results["task_metrics"][task] = metrics
        results["residual_matrix"].append(residuals)
    
    # 4. 转置残差矩阵：[5, n_samples] -> [n_samples, 5]
    results["residual_matrix"] = np.array(results["residual_matrix"]).T
    
    return results
```

#### 2.3 实现分组分析功能
```python
def _infer_sample_groups(self, n_samples):
    """根据样本数量推断组别划分"""
    # 假设数据按Control/MCI/AD顺序排列
    group_size = n_samples // 3
    groups = {
        "control": list(range(0, group_size)),
        "mci": list(range(group_size, 2 * group_size)),
        "ad": list(range(2 * group_size, n_samples))
    }
    return groups

def _calculate_group_metrics(self, residual_matrix, groups):
    """计算各组别的平均误差曲线"""
    group_metrics = {}
    for group_name, indices in groups.items():
        group_residuals = residual_matrix[indices]
        group_metrics[group_name] = {
            "avg_errors": np.mean(np.abs(group_residuals), axis=0).tolist(),
            "std_errors": np.std(np.abs(group_residuals), axis=0).tolist(),
            "sample_count": len(indices)
        }
    return group_metrics
```

### 阶段三：前端页面开发 (4-5天)

#### 3.1 页面布局设计
```html
<!-- 在enhanced_index.html中添加模块10-D部分 -->
<div id="module10d-performance" class="module-section" style="display: none;">
    <div class="module-header">
        <h3><i class="fas fa-chart-line"></i> 模块10-D: 模型性能评估与差异可视化</h3>
        <p class="module-description">深度分析模型预测性能，提供个体残差和任务级误差对比</p>
    </div>
    
    <!-- 控制面板 -->
    <div class="control-panel">
        <div class="row">
            <div class="col-md-4">
                <label>选择模型配置:</label>
                <select id="model-config-select" class="form-select">
                    <option value="">请选择...</option>
                </select>
            </div>
            <div class="col-md-4">
                <label>分组分析:</label>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="include-groups">
                    <label class="form-check-label">包含组别对比</label>
                </div>
            </div>
            <div class="col-md-4">
                <button id="analyze-performance" class="btn btn-primary">
                    <i class="fas fa-play"></i> 开始分析
                </button>
            </div>
        </div>
    </div>
    
    <!-- 指标概览 -->
    <div class="metrics-overview">
        <h4>性能指标概览</h4>
        <div id="metrics-table-container">
            <!-- 动态生成指标表格 -->
        </div>
    </div>
    
    <!-- 个体残差分析 -->
    <div class="residual-analysis">
        <h4>个体残差曲线分析</h4>
        <div class="chart-controls">
            <div class="group-filters">
                <label>显示组别:</label>
                <button class="btn btn-sm btn-outline-success" data-group="control">Control</button>
                <button class="btn btn-sm btn-outline-warning" data-group="mci">MCI</button>
                <button class="btn btn-sm btn-outline-danger" data-group="ad">AD</button>
                <button class="btn btn-sm btn-secondary" data-group="all">全部</button>
            </div>
            <button id="download-residual-chart" class="btn btn-sm btn-info">
                <i class="fas fa-download"></i> 下载图表
            </button>
        </div>
        <canvas id="residual-chart" width="800" height="400"></canvas>
    </div>
    
    <!-- 任务级误差对比 -->
    <div class="task-comparison">
        <h4>任务级误差对比分析</h4>
        <div class="chart-controls">
            <button id="download-comparison-chart" class="btn btn-sm btn-info">
                <i class="fas fa-download"></i> 下载图表
            </button>
        </div>
        <canvas id="task-comparison-chart" width="800" height="300"></canvas>
    </div>
    
    <!-- 分组性能对比 -->
    <div id="group-analysis-section" class="group-analysis" style="display: none;">
        <h4>分组性能对比</h4>
        <canvas id="group-comparison-chart" width="800" height="300"></canvas>
    </div>
</div>
```

#### 3.2 JavaScript逻辑实现
```javascript
class Module10DManager {
    constructor() {
        this.currentConfig = null;
        this.performanceData = null;
        this.residualChart = null;
        this.comparisonChart = null;
        this.groupChart = null;
        this.init();
    }
    
    init() {
        this.loadAvailableConfigs();
        this.bindEvents();
        this.initCharts();
    }
    
    async loadAvailableConfigs() {
        try {
            const response = await fetch('/api/m10d/configs');
            const configs = await response.json();
            this.populateConfigSelect(configs);
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }
    
    async analyzePerformance() {
        const config = document.getElementById('model-config-select').value;
        const includeGroups = document.getElementById('include-groups').checked;
        
        if (!config) {
            alert('请先选择模型配置');
            return;
        }
        
        try {
            const response = await fetch(
                `/api/m10d/performance?config=${config}&include_groups=${includeGroups}`
            );
            this.performanceData = await response.json();
            
            this.updateMetricsTable();
            this.updateResidualChart();
            this.updateComparisonChart();
            
            if (includeGroups) {
                this.updateGroupChart();
                document.getElementById('group-analysis-section').style.display = 'block';
            }
        } catch (error) {
            console.error('性能分析失败:', error);
        }
    }
    
    updateResidualChart() {
        const ctx = document.getElementById('residual-chart').getContext('2d');
        const data = this.performanceData.residual_data;
        
        // 构建数据集
        const datasets = [];
        
        // 添加个体曲线（默认隐藏）
        data.individual_errors.forEach((errors, index) => {
            const group = this.getGroupByIndex(index);
            datasets.push({
                label: `样本${index + 1}`,
                data: errors,
                borderColor: this.getGroupColor(group),
                backgroundColor: 'transparent',
                hidden: true,
                pointRadius: 2,
                borderWidth: 1
            });
        });
        
        // 添加平均误差线
        datasets.push({
            label: '平均误差',
            data: data.avg_errors,
            borderColor: '#333',
            backgroundColor: 'transparent',
            borderWidth: 3,
            pointRadius: 4
        });
        
        this.residualChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
                datasets: datasets
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: '预测误差'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false  // 自定义图例控制
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateComparisonChart() {
        const ctx = document.getElementById('task-comparison-chart').getContext('2d');
        const data = this.performanceData.task_comparison;
        
        this.comparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
                datasets: [{
                    label: '平均真实得分',
                    data: data.avg_actuals,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: '平均绝对误差',
                    data: data.avg_abs_errors,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '真实得分'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '绝对误差'
                        },
                        grid: {
                            drawOnChartArea: false,
                        }
                    }
                }
            }
        });
    }
    
    // 图表导出功能
    downloadChart(chartInstance, filename) {
        const canvas = chartInstance.canvas;
        const url = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = filename;
        link.href = url;
        link.click();
    }
    
    // 组别筛选功能
    filterByGroup(group) {
        if (!this.residualChart) return;
        
        this.residualChart.data.datasets.forEach((dataset, index) => {
            if (dataset.label.startsWith('样本')) {
                const sampleIndex = parseInt(dataset.label.replace('样本', '')) - 1;
                const sampleGroup = this.getGroupByIndex(sampleIndex);
                
                if (group === 'all') {
                    dataset.hidden = false;
                } else {
                    dataset.hidden = sampleGroup !== group;
                }
            }
        });
        
        this.residualChart.update();
    }
}

// 初始化模块10-D
let module10DManager;
function initModule10D() {
    module10DManager = new Module10DManager();
}
```

### 阶段四：高级功能实现 (3-4天)

#### 4.1 交互式图例控制
```javascript
// 自定义图例控制
createCustomLegend() {
    const legendContainer = document.getElementById('residual-legend');
    const groups = ['control', 'mci', 'ad'];
    
    groups.forEach(group => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <input type="checkbox" id="legend-${group}" checked>
            <span class="legend-color" style="background: ${this.getGroupColor(group)}"></span>
            <label for="legend-${group}">${this.getGroupLabel(group)}</label>
        `;
        
        legendItem.querySelector('input').addEventListener('change', (e) => {
            this.toggleGroupVisibility(group, e.target.checked);
        });
        
        legendContainer.appendChild(legendItem);
    });
}
```

#### 4.2 悬停详情增强
```javascript
// 增强的tooltip配置
tooltipConfig: {
    mode: 'point',
    intersect: false,
    callbacks: {
        title: function(tooltipItems) {
            return `任务: ${tooltipItems[0].label}`;
        },
        label: function(context) {
            const dataset = context.dataset;
            const value = context.parsed.y;
            
            if (dataset.label.startsWith('样本')) {
                const sampleIndex = parseInt(dataset.label.replace('样本', ''));
                const group = this.getGroupByIndex(sampleIndex - 1);
                return `${dataset.label} (${group}): ${value.toFixed(3)}`;
            }
            return `${dataset.label}: ${value.toFixed(3)}`;
        },
        afterBody: function(tooltipItems) {
            const context = tooltipItems[0];
            if (context.dataset.label.startsWith('样本')) {
                return [
                    '',
                    '点击查看该样本详细信息',
                    '双击高亮该样本曲线'
                ];
            }
            return [];
        }
    }
}
```

#### 4.3 数据导出功能
```javascript
async exportData(format = 'csv') {
    if (!this.performanceData) {
        alert('请先进行性能分析');
        return;
    }
    
    try {
        const config = this.currentConfig;
        const response = await fetch(
            `/api/m10d/export/data?config=${config}&format=${format}`
        );
        
        if (format === 'csv') {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `performance_analysis_${config}.csv`;
            link.click();
            window.URL.revokeObjectURL(url);
        } else {
            const data = await response.json();
            const jsonStr = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonStr], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `performance_analysis_${config}.json`;
            link.click();
            window.URL.revokeObjectURL(url);
        }
        
        this.showSuccessMessage('数据导出成功');
    } catch (error) {
        console.error('导出失败:', error);
        this.showErrorMessage('数据导出失败');
    }
}
```

### 阶段五：性能优化与测试 (2-3天)

#### 5.1 后端性能优化
```python
class PerformanceOptimizer:
    """性能优化工具"""
    
    def __init__(self):
        self.model_cache = LRUCache(maxsize=10)
        self.data_cache = LRUCache(maxsize=20)
    
    @lru_cache(maxsize=32)
    def get_cached_metrics(self, rqa_sig, task):
        """缓存计算结果"""
        return self._calculate_task_metrics(rqa_sig, task)
    
    def batch_predict(self, models, data_list):
        """批量预测优化"""
        if torch.cuda.is_available():
            return self._gpu_batch_predict(models, data_list)
        else:
            return self._cpu_batch_predict(models, data_list)
    
    def _gpu_batch_predict(self, models, data_list):
        """GPU批量预测"""
        predictions = []
        with torch.no_grad():
            for model, data in zip(models, data_list):
                model = model.to(self.device)
                data_tensor = torch.tensor(data, device=self.device)
                pred = model(data_tensor).cpu().numpy()
                predictions.append(pred)
        return predictions
```

#### 5.2 前端性能优化
```javascript
// 虚拟滚动优化大量数据显示
class VirtualizedLegend {
    constructor(container, items, itemHeight = 30) {
        this.container = container;
        this.items = items;
        this.itemHeight = itemHeight;
        this.visibleCount = Math.ceil(container.clientHeight / itemHeight);
        this.scrollTop = 0;
        
        this.init();
    }
    
    init() {
        this.container.style.overflow = 'auto';
        this.container.style.height = `${this.visibleCount * this.itemHeight}px`;
        
        this.container.addEventListener('scroll', () => {
            this.scrollTop = this.container.scrollTop;
            this.render();
        });
        
        this.render();
    }
    
    render() {
        const startIndex = Math.floor(this.scrollTop / this.itemHeight);
        const endIndex = Math.min(startIndex + this.visibleCount, this.items.length);
        
        this.container.innerHTML = '';
        
        for (let i = startIndex; i < endIndex; i++) {
            const item = this.createLegendItem(this.items[i], i);
            item.style.position = 'absolute';
            item.style.top = `${i * this.itemHeight}px`;
            this.container.appendChild(item);
        }
    }
}
```

#### 5.3 错误处理与用户反馈
```javascript
class ErrorHandler {
    static showError(message, details = null) {
        const toast = document.createElement('div');
        toast.className = 'toast toast-error';
        toast.innerHTML = `
            <div class="toast-header">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>错误</strong>
            </div>
            <div class="toast-body">
                ${message}
                ${details ? `<small class="text-muted">${details}</small>` : ''}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // 自动移除
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    static async handleApiError(response) {
        if (!response.ok) {
            const error = await response.json();
            this.showError(
                '请求失败',
                `${response.status}: ${error.message || '未知错误'}`
            );
            throw new Error(error.message);
        }
        return response;
    }
}
```

### 阶段六：集成与测试 (2天)

#### 6.1 主导航集成
```javascript
// 在enhanced_index.html中添加导航项
function updateNavigation() {
    const navItems = document.querySelectorAll('.nav-link');
    navItems.forEach(item => {
        if (item.textContent.includes('模块10')) {
            const submenu = item.nextElementSibling;
            if (submenu && submenu.classList.contains('submenu')) {
                const module10D = document.createElement('a');
                module10D.className = 'submenu-item';
                module10D.href = '#';
                module10D.innerHTML = '<i class="fas fa-chart-line"></i> 性能评估';
                module10D.onclick = () => showModule('module10d-performance');
                submenu.appendChild(module10D);
            }
        }
    });
}
```

#### 6.2 完整功能测试
```python
# 测试脚本
def test_module10d_complete_workflow():
    """测试完整工作流程"""
    
    # 1. 测试API可用性
    response = requests.get('http://localhost:8080/api/m10d/configs')
    assert response.status_code == 200
    
    # 2. 测试性能分析
    config = response.json()[0]['id']
    perf_response = requests.get(
        f'http://localhost:8080/api/m10d/performance?config={config}&include_groups=true'
    )
    assert perf_response.status_code == 200
    
    data = perf_response.json()
    assert 'task_metrics' in data
    assert 'residual_data' in data
    assert 'group_analysis' in data
    
    # 3. 测试数据导出
    export_response = requests.get(
        f'http://localhost:8080/api/m10d/export/data?config={config}&format=csv'
    )
    assert export_response.status_code == 200
    
    print("✅ 模块10-D所有功能测试通过")
```

---

## 技术实现细节

### 数据流架构
```
用户选择模型配置 
    ↓
前端发送API请求
    ↓
后端加载模型和数据
    ↓
批量执行预测计算
    ↓
计算残差和统计指标
    ↓
返回结构化JSON数据
    ↓
前端渲染交互式图表
    ↓
用户分析和导出结果
```

### 关键算法实现

#### 残差计算优化
```python
def calculate_residuals_optimized(self, models_dict, data_dict):
    """优化的残差计算"""
    tasks = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    n_samples = len(data_dict["Q1"]['y'])
    
    # 预分配结果矩阵
    residual_matrix = np.zeros((n_samples, 5))
    metrics_dict = {}
    
    with torch.no_grad():
        for i, task in enumerate(tasks):
            model = models_dict[task]
            X, y_true = data_dict[task]['X'], data_dict[task]['y']
            
            # 批量预测
            X_tensor = torch.FloatTensor(X).to(self.device)
            y_pred = model(X_tensor).cpu().numpy().flatten()
            
            # 计算残差
            residuals = y_pred - y_true
            residual_matrix[:, i] = residuals
            
            # 计算指标
            metrics_dict[task] = {
                'r2': r2_score(y_true, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
                'mae': mean_absolute_error(y_true, y_pred),
                'correlation': np.corrcoef(y_true, y_pred)[0, 1]
            }
    
    return residual_matrix, metrics_dict
```

#### 分组分析算法
```python
def analyze_group_performance(self, residual_matrix):
    """分组性能分析"""
    n_samples = residual_matrix.shape[0]
    group_size = n_samples // 3
    
    groups = {
        'control': residual_matrix[:group_size],
        'mci': residual_matrix[group_size:2*group_size],
        'ad': residual_matrix[2*group_size:]
    }
    
    group_stats = {}
    for group_name, group_residuals in groups.items():
        abs_residuals = np.abs(group_residuals)
        group_stats[group_name] = {
            'mean_errors': np.mean(abs_residuals, axis=0).tolist(),
            'std_errors': np.std(abs_residuals, axis=0).tolist(),
            'median_errors': np.median(abs_residuals, axis=0).tolist(),
            'max_errors': np.max(abs_residuals, axis=0).tolist(),
            'sample_count': len(group_residuals)
        }
    
    return group_stats
```

### 前端图表配置

#### 个体残差图表配置
```javascript
const residualChartConfig = {
    type: 'line',
    data: {
        labels: ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
        datasets: [] // 动态填充
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'point',
            intersect: false
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'MMSE子任务'
                }
            },
            y: {
                title: {
                    display: true,
                    text: '预测残差 (预测值 - 真实值)'
                },
                grid: {
                    color: 'rgba(0,0,0,0.1)'
                }
            }
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: 'rgba(0,0,0,0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: 'rgba(255,255,255,0.3)',
                borderWidth: 1
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
        }
    }
};
```

---

## 项目文件结构

```
模块10-D/
├── backend/
│   └── m10_evaluation/
│       ├── __init__.py
│       ├── evaluator.py          # 核心评估逻辑
│       ├── api.py                # Flask API路由
│       ├── config.py             # 配置管理
│       └── utils/
│           ├── __init__.py
│           ├── metrics.py        # 评估指标工具
│           ├── data_loader.py    # 数据加载工具
│           └── cache.py          # 缓存管理
├── frontend/
│   ├── templates/
│   │   └── enhanced_index.html   # 主页面（添加模块10-D部分）
│   └── static/
│       ├── js/
│       │   ├── module10d.js      # 模块10-D专用脚本
│       │   └── chart-utils.js    # 图表工具函数
│       └── css/
│           └── module10d.css     # 模块10-D样式
├── tests/
│   ├── test_evaluator.py         # 评估器测试
│   ├── test_api.py               # API测试
│   └── test_frontend.py          # 前端功能测试
└── docs/
    ├── API_Reference.md          # API文档
    └── User_Guide.md             # 用户指南
```

---

## 开发时间表

| 阶段 | 任务 | 预计时间 | 负责模块 |
|------|------|----------|----------|
| 1 | 后端架构搭建 | 2-3天 | ModelEvaluator, API路由 |
| 2 | 数据处理逻辑 | 3-4天 | 批量预测, 残差计算, 分组分析 |
| 3 | 前端页面开发 | 4-5天 | HTML布局, JavaScript逻辑 |
| 4 | 高级功能实现 | 3-4天 | 交互控制, 导出功能 |
| 5 | 性能优化 | 2-3天 | 缓存机制, 错误处理 |
| 6 | 集成测试 | 2天 | 完整流程测试 |
| **总计** | **完整开发** | **16-21天** | **全栈实现** |

---

## 质量保证

### 代码质量
- **类型注解**: 所有Python函数使用类型提示
- **文档字符串**: 详细的docstring文档
- **单元测试**: 覆盖率≥90%
- **代码审查**: 每个功能模块独立审查

### 性能基准
- **API响应时间**: <2秒（60样本×5任务）
- **图表渲染时间**: <1秒
- **内存使用**: 峰值<1GB
- **并发支持**: 支持5个用户同时分析

### 用户体验
- **响应式设计**: 支持桌面和平板设备
- **加载反馈**: 所有异步操作提供进度指示
- **错误处理**: 友好的错误提示和恢复建议
- **操作指导**: 内置帮助文档和操作提示

---

## 科研价值与应用

### 临床研究支持
1. **模型验证**: 提供科学严谨的模型性能评估
2. **个体差异分析**: 识别预测困难的样本类型
3. **任务特异性**: 发现模型在特定认知任务上的局限性
4. **组别对比**: 支持不同认知状态人群的模型适用性研究

### 学术价值
1. **方法学贡献**: 眼动数据机器学习模型的标准化评估流程
2. **可重现性**: 完整的评估指标和可视化方法
3. **可解释性**: 通过残差分析提供模型行为解释
4. **比较研究**: 支持不同模型架构和参数的对比分析

### 实际应用
1. **诊断辅助**: 为临床医生提供量化的认知评估工具
2. **研究工具**: 为认知科学研究提供分析平台
3. **教学演示**: 可用于机器学习和医学信息学教学
4. **技术转化**: 为产业化应用提供技术基础

---

## 总结

模块10-D的开发将完成Eye-Index系统的最后一环，通过深度的模型性能分析和直观的可视化展示，为研究者提供全面的模型验证工具。该模块不仅具有重要的科研价值，还将显著提升整个系统的实用性和专业性。

通过系统化的开发规划和严格的质量控制，模块10-D将成为Eye-Index系统的重要组成部分，为VR环境下的眼动-认知研究提供强有力的技术支撑。
