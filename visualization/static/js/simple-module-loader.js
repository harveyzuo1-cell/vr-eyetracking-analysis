/**
 * 简单模块加载器 - 支持全部七个模块的动态加载
 * 模块化拆分完成，支持所有模块：可视化、数据导入、RQA分析、事件分析、RQA流程、综合特征提取和数据整理模块
 */

// 模块配置
const moduleConfigs = {
    visualization: {
        containerId: 'visualizationModuleContainer',
        filename: 'module1_visualization.html',
        displayName: '数据可视化模块',
        initFunction: 'initVisualization'
    },
    dataImport: {
        containerId: 'dataImportModuleContainer',
        filename: 'module2_data_import.html',
        displayName: '数据导入模块',
        initFunction: 'initDataImport'
    },
    rqaAnalysis: {
        containerId: 'rqaAnalysisModuleContainer',
        filename: 'module3_rqa_analysis.html',
        displayName: 'RQA分析模块',
        initFunction: 'initRQAAnalysis'
    },
    eventAnalysis: {
        containerId: 'eventAnalysisModuleContainer',
        filename: 'module4_event_analysis.html',
        displayName: '事件分析模块',
        initFunction: 'initEventAnalysis'
    },
    rqaPipeline: {
        containerId: 'rqaPipelineModuleContainer',
        filename: 'module5_rqa_pipeline.html',
        displayName: 'RQA流程模块',
        initFunction: 'initRQAPipeline'
    },
    comprehensiveFeature: {
        containerId: 'comprehensiveFeatureModuleContainer',
        filename: 'module6_comprehensive_feature.html',
        displayName: '综合特征提取模块',
        initFunction: 'initComprehensiveFeature'
    },
    dataOrganization: {
        containerId: 'dataOrganizationModuleContainer',
        filename: 'module7_data_organization.html',
        displayName: '数据整理模块',
        initFunction: 'initDataOrganization'
    }
};

// 通用模块加载函数
async function loadModule(moduleId) {
    const config = moduleConfigs[moduleId];
    if (!config) {
        console.error(`❌ 未知的模块ID: ${moduleId}`);
        return;
    }

    const container = document.getElementById(config.containerId);
    if (!container) {
        console.error(`❌ 找不到模块容器: ${config.containerId}`);
        return;
    }

    try {
        // 显示加载状态
        container.innerHTML = `
            <div style="text-align: center; padding: 60px; color: #6c757d;">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <h5>正在加载${config.displayName}...</h5>
                <p class="text-muted">从独立文件 /static/modules/${config.filename} 加载</p>
            </div>
        `;

        // 加载模块文件
        const response = await fetch(`/static/modules/${config.filename}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const moduleHtml = await response.text();
        
        // 延迟一点时间，让用户看到加载效果
        setTimeout(() => {
            container.innerHTML = moduleHtml;
            console.log(`✅ ${config.displayName}加载完成`);
            
            // 触发模块加载完成事件，让其他脚本知道可以初始化了
            const event = new CustomEvent('moduleLoaded', {
                detail: { moduleId: moduleId }
            });
            document.dispatchEvent(event);
            
            // 调用模块初始化函数（如果存在）
            if (typeof window[config.initFunction] === 'function') {
                window[config.initFunction]();
            }
        }, 800);

    } catch (error) {
        console.error(`❌ ${config.displayName}加载失败:`, error);
        container.innerHTML = `
            <div style="text-align: center; padding: 60px; color: #dc3545;">
                <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                <h5>模块加载失败</h5>
                <p class="text-muted">${error.message}</p>
                <button class="btn btn-outline-primary" onclick="loadModule('${moduleId}')">
                    <i class="fas fa-redo"></i> 重试
                </button>
            </div>
        `;
    }
}

// 向后兼容的函数
function loadVisualizationModule() {
    return loadModule('visualization');
}

function loadDataImportModule() {
    return loadModule('dataImport');
}

function loadRQAAnalysisModule() {
    return loadModule('rqaAnalysis');
}

function loadEventAnalysisModule() {
    return loadModule('eventAnalysis');
}

function loadRQAPipelineModule() {
    return loadModule('rqaPipeline');
}

function loadComprehensiveFeatureModule() {
    return loadModule('comprehensiveFeature');
}

function loadDataOrganizationModule() {
    return loadModule('dataOrganization');
}

// 页面加载完成后自动加载已拆分的模块
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 简单模块加载器初始化（支持全部七个模块）');
    
    // 延迟加载，让页面先渲染完成
    setTimeout(() => {
        // 加载第一个模块（数据可视化）
        if (document.getElementById('visualizationModuleContainer')) {
            loadModule('visualization');
        }
        
        // 加载第二个模块（数据导入）
        if (document.getElementById('dataImportModuleContainer')) {
            loadModule('dataImport');
        }
        
        // 加载第三个模块（RQA分析）
        if (document.getElementById('rqaAnalysisModuleContainer')) {
            loadModule('rqaAnalysis');
        }
        
        // 加载第四个模块（事件分析）
        if (document.getElementById('eventAnalysisModuleContainer')) {
            loadModule('eventAnalysis');
        }
        
        // 加载第五个模块（RQA流程）
        if (document.getElementById('rqaPipelineModuleContainer')) {
            loadModule('rqaPipeline');
        }
        
        // 加载第六个模块（综合特征提取）
        if (document.getElementById('comprehensiveFeatureModuleContainer')) {
            loadModule('comprehensiveFeature');
        }
        
        // 加载第七个模块（数据整理）
        if (document.getElementById('dataOrganizationModuleContainer')) {
            loadModule('dataOrganization');
        }
    }, 500);
});