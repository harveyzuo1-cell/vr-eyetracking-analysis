"""
ROI分析器 - 基于老代码逻辑优化

实现功能:
1. ROI点匹配 (按优先级: keywords > instructions > background)
2. ROI统计计算 (逐帧分析法)
   - fixation_time: 停留时间(秒)
   - entry_count: 进入次数
   - regression_count: 回归次数 (entry_count - 1)
   - points_inside: 内部点数
   - coverage_ratio: 覆盖率
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ROIAnalyzer:
    """ROI统计分析器"""

    def __init__(self, roi_config: Dict[str, Any]):
        """
        初始化ROI分析器

        Args:
            roi_config: 增强版ROI配置
            {
                "keywords": [...],
                "instructions": [...],
                "background": [...]
            }
        """
        self.regions = self._flatten_regions(roi_config)
        logger.info(f"ROIAnalyzer initialized with {len(self.regions)} regions")

    def _flatten_regions(self, roi_config):
        """
        将分层ROI展平为优先级排序列表

        优先级: keywords(2) > instructions(1) > background(0)

        支持两种格式:
        1. 新格式: {"keywords": [...], "instructions": [...], "background": [...]}
        2. 旧格式: [{"id": "...", "x": ..., "y": ..., ...}, ...]
        """
        all_regions = []

        # 检测格式: 如果是dict则为新格式，如果是list则为旧格式
        if isinstance(roi_config, dict):
            # 新格式 (分层结构)
            for region in roi_config.get("keywords", []):
                all_regions.append(self._normalize_region(region))
            for region in roi_config.get("instructions", []):
                all_regions.append(self._normalize_region(region))
            for region in roi_config.get("background", []):
                all_regions.append(self._normalize_region(region))
        elif isinstance(roi_config, list):
            # 旧格式 (扁平列表)
            for region in roi_config:
                all_regions.append(self._normalize_region(region))
        else:
            logger.error(f"Unknown ROI config format: {type(roi_config)}")
            return []

        # 按priority降序排序 (优先匹配高优先级)
        all_regions.sort(key=lambda r: r.get("priority", 0), reverse=True)

        logger.debug(f"Flattened regions: {[r['id'] for r in all_regions]}")
        return all_regions

    def _normalize_region(self, region: Dict) -> Dict:
        """
        标准化region格式，确保包含x/y/width/height字段

        处理两种坐标格式:
        1. normalized_coords: [x, y, w, h]
        2. x, y, width, height (直接字段)
        """
        normalized = region.copy()

        # 如果有normalized_coords，转换为x/y/width/height
        if "normalized_coords" in region:
            coords = region["normalized_coords"]
            if len(coords) >= 4:
                normalized["x"] = coords[0]
                normalized["y"] = coords[1]
                normalized["width"] = coords[2]
                normalized["height"] = coords[3]

        # 确保必要字段存在
        if "x" not in normalized:
            normalized["x"] = 0
        if "y" not in normalized:
            normalized["y"] = 0
        if "width" not in normalized:
            normalized["width"] = 1
        if "height" not in normalized:
            normalized["height"] = 1

        # 确保有name和type字段
        if "name" not in normalized:
            normalized["name"] = normalized.get("id", "unknown")
        if "type" not in normalized:
            # 从ID推断类型
            region_id = normalized.get("id", "")
            if region_id.startswith("KW"):
                normalized["type"] = "keyword"
            elif region_id.startswith("INST"):
                normalized["type"] = "instruction"
            elif region_id.startswith("BG"):
                normalized["type"] = "background"
            else:
                normalized["type"] = "unknown"

        return normalized

    def find_roi_for_point(self, x: float, y: float) -> str:
        """
        查找点所属ROI (优先匹配高优先级区域)

        Args:
            x, y: 归一化坐标 [0, 1]

        Note:
            前端Plotly使用翻转的Y轴坐标系，因此需要对y坐标进行翻转(1-y)
            以匹配ROI配置中的坐标定义

        Returns:
            roi_id (str) or None
        """
        # Y轴翻转以匹配前端Plotly坐标系
        y_flipped = 1 - y

        for region in self.regions:
            x_min = region["x"]
            y_min = region["y"]
            x_max = x_min + region["width"]
            y_max = y_min + region["height"]

            # 点在矩形内（使用翻转后的y坐标）
            if x_min <= x <= x_max and y_min <= y_flipped <= y_max:
                return region["id"]

        return None

    def calculate_stats(self, gaze_data: pd.DataFrame) -> Dict[str, Dict]:
        """
        计算ROI统计信息 (逐帧分析法)

        Args:
            gaze_data: DataFrame with columns [x, y, timestamp]

        Returns:
            {
                "KW_q1_1": {
                    "fixation_time": 2.5,      # 秒
                    "entry_count": 3,          # 进入次数
                    "regression_count": 2,     # 回归次数
                    "points_inside": 25,       # 内部点数
                    "total_points": 100,       # 总点数
                    "coverage_ratio": 0.25,    # 覆盖率
                    "name": "KW_n2q1_1",      # 显示名称
                    "type": "keyword"          # 类型
                },
                ...
            }
        """
        if gaze_data is None or gaze_data.empty:
            logger.warning("Gaze data is empty or too short")
            return self._empty_stats()

        # 确保数据按时间排序
        gaze_data = gaze_data.sort_values("timestamp").reset_index(drop=True)

        # 初始化统计
        stats = {}
        for region in self.regions:
            stats[region["id"]] = {
                "fixation_time": 0.0,
                "entry_count": 0,
                "regression_count": 0,
                "points_inside": 0,
                "total_points": len(gaze_data),
                "coverage_ratio": 0.0,
                "name": region["name"],
                "type": region["type"]
            }

        # 计算时间差 (秒)
        time_diff = gaze_data["timestamp"].diff().fillna(0)

        # 逐帧分析
        prev_roi = None

        for i in range(len(gaze_data)):
            x = gaze_data.at[i, "x"]
            y = gaze_data.at[i, "y"]
            dt = time_diff.iloc[i]

            # 查找当前点所属ROI
            current_roi = self.find_roi_for_point(x, y)

            if current_roi:
                # 累加停留时间 (秒)
                stats[current_roi]["fixation_time"] += dt
                stats[current_roi]["points_inside"] += 1

                # 检测进入事件 (ROI切换)
                if current_roi != prev_roi:
                    stats[current_roi]["entry_count"] += 1

            prev_roi = current_roi

        # 计算回归次数和覆盖率
        for roi_id, st in stats.items():
            # 回归次数 = 进入次数 - 1 (第一次不算回归)
            st["regression_count"] = max(0, st["entry_count"] - 1)

            # 覆盖率
            st["coverage_ratio"] = (
                st["points_inside"] / st["total_points"]
                if st["total_points"] > 0 else 0.0
            )

        logger.info(f"ROI stats calculated for {len(gaze_data)} points")
        return stats

    def _empty_stats(self):
        """返回空统计 (数据不足时)"""
        stats = {}
        for region in self.regions:
            stats[region["id"]] = {
                "fixation_time": 0.0,
                "entry_count": 0,
                "regression_count": 0,
                "points_inside": 0,
                "total_points": 0,
                "coverage_ratio": 0.0,
                "name": region["name"],
                "type": region["type"]
            }
        return stats

    def get_summary(self, stats: Dict[str, Dict]) -> Dict[str, Any]:
        """
        生成统计摘要

        Args:
            stats: calculate_stats() 的返回值

        Returns:
            {
                "total_fixation_time": 10.5,
                "keywords_fixation_time": 5.2,
                "instructions_fixation_time": 3.3,
                "background_fixation_time": 2.0,
                "total_entry_count": 15,
                "most_visited_roi": "KW_q1_1"
            }
        """
        summary = {
            "total_fixation_time": 0.0,
            "keywords_fixation_time": 0.0,
            "instructions_fixation_time": 0.0,
            "background_fixation_time": 0.0,
            "total_entry_count": 0,
            "most_visited_roi": None,
            "max_entry_count": 0
        }

        for roi_id, st in stats.items():
            summary["total_fixation_time"] += st["fixation_time"]
            summary["total_entry_count"] += st["entry_count"]

            # 按类型累加
            if st["type"] == "keyword":
                summary["keywords_fixation_time"] += st["fixation_time"]
            elif st["type"] == "instruction":
                summary["instructions_fixation_time"] += st["fixation_time"]
            elif st["type"] == "background":
                summary["background_fixation_time"] += st["fixation_time"]

            # 记录最多访问的ROI
            if st["entry_count"] > summary["max_entry_count"]:
                summary["max_entry_count"] = st["entry_count"]
                summary["most_visited_roi"] = roi_id

        return summary
