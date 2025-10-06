# Module01 UI/UX 优化方案
# Module01 UI/UX Optimization Plan

**文档版本:** v1.0
**创建日期:** 2025-10-02
**优化目标:** 提升数据选择和可视化的用户体验

---

## 📋 目录 Table of Contents

1. [优化需求概述](#1-优化需求概述)
2. [当前实现分析](#2-当前实现分析)
3. [优化方案设计](#3-优化方案设计)
4. [国际化设计 (i18n)](#4-国际化设计-i18n)
5. [技术实现细节](#5-技术实现细节)
6. [开发计划](#6-开发计划)
7. [测试验证](#7-测试验证)

---

## 1. 优化需求概述

### 1.1 需求清单

#### 需求1: 数据版本筛选器
**描述:** 在数据选择区域添加"数据版本"筛选下拉框

**选项:**
- `全部版本` (all) - 显示所有v1和v2数据的受试者
- `V1 (旧数据)` (v1) - 只显示Legacy数据源的受试者
- `V2 (新数据)` (v2) - 只显示Eye Tracking v2数据源的受试者

**交互逻辑:**
- 默认选中"全部版本"
- 切换版本时，自动刷新受试者列表
- 受试者列表只显示符合所选版本的数据
- 如果当前选中的受试者不在新版本筛选结果中，自动选择第一个可用受试者

---

#### 需求2: 任务选择器增强
**描述:** 在任务下拉框中增加"全部任务"选项

**选项:**
- `全部任务` (all) - 显示Q1-Q5的综合信息和可视化
- `Q1` - 单个任务数据
- `Q2` - 单个任务数据
- `Q3` - 单个任务数据
- `Q4` - 单个任务数据
- `Q5` - 单个任务数据

**交互逻辑:**
- "全部任务"选项始终在下拉框顶部
- 选择"全部任务"时，加载当前受试者的Q1-Q5所有任务数据
- 数据统计显示合并后的总计信息
- 可视化区域显示Q1-Q5的综合轨迹和热力图

---

#### 需求3: 可视化布局重构
**描述:** 移除Tab切换，改为左右分栏显示

**布局设计:**
```
┌─────────────────────────────────────────────────────────┐
│              数据可视化 (Card Title)                     │
├──────────────────────────┬──────────────────────────────┤
│                          │                              │
│   眼动轨迹图 (50%)       │      热力图 (50%)            │
│   Gaze Trajectory        │      Heatmap                 │
│                          │                              │
│   - 显示范围: (0,0)-(1,1)│   - 显示范围: (0,0)-(1,1)   │
│   - 归一化坐标           │   - 网格密度: 50x50          │
│                          │                              │
└──────────────────────────┴──────────────────────────────┘
```

**实现要求:**
- 使用Ant Design的`Row`和`Col`组件实现左右分栏
- 左侧: 眼动轨迹图 (50%宽度)
- 右侧: 热力图 (50%宽度)
- 两个图表同时显示，无需Tab切换
- 图表高度一致，保持视觉平衡

---

#### 需求4: 眼动轨迹图归一化坐标
**描述:** 轨迹图的显示范围固定为(0,0)到(1,1)

**技术要求:**
- X轴范围: 0 - 1.0
- Y轴范围: 0 - 1.0
- 眼动点坐标已归一化，无需额外处理
- 坐标轴标签清晰标注"归一化坐标"
- 网格线辅助定位

---

## 2. 当前实现分析

### 2.1 架构符合性检查

**Module01当前职责 ✅:**
- ✅ 读取Module00维护的元数据 (使用共享MetadataReader)
- ✅ 提供数据可视化界面
- ✅ 不做数据验证和清洗 (信任Module00)

**数据流 ✅:**
```
Module00 (数据质量控制) → MetadataReader (共享工具) → Module01 (可视化)
```

**结论:** 本次优化只涉及UI/UX层面，不改变Module01的核心职责，符合现有架构设计。

---

### 2.2 当前功能清单

**前端组件:** `frontend/src/pages/Module01/Module01.jsx`
- ✅ 组别选择器 (Control/MCI/AD)
- ✅ 受试者选择器 (显示task_count, data_version, has_mmse)
- ✅ 任务选择器 (Q1-Q5)
- ✅ 数据加载按钮
- ✅ 数据统计卡片 (total_points, duration, x_range, y_range)
- ✅ 元数据信息卡片 (subject_id, group, task, data_version, roi_layout, mmse)
- ✅ Tab切换 (轨迹图 vs 热力图)

**后端API:** `src/web/modules/module01_data_visualization/`
- ✅ `GET /api/data/groups` - 获取组别列表
- ✅ `GET /api/data/subjects?group=control` - 获取受试者列表
- ✅ `GET /api/data/tasks?group=control&subject_id=control_01` - 获取任务列表
- ✅ `GET /api/data/raw?group=control&subject_id=control_01&task_id=q1` - 加载原始数据

**数据服务:** `frontend/src/services/dataService.js`
- ✅ `getGroups()` - 获取组别
- ✅ `getSubjects(group)` - 获取受试者
- ✅ `getTasks(group, subjectId)` - 获取任务
- ✅ `loadRawData(group, subjectId, taskId)` - 加载数据

---

### 2.3 需要修改的部分

#### 前端修改:
1. **Module01.jsx**
   - 新增: `selectedVersion` 状态 (数据版本筛选器)
   - 新增: 版本选择器下拉框
   - 修改: `loadSubjects()` 逻辑，支持版本筛选
   - 修改: 任务选择器，增加"全部任务"选项
   - 修改: `loadGazeData()` 逻辑，支持加载全部任务
   - 重构: 移除Tabs，改为Row/Col布局

2. **dataService.js**
   - 修改: `getSubjects(group, version)` - 支持版本参数
   - 新增: `loadAllTasksData(group, subjectId)` - 加载Q1-Q5所有数据

3. **GazeTrajectoryChart.jsx**
   - 修改: 固定坐标轴范围为(0,0)-(1,1)
   - 新增: 归一化坐标轴标签

4. **HeatmapChart.jsx**
   - 修改: 固定坐标轴范围为(0,0)-(1,1)

#### 后端修改:
1. **service.py**
   - 修改: `get_subjects(group, version=None)` - 支持版本筛选
   - 新增: `load_all_tasks_data(group, subject_id)` - 加载Q1-Q5数据

2. **api.py**
   - 修改: `GET /api/data/subjects?group=control&version=v1` - 支持version参数
   - 新增: `GET /api/data/raw/all?group=control&subject_id=control_01` - 加载所有任务

---

## 3. 优化方案设计

### 3.1 数据版本筛选器设计

#### 3.1.1 UI组件设计

**位置:** 数据选择卡片，组别选择器和受试者选择器之间

**组件代码:**
```jsx
<div>
  <label style={{ marginRight: 8 }}>数据版本:</label>
  <Select
    value={selectedVersion}
    onChange={handleVersionChange}
    style={{ width: 150 }}
  >
    <Option value="all">全部版本</Option>
    <Option value="v1">V1 (旧数据)</Option>
    <Option value="v2">V2 (新数据)</Option>
  </Select>
</div>
```

#### 3.1.2 状态管理

**新增状态:**
```javascript
const [selectedVersion, setSelectedVersion] = useState('all'); // 默认显示全部版本
```

**交互逻辑:**
```javascript
// 当组别或版本变化时，重新加载受试者列表
useEffect(() => {
  if (selectedGroup) {
    loadSubjects(selectedGroup, selectedVersion);
    // 重置受试者和任务选择
    setSelectedSubject(null);
    setSelectedTask(null);
    setTasks([]);
    setGazeData(null);
  }
}, [selectedGroup, selectedVersion]);

const handleVersionChange = (version) => {
  setSelectedVersion(version);
};
```

#### 3.1.3 后端API修改

**API端点:** `GET /api/data/subjects`

**请求参数:**
```
group: string (required) - 组别ID (control/mci/ad)
version: string (optional) - 数据版本 (all/v1/v2)，默认all
```

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": "control_legacy_1",
      "task_count": 5,
      "data_version": "v1",
      "source_type": "legacy",
      "has_mmse": true
    },
    {
      "id": "eyetrack_control_01",
      "task_count": 5,
      "data_version": "v2",
      "source_type": "eye_tracking",
      "has_mmse": false
    }
  ]
}
```

**Service层实现:**
```python
def get_subjects(self, group: str, version: Optional[str] = None) -> Dict[str, Any]:
    """
    获取指定组别和版本的受试者列表

    Args:
        group: 组别ID (control/mci/ad)
        version: 数据版本筛选 (all/v1/v2/None)，None或'all'表示全部

    Returns:
        {
            "success": True,
            "data": [...]
        }
    """
    try:
        # 从MetadataReader获取受试者列表
        subjects_meta = self.metadata_reader.get_subjects_by_group(group)

        subjects = []
        for meta in subjects_meta:
            subject_id = meta.get('subject_id')
            data_version = meta.get('data_version', 'v1')

            # 版本筛选逻辑
            if version and version != 'all':
                if data_version != version:
                    continue  # 跳过不匹配的版本

            subjects.append({
                "id": subject_id,
                "task_count": len(meta.get('tasks_available', [])),
                "data_version": data_version,
                "source_type": meta.get('source_type', 'legacy'),
                "has_mmse": self.metadata_reader.has_mmse_score(subject_id)
            })

        return {
            "success": True,
            "data": subjects
        }
    except Exception as e:
        logger.error(f"Failed to get subjects: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "data": []
        }
```

**API层修改:**
```python
@m01_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """
    获取指定组别的受试者列表（支持版本筛选）

    GET /api/data/subjects?group=control&version=v1

    Query Parameters:
        group: 组别ID (control/mci/ad)
        version: 数据版本 (all/v1/v2)，可选，默认all
    """
    try:
        group = request.args.get('group')
        version = request.args.get('version', 'all')  # 默认all

        if not group:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: group",
                "data": []
            }), 400

        result = viz_service.get_subjects(group, version)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting subjects: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        }), 500
```

---

### 3.2 全部任务加载设计

#### 3.2.1 UI组件修改

**任务选择器修改:**
```jsx
<Select
  value={selectedTask}
  onChange={setSelectedTask}
  placeholder="选择任务"
  style={{ width: 140 }}
  loading={loadingTasks}
  disabled={!selectedSubject}
>
  {/* 全部任务选项始终在顶部 */}
  <Option value="all">全部任务</Option>

  {/* 单个任务选项 */}
  {tasks.map(t => (
    <Option key={t} value={t}>
      {t.toUpperCase()}
    </Option>
  ))}
</Select>
```

#### 3.2.2 数据加载逻辑

**前端加载函数修改:**
```javascript
// 加载眼动数据
const loadGazeData = async () => {
  if (!selectedGroup || !selectedSubject || !selectedTask) {
    message.warning('请先选择组别、受试者和任务');
    return;
  }

  try {
    setLoadingData(true);

    let result;
    if (selectedTask === 'all') {
      // 加载全部任务数据
      result = await dataService.loadAllTasksData(
        selectedGroup,
        selectedSubject
      );
    } else {
      // 加载单个任务数据
      result = await dataService.loadRawData(
        selectedGroup,
        selectedSubject,
        selectedTask
      );
    }

    setGazeData(result.data);
    setStats(result.stats);
    setMetadata(result.metadata);

    const taskInfo = selectedTask === 'all' ? 'Q1-Q5全部任务' : selectedTask.toUpperCase();
    message.success(`成功加载${taskInfo} ${result.data.length} 个数据点`);
  } catch (error) {
    console.error('加载数据失败:', error);
    message.error('加载数据失败: ' + (error.message || '未知错误'));
  } finally {
    setLoadingData(false);
  }
};
```

**dataService新增方法:**
```javascript
// frontend/src/services/dataService.js

/**
 * 加载受试者的所有任务数据(Q1-Q5)
 */
async loadAllTasksData(group, subjectId) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/data/raw/all?group=${group}&subject_id=${subjectId}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || '加载数据失败');
    }

    return result;
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}
```

#### 3.2.3 后端API新增

**新增API端点:** `GET /api/data/raw/all`

**请求参数:**
```
group: string (required) - 组别ID
subject_id: string (required) - 受试者ID
```

**响应格式:**
```json
{
  "success": true,
  "data": [
    // Q1的所有数据点
    {"timestamp": 0.0, "x": 0.5, "y": 0.5, "task": "q1"},
    {"timestamp": 0.1, "x": 0.52, "y": 0.51, "task": "q1"},
    // ...
    // Q2的所有数据点
    {"timestamp": 0.0, "x": 0.3, "y": 0.4, "task": "q2"},
    // ... Q3, Q4, Q5
  ],
  "stats": {
    "total_points": 5000,      // Q1-Q5总数据点
    "duration": 25000.0,       // Q1-Q5总持续时间(秒)
    "x_range": [0.0, 1.0],
    "y_range": [0.0, 1.0],
    "tasks_loaded": ["q1", "q2", "q3", "q4", "q5"],
    "points_per_task": {
      "q1": 1000,
      "q2": 1020,
      "q3": 980,
      "q4": 1015,
      "q5": 985
    }
  },
  "metadata": {
    "group": "control",
    "subject_id": "control_01",
    "task": "all",             // 标识为全部任务
    "data_version": "v1",
    "source_type": "legacy",
    "has_mmse": true,
    "mmse_scores": {...}
  }
}
```

**Service层实现:**
```python
def load_all_tasks_data(self, group: str, subject_id: str) -> Dict[str, Any]:
    """
    加载受试者的Q1-Q5所有任务数据

    Args:
        group: 组别ID
        subject_id: 受试者ID

    Returns:
        {
            "success": True,
            "data": [...],      # 合并后的所有数据点
            "stats": {...},     # 合并后的统计信息
            "metadata": {...}
        }
    """
    try:
        # 验证受试者是否存在
        subject_info = self.metadata_reader.get_subject_info(subject_id)
        if not subject_info:
            return {
                "success": False,
                "error": f"Subject '{subject_id}' not found",
                "data": [],
                "stats": None,
                "metadata": None
            }

        # 获取可用任务列表
        available_tasks = self.metadata_reader.get_tasks_available(subject_id)
        if not available_tasks:
            return {
                "success": False,
                "error": f"No tasks available for subject '{subject_id}'",
                "data": [],
                "stats": None,
                "metadata": None
            }

        # 加载所有任务数据
        all_data = []
        total_points = 0
        total_duration = 0.0
        points_per_task = {}

        x_min, x_max = float('inf'), float('-inf')
        y_min, y_max = float('inf'), float('-inf')

        for task_id in sorted(available_tasks):  # q1, q2, q3, q4, q5
            # 构建文件路径
            data_file = self.data_root / "01_raw" / group / f"{subject_id}_{task_id}.csv"

            if not data_file.exists():
                logger.warning(f"Data file not found: {data_file}")
                continue

            # 读取CSV
            df = pd.read_csv(data_file)

            # 验证列
            required_columns = ['timestamp', 'x', 'y']
            if not all(col in df.columns for col in required_columns):
                logger.warning(f"Missing columns in {data_file}")
                continue

            # 处理timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_time = df['timestamp'].min()
            duration = (df['timestamp'].max() - start_time).total_seconds()
            df['timestamp_sec'] = (df['timestamp'] - start_time).dt.total_seconds()

            # 添加task标识
            df['task'] = task_id

            # 转换为字典列表
            task_data = df[['timestamp_sec', 'x', 'y', 'task']].rename(
                columns={'timestamp_sec': 'timestamp'}
            ).to_dict('records')

            all_data.extend(task_data)

            # 统计信息
            total_points += len(df)
            total_duration += duration
            points_per_task[task_id] = len(df)

            # 更新范围
            x_min = min(x_min, df['x'].min())
            x_max = max(x_max, df['x'].max())
            y_min = min(y_min, df['y'].min())
            y_max = max(y_max, df['y'].max())

        if not all_data:
            return {
                "success": False,
                "error": "No valid data files found",
                "data": [],
                "stats": None,
                "metadata": None
            }

        # 统计信息
        stats = {
            "total_points": total_points,
            "duration": float(total_duration),
            "x_range": [float(x_min), float(x_max)],
            "y_range": [float(y_min), float(y_max)],
            "tasks_loaded": sorted(available_tasks),
            "points_per_task": points_per_task
        }

        # 获取MMSE数据
        mmse_scores = self.metadata_reader.get_mmse_score(subject_id)

        # 元数据
        metadata = {
            "group": group,
            "subject_id": subject_id,
            "task": "all",  # 标识为全部任务
            "data_version": subject_info.get('data_version', 'v1'),
            "source_type": subject_info.get('source_type', 'legacy'),
            "roi_layout": subject_info.get('roi_layout', 'v1'),
            "has_mmse": self.metadata_reader.has_mmse_score(subject_id),
            "mmse_scores": mmse_scores
        }

        logger.info(
            f"Loaded {total_points} total data points from {len(available_tasks)} tasks "
            f"for subject {subject_id}"
        )

        return {
            "success": True,
            "data": all_data,
            "stats": stats,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Failed to load all tasks data: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "stats": None,
            "metadata": None
        }
```

**API层实现:**
```python
@m01_bp.route('/raw/all', methods=['GET'])
def get_all_tasks_data():
    """
    加载受试者的所有任务数据(Q1-Q5)

    GET /api/data/raw/all?group=control&subject_id=control_01

    Query Parameters:
        group: 组别ID
        subject_id: 受试者ID

    Returns:
        {
            "success": true,
            "data": [...],
            "stats": {...},
            "metadata": {...}
        }
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')

        if not all([group, subject_id]):
            return jsonify({
                "success": False,
                "error": "Missing required parameters: group, subject_id",
                "data": [],
                "stats": None,
                "metadata": None
            }), 400

        result = viz_service.load_all_tasks_data(group, subject_id)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error loading all tasks data: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": [],
            "stats": None,
            "metadata": None
        }), 500
```

---

### 3.3 可视化布局重构

#### 3.3.1 移除Tabs，改用左右分栏

**当前实现:**
```jsx
<Card title="数据可视化">
  <Tabs items={tabItems} defaultActiveKey="trajectory" />
</Card>
```

**优化后实现:**
```jsx
<Card title="数据可视化">
  {gazeData ? (
    <Row gutter={16}>
      {/* 左侧: 眼动轨迹图 */}
      <Col span={12}>
        <div style={{ padding: '16px', border: '1px solid #f0f0f0', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: 16, fontSize: 16 }}>
            <DotChartOutlined style={{ marginRight: 8 }} />
            眼动轨迹图
          </h3>
          <GazeTrajectoryChart
            data={gazeData}
            loading={loadingData}
            title={null}  // 标题已在外层显示
            xRange={[0, 1]}
            yRange={[0, 1]}
          />
        </div>
      </Col>

      {/* 右侧: 热力图 */}
      <Col span={12}>
        <div style={{ padding: '16px', border: '1px solid #f0f0f0', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: 16, fontSize: 16 }}>
            <HeatMapOutlined style={{ marginRight: 8 }} />
            热力图
          </h3>
          <HeatmapChart
            data={gazeData}
            loading={loadingData}
            title={null}
            gridSize={50}
            xRange={[0, 1]}
            yRange={[0, 1]}
          />
        </div>
      </Col>
    </Row>
  ) : (
    <div style={{ textAlign: 'center', padding: '100px 0', color: '#999' }}>
      <p>请加载数据后查看可视化图表</p>
    </div>
  )}
</Card>
```

#### 3.3.2 图表组件修改

**GazeTrajectoryChart.jsx 修改:**
```jsx
// frontend/src/components/Charts/GazeTrajectoryChart.jsx

const GazeTrajectoryChart = ({
  data,
  loading,
  title = '眼动轨迹图',
  xRange = [0, 1],  // 新增: 固定X轴范围
  yRange = [0, 1]   // 新增: 固定Y轴范围
}) => {
  // ... 其他代码

  const option = {
    title: title ? { text: title } : undefined,
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const point = params.data;
        return `
          时间: ${point[2].toFixed(2)}s<br/>
          X坐标: ${point[0].toFixed(3)}<br/>
          Y坐标: ${point[1].toFixed(3)}
          ${point[3] ? `<br/>任务: ${point[3].toUpperCase()}` : ''}
        `;
      }
    },
    xAxis: {
      type: 'value',
      name: 'X (归一化坐标)',
      nameLocation: 'middle',
      nameGap: 30,
      min: xRange[0],
      max: xRange[1],
      splitLine: { show: true, lineStyle: { color: '#f0f0f0' } }
    },
    yAxis: {
      type: 'value',
      name: 'Y (归一化坐标)',
      nameLocation: 'middle',
      nameGap: 40,
      min: yRange[0],
      max: yRange[1],
      splitLine: { show: true, lineStyle: { color: '#f0f0f0' } }
    },
    series: [
      {
        type: 'scatter',
        symbolSize: 4,
        data: data.map((d, idx) => [
          d.x,
          d.y,
          d.timestamp,
          d.task || null  // 如果是全部任务数据，包含task字段
        ]),
        itemStyle: {
          color: (params) => {
            // 如果是全部任务数据，用不同颜色区分
            if (params.data[3]) {
              const taskColors = {
                'q1': '#5470c6',
                'q2': '#91cc75',
                'q3': '#fac858',
                'q4': '#ee6666',
                'q5': '#73c0de'
              };
              return taskColors[params.data[3]] || '#5470c6';
            }
            return '#5470c6';
          }
        }
      }
    ]
  };

  return (
    <ReactECharts
      option={option}
      loading={loading}
      style={{ height: '500px', width: '100%' }}
    />
  );
};
```

**HeatmapChart.jsx 修改:**
```jsx
// frontend/src/components/Charts/HeatmapChart.jsx

const HeatmapChart = ({
  data,
  loading,
  title = '热力图',
  gridSize = 50,
  xRange = [0, 1],  // 新增: 固定X轴范围
  yRange = [0, 1]   // 新增: 固定Y轴范围
}) => {
  // 计算热力图数据
  const heatmapData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const grid = Array(gridSize).fill(0).map(() => Array(gridSize).fill(0));

    data.forEach(point => {
      // 归一化坐标映射到网格
      const xBin = Math.floor(point.x * gridSize);
      const yBin = Math.floor(point.y * gridSize);

      // 边界检查
      if (xBin >= 0 && xBin < gridSize && yBin >= 0 && yBin < gridSize) {
        grid[yBin][xBin] += 1;
      }
    });

    // 转换为ECharts需要的格式
    const result = [];
    for (let y = 0; y < gridSize; y++) {
      for (let x = 0; x < gridSize; x++) {
        result.push([x, y, grid[y][x]]);
      }
    }

    return result;
  }, [data, gridSize]);

  const option = {
    title: title ? { text: title } : undefined,
    tooltip: {
      position: 'top',
      formatter: (params) => {
        const [x, y, value] = params.data;
        const xCoord = (x / gridSize).toFixed(3);
        const yCoord = (y / gridSize).toFixed(3);
        return `网格: (${x}, ${y})<br/>坐标: (${xCoord}, ${yCoord})<br/>注视次数: ${value}`;
      }
    },
    grid: {
      left: 60,
      right: 60,
      top: 60,
      bottom: 60
    },
    xAxis: {
      type: 'category',
      name: 'X (归一化坐标)',
      nameLocation: 'middle',
      nameGap: 30,
      data: Array(gridSize).fill(0).map((_, i) => (i / gridSize).toFixed(2)),
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      name: 'Y (归一化坐标)',
      nameLocation: 'middle',
      nameGap: 40,
      data: Array(gridSize).fill(0).map((_, i) => (i / gridSize).toFixed(2)),
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: Math.max(...heatmapData.map(d => d[2])),
      calculable: true,
      orient: 'vertical',
      right: 10,
      top: 'center',
      inRange: {
        color: ['#ffffff', '#ffeda0', '#feb24c', '#f03b20', '#bd0026']
      }
    },
    series: [
      {
        type: 'heatmap',
        data: heatmapData,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };

  return (
    <ReactECharts
      option={option}
      loading={loading}
      style={{ height: '500px', width: '100%' }}
    />
  );
};
```

---

## 4. 国际化设计 (i18n)

### 4.1 为什么Module01需要国际化？

Module01是数据可视化模块，包含大量的**用户界面文字**和**图表标注**：
- ✅ 数据选择界面（组别、版本、受试者、任务）
- ✅ 图表标题和坐标轴（眼动轨迹图、热力图）
- ✅ 数据统计信息（数据点数、持续时间、坐标范围）
- ✅ 元数据信息（Subject ID、分组、数据版本）
- ✅ 错误提示和操作反馈

**目标用户:** 项目支持**简体中文**、**English**、**Bahasa Melayu**三种语言。

---

### 4.2 国际化架构方案

基于项目的[I18N_ARCHITECTURE_DESIGN.md](I18N_ARCHITECTURE_DESIGN.md)，Module01采用以下技术栈：

| 层级 | 技术方案 | 用途 |
|------|---------|------|
| **前端UI** | react-i18next | 组件文字翻译 |
| **图表** | react-i18next + ECharts配置 | 图表标题、坐标轴、Tooltip翻译 |
| **后端API** | Flask-Babel | API响应消息翻译（可选） |

---

### 4.3 翻译文件设计

#### 4.3.1 目录结构

```
frontend/src/locales/
├── zh-CN/
│   ├── common.json       # 通用翻译（继承自现有）
│   ├── module01.json     # Module01专用翻译 ⭐NEW
│   └── charts.json       # 图表翻译 ⭐NEW
├── en-US/
│   ├── common.json
│   ├── module01.json     ⭐NEW
│   └── charts.json       ⭐NEW
└── ms-MY/
    ├── common.json
    ├── module01.json     ⭐NEW
    └── charts.json       ⭐NEW
```

---

#### 4.3.2 翻译文件内容

**frontend/src/locales/zh-CN/module01.json:**
```json
{
  "title": "模块1: 数据可视化",
  "subtitle": "可视化眼球追踪数据，包括轨迹图、热力图等",

  "dataSelection": {
    "title": "数据选择",
    "group": {
      "label": "研究组别",
      "placeholder": "选择组别",
      "control": "对照组",
      "mci": "MCI组",
      "ad": "AD组",
      "count": "{{count}}人"
    },
    "version": {
      "label": "数据版本",
      "all": "全部版本",
      "v1": "V1 (旧数据)",
      "v2": "V2 (新数据)"
    },
    "subject": {
      "label": "受试者",
      "placeholder": "选择受试者",
      "taskCount": "{{count}}个任务",
      "hasMMSE": "MMSE"
    },
    "task": {
      "label": "任务",
      "placeholder": "选择任务",
      "all": "全部任务",
      "q1": "Q1",
      "q2": "Q2",
      "q3": "Q3",
      "q4": "Q4",
      "q5": "Q5"
    },
    "loadButton": "加载数据",
    "loading": "加载中..."
  },

  "dataStats": {
    "title": "数据统计",
    "totalPoints": "数据点数",
    "duration": "持续时间",
    "xRange": "X坐标范围",
    "yRange": "Y坐标范围",
    "unit": {
      "points": "个",
      "seconds": "秒"
    }
  },

  "metadata": {
    "title": "数据信息",
    "subjectId": "受试者ID",
    "group": "组别",
    "task": "任务",
    "dataVersion": "数据版本",
    "sourceType": {
      "label": "数据源",
      "legacy": "原始数据",
      "eyeTracking": "眼动仪v2"
    },
    "roiLayout": "ROI布局",
    "mmseScore": "MMSE评分",
    "hasScore": "已有",
    "noScore": "暂无"
  },

  "visualization": {
    "title": "数据可视化",
    "trajectory": {
      "title": "眼动轨迹图",
      "xAxis": "X (归一化坐标)",
      "yAxis": "Y (归一化坐标)"
    },
    "heatmap": {
      "title": "热力图",
      "xAxis": "X (归一化坐标)",
      "yAxis": "Y (归一化坐标)",
      "density": "注视密度"
    },
    "noData": "请加载数据后查看可视化图表"
  },

  "messages": {
    "selectAll": "请先选择组别、受试者和任务",
    "loadSuccess": "成功加载 {{count}} 个数据点",
    "loadError": "加载数据失败: {{error}}",
    "allTasksLoaded": "成功加载{{task}} {{count}} 个数据点"
  },

  "instructions": {
    "title": "使用说明",
    "step1": "1. 选择研究组别（对照组/MCI组/AD组）",
    "step2": "2. 选择数据版本（全部/V1/V2）",
    "step3": "3. 选择受试者ID",
    "step4": "4. 选择任务（全部任务/Q1-Q5）",
    "step5": "5. 点击"加载数据"按钮",
    "step6": "6. 查看眼动轨迹图和热力图"
  }
}
```

**frontend/src/locales/en-US/module01.json:**
```json
{
  "title": "Module 1: Data Visualization",
  "subtitle": "Visualize eye-tracking data including trajectory and heatmap",

  "dataSelection": {
    "title": "Data Selection",
    "group": {
      "label": "Research Group",
      "placeholder": "Select group",
      "control": "Control Group",
      "mci": "MCI Group",
      "ad": "AD Group",
      "count": "{{count}} subjects"
    },
    "version": {
      "label": "Data Version",
      "all": "All Versions",
      "v1": "V1 (Legacy)",
      "v2": "V2 (New Data)"
    },
    "subject": {
      "label": "Subject",
      "placeholder": "Select subject",
      "taskCount": "{{count}} tasks",
      "hasMMSE": "MMSE"
    },
    "task": {
      "label": "Task",
      "placeholder": "Select task",
      "all": "All Tasks",
      "q1": "Q1",
      "q2": "Q2",
      "q3": "Q3",
      "q4": "Q4",
      "q5": "Q5"
    },
    "loadButton": "Load Data",
    "loading": "Loading..."
  },

  "dataStats": {
    "title": "Data Statistics",
    "totalPoints": "Total Points",
    "duration": "Duration",
    "xRange": "X Range",
    "yRange": "Y Range",
    "unit": {
      "points": "points",
      "seconds": "sec"
    }
  },

  "metadata": {
    "title": "Data Information",
    "subjectId": "Subject ID",
    "group": "Group",
    "task": "Task",
    "dataVersion": "Data Version",
    "sourceType": {
      "label": "Data Source",
      "legacy": "Legacy Data",
      "eyeTracking": "Eye Tracking v2"
    },
    "roiLayout": "ROI Layout",
    "mmseScore": "MMSE Score",
    "hasScore": "Available",
    "noScore": "N/A"
  },

  "visualization": {
    "title": "Data Visualization",
    "trajectory": {
      "title": "Gaze Trajectory",
      "xAxis": "X (Normalized)",
      "yAxis": "Y (Normalized)"
    },
    "heatmap": {
      "title": "Heatmap",
      "xAxis": "X (Normalized)",
      "yAxis": "Y (Normalized)",
      "density": "Gaze Density"
    },
    "noData": "Please load data to view visualization"
  },

  "messages": {
    "selectAll": "Please select group, subject, and task first",
    "loadSuccess": "Successfully loaded {{count}} data points",
    "loadError": "Failed to load data: {{error}}",
    "allTasksLoaded": "Successfully loaded {{task}} {{count}} data points"
  },

  "instructions": {
    "title": "Instructions",
    "step1": "1. Select research group (Control/MCI/AD)",
    "step2": "2. Select data version (All/V1/V2)",
    "step3": "3. Select subject ID",
    "step4": "4. Select task (All tasks/Q1-Q5)",
    "step5": "5. Click 'Load Data' button",
    "step6": "6. View gaze trajectory and heatmap"
  }
}
```

**frontend/src/locales/ms-MY/module01.json:**
```json
{
  "title": "Modul 1: Visualisasi Data",
  "subtitle": "Visualisasi data penjejakan mata termasuk trajektori dan peta haba",

  "dataSelection": {
    "title": "Pemilihan Data",
    "group": {
      "label": "Kumpulan Kajian",
      "placeholder": "Pilih kumpulan",
      "control": "Kumpulan Kawalan",
      "mci": "Kumpulan MCI",
      "ad": "Kumpulan AD",
      "count": "{{count}} subjek"
    },
    "version": {
      "label": "Versi Data",
      "all": "Semua Versi",
      "v1": "V1 (Data Lama)",
      "v2": "V2 (Data Baru)"
    },
    "subject": {
      "label": "Subjek",
      "placeholder": "Pilih subjek",
      "taskCount": "{{count}} tugasan",
      "hasMMSE": "MMSE"
    },
    "task": {
      "label": "Tugasan",
      "placeholder": "Pilih tugasan",
      "all": "Semua Tugasan",
      "q1": "Q1",
      "q2": "Q2",
      "q3": "Q3",
      "q4": "Q4",
      "q5": "Q5"
    },
    "loadButton": "Muat Data",
    "loading": "Memuatkan..."
  },

  "dataStats": {
    "title": "Statistik Data",
    "totalPoints": "Jumlah Titik",
    "duration": "Tempoh",
    "xRange": "Julat X",
    "yRange": "Julat Y",
    "unit": {
      "points": "titik",
      "seconds": "saat"
    }
  },

  "metadata": {
    "title": "Maklumat Data",
    "subjectId": "ID Subjek",
    "group": "Kumpulan",
    "task": "Tugasan",
    "dataVersion": "Versi Data",
    "sourceType": {
      "label": "Sumber Data",
      "legacy": "Data Asal",
      "eyeTracking": "Penjejakan Mata v2"
    },
    "roiLayout": "Susun Atur ROI",
    "mmseScore": "Skor MMSE",
    "hasScore": "Ada",
    "noScore": "Tiada"
  },

  "visualization": {
    "title": "Visualisasi Data",
    "trajectory": {
      "title": "Trajektori Pandangan",
      "xAxis": "X (Ternormal)",
      "yAxis": "Y (Ternormal)"
    },
    "heatmap": {
      "title": "Peta Haba",
      "xAxis": "X (Ternormal)",
      "yAxis": "Y (Ternormal)",
      "density": "Ketumpatan Pandangan"
    },
    "noData": "Sila muat data untuk melihat visualisasi"
  },

  "messages": {
    "selectAll": "Sila pilih kumpulan, subjek, dan tugasan dahulu",
    "loadSuccess": "Berjaya memuat {{count}} titik data",
    "loadError": "Gagal memuat data: {{error}}",
    "allTasksLoaded": "Berjaya memuat {{task}} {{count}} titik data"
  },

  "instructions": {
    "title": "Arahan",
    "step1": "1. Pilih kumpulan kajian (Kawalan/MCI/AD)",
    "step2": "2. Pilih versi data (Semua/V1/V2)",
    "step3": "3. Pilih ID subjek",
    "step4": "4. Pilih tugasan (Semua tugasan/Q1-Q5)",
    "step5": "5. Klik butang 'Muat Data'",
    "step6": "6. Lihat trajektori pandangan dan peta haba"
  }
}
```

---

### 4.4 组件国际化实现

#### 4.4.1 Module01.jsx 主组件

**导入i18n:**
```javascript
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Select, Button, Space, message } from 'antd';

const Module01 = () => {
  const { t } = useTranslation(['module01', 'common']);

  // ... 状态管理

  return (
    <div>
      {/* 页面标题 - 使用翻译 */}
      <Card style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 16 }}>
          <LineChartOutlined style={{ marginRight: 8 }} />
          {t('module01:title')}
        </h2>
        <p style={{ color: '#666', marginBottom: 0 }}>
          {t('module01:subtitle')}
        </p>
      </Card>

      {/* 数据选择 - 使用翻译 */}
      <Card title={t('module01:dataSelection.title')} style={{ marginBottom: 24 }}>
        <Space size="large" wrap>
          {/* 组别选择器 */}
          <div>
            <label style={{ marginRight: 8 }}>
              {t('module01:dataSelection.group.label')}:
            </label>
            <Select
              value={selectedGroup}
              onChange={setSelectedGroup}
              style={{ width: 180 }}
            >
              {groups.map(g => (
                <Option key={g.id} value={g.id}>
                  {t(`module01:dataSelection.group.${g.id}`)}
                  ({t('module01:dataSelection.group.count', { count: g.count })})
                </Option>
              ))}
            </Select>
          </div>

          {/* 版本选择器 ⭐NEW */}
          <div>
            <label style={{ marginRight: 8 }}>
              {t('module01:dataSelection.version.label')}:
            </label>
            <Select
              value={selectedVersion}
              onChange={setSelectedVersion}
              style={{ width: 150 }}
            >
              <Option value="all">{t('module01:dataSelection.version.all')}</Option>
              <Option value="v1">{t('module01:dataSelection.version.v1')}</Option>
              <Option value="v2">{t('module01:dataSelection.version.v2')}</Option>
            </Select>
          </div>

          {/* 受试者选择器 */}
          <div>
            <label style={{ marginRight: 8 }}>
              {t('module01:dataSelection.subject.label')}:
            </label>
            <Select
              value={selectedSubject}
              onChange={setSelectedSubject}
              placeholder={t('module01:dataSelection.subject.placeholder')}
              style={{ width: 280 }}
            >
              {subjects.map(s => (
                <Option key={s.id} value={s.id}>
                  <Space>
                    <span>{s.id}</span>
                    <Tag color={s.data_version === 'v2' ? 'blue' : 'green'}>
                      {s.data_version || 'v1'}
                    </Tag>
                    {s.has_mmse && (
                      <Tag color="orange">
                        {t('module01:dataSelection.subject.hasMMSE')}
                      </Tag>
                    )}
                    <span style={{ color: '#999' }}>
                      ({t('module01:dataSelection.subject.taskCount', { count: s.task_count })})
                    </span>
                  </Space>
                </Option>
              ))}
            </Select>
          </div>

          {/* 任务选择器 ⭐NEW 全部任务 */}
          <div>
            <label style={{ marginRight: 8 }}>
              {t('module01:dataSelection.task.label')}:
            </label>
            <Select
              value={selectedTask}
              onChange={setSelectedTask}
              placeholder={t('module01:dataSelection.task.placeholder')}
              style={{ width: 140 }}
            >
              <Option value="all">{t('module01:dataSelection.task.all')}</Option>
              {tasks.map(t => (
                <Option key={t} value={t}>
                  {t(`module01:dataSelection.task.${t}`)}
                </Option>
              ))}
            </Select>
          </div>

          {/* 加载按钮 */}
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={loadGazeData}
            loading={loadingData}
          >
            {loadingData
              ? t('module01:dataSelection.loading')
              : t('module01:dataSelection.loadButton')}
          </Button>
        </Space>
      </Card>

      {/* 数据统计 - 使用翻译 */}
      {stats && (
        <Card title={t('module01:dataStats.title')} style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title={t('module01:dataStats.totalPoints')}
                value={stats.total_points}
                suffix={t('module01:dataStats.unit.points')}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={t('module01:dataStats.duration')}
                value={stats.duration}
                precision={2}
                suffix={t('module01:dataStats.unit.seconds')}
              />
            </Col>
            {/* ... 其他统计项 */}
          </Row>
        </Card>
      )}

      {/* 元数据信息 - 使用翻译 */}
      {metadata && (
        <Card title={t('module01:metadata.title')} style={{ marginBottom: 24 }}>
          <Descriptions column={3} size="small">
            <Descriptions.Item label={t('module01:metadata.subjectId')}>
              {metadata.subject_id}
            </Descriptions.Item>
            <Descriptions.Item label={t('module01:metadata.group')}>
              {t(`module01:dataSelection.group.${metadata.group}`)}
            </Descriptions.Item>
            <Descriptions.Item label={t('module01:metadata.task')}>
              {metadata.task === 'all'
                ? t('module01:dataSelection.task.all')
                : t(`module01:dataSelection.task.${metadata.task}`)}
            </Descriptions.Item>
            <Descriptions.Item label={t('module01:metadata.dataVersion')}>
              <Tag color={metadata.data_version === 'v2' ? 'blue' : 'green'}>
                {metadata.data_version || 'v1'}
              </Tag>
              <span style={{ marginLeft: 8, color: '#999' }}>
                ({t(`module01:metadata.sourceType.${metadata.source_type}`)})
              </span>
            </Descriptions.Item>
            {/* ... */}
          </Descriptions>
        </Card>
      )}

      {/* 可视化图表 - 左右分栏 ⭐NEW */}
      <Card title={t('module01:visualization.title')}>
        {gazeData ? (
          <Row gutter={16}>
            {/* 左侧: 眼动轨迹图 */}
            <Col span={12}>
              <GazeTrajectoryChart
                data={gazeData}
                loading={loadingData}
                xRange={[0, 1]}
                yRange={[0, 1]}
              />
            </Col>

            {/* 右侧: 热力图 */}
            <Col span={12}>
              <HeatmapChart
                data={gazeData}
                loading={loadingData}
                gridSize={50}
                xRange={[0, 1]}
                yRange={[0, 1]}
              />
            </Col>
          </Row>
        ) : (
          <div style={{ textAlign: 'center', padding: '100px 0', color: '#999' }}>
            <p>{t('module01:visualization.noData')}</p>
          </div>
        )}
      </Card>
    </div>
  );
};
```

---

#### 4.4.2 图表组件国际化

**GazeTrajectoryChart.jsx:**
```jsx
import React from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';

const GazeTrajectoryChart = ({
  data,
  loading,
  xRange = [0, 1],
  yRange = [0, 1]
}) => {
  const { t } = useTranslation('module01');

  const option = {
    title: {
      text: t('visualization.trajectory.title'),
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const point = params.data;
        return `
          ${t('dataStats.duration')}: ${point[2].toFixed(2)}${t('dataStats.unit.seconds')}<br/>
          X: ${point[0].toFixed(3)}<br/>
          Y: ${point[1].toFixed(3)}
          ${point[3] ? `<br/>${t('metadata.task')}: ${t(`dataSelection.task.${point[3]}`)}` : ''}
        `;
      }
    },
    xAxis: {
      type: 'value',
      name: t('visualization.trajectory.xAxis'),
      nameLocation: 'middle',
      nameGap: 30,
      min: xRange[0],
      max: xRange[1],
      splitLine: { show: true, lineStyle: { color: '#f0f0f0' } }
    },
    yAxis: {
      type: 'value',
      name: t('visualization.trajectory.yAxis'),
      nameLocation: 'middle',
      nameGap: 40,
      min: yRange[0],
      max: yRange[1],
      splitLine: { show: true, lineStyle: { color: '#f0f0f0' } }
    },
    series: [
      {
        type: 'scatter',
        symbolSize: 4,
        data: data.map((d) => [d.x, d.y, d.timestamp, d.task || null]),
        itemStyle: {
          color: (params) => {
            if (params.data[3]) {
              const taskColors = {
                'q1': '#5470c6',
                'q2': '#91cc75',
                'q3': '#fac858',
                'q4': '#ee6666',
                'q5': '#73c0de'
              };
              return taskColors[params.data[3]] || '#5470c6';
            }
            return '#5470c6';
          }
        }
      }
    ]
  };

  return (
    <ReactECharts
      option={option}
      loading={loading}
      style={{ height: '500px', width: '100%' }}
    />
  );
};

export default GazeTrajectoryChart;
```

**HeatmapChart.jsx:**
```jsx
import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';

const HeatmapChart = ({
  data,
  loading,
  gridSize = 50,
  xRange = [0, 1],
  yRange = [0, 1]
}) => {
  const { t } = useTranslation('module01');

  const heatmapData = useMemo(() => {
    // ... 计算热力图数据的逻辑
    // (代码省略，与之前一致)
  }, [data, gridSize]);

  const option = {
    title: {
      text: t('visualization.heatmap.title'),
      left: 'center',
      top: 10
    },
    tooltip: {
      position: 'top',
      formatter: (params) => {
        const [x, y, value] = params.data;
        const xCoord = (x / gridSize).toFixed(3);
        const yCoord = (y / gridSize).toFixed(3);
        return `
          X: ${xCoord}<br/>
          Y: ${yCoord}<br/>
          ${t('visualization.heatmap.density')}: ${value}
        `;
      }
    },
    xAxis: {
      type: 'category',
      name: t('visualization.heatmap.xAxis'),
      nameLocation: 'middle',
      nameGap: 30,
      data: Array(gridSize).fill(0).map((_, i) => (i / gridSize).toFixed(2)),
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      name: t('visualization.heatmap.yAxis'),
      nameLocation: 'middle',
      nameGap: 40,
      data: Array(gridSize).fill(0).map((_, i) => (i / gridSize).toFixed(2)),
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: Math.max(...heatmapData.map(d => d[2])),
      calculable: true,
      orient: 'vertical',
      right: 10,
      top: 'center',
      inRange: {
        color: ['#ffffff', '#ffeda0', '#feb24c', '#f03b20', '#bd0026']
      }
    },
    series: [
      {
        type: 'heatmap',
        data: heatmapData,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };

  return (
    <ReactECharts
      option={option}
      loading={loading}
      style={{ height: '500px', width: '100%' }}
    />
  );
};

export default HeatmapChart;
```

---

### 4.5 消息提示国际化

**使用message.success/error时的翻译:**
```javascript
// 加载数据成功
const loadGazeData = async () => {
  try {
    setLoadingData(true);

    let result;
    if (selectedTask === 'all') {
      result = await dataService.loadAllTasksData(selectedGroup, selectedSubject);
      message.success(
        t('module01:messages.allTasksLoaded', {
          task: t('module01:dataSelection.task.all'),
          count: result.data.length
        })
      );
    } else {
      result = await dataService.loadRawData(selectedGroup, selectedSubject, selectedTask);
      message.success(
        t('module01:messages.loadSuccess', { count: result.data.length })
      );
    }

    setGazeData(result.data);
    setStats(result.stats);
    setMetadata(result.metadata);
  } catch (error) {
    console.error('加载数据失败:', error);
    message.error(
      t('module01:messages.loadError', { error: error.message || 'Unknown error' })
    );
  } finally {
    setLoadingData(false);
  }
};

// 验证选择
if (!selectedGroup || !selectedSubject || !selectedTask) {
  message.warning(t('module01:messages.selectAll'));
  return;
}
```

---

### 4.6 i18n集成步骤

#### Step 1: 安装依赖 (如果尚未安装)

```bash
cd frontend
npm install react-i18next i18next i18next-browser-languagedetector
```

#### Step 2: 配置i18n (如果尚未配置)

参考 [I18N_ARCHITECTURE_DESIGN.md](I18N_ARCHITECTURE_DESIGN.md) 中的配置方式：

**frontend/src/i18n/config.js:**
```javascript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 导入Module01翻译
import zhCN_module01 from '../locales/zh-CN/module01.json';
import enUS_module01 from '../locales/en-US/module01.json';
import msMY_module01 from '../locales/ms-MY/module01.json';

// ... (导入其他模块翻译)

const resources = {
  'zh-CN': {
    common: zhCN_common,
    module01: zhCN_module01,  // ⭐NEW
  },
  'en-US': {
    common: enUS_common,
    module01: enUS_module01,  // ⭐NEW
  },
  'ms-MY': {
    common: msMY_common,
    module01: msMY_module01,  // ⭐NEW
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'zh-CN',
    defaultNS: 'common',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
```

#### Step 3: 在App.jsx中导入i18n

```javascript
import './i18n/config';  // ⭐确保i18n在应用启动时初始化
```

#### Step 4: 添加语言切换器（如果尚未添加）

在主布局中添加语言切换器（参考 `I18N_ARCHITECTURE_DESIGN.md` 中的 `LanguageSwitcher` 组件）。

---

### 4.7 国际化测试清单

#### 前端UI测试:
- [ ] 页面标题和副标题显示三种语言
- [ ] 数据选择器（组别、版本、受试者、任务）标签正确翻译
- [ ] 按钮文字（加载数据、加载中...）正确翻译
- [ ] 数据统计标题和单位正确翻译
- [ ] 元数据信息标题和内容正确翻译
- [ ] 使用说明步骤正确翻译

#### 图表测试:
- [ ] 眼动轨迹图标题正确翻译
- [ ] 轨迹图X/Y轴名称显示"归一化坐标"翻译
- [ ] Tooltip提示信息正确翻译
- [ ] 热力图标题正确翻译
- [ ] 热力图坐标轴名称正确翻译
- [ ] 热力图Tooltip显示密度信息翻译

#### 消息提示测试:
- [ ] 加载成功消息带参数翻译（显示数据点数量）
- [ ] 加载失败消息带错误信息翻译
- [ ] 全部任务加载消息正确翻译
- [ ] 选择提示消息正确翻译

#### 语言切换测试:
- [ ] 切换中文→英文，所有文字立即更新
- [ ] 切换英文→马来文，所有文字立即更新
- [ ] 切换马来文→中文，所有文字立即更新
- [ ] 刷新页面后语言设置保持（localStorage持久化）

---

### 4.8 国际化最佳实践

#### ✅ 推荐做法:

1. **使用命名空间组织翻译**
   ```javascript
   const { t } = useTranslation(['module01', 'common']);
   t('module01:title')  // Module01专用
   t('common:actions.submit')  // 通用操作
   ```

2. **参数化翻译（避免字符串拼接）**
   ```javascript
   // ❌ 错误
   const msg = "成功加载 " + count + " 个数据点";

   // ✅ 正确
   const msg = t('messages.loadSuccess', { count });
   ```

3. **图表标题和坐标轴使用翻译**
   ```javascript
   // ECharts配置中使用t()
   title: { text: t('visualization.trajectory.title') }
   ```

4. **枚举值映射翻译**
   ```javascript
   // ✅ 根据动态值翻译
   t(`dataSelection.group.${group}`)  // group = 'control' | 'mci' | 'ad'
   ```

#### ❌ 避免:

1. **硬编码文字**
   ```javascript
   <h1>模块1: 数据可视化</h1>  // ❌
   <h1>{t('module01:title')}</h1>  // ✅
   ```

2. **翻译key过于简单**
   ```json
   { "title": "标题" }  // ❌ 不清楚是哪个标题
   { "dataSelection.title": "数据选择" }  // ✅ 语义化
   ```

3. **不同语言文件结构不一致**
   ```
   // ❌ 结构不一致会导致翻译缺失
   zh-CN: { "dataSelection": { "group": "组别" } }
   en-US: { "group": "Group" }  // 缺少dataSelection层级
   ```

---

### 4.9 国际化开发时间估算

| 任务 | 预估时间 |
|-----|---------|
| 创建Module01翻译文件（3语） | 2小时 |
| Module01.jsx组件国际化改造 | 2小时 |
| GazeTrajectoryChart国际化 | 1小时 |
| HeatmapChart国际化 | 1小时 |
| 消息提示国际化 | 0.5小时 |
| 测试三语显示 | 1小时 |
| **总计** | **7.5小时** |

---

## 5. 技术实现细节

### 5.1 架构遵循

**✅ Module01职责不变:**
- 只负责可视化展示
- 不做数据验证和清洗
- 信任Module00的数据质量

**✅ 数据流不变:**
```
Module00 → MetadataReader → Module01
```

**✅ 前后端分离:**
- 前端: React + Ant Design + ECharts
- 后端: Flask + Pandas
- API: RESTful风格

---

### 4.2 代码复用

**✅ 使用共享MetadataReader:**
- 不重复实现元数据读取逻辑
- 版本筛选在Service层基于MetadataReader实现

**✅ 图表组件可配置:**
- 通过props传递xRange/yRange
- 支持单任务和全部任务数据

---

### 4.3 性能考虑

**数据加载优化:**
- 全部任务数据一次性加载（避免5次请求）
- 前端缓存已加载数据
- 切换任务时复用数据（如果已加载）

**图表渲染优化:**
- 热力图网格密度可配置(默认50x50)
- 大数据量时自动降采样
- 使用ECharts的dataZoom实现缩放

---

## 6. 开发计划

> **注意:** 国际化(i18n)将贯穿所有开发阶段。每个阶段完成功能开发后，立即进行对应的i18n改造和测试。

### 阶段1: 数据版本筛选器 (预估2小时)

**后端开发:**
- [ ] 修改`service.py` - `get_subjects()`支持version参数
- [ ] 修改`api.py` - `/api/data/subjects`支持version查询参数
- [ ] 单元测试 - 验证版本筛选逻辑

**前端开发:**
- [ ] 修改`Module01.jsx` - 添加版本选择器UI
- [ ] 修改`dataService.js` - `getSubjects()`传递version参数
- [ ] 交互测试 - 验证版本切换联动

**验收标准:**
- ✅ 选择"全部版本"显示所有受试者
- ✅ 选择"V1"只显示v1受试者
- ✅ 选择"V2"只显示v2受试者
- ✅ 版本切换时受试者列表正确更新

---

### 阶段2: 全部任务加载 (预估3小时)

**后端开发:**
- [ ] 新增`service.py` - `load_all_tasks_data()`方法
- [ ] 新增`api.py` - `GET /api/data/raw/all`端点
- [ ] 单元测试 - 验证数据合并逻辑
- [ ] API测试 - 验证响应格式

**前端开发:**
- [ ] 修改`Module01.jsx` - 任务选择器增加"全部任务"
- [ ] 新增`dataService.js` - `loadAllTasksData()`方法
- [ ] 修改`loadGazeData()` - 支持加载全部任务
- [ ] 数据统计卡片 - 显示各任务数据点数量

**验收标准:**
- ✅ 任务选择器顶部显示"全部任务"
- ✅ 选择"全部任务"成功加载Q1-Q5数据
- ✅ 数据统计显示合并后的总计信息
- ✅ 轨迹图和热力图正确显示多任务数据

---

### 阶段3: 可视化布局重构 (预估2小时)

**前端开发:**
- [ ] 修改`Module01.jsx` - 移除Tabs，改用Row/Col布局
- [ ] 修改`GazeTrajectoryChart.jsx` - 支持xRange/yRange props
- [ ] 修改`HeatmapChart.jsx` - 支持xRange/yRange props
- [ ] CSS调整 - 左右分栏样式优化
- [ ] 响应式测试 - 不同屏幕尺寸测试

**验收标准:**
- ✅ 轨迹图和热力图左右并排显示
- ✅ 两个图表高度一致
- ✅ 图表坐标轴范围固定为(0,0)-(1,1)
- ✅ 坐标轴标签显示"归一化坐标"

---

### 阶段4: 归一化坐标标注 (预估1小时)

**图表组件修改:**
- [ ] `GazeTrajectoryChart.jsx` - 坐标轴名称修改
- [ ] `HeatmapChart.jsx` - 坐标轴名称修改
- [ ] 网格线样式优化
- [ ] Tooltip信息完善

**验收标准:**
- ✅ X轴显示"X (归一化坐标)"
- ✅ Y轴显示"Y (归一化坐标)"
- ✅ 网格线清晰可见
- ✅ Tooltip显示精确坐标值

---

### 阶段5: 集成测试与文档 (预估1小时)

**测试:**
- [ ] 端到端测试 - 完整工作流测试
- [ ] 边界条件测试 - 空数据、单任务、缺失任务
- [ ] 性能测试 - 大数据量加载测试
- [ ] 浏览器兼容性测试

**文档:**
- [ ] 更新API文档
- [ ] 更新用户手册
- [ ] 创建优化完成报告

**验收标准:**
- ✅ 所有功能正常工作
- ✅ 无明显性能问题
- ✅ 文档完整准确

---

**总预估时间(含i18n):** 9小时 + 7.5小时 = **16.5小时**

---

## 7. 测试验证

### 7.1 功能测试用例

#### 测试用例1: 数据版本筛选

| 步骤 | 操作 | 预期结果 |
|-----|------|---------|
| 1 | 选择组别"对照组" | 默认显示"全部版本" |
| 2 | 版本选择器选择"全部版本" | 显示所有v1和v2受试者 |
| 3 | 版本选择器选择"V1 (旧数据)" | 只显示v1受试者 |
| 4 | 版本选择器选择"V2 (新数据)" | 只显示v2受试者 |
| 5 | 切换回"全部版本" | 恢复显示所有受试者 |

---

#### 测试用例2: 全部任务加载

| 步骤 | 操作 | 预期结果 |
|-----|------|---------|
| 1 | 选择受试者"control_01" | 任务选择器显示"全部任务"和Q1-Q5 |
| 2 | 选择"全部任务" | 任务选择器值为"all" |
| 3 | 点击"加载数据" | 成功加载Q1-Q5所有数据 |
| 4 | 查看数据统计 | 显示合并后总计(total_points, duration) |
| 5 | 查看轨迹图 | 显示Q1-Q5不同颜色的轨迹点 |
| 6 | 查看热力图 | 显示Q1-Q5合并的热力分布 |

---

#### 测试用例3: 可视化布局

| 步骤 | 操作 | 预期结果 |
|-----|------|---------|
| 1 | 加载任意任务数据 | 轨迹图和热力图左右并排 |
| 2 | 检查轨迹图坐标轴 | X轴和Y轴范围0-1 |
| 3 | 检查热力图坐标轴 | X轴和Y轴范围0-1 |
| 4 | 检查坐标轴标签 | 显示"归一化坐标" |
| 5 | 鼠标悬停数据点 | Tooltip显示精确坐标 |

---

### 6.2 边界条件测试

**场景1: 受试者只有部分任务**
- 选择"全部任务"时，只加载可用任务
- 数据统计正确反映实际加载的任务数

**场景2: 数据文件缺失**
- API返回友好错误提示
- 前端显示错误信息，不崩溃

**场景3: 版本筛选后无受试者**
- 受试者选择器显示为空
- 提示用户切换版本或组别

---

### 6.3 性能测试

**大数据量测试:**
- 加载Q1-Q5全部任务(约5000+数据点)
- 页面响应时间 < 2秒
- 图表渲染流畅，无卡顿

**并发测试:**
- 快速切换版本/受试者/任务
- 请求正确取消或去重
- 无重复加载

---

## 7. 风险评估

### 7.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|-----|-----|-----|---------|
| 大数据量导致前端渲染卡顿 | 中 | 中 | ECharts降采样，分页加载 |
| 全部任务数据合并逻辑错误 | 高 | 低 | 充分的单元测试和数据验证 |
| 坐标轴范围固定导致数据点超出范围 | 低 | 低 | Module00已归一化，理论上不会超出 |

---

### 7.2 用户体验风险

| 风险 | 影响 | 概率 | 应对措施 |
|-----|-----|-----|---------|
| 左右分栏在小屏幕上显示不佳 | 中 | 中 | 响应式设计，小屏幕改为上下布局 |
| 版本筛选逻辑不清晰 | 低 | 低 | 添加说明文字和Tooltip |
| 全部任务数据颜色区分不明显 | 低 | 中 | 添加图例，使用高对比度颜色 |

---

## 8. 回滚方案

**如果优化出现严重问题，可快速回滚:**

1. **前端回滚:**
   ```bash
   git checkout HEAD~1 frontend/src/pages/Module01/Module01.jsx
   git checkout HEAD~1 frontend/src/components/Charts/
   git checkout HEAD~1 frontend/src/services/dataService.js
   ```

2. **后端回滚:**
   ```bash
   git checkout HEAD~1 src/web/modules/module01_data_visualization/service.py
   git checkout HEAD~1 src/web/modules/module01_data_visualization/api.py
   ```

3. **数据库/元数据:**
   - 本次优化不涉及数据库修改
   - 无需回滚元数据

---

## 9. 附录

### 9.1 相关文档

- [Module01开发计划](MODULE01_DEVELOPMENT_PLAN.md)
- [MetadataReader共享化重构](OPTIMIZATION_METADATA_READER_REFACTOR.md)
- [前端编码规范](FRONTEND_CODING_STANDARDS.md)
- [后端编码规范](BACKEND_CODING_STANDARDS.md)

---

### 9.2 开发环境

**前端:**
- React 18.x
- Ant Design 5.x
- ECharts 5.x

**后端:**
- Python 3.9+
- Flask 2.x
- Pandas 2.x

---

### 9.3 i18n常见陷阱与最佳实践

#### 🚨 陷阱1: 变量名与翻译函数冲突

**问题描述:**
使用 `useTranslation()` 返回的 `t` 函数时，在回调函数（如map、filter等）中使用相同的变量名会导致命名冲突。

**❌ 错误示例:**
```javascript
const { t } = useTranslation(['module01']);

// ❌ 错误：map回调中的参数t覆盖了翻译函数t
const plotData = time.map((t, i) => `${t('label')}: ${t.toFixed(2)}`);
//                             ↑ 这个t是数字，不是翻译函数！
```

**错误信息:**
```
Uncaught TypeError: t is not a function
    at GazeTrajectoryChart.jsx:54:37
```

**✅ 正确示例:**
```javascript
const { t } = useTranslation(['module01']);

// ✅ 正确：使用描述性变量名
const plotData = time.map((timeValue, i) => `${t('label')}: ${timeValue.toFixed(2)}`);
//                          ↑ 使用语义化的变量名
```

**最佳实践:**
1. **避免使用单字母变量名**，尤其是 `t`, `i`, `e` 等常用名称
2. **使用描述性变量名**：
   - `timeValue` 而非 `t`
   - `item` 或 `element` 而非 `e`
   - `index` 或 `idx` 而非 `i`（如果不是循环计数器）
3. **在useMemo依赖中包含t**：确保翻译函数变化时重新计算

```javascript
const plotData = useMemo(() => {
  // ... 使用 t() 的代码
}, [data, t]); // ← 重要：将 t 添加到依赖数组
```

#### 🚨 陷阱2: 图表配置对象未使用useMemo包裹

**问题描述:**
图表配置对象（layout、config等）如果包含翻译函数调用，但没有使用useMemo包裹，会导致语言切换时不更新。

**❌ 错误示例:**
```javascript
const { t } = useTranslation(['module01']);

// ❌ 错误：layout是普通对象，不会响应语言变化
const layout = {
  xaxis: { title: t('xAxis') },
  yaxis: { title: t('yAxis') }
};
// 语言切换时，layout不会重新计算，仍然显示旧语言！
```

**✅ 正确示例:**
```javascript
const { t } = useTranslation(['module01']);

// ✅ 正确：使用useMemo并添加t依赖
const layout = useMemo(() => ({
  xaxis: { title: t('xAxis') },
  yaxis: { title: t('yAxis') }
}), [t]); // ← t作为依赖，语言切换时会重新计算
```

**实际代码示例 - GazeTrajectoryChart.jsx:**
```javascript
const { t } = useTranslation(['module01']);

// ✅ plotData: 使用useMemo，包含t依赖
const plotData = useMemo(() => {
  return [{
    x: data.x,
    y: data.y,
    name: t('trajectoryChart'),
    text: time.map((timeValue, i) =>
      `${t('point')} ${i + 1}<br>${t('timeSeconds')}: ${timeValue.toFixed(2)}`
    )
  }];
}, [data, t]); // ← 包含t依赖

// ✅ layout: 使用useMemo，包含t依赖
const layout = useMemo(() => ({
  xaxis: { title: t('xCoordinateNormalized') },
  yaxis: { title: t('yCoordinateNormalized') }
}), [t]); // ← 包含t依赖
```

#### 参考文档

详细的i18n最佳实践请参考：
- [I18N_QUICK_REFERENCE.md](I18N_QUICK_REFERENCE.md) - 快速参考指南（包含完整的陷阱说明）
- [I18N_ARCHITECTURE_DESIGN.md](I18N_ARCHITECTURE_DESIGN.md) - 架构设计文档

---

### 9.4 更新日志

| 日期 | 版本 | 更新内容 |
|-----|-----|---------|
| 2025-10-02 | v1.0 | 初始版本，包含3项优化需求的完整设计 |
| 2025-10-02 | v1.1 | 添加i18n常见陷阱与最佳实践 |

---

**文档状态:** ✅ 完成
**下一步:** 按阶段1-5顺序开始开发
