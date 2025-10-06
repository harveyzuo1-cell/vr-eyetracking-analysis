"""
数据平滑器

提供多种数据平滑方法:
- 移动平均
- 高斯滤波
- 中值滤波
- Savitzky-Golay滤波
"""
import numpy as np
import pandas as pd
from scipy.signal import medfilt, savgol_filter
from scipy.ndimage import gaussian_filter1d
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DataSmoother:
    """数据平滑器"""

    def __init__(self):
        self.config = {
            'method': 'gaussian',  # moving_average, gaussian, median, savgol
            'window_size': 5,
            'sigma': 1.5,
            'polyorder': 3,
            'smooth_x': True,
            'smooth_y': True
        }

    def smooth(self, df: pd.DataFrame, config: Optional[Dict] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        应用平滑滤波

        Args:
            df: 原始数据DataFrame
            config: 自定义配置

        Returns:
            (平滑后的DataFrame, 平滑日志)
        """
        if config:
            self.config.update(config)

        logger.info(f"开始数据平滑，数据点数: {len(df)}")

        df_smoothed = df.copy()
        method = self.config['method']

        smoothing_log = {
            'method': method,
            'columns_smoothed': []
        }

        # 选择要平滑的列
        cols_to_smooth = []
        if self.config['smooth_x'] and 'x' in df.columns:
            cols_to_smooth.append('x')
        if self.config['smooth_y'] and 'y' in df.columns:
            cols_to_smooth.append('y')

        # 应用平滑
        for col in cols_to_smooth:
            try:
                if method == 'moving_average':
                    df_smoothed[col] = self._moving_average(df[col].values)
                elif method == 'gaussian':
                    df_smoothed[col] = self._gaussian_filter(df[col].values)
                elif method == 'median':
                    df_smoothed[col] = self._median_filter(df[col].values)
                elif method == 'savgol':
                    df_smoothed[col] = self._savgol_filter(df[col].values)
                else:
                    logger.warning(f"未知的平滑方法: {method}，跳过平滑")
                    continue

                smoothing_log['columns_smoothed'].append(col)
            except Exception as e:
                logger.error(f"平滑列 {col} 时出错: {str(e)}")

        logger.info(f"数据平滑完成，平滑了 {len(smoothing_log['columns_smoothed'])} 列")

        return df_smoothed, smoothing_log

    def _moving_average(self, data: np.ndarray) -> np.ndarray:
        """
        移动平均滤波

        Args:
            data: 输入数据

        Returns:
            平滑后的数据
        """
        window_size = self.config['window_size']

        if len(data) < window_size:
            logger.warning(f"数据点数 {len(data)} 小于窗口大小 {window_size}，使用原始数据")
            return data

        # 使用卷积实现移动平均
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(data, kernel, mode='same')

        logger.debug(f"移动平均: 窗口大小 {window_size}")

        return smoothed

    def _gaussian_filter(self, data: np.ndarray) -> np.ndarray:
        """
        高斯滤波

        Args:
            data: 输入数据

        Returns:
            平滑后的数据
        """
        sigma = self.config['sigma']

        if len(data) < 3:
            logger.warning(f"数据点数 {len(data)} 太少，跳过高斯滤波")
            return data

        smoothed = gaussian_filter1d(data, sigma=sigma, mode='nearest')

        logger.debug(f"高斯滤波: sigma={sigma}")

        return smoothed

    def _median_filter(self, data: np.ndarray) -> np.ndarray:
        """
        中值滤波

        Args:
            data: 输入数据

        Returns:
            平滑后的数据
        """
        window_size = self.config['window_size']

        # 确保窗口大小为奇数
        if window_size % 2 == 0:
            window_size += 1
            logger.debug(f"中值滤波窗口大小调整为奇数: {window_size}")

        if len(data) < window_size:
            logger.warning(f"数据点数 {len(data)} 小于窗口大小 {window_size}，使用原始数据")
            return data

        smoothed = medfilt(data, kernel_size=window_size)

        logger.debug(f"中值滤波: 窗口大小 {window_size}")

        return smoothed

    def _savgol_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Savitzky-Golay滤波

        Args:
            data: 输入数据

        Returns:
            平滑后的数据
        """
        window_size = self.config['window_size']
        polyorder = self.config['polyorder']

        # 确保窗口大小为奇数
        if window_size % 2 == 0:
            window_size += 1
            logger.debug(f"Savgol滤波窗口大小调整为奇数: {window_size}")

        # 确保多项式阶数小于窗口大小
        if polyorder >= window_size:
            polyorder = window_size - 1
            logger.debug(f"Savgol多项式阶数调整为: {polyorder}")

        if len(data) < window_size:
            logger.warning(f"数据点数 {len(data)} 小于窗口大小 {window_size}，使用原始数据")
            return data

        try:
            smoothed = savgol_filter(data, window_length=window_size, polyorder=polyorder, mode='nearest')
            logger.debug(f"Savgol滤波: 窗口大小 {window_size}, 多项式阶数 {polyorder}")
        except Exception as e:
            logger.error(f"Savgol滤波失败: {str(e)}，使用原始数据")
            smoothed = data

        return smoothed

    def smooth_file(self, input_path: str, output_path: str, config: Optional[Dict] = None) -> Dict:
        """
        平滑单个文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            config: 自定义配置

        Returns:
            平滑结果字典
        """
        try:
            # 读取数据
            df = pd.read_csv(input_path)

            # 平滑数据
            df_smoothed, smoothing_log = self.smooth(df, config)

            # 保存结果
            df_smoothed.to_csv(output_path, index=False)

            return {
                'success': True,
                'input_file': input_path,
                'output_file': output_path,
                'log': smoothing_log
            }

        except Exception as e:
            logger.error(f"平滑文件 {input_path} 时出错: {str(e)}")
            return {
                'success': False,
                'input_file': input_path,
                'error': str(e)
            }

    @staticmethod
    def compare_methods(df: pd.DataFrame, column: str = 'x') -> Dict:
        """
        比较不同平滑方法的效果

        Args:
            df: 数据DataFrame
            column: 要平滑的列名

        Returns:
            各方法平滑结果的对比字典
        """
        if column not in df.columns:
            raise ValueError(f"列 {column} 不存在")

        methods = ['moving_average', 'gaussian', 'median', 'savgol']
        results = {}

        smoother = DataSmoother()

        for method in methods:
            try:
                config = {'method': method, 'smooth_x': True, 'smooth_y': False}
                df_smoothed, log = smoother.smooth(df, config)
                results[method] = {
                    'data': df_smoothed[column].values,
                    'log': log
                }
            except Exception as e:
                logger.error(f"方法 {method} 失败: {str(e)}")
                results[method] = {
                    'error': str(e)
                }

        return results
