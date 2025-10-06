"""
数据预处理流水线

整合质量检测、数据清洗、数据平滑等步骤，提供统一的预处理接口
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime

from .quality_checker import QualityChecker
from .data_cleaner import DataCleaner
from .data_smoother import DataSmoother

logger = logging.getLogger(__name__)


class Pipeline:
    """数据预处理流水线"""

    def __init__(self):
        self.quality_checker = QualityChecker()
        self.data_cleaner = DataCleaner()
        self.data_smoother = DataSmoother()

        self.config = {
            'enable_quality_check': True,
            'enable_cleaning': True,
            'enable_smoothing': True,
            'quality_check_config': {},
            'cleaning_config': {},
            'smoothing_config': {},
            'save_intermediate': False,  # 是否保存中间结果
            'min_quality_score': 0  # 最低质量分数要求（0-100）
        }

    def process(
        self,
        df: pd.DataFrame,
        config: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        执行完整的预处理流程

        Args:
            df: 原始数据DataFrame
            config: 自定义配置

        Returns:
            (处理后的DataFrame, 处理日志)
        """
        if config:
            self.config.update(config)

        logger.info(f"开始预处理流程，原始数据点数: {len(df)}")

        pipeline_log = {
            'start_time': datetime.now().isoformat(),
            'original_points': len(df),
            'steps': []
        }

        df_result = df.copy()

        # 1. 质量检测
        if self.config['enable_quality_check']:
            quality_report = self.quality_checker.check_quality(
                df_result,
                self.config.get('quality_check_config')
            )
            pipeline_log['steps'].append({
                'step': 'quality_check',
                'report': quality_report
            })

            # 检查是否满足最低质量要求
            min_score = self.config.get('min_quality_score', 0)
            if quality_report['quality_score'] < min_score:
                logger.warning(
                    f"质量分数 {quality_report['quality_score']:.2f} "
                    f"低于要求的 {min_score}，建议检查数据"
                )
                pipeline_log['warning'] = f"质量分数过低: {quality_report['quality_score']:.2f}"

        # 2. 数据清洗
        if self.config['enable_cleaning']:
            df_result, cleaning_log = self.data_cleaner.clean(
                df_result,
                self.config.get('cleaning_config')
            )
            pipeline_log['steps'].append({
                'step': 'cleaning',
                'log': cleaning_log
            })

        # 3. 数据平滑
        if self.config['enable_smoothing']:
            df_result, smoothing_log = self.data_smoother.smooth(
                df_result,
                self.config.get('smoothing_config')
            )
            pipeline_log['steps'].append({
                'step': 'smoothing',
                'log': smoothing_log
            })

        pipeline_log['end_time'] = datetime.now().isoformat()
        pipeline_log['final_points'] = len(df_result)

        logger.info(f"预处理流程完成，最终数据点数: {len(df_result)}")

        return df_result, pipeline_log

    def process_file(
        self,
        input_path: str,
        output_path: str,
        config: Optional[Dict] = None,
        save_log: bool = True
    ) -> Dict:
        """
        处理单个文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            config: 自定义配置
            save_log: 是否保存处理日志

        Returns:
            处理结果字典
        """
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            # 读取数据
            logger.info(f"读取文件: {input_path}")
            df = pd.read_csv(input_path)

            # 执行预处理
            df_processed, pipeline_log = self.process(df, config)

            # 创建输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存处理后的数据
            df_processed.to_csv(output_path, index=False)
            logger.info(f"保存处理结果: {output_path}")

            # 保存处理日志
            if save_log:
                log_path = output_path.parent / f"{output_path.stem}_log.json"
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(pipeline_log, f, ensure_ascii=False, indent=2)
                logger.info(f"保存处理日志: {log_path}")

            return {
                'success': True,
                'input_file': str(input_path),
                'output_file': str(output_path),
                'log': pipeline_log
            }

        except Exception as e:
            logger.error(f"处理文件 {input_path} 时出错: {str(e)}")
            return {
                'success': False,
                'input_file': str(input_path),
                'error': str(e)
            }

    def batch_process(
        self,
        input_files: List[str],
        output_dir: str,
        config: Optional[Dict] = None,
        save_log: bool = True
    ) -> Dict:
        """
        批量处理文件

        Args:
            input_files: 输入文件路径列表
            output_dir: 输出目录
            config: 自定义配置
            save_log: 是否保存处理日志

        Returns:
            批量处理结果字典
        """
        logger.info(f"开始批量处理，共 {len(input_files)} 个文件")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        successful = 0
        failed = 0

        for input_file in input_files:
            input_path = Path(input_file)
            output_path = output_dir / f"processed_{input_path.name}"

            result = self.process_file(
                str(input_path),
                str(output_path),
                config,
                save_log
            )

            results.append(result)

            if result['success']:
                successful += 1
            else:
                failed += 1

        summary = {
            'total_files': len(input_files),
            'successful': successful,
            'failed': failed,
            'output_directory': str(output_dir),
            'results': results
        }

        logger.info(
            f"批量处理完成: {successful} 成功, {failed} 失败"
        )

        return summary

    def get_default_config(self) -> Dict:
        """
        获取默认配置

        Returns:
            默认配置字典
        """
        return {
            'enable_quality_check': True,
            'enable_cleaning': True,
            'enable_smoothing': True,
            'min_quality_score': 60,
            'quality_check_config': {
                'outlier_method': '3sigma',
                'outlier_threshold': 3.0,
                'expected_range_x': [0, 1],
                'expected_range_y': [0, 1],
                'expected_sampling_rate': 60,
                'sampling_tolerance': 5
            },
            'cleaning_config': {
                'missing_method': 'interpolate',
                'outlier_method': '3sigma',
                'outlier_threshold': 3.0,
                'outlier_action': 'interpolate',
                'clip_range': True,
                'x_range': [0, 1],
                'y_range': [0, 1],
                'resample': False,
                'target_rate': 60
            },
            'smoothing_config': {
                'method': 'gaussian',
                'window_size': 5,
                'sigma': 1.5,
                'polyorder': 3,
                'smooth_x': True,
                'smooth_y': True
            }
        }

    def save_config(self, config: Dict, config_path: str):
        """
        保存配置到文件

        Args:
            config: 配置字典
            config_path: 配置文件路径
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"配置已保存: {config_path}")

    def load_config(self, config_path: str) -> Dict:
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self.get_default_config()

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        logger.info(f"配置已加载: {config_path}")

        return config
