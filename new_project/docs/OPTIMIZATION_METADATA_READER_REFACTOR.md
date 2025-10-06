# MetadataReader共享化重构方案
# Shared MetadataReader Refactoring Plan

**文档版本**: v1.0
**创建日期**: 2025-10-02
**状态**: 📋 待实施
**优先级**: 🟡 中等（可选优化）

---

## 📋 目录

1. [背景与目标](#背景与目标)
2. [现状分析](#现状分析)
3. [问题与动机](#问题与动机)
4. [解决方案设计](#解决方案设计)
5. [实施步骤](#实施步骤)
6. [代码示例](#代码示例)
7. [影响评估](#影响评估)
8. [测试计划](#测试计划)
9. [回滚方案](#回滚方案)
10. [实施建议](#实施建议)

---

## 🎯 背景与目标

### 当前问题
Module01维护了自己的`MetadataReader`类，用于读取Module00生成的元数据文件（`subject_metadata.json`, `mmse_scores.json`）。

随着项目发展，Module02-10也需要读取相同的元数据，这会导致：
1. **代码重复**：每个模块都需要实现相同的元数据读取逻辑
2. **维护困难**：元数据格式变更需要修改多个文件
3. **一致性风险**：不同模块的实现可能出现差异

### 优化目标
将`MetadataReader`提升为**共享工具类**，供所有模块复用：
- ✅ 消除代码重复
- ✅ 统一元数据读取接口
- ✅ 简化后续模块开发
- ✅ 便于统一维护和升级

---

## 🔍 现状分析

### 当前架构

```
new_project/
├── src/
│   └── web/
│       └── modules/
│           ├── module00_data_management/
│           │   └── metadata_manager.py          # ✅ 写元数据
│           ├── module01_data_visualization/
│           │   ├── service.py                   # 使用MetadataReader
│           │   └── metadata_reader.py           # ⚠️ Module01专用
│           ├── module02_data_import/            # ⏳ 未来需要读取元数据
│           ├── module03_rqa_analysis/           # ⏳ 未来需要读取元数据
│           └── ...
```

### MetadataReader当前位置
**路径**: `src/web/modules/module01_data_visualization/metadata_reader.py`

**职责**:
- 读取`subject_metadata.json`（受试者元数据）
- 读取`mmse_scores.json`（MMSE评分）
- 提供查询接口（按组别、版本、任务等）
- 计算统计信息（组别人数、v1/v2分布）

**代码行数**: 217行

---

## ❓ 问题与动机

### 问题1：代码重复风险

**场景**：Module03需要RQA分析，需要读取元数据筛选受试者

**当前方案**：复制Module01的`metadata_reader.py`
```python
# module03_rqa_analysis/metadata_reader.py
# 与module01完全相同的代码 ⚠️
```

**问题**：10个模块 = 10份相同代码

---

### 问题2：维护困难

**场景**：元数据格式升级，添加新字段`roi_layout_version`

**当前方案**：需要修改所有模块的`metadata_reader.py`
```python
# 需要修改10个文件 ⚠️
module01_data_visualization/metadata_reader.py
module02_data_import/metadata_reader.py
module03_rqa_analysis/metadata_reader.py
...
```

---

### 问题3：一致性风险

**场景**：不同开发者维护不同模块

**问题**：
- Module01的MetadataReader支持缓存
- Module03的MetadataReader不支持缓存
- Module05的MetadataReader有bug
- 行为不一致，难以调试

---

## 🛠️ 解决方案设计

### 方案A：提升为核心工具类（推荐）

**新架构**:
```
new_project/
├── src/
│   ├── core/                                    # 核心工具包
│   │   ├── data_loader.py                      # ✅ 已存在
│   │   ├── file_utils.py                       # ✅ 已存在
│   │   ├── validators.py                       # ✅ 已存在
│   │   └── metadata_reader.py                  # ⭐ 新增：共享元数据读取器
│   └── web/
│       └── modules/
│           ├── module00_data_management/
│           │   └── metadata_manager.py         # ✅ 写元数据
│           ├── module01_data_visualization/
│           │   ├── service.py                  # 使用 src.core.metadata_reader
│           │   └── metadata_reader.py          # ❌ 删除，改用共享版本
│           ├── module02_data_import/
│           │   └── service.py                  # ✅ 使用 src.core.metadata_reader
│           └── ...
```

**优势**:
- ✅ 所有模块统一导入：`from src.core.metadata_reader import MetadataReader`
- ✅ 与现有核心工具（DataLoader, FileUtils）架构一致
- ✅ 易于维护和升级
- ✅ 单元测试集中管理

**劣势**:
- ⚠️ 需要迁移Module01现有代码
- ⚠️ 需要更新Module01的import语句

---

### 方案B：保持现状（不推荐）

**架构**: 每个模块维护自己的`metadata_reader.py`

**优势**:
- ✅ 无需迁移代码
- ✅ 模块独立性强

**劣势**:
- ❌ 代码重复
- ❌ 维护困难
- ❌ 一致性风险

---

### 方案对比

| 评估项 | 方案A：共享工具类 | 方案B：保持现状 |
|--------|------------------|-----------------|
| 代码复用性 | ⭐⭐⭐⭐⭐ | ⭐ |
| 维护成本 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 一致性 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 实施成本 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 模块独立性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**推荐**: **方案A - 提升为核心工具类**

---

## 📝 实施步骤

### Phase 1: 创建共享MetadataReader（1-2小时）

#### 步骤1.1：复制现有代码到core/
```bash
# 复制文件
cp src/web/modules/module01_data_visualization/metadata_reader.py \
   src/core/metadata_reader.py
```

#### 步骤1.2：调整导入路径
```python
# src/core/metadata_reader.py
"""
共享元数据读取器
Shared Metadata Reader

供所有模块读取Module00维护的元数据文件
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MetadataReader:
    """
    共享元数据读取器

    读取Module00维护的元数据文件：
    - subject_metadata.json: 受试者元数据
    - mmse_scores.json: MMSE评分数据
    """

    def __init__(self, clinical_data_dir: Optional[str] = None):
        """
        初始化元数据读取器

        Args:
            clinical_data_dir: 临床数据目录路径
                默认: {project_root}/data/01_raw/clinical
        """
        if clinical_data_dir is None:
            # 自动检测项目根目录
            # src/core/metadata_reader.py -> ... -> new_project/
            project_root = Path(__file__).parent.parent.parent
            clinical_data_dir = project_root / "data" / "01_raw" / "clinical"

        self.clinical_data_dir = Path(clinical_data_dir)
        self.subject_metadata_file = self.clinical_data_dir / "subject_metadata.json"
        self.mmse_scores_file = self.clinical_data_dir / "mmse_scores.json"

        # 缓存数据
        self.subject_metadata = {}
        self.mmse_scores = {}

        # 加载元数据
        self._load_metadata()

        logger.info(f"MetadataReader initialized: {len(self.subject_metadata)} subjects")

    # ... 其他方法保持不变 ...
```

#### 步骤1.3：添加到`src/core/__init__.py`
```python
# src/core/__init__.py
"""
核心工具包
Core utilities
"""
from .data_loader import DataLoader
from .file_utils import FileUtils
from .validators import DataValidator
from .metadata_reader import MetadataReader  # ⭐ 新增

__all__ = [
    'DataLoader',
    'FileUtils',
    'DataValidator',
    'MetadataReader'  # ⭐ 新增
]
```

---

### Phase 2: 更新Module01使用共享版本（30分钟）

#### 步骤2.1：修改Module01的service.py
```python
# src/web/modules/module01_data_visualization/service.py

# ❌ 删除旧导入
# from .metadata_reader import MetadataReader

# ✅ 使用共享版本
from src.core.metadata_reader import MetadataReader

class DataVisualizationService:
    """数据可视化服务类"""

    def __init__(self, data_root: Optional[str] = None):
        # ... 其他代码保持不变 ...

        # MetadataReader初始化逻辑完全相同
        clinical_data_dir = self.data_root / "01_raw" / "clinical"
        self.metadata_reader = MetadataReader(clinical_data_dir=str(clinical_data_dir))
```

#### 步骤2.2：删除Module01的metadata_reader.py
```bash
# 删除旧文件
rm src/web/modules/module01_data_visualization/metadata_reader.py
```

#### 步骤2.3：更新Module01的`__init__.py`
```python
# src/web/modules/module01_data_visualization/__init__.py
"""
Module 01: 数据可视化模块
"""
from .api import data_bp
from .service import DataVisualizationService

# ❌ 删除
# from .metadata_reader import MetadataReader

__all__ = [
    'data_bp',
    'DataVisualizationService'
]
```

---

### Phase 3: 测试验证（30分钟）

#### 步骤3.1：单元测试
```python
# tests/core/test_metadata_reader.py
import pytest
from src.core.metadata_reader import MetadataReader

def test_metadata_reader_init():
    """测试MetadataReader初始化"""
    reader = MetadataReader()
    assert reader.subject_metadata is not None
    assert reader.mmse_scores is not None

def test_get_group_statistics():
    """测试获取组别统计"""
    reader = MetadataReader()
    stats = reader.get_group_statistics()

    assert 'control' in stats
    assert 'mci' in stats
    assert 'ad' in stats

    # 验证统计字段
    for group, data in stats.items():
        assert 'total' in data
        assert 'v1' in data
        assert 'v2' in data
        assert 'has_mmse' in data

def test_get_subject_info():
    """测试获取受试者信息"""
    reader = MetadataReader()

    # 获取第一个受试者
    all_subjects = reader.get_all_subjects()
    if all_subjects:
        subject_id = list(all_subjects.keys())[0]
        info = reader.get_subject_info(subject_id)

        assert info is not None
        assert 'group' in info
        assert 'data_version' in info
        assert 'tasks_available' in info
```

#### 步骤3.2：集成测试
```bash
# 启动后端服务
cd new_project
python run.py

# 测试Module01 API
curl http://127.0.0.1:9090/api/data/groups
curl http://127.0.0.1:9090/api/data/subjects?group=control
```

#### 步骤3.3：前端测试
```bash
# 启动前端
cd frontend
npm run dev

# 访问 http://localhost:5173
# 测试Module01页面功能是否正常
```

---

### Phase 4: 文档更新（15分钟）

#### 步骤4.1：更新架构文档
```markdown
# docs/ARCHITECTURE_REVIEW.md

### src/core/ - 核心工具

\```
src/core/
├── __init__.py                 ✅ 已实现
├── data_loader.py             ✅ 已实现 (261行)
├── file_utils.py              ✅ 已实现 (301行)
├── validators.py              ✅ 已实现 (303行)
└── metadata_reader.py         ✅ 新增 (217行)  # ⭐ 更新
\```

**实现功能**:
- ✅ DataLoader: 统一数据加载接口
- ✅ FileUtils: 文件操作封装
- ✅ DataValidator: 多层次数据验证
- ✅ MetadataReader: 共享元数据读取器  # ⭐ 新增
```

#### 步骤4.2：添加使用指南
```markdown
# docs/METADATA_READER_USAGE.md

# MetadataReader使用指南

## 导入

\```python
from src.core.metadata_reader import MetadataReader
\```

## 基本使用

\```python
# 初始化（自动检测路径）
reader = MetadataReader()

# 自定义路径
reader = MetadataReader(clinical_data_dir="/path/to/clinical")

# 获取组别统计
stats = reader.get_group_statistics()
# {'control': {'total': 52, 'v1': 22, 'v2': 30, 'has_mmse': 20}, ...}

# 获取受试者列表
subjects = reader.get_subjects_by_group('control')

# 获取单个受试者信息
info = reader.get_subject_info('control_legacy_1')

# 重新加载元数据（当Module00更新数据后）
reader.reload()
\```
```

---

## 💻 代码示例

### 示例1：Module02使用共享MetadataReader

```python
# src/web/modules/module02_data_import/service.py
"""
Module 02: 数据导入服务
"""
from pathlib import Path
from typing import Dict, Any
from src.core.metadata_reader import MetadataReader  # ⭐ 使用共享版本

class DataImportService:
    """数据导入服务类"""

    def __init__(self):
        # 初始化元数据读取器
        self.metadata_reader = MetadataReader()

    def get_importable_subjects(self, group: str) -> Dict[str, Any]:
        """
        获取可导入的受试者列表

        Args:
            group: 组别

        Returns:
            受试者列表
        """
        # 使用共享MetadataReader获取数据
        subjects = self.metadata_reader.get_subjects_by_group(group)

        return {
            "success": True,
            "data": subjects
        }
```

### 示例2：Module03使用共享MetadataReader

```python
# src/web/modules/module03_rqa_analysis/service.py
"""
Module 03: RQA分析服务
"""
from src.core.metadata_reader import MetadataReader  # ⭐ 使用共享版本

class RQAAnalysisService:
    """RQA分析服务类"""

    def __init__(self):
        self.metadata_reader = MetadataReader()

    def get_subjects_for_analysis(self, data_version: str = 'v2') -> list:
        """
        获取用于RQA分析的受试者列表

        Args:
            data_version: 数据版本 (v1/v2)

        Returns:
            受试者列表
        """
        # 使用共享MetadataReader按版本筛选
        subjects = self.metadata_reader.get_subjects_by_version(data_version)

        # 过滤：只保留有完整q1-q5任务的受试者
        complete_subjects = [
            s for s in subjects
            if set(s.get('tasks_available', [])) >= {'q1', 'q2', 'q3', 'q4', 'q5'}
        ]

        return complete_subjects
```

---

## 📊 影响评估

### 影响范围

| 模块 | 影响程度 | 修改内容 | 工作量 |
|------|---------|---------|--------|
| src/core/ | 🟢 新增 | 添加metadata_reader.py | 30分钟 |
| module01 | 🟡 中等 | 修改import，删除旧文件 | 30分钟 |
| module02-10 | 🟢 有益 | 直接使用共享版本 | 0分钟 |
| tests/ | 🟢 新增 | 添加单元测试 | 30分钟 |
| docs/ | 🟢 更新 | 更新架构文档 | 15分钟 |

**总工作量**: 约2小时

---

### 风险评估

| 风险 | 严重程度 | 概率 | 缓解措施 |
|------|---------|------|---------|
| Module01功能异常 | 🟡 中 | 低 | 充分测试，保留回滚方案 |
| 路径解析错误 | 🟡 中 | 低 | 单元测试覆盖路径逻辑 |
| 性能下降 | 🟢 低 | 极低 | 保持缓存机制不变 |

**总体风险**: 🟢 **低风险**

---

## 🧪 测试计划

### 单元测试清单

```python
# tests/core/test_metadata_reader.py

✅ test_metadata_reader_init()              # 初始化测试
✅ test_metadata_reader_with_custom_path()  # 自定义路径测试
✅ test_get_all_subjects()                  # 获取所有受试者
✅ test_get_subjects_by_group()             # 按组别过滤
✅ test_get_subjects_by_version()           # 按版本过滤
✅ test_get_subject_info()                  # 获取单个受试者信息
✅ test_get_tasks_available()               # 获取任务列表
✅ test_has_mmse_score()                    # 检查MMSE评分
✅ test_get_mmse_score()                    # 获取MMSE评分
✅ test_get_group_statistics()              # 组别统计
✅ test_reload()                            # 重新加载元数据
```

### 集成测试清单

```bash
✅ Module01 API端点测试
   - GET /api/data/groups
   - GET /api/data/subjects?group=control
   - GET /api/data/tasks?group=control&subject_id=control_legacy_1
   - GET /api/data/raw?group=control&subject_id=control_legacy_1&task=q1

✅ 前端功能测试
   - 访问Module01页面
   - 选择组别、受试者、任务
   - 加载眼动数据并显示图表

✅ 性能测试
   - 测量MetadataReader初始化时间
   - 测量reload()执行时间
   - 对比重构前后性能
```

---

## 🔄 回滚方案

### 场景：重构后发现严重问题

**回滚步骤**:

```bash
# 1. 恢复Module01的metadata_reader.py
git checkout src/web/modules/module01_data_visualization/metadata_reader.py

# 2. 删除共享版本
rm src/core/metadata_reader.py

# 3. 恢复Module01的import语句
git checkout src/web/modules/module01_data_visualization/service.py

# 4. 恢复Module01的__init__.py
git checkout src/web/modules/module01_data_visualization/__init__.py

# 5. 重启服务测试
python run.py
```

**回滚时间**: 5分钟

---

## 💡 实施建议

### 建议1: 分阶段实施（推荐）

**阶段1**: 先创建共享版本，保留Module01原有版本
```python
# 两个版本并存，先验证共享版本可用
src/core/metadata_reader.py                      # ✅ 新增
src/web/modules/module01_data_visualization/
    metadata_reader.py                           # ✅ 保留（暂不删除）
```

**阶段2**: 充分测试后，再切换Module01使用共享版本

**阶段3**: 验证无问题后，删除Module01旧版本

---

### 建议2: 添加版本标识

```python
# src/core/metadata_reader.py

class MetadataReader:
    """
    共享元数据读取器 v2.0

    迁移自: module01_data_visualization (v1.0)
    迁移日期: 2025-10-02
    """
    VERSION = "2.0.0"
```

---

### 建议3: 保持向后兼容

```python
# src/web/modules/module01_data_visualization/__init__.py
"""
为了向后兼容，保留别名导入
"""
from src.core.metadata_reader import MetadataReader

# 向后兼容别名（可选）
__all__ = ['MetadataReader']
```

---

## 📈 预期收益

### 短期收益
- ✅ Module01代码减少217行
- ✅ 代码复用性提升
- ✅ 维护成本降低

### 长期收益
- ✅ Module02-10直接复用，节省开发时间
- ✅ 元数据格式升级只需修改一处
- ✅ 统一行为，降低bug风险
- ✅ 单元测试集中管理，提升代码质量

---

## ✅ 实施决策

### 推荐方案
**✅ 实施方案A - 提升为核心工具类**

### 实施时机
- **立即实施**: 如果近期要开发Module02-10
- **延后实施**: 如果短期内只维护Module01

### 实施优先级
**🟡 中等（可选优化）**

理由：
- 当前Module01功能正常，无紧急问题
- 但后续模块开发会受益于共享版本
- 建议在开发Module02前实施

---

## 📞 联系与反馈

**文档维护者**: AI Assistant
**创建日期**: 2025-10-02
**下次审查**: Module02开发前

---

**附录**: 完整实施Checklist（见下页）

---

## 📋 实施Checklist

### Phase 1: 创建共享版本
- [ ] 复制`metadata_reader.py`到`src/core/`
- [ ] 调整导入路径（Path计算）
- [ ] 添加到`src/core/__init__.py`
- [ ] 添加版本标识和文档字符串

### Phase 2: 更新Module01
- [ ] 修改`service.py`的import语句
- [ ] 删除`metadata_reader.py`（或暂时保留）
- [ ] 更新`__init__.py`

### Phase 3: 测试
- [ ] 编写单元测试
- [ ] 运行集成测试
- [ ] 前端功能测试
- [ ] 性能对比测试

### Phase 4: 文档
- [ ] 更新架构文档
- [ ] 编写使用指南
- [ ] 更新README

### Phase 5: 部署
- [ ] Git提交
- [ ] 代码审查
- [ ] 合并到主分支
- [ ] 通知团队

---

**文档结束**
