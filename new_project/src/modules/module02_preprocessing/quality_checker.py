"""
数据质量检测器

检测眼动追踪数据中的质量问题:
- 缺失值检测
- 异常值检测
- 坐标范围检查
- 采样率分析
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class QualityChecker:
    """数据质量检测器"""

    def __init__(self):
        self.config = {
            'outlier_method': '3sigma',  # 3sigma 或 iqr
            'outlier_threshold': 3.0,
            'expected_range_x': [0, 1],
            'expected_range_y': [0, 1],
            'expected_sampling_rate': 60,  # Hz
            'sampling_tolerance': 5  # Hz
        }

    def check_quality(self, df: pd.DataFrame, config: Optional[Dict] = None) -> Dict:
        """
        完整质量检测流程

        Args:
            df: 眼动数据DataFrame (需要包含 x, y 列，可选 time 列)
            config: 自定义配置

        Returns:
            质量检测报告字典
        """
        if config:
            self.config.update(config)

        logger.info(f"开始质量检测，数据点数: {len(df)}")

        report = {
            'total_points': len(df),
            'missing_values': self._check_missing(df),
            'outliers': self._check_outliers(df),
            'range_violations': self._check_range(df),
            'sampling_issues': self._check_sampling(df),
            'quality_score': 0
        }

        # 计算综合质量分数（0-100）
        report['quality_score'] = self._calculate_quality_score(report)

        logger.info(f"质量检测完成，质量分数: {report['quality_score']:.2f}/100")

        return report

    def _check_missing(self, df: pd.DataFrame) -> Dict:
        """
        检测缺失值

        Args:
            df: 数据DataFrame

        Returns:
            缺失值信息字典
        """
        missing_info = {
            'x_missing': int(df['x'].isna().sum()) if 'x' in df.columns else 0,
            'y_missing': int(df['y'].isna().sum()) if 'y' in df.columns else 0,
            'time_missing': int(df['time'].isna().sum()) if 'time' in df.columns else 0,
            'total_missing': int(df.isna().sum().sum()),
            'missing_indices': df[df.isna().any(axis=1)].index.tolist()
        }

        logger.debug(f"缺失值检测: 总计 {missing_info['total_missing']} 个缺失值")

        return missing_info

    def _check_outliers(self, df: pd.DataFrame) -> Dict:
        """
        检测异常值

        Args:
            df: 数据DataFrame

        Returns:
            异常值信息字典
        """
        method = self.config['outlier_method']
        threshold = self.config['outlier_threshold']

        outliers = {
            'x_outliers': [],
            'y_outliers': [],
            'total_outliers': 0
        }

        for col in ['x', 'y']:
            if col not in df.columns:
                continue

            # 过滤掉缺失值
            valid_data = df[col].dropna()
            if len(valid_data) == 0:
                continue

            if method == '3sigma':
                mean = valid_data.mean()
                std = valid_data.std()
                outlier_mask = np.abs(df[col] - mean) > threshold * std
            elif method == 'iqr':
                q1, q3 = valid_data.quantile([0.25, 0.75])
                iqr = q3 - q1
                outlier_mask = (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
            else:
                logger.warning(f"未知的异常值检测方法: {method}，使用默认3sigma")
                mean = valid_data.mean()
                std = valid_data.std()
                outlier_mask = np.abs(df[col] - mean) > threshold * std

            outlier_indices = df[outlier_mask].index.tolist()
            outliers[f'{col}_outliers'] = outlier_indices
            outliers['total_outliers'] += len(outlier_indices)

        logger.debug(f"异常值检测 ({method}): 总计 {outliers['total_outliers']} 个异常值")

        return outliers

    def _check_range(self, df: pd.DataFrame) -> Dict:
        """
        检查坐标范围

        Args:
            df: 数据DataFrame

        Returns:
            范围违规信息字典
        """
        x_min, x_max = self.config['expected_range_x']
        y_min, y_max = self.config['expected_range_y']

        range_violations = {
            'x_below': int((df['x'] < x_min).sum()) if 'x' in df.columns else 0,
            'x_above': int((df['x'] > x_max).sum()) if 'x' in df.columns else 0,
            'y_below': int((df['y'] < y_min).sum()) if 'y' in df.columns else 0,
            'y_above': int((df['y'] > y_max).sum()) if 'y' in df.columns else 0
        }
        range_violations['total'] = sum(range_violations.values())

        logger.debug(f"范围检查: 总计 {range_violations['total']} 个超出范围的点")

        return range_violations

    def _check_sampling(self, df: pd.DataFrame) -> Dict:
        """
        检查采样率

        Args:
            df: 数据DataFrame

        Returns:
            采样率信息字典
        """
        if 'time' not in df.columns:
            return {'status': 'no_time_column'}

        time_values = df['time'].dropna().values
        if len(time_values) < 2:
            return {'status': 'insufficient_data'}

        time_diff = np.diff(time_values)
        if len(time_diff) == 0:
            return {'status': 'no_time_differences'}

        median_interval = float(np.median(time_diff))  # ms
        actual_rate = 1000.0 / median_interval if median_interval > 0 else 0  # Hz

        expected_rate = self.config['expected_sampling_rate']
        tolerance = self.config['sampling_tolerance']

        is_stable = abs(actual_rate - expected_rate) <= tolerance

        sampling_info = {
            'actual_rate': round(actual_rate, 2),
            'expected_rate': expected_rate,
            'is_stable': is_stable,
            'median_interval_ms': round(median_interval, 2),
            'std_interval_ms': round(float(np.std(time_diff)), 2)
        }

        logger.debug(f"采样率检查: 实际 {actual_rate:.2f}Hz, 期望 {expected_rate}Hz, 稳定: {is_stable}")

        return sampling_info

    def _calculate_quality_score(self, report: Dict) -> float:
        """
        计算综合质量分数

        Args:
            report: 质量检测报告

        Returns:
            质量分数 (0-100)
        """
        score = 100.0

        total_points = report['total_points']
        if total_points == 0:
            return 0.0

        # 缺失值扣分 (最多扣30分)
        missing_ratio = report['missing_values']['total_missing'] / total_points
        score -= missing_ratio * 30

        # 异常值扣分 (最多扣30分)
        outlier_ratio = report['outliers']['total_outliers'] / total_points
        score -= outlier_ratio * 30

        # 范围违规扣分 (最多扣20分)
        range_ratio = report['range_violations']['total'] / total_points
        score -= range_ratio * 20

        # 采样率不稳定扣分 (扣20分)
        sampling_issues = report['sampling_issues']
        if isinstance(sampling_issues, dict) and not sampling_issues.get('is_stable', True):
            score -= 20

        return max(0.0, min(100.0, score))

    def batch_check(self, data_files: List[Path], config: Optional[Dict] = None) -> Dict:
        """
        批量质量检测

        Args:
            data_files: 数据文件路径列表
            config: 自定义配置

        Returns:
            批量检测结果字典
        """
        logger.info(f"开始批量质量检测，共 {len(data_files)} 个文件")

        results = {}
        for file_path in data_files:
            try:
                # 读取CSV文件
                df = pd.read_csv(file_path)

                # 检测质量
                report = self.check_quality(df, config)

                results[file_path.name] = {
                    'success': True,
                    'report': report
                }

            except Exception as e:
                logger.error(f"检测文件 {file_path.name} 时出错: {str(e)}")
                results[file_path.name] = {
                    'success': False,
                    'error': str(e)
                }

        # 统计汇总
        successful = sum(1 for r in results.values() if r['success'])
        avg_score = np.mean([
            r['report']['quality_score']
            for r in results.values()
            if r['success']
        ]) if successful > 0 else 0

        summary = {
            'total_files': len(data_files),
            'successful': successful,
            'failed': len(data_files) - successful,
            'average_quality_score': round(float(avg_score), 2),
            'results': results
        }

        logger.info(f"批量质量检测完成，平均质量分数: {avg_score:.2f}/100")

        return summary
