# 📐 Module11: ROI可视化配置工具 - 开发设计文档

> **模块定位**: 配置管理中心 - ROI可视化编辑器
> **目标用户**: 研究人员、数据分析师
> **核心功能**: 为EyeTracking v2数据创建和编辑ROI配置
> **设计日期**: 2025-10-03

---

## 📋 目录

1. [需求分析](#需求分析)
2. [架构设计](#架构设计)
3. [功能设计](#功能设计)
4. [技术实现](#技术实现)
5. [数据结构](#数据结构)
6. [API设计](#api设计)
7. [前端组件](#前端组件)
8. [开发计划](#开发计划)

---

## 1. 需求分析

### 1.1 功能需求

#### 核心功能
1. **背景图片上传/选择**
   - 支持从v2数据目录选择已导入的背景图
   - 支持直接上传新的背景图片
   - 图片预览和缩放功能

2. **ROI可视化标记**
   - 在背景图上绘制矩形ROI
   - 支持3种ROI类型：
     - **Background ROI** (BG) - 背景区域，优先级0
     - **Instructions ROI** (INST) - 指示语区域，优先级1
     - **Keywords ROI** (KW) - 关键词区域，优先级2
   - 实时显示ROI边界和标签

3. **ROI属性编辑**
   - 设置ROI名称（遵循命名规范）
   - 设置ROI类型（BG/INST/KW）
   - 调整ROI坐标和尺寸
   - 设置优先级和颜色

4. **配置管理**
   - 保存ROI配置为JSON文件
   - 加载已有ROI配置
   - 导出/导入配置
   - 版本管理（v1/v2）

5. **命名规范验证**
   - 自动生成符合规范的ROI ID
   - 验证命名格式
   - 与老版本ROI命名兼容

### 1.2 非功能需求

- **响应性**: 实时预览，操作流畅（<100ms延迟）
- **易用性**: 拖拽式操作，所见即所得
- **兼容性**: 生成的配置与Module01 ROI分析器100%兼容
- **可维护性**: 清晰的代码结构，完整的文档

---

## 2. 架构设计

### 2.1 模块定位

**Module11: 配置管理中心**

```
src/web/modules/
└── module11_config_manager/
    ├── __init__.py
    ├── api.py                  # ROI配置API
    ├── service.py              # ROI配置服务
    ├── roi_editor.py           # ROI编辑器逻辑
    └── validators.py           # ROI命名验证

frontend/src/
├── pages/Module11/
│   └── Module11.jsx            # 配置管理主页
└── components/ROIEditor/
    ├── ROICanvas.jsx           # ROI画布组件
    ├── ROIToolbar.jsx          # 工具栏
    ├── ROIList.jsx             # ROI列表
    └── ROIPropertyPanel.jsx    # 属性面板
```

### 2.2 数据流设计

```
用户操作 → 前端画布 → 坐标转换 → 后端验证 → JSON配置 → 存储
   ↓                                                        ↓
预览更新 ←────────────── 实时同步 ←────────────── Module01使用
```

### 2.3 技术栈选型

**前端**:
- **Canvas绘图**: Konva.js (React Konva) - 高性能2D绘图库
- **或替代方案**: Fabric.js - 功能更丰富
- **文件上传**: Ant Design Upload组件
- **表单管理**: Ant Design Form

**后端**:
- **图片处理**: Pillow (PIL)
- **坐标验证**: 自定义validators
- **文件管理**: Flask send_file

---

## 3. 功能设计

### 3.1 功能模块划分

#### 3.1.1 背景图片管理
```
功能:
1. 从data/background_images/v2/选择已有图片
2. 上传新的背景图片
3. 图片预览（缩放、平移）
4. 图片信息显示（分辨率、文件大小）

界面:
┌─────────────────────────────────┐
│ 背景图片选择                      │
│ ○ 从已有图片选择 [下拉选择框]     │
│ ○ 上传新图片    [上传按钮]       │
│                                  │
│ [图片预览区域]                    │
│  - 缩放: 50% | 100% | 200%       │
│  - 分辨率: 1920x1080             │
└─────────────────────────────────┘
```

#### 3.1.2 ROI绘制工具
```
工具栏:
┌────────────────────────────────────┐
│ [选择] [矩形] [移动] [删除] | 撤销 重做 │
│                                     │
│ ROI类型: ○BG ○INST ●KW             │
│ 显示网格: □  吸附网格: □            │
└────────────────────────────────────┘

绘制模式:
1. 点击"矩形"工具
2. 在画布上拖拽绘制矩形
3. 自动生成ROI名称（可编辑）
4. 添加到ROI列表

交互:
- 双击ROI: 编辑属性
- 右键ROI: 删除/复制
- 拖拽边缘: 调整大小
- 拖拽中心: 移动位置
```

#### 3.1.3 ROI列表管理
```
ROI列表界面:
┌─────────────────────────────────┐
│ ROI列表 (5个)           [+新增]  │
├─────────────────────────────────┤
│ ☑ KW_task1_1 (关键词1)           │
│   类型: Keywords  优先级: 2      │
│   [编辑] [删除] [↑] [↓]          │
├─────────────────────────────────┤
│ ☑ INST_task1_1 (指示语)          │
│   类型: Instructions  优先级: 1  │
│   [编辑] [删除] [↑] [↓]          │
├─────────────────────────────────┤
│ ☑ BG_task1 (背景区域)            │
│   类型: Background  优先级: 0    │
│   [编辑] [删除] [↑] [↓]          │
└─────────────────────────────────┘

操作:
- ☑: 显示/隐藏ROI
- 拖拽调整顺序
- 批量操作（删除、复制）
```

#### 3.1.4 ROI属性面板
```
属性编辑:
┌─────────────────────────────────┐
│ ROI属性编辑                      │
├─────────────────────────────────┤
│ ID:   [KW_task1_1___________]   │
│ 名称: [关键词区域1__________]   │
│ 类型: [Keywords ▼]              │
│                                  │
│ 坐标 (归一化):                   │
│ X: [0.1000] Y: [0.2000]         │
│ 宽: [0.3000] 高: [0.1500]       │
│                                  │
│ 优先级: [2]                      │
│ 颜色: [🎨 #FF6B6B]               │
│                                  │
│ [保存] [取消]                    │
└─────────────────────────────────┘
```

#### 3.1.5 配置导出/导入
```
配置管理:
┌─────────────────────────────────┐
│ 配置管理                         │
├─────────────────────────────────┤
│ 任务ID: [task1_____________]    │
│ 任务名称: [时间定向________]    │
│ 数据版本: [v2 ▼]                │
│                                  │
│ [预览JSON] [保存配置]            │
│ [加载配置] [导出配置]            │
│                                  │
│ 保存路径:                        │
│ data/roi_configs/v2/task1.json  │
└─────────────────────────────────┘
```

---

## 4. 技术实现

### 4.1 坐标系统

#### 4.1.1 坐标系转换
```
图片坐标系 (像素) → 归一化坐标系 [0,1]

转换公式:
normalized_x = pixel_x / image_width
normalized_y = pixel_y / image_height
normalized_w = pixel_w / image_width
normalized_h = pixel_h / image_height

反向转换:
pixel_x = normalized_x * image_width
pixel_y = normalized_y * image_height
```

#### 4.1.2 Plotly坐标系
```
Plotly坐标系特点:
- 原点: 左下角 (0,0)
- X轴: 向右为正
- Y轴: 向上为正

Canvas坐标系:
- 原点: 左上角 (0,0)
- X轴: 向右为正
- Y轴: 向下为正

转换: plotly_y = 1 - canvas_y_normalized
```

### 4.2 ROI命名规范

#### 4.2.1 命名格式
```
格式: {TYPE}_{TASK}_{INDEX}

TYPE:
- KW   : Keywords (关键词)
- INST : Instructions (指示语)
- BG   : Background (背景)

TASK:
- task1, task2, ..., task5 (v2版本)
- q1, q2, ..., q5 (v1版本，兼容)

INDEX:
- 从1开始的序号

示例:
- KW_task1_1     # 任务1的第1个关键词ROI
- INST_task2_1   # 任务2的第1个指示语ROI
- BG_task3       # 任务3的背景ROI（只有1个）
```

#### 4.2.2 验证规则
```python
import re

ROI_PATTERN = r'^(KW|INST|BG)_(task\d+|q\d+)(_\d+)?$'

def validate_roi_id(roi_id: str) -> bool:
    """验证ROI ID格式"""
    if not re.match(ROI_PATTERN, roi_id):
        return False

    # BG类型不应该有索引
    if roi_id.startswith('BG_') and '_' in roi_id.split('_', 2)[-1]:
        return False

    return True

def generate_roi_id(roi_type: str, task_id: str, index: int = None) -> str:
    """自动生成ROI ID"""
    if roi_type == 'background':
        return f"BG_{task_id}"
    elif roi_type == 'instruction':
        return f"INST_{task_id}_{index}"
    elif roi_type == 'keyword':
        return f"KW_{task_id}_{index}"
```

### 4.3 JSON配置结构

#### 4.3.1 配置文件格式
```json
{
  "version": "v2",
  "layout": "eyetracking_v2",
  "coordinate_system": "plotly",
  "task_id": "task1",
  "task_name": "时间定向",
  "background_image": "task1.jpg",
  "image_resolution": {
    "width": 1920,
    "height": 1080
  },
  "regions": {
    "keywords": [
      {
        "id": "KW_task1_1",
        "name": "关键词区域1",
        "type": "keyword",
        "x": 0.1,
        "y": 0.2,
        "width": 0.3,
        "height": 0.15,
        "color": "#FF6B6B",
        "priority": 2
      }
    ],
    "instructions": [
      {
        "id": "INST_task1_1",
        "name": "指示语区域",
        "type": "instruction",
        "x": 0.05,
        "y": 0.05,
        "width": 0.4,
        "height": 0.1,
        "color": "#FFA500",
        "priority": 1
      }
    ],
    "background": [
      {
        "id": "BG_task1",
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
  },
  "metadata": {
    "created_at": "2025-10-03T10:00:00Z",
    "created_by": "user",
    "modified_at": "2025-10-03T10:30:00Z",
    "version": "1.0"
  }
}
```

#### 4.3.2 与v1配置的兼容性
```
v1配置特点:
- task_id: q1, q2, ..., q5
- layout: legacy

v2配置特点:
- task_id: task1, task2, ..., task5
- layout: eyetracking_v2

兼容策略:
1. 后端API自动识别版本
2. 前端根据version字段加载对应配置
3. ROI分析器支持两种命名格式
```

---

## 5. 数据结构

### 5.1 后端数据模型

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ROIRegion:
    """ROI区域数据模型"""
    id: str                    # ROI ID (KW_task1_1)
    name: str                  # 显示名称
    type: str                  # keyword/instruction/background
    x: float                   # 归一化X坐标 [0,1]
    y: float                   # 归一化Y坐标 [0,1]
    width: float               # 归一化宽度 [0,1]
    height: float              # 归一化高度 [0,1]
    color: str                 # 颜色 (#RRGGBB)
    priority: int              # 优先级 (0-2)

@dataclass
class ROIConfig:
    """ROI配置数据模型"""
    version: str               # v1/v2
    layout: str                # legacy/eyetracking_v2
    coordinate_system: str     # plotly
    task_id: str              # task1/q1
    task_name: str            # 任务名称
    background_image: str     # 背景图文件名
    image_resolution: Dict    # {width, height}
    regions: Dict[str, List[ROIRegion]]  # {keywords, instructions, background}
    metadata: Dict            # 元数据

@dataclass
class ROIEditorState:
    """ROI编辑器状态"""
    current_tool: str         # select/rect/move/delete
    selected_roi: Optional[str]  # 当前选中的ROI ID
    roi_type: str             # 当前绘制的ROI类型
    show_grid: bool           # 是否显示网格
    snap_to_grid: bool        # 是否吸附网格
    zoom_level: float         # 缩放级别
```

### 5.2 前端数据模型

```typescript
// TypeScript类型定义（可选，用于代码提示）

interface ROIRegion {
  id: string;
  name: string;
  type: 'keyword' | 'instruction' | 'background';
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  priority: number;
}

interface ROIConfig {
  version: string;
  layout: string;
  coordinate_system: string;
  task_id: string;
  task_name: string;
  background_image: string;
  image_resolution: {
    width: number;
    height: number;
  };
  regions: {
    keywords: ROIRegion[];
    instructions: ROIRegion[];
    background: ROIRegion[];
  };
  metadata: {
    created_at: string;
    created_by: string;
    modified_at: string;
    version: string;
  };
}
```

---

## 6. API设计

### 6.1 后端API端点

#### 6.1.1 背景图片管理
```python
# 获取可用背景图列表
GET /api/config/background-images
Query: ?version=v2
Response: {
  "success": true,
  "data": [
    {
      "filename": "task1.jpg",
      "path": "/static/background_images/v2/task1.jpg",
      "size": 245680,
      "resolution": {"width": 1920, "height": 1080}
    }
  ]
}

# 上传新背景图
POST /api/config/background-images
Body: FormData with file
Response: {
  "success": true,
  "data": {
    "filename": "task1.jpg",
    "path": "/static/background_images/v2/task1.jpg"
  }
}
```

#### 6.1.2 ROI配置管理
```python
# 获取ROI配置
GET /api/config/roi
Query: ?version=v2&task=task1
Response: {
  "success": true,
  "data": { /* ROIConfig JSON */ }
}

# 保存ROI配置
POST /api/config/roi
Body: {
  "version": "v2",
  "task_id": "task1",
  "config": { /* ROIConfig JSON */ }
}
Response: {
  "success": true,
  "data": {
    "config_path": "data/roi_configs/v2/task1.json"
  }
}

# 验证ROI配置
POST /api/config/roi/validate
Body: {
  "config": { /* ROIConfig JSON */ }
}
Response: {
  "success": true,
  "data": {
    "valid": true,
    "errors": [],
    "warnings": ["ROI_task1_1命名不规范"]
  }
}

# 导出ROI配置
GET /api/config/roi/export
Query: ?version=v2&task=task1&format=json
Response: File download (JSON)
```

#### 6.1.3 ROI命名验证
```python
# 验证ROI ID
POST /api/config/roi/validate-id
Body: {
  "roi_id": "KW_task1_1",
  "roi_type": "keyword",
  "task_id": "task1"
}
Response: {
  "success": true,
  "data": {
    "valid": true,
    "message": "ROI ID格式正确"
  }
}

# 生成ROI ID
POST /api/config/roi/generate-id
Body: {
  "roi_type": "keyword",
  "task_id": "task1",
  "existing_ids": ["KW_task1_1", "KW_task1_2"]
}
Response: {
  "success": true,
  "data": {
    "roi_id": "KW_task1_3"
  }
}
```

### 6.2 API实现示例

```python
# src/web/modules/module11_config_manager/api.py

from flask import Blueprint, request, jsonify, send_file
from .service import ROIConfigService
from .validators import ROIValidator

m11_bp = Blueprint('module11', __name__, url_prefix='/api/config')
roi_service = ROIConfigService()
roi_validator = ROIValidator()

@m11_bp.route('/background-images', methods=['GET'])
def get_background_images():
    """获取背景图列表"""
    version = request.args.get('version', 'v2')
    images = roi_service.list_background_images(version)
    return jsonify({"success": True, "data": images})

@m11_bp.route('/background-images', methods=['POST'])
def upload_background_image():
    """上传背景图"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file"}), 400

    file = request.files['file']
    version = request.form.get('version', 'v2')
    task_id = request.form.get('task_id')

    result = roi_service.save_background_image(file, version, task_id)
    return jsonify({"success": True, "data": result})

@m11_bp.route('/roi', methods=['GET'])
def get_roi_config():
    """获取ROI配置"""
    version = request.args.get('version', 'v2')
    task = request.args.get('task')

    config = roi_service.load_roi_config(version, task)
    return jsonify({"success": True, "data": config})

@m11_bp.route('/roi', methods=['POST'])
def save_roi_config():
    """保存ROI配置"""
    data = request.get_json()
    version = data.get('version')
    task_id = data.get('task_id')
    config = data.get('config')

    # 验证配置
    validation = roi_validator.validate_config(config)
    if not validation['valid']:
        return jsonify({"success": False, "errors": validation['errors']}), 400

    # 保存配置
    result = roi_service.save_roi_config(version, task_id, config)
    return jsonify({"success": True, "data": result})

@m11_bp.route('/roi/validate-id', methods=['POST'])
def validate_roi_id():
    """验证ROI ID"""
    data = request.get_json()
    roi_id = data.get('roi_id')
    roi_type = data.get('roi_type')
    task_id = data.get('task_id')

    result = roi_validator.validate_roi_id(roi_id, roi_type, task_id)
    return jsonify({"success": True, "data": result})
```

---

## 7. 前端组件

### 7.1 组件结构

```
frontend/src/components/ROIEditor/
├── ROIEditor.jsx              # 主容器组件
├── ROICanvas.jsx              # Canvas画布（Konva.js）
├── ROIToolbar.jsx             # 工具栏
├── ROIList.jsx                # ROI列表
├── ROIPropertyPanel.jsx       # 属性编辑面板
├── BackgroundImageSelector.jsx # 背景图选择器
└── ROIEditor.css              # 样式文件
```

### 7.2 核心组件实现

#### 7.2.1 ROICanvas组件（Konva.js）
```jsx
import React, { useState, useRef } from 'react';
import { Stage, Layer, Image, Rect, Text } from 'react-konva';
import useImage from 'use-image';

const ROICanvas = ({
  backgroundImage,
  rois,
  onROICreate,
  onROIUpdate,
  selectedROI
}) => {
  const [image] = useImage(backgroundImage);
  const [isDrawing, setIsDrawing] = useState(false);
  const [newRect, setNewRect] = useState(null);

  const handleMouseDown = (e) => {
    if (currentTool !== 'rect') return;

    const pos = e.target.getStage().getPointerPosition();
    setIsDrawing(true);
    setNewRect({
      x: pos.x,
      y: pos.y,
      width: 0,
      height: 0
    });
  };

  const handleMouseMove = (e) => {
    if (!isDrawing) return;

    const pos = e.target.getStage().getPointerPosition();
    setNewRect({
      ...newRect,
      width: pos.x - newRect.x,
      height: pos.y - newRect.y
    });
  };

  const handleMouseUp = () => {
    if (!isDrawing) return;
    setIsDrawing(false);

    // 转换为归一化坐标
    const normalized = normalizeRect(newRect, image.width, image.height);
    onROICreate(normalized);
    setNewRect(null);
  };

  return (
    <Stage
      width={800}
      height={600}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      <Layer>
        {/* 背景图 */}
        <Image image={image} />

        {/* 已有ROI */}
        {rois.map(roi => (
          <Rect
            key={roi.id}
            x={roi.x * image.width}
            y={roi.y * image.height}
            width={roi.width * image.width}
            height={roi.height * image.height}
            stroke={roi.color}
            strokeWidth={2}
            fill={`${roi.color}20`}
            draggable
            onDragEnd={(e) => onROIUpdate(roi.id, {
              x: e.target.x() / image.width,
              y: e.target.y() / image.height
            })}
          />
        ))}

        {/* 正在绘制的ROI */}
        {newRect && (
          <Rect
            {...newRect}
            stroke="#00ff00"
            strokeWidth={2}
            fill="rgba(0,255,0,0.1)"
          />
        )}
      </Layer>
    </Stage>
  );
};
```

#### 7.2.2 ROIToolbar组件
```jsx
const ROIToolbar = ({
  currentTool,
  onToolChange,
  roiType,
  onROITypeChange
}) => {
  return (
    <div className="roi-toolbar">
      <Space>
        {/* 工具按钮 */}
        <Radio.Group value={currentTool} onChange={(e) => onToolChange(e.target.value)}>
          <Radio.Button value="select">
            <SelectOutlined /> 选择
          </Radio.Button>
          <Radio.Button value="rect">
            <BorderOutlined /> 矩形
          </Radio.Button>
          <Radio.Button value="move">
            <DragOutlined /> 移动
          </Radio.Button>
          <Radio.Button value="delete">
            <DeleteOutlined /> 删除
          </Radio.Button>
        </Radio.Group>

        <Divider type="vertical" />

        {/* ROI类型 */}
        <Radio.Group value={roiType} onChange={(e) => onROITypeChange(e.target.value)}>
          <Radio.Button value="background">BG</Radio.Button>
          <Radio.Button value="instruction">INST</Radio.Button>
          <Radio.Button value="keyword">KW</Radio.Button>
        </Radio.Group>

        <Divider type="vertical" />

        {/* 其他选项 */}
        <Checkbox>显示网格</Checkbox>
        <Checkbox>吸附网格</Checkbox>
      </Space>
    </div>
  );
};
```

#### 7.2.3 ROIList组件
```jsx
const ROIList = ({ rois, onSelect, onDelete, onToggleVisibility }) => {
  return (
    <Card title="ROI列表" size="small">
      <List
        dataSource={rois}
        renderItem={(roi) => (
          <List.Item
            actions={[
              <Button size="small" onClick={() => onSelect(roi.id)}>编辑</Button>,
              <Button size="small" danger onClick={() => onDelete(roi.id)}>删除</Button>
            ]}
          >
            <List.Item.Meta
              avatar={
                <Checkbox
                  checked={roi.visible}
                  onChange={(e) => onToggleVisibility(roi.id, e.target.checked)}
                />
              }
              title={
                <Space>
                  <Tag color={getTypeColor(roi.type)}>{roi.type.toUpperCase()}</Tag>
                  {roi.name}
                </Space>
              }
              description={`ID: ${roi.id} | 优先级: ${roi.priority}`}
            />
          </List.Item>
        )}
      />
    </Card>
  );
};
```

---

## 8. 开发计划

### 8.1 阶段划分

#### **阶段1: 基础架构（2-3天）**
- ✅ 创建Module11目录结构
- ✅ 后端API框架（api.py, service.py）
- ✅ 前端页面框架（Module11.jsx）
- ✅ 路由配置

#### **阶段2: 背景图管理（1-2天）**
- ✅ 背景图上传功能
- ✅ 背景图选择器
- ✅ 图片预览和信息显示
- ✅ 图片存储管理

#### **阶段3: ROI绘制功能（3-4天）**
- ✅ Konva.js画布集成
- ✅ 矩形绘制工具
- ✅ ROI拖拽和调整
- ✅ 坐标系转换

#### **阶段4: ROI管理功能（2-3天）**
- ✅ ROI列表显示
- ✅ ROI属性编辑
- ✅ ROI命名验证
- ✅ ROI增删改查

#### **阶段5: 配置保存/加载（2-3天）**
- ✅ JSON配置生成
- ✅ 配置保存/加载
- ✅ 配置导出/导入
- ✅ 版本管理（v1/v2）

#### **阶段6: 测试和优化（2-3天）**
- ✅ 单元测试
- ✅ 集成测试
- ✅ 性能优化
- ✅ 用户体验优化

**总计**: 12-18天（约2-3周）

### 8.2 开发优先级

#### P0 (核心功能)
1. 背景图上传/选择
2. ROI矩形绘制
3. 基础属性编辑
4. 配置保存/加载

#### P1 (重要功能)
5. ROI命名自动生成
6. 坐标系验证
7. ROI列表管理
8. 配置导出

#### P2 (优化功能)
9. 网格显示/吸附
10. 撤销/重做
11. 批量操作
12. 快捷键支持

### 8.3 技术难点

#### 难点1: 坐标系转换
- **问题**: Canvas坐标 → 归一化坐标 → Plotly坐标
- **方案**: 封装转换工具函数，统一处理

#### 难点2: ROI命名规范
- **问题**: 自动生成符合规范的ROI ID
- **方案**: 正则验证 + 自增索引管理

#### 难点3: 实时预览性能
- **问题**: 大量ROI时渲染性能下降
- **方案**: 虚拟化渲染 + 防抖优化

---

## 9. 使用示例

### 9.1 用户操作流程

```
1. 进入Module11配置管理中心
   └─> 点击"ROI配置编辑器"

2. 选择/上传背景图
   └─> 从v2目录选择task1.jpg
   └─> 或上传新图片

3. 绘制ROI
   ├─> 选择"矩形"工具
   ├─> 选择ROI类型（KW）
   ├─> 在图片上拖拽绘制矩形
   └─> 自动生成ID: KW_task1_1

4. 编辑ROI属性
   ├─> 双击ROI打开属性面板
   ├─> 修改名称、颜色、优先级
   └─> 保存

5. 保存配置
   ├─> 点击"保存配置"按钮
   ├─> 选择任务ID: task1
   ├─> 确认保存路径
   └─> 保存为JSON文件

6. 在Module01中使用
   └─> Module01自动加载ROI配置
   └─> 显示ROI叠加和统计
```

### 9.2 配置文件示例

**保存路径**: `data/roi_configs/v2/task1.json`

```json
{
  "version": "v2",
  "layout": "eyetracking_v2",
  "coordinate_system": "plotly",
  "task_id": "task1",
  "task_name": "时间定向",
  "background_image": "task1.jpg",
  "image_resolution": {
    "width": 1920,
    "height": 1080
  },
  "regions": {
    "keywords": [
      {
        "id": "KW_task1_1",
        "name": "年份关键词",
        "type": "keyword",
        "x": 0.1,
        "y": 0.4,
        "width": 0.2,
        "height": 0.15,
        "color": "#FF6B6B",
        "priority": 2
      },
      {
        "id": "KW_task1_2",
        "name": "月份关键词",
        "type": "keyword",
        "x": 0.35,
        "y": 0.4,
        "width": 0.2,
        "height": 0.15,
        "color": "#FF6B6B",
        "priority": 2
      }
    ],
    "instructions": [
      {
        "id": "INST_task1_1",
        "name": "任务指示语",
        "type": "instruction",
        "x": 0.05,
        "y": 0.05,
        "width": 0.5,
        "height": 0.1,
        "color": "#FFA500",
        "priority": 1
      }
    ],
    "background": [
      {
        "id": "BG_task1",
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
  },
  "metadata": {
    "created_at": "2025-10-03T10:00:00Z",
    "created_by": "admin",
    "modified_at": "2025-10-03T10:30:00Z",
    "version": "1.0"
  }
}
```

---

## 10. 与现有模块的集成

### 10.1 与Module00的关系
```
Module00 (数据管理)
└─> 导入v2背景图片
    └─> 保存到 data/background_images/v2/

Module11 (配置管理) ⭐
└─> 从v2目录选择背景图
    └─> 绘制ROI并保存配置
        └─> 保存到 data/roi_configs/v2/

配置文件 + 背景图 → Module01使用
```

### 10.2 与Module01的关系
```
Module11生成配置 → Module01加载配置

Module01需要修改:
1. ROI配置加载逻辑
   - 优先加载v2配置（如果存在）
   - 回退到v1配置

2. 配置路径
   - v2: data/roi_configs/v2/{task_id}.json
   - v1: data/roi_configs/v1/{task_id}.json
```

### 10.3 数据流图
```
┌─────────────┐
│  Module00   │ 导入背景图
│ 数据管理    │────────────┐
└─────────────┘            │
                           ↓
                    ┌──────────────┐
                    │ background_  │
                    │  images/v2/  │
                    └──────────────┘
                           │
                           │ 选择
                           ↓
                    ┌─────────────┐
                    │  Module11   │ 创建ROI配置
                    │ 配置管理    │────────────┐
                    └─────────────┘            │
                                               ↓
                                        ┌─────────────┐
                                        │ roi_configs │
                                        │    /v2/     │
                                        └─────────────┘
                                               │
                                               │ 加载
                                               ↓
                                        ┌─────────────┐
                                        │  Module01   │
                                        │ 数据可视化  │
                                        └─────────────┘
```

---

## 11. 验收标准

### 11.1 功能验收
- [ ] 可以上传和选择背景图片
- [ ] 可以在图片上绘制矩形ROI
- [ ] 支持3种ROI类型（BG/INST/KW）
- [ ] ROI命名符合规范（自动验证）
- [ ] 可以编辑ROI属性（名称、颜色、优先级）
- [ ] 可以保存配置为JSON文件
- [ ] 可以加载已有配置
- [ ] 可以导出/导入配置
- [ ] 生成的配置与Module01 100%兼容

### 11.2 性能验收
- [ ] 绘制操作响应时间 < 100ms
- [ ] 配置保存时间 < 500ms
- [ ] 支持至少20个ROI无性能问题
- [ ] 图片加载时间 < 2s

### 11.3 代码质量
- [ ] 单元测试覆盖率 > 80%
- [ ] 无ESLint/Pylint错误
- [ ] 代码符合项目规范
- [ ] 完整的文档注释

---

## 12. 文档和培训

### 12.1 用户手册
- [ ] ROI配置编辑器使用指南
- [ ] 命名规范说明
- [ ] 常见问题解答
- [ ] 视频教程

### 12.2 开发文档
- [ ] API文档（Swagger）
- [ ] 组件文档（Storybook）
- [ ] 数据结构说明
- [ ] 架构设计文档

---

## 附录

### A. 技术选型对比

| 方案 | Konva.js | Fabric.js | SVG + D3.js |
|------|----------|-----------|-------------|
| 学习曲线 | 低 | 中 | 高 |
| 性能 | 高 | 中 | 中 |
| 功能丰富度 | 中 | 高 | 高 |
| React集成 | 优秀 | 一般 | 一般 |
| **推荐** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |

**选择: Konva.js**
- React集成最好（react-konva）
- 性能优秀
- API简洁易用
- 活跃维护

### B. 参考资源
- Konva.js官方文档: https://konvajs.org/
- React Konva: https://github.com/konvajs/react-konva
- ROI分析器源码: `src/web/modules/module01_data_visualization/roi_analyzer.py`
- 现有ROI配置: `config/roi_v1_enhanced.json`

---

**文档版本**: 1.0
**最后更新**: 2025-10-03
**维护人**: AI Assistant
**审核状态**: 待审核
