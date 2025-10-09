"""
多进程RQA计算Worker
独立的worker函数,可被pickle序列化传递给子进程
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import logging
import threading
import json
from datetime import datetime

from src.modules.module05_rqa_analysis.rqa_analyzer import RQAAnalyzer
from src.modules.module05_rqa_analysis.service import RQAAnalysisService
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def rqa_worker(
    file_path: str,
    params: Dict,
    groups: list,
    data_version: str = 'v1'
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    RQA计算worker函数 - 可被pickle序列化

    Args:
        file_path: CSV文件路径
        params: RQA参数字典 {'m': int, 'tau': int, 'eps': float, 'lmin': int}
        groups: 组别列表 ['control', 'mci', 'ad']
        data_version: 数据版本 'v1' 或 'v2'

    Returns:
        (success, result_dict, error_message)
    """
    try:
        # 在子进程中创建RQAAnalyzer实例
        analyzer = RQAAnalyzer()

        # 使用analyze_single_file方法进行RQA分析
        rqa_result = analyzer.analyze_single_file(file_path, params)

        # 从文件路径提取subject_id和task_id
        file_path_obj = Path(file_path)
        filename = file_path_obj.stem  # 去掉.csv后缀
        parts = filename.replace('_calibrated', '').split('_')

        if len(parts) >= 2:
            task_id = parts[-1]
            subject_id = '_'.join(parts[:-1])
        else:
            return False, None, f"无法解析文件名: {filename}"

        # 添加subject_id和task_id到结果
        result = {
            'subject_id': subject_id,
            'task_id': task_id,
            **rqa_result
        }

        return True, result, None

    except Exception as e:
        error_msg = f"处理文件 {file_path} 失败: {str(e)}"
        return False, None, error_msg


def save_rqa_result_worker(
    result: Dict,
    base_dir: str
) -> Tuple[bool, Optional[str]]:
    """
    保存RQA结果的worker函数

    Args:
        result: RQA计算结果字典
        base_dir: 基础目录路径

    Returns:
        (success, error_message)
    """
    try:
        from src.modules.module05_rqa_analysis.service import RQAAnalysisService

        # 在子进程中创建Service实例
        service = RQAAnalysisService(base_dir=Path(base_dir))

        # 保存结果
        params = result['parameters']
        service.save_param_metadata(
            params=params,
            step=1,
            data={
                'rqa_1d_x': result['rqa_1d_x'],
                'rqa_1d_y': result['rqa_1d_y'],
                'rqa_2d': result['rqa_2d'],
                'subject_id': result['subject_id'],
                'group': result['group'],
                'task_id': result['task_id']
            },
            task_id=result.get('batch_task_id'),
            data_version=result.get('data_version', 'v1')
        )

        return True, None

    except Exception as e:
        return False, str(e)
