"""
Eye Tracking V2 Data Importer

从eye_tracking_data目录导入v2眼球追踪数据
数据格式: x:value y:value z:value/timestamp----
导入到: data/01_raw/{group}/{subject_id}_{task}.csv

Author: Claude Code
Date: 2025-10-02
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import re

from src.services.task_config_service import TaskConfigService

logger = logging.getLogger(__name__)


class EyeTrackingV2Importer:
    """Eye Tracking V2数据导入器"""

    # Group name mapping (处理编码问题)
    GROUP_MAPPING = {
        '控制组': 'control',
        'MCI': 'mci',
        '阿尔兹海默': 'ad',
        'custom': 'control',  # 测试数据归为control
        # UTF-8编码的中文(从data_index.json读取时显示为乱码,但实际是正确的UTF-8 bytes)
        '对照组': 'control',  # b'\xe5\xaf\xb9\xe7\x85\xa7\xe7\xbb\x84'
        '帅哥': 'control',    # b'\xe5\xb8\x85\xe5\x93\xa5'
        # 可能的编码变体(显示为乱码)
        '������': 'control',
        '�����Ⱥ�Ĭ': 'ad',
        '˧��': 'control'
    }

    def __init__(self, v2_data_dir: Optional[str] = None, output_dir: Optional[str] = None,
                 task_config_service: Optional[TaskConfigService] = None, dataset_id: str = "mmse_v2"):
        """
        初始化导入器

        Args:
            v2_data_dir: v2数据目录路径,默认为项目根目录的eye_tracking_data
            output_dir: 输出目录路径,默认为data/01_raw
            task_config_service: 任务配置服务实例（可选，默认使用单例）
            dataset_id: 数据集ID，默认mmse_v2
        """
        if v2_data_dir is None:
            # 默认路径: new_project的父目录下的eye_tracking_data
            project_root = Path(__file__).parent.parent.parent.parent.parent.parent
            v2_data_dir = project_root / "eye_tracking_data"

        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            output_dir = project_root / "data" / "01_raw"

        self.v2_data_dir = Path(v2_data_dir)
        self.output_dir = Path(output_dir)
        self.data_index_file = self.v2_data_dir / "data_index.json"

        # 注入TaskConfigService
        self.task_config_service = task_config_service or TaskConfigService()
        self.dataset_id = dataset_id

        # 从TaskConfigService动态构建level到task的映射
        self._build_level_task_mapping()

        logger.info(f"EyeTrackingV2Importer initialized")
        logger.info(f"  V2 data dir: {self.v2_data_dir}")
        logger.info(f"  Output dir: {self.output_dir}")
        logger.info(f"  Dataset ID: {self.dataset_id}")
        logger.info(f"  Level-Task mapping: {self.level_task_mapping}")

    def _build_level_task_mapping(self):
        """从TaskConfigService动态构建Level到Task的映射"""
        self.level_task_mapping = {}

        # 获取数据集的所有任务（已按order排序）
        tasks = self.task_config_service.get_tasks(self.dataset_id)

        for task in tasks:
            # 使用任务的order作为level
            level = str(task.get('order', 0))
            task_id = task['id']
            self.level_task_mapping[level] = task_id

        logger.info(f"Built level-task mapping from dataset '{self.dataset_id}': {self.level_task_mapping}")

    def _normalize_group_name(self, raw_group: str) -> Optional[str]:
        """
        规范化组名

        Args:
            raw_group: 原始组名

        Returns:
            规范化后的组名(control/mci/ad),如果无法识别返回None
        """
        if not raw_group:
            return None

        # Direct mapping
        if raw_group in self.GROUP_MAPPING:
            return self.GROUP_MAPPING[raw_group]

        # Fuzzy matching for encoding issues
        raw_lower = raw_group.lower()
        if 'mci' in raw_lower:
            return 'mci'
        elif 'control' in raw_lower or 'custom' in raw_lower:
            return 'control'
        elif 'ad' in raw_lower or 'alzheimer' in raw_lower:
            return 'ad'

        # Default to None if can't identify
        logger.warning(f"Unknown group name: {raw_group}")
        return None

    def _parse_v2_txt_file(self, txt_file: Path) -> pd.DataFrame:
        """
        解析v2格式的txt文件

        格式: x:0.296941y:0.769334z:0.000000/2025-3-27-11-37-31-522----

        Args:
            txt_file: txt文件路径

        Returns:
            DataFrame with columns: x, y, z, timestamp
        """
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by ----
            entries = content.split('----')

            data_points = []
            for entry in entries:
                if not entry.strip():
                    continue

                # Extract x, y, z, timestamp using regex
                # Pattern: x:value y:value z:value/timestamp
                match = re.match(
                    r'x:([-\d.]+)y:([-\d.]+)z:([-\d.]+)/(\d{4}-\d+-\d+-\d+-\d+-\d+-\d+)',
                    entry.strip()
                )

                if match:
                    x, y, z, timestamp_str = match.groups()

                    # Parse timestamp: 2025-3-27-11-37-31-522
                    try:
                        parts = timestamp_str.split('-')
                        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        hour, minute, second = int(parts[3]), int(parts[4]), int(parts[5])
                        millisecond = int(parts[6])

                        timestamp = datetime(year, month, day, hour, minute, second, millisecond * 1000)

                        data_points.append({
                            'x': float(x),
                            'y': float(y),
                            'z': float(z),
                            'timestamp': timestamp
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
                        continue

            if not data_points:
                logger.warning(f"No valid data points found in {txt_file}")
                return pd.DataFrame(columns=['x', 'y', 'z', 'timestamp'])

            df = pd.DataFrame(data_points)
            logger.info(f"Parsed {len(df)} data points from {txt_file.name}")

            return df

        except Exception as e:
            logger.error(f"Failed to parse {txt_file}: {e}", exc_info=True)
            return pd.DataFrame(columns=['x', 'y', 'z', 'timestamp'])

    def _generate_subject_id(self, group: str, hospital_id: Optional[str], timestamp: str,
                               used_ids: set) -> str:
        """
        生成唯一Subject ID (防止hospital_id重复)

        策略:
        1. 如果有hospital_id: {group}_v2_{hospital_id}
        2. 如果hospital_id重复: {group}_v2_{hospital_id}_{timestamp_hash}
        3. 如果无hospital_id: {group}_v2_{timestamp_hash}

        Args:
            group: 组名(control/mci/ad)
            hospital_id: 医院ID(可选)
            timestamp: session时间戳(必需)
            used_ids: 已使用的subject_id集合

        Returns:
            唯一subject_id

        Examples:
            有hospital_id: control_v2_000001
            hospital_id重复: control_v2_001_a3f9d2e1
            无hospital_id: control_v2_a3f9d2e1 (timestamp hash)
        """
        import hashlib

        if hospital_id and hospital_id not in ['unknown', '', 'nan', 'None']:
            # 有hospital_id,先尝试使用它
            candidate_id = f"{group}_v2_{hospital_id}"

            # 如果ID已被使用,说明hospital_id重复,添加timestamp hash后缀
            if candidate_id in used_ids:
                ts_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
                return f"{group}_v2_{hospital_id}_{ts_hash}"
            else:
                return candidate_id
        else:
            # 无hospital_id,使用timestamp的MD5 hash前8位
            ts_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
            return f"{group}_v2_{ts_hash}"

    def load_v2_data(self) -> Dict[str, Dict]:
        """
        加载所有v2数据

        Returns:
            {
                subject_id: {
                    'group': group,
                    'hospital_id': hospital_id,
                    'data_version': 'v2',
                    'tasks': {
                        'q1': q1_dataframe,
                        'q2': q2_dataframe,
                        ...
                    },
                    'timestamp': session_timestamp
                }
            }
        """
        if not self.data_index_file.exists():
            logger.error(f"Data index file not found: {self.data_index_file}")
            return {}

        # Load data index
        with open(self.data_index_file, 'r', encoding='utf-8') as f:
            data_index = json.load(f)

        logger.info(f"Loaded {len(data_index)} sessions from data index")

        # Process sessions
        all_subjects = {}
        used_ids = set()  # 跟踪已使用的subject_id,防止重复
        skipped = 0

        for session_timestamp, session_data in data_index.items():
            raw_group = session_data.get('group')
            hospital_id = session_data.get('hospital_id')  # 可以为None

            # ✅ 新逻辑: 只要有group就处理(hospital_id可选)
            if not raw_group:
                skipped += 1
                logger.debug(f"Skipped session {session_timestamp}: missing group")
                continue

            # Normalize group name
            group = self._normalize_group_name(raw_group)
            if not group:
                skipped += 1
                logger.debug(f"Skipped session {session_timestamp}: unrecognized group '{raw_group}'")
                continue

            # Generate subject_id (hospital_id可选,使用timestamp作为后备,防止重复)
            subject_id = self._generate_subject_id(group, hospital_id, session_timestamp, used_ids)
            used_ids.add(subject_id)

            # Initialize subject if not exists
            if subject_id not in all_subjects:
                all_subjects[subject_id] = {
                    'group': group,
                    'hospital_id': hospital_id,
                    'data_version': 'v2',
                    'tasks': {},
                    'sessions': []
                }

            # Parse levels
            levels = session_data.get('levels', {})
            session_dir = self.v2_data_dir / session_timestamp

            for level_num, level_info in levels.items():
                if level_num not in self.level_task_mapping:
                    continue

                task_id = self.level_task_mapping[level_num]
                txt_file = level_info.get('txt_file')

                if not txt_file:
                    continue

                txt_path = session_dir / txt_file
                if not txt_path.exists():
                    logger.warning(f"TXT file not found: {txt_path}")
                    continue

                # Parse txt file
                df = self._parse_v2_txt_file(txt_path)

                if len(df) > 0:
                    # Store task data (use first session for each task)
                    if task_id not in all_subjects[subject_id]['tasks']:
                        all_subjects[subject_id]['tasks'][task_id] = df

            # Record session
            all_subjects[subject_id]['sessions'].append(session_timestamp)

        # ✅ Module00数据质量控制: 过滤掉不完整的受试者(缺少q1-q5任意任务)
        required_tasks = {'q1', 'q2', 'q3', 'q4', 'q5'}
        complete_subjects = {}
        incomplete_count = 0

        for subject_id, subject_info in all_subjects.items():
            available_tasks = set(subject_info['tasks'].keys())
            missing_tasks = required_tasks - available_tasks

            if not missing_tasks:
                # 完整数据,保留
                complete_subjects[subject_id] = subject_info
            else:
                # 不完整数据,过滤掉
                incomplete_count += 1
                logger.warning(
                    f"Filtered incomplete subject {subject_id}: "
                    f"missing tasks {missing_tasks}"
                )

        logger.info(
            f"Loaded {len(complete_subjects)} complete subjects "
            f"(filtered {incomplete_count} incomplete), "
            f"skipped {skipped} invalid sessions"
        )

        return complete_subjects

    def save_to_csv(self, subjects_data: Dict[str, Dict]) -> Dict:
        """
        保存数据为CSV文件

        Args:
            subjects_data: load_v2_data()返回的数据

        Returns:
            {
                'success': bool,
                'imported': int,
                'failed': int,
                'details': [...]
            }
        """
        result = {
            'success': True,
            'imported': 0,
            'failed': 0,
            'details': []
        }

        for subject_id, subject_info in subjects_data.items():
            group = subject_info['group']
            tasks = subject_info['tasks']

            # Create group directory
            group_dir = self.output_dir / group
            group_dir.mkdir(parents=True, exist_ok=True)

            # Save each task
            for task_id, df in tasks.items():
                csv_filename = f"{subject_id}_{task_id}.csv"
                csv_path = group_dir / csv_filename

                try:
                    # Save with proper format
                    df.to_csv(csv_path, index=False)
                    result['imported'] += 1
                    result['details'].append({
                        'status': 'imported',
                        'subject_id': subject_id,
                        'task': task_id,
                        'file': str(csv_path),
                        'rows': len(df)
                    })
                    logger.info(f"Saved {csv_filename}: {len(df)} rows")

                except Exception as e:
                    result['failed'] += 1
                    result['details'].append({
                        'status': 'failed',
                        'subject_id': subject_id,
                        'task': task_id,
                        'error': str(e)
                    })
                    logger.error(f"Failed to save {csv_filename}: {e}")

        if result['failed'] > 0:
            result['success'] = False

        return result
