"""
Module05 数据验证层 - 解决路径硬编码和数据格式不一致问题
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RQADataValidator:
    """RQA数据验证器"""

    @staticmethod
    def validate_rqa_params(params: Dict) -> Tuple[bool, Optional[str]]:
        """
        验证RQA参数的有效性

        Args:
            params: RQA参数字典 {'m': int, 'tau': int, 'eps': float, 'lmin': int}

        Returns:
            (is_valid, error_message)
        """
        required_keys = ['m', 'tau', 'eps', 'lmin']

        # 检查必需字段
        for key in required_keys:
            if key not in params:
                return False, f"缺少必需参数: {key}"

        # 验证m (embedding dimension)
        m = params['m']
        if not isinstance(m, int) or m < 1 or m > 20:
            return False, f"参数m必须是1-20之间的整数, 当前值: {m}"

        # 验证tau (time delay)
        tau = params['tau']
        if not isinstance(tau, int) or tau < 1 or tau > 20:
            return False, f"参数tau必须是1-20之间的整数, 当前值: {tau}"

        # 验证eps (threshold)
        eps = params['eps']
        if not isinstance(eps, (int, float)) or eps <= 0 or eps > 1:
            return False, f"参数eps必须是0-1之间的数值, 当前值: {eps}"

        # 验证lmin (minimum line length)
        lmin = params['lmin']
        if not isinstance(lmin, int) or lmin < 2 or lmin > 10:
            return False, f"参数lmin必须是2-10之间的整数, 当前值: {lmin}"

        return True, None

    @staticmethod
    def validate_groups(groups: List[str]) -> Tuple[bool, Optional[str]]:
        """
        验证分组列表

        Args:
            groups: 分组列表

        Returns:
            (is_valid, error_message)
        """
        valid_groups = ['control', 'mci', 'ad']

        if not groups:
            return False, "分组列表不能为空"

        for group in groups:
            if group not in valid_groups:
                return False, f"无效的分组: {group}, 有效值: {valid_groups}"

        return True, None

    @staticmethod
    def validate_data_version(data_version: str) -> Tuple[bool, Optional[str]]:
        """
        验证数据版本

        Args:
            data_version: 数据版本标识

        Returns:
            (is_valid, error_message)
        """
        valid_versions = ['v1', 'v2']

        if data_version not in valid_versions:
            return False, f"无效的数据版本: {data_version}, 有效值: {valid_versions}"

        return True, None

    @staticmethod
    def standardize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame格式（解决大小写不一致问题）

        Args:
            df: 原始DataFrame

        Returns:
            标准化后的DataFrame
        """
        # 1. 列名标准化为小写
        df.columns = df.columns.str.lower()

        # 2. group列值标准化为小写
        if 'group' in df.columns:
            df['group'] = df['group'].str.lower()

        # 3. subject_id列值标准化（如果存在）
        if 'subject_id' in df.columns:
            df['subject_id'] = df['subject_id'].str.lower()

        return df

    @staticmethod
    def validate_file_path(file_path: Path, expected_subdir: str) -> Tuple[bool, Optional[str]]:
        """
        验证文件路径是否在预期的子目录中（解决路径硬编码问题）

        Args:
            file_path: 文件路径
            expected_subdir: 预期的子目录名称 (如 'step3_feature_enrichment')

        Returns:
            (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"文件不存在: {file_path}"

        if expected_subdir not in str(file_path):
            return False, f"文件不在预期子目录 {expected_subdir} 中: {file_path}"

        return True, None

    @staticmethod
    def get_step_file_path(param_dir: Path, step_num: int, filename: str) -> Path:
        """
        获取步骤文件的标准化路径（消除硬编码）

        Args:
            param_dir: 参数目录
            step_num: 步骤编号 (1-5)
            filename: 文件名

        Returns:
            标准化的文件路径
        """
        step_map = {
            1: 'step1_rqa_features',
            2: 'step2_data_merging',
            3: 'step3_feature_enrichment',
            4: 'step4_statistical_analysis',
            5: 'step5_visualization'
        }

        if step_num not in step_map:
            raise ValueError(f"无效的步骤编号: {step_num}, 必须是1-5")

        step_dir = param_dir / step_map[step_num]
        return step_dir / filename

    @staticmethod
    def validate_rqa_features_dataframe(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        验证RQA特征DataFrame的格式

        Args:
            df: RQA特征DataFrame

        Returns:
            (is_valid, error_message)
        """
        required_columns = ['subject_id', 'group']

        # 标准化
        df_std = RQADataValidator.standardize_dataframe(df.copy())

        # 检查必需列
        missing_cols = [col for col in required_columns if col not in df_std.columns]
        if missing_cols:
            return False, f"缺少必需列: {missing_cols}"

        # 检查RQA特征列（应至少有一些RQA指标）
        rqa_features = [col for col in df_std.columns if any(
            col.startswith(prefix) or 'rqa' in col
            for prefix in ['x_', 'y_', 'combined_', 'rr', 'det', 'ent', 'lam']
        )]

        if not rqa_features:
            return False, "DataFrame中未找到RQA特征列"

        # 检查分组值
        if 'group' in df_std.columns:
            groups = df_std['group'].unique()
            valid_groups = ['control', 'mci', 'ad']
            invalid_groups = [g for g in groups if g not in valid_groups]
            if invalid_groups:
                return False, f"DataFrame包含无效的分组值: {invalid_groups}"

        return True, None


class RQAPathManager:
    """RQA路径管理器 - 集中管理所有路径构建逻辑"""

    def __init__(self, data_root: Path):
        """
        初始化路径管理器

        Args:
            data_root: 数据根目录
        """
        self.data_root = data_root
        self.results_dir = data_root / '05_rqa_analysis' / 'results'

    def get_enriched_features_file(self, param_dir: Path) -> Path:
        """获取增强特征文件的标准路径"""
        return param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'

    def get_merged_features_file(self, param_dir: Path) -> Path:
        """获取合并特征文件的标准路径"""
        return param_dir / 'step2_data_merging' / 'merged_rqa_features.csv'

    def get_group_comparison_file(self, param_dir: Path) -> Path:
        """获取组间比较文件的标准路径"""
        return param_dir / 'step4_statistical_analysis' / 'group_comparison.csv'

    def get_visualization_dir(self, param_dir: Path) -> Path:
        """获取可视化目录的标准路径"""
        return param_dir / 'step5_visualization' / 'statistical_plots'

    def ensure_step_directories(self, param_dir: Path) -> None:
        """确保所有步骤目录存在"""
        for step_num in range(1, 6):
            step_file = RQADataValidator.get_step_file_path(param_dir, step_num, 'dummy')
            step_file.parent.mkdir(parents=True, exist_ok=True)
