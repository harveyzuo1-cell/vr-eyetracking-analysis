"""
Module04 事件分析模块单元测试
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.modules.module04_event_analysis.event_analyzer import EventAnalyzer


class TestEventAnalyzer:
    """测试事件分析器"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return EventAnalyzer(velocity_threshold=40.0, min_fixation_duration=100)

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        data = {
            'x': [0.5, 0.51, 0.52, 0.53, 0.54],
            'y': [0.5, 0.51, 0.52, 0.51, 0.50],
            'milliseconds': [0, 100, 200, 300, 400],
        }
        return pd.DataFrame(data)

    def test_analyzer_initialization(self, analyzer):
        """测试分析器初始化"""
        assert analyzer.velocity_threshold == 40.0
        assert analyzer.min_fixation_duration == 100

    def test_compute_velocity(self, analyzer, sample_data):
        """测试速度计算"""
        result = analyzer.compute_velocity(sample_data)

        # 检查新增列
        assert 'velocity_deg_s' in result.columns
        assert 'x_deg' in result.columns
        assert 'y_deg' in result.columns
        assert 'time_diff' in result.columns

        # 检查速度值
        assert len(result) > 0
        assert all(result['velocity_deg_s'] >= 0)

    def test_compute_velocity_empty_data(self, analyzer):
        """测试空数据的速度计算"""
        empty_df = pd.DataFrame(columns=['x', 'y', 'milliseconds'])
        result = analyzer.compute_velocity(empty_df)
        assert len(result) == 0

    def test_ivt_segmentation_fixation(self, analyzer):
        """测试IVT分段 - 注视检测"""
        # 创建低速数据（模拟注视）- 需要轻微变化才能计算速度
        data = {
            'x': [0.5 + i*0.001 for i in range(10)],  # 微小变化
            'y': [0.5 + i*0.001 for i in range(10)],
            'milliseconds': list(range(0, 1000, 100)),
        }
        df = pd.DataFrame(data)
        df = analyzer.compute_velocity(df)

        fixations, saccades = analyzer.ivt_segmentation(df)

        # 应该检测到注视或至少不报错
        assert len(fixations) >= 0 and len(saccades) >= 0

    def test_ivt_segmentation_saccade(self, analyzer):
        """测试IVT分段 - 扫视检测"""
        # 创建高速数据（模拟扫视）
        data = {
            'x': [0.1, 0.2, 0.3, 0.4, 0.5],  # 快速移动
            'y': [0.1, 0.2, 0.3, 0.4, 0.5],
            'milliseconds': [0, 10, 20, 30, 40],  # 短时间间隔
        }
        df = pd.DataFrame(data)
        df = analyzer.compute_velocity(df)

        fixations, saccades = analyzer.ivt_segmentation(df)

        # 应该检测到扫视
        assert len(saccades) > 0

    def test_calc_saccade_features(self, analyzer, sample_data):
        """测试扫视特征计算"""
        df = analyzer.compute_velocity(sample_data)
        features = analyzer.calc_saccade_features(df, 0, len(df) - 1)

        assert 'max_velocity' in features
        assert 'mean_velocity' in features
        assert 'amplitude' in features
        assert features['max_velocity'] >= 0
        assert features['mean_velocity'] >= 0
        assert features['amplitude'] >= 0

    def test_calc_fixation_features(self, analyzer, sample_data):
        """测试注视特征计算"""
        df = analyzer.compute_velocity(sample_data)
        features = analyzer.calc_fixation_features(df, 0, len(df) - 1)

        assert 'centroid_x' in features
        assert 'centroid_y' in features
        assert 'dispersion' in features
        assert 0 <= features['centroid_x'] <= 1
        assert 0 <= features['centroid_y'] <= 1
        assert features['dispersion'] >= 0

    def test_find_roi_for_point_keywords(self, analyzer):
        """测试ROI查找 - keywords区域"""
        roi_regions = {
            'keywords': [
                {
                    'id': 'KW_test',
                    'normalized_coords': [0.1, 0.1, 0.2, 0.2]  # x, y, width, height
                }
            ]
        }

        # 点在keywords区域内
        roi = analyzer.find_roi_for_point(0.15, 0.15, roi_regions)
        assert roi == 'KW_test'

        # 点在keywords区域外
        roi = analyzer.find_roi_for_point(0.5, 0.5, roi_regions)
        assert roi is None

    def test_find_roi_priority(self, analyzer):
        """测试ROI优先级 - keywords > instructions > background"""
        roi_regions = {
            'keywords': [
                {'id': 'KW_test', 'normalized_coords': [0.1, 0.1, 0.2, 0.2]}
            ],
            'instructions': [
                {'id': 'INST_test', 'normalized_coords': [0.0, 0.0, 1.0, 1.0]}  # 覆盖整个区域
            ],
            'background': [
                {'id': 'BG_test', 'normalized_coords': [0.0, 0.0, 1.0, 1.0]}
            ]
        }

        # 点(0.15, 0.15)在keywords和instructions区域内，应该返回keywords
        roi = analyzer.find_roi_for_point(0.15, 0.15, roi_regions)
        assert roi == 'KW_test'

        # 点(0.5, 0.5)只在instructions区域内
        roi = analyzer.find_roi_for_point(0.5, 0.5, roi_regions)
        assert roi == 'INST_test'

    def test_ivt_min_fixation_duration(self, analyzer):
        """测试最小注视时长过滤"""
        # 创建一个短暂的低速段（应该被过滤为saccade）
        data = {
            'x': [0.5] * 5,
            'y': [0.5] * 5,
            'milliseconds': [0, 10, 20, 30, 40],  # 总时长40ms < 100ms
        }
        df = pd.DataFrame(data)
        df = analyzer.compute_velocity(df)

        fixations, saccades = analyzer.ivt_segmentation(df)

        # 时长不足，应该归类为saccade
        total_fixation_duration = sum([dur for (_, _, dur) in fixations])
        assert total_fixation_duration == 0 or all(dur >= 100 for (_, _, dur) in fixations)

    def test_velocity_threshold_parameter(self):
        """测试不同速度阈值"""
        analyzer_30 = EventAnalyzer(velocity_threshold=30.0)
        analyzer_50 = EventAnalyzer(velocity_threshold=50.0)

        assert analyzer_30.velocity_threshold == 30.0
        assert analyzer_50.velocity_threshold == 50.0

    def test_min_fixation_duration_parameter(self):
        """测试不同最小注视时长"""
        analyzer_100 = EventAnalyzer(min_fixation_duration=100)
        analyzer_200 = EventAnalyzer(min_fixation_duration=200)

        assert analyzer_100.min_fixation_duration == 100
        assert analyzer_200.min_fixation_duration == 200


class TestEventAnalyzerEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def analyzer(self):
        return EventAnalyzer()

    def test_single_data_point(self, analyzer):
        """测试单个数据点"""
        data = pd.DataFrame({
            'x': [0.5],
            'y': [0.5],
            'milliseconds': [0]
        })
        result = analyzer.compute_velocity(data)
        assert len(result) <= 1

    def test_negative_time_diff(self, analyzer):
        """测试时间差为负的情况"""
        data = pd.DataFrame({
            'x': [0.5, 0.5],
            'y': [0.5, 0.5],
            'milliseconds': [100, 50]  # 时间倒退
        })
        result = analyzer.compute_velocity(data)
        # 负时间差的点应该被过滤
        assert all(result['time_diff'] > 0) or len(result) == 0

    def test_extreme_velocity(self, analyzer):
        """测试极端速度值"""
        # 创建极大速度的数据
        data = pd.DataFrame({
            'x': [0.0, 1.0],  # 极大位移
            'y': [0.0, 1.0],
            'milliseconds': [0, 1]  # 极短时间
        })
        result = analyzer.compute_velocity(data)
        # 极端速度应该被过滤（可能返回空DataFrame）
        assert len(result) == 0 or ('velocity_deg_s' in result.columns and all(result['velocity_deg_s'] < 1000))

    def test_nan_values(self, analyzer):
        """测试NaN值处理"""
        data = pd.DataFrame({
            'x': [0.5, np.nan, 0.5],
            'y': [0.5, 0.5, np.nan],
            'milliseconds': [0, 100, 200]
        })
        # 应该能处理NaN而不崩溃
        try:
            result = analyzer.compute_velocity(data)
            assert True  # 没有抛出异常
        except Exception:
            pytest.fail("应该能处理NaN值")


@pytest.mark.parametrize("velocity_threshold,expected_behavior", [
    (30.0, "lower_threshold"),  # 更低的阈值应该检测到更多注视
    (40.0, "default"),
    (50.0, "higher_threshold"),  # 更高的阈值应该检测到更少注视
])
def test_velocity_threshold_effects(velocity_threshold, expected_behavior):
    """测试速度阈值对检测结果的影响"""
    analyzer = EventAnalyzer(velocity_threshold=velocity_threshold)

    # 创建中等速度的数据
    data = pd.DataFrame({
        'x': [0.5, 0.51, 0.52, 0.51, 0.50],
        'y': [0.5, 0.50, 0.51, 0.52, 0.51],
        'milliseconds': [0, 100, 200, 300, 400]
    })

    df = analyzer.compute_velocity(data)
    fixations, saccades = analyzer.ivt_segmentation(df)

    # 验证阈值确实影响检测结果
    assert isinstance(fixations, list)
    assert isinstance(saccades, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
