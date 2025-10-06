#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI分析器单元测试
ROIAnalyzer Unit Tests

测试内容:
- ROI区域匹配（优先级）
- 统计计算（进入次数、注视时长、回视次数）
- 边界情况处理
"""

import unittest
import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.web.modules.module01_data_visualization.roi_analyzer import ROIAnalyzer


class TestROIAnalyzer(unittest.TestCase):
    """ROI分析器测试用例"""

    def setUp(self):
        """测试前准备 - 创建测试用ROI配置"""
        self.roi_config = {
            "keywords": [
                {
                    "id": "KW_test_1",
                    "name": "测试关键词1",
                    "type": "keyword",
                    "x": 0.2,
                    "y": 0.2,
                    "width": 0.2,
                    "height": 0.2,
                    "color": "#FF6B6B",
                    "priority": 2
                },
                {
                    "id": "KW_test_2",
                    "name": "测试关键词2",
                    "type": "keyword",
                    "x": 0.6,
                    "y": 0.6,
                    "width": 0.2,
                    "height": 0.2,
                    "color": "#FF6B6B",
                    "priority": 2
                }
            ],
            "instructions": [
                {
                    "id": "INST_test_1",
                    "name": "测试指示语",
                    "type": "instruction",
                    "x": 0.1,
                    "y": 0.1,
                    "width": 0.4,
                    "height": 0.15,
                    "color": "#FFA500",
                    "priority": 1
                }
            ],
            "background": [
                {
                    "id": "BG_test",
                    "name": "背景区域",
                    "type": "background",
                    "x": 0,
                    "y": 0,
                    "width": 1,
                    "height": 1,
                    "color": "#87CEEB",
                    "priority": 0
                }
            ]
        }
        self.analyzer = ROIAnalyzer(self.roi_config)

    def test_region_flattening(self):
        """测试ROI区域展平和优先级排序"""
        regions = self.analyzer.regions

        # 应该有4个区域 (2个KW + 1个INST + 1个BG)
        self.assertEqual(len(regions), 4)

        # 检查优先级排序（从高到低）
        priorities = [r.get("priority", 0) for r in regions]
        self.assertEqual(priorities, [2, 2, 1, 0])  # KW(2), KW(2), INST(1), BG(0)

    def test_point_in_roi_keyword(self):
        """测试点在关键词区域内的匹配"""
        # 点 (0.3, 0.3) 应该在 KW_test_1 内
        roi_id = self.analyzer.find_roi_for_point(0.3, 0.3)
        self.assertEqual(roi_id, "KW_test_1")

        # 点 (0.7, 0.7) 应该在 KW_test_2 内
        roi_id = self.analyzer.find_roi_for_point(0.7, 0.7)
        self.assertEqual(roi_id, "KW_test_2")

    def test_point_in_roi_instruction(self):
        """测试点在指示语区域内的匹配"""
        # 点 (0.15, 0.15) 应该在 INST_test_1 内
        roi_id = self.analyzer.find_roi_for_point(0.15, 0.15)
        self.assertEqual(roi_id, "INST_test_1")

    def test_point_in_roi_background(self):
        """测试点在背景区域内的匹配"""
        # 点 (0.05, 0.05) 不在KW/INST内，应该匹配背景
        roi_id = self.analyzer.find_roi_for_point(0.05, 0.05)
        self.assertEqual(roi_id, "BG_test")

    def test_point_outside_all_rois(self):
        """测试点不在任何ROI内（理论上不会发生，因为BG覆盖全屏）"""
        # 创建没有背景的配置
        config_no_bg = {
            "keywords": [self.roi_config["keywords"][0]],
            "instructions": [],
            "background": []
        }
        analyzer_no_bg = ROIAnalyzer(config_no_bg)

        # 点 (0.05, 0.05) 不在任何ROI内
        roi_id = analyzer_no_bg.find_roi_for_point(0.05, 0.05)
        self.assertIsNone(roi_id)

    def test_roi_priority_matching(self):
        """测试ROI优先级匹配（KW > INST > BG）"""
        # 创建重叠的ROI配置
        overlapping_config = {
            "keywords": [
                {
                    "id": "KW_overlap",
                    "name": "关键词",
                    "type": "keyword",
                    "x": 0.2,
                    "y": 0.2,
                    "width": 0.3,
                    "height": 0.3,
                    "priority": 2
                }
            ],
            "instructions": [
                {
                    "id": "INST_overlap",
                    "name": "指示语",
                    "type": "instruction",
                    "x": 0.1,
                    "y": 0.1,
                    "width": 0.5,
                    "height": 0.5,
                    "priority": 1
                }
            ],
            "background": []
        }
        analyzer = ROIAnalyzer(overlapping_config)

        # 点 (0.3, 0.3) 同时在KW和INST内，应该匹配优先级更高的KW
        roi_id = analyzer.find_roi_for_point(0.3, 0.3)
        self.assertEqual(roi_id, "KW_overlap")

    def test_calculate_stats_entry_count(self):
        """测试ROI统计计算 - 进入次数"""
        # 模拟轨迹: 外部 -> KW区域 -> 外部 -> KW区域（2次进入）
        gaze_data = pd.DataFrame([
            {"x": 0.05, "y": 0.05, "timestamp": 0.0},  # BG
            {"x": 0.3, "y": 0.3, "timestamp": 0.5},    # 进入KW_test_1 (第1次)
            {"x": 0.05, "y": 0.05, "timestamp": 1.0},  # 离开到BG
            {"x": 0.3, "y": 0.3, "timestamp": 1.5},    # 进入KW_test_1 (第2次)
        ])

        stats = self.analyzer.calculate_stats(gaze_data)

        # 验证KW_test_1的进入次数
        kw_stats = stats["KW_test_1"]
        self.assertEqual(kw_stats["entry_count"], 2)
        self.assertEqual(kw_stats["regression_count"], 1)  # 回视次数 = 进入次数 - 1

    def test_calculate_stats_fixation_time(self):
        """测试ROI统计计算 - 注视时长"""
        # 模拟轨迹: 在KW区域停留1秒
        gaze_data = pd.DataFrame([
            {"x": 0.05, "y": 0.05, "timestamp": 0.0},  # BG
            {"x": 0.3, "y": 0.3, "timestamp": 0.5},    # 进入KW (dt=0.5)
            {"x": 0.35, "y": 0.35, "timestamp": 1.0},  # 仍在KW (dt=0.5)
            {"x": 0.32, "y": 0.32, "timestamp": 1.5},  # 仍在KW (dt=0.5)
            {"x": 0.05, "y": 0.05, "timestamp": 2.0},  # 离开到BG
        ])

        stats = self.analyzer.calculate_stats(gaze_data)

        # 验证KW_test_1的注视时长 (0.5 + 0.5 + 0.5 = 1.5秒)
        kw_stats = stats["KW_test_1"]
        self.assertAlmostEqual(kw_stats["fixation_time"], 1.5, places=2)

    def test_calculate_stats_points_inside(self):
        """测试ROI统计计算 - 内部点数"""
        gaze_data = pd.DataFrame([
            {"x": 0.05, "y": 0.05, "timestamp": 0.0},  # BG
            {"x": 0.3, "y": 0.3, "timestamp": 0.5},    # KW_test_1
            {"x": 0.35, "y": 0.35, "timestamp": 1.0},  # KW_test_1
            {"x": 0.05, "y": 0.05, "timestamp": 1.5},  # BG
        ])

        stats = self.analyzer.calculate_stats(gaze_data)

        # 验证KW_test_1的内部点数
        kw_stats = stats["KW_test_1"]
        self.assertEqual(kw_stats["points_inside"], 2)
        self.assertEqual(kw_stats["total_points"], 4)

    def test_calculate_stats_coverage_ratio(self):
        """测试ROI统计计算 - 覆盖率"""
        gaze_data = pd.DataFrame([
            {"x": 0.3, "y": 0.3, "timestamp": 0.0},    # KW_test_1
            {"x": 0.3, "y": 0.3, "timestamp": 0.5},    # KW_test_1
            {"x": 0.05, "y": 0.05, "timestamp": 1.0},  # BG
            {"x": 0.05, "y": 0.05, "timestamp": 1.5},  # BG
        ])

        stats = self.analyzer.calculate_stats(gaze_data)

        # 验证KW_test_1的覆盖率 (2/4 = 0.5)
        kw_stats = stats["KW_test_1"]
        self.assertAlmostEqual(kw_stats["coverage_ratio"], 0.5, places=2)

    def test_calculate_stats_empty_data(self):
        """测试空数据的统计计算"""
        gaze_data = pd.DataFrame([])

        stats = self.analyzer.calculate_stats(gaze_data)

        # 验证所有ROI的统计都是0
        for roi_id, roi_stats in stats.items():
            self.assertEqual(roi_stats["entry_count"], 0)
            self.assertEqual(roi_stats["points_inside"], 0)
            self.assertEqual(roi_stats["fixation_time"], 0)

    def test_calculate_stats_single_point(self):
        """测试单点数据的统计计算"""
        gaze_data = pd.DataFrame([
            {"x": 0.3, "y": 0.3, "timestamp": 0.0}
        ])

        stats = self.analyzer.calculate_stats(gaze_data)

        kw_stats = stats["KW_test_1"]
        self.assertEqual(kw_stats["entry_count"], 1)
        self.assertEqual(kw_stats["points_inside"], 1)
        self.assertEqual(kw_stats["regression_count"], 0)

    def test_get_summary(self):
        """测试汇总统计生成"""
        gaze_data = pd.DataFrame([
            {"x": 0.3, "y": 0.3, "timestamp": 0.0},    # KW_test_1
            {"x": 0.3, "y": 0.3, "timestamp": 0.5},    # KW_test_1
            {"x": 0.15, "y": 0.15, "timestamp": 1.0},  # INST_test_1
            {"x": 0.05, "y": 0.05, "timestamp": 1.5},  # BG_test
        ])

        stats = self.analyzer.calculate_stats(gaze_data)
        summary = self.analyzer.get_summary(stats)

        # 验证汇总统计
        self.assertIn("total_fixation_time", summary)
        self.assertIn("keywords_fixation_time", summary)
        self.assertIn("instructions_fixation_time", summary)
        self.assertIn("background_fixation_time", summary)
        self.assertIn("total_entry_count", summary)
        self.assertIn("most_visited_roi", summary)

        # 验证总进入次数 (KW_test_1:1次, INST_test_1:1次, BG_test:1次 = 3次)
        # 注意：最后一个点在BG但是从INST转移过来的，所以是3次而不是4次
        self.assertEqual(summary["total_entry_count"], 3)

        # 验证最多访问的ROI（KW_test_1有2个点）
        self.assertEqual(summary["most_visited_roi"], "KW_test_1")

    def test_boundary_points(self):
        """测试边界点的匹配"""
        # 测试左下角边界点
        roi_id = self.analyzer.find_roi_for_point(0.2, 0.2)
        self.assertEqual(roi_id, "KW_test_1")  # 应该匹配到KW_test_1

        # 测试右上角边界点
        roi_id = self.analyzer.find_roi_for_point(0.4, 0.4)
        self.assertEqual(roi_id, "KW_test_1")  # 应该匹配到KW_test_1

    def test_consecutive_same_roi(self):
        """测试连续在同一ROI内的情况"""
        gaze_data = pd.DataFrame([
            {"x": 0.3, "y": 0.3, "timestamp": 0.0},
            {"x": 0.31, "y": 0.31, "timestamp": 0.1},
            {"x": 0.32, "y": 0.32, "timestamp": 0.2},
            {"x": 0.33, "y": 0.33, "timestamp": 0.3},
        ])

        stats = self.analyzer.calculate_stats(gaze_data)

        kw_stats = stats["KW_test_1"]
        # 连续在同一ROI内，只应该算1次进入
        self.assertEqual(kw_stats["entry_count"], 1)
        self.assertEqual(kw_stats["points_inside"], 4)


class TestROIAnalyzerEdgeCases(unittest.TestCase):
    """ROI分析器边界情况测试"""

    def test_no_regions(self):
        """测试没有ROI区域的配置"""
        config = {
            "keywords": [],
            "instructions": [],
            "background": []
        }
        analyzer = ROIAnalyzer(config)

        self.assertEqual(len(analyzer.regions), 0)

        # 任意点都不应该匹配到ROI
        roi_id = analyzer.find_roi_for_point(0.5, 0.5)
        self.assertIsNone(roi_id)

    def test_missing_priority(self):
        """测试缺失优先级的ROI"""
        config = {
            "keywords": [
                {
                    "id": "KW_no_priority",
                    "name": "无优先级",
                    "type": "keyword",
                    "x": 0.2,
                    "y": 0.2,
                    "width": 0.2,
                    "height": 0.2
                    # 缺少 priority 字段
                }
            ],
            "instructions": [],
            "background": []
        }
        analyzer = ROIAnalyzer(config)

        # 应该使用默认优先级0
        self.assertEqual(analyzer.regions[0].get("priority", 0), 0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestROIAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestROIAnalyzerEdgeCases))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
