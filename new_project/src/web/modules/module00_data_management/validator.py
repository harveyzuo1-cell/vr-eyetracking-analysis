"""
Module 00: 数据验证器
Data Validator
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""

    ALLOWED_EXTENSIONS = {'csv', 'txt'}
    REQUIRED_COLUMNS = ['x', 'y', 'time']  # 基础必需列
    OPTIONAL_COLUMNS = ['z', 'abs_datetime', 'milliseconds']  # 可选列

    def is_allowed_file(self, filename):
        """
        检查文件扩展名是否允许

        Args:
            filename: 文件名

        Returns:
            bool: 是否允许
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def validate_dataframe(self, df):
        """
        验证DataFrame的数据质量

        Args:
            df: pandas DataFrame

        Returns:
            dict: 验证结果
                {
                    'valid': bool,
                    'errors': list,
                    'warnings': list,
                    'quality_score': float (0-100)
                }
        """
        errors = []
        warnings = []
        score = 100.0

        # 1. 检查必需列
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必需列: {', '.join(missing_columns)}")
            score -= 50

        # 2. 检查数据点数量
        if len(df) < 100:
            warnings.append(f"数据点数量过少: {len(df)} (建议至少100点)")
            score -= 10
        elif len(df) > 50000:
            warnings.append(f"数据点数量过多: {len(df)} (可能影响性能)")

        # 3. 检查缺失值
        missing_count = df.isnull().sum().sum()
        missing_ratio = missing_count / (df.shape[0] * df.shape[1])
        if missing_ratio > 0:
            warnings.append(f"存在缺失值: {missing_count} ({missing_ratio*100:.2f}%)")
            score -= min(20, missing_ratio * 100)

        # 4. 检查坐标范围
        if 'x' in df.columns and 'y' in df.columns:
            x_min, x_max = df['x'].min(), df['x'].max()
            y_min, y_max = df['y'].min(), df['y'].max()

            # 检查是否在[0, 1]范围内(归一化坐标)
            if x_min < -0.1 or x_max > 1.1:
                warnings.append(f"X坐标超出正常范围: [{x_min:.3f}, {x_max:.3f}]")
                score -= 10

            if y_min < -0.1 or y_max > 1.1:
                warnings.append(f"Y坐标超出正常范围: [{y_min:.3f}, {y_max:.3f}]")
                score -= 10

        # 5. 检查时间列
        if 'time' in df.columns:
            time_diff = df['time'].diff()

            # 检查时间是否单调递增
            if (time_diff[1:] < 0).any():
                errors.append("时间戳不是单调递增的")
                score -= 15

            # 检查采样率
            median_interval = time_diff.median()
            if median_interval > 0:
                sample_rate = 1000.0 / median_interval  # ms to Hz
                if sample_rate < 30:
                    warnings.append(f"采样率较低: {sample_rate:.1f} Hz (建议>30Hz)")
                    score -= 5
                elif sample_rate > 250:
                    warnings.append(f"采样率异常高: {sample_rate:.1f} Hz")
                    score -= 5

        # 6. 检查异常值
        if 'x' in df.columns and 'y' in df.columns:
            x_outliers = self._detect_outliers(df['x'].values)
            y_outliers = self._detect_outliers(df['y'].values)

            outlier_count = x_outliers.sum() + y_outliers.sum()
            outlier_ratio = outlier_count / (len(df) * 2)

            if outlier_ratio > 0.05:
                warnings.append(
                    f"异常值较多: {outlier_count} ({outlier_ratio*100:.2f}%)"
                )
                score -= min(10, outlier_ratio * 100)

        # 确保分数在0-100范围内
        score = max(0.0, min(100.0, score))

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'quality_score': round(score, 1)
        }

    def _detect_outliers(self, data, method='iqr', threshold=1.5):
        """
        检测异常值

        Args:
            data: numpy array
            method: 'iqr' or '3sigma'
            threshold: 阈值

        Returns:
            numpy array of bool: 异常值mask
        """
        if method == 'iqr':
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            return (data < lower_bound) | (data > upper_bound)

        elif method == '3sigma':
            mean = np.mean(data)
            std = np.std(data)
            return np.abs(data - mean) > threshold * std

        return np.zeros(len(data), dtype=bool)

    def analyze_statistics(self, df):
        """
        分析数据统计信息

        Args:
            df: pandas DataFrame

        Returns:
            dict: 统计信息
        """
        stats = {
            'total_points': len(df),
            'columns': list(df.columns),
            'missing_values': int(df.isnull().sum().sum())
        }

        # 时间统计
        if 'time' in df.columns:
            stats['time_range'] = [
                float(df['time'].min()),
                float(df['time'].max())
            ]
            stats['duration'] = float(df['time'].max() - df['time'].min())

            # 采样率
            time_diff = df['time'].diff()
            median_interval = time_diff.median()
            if median_interval > 0:
                stats['sample_rate'] = round(1000.0 / median_interval, 1)

        # 坐标统计
        if 'x' in df.columns:
            stats['x_range'] = [float(df['x'].min()), float(df['x'].max())]
            stats['x_mean'] = float(df['x'].mean())
            stats['x_std'] = float(df['x'].std())

        if 'y' in df.columns:
            stats['y_range'] = [float(df['y'].min()), float(df['y'].max())]
            stats['y_mean'] = float(df['y'].mean())
            stats['y_std'] = float(df['y'].std())

        return stats
