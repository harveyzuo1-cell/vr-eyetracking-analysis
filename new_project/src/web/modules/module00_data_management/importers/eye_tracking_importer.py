"""
新版眼动数据导入器
导入 eye_tracking_data/ 目录中的新版数据(v2)
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from converter import EyeTrackingDataConverter
from metadata_manager import MetadataManager


# 组别映射 - 扩展支持多种中文表述
GROUP_MAPPING = {
    # 标准命名
    "对照组": "control",
    "轻度认知障碍组": "mci",
    "阿尔兹海默症组": "ad",

    # 简称/变体
    "MCI": "mci",
    "阿尔兹海默": "ad",
    "阿尔茨海默症组": "ad",
    "阿尔茨海默": "ad",

    # Custom分组
    "custom": "control",  # custom映射到control

    # 其他未知分组默认为control (在代码中处理)
}


class EyeTrackingDataImporter:
    """新版眼动数据导入器 (eye_tracking_data/)"""

    def __init__(self, base_dir: str = None):
        """
        初始化新版数据导入器

        Args:
            base_dir: 项目基础目录，默认自动检测
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # 自动检测项目根目录
            current = Path(__file__).parent
            while current.name != "new_project" and current.parent != current:
                current = current.parent
            self.base_dir = current.parent if current.name != "new_project" else current.parent

        # 新版数据源目录
        self.source_dir = self.base_dir / "eye_tracking_data"
        self.data_index_path = self.source_dir / "data_index.json"

        # 新项目输出目录
        self.target_base_dir = self.base_dir / "new_project" / "data" / "01_raw"

        # 工具实例
        self.converter = EyeTrackingDataConverter()
        self.metadata_manager = MetadataManager(
            str(self.base_dir / "new_project" / "data" / "01_raw" / "clinical")
        )

    def load_data_index(self) -> Dict:
        """
        加载 data_index.json

        Returns:
            {
                "2025-3-27-11-37-22": {
                    "timestamp": "2025-3-27-11-37-22",
                    "patient_name": "黄鹤鸣",
                    "hospital_id": "000000",
                    "group": "对照组",
                    "levels": {...}
                },
                ...
            }
        """
        if not self.data_index_path.exists():
            raise FileNotFoundError(f"data_index.json not found: {self.data_index_path}")

        with open(self.data_index_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def scan_new_data(self) -> Dict:
        """
        扫描新版数据目录

        Returns:
            {
                "total_dirs": 101,
                "indexed_entries": 94,
                "valid_entries": [
                    {
                        "timestamp": "2025-3-27-11-37-22",
                        "patient_name": "黄鹤鸣",
                        "hospital_id": "000000",
                        "group": "对照组",
                        "group_code": "control",
                        "subject_id": "control_000000",
                        "data_version": "v2",
                        "roi_layout": "v2",
                        "source_type": "eye_tracking",
                        "files_complete": True
                    },
                    ...
                ],
                "incomplete_entries": []
            }
        """
        # 加载data_index.json
        data_index = self.load_data_index()

        # 统计目录数
        timestamp_dirs = list(self.source_dir.glob("2025-*"))
        total_dirs = len(timestamp_dirs)

        valid_entries = []
        incomplete_entries = []

        for timestamp, metadata in data_index.items():
            timestamp_dir = self.source_dir / timestamp

            # 检查目录是否存在
            if not timestamp_dir.exists():
                incomplete_entries.append({
                    "timestamp": timestamp,
                    "error": "Directory not found"
                })
                continue

            # 检查文件完整性 (level_1.txt ~ level_5.txt)
            required_files = [f"level_{i}.txt" for i in range(1, 6)]
            files_complete = all((timestamp_dir / f).exists() for f in required_files)

            # 组别映射 - 未知分组默认为control
            group_raw = metadata.get("group")
            group_code = GROUP_MAPPING.get(group_raw, "control")  # 默认control

            # 生成subject_id - 空hospital_id显示为N/A
            hospital_id = metadata.get("hospital_id")
            if not hospital_id or hospital_id == "":
                hospital_id = "N/A"
            subject_id = f"{group_code}_{hospital_id}"

            entry = {
                "timestamp": timestamp,
                "patient_name": metadata.get("patient_name"),
                "hospital_id": hospital_id,
                "group": group_raw,
                "group_code": group_code,
                "subject_id": subject_id,
                "data_version": "v2",
                "roi_layout": "v2",
                "source_type": "eye_tracking",
                "files_complete": files_complete
            }

            # 只加载完整记录，不完整的直接跳过
            if files_complete:
                valid_entries.append(entry)
            else:
                # 记录不完整条目用于统计，但不返回详细信息
                incomplete_entries.append({
                    "timestamp": timestamp,
                    "hospital_id": hospital_id,
                    "error": "Incomplete files"
                })

        return {
            "total_dirs": total_dirs,
            "indexed_entries": len(data_index),
            "valid_entries": valid_entries,
            "incomplete_count": len(incomplete_entries)  # 只返回数量
        }

    def import_single(self, timestamp: str, metadata: Dict = None) -> Dict:
        """
        导入单个时间戳的数据

        Args:
            timestamp: 时间戳目录名，如 "2025-3-27-11-37-22"
            metadata: 元数据字典，如果为None则从data_index.json读取

        Returns:
            {
                "success": True,
                "subject_id": "control_000000",
                "metadata": {...},
                "conversion_stats": {...}
            }
        """
        # 如果没有提供metadata,从data_index读取
        if metadata is None:
            data_index = self.load_data_index()
            if timestamp not in data_index:
                raise KeyError(f"Timestamp not found in data_index.json: {timestamp}")
            metadata = data_index[timestamp]

        timestamp_dir = self.source_dir / timestamp

        if not timestamp_dir.exists():
            raise FileNotFoundError(f"Timestamp directory not found: {timestamp_dir}")

        # 验证文件完整性
        required_files = [f"level_{i}.txt" for i in range(1, 6)]
        if not all((timestamp_dir / f).exists() for f in required_files):
            raise ValueError(f"Incomplete data for {timestamp}: missing level files")

        # 组别映射
        group_raw = metadata.get("group", "custom")
        group_code = GROUP_MAPPING.get(group_raw, "custom")

        # 生成subject_id
        hospital_id = metadata.get("hospital_id", "unknown")
        subject_id = f"{group_code}_{hospital_id}"

        # 输出目录
        output_dir = self.target_base_dir / group_code
        output_dir.mkdir(parents=True, exist_ok=True)

        # 转换5个任务
        conversion_stats = self.converter.convert_subject_all_tasks(
            source_dir=timestamp_dir,
            output_dir=output_dir,
            subject_id=subject_id,
            task_count=5
        )

        if not conversion_stats["success"]:
            raise RuntimeError(f"Failed to convert data for {subject_id}")

        # 生成元数据
        subject_metadata = {
            "subject_id": subject_id,
            "patient_name": metadata.get("patient_name"),
            "hospital_id": hospital_id,
            "group": group_code,
            "data_version": "v2",
            "roi_layout": "v2",
            "source_type": "eye_tracking",
            "source_timestamp": timestamp,
            "import_date": datetime.now().isoformat(),
            "tasks_available": conversion_stats["converted_tasks"],
            "has_mmse": False,
            "mmse_scores": None
        }

        # 保存元数据
        self.metadata_manager.save_subject_metadata(subject_metadata)

        return {
            "success": True,
            "subject_id": subject_id,
            "metadata": subject_metadata,
            "conversion_stats": conversion_stats
        }

    def import_all_new(self, overwrite: bool = False) -> Dict:
        """
        批量导入所有新数据

        Args:
            overwrite: 是否覆盖已存在数据

        Returns:
            {
                "success": True,
                "total": 94,
                "imported": 94,
                "skipped": 0,
                "failed": 0,
                "imported_subjects": [...],
                "imported_timestamps": [...],
                "failed_entries": [...]
            }
        """
        # 扫描数据
        scan_result = self.scan_new_data()
        valid_entries = scan_result["valid_entries"]

        # 如果不覆盖，获取已导入列表
        already_imported_timestamps = set()
        if not overwrite:
            already_imported_timestamps = set(
                self.metadata_manager.get_imported_timestamps()
            )

        imported_subjects = []
        imported_timestamps = []
        failed_entries = []
        skipped_count = 0

        for entry in valid_entries:
            timestamp = entry["timestamp"]

            # 检查是否已导入
            if not overwrite and timestamp in already_imported_timestamps:
                skipped_count += 1
                continue

            try:
                # 加载元数据
                data_index = self.load_data_index()
                metadata = data_index.get(timestamp)

                if not metadata:
                    failed_entries.append({
                        "timestamp": timestamp,
                        "error": "Metadata not found in data_index.json"
                    })
                    continue

                # 导入
                result = self.import_single(timestamp, metadata)
                imported_subjects.append(result["subject_id"])
                imported_timestamps.append(timestamp)

            except Exception as e:
                failed_entries.append({
                    "timestamp": timestamp,
                    "subject_id": entry.get("subject_id"),
                    "error": str(e)
                })

        # 记录导入历史
        if imported_timestamps:
            self.metadata_manager.add_import_log(
                source="eye_tracking",
                imported_count=len(imported_timestamps),
                subjects=imported_subjects,
                source_timestamps=imported_timestamps
            )

        return {
            "success": True,
            "total": len(valid_entries),
            "imported": len(imported_subjects),
            "skipped": skipped_count,
            "failed": len(failed_entries),
            "imported_subjects": imported_subjects,
            "imported_timestamps": imported_timestamps,
            "failed_entries": failed_entries
        }

    def get_statistics(self) -> Dict:
        """
        获取新版数据统计

        Returns:
            {
                "total_dirs": 101,
                "indexed_entries": 94,
                "valid_entries": 87,
                "incomplete_entries": 7
            }
        """
        scan_result = self.scan_new_data()

        return {
            "total_dirs": scan_result["total_dirs"],
            "indexed_entries": scan_result["indexed_entries"],
            "valid_entries": len(scan_result["valid_entries"]),
            "incomplete_entries": len(scan_result["incomplete_entries"])
        }


if __name__ == '__main__':
    # 测试代码
    importer = EyeTrackingDataImporter()

    # 扫描数据
    print("=== Scanning Eye Tracking Data ===")
    scan_result = importer.scan_new_data()

    print(f"Total dirs: {scan_result['total_dirs']}")
    print(f"Indexed entries: {scan_result['indexed_entries']}")
    print(f"Valid entries: {len(scan_result['valid_entries'])}")
    print(f"Incomplete entries: {len(scan_result['incomplete_entries'])}")

    # 显示前3个有效条目
    print("\nFirst 3 valid entries:")
    for entry in scan_result['valid_entries'][:3]:
        print(f"  - {entry['subject_id']} ({entry['timestamp']})")
        print(f"    Patient: {entry['patient_name']}, Group: {entry['group']}")

    # 统计信息
    print("\n=== Statistics ===")
    stats = importer.get_statistics()
    print(f"Total dirs: {stats['total_dirs']}")
    print(f"Valid for import: {stats['valid_entries']}")
