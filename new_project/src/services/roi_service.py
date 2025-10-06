"""
统一ROI配置服务
Unified ROI Configuration Service

提供统一的ROI配置读取接口，处理格式转换和Task ID映射
从ModuleEX实时获取ROI配置，确保数据的唯一来源
"""
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime

from config.settings import Config
from src.utils.logger import setup_logger
from src.services.task_config_service import TaskConfigService

logger = setup_logger(__name__)


class UnifiedROIService:
    """统一ROI配置服务 - 从ModuleEX实时获取ROI配置"""

    def __init__(self, task_config_service: Optional[TaskConfigService] = None):
        """
        初始化服务

        Args:
            task_config_service: 任务配置服务实例（可选，默认使用单例）
        """
        self.data_root = Path(Config.DATA_ROOT)
        self.roi_configs_dir = self.data_root / 'roi_configs'
        self.legacy_config_dir = Path(Config.DATA_ROOT).parent / 'config'

        # 注入TaskConfigService，如果未提供则使用单例
        self.task_config_service = task_config_service or TaskConfigService()

        # 不要导入ModuleEX的ROIConfigService - 会造成循环依赖
        # 相反，ModuleEX应该依赖UnifiedROIService
        self.moduleex_service = None
        self.use_moduleex = False

        # ROI配置缓存（禁用缓存以确保实时获取最新数据）
        self._cache = {}
        self._use_cache = False  # 禁用缓存

        logger.info(f"UnifiedROIService initialized: roi_configs={self.roi_configs_dir}")

    def normalize_task_id(self, task_id: str, dataset_id: str = "mmse_v1") -> Tuple[str, str]:
        """
        标准化Task ID（使用TaskConfigService）

        Args:
            task_id: 原始task ID (q1/task1等)
            dataset_id: 数据集ID，默认mmse_v1

        Returns:
            (legacy_id, new_id) 例如: ("q1", "task1")

        Note:
            保持向后兼容的返回格式，内部使用TaskConfigService
        """
        task_lower = task_id.lower()

        # 使用TaskConfigService来标准化task ID
        normalized_id = self.task_config_service.normalize_task_id(dataset_id, task_lower)

        # 如果找到了标准化的ID，获取任务的所有备用IDs
        if normalized_id:
            task_config = self.task_config_service.get_task_by_id(dataset_id, normalized_id)
            if task_config:
                # 从alt_ids中查找 "taskX" 格式的ID
                alt_ids = task_config.get('alt_ids', [])
                task_format_id = next((aid for aid in alt_ids if aid.startswith('task')), None)

                if normalized_id.startswith('q'):
                    legacy_id = normalized_id
                    new_id = task_format_id if task_format_id else normalized_id
                elif normalized_id.startswith('task'):
                    new_id = normalized_id
                    # 查找q格式的ID
                    legacy_id = next((aid for aid in alt_ids if aid.startswith('q')), normalized_id)
                else:
                    legacy_id = normalized_id
                    new_id = normalized_id

                return legacy_id, new_id

        # 回退：保持原始值不变
        return task_lower, task_lower

    def get_roi_config_path(self, version: str, task_id: str) -> Optional[Path]:
        """
        获取ROI配置文件路径

        Args:
            version: v1/v2
            task_id: 任务ID (q1-q5 或 task1-task5)

        Returns:
            配置文件路径，如果不存在返回None
        """
        legacy_id, new_id = self.normalize_task_id(task_id)

        # 优先尝试新路径: data/roi_configs/{version}/{legacy_id}_roi.json
        new_path = self.roi_configs_dir / version / f"{legacy_id}_roi.json"
        if new_path.exists():
            return new_path

        # 尝试使用new_id
        new_path_alt = self.roi_configs_dir / version / f"{new_id}_roi.json"
        if new_path_alt.exists():
            return new_path_alt

        # 回退到旧路径: config/roi_{version}.json (需要从中提取)
        legacy_path = self.legacy_config_dir / f"roi_{version}.json"
        if legacy_path.exists():
            return legacy_path

        # 尝试enhanced版本
        enhanced_path = self.legacy_config_dir / f"roi_{version}_enhanced.json"
        if enhanced_path.exists():
            return enhanced_path

        return None

    def load_from_legacy_file(self, version: str, task_id: str) -> Optional[Dict]:
        """
        从旧的统一配置文件中加载特定任务的ROI

        Args:
            version: v1/v2
            task_id: 任务ID

        Returns:
            ROI配置数据或None
        """
        legacy_id, new_id = self.normalize_task_id(task_id)
        legacy_path = self.legacy_config_dir / f"roi_{version}.json"

        if not legacy_path.exists():
            return None

        try:
            with open(legacy_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 筛选特定任务的regions
            if 'regions' in data:
                task_regions = [
                    r for r in data['regions']
                    if r.get('task') == legacy_id or r.get('task_id') == legacy_id
                ]

                if task_regions:
                    # 转换为新格式
                    return self.convert_legacy_to_new({
                        'version': version,
                        'task': legacy_id,
                        'regions': task_regions
                    })

            return None

        except Exception as e:
            logger.error(f"Failed to load from legacy file {legacy_path}: {e}")
            return None

    def convert_legacy_to_new(self, legacy_config: Dict) -> Dict:
        """
        将旧格式转换为新格式

        旧格式:
        {
            "regions": [
                {"id": "KW_q1_1", "task": "q1", "type": "KW", "coords": [...]}
            ]
        }

        新格式:
        {
            "regions": {
                "keywords": [...],
                "instructions": [...],
                "background": [...]
            }
        }
        """
        regions = legacy_config.get('regions', [])

        # 按类型分组
        grouped_regions = {
            'keywords': [],
            'instructions': [],
            'background': []
        }

        for region in regions:
            region_type = region.get('type', '').upper()

            # 转换坐标格式
            if 'coords' in region:
                region['normalized_coords'] = region.pop('coords')

            # 分组
            if region_type == 'KW':
                grouped_regions['keywords'].append(region)
            elif region_type == 'INST':
                grouped_regions['instructions'].append(region)
            elif region_type == 'BG':
                grouped_regions['background'].append(region)
            else:
                # 未知类型，放入background
                grouped_regions['background'].append(region)

        return {
            'version': legacy_config.get('version', 'v1'),
            'task_id': legacy_config.get('task', 'q1'),
            'regions': grouped_regions,
            'last_modified': datetime.now().isoformat()
        }

    def get_roi_config(self, version: str, task_id: str) -> Dict[str, Any]:
        """
        获取ROI配置（统一接口）- 从ModuleEX实时加载

        Args:
            version: v1/v2
            task_id: q1-q5 或 task1-task5（自动转换）

        Returns:
            {
                "success": True,
                "data": {
                    "version": "v1",
                    "task_id": "q1",
                    "task_id_alt": "task1",
                    "regions": {...}
                }
            }
        """
        legacy_id, new_id = self.normalize_task_id(task_id)

        # 优先从ModuleEX ROIConfigService获取（避免循环依赖，延迟导入）
        try:
            from src.web.modules.moduleEX_roi_config.service import ROIConfigService
            moduleex_service = ROIConfigService()

            logger.info(f"Loading ROI config from ModuleEX: version={version}, task_id={legacy_id}")
            result = moduleex_service.load_roi_config(version, legacy_id)

            if result['success']:
                config_data = result['data']
                # 添加双重task_id
                config_data['task_id'] = legacy_id
                config_data['task_id_alt'] = new_id
                logger.info(f"Successfully loaded ROI config from ModuleEX: {version}/{legacy_id}")
                return {"success": True, "data": config_data}
            else:
                logger.warning(f"ModuleEX returned failure: {result.get('message', 'Unknown error')}")
                # 继续fallback到文件系统
        except Exception as e:
            logger.error(f"Error loading from ModuleEX: {e}", exc_info=True)
            # 继续fallback到文件系统

        # Fallback: 从文件系统加载
        logger.info(f"Falling back to file-based ROI config: version={version}, task_id={legacy_id}")

        # 获取配置文件路径
        config_path = self.get_roi_config_path(version, task_id)

        if not config_path:
            # 尝试从旧文件加载
            config_data = self.load_from_legacy_file(version, task_id)
            if config_data:
                return {"success": True, "data": config_data}

            return {
                "success": False,
                "error": f"ROI config not found for version={version}, task={task_id}",
                "data": None
            }

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 如果是旧的统一文件，需要筛选和转换
            if config_path.name.startswith('roi_'):
                config_data = self.load_from_legacy_file(version, task_id)
                if not config_data:
                    return {
                        "success": False,
                        "error": f"Task {task_id} not found in {config_path}",
                        "data": None
                    }

            # 确保格式正确
            if 'regions' not in config_data:
                config_data = self.convert_legacy_to_new(config_data)

            # 添加双重task_id
            config_data['task_id'] = legacy_id
            config_data['task_id_alt'] = new_id

            logger.info(f"Loaded ROI config from file: {config_path}")
            return {"success": True, "data": config_data}

        except Exception as e:
            logger.error(f"Failed to load ROI config from {config_path}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    def get_roi_config_enhanced(self, version: str, task_id: str) -> Dict[str, Any]:
        """
        获取增强版ROI配置（包含背景图片等元数据）

        Returns:
            {
                "success": True,
                "data": {
                    "version": "v1",
                    "task_id": "q1",
                    "task_name": "时间定向",
                    "background_image": "/static/background_images/v1/Q1.jpg",
                    "regions": {...}
                }
            }
        """
        # 获取基础配置
        result = self.get_roi_config(version, task_id)

        if not result["success"]:
            return result

        config_data = result["data"]
        legacy_id, new_id = self.normalize_task_id(task_id)

        # 添加背景图片路径
        bg_image_name = self._get_background_image_name(version, legacy_id)
        config_data['background_image'] = f"/static/background_images/{version}/{bg_image_name}"

        # 添加任务名称（如果有）
        task_names = {
            'q1': '时间定向',
            'q2': '地点定向',
            'q3': '记忆',
            'q4': '注意与计算',
            'q5': '回忆'
        }
        config_data['task_name'] = task_names.get(legacy_id, legacy_id.upper())

        return {"success": True, "data": config_data}

    def _get_background_image_name(self, version: str, task_id: str) -> str:
        """获取背景图片文件名"""
        if version == 'v1':
            # v1使用大写Q1-Q5格式
            num = task_id[1] if len(task_id) > 1 else '1'
            return f"Q{num}.jpg"
        else:
            # v2使用task1-task5格式
            legacy_id, new_id = self.normalize_task_id(task_id)
            return f"{new_id}.png"

    def list_available_tasks(self, version: str) -> List[str]:
        """
        列出指定版本可用的任务列表

        Returns:
            ["q1", "q2", "q3", "q4", "q5"]
        """
        version_dir = self.roi_configs_dir / version
        tasks = []

        if version_dir.exists():
            for config_file in version_dir.glob('*_roi.json'):
                task_id = config_file.stem.replace('_roi', '')
                tasks.append(task_id)

        # 如果新路径没有，尝试从旧文件获取
        if not tasks:
            legacy_path = self.legacy_config_dir / f"roi_{version}.json"
            if legacy_path.exists():
                try:
                    with open(legacy_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    tasks = list(set(r.get('task', '') for r in data.get('regions', [])))
                except:
                    pass

        return sorted(tasks)

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("ROI config cache cleared")


# 全局单例
_unified_roi_service = None

def get_unified_roi_service() -> UnifiedROIService:
    """获取统一ROI服务单例"""
    global _unified_roi_service
    if _unified_roi_service is None:
        _unified_roi_service = UnifiedROIService()
    return _unified_roi_service
