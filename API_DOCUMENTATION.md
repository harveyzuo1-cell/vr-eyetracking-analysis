# API 技术文档 (API Documentation)

## 📋 概述

本文档详细描述了眼动数据分析系统的所有REST API接口，包括数据管理、RQA分析、可视化等功能的API调用方法。

**基础URL**: `http://localhost:8080`

---

## 🔐 认证

当前版本无需认证，所有API均为公开访问。

---

## 📊 数据管理API

### 1. 获取所有组别数据

```http
GET /api/groups
```

**描述**: 获取系统中所有数据组的概览信息

**响应**:
```json
{
  "control": {
    "total_files": 100,
    "total_size": "2.5MB",
    "groups": ["control_group_1", "control_group_2", ...]
  },
  "mci": {
    "total_files": 100,
    "total_size": "2.3MB", 
    "groups": ["mci_group_1", "mci_group_2", ...]
  },
  "ad": {
    "total_files": 105,
    "total_size": "2.7MB",
    "groups": ["ad_group_3", "ad_group_4", ...]
  }
}
```

### 2. 获取指定组别数据

```http
GET /api/group/{group_type}/data
```

**路径参数**:
- `group_type` (string): 组别类型 (`control`, `mci`, `ad`)

**响应**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "c1q1",
      "display_name": "control - c1q1",
      "file_path": "n1q1_preprocessed_calibrated.csv",
      "question": "Q1",
      "size": "45KB",
      "last_modified": "2025-01-28T10:30:00Z"
    },
    ...
  ],
  "total": 100
}
```

### 3. 获取单个数据文件详情

```http
GET /api/data/{data_id}/info
```

**路径参数**:
- `data_id` (string): 数据ID (如 `c1q1`, `m5q3`)

**响应**:
```json
{
  "id": "c1q1",
  "group": "control",
  "participant": 1,
  "question": "Q1",
  "file_info": {
    "path": "data/control_calibrated/control_group_1/n1q1_preprocessed_calibrated.csv",
    "size": "45KB",
    "rows": 2890,
    "columns": ["timestamp", "x", "y", "milliseconds", "ROI", "SequenceID"]
  },
  "statistics": {
    "duration_ms": 46320,
    "total_fixations": 142,
    "total_saccades": 141,
    "roi_coverage": {
      "INST": 35.2,
      "KW": 28.7,
      "BG": 36.1
    }
  }
}
```

---

## 🔬 RQA分析API

### 1. 启动RQA批量渲染

```http
POST /api/rqa-batch-render
```

**请求体**:
```json
{
  "analysis_mode": "2d_xy",           // 1d_x | 1d_amplitude | 2d_xy
  "distance_metric": "euclidean",     // 1d_abs | euclidean
  "embedding_dimension": 2,           // 通常 2-10
  "time_delay": 1,                    // 通常 1
  "recurrence_threshold": 0.05,       // 0.01-0.1
  "min_line_length": 2,               // 2-5
  "color_theme": "green_gradient"     // green_gradient | gray_scale
}
```

**响应**:
```json
{
  "status": "success",
  "message": "RQA批量渲染已启动",
  "param_signature": "mode_2d_xy_dist_euclidean_m2_tau1_eps0.05_lmin2_green",
  "total_files": 305,
  "expected_images": 915
}
```

### 2. 获取RQA渲染状态

```http
GET /api/rqa-render-status
```

**查询参数**:
- `param_signature` (可选): 特定参数组合的状态

**响应**:
```json
{
  "status": "in_progress",
  "total_files": 305,
  "processed_files": 156,
  "progress_percentage": 51.1,
  "total_images": 468,
  "expected_images": 915,
  "current_file": "n52q3_preprocessed_calibrated",
  "estimated_remaining_time": "3分25秒",
  "param_signatures": [
    {
      "signature": "mode_2d_xy_dist_euclidean_m2_tau1_eps0.05_lmin2_green",
      "files_processed": 156,
      "images_generated": 468
    }
  ]
}
```

### 3. 获取RQA渲染结果

```http
GET /api/rqa-rendered-results
```

**查询参数**:
- `param_signature` (可选): 过滤特定参数组合
- `group` (可选): 过滤组别 (`control`, `mci`, `ad`)
- `question` (可选): 过滤问题 (`Q1`, `Q2`, `Q3`, `Q4`, `Q5`)

**响应**:
```json
{
  "status": "success",
  "param_signature": "mode_2d_xy_dist_euclidean_m2_tau1_eps0.05_lmin2_green",
  "results": {
    "control": {
      "Q1": [
        {
          "data_id": "c1q1",
          "images": {
            "trajectory": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
            "amplitude": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
            "recurrence_plot": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
          },
          "rqa_metrics": {
            "RR": 0.045,
            "DET": 0.823, 
            "ENT": 2.341
          }
        },
        ...
      ],
      "Q2": [...],
      ...
    },
    "mci": {...},
    "ad": {...}
  },
  "total_images": 915
}
```

### 4. 获取RQA参数预设

```http
GET /api/rqa-parameters/presets
```

**响应**:
```json
{
  "presets": [
    {
      "name": "标准2D分析",
      "description": "适用于2D眼动轨迹的标准RQA分析",
      "parameters": {
        "analysis_mode": "2d_xy",
        "distance_metric": "euclidean",
        "embedding_dimension": 2,
        "time_delay": 1,
        "recurrence_threshold": 0.05,
        "min_line_length": 2,
        "color_theme": "green_gradient"
      }
    },
    {
      "name": "X坐标1D分析",
      "description": "专注于X坐标变化的1D分析",
      "parameters": {
        "analysis_mode": "1d_x",
        "distance_metric": "1d_abs",
        "embedding_dimension": 3,
        "time_delay": 1,
        "recurrence_threshold": 0.03,
        "min_line_length": 2,
        "color_theme": "gray_scale"
      }
    }
  ]
}
```

---

## 🔄 RQA分析流程API (第五模块)

### 概述

第五模块提供了一个完整的参数化RQA分析流程，从数据处理到统计分析再到可视化。该模块支持多参数组合的并行分析和结果管理。

### 参数化管理

所有API端点都支持参数化配置，参数会生成唯一的签名用于目录管理：

**标准参数格式**:
```json
{
  "m": 2,           // 嵌入维度 (1-10)
  "tau": 1,         // 时间延迟 (1-10) 
  "eps": 0.05,      // 递归阈值 (0.01-0.2)
  "lmin": 2         // 最小线长 (2-10)
}
```

**参数签名示例**: `m2_tau1_eps0.05_lmin2`

### 1. RQA计算 (步骤1)

```http
POST /api/rqa-pipeline/calculate
```

**描述**: 对所有数据文件执行RQA分析计算

**请求体**:
```json
{
  "parameters": {
    "m": 2,
    "tau": 1,
    "eps": 0.05,
    "lmin": 2
  }
}
```

**响应**:
```json
{
  "status": "success",
  "message": "RQA计算完成",
  "data": {
    "param_signature": "m2_tau1_eps0.05_lmin2",
    "total_files": 305,
    "control_files": 100,
    "mci_files": 105,
    "ad_files": 100,
    "output_directory": "data/rqa_pipeline_results/m2_tau1_eps0.05_lmin2/step1_rqa_calculation"
  }
}
```

### 2. 数据合并 (步骤2)

```http
POST /api/rqa-pipeline/merge
```

**描述**: 合并三组(Control/MCI/AD)的RQA计算结果

**请求体**:
```json
{
  "parameters": {
    "m": 2,
    "tau": 1,
    "eps": 0.05,
    "lmin": 2
  }
}
```

**响应**:
```json
{
  "status": "success",
  "message": "数据合并完成",
  "data": {
    "param_signature": "m2_tau1_eps0.05_lmin2",
    "output_file": "data/rqa_pipeline_results/m2_tau1_eps0.05_lmin2/step2_data_merging/All_Subjects_RQA_EyeMetrics.csv",
    "total_records": 305,
    "groups": {
      "Control": 100,
      "MCI": 105,
      "AD": 100
    }
  }
}
```

### 3. 特征补充 (步骤3)

```http
POST /api/rqa-pipeline/enrich
```

**描述**: 补充眼动事件特征和ROI统计信息

**请求体**:
```json
{
  "parameters": {
    "m": 2,
    "tau": 1,
    "eps": 0.05,
    "lmin": 2
  }
}
```

**响应**:
```json
{
  "status": "success",
  "message": "特征补充完成",
  "data": {
    "param_signature": "m2_tau1_eps0.05_lmin2",
    "output_file": "data/rqa_pipeline_results/m2_tau1_eps0.05_lmin2/step3_feature_enrichment/All_Subjects_RQA_EyeMetrics_Filled.csv",
    "total_records": 305,
    "added_features": [
      "FixDurSum", "FixCount", "SaccAmpMean", 
      "SaccMaxVelPeak", "SaccCount", "RegCountSum", "ROIFixDurSum"
    ]
  }
}
```

### 4. 统计分析 (步骤4)

```http
POST /api/rqa-pipeline/analyze
```

**描述**: 执行多层次统计分析

**请求体**:
```json
{
  "parameters": {
    "m": 2,
    "tau": 1,
    "eps": 0.05,
    "lmin": 2
  }
}
```

**响应**:
```json
{
  "status": "success",
  "message": "统计分析完成",
  "data": {
    "param_signature": "m2_tau1_eps0.05_lmin2",
    "group_stats_file": "data/rqa_pipeline_results/m2_tau1_eps0.05_lmin2/step4_statistical_analysis/group_stats_output.csv",
    "multi_level_stats_file": "data/rqa_pipeline_results/m2_tau1_eps0.05_lmin2/step4_statistical_analysis/multi_level_stats_output.csv",
    "group_summary": [
      {
        "Group": "Control",
        "Count": 100,
        "RR_mean": 0.0510,
        "RR_std": 0.0234,
        "DET_mean": 0.8456,
        "DET_std": 0.1123,
        "ENT_mean": 2.1567,
        "ENT_std": 0.4321
      },
      ...
    ]
  }
}
```

### 5. 可视化 (步骤5)

```http
POST /api/rqa-pipeline/visualize
```

**描述**: 生成统计图表和分析报告

**请求体**:
```json
{
  "parameters": {
    "m": 2,
    "tau": 1,
    "eps": 0.05,
    "lmin": 2
  }
}
```

**响应**:
```json
{
  "status": "success",
  "message": "可视化生成完成",
  "data": {
    "param_signature": "m2_tau1_eps0.05_lmin2",
    "charts": [
      {
        "title": "RR-2D-xy 组别对比",
        "metric": "RR-2D-xy",
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
      },
      {
        "title": "DET-2D-xy 组别对比", 
        "metric": "DET-2D-xy",
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
      },
      {
        "title": "ENT-2D-xy 组别对比",
        "metric": "ENT-2D-xy", 
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
      },
      {
        "title": "Average RR-2D-xy across tasks by Group",
        "metric": "RR-2D-xy",
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        "description": "跨任务的平均RR-2D-xy变化趋势 (按认知组分组)"
      }
    ],
    "group_stats": [
      {
        "Group": "Control",
        "RR_mean": 0.0510,
        "RR_std": 0.0234,
        "DET_mean": 0.8456,
        "DET_std": 0.1123,
        "ENT_mean": 2.1567,
        "ENT_std": 0.4321
      },
      ...
    ],
    "total_charts": 4,
    "output_directory": "data/rqa_pipeline_results/m2_tau1_eps0.05_lmin2/step5_visualization",
    "generated_files": [
      "bar_chart_RR_2D_xy.png",
      "bar_chart_DET_2D_xy.png", 
      "bar_chart_ENT_2D_xy.png",
      "trend_chart_RR_2D_xy.png",
      "visualization_charts.json",
      "group_statistics.json"
    ]
  }
}
```

### 6. 流程状态查询

```http
GET /api/rqa-pipeline/status
```

**查询参数** (可选):
- `m` (int): 嵌入维度
- `tau` (int): 时间延迟  
- `eps` (float): 递归阈值
- `lmin` (int): 最小线长

**响应**:
```json
{
  "status": "success",
  "data": {
    "step_status": {
      "step1": true,
      "step2": true,
      "step3": true,
      "step4": false,
      "step5": false
    },
    "completed_steps": 3,
    "total_steps": 5,
    "progress_percentage": 60.0,
    "param_signature": "m2_tau1_eps0.05_lmin2"
  }
}
```

### 7. 参数历史记录

```http
GET /api/rqa-pipeline/param-history
```

**响应**:
```json
{
  "status": "success",
  "data": [
    {
      "signature": "m2_tau1_eps0.05_lmin2",
      "params": {
        "m": 2,
        "tau": 1,
        "eps": 0.05,
        "lmin": 2
      },
      "completed_steps": 5,
      "progress": 100.0,
      "last_updated": "2025-01-28T10:30:45Z"
    },
    {
      "signature": "m3_tau2_eps0.08_lmin3",
      "params": {
        "m": 3,
        "tau": 2, 
        "eps": 0.08,
        "lmin": 3
      },
      "completed_steps": 3,
      "progress": 60.0,
      "last_updated": "2025-01-28T09:15:32Z"
    }
  ],
  "total_records": 2
}
```

### 8. 获取特定参数结果

```http
GET /api/rqa-pipeline/results/{signature}
```

**路径参数**:
- `signature` (string): 参数签名 (如: `m2_tau1_eps0.05_lmin2`)

**响应**:
```json
{
  "status": "success",
  "data": {
    "signature": "m2_tau1_eps0.05_lmin2",
    "metadata": {
      "signature": "m2_tau1_eps0.05_lmin2",
      "parameters": {
        "m": 2,
        "tau": 1,
        "eps": 0.05,
        "lmin": 2
      },
      "last_updated": "2025-01-28T10:30:45Z",
      "step_1_completed": true,
      "step_2_completed": true,
      "step_3_completed": true,
      "step_4_completed": true,
      "step_5_completed": true
    },
    "completed_steps": [
      "step1_rqa_calculation",
      "step2_data_merging",
      "step3_feature_enrichment", 
      "step4_statistical_analysis",
      "step5_visualization"
    ],
    "completed_count": 5,
    "total_steps": 5,
    "results": {
      "charts": [...],
      "group_stats": [...]
    }
  }
}
```

### 9. 删除参数结果

```http
DELETE /api/rqa-pipeline/delete/{signature}
```

**路径参数**:
- `signature` (string): 参数签名

**响应**:
```json
{
  "status": "success",
  "message": "已删除参数组合 m2_tau1_eps0.05_lmin2 的所有结果"
}
```

### 使用示例

#### Python示例：完整流程

```python
import requests
import time

BASE_URL = "http://localhost:8080"
params = {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}

# 执行完整的5步骤流程
steps = ['calculate', 'merge', 'enrich', 'analyze', 'visualize']

for i, step in enumerate(steps, 1):
    print(f"执行步骤{i}: {step}")
    
    response = requests.post(
        f"{BASE_URL}/api/rqa-pipeline/{step}",
        json={"parameters": params}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 步骤{i}完成: {result['message']}")
        
        if step == 'visualize':
            # 获取可视化结果
            charts = result['data']['charts']
            print(f"生成了 {len(charts)} 个图表")
    else:
        print(f"❌ 步骤{i}失败: {response.status_code}")
        break

# 查看最终结果
signature = "m2_tau1_eps0.05_lmin2"
response = requests.get(f"{BASE_URL}/api/rqa-pipeline/results/{signature}")
if response.status_code == 200:
    results = response.json()
    print(f"最终结果: {results['data']['completed_count']}/5 步骤完成")
```

#### JavaScript示例：前端集成

```javascript
class RQAPipeline {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
        this.currentParams = null;
    }
    
    async runStep(stepName, parameters) {
        const response = await fetch(`${this.baseUrl}/api/rqa-pipeline/${stepName}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({parameters})
        });
        
        if (!response.ok) {
            throw new Error(`步骤 ${stepName} 失败: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async runFullPipeline(parameters) {
        this.currentParams = parameters;
        const steps = ['calculate', 'merge', 'enrich', 'analyze', 'visualize'];
        const results = [];
        
        for (const step of steps) {
            try {
                console.log(`执行步骤: ${step}`);
                const result = await this.runStep(step, parameters);
                results.push({step, result});
                console.log(`✅ ${step} 完成`);
            } catch (error) {
                console.error(`❌ ${step} 失败:`, error);
                throw error;
            }
        }
        
        return results;
    }
    
    async getResults(signature) {
        const response = await fetch(`${this.baseUrl}/api/rqa-pipeline/results/${signature}`);
        return await response.json();
    }
    
    async getHistory() {
        const response = await fetch(`${this.baseUrl}/api/rqa-pipeline/param-history`);
        return await response.json();
    }
}

// 使用示例
const pipeline = new RQAPipeline();

pipeline.runFullPipeline({m: 2, tau: 1, eps: 0.05, lmin: 2})
    .then(results => {
        console.log('流程完成:', results);
        return pipeline.getResults('m2_tau1_eps0.05_lmin2');
    })
    .then(finalResults => {
        console.log('最终结果:', finalResults);
    })
    .catch(error => {
        console.error('流程失败:', error);
    });
```

---

## 🎨 可视化API

### 1. 生成单个数据可视化

```http
POST /api/visualize
```

**请求体**:
```json
{
  "data_id": "c1q1",
  "visualization_type": "trajectory",  // trajectory | heatmap | amplitude
  "parameters": {
    "show_fixations": true,
    "fixation_size": 8,
    "show_saccades": true,
    "saccade_width": 2,
    "roi_highlight": true,
    "background_image": "Q1.jpg"
  }
}
```

**响应**:
```json
{
  "status": "success",
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "statistics": {
    "total_fixations": 142,
    "total_saccades": 141,
    "duration_ms": 46320,
    "roi_statistics": {
      "INST": {"count": 45, "duration": 16230},
      "KW": {"count": 38, "duration": 13290},
      "BG": {"count": 59, "duration": 16800}
    }
  }
}
```

### 2. 生成热力图

```http
POST /api/generate-heatmap
```

**请求体**:
```json
{
  "data_ids": ["c1q1", "c1q2", "c1q3"],
  "heatmap_type": "gaussian",     // gaussian | kernel | grid
  "parameters": {
    "sigma": 30,
    "alpha": 0.7,
    "colormap": "hot",
    "resolution": [1920, 1080],
    "background_image": "Q1.jpg"
  }
}
```

**响应**:
```json
{
  "status": "success",
  "heatmap_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "combined_statistics": {
    "total_participants": 3,
    "total_fixations": 426,
    "hotspots": [
      {"x": 960, "y": 540, "intensity": 0.85},
      {"x": 1200, "y": 300, "intensity": 0.72}
    ]
  }
}
```

---

## 📋 事件分析API

### 1. 获取眼动事件数据

```http
GET /api/event-analysis/data
```

**查询参数**:
- `page` (int): 页码，默认1
- `per_page` (int): 每页数量，默认50
- `group` (string): 过滤组别
- `event_type` (string): 事件类型 (`fixation`, `saccade`)
- `roi` (string): ROI过滤

**响应**:
```json
{
  "status": "success",
  "data": [
    {
      "ADQ_ID": "c1q1",
      "EventID": 1,
      "EventType": "fixation",
      "StartTime": 16,
      "EndTime": 248,
      "Duration": 232,
      "StartX": 960.5,
      "StartY": 540.2,
      "EndX": 962.1,
      "EndY": 541.8,
      "ROI": "INST",
      "Amplitude": 2.3,
      "MeanVelocity": 12.5,
      "MaxVelocity": 28.7
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 25830,
    "pages": 517
  }
}
```

### 2. 获取ROI统计摘要

```http
GET /api/event-analysis/roi-summary
```

**查询参数**:
- `group` (string): 过滤组别
- `question` (string): 过滤问题

**响应**:
```json
{
  "status": "success",
  "summary": [
    {
      "ADQ_ID": "c1q1",
      "Group": "control",
      "Question": "Q1",
      "INST_FixTime": 16230,
      "INST_EnterCount": 8,
      "INST_RegressionCount": 2,
      "KW_FixTime": 13290,
      "KW_EnterCount": 6,
      "KW_RegressionCount": 1,
      "BG_FixTime": 16800,
      "BG_EnterCount": 12,
      "BG_RegressionCount": 3,
      "TotalFixTime": 46320,
      "TotalEnterCount": 26,
      "TotalRegressionCount": 6
    },
    ...
  ],
  "statistics": {
    "total_participants": 300,
    "average_fix_time": 42156,
    "roi_distribution": {
      "INST": 34.2,
      "KW": 29.8,
      "BG": 36.0
    }
  }
}
```

### 3. 重新生成事件分析

```http
POST /api/event-analysis/regenerate
```

**请求体**:
```json
{
  "groups": ["control", "mci"],       // 可选，默认所有组
  "force_regenerate": false,          // 是否强制重新生成
  "parameters": {
    "velocity_threshold": 30,         // 速度阈值
    "min_fixation_duration": 100,    // 最小注视时长(ms)
    "dispersion_threshold": 25        // 离散度阈值
  }
}
```

**响应**:
```json
{
  "status": "started",
  "message": "事件分析重新生成已启动",
  "task_id": "event_analysis_20250128_103045",
  "expected_files": 200,
  "estimated_duration": "15分钟"
}
```

---

## ⚙️ 系统API

### 1. 获取系统状态

```http
GET /api/system/status
```

**响应**:
```json
{
  "status": "healthy",
  "uptime": "2h 34m 15s",
  "version": "1.0.0",
  "services": {
    "web_server": "running",
    "rqa_renderer": "idle",
    "event_analyzer": "idle"
  },
  "system_info": {
    "python_version": "3.9.7",
    "memory_usage": "1.2GB / 8GB",
    "disk_usage": "450MB / 100GB",
    "active_tasks": 0
  }
}
```

### 2. 获取配置信息

```http
GET /api/system/config
```

**响应**:
```json
{
  "data_directories": {
    "control_calibrated": "data/control_calibrated/",
    "mci_calibrated": "data/mci_calibrated/",
    "ad_calibrated": "data/ad_calibrated/",
    "rqa_results": "data/rqa_results/",
    "event_results": "data/event_analysis_results/"
  },
  "default_parameters": {
    "rqa": {
      "embedding_dimension": 2,
      "time_delay": 1,
      "recurrence_threshold": 0.05,
      "min_line_length": 2
    },
    "visualization": {
      "image_dpi": 150,
      "figure_size": [8, 8],
      "font_size": 16
    }
  },
  "limits": {
    "max_file_size": "10MB",
    "max_concurrent_renders": 5,
    "api_rate_limit": "100/minute"
  }
}
```

---

## 📤 数据导出API

### 1. 导出RQA结果

```http
POST /api/export/rqa-results
```

**请求体**:
```json
{
  "param_signature": "mode_2d_xy_dist_euclidean_m2_tau1_eps0.05_lmin2_green",
  "format": "csv",                    // csv | json | excel
  "include_images": false,            // 是否包含图片
  "groups": ["control", "mci"],       // 可选，默认所有组
  "questions": ["Q1", "Q2"]          // 可选，默认所有问题
}
```

**响应**:
```json
{
  "status": "success",
  "download_url": "/api/download/rqa_results_20250128_103045.csv",
  "file_size": "2.3MB",
  "expires_at": "2025-01-29T10:30:45Z"
}
```

### 2. 导出事件分析结果

```http
POST /api/export/event-analysis
```

**请求体**:
```json
{
  "export_type": "events",           // events | roi_summary | both
  "format": "excel",                 // csv | json | excel
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-01-28"
  },
  "filters": {
    "groups": ["control"],
    "event_types": ["fixation"],
    "min_duration": 100
  }
}
```

**响应**:
```json
{
  "status": "success", 
  "download_url": "/api/download/events_20250128_103045.xlsx",
  "file_size": "5.7MB",
  "record_count": 12580,
  "expires_at": "2025-01-29T10:30:45Z"
}
```

---

## 🔄 实时更新API (WebSocket)

### 连接WebSocket

```javascript
// WebSocket连接
const ws = new WebSocket('ws://localhost:8080/ws');

// 监听RQA渲染进度
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'rqa_progress',
  param_signature: 'mode_2d_xy_dist_euclidean_m2_tau1_eps0.05_lmin2_green'
}));

// 接收进度更新
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.progress_percentage);
};
```

**进度消息格式**:
```json
{
  "type": "rqa_progress",
  "param_signature": "mode_2d_xy_dist_euclidean_m2_tau1_eps0.05_lmin2_green",
  "progress_percentage": 65.2,
  "current_file": "n89q4_preprocessed_calibrated",
  "processed_files": 199,
  "total_files": 305,
  "estimated_remaining": "2分15秒"
}
```

---

## ❌ 错误处理

### 标准错误响应格式

```json
{
  "status": "error",
  "error_code": "INVALID_PARAMETER",
  "message": "参数 'embedding_dimension' 必须在2-10范围内",
  "details": {
    "parameter": "embedding_dimension",
    "provided_value": 15,
    "valid_range": [2, 10]
  },
  "timestamp": "2025-01-28T10:30:45Z"
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 说明 |
|---------|-----------|------|
| `INVALID_PARAMETER` | 400 | 请求参数无效 |
| `DATA_NOT_FOUND` | 404 | 请求的数据不存在 |
| `PROCESSING_ERROR` | 500 | 数据处理过程中出错 |
| `RESOURCE_BUSY` | 503 | 系统资源繁忙，请稍后重试 |
| `INSUFFICIENT_DATA` | 422 | 数据不足，无法完成分析 |
| `FILE_FORMAT_ERROR` | 422 | 文件格式不支持 |

---

## 🔧 开发工具

### API测试示例 (Python)

```python
import requests

# 基础URL
BASE_URL = "http://localhost:8080"

# 启动RQA分析
response = requests.post(f"{BASE_URL}/api/rqa-batch-render", json={
    "analysis_mode": "2d_xy",
    "distance_metric": "euclidean",
    "embedding_dimension": 2,
    "time_delay": 1,
    "recurrence_threshold": 0.05,
    "min_line_length": 2,
    "color_theme": "green_gradient"
})

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# 检查进度
import time
while True:
    status = requests.get(f"{BASE_URL}/api/rqa-render-status").json()
    print(f"Progress: {status['progress_percentage']:.1f}%")
    if status['status'] == 'completed':
        break
    time.sleep(10)
```

### cURL示例

```bash
# 获取所有组数据
curl -X GET "http://localhost:8080/api/groups"

# 启动RQA渲染
curl -X POST "http://localhost:8080/api/rqa-batch-render" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_mode": "2d_xy",
    "distance_metric": "euclidean", 
    "embedding_dimension": 2,
    "time_delay": 1,
    "recurrence_threshold": 0.05,
    "min_line_length": 2,
    "color_theme": "green_gradient"
  }'

# 获取渲染状态
curl -X GET "http://localhost:8080/api/rqa-render-status"
```

---

## 📈 性能考虑

### API限制
- **请求频率**: 每分钟最多100次请求
- **文件大小**: 单个文件最大10MB
- **并发渲染**: 最多5个并发RQA渲染任务
- **WebSocket连接**: 每个客户端最多10个连接

### 优化建议
- 使用`param_signature`参数过滤结果，避免获取不必要的数据
- 对于大批量操作，使用WebSocket获取实时进度
- 合理设置分页参数，避免一次请求过多数据
- 缓存不变的数据，如系统配置和参数预设

---

**最后更新**: 2025年1月28日  
**API版本**: v1.0.0  
**文档状态**: 活跃维护中 🚀 