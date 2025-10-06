"""
数据清洗器

提供多种数据清洗功能:
- 缺失值处理（插值、前向填充、删除）
- 异常值处理（插值、删除、裁剪）
- 坐标范围裁剪
- 数据重采样
"""
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        self.config = {
            'missing_method': 'interpolate',  # interpolate, ffill, drop
            'outlier_method': '3sigma',  # 3sigma, iqr
            'outlier_threshold': 3.0,
            'outlier_action': 'interpolate',  # interpolate, drop, clip
            'clip_range': True,
            'x_range': [0, 1],
            'y_range': [0, 1],
            'resample': False,
            'target_rate': 60  # Hz
        }

    def clean(self, df: pd.DataFrame, config: Optional[Dict] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        完整清洗流程

        Args:
            df: 原始数据DataFrame
            config: 自定义配置

        Returns:
            (清洗后的DataFrame, 清洗日志)
        """
        if config:
            self.config.update(config)

        logger.info(f"开始数据清洗，原始数据点数: {len(df)}")

        df_cleaned = df.copy()
        cleaning_log = {
            'original_points': len(df),
            'steps': []
        }

        # 1. 处理缺失值
        df_cleaned, step1_log = self._handle_missing(df_cleaned)
        cleaning_log['steps'].append(step1_log)

        # 2. 处理异常值
        df_cleaned, step2_log = self._handle_outliers(df_cleaned)
        cleaning_log['steps'].append(step2_log)

        # 3. 坐标裁剪
        if self.config['clip_range']:
            df_cleaned, step3_log = self._clip_coordinates(df_cleaned)
            cleaning_log['steps'].append(step3_log)

        # 4. 重采样（可选）
        if self.config['resample']:
            df_cleaned, step4_log = self._resample_data(df_cleaned)
            cleaning_log['steps'].append(step4_log)

        cleaning_log['final_points'] = len(df_cleaned)
        cleaning_log['points_removed'] = cleaning_log['original_points'] - cleaning_log['final_points']

        logger.info(f"数据清洗完成，最终数据点数: {len(df_cleaned)}")

        return df_cleaned, cleaning_log

    def _handle_missing(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        处理缺失值

        Args:
            df: 数据DataFrame

        Returns:
            (处理后的DataFrame, 日志)
        """
        method = self.config['missing_method']
        original_missing = int(df.isna().sum().sum())

        df_result = df.copy()

        if method == 'interpolate':
            df_result = df_result.interpolate(method='linear', limit_direction='both')
        elif method == 'ffill':
            df_result = df_result.fillna(method='ffill')
        elif method == 'drop':
            df_result = df_result.dropna()
        else:
            logger.warning(f"未知的缺失值处理方法: {method}，跳过处理")

        log = {
            'step': 'missing_value_handling',
            'method': method,
            'original_missing': original_missing,
            'remaining_missing': int(df_result.isna().sum().sum()),
            'rows_removed': len(df) - len(df_result) if method == 'drop' else 0
        }

        logger.debug(f"缺失值处理 ({method}): 原始 {original_missing} 个，剩余 {log['remaining_missing']} 个")

        return df_result, log

    def _handle_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        处理异常值

        Args:
            df: 数据DataFrame

        Returns:
            (处理后的DataFrame, 日志)
        """
        method = self.config['outlier_method']
        threshold = self.config['outlier_threshold']
        action = self.config['outlier_action']

        df_result = df.copy()
        outliers_handled = 0

        for col in ['x', 'y']:
            if col not in df.columns:
                continue

            # 检测异常值
            valid_data = df[col].dropna()
            if len(valid_data) == 0:
                continue

            if method == '3sigma':
                mean = valid_data.mean()
                std = valid_data.std()
                outlier_mask = np.abs(df_result[col] - mean) > threshold * std
            elif method == 'iqr':
                q1, q3 = valid_data.quantile([0.25, 0.75])
                iqr = q3 - q1
                outlier_mask = (df_result[col] < q1 - 1.5 * iqr) | (df_result[col] > q3 + 1.5 * iqr)
            else:
                logger.warning(f"未知的异常值检测方法: {method}，使用默认3sigma")
                mean = valid_data.mean()
                std = valid_data.std()
                outlier_mask = np.abs(df_result[col] - mean) > threshold * std

            # 处理异常值
            if action == 'interpolate':
                df_result.loc[outlier_mask, col] = np.nan
                df_result[col] = df_result[col].interpolate(method='linear', limit_direction='both')
            elif action == 'drop':
                df_result = df_result[~outlier_mask]
            elif action == 'clip':
                if method == '3sigma':
                    lower = mean - threshold * std
                    upper = mean + threshold * std
                else:  # iqr
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                df_result[col] = df_result[col].clip(lower, upper)
            else:
                logger.warning(f"未知的异常值处理方式: {action}，跳过处理")

            outliers_handled += int(outlier_mask.sum())

        log = {
            'step': 'outlier_handling',
            'method': method,
            'action': action,
            'outliers_handled': outliers_handled,
            'rows_removed': len(df) - len(df_result) if action == 'drop' else 0
        }

        logger.debug(f"异常值处理 ({method}, {action}): 处理了 {outliers_handled} 个异常值")

        return df_result, log

    def _clip_coordinates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        裁剪坐标到指定范围

        Args:
            df: 数据DataFrame

        Returns:
            (裁剪后的DataFrame, 日志)
        """
        x_min, x_max = self.config['x_range']
        y_min, y_max = self.config['y_range']

        df_result = df.copy()

        original_out_of_range = 0
        if 'x' in df.columns:
            original_out_of_range += int(((df['x'] < x_min) | (df['x'] > x_max)).sum())
            df_result['x'] = df_result['x'].clip(x_min, x_max)

        if 'y' in df.columns:
            original_out_of_range += int(((df['y'] < y_min) | (df['y'] > y_max)).sum())
            df_result['y'] = df_result['y'].clip(y_min, y_max)

        log = {
            'step': 'coordinate_clipping',
            'x_range': [x_min, x_max],
            'y_range': [y_min, y_max],
            'points_clipped': original_out_of_range
        }

        logger.debug(f"坐标裁剪: 裁剪了 {original_out_of_range} 个点到范围 [{x_min}, {x_max}] x [{y_min}, {y_max}]")

        return df_result, log

    def _resample_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        重采样到目标频率

        Args:
            df: 数据DataFrame

        Returns:
            (重采样后的DataFrame, 日志)
        """
        if 'time' not in df.columns:
            log = {
                'step': 'resampling',
                'status': 'skipped_no_time',
                'message': '缺少time列，跳过重采样'
            }
            logger.debug("重采样: 缺少time列，跳过")
            return df, log

        if len(df) < 2:
            log = {
                'step': 'resampling',
                'status': 'skipped_insufficient_data',
                'message': '数据点不足，跳过重采样'
            }
            logger.debug("重采样: 数据点不足，跳过")
            return df, log

        target_rate = self.config['target_rate']
        interval = 1000.0 / target_rate  # ms

        # 创建均匀时间轴
        time_min = df['time'].min()
        time_max = df['time'].max()
        time_new = np.arange(time_min, time_max, interval)

        # 插值
        df_resampled = pd.DataFrame({'time': time_new})

        for col in df.columns:
            if col != 'time':
                try:
                    # 移除缺失值
                    valid_mask = ~df[col].isna()
                    if valid_mask.sum() < 2:
                        df_resampled[col] = np.nan
                        continue

                    f = interp1d(
                        df.loc[valid_mask, 'time'].values,
                        df.loc[valid_mask, col].values,
                        kind='linear',
                        fill_value='extrapolate'
                    )
                    df_resampled[col] = f(time_new)
                except Exception as e:
                    logger.warning(f"列 {col} 插值失败: {str(e)}")
                    df_resampled[col] = np.nan

        log = {
            'step': 'resampling',
            'status': 'success',
            'original_points': len(df),
            'resampled_points': len(df_resampled),
            'target_rate': target_rate,
            'interval_ms': interval
        }

        logger.debug(f"重采样: {len(df)} 点 -> {len(df_resampled)} 点 ({target_rate}Hz)")

        return df_resampled, log

    def clean_file(self, input_path: str, output_path: str, config: Optional[Dict] = None) -> Dict:
        """
        清洗单个文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            config: 自定义配置

        Returns:
            清洗结果字典
        """
        try:
            # 读取数据
            df = pd.read_csv(input_path)

            # 清洗数据
            df_cleaned, cleaning_log = self.clean(df, config)

            # 保存结果
            df_cleaned.to_csv(output_path, index=False)

            return {
                'success': True,
                'input_file': input_path,
                'output_file': output_path,
                'log': cleaning_log
            }

        except Exception as e:
            logger.error(f"清洗文件 {input_path} 时出错: {str(e)}")
            return {
                'success': False,
                'input_file': input_path,
                'error': str(e)
            }
