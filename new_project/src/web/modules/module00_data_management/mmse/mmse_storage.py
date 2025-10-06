"""
MMSE存储管理器

负责mmse_scores.json文件的读写和管理
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MMSEStorage:
    """MMSE存储管理器"""

    def __init__(self, clinical_data_dir: Optional[str] = None):
        """
        初始化MMSE存储管理器

        Args:
            clinical_data_dir: 临床数据目录,默认为data/01_raw/clinical/
        """
        if clinical_data_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent.parent.parent
            clinical_data_dir = project_root / "data" / "01_raw" / "clinical"

        self.clinical_data_dir = Path(clinical_data_dir)
        self.mmse_scores_file = self.clinical_data_dir / "mmse_scores.json"
        self.subject_metadata_file = self.clinical_data_dir / "subject_metadata.json"

        # 确保目录存在
        self.clinical_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"MMSEStorage initialized with file: {self.mmse_scores_file}")

    def load_mmse_scores(self) -> Dict[str, Dict]:
        """
        加载MMSE评分数据

        Returns:
            {
                "control_legacy_1": {
                    "subject_id": "control_legacy_1",
                    "group": "control",
                    "data_version": "v1",
                    "q1_year": 1,
                    "total_score": 21,
                    "last_updated": "2025-10-02T10:40:00"
                },
                ...
            }
        """
        if not self.mmse_scores_file.exists():
            logger.info("mmse_scores.json not found, returning empty dict")
            return {}

        try:
            with open(self.mmse_scores_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} MMSE records from {self.mmse_scores_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load mmse_scores.json: {e}", exc_info=True)
            return {}

    def save_mmse_scores(self, mmse_data: Dict[str, Dict]) -> bool:
        """
        保存MMSE评分数据

        Args:
            mmse_data: MMSE数据字典

        Returns:
            是否保存成功
        """
        try:
            # 添加保存时间戳
            for subject_id, record in mmse_data.items():
                if 'last_updated' not in record:
                    record['last_updated'] = datetime.now().isoformat()

            # 保存到文件
            with open(self.mmse_scores_file, 'w', encoding='utf-8') as f:
                json.dump(mmse_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(mmse_data)} MMSE records to {self.mmse_scores_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save mmse_scores.json: {e}", exc_info=True)
            return False

    def update_subject_metadata(self, subject_id: str, mmse_scores: Dict) -> bool:
        """
        更新subject_metadata.json中的MMSE信息

        Args:
            subject_id: 受试者ID
            mmse_scores: MMSE评分数据

        Returns:
            是否更新成功
        """
        try:
            # 读取subject_metadata.json
            if not self.subject_metadata_file.exists():
                logger.error("subject_metadata.json not found")
                return False

            with open(self.subject_metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 更新指定受试者的MMSE信息
            if subject_id in metadata:
                metadata[subject_id]['has_mmse'] = True
                metadata[subject_id]['mmse_scores'] = {
                    'total_score': mmse_scores.get('total_score'),
                    'last_updated': mmse_scores.get('last_updated')
                }

                # 保存回文件
                with open(self.subject_metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

                logger.info(f"Updated MMSE metadata for {subject_id}")
                return True
            else:
                logger.warning(f"Subject {subject_id} not found in metadata")
                return False

        except Exception as e:
            logger.error(f"Failed to update subject_metadata: {e}", exc_info=True)
            return False

    def batch_import_mmse(self, mmse_data: Dict[str, Dict]) -> Dict:
        """
        批量导入MMSE数据

        Args:
            mmse_data: MMSE数据字典

        Returns:
            {
                "success": True,
                "imported": 60,
                "skipped": 5,
                "failed": 0,
                "details": [...]
            }
        """
        result = {
            'success': True,
            'imported': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }

        # 加载现有MMSE数据
        existing_mmse = self.load_mmse_scores()

        # 逐个导入
        for subject_id, mmse_record in mmse_data.items():
            try:
                # 检查是否已存在
                if subject_id in existing_mmse:
                    logger.info(f"MMSE for {subject_id} already exists, skipping")
                    result['skipped'] += 1
                    result['details'].append({
                        'subject_id': subject_id,
                        'status': 'skipped',
                        'reason': 'already_exists'
                    })
                    continue

                # 添加到existing_mmse
                existing_mmse[subject_id] = mmse_record
                result['imported'] += 1
                result['details'].append({
                    'subject_id': subject_id,
                    'status': 'imported'
                })

            except Exception as e:
                logger.error(f"Failed to import MMSE for {subject_id}: {e}")
                result['failed'] += 1
                result['details'].append({
                    'subject_id': subject_id,
                    'status': 'failed',
                    'error': str(e)
                })

        # 保存更新后的MMSE数据
        if result['imported'] > 0:
            if not self.save_mmse_scores(existing_mmse):
                result['success'] = False
                return result

            # 批量更新subject_metadata.json
            for subject_id in existing_mmse.keys():
                self.update_subject_metadata(subject_id, existing_mmse[subject_id])

        return result

    def get_mmse_for_subject(self, subject_id: str) -> Optional[Dict]:
        """
        获取指定受试者的MMSE数据

        Args:
            subject_id: 受试者ID

        Returns:
            MMSE数据,如果不存在返回None
        """
        mmse_data = self.load_mmse_scores()
        return mmse_data.get(subject_id)

    def delete_mmse_for_subject(self, subject_id: str) -> bool:
        """
        删除指定受试者的MMSE数据

        Args:
            subject_id: 受试者ID

        Returns:
            是否删除成功
        """
        try:
            mmse_data = self.load_mmse_scores()

            if subject_id not in mmse_data:
                logger.warning(f"MMSE for {subject_id} not found")
                return False

            # 删除记录
            del mmse_data[subject_id]

            # 保存
            if not self.save_mmse_scores(mmse_data):
                return False

            # 更新subject_metadata
            try:
                with open(self.subject_metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                if subject_id in metadata:
                    metadata[subject_id]['has_mmse'] = False
                    metadata[subject_id]['mmse_scores'] = None

                    with open(self.subject_metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"Failed to update metadata: {e}")

            logger.info(f"Deleted MMSE for {subject_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete MMSE: {e}", exc_info=True)
            return False

    def get_statistics(self) -> Dict:
        """
        获取MMSE数据统计信息

        Returns:
            {
                "total": 60,
                "by_group": {"control": 20, "mci": 20, "ad": 20},
                "by_version": {"v1": 60, "v2": 0}
            }
        """
        mmse_data = self.load_mmse_scores()

        by_group = {'control': 0, 'mci': 0, 'ad': 0}
        by_version = {'v1': 0, 'v2': 0}

        for subject_id, record in mmse_data.items():
            group = record.get('group', 'unknown')
            version = record.get('data_version', 'v1')

            if group in by_group:
                by_group[group] += 1

            if version in by_version:
                by_version[version] += 1

        return {
            'total': len(mmse_data),
            'by_group': by_group,
            'by_version': by_version
        }
