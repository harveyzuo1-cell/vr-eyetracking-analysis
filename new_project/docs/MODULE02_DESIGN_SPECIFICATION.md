# Module02 功能设计文档
## VR眼球追踪数据分析平台 - 数据预处理与质量控制模块

---

## 📋 文档信息

**模块名称**: Module02 - 数据预处理与质量控制
**版本**: v1.0
**编制日期**: 2025-10-05
**编制人**: AI Assistant
**状态**: 设计阶段

---

## 🎯 模块定位与设计理念

### 1.1 模块定位

Module02 位于整个数据处理流程的**第二阶段**，承担"数据清洗与质量控制"的核心职责：

```
数据流程:
Module00 (数据导入)
    ↓
Module01 (数据可视化查看原始数据)
    ↓
Module02 (数据预处理与质量控制) ← 当前模块
    ↓
Module03 (RQA分析)
    ↓
Module04+ (后续分析模块)
```

### 1.2 设计理念

**基于 Module00、Module01、ModuleEX 的架构规范**：

#### 借鉴 Module01 的成功经验：
- ✅ **清晰的数据选择流程**: 版本 → 组别 → 受试者 → 任务
- ✅ **实时数据加载与预览**: 快速响应的数据显示
- ✅ **统计信息面板**: 直观展示数据质量指标
- ✅ **分标签页组织**: 不同功能独立Tab展示

#### 借鉴 ModuleEX 的交互设计：
- ✅ **参数配置面板**: 侧边栏实时参数调整
- ✅ **可视化预览**: 实时显示处理前后对比
- ✅ **保存/加载功能**: 便捷的配置保存和读取

#### 符合整体架构规范：
- ✅ **前后端分离**: React前端 + Flask后端API
- ✅ **模块化设计**: 组件独立、职责清晰
- ✅ **配置驱动**: 所有参数可配置、可保存
- ✅ **数据版本支持**: 同时支持V1和V2数据格式

---

## 🏗️ 核心功能设计

### 2.1 功能概述

Module02 提供**6大核心功能**：

1. **受试者信息管理** ⭐ 新增
   - 查看受试者基本信息
   - 添加/编辑人口学数据（性别、年龄、受教育程度）
   - 批量导入受试者信息
   - 信息完整性检查

2. **MMSE数据管理** ⭐ 新增
   - 查看MMSE总分及各子问题得分
   - 添加/编辑MMSE评分数据
   - 批量导入MMSE数据
   - MMSE数据与受试者关联

3. **数据质量检测**
   - 缺失值检测
   - 异常值检测
   - 数据范围检查
   - 采样率分析

4. **数据清洗处理**
   - 缺失值填充（插值/删除/前向填充）
   - 异常值处理（3σ法则/IQR法）
   - 坐标范围裁剪
   - 时间戳规范化

5. **数据平滑滤波**
   - 移动平均滤波
   - 高斯滤波
   - 中值滤波
   - Savitzky-Golay滤波

6. **处理结果导出**
   - 预处理数据保存
   - 质量报告生成
   - 处理前后对比
   - 批量处理支持

---

## 📐 界面设计

### 3.1 页面布局

采用 **Module01 相同的布局结构**，保持用户体验一致性：

```
┌─────────────────────────────────────────────────────────────┐
│  📌 模块标题: Module02 - 数据预处理与质量控制               │
│  描述: 对眼球追踪数据进行质量检测、清洗和平滑处理           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🎯 数据选择                                                │
│  [数据版本: V1/V2/全部] [组别] [受试者] [任务] [加载数据]  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📊 数据质量诊断                                            │
│  [总数据点] [缺失值] [异常值] [质量评分] [采样率]          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔧 处理配置与可视化 (Tabs)                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Tab 1: 质量检测  Tab 2: 数据清洗  Tab 3: 数据平滑 │    │
│  ├────────────────────────────────────────────────────┤    │
│  │                                                    │    │
│  │  ┌──────────────────┐  ┌─────────────────────┐   │    │
│  │  │  参数配置面板    │  │   处理预览图表      │   │    │
│  │  │                  │  │                     │   │    │
│  │  │  [参数1]         │  │   [对比图/统计图]   │   │    │
│  │  │  [参数2]         │  │                     │   │    │
│  │  │  [参数3]         │  │                     │   │    │
│  │  │                  │  │                     │   │    │
│  │  │  [应用预处理]    │  │                     │   │    │
│  │  └──────────────────┘  └─────────────────────┘   │    │
│  │                                                    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  💾 处理结果                                                │
│  [保存预处理数据] [导出质量报告] [批量处理配置]            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Tab页面详细设计

#### **Tab 1: 质量检测**

**左侧参数面板**:
```jsx
┌─────────────────────────┐
│ 质量检测配置            │
├─────────────────────────┤
│ □ 缺失值检测            │
│   显示缺失数据点位置     │
│                         │
│ □ 异常值检测            │
│   方法: [3σ法则 ▼]     │
│   阈值: [3.0]          │
│                         │
│ □ 坐标范围检查          │
│   X范围: [0-1]         │
│   Y范围: [0-1]         │
│                         │
│ □ 采样率分析            │
│   期望采样率: [60Hz]    │
│   误差容忍: [±5Hz]      │
│                         │
│ [执行检测]              │
└─────────────────────────┘
```

**右侧可视化**:
- 轨迹图（标注异常点和缺失段）
- 质量分布柱状图
- 时间序列图（X/Y坐标随时间变化）
- 采样率波动图

#### **Tab 2: 数据清洗**

**左侧参数面板**:
```jsx
┌─────────────────────────┐
│ 数据清洗配置            │
├─────────────────────────┤
│ 1. 缺失值处理           │
│   方法: [线性插值 ▼]   │
│   选项:                 │
│     ○ 线性插值          │
│     ○ 前向填充          │
│     ○ 删除缺失行        │
│                         │
│ 2. 异常值处理           │
│   方法: [3σ替换 ▼]     │
│   阈值: [3.0]          │
│   选项:                 │
│     ○ 插值替换          │
│     ○ 删除              │
│     ○ 保留标记          │
│                         │
│ 3. 坐标裁剪             │
│   □ 启用坐标裁剪        │
│   范围: X[0-1] Y[0-1]  │
│                         │
│ 4. 时间规范化           │
│   □ 重采样到固定频率    │
│   目标频率: [60Hz]      │
│                         │
│ [应用清洗] [重置]       │
└─────────────────────────┘
```

**右侧可视化**:
- 清洗前后对比图（双轨迹叠加）
- 处理点统计表
- 清洗效果评分

#### **Tab 3: 数据平滑**

**左侧参数面板**:
```jsx
┌─────────────────────────┐
│ 数据平滑配置            │
├─────────────────────────┤
│ 平滑方法:               │
│   ○ 移动平均滤波        │
│      窗口大小: [5]      │
│                         │
│   ○ 高斯滤波            │
│      σ值: [1.5]        │
│      窗口大小: [9]      │
│                         │
│   ○ 中值滤波            │
│      窗口大小: [5]      │
│                         │
│   ○ Savitzky-Golay     │
│      窗口大小: [11]     │
│      多项式阶数: [3]    │
│                         │
│ 平滑强度预设:           │
│   [轻度] [中度] [强度]  │
│                         │
│ □ 仅平滑X坐标           │
│ □ 仅平滑Y坐标           │
│ ☑ 平滑X和Y坐标          │
│                         │
│ [应用平滑] [对比预览]   │
└─────────────────────────┘
```

**右侧可视化**:
- 平滑前后轨迹对比
- 频谱分析图（显示滤波效果）
- 速度曲线对比（原始vs平滑）

---

## 🔌 后端API设计

### 4.1 API端点规划

遵循 **RESTful 架构**，与 Module01 保持一致的命名规范：

```python
# 基础路径: /api/m02/

# 1. 数据加载
GET  /api/m02/load-data
参数: group, subject_id, task, version
返回: 原始数据 + 基础统计信息

# 2. 质量检测
POST /api/m02/quality-check
输入: {data, config: {check_missing, check_outliers, check_range, check_sampling}}
返回: {quality_report, issues_found, quality_score}

# 3. 数据清洗
POST /api/m02/clean-data
输入: {data, config: {missing_method, outlier_method, ...}}
返回: {cleaned_data, cleaning_report, removed_points}

# 4. 数据平滑
POST /api/m02/smooth-data
输入: {data, config: {method, window_size, sigma, ...}}
返回: {smoothed_data, smoothing_stats}

# 5. 完整预处理流程
POST /api/m02/preprocess
输入: {group, subject_id, task, pipeline_config}
返回: {preprocessed_data, pipeline_report, saved_path}

# 6. 保存预处理结果
POST /api/m02/save-preprocessed
输入: {group, subject_id, task, data, metadata}
返回: {success, file_path, metadata_path}

# 7. 批量处理
POST /api/m02/batch-process
输入: {subjects_list, pipeline_config}
返回: {job_id, status}

GET  /api/m02/batch-status/{job_id}
返回: {progress, completed_count, total_count, current_subject}

# 8. 预设配置管理
GET  /api/m02/presets
返回: {presets: [{name, config}, ...]}

POST /api/m02/presets
输入: {name, config}
返回: {success, preset_id}

DELETE /api/m02/presets/{preset_id}
返回: {success}
```

### 4.2 后端文件结构

```
src/modules/module02_preprocessing/
├── __init__.py
├── api.py                    # API路由（150行）
├── service.py                # 业务逻辑（200行）
├── quality_checker.py        # 质量检测算法（250行）
├── data_cleaner.py           # 数据清洗算法（300行）
├── data_smoother.py          # 数据平滑算法（250行）
├── pipeline.py               # 预处理流水线（150行）
└── static/
    └── presets/
        ├── light_cleaning.json
        ├── standard_cleaning.json
        └── aggressive_cleaning.json
```

---

## 💻 前端组件设计

### 5.1 组件结构

```
frontend/src/pages/Module02/
├── Module02.jsx              # 主页面（400行，参考Module01结构）
└── components/
    ├── DataSelector.jsx      # 数据选择组件（复用Module01）
    ├── QualityDashboard.jsx  # 质量诊断面板（150行）
    ├── QualityCheckTab.jsx   # 质量检测Tab（200行）
    ├── CleaningTab.jsx       # 数据清洗Tab（250行）
    ├── SmoothingTab.jsx      # 数据平滑Tab（200行）
    ├── ComparisonChart.jsx   # 前后对比图表（150行）
    └── PreprocessingReport.jsx # 预处理报告（100行）
```

### 5.2 核心组件设计

#### **Module02.jsx** (主页面)

```jsx
import React, { useState, useEffect } from 'react';
import { Card, Tabs, message, Space, Button } from 'antd';
import DataSelector from './components/DataSelector';
import QualityDashboard from './components/QualityDashboard';
import QualityCheckTab from './components/QualityCheckTab';
import CleaningTab from './components/CleaningTab';
import SmoothingTab from './components/SmoothingTab';

const Module02 = () => {
  // 状态管理（参考Module01）
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [selectedVersion, setSelectedVersion] = useState('all');

  const [rawData, setRawData] = useState(null);
  const [processedData, setProcessedData] = useState(null);
  const [qualityReport, setQualityReport] = useState(null);

  const [loadingData, setLoadingData] = useState(false);
  const [processingData, setProcessingData] = useState(false);

  // 加载原始数据
  const loadData = async () => {
    // 调用 /api/m02/load-data
  };

  // 应用预处理
  const applyPreprocessing = async (config) => {
    // 调用 /api/m02/preprocess
  };

  return (
    <div>
      {/* 页面标题 */}
      <Card style={{ marginBottom: 24 }}>
        <h2>Module02: 数据预处理与质量控制</h2>
        <p>对眼球追踪数据进行质量检测、清洗和平滑处理</p>
      </Card>

      {/* 数据选择 */}
      <DataSelector
        onDataLoad={loadData}
        // ... props
      />

      {/* 质量诊断 */}
      {qualityReport && (
        <QualityDashboard report={qualityReport} />
      )}

      {/* 处理配置 */}
      <Card title="数据预处理">
        <Tabs
          items={[
            {
              key: 'quality',
              label: '质量检测',
              children: <QualityCheckTab data={rawData} />
            },
            {
              key: 'cleaning',
              label: '数据清洗',
              children: <CleaningTab data={rawData} />
            },
            {
              key: 'smoothing',
              label: '数据平滑',
              children: <SmoothingTab data={processedData || rawData} />
            }
          ]}
        />
      </Card>

      {/* 保存按钮 */}
      <Card>
        <Space>
          <Button type="primary" onClick={savePreprocessedData}>
            保存预处理数据
          </Button>
          <Button onClick={exportReport}>
            导出质量报告
          </Button>
        </Space>
      </Card>
    </div>
  );
};
```

#### **QualityCheckTab.jsx**

```jsx
const QualityCheckTab = ({ data }) => {
  const [config, setConfig] = useState({
    checkMissing: true,
    checkOutliers: true,
    outlierMethod: '3sigma',
    outlierThreshold: 3.0,
    checkRange: true,
    checkSampling: true,
    expectedSamplingRate: 60
  });

  const [qualityResult, setQualityResult] = useState(null);

  const runQualityCheck = async () => {
    const result = await api.post('/api/m02/quality-check', {
      data,
      config
    });
    setQualityResult(result.data);
  };

  return (
    <Row gutter={16}>
      <Col span={8}>
        {/* 参数配置面板 */}
        <Card title="检测配置">
          <Form layout="vertical">
            <Form.Item label="缺失值检测">
              <Switch checked={config.checkMissing} />
            </Form.Item>
            <Form.Item label="异常值检测">
              <Switch checked={config.checkOutliers} />
              <Select value={config.outlierMethod}>
                <Option value="3sigma">3σ法则</Option>
                <Option value="iqr">IQR方法</Option>
              </Select>
            </Form.Item>
            {/* ... 更多配置 */}
            <Button type="primary" onClick={runQualityCheck}>
              执行检测
            </Button>
          </Form>
        </Card>
      </Col>

      <Col span={16}>
        {/* 检测结果可视化 */}
        {qualityResult && (
          <Card title="检测结果">
            {/* 轨迹图（标注问题点） */}
            <GazeTrajectoryChart
              data={data}
              highlightPoints={qualityResult.issues_found}
            />

            {/* 统计图表 */}
            <Row gutter={16}>
              <Col span={8}>
                <Statistic title="缺失值" value={qualityResult.missing_count} />
              </Col>
              <Col span={8}>
                <Statistic title="异常值" value={qualityResult.outlier_count} />
              </Col>
              <Col span={8}>
                <Statistic
                  title="质量评分"
                  value={qualityResult.quality_score}
                  suffix="/ 100"
                />
              </Col>
            </Row>
          </Card>
        )}
      </Col>
    </Row>
  );
};
```

---

## 🧮 核心算法设计

### 6.1 质量检测算法

**QualityChecker类** (quality_checker.py):

```python
class QualityChecker:
    """数据质量检测器"""

    def __init__(self):
        self.config = {
            'outlier_method': '3sigma',
            'outlier_threshold': 3.0,
            'expected_range_x': [0, 1],
            'expected_range_y': [0, 1],
            'expected_sampling_rate': 60,
            'sampling_tolerance': 5
        }

    def check_quality(self, df, config=None):
        """完整质量检测流程"""
        if config:
            self.config.update(config)

        report = {
            'total_points': len(df),
            'missing_values': self._check_missing(df),
            'outliers': self._check_outliers(df),
            'range_violations': self._check_range(df),
            'sampling_issues': self._check_sampling(df),
            'quality_score': 0
        }

        # 计算综合质量分数（0-100）
        report['quality_score'] = self._calculate_quality_score(report)

        return report

    def _check_missing(self, df):
        """检测缺失值"""
        missing_info = {
            'x_missing': df['x'].isna().sum(),
            'y_missing': df['y'].isna().sum(),
            'time_missing': df['time'].isna().sum() if 'time' in df.columns else 0,
            'total_missing': df.isna().sum().sum(),
            'missing_indices': df[df.isna().any(axis=1)].index.tolist()
        }
        return missing_info

    def _check_outliers(self, df):
        """检测异常值"""
        method = self.config['outlier_method']
        threshold = self.config['outlier_threshold']

        outliers = {
            'x_outliers': [],
            'y_outliers': [],
            'total_outliers': 0
        }

        for col in ['x', 'y']:
            if col in df.columns:
                if method == '3sigma':
                    mean = df[col].mean()
                    std = df[col].std()
                    outlier_mask = np.abs(df[col] - mean) > threshold * std
                elif method == 'iqr':
                    q1, q3 = df[col].quantile([0.25, 0.75])
                    iqr = q3 - q1
                    outlier_mask = (df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)

                outlier_indices = df[outlier_mask].index.tolist()
                outliers[f'{col}_outliers'] = outlier_indices
                outliers['total_outliers'] += len(outlier_indices)

        return outliers

    def _check_range(self, df):
        """检查坐标范围"""
        x_min, x_max = self.config['expected_range_x']
        y_min, y_max = self.config['expected_range_y']

        range_violations = {
            'x_below': (df['x'] < x_min).sum(),
            'x_above': (df['x'] > x_max).sum(),
            'y_below': (df['y'] < y_min).sum(),
            'y_above': (df['y'] > y_max).sum()
        }
        range_violations['total'] = sum(range_violations.values())

        return range_violations

    def _check_sampling(self, df):
        """检查采样率"""
        if 'time' not in df.columns:
            return {'status': 'no_time_column'}

        time_diff = np.diff(df['time'].values)
        median_interval = np.median(time_diff)  # ms
        actual_rate = 1000.0 / median_interval  # Hz

        expected_rate = self.config['expected_sampling_rate']
        tolerance = self.config['sampling_tolerance']

        is_stable = abs(actual_rate - expected_rate) <= tolerance

        return {
            'actual_rate': actual_rate,
            'expected_rate': expected_rate,
            'is_stable': is_stable,
            'median_interval_ms': median_interval,
            'std_interval_ms': np.std(time_diff)
        }

    def _calculate_quality_score(self, report):
        """计算综合质量分数"""
        score = 100

        # 缺失值扣分
        missing_ratio = report['missing_values']['total_missing'] / report['total_points']
        score -= missing_ratio * 30

        # 异常值扣分
        outlier_ratio = report['outliers']['total_outliers'] / report['total_points']
        score -= outlier_ratio * 30

        # 范围违规扣分
        range_ratio = report['range_violations']['total'] / report['total_points']
        score -= range_ratio * 20

        # 采样率不稳定扣分
        if not report['sampling_issues'].get('is_stable', True):
            score -= 20

        return max(0, min(100, score))
```

### 6.2 数据清洗算法

**DataCleaner类** (data_cleaner.py):

```python
class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        self.config = {
            'missing_method': 'interpolate',
            'outlier_method': '3sigma',
            'outlier_threshold': 3.0,
            'outlier_action': 'interpolate',
            'clip_range': True,
            'x_range': [0, 1],
            'y_range': [0, 1],
            'resample': False,
            'target_rate': 60
        }

    def clean(self, df, config=None):
        """完整清洗流程"""
        if config:
            self.config.update(config)

        df_cleaned = df.copy()
        cleaning_log = {
            'original_points': len(df),
            'steps': []
        }

        # 1. 处理缺失值
        df_cleaned, step1_log = self._handle_missing(df_cleaned)
        cleaning_log['steps'].append(step1_log)

        # 2. 处理异常值
        df_cleaned, step2_log = self._handle_outliers(df_cleaned)
        cleaning_log['steps'].append(step2_log)

        # 3. 坐标裁剪
        if self.config['clip_range']:
            df_cleaned, step3_log = self._clip_coordinates(df_cleaned)
            cleaning_log['steps'].append(step3_log)

        # 4. 重采样（可选）
        if self.config['resample']:
            df_cleaned, step4_log = self._resample_data(df_cleaned)
            cleaning_log['steps'].append(step4_log)

        cleaning_log['final_points'] = len(df_cleaned)
        cleaning_log['points_removed'] = cleaning_log['original_points'] - cleaning_log['final_points']

        return df_cleaned, cleaning_log

    def _handle_missing(self, df):
        """处理缺失值"""
        method = self.config['missing_method']
        original_missing = df.isna().sum().sum()

        if method == 'interpolate':
            df = df.interpolate(method='linear', limit_direction='both')
        elif method == 'ffill':
            df = df.fillna(method='ffill')
        elif method == 'drop':
            df = df.dropna()

        log = {
            'step': 'missing_value_handling',
            'method': method,
            'original_missing': original_missing,
            'remaining_missing': df.isna().sum().sum()
        }

        return df, log

    def _handle_outliers(self, df):
        """处理异常值"""
        method = self.config['outlier_method']
        threshold = self.config['outlier_threshold']
        action = self.config['outlier_action']

        outliers_handled = 0

        for col in ['x', 'y']:
            if col in df.columns:
                # 检测异常值
                if method == '3sigma':
                    mean = df[col].mean()
                    std = df[col].std()
                    outlier_mask = np.abs(df[col] - mean) > threshold * std
                elif method == 'iqr':
                    q1, q3 = df[col].quantile([0.25, 0.75])
                    iqr = q3 - q1
                    outlier_mask = (df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)

                # 处理异常值
                if action == 'interpolate':
                    df.loc[outlier_mask, col] = np.nan
                    df[col] = df[col].interpolate(method='linear')
                elif action == 'drop':
                    df = df[~outlier_mask]
                elif action == 'clip':
                    if method == '3sigma':
                        lower = mean - threshold * std
                        upper = mean + threshold * std
                    else:
                        lower = q1 - 1.5*iqr
                        upper = q3 + 1.5*iqr
                    df[col] = df[col].clip(lower, upper)

                outliers_handled += outlier_mask.sum()

        log = {
            'step': 'outlier_handling',
            'method': method,
            'action': action,
            'outliers_handled': outliers_handled
        }

        return df, log

    def _clip_coordinates(self, df):
        """裁剪坐标到指定范围"""
        x_min, x_max = self.config['x_range']
        y_min, y_max = self.config['y_range']

        original_out_of_range = (
            (df['x'] < x_min) | (df['x'] > x_max) |
            (df['y'] < y_min) | (df['y'] > y_max)
        ).sum()

        df['x'] = df['x'].clip(x_min, x_max)
        df['y'] = df['y'].clip(y_min, y_max)

        log = {
            'step': 'coordinate_clipping',
            'points_clipped': original_out_of_range
        }

        return df, log

    def _resample_data(self, df):
        """重采样到目标频率"""
        if 'time' not in df.columns:
            return df, {'step': 'resampling', 'status': 'skipped_no_time'}

        target_rate = self.config['target_rate']
        interval = 1000.0 / target_rate  # ms

        # 创建均匀时间轴
        time_new = np.arange(df['time'].min(), df['time'].max(), interval)

        # 插值
        df_resampled = pd.DataFrame({'time': time_new})
        for col in df.columns:
            if col != 'time':
                f = interp1d(df['time'], df[col], kind='linear', fill_value='extrapolate')
                df_resampled[col] = f(time_new)

        log = {
            'step': 'resampling',
            'original_points': len(df),
            'resampled_points': len(df_resampled),
            'target_rate': target_rate
        }

        return df_resampled, log
```

### 6.3 数据平滑算法

**DataSmoother类** (data_smoother.py):

```python
from scipy.signal import medfilt, savgol_filter
from scipy.ndimage import gaussian_filter1d

class DataSmoother:
    """数据平滑器"""

    def __init__(self):
        self.config = {
            'method': 'gaussian',
            'window_size': 5,
            'sigma': 1.5,
            'polyorder': 3,
            'smooth_x': True,
            'smooth_y': True
        }

    def smooth(self, df, config=None):
        """应用平滑滤波"""
        if config:
            self.config.update(config)

        df_smoothed = df.copy()
        method = self.config['method']

        smoothing_log = {
            'method': method,
            'columns_smoothed': []
        }

        # 选择要平滑的列
        cols_to_smooth = []
        if self.config['smooth_x']:
            cols_to_smooth.append('x')
        if self.config['smooth_y']:
            cols_to_smooth.append('y')

        # 应用平滑
        for col in cols_to_smooth:
            if col in df.columns:
                if method == 'moving_average':
                    df_smoothed[col] = self._moving_average(df[col].values)
                elif method == 'gaussian':
                    df_smoothed[col] = self._gaussian_filter(df[col].values)
                elif method == 'median':
                    df_smoothed[col] = self._median_filter(df[col].values)
                elif method == 'savgol':
                    df_smoothed[col] = self._savgol_filter(df[col].values)

                smoothing_log['columns_smoothed'].append(col)

        return df_smoothed, smoothing_log

    def _moving_average(self, data):
        """移动平均滤波"""
        window = self.config['window_size']
        return pd.Series(data).rolling(window=window, center=True, min_periods=1).mean().values

    def _gaussian_filter(self, data):
        """高斯滤波"""
        sigma = self.config['sigma']
        return gaussian_filter1d(data, sigma=sigma)

    def _median_filter(self, data):
        """中值滤波"""
        window = self.config['window_size']
        # 确保窗口大小为奇数
        if window % 2 == 0:
            window += 1
        return medfilt(data, kernel_size=window)

    def _savgol_filter(self, data):
        """Savitzky-Golay滤波"""
        window = self.config['window_size']
        polyorder = self.config['polyorder']

        # 确保窗口大小为奇数且大于多项式阶数
        if window % 2 == 0:
            window += 1
        if window <= polyorder:
            window = polyorder + 2

        return savgol_filter(data, window, polyorder)
```

---

## 📊 数据流与处理管道

### 7.1 数据流图

```
┌─────────────────────────────────────────────────────────────┐
│  1. 数据加载阶段                                            │
│  ┌──────────┐                                               │
│  │ 原始数据 │ → data/01_raw/{group}/{subject}/{task}.csv   │
│  └──────────┘                                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. 质量检测阶段                                            │
│  ┌────────────────────────────────────────────────┐        │
│  │ QualityChecker.check_quality()                 │        │
│  │  → 缺失值检测                                  │        │
│  │  → 异常值检测                                  │        │
│  │  → 范围检查                                    │        │
│  │  → 采样率分析                                  │        │
│  └────────────────────────────────────────────────┘        │
│  输出: quality_report.json                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. 数据清洗阶段                                            │
│  ┌────────────────────────────────────────────────┐        │
│  │ DataCleaner.clean()                            │        │
│  │  Step 1: 处理缺失值（插值/删除/填充）         │        │
│  │  Step 2: 处理异常值（替换/删除/裁剪）         │        │
│  │  Step 3: 坐标裁剪（限制到[0,1]范围）          │        │
│  │  Step 4: 重采样（可选，统一采样率）           │        │
│  └────────────────────────────────────────────────┘        │
│  输出: cleaned_data + cleaning_log                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 数据平滑阶段                                            │
│  ┌────────────────────────────────────────────────┐        │
│  │ DataSmoother.smooth()                          │        │
│  │  选择方法:                                     │        │
│  │    - 移动平均 / 高斯 / 中值 / Savgol          │        │
│  │  选择列: X坐标 / Y坐标 / 两者                 │        │
│  └────────────────────────────────────────────────┘        │
│  输出: smoothed_data + smoothing_log                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  5. 数据保存阶段                                            │
│  ┌──────────────────────────────────────────────┐          │
│  │ 预处理数据保存到:                            │          │
│  │ data/02_preprocessed/{group}/{subject}/     │          │
│  │   → {task}_preprocessed.csv                 │          │
│  │   → {task}_preprocessing_metadata.json      │          │
│  │   → {task}_quality_report.json              │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 预处理管道

**Pipeline类** (pipeline.py):

```python
class PreprocessingPipeline:
    """预处理流水线"""

    def __init__(self):
        self.quality_checker = QualityChecker()
        self.data_cleaner = DataCleaner()
        self.data_smoother = DataSmoother()

    def run(self, df, config):
        """执行完整预处理流程"""
        pipeline_log = {
            'start_time': datetime.now().isoformat(),
            'input_points': len(df),
            'stages': []
        }

        # Stage 1: 质量检测
        quality_report = self.quality_checker.check_quality(df, config.get('quality'))
        pipeline_log['stages'].append({
            'name': 'quality_check',
            'report': quality_report
        })

        # Stage 2: 数据清洗
        df_cleaned, cleaning_log = self.data_cleaner.clean(df, config.get('cleaning'))
        pipeline_log['stages'].append({
            'name': 'cleaning',
            'log': cleaning_log
        })

        # Stage 3: 数据平滑
        df_final, smoothing_log = self.data_smoother.smooth(df_cleaned, config.get('smoothing'))
        pipeline_log['stages'].append({
            'name': 'smoothing',
            'log': smoothing_log
        })

        # 最终质量检测
        final_quality = self.quality_checker.check_quality(df_final)
        pipeline_log['final_quality'] = final_quality
        pipeline_log['output_points'] = len(df_final)
        pipeline_log['end_time'] = datetime.now().isoformat()

        return df_final, pipeline_log
```

---

## 🎨 UI/UX设计细节

### 8.1 配色方案

**沿用Module01的配色体系**：

```css
/* 主色调 */
--primary-color: #1890ff;      /* 蓝色 - 主要按钮 */
--success-color: #52c41a;      /* 绿色 - 成功状态 */
--warning-color: #faad14;      /* 橙色 - 警告信息 */
--error-color: #f5222d;        /* 红色 - 错误状态 */

/* 质量评分颜色 */
--quality-excellent: #52c41a;  /* 90-100分 */
--quality-good: #1890ff;       /* 70-89分 */
--quality-fair: #faad14;       /* 50-69分 */
--quality-poor: #f5222d;       /* 0-49分 */

/* 数据点状态颜色 */
--point-normal: #1890ff;       /* 正常数据点 */
--point-missing: #d9d9d9;      /* 缺失数据点 */
--point-outlier: #f5222d;      /* 异常数据点 */
--point-cleaned: #52c41a;      /* 清洗后数据点 */
```

### 8.2 交互反馈

#### **实时预览**:
- 参数调整时，图表立即更新
- 使用防抖（debounce）优化性能

#### **处理进度**:
- 批量处理显示进度条
- 当前处理的受试者/任务高亮

#### **错误处理**:
- 参数验证提示（如窗口大小不能为偶数）
- 数据异常友好提示
- 操作失败回滚机制

### 8.3 响应式设计

**支持不同屏幕尺寸**：

```jsx
// 大屏幕（>1400px）
<Row gutter={16}>
  <Col span={6}>参数面板</Col>
  <Col span={18}>可视化图表</Col>
</Row>

// 中屏幕（992-1400px）
<Row gutter={16}>
  <Col span={8}>参数面板</Col>
  <Col span={16}>可视化图表</Col>
</Row>

// 小屏幕（<992px）
<Row gutter={16}>
  <Col span={24}>参数面板</Col>
  <Col span={24}>可视化图表</Col>
</Row>
```

---

## 📋 配置预设

### 9.1 预设配置文件

**轻度清洗 (light_cleaning.json)**:
```json
{
  "name": "轻度清洗",
  "description": "适用于高质量数据，仅处理明显问题",
  "quality": {
    "outlier_method": "3sigma",
    "outlier_threshold": 4.0
  },
  "cleaning": {
    "missing_method": "interpolate",
    "outlier_method": "3sigma",
    "outlier_threshold": 4.0,
    "outlier_action": "interpolate",
    "clip_range": true,
    "resample": false
  },
  "smoothing": {
    "method": "gaussian",
    "sigma": 1.0,
    "smooth_x": true,
    "smooth_y": true
  }
}
```

**标准清洗 (standard_cleaning.json)**:
```json
{
  "name": "标准清洗",
  "description": "适用于常规数据质量",
  "quality": {
    "outlier_method": "3sigma",
    "outlier_threshold": 3.0
  },
  "cleaning": {
    "missing_method": "interpolate",
    "outlier_method": "3sigma",
    "outlier_threshold": 3.0,
    "outlier_action": "interpolate",
    "clip_range": true,
    "resample": true,
    "target_rate": 60
  },
  "smoothing": {
    "method": "gaussian",
    "sigma": 1.5,
    "smooth_x": true,
    "smooth_y": true
  }
}
```

**强力清洗 (aggressive_cleaning.json)**:
```json
{
  "name": "强力清洗",
  "description": "适用于噪声较大的数据",
  "quality": {
    "outlier_method": "iqr",
    "outlier_threshold": 1.5
  },
  "cleaning": {
    "missing_method": "interpolate",
    "outlier_method": "iqr",
    "outlier_threshold": 1.5,
    "outlier_action": "interpolate",
    "clip_range": true,
    "resample": true,
    "target_rate": 60
  },
  "smoothing": {
    "method": "savgol",
    "window_size": 11,
    "polyorder": 3,
    "smooth_x": true,
    "smooth_y": true
  }
}
```

---

## 🧪 测试用例

### 10.1 单元测试

```python
# tests/test_module02.py

class TestQualityChecker(unittest.TestCase):

    def test_missing_value_detection(self):
        """测试缺失值检测"""
        df = pd.DataFrame({
            'x': [0.1, np.nan, 0.3, 0.4],
            'y': [0.5, 0.6, np.nan, 0.8],
            'time': [0, 10, 20, 30]
        })

        checker = QualityChecker()
        report = checker.check_quality(df)

        self.assertEqual(report['missing_values']['x_missing'], 1)
        self.assertEqual(report['missing_values']['y_missing'], 1)
        self.assertEqual(report['missing_values']['total_missing'], 2)

    def test_outlier_detection_3sigma(self):
        """测试3σ法则异常检测"""
        df = pd.DataFrame({
            'x': [0.5, 0.51, 0.49, 0.5, 10.0],  # 最后一个是异常值
            'y': [0.5, 0.5, 0.5, 0.5, 0.5]
        })

        checker = QualityChecker()
        report = checker.check_quality(df, {'outlier_method': '3sigma'})

        self.assertEqual(len(report['outliers']['x_outliers']), 1)
        self.assertEqual(report['outliers']['x_outliers'][0], 4)

class TestDataCleaner(unittest.TestCase):

    def test_interpolate_missing(self):
        """测试缺失值插值"""
        df = pd.DataFrame({
            'x': [0.0, np.nan, 1.0],
            'y': [0.0, 0.5, 1.0]
        })

        cleaner = DataCleaner()
        df_cleaned, log = cleaner.clean(df, {'missing_method': 'interpolate'})

        self.assertEqual(df_cleaned.isna().sum().sum(), 0)
        self.assertAlmostEqual(df_cleaned.loc[1, 'x'], 0.5)

class TestDataSmoother(unittest.TestCase):

    def test_gaussian_smoothing(self):
        """测试高斯平滑"""
        df = pd.DataFrame({
            'x': np.sin(np.linspace(0, 10, 100)),
            'y': np.cos(np.linspace(0, 10, 100))
        })

        smoother = DataSmoother()
        df_smoothed, log = smoother.smooth(df, {
            'method': 'gaussian',
            'sigma': 1.5
        })

        # 平滑后的数据应该更"平缓"
        original_std = df['x'].std()
        smoothed_std = df_smoothed['x'].std()
        self.assertLess(smoothed_std, original_std)
```

### 10.2 集成测试

```python
class TestPreprocessingPipeline(unittest.TestCase):

    def test_complete_pipeline(self):
        """测试完整预处理流程"""
        # 创建模拟数据
        df = create_mock_gaze_data(
            points=1000,
            missing_ratio=0.05,
            outlier_ratio=0.02,
            noise_level=0.01
        )

        # 运行流水线
        pipeline = PreprocessingPipeline()
        config = load_preset('standard_cleaning')

        df_processed, log = pipeline.run(df, config)

        # 验证结果
        self.assertGreater(len(df_processed), 900)  # 大部分数据保留
        self.assertEqual(df_processed.isna().sum().sum(), 0)  # 无缺失值

        # 质量分数应该提升
        initial_score = log['stages'][0]['report']['quality_score']
        final_score = log['final_quality']['quality_score']
        self.assertGreater(final_score, initial_score)
```

---

## 📈 性能优化

### 11.1 数据处理优化

#### **向量化计算**:
```python
# ❌ 慢速：循环
for i in range(len(df)):
    if df.loc[i, 'x'] > threshold:
        df.loc[i, 'x'] = threshold

# ✅ 快速：向量化
df['x'] = df['x'].clip(upper=threshold)
```

#### **批处理优化**:
```python
# 批量处理多个受试者
def batch_process(subjects, config):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(process_subject, s, config)
            for s in subjects
        ]
        results = [f.result() for f in futures]
    return results
```

### 11.2 前端性能优化

#### **防抖/节流**:
```jsx
import { debounce } from 'lodash';

const handleParamChange = debounce((value) => {
  updatePreview(value);
}, 300);
```

#### **大数据集降采样显示**:
```jsx
// 超过10000个点时，降采样显示
const displayData = rawData.length > 10000
  ? downsample(rawData, 10000)
  : rawData;
```

---

## 🔒 数据安全

### 12.1 数据备份

**自动备份机制**:
```python
def save_preprocessed_data(df, metadata, backup=True):
    """保存预处理数据（含备份）"""

    # 主文件路径
    output_path = get_preprocessed_path(metadata)

    # 备份旧文件（如果存在）
    if backup and os.path.exists(output_path):
        backup_path = output_path.replace('.csv', f'_backup_{timestamp}.csv')
        shutil.copy(output_path, backup_path)

    # 保存新文件
    df.to_csv(output_path, index=False)

    # 保存元数据
    metadata_path = output_path.replace('.csv', '_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
```

### 12.2 操作日志

**详细记录所有操作**:
```python
# logs/preprocessing/{date}/{subject}_{task}_preprocessing.log

2025-10-05 10:30:15 | INFO | 开始预处理: n1_q1
2025-10-05 10:30:15 | INFO | 质量检测: 缺失值=10, 异常值=5, 质量分=85
2025-10-05 10:30:16 | INFO | 数据清洗: 插值缺失值, 处理异常值
2025-10-05 10:30:16 | INFO | 数据平滑: 高斯滤波 (σ=1.5)
2025-10-05 10:30:17 | INFO | 保存到: data/02_preprocessed/control/n1/q1_preprocessed.csv
2025-10-05 10:30:17 | INFO | 最终质量分: 95
```

---

## 📖 用户文档

### 13.1 快速开始

**步骤1: 选择数据**
1. 选择数据版本（V1/V2）
2. 选择组别（Control/MCI/AD）
3. 选择受试者
4. 选择任务（Q1-Q5）
5. 点击"加载数据"

**步骤2: 查看质量报告**
- 系统自动显示数据质量诊断
- 查看缺失值、异常值统计
- 注意质量评分（建议>70分）

**步骤3: 配置预处理**
- 选择预设配置（轻度/标准/强力）
- 或手动调整参数
- 实时预览处理效果

**步骤4: 保存结果**
- 点击"应用预处理"
- 保存到 `data/02_preprocessed/`
- 自动生成质量报告

### 13.2 常见问题

**Q: 如何选择合适的预设？**
A:
- 质量分>85: 使用"轻度清洗"
- 质量分70-85: 使用"标准清洗"
- 质量分<70: 使用"强力清洗"

**Q: 为什么平滑后数据点变少了？**
A: 某些滤波方法（如中值滤波）会在边缘丢失部分数据点，这是正常现象。

**Q: 如何撤销预处理？**
A: 系统自动备份原始文件，可在备份目录中恢复。

---

## 🚀 开发计划

### 14.1 开发阶段

**Phase 1: 后端核心 (3天)**
- Day 1: 质量检测算法
- Day 2: 清洗和平滑算法
- Day 3: API接口和Pipeline

**Phase 2: 前端UI (3天)**
- Day 4: 主页面框架
- Day 5: 3个Tab页面
- Day 6: 可视化图表

**Phase 3: 集成测试 (2天)**
- Day 7: 单元测试 + 集成测试
- Day 8: 前后端联调

**Phase 4: 优化完善 (2天)**
- Day 9: 性能优化
- Day 10: 文档编写

**总计**: 10个工作日

### 14.2 里程碑

- [x] 需求文档编写 (本文档)
- [ ] 后端API完成
- [ ] 前端UI完成
- [ ] 测试通过
- [ ] 正式发布

---

## 📝 验收标准

### 15.1 功能验收

- ✅ 支持V1和V2数据格式
- ✅ 质量检测准确率>95%
- ✅ 清洗处理无数据丢失（除明确删除）
- ✅ 平滑效果可视化对比
- ✅ 保存预处理数据和元数据
- ✅ 批量处理支持
- ✅ 配置预设功能

### 15.2 性能验收

- ✅ 单个受试者处理时间<5秒
- ✅ 批量处理10个受试者<1分钟
- ✅ 前端响应时间<1秒
- ✅ 大数据集（>10000点）流畅显示

### 15.3 质量验收

- ✅ 单元测试覆盖率>80%
- ✅ 无已知Bug
- ✅ 代码符合PEP8规范
- ✅ API文档完整
- ✅ 用户文档清晰

---

## 📚 参考资料

### 技术文档
- Pandas文档: https://pandas.pydata.org/
- SciPy信号处理: https://docs.scipy.org/doc/scipy/reference/signal.html
- Ant Design组件库: https://ant.design/

### 相关论文
- Salvucci, D. D., & Goldberg, J. H. (2000). Identifying fixations and saccades in eye-tracking protocols.
- Nyström, M., & Holmqvist, K. (2010). An adaptive algorithm for fixation, saccade, and glissade detection.

---

**文档状态**: ✅ 已完成
**下一步**: 开始后端开发
**负责人**: 开发团队
**预计完成**: 2025-10-15

---

## 👥 受试者信息管理系统 (新增功能)

### 16.1 功能定位

受试者信息管理是Module02的**重要扩展功能**,用于管理受试者的人口学信息和MMSE认知评估数据,为后续数据分析提供必要的分组和关联信息。

### 16.2 数据模型设计

#### **Subject (受试者)数据模型**:

```json
{
  "subject_id": "n1",
  "group": "control",
  "demographics": {
    "gender": "male",           // 性别: male/female
    "age": 65,                  // 年龄(岁)
    "education_level": "undergraduate"  // 受教育程度
  },
  "mmse": {
    "total_score": 28,          // MMSE总分(0-30)
    "test_date": "2024-03-15",  // 测试日期
    "sub_scores": {
      "orientation": 10,        // 定向力(0-10)
      "registration": 3,        // 即时记忆(0-3)
      "attention": 5,           // 注意力和计算(0-5)
      "recall": 3,              // 延迟回忆(0-3)
      "language": 7             // 语言(0-9)
    }
  },
  "data_version": "v1",         // 数据版本
  "task_count": 5,              // 拥有的任务数
  "created_at": "2024-03-15T10:30:00",
  "updated_at": "2024-03-20T14:25:00"
}
```

#### **教育程度枚举**:

```python
EDUCATION_LEVELS = {
    'primary': '小学',
    'junior_high': '初中',
    'senior_high': '高中',
    'vocational': '中专/职高',
    'junior_college': '大专',
    'undergraduate': '本科',
    'postgraduate': '研究生及以上'
}
```

### 16.3 数据存储结构

```
data/subject_info/
├── subjects.json              # 所有受试者信息的主文件
├── control/
│   ├── n1.json               # 单个受试者详细信息
│   ├── n2.json
│   └── ...
├── mci/
│   ├── m1.json
│   └── ...
└── ad/
    ├── a1.json
    └── ...
```

**subjects.json 主索引文件**:
```json
{
  "last_updated": "2024-03-20T14:25:00",
  "total_subjects": 60,
  "groups": {
    "control": {
      "count": 20,
      "subjects": ["n1", "n2", ...]
    },
    "mci": {
      "count": 20,
      "subjects": ["m1", "m2", ...]
    },
    "ad": {
      "count": 20,
      "subjects": ["a1", "a2", ...]
    }
  }
}
```

### 16.4 后端API设计

```python
# 基础路径: /api/m02/subjects

# 1. 获取受试者列表
GET  /api/m02/subjects
参数: group (可选), with_mmse (可选)
返回: {subjects: [{subject_id, group, demographics, mmse_summary}, ...]}

# 2. 获取单个受试者详细信息
GET  /api/m02/subjects/{subject_id}
返回: {subject: {完整受试者信息}}

# 3. 创建新受试者
POST /api/m02/subjects
输入: {subject_id, group, demographics, mmse (可选)}
返回: {success, subject_id, message}

# 4. 更新受试者信息
PUT  /api/m02/subjects/{subject_id}
输入: {demographics (可选), mmse (可选)}
返回: {success, subject, message}

# 5. 删除受试者
DELETE /api/m02/subjects/{subject_id}
返回: {success, message}

# 6. 批量导入受试者信息
POST /api/m02/subjects/batch-import
输入: {subjects: [{subject_id, group, demographics, mmse}, ...]}
返回: {success, imported_count, failed_count, errors}

# 7. 导出受试者信息
GET  /api/m02/subjects/export
参数: group (可选), format (json/csv)
返回: 文件下载

# 8. 更新MMSE数据
PUT  /api/m02/subjects/{subject_id}/mmse
输入: {total_score, test_date, sub_scores}
返回: {success, mmse, message}

# 9. 获取统计信息
GET  /api/m02/subjects/statistics
返回: {
  total_subjects,
  by_group,
  by_gender,
  by_education,
  age_distribution,
  mmse_distribution
}
```

### 16.5 前端UI设计

#### **Tab 4: 受试者信息管理**

```jsx
┌─────────────────────────────────────────────────────────────┐
│  受试者信息管理                                              │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌─────────────┐ ┌──────────┐               │
│  │ 全部(60)   │ │ 对照组(20) │ │ MCI(20) │ AD(20)        │
│  └────────────┘ └─────────────┘ └──────────┘               │
│                                                              │
│  [+ 添加受试者] [批量导入] [导出数据] [搜索: _________]    │
│                                                              │
│  受试者列表:                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ID   │ 组别 │ 性别 │ 年龄 │ 教育 │ MMSE │ 任务 │操作│  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ n1   │ 对照 │ 男   │ 65  │ 本科 │ 28  │ 5   │[编辑]│  │
│  │ n2   │ 对照 │ 女   │ 62  │ 高中 │ 29  │ 5   │[编辑]│  │
│  │ m1   │ MCI  │ 男   │ 70  │ 初中 │ 24  │ 5   │[编辑]│  │
│  │ ...  │ ...  │ ...  │ ... │ ...  │ ... │ ... │ ...  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  页码: [1] [2] [3] ... 共60条                              │
└─────────────────────────────────────────────────────────────┘
```

#### **受试者编辑弹窗**:

```jsx
┌─────────────────────────────────────┐
│  编辑受试者信息: n1                  │
├─────────────────────────────────────┤
│  基本信息                           │
│  ┌────────────────────────────────┐ │
│  │ 受试者ID: n1        (不可编辑)│ │
│  │ 研究组别: [对照组 ▼] (不可编辑)│ │
│  │ 数据版本: v1        (不可编辑)│ │
│  └────────────────────────────────┘ │
│                                     │
│  人口学信息                         │
│  ┌────────────────────────────────┐ │
│  │ 性别: ○ 男  ○ 女               │ │
│  │ 年龄: [65] 岁                  │ │
│  │ 受教育程度:                    │ │
│  │   [本科 ▼]                     │ │
│  │   选项:                        │ │
│  │     - 小学                     │ │
│  │     - 初中                     │ │
│  │     - 高中                     │ │
│  │     - 中专/职高                │ │
│  │     - 大专                     │ │
│  │     - 本科 ✓                   │ │
│  │     - 研究生及以上             │ │
│  └────────────────────────────────┘ │
│                                     │
│  MMSE评分                           │
│  ┌────────────────────────────────┐ │
│  │ 测试日期: [2024-03-15]        │ │
│  │ 总分: [28] / 30               │ │
│  │                               │ │
│  │ 各项得分:                     │ │
│  │   定向力: [10] / 10          │ │
│  │   即时记忆: [3] / 3          │ │
│  │   注意力: [5] / 5            │ │
│  │   延迟回忆: [3] / 3          │ │
│  │   语言: [7] / 9              │ │
│  │                               │ │
│  │ 认知状态: 正常 (≥24分)       │ │
│  └────────────────────────────────┘ │
│                                     │
│  [保存] [取消]                      │
└─────────────────────────────────────┘
```

### 16.6 前端组件实现

**SubjectManagementTab.jsx**:

```jsx
import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, DatePicker, message, Tabs, Tag, Space, Upload, Statistic, Row, Col } from 'antd';
import { UserAddOutlined, UploadOutlined, DownloadOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { subjectService } from '../../services/subjectService';
import moment from 'moment';

const { Option } = Select;

const EDUCATION_LEVELS = {
  'primary': '小学',
  'junior_high': '初中',
  'senior_high': '高中',
  'vocational': '中专/职高',
  'junior_college': '大专',
  'undergraduate': '本科',
  'postgraduate': '研究生及以上'
};

const SubjectManagementTab = () => {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState('all');
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentSubject, setCurrentSubject] = useState(null);
  const [form] = Form.useForm();

  // 加载受试者列表
  const loadSubjects = async (group = 'all') => {
    setLoading(true);
    try {
      const result = await subjectService.getSubjects({ group });
      setSubjects(result.data);
    } catch (error) {
      message.error('加载受试者列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubjects(selectedGroup);
  }, [selectedGroup]);

  // 打开编辑弹窗
  const handleEdit = async (subjectId) => {
    const result = await subjectService.getSubject(subjectId);
    if (result.success) {
      setCurrentSubject(result.data);
      form.setFieldsValue({
        gender: result.data.demographics.gender,
        age: result.data.demographics.age,
        education_level: result.data.demographics.education_level,
        mmse_total: result.data.mmse?.total_score,
        mmse_test_date: result.data.mmse?.test_date ? moment(result.data.mmse.test_date) : null,
        mmse_orientation: result.data.mmse?.sub_scores?.orientation,
        mmse_registration: result.data.mmse?.sub_scores?.registration,
        mmse_attention: result.data.mmse?.sub_scores?.attention,
        mmse_recall: result.data.mmse?.sub_scores?.recall,
        mmse_language: result.data.mmse?.sub_scores?.language
      });
      setEditModalVisible(true);
    }
  };

  // 保存编辑
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      const updateData = {
        demographics: {
          gender: values.gender,
          age: values.age,
          education_level: values.education_level
        },
        mmse: {
          total_score: values.mmse_total,
          test_date: values.mmse_test_date?.format('YYYY-MM-DD'),
          sub_scores: {
            orientation: values.mmse_orientation,
            registration: values.mmse_registration,
            attention: values.mmse_attention,
            recall: values.mmse_recall,
            language: values.mmse_language
          }
        }
      };

      const result = await subjectService.updateSubject(currentSubject.subject_id, updateData);

      if (result.success) {
        message.success('保存成功');
        setEditModalVisible(false);
        loadSubjects(selectedGroup);
      } else {
        message.error('保存失败: ' + result.message);
      }
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '受试者ID',
      dataIndex: 'subject_id',
      key: 'subject_id',
      width: 120
    },
    {
      title: '组别',
      dataIndex: 'group',
      key: 'group',
      width: 100,
      render: (group) => (
        <Tag color={
          group === 'control' ? 'green' :
          group === 'mci' ? 'orange' : 'red'
        }>
          {group === 'control' ? '对照组' :
           group === 'mci' ? 'MCI' : 'AD'}
        </Tag>
      )
    },
    {
      title: '性别',
      dataIndex: ['demographics', 'gender'],
      key: 'gender',
      width: 80,
      render: (gender) => gender === 'male' ? '男' : '女'
    },
    {
      title: '年龄',
      dataIndex: ['demographics', 'age'],
      key: 'age',
      width: 80
    },
    {
      title: '受教育程度',
      dataIndex: ['demographics', 'education_level'],
      key: 'education',
      width: 150,
      render: (level) => EDUCATION_LEVELS[level] || level
    },
    {
      title: 'MMSE',
      dataIndex: ['mmse', 'total_score'],
      key: 'mmse',
      width: 100,
      render: (score) => {
        if (score === null || score === undefined) {
          return <Tag>未测</Tag>;
        }
        const color = score >= 24 ? 'green' : score >= 18 ? 'orange' : 'red';
        return <Tag color={color}>{score}/30</Tag>;
      }
    },
    {
      title: '任务数',
      dataIndex: 'task_count',
      key: 'task_count',
      width: 80
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record.subject_id)}
          >
            编辑
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      {/* 顶部统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic title="总受试者数" value={subjects.length} />
        </Col>
        <Col span={6}>
          <Statistic
            title="对照组"
            value={subjects.filter(s => s.group === 'control').length}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="MCI组"
            value={subjects.filter(s => s.group === 'mci').length}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="AD组"
            value={subjects.filter(s => s.group === 'ad').length}
          />
        </Col>
      </Row>

      {/* 过滤和操作按钮 */}
      <Space style={{ marginBottom: 16 }}>
        <Select
          value={selectedGroup}
          onChange={setSelectedGroup}
          style={{ width: 150 }}
        >
          <Option value="all">全部组别</Option>
          <Option value="control">对照组</Option>
          <Option value="mci">MCI组</Option>
          <Option value="ad">AD组</Option>
        </Select>

        <Button type="primary" icon={<UserAddOutlined />}>
          添加受试者
        </Button>
        <Button icon={<UploadOutlined />}>
          批量导入
        </Button>
        <Button icon={<DownloadOutlined />}>
          导出数据
        </Button>
      </Space>

      {/* 受试者表格 */}
      <Table
        columns={columns}
        dataSource={subjects}
        loading={loading}
        rowKey="subject_id"
        pagination={{
          pageSize: 20,
          showTotal: (total) => `共 ${total} 条记录`
        }}
      />

      {/* 编辑弹窗 */}
      <Modal
        title={`编辑受试者信息: ${currentSubject?.subject_id}`}
        visible={editModalVisible}
        onOk={handleSave}
        onCancel={() => setEditModalVisible(false)}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item label="基本信息">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>受试者ID: {currentSubject?.subject_id}</div>
              <div>研究组别: {currentSubject?.group}</div>
              <div>数据版本: {currentSubject?.data_version}</div>
            </Space>
          </Form.Item>

          <h4>人口学信息</h4>
          <Form.Item
            label="性别"
            name="gender"
            rules={[{ required: true, message: '请选择性别' }]}
          >
            <Select>
              <Option value="male">男</Option>
              <Option value="female">女</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="年龄(岁)"
            name="age"
            rules={[
              { required: true, message: '请输入年龄' },
              { type: 'number', min: 0, max: 120, message: '年龄范围0-120' }
            ]}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="受教育程度"
            name="education_level"
            rules={[{ required: true, message: '请选择受教育程度' }]}
          >
            <Select>
              {Object.entries(EDUCATION_LEVELS).map(([key, value]) => (
                <Option key={key} value={key}>{value}</Option>
              ))}
            </Select>
          </Form.Item>

          <h4>MMSE评分</h4>
          <Form.Item label="测试日期" name="mmse_test_date">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="总分"
            name="mmse_total"
            rules={[
              { type: 'number', min: 0, max: 30, message: '总分范围0-30' }
            ]}
          >
            <InputNumber style={{ width: '100%' }} addonAfter="/ 30" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="定向力" name="mmse_orientation">
                <InputNumber style={{ width: '100%' }} min={0} max={10} addonAfter="/ 10" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="即时记忆" name="mmse_registration">
                <InputNumber style={{ width: '100%' }} min={0} max={3} addonAfter="/ 3" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="注意力" name="mmse_attention">
                <InputNumber style={{ width: '100%' }} min={0} max={5} addonAfter="/ 5" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="延迟回忆" name="mmse_recall">
                <InputNumber style={{ width: '100%' }} min={0} max={3} addonAfter="/ 3" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="语言" name="mmse_language">
            <InputNumber style={{ width: '100%' }} min={0} max={9} addonAfter="/ 9" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SubjectManagementTab;
```

### 16.7 后端实现

**subject_manager.py** (新建文件):

```python
"""
受试者信息管理器
"""
import os
import json
from datetime import datetime
from pathlib import Path

class SubjectManager:
    """受试者信息管理"""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir) / 'subject_info'
        self.subjects_file = self.data_dir / 'subjects.json'
        self._ensure_directories()

    def _ensure_directories(self):
        """确保目录存在"""
        for group in ['control', 'mci', 'ad']:
            (self.data_dir / group).mkdir(parents=True, exist_ok=True)

    def get_all_subjects(self, group=None, with_mmse=False):
        """获取所有受试者列表"""
        if not self.subjects_file.exists():
            return []

        with open(self.subjects_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        subjects = []
        groups_to_scan = [group] if group else ['control', 'mci', 'ad']

        for grp in groups_to_scan:
            for subject_id in data['groups'].get(grp, {}).get('subjects', []):
                subject_data = self.get_subject(subject_id)
                if subject_data:
                    # 只返回摘要信息
                    summary = {
                        'subject_id': subject_data['subject_id'],
                        'group': subject_data['group'],
                        'demographics': subject_data['demographics'],
                        'task_count': subject_data.get('task_count', 0),
                        'data_version': subject_data.get('data_version', 'v1')
                    }

                    if with_mmse or subject_data.get('mmse'):
                        summary['mmse'] = {
                            'total_score': subject_data.get('mmse', {}).get('total_score'),
                            'test_date': subject_data.get('mmse', {}).get('test_date')
                        }

                    subjects.append(summary)

        return subjects

    def get_subject(self, subject_id):
        """获取单个受试者详细信息"""
        # 确定组别
        group = self._get_group_from_id(subject_id)
        if not group:
            return None

        subject_file = self.data_dir / group / f'{subject_id}.json'
        if not subject_file.exists():
            return None

        with open(subject_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_subject(self, subject_id, group, demographics, mmse=None):
        """创建新受试者"""
        subject_data = {
            'subject_id': subject_id,
            'group': group,
            'demographics': demographics,
            'mmse': mmse,
            'data_version': 'v1',
            'task_count': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # 保存受试者文件
        subject_file = self.data_dir / group / f'{subject_id}.json'
        with open(subject_file, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

        # 更新主索引
        self._update_index(subject_id, group, action='add')

        return subject_data

    def update_subject(self, subject_id, demographics=None, mmse=None):
        """更新受试者信息"""
        subject_data = self.get_subject(subject_id)
        if not subject_data:
            return None

        if demographics:
            subject_data['demographics'] = demographics

        if mmse:
            subject_data['mmse'] = mmse

        subject_data['updated_at'] = datetime.now().isoformat()

        # 保存
        group = subject_data['group']
        subject_file = self.data_dir / group / f'{subject_id}.json'
        with open(subject_file, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

        return subject_data

    def _get_group_from_id(self, subject_id):
        """从ID推断组别"""
        prefix = subject_id[0].lower()
        if prefix == 'n':
            return 'control'
        elif prefix == 'm':
            return 'mci'
        elif prefix == 'a':
            return 'ad'
        return None

    def _update_index(self, subject_id, group, action='add'):
        """更新主索引文件"""
        # 读取现有索引
        if self.subjects_file.exists():
            with open(self.subjects_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {
                'last_updated': datetime.now().isoformat(),
                'total_subjects': 0,
                'groups': {
                    'control': {'count': 0, 'subjects': []},
                    'mci': {'count': 0, 'subjects': []},
                    'ad': {'count': 0, 'subjects': []}
                }
            }

        # 更新索引
        if action == 'add':
            if subject_id not in index['groups'][group]['subjects']:
                index['groups'][group]['subjects'].append(subject_id)
                index['groups'][group]['count'] += 1
                index['total_subjects'] += 1
        elif action == 'remove':
            if subject_id in index['groups'][group]['subjects']:
                index['groups'][group]['subjects'].remove(subject_id)
                index['groups'][group]['count'] -= 1
                index['total_subjects'] -= 1

        index['last_updated'] = datetime.now().isoformat()

        # 保存索引
        with open(self.subjects_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
```

### 16.8 批量导入功能

**批量导入CSV模板**:

```csv
subject_id,group,gender,age,education_level,mmse_total,mmse_date,mmse_orientation,mmse_registration,mmse_attention,mmse_recall,mmse_language
n1,control,male,65,undergraduate,28,2024-03-15,10,3,5,3,7
n2,control,female,62,senior_high,29,2024-03-16,10,3,5,3,8
m1,mci,male,70,junior_high,24,2024-03-17,9,3,4,2,6
```

**批量导入处理**:

```python
def batch_import_subjects(csv_file):
    """批量导入受试者信息"""
    import pandas as pd

    df = pd.read_csv(csv_file)
    results = {
        'success': [],
        'failed': []
    }

    for _, row in df.iterrows():
        try:
            demographics = {
                'gender': row['gender'],
                'age': int(row['age']),
                'education_level': row['education_level']
            }

            mmse = None
            if pd.notna(row.get('mmse_total')):
                mmse = {
                    'total_score': int(row['mmse_total']),
                    'test_date': row.get('mmse_date'),
                    'sub_scores': {
                        'orientation': int(row.get('mmse_orientation', 0)),
                        'registration': int(row.get('mmse_registration', 0)),
                        'attention': int(row.get('mmse_attention', 0)),
                        'recall': int(row.get('mmse_recall', 0)),
                        'language': int(row.get('mmse_language', 0))
                    }
                }

            subject_manager.create_subject(
                row['subject_id'],
                row['group'],
                demographics,
                mmse
            )

            results['success'].append(row['subject_id'])
        except Exception as e:
            results['failed'].append({
                'subject_id': row['subject_id'],
                'error': str(e)
            })

    return results
```

### 16.9 数据验证

```python
def validate_subject_data(data):
    """验证受试者数据"""
    errors = []

    # 验证subject_id
    if not data.get('subject_id'):
        errors.append('缺少subject_id')

    # 验证group
    if data.get('group') not in ['control', 'mci', 'ad']:
        errors.append('无效的group值')

    # 验证demographics
    demographics = data.get('demographics', {})
    if demographics.get('gender') not in ['male', 'female']:
        errors.append('无效的性别')

    if not isinstance(demographics.get('age'), int) or not (0 <= demographics.get('age') <= 120):
        errors.append('年龄必须是0-120之间的整数')

    valid_education = ['primary', 'junior_high', 'senior_high', 'vocational', 'junior_college', 'undergraduate', 'postgraduate']
    if demographics.get('education_level') not in valid_education:
        errors.append('无效的受教育程度')

    # 验证MMSE
    if 'mmse' in data and data['mmse']:
        mmse = data['mmse']
        if not isinstance(mmse.get('total_score'), int) or not (0 <= mmse.get('total_score') <= 30):
            errors.append('MMSE总分必须是0-30之间的整数')

        sub_scores = mmse.get('sub_scores', {})
        if not (0 <= sub_scores.get('orientation', 0) <= 10):
            errors.append('定向力得分范围: 0-10')
        if not (0 <= sub_scores.get('registration', 0) <= 3):
            errors.append('即时记忆得分范围: 0-3')
        if not (0 <= sub_scores.get('attention', 0) <= 5):
            errors.append('注意力得分范围: 0-5')
        if not (0 <= sub_scores.get('recall', 0) <= 3):
            errors.append('延迟回忆得分范围: 0-3')
        if not (0 <= sub_scores.get('language', 0) <= 9):
            errors.append('语言得分范围: 0-9')

    return errors
```

---

## 🎉 总结

Module02 是数据处理流程中的**关键质量控制节点**，通过系统化的质量检测、清洗和平滑流程，确保后续分析的数据质量。**新增的受试者信息管理和MMSE数据管理功能**，为研究提供了完整的受试者档案管理能力。

**核心优势**:
1. ✅ **架构一致性**: 完全符合Module01、ModuleEX的设计规范
2. ✅ **用户友好**: 直观的UI、实时预览、预设配置
3. ✅ **功能完整**: 覆盖数据预处理、受试者管理、MMSE管理全流程
4. ✅ **数据完整性**: 人口学信息、认知评估数据完整关联
5. ✅ **性能优秀**: 向量化计算、批处理支持
6. ✅ **可扩展性**: 易于添加新的处理方法和管理功能

**设计理念**: "让数据预处理和受试者管理像模块01查看数据一样简单直观"
