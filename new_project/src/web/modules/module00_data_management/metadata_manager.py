"""
元数据管理器
管理subject_metadata.json和import_history.json
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class MetadataManager:
    """元数据管理器"""

    def __init__(self, data_dir: str = "data/01_raw/clinical"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.data_dir / "subject_metadata.json"
        self.history_file = self.data_dir / "import_history.json"

        # 初始化文件
        self._init_files()

    def _init_files(self):
        """初始化元数据文件"""
        if not self.metadata_file.exists():
            self._save_json(self.metadata_file, {})

        if not self.history_file.exists():
            self._save_json(self.history_file, {
                "last_import_time": None,
                "import_logs": []
            })

    def _load_json(self, file_path: Path) -> Dict:
        """加载JSON文件"""
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json(self, file_path: Path, data: Dict):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ========== Subject Metadata管理 ==========

    def load_all_subjects(self) -> Dict:
        """
        加载所有受试者元数据

        Returns:
            {
                "control_legacy_1": {...},
                "control_000000": {...},
                ...
            }
        """
        return self._load_json(self.metadata_file)

    def load_subject_metadata(self, subject_id: str) -> Optional[Dict]:
        """
        加载单个受试者元数据

        Args:
            subject_id: 受试者ID

        Returns:
            元数据字典,不存在返回None
        """
        all_metadata = self.load_all_subjects()
        return all_metadata.get(subject_id)

    def save_subject_metadata(self, metadata: Dict) -> bool:
        """
        保存单个受试者元数据

        Args:
            metadata: {
                "subject_id": "control_000000",
                "group": "control",
                "data_version": "v2",
                ...
            }

        Returns:
            保存是否成功
        """
        subject_id = metadata.get("subject_id")
        if not subject_id:
            raise ValueError("Metadata must contain 'subject_id'")

        # 加载现有数据
        all_metadata = self.load_all_subjects()

        # 更新
        all_metadata[subject_id] = metadata

        # 保存
        self._save_json(self.metadata_file, all_metadata)
        return True

    def batch_save_subjects(self, subjects: List[Dict]) -> Dict:
        """
        批量保存受试者元数据

        Args:
            subjects: 元数据列表

        Returns:
            {
                "success": True,
                "saved_count": 10,
                "failed_count": 0
            }
        """
        all_metadata = self.load_all_subjects()

        saved_count = 0
        failed_count = 0

        for metadata in subjects:
            try:
                subject_id = metadata.get("subject_id")
                if subject_id:
                    all_metadata[subject_id] = metadata
                    saved_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1

        self._save_json(self.metadata_file, all_metadata)

        return {
            "success": True,
            "saved_count": saved_count,
            "failed_count": failed_count
        }

    def delete_subject(self, subject_id: str) -> bool:
        """删除受试者元数据"""
        all_metadata = self.load_all_subjects()

        if subject_id in all_metadata:
            del all_metadata[subject_id]
            self._save_json(self.metadata_file, all_metadata)
            return True

        return False

    def get_subjects_by_version(self, data_version: str) -> List[Dict]:
        """
        按数据版本筛选受试者

        Args:
            data_version: "v1", "v2", or "all"

        Returns:
            受试者列表
        """
        all_subjects = self.load_all_subjects()

        if data_version == "all":
            return list(all_subjects.values())

        return [
            subject for subject in all_subjects.values()
            if subject.get("data_version") == data_version
        ]

    def get_subjects_by_group(self, group: str) -> List[Dict]:
        """按组别筛选受试者"""
        all_subjects = self.load_all_subjects()

        if group == "all":
            return list(all_subjects.values())

        return [
            subject for subject in all_subjects.values()
            if subject.get("group") == group
        ]

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            {
                "total": 159,
                "v1_count": 65,
                "v2_count": 94,
                "by_group": {
                    "control": 52,
                    "mci": 54,
                    "ad": 53
                }
            }
        """
        all_subjects = self.load_all_subjects().values()

        v1_count = sum(1 for s in all_subjects if s.get("data_version") == "v1")
        v2_count = sum(1 for s in all_subjects if s.get("data_version") == "v2")

        by_group = {}
        for subject in all_subjects:
            group = subject.get("group", "unknown")
            by_group[group] = by_group.get(group, 0) + 1

        return {
            "total": len(list(all_subjects)),
            "v1_count": v1_count,
            "v2_count": v2_count,
            "by_group": by_group
        }

    # ========== Import History管理 ==========

    def load_import_history(self) -> Dict:
        """
        加载导入历史

        Returns:
            {
                "last_import_time": "2025-10-02T15:30:00",
                "import_logs": [...]
            }
        """
        return self._load_json(self.history_file)

    def add_import_log(self, source: str, imported_count: int,
                      subjects: List[str] = None,
                      source_timestamps: List[str] = None) -> bool:
        """
        添加导入日志

        Args:
            source: "legacy" or "eye_tracking"
            imported_count: 导入数量
            subjects: 受试者ID列表
            source_timestamps: 源时间戳列表(仅eye_tracking)

        Returns:
            是否成功
        """
        history = self.load_import_history()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "imported_count": imported_count
        }

        if subjects:
            log_entry["subjects"] = subjects

        if source_timestamps:
            log_entry["source_timestamps"] = source_timestamps

        history["import_logs"].append(log_entry)
        history["last_import_time"] = log_entry["timestamp"]

        self._save_json(self.history_file, history)
        return True

    def get_imported_subjects(self) -> List[str]:
        """获取所有已导入的受试者ID列表"""
        history = self.load_import_history()
        imported = []

        for log in history.get("import_logs", []):
            if "subjects" in log:
                imported.extend(log["subjects"])

        return list(set(imported))  # 去重

    def get_imported_timestamps(self) -> List[str]:
        """获取所有已导入的时间戳列表(eye_tracking)"""
        history = self.load_import_history()
        timestamps = []

        for log in history.get("import_logs", []):
            if log.get("source") == "eye_tracking" and "source_timestamps" in log:
                timestamps.extend(log["source_timestamps"])

        return list(set(timestamps))  # 去重

    def clear_history(self) -> bool:
        """清空导入历史(谨慎使用)"""
        self._save_json(self.history_file, {
            "last_import_time": None,
            "import_logs": []
        })
        return True


if __name__ == '__main__':
    # 测试代码
    manager = MetadataManager(data_dir="test_data/clinical")

    # 测试保存元数据
    test_metadata = {
        "subject_id": "control_000000",
        "patient_name": "测试患者",
        "group": "control",
        "data_version": "v2",
        "roi_layout": "v2",
        "source_type": "eye_tracking",
        "import_date": datetime.now().isoformat(),
        "has_mmse": False
    }

    manager.save_subject_metadata(test_metadata)
    print("Saved metadata:", manager.load_subject_metadata("control_000000"))

    # 测试统计
    print("Statistics:", manager.get_statistics())

    # 测试导入历史
    manager.add_import_log("eye_tracking", 1, subjects=["control_000000"])
    print("Import history:", manager.load_import_history())
