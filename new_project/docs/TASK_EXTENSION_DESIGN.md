# 任务扩展性设计与开发文档
# Task Extension Design and Development Guide

**文档版本**: 1.0.0
**创建时间**: 2025-10-03
**作者**: VR Eye Tracking Team
**状态**: 设计规范

---

## 📋 目录

1. [问题分析](#1-问题分析)
2. [设计目标](#2-设计目标)
3. [架构设计](#3-架构设计)
4. [实施方案](#4-实施方案)
5. [开发指南](#5-开发指南)
6. [示例场景](#6-示例场景)
7. [迁移计划](#7-迁移计划)

---

## 1. 问题分析

### 1.1 当前硬编码问题

当前系统存在以下任务配置硬编码问题:

#### 后端硬编码位置

| 文件 | 行数 | 硬编码内容 | 影响范围 |
|------|------|-----------|---------|
| `src/services/roi_service.py` | 19-31 | `TASK_ID_MAPPING = {"q1": "task1", ...}` | ROI配置加载 |
| `src/services/roi_service.py` | 317-322 | `task_names = {"q1": "时间定向", ...}` | 任务名称显示 |
| `src/services/roi_service.py` | 344 | `["q1", "q2", "q3", "q4", "q5"]` | 默认任务列表 |
| `module00/eye_tracking_v2_importer.py` | 308 | `required_tasks = {"q1", "q2", "q3", "q4", "q5"}` | 数据导入验证 |
| `module00/converter.py` | 142 | `'converted_tasks': ['q1', 'q2', 'q3', 'q4', 'q5']` | 数据转换记录 |

#### 前端硬编码位置

| 文件 | 硬编码内容 | 影响范围 |
|------|-----------|---------|
| `frontend/src/pages/Module01/Module01.jsx` | 任务选择下拉列表 | UI显示 |
| `frontend/src/components/Charts/*` | ROI配置假设5个任务 | 图表渲染 |

### 1.2 扩展性限制

**当前系统无法支持以下场景:**

1. ❌ **任务数量变化**: 导入Q1-Q8数据时,系统只识别Q1-Q5
2. ❌ **任务ID变化**: 使用不同命名(如T1-T5)时无法识别
3. ❌ **任务内容变化**: 不同实验设计的任务集合无法支持
4. ❌ **多数据集混合**: 不同任务配置的数据无法共存

### 1.3 根本原因

- **配置分散**: 任务配置散落在多个文件中
- **缺少元数据**: 没有统一的任务配置元数据文件
- **硬编码依赖**: 代码逻辑直接依赖固定任务列表

---

## 2. 设计目标

### 2.1 核心目标

1. ✅ **动态任务配置**: 支持任意数量和类型的任务
2. ✅ **向后兼容**: 现有Q1-Q5数据无缝迁移
3. ✅ **自动发现**: 根据数据自动识别任务配置
4. ✅ **多版本共存**: 支持不同任务配置的数据集并存

### 2.2 设计原则

- **配置驱动**: 所有任务信息从配置文件读取
- **数据驱动**: 根据实际数据自动推断任务列表
- **中心化管理**: 统一的任务配置管理服务
- **架构合规**: 符合现有Flask + React架构规范

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     任务配置层 (Task Config Layer)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         TaskConfigService (中心化服务)                 │  │
│  │  - 读取任务配置文件                                      │  │
│  │  - 自动发现数据集任务                                    │  │
│  │  │  - 提供统一任务查询接口                              │  │
│  └──────────────────────────────────────────────────────┘  │
│         ▲                    ▲                    ▲         │
│         │                    │                    │         │
└─────────┼────────────────────┼────────────────────┼─────────┘
          │                    │                    │
┌─────────┴────────┐  ┌────────┴────────┐  ┌───────┴─────────┐
│   Module00       │  │   Module01      │  │   ModuleEX      │
│ 数据导入模块        │  │ 数据可视化模块     │  │  ROI配置模块     │
│                  │  │                 │  │                 │
│ - 动态任务验证     │  │ - 动态任务列表    │  │ - 动态ROI配置   │
│ - 自适应导入       │  │ - 动态图表渲染    │  │ - 任务模板管理   │
└──────────────────┘  └─────────────────┘  └─────────────────┘
```

### 3.2 核心组件

#### 3.2.1 任务配置文件结构

**路径**: `config/task_configs.json`

```json
{
  "version": "1.0.0",
  "last_modified": "2025-10-03T00:00:00Z",
  "datasets": {
    "mmse_v1": {
      "name": "MMSE认知评估 (V1版本)",
      "description": "包含5个MMSE任务的眼动数据",
      "data_version": "v1",
      "tasks": [
        {
          "id": "q1",
          "alt_ids": ["task1", "Q1"],
          "name": "时间定向",
          "name_en": "Time Orientation",
          "description": "评估受试者对时间的定向能力",
          "order": 1,
          "background_image": "Q1.jpg",
          "roi_config": "q1_roi.json",
          "required": true
        },
        {
          "id": "q2",
          "alt_ids": ["task2", "Q2"],
          "name": "地点定向",
          "name_en": "Place Orientation",
          "description": "评估受试者对地点的定向能力",
          "order": 2,
          "background_image": "Q2.jpg",
          "roi_config": "q2_roi.json",
          "required": true
        }
        // ... q3-q5
      ]
    },
    "mmse_v2": {
      "name": "MMSE认知评估 (V2版本)",
      "description": "扩展至8个任务的MMSE眼动数据",
      "data_version": "v2",
      "tasks": [
        // Q1-Q8 任务配置
        {
          "id": "q6",
          "alt_ids": ["task6"],
          "name": "语言能力",
          "name_en": "Language Ability",
          "description": "评估受试者的语言表达能力",
          "order": 6,
          "background_image": "task6.png",
          "roi_config": "q6_roi.json",
          "required": false
        }
      ]
    },
    "custom_experiment": {
      "name": "自定义实验数据集",
      "description": "用户自定义的任务配置",
      "data_version": "custom",
      "tasks": [
        {
          "id": "t1",
          "alt_ids": ["task1"],
          "name": "阅读理解",
          "name_en": "Reading Comprehension",
          "description": "阅读理解任务",
          "order": 1,
          "background_image": "reading.png",
          "roi_config": "reading_roi.json",
          "required": true
        }
      ]
    }
  }
}
```

#### 3.2.2 TaskConfigService 服务类

**路径**: `src/services/task_config_service.py`

```python
"""
任务配置管理服务
Task Configuration Management Service
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from config.settings import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskConfigService:
    """任务配置管理服务"""

    def __init__(self):
        """初始化服务"""
        self.config_file = Path(Config.PROJECT_ROOT) / "config" / "task_configs.json"
        self._config_cache = None
        self._load_config()

    def _load_config(self):
        """加载任务配置文件"""
        if not self.config_file.exists():
            logger.warning(f"Task config file not found: {self.config_file}")
            self._create_default_config()

        with open(self.config_file, 'r', encoding='utf-8') as f:
            self._config_cache = json.load(f)

        logger.info(f"Loaded task config: {len(self._config_cache.get('datasets', {}))} datasets")

    def _create_default_config(self):
        """创建默认配置文件(向后兼容Q1-Q5)"""
        default_config = {
            "version": "1.0.0",
            "last_modified": datetime.now().isoformat(),
            "datasets": {
                "mmse_v1": self._generate_default_v1_config(),
                "mmse_v2": self._generate_default_v2_config()
            }
        }

        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

        logger.info(f"Created default task config: {self.config_file}")

    def get_dataset_config(self, dataset_id: str) -> Optional[Dict]:
        """
        获取数据集配置

        Args:
            dataset_id: 数据集ID (如 "mmse_v1", "custom_experiment")

        Returns:
            数据集配置字典或None
        """
        return self._config_cache.get("datasets", {}).get(dataset_id)

    def get_tasks(self, dataset_id: str) -> List[Dict]:
        """
        获取数据集的任务列表

        Args:
            dataset_id: 数据集ID

        Returns:
            任务配置列表
        """
        dataset = self.get_dataset_config(dataset_id)
        if not dataset:
            return []

        return dataset.get("tasks", [])

    def get_task_by_id(self, dataset_id: str, task_id: str) -> Optional[Dict]:
        """
        根据任务ID获取任务配置

        Args:
            dataset_id: 数据集ID
            task_id: 任务ID (支持主ID和备用ID)

        Returns:
            任务配置字典或None
        """
        tasks = self.get_tasks(dataset_id)

        for task in tasks:
            # 匹配主ID或备用ID
            if task["id"] == task_id or task_id in task.get("alt_ids", []):
                return task

        return None

    def normalize_task_id(self, dataset_id: str, task_id: str) -> Optional[str]:
        """
        标准化任务ID (将备用ID转换为主ID)

        Args:
            dataset_id: 数据集ID
            task_id: 原始任务ID

        Returns:
            标准化后的主ID或None
        """
        task = self.get_task_by_id(dataset_id, task_id)
        return task["id"] if task else None

    def get_required_tasks(self, dataset_id: str) -> List[str]:
        """
        获取必需任务列表

        Args:
            dataset_id: 数据集ID

        Returns:
            必需任务ID列表
        """
        tasks = self.get_tasks(dataset_id)
        return [task["id"] for task in tasks if task.get("required", False)]

    def infer_dataset_from_data(self, available_tasks: List[str]) -> Optional[str]:
        """
        根据实际数据推断数据集类型

        Args:
            available_tasks: 可用的任务ID列表

        Returns:
            推断的数据集ID或None
        """
        available_set = set(available_tasks)

        # 遍历所有数据集,找到最佳匹配
        best_match = None
        best_score = 0

        for dataset_id, dataset_config in self._config_cache.get("datasets", {}).items():
            tasks = dataset_config.get("tasks", [])
            dataset_task_ids = set(task["id"] for task in tasks)

            # 计算匹配度
            match_count = len(available_set & dataset_task_ids)
            total_count = len(dataset_task_ids)
            score = match_count / total_count if total_count > 0 else 0

            if score > best_score:
                best_score = score
                best_match = dataset_id

        # 匹配度超过50%即认为是该数据集
        if best_score >= 0.5:
            logger.info(f"Inferred dataset '{best_match}' with {best_score*100:.1f}% confidence")
            return best_match

        return None

    def register_dataset(self, dataset_config: Dict) -> bool:
        """
        动态注册新数据集配置

        Args:
            dataset_config: 数据集配置字典

        Returns:
            是否注册成功
        """
        try:
            dataset_id = dataset_config.get("id")
            if not dataset_id:
                logger.error("Dataset config missing 'id' field")
                return False

            # 添加到配置
            if "datasets" not in self._config_cache:
                self._config_cache["datasets"] = {}

            self._config_cache["datasets"][dataset_id] = dataset_config
            self._config_cache["last_modified"] = datetime.now().isoformat()

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, ensure_ascii=False, indent=2)

            logger.info(f"Registered new dataset: {dataset_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register dataset: {e}")
            return False


# 单例模式
_task_config_service_instance = None

def get_task_config_service() -> TaskConfigService:
    """获取TaskConfigService单例"""
    global _task_config_service_instance
    if _task_config_service_instance is None:
        _task_config_service_instance = TaskConfigService()
    return _task_config_service_instance
```

---

## 4. 实施方案

### 4.1 三阶段迁移策略

#### 阶段1: 创建任务配置服务 (不影响现有功能)

**目标**: 建立新的任务配置基础设施

**工作内容**:
1. ✅ 创建 `config/task_configs.json` 配置文件
2. ✅ 实现 `TaskConfigService` 服务类
3. ✅ 添加单元测试
4. ✅ 生成默认配置(兼容Q1-Q5)

**影响范围**: 无,仅添加新代码

#### 阶段2: 模块迁移到任务配置服务

**目标**: 逐步替换硬编码,使用动态配置

**迁移顺序**:

1. **Module00 (数据导入)**
   ```python
   # 修改前 (硬编码)
   required_tasks = {'q1', 'q2', 'q3', 'q4', 'q5'}

   # 修改后 (动态配置)
   from src.services.task_config_service import get_task_config_service

   task_service = get_task_config_service()
   dataset_id = task_service.infer_dataset_from_data(available_tasks)
   required_tasks = set(task_service.get_required_tasks(dataset_id))
   ```

2. **UnifiedROIService (ROI配置)**
   ```python
   # 修改前 (硬编码映射)
   TASK_ID_MAPPING = {"q1": "task1", ...}

   # 修改后 (动态查询)
   def normalize_task_id(self, task_id: str, dataset_id: str = "mmse_v1") -> str:
       task_service = get_task_config_service()
       return task_service.normalize_task_id(dataset_id, task_id) or task_id
   ```

3. **Module01 (数据可视化)**
   ```javascript
   // 前端: 动态加载任务列表
   const loadTasks = async (datasetId) => {
     const result = await taskConfigService.getTasks(datasetId);
     setAvailableTasks(result.data);
   };
   ```

4. **ModuleEX (ROI配置工具)**
   - 支持多数据集切换
   - 动态任务列表UI

#### 阶段3: 清理硬编码 + 文档更新

**工作内容**:
1. 删除所有硬编码任务配置
2. 更新API文档
3. 更新用户手册
4. 添加任务配置示例

### 4.2 向后兼容策略

**保证现有Q1-Q5数据无缝工作:**

1. **默认数据集**: 未指定数据集时,默认使用 `mmse_v1`
2. **自动推断**: 根据目录结构自动推断数据集类型
3. **ID映射**: 保留 `q1 <-> task1` 映射支持

---

## 5. 开发指南

### 5.1 添加新数据集配置

**场景**: 导入Q1-Q8数据集

**步骤**:

1. **编辑配置文件** `config/task_configs.json`:
   ```json
   {
     "datasets": {
       "mmse_extended": {
         "name": "MMSE扩展版 (Q1-Q8)",
         "data_version": "v2_extended",
         "tasks": [
           {"id": "q1", "name": "时间定向", ...},
           {"id": "q2", "name": "地点定向", ...},
           // ... Q3-Q5
           {"id": "q6", "name": "语言能力", "order": 6, ...},
           {"id": "q7", "name": "视空间能力", "order": 7, ...},
           {"id": "q8", "name": "执行功能", "order": 8, ...}
         ]
       }
     }
   }
   ```

2. **准备ROI配置文件**:
   ```
   data/roi_configs/v2_extended/
   ├── q1_roi.json
   ├── q2_roi.json
   ...
   ├── q6_roi.json
   ├── q7_roi.json
   └── q8_roi.json
   ```

3. **准备背景图片**:
   ```
   data/background_images/v2_extended/
   ├── Q1.jpg
   ...
   ├── Q6.jpg
   ├── Q7.jpg
   └── Q8.jpg
   ```

4. **导入数据** (Module00自动识别):
   - 系统自动检测Q1-Q8任务
   - 根据配置验证数据完整性
   - 生成元数据文件

### 5.2 API使用示例

#### 后端API

```python
from src.services.task_config_service import get_task_config_service

# 获取服务实例
task_service = get_task_config_service()

# 获取数据集的所有任务
tasks = task_service.get_tasks("mmse_extended")
# [{"id": "q1", "name": "时间定向", ...}, ..., {"id": "q8", ...}]

# 根据任务ID查询配置
task_config = task_service.get_task_by_id("mmse_extended", "q6")
# {"id": "q6", "name": "语言能力", "background_image": "Q6.jpg", ...}

# 标准化任务ID (支持别名)
normalized_id = task_service.normalize_task_id("mmse_v1", "task1")
# "q1"

# 获取必需任务列表
required = task_service.get_required_tasks("mmse_extended")
# ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"]

# 自动推断数据集
available_tasks = ["q1", "q2", "q6", "q7", "q8"]
dataset_id = task_service.infer_dataset_from_data(available_tasks)
# "mmse_extended"
```

#### 前端API

新增API端点: `/api/config/tasks`

```javascript
// 获取数据集任务列表
GET /api/config/tasks?dataset_id=mmse_extended

// 响应:
{
  "success": true,
  "data": {
    "dataset_id": "mmse_extended",
    "dataset_name": "MMSE扩展版 (Q1-Q8)",
    "tasks": [
      {"id": "q1", "name": "时间定向", "order": 1, ...},
      {"id": "q2", "name": "地点定向", "order": 2, ...},
      ...
      {"id": "q8", "name": "执行功能", "order": 8, ...}
    ]
  }
}
```

```javascript
// React组件中使用
import { taskConfigService } from '@/services/taskConfigService';

const MyComponent = () => {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    const loadTasks = async () => {
      const result = await taskConfigService.getTasks('mmse_extended');
      if (result.success) {
        setTasks(result.data.tasks);
      }
    };
    loadTasks();
  }, []);

  return (
    <Select>
      {tasks.map(task => (
        <Option key={task.id} value={task.id}>
          {task.name} ({task.name_en})
        </Option>
      ))}
    </Select>
  );
};
```

---

## 6. 示例场景

### 场景1: 导入Q1-Q8数据

**用户操作**:
1. 在ModuleEX中添加Q6-Q8的ROI配置
2. 在Module00中选择包含Q1-Q8数据的目录
3. 点击"扫描数据"

**系统行为**:
```python
# 1. Module00扫描到8个任务文件
scanned_tasks = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"]

# 2. 自动推断数据集类型
dataset_id = task_service.infer_dataset_from_data(scanned_tasks)
# -> "mmse_extended"

# 3. 获取必需任务列表
required_tasks = task_service.get_required_tasks(dataset_id)
# -> ["q1", "q2", ..., "q8"]

# 4. 验证数据完整性
missing = set(required_tasks) - set(scanned_tasks)
if missing:
    raise ValueError(f"Missing required tasks: {missing}")

# 5. 导入数据 (所有8个任务)
```

### 场景2: 自定义实验数据集

**用户需求**: 导入自定义的阅读理解实验数据(T1-T3)

**配置步骤**:

1. **创建配置** `config/task_configs.json`:
   ```json
   {
     "datasets": {
       "reading_experiment": {
         "name": "阅读理解实验",
         "data_version": "custom_reading",
         "tasks": [
           {
             "id": "reading_task1",
             "alt_ids": ["t1", "task1"],
             "name": "故事阅读",
             "order": 1,
             "required": true
           },
           {
             "id": "reading_task2",
             "alt_ids": ["t2", "task2"],
             "name": "问题回答",
             "order": 2,
             "required": true
           },
           {
             "id": "reading_task3",
             "alt_ids": ["t3", "task3"],
             "name": "内容回忆",
             "order": 3,
             "required": true
           }
         ]
       }
     }
   }
   ```

2. **准备数据目录**:
   ```
   data/01_raw/eye_tracking/reading_experiment/
   ├── subject001/
   │   ├── reading_task1.csv
   │   ├── reading_task2.csv
   │   └── reading_task3.csv
   └── subject002/
       └── ...
   ```

3. **导入数据**:
   - 系统自动识别`reading_task1-3`
   - 推断数据集为`reading_experiment`
   - 验证并导入

---

## 7. 迁移计划

### 7.1 时间表

| 阶段 | 时间 | 工作内容 | 责任人 |
|------|------|---------|--------|
| 阶段1 | Week 1 | 创建TaskConfigService + 默认配置 | 后端开发 |
| 阶段2.1 | Week 2 | 迁移Module00 (数据导入) | 后端开发 |
| 阶段2.2 | Week 3 | 迁移UnifiedROIService | 后端开发 |
| 阶段2.3 | Week 4 | 迁移Module01 (前后端) | 全栈开发 |
| 阶段2.4 | Week 5 | 迁移ModuleEX (前后端) | 全栈开发 |
| 阶段3 | Week 6 | 清理硬编码 + 文档更新 | 全员 |

### 7.2 风险控制

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 向后兼容性破坏 | 高 | 保留默认配置,充分测试Q1-Q5数据 |
| 性能下降 | 中 | 配置文件缓存,避免重复读取 |
| 配置文件损坏 | 中 | 配置文件版本控制,自动备份 |
| 用户学习成本 | 低 | 提供详细文档和示例 |

### 7.3 测试计划

#### 单元测试

```python
# tests/test_task_config_service.py
def test_get_tasks_mmse_v1():
    """测试获取MMSE v1任务列表"""
    service = get_task_config_service()
    tasks = service.get_tasks("mmse_v1")
    assert len(tasks) == 5
    assert tasks[0]["id"] == "q1"

def test_normalize_task_id():
    """测试任务ID标准化"""
    service = get_task_config_service()
    assert service.normalize_task_id("mmse_v1", "task1") == "q1"
    assert service.normalize_task_id("mmse_v1", "Q1") == "q1"

def test_infer_dataset():
    """测试数据集推断"""
    service = get_task_config_service()
    dataset_id = service.infer_dataset_from_data(["q1", "q2", "q3", "q4", "q5"])
    assert dataset_id == "mmse_v1"

def test_extended_tasks():
    """测试Q1-Q8扩展任务"""
    service = get_task_config_service()
    tasks = service.get_tasks("mmse_extended")
    assert len(tasks) == 8
    assert tasks[7]["id"] == "q8"
```

#### 集成测试

```python
def test_module00_import_extended_data():
    """测试Module00导入Q1-Q8数据"""
    # 模拟Q1-Q8数据导入
    # 验证所有任务正确识别
    # 验证元数据正确生成

def test_module01_visualize_extended_tasks():
    """测试Module01可视化Q1-Q8任务"""
    # 加载Q1-Q8数据
    # 验证任务列表正确显示
    # 验证ROI配置正确加载
```

---

## 8. 附录

### 8.1 配置文件Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "datasets"],
  "properties": {
    "version": {"type": "string"},
    "last_modified": {"type": "string", "format": "date-time"},
    "datasets": {
      "type": "object",
      "patternProperties": {
        "^[a-z0-9_]+$": {
          "type": "object",
          "required": ["name", "data_version", "tasks"],
          "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "data_version": {"type": "string"},
            "tasks": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["id", "name", "order"],
                "properties": {
                  "id": {"type": "string"},
                  "alt_ids": {"type": "array", "items": {"type": "string"}},
                  "name": {"type": "string"},
                  "name_en": {"type": "string"},
                  "description": {"type": "string"},
                  "order": {"type": "integer"},
                  "background_image": {"type": "string"},
                  "roi_config": {"type": "string"},
                  "required": {"type": "boolean"}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 8.2 API参考

详见文档: `docs/API_REFERENCE.md#任务配置API`

---

**文档状态**: ✅ 设计完成,等待评审
**下一步**: 开始阶段1实施
