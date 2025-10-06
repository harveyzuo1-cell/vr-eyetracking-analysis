"""
全局配置文件

定义项目的所有配置参数
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class Config:
    """基础配置类"""

    # ==================== 项目信息 ====================
    PROJECT_NAME = "VR Eye-Tracking Analysis Platform"
    VERSION = "2.0.0"

    # ==================== 目录配置 ====================
    # 数据目录
    DATA_ROOT = PROJECT_ROOT / "data"
    RAW_DATA_DIR = DATA_ROOT / "01_raw"
    PREPROCESSED_DATA_DIR = DATA_ROOT / "02_preprocessed"
    CALIBRATED_DATA_DIR = DATA_ROOT / "03_calibrated"
    FEATURES_DIR = DATA_ROOT / "04_features"
    MODELS_DIR = DATA_ROOT / "05_models"
    RESULTS_DIR = DATA_ROOT / "06_results"

    # 原始数据子目录
    RAW_CONTROL_DIR = RAW_DATA_DIR / "control"
    RAW_MCI_DIR = RAW_DATA_DIR / "mci"
    RAW_AD_DIR = RAW_DATA_DIR / "ad"
    RAW_CLINICAL_DIR = RAW_DATA_DIR / "clinical"

    # 特征子目录
    RQA_FEATURES_DIR = FEATURES_DIR / "rqa"
    EVENT_FEATURES_DIR = FEATURES_DIR / "events"
    COMPREHENSIVE_FEATURES_DIR = FEATURES_DIR / "comprehensive"

    # 模型子目录
    MODEL_CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
    MODEL_PRODUCTION_DIR = MODELS_DIR / "production"

    # 结果子目录
    VISUALIZATIONS_DIR = RESULTS_DIR / "visualizations"
    REPORTS_DIR = RESULTS_DIR / "reports"
    EXPORTS_DIR = RESULTS_DIR / "exports"

    # 临时目录
    TEMP_DIR = PROJECT_ROOT / "temp"
    UPLOAD_DIR = TEMP_DIR / "uploads"
    CACHE_DIR = TEMP_DIR / "cache"

    # ==================== 服务器配置 ====================
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 9090))  # 使用9090端口避免与旧项目冲突
    DEBUG = False
    TESTING = False

    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

    # ==================== 数据处理配置 ====================
    # 文件命名格式
    DATA_FILENAME_FORMAT = "{group}_{subject_id}_{task_id}.csv"
    PROCESSED_FILENAME_FORMAT = "{group}_{subject_id}_{task_id}_{stage}.csv"

    # 支持的组别
    VALID_GROUPS = ['control', 'mci', 'ad']

    # 支持的任务
    VALID_TASKS = ['q1', 'q2', 'q3', 'q4', 'q5']

    # CSV列名映射（支持旧格式兼容）
    COLUMN_MAPPING = {
        'GazePointX_normalized': 'x',
        'GazePointY_normalized': 'y',
        'milliseconds': 'time'
    }

    # 必需的列
    REQUIRED_COLUMNS = ['x', 'y', 'time']

    # ==================== RQA分析配置 ====================
    # RQA参数默认值
    RQA_DEFAULT_PARAMS = {
        'm': 2,           # 嵌入维度
        'tau': 1,         # 时间延迟
        'eps': 0.05,      # 距离阈值
        'lmin': 2         # 最小线长
    }

    # RQA参数范围
    RQA_PARAM_RANGES = {
        'm': {'min': 1, 'max': 10, 'default': 2},
        'tau': {'min': 1, 'max': 20, 'default': 1},
        'eps': {'min': 0.01, 'max': 1.0, 'default': 0.05},
        'lmin': {'min': 2, 'max': 10, 'default': 2}
    }

    # ==================== GPU配置 ====================
    USE_GPU = True
    GPU_BATCH_SIZE = 16
    GPU_MEMORY_FRACTION = 0.8

    # ==================== 事件检测配置 ====================
    # IVT算法参数
    IVT_VELOCITY_THRESHOLD = 40.0  # 度/秒

    # ROI定义
    ROI_DEFINITIONS = {
        'q1': {'x': 0.2, 'y': 0.3, 'width': 0.6, 'height': 0.4},
        'q2': {'x': 0.1, 'y': 0.2, 'width': 0.8, 'height': 0.6},
        'q3': {'x': 0.15, 'y': 0.25, 'width': 0.7, 'height': 0.5},
        'q4': {'x': 0.2, 'y': 0.2, 'width': 0.6, 'height': 0.6},
        'q5': {'x': 0.1, 'y': 0.15, 'width': 0.8, 'height': 0.7}
    }

    # ==================== 机器学习配置 ====================
    # 模型参数
    ML_RANDOM_SEED = 42
    ML_TEST_SIZE = 0.2
    ML_VALIDATION_SIZE = 0.1

    # MLP模型配置
    MLP_HIDDEN_LAYERS = [128, 64, 32]
    MLP_DROPOUT_RATE = 0.3
    MLP_LEARNING_RATE = 0.001
    MLP_EPOCHS = 100
    MLP_BATCH_SIZE = 32

    # ==================== 日志配置 ====================
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = PROJECT_ROOT / 'logs' / 'app.log'

    # ==================== 性能配置 ====================
    # 缓存配置
    ENABLE_CACHE = True
    CACHE_TIMEOUT = 3600  # 1小时

    # 并发配置
    MAX_WORKERS = 4

    @classmethod
    def init_directories(cls):
        """初始化所有必需的目录"""
        directories = [
            cls.DATA_ROOT,
            cls.RAW_DATA_DIR,
            cls.RAW_CONTROL_DIR,
            cls.RAW_MCI_DIR,
            cls.RAW_AD_DIR,
            cls.RAW_CLINICAL_DIR,
            cls.PREPROCESSED_DATA_DIR,
            cls.CALIBRATED_DATA_DIR,
            cls.FEATURES_DIR,
            cls.RQA_FEATURES_DIR,
            cls.EVENT_FEATURES_DIR,
            cls.COMPREHENSIVE_FEATURES_DIR,
            cls.MODELS_DIR,
            cls.MODEL_CHECKPOINTS_DIR,
            cls.MODEL_PRODUCTION_DIR,
            cls.RESULTS_DIR,
            cls.VISUALIZATIONS_DIR,
            cls.REPORTS_DIR,
            cls.EXPORTS_DIR,
            cls.TEMP_DIR,
            cls.UPLOAD_DIR,
            cls.CACHE_DIR,
            cls.LOG_FILE.parent
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_data_path(cls, group: str, subject_id: str, task_id: str, stage: str = 'raw') -> Path:
        """
        获取数据文件路径

        Args:
            group: 组别 (control/mci/ad)
            subject_id: 受试者ID (如 s001)
            task_id: 任务ID (如 q1)
            stage: 数据阶段 (raw/preprocessed/calibrated)

        Returns:
            Path: 数据文件路径
        """
        if group not in cls.VALID_GROUPS:
            raise ValueError(f"Invalid group: {group}. Must be one of {cls.VALID_GROUPS}")

        if task_id not in cls.VALID_TASKS:
            raise ValueError(f"Invalid task: {task_id}. Must be one of {cls.VALID_TASKS}")

        # 确定目录
        if stage == 'raw':
            base_dir = cls.RAW_DATA_DIR / group
        elif stage == 'preprocessed':
            base_dir = cls.PREPROCESSED_DATA_DIR / group
        elif stage == 'calibrated':
            base_dir = cls.CALIBRATED_DATA_DIR / group
        else:
            raise ValueError(f"Invalid stage: {stage}")

        # 生成文件名
        if stage == 'raw':
            filename = f"{group}_{subject_id}_{task_id}.csv"
        else:
            filename = f"{group}_{subject_id}_{task_id}_{stage}.csv"

        return base_dir / filename


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


# 根据环境变量选择配置
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """
    获取配置对象

    Args:
        env: 环境名称 (development/production/testing)

    Returns:
        Config: 配置对象
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')

    return config_map.get(env, config_map['default'])
