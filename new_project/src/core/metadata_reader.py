"""
共享元数据读取器
Shared Metadata Reader

供所有模块读取Module00维护的元数据文件

迁移自: module01_data_visualization (v1.0)
迁移日期: 2025-10-02
版本: v2.0.0
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MetadataReader:
    """
    共享元数据读取器 v2.0

    读取Module00维护的元数据文件：
    - subject_metadata.json: 受试者元数据
    - mmse_scores.json: MMSE评分数据

    所有模块（Module01-10）共享使用此类读取元数据
    """

    VERSION = "2.0.0"

    def __init__(self, clinical_data_dir: Optional[str] = None):
        """
        初始化元数据读取器

        Args:
            clinical_data_dir: 临床数据目录路径
                默认: {project_root}/data/01_raw/clinical
        """
        if clinical_data_dir is None:
            # 自动检测项目根目录
            # src/core/metadata_reader.py -> src/core/ -> src/ -> new_project/
            project_root = Path(__file__).parent.parent.parent
            clinical_data_dir = project_root / "data" / "01_raw" / "clinical"

        self.clinical_data_dir = Path(clinical_data_dir)
        self.subject_metadata_file = self.clinical_data_dir / "subject_metadata.json"
        self.mmse_scores_file = self.clinical_data_dir / "mmse_scores.json"

        # 缓存数据
        self.subject_metadata = {}
        self.mmse_scores = {}

        # 加载元数据
        self._load_metadata()

        logger.info(
            f"MetadataReader v{self.VERSION} initialized: "
            f"{len(self.subject_metadata)} subjects loaded"
        )

    def _load_metadata(self):
        """加载元数据文件"""
        try:
            # 加载subject_metadata.json
            if self.subject_metadata_file.exists():
                with open(self.subject_metadata_file, 'r', encoding='utf-8') as f:
                    self.subject_metadata = json.load(f)
                logger.info(
                    f"Loaded {len(self.subject_metadata)} subjects "
                    f"from subject_metadata.json"
                )
            else:
                logger.warning(
                    f"subject_metadata.json not found: {self.subject_metadata_file}"
                )

            # 加载mmse_scores.json（如果存在）
            if self.mmse_scores_file.exists():
                with open(self.mmse_scores_file, 'r', encoding='utf-8') as f:
                    self.mmse_scores = json.load(f)
                logger.info(f"Loaded MMSE scores for {len(self.mmse_scores)} subjects")
            else:
                logger.info("mmse_scores.json not found, will be created by Module00")

        except Exception as e:
            logger.error(f"Failed to load metadata: {e}", exc_info=True)
            raise

    def reload(self):
        """
        重新加载元数据（当Module00更新数据后调用）

        用途：
        - Module00导入新数据后，其他模块调用此方法刷新缓存
        - 配合数据变更通知机制使用
        """
        self._load_metadata()
        logger.info("MetadataReader reloaded")

    def get_all_subjects(self) -> Dict[str, Dict]:
        """
        获取所有受试者的元数据

        Returns:
            {subject_id: metadata_dict}

        Example:
            {
                "control_legacy_1": {
                    "group": "control",
                    "data_version": "v1",
                    "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
                    ...
                },
                ...
            }
        """
        return self.subject_metadata

    def get_subjects_by_group(self, group: str) -> List[Dict]:
        """
        按组别过滤受试者

        Args:
            group: 组别 (control/mci/ad)

        Returns:
            受试者元数据列表

        Example:
            >>> reader.get_subjects_by_group('control')
            [
                {"subject_id": "control_legacy_1", "group": "control", ...},
                {"subject_id": "control_v2_000001", "group": "control", ...},
                ...
            ]
        """
        subjects = []
        for subject_id, meta in self.subject_metadata.items():
            if meta.get('group') == group:
                # 添加subject_id到元数据中（方便使用）
                meta_with_id = meta.copy()
                meta_with_id['subject_id'] = subject_id
                subjects.append(meta_with_id)

        return subjects

    def get_subjects_by_version(self, data_version: str) -> List[Dict]:
        """
        按数据版本过滤受试者

        Args:
            data_version: 数据版本 (v1/v2)

        Returns:
            受试者元数据列表

        Example:
            >>> reader.get_subjects_by_version('v2')
            [
                {"subject_id": "control_v2_000001", "data_version": "v2", ...},
                ...
            ]
        """
        subjects = []
        for subject_id, meta in self.subject_metadata.items():
            if meta.get('data_version') == data_version:
                meta_with_id = meta.copy()
                meta_with_id['subject_id'] = subject_id
                subjects.append(meta_with_id)

        return subjects

    def get_subject_info(self, subject_id: str) -> Optional[Dict]:
        """
        获取单个受试者的元数据

        Args:
            subject_id: 受试者ID

        Returns:
            元数据字典，如果不存在返回None

        Example:
            >>> reader.get_subject_info('control_legacy_1')
            {
                "group": "control",
                "data_version": "v1",
                "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
                "has_mmse": True,
                ...
            }
        """
        return self.subject_metadata.get(subject_id)

    def get_tasks_available(self, subject_id: str) -> List[str]:
        """
        获取受试者的可用任务列表

        Args:
            subject_id: 受试者ID

        Returns:
            任务列表，例如 ['q1', 'q2', 'q3', 'q4', 'q5']

        Example:
            >>> reader.get_tasks_available('control_legacy_1')
            ['q1', 'q2', 'q3', 'q4', 'q5']
        """
        meta = self.get_subject_info(subject_id)
        if meta:
            return meta.get('tasks_available', [])
        return []

    def has_mmse_score(self, subject_id: str) -> bool:
        """
        检查受试者是否有MMSE评分

        Args:
            subject_id: 受试者ID

        Returns:
            True如果有MMSE评分

        Example:
            >>> reader.has_mmse_score('control_legacy_1')
            True
        """
        # 优先从mmse_scores.json检查
        if subject_id in self.mmse_scores and self.mmse_scores[subject_id] is not None:
            return True

        # 降级：从subject_metadata.json检查
        meta = self.get_subject_info(subject_id)
        if meta:
            return meta.get('has_mmse', False)

        return False

    def get_mmse_score(self, subject_id: str) -> Optional[Dict]:
        """
        获取MMSE评分

        Args:
            subject_id: 受试者ID

        Returns:
            MMSE评分字典，如果不存在返回None

        Example:
            >>> reader.get_mmse_score('control_legacy_1')
            {
                "total_score": 28,
                "q1_year": 1,
                "q1_season": 1,
                ...
            }
        """
        # 优先从mmse_scores.json读取
        if subject_id in self.mmse_scores:
            return self.mmse_scores[subject_id]

        # 降级：从subject_metadata.json读取（旧数据可能存储在这里）
        meta = self.get_subject_info(subject_id)
        if meta and meta.get('has_mmse'):
            return meta.get('mmse_scores')

        return None

    def get_group_statistics(self) -> Dict[str, Any]:
        """
        获取组别统计信息

        Returns:
            {
                "control": {"total": 54, "v1": 22, "v2": 32, "has_mmse": 20},
                "mci": {"total": 30, "v1": 22, "v2": 8, "has_mmse": 20},
                "ad": {"total": 29, "v1": 21, "v2": 8, "has_mmse": 20}
            }

        Example:
            >>> stats = reader.get_group_statistics()
            >>> stats['control']['total']
            54
            >>> stats['control']['v2']
            32
        """
        stats = {
            "control": {"total": 0, "v1": 0, "v2": 0, "has_mmse": 0},
            "mci": {"total": 0, "v1": 0, "v2": 0, "has_mmse": 0},
            "ad": {"total": 0, "v1": 0, "v2": 0, "has_mmse": 0}
        }

        for subject_id, meta in self.subject_metadata.items():
            group = meta.get('group')
            if group in stats:
                stats[group]["total"] += 1

                # 数据版本统计
                data_version = meta.get('data_version', 'v1')
                if data_version == 'v1':
                    stats[group]["v1"] += 1
                else:
                    stats[group]["v2"] += 1

                # MMSE统计
                if self.has_mmse_score(subject_id):
                    stats[group]["has_mmse"] += 1

        return stats
