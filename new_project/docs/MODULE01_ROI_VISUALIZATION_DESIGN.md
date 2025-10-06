# Module01 ROI可视化与统计功能设计文档
# Module01 ROI Visualization and Analytics Design

**文档版本**: v1.0
**创建日期**: 2025-10-02
**状态**: 设计阶段
**作者**: Claude

---

## 📋 目录

1. [需求概述](#1-需求概述)
2. [现状分析](#2-现状分析)
3. [ROI数据结构分析](#3-roi数据结构分析)
4. [技术方案设计](#4-技术方案设计)
5. [后端实现](#5-后端实现)
6. [前端实现](#6-前端实现)
7. [ROI进出统计算法](#7-roi进出统计算法)
8. [开发计划](#8-开发计划)
9. [测试验证](#9-测试验证)
10. [架构合规性](#10-架构合规性)

---

## 1. 需求概述

### 1.1 功能需求

**核心需求**：
当用户选择**V1旧数据**时，在眼动轨迹图中叠加显示对应任务的ROI（Region of Interest，感兴趣区域）图层，并计算眼动点进出ROI的次数。

**具体要求**：

1. **ROI图层显示**
   - ROI区域以半透明矩形显示在轨迹图上
   - 坐标范围：(0,0) ~ (1,1) 归一化坐标
   - 每个任务(Q1-Q5)有对应的ROI区域
   - 使用不同颜色区分不同任务的ROI

2. **数据版本适配**
   - **V1数据**：使用`config/roi_v1.json`配置
   - **V2数据**：不显示ROI（新版数据ROI布局不同）
   - **全部版本**：不显示ROI（混合数据）

3. **ROI进出统计**
   - 计算眼动轨迹进入ROI的次数
   - 计算眼动轨迹离开ROI的次数
   - 统计在ROI内部的数据点数量
   - 计算ROI内停留时间占比

4. **可视化效果**
   - ROI矩形：半透明填充（opacity: 0.2-0.3）
   - ROI边框：与填充同色，宽度2-3px
   - ROI标签：显示任务名称（如"Q1_时间定向区"）
   - 支持i18n多语言

### 1.2 使用场景

**场景1：单任务查看**
```
用户操作：数据版本=V1 → 研究组别=对照组 → 受试者=n21 → 任务=Q1
预期效果：眼动轨迹图叠加显示Q1的ROI区域
统计结果：显示该受试者在Q1 ROI的进出次数
```

**场景2：全部任务查看**
```
用户操作：数据版本=V1 → 研究组别=对照组 → 受试者=n21 → 任务=全部任务
预期效果：眼动轨迹图叠加显示Q1-Q5所有ROI区域
统计结果：显示该受试者在各个ROI的进出次数统计
```

**场景3：V2数据查看**
```
用户操作：数据版本=V2 → 研究组别=对照组 → 受试者=s001 → 任务=Q1
预期效果：不显示ROI（因为V2数据ROI布局不同）
```

---

## 2. 现状分析

### 2.1 当前Module01架构

**前端组件结构**：
```
Module01/
├── Module01.jsx                 # 主页面
├── components/Charts/
│   ├── GazeTrajectoryChart.jsx  # 眼动轨迹图（需要修改）
│   └── HeatmapChart.jsx         # 热力图
└── services/
    └── dataService.js           # API服务
```

**后端模块结构**：
```
src/web/modules/module01_data_visualization/
├── api.py                       # API路由
└── service.py                   # 业务逻辑（需要扩展）
```

### 2.2 现有数据流

```
用户选择 → Module01.jsx → dataService.js →
  Module01 API → service.py → MetadataReader →
    返回眼动数据 → GazeTrajectoryChart.jsx → 显示轨迹
```

### 2.3 需要新增的数据流

```
用户选择版本=V1 + 任务 →
  Module01 API (新增ROI端点) →
    读取config/roi_v1.json →
      返回对应任务的ROI配置 →
        GazeTrajectoryChart.jsx →
          叠加显示ROI图层 + 计算进出次数
```

---

## 3. ROI数据结构分析

### 3.1 ROI配置文件结构

**文件位置**：`config/roi_v1.json`, `config/roi_v2.json`

**数据结构**：
```json
{
  "version": "v1",
  "layout": "legacy",
  "description": "旧版ROI布局",
  "regions": [
    {
      "id": "q1_time_orientation",
      "name": "Q1_时间定向区",
      "task": "q1",
      "x": 0.1,          // ROI左上角X坐标（归一化）
      "y": 0.2,          // ROI左上角Y坐标（归一化）
      "width": 0.3,      // ROI宽度（归一化）
      "height": 0.2,     // ROI高度（归一化）
      "color": "#FF6B6B", // ROI颜色
      "description": "时间定向任务关键区域"
    },
    // ... Q2-Q5的ROI定义
  ]
}
```

### 3.2 ROI坐标系统

**归一化坐标系**：
- X轴范围：[0, 1] （左→右）
- Y轴范围：[0, 1] （上→下）
- 原点(0,0)：左上角
- 终点(1,1)：右下角

**ROI矩形定义**：
```
左上角：(x, y)
右上角：(x + width, y)
左下角：(x, y + height)
右下角：(x + width, y + height)
```

### 3.3 V1与V2的ROI差异

| 特征 | V1 (65受试者) | V2 (94受试者) |
|------|--------------|---------------|
| 数据时期 | 2025-01 | 2025-03 ~ 2025-04 |
| ROI布局 | legacy | new |
| Q1位置 | (0.1, 0.2) | (0.15, 0.25) |
| Q1大小 | 0.3×0.2 | 0.35×0.22 |
| 差异原因 | VR系统更新后布局微调 | |

**设计决策**：仅在V1数据时显示ROI，避免V2数据使用错误的ROI配置。

---

## 4. 技术方案设计

### 4.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│  用户选择: 版本=V1 + 组别 + 受试者 + 任务                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Frontend: Module01.jsx                                  │
│  - 检测版本是否为V1                                      │
│  - 如果是V1，调用ROI API获取配置                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Backend: GET /api/data/roi?version=v1&task=q1          │
│  - 读取config/roi_v1.json                               │
│  - 筛选对应任务的ROI区域                                 │
│  - 返回ROI配置JSON                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Frontend: GazeTrajectoryChart.jsx                       │
│  - 接收ROI配置props                                      │
│  - 在Plotly图表中添加ROI矩形shapes                       │
│  - 调用ROI统计算法计算进出次数                           │
│  - 显示统计结果                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 数据流设计

**1. ROI配置获取**：
```javascript
// 前端请求
GET /api/data/roi?version=v1&task=q1

// 后端响应
{
  "success": true,
  "data": {
    "version": "v1",
    "task": "q1",
    "regions": [
      {
        "id": "q1_time_orientation",
        "name": "Q1_时间定向区",
        "x": 0.1,
        "y": 0.2,
        "width": 0.3,
        "height": 0.2,
        "color": "#FF6B6B"
      }
    ]
  }
}
```

**2. 眼动数据 + ROI统计**：
```javascript
// 前端计算（客户端计算，减轻服务器负担）
{
  "gazeData": [...],  // 眼动轨迹数据
  "roiStats": {
    "q1_time_orientation": {
      "entry_count": 5,      // 进入次数
      "exit_count": 5,       // 离开次数
      "points_inside": 120,  // ROI内数据点数
      "total_points": 500,   // 总数据点数
      "inside_ratio": 0.24,  // ROI内停留比例
      "duration_inside": 2.5 // ROI内停留时间(秒)
    }
  }
}
```

### 4.3 组件设计

**新增/修改组件**：

1. **ROI Service (新增)**
   - 文件：`frontend/src/services/roiService.js`
   - 功能：获取ROI配置

2. **ROI Analyzer (新增)**
   - 文件：`frontend/src/utils/roiAnalyzer.js`
   - 功能：计算ROI进出统计

3. **GazeTrajectoryChart (修改)**
   - 添加ROI图层显示
   - 集成ROI统计计算
   - 显示统计结果

4. **Module01.jsx (修改)**
   - 根据版本加载ROI配置
   - 传递ROI数据到图表组件

---

## 5. 后端实现

### 5.1 新增ROI API端点

**文件**: `src/web/modules/module01_data_visualization/api.py`

```python
@m01_bp.route('/roi', methods=['GET'])
def get_roi_config():
    """
    获取ROI配置

    GET /api/data/roi?version=v1&task=q1

    Query Parameters:
        version: 数据版本 (v1/v2)
        task: 任务ID (q1/q2/q3/q4/q5/all)，all表示返回所有ROI

    Returns:
        {
            "success": true,
            "data": {
                "version": "v1",
                "task": "q1",
                "regions": [...]
            }
        }
    """
    try:
        version = request.args.get('version', 'v1')
        task = request.args.get('task', 'q1')

        result = viz_service.get_roi_config(version, task)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting ROI config: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500
```

### 5.2 Service层ROI方法

**文件**: `src/web/modules/module01_data_visualization/service.py`

```python
import json
from pathlib import Path

class DataVisualizationService:

    def get_roi_config(self, version: str, task: str) -> Dict[str, Any]:
        """
        获取ROI配置

        Args:
            version: 数据版本 (v1/v2)
            task: 任务ID (q1/q2/q3/q4/q5/all)

        Returns:
            {
                "success": True,
                "data": {
                    "version": "v1",
                    "task": "q1",
                    "regions": [...]
                }
            }
        """
        try:
            # 构建ROI配置文件路径
            project_root = Path(__file__).parent.parent.parent.parent.parent
            config_file = project_root / "config" / f"roi_{version}.json"

            # 检查文件是否存在
            if not config_file.exists():
                return {
                    "success": False,
                    "error": f"ROI config file not found: roi_{version}.json",
                    "data": None
                }

            # 读取ROI配置
            with open(config_file, 'r', encoding='utf-8') as f:
                roi_config = json.load(f)

            # 筛选对应任务的ROI区域
            if task == 'all':
                # 返回所有ROI区域
                filtered_regions = roi_config['regions']
            else:
                # 筛选特定任务的ROI
                filtered_regions = [
                    region for region in roi_config['regions']
                    if region['task'] == task
                ]

            return {
                "success": True,
                "data": {
                    "version": roi_config['version'],
                    "layout": roi_config['layout'],
                    "task": task,
                    "regions": filtered_regions
                }
            }

        except Exception as e:
            logger.error(f"Failed to get ROI config: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
```

---

## 6. 前端实现

### 6.1 ROI Service

**文件**: `frontend/src/services/roiService.js`

```javascript
import { api } from './api';

export const roiService = {
  /**
   * 获取ROI配置
   * @param {string} version - 数据版本 (v1/v2)
   * @param {string} task - 任务ID (q1/q2/q3/q4/q5/all)
   */
  getROIConfig: async (version, task) => {
    try {
      const response = await api.get('/api/data/roi', { version, task });
      return response;
    } catch (error) {
      console.error('Failed to fetch ROI config:', error);
      return { success: false, data: null };
    }
  }
};
```

### 6.2 ROI Analyzer工具

**文件**: `frontend/src/utils/roiAnalyzer.js`

```javascript
/**
 * ROI分析工具
 * 计算眼动轨迹与ROI的交互统计
 */

/**
 * 检查点是否在ROI内部
 * @param {number} x - 点的X坐标
 * @param {number} y - 点的Y坐标
 * @param {Object} roi - ROI配置 {x, y, width, height}
 * @returns {boolean}
 */
function isPointInROI(x, y, roi) {
  return (
    x >= roi.x &&
    x <= roi.x + roi.width &&
    y >= roi.y &&
    y <= roi.y + roi.height
  );
}

/**
 * 计算单个ROI的统计信息
 * @param {Array} gazeData - 眼动数据 [{x, y, timestamp}, ...]
 * @param {Object} roi - ROI配置
 * @returns {Object} 统计结果
 */
export function calculateROIStats(gazeData, roi) {
  let entryCount = 0;      // 进入次数
  let exitCount = 0;       // 离开次数
  let pointsInside = 0;    // ROI内数据点数
  let durationInside = 0;  // ROI内停留时间(秒)

  let wasInside = false;   // 上一个点是否在ROI内

  for (let i = 0; i < gazeData.length; i++) {
    const point = gazeData[i];
    const isInside = isPointInROI(point.x, point.y, roi);

    // 统计进入和离开
    if (isInside && !wasInside) {
      entryCount++;  // 从外部进入ROI
    } else if (!isInside && wasInside) {
      exitCount++;   // 从ROI离开到外部
    }

    // 统计ROI内数据点
    if (isInside) {
      pointsInside++;

      // 计算停留时间（当前点到下一个点的时间差）
      if (i < gazeData.length - 1) {
        const timeDiff = gazeData[i + 1].timestamp - point.timestamp;
        durationInside += timeDiff;
      }
    }

    wasInside = isInside;
  }

  const totalPoints = gazeData.length;
  const insideRatio = totalPoints > 0 ? pointsInside / totalPoints : 0;

  return {
    entry_count: entryCount,
    exit_count: exitCount,
    points_inside: pointsInside,
    total_points: totalPoints,
    inside_ratio: insideRatio,
    duration_inside: durationInside
  };
}

/**
 * 计算所有ROI的统计信息
 * @param {Array} gazeData - 眼动数据
 * @param {Array} regions - ROI区域列表
 * @returns {Object} ROI统计结果映射 {roiId: stats}
 */
export function calculateAllROIStats(gazeData, regions) {
  const roiStats = {};

  regions.forEach(roi => {
    roiStats[roi.id] = calculateROIStats(gazeData, roi);
  });

  return roiStats;
}
```

### 6.3 GazeTrajectoryChart组件修改

**文件**: `frontend/src/components/Charts/GazeTrajectoryChart.jsx`

```javascript
import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { calculateAllROIStats } from '../../utils/roiAnalyzer';
import PlotlyChart from './PlotlyChart';

const GazeTrajectoryChart = ({
  data,
  roiConfig = null,  // 新增: ROI配置
  loading = false,
  title = '眼动轨迹图',
  showColorbar = true,
  style = {}
}) => {
  const { t } = useTranslation(['module01']);

  // 计算ROI统计（如果有ROI配置）
  const roiStats = useMemo(() => {
    if (!roiConfig || !roiConfig.regions || !data || data.length === 0) {
      return null;
    }
    return calculateAllROIStats(data, roiConfig.regions);
  }, [data, roiConfig]);

  // 处理数据并生成Plotly图表数据
  const plotData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return [];
    }

    const x = data.map(d => d.x);
    const y = data.map(d => d.y);
    const time = data.map(d => d.timestamp || d.time || 0);

    return [
      {
        type: 'scatter',
        mode: 'lines+markers',
        x: x,
        y: y,
        marker: {
          size: 6,
          color: time,
          colorscale: 'Viridis',
          showscale: showColorbar,
          colorbar: {
            title: t('timeSeconds'),
            titleside: 'right'
          },
          line: { color: 'white', width: 1 }
        },
        line: { color: 'rgba(100, 100, 100, 0.3)', width: 1 },
        text: time.map((timeValue, i) =>
          `${t('point')} ${i + 1}<br>${t('timeSeconds')}: ${timeValue.toFixed(2)}<br>${t('position')}: (${x[i].toFixed(3)}, ${y[i].toFixed(3)})`
        ),
        hoverinfo: 'text',
        name: t('trajectoryChart')
      },
      {
        type: 'scatter',
        mode: 'markers',
        x: [x[0]],
        y: [y[0]],
        marker: { size: 15, color: 'green', symbol: 'star', line: { color: 'white', width: 2 } },
        text: [t('startPoint')],
        hoverinfo: 'text',
        name: t('startPoint'),
        showlegend: true
      },
      {
        type: 'scatter',
        mode: 'markers',
        x: [x[x.length - 1]],
        y: [y[y.length - 1]],
        marker: { size: 15, color: 'red', symbol: 'square', line: { color: 'white', width: 2 } },
        text: [t('endPoint')],
        hoverinfo: 'text',
        name: t('endPoint'),
        showlegend: true
      }
    ];
  }, [data, showColorbar, t]);

  // 图表布局配置 - 添加ROI矩形
  const layout = useMemo(() => {
    const baseLayout = {
      title: { text: title, font: { size: 16, weight: 'bold' } },
      xaxis: {
        title: t('xCoordinateNormalized'),
        range: [0, 1],
        showgrid: true,
        gridcolor: '#e0e0e0',
        zeroline: false
      },
      yaxis: {
        title: t('yCoordinateNormalized'),
        range: [0, 1],
        showgrid: true,
        gridcolor: '#e0e0e0',
        zeroline: false,
        scaleanchor: 'x',
        scaleratio: 1
      },
      hovermode: 'closest',
      showlegend: true,
      legend: {
        x: 1,
        xanchor: 'right',
        y: 1,
        bgcolor: 'rgba(255, 255, 255, 0.8)',
        bordercolor: '#ccc',
        borderwidth: 1
      },
      plot_bgcolor: '#f9f9f9',
      paper_bgcolor: 'white'
    };

    // 如果有ROI配置，添加ROI矩形
    if (roiConfig && roiConfig.regions) {
      baseLayout.shapes = roiConfig.regions.map(roi => ({
        type: 'rect',
        xref: 'x',
        yref: 'y',
        x0: roi.x,
        y0: roi.y,
        x1: roi.x + roi.width,
        y1: roi.y + roi.height,
        fillcolor: roi.color,
        opacity: 0.25,  // 半透明
        line: {
          color: roi.color,
          width: 2
        }
      }));

      // 添加ROI标签注释
      baseLayout.annotations = roiConfig.regions.map(roi => ({
        x: roi.x + roi.width / 2,
        y: roi.y + roi.height / 2,
        text: roi.name,
        showarrow: false,
        font: {
          size: 10,
          color: '#333'
        },
        bgcolor: 'rgba(255, 255, 255, 0.7)',
        borderpad: 2
      }));
    }

    return baseLayout;
  }, [title, t, roiConfig]);

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d', 'autoScale2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'gaze_trajectory',
      height: 800,
      width: 800,
      scale: 2
    }
  };

  return (
    <div>
      <PlotlyChart
        data={plotData}
        layout={layout}
        config={config}
        loading={loading}
        style={{ height: '500px', ...style }}
      />

      {/* ROI统计信息显示 */}
      {roiStats && (
        <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
          <h4 style={{ margin: '0 0 12px 0' }}>ROI统计</h4>
          {roiConfig.regions.map(roi => {
            const stats = roiStats[roi.id];
            return (
              <div key={roi.id} style={{ marginBottom: 8 }}>
                <strong>{roi.name}</strong>:
                进入{stats.entry_count}次 /
                离开{stats.exit_count}次 /
                内部点数{stats.points_inside} /
                停留{stats.duration_inside.toFixed(2)}秒 ({(stats.inside_ratio * 100).toFixed(1)}%)
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default GazeTrajectoryChart;
```

### 6.4 Module01.jsx主组件修改

**文件**: `frontend/src/pages/Module01/Module01.jsx`

```javascript
import React, { useState, useEffect } from 'react';
import { roiService } from '../../services/roiService';
// ... 其他imports

const Module01 = () => {
  // ... 现有state
  const [roiConfig, setRoiConfig] = useState(null);  // 新增: ROI配置

  // 当版本或任务变化时，加载ROI配置
  useEffect(() => {
    const loadROIConfig = async () => {
      // 仅在V1数据时加载ROI
      if (selectedVersion === 'v1' && selectedTask) {
        const result = await roiService.getROIConfig('v1', selectedTask);
        if (result.success) {
          setRoiConfig(result.data);
        } else {
          setRoiConfig(null);
        }
      } else {
        // V2或全部版本时不显示ROI
        setRoiConfig(null);
      }
    };

    loadROIConfig();
  }, [selectedVersion, selectedTask]);

  return (
    <div>
      {/* ... 其他UI */}

      {/* 眼动轨迹图 - 传递ROI配置 */}
      <GazeTrajectoryChart
        data={gazeData}
        roiConfig={roiConfig}  // 传递ROI配置
        loading={loadingData}
        title=""
      />
    </div>
  );
};
```

---

## 7. ROI进出统计算法

### 7.1 算法原理

**状态机方法**：

```
状态定义：
- OUTSIDE: 当前点在ROI外部
- INSIDE:  当前点在ROI内部

转换规则：
OUTSIDE → INSIDE: entry_count++  (进入)
INSIDE → OUTSIDE: exit_count++   (离开)
INSIDE → INSIDE:  points_inside++ (内部停留)
OUTSIDE → OUTSIDE: (忽略)
```

**伪代码**：
```python
def calculate_roi_stats(gaze_data, roi):
    entry_count = 0
    exit_count = 0
    points_inside = 0
    was_inside = False

    for point in gaze_data:
        is_inside = is_point_in_roi(point.x, point.y, roi)

        if is_inside and not was_inside:
            entry_count += 1  # 进入ROI
        elif not is_inside and was_inside:
            exit_count += 1   # 离开ROI

        if is_inside:
            points_inside += 1

        was_inside = is_inside

    return {entry_count, exit_count, points_inside}
```

### 7.2 边界情况处理

1. **起点在ROI内**：不计入entry_count（因为没有"进入"动作）
2. **终点在ROI内**：不计入exit_count（因为没有"离开"动作）
3. **空数据集**：返回全0统计
4. **单点数据**：根据该点是否在ROI内返回相应统计

### 7.3 性能优化

- **客户端计算**：统计计算在前端进行，减轻服务器负担
- **Memoization**：使用`useMemo`缓存计算结果
- **批量计算**：一次计算所有ROI的统计，避免重复遍历

---

## 8. 开发计划

### 8.1 开发阶段

| 阶段 | 任务 | 工作量 | 优先级 |
|------|------|--------|--------|
| 阶段1 | 后端ROI API开发 | 2h | P0 |
| 阶段2 | ROI Service和Analyzer | 2h | P0 |
| 阶段3 | GazeTrajectoryChart修改 | 3h | P0 |
| 阶段4 | Module01主组件集成 | 1h | P0 |
| 阶段5 | i18n翻译添加 | 1h | P1 |
| 阶段6 | 测试与优化 | 2h | P0 |
| **总计** | | **11h** | |

### 8.2 开发顺序

```
第1步: 后端ROI API
  ├── 添加get_roi_config方法到service.py
  └── 添加/api/data/roi路由到api.py

第2步: 前端基础设施
  ├── 创建roiService.js
  └── 创建roiAnalyzer.js

第3步: 图表组件修改
  ├── 修改GazeTrajectoryChart.jsx
  │   ├── 添加roiConfig prop
  │   ├── 添加ROI shapes到layout
  │   ├── 集成ROI统计计算
  │   └── 显示统计结果UI
  └── 更新组件prop types

第4步: 主组件集成
  ├── Module01.jsx加载ROI配置
  └── 传递ROI配置到图表组件

第5步: i18n支持
  ├── 添加ROI相关翻译key
  └── 更新三语翻译文件

第6步: 测试
  ├── V1单任务测试
  ├── V1全部任务测试
  ├── V2数据测试（不显示ROI）
  └── 进出次数统计验证
```

---

## 9. 测试验证

### 9.1 功能测试

**测试用例1: V1单任务ROI显示**
```
前置条件: 已有V1数据
步骤:
  1. 选择数据版本=V1
  2. 选择研究组别=对照组
  3. 选择受试者=n21
  4. 选择任务=Q1
  5. 点击加载数据
预期结果:
  ✓ 眼动轨迹图显示
  ✓ Q1的ROI矩形叠加显示（半透明，颜色#FF6B6B）
  ✓ ROI标签显示"Q1_时间定向区"
  ✓ ROI统计显示进出次数
```

**测试用例2: V1全部任务ROI显示**
```
步骤:
  1. 选择数据版本=V1
  2. 选择任务=全部任务
  3. 点击加载数据
预期结果:
  ✓ 显示Q1-Q5所有5个ROI区域
  ✓ 每个ROI不同颜色
  ✓ 显示所有ROI的统计信息
```

**测试用例3: V2数据不显示ROI**
```
步骤:
  1. 选择数据版本=V2
  2. 选择任务=Q1
  3. 点击加载数据
预期结果:
  ✓ 眼动轨迹图正常显示
  ✗ 不显示ROI矩形
  ✗ 不显示ROI统计
```

### 9.2 ROI统计算法验证

**测试数据**：
```javascript
// 模拟眼动数据
const testData = [
  {x: 0.05, y: 0.1, timestamp: 0},    // 外部
  {x: 0.15, y: 0.25, timestamp: 0.1}, // 进入ROI
  {x: 0.20, y: 0.30, timestamp: 0.2}, // ROI内
  {x: 0.25, y: 0.35, timestamp: 0.3}, // ROI内
  {x: 0.45, y: 0.45, timestamp: 0.4}, // 离开ROI
  {x: 0.50, y: 0.50, timestamp: 0.5}  // 外部
];

// ROI配置
const testROI = {
  x: 0.1, y: 0.2, width: 0.3, height: 0.2
};

// 预期结果
{
  entry_count: 1,     // 1次进入
  exit_count: 1,      // 1次离开
  points_inside: 3,   // 3个点在内部
  inside_ratio: 0.5   // 50%停留
}
```

### 9.3 性能测试

**测试场景**：大数据集
```
数据点数: 10,000个眼动点
ROI数量: 5个区域
预期性能: < 100ms计算时间
```

---

## 10. 架构合规性

### 10.1 符合现有架构

✅ **Module00/Module01分离原则**
- ROI配置文件放在`config/`目录（静态配置）
- Module01仅读取和展示，不修改数据

✅ **MetadataReader共享原则**
- ROI配置独立于MetadataReader
- 不影响现有元数据管理

✅ **i18n国际化支持**
- ROI名称支持多语言
- 统计结果UI支持i18n

✅ **前后端分离**
- 后端提供ROI配置API
- 前端负责可视化和统计计算

### 10.2 设计决策理由

**Q: 为什么ROI统计在前端计算？**
A:
1. 减轻服务器负担
2. 提高响应速度（无需网络往返）
3. 便于实时交互（未来可扩展）

**Q: 为什么只支持V1数据的ROI？**
A:
1. V1和V2的ROI布局不同
2. 避免使用错误的ROI配置
3. 保持数据准确性

**Q: 为什么使用半透明显示ROI？**
A:
1. 不遮挡眼动轨迹
2. 清晰标识ROI区域
3. 符合数据可视化最佳实践

---

## 11. 附录

### 11.1 ROI配置示例

完整的V1 ROI配置见：`config/roi_v1.json`

### 11.2 相关文档

- [MODULE01_UI_UX_OPTIMIZATION.md](MODULE01_UI_UX_OPTIMIZATION.md) - Module01优化设计
- [I18N_QUICK_REFERENCE.md](I18N_QUICK_REFERENCE.md) - i18n快速参考
- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) - 架构总览

### 11.3 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2025-10-02 | v1.0 | 初始版本，完整的ROI可视化与统计设计 |

---

**文档状态**: ✅ 设计完成，待评审
**下一步**: 用户确认设计方案后开始开发

