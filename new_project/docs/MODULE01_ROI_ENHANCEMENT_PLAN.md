# 📊 Module01 ROI增强功能优化方案

> **目标**: 将老项目的完整ROI分析功能整合到新架构
> **当前状态**: 基础ROI可视化已完成，需要增强真实数据统计和背景图叠加
> **分析日期**: 2025-10-02
> **参考代码**: 老项目ROI分析脚本 (Python + OpenCV + PIL)

---

## 🔍 问题分析

### 当前问题

1. **ROI统计不准确**
   - 显示: `roiEntryCount: 0, roiExitCount: 0, roiPointsInside: 0`
   - 原因: 当前ROI配置 (`roi_v1.json`) 是简化版，只有1个区域/任务
   - 老代码: 每个任务有多个ROI (keywords, instructions, background)

2. **背景图未显示**
   - 原因: 前端未实现图片叠加功能
   - 老代码: 使用PIL将背景图、ROI矩形、轨迹叠加绘制

3. **ROI配置不完整**
   - 当前: 每个任务只有1个简单矩形
   - 老代码: 每个任务包含多个KW (keywords) + INST (instructions) + BG (background)

---

## 🎯 核心差异对比

### 老代码的ROI结构 (n2q1示例)

```python
USER_DEFINED_ROI = {
    "n2q1": {
        "keywords": [
            ("KW_n2q1_1", 0.01, 0.5886, 0.39, 0.4164),   # 4个关键词区域
            ("KW_n2q1_2", 0.39, 0.5886, 0.668, 0.4164),
            ("KW_n2q1_3", 0.01, 0.3494, 0.49, 0.1716),
            ("KW_n2q1_4", 0.49, 0.3494, 0.915, 0.1716),
        ],
        "instructions": [
            ("INST_n2q1_1", 0.01, 0.8250, 0.355, 0.6500)  # 1个指令区域
        ],
        "background": [
            ("BG_n2q1", 0, 0, 1, 1)  # 1个背景区域(全屏)
        ]
    }
}
```

**坐标格式**: `(name, x_min, y_max, x_max, y_min)`
**注意**: Y轴坐标是**倒置的** (OpenCV坐标系，原点在左上)

### 新架构的ROI结构 (roi_v1.json)

```json
{
    "id": "q1_time_orientation",
    "name": "Q1_时间定向区",
    "task": "q1",
    "x": 0.1,        // x_min
    "y": 0.2,        // y_min (Plotly坐标系，原点在左下)
    "width": 0.3,    // width
    "height": 0.2,   // height
    "color": "#FF6B6B"
}
```

**坐标格式**: `(x, y, width, height)`
**注意**: Y轴坐标是**正向的** (Plotly坐标系，原点在左下)

---

## 🏗️ 优化方案设计

### 架构原则

1. ✅ **配置驱动**: ROI定义完全通过JSON配置，不硬编码
2. ✅ **版本隔离**: V1/V2数据使用不同ROI配置
3. ✅ **前后端分离**: 后端提供数据，前端负责渲染
4. ✅ **模块化**: 按功能拆分成独立组件
5. ✅ **可扩展**: 支持新任务/新版本ROI的导入

---

## 📐 Phase 1: ROI配置增强

### 1.1 扩展ROI配置结构

**目标**: 支持多层次ROI (KW/INST/BG)

**新的 `roi_v1_enhanced.json` 结构**:

```json
{
    "version": "v1",
    "layout": "legacy",
    "coordinate_system": "plotly",  // 新增: 坐标系标识
    "tasks": {
        "q1": {
            "task_id": "q1",
            "task_name": "时间定向",
            "background_image": "Q1.jpg",
            "regions": {
                "keywords": [
                    {
                        "id": "KW_q1_1",
                        "name": "关键词区域1",
                        "type": "keyword",
                        "x": 0.01,
                        "y": 0.4164,  // 已转换为Plotly坐标 (1 - 0.5886)
                        "width": 0.38,  // 0.39 - 0.01
                        "height": 0.1722,  // 0.5886 - 0.4164
                        "color": "#FF6B6B",
                        "priority": 2  // 优先级: KW > INST > BG
                    },
                    // ... 其他KW区域
                ],
                "instructions": [
                    {
                        "id": "INST_q1_1",
                        "name": "指令区域",
                        "type": "instruction",
                        "x": 0.01,
                        "y": 0.6500,  // 1 - 0.8250 (Y轴转换)
                        "width": 0.345,
                        "height": 0.175,
                        "color": "#FFA500",
                        "priority": 1
                    }
                ],
                "background": [
                    {
                        "id": "BG_q1",
                        "name": "背景区域",
                        "type": "background",
                        "x": 0,
                        "y": 0,
                        "width": 1,
                        "height": 1,
                        "color": "#87CEEB",
                        "priority": 0
                    }
                ]
            }
        }
        // q2, q3, q4, q5 类似结构
    }
}
```

**坐标转换规则**:
```javascript
// OpenCV (老代码) -> Plotly (新架构)
plotly_y_min = 1 - opencv_y_max
plotly_y_max = 1 - opencv_y_min
plotly_height = opencv_y_max - opencv_y_min
```

### 1.2 配置生成工具

**新建**: `scripts/convert_old_roi_to_new.py`

```python
"""
将老项目的ROI配置转换为新架构JSON格式
"""
import json
from pathlib import Path

# 老代码的ROI定义
OLD_ROI_CONFIG = {
    "n2q1": {
        "keywords": [...],
        "instructions": [...],
        "background": [...]
    },
    # ...
}

def convert_opencv_to_plotly(x_min, y_max, x_max, y_min):
    """
    OpenCV坐标 -> Plotly坐标
    老代码: (x_min, y_max, x_max, y_min) Y轴倒置
    新代码: (x, y, width, height) Y轴正向
    """
    x = x_min
    y = 1 - y_max  # Y轴反转
    width = x_max - x_min
    height = y_max - y_min  # 已经是正值
    return x, y, width, height

def convert_roi_config(old_config, version="v1"):
    """主转换函数"""
    new_config = {
        "version": version,
        "layout": "legacy" if version == "v1" else "new",
        "coordinate_system": "plotly",
        "description": f"从老项目ROI配置转换 (版本{version})",
        "created_date": "2025-10-02",
        "tasks": {}
    }

    for task_key, roi_def in old_config.items():
        # task_key = "n2q1" => qid = "q1"
        qid = task_key[-2:]  # "q1"

        task_config = {
            "task_id": qid,
            "task_name": get_task_name(qid),
            "background_image": f"{qid.upper()}.jpg",
            "regions": {
                "keywords": [],
                "instructions": [],
                "background": []
            }
        }

        # 转换keywords
        for i, (name, x_min, y_max, x_max, y_min) in enumerate(roi_def["keywords"]):
            x, y, w, h = convert_opencv_to_plotly(x_min, y_max, x_max, y_min)
            task_config["regions"]["keywords"].append({
                "id": f"KW_{qid}_{i+1}",
                "name": name,
                "type": "keyword",
                "x": round(x, 4),
                "y": round(y, 4),
                "width": round(w, 4),
                "height": round(h, 4),
                "color": "#FF6B6B",
                "priority": 2
            })

        # 转换instructions (同理)
        # 转换background (同理)

        new_config["tasks"][qid] = task_config

    return new_config

def get_task_name(qid):
    names = {
        "q1": "时间定向",
        "q2": "空间定向",
        "q3": "即刻记忆",
        "q4": "注意力与计算",
        "q5": "延迟回忆"
    }
    return names.get(qid, f"任务{qid}")

if __name__ == "__main__":
    new_config = convert_roi_config(OLD_ROI_CONFIG, version="v1")

    output_path = Path("config/roi_v1_enhanced.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)

    print(f"✅ 转换完成: {output_path}")
```

---

## 🔧 Phase 2: 后端ROI数据服务增强

### 2.1 ROI配置加载器升级

**修改**: `src/web/modules/module01_data_visualization/service.py`

```python
def get_roi_config_enhanced(self, version: str, task: str) -> Dict[str, Any]:
    """
    获取增强版ROI配置 (支持多层次ROI)

    Returns:
        {
            "success": True,
            "data": {
                "version": "v1",
                "task": "q1",
                "background_image": "/static/background_images/v1/Q1.jpg",
                "regions": {
                    "keywords": [...],      // 关键词区域列表
                    "instructions": [...],  // 指令区域列表
                    "background": [...]     // 背景区域列表
                }
            }
        }
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent.parent
        config_file = project_root / "config" / f"roi_{version}_enhanced.json"

        if not config_file.exists():
            # 降级到简单版
            logger.warning(f"Enhanced config not found, fallback to simple: {config_file}")
            return self.get_roi_config(version, task)

        with open(config_file, 'r', encoding='utf-8') as f:
            full_config = json.load(f)

        # 提取指定任务的配置
        task_config = full_config["tasks"].get(task, None)
        if not task_config:
            return {"success": False, "error": f"Task {task} not found", "data": None}

        # 构建背景图路径
        bg_image = f"/static/background_images/{version}/{task_config['background_image']}"

        return {
            "success": True,
            "data": {
                "version": version,
                "task": task,
                "task_name": task_config["task_name"],
                "background_image": bg_image,
                "regions": task_config["regions"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get enhanced ROI config: {e}", exc_info=True)
        return {"success": False, "error": str(e), "data": None}
```

### 2.2 ROI统计算法实现

**新增**: `src/web/modules/module01_data_visualization/roi_analyzer.py`

```python
"""
ROI分析器 - 基于老代码逻辑优化
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ROIAnalyzer:
    """ROI统计分析器"""

    def __init__(self, roi_config: Dict[str, Any]):
        """
        Args:
            roi_config: 增强版ROI配置
            {
                "keywords": [...],
                "instructions": [...],
                "background": [...]
            }
        """
        self.regions = self._flatten_regions(roi_config)

    def _flatten_regions(self, roi_config):
        """将分层ROI展平为优先级排序列表"""
        all_regions = []

        # 按优先级顺序: keywords > instructions > background
        for region in roi_config.get("keywords", []):
            all_regions.append(region)
        for region in roi_config.get("instructions", []):
            all_regions.append(region)
        for region in roi_config.get("background", []):
            all_regions.append(region)

        # 按priority降序排序 (优先匹配高优先级)
        all_regions.sort(key=lambda r: r.get("priority", 0), reverse=True)
        return all_regions

    def find_roi_for_point(self, x: float, y: float) -> str:
        """
        查找点所属ROI (优先匹配高优先级)

        Args:
            x, y: 归一化坐标 [0, 1]

        Returns:
            roi_id or None
        """
        for region in self.regions:
            x_min = region["x"]
            y_min = region["y"]
            x_max = x_min + region["width"]
            y_max = y_min + region["height"]

            if x_min <= x <= x_max and y_min <= y <= y_max:
                return region["id"]

        return None

    def calculate_stats(self, gaze_data: pd.DataFrame) -> Dict[str, Dict]:
        """
        计算ROI统计信息 (逐帧分析法)

        Args:
            gaze_data: DataFrame with columns [x, y, timestamp]

        Returns:
            {
                "KW_q1_1": {
                    "fixation_time": 2.5,  // 秒
                    "entry_count": 3,
                    "regression_count": 2,
                    "points_inside": 25,
                    "total_points": 100,
                    "coverage_ratio": 0.25
                },
                ...
            }
        """
        if gaze_data.empty or len(gaze_data) < 2:
            return {}

        # 初始化统计
        stats = {}
        for region in self.regions:
            stats[region["id"]] = {
                "fixation_time": 0.0,
                "entry_count": 0,
                "regression_count": 0,
                "points_inside": 0,
                "total_points": len(gaze_data),
                "coverage_ratio": 0.0,
                "name": region["name"],
                "type": region["type"]
            }

        # 计算time_diff
        gaze_data = gaze_data.sort_values("timestamp").reset_index(drop=True)
        time_diff = gaze_data["timestamp"].diff().fillna(0)

        prev_roi = None

        for i in range(len(gaze_data)):
            x = gaze_data.at[i, "x"]
            y = gaze_data.at[i, "y"]
            dt = time_diff.iloc[i]

            # 查找当前点所属ROI
            current_roi = self.find_roi_for_point(x, y)

            if current_roi:
                # 累加停留时间 (秒)
                stats[current_roi]["fixation_time"] += dt
                stats[current_roi]["points_inside"] += 1

                # 检测进入事件
                if current_roi != prev_roi:
                    stats[current_roi]["entry_count"] += 1

            prev_roi = current_roi

        # 计算回归次数 (entry_count - 1)
        for roi_id, st in stats.items():
            st["regression_count"] = max(0, st["entry_count"] - 1)
            st["coverage_ratio"] = st["points_inside"] / st["total_points"] if st["total_points"] > 0 else 0.0

        return stats
```

### 2.3 新增API端点

**修改**: `src/web/modules/module01_data_visualization/api.py`

```python
@m01_bp.route('/roi-stats', methods=['POST'])
def calculate_roi_stats():
    """
    计算ROI统计信息

    POST /api/data/roi-stats

    Body:
        {
            "version": "v1",
            "task": "q1",
            "gaze_data": [
                {"x": 0.5, "y": 0.5, "timestamp": 0.0},
                {"x": 0.51, "y": 0.52, "timestamp": 0.016},
                ...
            ]
        }

    Returns:
        {
            "success": true,
            "data": {
                "KW_q1_1": {
                    "fixation_time": 2.5,
                    "entry_count": 3,
                    ...
                },
                ...
            }
        }
    """
    try:
        data = request.get_json()
        version = data.get("version")
        task = data.get("task")
        gaze_data_list = data.get("gaze_data", [])

        if not version or not task:
            return jsonify({"success": False, "error": "Missing version or task"}), 400

        # 获取ROI配置
        roi_result = viz_service.get_roi_config_enhanced(version, task)
        if not roi_result["success"]:
            return jsonify(roi_result), 404

        # 转换为DataFrame
        gaze_df = pd.DataFrame(gaze_data_list)

        # 计算统计
        from .roi_analyzer import ROIAnalyzer
        analyzer = ROIAnalyzer(roi_result["data"]["regions"])
        stats = analyzer.calculate_stats(gaze_df)

        return jsonify({"success": True, "data": stats})

    except Exception as e:
        logger.error(f"Error calculating ROI stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
```

---

## 🎨 Phase 3: 前端可视化增强

### 3.1 背景图叠加组件

**新增**: `frontend/src/components/Charts/BackgroundImageLayer.jsx`

```jsx
/**
 * 背景图层组件 - 在Plotly图表下方显示背景图
 */
import React from 'react';

const BackgroundImageLayer = ({ imagePath, visible = true, opacity = 0.3 }) => {
  if (!visible || !imagePath) return null;

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      pointerEvents: 'none',  // 允许点击穿透
      zIndex: 1  // 在图表下方
    }}>
      <img
        src={`http://127.0.0.1:9090${imagePath}`}
        alt="Task Background"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          opacity: opacity
        }}
      />
    </div>
  );
};

export default BackgroundImageLayer;
```

### 3.2 增强版轨迹图组件

**修改**: `frontend/src/components/Charts/GazeTrajectoryChart.jsx`

```jsx
import BackgroundImageLayer from './BackgroundImageLayer';

const GazeTrajectoryChart = ({
  data,
  roiConfig = null,
  backgroundImage = null,  // 新增: 背景图路径
  showBackground = true,   // 新增: 是否显示背景
  backgroundOpacity = 0.3, // 新增: 背景透明度
  loading = false,
  title = '眼动轨迹图',
  showColorbar = true,
  style = {}
}) => {
  const { t } = useTranslation(['module01']);

  // ROI统计计算 (使用增强版配置)
  const roiStats = useMemo(() => {
    if (!roiConfig || !roiConfig.regions || !data || data.length === 0) {
      return null;
    }

    // 将分层regions展平
    const allRegions = [
      ...(roiConfig.regions.keywords || []),
      ...(roiConfig.regions.instructions || []),
      ...(roiConfig.regions.background || [])
    ];

    return calculateAllROIStats(data, allRegions);
  }, [data, roiConfig]);

  // Plotly layout (添加所有ROI矩形)
  const layout = useMemo(() => {
    const baseLayout = { /* ... 现有布局 ... */ };

    if (roiConfig && roiConfig.regions) {
      const allRegions = [
        ...(roiConfig.regions.keywords || []),
        ...(roiConfig.regions.instructions || []),
        ...(roiConfig.regions.background || [])
      ];

      // 绘制所有ROI
      baseLayout.shapes = allRegions.map(roi => ({
        type: 'rect',
        xref: 'x',
        yref: 'y',
        x0: roi.x,
        y0: roi.y,
        x1: roi.x + roi.width,
        y1: roi.y + roi.height,
        fillcolor: roi.color,
        opacity: roi.type === 'background' ? 0.1 : 0.25,
        line: { color: roi.color, width: 2 }
      }));

      // 标签
      baseLayout.annotations = allRegions
        .filter(roi => roi.type !== 'background')  // 背景不显示标签
        .map(roi => ({
          x: roi.x + roi.width / 2,
          y: roi.y + roi.height / 2,
          text: roi.name,
          showarrow: false,
          font: { size: 10, color: '#333', weight: 'bold' },
          bgcolor: 'rgba(255, 255, 255, 0.7)',
          borderpad: 2
        }));
    }

    return baseLayout;
  }, [title, t, roiConfig]);

  return (
    <div style={{ position: 'relative' }}>
      {/* 背景图层 */}
      <BackgroundImageLayer
        imagePath={backgroundImage}
        visible={showBackground}
        opacity={backgroundOpacity}
      />

      {/* Plotly图表 */}
      <PlotlyChart
        data={plotData}
        layout={layout}
        config={config}
        loading={loading}
        style={{ height: '500px', position: 'relative', zIndex: 2, ...style }}
      />

      {/* ROI统计面板 (分类显示) */}
      {roiStats && roiConfig && (
        <div style={{ marginTop: 16 }}>
          <h4>{t('roiStatistics')}</h4>

          {/* 关键词区域 */}
          {roiConfig.regions.keywords && roiConfig.regions.keywords.length > 0 && (
            <div>
              <h5>关键词区域 (Keywords)</h5>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12 }}>
                {roiConfig.regions.keywords.map(roi => renderROIStats(roi, roiStats[roi.id]))}
              </div>
            </div>
          )}

          {/* 指令区域 */}
          {roiConfig.regions.instructions && roiConfig.regions.instructions.length > 0 && (
            <div>
              <h5>指令区域 (Instructions)</h5>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12 }}>
                {roiConfig.regions.instructions.map(roi => renderROIStats(roi, roiStats[roi.id]))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

function renderROIStats(roi, stats) {
  if (!stats) return null;

  return (
    <div key={roi.id} style={{
      padding: 8,
      background: 'white',
      borderRadius: 4,
      borderLeft: `4px solid ${roi.color}`
    }}>
      <div style={{ fontWeight: 'bold', color: roi.color }}>
        {roi.name}
      </div>
      <div style={{ fontSize: 12, color: '#666' }}>
        <div>停留时间: <strong>{stats.fixation_time.toFixed(2)}s</strong></div>
        <div>进入次数: <strong>{stats.entry_count}</strong></div>
        <div>回归次数: <strong>{stats.regression_count}</strong></div>
        <div>覆盖率: <strong>{(stats.coverage_ratio * 100).toFixed(1)}%</strong></div>
      </div>
    </div>
  );
}
```

---

## 📊 Phase 4: 数据流整合

### 4.1 Module01页面集成

**修改**: `frontend/src/pages/Module01/Module01.jsx`

```jsx
const loadGazeData = async () => {
  // ... 现有数据加载逻辑 ...

  // 加载增强版ROI配置
  const dataVersion = result.metadata?.data_version || 'v1';
  const roiResult = await roiService.getROIConfigEnhanced(dataVersion, selectedTask);

  if (roiResult.success) {
    setRoiConfig(roiResult.data);
    setBackgroundImage(roiResult.data.background_image);

    // 【可选】调用后端计算ROI统计
    const statsResult = await roiService.calculateROIStats({
      version: dataVersion,
      task: selectedTask,
      gaze_data: result.data
    });

    if (statsResult.success) {
      setRoiStats(statsResult.data);
    }
  }
};
```

### 4.2 前端服务扩展

**修改**: `frontend/src/services/roiService.js`

```javascript
export const roiService = {
  // 获取增强版ROI配置
  getROIConfigEnhanced: async (version, task) => {
    try {
      const response = await api.get('/data/roi-enhanced', { version, task });
      return response;
    } catch (error) {
      console.error('Failed to fetch enhanced ROI config:', error);
      return { success: false, data: null, error: error.message };
    }
  },

  // 计算ROI统计 (后端计算)
  calculateROIStats: async (payload) => {
    try {
      const response = await api.post('/data/roi-stats', payload);
      return response;
    } catch (error) {
      console.error('Failed to calculate ROI stats:', error);
      return { success: false, data: null, error: error.message };
    }
  }
};
```

---

## 🔄 Phase 5: 配置导入工具

### 5.1 ROI配置管理界面 (Module00扩展)

**新增**: `frontend/src/components/Module00/ROIConfigManager.jsx`

```jsx
/**
 * ROI配置管理器 - 支持导入/编辑/导出ROI配置
 */
import React, { useState } from 'react';
import { Upload, Button, Table, message, Modal } from 'antd';
import { UploadOutlined, EditOutlined, DownloadOutlined } from '@ant-design/icons';

const ROIConfigManager = () => {
  const [configs, setConfigs] = useState([]);
  const [editModal, setEditModal] = useState({ visible: false, config: null });

  // 导入ROI配置
  const handleImportConfig = async (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const config = JSON.parse(e.target.result);
        // 验证配置格式
        if (!config.version || !config.tasks) {
          message.error('无效的ROI配置文件格式');
          return;
        }

        // 上传到后端
        uploadROIConfig(config);
      } catch (error) {
        message.error('配置文件解析失败');
      }
    };
    reader.readAsText(file);
    return false;  // 阻止自动上传
  };

  const uploadROIConfig = async (config) => {
    try {
      const response = await fetch('http://127.0.0.1:9090/api/management/roi-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        message.success('ROI配置导入成功');
        loadConfigs();
      }
    } catch (error) {
      message.error('导入失败: ' + error.message);
    }
  };

  // 导出ROI配置
  const handleExportConfig = (config) => {
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `roi_${config.version}_${new Date().toISOString()}.json`;
    a.click();
  };

  return (
    <div>
      <h3>ROI配置管理</h3>
      <Upload beforeUpload={handleImportConfig} showUploadList={false}>
        <Button icon={<UploadOutlined />}>导入ROI配置</Button>
      </Upload>

      <Table
        dataSource={configs}
        columns={[
          { title: '版本', dataIndex: 'version', key: 'version' },
          { title: '布局', dataIndex: 'layout', key: 'layout' },
          { title: '任务数', render: (_, record) => Object.keys(record.tasks || {}).length },
          {
            title: '操作',
            render: (_, record) => (
              <>
                <Button icon={<EditOutlined />} onClick={() => setEditModal({ visible: true, config: record })}>
                  编辑
                </Button>
                <Button icon={<DownloadOutlined />} onClick={() => handleExportConfig(record)}>
                  导出
                </Button>
              </>
            )
          }
        ]}
      />
    </div>
  );
};

export default ROIConfigManager;
```

### 5.2 背景图批量导入工具

**新增**: `scripts/import_background_images.py`

```python
"""
批量导入背景图片
"""
import os
import shutil
from pathlib import Path

def import_backgrounds(source_dir, target_version="v2"):
    """
    从源目录导入背景图到新架构

    Args:
        source_dir: 老项目背景图目录 (包含Q1.jpg, Q2.jpg, ...)
        target_version: 目标版本 (v1/v2)
    """
    project_root = Path(__file__).parent.parent
    target_dir = project_root / "data" / "background_images" / target_version
    target_dir.mkdir(parents=True, exist_ok=True)

    # 查找Q1-Q5图片
    for i in range(1, 6):
        img_name = f"Q{i}.jpg"
        source_file = Path(source_dir) / img_name

        if source_file.exists():
            target_file = target_dir / img_name
            shutil.copy2(source_file, target_file)
            print(f"✅ 已导入: {img_name} -> {target_file}")
        else:
            print(f"⚠️ 未找到: {img_name}")

    print(f"\n✅ 背景图导入完成: {target_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python import_background_images.py <源目录> [版本]")
        print("示例: python import_background_images.py C:/old_project/images v2")
        sys.exit(1)

    source = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "v2"

    import_backgrounds(source, version)
```

---

## 🧪 Phase 6: 测试验证

### 6.1 单元测试

**新增**: `tests/test_roi_analyzer.py`

```python
import unittest
import pandas as pd
from src.web.modules.module01_data_visualization.roi_analyzer import ROIAnalyzer

class TestROIAnalyzer(unittest.TestCase):

    def setUp(self):
        """设置测试ROI配置"""
        self.roi_config = {
            "keywords": [
                {
                    "id": "KW_test_1",
                    "name": "测试区域1",
                    "type": "keyword",
                    "x": 0.2,
                    "y": 0.2,
                    "width": 0.3,
                    "height": 0.3,
                    "color": "#FF0000",
                    "priority": 2
                }
            ],
            "instructions": [],
            "background": [
                {
                    "id": "BG_test",
                    "name": "背景",
                    "type": "background",
                    "x": 0,
                    "y": 0,
                    "width": 1,
                    "height": 1,
                    "color": "#0000FF",
                    "priority": 0
                }
            ]
        }
        self.analyzer = ROIAnalyzer(self.roi_config)

    def test_find_roi_for_point(self):
        """测试ROI点匹配"""
        # 点在KW区域内
        roi_id = self.analyzer.find_roi_for_point(0.3, 0.3)
        self.assertEqual(roi_id, "KW_test_1")

        # 点在背景区域
        roi_id = self.analyzer.find_roi_for_point(0.1, 0.1)
        self.assertEqual(roi_id, "BG_test")

    def test_calculate_stats(self):
        """测试ROI统计计算"""
        # 模拟轨迹: 外部(0.1,0.1) -> KW区域(0.3,0.3) -> 再回外部
        gaze_data = pd.DataFrame([
            {"x": 0.1, "y": 0.1, "timestamp": 0.0},
            {"x": 0.3, "y": 0.3, "timestamp": 0.5},  # 进入KW
            {"x": 0.35, "y": 0.35, "timestamp": 1.0},  # 仍在KW
            {"x": 0.1, "y": 0.1, "timestamp": 1.5},  # 离开KW
        ])

        stats = self.analyzer.calculate_stats(gaze_data)

        # 验证KW区域统计
        kw_stats = stats["KW_test_1"]
        self.assertEqual(kw_stats["entry_count"], 1)  # 进入1次
        self.assertEqual(kw_stats["points_inside"], 2)  # 2个点
        self.assertAlmostEqual(kw_stats["fixation_time"], 1.0, places=2)  # 停留1秒
        self.assertEqual(kw_stats["regression_count"], 0)  # 无回归

if __name__ == '__main__':
    unittest.main()
```

### 6.2 集成测试

**测试场景**:
1. ✅ 加载V1数据 + 增强版ROI配置 => 显示多个KW/INST区域
2. ✅ 背景图正确显示在轨迹下方
3. ✅ ROI统计准确 (与老代码结果对比)
4. ✅ 语言切换后ROI标签更新
5. ✅ 导入新版本ROI配置 => 自动生效

---

## 📋 实施计划

### 时间估算 (总计: ~16小时)

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|---------|--------|
| **Phase 1** | ROI配置增强 | 3h | P0 |
| 1.1 | 设计增强版JSON结构 | 1h | P0 |
| 1.2 | 开发配置转换工具 | 2h | P0 |
| **Phase 2** | 后端服务增强 | 4h | P0 |
| 2.1 | 实现ROI配置加载器 | 1h | P0 |
| 2.2 | 实现ROI分析器 | 2h | P0 |
| 2.3 | 添加API端点 | 1h | P0 |
| **Phase 3** | 前端可视化增强 | 5h | P0 |
| 3.1 | 背景图叠加组件 | 1.5h | P0 |
| 3.2 | 增强版轨迹图组件 | 3.5h | P0 |
| **Phase 4** | 数据流整合 | 2h | P1 |
| 4.1 | Module01页面集成 | 1h | P1 |
| 4.2 | 前端服务扩展 | 1h | P1 |
| **Phase 5** | 配置管理工具 | 3h | P2 |
| 5.1 | ROI配置管理界面 | 2h | P2 |
| 5.2 | 背景图导入工具 | 1h | P2 |
| **Phase 6** | 测试验证 | 2h | P0 |
| 6.1 | 单元测试 | 1h | P0 |
| 6.2 | 集成测试 | 1h | P0 |

### 执行顺序

**阶段1 (核心功能, 4-6小时)**:
1. Phase 1.1-1.2: 转换ROI配置 ✅
2. Phase 2.1-2.2: 后端ROI分析器 ✅
3. Phase 3.1: 背景图叠加 ✅
4. Phase 6.2: 基础测试 ✅

**阶段2 (完善功能, 4-6小时)**:
1. Phase 2.3: ROI统计API ✅
2. Phase 3.2: 增强版图表 ✅
3. Phase 4.1-4.2: 数据流整合 ✅
4. Phase 6.1: 单元测试 ✅

**阶段3 (扩展功能, 2-4小时)**:
1. Phase 5.1-5.2: 配置管理工具 ⏳
2. 性能优化 ⏳
3. 文档完善 ⏳

---

## 🎯 验收标准

### 功能验收

- [ ] ROI配置支持多层次 (KW/INST/BG)
- [ ] 背景图正确显示在轨迹下方
- [ ] ROI统计数据准确 (对比老代码验证)
- [ ] 支持V1/V2两个版本的ROI
- [ ] 支持导入新ROI配置
- [ ] 多语言ROI标签正确切换

### 性能验收

- [ ] ROI统计计算 < 500ms (100个点)
- [ ] 页面渲染流畅 (无卡顿)
- [ ] 背景图加载 < 1s

### 代码质量

- [ ] 单元测试覆盖率 > 80%
- [ ] 无ESLint/Pylint错误
- [ ] 符合现有架构模式

---

## 📚 附录

### A. 坐标系转换参考

```
OpenCV坐标系 (老代码):
  原点: 左上角
  Y轴: 向下为正
  格式: (x_min, y_max, x_max, y_min)

Plotly坐标系 (新代码):
  原点: 左下角
  Y轴: 向上为正
  格式: (x, y, width, height)

转换公式:
  plotly_x = opencv_x_min
  plotly_y = 1 - opencv_y_max
  plotly_width = opencv_x_max - opencv_x_min
  plotly_height = opencv_y_max - opencv_y_min
```

### B. ROI类型说明

| 类型 | 英文 | 优先级 | 颜色 | 用途 |
|------|------|--------|------|------|
| 关键词 | Keywords (KW) | 2 | 红色系 | MMSE任务关键信息区域 |
| 指令 | Instructions (INST) | 1 | 橙色系 | 任务指令文本区域 |
| 背景 | Background (BG) | 0 | 蓝色系 | 全屏背景(兜底匹配) |

### C. 文件清单

**新增文件**:
- `config/roi_v1_enhanced.json` - 增强版ROI配置
- `scripts/convert_old_roi_to_new.py` - 配置转换工具
- `scripts/import_background_images.py` - 背景图导入工具
- `src/web/modules/module01_data_visualization/roi_analyzer.py` - ROI分析器
- `frontend/src/components/Charts/BackgroundImageLayer.jsx` - 背景图组件
- `frontend/src/components/Module00/ROIConfigManager.jsx` - 配置管理器
- `tests/test_roi_analyzer.py` - 单元测试

**修改文件**:
- `src/web/modules/module01_data_visualization/service.py` - 新增 `get_roi_config_enhanced()`
- `src/web/modules/module01_data_visualization/api.py` - 新增 `/roi-stats` 端点
- `frontend/src/components/Charts/GazeTrajectoryChart.jsx` - 集成背景图和增强ROI
- `frontend/src/pages/Module01/Module01.jsx` - 集成新功能
- `frontend/src/services/roiService.js` - 新增增强API调用

---

**🚀 下一步行动**:

1. **立即执行**: Phase 1 配置转换 (生成 `roi_v1_enhanced.json`)
2. **核心开发**: Phase 2 后端ROI分析器
3. **验证测试**: 对比老代码结果，确保统计准确性

**预计第一版完成时间**: 4-6小时
**完整功能上线时间**: 12-16小时
