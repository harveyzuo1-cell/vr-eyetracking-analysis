"""
任务配置管理服务
Task Configuration Management Service

提供动态任务配置管理,支持任意数量和类型的任务扩展
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from config.settings import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskConfigService:
    """任务配置管理服务"""

    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化服务

        Args:
            config_file: 配置文件路径,默认为 config/task_configs.json
        """
        if config_file is None:
            project_root = Path(Config.DATA_ROOT).parent
            config_file = project_root / "config" / "task_configs.json"

        self.config_file = Path(config_file)
        self._config_cache = None
        self._load_config()

    def _load_config(self):
        """加载任务配置文件"""
        if not self.config_file.exists():
            logger.warning(f"Task config file not found: {self.config_file}")
            logger.info("Creating default config file...")
            self._create_default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config_cache = json.load(f)

            dataset_count = len(self._config_cache.get('datasets', {}))
            logger.info(f"Loaded task config: {dataset_count} datasets, version {self._config_cache.get('version')}")

        except Exception as e:
            logger.error(f"Failed to load task config: {e}")
            logger.info("Creating default config file...")
            self._create_default_config()
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config_cache = json.load(f)

    def _create_default_config(self):
        """创建默认配置文件(向后兼容Q1-Q5)"""
        default_config = {
            "version": "1.0.0",
            "last_modified": datetime.now().isoformat(),
            "description": "任务配置中心 - 默认配置(自动生成)",
            "datasets": {
                "mmse_v1": self._generate_default_v1_config(),
                "mmse_v2": self._generate_default_v2_config()
            }
        }

        # 确保目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

        logger.info(f"Created default task config: {self.config_file}")

    def _generate_default_v1_config(self) -> Dict:
        """生成默认V1配置"""
        return {
            "id": "mmse_v1",
            "name": "MMSE认知评估 (V1版本)",
            "name_en": "MMSE Cognitive Assessment (V1)",
            "description": "包含5个MMSE任务的眼动数据",
            "data_version": "v1",
            "created_date": "2025-01-01",
            "tasks": [
                {
                    "id": "q1",
                    "alt_ids": ["task1", "Q1"],
                    "name": "时间定向",
                    "name_en": "Time Orientation",
                    "description": "评估受试者对时间的定向能力",
                    "order": 1,
                    "background_image": "Q1.jpg",
                    "roi_config": "q1_roi.json",
                    "required": True,
                    "category": "orientation"
                },
                {
                    "id": "q2",
                    "alt_ids": ["task2", "Q2"],
                    "name": "地点定向",
                    "name_en": "Place Orientation",
                    "description": "评估受试者对地点的定向能力",
                    "order": 2,
                    "background_image": "Q2.jpg",
                    "roi_config": "q2_roi.json",
                    "required": True,
                    "category": "orientation"
                },
                {
                    "id": "q3",
                    "alt_ids": ["task3", "Q3"],
                    "name": "记忆",
                    "name_en": "Memory",
                    "description": "评估受试者的即时记忆能力",
                    "order": 3,
                    "background_image": "Q3.jpg",
                    "roi_config": "q3_roi.json",
                    "required": True,
                    "category": "memory"
                },
                {
                    "id": "q4",
                    "alt_ids": ["task4", "Q4"],
                    "name": "注意与计算",
                    "name_en": "Attention and Calculation",
                    "description": "评估受试者的注意力和计算能力",
                    "order": 4,
                    "background_image": "Q4.jpg",
                    "roi_config": "q4_roi.json",
                    "required": True,
                    "category": "attention"
                },
                {
                    "id": "q5",
                    "alt_ids": ["task5", "Q5"],
                    "name": "回忆",
                    "name_en": "Recall",
                    "description": "评估受试者的延迟回忆能力",
                    "order": 5,
                    "background_image": "Q5.jpg",
                    "roi_config": "q5_roi.json",
                    "required": True,
                    "category": "memory"
                }
            ]
        }

    def _generate_default_v2_config(self) -> Dict:
        """生成默认V2配置"""
        return {
            "id": "mmse_v2",
            "name": "MMSE认知评估 (V2版本)",
            "name_en": "MMSE Cognitive Assessment (V2)",
            "description": "新版MMSE眼动数据集",
            "data_version": "v2",
            "created_date": "2025-03-01",
            "tasks": [
                {
                    "id": "q1",
                    "alt_ids": ["task1"],
                    "name": "时间定向",
                    "name_en": "Time Orientation",
                    "description": "评估受试者对时间的定向能力 (V2版本)",
                    "order": 1,
                    "background_image": "task1.png",
                    "roi_config": "q1_roi.json",
                    "required": True,
                    "category": "orientation"
                },
                {
                    "id": "q2",
                    "alt_ids": ["task2"],
                    "name": "地点定向",
                    "name_en": "Place Orientation",
                    "description": "评估受试者对地点的定向能力 (V2版本)",
                    "order": 2,
                    "background_image": "task2.png",
                    "roi_config": "q2_roi.json",
                    "required": True,
                    "category": "orientation"
                },
                {
                    "id": "q3",
                    "alt_ids": ["task3"],
                    "name": "记忆",
                    "name_en": "Memory",
                    "description": "评估受试者的即时记忆能力 (V2版本)",
                    "order": 3,
                    "background_image": "task3.png",
                    "roi_config": "q3_roi.json",
                    "required": True,
                    "category": "memory"
                },
                {
                    "id": "q4",
                    "alt_ids": ["task4"],
                    "name": "注意与计算",
                    "name_en": "Attention and Calculation",
                    "description": "评估受试者的注意力和计算能力 (V2版本)",
                    "order": 4,
                    "background_image": "task4.png",
                    "roi_config": "q4_roi.json",
                    "required": True,
                    "category": "attention"
                },
                {
                    "id": "q5",
                    "alt_ids": ["task5"],
                    "name": "回忆",
                    "name_en": "Recall",
                    "description": "评估受试者的延迟回忆能力 (V2版本)",
                    "order": 5,
                    "background_image": "task5.png",
                    "roi_config": "q5_roi.json",
                    "required": True,
                    "category": "memory"
                }
            ]
        }

    def get_all_datasets(self) -> List[Dict]:
        """
        获取所有数据集配置列表

        Returns:
            数据集配置列表
        """
        datasets = self._config_cache.get("datasets", {})
        return list(datasets.values())

    def get_dataset_config(self, dataset_id: str) -> Optional[Dict]:
        """
        获取数据集配置

        Args:
            dataset_id: 数据集ID (如 "mmse_v1", "mmse_extended")

        Returns:
            数据集配置字典或None
        """
        return self._config_cache.get("datasets", {}).get(dataset_id)

    def get_tasks(self, dataset_id: str) -> List[Dict]:
        """
        获取数据集的任务列表

        Args:
            dataset_id: 数据集ID

        Returns:
            任务配置列表 (按order排序)
        """
        dataset = self.get_dataset_config(dataset_id)
        if not dataset:
            return []

        tasks = dataset.get("tasks", [])
        # 按order字段排序
        return sorted(tasks, key=lambda t: t.get("order", 999))

    def get_task_by_id(self, dataset_id: str, task_id: str) -> Optional[Dict]:
        """
        根据任务ID获取任务配置

        Args:
            dataset_id: 数据集ID
            task_id: 任务ID (支持主ID和备用ID)

        Returns:
            任务配置字典或None
        """
        tasks = self.get_tasks(dataset_id)

        task_id_lower = task_id.lower()

        for task in tasks:
            # 匹配主ID或备用ID (不区分大小写)
            if task["id"].lower() == task_id_lower:
                return task

            alt_ids = task.get("alt_ids", [])
            if any(alt_id.lower() == task_id_lower for alt_id in alt_ids):
                return task

        return None

    def normalize_task_id(self, dataset_id: str, task_id: str) -> Optional[str]:
        """
        标准化任务ID (将备用ID转换为主ID)

        Args:
            dataset_id: 数据集ID
            task_id: 原始任务ID

        Returns:
            标准化后的主ID或None

        Examples:
            normalize_task_id("mmse_v1", "task1") -> "q1"
            normalize_task_id("mmse_v1", "Q1") -> "q1"
        """
        task = self.get_task_by_id(dataset_id, task_id)
        return task["id"] if task else None

    def get_required_tasks(self, dataset_id: str) -> List[str]:
        """
        获取必需任务列表

        Args:
            dataset_id: 数据集ID

        Returns:
            必需任务ID列表
        """
        tasks = self.get_tasks(dataset_id)
        return [task["id"] for task in tasks if task.get("required", False)]

    def get_all_task_ids(self, dataset_id: str, include_alt_ids: bool = False) -> List[str]:
        """
        获取所有任务ID

        Args:
            dataset_id: 数据集ID
            include_alt_ids: 是否包含备用ID

        Returns:
            任务ID列表
        """
        tasks = self.get_tasks(dataset_id)
        task_ids = [task["id"] for task in tasks]

        if include_alt_ids:
            for task in tasks:
                task_ids.extend(task.get("alt_ids", []))

        return task_ids

    def infer_dataset_from_data(self, available_tasks: List[str]) -> Tuple[Optional[str], float]:
        """
        根据实际数据推断数据集类型

        Args:
            available_tasks: 可用的任务ID列表

        Returns:
            (推断的数据集ID, 匹配度0-1) 或 (None, 0.0)

        Examples:
            infer_dataset_from_data(["q1", "q2", "q3", "q4", "q5"])
            -> ("mmse_v1", 1.0)

            infer_dataset_from_data(["q1", "q2", "q6", "q7", "q8"])
            -> ("mmse_extended", 0.6)
        """
        available_set = set(task_id.lower() for task_id in available_tasks)

        # 遍历所有数据集,找到最佳匹配
        best_match = None
        best_score = 0.0

        for dataset_id, dataset_config in self._config_cache.get("datasets", {}).items():
            tasks = dataset_config.get("tasks", [])

            # 构建数据集任务ID集合(包含备用ID)
            dataset_task_ids = set()
            for task in tasks:
                dataset_task_ids.add(task["id"].lower())
                for alt_id in task.get("alt_ids", []):
                    dataset_task_ids.add(alt_id.lower())

            # 计算匹配度
            match_count = len(available_set & dataset_task_ids)
            total_count = len(tasks)  # 使用任务数量作为总数

            if total_count == 0:
                continue

            score = match_count / total_count

            if score > best_score:
                best_score = score
                best_match = dataset_id

        # 匹配度超过50%即认为是该数据集
        if best_score >= 0.5:
            logger.info(f"Inferred dataset '{best_match}' with {best_score*100:.1f}% confidence from tasks: {available_tasks}")
            return best_match, best_score

        logger.warning(f"Could not infer dataset from tasks: {available_tasks} (best match: {best_match} with {best_score*100:.1f}%)")
        return None, 0.0

    def register_dataset(self, dataset_config: Dict) -> bool:
        """
        动态注册新数据集配置

        Args:
            dataset_config: 数据集配置字典,必须包含 'id' 字段

        Returns:
            是否注册成功
        """
        try:
            dataset_id = dataset_config.get("id")
            if not dataset_id:
                logger.error("Dataset config missing 'id' field")
                return False

            # 验证必需字段
            required_fields = ["id", "name", "data_version", "tasks"]
            missing_fields = [f for f in required_fields if f not in dataset_config]
            if missing_fields:
                logger.error(f"Dataset config missing required fields: {missing_fields}")
                return False

            # 添加到配置
            if "datasets" not in self._config_cache:
                self._config_cache["datasets"] = {}

            self._config_cache["datasets"][dataset_id] = dataset_config
            self._config_cache["last_modified"] = datetime.now().isoformat()

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, ensure_ascii=False, indent=2)

            logger.info(f"Registered new dataset: {dataset_id} with {len(dataset_config.get('tasks', []))} tasks")
            return True

        except Exception as e:
            logger.error(f"Failed to register dataset: {e}", exc_info=True)
            return False

    def reload_config(self):
        """重新加载配置文件"""
        self._config_cache = None
        self._load_config()
        logger.info("Task config reloaded")


# 单例模式
_task_config_service_instance = None


def get_task_config_service() -> TaskConfigService:
    """
    获取TaskConfigService单例

    Returns:
        TaskConfigService实例
    """
    global _task_config_service_instance
    if _task_config_service_instance is None:
        _task_config_service_instance = TaskConfigService()
    return _task_config_service_instance
