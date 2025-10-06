"""
数据验证器

提供各种数据验证功能
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

from config.settings import Config

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器类"""

    def __init__(self, config: Config = None):
        """
        初始化验证器

        Args:
            config: 配置对象
        """
        self.config = config or Config

    def validate_eyetracking_data(
        self,
        df: pd.DataFrame,
        stage: str = 'raw'
    ) -> Tuple[bool, List[str]]:
        """
        验证眼动数据

        Args:
            df: 眼动数据DataFrame
            stage: 数据阶段

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查DataFrame是否为空
        if df.empty:
            errors.append("数据为空")
            return False, errors

        # 检查必需列
        required_cols = self.config.REQUIRED_COLUMNS
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"缺少必要列: {missing_cols}")

        # 检查数据范围
        if 'x' in df.columns:
            x_min, x_max = df['x'].min(), df['x'].max()
            if x_min < 0 or x_max > 1:
                errors.append(f"x坐标超出范围 [0, 1]: [{x_min:.4f}, {x_max:.4f}]")

        if 'y' in df.columns:
            y_min, y_max = df['y'].min(), df['y'].max()
            if y_min < 0 or y_max > 1:
                errors.append(f"y坐标超出范围 [0, 1]: [{y_min:.4f}, {y_max:.4f}]")

        # 检查时间列
        if 'time' in df.columns:
            if df['time'].isnull().any():
                errors.append("时间列包含空值")

            if not df['time'].is_monotonic_increasing:
                errors.append("时间列非递增")

            if df['time'].min() < 0:
                errors.append("时间列包含负值")

        # 检查空值
        null_counts = df[required_cols].isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        if not cols_with_nulls.empty:
            errors.append(f"以下列包含空值: {cols_with_nulls.to_dict()}")

        # 检查数据点数量
        if len(df) < 10:
            errors.append(f"数据点过少: {len(df)} 行")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"眼动数据验证通过: {len(df)} 行")
        else:
            logger.warning(f"眼动数据验证失败: {len(errors)} 个错误")

        return is_valid, errors

    def validate_mmse_data(
        self,
        df: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        验证MMSE数据

        Args:
            df: MMSE数据DataFrame

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查DataFrame是否为空
        if df.empty:
            errors.append("MMSE数据为空")
            return False, errors

        # 检查必需列
        required_cols = ['subject_id', 'group_type', 'task_id', 'mmse_score']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"缺少必要列: {missing_cols}")

        # 检查组别
        if 'group_type' in df.columns:
            invalid_groups = set(df['group_type'].unique()) - set(self.config.VALID_GROUPS)
            if invalid_groups:
                errors.append(f"包含无效组别: {invalid_groups}")

        # 检查任务ID
        if 'task_id' in df.columns:
            task_ids = [t.lower() for t in df['task_id'].unique()]
            valid_tasks = [t.lower() for t in self.config.VALID_TASKS]
            invalid_tasks = set(task_ids) - set(valid_tasks)
            if invalid_tasks:
                errors.append(f"包含无效任务ID: {invalid_tasks}")

        # 检查MMSE分数范围
        if 'mmse_score' in df.columns:
            if df['mmse_score'].min() < 0:
                errors.append("MMSE分数包含负值")
            if df['mmse_score'].max() > 30:
                errors.append("MMSE分数超过30分")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"MMSE数据验证通过: {len(df)} 行")
        else:
            logger.warning(f"MMSE数据验证失败: {len(errors)} 个错误")

        return is_valid, errors

    def validate_features(
        self,
        df: pd.DataFrame,
        feature_names: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        验证特征数据

        Args:
            df: 特征数据DataFrame
            feature_names: 期望的特征名列表

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查DataFrame是否为空
        if df.empty:
            errors.append("特征数据为空")
            return False, errors

        # 检查特征列
        if feature_names is not None:
            missing_features = set(feature_names) - set(df.columns)
            if missing_features:
                errors.append(f"缺少特征列: {missing_features}")

        # 检查数值类型
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        non_numeric_cols = set(df.columns) - set(numeric_cols) - {'subject_id', 'task_id', 'group_type', 'session_id'}
        if non_numeric_cols:
            errors.append(f"以下列非数值类型: {non_numeric_cols}")

        # 检查特征值范围（归一化特征应在0-1之间）
        for col in numeric_cols:
            col_min, col_max = df[col].min(), df[col].max()
            if col_min < 0 or col_max > 1:
                # 允许一定的容差
                if col_min < -0.01 or col_max > 1.01:
                    errors.append(f"特征 {col} 超出范围 [0, 1]: [{col_min:.4f}, {col_max:.4f}]")

        # 检查无穷值和NaN
        if df[numeric_cols].isnull().any().any():
            null_cols = df[numeric_cols].isnull().sum()
            null_cols = null_cols[null_cols > 0]
            errors.append(f"以下特征列包含空值: {null_cols.to_dict()}")

        if np.isinf(df[numeric_cols].values).any():
            errors.append("特征数据包含无穷值")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"特征数据验证通过: {len(df)} 行, {len(numeric_cols)} 个特征")
        else:
            logger.warning(f"特征数据验证失败: {len(errors)} 个错误")

        return is_valid, errors

    def validate_file_naming(
        self,
        filename: str,
        stage: str = 'raw'
    ) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        验证文件命名规范

        Args:
            filename: 文件名（不含路径）
            stage: 数据阶段

        Returns:
            Tuple[bool, Optional[Dict]]: (是否有效, 解析出的信息字典)
        """
        # 移除扩展名
        name_without_ext = filename.rsplit('.', 1)[0]

        # 解析文件名
        parts = name_without_ext.split('_')

        # 原始数据: <group>_<subject_id>_<task_id>.csv
        # 处理后数据: <group>_<subject_id>_<task_id>_<stage>.csv
        expected_parts = 3 if stage == 'raw' else 4

        if len(parts) != expected_parts:
            logger.warning(f"文件名格式错误: {filename}, 期望 {expected_parts} 部分，实际 {len(parts)} 部分")
            return False, None

        info = {
            'group': parts[0],
            'subject_id': parts[1],
            'task_id': parts[2]
        }

        if stage != 'raw' and len(parts) == 4:
            info['stage'] = parts[3]

        # 验证组别
        if info['group'] not in self.config.VALID_GROUPS:
            logger.warning(f"无效的组别: {info['group']}")
            return False, None

        # 验证任务ID
        if info['task_id'].lower() not in [t.lower() for t in self.config.VALID_TASKS]:
            logger.warning(f"无效的任务ID: {info['task_id']}")
            return False, None

        logger.debug(f"文件名验证通过: {filename}")
        return True, info

    def validate_rqa_params(
        self,
        params: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        验证RQA参数

        Args:
            params: RQA参数字典

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查必需参数
        required_params = ['m', 'tau', 'eps', 'lmin']
        missing_params = set(required_params) - set(params.keys())
        if missing_params:
            errors.append(f"缺少RQA参数: {missing_params}")
            return False, errors

        # 检查参数范围
        for param_name, param_value in params.items():
            if param_name not in self.config.RQA_PARAM_RANGES:
                continue

            ranges = self.config.RQA_PARAM_RANGES[param_name]
            if param_value < ranges['min'] or param_value > ranges['max']:
                errors.append(
                    f"参数 {param_name} 超出范围 "
                    f"[{ranges['min']}, {ranges['max']}]: {param_value}"
                )

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"RQA参数验证通过: {params}")
        else:
            logger.warning(f"RQA参数验证失败: {len(errors)} 个错误")

        return is_valid, errors
