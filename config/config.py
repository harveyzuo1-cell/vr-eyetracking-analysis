# -*- coding: utf-8 -*-
"""
VR眼动数据处理系统 - 核心配置文件
"""
import os
from datetime import datetime
from typing import Dict, List, Any

# =============================================================================
# 基础配置
# =============================================================================

# 编码设置
INPUT_ENCODING = 'utf-8'
OUTPUT_ENCODING = 'utf-8'

# 视场角设置
FOV_DEGREE = 110.0

# 速度阈值设置
VELOCITY_THRESHOLD = 200.0  # deg/s

# 输出文件命名
OUTPUT_PREFIX = ""
OUTPUT_MIDDLE = "_preprocessed"
OUTPUT_SUFFIX = ".csv"

# =============================================================================
# 数据目录结构
# =============================================================================

# 控制组配置
CONTROL_GROUP_START = 1
CONTROL_GROUP_END = 20
CONTROL_GROUP_BASE_PATH = "C:/Users/asino/entropy/ip/mci-dataprocessing/ctg"

# MCI组配置
MCI_GROUP_BASE_PATH = "C:/Users/asino/entropy/ip/mci-dataprocessing/trans_mci"

# AD组配置
AD_GROUP_BASE_PATH = "C:/Users/asino/entropy/ip/mci-dataprocessing/trans_ad"

# 项目数据目录
DATA_DIRECTORIES = {
    'control_raw': 'data/control_raw',
    'control_processed': 'data/control_processed', 
    'control_calibrated': 'data/control_calibrated',
    'mci_raw': 'data/mci_raw',
    'mci_processed': 'data/mci_processed',
    'mci_calibrated': 'data/mci_calibrated',
    'ad_raw': 'data/ad_raw',
    'ad_processed': 'data/ad_processed',
    'ad_calibrated': 'data/ad_calibrated',
    'background_images': 'data/background_images'
}

# =============================================================================
# 任务文件配置
# =============================================================================

TASK_FILES = {
    'question_1': '1.txt',
    'question_2': '2.txt', 
    'question_3': '3.txt',
    'question_4': '4.txt',
    'question_5': '5.txt'
}

# =============================================================================
# 验证设置
# =============================================================================

VALIDATION_SETTINGS = {
    'check_file_existence': True,
    'check_data_format': True,
    'check_coordinate_range': True,
    'coordinate_min': 0.0,
    'coordinate_max': 1.0
}

# =============================================================================
# 进度条设置
# =============================================================================

PROGRESS_BAR_SETTINGS = {
    'show_progress': True,
    'bar_format': '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
    'colour': 'green'
}

# =============================================================================
# 错误处理
# =============================================================================

ERROR_HANDLING = {
    'skip_corrupted_files': True,
    'log_errors': True,
    'error_log_file': 'error_log.txt'
}

# =============================================================================
# 统计设置
# =============================================================================

STATISTICS_CONFIG = {
    'calculate_velocity_stats': True,
    'calculate_coordinate_stats': True,
    'z_score_threshold': 3.0,
    'outlier_detection': True
}

# =============================================================================
# 配置验证函数
# =============================================================================

def validate_config() -> bool:
    """验证配置的有效性"""
    try:
        # 检查基本参数
        assert FOV_DEGREE > 0, "视场角必须大于0"
        assert VELOCITY_THRESHOLD > 0, "速度阈值必须大于0"
        assert CONTROL_GROUP_START <= CONTROL_GROUP_END, "控制组起始编号不能大于结束编号"
        
        # 检查数据目录
        for key, path in DATA_DIRECTORIES.items():
            if not os.path.exists(path):
                print(f"⚠️  数据目录不存在: {path}")
        
        return True
        
    except AssertionError as e:
        print(f"❌ 配置验证失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置验证出错: {e}")
        return False

def show_config_summary():
    """显示配置摘要"""
    print("=" * 60)
    print("📋 VR眼动数据处理系统 - 配置摘要")
    print("=" * 60)
    print(f"视场角: {FOV_DEGREE}°")
    print(f"速度阈值: {VELOCITY_THRESHOLD} deg/s")
    print(f"控制组范围: {CONTROL_GROUP_START}-{CONTROL_GROUP_END}")
    print(f"编码: 输入={INPUT_ENCODING}, 输出={OUTPUT_ENCODING}")
    print("=" * 60)

# =============================================================================
# 自动验证
# =============================================================================

if __name__ == "__main__":
    if validate_config():
        print("✓ Configuration validation passed")
        show_config_summary()
    else:
        print("✗ Configuration validation failed") 