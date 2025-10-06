"""
数据加载器

统一的数据加载接口，支持各种数据格式和阶段
"""
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

from config.settings import Config

logger = logging.getLogger(__name__)


class DataLoader:
    """数据加载器类"""

    def __init__(self, config: Config = None):
        """
        初始化数据加载器

        Args:
            config: 配置对象，默认使用Config
        """
        self.config = config or Config

    def load_raw_data(
        self,
        group: str,
        subject_id: str,
        task_id: str
    ) -> pd.DataFrame:
        """
        加载原始眼动数据

        Args:
            group: 组别 (control/mci/ad)
            subject_id: 受试者ID
            task_id: 任务ID

        Returns:
            DataFrame: 原始眼动数据

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 数据格式错误
        """
        file_path = self.config.get_data_path(group, subject_id, task_id, stage='raw')

        if not file_path.exists():
            raise FileNotFoundError(f"原始数据文件不存在: {file_path}")

        try:
            df = pd.read_csv(file_path)

            # 应用列名映射（兼容旧格式）
            df = self._apply_column_mapping(df)

            # 验证必需列
            missing_cols = set(self.config.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                raise ValueError(f"缺少必要列: {missing_cols}")

            logger.info(f"成功加载原始数据: {file_path.name}, {len(df)} 行")
            return df

        except Exception as e:
            logger.error(f"加载原始数据失败: {file_path}, 错误: {str(e)}")
            raise

    def load_processed_data(
        self,
        group: str,
        subject_id: str,
        task_id: str,
        stage: str = 'preprocessed'
    ) -> pd.DataFrame:
        """
        加载处理后的数据

        Args:
            group: 组别
            subject_id: 受试者ID
            task_id: 任务ID
            stage: 数据阶段 (preprocessed/calibrated)

        Returns:
            DataFrame: 处理后的数据
        """
        file_path = self.config.get_data_path(group, subject_id, task_id, stage=stage)

        if not file_path.exists():
            raise FileNotFoundError(f"{stage}数据文件不存在: {file_path}")

        try:
            df = pd.read_csv(file_path)
            df = self._apply_column_mapping(df)

            logger.info(f"成功加载{stage}数据: {file_path.name}")
            return df

        except Exception as e:
            logger.error(f"加载{stage}数据失败: {file_path}, 错误: {str(e)}")
            raise

    def load_mmse_data(self, group: Optional[str] = None) -> pd.DataFrame:
        """
        加载MMSE分数数据

        Args:
            group: 组别，如果为None则加载所有组

        Returns:
            DataFrame: MMSE分数数据
        """
        mmse_file = self.config.RAW_CLINICAL_DIR / "mmse_scores.csv"

        if not mmse_file.exists():
            raise FileNotFoundError(f"MMSE数据文件不存在: {mmse_file}")

        try:
            df = pd.read_csv(mmse_file)

            if group is not None:
                if group not in self.config.VALID_GROUPS:
                    raise ValueError(f"无效的组别: {group}")
                df = df[df['group_type'] == group]

            logger.info(f"成功加载MMSE数据: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"加载MMSE数据失败: {mmse_file}, 错误: {str(e)}")
            raise

    def load_features(
        self,
        group: str,
        subject_id: str,
        task_id: str,
        feature_type: str = 'comprehensive'
    ) -> pd.DataFrame:
        """
        加载特征数据

        Args:
            group: 组别
            subject_id: 受试者ID
            task_id: 任务ID
            feature_type: 特征类型 (rqa/events/comprehensive)

        Returns:
            DataFrame: 特征数据
        """
        if feature_type == 'rqa':
            features_dir = self.config.RQA_FEATURES_DIR
        elif feature_type == 'events':
            features_dir = self.config.EVENT_FEATURES_DIR
        elif feature_type == 'comprehensive':
            features_dir = self.config.COMPREHENSIVE_FEATURES_DIR
        else:
            raise ValueError(f"不支持的特征类型: {feature_type}")

        filename = f"{group}_{subject_id}_{task_id}_{feature_type}.csv"
        file_path = features_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"特征文件不存在: {file_path}")

        try:
            df = pd.read_csv(file_path)
            logger.info(f"成功加载{feature_type}特征: {file_path.name}")
            return df

        except Exception as e:
            logger.error(f"加载特征失败: {file_path}, 错误: {str(e)}")
            raise

    def list_subjects(
        self,
        group: str,
        stage: str = 'raw'
    ) -> List[str]:
        """
        列出指定组别的所有受试者ID

        Args:
            group: 组别
            stage: 数据阶段

        Returns:
            List[str]: 受试者ID列表
        """
        if stage == 'raw':
            base_dir = self.config.RAW_DATA_DIR / group
        elif stage == 'preprocessed':
            base_dir = self.config.PREPROCESSED_DATA_DIR / group
        elif stage == 'calibrated':
            base_dir = self.config.CALIBRATED_DATA_DIR / group
        else:
            raise ValueError(f"不支持的阶段: {stage}")

        if not base_dir.exists():
            return []

        # 从文件名提取受试者ID
        subject_ids = set()
        for file_path in base_dir.glob("*.csv"):
            # 文件名格式: <group>_<subject_id>_<task_id>[_<stage>].csv
            parts = file_path.stem.split('_')
            if len(parts) >= 3:
                subject_id = parts[1]
                subject_ids.add(subject_id)

        return sorted(list(subject_ids))

    def list_tasks(
        self,
        group: str,
        subject_id: str,
        stage: str = 'raw'
    ) -> List[str]:
        """
        列出指定受试者的所有任务ID

        Args:
            group: 组别
            subject_id: 受试者ID
            stage: 数据阶段

        Returns:
            List[str]: 任务ID列表
        """
        if stage == 'raw':
            base_dir = self.config.RAW_DATA_DIR / group
        elif stage == 'preprocessed':
            base_dir = self.config.PREPROCESSED_DATA_DIR / group
        elif stage == 'calibrated':
            base_dir = self.config.CALIBRATED_DATA_DIR / group
        else:
            raise ValueError(f"不支持的阶段: {stage}")

        if not base_dir.exists():
            return []

        # 查找匹配的文件
        pattern = f"{group}_{subject_id}_*.csv"
        task_ids = []

        for file_path in base_dir.glob(pattern):
            parts = file_path.stem.split('_')
            if len(parts) >= 3:
                task_id = parts[2]
                task_ids.append(task_id)

        return sorted(list(set(task_ids)))

    def _apply_column_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        应用列名映射（兼容旧格式）

        Args:
            df: 原始DataFrame

        Returns:
            DataFrame: 映射后的DataFrame
        """
        # 检查是否需要映射
        rename_dict = {}
        for old_name, new_name in self.config.COLUMN_MAPPING.items():
            if old_name in df.columns and new_name not in df.columns:
                rename_dict[old_name] = new_name

        if rename_dict:
            df = df.rename(columns=rename_dict)
            logger.debug(f"应用列名映射: {rename_dict}")

        return df
