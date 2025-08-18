"""
模块10-C配置文件
==============

定义服务层的路径、缓存限制等配置参数。
"""

from pathlib import Path

# 路径配置 - 使用绝对路径避免工作目录问题
import os
_PROJECT_ROOT = Path(__file__).parent.parent.parent  # 项目根目录
MODELS_ROOT = _PROJECT_ROOT / "models"              # 10-B权重目录
LOGS_ROOT = _PROJECT_ROOT / "runs"                  # TensorBoard日志目录
DATA_ROOT = _PROJECT_ROOT / "data/module10_datasets" # 数据集目录

# 模型缓存配置
CACHE_LIMIT = 5                          # 同时常驻内存的模型数量上限

# 默认配置
DEFAULT_SIG = "m2_tau1_eps0.055_lmin2"   # 默认RQA参数签名

# 推理配置
PREDICTION_DEVICE = "cpu"                # 推理设备，优先CPU避免GPU冲突
TORCH_THREADS = 1                        # PyTorch线程数（推理时单线程更稳定）

# API配置
MAX_FEATURES = 10                        # 特征向量长度
MIN_FEATURES = 10                        # 最小特征数量
VALID_Q_TAGS = ["Q1", "Q2", "Q3", "Q4", "Q5"]  # 有效的任务标签

# 性能配置
MODEL_LOAD_TIMEOUT = 30                  # 模型加载超时时间（秒）
PREDICTION_TIMEOUT = 5                   # 单次预测超时时间（秒）

# 日志配置
SERVICE_LOG_LEVEL = "INFO"               # 服务日志级别
MODEL_LOG_ENABLED = True                 # 是否记录模型操作日志