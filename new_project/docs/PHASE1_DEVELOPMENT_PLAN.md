# Phase 1 开发计划 - 数据处理基础

## 📋 概述

**目标**: 完成从原始数据到校准数据的完整流程
**周期**: 2-3周
**模块**: Module 00, Module 02, Module 03
**优先级**: P0 (最高优先级)

---

## 🎯 Phase 1 目标

建立完整的数据处理链路:
```
数据导入(Module00) → 原始数据(Module01✅) → 预处理(Module02) → 校准(Module03)
```

完成后可实现:
1. ✅ 用户可以上传自己的眼动数据
2. ✅ 系统自动进行数据清洗和预处理
3. ✅ 提供交互式校准工具
4. ✅ 输出标准化的校准数据供后续分析

---

## 📦 Module 00: 数据管理中心

### 功能需求

#### 1. 文件上传 (核心功能)
- **拖拽上传**: 支持拖拽多个CSV/TXT文件
- **批量上传**: 一次上传多个受试者数据
- **进度显示**: 实时上传进度条
- **格式验证**: 自动检测文件格式和列名

#### 2. 数据预览
- **表格预览**: 显示前100行数据
- **基础统计**: 数据点数、时间范围、坐标范围
- **质量检查**: 缺失值、异常值自动检测

#### 3. 元数据编辑
- **组别选择**: Control/MCI/AD
- **受试者ID**: 手动输入或自动提取
- **任务ID**: Q1-Q5选择
- **备注信息**: 可选的附加信息

#### 4. 数据导出
- **原始数据导出**: CSV格式
- **预处理数据导出**: CSV格式
- **批量导出**: ZIP打包下载

### 技术实现

#### 前端组件

**FileUploader.jsx** (文件上传组件):
```jsx
import React, { useState } from 'react';
import { Upload, message, Progress } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const FileUploader = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const uploadProps = {
    name: 'file',
    multiple: true,
    action: '/api/m00/upload',
    accept: '.csv,.txt',
    onChange(info) {
      const { status } = info.file;
      if (status === 'uploading') {
        setProgress(info.file.percent);
      }
      if (status === 'done') {
        message.success(`${info.file.name} 上传成功`);
        onUploadSuccess(info.file.response);
      } else if (status === 'error') {
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  return (
    <Upload.Dragger {...uploadProps}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p className="ant-upload-hint">
        支持单个或批量上传，接受CSV和TXT格式
      </p>
      {uploading && <Progress percent={progress} />}
    </Upload.Dragger>
  );
};
```

**DataPreview.jsx** (数据预览组件):
```jsx
import React from 'react';
import { Table, Card, Statistic, Row, Col, Tag } from 'antd';

const DataPreview = ({ data, stats, filename }) => {
  const columns = [
    { title: 'X坐标', dataIndex: 'x', key: 'x' },
    { title: 'Y坐标', dataIndex: 'y', key: 'y' },
    { title: '时间戳', dataIndex: 'time', key: 'time' },
  ];

  return (
    <Card title={`数据预览: ${filename}`}>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic title="数据点数" value={stats.total_points} />
        </Col>
        <Col span={6}>
          <Statistic
            title="时长(秒)"
            value={stats.duration}
            precision={2}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="缺失值"
            value={stats.missing_values}
            valueStyle={{ color: stats.missing_values > 0 ? '#cf1322' : '#3f8600' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="数据质量"
            value={stats.quality_score}
            suffix="/ 100"
          />
        </Col>
      </Row>
      <Table
        dataSource={data.slice(0, 100)}
        columns={columns}
        pagination={{ pageSize: 10 }}
        size="small"
      />
    </Card>
  );
};
```

#### 后端API

**upload_api.py**:
```python
"""
Module 00: 数据管理中心 - 上传API
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import pandas as pd
from pathlib import Path

upload_bp = Blueprint('upload', __name__, url_prefix='/api/m00')

ALLOWED_EXTENSIONS = {'csv', 'txt'}
UPLOAD_FOLDER = Path(__file__).parent.parent.parent / 'data' / 'uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        file.save(filepath)

        # 读取并验证数据
        try:
            df = pd.read_csv(filepath)
            stats = analyze_data(df)

            return jsonify({
                'success': True,
                'filename': filename,
                'stats': stats,
                'preview': df.head(100).to_dict('records')
            })
        except Exception as e:
            return jsonify({'error': f'文件解析失败: {str(e)}'}), 400

    return jsonify({'error': '不支持的文件格式'}), 400

def analyze_data(df):
    """分析数据质量"""
    return {
        'total_points': len(df),
        'duration': df['time'].max() - df['time'].min() if 'time' in df.columns else 0,
        'missing_values': df.isnull().sum().sum(),
        'columns': list(df.columns),
        'x_range': [df['x'].min(), df['x'].max()] if 'x' in df.columns else [0, 0],
        'y_range': [df['y'].min(), df['y'].max()] if 'y' in df.columns else [0, 0],
        'quality_score': calculate_quality_score(df)
    }

def calculate_quality_score(df):
    """计算数据质量分数 (0-100)"""
    score = 100

    # 扣分项
    if df.isnull().sum().sum() > 0:
        score -= 20  # 有缺失值

    if 'x' in df.columns and 'y' in df.columns:
        if (df['x'] < 0).any() or (df['x'] > 1).any():
            score -= 15  # 坐标超出范围
        if (df['y'] < 0).any() or (df['y'] > 1).any():
            score -= 15
    else:
        score -= 50  # 缺少必要列

    return max(0, score)
```

### 前端页面

**Module00.jsx**:
```jsx
import React, { useState } from 'react';
import { Card, Steps, Button, Form, Select, Input, Space } from 'antd';
import FileUploader from '../../components/Upload/FileUploader';
import DataPreview from '../../components/Upload/DataPreview';

const Module00 = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [metadata, setMetadata] = useState({});

  const steps = [
    { title: '上传文件' },
    { title: '数据预览' },
    { title: '元数据编辑' },
    { title: '保存数据' }
  ];

  const handleUploadSuccess = (response) => {
    setUploadedFiles([...uploadedFiles, response]);
    setSelectedFile(response);
    setCurrentStep(1);
  };

  const handleSaveData = async () => {
    const response = await fetch('/api/m00/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.filename,
        metadata: metadata
      })
    });

    if (response.ok) {
      message.success('数据保存成功');
      setCurrentStep(0);
      setUploadedFiles([]);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Module 00: 数据管理中心">
        <Steps current={currentStep} items={steps} style={{ marginBottom: 24 }} />

        {currentStep === 0 && (
          <FileUploader onUploadSuccess={handleUploadSuccess} />
        )}

        {currentStep === 1 && selectedFile && (
          <>
            <DataPreview
              data={selectedFile.preview}
              stats={selectedFile.stats}
              filename={selectedFile.filename}
            />
            <Space style={{ marginTop: 16 }}>
              <Button onClick={() => setCurrentStep(0)}>重新上传</Button>
              <Button type="primary" onClick={() => setCurrentStep(2)}>
                下一步
              </Button>
            </Space>
          </>
        )}

        {currentStep === 2 && (
          <>
            <Card title="元数据编辑">
              <Form layout="vertical" onValuesChange={(_, values) => setMetadata(values)}>
                <Form.Item label="组别" name="group" required>
                  <Select>
                    <Select.Option value="control">对照组</Select.Option>
                    <Select.Option value="mci">MCI组</Select.Option>
                    <Select.Option value="ad">AD组</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item label="受试者ID" name="subject_id" required>
                  <Input placeholder="例如: s001" />
                </Form.Item>
                <Form.Item label="任务ID" name="task_id" required>
                  <Select>
                    <Select.Option value="q1">Q1</Select.Option>
                    <Select.Option value="q2">Q2</Select.Option>
                    <Select.Option value="q3">Q3</Select.Option>
                    <Select.Option value="q4">Q4</Select.Option>
                    <Select.Option value="q5">Q5</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item label="备注" name="notes">
                  <Input.TextArea rows={3} />
                </Form.Item>
              </Form>
            </Card>
            <Space style={{ marginTop: 16 }}>
              <Button onClick={() => setCurrentStep(1)}>上一步</Button>
              <Button type="primary" onClick={handleSaveData}>
                保存数据
              </Button>
            </Space>
          </>
        )}
      </Card>
    </div>
  );
};

export default Module00;
```

### 开发任务清单

- [ ] 创建后端API blueprint (upload_api.py)
- [ ] 实现文件上传接口 (/api/m00/upload)
- [ ] 实现数据保存接口 (/api/m00/save)
- [ ] 实现文件列表接口 (/api/m00/files)
- [ ] 创建前端FileUploader组件
- [ ] 创建前端DataPreview组件
- [ ] 创建Module00主页面
- [ ] 添加路由配置
- [ ] 测试完整上传流程
- [ ] 编写单元测试

**预计工时**: 40小时 (5个工作日)

---

## 🔧 Module 02: 数据预处理

### 功能需求

#### 1. 异常值检测
- **统计方法**: 3σ原则、IQR方法
- **可视化**: 异常点高亮显示
- **处理策略**: 删除、插值、保留

#### 2. 数据平滑
- **移动平均**: 窗口大小可调
- **高斯滤波**: σ参数可调
- **中值滤波**: 适合处理跳点

#### 3. 缺失值处理
- **线性插值**: 适合连续数据
- **前向填充**: 保持最后有效值
- **删除**: 删除缺失数据行

#### 4. 采样率标准化
- **重采样**: 统一到固定采样率(如60Hz)
- **时间对齐**: 确保时间戳连续

### 技术实现

#### 后端核心算法

**preprocessor.py**:
```python
"""
数据预处理核心算法
"""
import numpy as np
import pandas as pd
from scipy.signal import medfilt, gaussian
from scipy.interpolate import interp1d

class DataPreprocessor:
    """数据预处理器"""

    def __init__(self):
        self.config = {
            'outlier_method': '3sigma',  # 3sigma, iqr
            'outlier_threshold': 3.0,
            'smooth_method': 'gaussian',  # gaussian, moving_avg, median
            'smooth_window': 5,
            'missing_method': 'interpolate',  # interpolate, ffill, drop
            'target_sample_rate': 60  # Hz
        }

    def detect_outliers(self, data, method='3sigma', threshold=3.0):
        """检测异常值"""
        if method == '3sigma':
            mean = np.mean(data)
            std = np.std(data)
            outliers = np.abs(data - mean) > threshold * std
        elif method == 'iqr':
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            outliers = (data < q1 - 1.5*iqr) | (data > q3 + 1.5*iqr)
        return outliers

    def smooth_data(self, data, method='gaussian', window=5):
        """数据平滑"""
        if method == 'moving_avg':
            return pd.Series(data).rolling(window=window, center=True).mean().values
        elif method == 'gaussian':
            sigma = window / 3.0
            return gaussian(len(data), sigma) * data
        elif method == 'median':
            return medfilt(data, kernel_size=window)
        return data

    def handle_missing(self, df, method='interpolate'):
        """处理缺失值"""
        if method == 'interpolate':
            return df.interpolate(method='linear')
        elif method == 'ffill':
            return df.fillna(method='ffill')
        elif method == 'drop':
            return df.dropna()
        return df

    def resample_data(self, df, target_rate=60):
        """重采样到目标采样率"""
        if 'time' not in df.columns:
            return df

        # 计算当前采样率
        time_diff = np.diff(df['time'].values)
        current_rate = 1000.0 / np.median(time_diff)  # ms to Hz

        if abs(current_rate - target_rate) < 1:
            return df  # 已经接近目标采样率

        # 重采样
        time_new = np.arange(df['time'].min(), df['time'].max(), 1000.0/target_rate)
        df_resampled = pd.DataFrame({'time': time_new})

        for col in df.columns:
            if col != 'time':
                f = interp1d(df['time'], df[col], kind='linear', fill_value='extrapolate')
                df_resampled[col] = f(time_new)

        return df_resampled

    def preprocess(self, df, config=None):
        """完整预处理流程"""
        if config:
            self.config.update(config)

        # 1. 检测并处理异常值
        for col in ['x', 'y']:
            if col in df.columns:
                outliers = self.detect_outliers(
                    df[col].values,
                    method=self.config['outlier_method'],
                    threshold=self.config['outlier_threshold']
                )
                df.loc[outliers, col] = np.nan

        # 2. 处理缺失值
        df = self.handle_missing(df, method=self.config['missing_method'])

        # 3. 数据平滑
        for col in ['x', 'y']:
            if col in df.columns:
                df[col] = self.smooth_data(
                    df[col].values,
                    method=self.config['smooth_method'],
                    window=self.config['smooth_window']
                )

        # 4. 重采样
        df = self.resample_data(df, target_rate=self.config['target_sample_rate'])

        return df
```

### 开发任务清单

- [ ] 实现异常值检测算法
- [ ] 实现数据平滑算法
- [ ] 实现缺失值处理
- [ ] 实现重采样功能
- [ ] 创建预处理API
- [ ] 创建前端参数配置界面
- [ ] 创建前后对比可视化
- [ ] 测试各种预处理组合
- [ ] 编写文档

**预计工时**: 40小时 (5个工作日)

---

## 📏 Module 03: 数据校准

### 功能需求

#### 1. 时间对齐
- **VR任务时间**: 解析VR事件时间戳
- **眼动数据时间**: 眼动设备时间戳
- **时间同步**: 两个时间轴的对齐

#### 2. 空间校准
- **坐标转换**: 设备坐标 → 屏幕坐标
- **ROI映射**: 定义感兴趣区域
- **可视化调整**: 交互式校准界面

#### 3. 速度计算
- **一阶导数**: 计算瞬时速度
- **平滑速度**: 去除噪声影响
- **加速度**: 二阶导数

### 技术实现

**calibrator.py**:
```python
"""
数据校准核心算法
"""
import numpy as np

class DataCalibrator:
    """数据校准器"""

    def __init__(self):
        self.config = {
            'screen_width': 1920,
            'screen_height': 1080,
            'time_offset': 0,  # ms
            'spatial_offset_x': 0,
            'spatial_offset_y': 0,
            'roi_definitions': {}
        }

    def align_time(self, df, offset=0):
        """时间对齐"""
        df['time_aligned'] = df['time'] + offset
        return df

    def calibrate_spatial(self, df, offset_x=0, offset_y=0):
        """空间校准"""
        df['x_calibrated'] = df['x'] + offset_x
        df['y_calibrated'] = df['y'] + offset_y
        return df

    def calculate_velocity(self, df):
        """计算速度"""
        # 计算位置差
        dx = np.diff(df['x_calibrated'].values)
        dy = np.diff(df['y_calibrated'].values)
        dt = np.diff(df['time_aligned'].values) / 1000.0  # ms to s

        # 计算速度 (deg/s)
        velocity = np.sqrt(dx**2 + dy**2) / dt
        velocity = np.insert(velocity, 0, 0)  # 第一个点速度为0

        df['velocity'] = velocity
        return df

    def map_roi(self, df, roi_definitions):
        """ROI映射"""
        df['roi'] = 'background'

        for roi_name, roi_bounds in roi_definitions.items():
            x_min, y_min, x_max, y_max = roi_bounds
            mask = (
                (df['x_calibrated'] >= x_min) &
                (df['x_calibrated'] <= x_max) &
                (df['y_calibrated'] >= y_min) &
                (df['y_calibrated'] <= y_max)
            )
            df.loc[mask, 'roi'] = roi_name

        return df

    def calibrate(self, df, config=None):
        """完整校准流程"""
        if config:
            self.config.update(config)

        # 1. 时间对齐
        df = self.align_time(df, offset=self.config['time_offset'])

        # 2. 空间校准
        df = self.calibrate_spatial(
            df,
            offset_x=self.config['spatial_offset_x'],
            offset_y=self.config['spatial_offset_y']
        )

        # 3. 计算速度
        df = self.calculate_velocity(df)

        # 4. ROI映射
        if self.config['roi_definitions']:
            df = self.map_roi(df, self.config['roi_definitions'])

        return df
```

### 开发任务清单

- [ ] 实现时间对齐算法
- [ ] 实现空间校准算法
- [ ] 实现速度计算
- [ ] 实现ROI映射
- [ ] 创建校准API
- [ ] 创建交互式校准界面
- [ ] 实现校准效果实时预览
- [ ] 测试校准精度
- [ ] 编写文档

**预计工时**: 40小时 (5个工作日)

---

## 📅 时间计划

### 第1周 (Module 00)
- Day 1-2: 后端API开发 (upload, save, list)
- Day 3-4: 前端组件开发 (FileUploader, DataPreview)
- Day 5: 主页面集成和测试

### 第2周 (Module 02)
- Day 1-2: 预处理算法实现
- Day 3-4: 前端参数配置界面
- Day 5: 可视化对比和测试

### 第3周 (Module 03)
- Day 1-2: 校准算法实现
- Day 3-4: 交互式校准界面
- Day 5: 完整流程测试和文档

---

## ✅ 验收标准

### Module 00验收
- [ ] 可以上传CSV/TXT文件
- [ ] 自动验证文件格式
- [ ] 显示数据预览和统计信息
- [ ] 可以编辑元数据
- [ ] 保存到data/01_raw/目录
- [ ] 单元测试覆盖率>70%

### Module 02验收
- [ ] 异常值检测准确
- [ ] 数据平滑效果良好
- [ ] 缺失值正确处理
- [ ] 重采样功能正常
- [ ] 保存到data/02_preprocessed/目录
- [ ] 提供前后对比可视化

### Module 03验收
- [ ] 时间对齐精度高
- [ ] 空间校准可调节
- [ ] 速度计算准确
- [ ] ROI映射正确
- [ ] 保存到data/03_calibrated/目录
- [ ] 交互式校准界面友好

### Phase 1整体验收
- [ ] 完整数据流打通: 上传→预处理→校准
- [ ] 所有API端点正常工作
- [ ] 前端页面完整实现
- [ ] 数据质量显著提升
- [ ] 文档齐全(API文档、用户手册)
- [ ] 代码质量达标(无重复代码、良好注释)

---

## 🚀 下一步

Phase 1完成后,进入Phase 2: 特征提取核心
- Module 04-A: RQA递归量化分析
- Module 04-B: 眼动事件检测
- Module 04-C: 统计特征提取

---

**文档编制**: Claude AI
**状态**: 准备开始实施
**版本**: v1.0
**日期**: 2025-10-01
