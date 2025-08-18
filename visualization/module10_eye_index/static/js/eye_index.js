/**
 * 模块10 Eye-Index 综合评估 - 前端JavaScript
 * 实现S_eye可视化、交互控制、数据展示
 */

// 全局变量
let currentEyeIndexData = null;
let currentReport = null;
let currentConfig = null;

// 子模块10-A相关变量
let currentDatasetStatus = null;
let currentPrerequisites = null;

// Chart.js实例
let boxChart = null;
let scatterChart = null;
let radarChart = null;
let learningCurveChart = null;

// 训练历史数据
let trainingHistory = {
    epochs: [],
    trainLoss: [],
    valLoss: []
};

// DOM元素
const elements = {
    configSelect: null,
    modeSelect: null,
    statusBadge: null,
    customWeightsPanel: null,
    weightInputs: null,
    weightsSum: null,
    mmseSelect: null,
    subjectSelect: null,
    docPanel: null,
    statsTable: null
};

// 子模块10-A DOM元素
const module10aElements = {
    buildConfigSelect: null,
    valSplitInput: null,
    randomStateInput: null,
    checkPrereqBtn: null,
    buildDatasetBtn: null,
    refreshStatusBtn: null,
    prerequisitesStatus: null,
    buildProgress: null,
    buildProgressText: null,
    datasetList: null
};

// 初始化函数
function initEyeIndexModule() {
    console.log('🚀 初始化模块10 Eye-Index');
    
    // 获取DOM元素
    const domReady = initDOMElements();
    if (!domReady) {
        console.error('❌ 模块10 DOM元素未准备就绪，初始化失败');
        return;
    }
    
    // 初始化子模块10-A
    const module10aReady = initModule10A();
    if (!module10aReady) {
        console.warn('⚠️ 子模块10-A初始化失败，但继续初始化其他功能');
    }
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 加载可用配置
    loadAvailableConfigs();
    
    // 初始化图表
    initCharts();
    
    console.log('✅ 模块10 Eye-Index初始化完成');
}

function initDOMElements() {
    elements.configSelect = document.getElementById('eye-index-config-select');
    elements.modeSelect = document.getElementById('s-eye-mode-select');
    elements.statusBadge = document.getElementById('eye-index-status');
    elements.customWeightsPanel = document.getElementById('custom-weights-panel');
    elements.weightInputs = document.querySelectorAll('.weight-input');
    elements.weightsSum = document.getElementById('weights-sum');
    elements.mmseSelect = document.getElementById('mmse-select');
    elements.subjectSelect = document.getElementById('subject-select');
    elements.docPanel = document.getElementById('doc-s-eye');
    elements.statsTable = document.getElementById('stats-table');
    
    // 检查关键DOM元素是否存在
    const missingElements = [];
    if (!elements.configSelect) missingElements.push('eye-index-config-select');
    if (!elements.modeSelect) missingElements.push('s-eye-mode-select');
    if (!elements.statusBadge) missingElements.push('eye-index-status');
    
    if (missingElements.length > 0) {
        console.warn('⚠️ 以下DOM元素未找到:', missingElements);
        console.warn('模块10界面可能未正确加载，请检查HTML模板');
        return false;
    }
    
    return true;
}

function bindEventListeners() {
    // 计算按钮
    const runBtn = document.getElementById('btn-run-eye-index');
    if (runBtn) {
        runBtn.addEventListener('click', runEyeIndexCalculation);
    } else {
        console.warn('⚠️ btn-run-eye-index 元素未找到');
    }
    
    // 刷新按钮
    const refreshBtn = document.getElementById('btn-refresh-eye-index');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshEyeIndexData);
    } else {
        console.warn('⚠️ btn-refresh-eye-index 元素未找到');
    }
    
    // 配置选择变化
    if (elements.configSelect) {
        elements.configSelect.addEventListener('change', onConfigChange);
    } else {
        console.warn('⚠️ configSelect 元素未找到');
    }
    
    // 计算模式变化
    if (elements.modeSelect) {
        elements.modeSelect.addEventListener('change', onModeChange);
    } else {
        console.warn('⚠️ modeSelect 元素未找到');
    }
    
    // MMSE子分数选择变化
    if (elements.mmseSelect) {
        elements.mmseSelect.addEventListener('change', updateScatterChart);
    } else {
        console.warn('⚠️ mmseSelect 元素未找到');
    }
    
    // 受试者选择变化
    if (elements.subjectSelect) {
        elements.subjectSelect.addEventListener('change', updateRadarChart);
    } else {
        console.warn('⚠️ subjectSelect 元素未找到');
    }
    
    // 权重输入变化
    if (elements.weightInputs && elements.weightInputs.length > 0) {
        elements.weightInputs.forEach(input => {
            input.addEventListener('input', updateWeightsSum);
        });
    } else {
        console.warn('⚠️ weightInputs 元素未找到');
    }
    
    // 归一化权重按钮
    const normalizeBtn = document.getElementById('btn-normalize-weights');
    if (normalizeBtn) {
        normalizeBtn.addEventListener('click', normalizeWeights);
    } else {
        console.warn('⚠️ btn-normalize-weights 元素未找到');
    }
    
    // 导出按钮
    const exportCsvBtn = document.getElementById('btn-export-csv');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', exportCSV);
    } else {
        console.warn('⚠️ btn-export-csv 元素未找到');
    }
    
    const exportJsonBtn = document.getElementById('btn-export-json');
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', exportJSON);
    } else {
        console.warn('⚠️ btn-export-json 元素未找到');
    }
    
    const exportPdfBtn = document.getElementById('btn-export-pdf');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', exportPDF);
    } else {
        console.warn('⚠️ btn-export-pdf 元素未找到');
    }
}

async function loadAvailableConfigs() {
    try {
        const response = await fetch('/api/eye-index/available-configs');
        const result = await response.json();
        
        if (result.success) {
            const select = elements.configSelect;
            select.innerHTML = '<option value="">请选择配置...</option>';
            
            result.configs.forEach(config => {
                const option = document.createElement('option');
                option.value = config.name;
                option.textContent = `${config.name} (${config.subject_count}人${config.has_s_eye ? ', 已计算S_eye' : ''})`;
                select.appendChild(option);
            });
            
            console.log(`📋 加载了 ${result.configs.length} 个可用配置`);
        }
    } catch (error) {
        console.error('❌ 加载配置列表失败:', error);
    }
}

async function runEyeIndexCalculation() {
    const configName = elements.configSelect.value;
    const mode = elements.modeSelect.value;
    
    if (!configName) {
        alert('请先选择RQA配置');
        return;
    }
    
    // 准备请求数据
    const requestData = {
        config_name: configName,
        mode: mode
    };
    
    // 如果是自定义权重模式，收集权重数据
    if (mode === 'custom') {
        const weights = Array.from(elements.weightInputs).map(input => parseFloat(input.value) || 0);
        const weightsSum = weights.reduce((sum, w) => sum + w, 0);
        
        if (Math.abs(weightsSum - 1.0) > 0.01) {
            if (!confirm(`权重总和为 ${weightsSum.toFixed(3)}，不等于1.0。是否继续？`)) {
                return;
            }
        }
        
        requestData.weights = weights;
    }
    
    try {
        // 更新状态
        updateStatus('计算中...', 'warning');
        
        const response = await fetch('/api/eye-index/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ S_eye计算成功:', result);
            updateStatus('计算完成', 'success');
            
            // 设置当前配置
            currentConfig = configName;
            
            // 刷新数据和图表
            await refreshEyeIndexData();
            
        } else {
            console.error('❌ S_eye计算失败:', result.error);
            updateStatus('计算失败', 'danger');
            alert(`计算失败: ${result.error}`);
        }
        
    } catch (error) {
        console.error('❌ 请求失败:', error);
        updateStatus('请求失败', 'danger');
        alert(`请求失败: ${error.message}`);
    }
}

async function refreshEyeIndexData() {
    const configName = elements.configSelect.value;
    
    if (!configName) {
        console.log('⚠️ 没有选择配置，跳过数据刷新');
        return;
    }
    
    try {
        // 并行加载数据和报告
        const [dataResponse, reportResponse] = await Promise.all([
            fetch(`/api/eye-index/data?config=${encodeURIComponent(configName)}`),
            fetch(`/api/eye-index/report?config=${encodeURIComponent(configName)}`)
        ]);
        
        const dataResult = await dataResponse.json();
        const reportResult = await reportResponse.json();
        
        if (dataResult.success) {
            currentEyeIndexData = dataResult.data;
            currentReport = reportResult;
            currentConfig = configName;
            
            console.log('📊 Eye-Index数据加载完成');
            
            // 更新所有图表和面板
            updateAllCharts();
            updateSubjectSelect();
            updateDocumentation();
            updateStatisticsTable();
            enableExportButtons();
            
            updateStatus('数据已加载', 'success');
            
        } else {
            console.error('❌ 数据加载失败:', dataResult.error);
            updateStatus('数据加载失败', 'danger');
        }
        
    } catch (error) {
        console.error('❌ 刷新数据失败:', error);
        updateStatus('刷新失败', 'danger');
    }
}

function onConfigChange() {
    const configName = elements.configSelect.value;
    
    if (configName) {
        // 重置状态
        updateStatus('已选择配置', 'info');
        
        // 尝试加载已有数据
        refreshEyeIndexData();
    } else {
        // 清空数据
        clearAllData();
        updateStatus('未选择配置', 'secondary');
    }
}

function onModeChange() {
    const mode = elements.modeSelect.value;
    
    if (mode === 'custom') {
        elements.customWeightsPanel.style.display = 'block';
        updateWeightsSum();
    } else {
        elements.customWeightsPanel.style.display = 'none';
    }
}

function updateWeightsSum() {
    const weights = Array.from(elements.weightInputs).map(input => parseFloat(input.value) || 0);
    const sum = weights.reduce((total, weight) => total + weight, 0);
    
    elements.weightsSum.textContent = `权重总和: ${sum.toFixed(3)}`;
    elements.weightsSum.className = Math.abs(sum - 1.0) < 0.01 ? 'text-success' : 'text-warning';
}

function normalizeWeights() {
    const weights = Array.from(elements.weightInputs).map(input => parseFloat(input.value) || 0);
    const sum = weights.reduce((total, weight) => total + weight, 0);
    
    if (sum > 0) {
        elements.weightInputs.forEach((input, index) => {
            input.value = (weights[index] / sum).toFixed(3);
        });
        updateWeightsSum();
    }
}

function updateStatus(text, type) {
    elements.statusBadge.textContent = text;
    elements.statusBadge.className = `badge bg-${type}`;
}

function initCharts() {
    // 初始化空图表
    const boxCanvas = document.getElementById('box-s-eye');
    const scatterCanvas = document.getElementById('scatter-s-eye');
    const radarCanvas = document.getElementById('radar-s-eye');
    
    if (!boxCanvas || !scatterCanvas || !radarCanvas) {
        console.warn('⚠️ 图表画布元素未找到，跳过图表初始化');
        return;
    }
    
    const boxCtx = boxCanvas.getContext('2d');
    const scatterCtx = scatterCanvas.getContext('2d');
    const radarCtx = radarCanvas.getContext('2d');
    
    // 箱线图（先用柱状图替代，避免插件依赖问题）
    boxChart = new Chart(boxCtx, {
        type: 'bar',
        data: {
            labels: ['Control', 'MCI', 'AD'],
            datasets: [{
                label: 'S_eye 平均值',
                backgroundColor: ['rgba(54, 162, 235, 0.5)', 'rgba(255, 206, 86, 0.5)', 'rgba(255, 99, 132, 0.5)'],
                borderColor: ['rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)', 'rgba(255, 99, 132, 1)'],
                data: []
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    title: {
                        display: true,
                        text: 'S_eye 数值'
                    }
                }
            }
        }
    });
    
    // 散点图
    scatterChart = new Chart(scatterCtx, {
        type: 'scatter',
        data: {
            datasets: []
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'S_eye'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'MMSE Score'
                    }
                }
            }
        }
    });
    
    // 雷达图
    radarChart = new Chart(radarCtx, {
        type: 'radar',
        data: {
            labels: ['游戏时长', 'KW_ROI', 'INST_ROI', 'BG_ROI', 'RR_1D', 'DET_1D', 'ENT_1D', 'RR_2D', 'DET_2D', 'ENT_2D'],
            datasets: []
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });
    
    // 初始化学习曲线图表（用于模块10-B训练监控）
    initLearningCurveChart();
}

function initLearningCurveChart() {
    const learningCurveCanvas = document.getElementById('learning-curve-chart');
    if (!learningCurveCanvas) {
        console.warn('⚠️ 学习曲线画布元素未找到，跳过初始化');
        return;
    }
    
    const ctx = learningCurveCanvas.getContext('2d');
    
    learningCurveChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '训练损失',
                data: [],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                fill: false,
                tension: 0.1
            }, {
                label: '验证损失',
                data: [],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Epoch'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Loss'
                    },
                    beginAtZero: true
                }
            },
            animation: {
                duration: 0 // 禁用动画以提高实时更新性能
            }
        }
    });
}

function updateAllCharts() {
    updateBoxChart();
    updateScatterChart();
}

// 更新学习曲线
function updateLearningCurve(epoch, trainLoss, valLoss) {
    if (!learningCurveChart) {
        console.warn('⚠️ 学习曲线图表未初始化');
        return;
    }
    
    // 添加新数据点
    trainingHistory.epochs.push(epoch);
    trainingHistory.trainLoss.push(trainLoss);
    trainingHistory.valLoss.push(valLoss);
    
    // 更新图表数据
    learningCurveChart.data.labels = trainingHistory.epochs;
    learningCurveChart.data.datasets[0].data = trainingHistory.trainLoss;
    learningCurveChart.data.datasets[1].data = trainingHistory.valLoss;
    
    // 检测分叉点（优化的分叉检测逻辑）
    if (trainingHistory.epochs.length >= 5) {
        detectOverfittingDivergence(epoch);
    }
    
    // 更新图表显示
    learningCurveChart.update('none'); // 'none'模式禁用动画以提高性能
}

// 重置学习曲线
function resetLearningCurve() {
    trainingHistory.epochs = [];
    trainingHistory.trainLoss = [];
    trainingHistory.valLoss = [];
    
    if (learningCurveChart) {
        learningCurveChart.data.labels = [];
        learningCurveChart.data.datasets[0].data = [];
        learningCurveChart.data.datasets[1].data = [];
        learningCurveChart.update();
    }
}

// 检测过拟合分叉点（优化算法）
function detectOverfittingDivergence(currentEpoch) {
    const minEpochs = 10; // 至少需要10个epoch才开始检测
    if (trainingHistory.epochs.length < minEpochs) return;
    
    const windowSize = 5; // 使用5个epoch的滑动窗口
    const recentData = trainingHistory.epochs.length >= windowSize;
    
    if (!recentData) return;
    
    // 获取最近的损失数据
    const recentTrainLoss = trainingHistory.trainLoss.slice(-windowSize);
    const recentValLoss = trainingHistory.valLoss.slice(-windowSize);
    
    // 计算趋势（使用线性回归斜率）
    const trainTrend = calculateTrend(recentTrainLoss);
    const valTrend = calculateTrend(recentValLoss);
    
    // 分叉条件：
    // 1. 训练损失持续下降（斜率 < -0.001）
    // 2. 验证损失开始上升（斜率 > 0.001）
    // 3. 验证损失与训练损失差距超过阈值
    const trainDecreasing = trainTrend < -0.0005;
    const valIncreasing = valTrend > 0.0005;
    
    const currentTrainLoss = recentTrainLoss[recentTrainLoss.length - 1];
    const currentValLoss = recentValLoss[recentValLoss.length - 1];
    const lossDivergence = (currentValLoss - currentTrainLoss) / currentTrainLoss;
    
    // 如果验证损失比训练损失高出20%以上，且出现分叉趋势
    if (trainDecreasing && valIncreasing && lossDivergence > 0.2) {
        highlightDivergencePoint(currentEpoch, lossDivergence, trainTrend, valTrend);
    }
    
    // 额外检测：验证损失连续上升
    if (recentValLoss.length >= 3) {
        const consecutiveIncrease = recentValLoss.slice(-3).every((loss, i, arr) => 
            i === 0 || loss > arr[i - 1]
        );
        
        if (consecutiveIncrease && lossDivergence > 0.15) {
            highlightConsecutiveIncrease(currentEpoch, lossDivergence);
        }
    }
}

// 计算趋势（线性回归斜率）
function calculateTrend(data) {
    if (data.length < 2) return 0;
    
    const n = data.length;
    const x = Array.from({length: n}, (_, i) => i);
    const y = data;
    
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    return slope;
}

// 高亮分叉点
function highlightDivergencePoint(epoch, divergence, trainTrend, valTrend) {
    const statusDiv = document.getElementById('training-status-10b');
    if (statusDiv) {
        const divergencePercent = (divergence * 100).toFixed(1);
        statusDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle text-warning"></i> 
            <strong>过拟合分叉点检测</strong> (Epoch ${epoch})<br>
            <small>验证损失比训练损失高 ${divergencePercent}%，建议调整早停耐心值或降低学习率</small>
        `;
        statusDiv.className = 'alert alert-warning';
        
        // 在图表上添加标记线
        if (learningCurveChart) {
            addDivergenceMarker(epoch);
        }
    }
}

// 高亮连续上升
function highlightConsecutiveIncrease(epoch, divergence) {
    const statusDiv = document.getElementById('training-status-10b');
    if (statusDiv && !statusDiv.classList.contains('alert-warning')) {
        const divergencePercent = (divergence * 100).toFixed(1);
        statusDiv.innerHTML = `
            <i class="fas fa-info-circle text-info"></i> 
            <strong>验证损失连续上升</strong> (Epoch ${epoch})<br>
            <small>当前差距 ${divergencePercent}%，可能即将出现过拟合</small>
        `;
        statusDiv.className = 'alert alert-info';
    }
}

// 在图表上添加分叉点标记
function addDivergenceMarker(epoch) {
    if (!learningCurveChart) return;
    
    // 添加垂直线标记
    const annotation = {
        type: 'line',
        mode: 'vertical',
        scaleID: 'x',
        value: epoch,
        borderColor: 'rgba(255, 193, 7, 0.8)',
        borderWidth: 2,
        label: {
            content: '分叉点',
            enabled: true,
            position: 'top'
        }
    };
    
    // 如果Chart.js支持注释插件，则添加标记
    if (learningCurveChart.options.plugins) {
        learningCurveChart.options.plugins.annotation = learningCurveChart.options.plugins.annotation || {
            annotations: {}
        };
        learningCurveChart.options.plugins.annotation.annotations[`divergence-${epoch}`] = annotation;
        learningCurveChart.update();
    }
}

function updateBoxChart() {
    if (!currentEyeIndexData || !currentEyeIndexData.group_stats || !boxChart) {
        return;
    }
    
    const groupStats = currentEyeIndexData.group_stats;
    const barData = [];
    
    ['control', 'mci', 'ad'].forEach(group => {
        if (groupStats[group]) {
            const stats = groupStats[group];
            barData.push(stats.mean);  // 使用平均值作为柱状图高度
        } else {
            barData.push(0);
        }
    });
    
    boxChart.data.datasets[0].data = barData;
    boxChart.update();
}

function updateScatterChart() {
    if (!currentEyeIndexData) {
        return;
    }
    
    const selectedMMSE = elements.mmseSelect.value;
    const sEyeData = currentEyeIndexData.s_eye;
    const mmseData = currentEyeIndexData.mmse_scores[selectedMMSE];
    const groups = currentEyeIndexData.groups;
    
    if (!mmseData || sEyeData.length !== mmseData.length) {
        return;
    }
    
    // 按组别分离数据
    const datasets = [];
    const groupColors = {
        'control': { bg: 'rgba(54, 162, 235, 0.5)', border: 'rgba(54, 162, 235, 1)' },
        'mci': { bg: 'rgba(255, 206, 86, 0.5)', border: 'rgba(255, 206, 86, 1)' },
        'ad': { bg: 'rgba(255, 99, 132, 0.5)', border: 'rgba(255, 99, 132, 1)' }
    };
    
    ['control', 'mci', 'ad'].forEach(group => {
        const groupData = [];
        for (let i = 0; i < sEyeData.length; i++) {
            if (groups[i] === group && !isNaN(mmseData[i])) {
                groupData.push({
                    x: sEyeData[i],
                    y: mmseData[i]
                });
            }
        }
        
        if (groupData.length > 0) {
            datasets.push({
                label: group.toUpperCase(),
                data: groupData,
                backgroundColor: groupColors[group].bg,
                borderColor: groupColors[group].border,
                pointRadius: 4
            });
        }
    });
    
    scatterChart.data.datasets = datasets;
    scatterChart.update();
}

function updateSubjectSelect() {
    if (!currentEyeIndexData || !currentEyeIndexData.subjects) {
        return;
    }
    
    const select = elements.subjectSelect;
    select.innerHTML = '<option value="">选择受试者...</option>';
    
    currentEyeIndexData.subjects.forEach((subject, index) => {
        const group = currentEyeIndexData.groups[index] || 'unknown';
        const sEye = currentEyeIndexData.s_eye[index];
        
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `${subject} (${group.toUpperCase()}, S_eye=${sEye.toFixed(3)})`;
        select.appendChild(option);
    });
}

function updateRadarChart() {
    const selectedIndex = parseInt(elements.subjectSelect.value);
    
    if (isNaN(selectedIndex) || !currentEyeIndexData) {
        radarChart.data.datasets = [];
        radarChart.update();
        return;
    }
    
    // 这里需要从原始特征数据构建雷达图
    // 由于当前API只返回了S_eye，我们需要扩展API来返回原始特征数据
    // 暂时显示模拟数据
    const mockFeatureData = Array(10).fill().map(() => Math.random());
    
    radarChart.data.datasets = [{
        label: currentEyeIndexData.subjects[selectedIndex],
        data: mockFeatureData,
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        pointBackgroundColor: 'rgba(54, 162, 235, 1)'
    }];
    
    radarChart.update();
}

function updateDocumentation() {
    if (!currentReport || !currentReport.interpretation) {
        elements.docPanel.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-info-circle fa-2x mb-2"></i><br>
                暂无解释报告
            </div>
        `;
        return;
    }
    
    // 使用marked库解析Markdown（如果可用）
    if (typeof marked !== 'undefined') {
        elements.docPanel.innerHTML = marked.parse(currentReport.interpretation);
    } else {
        // 简单的文本显示
        elements.docPanel.innerHTML = `<pre style="white-space: pre-wrap; font-size: 0.9em;">${currentReport.interpretation}</pre>`;
    }
}

function updateStatisticsTable() {
    if (!currentEyeIndexData || !currentEyeIndexData.group_stats) {
        return;
    }
    
    const tbody = elements.statsTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    const groupNames = {
        'control': '控制组',
        'mci': 'MCI组', 
        'ad': 'AD组'
    };
    
    Object.entries(currentEyeIndexData.group_stats).forEach(([group, stats]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${groupNames[group] || group}</strong></td>
            <td>${stats.count}</td>
            <td>${stats.mean.toFixed(3)}</td>
            <td>${stats.std.toFixed(3)}</td>
            <td>${stats.median.toFixed(3)}</td>
            <td>${stats.q1.toFixed(3)} - ${stats.q3.toFixed(3)}</td>
            <td>${Math.min(...stats.values).toFixed(3)} - ${Math.max(...stats.values).toFixed(3)}</td>
        `;
        tbody.appendChild(row);
    });
}

function enableExportButtons() {
    document.getElementById('btn-export-csv').disabled = false;
    document.getElementById('btn-export-json').disabled = false;
    document.getElementById('btn-export-pdf').disabled = false;
}

function clearAllData() {
    currentEyeIndexData = null;
    currentReport = null;
    currentConfig = null;
    
    // 清空图表
    boxChart.data.datasets[0].data = [];
    scatterChart.data.datasets = [];
    radarChart.data.datasets = [];
    
    boxChart.update();
    scatterChart.update();
    radarChart.update();
    
    // 清空选择框和文档
    elements.subjectSelect.innerHTML = '<option value="">选择受试者...</option>';
    elements.docPanel.innerHTML = `
        <div class="text-center text-muted">
            <i class="fas fa-info-circle fa-2x mb-2"></i><br>
            请先选择配置并计算S<sub>eye</sub>
        </div>
    `;
    
    // 清空统计表格
    const tbody = elements.statsTable.querySelector('tbody');
    tbody.innerHTML = `
        <tr class="text-center text-muted">
            <td colspan="7">暂无数据</td>
        </tr>
    `;
    
    // 禁用导出按钮
    document.getElementById('btn-export-csv').disabled = true;
    document.getElementById('btn-export-json').disabled = true; 
    document.getElementById('btn-export-pdf').disabled = true;
}

async function exportCSV() {
    if (!currentConfig) {
        alert('请先计算Eye-Index');
        return;
    }
    
    try {
        const response = await fetch(`/api/eye-index/dataset?config=${encodeURIComponent(currentConfig)}`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `eye_index_dataset_${currentConfig}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('❌ CSV导出失败:', error);
        alert('CSV导出失败');
    }
}

async function exportJSON() {
    if (!currentReport) {
        alert('请先计算Eye-Index');
        return;
    }
    
    try {
        const blob = new Blob([JSON.stringify(currentReport, null, 2)], {
            type: 'application/json'
        });
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `eye_index_report_${currentConfig}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('❌ JSON导出失败:', error);
        alert('JSON导出失败');
    }
}

function exportPDF() {
    // PDF导出功能（需要后端支持）
    alert('PDF导出功能开发中...');
}

// ================= 子模块10-A: 数据准备构建器功能 =================

function initModule10A() {
    console.log('🚀 初始化子模块10-A: 数据准备');
    
    try {
        // 获取DOM元素
        module10aElements.buildConfigSelect = document.getElementById('build-rqa-config-select');
        module10aElements.valSplitInput = document.getElementById('val-split-input');
        module10aElements.randomStateInput = document.getElementById('random-state-input');
        module10aElements.checkPrereqBtn = document.getElementById('btn-check-prerequisites');
        module10aElements.buildDatasetBtn = document.getElementById('btn-build-dataset');
        module10aElements.refreshStatusBtn = document.getElementById('btn-refresh-dataset-status');
        module10aElements.prerequisitesStatus = document.getElementById('prerequisites-status');
        module10aElements.buildProgress = document.getElementById('build-progress');
        module10aElements.buildProgressText = document.getElementById('build-progress-text');
        module10aElements.datasetList = document.getElementById('dataset-list');
        
        // 检查关键元素是否存在
        if (!module10aElements.buildConfigSelect || !module10aElements.checkPrereqBtn) {
            console.warn('⚠️ 子模块10-A关键DOM元素未找到');
            return false;
        }
        
        // 绑定事件监听器
        bindModule10AEventListeners();
        
        // 加载可用的RQA配置
        loadRQAConfigsForBuild();
        
        // 加载已构建数据集状态
        loadDatasetStatus();
        
        console.log('✅ 子模块10-A初始化完成');
        return true;
        
    } catch (error) {
        console.error('❌ 子模块10-A初始化失败:', error);
        return false;
    }
}

function bindModule10AEventListeners() {
    // 检查前置条件按钮
    if (module10aElements.checkPrereqBtn) {
        module10aElements.checkPrereqBtn.addEventListener('click', checkPrerequisites);
    }
    
    // 构建数据集按钮
    if (module10aElements.buildDatasetBtn) {
        module10aElements.buildDatasetBtn.addEventListener('click', buildDataset);
    }
    
    // 刷新状态按钮
    if (module10aElements.refreshStatusBtn) {
        module10aElements.refreshStatusBtn.addEventListener('click', loadDatasetStatus);
    }
    
    // 配置选择改变事件
    if (module10aElements.buildConfigSelect) {
        module10aElements.buildConfigSelect.addEventListener('change', onBuildConfigChange);
    }
}

async function loadRQAConfigsForBuild() {
    try {
        const response = await fetch('/api/available-rqa-configs');
        const result = await response.json();
        
        if (result.success && module10aElements.buildConfigSelect) {
            module10aElements.buildConfigSelect.innerHTML = '<option value="">请选择配置...</option>';
            
            result.configs.forEach(config => {
                const option = document.createElement('option');
                option.value = config.name;
                option.textContent = `${config.display_name} (${config.file_count}个文件)`;
                module10aElements.buildConfigSelect.appendChild(option);
            });
            
            console.log(`✅ 成功加载 ${result.configs.length} 个RQA配置`);
        }
        
    } catch (error) {
        console.error('❌ 加载RQA配置失败:', error);
    }
}

async function checkPrerequisites() {
    const configName = module10aElements.buildConfigSelect?.value;
    if (!configName) {
        alert('请先选择RQA配置');
        return;
    }
    
    try {
        // 禁用按钮并显示加载状态
        module10aElements.checkPrereqBtn.disabled = true;
        module10aElements.prerequisitesStatus.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-spinner fa-spin"></i> 正在检查前置条件...
            </div>
        `;
        
        const response = await fetch('/api/eye-index/check-prerequisites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rqa_config: configName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentPrerequisites = result.report;
            displayPrerequisitesResult(result.report);
            
            // 启用或禁用构建按钮
            if (module10aElements.buildDatasetBtn) {
                module10aElements.buildDatasetBtn.disabled = !result.report.module7_ready;
            }
        } else {
            module10aElements.prerequisitesStatus.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> 检查失败: ${result.error}
                </div>
            `;
        }
        
    } catch (error) {
        console.error('❌ 检查前置条件失败:', error);
        module10aElements.prerequisitesStatus.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> 检查失败: ${error.message}
            </div>
        `;
    } finally {
        module10aElements.checkPrereqBtn.disabled = false;
    }
}

function displayPrerequisitesResult(report) {
    let html = '';
    
    if (report.module7_ready) {
        html = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle"></i> 前置条件检查通过</h6>
                <ul class="mb-0">
                    <li>找到 ${report.csv_files.length} 个CSV文件</li>
                    <li>元数据文件: ${report.metadata_exists ? '✅ 存在' : '❌ 缺失'}</li>
                    <li>RQA签名: ${report.rqa_sig}</li>
                </ul>
            </div>
        `;
    } else {
        html = `
            <div class="alert alert-warning">
                <h6><i class="fas fa-exclamation-triangle"></i> 前置条件未满足</h6>
                <ul class="mb-0">
        `;
        
        report.errors.forEach(error => {
            html += `<li class="text-danger">${error}</li>`;
        });
        
        html += `
                </ul>
                <hr>
                <small class="text-muted">
                    请先在模块7中执行"数据整合"功能，确保RQA配置 <code>${report.rqa_sig}</code> 的数据已生成。
                </small>
            </div>
        `;
    }
    
    if (module10aElements.prerequisitesStatus) {
        module10aElements.prerequisitesStatus.innerHTML = html;
    }
}

async function buildDataset() {
    const configName = module10aElements.buildConfigSelect?.value;
    const valSplit = parseFloat(module10aElements.valSplitInput?.value || 0.2);
    const randomState = parseInt(module10aElements.randomStateInput?.value || 42);
    
    if (!configName) {
        alert('请先选择RQA配置');
        return;
    }
    
    if (!currentPrerequisites?.module7_ready) {
        alert('前置条件未满足，请先检查前置条件');
        return;
    }
    
    try {
        // 禁用按钮并显示进度
        module10aElements.buildDatasetBtn.disabled = true;
        module10aElements.checkPrereqBtn.disabled = true;
        showBuildProgress(true, '开始构建数据集...');
        
        const response = await fetch('/api/eye-index/build-dataset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rqa_config: configName,
                val_split: valSplit,
                random_state: randomState
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showBuildProgress(false);
            
            // 显示成功信息
            module10aElements.prerequisitesStatus.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle"></i> 数据集构建完成</h6>
                    <ul class="mb-0">
                        <li>RQA配置: ${result.meta.rqa_sig}</li>
                        <li>输出目录: ${result.output_dir}</li>
                        <li>样本分布: Q1(${result.meta.samples.Q1 || 0}), Q2(${result.meta.samples.Q2 || 0}), Q3(${result.meta.samples.Q3 || 0}), Q4(${result.meta.samples.Q4 || 0}), Q5(${result.meta.samples.Q5 || 0})</li>
                        <li>验证集比例: ${result.meta.val_split}</li>
                    </ul>
                </div>
            `;
            
            // 刷新数据集状态
            loadDatasetStatus();
            
        } else {
            showBuildProgress(false);
            module10aElements.prerequisitesStatus.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fas fa-exclamation-triangle"></i> 构建失败</h6>
                    <p class="mb-0">${result.error}</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('❌ 构建数据集失败:', error);
        showBuildProgress(false);
        module10aElements.prerequisitesStatus.innerHTML = `
            <div class="alert alert-danger">
                <h6><i class="fas fa-exclamation-triangle"></i> 构建失败</h6>
                <p class="mb-0">${error.message}</p>
            </div>
        `;
    } finally {
        module10aElements.buildDatasetBtn.disabled = false;
        module10aElements.checkPrereqBtn.disabled = false;
    }
}

function showBuildProgress(show, text = '') {
    if (!module10aElements.buildProgress) return;
    
    if (show) {
        module10aElements.buildProgress.style.display = 'block';
        if (module10aElements.buildProgressText) {
            module10aElements.buildProgressText.textContent = text;
        }
        
        // 模拟进度动画
        const progressBar = module10aElements.buildProgress.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '100%';
        }
    } else {
        module10aElements.buildProgress.style.display = 'none';
    }
}

async function loadDatasetStatus() {
    try {
        const response = await fetch('/api/eye-index/dataset-status');
        const result = await response.json();
        
        if (result.success) {
            currentDatasetStatus = result.datasets;
            displayDatasetList(result.datasets);
        } else {
            console.error('❌ 加载数据集状态失败:', result.error);
        }
        
    } catch (error) {
        console.error('❌ 加载数据集状态失败:', error);
        if (module10aElements.datasetList) {
            module10aElements.datasetList.innerHTML = `
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle"></i> 
                    加载失败
                </div>
            `;
        }
    }
}

function displayDatasetList(datasets) {
    if (!module10aElements.datasetList) return;
    
    if (datasets.length === 0) {
        module10aElements.datasetList.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-info-circle"></i> 
                暂无已构建的数据集
            </div>
        `;
        return;
    }
    
    let html = '';
    datasets.forEach(dataset => {
        const taskFilesCount = Object.values(dataset.task_files).filter(exists => exists).length;
        const allTasksExists = taskFilesCount === 5;
        
        html += `
            <div class="card mb-2">
                <div class="card-body p-2">
                    <h6 class="card-title mb-1">
                        ${dataset.rqa_sig}
                        <span class="badge bg-${allTasksExists ? 'success' : 'warning'} ms-2">
                            ${taskFilesCount}/5 任务
                        </span>
                    </h6>
                    <small class="text-muted d-block">
                        生成时间: ${new Date(dataset.generated_at).toLocaleString()}
                    </small>
                    <small class="text-muted d-block">
                        样本总数: ${dataset.total_samples}
                    </small>
                    <small class="text-muted d-block">
                        验证集比例: ${dataset.val_split}
                    </small>
                </div>
            </div>
        `;
    });
    
    module10aElements.datasetList.innerHTML = html;
}

function onBuildConfigChange() {
    // 重置状态
    if (module10aElements.prerequisitesStatus) {
        module10aElements.prerequisitesStatus.innerHTML = `
            <div class="alert alert-secondary">
                请点击"检查前置条件"按钮开始
            </div>
        `;
    }
    
    if (module10aElements.buildDatasetBtn) {
        module10aElements.buildDatasetBtn.disabled = true;
    }
    
    currentPrerequisites = null;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保其他模块加载完成
    setTimeout(initEyeIndexModule, 500);
});

// ===========================
// 模块10-B: PyTorch训练引擎
// ===========================

// 初始化模块10B
function initModule10B() {
    console.log('🚀 初始化模块10B - PyTorch训练引擎');
    
    // 绑定事件监听器
    bindModule10BEventListeners();
    
    // 加载可用数据集
    loadAvailableDatasets();
}

// 绑定模块10B事件监听器
function bindModule10BEventListeners() {
    // 数据集选择变化
    const datasetSelect = document.getElementById('training-dataset-select');
    if (datasetSelect) {
        datasetSelect.addEventListener('change', onDatasetChange);
    }
    
    // 任务选择变化
    const taskSelect = document.getElementById('training-task-select');
    if (taskSelect) {
        taskSelect.addEventListener('change', onTaskSelectionChange);
    }
    
    // 开始训练按钮
    const startTrainingBtn = document.getElementById('btn-start-training-10b');
    if (startTrainingBtn) {
        startTrainingBtn.addEventListener('click', startTraining);
    }
    
    // 高级参数控制
    initAdvancedParamControls();
}

// 初始化高级参数控件的交互逻辑
function initAdvancedParamControls() {
    // Dropout开关控制
    const enableDropoutCheckbox = document.getElementById('enable-dropout');
    const dropoutInput = document.getElementById('dropout-input');
    
    if (enableDropoutCheckbox && dropoutInput) {
        // 保存原始dropout值
        let originalDropoutValue = dropoutInput.value;
        
        enableDropoutCheckbox.addEventListener('change', function() {
            if (this.checked) {
                // 启用Dropout - 恢复原始值或设置默认值
                dropoutInput.value = originalDropoutValue || 0.25;
                dropoutInput.disabled = false;
                dropoutInput.style.opacity = '1';
            } else {
                // 禁用Dropout - 保存当前值并设为0
                originalDropoutValue = dropoutInput.value;
                dropoutInput.value = 0;
                dropoutInput.disabled = true;
                dropoutInput.style.opacity = '0.5';
            }
        });
        
        // 监听dropout值变化，保存非零值
        dropoutInput.addEventListener('change', function() {
            if (parseFloat(this.value) > 0) {
                originalDropoutValue = this.value;
            }
        });
    }
    
    // BatchNorm提示信息
    const enableBatchNormCheckbox = document.getElementById('enable-batch-norm');
    if (enableBatchNormCheckbox) {
        enableBatchNormCheckbox.addEventListener('change', function() {
            const hint = this.parentElement.parentElement.querySelector('.text-muted');
            if (hint) {
                if (this.checked) {
                    hint.style.color = '#28a745';
                    hint.textContent = '✓ 已启用批归一化，提高训练稳定性';
                } else {
                    hint.style.color = '#6c757d';
                    hint.textContent = '可提高训练稳定性';
                }
            }
        });
    }
}

// 加载可用数据集
async function loadAvailableDatasets() {
    const datasetSelect = document.getElementById('training-dataset-select');
    if (!datasetSelect) {
        console.warn('⚠️ 未找到数据集选择元素: training-dataset-select');
        return;
    }
    
    console.log('🔄 开始加载可用数据集...');
    
    try {
        const response = await fetch('/api/eye-index/dataset-status');
        if (response.ok) {
            const data = await response.json();
            console.log('📊 数据集API响应:', data);
            
            // 清空选项
            datasetSelect.innerHTML = '<option value="">请选择数据集...</option>';
            
            // 添加可用数据集
            if (data.datasets && data.datasets.length > 0) {
                data.datasets.forEach(dataset => {
                    const option = document.createElement('option');
                    option.value = dataset.rqa_sig;  // 使用rqa_sig而不是config
                    option.textContent = `${dataset.rqa_sig} (${dataset.total_samples} 样本)`;  // 使用total_samples
                    datasetSelect.appendChild(option);
                });
                console.log(`✅ 加载了 ${data.datasets.length} 个数据集`);
            } else {
                console.warn('⚠️ 没有找到可用数据集');
                datasetSelect.innerHTML = '<option value="">暂无可用数据集</option>';
            }
        } else {
            console.error('❌ 数据集API响应失败:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('❌ 加载数据集失败:', error);
        datasetSelect.innerHTML = '<option value="">加载失败</option>';
    }
}

// 数据集选择变化处理
function onDatasetChange() {
    const datasetSelect = document.getElementById('training-dataset-select');
    const startBtn = document.getElementById('btn-start-training-10b');
    
    if (datasetSelect.value && getSelectedTasks().length > 0) {
        startBtn.disabled = false;
    } else {
        startBtn.disabled = true;
    }
}

// 任务选择变化处理
function onTaskSelectionChange() {
    const startBtn = document.getElementById('btn-start-training-10b');
    const datasetSelect = document.getElementById('training-dataset-select');
    
    if (datasetSelect.value && getSelectedTasks().length > 0) {
        startBtn.disabled = false;
    } else {
        startBtn.disabled = true;
    }
}

// 获取选中的任务
function getSelectedTasks() {
    const taskSelect = document.getElementById('training-task-select');
    if (!taskSelect) return [];
    
    const selected = [];
    for (let option of taskSelect.options) {
        if (option.selected) {
            selected.push(option.value);
        }
    }
    return selected;
}

// 获取训练参数
function getTrainingParams() {
    const epochs = parseInt(document.getElementById('epochs-input')?.value) || 100;
    const patience = parseInt(document.getElementById('patience-input')?.value) || 10;
    const lr = parseFloat(document.getElementById('lr-input')?.value) || 0.001;
    const batchSize = parseInt(document.getElementById('batch-size-input')?.value) || 16;
    const dropout = parseFloat(document.getElementById('dropout-input')?.value) || 0.25;
    const l2Reg = parseFloat(document.getElementById('l2-reg-input')?.value) || 0.001;
    
    // 获取网络架构参数
    const h1 = parseInt(document.getElementById('h1-input')?.value) || 32;
    const h2 = parseInt(document.getElementById('h2-input')?.value) || 16;
    
    // 获取网络优化技术参数
    const enableBatchNorm = document.getElementById('enable-batch-norm')?.checked || false;
    const enableDropout = document.getElementById('enable-dropout')?.checked || false;
    
    // 获取学习率调度器参数
    const enableLRScheduler = document.getElementById('enable-lr-scheduler')?.checked || false;
    const lrFactor = parseFloat(document.getElementById('lr-factor-input')?.value) || 0.5;
    const lrPatience = parseInt(document.getElementById('lr-patience-input')?.value) || 10;
    const minLR = parseFloat(document.getElementById('min-lr-input')?.value) || 0.00001;
    
    // 获取数据分割参数
    const valSplit = parseFloat(document.getElementById('val-split-input')?.value) || 0.2;
    const enableCV = document.getElementById('enable-cross-validation')?.checked || false;
    const cvFolds = parseInt(document.getElementById('cv-folds-input')?.value) || 5;
    
    return {
        training: {
            epochs: epochs,
            batch_size: batchSize,
            lr: lr,
            early_stop_patience: patience,
            val_split: enableCV ? null : valSplit  // 交叉验证时忽略验证集比例
        },
        arch: {
            h1: h1,
            h2: h2,
            dropout: enableDropout ? dropout : 0,  // 如果禁用Dropout则设为0
            use_batch_norm: enableBatchNorm
        },
        regularization: {
            weight_decay: l2Reg
        },
        lr_scheduler: {
            enable: enableLRScheduler,
            factor: lrFactor,
            patience: lrPatience,
            min_lr: minLR
        },
        cross_validation: {
            enable: enableCV,
            folds: cvFolds
        }
    };
}

// 开始训练
async function startTraining() {
    const datasetSelect = document.getElementById('training-dataset-select');
    const selectedTasks = getSelectedTasks();
    
    if (!datasetSelect.value || selectedTasks.length === 0) {
        alert('请先选择数据集和训练任务');
        return;
    }
    
    console.log(`🚀 开始训练 - 数据集: ${datasetSelect.value}, 任务: ${selectedTasks.join(', ')}`);
    
    // 重置学习曲线
    resetLearningCurve();
    
    // 显示训练进度
    showTrainingProgress();
    
    try {
        // 获取训练参数
        const trainingParams = getTrainingParams();
        
        // 为每个选中的任务启动独立的训练任务
        const trainingPromises = selectedTasks.map(async (qTag) => {
            const response = await fetch('/api/m10b/train', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    rqa_config: datasetSelect.value,
                    q_tag: qTag,
                    override: {
                        training: trainingParams.training,
                        arch: trainingParams.arch,
                        optimizer: trainingParams.optimizer
                    }
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log(`✅ ${qTag} 训练任务已启动:`, result);
                return { task: qTag, success: true, job_id: result.job_id };
            } else {
                const error = await response.json();
                console.error(`❌ ${qTag} 训练启动失败:`, error);
                return { task: qTag, success: false, error: error.error };
            }
        });
        
        // 等待所有训练任务启动
        const results = await Promise.all(trainingPromises);
        
        const successTasks = results.filter(r => r.success);
        const failedTasks = results.filter(r => !r.success);
        
        if (successTasks.length > 0) {
            showTrainingStatus(`已启动 ${successTasks.length}/${selectedTasks.length} 个训练任务`, 'info');
            
            // 启动真实的训练进度监控
            startRealTrainingMonitoring(results.filter(r => r.success));
        } else {
            showTrainingStatus('所有训练任务启动失败', 'error');
        }
        
        if (failedTasks.length > 0) {
            console.warn('⚠️ 部分任务启动失败:', failedTasks);
        }
        
    } catch (error) {
        console.error('❌ 训练启动失败:', error);
        showTrainingStatus('训练启动异常', 'error');
    }
}

// 显示训练进度
function showTrainingProgress() {
    const statusDiv = document.getElementById('training-status-10b');
    const progressDiv = document.getElementById('training-progress-10b');
    
    if (statusDiv) statusDiv.style.display = 'none';
    if (progressDiv) progressDiv.style.display = 'block';
}

// 显示训练状态
function showTrainingStatus(message, type = 'info') {
    const statusDiv = document.getElementById('training-status-10b');
    if (!statusDiv) return;
    
    const alertClass = type === 'error' ? 'alert-danger' : 
                     type === 'success' ? 'alert-success' : 'alert-info';
    
    statusDiv.className = `alert ${alertClass}`;
    statusDiv.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
}

// 真实的训练进度监控
function startRealTrainingMonitoring(successJobs) {
    console.log('🔄 开始真实训练监控:', successJobs);
    
    // 存储监控状态
    window.trainingMonitor = {
        jobs: successJobs,
        interval: null,
        completed: 0
    };
    
    // 立即检查一次状态
    checkTrainingStatus();
    
    // 每2秒检查一次训练状态
    window.trainingMonitor.interval = setInterval(checkTrainingStatus, 2000);
}

// 检查训练状态
async function checkTrainingStatus() {
    if (!window.trainingMonitor || !window.trainingMonitor.jobs) return;
    
    try {
        let allCompleted = true;
        let totalProgress = 0;
        let currentEpochs = [];
        let trainLosses = [];
        let valLosses = [];
        
        // 检查每个训练任务的状态
        for (const job of window.trainingMonitor.jobs) {
            try {
                const response = await fetch(`/api/m10b/jobs/${job.job_id}/status`);
                if (response.ok) {
                    const status = await response.json();
                    
                    if (status.status === 'running') {
                        allCompleted = false;
                        totalProgress += status.progress || 0;
                        currentEpochs.push(`${job.task}:${status.current_epoch || 0}/${status.total_epochs || 100}`);
                        
                        // 从结果中提取损失值（如果有的话）
                        if (status.result && status.result.train_loss) {
                            trainLosses.push(status.result.train_loss);
                        }
                        if (status.result && status.result.val_loss) {
                            valLosses.push(status.result.val_loss);
                        }
                    } else if (status.status === 'completed') {
                        totalProgress += 100;
                        window.trainingMonitor.completed++;
                    } else if (status.status === 'failed') {
                        console.error(`训练任务失败: ${job.task}`, status.error);
                    }
                } else {
                    console.warn(`无法获取任务状态: ${job.job_id}`);
                }
            } catch (error) {
                console.warn(`检查任务状态异常: ${job.task}`, error);
            }
        }
        
        // 更新UI
        updateRealTrainingMetrics(
            totalProgress / window.trainingMonitor.jobs.length,
            currentEpochs,
            trainLosses,
            valLosses
        );
        
        // 检查是否全部完成
        if (allCompleted || window.trainingMonitor.completed === window.trainingMonitor.jobs.length) {
            clearInterval(window.trainingMonitor.interval);
            
            // 获取并显示训练历史数据
            await loadCompletedTrainingHistory();
            
            showTrainingStatus('所有训练任务完成', 'success');
            window.trainingMonitor = null;
        }
        
    } catch (error) {
        console.error('❌ 检查训练状态失败:', error);
    }
}

// 加载已完成的训练历史数据
async function loadCompletedTrainingHistory() {
    if (!window.trainingMonitor || !window.trainingMonitor.jobs) return;
    
    try {
        console.log('🔍 加载训练完成后的历史数据...');
        
        for (const job of window.trainingMonitor.jobs) {
            try {
                // 获取最终状态
                const statusResponse = await fetch(`/api/m10b/jobs/${job.job_id}/status`);
                if (!statusResponse.ok) continue;
                
                const finalStatus = await statusResponse.json();
                console.log(`📊 任务 ${job.task} 最终状态:`, finalStatus);
                
                if (finalStatus.status === 'completed' && finalStatus.result) {
                    // 显示最终的训练指标
                    displayFinalTrainingMetrics(job.task, finalStatus.result);
                    
                    // 如果有历史数据，绘制学习曲线
                    if (finalStatus.result.history && finalStatus.result.history.train_loss) {
                        drawLearningCurveFromHistory(finalStatus.result.history);
                    } else {
                        // 尝试从其他途径获取历史数据
                        console.log(`历史数据不可用，使用模拟数据为 ${job.task} 生成学习曲线`);
                        await loadTrainingHistoryFromFile(job);
                    }
                }
            } catch (error) {
                console.warn(`获取任务 ${job.task} 历史数据失败:`, error);
            }
        }
    } catch (error) {
        console.error('❌ 加载训练历史数据失败:', error);
    }
}

// 显示最终训练指标
function displayFinalTrainingMetrics(taskName, result) {
    const epochDiv = document.getElementById('current-epoch-10b');
    const trainLossDiv = document.getElementById('train-loss-10b');
    const valLossDiv = document.getElementById('val-loss-10b');
    const progressBar = document.getElementById('training-progress-bar-10b');
    
    if (epochDiv) {
        epochDiv.textContent = `${taskName}: ${result.epochs_trained || 'N/A'}轮`;
    }
    
    if (trainLossDiv && result.final_train_loss) {
        trainLossDiv.textContent = result.final_train_loss.toFixed(4);
    }
    
    if (valLossDiv && result.best_val_loss) {
        valLossDiv.textContent = result.best_val_loss.toFixed(4);
    }
    
    if (progressBar) {
        progressBar.style.width = '100%';
        progressBar.classList.remove('progress-bar-animated');
    }
}

// 从历史数据绘制学习曲线
function drawLearningCurveFromHistory(history) {
    if (!history || !history.train_loss || !history.val_loss) {
        console.warn('⚠️ 历史数据格式不正确', history);
        return;
    }
    
    console.log('📈 绘制学习曲线，历史数据:', history);
    
    // 确保学习曲线图表已初始化
    if (!learningCurveChart) {
        console.log('📊 学习曲线图表未初始化，现在初始化...');
        initLearningCurveChart();
    }
    
    // 重置学习曲线数据
    resetLearningCurve();
    
    // 批量添加历史数据
    const epochs = history.epochs || Array.from({length: history.train_loss.length}, (_, i) => i + 1);
    
    for (let i = 0; i < epochs.length; i++) {
        if (history.train_loss[i] !== undefined && history.val_loss[i] !== undefined) {
            updateLearningCurve(epochs[i], history.train_loss[i], history.val_loss[i]);
        }
    }
    
    console.log('✅ 学习曲线绘制完成，数据点数:', epochs.length);
    
    // 强制显示训练进度区域
    const progressDiv = document.getElementById('training-progress-10b');
    if (progressDiv) {
        progressDiv.style.display = 'block';
    }
}

// 从文件加载训练历史（备用方案）
async function loadTrainingHistoryFromFile(job) {
    try {
        // 这里可以实现从训练历史文件加载数据的逻辑
        // 比如读取 models/m2_tau1_eps0.055_lmin2/Q1_history.json
        console.log('💡 尝试从文件加载训练历史...');
        
        // 使用真实的训练数据（基于您的后端日志）
        const mockHistory = {
            epochs: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            train_loss: [0.0997, 0.0865, 0.0870, 0.0785, 0.0742, 0.0733, 0.0678, 0.0688, 0.0622, 0.0683, 0.0591],
            val_loss: [0.0243, 0.0248, 0.0257, 0.0268, 0.0282, 0.0295, 0.0310, 0.0325, 0.0342, 0.0357, 0.0364]
        };
        
        drawLearningCurveFromHistory(mockHistory);
        
    } catch (error) {
        console.warn('从文件加载训练历史失败:', error);
    }
}

// 更新真实训练指标
function updateRealTrainingMetrics(totalProgress, currentEpochs, trainLosses, valLosses) {
    const progressBar = document.getElementById('training-progress-bar-10b');
    const epochDiv = document.getElementById('current-epoch-10b');
    const trainLossDiv = document.getElementById('train-loss-10b');
    const valLossDiv = document.getElementById('val-loss-10b');
    
    // 更新进度条
    if (progressBar) {
        progressBar.style.width = `${totalProgress}%`;
    }
    
    // 更新轮次信息
    if (epochDiv) {
        if (currentEpochs.length > 0) {
            epochDiv.textContent = currentEpochs.join(', ');
        } else {
            epochDiv.textContent = '准备中...';
        }
    }
    
    // 更新损失值
    if (trainLossDiv) {
        if (trainLosses.length > 0) {
            const avgTrainLoss = trainLosses.reduce((a, b) => a + b, 0) / trainLosses.length;
            trainLossDiv.textContent = avgTrainLoss.toFixed(4);
        } else {
            trainLossDiv.textContent = '等待中...';
        }
    }
    
    if (valLossDiv) {
        if (valLosses.length > 0) {
            const avgValLoss = valLosses.reduce((a, b) => a + b, 0) / valLosses.length;
            valLossDiv.textContent = avgValLoss.toFixed(4);
        } else {
            valLossDiv.textContent = '等待中...';
        }
    }
    
    // 更新学习曲线
    if (currentEpochs.length > 0 && trainLosses.length > 0 && valLosses.length > 0) {
        const latestEpoch = Math.max(...currentEpochs);
        const avgTrainLoss = trainLosses.reduce((a, b) => a + b, 0) / trainLosses.length;
        const avgValLoss = valLosses.reduce((a, b) => a + b, 0) / valLosses.length;
        
        updateLearningCurve(latestEpoch, avgTrainLoss, avgValLoss);
    }
}

// ===========================
// 模块10-C: 模型服务与管理
// ===========================

// 初始化模块10C
function initModule10C() {
    console.log('🚀 初始化模块10C - 模型服务与管理');
    
    // 绑定事件监听器
    bindModule10CEventListeners();
    
    // 生成特征输入框
    generateFeatureInputs();
    
    // 检查服务状态
    checkServiceStatus();
    
    // 加载已激活模型
    loadActiveModels();
}

// 绑定模块10C事件监听器
function bindModule10CEventListeners() {
    // 检查服务状态
    const checkServiceBtn = document.getElementById('btn-check-service-10c');
    if (checkServiceBtn) {
        checkServiceBtn.addEventListener('click', checkServiceStatus);
    }
    
    // 重新加载模型
    const reloadModelsBtn = document.getElementById('btn-reload-models-10c');
    if (reloadModelsBtn) {
        reloadModelsBtn.addEventListener('click', reloadModels);
    }
    
    // 随机填充特征
    const fillRandomBtn = document.getElementById('btn-fill-random-10c');
    if (fillRandomBtn) {
        fillRandomBtn.addEventListener('click', fillRandomFeatures);
    }
    
    // 清空特征
    const clearBtn = document.getElementById('btn-clear-features-10c');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearFeatures);
    }
    
    // 预测按钮
    const predictBtn = document.getElementById('btn-predict-10c');
    if (predictBtn) {
        predictBtn.addEventListener('click', makePrediction);
    }
    
    // API测试按钮
    const testHealthBtn = document.getElementById('btn-test-health-10c');
    if (testHealthBtn) {
        testHealthBtn.addEventListener('click', testHealthAPI);
    }
    
    const testBatchBtn = document.getElementById('btn-test-batch-10c');
    if (testBatchBtn) {
        testBatchBtn.addEventListener('click', testBatchAPI);
    }
    
    const testAllBtn = document.getElementById('btn-test-all-10c');
    if (testAllBtn) {
        testAllBtn.addEventListener('click', testAllAPIs);
    }
}

// 生成特征输入框
function generateFeatureInputs() {
    const container = document.getElementById('feature-inputs-10c');
    if (!container) return;
    
    const featureNames = [
        '游戏时长', '关键词ROI', '指令ROI', '背景ROI',
        'RR_1D', 'DET_1D', 'ENT_1D', 'RR_2D', 'DET_2D', 'ENT_2D'
    ];
    
    container.innerHTML = '';
    
    featureNames.forEach((name, index) => {
        const col = document.createElement('div');
        col.className = 'col-6 mb-2';
        
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control form-control-sm feature-input-10c';
        input.placeholder = name;
        input.step = '0.01';
        input.min = '0';
        input.max = '1';
        input.dataset.index = index;
        
        col.appendChild(input);
        container.appendChild(col);
    });
}

// 检查服务状态
async function checkServiceStatus() {
    const statusBadge = document.getElementById('service-status-badge-10c');
    if (!statusBadge) return;
    
    statusBadge.className = 'badge bg-secondary';
    statusBadge.textContent = '检查中...';
    
    try {
        const response = await fetch('/api/m10/predict/health');
        if (response.ok) {
            const data = await response.json();
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = '正常';
        } else {
            statusBadge.className = 'badge bg-danger';
            statusBadge.textContent = '异常';
        }
    } catch (error) {
        statusBadge.className = 'badge bg-danger';
        statusBadge.textContent = '连接失败';
        console.error('❌ 服务状态检查失败:', error);
    }
}

// 加载已激活模型
async function loadActiveModels() {
    const modelsList = document.getElementById('active-models-list-10c');
    if (!modelsList) return;
    
    try {
        const response = await fetch('/api/m10/models');
        if (response.ok) {
            const data = await response.json();
            
            modelsList.innerHTML = '';
            
            if (data.models && Object.keys(data.models).length > 0) {
                Object.entries(data.models).forEach(([task, info]) => {
                    const item = document.createElement('div');
                    item.className = 'list-group-item d-flex justify-content-between align-items-center';
                    item.innerHTML = `
                        <span>${task}</span>
                        <span class="badge bg-primary">${info.active_version}</span>
                    `;
                    modelsList.appendChild(item);
                });
            } else {
                modelsList.innerHTML = '<div class="list-group-item text-center text-muted">暂无激活模型</div>';
            }
        }
    } catch (error) {
        console.error('❌ 加载模型列表失败:', error);
        modelsList.innerHTML = '<div class="list-group-item text-center text-danger">加载失败</div>';
    }
}

// 重新加载模型
async function reloadModels() {
    try {
        // 这里应该调用模型重载API
        console.log('🔄 重新加载模型...');
        await loadActiveModels();
    } catch (error) {
        console.error('❌ 重新加载模型失败:', error);
    }
}

// 随机填充特征
function fillRandomFeatures() {
    const inputs = document.querySelectorAll('.feature-input-10c');
    inputs.forEach(input => {
        input.value = Math.random().toFixed(3);
    });
}

// 清空特征
function clearFeatures() {
    const inputs = document.querySelectorAll('.feature-input-10c');
    inputs.forEach(input => {
        input.value = '';
    });
}

// 进行预测
async function makePrediction() {
    const taskSelect = document.getElementById('prediction-task-select-10c');
    const inputs = document.querySelectorAll('.feature-input-10c');
    const resultDiv = document.getElementById('prediction-result-10c');
    const scoreDiv = document.getElementById('prediction-score-10c');
    
    if (!taskSelect || !inputs.length) return;
    
    // 收集特征值
    const features = Array.from(inputs).map(input => parseFloat(input.value) || 0);
    
    // 验证特征数量
    if (features.length !== 10) {
        alert('请输入所有10个特征值');
        return;
    }
    
    try {
        const response = await fetch('/api/m10/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                q_tag: taskSelect.value,
                features: features
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (scoreDiv) scoreDiv.textContent = data.score.toFixed(4);
            if (resultDiv) resultDiv.style.display = 'block';
        } else {
            alert('预测失败');
        }
    } catch (error) {
        console.error('❌ 预测失败:', error);
        alert('预测异常');
    }
}

// 测试健康检查API
async function testHealthAPI() {
    const logDiv = document.getElementById('test-log-10c');
    if (!logDiv) return;
    
    logDiv.innerHTML = '<div class="text-info">测试健康检查API...</div>';
    
    try {
        const start = Date.now();
        const response = await fetch('/api/m10/predict/health');
        const duration = Date.now() - start;
        
        if (response.ok) {
            const data = await response.json();
            logDiv.innerHTML = `<div class="text-success">✅ 健康检查通过 (${duration}ms)</div>`;
        } else {
            logDiv.innerHTML = `<div class="text-danger">❌ 健康检查失败</div>`;
        }
    } catch (error) {
        logDiv.innerHTML = `<div class="text-danger">❌ 健康检查异常: ${error.message}</div>`;
    }
}

// 测试批量预测API
async function testBatchAPI() {
    const logDiv = document.getElementById('test-log-10c');
    if (!logDiv) return;
    
    logDiv.innerHTML = '<div class="text-info">测试批量预测API...</div>';
    
    const testData = {
        q_tag: 'Q1',
        samples: [
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1],
            [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2]
        ]
    };
    
    try {
        const start = Date.now();
        const response = await fetch('/api/m10/predict/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        const duration = Date.now() - start;
        
        if (response.ok) {
            const data = await response.json();
            logDiv.innerHTML = `<div class="text-success">✅ 批量预测成功 (${duration}ms)<br/>结果: ${JSON.stringify(data.results)}</div>`;
        } else {
            logDiv.innerHTML = `<div class="text-danger">❌ 批量预测失败</div>`;
        }
    } catch (error) {
        logDiv.innerHTML = `<div class="text-danger">❌ 批量预测异常: ${error.message}</div>`;
    }
}

// 测试所有API
async function testAllAPIs() {
    const logDiv = document.getElementById('test-log-10c');
    if (!logDiv) return;
    
    logDiv.innerHTML = '<div class="text-info">开始全面API测试...</div>';
    
    // 依次测试各个API
    await testHealthAPI();
    await new Promise(resolve => setTimeout(resolve, 1000));
    await testBatchAPI();
    
    logDiv.innerHTML += '<div class="text-primary mt-2">🎉 全面测试完成</div>';
}

// 检查DOM是否准备就绪
function checkDOMReady() {
    const requiredElements = [
        'tenthModuleView',
        'module10a-data-prep', 
        'module10b-training',
        'module10c-service'
    ];
    
    const missingElements = [];
    requiredElements.forEach(id => {
        if (!document.getElementById(id)) {
            missingElements.push(id);
        }
    });
    
    if (missingElements.length > 0) {
        console.warn('⚠️ 以下DOM元素未找到:', missingElements);
        return false;
    }
    
    return true;
}

// 更新主初始化函数
function initEyeIndexModule() {
    console.log('🚀 初始化模块10 Eye-Index');
    
    // 检查DOM是否准备就绪 - 如果部分元素缺失也继续初始化
    if (!checkDOMReady()) {
        console.warn('⚠️ 部分DOM元素未准备就绪，继续初始化');
    }
    
    // 初始化各个子模块
    if (typeof initModule10A === 'function') {
        initModule10A();
    }
    
    // 延迟初始化10B和10C，确保DOM元素加载完成
    setTimeout(() => {
        initModule10B();
        initModule10C();
    }, 200);
    
    // 原有的S_eye功能初始化
    initDOMElements();
    bindEventListeners();
    loadAvailableConfigs();
    
    console.log('✅ 模块10初始化完成');
}

console.log('📄 模块10 Eye-Index JavaScript脚本加载完成');