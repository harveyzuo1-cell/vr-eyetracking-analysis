# 任务扩展性开发文档总览
# Task Extension Development Documentation Overview

**项目**: VR眼球追踪数据分析平台 - 任务扩展性改进
**版本**: 1.0.0
**创建时间**: 2025-10-03

---

## 📚 文档导航

### 核心设计文档

1. **[TASK_EXTENSION_DESIGN.md](./TASK_EXTENSION_DESIGN.md)** ⭐
   - **内容**: 任务扩展性整体设计方案
   - **关键内容**:
     - 问题分析 (12处硬编码位置)
     - TaskConfigService架构设计
     - 配置文件格式 (task_configs.json)
     - 三阶段实施计划
     - 示例场景 (Q1-Q8, 自定义实验)
   - **适用对象**: 架构师、项目经理、技术负责人

2. **[PHASE2_MIGRATION_DESIGN.md](./PHASE2_MIGRATION_DESIGN.md)** ⭐
   - **内容**: 阶段2模块迁移详细设计
   - **关键内容**:
     - Module00/01/EX现状分析
     - 4个子阶段迁移计划
     - 详细代码修改示例
     - 测试计划和验收标准
   - **适用对象**: 开发人员、测试人员

3. **[PYTEST_INTEGRATION_GUIDE.md](./PYTEST_INTEGRATION_GUIDE.md)**
   - **内容**: Pytest测试框架集成指南
   - **关键内容**:
     - Pytest配置
     - Fixtures设计
     - 测试编写规范
     - CI/CD集成
   - **适用对象**: 测试工程师、质量保证团队

---

## 🎯 快速开始

### 开发人员快速上手

1. **了解整体设计**
   ```bash
   # 阅读总体设计文档
   cat docs/TASK_EXTENSION_DESIGN.md
   ```

2. **查看已完成的阶段1**
   ```bash
   # TaskConfigService已实现
   ls src/services/task_config_service.py
   ls config/task_configs.json

   # API已就绪
   curl http://localhost:9090/api/task-config/health
   ```

3. **准备开发阶段2**
   ```bash
   # 阅读迁移设计文档
   cat docs/PHASE2_MIGRATION_DESIGN.md

   # 安装测试依赖
   pip install -r requirements-test.txt

   # 运行现有测试
   pytest tests/ -v
   ```

### 测试人员快速上手

1. **安装pytest环境**
   ```bash
   pip install -r requirements-test.txt
   ```

2. **运行测试**
   ```bash
   # 运行所有测试
   pytest

   # 运行单元测试
   pytest -m unit

   # 运行特定模块测试
   pytest -m task_config

   # 生成覆盖率报告
   pytest --cov=src --cov-report=html
   ```

3. **查看测试报告**
   ```bash
   # HTML覆盖率报告
   open htmlcov/index.html
   ```

---

## 📂 项目结构

### 新增文件清单

```
new_project/
├── config/
│   └── task_configs.json                    # ✅ 任务配置中心
│
├── src/services/
│   └── task_config_service.py               # ✅ TaskConfigService核心服务
│
├── src/web/modules/moduleEX_roi_config/
│   └── task_config_api.py                   # ✅ 任务配置API
│
├── frontend/src/services/
│   └── taskConfigService.js                 # ✅ 前端API客户端
│
├── tests/
│   ├── conftest.py                          # ✅ Pytest全局配置
│   └── test_task_config_service.py          # ✅ TaskConfigService测试
│
├── docs/
│   ├── TASK_EXTENSION_DESIGN.md             # ✅ 总体设计文档
│   ├── PHASE2_MIGRATION_DESIGN.md           # ✅ 阶段2迁移文档
│   ├── PYTEST_INTEGRATION_GUIDE.md          # ✅ Pytest集成指南
│   └── TASK_EXTENSION_README.md             # ✅ 本文档
│
├── pytest.ini                                # ✅ Pytest配置文件
└── requirements-test.txt                     # ✅ 测试依赖
```

---

## 🚀 开发进度

### 阶段1: 任务配置服务基础设施 ✅ 已完成

**时间**: Week 1 (2025-10-03)
**状态**: ✅ 100%完成

| 任务 | 状态 | 文件 |
|------|------|------|
| 创建配置文件 | ✅ | config/task_configs.json |
| 实现TaskConfigService | ✅ | src/services/task_config_service.py (486行) |
| 实现后端API | ✅ | task_config_api.py (379行) |
| 创建前端服务 | ✅ | taskConfigService.js (166行) |
| 编写单元测试 | ✅ | test_task_config_service.py (385行) |
| 配置pytest | ✅ | pytest.ini, conftest.py |

**功能验证**:
```bash
✅ GET /api/task-config/datasets      → 2个数据集
✅ GET /api/task-config/tasks         → 5个任务
✅ POST /api/task-config/infer-dataset → 自动推断
```

### 阶段2: 模块迁移 ⏳ 设计完成,等待实施

**时间**: Week 2-5
**状态**: 📝 设计文档已完成

| 子阶段 | 模块 | 时间 | 状态 |
|--------|------|------|------|
| 2.1 | UnifiedROIService | Week 2 | 📝 待实施 |
| 2.2 | Module00 | Week 3 | 📝 待实施 |
| 2.3 | Module01 | Week 4 | 📝 待实施 |
| 2.4 | ModuleEX | Week 5 | 📝 待实施 |

---

## 📖 关键概念

### TaskConfigService

**作用**: 中心化任务配置管理服务

**核心方法**:
```python
get_tasks(dataset_id)              # 获取任务列表
get_task_by_id(dataset_id, task_id)  # 查询任务
normalize_task_id(dataset_id, task_id)  # 标准化ID
infer_dataset_from_data(tasks)     # 自动推断数据集
register_dataset(config)            # 动态注册数据集
```

### 配置文件结构

**路径**: `config/task_configs.json`

**结构**:
```json
{
  "datasets": {
    "mmse_v1": {
      "tasks": [
        {
          "id": "q1",
          "alt_ids": ["task1", "Q1"],
          "name": "时间定向",
          "order": 1,
          "required": true
        }
      ]
    }
  }
}
```

### 数据集推断算法

```python
# 输入: ["q1", "q2", "q3", "q4", "q5"]
# 输出: ("mmse_v1", 1.0)  # 100%匹配

# 输入: ["q1", "q2", "q6", "q7", "q8"]
# 输出: ("mmse_extended", 0.6)  # 60%匹配
```

---

## 🧪 测试策略

### 测试金字塔

```
        /\          端到端测试 (50%覆盖)
       /  \
      /    \        集成测试 (60%覆盖)
     /______\
    /        \      单元测试 (80%覆盖)
   /__________\
```

### 测试标记系统

```bash
pytest -m unit          # 单元测试
pytest -m integration   # 集成测试
pytest -m task_config   # TaskConfig相关
pytest -m module00      # Module00相关
pytest -m slow          # 慢速测试
```

### 覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| TaskConfigService | 90%+ | ✅ 已达标 |
| UnifiedROIService | 85%+ | ⏳ 待迁移 |
| Module00 | 80%+ | ⏳ 待迁移 |
| Module01 | 75%+ | ⏳ 待迁移 |

---

## 🔧 开发工具

### Pytest命令速查

```bash
# 基础测试
pytest                              # 运行所有测试
pytest tests/test_file.py          # 运行单个文件
pytest tests/test_file.py::test_func  # 运行单个测试

# 标记过滤
pytest -m unit                     # 只运行单元测试
pytest -m "not slow"               # 排除慢速测试

# 输出控制
pytest -v                          # 详细输出
pytest -s                          # 显示print输出
pytest --lf                        # 只运行上次失败的测试

# 覆盖率
pytest --cov=src                   # 覆盖率报告
pytest --cov-report=html           # HTML报告

# 并行测试
pytest -n 4                        # 4个进程并行
```

### 调试技巧

```bash
# 进入pdb调试
pytest --pdb

# 在第一个失败时停止
pytest -x

# 显示最慢的10个测试
pytest --durations=10
```

---

## 📝 开发规范

### 代码审查检查点

**阶段2迁移代码审查清单**:

- [ ] 移除了硬编码的TASK_ID_MAPPING
- [ ] 使用TaskConfigService.get_task_by_id()
- [ ] 添加dataset_id参数(默认"mmse_v1")
- [ ] 向后兼容Q1-Q5数据
- [ ] 编写了单元测试(覆盖率>80%)
- [ ] 更新了API文档
- [ ] 通过了回归测试

### 测试编写规范

```python
# ✅ 好的测试
def test_normalize_task_id_with_alt_id(task_service):
    """测试使用备用ID标准化任务ID"""
    result = task_service.normalize_task_id("mmse_v1", "task1")
    assert result == "q1"

# ❌ 不好的测试
def test_something():
    # 没有文档字符串
    # 没有使用fixture
    # 断言不明确
    assert True
```

---

## 🎓 学习资源

### 内部文档

- [Backend Coding Standards](./BACKEND_CODING_STANDARDS.md)
- [Frontend Coding Standards](./FRONTEND_CODING_STANDARDS.md)
- [Architecture Review](./ARCHITECTURE_REVIEW.md)

### Pytest学习

- [Pytest官方文档](https://docs.pytest.org/)
- [Pytest Fixtures指南](https://docs.pytest.org/en/latest/fixture.html)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)

---

## 🐛 常见问题

### Q: 如何添加新的数据集配置?

**A**: 编辑`config/task_configs.json`,添加新数据集:

```json
{
  "datasets": {
    "my_experiment": {
      "id": "my_experiment",
      "name": "我的实验",
      "data_version": "custom",
      "tasks": [...]
    }
  }
}
```

### Q: 如何运行特定模块的测试?

**A**: 使用pytest标记:

```bash
pytest -m task_config  # TaskConfig相关测试
pytest -m module00     # Module00相关测试
```

### Q: 测试覆盖率不达标怎么办?

**A**: 查看HTML报告,补充缺失的测试:

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 📧 联系方式

**技术负责人**: VR Eye Tracking Team
**文档维护**: 项目架构组
**更新频率**: 随项目进展持续更新

---

**最后更新**: 2025-10-03
**文档版本**: 1.0.0
**状态**: ✅ 阶段1完成, 阶段2设计就绪
