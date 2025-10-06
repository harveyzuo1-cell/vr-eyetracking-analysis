# Module02 IVT预处理开发规范

## 文档信息
- **版本**: 1.0
- **日期**: 2025-10-06
- **目标**: 在Module02现有架构上集成IVT事件检测预处理

---

## 目录
1. [现有架构分析](#1-现有架构分析)
2. [输入数据规格](#2-输入数据规格)
3. [新预处理方案设计](#3-新预处理方案设计)
4. [开发任务清单](#4-开发任务清单)
5. [API接口规范](#5-api接口规范)
6. [数据流和存储](#6-数据流和存储)

---

## 1. 现有架构分析

### 1.1 Module02当前结构

```
src/modules/module02_preprocessing/
├── subject_manager.py        # 受试者信息管理
├── mmse_manager.py            # MMSE评分管理
├── v1_data_manager.py         # V1数据(Excel)管理
├── v2_data_manager.py         # V2数据(scan_result_v2.json)管理
├── quality_checker.py         # 数据质量检查
├── data_cleaner.py            # 数据清洗(插值/异常处理)
├── data_smoother.py           # 数据平滑(高斯/Savgol等)
├── pipeline.py                # 预处理流水线
└── api.py                     # Flask API端点
```

### 1.2 现有数据流

```
V2原始数据(scan_result_v2.json)
    ↓
[V2DataManager] 扫描和导入
    ↓
SubjectManager存储
    ├─ data/subject_info/{group}/{subject_id}.json
    └─ 包含: demographics, mmse, metadata
    ↓
[当前Pipeline] 质量检查 → 清洗 → 平滑
    ↓
输出: 处理后CSV (暂无事件检测)
```

### 1.3 关键发现

**已有组件**:
- ✅ `QualityChecker`: 采样率检查、缺失值统计
- ✅ `DataCleaner`: 缺失值插值、异常值处理
- ✅ `DataSmoother`: 高斯/中值/Savgol滤波
- ✅ `Pipeline`: 串联执行

**缺失组件**:
- ❌ IVT事件检测器
- ❌ 速度计算器
- ❌ 事件序列生成器
- ❌ 保守模式清理策略

---

## 2. 输入数据规格

### 2.1 V2数据来源

**文件**: `scan_result_v2.json` (由VR眼动采集系统生成)

**结构**:
```json
[
  {
    "subject_id": "N_01",
    "group_code": "N",
    "name": "张三",
    "hospital_id": "H001",
    "age": 65,
    "gender": "男",
    "education_level": "本科",
    "timestamp": "2024-01-15 10:30:00",
    "eyetracking_data": [
      {
        "timestamp": 0.0167,
        "gaze_x": 0.512,
        "gaze_y": 0.488,
        "pupil_diameter": 3.2,
        "validity": 1
      },
      ...
    ],
    "questions": {
      "Q1": {
        "answer": "正确",
        "score": 1,
        "eyetracking_data": [...]
      },
      ...
    }
  },
  ...
]
```

**关键字段**:
- `subject_id`: 原始受试者ID (如 "N_01", "M_03", "A_05")
- `group_code`: 组别代码 ("N"=control, "M"=mci, "A"=ad)
- `timestamp`: 实验时间戳 (用于区分同一受试者的多次实验)
- `eyetracking_data`: 眼动轨迹数组
  - `timestamp`: 时间戳(秒)
  - `gaze_x`, `gaze_y`: 注视坐标(归一化0-1)
  - `pupil_diameter`: 瞳孔直径(mm)
  - `validity`: 有效性(1=有效, 0=无效)

### 2.2 SubjectManager存储格式

**文件**: `data/subject_info/{group}/{subject_id}.json`

**示例**: `data/subject_info/control/v2_control_001.json`
```json
{
  "subject_id": "v2_control_001",
  "group": "control",
  "demographics": {
    "name": "张三",
    "hospital_id": "H001",
    "age": 65,
    "gender": "男",
    "education_level": "undergraduate"
  },
  "mmse": null,
  "data_version": "v2",
  "metadata": {
    "original_id": "N_01",
    "timestamp": "2024-01-15 10:30:00",
    "v2_import_date": "2025-10-06T14:00:00",
    "data_path": "path/to/raw/data.csv"
  }
}
```

**重要约定**:
- 使用 `subject_id + timestamp` 作为唯一键(允许同一受试者多次实验)
- `data_version='v2'` 标识V2数据
- `metadata.original_id` 保留原始ID

### 2.3 眼动CSV格式

**预处理后的CSV** (由Pipeline处理后生成):

```csv
timestamp,x,y,pupil_diameter,validity
0.0167,0.512,0.488,3.2,1
0.0333,0.515,0.490,3.2,1
0.0500,0.518,0.491,3.1,1
...
```

**列说明**:
- `timestamp`: 时间戳(秒),float
- `x`, `y`: 归一化坐标(0-1),float
- `pupil_diameter`: 瞳孔直径(mm),float
- `validity`: 有效性(0/1),int

---

## 3. 新预处理方案设计

### 3.1 设计原则

```
原则1: 最小改动 - 在现有Pipeline基础上扩展
原则2: 数据保留 - 标记异常而非删除(保守模式)
原则3: 可选执行 - 用户可选择启用/禁用IVT检测
原则4: 向后兼容 - 不破坏现有V1数据流
```

### 3.2 新方案流程

```
CSV眼动数据
    ↓
[阶段1: 质量评估]
    ├─ QualityChecker (现有)
    ├─ 采样率检查
    ├─ 有效数据率
    └─ 噪声水平评估
    ↓
[阶段2: 保守清理]
    ├─ 范围裁剪(硬件限制)
    ├─ 移除validity=0样本
    ├─ 标记缺失值(不插值!)  ← 新增
    └─ 标记极端异常(生理极限) ← 新增
    ↓
[阶段3: 可选降噪]
    ├─ 条件启用(噪声>0.1°)  ← 修改
    ├─ 中值滤波(window=3)   ← 替换高斯
    └─ 不处理瞳孔数据
    ↓
[阶段4: IVT事件检测]  ← 新增
    ├─ 速度计算
    ├─ 注视/扫视分类(阈值30°/s)
    ├─ 自适应阈值(年龄/任务)
    └─ 事件序列生成
    ↓
输出
    ├─ processed_data.csv (带标记列)
    ├─ events.json (事件序列)
    └─ report.json (处理报告)
```

### 3.3 关键差异对比

| 项目 | 现有Pipeline | 新保守模式 |
|------|-------------|-----------|
| **缺失值** | 线性插值 | 标记(is_missing列) |
| **异常值** | 3sigma插值 | 标记(is_extreme列) |
| **平滑** | 强制高斯(σ=1.5) | 条件中值(w=3) |
| **事件检测** | 无 | IVT检测 |
| **眨眼处理** | 无 | ~~眨眼检测~~ **移除!** |
| **输出** | CSV | CSV + events.json + report.json |

**注意**: **不实现眨眼检测**,理由:
1. VR数据已经过实验控制,眨眼很少
2. 瞳孔数据可能不可靠
3. IVT本身会将眨眼期间标记为无效样本

---

## 4. 开发任务清单

### 4.1 新增文件清单

```
src/modules/module02_preprocessing/
│
├── conservative/               # 新增: 保守模式目录
│   ├── __init__.py
│   ├── conservative_cleaner.py      # 保守清理器
│   └── noise_reducer.py             # 条件降噪器
│
├── ivt/                        # 新增: IVT检测目录
│   ├── __init__.py
│   ├── velocity_calculator.py       # 速度计算
│   ├── ivt_detector.py              # IVT事件检测
│   ├── event_types.py               # 事件类型定义
│   └── adaptive_threshold.py        # 自适应阈值
│
├── reports/                    # 新增: 报告生成
│   ├── __init__.py
│   └── processing_reporter.py       # 处理报告生成器
│
└── configs/                    # 新增: 配置管理
    ├── __init__.py
    ├── conservative_config.py       # 保守模式配置
    └── legacy_config.py             # 兼容模式配置
```

### 4.2 修改文件清单

```
需要修改的现有文件:
├── pipeline.py                 # 集成新阶段
├── api.py                      # 新增IVT相关端点
└── __init__.py                 # 导出新组件
```

### 4.3 开发优先级

#### 第一阶段: 核心组件 (Week 1-2)

**任务1.1: 速度计算器**
```python
# ivt/velocity_calculator.py

class VelocityCalculator:
    """
    计算眼动速度

    输入: DataFrame with columns [timestamp, x, y]
    输出: DataFrame with additional column [velocity]
    """

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算点对点速度

        公式:
        distance = sqrt((x2-x1)^2 + (y2-y1)^2)  # 假设已归一化为角度
        velocity = distance / (t2-t1)  # °/s
        """
        pass
```

**任务1.2: IVT检测器**
```python
# ivt/ivt_detector.py

class IVTDetector:
    """
    I-VT算法事件检测

    参数:
    - velocity_threshold: 30 °/s (默认)
    - min_fixation_duration: 60 ms
    - merge_distance: 0.5 °
    - merge_time_window: 75 ms
    """

    def detect(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        执行IVT检测

        返回:
        - df_with_events: 添加event_type列的DataFrame
        - events: 事件列表
        """
        pass
```

**任务1.3: 保守清理器**
```python
# conservative/conservative_cleaner.py

class ConservativeCleaner:
    """
    保守数据清理

    特点:
    - 不插值
    - 仅标记
    - 保留原始数据
    """

    def clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        执行保守清理

        添加标记列:
        - is_missing: 缺失值标记
        - is_extreme: 极端异常标记
        """
        pass
```

#### 第二阶段: 集成和API (Week 3)

**任务2.1: 修改Pipeline**
```python
# pipeline.py (修改)

class Pipeline:
    def __init__(self):
        self.mode = 'conservative'  # 新增: 模式选择

    def process(self, df, config):
        # 1. 质量检查 (现有)
        # 2. 保守清理 (新增/替换DataCleaner)
        # 3. 条件降噪 (修改DataSmoother逻辑)
        # 4. IVT检测 (新增)
        pass
```

**任务2.2: 新增API端点**
```python
# api.py (新增)

@m02_bp.route('/preprocessing/ivt-process', methods=['POST'])
def ivt_process():
    """
    IVT预处理接口

    Request Body:
    {
      "subject_id": "v2_control_001",
      "input_file": "path/to/raw.csv",
      "config": {
        "velocity_threshold": 30,
        "enable_noise_reduction": false
      },
      "metadata": {
        "age": 65,
        "task_type": "cognitive"
      }
    }

    Response:
    {
      "success": true,
      "output_files": {
        "processed_csv": "path/to/processed.csv",
        "events_json": "path/to/events.json",
        "report_json": "path/to/report.json"
      },
      "summary": {
        "fixations": 123,
        "saccades": 98,
        "data_quality": 85.5
      }
    }
    """
    pass
```

#### 第三阶段: 前端和测试 (Week 4)

**任务3.1: 前端配置界面**
- 在Module02数据预处理页面添加IVT选项
- 参数调节器(velocity_threshold, min_fixation_duration等)
- 结果可视化(事件时间线图)

**任务3.2: 测试**
- 单元测试: 每个组件独立测试
- 集成测试: 完整流程测试
- 性能测试: 处理100个受试者的时间

---

## 5. API接口规范

### 5.1 新增端点列表

```python
# 1. IVT预处理(单文件)
POST /api/m02/preprocessing/ivt-process
Body: {subject_id, input_file, config, metadata}
Return: {success, output_files, summary}

# 2. IVT批量处理
POST /api/m02/preprocessing/ivt-batch-process
Body: {subjects: [{subject_id, input_file, metadata}, ...], config}
Return: {success, summary, results: [...]}

# 3. 获取IVT配置模板
GET /api/m02/preprocessing/ivt-config
Return: {conservative_config, legacy_config}

# 4. 查询事件数据
GET /api/m02/preprocessing/events/<subject_id>
Return: {events: [...], statistics: {...}}
```

### 5.2 API调用示例

**示例1: 处理单个受试者**
```bash
curl -X POST http://localhost:9090/api/m02/preprocessing/ivt-process \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "v2_control_001",
    "input_file": "data/raw/v2_control_001_Q1.csv",
    "config": {
      "velocity_threshold": 30,
      "enable_noise_reduction": false,
      "min_fixation_duration": 60
    },
    "metadata": {
      "age": 65,
      "task_type": "cognitive_assessment",
      "question": "Q1"
    }
  }'
```

**响应**:
```json
{
  "success": true,
  "subject_id": "v2_control_001",
  "output_files": {
    "processed_csv": "data/preprocessing_results/v2_control_001/Q1_processed.csv",
    "events_json": "data/preprocessing_results/v2_control_001/Q1_events.json",
    "report_json": "data/preprocessing_results/v2_control_001/Q1_report.json"
  },
  "summary": {
    "original_points": 6000,
    "valid_points": 5850,
    "fixations": 123,
    "saccades": 98,
    "mean_fixation_duration_ms": 245.6,
    "data_quality_score": 85.5,
    "processing_time_ms": 156
  }
}
```

---

## 6. 数据流和存储

### 6.1 完整数据流

```
1. V2原始数据导入
   scan_result_v2.json
        ↓
   [V2DataManager.batch_import_v2_subjects]
        ↓
   data/subject_info/{group}/{subject_id}.json
        ↓ (metadata.data_path指向原始CSV)

2. IVT预处理
   原始CSV (从data_path读取)
        ↓
   [Pipeline with IVT]
        ├─ QualityChecker
        ├─ ConservativeCleaner
        ├─ NoiseReducer (可选)
        └─ IVTDetector
        ↓
   输出3个文件:
        ├─ {subject_id}_Q{n}_processed.csv
        ├─ {subject_id}_Q{n}_events.json
        └─ {subject_id}_Q{n}_report.json

3. 后续分析
   events.json
        ↓
   [Module05: RQA Pipeline]
        ↓
   RQA特征
```

### 6.2 输出文件格式

#### 6.2.1 processed.csv

```csv
timestamp,x,y,pupil_diameter,validity,velocity,event_type,event_id,is_missing,is_extreme
0.0167,0.512,0.488,3.2,1,0,fixation,0,False,False
0.0333,0.515,0.490,3.2,1,15.2,fixation,0,False,False
0.0500,0.518,0.491,3.1,1,12.8,fixation,0,False,False
0.0667,0.650,0.520,3.0,1,850.3,saccade,1,False,False
...
```

**新增列说明**:
- `velocity`: 速度(°/s)
- `event_type`: 事件类型(fixation/saccade/unknown)
- `event_id`: 事件ID(同一事件的样本ID相同)
- `is_missing`: 缺失值标记
- `is_extreme`: 极端异常标记

#### 6.2.2 events.json

```json
{
  "subject_id": "v2_control_001",
  "question": "Q1",
  "processing_date": "2025-10-06T14:30:00",
  "config": {
    "velocity_threshold": 30,
    "min_fixation_duration": 60
  },
  "events": [
    {
      "event_id": 0,
      "type": "fixation",
      "start_time": 0.0167,
      "end_time": 0.2833,
      "duration_ms": 266.6,
      "start_index": 0,
      "end_index": 15,
      "center_x": 0.515,
      "center_y": 0.489,
      "dispersion": 0.025
    },
    {
      "event_id": 1,
      "type": "saccade",
      "start_time": 0.3000,
      "end_time": 0.3333,
      "duration_ms": 33.3,
      "start_index": 16,
      "end_index": 18,
      "start_x": 0.518,
      "start_y": 0.491,
      "end_x": 0.650,
      "end_y": 0.520,
      "amplitude": 0.145,
      "peak_velocity": 892.5
    },
    ...
  ],
  "statistics": {
    "fixation_count": 123,
    "saccade_count": 98,
    "mean_fixation_duration_ms": 245.6,
    "mean_saccade_amplitude": 0.182,
    "fixation_rate_per_second": 12.3
  }
}
```

#### 6.2.3 report.json

```json
{
  "subject_id": "v2_control_001",
  "question": "Q1",
  "processing_date": "2025-10-06T14:30:00",
  "processing_mode": "conservative",
  "stages": [
    {
      "stage": 1,
      "name": "QualityAssessment",
      "status": "success",
      "metrics": {
        "sampling_rate": 60.2,
        "valid_data_rate": 0.975,
        "noise_level": 0.08,
        "quality_score": 85.5
      }
    },
    {
      "stage": 2,
      "name": "ConservativeCleaning",
      "status": "success",
      "metrics": {
        "missing_marked": 50,
        "extreme_marked": 10,
        "points_removed": 60
      }
    },
    {
      "stage": 3,
      "name": "NoiseReduction",
      "status": "skipped",
      "reason": "Noise level below threshold"
    },
    {
      "stage": 4,
      "name": "IVTDetection",
      "status": "success",
      "metrics": {
        "fixations_detected": 123,
        "saccades_detected": 98,
        "mean_velocity": 45.6
      }
    }
  ],
  "summary": {
    "total_processing_time_ms": 156,
    "original_points": 6000,
    "final_points": 5940,
    "data_quality": "Good"
  }
}
```

---

## 7. 配置参数详解

### 7.1 保守模式默认配置

```python
# configs/conservative_config.py

CONSERVATIVE_CONFIG = {
    # 质量评估
    'quality_assessment': {
        'expected_sampling_rate': 60,
        'sampling_rate_tolerance': 10,
        'min_valid_data_rate': 0.75,
        'noise_threshold': 0.1  # °
    },

    # 保守清理
    'cleaning': {
        'clip_range': True,
        'x_range': [0, 1],
        'y_range': [0, 1],
        'remove_invalid_samples': True,  # validity=0
        'missing_strategy': 'mark_only',  # 标记而非插值
        'extreme_outlier_threshold': 1000  # °/s (生理极限)
    },

    # 条件降噪
    'noise_reduction': {
        'enabled': False,  # 默认关闭
        'auto_enable_threshold': 0.1,  # 噪声>0.1°时启用
        'method': 'median',
        'window_size': 3
    },

    # IVT检测
    'ivt': {
        'velocity_threshold': 30,  # °/s
        'min_fixation_duration': 60,  # ms
        'min_saccade_duration': 10,  # ms
        'merge_distance': 0.5,  # °
        'merge_time_window': 75,  # ms
        'adaptive_threshold': {
            'enabled': True,
            'age_factor': True,  # 年龄>65时降低15%
            'task_factor': True  # 阅读任务降低20%
        }
    }
}
```

### 7.2 自适应阈值计算

```python
# ivt/adaptive_threshold.py

def get_adaptive_threshold(base_threshold: float, metadata: Dict) -> float:
    """
    计算自适应IVT阈值

    Args:
        base_threshold: 基础阈值(默认30°/s)
        metadata: 包含age, task_type的元数据

    Returns:
        调整后的阈值
    """
    threshold = base_threshold

    # 年龄调整
    age = metadata.get('age')
    if age and age > 65:
        threshold *= 0.85  # 老年人扫视慢15%

    # 任务类型调整
    task_type = metadata.get('task_type', '')
    if 'reading' in task_type.lower():
        threshold *= 0.8  # 阅读任务降低20%
    elif 'exploration' in task_type.lower():
        threshold *= 1.15  # 探索任务提高15%

    return threshold
```

---

## 8. 测试用例

### 8.1 单元测试

```python
# tests/test_ivt_detector.py

def test_ivt_basic_detection():
    """测试基本IVT检测"""
    # 构造测试数据: 2个注视 + 1个扫视
    df = pd.DataFrame({
        'timestamp': np.linspace(0, 1, 60),
        'x': [0.5]*30 + [0.8]*30,  # 注视1 -> 扫视 -> 注视2
        'y': [0.5]*30 + [0.6]*30
    })

    detector = IVTDetector(velocity_threshold=30)
    df_result, events = detector.detect(df)

    assert len(events) >= 2
    assert events[0]['type'] == 'fixation'
    assert events[1]['type'] in ['saccade', 'fixation']

def test_adaptive_threshold():
    """测试自适应阈值"""
    threshold = get_adaptive_threshold(
        base_threshold=30,
        metadata={'age': 70, 'task_type': 'reading'}
    )

    # 70岁老人,阅读任务: 30 * 0.85 * 0.8 = 20.4
    assert threshold < 30
    assert 20 <= threshold <= 21
```

### 8.2 集成测试

```python
# tests/test_pipeline_ivt.py

def test_full_ivt_pipeline():
    """测试完整IVT流程"""
    # 准备测试CSV
    df = pd.read_csv('tests/data/sample_eyetracking.csv')

    # 执行Pipeline
    pipeline = Pipeline(mode='conservative')
    df_processed, events, report = pipeline.process(
        df=df,
        config=CONSERVATIVE_CONFIG,
        metadata={'age': 65, 'task_type': 'cognitive'}
    )

    # 验证输出
    assert 'velocity' in df_processed.columns
    assert 'event_type' in df_processed.columns
    assert len(events) > 0
    assert report['stages'][3]['name'] == 'IVTDetection'
    assert report['summary']['data_quality'] in ['Excellent', 'Good', 'Fair', 'Poor']
```

---

## 9. 性能要求

### 9.1 处理速度

| 数据规模 | 采样率 | 时长 | 预期处理时间 |
|---------|--------|------|-------------|
| 小 | 60Hz | 1分钟(3600点) | <50ms |
| 中 | 60Hz | 5分钟(18000点) | <200ms |
| 大 | 60Hz | 10分钟(36000点) | <500ms |
| 批量100个 | 60Hz | 5分钟/个 | <30秒 |

### 9.2 内存占用

- 单个受试者处理: <100MB
- 批量处理: <500MB
- 峰值内存: <1GB

---

## 10. 部署检查清单

### 10.1 代码完成度

- [ ] VelocityCalculator实现并测试
- [ ] IVTDetector实现并测试
- [ ] ConservativeCleaner实现并测试
- [ ] Pipeline集成并测试
- [ ] API端点实现并测试
- [ ] 前端界面完成

### 10.2 文档完成度

- [ ] 代码注释完整
- [ ] API文档完整
- [ ] 用户手册更新
- [ ] 配置说明文档

### 10.3 测试覆盖

- [ ] 单元测试覆盖率>80%
- [ ] 集成测试通过
- [ ] 性能测试达标
- [ ] 边界情况测试

---

## 11. 常见问题FAQ

### Q1: 为什么不检测眨眼?

**A**:
1. VR实验设计已最小化眨眼影响
2. IVT会自然地将眨眼期间标记为无效
3. 瞳孔数据在VR中可能不可靠
4. 简化实现,减少复杂度

### Q2: 如何处理缺失值?

**A**:
保守模式**不插值**,仅标记(`is_missing=True`)。原因:
- 眨眼时眼球位置不可预测
- 插值会创造虚假注视路径
- 后续分析可基于事件序列,不依赖原始样本

### Q3: 速度计算是否需要转换为角度?

**A**:
如果x,y已归一化(0-1),需要根据FOV转换:
```python
# 假设VR FOV=110°
fov_horizontal = 110  # 度
fov_vertical = 110

dx_degree = dx * fov_horizontal
dy_degree = dy * fov_vertical
angular_distance = sqrt(dx_degree^2 + dy_degree^2)
```

### Q4: 如何选择velocity_threshold?

**A**:
- **默认**: 30°/s (Tobii标准)
- **阅读任务**: 25°/s (更多小注视)
- **探索任务**: 35°/s (更多大扫视)
- **老年人**: 减少15%

---

## 附录A: 数学公式汇总

### A.1 速度计算

```
给定两点 P1(x1, y1, t1) 和 P2(x2, y2, t2)

欧氏距离(归一化坐标):
d = √[(x2-x1)² + (y2-y1)²]

转换为角度(假设FOV=110°):
d_degree = d × 110

速度(°/s):
v = d_degree / (t2 - t1)
```

### A.2 IVT分类

```
IF v < threshold:
    event_type = "fixation"
ELSE:
    event_type = "saccade"
```

### A.3 注视中心计算

```
给定注视事件包含样本点 {(x1,y1), (x2,y2), ..., (xn,yn)}

中心坐标:
center_x = mean(x1, x2, ..., xn)
center_y = mean(y1, y2, ..., yn)

离散度:
dispersion = max(distance(pi, center))
```

---

**文档结束**

*本文档为Module02 IVT预处理的完整开发规范,涵盖输入数据、架构设计、开发任务、API规范和测试要求。如有疑问,请联系开发团队。*
