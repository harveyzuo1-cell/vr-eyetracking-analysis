"""
V1格式眼动数据管理器

负责V1版本眼动数据的扫描、导入和管理
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class V1DataManager:
    """V1格式眼动数据管理器"""

    def __init__(self, data_dir: Path):
        """
        初始化V1数据管理器

        Args:
            data_dir: 数据根目录
        """
        self.data_dir = Path(data_dir)
        self.v1_scan_dir = self.data_dir / 'v1_raw_data'  # V1原始数据目录

        logger.info(f"初始化V1数据管理器: {self.v1_scan_dir}")

    def scan_v1_subjects(self) -> List[Dict]:
        """
        扫描Module01中已导入的V1受试者数据

        从01_raw/clinical/subject_metadata.json读取所有data_version='v1'的受试者

        Returns:
            [
                {
                    'subject_id': 'control_legacy_1',
                    'group': 'control',
                    'name': '张三',
                    'hospital_id': 'H001',
                    'age': 65,
                    'gender': 'male',
                    'education_level': 'undergraduate',
                    'timestamp': '2024-01-01 10:30:00',
                    'data_version': 'v1',
                    'has_mmse': True,
                    'mmse_score': 28,
                    'status': 'available'
                },
                ...
            ]
        """
        logger.info("开始扫描Module01中的V1受试者数据...")

        # 从Module01的clinical目录读取subject_metadata.json
        clinical_dir = self.data_dir / '01_raw' / 'clinical'
        metadata_file = clinical_dir / 'subject_metadata.json'

        if not metadata_file.exists():
            logger.warning(f"subject_metadata.json不存在: {metadata_file}")
            return []

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                all_subjects = json.load(f)
        except Exception as e:
            logger.error(f"读取subject_metadata.json失败: {e}")
            return []

        v1_subjects = []

        # 遍历所有受试者，筛选data_version='v1'的
        for subject_id, subject_data in all_subjects.items():
            # 只返回data_version='v1'的受试者
            if subject_data.get('data_version') != 'v1':
                continue

            try:
                # 提取demographics信息
                demographics = subject_data.get('demographics', {})

                # 提取MMSE信息
                has_mmse = subject_data.get('mmse') is not None
                mmse_score = None
                if has_mmse:
                    mmse_data = subject_data.get('mmse', {})
                    mmse_score = mmse_data.get('total_score')

                v1_subjects.append({
                    'subject_id': subject_id,
                    'group': subject_data.get('group', 'unknown'),
                    'name': demographics.get('name', 'N/A'),
                    'hospital_id': demographics.get('hospital_id', 'N/A'),
                    'age': demographics.get('age', 'N/A'),
                    'gender': demographics.get('gender', 'N/A'),
                    'education_level': demographics.get('education_level', 'N/A'),
                    'timestamp': subject_data.get('created_at', 'N/A'),
                    'data_version': 'v1',
                    'has_mmse': has_mmse,
                    'mmse_score': mmse_score,
                    'status': 'available',  # 可导入状态
                    'task_count': subject_data.get('task_count', 0)
                })

            except Exception as e:
                logger.error(f"处理受试者数据失败 {subject_id}: {str(e)}")
                continue

        logger.info(f"扫描完成，找到 {len(v1_subjects)} 个V1受试者")
        return v1_subjects

    def _read_v1_metadata(self, subject_dir: Path) -> Dict:
        """
        读取V1受试者的metadata.json（如果存在）

        Args:
            subject_dir: 受试者目录

        Returns:
            元数据字典
        """
        metadata_file = subject_dir / 'metadata.json'

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取metadata失败: {metadata_file}, {e}")

        return {}

    def _get_earliest_file_time(self, files: List[Path]) -> str:
        """
        获取文件列表中最早的修改时间

        Args:
            files: 文件列表

        Returns:
            ISO格式时间字符串
        """
        if not files:
            return datetime.now().isoformat()

        earliest_time = min(f.stat().st_mtime for f in files)
        return datetime.fromtimestamp(earliest_time).strftime('%Y-%m-%d %H:%M:%S')

    def import_v1_subject(
        self,
        subject_id: str,
        demographics: Dict,
        subject_manager
    ) -> Dict:
        """
        导入V1受试者到subject_manager

        Args:
            subject_id: V1受试者ID
            demographics: 人口学信息 {'age': 65, 'gender': 'male', 'education_level': 'undergraduate'}
            subject_manager: SubjectManager实例

        Returns:
            创建的受试者信息
        """
        logger.info(f"开始导入V1受试者: {subject_id}")

        # 从扫描结果获取V1受试者
        v1_subjects = self.scan_v1_subjects()
        v1_subject = next((s for s in v1_subjects if s['subject_id'] == subject_id), None)

        if not v1_subject:
            raise ValueError(f"V1受试者不存在: {subject_id}")

        # 合并metadata中的信息到demographics
        full_demographics = {
            'name': v1_subject.get('name', ''),
            'hospital_id': v1_subject.get('hospital_id', ''),
            **demographics  # 用户提供的信息优先
        }

        # 创建受试者记录
        subject = subject_manager.create_subject(
            subject_id=subject_id,
            group=v1_subject['group'],
            demographics=full_demographics,
            mmse=None,  # V1初始无MMSE
            data_version='v1',
            metadata={
                'timestamp': v1_subject['timestamp'],
                'data_path': v1_subject['data_path'],
                'file_count': v1_subject['file_count'],
                'v1_import_date': datetime.now().isoformat()
            }
        )

        logger.info(f"V1受试者导入成功: {subject_id}")
        return subject

    def batch_import_v1_subjects(
        self,
        subjects_data: List[Dict],
        subject_manager
    ) -> Dict:
        """
        批量导入V1受试者

        Args:
            subjects_data: [
                {
                    'subject_id': 'control_001',
                    'demographics': {'age': 65, 'gender': 'male', ...}
                },
                ...
            ]
            subject_manager: SubjectManager实例

        Returns:
            {
                'imported': 10,
                'failed': 0,
                'errors': []
            }
        """
        logger.info(f"开始批量导入V1受试者，共 {len(subjects_data)} 个")

        results = {
            'imported': 0,
            'failed': 0,
            'errors': []
        }

        for item in subjects_data:
            subject_id = item['subject_id']

            try:
                self.import_v1_subject(
                    subject_id=subject_id,
                    demographics=item['demographics'],
                    subject_manager=subject_manager
                )
                results['imported'] += 1

            except Exception as e:
                logger.error(f"导入V1受试者失败: {subject_id}, {e}")
                results['failed'] += 1
                results['errors'].append({
                    'subject_id': subject_id,
                    'error': str(e)
                })

        logger.info(f"V1批量导入完成: 成功 {results['imported']}, 失败 {results['failed']}")
        return results

    def get_v1_subject_detail(self, subject_id: str) -> Optional[Dict]:
        """
        获取V1受试者详细信息（包括数据文件列表）

        Args:
            subject_id: 受试者ID

        Returns:
            详细信息字典，不存在返回None
        """
        v1_subjects = self.scan_v1_subjects()
        v1_subject = next((s for s in v1_subjects if s['subject_id'] == subject_id), None)

        if not v1_subject:
            return None

        # 添加数据文件列表
        data_path = Path(v1_subject['data_path'])
        v1_subject['files'] = [
            {
                'name': f.name,
                'size': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in data_path.iterdir() if f.is_file()
        ]

        return v1_subject
