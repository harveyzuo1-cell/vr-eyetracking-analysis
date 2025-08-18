/**
 * 模块10-D Eye-Index 可视化分析 - 前端JavaScript
 * 实现10个功能点的完整交互
 */

// 全局变量
let currentModels = [];
let currentActiveModels = {};
let trainingCurveChart = null;
let lastAction = null; // 用于重试功能
let systemHealthy = false;

// DOM元素缓存
const elements = {
    // 10-A相关
    buildConfigSelect: null,
    valSplitInput: null,
    randomStateInput: null,
    checkPrereqBtn: null,
    buildDatasetBtn: null,
    refreshStatusBtn: null,
    prerequisitesStatus: null,
    buildProgress: null,
    buildProgressText: null,
    datasetList: null,
    
    // 10-D相关
    healthStatusBar: null,
    healthStatusText: null,
    errorAlertBar: null,
    errorAlertText: null,
    retryBtn: null,
    modelDashboard: null,
    modelDetailsSection: null,
    currentModelLabel: null,
    trainingCurveCanvas: null,
    mlpStructureDiagram: null,
    statusModal: null,
    statusContent: null,
    metricsTable: null
};

// 初始化函数
function initEyeIndexModule() {
    console.log('🚀 初始化模块10 Eye-Index (10-D版本)');
    
    // 获取DOM元素
    if (!initDOMElements()) {
        console.error('❌ DOM元素初始化失败');
        return;
    }
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 执行健康检查
    performHealthCheck().then(() => {
        if (systemHealthy) {
            // 初始化10-A模块
            initModule10A();
            
            // 加载模型仪表盘
            loadModelDashboard();
            
            // 加载指标总览
            loadMetricsOverview();
        }
    });
    
    console.log('✅ 模块10初始化完成');
}

// DOM元素初始化
function initDOMElements() {
    try {
        // 10-A相关元素
        elements.buildConfigSelect = document.getElementById('build-rqa-config-select');
        elements.valSplitInput = document.getElementById('val-split-input');
        elements.randomStateInput = document.getElementById('random-state-input');
        elements.checkPrereqBtn = document.getElementById('btn-check-prerequisites');
        elements.buildDatasetBtn = document.getElementById('btn-build-dataset');
        elements.refreshStatusBtn = document.getElementById('btn-refresh-dataset-status');
        elements.prerequisitesStatus = document.getElementById('prerequisites-status');
        elements.buildProgress = document.getElementById('build-progress');
        elements.buildProgressText = document.getElementById('build-progress-text');
        elements.datasetList = document.getElementById('dataset-list');
        
        // 10-D相关元素
        elements.healthStatusBar = document.getElementById('health-status-bar');
        elements.healthStatusText = document.getElementById('health-status-text');
        elements.errorAlertBar = document.getElementById('error-alert-bar');
        elements.errorAlertText = document.getElementById('error-alert-text');
        elements.retryBtn = document.getElementById('btn-retry-last-action');
        elements.modelDashboard = document.getElementById('model-dashboard');
        elements.modelDetailsSection = document.getElementById('model-details-section');
        elements.currentModelLabel = document.getElementById('current-model-label');
        elements.trainingCurveCanvas = document.getElementById('training-curve-chart');
        elements.mlpStructureDiagram = document.getElementById('mlp-structure-diagram');
        elements.statusModal = document.getElementById('statusModal');
        elements.statusContent = document.getElementById('status-content');
        elements.metricsTable = document.getElementById('metrics-overview-table').querySelector('tbody');
        
        return true;
    } catch (error) {
        console.error('DOM元素初始化错误:', error);
        return false;
    }
}

// 事件监听器绑定
function bindEventListeners() {
    // 10-A相关事件
    if (elements.checkPrereqBtn) {
        elements.checkPrereqBtn.addEventListener('click', checkPrerequisites);
    }
    if (elements.buildDatasetBtn) {
        elements.buildDatasetBtn.addEventListener('click', buildDataset);
    }
    if (elements.refreshStatusBtn) {
        elements.refreshStatusBtn.addEventListener('click', loadDatasetStatus);
    }
    
    // 10-D相关事件
    document.getElementById('btn-health-check')?.addEventListener('click', performHealthCheck);
    document.getElementById('btn-refresh-all')?.addEventListener('click', refreshAllData);
    document.getElementById('btn-view-status')?.addEventListener('click', showStatusModal);
    document.getElementById('btn-close-details')?.addEventListener('click', closeModelDetails);
    document.getElementById('btn-refresh-curve')?.addEventListener('click', refreshTrainingCurve);
    document.getElementById('btn-view-structure')?.addEventListener('click', showMLPStructure);
    document.getElementById('btn-single-predict')?.addEventListener('click', performSinglePrediction);
    document.getElementById('btn-batch-predict')?.addEventListener('click', performBatchPrediction);
    document.getElementById('btn-random-features')?.addEventListener('click', generateRandomFeatures);
    document.getElementById('btn-load-sample-batch')?.addEventListener('click', loadSampleBatch);
    document.getElementById('btn-refresh-metrics')?.addEventListener('click', loadMetricsOverview);
    document.getElementById('btn-refresh-status-modal')?.addEventListener('click', refreshStatusModal);
    
    if (elements.retryBtn) {
        elements.retryBtn.addEventListener('click', retryLastAction);
    }
}

// ==================== 功能点8: 健康检查 ====================
async function performHealthCheck() {
    showHealthStatus('正在检查系统健康状态...', 'info');
    
    try {
        const response = await fetch('/api/m10/predict/health');
        const data = await response.json();
        
        if (response.ok && data.status === 'healthy') {
            systemHealthy = true;
            showHealthStatus('系统状态正常', 'success');
            hideHealthStatus(3000);
        } else {
            systemHealthy = false;
            showHealthStatus('系统状态异常: ' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        systemHealthy = false;
        showHealthStatus('健康检查失败: ' + error.message, 'danger');
        console.error('健康检查错误:', error);
    }
}

// ==================== 功能点1: 模型仪表盘 ====================
async function loadModelDashboard() {
    try {
        // 获取可用模型列表
        const modelsResponse = await fetch('/api/m10/models');
        if (!modelsResponse.ok) throw new Error('获取模型列表失败');
        const modelsData = await modelsResponse.json();
        currentModels = modelsData.models || [];
        
        // 渲染模型卡片
        renderModelCards();
        
    } catch (error) {
        showError('加载模型仪表盘失败: ' + error.message, () => loadModelDashboard());
        console.error('模型仪表盘加载错误:', error);
    }
}

function renderModelCards() {
    if (!elements.modelDashboard) return;
    
    if (currentModels.length === 0) {
        elements.modelDashboard.innerHTML = `
            <div class="col-12 text-center text-muted">
                <i class="fas fa-exclamation-circle"></i>
                <p>未找到可用模型</p>
            </div>
        `;
        return;
    }
    
    elements.modelDashboard.innerHTML = '';
    
    currentModels.forEach(model => {
        const cardHtml = `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card model-card" data-q="${model.q}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${model.q} - ${getQDescription(model.q)}</h6>
                        <span class="badge bg-primary" id="status-${model.q}">
                            ${model.active_version || '未激活'}
                        </span>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-6">
                                <small class="text-muted">RMSE</small>
                                <div class="fw-bold" id="rmse-${model.q}">--</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">R²</small>
                                <div class="fw-bold" id="r2-${model.q}">--</div>
                            </div>
                        </div>
                        <div class="mt-3">
                            <div class="btn-group w-100" role="group">
                                <button class="btn btn-sm btn-outline-primary" onclick="showModelDetails('${model.q}')">
                                    <i class="fas fa-chart-line"></i> 详情
                                </button>
                                <div class="btn-group" role="group">
                                    <button class="btn btn-sm btn-outline-success dropdown-toggle" 
                                            data-bs-toggle="dropdown" id="activate-btn-${model.q}">
                                        <i class="fas fa-play"></i> 激活
                                    </button>
                                    <ul class="dropdown-menu" id="versions-${model.q}">
                                        <!-- 版本列表将动态生成 -->
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        elements.modelDashboard.insertAdjacentHTML('beforeend', cardHtml);
        
        // 加载该模型的指标和版本
        loadModelMetrics(model.q);
        loadModelVersions(model.q);
    });
}

function getQDescription(q) {
    const descriptions = {
        'Q1': '时间定向',
        'Q2': '空间定向', 
        'Q3': '即刻记忆',
        'Q4': '注意力计算',
        'Q5': '延迟回忆'
    };
    return descriptions[q] || q;
}

async function loadModelMetrics(q) {
    try {
        const response = await fetch(`/api/m10/metrics?q=${q}`);
        if (response.ok) {
            const data = await response.json();
            
            const rmseElement = document.getElementById(`rmse-${q}`);
            const r2Element = document.getElementById(`r2-${q}`);
            
            if (rmseElement) rmseElement.textContent = data.rmse?.toFixed(3) || '--';
            if (r2Element) r2Element.textContent = data.r2?.toFixed(3) || '--';
        }
    } catch (error) {
        console.error(`加载${q}指标失败:`, error);
    }
}

async function loadModelVersions(q) {
    try {
        const response = await fetch('/api/m10/models');
        if (response.ok) {
            const data = await response.json();
            const model = data.models.find(m => m.q === q);
            
            if (model && model.versions) {
                const versionsDropdown = document.getElementById(`versions-${q}`);
                if (versionsDropdown) {
                    versionsDropdown.innerHTML = '';
                    model.versions.forEach(version => {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <a class="dropdown-item" href="#" onclick="activateModel('${q}', '${version}')">
                                ${version}
                            </a>
                        `;
                        versionsDropdown.appendChild(li);
                    });
                }
            }
        }
    } catch (error) {
        console.error(`加载${q}版本失败:`, error);
    }
}

// ==================== 功能点2: 模型版本激活 ====================
async function activateModel(q, version) {
    try {
        const response = await fetch('/api/m10/activate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({q_tag: q, version: version})
        });
        
        if (response.ok) {
            // 更新状态显示
            const statusElement = document.getElementById(`status-${q}`);
            if (statusElement) {
                statusElement.textContent = version;
                statusElement.className = 'badge bg-success';
            }
            
            // 重新加载指标
            loadModelMetrics(q);
            
            showSuccess(`${q} 模型已激活版本: ${version}`);
        } else {
            throw new Error('激活失败');
        }
    } catch (error) {
        showError(`激活模型失败: ${error.message}`, () => activateModel(q, version));
    }
}

// ==================== 功能点3: 训练曲线查看 ====================
function showModelDetails(q) {
    elements.currentModelLabel.textContent = q;
    elements.modelDetailsSection.style.display = 'block';
    loadTrainingCurve(q);
    
    // 滚动到详情区域
    elements.modelDetailsSection.scrollIntoView({behavior: 'smooth'});
}

function closeModelDetails() {
    elements.modelDetailsSection.style.display = 'none';
    if (trainingCurveChart) {
        trainingCurveChart.destroy();
        trainingCurveChart = null;
    }
}

async function loadTrainingCurve(q) {
    try {
        const response = await fetch(`/api/m10/events?q=${q}`);
        if (!response.ok) throw new Error('获取训练数据失败');
        
        const events = await response.json();
        renderTrainingCurve(events);
        
    } catch (error) {
        showError(`加载训练曲线失败: ${error.message}`, () => loadTrainingCurve(q));
    }
}

function renderTrainingCurve(events) {
    const ctx = elements.trainingCurveCanvas.getContext('2d');
    
    if (trainingCurveChart) {
        trainingCurveChart.destroy();
    }
    
    const steps = events.map(e => e.step);
    const valLoss = events.map(e => e.val);
    
    trainingCurveChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: steps,
            datasets: [{
                label: 'Validation Loss',
                data: valLoss,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {title: {display: true, text: 'Epoch'}},
                y: {title: {display: true, text: 'Loss'}}
            },
            plugins: {
                title: {display: true, text: 'Training Validation Loss Curve'}
            }
        }
    });
}

function refreshTrainingCurve() {
    const q = elements.currentModelLabel.textContent;
    loadTrainingCurve(q);
}

// ==================== 功能点4: MLP结构示意图 ====================
function showMLPStructure() {
    const mermaidCode = `
graph LR
    A[Input<br/>10 features] --> B[Hidden Layer 1<br/>32 neurons<br/>ReLU + Dropout]
    B --> C[Hidden Layer 2<br/>16 neurons<br/>ReLU]
    C --> D[Output<br/>1 neuron<br/>Sigmoid]
    
    E[Adam Optimizer<br/>lr=1e-3] -.-> B
    E -.-> C
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#f3e5f5
    style D fill:#e8f5e8
    style E fill:#fff3e0
    `;
    
    elements.mlpStructureDiagram.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
    
    // 如果mermaid已加载，重新渲染
    if (typeof mermaid !== 'undefined') {
        mermaid.init(undefined, elements.mlpStructureDiagram.querySelector('.mermaid'));
    } else {
        // 动态加载mermaid
        loadMermaidScript().then(() => {
            mermaid.init(undefined, elements.mlpStructureDiagram.querySelector('.mermaid'));
        });
    }
}

function loadMermaidScript() {
    return new Promise((resolve) => {
        if (typeof mermaid !== 'undefined') {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
        script.onload = () => {
            mermaid.initialize({startOnLoad: false});
            resolve();
        };
        document.head.appendChild(script);
    });
}

// ==================== 功能点5: 单条预测 ====================
async function performSinglePrediction() {
    const qTag = document.getElementById('predict-q-select').value;
    if (!qTag) {
        showError('请先选择模型');
        return;
    }
    
    // 收集特征值
    const features = [];
    const inputs = document.querySelectorAll('.feature-input');
    
    for (let input of inputs) {
        const value = parseFloat(input.value);
        if (isNaN(value) || value < 0 || value > 1) {
            showError(`特征值必须在0-1范围内: ${input.previousElementSibling.textContent}`);
            return;
        }
        features.push(value);
    }
    
    if (features.length !== 10) {
        showError('必须输入10个特征值');
        return;
    }
    
    try {
        const response = await fetch('/api/m10/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({q_tag: qTag, features: features})
        });
        
        if (!response.ok) throw new Error('预测失败');
        
        const data = await response.json();
        displaySinglePredictResult(data.score);
        
    } catch (error) {
        showError(`预测失败: ${error.message}`, () => performSinglePrediction());
    }
}

function displaySinglePredictResult(score) {
    const resultDiv = document.getElementById('single-predict-result');
    const scoreSpan = document.getElementById('predict-score');
    
    scoreSpan.textContent = score.toFixed(3);
    resultDiv.style.display = 'block';
    
    // 滚动到结果区域
    resultDiv.scrollIntoView({behavior: 'smooth'});
}

function generateRandomFeatures() {
    const inputs = document.querySelectorAll('.feature-input');
    inputs.forEach(input => {
        input.value = Math.random().toFixed(3);
    });
}

// ==================== 功能点6: 批量预测 ====================
async function performBatchPrediction() {
    const qTag = document.getElementById('batch-predict-q-select').value;
    if (!qTag) {
        showError('请先选择模型');
        return;
    }
    
    const textarea = document.getElementById('batch-input-textarea');
    const text = textarea.value.trim();
    
    if (!text) {
        showError('请输入批量数据');
        return;
    }
    
    // 解析输入数据
    const lines = text.split('\n').filter(line => line.trim());
    const batchFeatures = [];
    
    for (let i = 0; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => parseFloat(v.trim()));
        
        if (values.length !== 10) {
            showError(`第${i+1}行必须包含10个特征值`);
            return;
        }
        
        if (values.some(v => isNaN(v) || v < 0 || v > 1)) {
            showError(`第${i+1}行存在无效的特征值(必须在0-1范围内)`);
            return;
        }
        
        batchFeatures.push(values);
    }
    
    try {
        const response = await fetch('/api/m10/predict/batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({q_tag: qTag, features: batchFeatures})
        });
        
        if (!response.ok) throw new Error('批量预测失败');
        
        const data = await response.json();
        displayBatchPredictResults(data.scores);
        
    } catch (error) {
        showError(`批量预测失败: ${error.message}`, () => performBatchPrediction());
    }
}

function displayBatchPredictResults(scores) {
    const resultDiv = document.getElementById('batch-predict-results');
    const tbody = document.getElementById('batch-results-tbody');
    
    tbody.innerHTML = '';
    scores.forEach((score, index) => {
        const row = tbody.insertRow();
        row.insertCell(0).textContent = `样本 ${index + 1}`;
        row.insertCell(1).textContent = score.toFixed(3);
    });
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({behavior: 'smooth'});
}

function loadSampleBatch() {
    const sampleData = [
        '0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0',
        '0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5',
        '0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1,0.9,0.8'
    ];
    
    document.getElementById('batch-input-textarea').value = sampleData.join('\n');
}

// ==================== 功能点7: 运行状态查看 ====================
function showStatusModal() {
    const modal = new bootstrap.Modal(elements.statusModal);
    modal.show();
    loadSystemStatus();
}

async function loadSystemStatus() {
    elements.statusContent.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> 正在获取状态信息...</div>';
    
    try {
        const response = await fetch('/api/m10/predict/status');
        if (!response.ok) throw new Error('获取状态失败');
        
        const data = await response.json();
        renderSystemStatus(data);
        
    } catch (error) {
        elements.statusContent.innerHTML = `<div class="alert alert-danger">获取状态失败: ${error.message}</div>`;
    }
}

function renderSystemStatus(status) {
    const html = `
        <div class="row">
            <div class="col-6">
                <h6><i class="fas fa-memory"></i> 缓存状态</h6>
                <p>已缓存模型: <span class="badge bg-info">${status.cached_models || 0}</span></p>
                <p>缓存限制: <span class="badge bg-secondary">${status.cache_limit || 5}</span></p>
            </div>
            <div class="col-6">
                <h6><i class="fas fa-play"></i> 激活模型</h6>
                ${Object.entries(status.active_models || {}).map(([q, info]) => 
                    `<p>${q}: <span class="badge bg-success">${info.version || '未知'}</span></p>`
                ).join('')}
            </div>
        </div>
        <hr>
        <div class="row">
            <div class="col-12">
                <h6><i class="fas fa-chart-line"></i> 系统性能</h6>
                <p>系统状态: <span class="badge bg-${systemHealthy ? 'success' : 'danger'}">${systemHealthy ? '正常' : '异常'}</span></p>
                <p>最后检查: <span class="text-muted">${new Date().toLocaleTimeString()}</span></p>
            </div>
        </div>
    `;
    
    elements.statusContent.innerHTML = html;
}

function refreshStatusModal() {
    loadSystemStatus();
}

// ==================== 功能点9: 指标总览 ====================
async function loadMetricsOverview() {
    if (!elements.metricsTable) return;
    
    elements.metricsTable.innerHTML = `
        <tr>
            <td colspan="6" class="text-center text-muted">
                <i class="fas fa-spinner fa-spin"></i> 正在加载指标数据...
            </td>
        </tr>
    `;
    
    try {
        const response = await fetch('/api/m10/metrics/summary');
        let data;
        
        if (response.ok) {
            data = await response.json();
        } else {
            // 如果没有summary端点，手动收集数据
            data = await collectMetricsSummary();
        }
        
        renderMetricsOverview(data);
        
    } catch (error) {
        elements.metricsTable.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    加载指标失败: ${error.message}
                </td>
            </tr>
        `;
    }
}

async function collectMetricsSummary() {
    const summary = {};
    const qTags = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'];
    
    for (const q of qTags) {
        try {
            const response = await fetch(`/api/m10/metrics?q=${q}`);
            if (response.ok) {
                summary[q] = await response.json();
            }
        } catch (error) {
            console.error(`获取${q}指标失败:`, error);
        }
    }
    
    return summary;
}

function renderMetricsOverview(data) {
    if (!elements.metricsTable) return;
    
    elements.metricsTable.innerHTML = '';
    
    const qTags = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'];
    qTags.forEach(q => {
        const metrics = data[q] || {};
        const activeVersion = currentActiveModels[q] || '未激活';
        
        const row = elements.metricsTable.insertRow();
        row.innerHTML = `
            <td><span class="badge bg-primary">${q}</span> ${getQDescription(q)}</td>
            <td><span class="badge bg-success">${activeVersion}</span></td>
            <td>${metrics.rmse ? metrics.rmse.toFixed(3) : '--'}</td>
            <td>${metrics.mae ? metrics.mae.toFixed(3) : '--'}</td>
            <td>${metrics.r2 ? metrics.r2.toFixed(3) : '--'}</td>
            <td><small class="text-muted">${new Date().toLocaleTimeString()}</small></td>
        `;
    });
}

// ==================== 10-A模块功能 ====================
function initModule10A() {
    loadRQAConfigsForBuild();
    loadDatasetStatus();
}

async function loadRQAConfigsForBuild() {
    if (!elements.buildConfigSelect) return;
    
    try {
        const response = await fetch('/api/available-rqa-configs');
        if (!response.ok) throw new Error('获取配置失败');
        
        const data = await response.json();
        const configs = data.configs || data; // 兼容两种格式
        elements.buildConfigSelect.innerHTML = '<option value="">请选择配置...</option>';
        
        configs.forEach(config => {
            const option = document.createElement('option');
            option.value = config.name;
            option.textContent = config.display_name || config.name;
            elements.buildConfigSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('加载RQA配置失败:', error);
        elements.buildConfigSelect.innerHTML = '<option value="">加载失败</option>';
    }
}

async function checkPrerequisites() {
    const config = elements.buildConfigSelect.value;
    if (!config) {
        showError('请先选择RQA配置');
        return;
    }
    
    try {
        const response = await fetch(`/api/eye-index/check-prerequisites?config=${config}`);
        const data = await response.json();
        
        if (data.success) {
            elements.prerequisitesStatus.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> 前置条件检查通过
                    <ul class="mt-2 mb-0">
                        <li>找到数据文件: ${data.details.csv_file}</li>
                        <li>数据记录数: ${data.details.total_records}</li>
                        <li>可用任务: ${data.details.available_tasks.join(', ')}</li>
                    </ul>
                </div>
            `;
            elements.buildDatasetBtn.disabled = false;
        } else {
            elements.prerequisitesStatus.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i> ${data.message}
                </div>
            `;
            elements.buildDatasetBtn.disabled = true;
        }
    } catch (error) {
        showError('检查前置条件失败: ' + error.message);
    }
}

async function buildDataset() {
    const config = elements.buildConfigSelect.value;
    const valSplit = elements.valSplitInput.value;
    const randomState = elements.randomStateInput.value;
    
    if (!config) {
        showError('请先选择RQA配置');
        return;
    }
    
    // 显示进度条
    elements.buildProgress.style.display = 'block';
    elements.buildDatasetBtn.disabled = true;
    
    try {
        const response = await fetch('/api/eye-index/build-dataset', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                config_name: config,
                val_split: parseFloat(valSplit),
                random_state: parseInt(randomState)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            elements.buildProgressText.textContent = '构建完成!';
            showSuccess('数据集构建成功');
            loadDatasetStatus();
        } else {
            throw new Error(data.message || '构建失败');
        }
    } catch (error) {
        showError('构建数据集失败: ' + error.message);
    } finally {
        elements.buildProgress.style.display = 'none';
        elements.buildDatasetBtn.disabled = false;
    }
}

async function loadDatasetStatus() {
    if (!elements.datasetList) return;
    
    elements.datasetList.innerHTML = '<div class="text-center text-muted"><i class="fas fa-spinner fa-spin"></i> 加载中...</div>';
    
    try {
        const response = await fetch('/api/eye-index/dataset-status');
        const data = await response.json();
        
        if (data.datasets && data.datasets.length > 0) {
            elements.datasetList.innerHTML = '';
            data.datasets.forEach(dataset => {
                const item = document.createElement('div');
                item.className = 'list-group-item list-group-item-action';
                item.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${dataset.config}</h6>
                        <small class="text-success">
                            <i class="fas fa-check-circle"></i>
                        </small>
                    </div>
                    <p class="mb-1">
                        <small>数据集: ${dataset.tasks.join(', ')}</small>
                    </p>
                    <small class="text-muted">
                        总样本: ${dataset.total_samples} | 
                        创建时间: ${new Date(dataset.created_at).toLocaleString()}
                    </small>
                `;
                elements.datasetList.appendChild(item);
            });
        } else {
            elements.datasetList.innerHTML = '<div class="text-center text-muted">暂无已构建的数据集</div>';
        }
    } catch (error) {
        elements.datasetList.innerHTML = '<div class="text-center text-danger">加载失败</div>';
    }
}

// ==================== 通用工具函数 ====================
function showHealthStatus(message, type = 'info') {
    if (!elements.healthStatusBar || !elements.healthStatusText) return;
    
    elements.healthStatusText.textContent = message;
    elements.healthStatusBar.className = `alert alert-${type}`;
    elements.healthStatusBar.classList.remove('d-none');
}

function hideHealthStatus(delay = 0) {
    if (!elements.healthStatusBar) return;
    
    setTimeout(() => {
        elements.healthStatusBar.classList.add('d-none');
    }, delay);
}

function showError(message, retryFunction = null) {
    if (!elements.errorAlertBar || !elements.errorAlertText) {
        console.error('Error:', message);
        return;
    }
    
    elements.errorAlertText.textContent = message;
    elements.errorAlertBar.classList.remove('d-none');
    
    if (retryFunction) {
        lastAction = retryFunction;
        elements.retryBtn.style.display = 'inline-block';
    } else {
        elements.retryBtn.style.display = 'none';
    }
    
    // 自动隐藏
    setTimeout(() => {
        elements.errorAlertBar.classList.add('d-none');
    }, 10000);
}

function showSuccess(message) {
    // 临时创建成功提示
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        <i class="fas fa-check-circle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function retryLastAction() {
    if (lastAction && typeof lastAction === 'function') {
        elements.errorAlertBar.classList.add('d-none');
        lastAction();
    }
}

function refreshAllData() {
    performHealthCheck().then(() => {
        if (systemHealthy) {
            loadModelDashboard();
            loadMetricsOverview();
            loadDatasetStatus();
        }
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化以确保DOM完全准备就绪
    setTimeout(initEyeIndexModule, 500);
});

// 导出全局函数供HTML调用
window.showModelDetails = showModelDetails;
window.activateModel = activateModel;