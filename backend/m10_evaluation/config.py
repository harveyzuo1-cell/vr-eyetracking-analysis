"""
模块10-D配置管理
"""
import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 模型和数据路径配置
MODELS_ROOT = PROJECT_ROOT / "models"
DATA_ROOT = PROJECT_ROOT / "data" / "module10_datasets"
LOGS_ROOT = PROJECT_ROOT / "runs"

# 性能评估配置
EVALUATION_CONFIG = {
    "tasks": ["Q1", "Q2", "Q3", "Q4", "Q5"],
    "model_cache_size": 10,  # 最多缓存10组模型
    "batch_size": 32,
    "device": "cuda",  # 自动检测
    "group_mapping": {
        # 默认按样本索引划分组别
        "control": (0, 20),  # 样本0-19
        "mci": (20, 40),     # 样本20-39  
        "ad": (40, 60)       # 样本40-59
    }
}

# API配置
API_CONFIG = {
    "max_samples_display": 1000,  # 最多显示的样本数
    "cache_ttl": 300,  # 缓存时间（秒）
    "export_formats": ["csv", "json", "png"]
}

def get_model_path(rqa_sig: str, task: str) -> Path:
    """获取模型文件路径"""
    return MODELS_ROOT / rqa_sig / f"{task}_best.pt"

def get_data_path(rqa_sig: str, task: str) -> Path:
    """获取数据文件路径"""
    return DATA_ROOT / rqa_sig / f"{task}.npz"

def get_metrics_path(rqa_sig: str, task: str) -> Path:
    """获取指标文件路径"""
    return MODELS_ROOT / rqa_sig / f"{task}_best_metrics.json"
