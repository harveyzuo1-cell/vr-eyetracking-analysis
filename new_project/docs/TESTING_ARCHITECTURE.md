# 测试架构文档

## 📋 概述

本文档描述VR眼球追踪数据分析平台的测试架构、策略和最佳实践。

**更新时间**: 2025-10-03
**测试框架**: pytest 7.4.3
**当前覆盖率**: 32% (核心服务 91%)

---

## 🏗️ 测试框架架构

### 技术栈

```yaml
核心框架:
  - pytest: 7.4.3              # 测试运行器
  - pytest-cov: 4.1.0          # 覆盖率分析
  - coverage: 7.3.4            # 覆盖率工具

Flask集成:
  - pytest-flask: 1.3.0        # Flask测试支持

测试辅助:
  - pytest-mock: 3.12.0        # Mock支持
  - pytest-xdist: 3.5.0        # 并行测试
  - pytest-timeout: 2.2.0      # 超时控制
  - faker: 20.1.0              # 测试数据生成
  - freezegun: 1.4.0           # 时间mock
  - responses: 0.24.1          # HTTP mock

报告工具:
  - pytest-html: 4.1.1         # HTML报告
  - pytest-json-report: 1.5.0  # JSON报告

代码质量:
  - pytest-flake8: 1.1.1       # 代码风格检查
  - pytest-pylint: 0.21.0      # 代码质量检查
```

### 目录结构

```
new_project/
├── tests/                           # 测试根目录
│   ├── conftest.py                  # 全局fixtures
│   ├── test_task_config_service.py  # 任务配置服务测试
│   ├── test_roi_analyzer.py         # ROI分析器测试
│   └── __init__.py
│
├── pytest.ini                       # pytest配置文件
├── requirements-test.txt            # 测试依赖
└── .coverage                        # 覆盖率数据
```

---

## ⚙️ pytest配置

### pytest.ini

```ini
[pytest]
# 测试发现路径
testpaths = tests

# 命令行选项
addopts =
    -v                              # 详细输出
    --cov=src                       # 覆盖率目标
    --cov-report=html               # HTML报告
    --cov-report=term-missing       # 终端缺失行报告
    --strict-markers                # 严格标记模式
    --tb=short                      # 简短traceback

# 测试标记
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试 (>1s)
    api: API层测试
    service: 服务层测试
    module00: Module00相关测试
    module01: Module01相关测试
    moduleex: ModuleEX相关测试
    task_config: TaskConfigService测试
    roi: ROI相关测试

# Python路径
pythonpath = .

# 日志配置
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S
```

---

## 🧪 全局Fixtures

### conftest.py

```python
import pytest
import tempfile
import json
from pathlib import Path

@pytest.fixture(scope="session")
def temp_config_dir():
    """创建临时配置目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def task_config_file(temp_config_dir):
    """创建测试用task_configs.json"""
    config_file = temp_config_dir / "task_configs.json"
    default_config = {
        "version": "1.0.0",
        "datasets": {
            "mmse_v1": {
                "id": "mmse_v1",
                "name": "MMSE标准版v1",
                "data_version": "v1",
                "tasks": [
                    {
                        "id": "q1",
                        "alt_ids": ["task1", "Q1"],
                        "name": "时间定向",
                        "order": 1,
                        "required": True
                    },
                    # ... 其他任务
                ]
            }
        }
    }
    config_file.write_text(json.dumps(default_config, indent=2))
    return config_file

@pytest.fixture
def task_service(task_config_file):
    """TaskConfigService测试实例"""
    from src.services.task_config_service import TaskConfigService
    return TaskConfigService(config_file=task_config_file)

@pytest.fixture(scope="session")
def app():
    """Flask应用实例 (测试模式)"""
    from src.web.app import create_app
    app = create_app(env='testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Flask测试客户端"""
    return app.test_client()

@pytest.fixture
def sample_gaze_data():
    """示例眼动数据"""
    return {
        'x': [0.1, 0.2, 0.3, 0.4, 0.5],
        'y': [0.1, 0.2, 0.3, 0.4, 0.5],
        'timestamp': [0, 100, 200, 300, 400]
    }

@pytest.fixture
def sample_roi_config():
    """示例ROI配置"""
    return {
        "version": "v2",
        "task_id": "q1",
        "regions": {
            "keywords": [
                {
                    "id": "KW_1",
                    "normalized_coords": [0.1, 0.1, 0.2, 0.2],
                    "color": "#1890ff"
                }
            ]
        }
    }
```

---

## 📊 测试策略

### 1. 测试分层

```
┌─────────────────────────────────────┐
│      E2E测试 (未实现)               │
│  完整业务流程的端到端测试            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      集成测试                        │
│  多个模块协作的测试                  │
│  - test_v1_and_v2_compatibility     │
│  - test_multi_dataset_coexistence   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      单元测试 (主要)                 │
│  独立模块/函数的测试                 │
│  - TestTaskConfigService (22个)     │
│  - TestROIAnalyzer (17个)           │
└─────────────────────────────────────┘
```

### 2. 测试覆盖目标

| 层级 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| 核心服务 (services/) | 90%+ | **91%** ✅ |
| 业务逻辑 (modules/) | 70%+ | 14-20% ⏳ |
| 工具函数 (utils/) | 80%+ | 22-80% ⏳ |
| API层 (web/) | 70%+ | 0-20% ⏳ |
| 整体项目 | 70%+ | 32% ⏳ |

### 3. 测试标记使用

```bash
# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行特定模块测试
pytest -m task_config

# 排除慢速测试
pytest -m "not slow"

# 组合标记
pytest -m "unit and task_config"
```

---

## 🔧 测试最佳实践

### 1. 测试命名约定

```python
# 测试类命名: Test + 被测类名
class TestTaskConfigService:
    pass

class TestROIAnalyzer:
    pass

# 测试方法命名: test_ + 功能描述
def test_get_tasks_returns_sorted_by_order():
    pass

def test_normalize_task_id_with_alt_ids():
    pass

def test_infer_dataset_perfect_match():
    pass
```

### 2. AAA模式 (Arrange-Act-Assert)

```python
def test_get_task_by_id_main_id(task_service):
    # Arrange (准备)
    dataset_id = "mmse_v1"
    task_id = "q1"

    # Act (执行)
    task = task_service.get_task_by_id(dataset_id, task_id)

    # Assert (断言)
    assert task is not None
    assert task['id'] == "q1"
    assert task['name'] == "时间定向"
```

### 3. Fixture使用原则

```python
# ✅ 好的实践: 使用fixture共享测试数据
def test_something(task_service, sample_roi_config):
    result = task_service.process(sample_roi_config)
    assert result is not None

# ❌ 避免: 在测试中重复创建数据
def test_something_bad():
    service = TaskConfigService()  # 重复
    config = {...}  # 重复
    result = service.process(config)
```

### 4. Mock使用指南

```python
# 使用pytest-mock进行mock
def test_api_call(mocker):
    # Mock外部API调用
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"status": "ok"}

    mocker.patch('requests.get', return_value=mock_response)

    result = call_external_api()
    assert result['status'] == "ok"
```

---

## 📈 覆盖率报告

### 生成覆盖率报告

```bash
# HTML报告 (推荐)
pytest --cov=src --cov-report=html
# 输出: htmlcov/index.html

# 终端报告
pytest --cov=src --cov-report=term-missing

# XML报告 (CI/CD用)
pytest --cov=src --cov-report=xml

# 多种报告同时生成
pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term
```

### 当前覆盖率详情

```
Name                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
src/services/task_config_service.py     130     12    91%   50-55, 257...
src/modules/.../roi_analyzer.py         110     24    78%   60-66, 86-91...
src/services/roi_service.py             152    131    14%   29-39, 55-82...
-------------------------------------------------------------------
TOTAL                                  1711   1160    32%
```

---

## 🚀 运行测试

### 基本命令

```bash
# 运行所有测试
pytest

# 详细输出
pytest -v

# 显示print输出
pytest -s

# 运行特定文件
pytest tests/test_task_config_service.py

# 运行特定测试
pytest tests/test_task_config_service.py::TestTaskConfigService::test_get_tasks

# 失败时立即停止
pytest -x

# 重新运行失败的测试
pytest --lf
```

### 高级命令

```bash
# 并行运行 (使用4个进程)
pytest -n 4

# 设置超时
pytest --timeout=300

# 生成HTML报告
pytest --html=report.html --self-contained-html

# 生成JSON报告
pytest --json-report --json-report-file=report.json

# 代码质量检查
pytest --flake8
pytest --pylint
```

### CI/CD命令

```bash
# 完整测试流程
pytest \
  --cov=src \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-fail-under=70 \
  --html=test-report.html \
  --json-report \
  --json-report-file=test-results.json
```

---

## 📝 编写新测试

### 1. 单元测试示例

```python
# tests/test_new_feature.py
import pytest
from src.services.new_service import NewService

class TestNewService:
    """NewService单元测试"""

    @pytest.fixture
    def service(self):
        """服务实例fixture"""
        return NewService()

    def test_basic_functionality(self, service):
        """测试基本功能"""
        result = service.do_something("input")
        assert result == "expected"

    def test_error_handling(self, service):
        """测试错误处理"""
        with pytest.raises(ValueError):
            service.do_something(None)

    @pytest.mark.parametrize("input,expected", [
        ("a", 1),
        ("b", 2),
        ("c", 3),
    ])
    def test_multiple_cases(self, service, input, expected):
        """参数化测试"""
        assert service.process(input) == expected
```

### 2. 集成测试示例

```python
# tests/test_integration.py
import pytest

@pytest.mark.integration
class TestModuleIntegration:
    """模块集成测试"""

    def test_module_interaction(self, task_service, roi_service):
        """测试模块间交互"""
        # 从TaskConfigService获取任务
        tasks = task_service.get_tasks("mmse_v1")

        # 使用ROIService加载配置
        for task in tasks:
            roi_config = roi_service.load_config("v1", task['id'])
            assert roi_config is not None
```

---

## 🔍 调试测试

### 使用pdb调试

```python
def test_debug_example():
    result = complex_function()

    # 设置断点
    import pdb; pdb.set_trace()

    assert result == expected
```

### pytest调试选项

```bash
# 在第一个失败处启动pdb
pytest --pdb

# 在每个测试前启动pdb
pytest --trace

# 显示locals变量
pytest -l

# 完整的traceback
pytest --tb=long
```

---

## 📋 测试清单

### 新功能测试清单

- [ ] 单元测试覆盖核心逻辑
- [ ] 边界条件测试
- [ ] 错误处理测试
- [ ] 参数化测试 (多种输入)
- [ ] Mock外部依赖
- [ ] 集成测试 (如需要)
- [ ] 性能测试 (如需要)
- [ ] 文档字符串说明测试目的
- [ ] 覆盖率 > 90%

### 代码审查清单

- [ ] 测试命名清晰描述功能
- [ ] 遵循AAA模式
- [ ] 适当使用fixtures
- [ ] 避免测试间依赖
- [ ] 测试独立且可重复
- [ ] Mock使用合理
- [ ] 断言明确具体

---

## 🎯 覆盖率提升计划

### 短期目标 (1-2周)

1. **ROI Service**: 14% → 70%+
   - 添加normalize_task_id测试
   - 添加get_roi_config_path测试
   - 添加load_roi_config测试

2. **Module00 API**: 0% → 60%+
   - 添加数据导入API测试
   - 添加验证逻辑测试

3. **Module01 Service**: 14% → 70%+
   - 添加数据加载测试
   - 添加ROI分析测试

### 中期目标 (1个月)

4. **整体覆盖率**: 32% → 70%+
   - Web API层测试
   - 数据处理流程测试
   - 错误处理测试

5. **E2E测试**: 新增
   - 完整数据导入流程
   - 完整分析流程
   - 用户操作流程

---

## 📚 相关文档

- [PYTEST_INTEGRATION_GUIDE.md](./PYTEST_INTEGRATION_GUIDE.md) - pytest快速指南
- [BACKEND_CODING_STANDARDS.md](./BACKEND_CODING_STANDARDS.md) - 后端编码规范
- [PHASE2_MIGRATION_COMPLETE.md](./PHASE2_MIGRATION_COMPLETE.md) - Phase 2完成报告

---

## 🔗 参考资源

- [pytest官方文档](https://docs.pytest.org/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [Python测试最佳实践](https://docs.python-guide.org/writing/tests/)
- [Flask测试指南](https://flask.palletsprojects.com/en/2.3.x/testing/)

---

**最后更新**: 2025-10-03
**维护者**: 开发团队
