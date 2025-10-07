"""
Module 01: 数据可视化服务层
Data Visualization Service Layer

Business logic for loading and processing eye-tracking data for visualization
Updated: 2025-10-02 - Migrated to shared MetadataReader
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from src.core.metadata_reader import MetadataReader

logger = logging.getLogger(__name__)


class DataVisualizationService:
    """数据可视化服务类"""

    def __init__(self, data_root: Optional[str] = None):
        """
        初始化服务

        Args:
            data_root: 数据根目录路径
        """
        if data_root is None:
            # 默认使用项目根目录下的data文件夹
            project_root = Path(__file__).parent.parent.parent.parent.parent
            data_root = project_root / "data"

        self.data_root = Path(data_root)

        # 初始化MetadataReader - 读取Module00维护的元数据
        clinical_data_dir = self.data_root / "01_raw" / "clinical"
        self.metadata_reader = MetadataReader(clinical_data_dir=str(clinical_data_dir))

        logger.info(f"DataVisualizationService initialized with data_root: {self.data_root}")

    def get_groups(self, version: Optional[str] = None) -> Dict[str, Any]:
        """
        获取组别列表（支持版本筛选）

        Args:
            version: 数据版本筛选 (all/v1/v2/None)，None或'all'表示全部

        Returns:
            {
                "success": True,
                "data": [
                    {"id": "control", "name": "对照组", "count": 65, "v1": 22, "v2": 43, "has_mmse": 20},
                    {"id": "mci", "name": "MCI组", "count": 42, "v1": 20, "v2": 22, "has_mmse": 20},
                    {"id": "ad", "name": "AD组", "count": 42, "v1": 21, "v2": 21, "has_mmse": 20}
                ]
            }
        """
        try:
            # 从MetadataReader获取统计信息
            stats = self.metadata_reader.get_group_statistics()

            group_mapping = {
                'control': '对照组',
                'mci': 'MCI组',
                'ad': 'AD组'
            }

            groups = []
            for group_id, group_name in group_mapping.items():
                if group_id in stats:
                    group_stats = stats[group_id]

                    # 根据版本选择显示的count
                    if version and version != 'all':
                        display_count = group_stats.get(version, 0)
                    else:
                        display_count = group_stats["total"]

                    groups.append({
                        "id": group_id,
                        "name": group_name,
                        "count": display_count,
                        "v1": group_stats["v1"],
                        "v2": group_stats["v2"],
                        "has_mmse": group_stats["has_mmse"]
                    })

            return {
                "success": True,
                "data": groups
            }
        except Exception as e:
            logger.error(f"Failed to get groups: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    def get_subjects(self, group: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定组别和版本的受试者列表

        Args:
            group: 组别ID (control/mci/ad)
            version: 数据版本筛选 (all/v1/v2/None)，None或'all'表示全部

        Returns:
            {
                "success": True,
                "data": [
                    {
                        "id": "control_legacy_1",
                        "task_count": 5,
                        "data_version": "v1",
                        "source_type": "legacy",
                        "has_mmse": true
                    },
                    ...
                ]
            }
        """
        try:
            # 从MetadataReader获取受试者列表
            subjects_meta = self.metadata_reader.get_subjects_by_group(group)

            subjects = []
            for meta in subjects_meta:
                subject_id = meta.get('subject_id')
                data_version = meta.get('data_version', 'v1')

                # 版本筛选逻辑
                if version and version != 'all':
                    if data_version != version:
                        continue  # 跳过不匹配的版本

                subjects.append({
                    "id": subject_id,
                    "task_count": len(meta.get('tasks_available', [])),
                    "data_version": data_version,
                    "source_type": meta.get('source_type', 'legacy'),
                    "has_mmse": self.metadata_reader.has_mmse_score(subject_id)
                })

            return {
                "success": True,
                "data": subjects
            }
        except Exception as e:
            logger.error(f"Failed to get subjects for group '{group}': {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    def get_tasks(self, group: str, subject_id: str) -> Dict[str, Any]:
        """
        获取指定受试者的任务列表

        Args:
            group: 组别ID
            subject_id: 受试者ID

        Returns:
            {
                "success": True,
                "data": ["q1", "q2", "q3", "q4", "q5"]
            }
        """
        try:
            # 从MetadataReader获取任务列表
            tasks = self.metadata_reader.get_tasks_available(subject_id)

            if not tasks:
                # 如果metadata中没有找到，检查受试者是否存在
                subject_info = self.metadata_reader.get_subject_info(subject_id)
                if not subject_info:
                    return {
                        "success": False,
                        "error": f"Subject '{subject_id}' not found",
                        "data": []
                    }

            return {
                "success": True,
                "data": tasks
            }
        except Exception as e:
            logger.error(f"Failed to get tasks for subject '{subject_id}' in group '{group}': {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    def load_raw_data(self, group: str, subject_id: str, task_id: str) -> Dict[str, Any]:
        """
        加载原始眼动数据

        Args:
            group: 组别ID
            subject_id: 受试者ID
            task_id: 任务ID (q1-q5)

        Returns:
            {
                "success": True,
                "data": [
                    {"timestamp": 0.0, "x": 0.5, "y": 0.5},
                    ...
                ],
                "stats": {
                    "total_points": 1000,
                    "duration": 5000.0,
                    "x_range": [0.0, 1.0],
                    "y_range": [0.0, 1.0]
                },
                "metadata": {
                    "group": "control",
                    "subject_id": "control_legacy_1",
                    "task": "q1",
                    "data_version": "v1",
                    "source_type": "legacy",
                    "has_mmse": true,
                    "mmse_scores": {...}
                }
            }
        """
        try:
            # 验证受试者是否存在
            subject_info = self.metadata_reader.get_subject_info(subject_id)
            if not subject_info:
                return {
                    "success": False,
                    "error": f"Subject '{subject_id}' not found",
                    "data": [],
                    "stats": None,
                    "metadata": None
                }

            # 验证任务是否可用
            available_tasks = self.metadata_reader.get_tasks_available(subject_id)
            if task_id not in available_tasks:
                return {
                    "success": False,
                    "error": f"Task '{task_id}' not available for subject '{subject_id}'",
                    "data": [],
                    "stats": None,
                    "metadata": None
                }

            # 构建正确的文件路径：data/01_raw/{group}/{subject_id}_{task}.csv
            data_file = self.data_root / "01_raw" / group / f"{subject_id}_{task_id}.csv"

            if not data_file.exists():
                return {
                    "success": False,
                    "error": f"Data file not found: {data_file}",
                    "data": [],
                    "stats": None,
                    "metadata": None
                }

            # 读取CSV文件
            df = pd.read_csv(data_file)

            # 验证必需的列
            required_columns = ['timestamp', 'x', 'y']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_columns}",
                    "data": [],
                    "stats": None,
                    "metadata": None
                }

            # 转换timestamp为datetime类型并计算duration
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_time = df['timestamp'].min()
            duration_seconds = (df['timestamp'].max() - start_time).total_seconds()

            # 转换timestamp为相对秒数（从第一个点开始）
            df['timestamp_sec'] = (df['timestamp'] - start_time).dt.total_seconds()

            # 转换为列表格式（使用相对时间）
            data = df[['timestamp_sec', 'x', 'y']].rename(columns={'timestamp_sec': 'timestamp'}).to_dict('records')

            # 计算统计信息
            stats = {
                "total_points": len(df),
                "duration": float(duration_seconds),
                "x_range": [float(df['x'].min()), float(df['x'].max())],
                "y_range": [float(df['y'].min()), float(df['y'].max())]
            }

            # 获取MMSE数据
            mmse_scores = self.metadata_reader.get_mmse_score(subject_id)

            # 元数据（包含v1/v2版本信息和MMSE）
            metadata = {
                "group": group,
                "subject_id": subject_id,
                "task": task_id,
                "data_version": subject_info.get('data_version', 'v1'),
                "source_type": subject_info.get('source_type', 'legacy'),
                "roi_layout": subject_info.get('roi_layout', 'v1'),
                "has_mmse": self.metadata_reader.has_mmse_score(subject_id),
                "mmse_scores": mmse_scores,
                "file_path": str(data_file)
            }

            logger.info(f"Loaded {len(data)} data points from {data_file}")

            return {
                "success": True,
                "data": data,
                "stats": stats,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Failed to load raw data: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "stats": None,
                "metadata": None
            }

    def load_all_tasks_data(self, group: str, subject_id: str) -> Dict[str, Any]:
        """
        加载受试者的Q1-Q5所有任务数据

        Args:
            group: 组别ID
            subject_id: 受试者ID

        Returns:
            {
                "success": True,
                "data": [...],      # 合并后的所有数据点
                "stats": {...},     # 合并后的统计信息
                "metadata": {...}
            }
        """
        try:
            # 验证受试者是否存在
            subject_info = self.metadata_reader.get_subject_info(subject_id)
            if not subject_info:
                return {
                    "success": False,
                    "error": f"Subject '{subject_id}' not found",
                    "data": [],
                    "stats": None,
                    "metadata": None
                }

            # 获取可用任务列表
            available_tasks = self.metadata_reader.get_tasks_available(subject_id)
            if not available_tasks:
                return {
                    "success": False,
                    "error": f"No tasks available for subject '{subject_id}'",
                    "data": [],
                    "stats": None,
                    "metadata": None
                }

            # 加载所有任务数据
            all_data = []
            total_points = 0
            total_duration = 0.0
            points_per_task = {}

            x_min, x_max = float('inf'), float('-inf')
            y_min, y_max = float('inf'), float('-inf')

            for task_id in sorted(available_tasks):  # q1, q2, q3, q4, q5
                # 构建文件路径
                data_file = self.data_root / "01_raw" / group / f"{subject_id}_{task_id}.csv"

                if not data_file.exists():
                    logger.warning(f"Data file not found: {data_file}")
                    continue

                # 读取CSV
                df = pd.read_csv(data_file)

                # 验证列
                required_columns = ['timestamp', 'x', 'y']
                if not all(col in df.columns for col in required_columns):
                    logger.warning(f"Missing columns in {data_file}")
                    continue

                # 处理timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                start_time = df['timestamp'].min()
                duration = (df['timestamp'].max() - start_time).total_seconds()
                df['timestamp_sec'] = (df['timestamp'] - start_time).dt.total_seconds()

                # 添加task标识
                df['task'] = task_id

                # 转换为字典列表
                task_data = df[['timestamp_sec', 'x', 'y', 'task']].rename(
                    columns={'timestamp_sec': 'timestamp'}
                ).to_dict('records')

                all_data.extend(task_data)

                # 统计信息
                total_points += len(df)
                total_duration += duration
                points_per_task[task_id] = len(df)

                # 更新范围
                x_min = min(x_min, df['x'].min())
                x_max = max(x_max, df['x'].max())
                y_min = min(y_min, df['y'].min())
                y_max = max(y_max, df['y'].max())

            if not all_data:
                return {
                    "success": False,
                    "error": "No valid data files found",
                    "data": [],
                    "stats": None,
                    "metadata": None
                }

            # 统计信息
            stats = {
                "total_points": total_points,
                "duration": float(total_duration),
                "x_range": [float(x_min), float(x_max)],
                "y_range": [float(y_min), float(y_max)],
                "tasks_loaded": sorted(available_tasks),
                "points_per_task": points_per_task
            }

            # 获取MMSE数据
            mmse_scores = self.metadata_reader.get_mmse_score(subject_id)

            # 元数据
            metadata = {
                "group": group,
                "subject_id": subject_id,
                "task": "all",  # 标识为全部任务
                "data_version": subject_info.get('data_version', 'v1'),
                "source_type": subject_info.get('source_type', 'legacy'),
                "roi_layout": subject_info.get('roi_layout', 'v1'),
                "has_mmse": self.metadata_reader.has_mmse_score(subject_id),
                "mmse_scores": mmse_scores
            }

            logger.info(
                f"Loaded {total_points} total data points from {len(available_tasks)} tasks "
                f"for subject {subject_id}"
            )

            return {
                "success": True,
                "data": all_data,
                "stats": stats,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Failed to load all tasks data: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "stats": None,
                "metadata": None
            }

    def get_roi_config(self, version: str, task: str) -> Dict[str, Any]:
        """
        获取ROI配置

        使用统一ROI服务获取配置

        Args:
            version: 数据版本 (v1/v2)
            task: 任务ID (q1/q2/q3/q4/q5/all)

        Returns:
            {
                "success": True,
                "data": {
                    "version": "v1",
                    "task_id": "q1",
                    "regions": {...}  # 新格式为dict
                }
            }
        """
        try:
            # 使用统一ROI服务
            from src.services.roi_service import get_unified_roi_service

            roi_service = get_unified_roi_service()

            # 获取ROI配置
            result = roi_service.get_roi_config(version, task)

            if result["success"]:
                # 转换为旧API格式（保持兼容性）
                data = result["data"]
                return {
                    "success": True,
                    "data": {
                        "version": data.get("version"),
                        "layout": "enhanced",  # 标记为增强格式
                        "task": data.get("task_id"),
                        "regions": data.get("regions")  # 已经是新格式（dict）
                    }
                }

            return result

        except Exception as e:
            logger.error(f"Failed to get ROI config: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    def get_background_image(self, version: str, task: str) -> Dict[str, Any]:
        """
        获取任务背景图片路径

        Args:
            version: 数据版本 (v1/v2)
            task: 任务ID (q1/q2/q3/q4/q5)

        Returns:
            {
                "success": True,
                "data": {
                    "version": "v1",
                    "task": "q1",
                    "image_path": "/static/background_images/v1/Q1.jpg",
                    "exists": True
                }
            }
        """
        try:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            bg_dir = project_root / "data" / "background_images" / version

            # V2数据: level_X -> taskX.png
            # V1数据: qX -> QX.jpg
            if version == 'v2':
                # 映射 level_X -> taskX
                if task.startswith('level_'):
                    task_num = task.split('_')[1]  # level_1 -> 1
                    file_base = f"task{task_num}"
                else:
                    file_base = task

                # 尝试多种扩展名
                image_path = None
                for ext in ['.png', '.jpg', '.jpeg']:
                    candidate = bg_dir / f"{file_base}{ext}"
                    if candidate.exists():
                        image_path = candidate
                        break
            else:
                # V1数据使用原逻辑
                task_upper = task.upper()
                image_path = bg_dir / f"{task_upper}.jpg"

            # 检查文件是否存在
            if image_path and image_path.exists():
                relative_path = f"/static/background_images/{version}/{image_path.name}"
                exists = True
            else:
                relative_path = None
                exists = False

            logger.info(f"Background image for version={version}, task={task}: path={relative_path}, exists={exists}")

            return {
                "success": True,
                "data": {
                    "version": version,
                    "task": task,
                    "image_path": relative_path,
                    "exists": exists
                }
            }
        except Exception as e:
            logger.error(f"Failed to get background image: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    def get_roi_config_enhanced(self, version: str, task: str) -> Dict[str, Any]:
        """
        获取增强版ROI配置 (支持多层次ROI: keywords/instructions/background)

        使用统一ROI服务获取配置

        Args:
            version: 数据版本 (v1/v2)
            task: 任务ID (q1/q2/q3/q4/q5/all)

        Returns:
            {
                "success": True,
                "data": {
                    "version": "v1",
                    "task": "q1",
                    "task_name": "时间定向",
                    "background_image": "/static/background_images/v1/Q1.jpg",
                    "regions": {
                        "keywords": [...],
                        "instructions": [...],
                        "background": [...]
                    }
                }
            }
        """
        try:
            # 使用统一ROI服务
            from src.services.roi_service import get_unified_roi_service

            roi_service = get_unified_roi_service()

            # 获取增强配置
            result = roi_service.get_roi_config_enhanced(version, task)

            if result["success"]:
                logger.info(f"Loaded enhanced ROI config for version={version}, task={task} via UnifiedROIService")

            return result

        except Exception as e:
            logger.error(f"Failed to get enhanced ROI config: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    def calculate_roi_stats(self, version: str, task: str, gaze_data_list: List[Dict]) -> Dict[str, Any]:
        """
        计算ROI统计信息

        Args:
            version: 数据版本 (v1/v2)
            task: 任务ID (q1/q2/q3/q4/q5/all)
            gaze_data_list: 眼动数据列表 [{"x": 0.5, "y": 0.5, "timestamp": 0.0}, ...]

        Returns:
            {
                "success": True,
                "data": {
                    "stats": {...},    # 详细统计
                    "summary": {...}   # 摘要
                }
            }
        """
        try:
            # 获取增强版ROI配置
            roi_result = self.get_roi_config_enhanced(version, task)
            if not roi_result["success"]:
                return roi_result

            # 转换为DataFrame
            import pandas as pd
            gaze_df = pd.DataFrame(gaze_data_list)

            # 创建分析器并计算统计
            from .roi_analyzer import ROIAnalyzer
            analyzer = ROIAnalyzer(roi_result["data"]["regions"])
            stats = analyzer.calculate_stats(gaze_df)
            summary = analyzer.get_summary(stats)

            logger.info(f"ROI stats calculated: {len(stats)} regions analyzed")

            return {
                "success": True,
                "data": {
                    "stats": stats,
                    "summary": summary
                }
            }

        except Exception as e:
            logger.error(f"Failed to calculate ROI stats: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
