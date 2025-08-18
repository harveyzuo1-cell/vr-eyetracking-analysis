"""
模块10-A配置文件
包含常量定义、路径配置和默认参数
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

# 模块7输出路径
MODULE7_ROOT = DATA_ROOT / "module7_integrated_results"

# 模块10输出路径
MODULE10_ROOT = DATA_ROOT / "module10_datasets"

# 确保输出目录存在
MODULE10_ROOT.mkdir(parents=True, exist_ok=True)

# 10个核心特征名称（与模块7保持一致）
FEATURE_NAMES = [
    "game_duration",    # 游戏时长
    "roi_kw_time",      # 关键词ROI时间
    "roi_inst_time",    # 指令ROI时间  
    "roi_bg_time",      # 背景ROI时间
    "rr_1d",           # 1D递归率
    "det_1d",          # 1D确定性
    "ent_1d",          # 1D熵值
    "rr_2d",           # 2D递归率
    "det_2d",          # 2D确定性
    "ent_2d"           # 2D熵值
]

# 特征列映射：若CSV中存在*_norm列，则使用归一化列；否则回退到原列
FEATURE_ALIAS = {f: f"{f}_norm" for f in FEATURE_NAMES}

# MMSE任务类别
TASK_IDS = ["Q1", "Q2", "Q3", "Q4", "Q5"]

# 受试者组别
GROUP_TYPES = ["control", "mci", "ad"]

# 数据验证参数
VALIDATION_CONFIG = {
    "feature_range": (0.0, 1.0),  # 特征值范围
    "tolerance": 1e-6,            # 容差范围
    "min_samples_per_task": 10,   # 每个任务最小样本数
    "required_columns": [
        "session_id", "subject_id", "task_id", "group_type"
    ] + FEATURE_NAMES
}

# 默认参数
DEFAULT_CONFIG = {
    "val_split": 0.2,             # 验证集比例
    "random_state": 42,           # 随机种子
    "compression_level": 6        # npz压缩级别
}

# 文件名模式
FILE_PATTERNS = {
    "module7_csv": "integrated_features_summary.csv",
    "module7_meta": "metadata.json", 
    "module10_task": "{task_id}.npz",
    "module10_meta": "meta.json"
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "[%(asctime)s] %(levelname)s - %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S"
}