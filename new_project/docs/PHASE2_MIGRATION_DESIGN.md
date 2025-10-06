# 阶段2: 模块迁移设计与开发文档
# Phase 2: Module Migration Design and Development Guide

**文档版本**: 1.0.0
**创建时间**: 2025-10-03
**前置依赖**: 阶段1完成(TaskConfigService已实现)
**状态**: 设计规范

---

## 📋 执行摘要

**目标**: 将Module00, Module01, ModuleEX, UnifiedROIService从硬编码任务配置迁移到TaskConfigService动态配置

**时间**: 4周 (Week 2-5)
**影响**: 中等 (渐进式迁移,向后兼容)
**收益**: 支持Q1-Q8及任意任务扩展

---

## 1. 模块现状分析

### 1.1 硬编码位置清单

#### Module00 (数据导入模块)

| 文件 | 行号 | 硬编码内容 | 影响 |
|------|------|-----------|------|
| `eye_tracking_v2_importer.py` | 308 | `required_tasks = {'q1', 'q2', 'q3', 'q4', 'q5'}` | 数据验证 |
| `converter.py` | 142 | `'converted_tasks': ['q1', 'q2', 'q3', 'q4', 'q5']` | 转换记录 |

**代码示例**:
```python
# 当前硬编码 (eye_tracking_v2_importer.py:308)
required_tasks = {'q1', 'q2', 'q3', 'q4', 'q5'}
missing_tasks = required_tasks - set(available_tasks)
if missing_tasks:
    logger.warning(f"Subject {subject_id} missing tasks: {missing_tasks}")
    continue
```

#### UnifiedROIService (ROI配置服务)

| 文件 | 行号 | 硬编码内容 | 影响 |
|------|------|-----------|------|
| `src/services/roi_service.py` | 19-31 | `TASK_ID_MAPPING = {...}` | ID映射 |
| `src/services/roi_service.py` | 317-322 | `task_names = {...}` | 任务名称 |
| `src/services/roi_service.py` | 344 | `["q1", "q2", "q3", "q4", "q5"]` | 默认列表 |

**代码示例**:
```python
# 当前硬编码 (roi_service.py:19-31)
TASK_ID_MAPPING = {
    "q1": "task1",
    "q2": "task2",
    # ...
}

# 当前硬编码 (roi_service.py:317-322)
task_names = {
    'q1': '时间定向',
    'q2': '地点定向',
    # ...
}
```

#### ModuleEX (ROI配置工具)

| 文件 | 行号 | 硬编码内容 | 影响 |
|------|------|-----------|------|
| `moduleEX_roi_config/service.py` | 21-34 | `TASK_ID_MAPPING` (重复) | ID映射 |

#### Module01 (数据可视化)

| 文件 | 位置 | 硬编码内容 | 影响 |
|------|------|-----------|------|
| `service.py` | 多处 | 使用UnifiedROIService的硬编码 | 间接依赖 |
| `Module01.jsx` | 前端 | 任务选择UI固定 | 用户体验 |

---

## 2. 迁移策略

### 2.1 分模块迁移顺序

```
阶段2.1: UnifiedROIService  (Week 2)  [基础服务层]
    ↓
阶段2.2: Module00           (Week 3)  [数据导入]
    ↓
阶段2.3: Module01           (Week 4)  [数据可视化]
    ↓
阶段2.4: ModuleEX           (Week 5)  [ROI配置工具]
```

**迁移原则**:
- ✅ 自底向上 (先服务层,后业务层)
- ✅ 渐进式 (每个模块独立迁移)
- ✅ 向后兼容 (默认mmse_v1数据集)
- ✅ 充分测试 (每阶段完成后验证)

---

## 3. 阶段2.1: UnifiedROIService迁移

### 3.1 迁移目标

将UnifiedROIService的任务ID映射和任务名称从硬编码转为从TaskConfigService动态查询

### 3.2 修改内容

#### 修改1: 移除硬编码TASK_ID_MAPPING

**文件**: `src/services/roi_service.py`

**修改前** (Line 19-31):
```python
TASK_ID_MAPPING = {
    "q1": "task1",
    "q2": "task2",
    "q3": "task3",
    "q4": "task4",
    "q5": "task5",
    "task1": "q1",
    "task2": "q2",
    "task3": "q3",
    "task4": "q4",
    "task5": "q5"
}
```

**修改后**:
```python
# TASK_ID_MAPPING 已移除,使用TaskConfigService动态查询
from src.services.task_config_service import get_task_config_service
```

#### 修改2: normalize_task_id方法重构

**修改前** (Line 49-74):
```python
def normalize_task_id(self, task_id: str) -> Tuple[str, str]:
    task_lower = task_id.lower()

    if task_lower.startswith('q'):
        legacy_id = task_lower
        new_id = TASK_ID_MAPPING.get(task_lower, task_lower)
    elif task_lower.startswith('task'):
        new_id = task_lower
        legacy_id = TASK_ID_MAPPING.get(task_lower, task_lower)
    else:
        legacy_id = task_lower
        new_id = task_lower

    return legacy_id, new_id
```

**修改后**:
```python
def normalize_task_id(self, task_id: str, dataset_id: str = "mmse_v1") -> Tuple[str, str]:
    """
    标准化Task ID (使用TaskConfigService动态查询)

    Args:
        task_id: 原始task ID
        dataset_id: 数据集ID,默认mmse_v1 (向后兼容)

    Returns:
        (legacy_id, new_id) 例如: ("q1", "task1")
    """
    task_service = get_task_config_service()

    # 使用TaskConfigService查询任务配置
    normalized_id = task_service.normalize_task_id(dataset_id, task_id)

    if normalized_id:
        # 查询成功,获取任务配置
        task_config = task_service.get_task_by_id(dataset_id, normalized_id)
        alt_ids = task_config.get("alt_ids", [])

        # 返回主ID和第一个备用ID (模拟旧的legacy_id/new_id逻辑)
        new_id = alt_ids[0] if alt_ids else normalized_id
        return normalized_id, new_id
    else:
        # 查询失败,回退到原始ID
        logger.warning(f"Task '{task_id}' not found in dataset '{dataset_id}', using original ID")
        return task_id, task_id
```

#### 修改3: 移除硬编码task_names

**修改前** (Line 317-322):
```python
task_names = {
    'q1': '时间定向',
    'q2': '地点定向',
    'q3': '记忆',
    'q4': '注意与计算',
    'q5': '回忆'
}
config_data['task_name'] = task_names.get(legacy_id, legacy_id.upper())
```

**修改后**:
```python
# 从TaskConfigService获取任务名称
task_service = get_task_config_service()
task_config = task_service.get_task_by_id(dataset_id, legacy_id)
config_data['task_name'] = task_config['name'] if task_config else legacy_id.upper()
```

### 3.3 测试用例

**文件**: `tests/test_unified_roi_service.py`

```python
def test_normalize_task_id_with_task_config():
    """测试使用TaskConfigService的normalize_task_id"""
    service = UnifiedROIService()

    # 测试V1数据集
    legacy_id, new_id = service.normalize_task_id("task1", dataset_id="mmse_v1")
    assert legacy_id == "q1"
    assert new_id == "task1"

    # 测试V2数据集
    legacy_id2, new_id2 = service.normalize_task_id("q2", dataset_id="mmse_v2")
    assert legacy_id2 == "q2"

def test_get_task_name_from_config():
    """测试从TaskConfigService获取任务名称"""
    service = UnifiedROIService()
    result = service.get_roi_config_enhanced("v1", "q1")

    assert result["success"] is True
    assert result["data"]["task_name"] == "时间定向"
```

---

## 4. 阶段2.2: Module00迁移

### 4.1 迁移目标

将数据导入验证从硬编码必需任务列表改为动态查询

### 4.2 修改内容

#### 修改1: eye_tracking_v2_importer.py

**文件**: `src/web/modules/module00_data_management/eye_tracking_v2_importer.py`

**修改前** (Line 308):
```python
# 硬编码必需任务
required_tasks = {'q1', 'q2', 'q3', 'q4', 'q5'}

# 验证数据完整性
available_tasks = set(subject_tasks.keys())
missing_tasks = required_tasks - available_tasks

if missing_tasks:
    logger.warning(f"Subject {subject_id} missing required tasks: {missing_tasks}, skipping")
    skipped_subjects.append({
        'id': subject_id,
        'reason': f'Missing tasks: {missing_tasks}'
    })
    continue
```

**修改后**:
```python
from src.services.task_config_service import get_task_config_service

# 动态获取必需任务列表
task_service = get_task_config_service()
available_tasks = set(subject_tasks.keys())

# 自动推断数据集类型
dataset_id, confidence = task_service.infer_dataset_from_data(list(available_tasks))

if dataset_id:
    # 成功推断数据集,获取必需任务
    required_tasks = set(task_service.get_required_tasks(dataset_id))
    logger.info(f"Inferred dataset '{dataset_id}' for subject {subject_id} (confidence: {confidence*100:.1f}%)")
else:
    # 无法推断,使用默认数据集
    dataset_id = "mmse_v1"
    required_tasks = set(task_service.get_required_tasks(dataset_id))
    logger.warning(f"Could not infer dataset for subject {subject_id}, using default '{dataset_id}'")

# 验证数据完整性
missing_tasks = required_tasks - available_tasks

if missing_tasks:
    logger.warning(f"Subject {subject_id} missing required tasks: {missing_tasks}, skipping")
    skipped_subjects.append({
        'id': subject_id,
        'reason': f'Missing tasks: {missing_tasks}',
        'dataset': dataset_id
    })
    continue

# 记录数据集信息到元数据
subject_metadata['dataset_id'] = dataset_id
subject_metadata['dataset_confidence'] = confidence
```

### 4.3 元数据增强

在导入的元数据中添加数据集信息:

```python
# metadata.json 增强字段
{
    "subject_id": "control_001",
    "group": "control",
    "data_version": "v1",
    "dataset_id": "mmse_v1",        # 新增
    "dataset_confidence": 1.0,       # 新增
    "tasks": ["q1", "q2", "q3", "q4", "q5"],
    ...
}
```

---

## 5. 阶段2.3: Module01迁移

### 5.1 前端迁移

#### 修改1: 动态任务选择器

**文件**: `frontend/src/pages/Module01/Module01.jsx`

**修改前**:
```jsx
// 硬编码任务选择
<Select value={selectedTask} onChange={setSelectedTask}>
  <Option value="all">全部任务</Option>
  <Option value="q1">Q1 - 时间定向</Option>
  <Option value="q2">Q2 - 地点定向</Option>
  <Option value="q3">Q3 - 记忆</Option>
  <Option value="q4">Q4 - 注意与计算</Option>
  <Option value="q5">Q5 - 回忆</Option>
</Select>
```

**修改后**:
```jsx
import { taskConfigService } from '../../services/taskConfigService';

const [availableTasks, setAvailableTasks] = useState([]);
const [datasetId, setDatasetId] = useState('mmse_v1');

// 加载任务列表
useEffect(() => {
  const loadTasks = async () => {
    const result = await taskConfigService.getTasks(datasetId);
    if (result.success) {
      setAvailableTasks(result.data.tasks);
    }
  };
  loadTasks();
}, [datasetId]);

// 动态渲染任务选择器
<Select value={selectedTask} onChange={setSelectedTask}>
  <Option value="all">全部任务</Option>
  {availableTasks.map(task => (
    <Option key={task.id} value={task.id}>
      {task.id.toUpperCase()} - {task.name}
    </Option>
  ))}
</Select>
```

#### 修改2: 数据集选择器 (新增功能)

```jsx
<Select
  value={datasetId}
  onChange={setDatasetId}
  style={{ width: 200, marginRight: 16 }}
>
  <Option value="mmse_v1">MMSE V1 (Q1-Q5)</Option>
  <Option value="mmse_v2">MMSE V2 (Q1-Q5)</Option>
  {/* 未来支持: mmse_extended (Q1-Q8) */}
</Select>
```

---

## 6. 阶段2.4: ModuleEX迁移

### 6.1 迁移目标

支持多数据集ROI配置管理,动态任务列表

### 6.2 修改内容

#### 修改1: ROIEditor数据集切换

**文件**: `frontend/src/components/ModuleEX/ROIEditor.jsx`

**新增功能**:
```jsx
import { taskConfigService } from '../../services/taskConfigService';

const ROIEditor = () => {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState('mmse_v1');
  const [availableTasks, setAvailableTasks] = useState([]);

  // 加载数据集列表
  useEffect(() => {
    const loadDatasets = async () => {
      const result = await taskConfigService.getDatasets();
      if (result.success) {
        setDatasets(result.data);
      }
    };
    loadDatasets();
  }, []);

  // 加载任务列表
  useEffect(() => {
    const loadTasks = async () => {
      const result = await taskConfigService.getTasks(selectedDataset);
      if (result.success) {
        setAvailableTasks(result.data.tasks);
      }
    };
    loadTasks();
  }, [selectedDataset]);

  return (
    <Card>
      {/* 数据集选择器 */}
      <Select
        value={selectedDataset}
        onChange={setSelectedDataset}
        style={{ width: 300, marginBottom: 16 }}
      >
        {datasets.map(ds => (
          <Option key={ds.id} value={ds.id}>
            {ds.name} ({ds.task_count}个任务)
          </Option>
        ))}
      </Select>

      {/* 任务选择器 - 动态渲染 */}
      <Select value={selectedTaskId} onChange={loadBackgroundImage}>
        {availableTasks.map(task => (
          <Option key={task.id} value={task.id}>
            {task.id.toUpperCase()} - {task.name}
          </Option>
        ))}
      </Select>

      {/* ROI Canvas等其他组件 */}
    </Card>
  );
};
```

---

## 7. 测试计划

### 7.1 单元测试

| 测试文件 | 测试内容 | 覆盖率目标 |
|---------|---------|-----------|
| `test_unified_roi_service.py` | ROI服务动态配置 | 90%+ |
| `test_module00_importer.py` | 数据导入动态验证 | 85%+ |
| `test_task_config_integration.py` | 集成测试 | 80%+ |

### 7.2 集成测试场景

#### 场景1: V1数据导入和可视化

```python
def test_v1_data_end_to_end():
    """测试V1数据完整流程"""
    # 1. Module00导入V1数据 (Q1-Q5)
    importer = EyeTrackingV2Importer()
    result = importer.import_data(v1_data_path)
    assert result['success'] is True
    assert result['metadata']['dataset_id'] == 'mmse_v1'

    # 2. Module01加载ROI配置
    roi_service = UnifiedROIService()
    roi_result = roi_service.get_roi_config_enhanced("v1", "q1")
    assert roi_result['success'] is True
    assert roi_result['data']['task_name'] == '时间定向'
```

#### 场景2: 扩展数据集 (Q1-Q8)

```python
def test_extended_dataset():
    """测试Q1-Q8扩展数据集"""
    # 1. 注册扩展数据集
    task_service = get_task_config_service()
    extended_dataset = create_extended_dataset_config()  # Q1-Q8
    task_service.register_dataset(extended_dataset)

    # 2. 导入Q1-Q8数据
    importer = EyeTrackingV2Importer()
    result = importer.import_data(extended_data_path)
    assert result['metadata']['dataset_id'] == 'mmse_extended'

    # 3. 验证8个任务都正确导入
    assert len(result['imported_tasks']) == 8
```

---

## 8. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 向后兼容性破坏 | 高 | 低 | 默认dataset_id="mmse_v1",充分回归测试 |
| 性能下降 | 中 | 低 | 配置缓存,避免重复查询 |
| 数据集推断错误 | 中 | 中 | 提供手动指定dataset_id选项 |
| 前端UI不兼容 | 低 | 低 | 渐进式增强,保留原有UI |

---

## 9. 验收标准

### 阶段2.1完成标准
- ✅ UnifiedROIService不再使用硬编码TASK_ID_MAPPING
- ✅ 所有ROI相关测试通过
- ✅ V1和V2数据ROI配置正常加载

### 阶段2.2完成标准
- ✅ Module00能自动推断数据集类型
- ✅ 支持Q1-Q5和Q1-Q8数据导入
- ✅ 元数据包含dataset_id字段

### 阶段2.3完成标准
- ✅ Module01前端动态加载任务列表
- ✅ 支持数据集切换
- ✅ ROI可视化适配动态任务

### 阶段2.4完成标准
- ✅ ModuleEX支持多数据集管理
- ✅ 可为Q1-Q8配置ROI
- ✅ UI动态渲染任务列表

---

## 10. 里程碑时间表

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| 阶段2.1完成 | Week 2 末 | UnifiedROIService迁移 + 测试 |
| 阶段2.2完成 | Week 3 末 | Module00迁移 + 测试 |
| 阶段2.3完成 | Week 4 末 | Module01迁移 + 测试 |
| 阶段2.4完成 | Week 5 末 | ModuleEX迁移 + 测试 |
| 阶段2验收 | Week 5 末 | 全面回归测试 + 文档更新 |

---

**文档状态**: ✅ 设计完成,等待实施
**下一步**: 开始阶段2.1 UnifiedROIService迁移
