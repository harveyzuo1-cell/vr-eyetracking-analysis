"""
Module 00: 数据管理服务 - 双数据源导入编排层
Data Management Service - Dual-source Import Orchestration

负责协调 LegacyDataImporter (v1) 和 EyeTrackingDataImporter (v2)
"""
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

from .importers.legacy_importer import LegacyDataImporter
from .importers.eye_tracking_importer import EyeTrackingDataImporter
from .metadata_manager import MetadataManager

logger = logging.getLogger(__name__)


def convert_paths_to_str(obj):
    """递归将字典/列表中的所有Path对象转换为字符串"""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_paths_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_paths_to_str(item) for item in obj]
    else:
        return obj


class DataManagementService:
    """数据管理服务 - 编排双数据源导入"""

    def __init__(self):
        """初始化服务"""
        # 路径配置
        # service.py位置: new_project/src/web/modules/module00_data_management/service.py
        # 向上6层到达项目根目录: az - 副本 (11)/
        current_file = Path(__file__)
        self.project_root = current_file.parent.parent.parent.parent.parent.parent
        self.new_project_dir = self.project_root / 'new_project'
        self.data_dir = self.new_project_dir / 'data'
        self.raw_dir = self.data_dir / '01_raw'
        self.clinical_dir = self.raw_dir / 'clinical'

        # 确保目录存在
        self.clinical_dir.mkdir(parents=True, exist_ok=True)

        # 初始化导入器
        try:
            self.legacy_importer = LegacyDataImporter(str(self.project_root))
            self.eye_tracking_importer = EyeTrackingDataImporter(str(self.project_root))
            self.metadata_manager = MetadataManager(str(self.clinical_dir))
            logger.info("数据管理服务初始化成功")
        except Exception as e:
            logger.error(f"初始化导入器失败: {str(e)}", exc_info=True)
            raise

    def scan_all_sources(self) -> Dict:
        """
        扫描所有数据源 (Legacy v1 + EyeTracking v2)

        Returns:
            {
                "legacy_data": {
                    "source_dir": "data/*_raw/",
                    "control": 22,
                    "mci": 22,
                    "ad": 21,
                    "total_subjects": 65,
                    "details": {...}
                },
                "eye_tracking_data": {
                    "source_dir": "eye_tracking_data/",
                    "control": ~32,
                    "mci": ~32,
                    "ad": ~30,
                    "total_subjects": 94,
                    "details": {...}
                },
                "summary": {
                    "total_subjects": 159,
                    "sources": 2
                }
            }
        """
        try:
            logger.info("开始扫描所有数据源...")

            # 扫描旧版数据 (v1)
            legacy_result = self.legacy_importer.scan_legacy_data()
            legacy_result_clean = convert_paths_to_str(legacy_result)
            legacy_stats = {
                "source_dir": "data/*_raw/",
                "control": len(legacy_result.get("control", [])),
                "mci": len(legacy_result.get("mci", [])),
                "ad": len(legacy_result.get("ad", [])),
                "total_subjects": 0,
                "details": legacy_result_clean
            }
            legacy_stats["total_subjects"] = (
                legacy_stats["control"] +
                legacy_stats["mci"] +
                legacy_stats["ad"]
            )

            # 扫描眼动追踪数据 (v2)
            eye_tracking_result = self.eye_tracking_importer.scan_new_data()
            eye_tracking_result_clean = convert_paths_to_str(eye_tracking_result)
            valid_entries = eye_tracking_result.get("valid_entries", [])

            # 按组别统计
            group_counts = {"control": 0, "mci": 0, "ad": 0, "custom": 0}
            for entry in valid_entries:
                group_code = entry.get("group_code", "custom")
                group_counts[group_code] = group_counts.get(group_code, 0) + 1

            eye_tracking_stats = {
                "source_dir": "eye_tracking_data/",
                "control": group_counts["control"],
                "mci": group_counts["mci"],
                "ad": group_counts["ad"],
                "custom": group_counts["custom"],
                "total_subjects": len(valid_entries),
                "details": eye_tracking_result_clean
            }

            # 汇总
            summary = {
                "total_subjects": legacy_stats["total_subjects"] + eye_tracking_stats["total_subjects"],
                "sources": 2,
                "legacy_v1_count": legacy_stats["total_subjects"],
                "eye_tracking_v2_count": eye_tracking_stats["total_subjects"]
            }

            logger.info(f"扫描完成: 共发现 {summary['total_subjects']} 名受试者")

            return {
                "legacy_data": legacy_stats,
                "eye_tracking_data": eye_tracking_stats,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"扫描数据源失败: {str(e)}", exc_info=True)
            raise

    def preview_import_data(self, source: str = "all", limit: int = 10) -> Dict:
        """
        预览待导入数据

        Args:
            source: 'legacy' | 'eye_tracking' | 'all'
            limit: 预览数量限制

        Returns:
            {
                "legacy_preview": [...],
                "eye_tracking_preview": [...],
                "total_count": int
            }
        """
        try:
            result = {
                "legacy_preview": [],
                "eye_tracking_preview": [],
                "total_count": 0
            }

            if source in ["legacy", "all"]:
                legacy_data = self.legacy_importer.scan_legacy_data()
                # 取前limit个受试者预览
                preview_items = []
                count = 0
                for group, subjects in legacy_data.items():
                    for subject in subjects:
                        if count >= limit:
                            break
                        preview_items.append({
                            "group": group,
                            "subject_dir": str(subject["subject_dir"]),
                            "tasks": subject["tasks"],
                            "data_version": "v1",
                            "roi_layout": "v1",
                            "source_type": "legacy"
                        })
                        count += 1
                    if count >= limit:
                        break
                result["legacy_preview"] = preview_items

            if source in ["eye_tracking", "all"]:
                eye_tracking_data = self.eye_tracking_importer.scan_new_data()
                valid_entries = eye_tracking_data.get("valid_entries", [])
                # 取前limit个受试者预览
                preview_items = []
                for i, entry in enumerate(valid_entries):
                    if i >= limit:
                        break
                    preview_items.append({
                        "group": entry.get("group"),
                        "group_code": entry.get("group_code"),
                        "timestamp": entry.get("timestamp"),
                        "hospital_id": entry.get("hospital_id", "unknown"),
                        "subject_id": entry.get("subject_id"),
                        "data_version": "v2",
                        "roi_layout": "v2",
                        "source_type": "eye_tracking",
                        "files_complete": entry.get("files_complete", False)
                    })
                result["eye_tracking_preview"] = preview_items

            result["total_count"] = len(result["legacy_preview"]) + len(result["eye_tracking_preview"])

            return result

        except Exception as e:
            logger.error(f"预览数据失败: {str(e)}", exc_info=True)
            raise

    def batch_import(self, source: str = "all", overwrite: bool = False) -> Dict:
        """
        批量导入数据

        Args:
            source: 'legacy' | 'eye_tracking' | 'all'
            overwrite: 是否覆盖已存在数据

        Returns:
            {
                "success": true,
                "imported_count": 159,
                "legacy_imported": 65,
                "eye_tracking_imported": 94,
                "skipped_count": 0,
                "errors": []
            }
        """
        try:
            logger.info(f"开始批量导入: source={source}, overwrite={overwrite}")

            result = {
                "success": True,
                "imported_count": 0,
                "legacy_imported": 0,
                "eye_tracking_imported": 0,
                "skipped_count": 0,
                "errors": []
            }

            # 导入旧版数据
            if source in ["legacy", "all"]:
                try:
                    legacy_result = self.legacy_importer.import_all(overwrite=overwrite)
                    result["legacy_imported"] = legacy_result.get("imported_count", 0)
                    result["imported_count"] += result["legacy_imported"]
                    if legacy_result.get("errors"):
                        result["errors"].extend(legacy_result["errors"])
                    logger.info(f"旧版数据导入完成: {result['legacy_imported']} 名受试者")
                except Exception as e:
                    error_msg = f"旧版数据导入失败: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    result["errors"].append(error_msg)

            # 导入眼动追踪数据
            if source in ["eye_tracking", "all"]:
                try:
                    eye_tracking_result = self.eye_tracking_importer.import_all_new(overwrite=overwrite)
                    result["eye_tracking_imported"] = eye_tracking_result.get("imported_count", 0)
                    result["imported_count"] += result["eye_tracking_imported"]
                    if eye_tracking_result.get("errors"):
                        result["errors"].extend(eye_tracking_result["errors"])
                    logger.info(f"眼动追踪数据导入完成: {result['eye_tracking_imported']} 名受试者")
                except Exception as e:
                    error_msg = f"眼动追踪数据导入失败: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    result["errors"].append(error_msg)

            # 判断成功状态
            if result["errors"] and result["imported_count"] == 0:
                result["success"] = False

            logger.info(f"批量导入完成: 总计 {result['imported_count']} 名受试者")

            return result

        except Exception as e:
            logger.error(f"批量导入失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "imported_count": 0,
                "legacy_imported": 0,
                "eye_tracking_imported": 0,
                "skipped_count": 0,
                "errors": [str(e)]
            }

    def get_subjects(
        self,
        data_version: str = "all",
        group: str = "all",
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        获取受试者列表（分页 + 过滤）

        Args:
            data_version: 'v1' | 'v2' | 'all'
            group: 'control' | 'mci' | 'ad' | 'all'
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            {
                "subjects": [...],
                "total_count": 159,
                "page": 1,
                "page_size": 50,
                "total_pages": 4
            }
        """
        try:
            # 加载所有受试者元数据
            all_metadata = self.metadata_manager.load_subject_metadata()

            # 过滤
            filtered_subjects = []
            for subject_id, metadata in all_metadata.items():
                # 数据版本过滤
                if data_version != "all":
                    if metadata.get("data_version") != data_version:
                        continue

                # 组别过滤
                if group != "all":
                    if metadata.get("group") != group:
                        continue

                filtered_subjects.append({
                    "subject_id": subject_id,
                    **metadata
                })

            # 排序（按subject_id）
            filtered_subjects.sort(key=lambda x: x["subject_id"])

            # 分页
            total_count = len(filtered_subjects)
            total_pages = (total_count + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_subjects = filtered_subjects[start_idx:end_idx]

            return {
                "subjects": page_subjects,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }

        except Exception as e:
            logger.error(f"获取受试者列表失败: {str(e)}", exc_info=True)
            raise

    def get_import_history(self, limit: int = 20) -> Dict:
        """
        获取导入历史记录

        Args:
            limit: 返回数量限制

        Returns:
            {
                "history": [...],
                "total_imports": int
            }
        """
        try:
            history_data = self.metadata_manager.load_import_history()

            # 取最新的limit条
            history_list = history_data.get("imports", [])
            history_list.reverse()  # 最新的在前
            limited_history = history_list[:limit]

            return {
                "history": limited_history,
                "total_imports": len(history_list)
            }

        except Exception as e:
            logger.error(f"获取导入历史失败: {str(e)}", exc_info=True)
            raise

    def get_imported_data_stats(self) -> Dict:
        """
        获取已导入数据的统计信息（从metadata读取）

        Returns:
            {
                "v1_data": {
                    "control": 20,
                    "mci": 20,
                    "ad": 20,
                    "total": 60
                },
                "v2_data": {
                    "control": 77,
                    "mci": 8,
                    "ad": 8,
                    "total": 93
                },
                "summary": {
                    "total_subjects": 153,
                    "v1_count": 60,
                    "v2_count": 93
                }
            }
        """
        try:
            import json

            # 直接读取subject_metadata.json文件
            metadata_file = self.clinical_dir / 'subject_metadata.json'

            if not metadata_file.exists():
                return {
                    "v1_data": {"control": 0, "mci": 0, "ad": 0, "total": 0},
                    "v2_data": {"control": 0, "mci": 0, "ad": 0, "total": 0},
                    "summary": {"total_subjects": 0, "v1_count": 0, "v2_count": 0}
                }

            with open(metadata_file, 'r', encoding='utf-8') as f:
                all_metadata = json.load(f)

            # 统计V1数据
            v1_stats = {"control": 0, "mci": 0, "ad": 0, "total": 0}
            v2_stats = {"control": 0, "mci": 0, "ad": 0, "total": 0}

            for subject_id, metadata in all_metadata.items():
                data_version = metadata.get("data_version", "")
                group = metadata.get("group", "")

                if data_version == "v1":
                    if group in v1_stats:
                        v1_stats[group] += 1
                    v1_stats["total"] += 1
                elif data_version == "v2":
                    if group in v2_stats:
                        v2_stats[group] += 1
                    v2_stats["total"] += 1

            summary = {
                "total_subjects": v1_stats["total"] + v2_stats["total"],
                "v1_count": v1_stats["total"],
                "v2_count": v2_stats["total"]
            }

            return {
                "v1_data": v1_stats,
                "v2_data": v2_stats,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"获取已导入数据统计失败: {str(e)}", exc_info=True)
            raise
