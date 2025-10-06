# ROI坐标系统修复报告

## 📋 问题总结

**日期**: 2025-10-03
**修复内容**: ModuleEX加载v1 ROI报错 + Module1 ROI可视化上下颠倒

---

## 🐛 问题1: ModuleEX加载v1 ROI时崩溃

### 错误信息
```
Uncaught TypeError: Cannot read properties of undefined (reading '0')
    at ROICanvas.jsx:75:21
```

### 根本原因
- **v1 ROI数据格式**: 使用 `{x, y, width, height}` 字段
- **v2 ROI数据格式**: 使用 `normalized_coords: [x, y, w, h]` 数组
- **ROICanvas.jsx**: 只支持数组格式，尝试访问 `roi.normalized_coords[0]` 导致报错

### 数据格式对比

**v1格式** (`data/roi_configs/v1/q1_roi.json`):
```json
{
  "regions": {
    "background": [{
      "id": "q1_time_orientation",
      "x": 0.1,
      "y": 0.2,
      "width": 0.3,
      "height": 0.2
    }]
  }
}
```

**v2格式** (`data/roi_configs/v2/task1_roi.json`):
```json
{
  "regions": {
    "keywords": [{
      "id": "KW_task1_1",
      "normalized_coords": [0.0923, 0.45, 0.3318, 0.15]
    }]
  }
}
```

### 修复方案

**文件**: `frontend/src/components/ModuleEX/ROICanvas.jsx`

**修改位置1** - 绘制ROI (第69-92行):
```javascript
// 修复前
const x = roi.normalized_coords[0] * width;
const y = roi.normalized_coords[1] * height;
const w = roi.normalized_coords[2] * width;
const h = roi.normalized_coords[3] * height;

// 修复后 - 兼容两种格式
let x, y, w, h;
if (roi.normalized_coords && Array.isArray(roi.normalized_coords)) {
  // 新格式: normalized_coords数组
  x = roi.normalized_coords[0] * width;
  y = roi.normalized_coords[1] * height;
  w = roi.normalized_coords[2] * width;
  h = roi.normalized_coords[3] * height;
} else if (roi.x !== undefined && roi.y !== undefined) {
  // 旧格式: x/y/width/height字段
  x = roi.x * width;
  y = roi.y * height;
  w = (roi.width || 0) * width;
  h = (roi.height || 0) * height;
} else {
  console.warn('Invalid ROI format:', roi);
  return;
}
```

**修改位置2** - 点击选择ROI (第217-234行):
```javascript
// 同样的兼容性逻辑应用于handleCanvasClick
for (let i = allRois.length - 1; i >= 0; i--) {
  const roi = allRois[i];

  let roiX, roiY, roiW, roiH;
  if (roi.normalized_coords && Array.isArray(roi.normalized_coords)) {
    roiX = roi.normalized_coords[0] * width;
    roiY = roi.normalized_coords[1] * height;
    roiW = roi.normalized_coords[2] * width;
    roiH = roi.normalized_coords[3] * height;
  } else if (roi.x !== undefined && roi.y !== undefined) {
    roiX = roi.x * width;
    roiY = roi.y * height;
    roiW = (roi.width || 0) * width;
    roiH = (roi.height || 0) * height;
  } else {
    continue;
  }

  if (x >= roiX && x <= roiX + roiW && y >= roiY && y <= roiY + roiH) {
    onSelectRoi(roi);
    return;
  }
}
```

---

## 🐛 问题2: Module1 ROI可视化上下颠倒

### 问题描述
- Module1中显示的ROI位置与实际位置上下颠倒
- v1的ROI信息是完整的，但在Plotly图表中显示位置错误

### 根本原因

**坐标系差异**:
- **ROI坐标系**: Y轴从上到下（0在顶部，1在底部）- 类似屏幕坐标系
- **Plotly坐标系**: Y轴从下到上（0在底部，1在顶部）- 类似数学坐标系

```
ROI坐标系 (0,0在左上)        Plotly坐标系 (0,0在左下)
┌─────────────┐              ┌─────────────┐
│(0,0)        │              │      (0,1)  │
│             │              │             │
│      ROI    │              │      ROI    │
│             │              │             │
│        (1,1)│              │(0,0)        │
└─────────────┘              └─────────────┘
```

### 修复方案

**文件**: `frontend/src/components/Charts/GazeTrajectoryChartEnhanced.jsx`

**修改位置** - Y轴翻转公式 (第186-216行):

```javascript
// 修复前 - 直接使用ROI坐标
baseLayout.shapes = allRegions.map(roi => ({
  type: 'rect',
  x0: roi.x,
  y0: roi.y,
  x1: roi.x + roi.width,
  y1: roi.y + roi.height,
  // ...
}));

// 修复后 - Y轴翻转：1-y
baseLayout.shapes = allRegions.map(roi => ({
  type: 'rect',
  x0: roi.x,
  y0: 1 - roi.y - roi.height,  // Y轴翻转
  x1: roi.x + roi.width,
  y1: 1 - roi.y,               // Y轴翻转
  // ...
}));

// 标签也需要翻转
baseLayout.annotations = allRegions.map(roi => ({
  x: roi.x + roi.width / 2,
  y: 1 - roi.y - roi.height / 2,  // Y轴翻转
  // ...
}));
```

### Y轴翻转数学推导

对于ROI矩形：
- ROI顶部Y坐标: `y`
- ROI底部Y坐标: `y + height`

翻转到Plotly坐标系：
- Plotly底部Y坐标: `1 - (y + height)` = `1 - y - height`
- Plotly顶部Y坐标: `1 - y`

因此：
- `y0 = 1 - y - height`（矩形底部）
- `y1 = 1 - y`（矩形顶部）
- 标签中心: `y = 1 - y - height/2`

---

## ✅ 修复验证

### 测试用例

**测试1**: ModuleEX加载v1 ROI
```
✅ 不再报错 "Cannot read properties of undefined"
✅ 正确显示v1的background区域
✅ 可以点击选择v1的ROI
```

**测试2**: ModuleEX加载v2 ROI
```
✅ 正常显示keywords/instructions/background
✅ normalized_coords格式正常工作
```

**测试3**: Module1显示ROI
```
✅ ROI位置正确（不再上下颠倒）
✅ 标签位置准确
✅ ROI框与背景图片对齐
```

---

## 📊 影响范围

### 修改的文件
1. ✅ `frontend/src/components/ModuleEX/ROICanvas.jsx`
   - 添加坐标格式检测和兼容逻辑
   - 支持v1和v2两种数据格式

2. ✅ `frontend/src/components/Charts/GazeTrajectoryChartEnhanced.jsx`
   - Y轴翻转修复
   - 正确映射ROI到Plotly坐标系

### 受益功能
- ✅ ModuleEX: 可以正常加载和编辑v1的ROI配置
- ✅ Module1: ROI可视化位置准确
- ✅ 数据互通: v1和v2 ROI在两个模块间正常工作

---

## 🔍 技术要点

### 1. 坐标格式兼容性模式

```javascript
// 通用的坐标读取函数
function getROICoords(roi, width, height) {
  if (roi.normalized_coords && Array.isArray(roi.normalized_coords)) {
    return {
      x: roi.normalized_coords[0] * width,
      y: roi.normalized_coords[1] * height,
      w: roi.normalized_coords[2] * width,
      h: roi.normalized_coords[3] * height
    };
  } else if (roi.x !== undefined) {
    return {
      x: roi.x * width,
      y: roi.y * height,
      w: (roi.width || 0) * width,
      h: (roi.height || 0) * height
    };
  }
  return null;
}
```

### 2. Y轴坐标系转换公式

```javascript
// ROI坐标 -> Plotly坐标
function flipY(roiY, roiHeight) {
  return {
    plotlyY0: 1 - roiY - roiHeight,  // 底部
    plotlyY1: 1 - roiY,              // 顶部
    plotlyYCenter: 1 - roiY - roiHeight / 2  // 中心
  };
}
```

---

## 🎯 遗留问题

### v1数据不完整
- **现象**: v1只有background区域，缺少keywords和instructions
- **原因**: 原始`config/roi_v1.json`可能数据不全，或迁移时只提取了background
- **建议**: 手动补充v1的完整ROI区域数据

### 后续优化
1. 统一坐标格式为`normalized_coords`
2. 提供v1到v2的自动转换工具
3. 添加坐标系可视化调试工具

---

## 📝 相关文档

- [Module01与ModuleEX集成完成报告](MODULE01_MODULEEX_INTEGRATION_COMPLETE.md)
- [ROI数据格式规范](MODULE01_ROI_ENHANCEMENT_PLAN.md)

---

**修复完成时间**: 2025-10-03
**状态**: ✅ 已验证通过
