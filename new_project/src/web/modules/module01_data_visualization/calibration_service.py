"""
眼动数据校正服务
Gaze Data Calibration Service

提供位置偏移和时间裁剪功能
Fixed: Timestamp type conversion issue (2025-10-04)
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from config.settings import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CalibrationService:
    """眼动数据校正服务"""

    def __init__(self):
        self.data_root = Path(Config.DATA_ROOT)
        self.raw_dir = self.data_root / '01_raw'
        self.processed_dir = self.data_root / '02_processed'

        # 确保目录存在
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"CalibrationService initialized: processed_dir={self.processed_dir}")

    def apply_position_offset(
        self,
        data: pd.DataFrame,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> pd.DataFrame:
        """
        应用位置偏移

        Args:
            data: 原始数据 (必须包含x, y列)
            offset_x: X轴偏移量 (-0.1 ~ 0.1)
            offset_y: Y轴偏移量 (-0.1 ~ 0.1)

        Returns:
            校正后的数据

        Example:
            >>> data = pd.DataFrame({'x': [0.1, 0.2], 'y': [0.1, 0.2]})
            >>> result = service.apply_position_offset(data, 0.01, -0.02)
            >>> result['x'].iloc[0]  # 0.11
        """
        if data.empty:
            logger.warning("Empty dataframe provided to apply_position_offset")
            return data

        result = data.copy()

        if offset_x != 0:
            result['x'] = result['x'] + offset_x
            logger.debug(f"Applied X offset: {offset_x}")

        if offset_y != 0:
            result['y'] = result['y'] + offset_y
            logger.debug(f"Applied Y offset: {offset_y}")

        logger.info(f"Position offset applied: X={offset_x}, Y={offset_y}")
        return result

    def apply_time_trim(
        self,
        data: pd.DataFrame,
        trim_start: float = 0.0,
        trim_end: float = 0.0
    ) -> pd.DataFrame:
        """
        应用时间裁剪

        Args:
            data: 原始数据 (必须包含timestamp列)
            trim_start: 起始裁剪秒数
            trim_end: 结束裁剪秒数

        Returns:
            裁剪后的数据

        Example:
            >>> data = pd.DataFrame({
            ...     'x': [0.1, 0.2, 0.3, 0.4, 0.5],
            ...     'y': [0.1, 0.2, 0.3, 0.4, 0.5],
            ...     'timestamp': [0, 0.1, 0.2, 0.3, 0.4]
            ... })
            >>> result = service.apply_time_trim(data, 0.1, 0.1)
            >>> len(result)  # 3 (middle 3 points)
        """
        if data.empty:
            logger.warning("Empty dataframe provided to apply_time_trim")
            return data

        if trim_start == 0 and trim_end == 0:
            return data

        result = data.copy()

        # 确保 timestamp 列是数值类型
        result['timestamp'] = pd.to_numeric(result['timestamp'], errors='coerce')

        # 计算时间范围
        min_time = result['timestamp'].min()
        max_time = result['timestamp'].max()
        total_duration = max_time - min_time

        # 应用裁剪
        start_threshold = min_time + trim_start
        end_threshold = max_time - trim_end

        # 过滤数据
        result = result[
            (result['timestamp'] >= start_threshold) &
            (result['timestamp'] <= end_threshold)
        ].copy()

        # 重置timestamp从0开始
        if not result.empty:
            result['timestamp'] = result['timestamp'] - result['timestamp'].min()

        points_before = len(data)
        points_after = len(result)

        logger.info(
            f"Time trim applied: start={trim_start}s, end={trim_end}s, "
            f"duration={total_duration:.2f}s, points: {points_before} -> {points_after}"
        )

        return result

    def save_calibrated_data(
        self,
        group: str,
        subject_id: str,
        task: str,
        params: Dict
    ) -> Dict:
        """
        保存校正数据

        Args:
            group: 组别 (control/mci/ad)
            subject_id: 受试者ID
            task: 任务ID (q1/q2/...)
            params: 校正参数 {offsetX, offsetY, trimStart, trimEnd}

        Returns:
            保存结果信息字典

        Raises:
            FileNotFoundError: 原始数据文件不存在
            ValueError: 数据格式错误
        """
        # 读取原始数据
        raw_file = self.raw_dir / group / f"{subject_id}_{task}.csv"

        if not raw_file.exists():
            raise FileNotFoundError(f"原始数据文件不存在: {raw_file}")

        logger.info(f"Loading raw data from: {raw_file}")
        data = pd.read_csv(raw_file)

        # 验证必需列
        required_cols = ['x', 'y', 'timestamp']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"数据缺少必需列: {missing_cols}")

        original_points = len(data)
        logger.info(f"Loaded {original_points} data points")

        # 确保 timestamp 列是数值类型（在所有操作之前）
        # 首先尝试转换为datetime，如果失败则尝试直接转换为数值
        try:
            # 尝试解析为datetime并转换为Unix时间戳（秒）
            data['timestamp'] = pd.to_datetime(data['timestamp']).astype('int64') / 1e9
        except:
            # 如果已经是数值格式，直接转换
            data['timestamp'] = pd.to_numeric(data['timestamp'], errors='coerce')

        # 应用校正
        calibrated = data.copy()

        # 1. 位置偏移
        offset_x = params.get('offsetX', 0)
        offset_y = params.get('offsetY', 0)

        if offset_x != 0 or offset_y != 0:
            calibrated = self.apply_position_offset(
                calibrated,
                offset_x=offset_x,
                offset_y=offset_y
            )

        # 2. 时间裁剪
        trim_start = params.get('trimStart', 0)
        trim_end = params.get('trimEnd', 0)

        if trim_start != 0 or trim_end != 0:
            calibrated = self.apply_time_trim(
                calibrated,
                trim_start=trim_start,
                trim_end=trim_end
            )

        # 保存校正数据
        output_dir = self.processed_dir / group
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建历史版本目录
        history_dir = output_dir / 'calibration_history'
        history_dir.mkdir(parents=True, exist_ok=True)

        # 获取下一个版本号
        version_num = self._get_next_version(group, subject_id, task)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存到历史版本
        history_data_file = history_dir / f"{subject_id}_{task}_v{version_num}_{timestamp}.csv"
        history_params_file = history_dir / f"{subject_id}_{task}_v{version_num}_{timestamp}.json"

        calibrated.to_csv(history_data_file, index=False)

        # 同时更新当前版本（最新版本的快捷方式）
        output_file = output_dir / f"{subject_id}_{task}_calibrated.csv"
        calibrated.to_csv(output_file, index=False)

        logger.info(f"Saved calibrated data to: {output_file}")
        logger.info(f"Saved history version v{version_num}: {history_data_file}")

        # 保存校正参数和元数据
        params_file = output_dir / f"{subject_id}_{task}_calibration_params.json"
        metadata = {
            'version': version_num,
            'params': params,
            'metadata': {
                'subject_id': subject_id,
                'task': task,
                'group': group,
                'calibrated_at': datetime.now().isoformat(),
                'points_before': original_points,
                'points_after': len(calibrated),
                'original_file': str(raw_file),
                'calibrated_file': str(output_file),
                'history_file': str(history_data_file)
            }
        }

        # 保存当前版本参数
        with open(params_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # 保存历史版本参数
        with open(history_params_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved calibration params to: {params_file}")

        return {
            'output_file': str(output_file),
            'params_file': str(params_file),
            'points_before': original_points,
            'points_after': len(calibrated),
            'duration_before': data['timestamp'].max() - data['timestamp'].min() if not data.empty else 0,
            'duration_after': calibrated['timestamp'].max() - calibrated['timestamp'].min() if not calibrated.empty else 0
        }

    def get_saved_params(
        self,
        group: str,
        subject_id: str,
        task: str
    ) -> Optional[Dict]:
        """
        获取已保存的校正参数

        Args:
            group: 组别
            subject_id: 受试者ID
            task: 任务ID

        Returns:
            校正参数字典，如果不存在返回None
        """
        params_file = (
            self.processed_dir / group /
            f"{subject_id}_{task}_calibration_params.json"
        )

        if not params_file.exists():
            logger.debug(f"Calibration params not found: {params_file}")
            return None

        with open(params_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded calibration params from: {params_file}")
            return data

    def load_calibrated_data(
        self,
        group: str,
        subject_id: str,
        task: str
    ) -> List[Dict]:
        """
        加载校正后的数据

        Args:
            group: 组别
            subject_id: 受试者ID
            task: 任务ID

        Returns:
            校正数据的字典列表

        Raises:
            FileNotFoundError: 校正数据不存在
        """
        calibrated_file = (
            self.processed_dir / group /
            f"{subject_id}_{task}_calibrated.csv"
        )

        if not calibrated_file.exists():
            raise FileNotFoundError(f"校正数据不存在: {calibrated_file}")

        logger.info(f"Loading calibrated data from: {calibrated_file}")
        data = pd.read_csv(calibrated_file)

        return data.to_dict('records')

    def delete_calibration(
        self,
        group: str,
        subject_id: str,
        task: str
    ) -> bool:
        """
        删除校正数据

        Args:
            group: 组别
            subject_id: 受试者ID
            task: 任务ID

        Returns:
            是否删除成功
        """
        calibrated_file = (
            self.processed_dir / group /
            f"{subject_id}_{task}_calibrated.csv"
        )
        params_file = (
            self.processed_dir / group /
            f"{subject_id}_{task}_calibration_params.json"
        )

        deleted = False

        if calibrated_file.exists():
            calibrated_file.unlink()
            logger.info(f"Deleted calibrated file: {calibrated_file}")
            deleted = True

        if params_file.exists():
            params_file.unlink()
            logger.info(f"Deleted params file: {params_file}")
            deleted = True

        return deleted

    def _get_next_version(
        self,
        group: str,
        subject_id: str,
        task: str
    ) -> int:
        """
        获取下一个版本号

        Args:
            group: 组别
            subject_id: 受试者ID
            task: 任务ID

        Returns:
            下一个版本号
        """
        history_dir = self.processed_dir / group / 'calibration_history'
        if not history_dir.exists():
            return 1

        # 查找所有匹配的历史文件
        pattern = f"{subject_id}_{task}_v*.json"
        history_files = list(history_dir.glob(pattern))

        if not history_files:
            return 1

        # 提取版本号
        versions = []
        for file in history_files:
            try:
                # 文件名格式: {subject}_{task}_v{version}_{timestamp}.json
                parts = file.stem.split('_v')
                if len(parts) >= 2:
                    version_str = parts[1].split('_')[0]
                    versions.append(int(version_str))
            except (ValueError, IndexError):
                continue

        return max(versions) + 1 if versions else 1

    def get_calibration_versions(
        self,
        group: str,
        subject_id: str,
        task: str
    ) -> list:
        """
        获取所有校准版本列表

        Args:
            group: 组别
            subject_id: 受试者ID
            task: 任务ID

        Returns:
            版本列表，按时间倒序排列（最新的在前）
        """
        history_dir = self.processed_dir / group / 'calibration_history'
        if not history_dir.exists():
            return []

        # 查找所有匹配的历史文件
        pattern = f"{subject_id}_{task}_v*.json"
        history_files = list(history_dir.glob(pattern))

        versions = []
        for file in history_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                    # 提取文件名中的版本号和时间戳
                    parts = file.stem.split('_v')
                    if len(parts) >= 2:
                        version_parts = parts[1].split('_')
                        version_num = int(version_parts[0])
                        timestamp_str = '_'.join(version_parts[1:])

                        versions.append({
                            'version': version_num,
                            'timestamp': timestamp_str,
                            'calibrated_at': metadata.get('metadata', {}).get('calibrated_at', ''),
                            'params': metadata.get('params', {}),
                            'points_before': metadata.get('metadata', {}).get('points_before', 0),
                            'points_after': metadata.get('metadata', {}).get('points_after', 0),
                            'data_file': str(file.with_suffix('.csv')),
                            'params_file': str(file)
                        })
            except (ValueError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse version file {file}: {e}")
                continue

        # 按版本号降序排序（最新的在前）
        versions.sort(key=lambda x: x['version'], reverse=True)

        logger.info(f"Found {len(versions)} calibration versions for {group}/{subject_id}_{task}")
        return versions

    def restore_calibration_version(
        self,
        group: str,
        subject_id: str,
        task: str,
        version: int
    ) -> dict:
        """
        恢复到指定版本

        Args:
            group: 组别
            subject_id: 受试者ID
            task: 任务ID
            version: 要恢复的版本号

        Returns:
            恢复后的数据信息

        Raises:
            FileNotFoundError: 指定版本不存在
        """
        history_dir = self.processed_dir / group / 'calibration_history'

        # 查找指定版本的文件
        pattern = f"{subject_id}_{task}_v{version}_*.json"
        matching_files = list(history_dir.glob(pattern))

        if not matching_files:
            raise FileNotFoundError(f"Version {version} not found")

        # 使用最新的匹配文件（如果有多个）
        version_params_file = matching_files[-1]
        version_data_file = version_params_file.with_suffix('.csv')

        if not version_data_file.exists():
            raise FileNotFoundError(f"Version data file not found: {version_data_file}")

        # 读取版本数据
        version_data = pd.read_csv(version_data_file)
        with open(version_params_file, 'r', encoding='utf-8') as f:
            version_metadata = json.load(f)

        # 更新当前版本
        output_dir = self.processed_dir / group
        current_data_file = output_dir / f"{subject_id}_{task}_calibrated.csv"
        current_params_file = output_dir / f"{subject_id}_{task}_calibration_params.json"

        version_data.to_csv(current_data_file, index=False)

        # 更新元数据，标记为恢复的版本
        version_metadata['metadata']['restored_from_version'] = version
        version_metadata['metadata']['restored_at'] = datetime.now().isoformat()

        with open(current_params_file, 'w', encoding='utf-8') as f:
            json.dump(version_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Restored calibration to version {version}")

        return {
            'version': version,
            'data_file': str(current_data_file),
            'params_file': str(current_params_file),
            'metadata': version_metadata
        }
