# Module01 数据可视化 - 开发规划文档
# Module01 Data Visualization - Development Plan

**文档版本：** v3.0 - 真实数据对接版
**创建日期：** 2025-10-02
**最后更新：** 2025-10-02
**状态：** 📋 待用户确认

---

## 📋 目录 / Table of Contents

1. [模块概述](#模块概述)
2. [当前状态分析](#当前状态分析)
3. [Module00数据结构分析](#module00数据结构分析)
4. [核心问题与解决方案](#核心问题与解决方案)
5. [数据对接设计](#数据对接设计)
6. [开发任务清单](#开发任务清单)
7. [API设计升级](#api设计升级)
8. [前端组件升级](#前端组件升级)
9. [测试计划](#测试计划)
10. [实施优先级](#实施优先级)

---

## 📖 模块概述

### 功能定位
Module01是**数据可视化模块**，负责加载Module00导入的原始眼动数据并进行可视化展示。

### 核心功能
1. ✅ 从Module00导入的数据中加载真实数据（非模拟数据）
2. ✅ 三级联动选择：组别 → 受试者 → 任务
3. ✅ 眼动轨迹图可视化（Gaze Trajectory）
4. ✅ 热力图可视化（Heatmap）
5. ✅ 数据统计信息展示
6. ✅ 区分v1 (legacy)和v2 (eye_tracking)数据

### ⚠️ 核心需求（用户强调）
**Module01必须使用Module00导入的真实数据，而非模拟数据！**

---

## 🔍 当前状态分析

### ✅ 已完成部分

1. **Backend API基础实现**
   - 模块路径：`src/web/modules/module01_data_visualization/`
   - 已创建文件：`api.py`, `service.py`, `__init__.py`
   - Blueprint已注册：`/api/data/*`

2. **现有API端点**
   ```
   GET /api/data/groups         - 获取组别列表
   GET /api/data/subjects       - 获取受试者列表
   GET /api/data/tasks          - 获取任务列表
   GET /api/data/raw            - 加载原始眼动数据
   ```

3. **Frontend组件**
   - 页面文件：`frontend/src/pages/Module01/Module01.jsx`
   - 图表组件：`GazeTrajectoryChart`, `HeatmapChart`
   - 数据服务：`dataService.js`

### ❌ 存在的核心问题

#### 问题1：数据源不一致 🚨 **最严重**

**当前Service读取路径：**
```python
data_file = self.data_root / group / subject_id / task_filename
# 示例：data/control/s001/Q1.csv
```

**Module00实际导入路径：**
```
data/01_raw/control/control_legacy_1_q1.csv
data/01_raw/mci/mci_legacy_5_q2.csv
data/01_raw/ad/ad_eyetrack_s010_q3.csv
```

**问题：** Service读取的是旧的模拟数据目录，完全没有使用Module00导入的真实数据！

#### 问题2：未使用元数据

**Module00维护的元数据：**
- `data/01_raw/clinical/subject_metadata.json` - 受试者详细信息
- `data/01_raw/clinical/import_history.json` - 导入历史

**问题：** Module01完全没有利用这些元数据，无法：
- 区分v1 (legacy)和v2 (eye_tracking)数据
- 获取MMSE评分信息
- 获取导入时间等额外信息

#### 问题3：文件命名规则不匹配

**Module00命名：** `{group}_{source_type}_{number}_{task}.csv`
- 示例：`control_legacy_1_q1.csv`, `mci_eyetrack_s005_q3.csv`

**Module01期望命名：** `{subject_id}/Q*.csv`
- 示例：`control_01/Q1.csv`

---

## 📊 Module00数据结构分析

### 1. 数据存储结构

```
new_project/data/01_raw/
├── control/                                    # 对照组
│   ├── control_legacy_1_q1.csv                # Legacy数据: 编号1, 任务Q1
│   ├── control_legacy_1_q2.csv
│   ├── control_legacy_1_q3.csv
│   ├── control_legacy_1_q4.csv
│   ├── control_legacy_1_q5.csv
│   ├── control_legacy_10_q1.csv               # Legacy数据: 编号10
│   ├── ...
│   ├── control_eyetrack_s001_q1.csv          # Eye Tracking数据: s001
│   └── ...
├── mci/                                        # MCI组
│   ├── mci_legacy_1_q1.csv
│   ├── mci_eyetrack_s005_q1.csv
│   └── ...
├── ad/                                         # AD组
│   ├── ad_legacy_1_q1.csv
│   ├── ad_eyetrack_s010_q1.csv
│   └── ...
└── clinical/                                   # 临床数据
    ├── subject_metadata.json                  # 受试者元数据 ⭐核心
    └── import_history.json                    # 导入历史
```

### 2. 文件命名规则

**格式：** `{group}_{source_type}_{number}_{task}.csv`

**组成部分：**
- `{group}`: 组别 - control/mci/ad
- `{source_type}`: 数据来源 - legacy/eyetrack
- `{number}`: 编号 - 1, 2, 3, ... 或 s001, s002, ...
- `{task}`: 任务 - q1, q2, q3, q4, q5

**示例：**
```
control_legacy_1_q1.csv       → 对照组, Legacy数据, 编号1, 任务Q1
mci_eyetrack_s005_q3.csv      → MCI组, Eye Tracking数据, s005, 任务Q3
ad_legacy_15_q2.csv           → AD组, Legacy数据, 编号15, 任务Q2
```

### 3. CSV数据格式

```csv
timestamp,x,y
2025-01-23 15:20:02.948,0.211183,0.905262
2025-01-23 15:20:03.062,0.21236,0.903503
2025-01-23 15:20:03.190,0.214982,0.897665
...
```

**列说明：**
- `timestamp`: 时间戳（字符串格式，带日期时间）
- `x`: X坐标（归一化，范围0-1）
- `y`: Y坐标（归一化，范围0-1）

### 4. 元数据结构（核心）⭐

`data/01_raw/clinical/subject_metadata.json`:

```json
{
  "control_legacy_1": {
    "subject_id": "control_legacy_1",
    "group": "control",
    "data_version": "v1",
    "roi_layout": "v1",
    "source_type": "legacy",
    "source_path": "C:\\...\\data\\control_raw\\control_group_1",
    "import_date": "2025-10-02T01:07:50.655133",
    "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
    "has_mmse": false,
    "mmse_scores": null
  },
  "mci_eyetrack_s005": {
    "subject_id": "mci_eyetrack_s005",
    "group": "mci",
    "data_version": "v2",
    "roi_layout": "v2",
    "source_type": "eye_tracking",
    "source_path": "C:\\...\\eye_tracking_data\\hospital_id_028",
    "import_date": "2025-10-02T01:08:15.123456",
    "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
    "has_mmse": true,
    "mmse_scores": {
      "total": 28,
      "q1_time_orientation": 5,
      "q2_place_orientation": 5,
      ...
    }
  }
}
```

**关键字段说明：**
- `subject_id`: 唯一标识符（用于构建文件路径）
- `group`: 组别（control/mci/ad）
- `data_version`: 数据版本（v1=legacy旧版, v2=eye_tracking新版）
- `roi_layout`: ROI布局版本（v1/v2）
- `source_type`: 数据来源类型（legacy/eye_tracking）
- `tasks_available`: 可用任务列表（通常为q1-q5）
- `has_mmse`: 是否有MMSE评分
- `mmse_scores`: MMSE评分详情（如有）

---

## 🎯 核心问题与解决方案

### 问题总结表

| 问题 | 严重程度 | 解决方案 | 优先级 |
|-----|---------|---------|--------|
| 数据路径不一致 | 🔴 严重 | 修改Service读取 `data/01_raw/{group}/{subject_id}_{task}.csv` | P0 |
| 未使用元数据 | 🟡 中等 | 读取 `subject_metadata.json` 获取受试者列表和信息 | P0 |
| 无法区分v1/v2 | 🟡 中等 | 从元数据读取 `data_version` 和 `roi_layout` | P1 |
| Subject ID格式 | 🟢 轻微 | 使用完整ID如 `control_legacy_1` | P0 |

---

## 🔗 数据对接设计

### 核心设计原则

1. **以元数据为准**
   - 所有受试者列表从 `subject_metadata.json` 读取
   - 根据元数据确定数据版本、任务列表
   - 利用元数据提供MMSE等额外信息

2. **统一数据路径**
   - 所有CSV文件从 `data/01_raw/{group}/` 读取
   - 文件命名遵循：`{subject_id}_{task}.csv`

3. **保持API兼容性**
   - 前端API调用方式保持不变
   - 后端Service层适配真实数据结构
   - 新增字段采用可选模式

### 数据流架构

```
用户操作: 选择组别 → 选择受试者 → 选择任务 → 加载数据
          ↓            ↓             ↓           ↓
API请求:  /groups → /subjects → /tasks → /raw
          ↓            ↓             ↓           ↓
Backend:  扫描目录 → 读取元数据 → 从元数据获取 → 读取CSV文件
                    ↓             ↓           ↓
数据源:            subject_     tasks_      {subject_id}_
                   metadata.json available    {task}.csv
```

### 对接方案（推荐）

#### 方案：元数据驱动 + 文件读取

**优点：**
- ✅ 数据权威（基于Module00维护的元数据）
- ✅ 支持增量导入（新数据导入后自动可用）
- ✅ 可区分数据版本和来源
- ✅ 提供MMSE等额外信息
- ✅ 性能良好（元数据文件小，一次性加载）

**实现流程：**

```python
# Step 1: 初始化时加载元数据
def __init__(self):
    self.metadata = self.load_metadata()  # 读取 subject_metadata.json

# Step 2: 获取组别列表
def get_groups():
    groups_stats = {}
    for subject_id, meta in self.metadata.items():
        group = meta['group']
        if group not in groups_stats:
            groups_stats[group] = {'count': 0, 'v1': 0, 'v2': 0}
        groups_stats[group]['count'] += 1
        if meta['data_version'] == 'v1':
            groups_stats[group]['v1'] += 1
        else:
            groups_stats[group]['v2'] += 1
    return groups_stats

# Step 3: 获取受试者列表（按group过滤）
def get_subjects(group):
    subjects = []
    for subject_id, meta in self.metadata.items():
        if meta['group'] == group:
            subjects.append({
                'id': subject_id,
                'task_count': len(meta['tasks_available']),
                'data_version': meta['data_version'],
                'source_type': meta['source_type'],
                'has_mmse': meta['has_mmse']
            })
    return subjects

# Step 4: 获取任务列表（从元数据）
def get_tasks(group, subject_id):
    meta = self.metadata.get(subject_id)
    return meta['tasks_available'] if meta else []

# Step 5: 加载原始数据（构建路径并读取CSV）
def load_raw_data(group, subject_id, task_id):
    # 构建文件路径
    file_path = f"data/01_raw/{group}/{subject_id}_{task_id}.csv"

    # 读取CSV
    df = pd.read_csv(file_path)

    # 获取元数据
    meta = self.metadata.get(subject_id, {})

    return {
        'data': df.to_dict('records'),
        'stats': {...},
        'metadata': meta
    }
```

---

## ✅ 开发任务清单

### Phase 1: Backend数据对接（🔴 核心任务 - 必须完成）

#### Task 1.1: 创建MetadataReader类
**优先级：** P0
**工作量：** 1小时

**文件：** `src/web/modules/module01_data_visualization/metadata_reader.py`

```python
class MetadataReader:
    """元数据读取器 - 读取Module00维护的subject_metadata.json"""

    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path)
        self.metadata = {}
        self.load_metadata()

    def load_metadata(self):
        """加载元数据文件"""
        pass

    def get_all_subjects(self):
        """获取所有受试者"""
        pass

    def get_subjects_by_group(self, group: str):
        """按组别过滤受试者"""
        pass

    def get_subjects_by_version(self, data_version: str):
        """按数据版本过滤"""
        pass

    def get_subject_info(self, subject_id: str):
        """获取单个受试者信息"""
        pass
```

#### Task 1.2: 重构DataVisualizationService
**优先级：** P0
**工作量：** 2小时

**修改文件：** `src/web/modules/module01_data_visualization/service.py`

**需修改的方法：**
1. `__init__()` - 初始化MetadataReader
2. `get_groups()` - 从元数据统计组别信息
3. `get_subjects()` - 从元数据读取受试者列表
4. `get_tasks()` - 从元数据读取任务列表
5. `load_raw_data()` - 修改文件路径构建逻辑

**关键改动：**
```python
# 旧代码：
data_file = self.data_root / group / subject_id / task_filename

# 新代码：
data_file = self.data_root / "01_raw" / group / f"{subject_id}_{task_id}.csv"
```

#### Task 1.3: 更新文件路径逻辑
**优先级：** P0
**工作量：** 30分钟

**核心改动：**
- 数据根目录：`data/` → `data/01_raw/`
- 文件路径：`{group}/{subject_id}/Q*.csv` → `{group}/{subject_id}_{task}.csv`

---

### Phase 2: API响应增强

#### Task 2.1: 扩展groups API响应
**优先级：** P1
**工作量：** 30分钟

**当前响应：**
```json
{
  "success": true,
  "data": [
    {"id": "control", "name": "对照组", "count": 22}
  ]
}
```

**新响应（新增字段）：**
```json
{
  "success": true,
  "data": [
    {
      "id": "control",
      "name": "对照组",
      "count": 54,
      "v1_count": 22,
      "v2_count": 32,
      "has_mmse_count": 10
    }
  ]
}
```

#### Task 2.2: 扩展subjects API响应
**优先级：** P1
**工作量：** 30分钟

**新增返回字段：**
- `data_version`: "v1" / "v2"
- `source_type`: "legacy" / "eye_tracking"
- `has_mmse`: true / false
- `import_date`: ISO格式时间戳

#### Task 2.3: 扩展raw data API响应
**优先级：** P1
**工作量：** 30分钟

**新增metadata字段：**
- `data_version`
- `source_type`
- `roi_layout`
- `import_date`

---

### Phase 3: Frontend组件优化

#### Task 3.1: 更新Module01主页面
**优先级：** P1
**工作量：** 1小时

**文件：** `frontend/src/pages/Module01/Module01.jsx`

**新增功能：**
1. 显示数据版本徽章（v1蓝色, v2绿色）
2. 显示数据来源标签（Legacy/Eye Tracking）
3. 显示MMSE可用状态

#### Task 3.2: 创建SubjectInfo卡片组件
**优先级：** P2
**工作量：** 1小时

**新组件：** `frontend/src/components/Module01/SubjectInfo.jsx`

**显示内容：**
- 受试者ID
- 数据版本标签
- 数据来源
- 导入日期
- MMSE状态

#### Task 3.3: 添加数据过滤器
**优先级：** P2
**工作量：** 1小时

**过滤选项：**
- 全部数据
- 仅v1 (Legacy)
- 仅v2 (Eye Tracking)
- 仅有MMSE评分

#### Task 3.4: 错误处理优化
**优先级：** P2
**工作量：** 30分钟

**改进点：**
- 数据文件不存在的友好提示
- 加载失败的详细错误信息
- 空数据状态的引导提示

---

### Phase 4: i18n国际化

#### Task 4.1: 添加Module01翻译文件
**优先级：** P2
**工作量：** 1小时

**文件：**
- `frontend/src/locales/zh-CN/module01.json`
- `frontend/src/locales/en-US/module01.json`
- `frontend/src/locales/ms-MY/module01.json`

**翻译内容：**
- 页面标题和说明
- 数据选择器标签
- 统计信息标签
- 错误提示信息

#### Task 4.2: 更新组件使用翻译
**优先级：** P2
**工作量：** 30分钟

**修改文件：**
- Module01.jsx
- SubjectInfo.jsx
- GazeTrajectoryChart.jsx
- HeatmapChart.jsx

---

### Phase 5: 测试与验证

#### Task 5.1: Backend API测试
**优先级：** P0
**工作量：** 1.5小时

**测试用例：**
1. ✅ 测试3个组别（control/mci/ad）的数据加载
2. ✅ 测试v1和v2数据都能正确返回
3. ✅ 测试边界情况（空组别、不存在的subject_id）
4. ✅ 测试CSV文件缺失的错误处理
5. ✅ 测试元数据文件不存在的降级方案

#### Task 5.2: Frontend功能测试
**优先级：** P0
**工作量：** 1小时

**测试流程：**
1. ✅ 测试三级联动选择（组别 → 受试者 → 任务）
2. ✅ 测试数据可视化显示（轨迹图、热力图）
3. ✅ 测试数据统计信息准确性
4. ✅ 测试v1/v2数据标签显示
5. ✅ 测试语言切换（中文/英文/马来文）

#### Task 5.3: 端到端集成测试
**优先级：** P1
**工作量：** 1小时

**测试场景：**
1. ✅ Legacy数据完整流程测试
2. ✅ Eye Tracking数据完整流程测试
3. ✅ 有MMSE评分的受试者测试
4. ✅ 跨组别切换测试

#### Task 5.4: 性能测试
**优先级：** P2
**工作量：** 1小时

**测试指标：**
- 大CSV文件（>10MB）加载时间
- 图表渲染性能
- 元数据加载缓存效果

---

## 🔌 API设计升级

### API 1: GET /api/data/groups

**优化后响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": "control",
      "name": "对照组 / Control Group / Kumpulan Kawalan",
      "count": 54,
      "v1_count": 22,
      "v2_count": 32,
      "has_mmse_count": 10,
      "description": "认知正常的对照组受试者"
    },
    {
      "id": "mci",
      "name": "MCI组 / MCI Group / Kumpulan MCI",
      "count": 42,
      "v1_count": 22,
      "v2_count": 20,
      "has_mmse_count": 42
    },
    {
      "id": "ad",
      "name": "AD组 / AD Group / Kumpulan AD",
      "count": 42,
      "v1_count": 21,
      "v2_count": 21,
      "has_mmse_count": 42
    }
  ],
  "summary": {
    "total_subjects": 138,
    "total_v1": 65,
    "total_v2": 73,
    "total_with_mmse": 94
  }
}
```

---

### API 2: GET /api/data/subjects?group=control

**优化后响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": "control_legacy_1",
      "task_count": 5,
      "data_version": "v1",
      "roi_layout": "v1",
      "source_type": "legacy",
      "has_mmse": false,
      "import_date": "2025-10-02T01:07:50.655133",
      "display_name": "Control Legacy #1"
    },
    {
      "id": "control_eyetrack_s001",
      "task_count": 5,
      "data_version": "v2",
      "roi_layout": "v2",
      "source_type": "eye_tracking",
      "has_mmse": true,
      "mmse_total": 30,
      "import_date": "2025-10-02T01:08:15.123456",
      "display_name": "Control Eye Tracking #s001"
    }
  ],
  "count": 54,
  "filters": {
    "group": "control",
    "data_version": "all"
  }
}
```

---

### API 3: GET /api/data/tasks?group=control&subject_id=control_legacy_1

**保持不变，但增加验证：**
```json
{
  "success": true,
  "data": ["q1", "q2", "q3", "q4", "q5"],
  "subject_id": "control_legacy_1",
  "group": "control"
}
```

---

### API 4: GET /api/data/raw?group=control&subject_id=control_legacy_1&task_id=q1

**优化后响应（新增metadata字段）：**
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2025-01-23 15:20:02.948",
      "x": 0.211183,
      "y": 0.905262
    },
    ...
  ],
  "stats": {
    "total_points": 1523,
    "duration": 45320.5,
    "x_range": [0.0123, 0.9876],
    "y_range": [0.0567, 0.9543],
    "sampling_rate": 90.0
  },
  "metadata": {
    "subject_id": "control_legacy_1",
    "group": "control",
    "task": "q1",
    "data_version": "v1",
    "roi_layout": "v1",
    "source_type": "legacy",
    "import_date": "2025-10-02T01:07:50.655133",
    "has_mmse": false,
    "file_path": "data/01_raw/control/control_legacy_1_q1.csv"
  }
}
```

---

## 🎨 前端组件升级

### 组件结构

```
frontend/src/pages/Module01/
├── Module01.jsx                 # 主页面（更新）
└── components/
    ├── DataSelector.jsx         # 数据选择器
    ├── SubjectInfo.jsx          # 受试者信息卡片（新增）⭐
    ├── DataStats.jsx            # 数据统计
    ├── VersionBadge.jsx         # 版本徽章（新增）⭐
    └── VisualizationTabs.jsx    # 可视化标签页
```

### 新增组件1：VersionBadge.jsx

**功能：** 显示数据版本标签

```jsx
const VersionBadge = ({ version, sourceType }) => {
  const versionConfig = {
    v1: { color: 'blue', text: 'v1 Legacy' },
    v2: { color: 'green', text: 'v2 Eye Tracking' }
  };

  const config = versionConfig[version];

  return (
    <Space>
      <Tag color={config.color}>{config.text}</Tag>
      <Text type="secondary">{sourceType}</Text>
    </Space>
  );
};
```

### 新增组件2：SubjectInfo.jsx

**功能：** 显示受试者详细信息

```jsx
const SubjectInfo = ({ subjectData }) => {
  const { t } = useTranslation('module01');

  if (!subjectData) return null;

  return (
    <Card title={t('subjectInfo.title')} size="small">
      <Descriptions column={2} size="small">
        <Descriptions.Item label={t('subjectInfo.id')}>
          {subjectData.id}
        </Descriptions.Item>
        <Descriptions.Item label={t('subjectInfo.version')}>
          <VersionBadge
            version={subjectData.data_version}
            sourceType={subjectData.source_type}
          />
        </Descriptions.Item>
        <Descriptions.Item label={t('subjectInfo.importDate')}>
          {new Date(subjectData.import_date).toLocaleDateString()}
        </Descriptions.Item>
        <Descriptions.Item label={t('subjectInfo.mmse')}>
          {subjectData.has_mmse ? (
            <Tag color="success">
              {t('subjectInfo.mmseAvailable')} (Total: {subjectData.mmse_total})
            </Tag>
          ) : (
            <Tag>{t('subjectInfo.mmseNotAvailable')}</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label={t('subjectInfo.taskCount')}>
          {subjectData.task_count} {t('subjectInfo.tasks')}
        </Descriptions.Item>
        <Descriptions.Item label={t('subjectInfo.roiLayout')}>
          <Tag color={subjectData.roi_layout === 'v1' ? 'blue' : 'green'}>
            ROI {subjectData.roi_layout}
          </Tag>
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};
```

---

## 🧪 测试计划

### 单元测试

#### Backend测试

**文件：** `tests/test_module01_service.py`

```python
def test_metadata_reader():
    """测试元数据读取器"""
    reader = MetadataReader("data/01_raw/clinical/subject_metadata.json")

    # 测试加载
    assert len(reader.metadata) > 0

    # 测试按组过滤
    control_subjects = reader.get_subjects_by_group('control')
    assert len(control_subjects) > 0

    # 测试按版本过滤
    v1_subjects = reader.get_subjects_by_version('v1')
    v2_subjects = reader.get_subjects_by_version('v2')
    assert len(v1_subjects) > 0
    assert len(v2_subjects) > 0

def test_get_groups():
    """测试组别API"""
    service = DataVisualizationService()
    result = service.get_groups()

    assert result['success'] == True
    assert len(result['data']) == 3

    # 验证统计准确性
    total = sum(g['count'] for g in result['data'])
    assert total == result['summary']['total_subjects']

def test_load_raw_data_v1():
    """测试加载v1数据"""
    service = DataVisualizationService()
    result = service.load_raw_data('control', 'control_legacy_1', 'q1')

    assert result['success'] == True
    assert len(result['data']) > 0
    assert result['metadata']['data_version'] == 'v1'
    assert result['metadata']['roi_layout'] == 'v1'

def test_load_raw_data_v2():
    """测试加载v2数据"""
    service = DataVisualizationService()
    result = service.load_raw_data('mci', 'mci_eyetrack_s005', 'q2')

    assert result['success'] == True
    assert len(result['data']) > 0
    assert result['metadata']['data_version'] == 'v2'
    assert result['metadata']['roi_layout'] == 'v2'
```

#### Frontend测试

**文件：** `frontend/src/pages/Module01/__tests__/Module01.test.jsx`

```javascript
describe('Module01 Component', () => {
  test('显示版本徽章', () => {
    const subjectData = {
      id: 'control_legacy_1',
      data_version: 'v1',
      source_type: 'legacy'
    };

    render(<VersionBadge version={subjectData.data_version} sourceType={subjectData.source_type} />);

    expect(screen.getByText('v1 Legacy')).toBeInTheDocument();
  });

  test('三级联动选择', async () => {
    render(<Module01 />);

    // 选择组别
    await userEvent.selectOptions(screen.getByLabelText('组别'), 'control');

    // 验证受试者列表加载
    await waitFor(() => {
      expect(screen.getByText(/control_legacy_1/)).toBeInTheDocument();
    });

    // 选择受试者
    await userEvent.click(screen.getByText('control_legacy_1'));

    // 验证任务列表加载
    await waitFor(() => {
      expect(screen.getByText('q1')).toBeInTheDocument();
    });
  });
});
```

### 集成测试

#### 端到端测试流程

```
测试1: Legacy数据完整流程
1. 访问 http://localhost:5173/module01
2. 选择组别: control
3. 选择受试者: control_legacy_1 (应显示v1徽章)
4. 选择任务: q1
5. 点击"加载数据"
6. 验证：
   - 轨迹图正确渲染
   - 热力图正确渲染
   - 统计信息准确（数据点数、持续时间等）
   - 元数据显示v1/legacy

测试2: Eye Tracking数据完整流程
1. 选择组别: mci
2. 选择受试者: mci_eyetrack_s005 (应显示v2徽章)
3. 选择任务: q3
4. 点击"加载数据"
5. 验证：
   - 数据正确加载
   - 元数据显示v2/eye_tracking
   - MMSE信息显示（如有）

测试3: 版本筛选
1. 选择"仅v1数据"过滤器
2. 验证受试者列表只显示v1数据
3. 选择"仅v2数据"过滤器
4. 验证受试者列表只显示v2数据
```

### 性能测试

```python
def test_large_csv_loading():
    """测试大CSV文件加载性能"""
    import time

    service = DataVisualizationService()

    start = time.time()
    result = service.load_raw_data('control', 'control_legacy_1', 'q1')
    duration = time.time() - start

    assert duration < 2.0  # 应在2秒内完成
    assert result['success'] == True

def test_metadata_cache():
    """测试元数据缓存"""
    service = DataVisualizationService()

    # 第一次加载
    start1 = time.time()
    result1 = service.get_subjects('control')
    duration1 = time.time() - start1

    # 第二次加载（应使用缓存）
    start2 = time.time()
    result2 = service.get_subjects('control')
    duration2 = time.time() - start2

    assert duration2 < duration1 * 0.5  # 缓存应显著加快
```

---

## 📝 实施优先级与时间规划

### 第一优先级（P0 - 核心功能，必须完成）

**预计工时：** 5小时

1. **Task 1.1** - 创建MetadataReader类 (1h)
2. **Task 1.2** - 重构DataVisualizationService (2h)
3. **Task 1.3** - 更新文件路径逻辑 (0.5h)
4. **Task 5.1** - Backend API测试 (1.5h)

**里程碑：** Backend能正确读取Module00导入的真实数据

---

### 第二优先级（P1 - 功能增强）

**预计工时：** 4小时

5. **Task 2.1-2.3** - API响应增强 (1.5h)
6. **Task 3.1** - 更新Module01主页面 (1h)
7. **Task 3.2** - 创建SubjectInfo组件 (1h)
8. **Task 5.2-5.3** - Frontend测试 (2h)

**里程碑：** 前端能显示v1/v2数据版本信息

---

### 第三优先级（P2 - 体验优化）

**预计工时：** 3.5小时

9. **Task 3.3** - 添加数据过滤器 (1h)
10. **Task 3.4** - 错误处理优化 (0.5h)
11. **Task 4.1-4.2** - i18n国际化 (1.5h)
12. **Task 5.4** - 性能测试 (0.5h)

**里程碑：** 完整的用户体验和多语言支持

---

### 总体时间规划

| 优先级 | 任务数 | 预计工时 | 完成标准 |
|-------|--------|---------|---------|
| P0 核心 | 4项 | 5小时 | Backend读取真实数据 |
| P1 增强 | 6项 | 4小时 | Frontend显示完整信息 |
| P2 优化 | 4项 | 3.5小时 | 完整用户体验 |
| **总计** | **14项** | **12.5小时** | **约2个工作日** |

---

## ⚠️ 注意事项与最佳实践

### 1. 数据一致性

- ✅ 严格遵循文件命名：`{subject_id}_{task}.csv`
- ✅ 确保路径与Module00完全一致：`data/01_raw/{group}/`
- ✅ 使用元数据作为唯一数据源

### 2. 向后兼容性

- ✅ 保持API接口签名不变
- ✅ 新增字段使用可选模式
- ✅ 降级方案：元数据不存在时使用文件扫描

### 3. 性能优化

- ✅ 元数据文件在Service初始化时一次性加载
- ✅ 考虑大CSV文件采样显示
- ✅ 图表渲染使用虚拟化列表

### 4. 错误处理

- ✅ 元数据文件不存在 → 降级为文件扫描 + 警告提示
- ✅ CSV文件缺失 → 友好错误提示 + 建议重新导入
- ✅ 数据格式错误 → 详细错误信息 + 问题定位

### 5. 安全性

- ✅ 验证subject_id格式，防止路径遍历攻击
- ✅ 验证group在允许列表内（control/mci/ad）
- ✅ 验证task_id在允许列表内（q1-q5）

---

## 📚 相关文档链接

- [Module00开发文档](./MODULE00_DEVELOPMENT_LOG.md)
- [Frontend编码规范](./FRONTEND_CODING_STANDARDS.md)
- [Backend编码规范](./BACKEND_CODING_STANDARDS.md)
- [i18n架构设计](./I18N_ARCHITECTURE_DESIGN.md)
- [代码审查报告](./CODE_REVIEW_REPORT.md)

---

## 📌 文档状态

**当前状态：** ✅ 待用户确认

**下一步行动：**
1. 用户审阅本规划文档
2. 用户确认后开始实施P0任务
3. 完成P0任务后进行测试验证
4. 根据测试结果调整P1/P2任务

**预期交付时间：** 2个工作日（按优先级分阶段交付）

---

**文档维护者：** Claude
**最后审阅：** 待用户确认
**版本历史：**
- v1.0 (2025-10-02): 初始版本，包含基础规划
- v2.0 (2025-10-02): 增加数据版本支持
- v3.0 (2025-10-02): 重写为真实数据对接方案，基于Module00实际导入数据
