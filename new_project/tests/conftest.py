"""
Pytest全局配置和Fixtures
Pytest Global Configuration and Fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import json

# 将项目根目录添加到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ==================== 全局Fixtures ====================

@pytest.fixture(scope="session")
def project_root():
    """项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir():
    """临时目录 (每个测试独立)"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="session")
def temp_dir_session():
    """临时目录 (整个测试会话共享)"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


# ==================== TaskConfigService Fixtures ====================

@pytest.fixture
def task_config_file(temp_dir):
    """临时任务配置文件"""
    config_file = temp_dir / "task_configs.json"
    config_data = {
        "version": "1.0.0",
        "datasets": {
            "test_dataset": {
                "id": "test_dataset",
                "name": "测试数据集",
                "data_version": "test",
                "tasks": [
                    {
                        "id": "t1",
                        "alt_ids": ["task1"],
                        "name": "测试任务1",
                        "order": 1,
                        "required": True
                    },
                    {
                        "id": "t2",
                        "alt_ids": ["task2"],
                        "name": "测试任务2",
                        "order": 2,
                        "required": False
                    }
                ]
            }
        }
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)

    return config_file


@pytest.fixture
def task_service(task_config_file):
    """TaskConfigService测试实例"""
    from src.services.task_config_service import TaskConfigService
    return TaskConfigService(config_file=task_config_file)


# ==================== Flask App Fixtures ====================

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
def runner(app):
    """Flask CLI runner"""
    return app.test_cli_runner()


# ==================== 数据Fixtures ====================

@pytest.fixture
def sample_gaze_data():
    """示例眼动数据"""
    return [
        {"x": 0.1, "y": 0.2, "timestamp": 0.0},
        {"x": 0.15, "y": 0.25, "timestamp": 0.1},
        {"x": 0.2, "y": 0.3, "timestamp": 0.2},
    ]


@pytest.fixture
def sample_roi_config():
    """示例ROI配置"""
    return {
        "version": "v1",
        "task_id": "q1",
        "regions": {
            "keywords": [
                {
                    "id": "KW_q1_1",
                    "normalized_coords": [0.1, 0.2, 0.3, 0.2],
                    "color": "#1890ff"
                }
            ],
            "instructions": [],
            "background": [
                {
                    "id": "BG_q1",
                    "normalized_coords": [0, 0, 1, 1],
                    "color": "#faad14"
                }
            ]
        }
    }


# ==================== Pytest Hooks ====================

def pytest_configure(config):
    """Pytest配置钩子"""
    # 添加自定义标记说明
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为所有test_开头的函数自动添加unit标记
    for item in items:
        if "integration" not in item.keywords and "slow" not in item.keywords:
            item.add_marker(pytest.mark.unit)
