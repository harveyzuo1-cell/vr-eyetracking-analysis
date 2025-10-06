"""
旧版数据导入器
导入 data/*_raw/ 目录中的旧版数据(v1)
"""
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from converter import EyeTrackingDataConverter
from metadata_manager import MetadataManager


class LegacyDataImporter:
    """旧版数据导入器 (data/*_raw/)"""

    def __init__(self, base_dir: str = None):
        """
        初始化旧版数据导入器

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

        # 旧版数据源目录
        self.source_dirs = {
            "control": self.base_dir / "data" / "control_raw",
            "mci": self.base_dir / "data" / "mci_raw",
            "ad": self.base_dir / "data" / "ad_raw"
        }

        # 新项目输出目录
        self.target_base_dir = self.base_dir / "new_project" / "data" / "01_raw"

        # 工具实例
        self.converter = EyeTrackingDataConverter()
        self.metadata_manager = MetadataManager(
            str(self.base_dir / "new_project" / "data" / "01_raw" / "clinical")
        )

    def scan_legacy_data(self) -> Dict:
        """
        扫描所有旧版数据目录

        Returns:
            {
                "control": [
                    {
                        "subject_dir": Path("data/control_raw/control_group_1"),
                        "subject_id": "control_legacy_1",
                        "group": "control",
                        "data_version": "v1",
                        "roi_layout": "v1",
                        "source_type": "legacy",
                        "files_complete": True
                    },
                    ...
                ],
                "mci": [...],
                "ad": [...]
            }
        """
        result = {}

        for group, source_dir in self.source_dirs.items():
            if not source_dir.exists():
                result[group] = []
                continue

            # 查找所有 {group}_group_X 目录
            pattern = f"{group}_group_*"
            subject_dirs = sorted(source_dir.glob(pattern))

            group_subjects = []

            for subj_dir in subject_dirs:
                # 提取组号
                parts = subj_dir.name.split('_')
                if len(parts) >= 3:
                    group_number = parts[-1]
                else:
                    continue

                # 生成subject_id
                subject_id = f"{group}_legacy_{group_number}"

                # 检查文件完整性
                required_files = ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
                files_complete = all((subj_dir / f).exists() for f in required_files)

                group_subjects.append({
                    "subject_dir": subj_dir,
                    "subject_id": subject_id,
                    "group": group,
                    "data_version": "v1",
                    "roi_layout": "v1",
                    "source_type": "legacy",
                    "files_complete": files_complete
                })

            result[group] = group_subjects

        return result

    def import_single_subject(self, subject_info: Dict) -> Dict:
        """
        导入单个旧版受试者数据

        Args:
            subject_info: 从scan_legacy_data返回的受试者信息

        Returns:
            {
                "success": True,
                "subject_id": "control_legacy_1",
                "metadata": {...},
                "conversion_stats": {...}
            }
        """
        subject_dir = subject_info["subject_dir"]
        subject_id = subject_info["subject_id"]
        group = subject_info["group"]

        # 验证文件完整性
        required_files = ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
        if not all((subject_dir / f).exists() for f in required_files):
            raise ValueError(f"Incomplete data for {subject_id}: missing files")

        # 输出目录
        output_dir = self.target_base_dir / group
        output_dir.mkdir(parents=True, exist_ok=True)

        # 转换5个任务
        conversion_stats = self.converter.convert_subject_all_tasks(
            source_dir=subject_dir,
            output_dir=output_dir,
            subject_id=subject_id,
            task_count=5
        )

        if not conversion_stats["success"]:
            raise RuntimeError(f"Failed to convert data for {subject_id}")

        # 生成元数据
        metadata = {
            "subject_id": subject_id,
            "group": group,
            "data_version": "v1",
            "roi_layout": "v1",
            "source_type": "legacy",
            "source_path": str(subject_dir),
            "import_date": datetime.now().isoformat(),
            "tasks_available": conversion_stats["converted_tasks"],
            "has_mmse": False,
            "mmse_scores": None
        }

        # 保存元数据
        self.metadata_manager.save_subject_metadata(metadata)

        return {
            "success": True,
            "subject_id": subject_id,
            "metadata": metadata,
            "conversion_stats": conversion_stats
        }

    def import_all(self, overwrite: bool = False) -> Dict:
        """
        批量导入所有旧版数据

        Args:
            overwrite: 是否覆盖已存在数据

        Returns:
            {
                "success": True,
                "total": 65,
                "imported": 65,
                "skipped": 0,
                "failed": 0,
                "by_group": {
                    "control": 22,
                    "mci": 22,
                    "ad": 21
                },
                "imported_subjects": [...],
                "failed_subjects": [...]
            }
        """
        # 扫描所有数据
        scan_result = self.scan_legacy_data()

        # 如果不覆盖，获取已导入列表
        already_imported = set()
        if not overwrite:
            already_imported = set(self.metadata_manager.get_imported_subjects())

        imported_subjects = []
        failed_subjects = []
        skipped_count = 0

        by_group = {"control": 0, "mci": 0, "ad": 0}

        for group, subjects in scan_result.items():
            for subj_info in subjects:
                subject_id = subj_info["subject_id"]

                # 检查是否已导入
                if not overwrite and subject_id in already_imported:
                    skipped_count += 1
                    continue

                # 检查文件完整性
                if not subj_info["files_complete"]:
                    failed_subjects.append({
                        "subject_id": subject_id,
                        "error": "Incomplete data files"
                    })
                    continue

                try:
                    # 导入
                    result = self.import_single_subject(subj_info)
                    imported_subjects.append(result["subject_id"])
                    by_group[group] += 1
                except Exception as e:
                    failed_subjects.append({
                        "subject_id": subject_id,
                        "error": str(e)
                    })

        # 记录导入历史
        if imported_subjects:
            self.metadata_manager.add_import_log(
                source="legacy",
                imported_count=len(imported_subjects),
                subjects=imported_subjects
            )

        return {
            "success": True,
            "total": sum(len(subjects) for subjects in scan_result.values()),
            "imported": len(imported_subjects),
            "skipped": skipped_count,
            "failed": len(failed_subjects),
            "by_group": by_group,
            "imported_subjects": imported_subjects,
            "failed_subjects": failed_subjects
        }

    def get_statistics(self) -> Dict:
        """
        获取旧版数据统计

        Returns:
            {
                "total_subjects": 65,
                "by_group": {
                    "control": 22,
                    "mci": 22,
                    "ad": 21
                },
                "complete_subjects": 65,
                "incomplete_subjects": 0
            }
        """
        scan_result = self.scan_legacy_data()

        by_group = {}
        complete_count = 0
        incomplete_count = 0

        for group, subjects in scan_result.items():
            by_group[group] = len(subjects)

            for subj in subjects:
                if subj["files_complete"]:
                    complete_count += 1
                else:
                    incomplete_count += 1

        return {
            "total_subjects": sum(by_group.values()),
            "by_group": by_group,
            "complete_subjects": complete_count,
            "incomplete_subjects": incomplete_count
        }


if __name__ == '__main__':
    # 测试代码
    importer = LegacyDataImporter()

    # 扫描数据
    print("=== Scanning Legacy Data ===")
    scan_result = importer.scan_legacy_data()

    for group, subjects in scan_result.items():
        print(f"\n{group.upper()}: {len(subjects)} subjects")
        for subj in subjects[:2]:  # 只显示前2个
            print(f"  - {subj['subject_id']}: complete={subj['files_complete']}")

    # 统计信息
    print("\n=== Statistics ===")
    stats = importer.get_statistics()
    print(f"Total: {stats['total_subjects']}")
    print(f"By group: {stats['by_group']}")
    print(f"Complete: {stats['complete_subjects']}")
    print(f"Incomplete: {stats['incomplete_subjects']}")
