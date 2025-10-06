"""
Module02 数据预处理功能 pytest 测试套件
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from src.modules.module02_preprocessing import (
    QualityChecker,
    DataCleaner,
    DataSmoother,
    Pipeline
)


@pytest.fixture
def sample_data():
    """生成测试数据"""
    n_points = 100
    time = np.linspace(0, 1000, n_points)
    x = 0.5 + 0.3 * np.sin(2 * np.pi * time / 1000)
    y = 0.5 + 0.2 * np.cos(2 * np.pi * time / 1000)

    df = pd.DataFrame({'time': time, 'x': x, 'y': y})
    return df


@pytest.fixture
def noisy_data():
    """生成带噪声的测试数据"""
    n_points = 100
    time = np.linspace(0, 1000, n_points)
    x = 0.5 + 0.3 * np.sin(2 * np.pi * time / 1000)
    y = 0.5 + 0.2 * np.cos(2 * np.pi * time / 1000)

    # 添加噪声
    x += np.random.normal(0, 0.02, n_points)
    y += np.random.normal(0, 0.02, n_points)

    # 添加缺失值
    missing_idx = np.random.choice(n_points, size=5, replace=False)
    x[missing_idx] = np.nan
    y[missing_idx] = np.nan

    # 添加异常值
    outlier_idx = np.random.choice(n_points, size=3, replace=False)
    x[outlier_idx] += 0.5

    df = pd.DataFrame({'time': time, 'x': x, 'y': y})
    return df


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


class TestQualityChecker:
    """测试质量检测器"""

    def test_check_quality_clean_data(self, sample_data):
        """测试干净数据的质量检测"""
        checker = QualityChecker()
        report = checker.check_quality(sample_data)

        assert report['total_points'] == 100
        assert report['missing_values']['total_missing'] == 0
        assert report['quality_score'] >= 80

    def test_check_quality_noisy_data(self, noisy_data):
        """测试噪声数据的质量检测"""
        checker = QualityChecker()
        report = checker.check_quality(noisy_data)

        assert report['total_points'] == 100
        assert report['missing_values']['total_missing'] > 0
        assert report['outliers']['total_outliers'] > 0
        assert 0 <= report['quality_score'] <= 100

    def test_check_missing_values(self, noisy_data):
        """测试缺失值检测"""
        checker = QualityChecker()
        report = checker.check_quality(noisy_data)

        assert 'missing_values' in report
        assert 'x_missing' in report['missing_values']
        assert 'y_missing' in report['missing_values']
        assert report['missing_values']['total_missing'] >= 0

    def test_check_outliers_3sigma(self, noisy_data):
        """测试3sigma异常值检测"""
        checker = QualityChecker()
        config = {'outlier_method': '3sigma', 'outlier_threshold': 3.0}
        report = checker.check_quality(noisy_data, config)

        assert 'outliers' in report
        assert report['outliers']['total_outliers'] >= 0

    def test_check_outliers_iqr(self, noisy_data):
        """测试IQR异常值检测"""
        checker = QualityChecker()
        config = {'outlier_method': 'iqr'}
        report = checker.check_quality(noisy_data, config)

        assert 'outliers' in report
        assert report['outliers']['total_outliers'] >= 0

    def test_quality_score_range(self, sample_data):
        """测试质量分数范围"""
        checker = QualityChecker()
        report = checker.check_quality(sample_data)

        assert 0 <= report['quality_score'] <= 100


class TestDataCleaner:
    """测试数据清洗器"""

    def test_clean_interpolate_missing(self, noisy_data):
        """测试插值处理缺失值"""
        cleaner = DataCleaner()
        config = {'missing_method': 'interpolate'}
        df_cleaned, log = cleaner.clean(noisy_data, config)

        assert df_cleaned.isna().sum().sum() == 0
        assert log['steps'][0]['step'] == 'missing_value_handling'

    def test_clean_drop_missing(self, noisy_data):
        """测试删除缺失值"""
        cleaner = DataCleaner()
        config = {'missing_method': 'drop'}
        df_cleaned, log = cleaner.clean(noisy_data, config)

        assert len(df_cleaned) <= len(noisy_data)
        assert df_cleaned.isna().sum().sum() == 0

    def test_clean_outliers_interpolate(self, noisy_data):
        """测试插值处理异常值"""
        cleaner = DataCleaner()
        config = {
            'outlier_method': '3sigma',
            'outlier_action': 'interpolate'
        }
        df_cleaned, log = cleaner.clean(noisy_data, config)

        assert 'outlier_handling' in [step['step'] for step in log['steps']]

    def test_clean_outliers_clip(self, noisy_data):
        """测试裁剪异常值"""
        cleaner = DataCleaner()
        config = {
            'outlier_method': '3sigma',
            'outlier_action': 'clip'
        }
        df_cleaned, log = cleaner.clean(noisy_data, config)

        assert len(df_cleaned) == len(noisy_data)

    def test_clip_coordinates(self, sample_data):
        """测试坐标裁剪"""
        cleaner = DataCleaner()
        config = {
            'clip_range': True,
            'x_range': [0, 1],
            'y_range': [0, 1]
        }
        df_cleaned, log = cleaner.clean(sample_data, config)

        assert df_cleaned['x'].min() >= 0
        assert df_cleaned['x'].max() <= 1
        assert df_cleaned['y'].min() >= 0
        assert df_cleaned['y'].max() <= 1


class TestDataSmoother:
    """测试数据平滑器"""

    def test_smooth_moving_average(self, sample_data):
        """测试移动平均"""
        smoother = DataSmoother()
        config = {'method': 'moving_average', 'window_size': 5}
        df_smoothed, log = smoother.smooth(sample_data, config)

        assert len(df_smoothed) == len(sample_data)
        assert log['method'] == 'moving_average'
        assert 'x' in log['columns_smoothed']
        assert 'y' in log['columns_smoothed']

    def test_smooth_gaussian(self, sample_data):
        """测试高斯滤波"""
        smoother = DataSmoother()
        config = {'method': 'gaussian', 'sigma': 1.5}
        df_smoothed, log = smoother.smooth(sample_data, config)

        assert len(df_smoothed) == len(sample_data)
        assert log['method'] == 'gaussian'

    def test_smooth_median(self, sample_data):
        """测试中值滤波"""
        smoother = DataSmoother()
        config = {'method': 'median', 'window_size': 5}
        df_smoothed, log = smoother.smooth(sample_data, config)

        assert len(df_smoothed) == len(sample_data)
        assert log['method'] == 'median'

    def test_smooth_savgol(self, sample_data):
        """测试Savitzky-Golay滤波"""
        smoother = DataSmoother()
        config = {'method': 'savgol', 'window_size': 5, 'polyorder': 3}
        df_smoothed, log = smoother.smooth(sample_data, config)

        assert len(df_smoothed) == len(sample_data)
        assert log['method'] == 'savgol'

    def test_smooth_selective_columns(self, sample_data):
        """测试选择性平滑"""
        smoother = DataSmoother()
        config = {'method': 'gaussian', 'smooth_x': True, 'smooth_y': False}
        df_smoothed, log = smoother.smooth(sample_data, config)

        assert 'x' in log['columns_smoothed']
        assert 'y' not in log['columns_smoothed']


class TestPipeline:
    """测试预处理流水线"""

    def test_pipeline_full_process(self, noisy_data):
        """测试完整流水线"""
        pipeline = Pipeline()
        config = {
            'enable_quality_check': True,
            'enable_cleaning': True,
            'enable_smoothing': True
        }
        df_processed, log = pipeline.process(noisy_data, config)

        assert len(df_processed) > 0
        assert 'steps' in log
        assert len(log['steps']) == 3

    def test_pipeline_quality_only(self, sample_data):
        """测试仅质量检测"""
        pipeline = Pipeline()
        config = {
            'enable_quality_check': True,
            'enable_cleaning': False,
            'enable_smoothing': False
        }
        df_processed, log = pipeline.process(sample_data, config)

        assert len(log['steps']) == 1
        assert log['steps'][0]['step'] == 'quality_check'

    def test_pipeline_clean_only(self, noisy_data):
        """测试仅数据清洗"""
        pipeline = Pipeline()
        config = {
            'enable_quality_check': False,
            'enable_cleaning': True,
            'enable_smoothing': False
        }
        df_processed, log = pipeline.process(noisy_data, config)

        assert len(log['steps']) == 1
        assert log['steps'][0]['step'] == 'cleaning'

    def test_pipeline_file_processing(self, sample_data, temp_dir):
        """测试文件处理"""
        pipeline = Pipeline()

        # 保存测试数据
        input_path = temp_dir / "test_input.csv"
        output_path = temp_dir / "test_output.csv"
        sample_data.to_csv(input_path, index=False)

        # 处理文件
        result = pipeline.process_file(str(input_path), str(output_path))

        assert result['success'] is True
        assert output_path.exists()

    def test_pipeline_default_config(self):
        """测试默认配置"""
        pipeline = Pipeline()
        config = pipeline.get_default_config()

        assert 'enable_quality_check' in config
        assert 'enable_cleaning' in config
        assert 'enable_smoothing' in config
        assert 'quality_check_config' in config
        assert 'cleaning_config' in config
        assert 'smoothing_config' in config

    def test_pipeline_min_quality_score(self, noisy_data):
        """测试最低质量分数要求"""
        pipeline = Pipeline()
        config = {
            'enable_quality_check': True,
            'min_quality_score': 90
        }
        df_processed, log = pipeline.process(noisy_data, config)

        if 'warning' in log:
            assert '质量分数过低' in log['warning']


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self, noisy_data):
        """测试完整工作流程"""
        # 1. 质量检测
        checker = QualityChecker()
        initial_report = checker.check_quality(noisy_data)
        initial_score = initial_report['quality_score']

        # 2. 清洗
        cleaner = DataCleaner()
        df_cleaned, _ = cleaner.clean(noisy_data)

        # 3. 平滑
        smoother = DataSmoother()
        df_smoothed, _ = smoother.smooth(df_cleaned)

        # 4. 再次质量检测
        final_report = checker.check_quality(df_smoothed)
        final_score = final_report['quality_score']

        # 质量分数应该提升
        assert final_score >= initial_score or final_score > 80
        assert df_smoothed.isna().sum().sum() == 0
