"""
Module05 RQA分析服务层
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from config.settings import Config
from src.utils.logger import setup_logger
from .rqa_analyzer import RQAAnalyzer
from .utils import generate_param_signature
from src.modules.module02_preprocessing.subject_manager import SubjectManager

logger = setup_logger(__name__)


class RQAAnalysisService:
    """RQA分析服务"""

    def __init__(self):
        """初始化RQA分析服务"""
        self.data_root = Path(Config.DATA_ROOT)
        self.processed_dir = self.data_root / '02_processed'
        self.results_dir = self.data_root / '05_rqa_analysis' / 'results'
        self.cache_dir = self.data_root / '05_rqa_analysis' / 'cache'
        self.exports_dir = self.data_root / '05_rqa_analysis' / 'exports'

        # 创建目录
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        # RQA分析器
        self.analyzer = RQAAnalyzer()

        # 初始化SubjectManager
        subject_info_dir = self.data_root / 'subject_info'
        self.subject_manager = SubjectManager(subject_info_dir)

        logger.info("RQA分析服务初始化完成")

    def generate_param_combinations(self, m_range: Dict, tau_range: Dict,
                                    eps_range: Dict, lmin_range: Dict) -> Dict:
        """
        生成参数组合空间

        Args:
            m_range: {'start': 1, 'end': 10, 'step': 1}
            tau_range: {'start': 1, 'end': 10, 'step': 1}
            eps_range: {'start': 0.05, 'end': 0.1, 'step': 0.001}
            lmin_range: {'start': 2, 'end': 3, 'step': 1}

        Returns:
            {
                'success': True,
                'total_combinations': int,
                'combinations': List[Dict],
                'estimated_time_minutes': float
            }
        """
        try:
            combinations = []

            # 生成m值列表
            m_values = list(range(
                m_range['start'],
                m_range['end'] + 1,
                m_range['step']
            ))

            # 生成tau值列表
            tau_values = list(range(
                tau_range['start'],
                tau_range['end'] + 1,
                tau_range['step']
            ))

            # 生成eps值列表
            eps_start = eps_range['start']
            eps_end = eps_range['end']
            eps_step = eps_range['step']
            eps_values = []
            current_eps = eps_start
            while current_eps <= eps_end:
                eps_values.append(round(current_eps, 6))  # 避免浮点精度问题
                current_eps += eps_step

            # 生成lmin值列表
            lmin_values = list(range(
                lmin_range['start'],
                lmin_range['end'] + 1,
                lmin_range['step']
            ))

            # 生成所有组合
            for m in m_values:
                for tau in tau_values:
                    for eps in eps_values:
                        for lmin in lmin_values:
                            combinations.append({
                                'm': m,
                                'tau': tau,
                                'eps': eps,
                                'lmin': lmin
                            })

            total_combinations = len(combinations)

            # 估算处理时间（假设每个文件2秒，每组500个文件）
            estimated_time_minutes = (total_combinations * 500 * 2) / 60

            # 保存参数组合到缓存
            cache_file = self.cache_dir / 'param_combinations.json'
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'total_combinations': total_combinations,
                    'combinations': combinations,
                    'ranges': {
                        'm': m_range,
                        'tau': tau_range,
                        'eps': eps_range,
                        'lmin': lmin_range
                    }
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"生成参数组合完成: {total_combinations}个")

            return {
                'success': True,
                'total_combinations': total_combinations,
                'combinations': combinations,
                'estimated_time_minutes': estimated_time_minutes
            }

        except Exception as e:
            logger.error(f"生成参数组合失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_param_directory(self, params: Dict) -> Path:
        """获取参数对应的目录路径"""
        signature = generate_param_signature(params)
        param_dir = self.results_dir / signature
        param_dir.mkdir(parents=True, exist_ok=True)
        return param_dir

    def get_step_directory(self, params: Dict, step_name: str) -> Path:
        """获取特定步骤的目录路径"""
        param_dir = self.get_param_directory(params)
        step_dir = param_dir / step_name
        step_dir.mkdir(parents=True, exist_ok=True)
        return step_dir

    def save_param_metadata(self, params: Dict, step: int, data: Dict):
        """
        保存参数元数据

        Args:
            params: RQA参数
            step: 完成的步骤编号 (1-5)
            data: 步骤结果数据
        """
        param_dir = self.get_param_directory(params)
        metadata_file = param_dir / 'metadata.json'

        # 读取现有元数据
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                pass

        # 更新元数据
        if 'signature' not in metadata:
            metadata['signature'] = generate_param_signature(params)
            metadata['parameters'] = params
            metadata['creation_time'] = datetime.now().isoformat()

        metadata['last_updated'] = datetime.now().isoformat()

        # 更新步骤完成状态
        step_names = [
            'step1_rqa_calculation',
            'step2_data_merging',
            'step3_feature_enrichment',
            'step4_statistical_analysis',
            'step5_visualization'
        ]

        if 'steps_completed' not in metadata:
            metadata['steps_completed'] = {}

        step_name = step_names[step - 1]
        metadata['steps_completed'][step_name] = {
            'completed': True,
            'timestamp': datetime.now().isoformat(),
            **data
        }

        # 保存元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"保存元数据: {metadata_file}")

    def scan_calibrated_files(self, group: str) -> List[Path]:
        """
        扫描校准后的CSV文件

        Args:
            group: 分组名称 ('control', 'mci', 'ad')

        Returns:
            文件路径列表
        """
        group_dir = self.processed_dir / group

        if not group_dir.exists():
            logger.warning(f"分组目录不存在: {group_dir}")
            return []

        # 查找所有 *_calibrated.csv 文件
        csv_files = list(group_dir.glob('*_calibrated.csv'))

        logger.info(f"扫描到 {len(csv_files)} 个文件: {group}")

        return csv_files

    def step1_rqa_calculation(self, params: Dict, groups: List[str]) -> Dict:
        """
        Step 1: RQA计算

        对所有受试者的所有任务进行RQA计算

        Args:
            params: RQA参数
            groups: 分组列表 ['control', 'mci', 'ad']

        Returns:
            {
                'success': True,
                'total_files_processed': int,
                'files_failed': int,
                'output_files': List[str]
            }
        """
        try:
            logger.info(f"开始Step 1: RQA计算, 参数={params}")

            results = {group: [] for group in groups}
            total_processed = 0
            total_failed = 0

            for group in groups:
                # 扫描文件
                csv_files = self.scan_calibrated_files(group)

                logger.info(f"处理 {group} 组: {len(csv_files)} 个文件")

                # 处理每个文件
                for csv_file in csv_files:
                    try:
                        # 提取subject_id和task_id
                        filename = csv_file.stem  # 去掉.csv后缀
                        # 格式: control_legacy_1_q1_calibrated
                        parts = filename.replace('_calibrated', '').split('_')

                        if len(parts) >= 2:
                            # 重组subject_id (去掉最后的task_id)
                            task_id = parts[-1]  # q1, q2, etc.
                            subject_id = '_'.join(parts[:-1])  # control_legacy_1
                        else:
                            logger.warning(f"无法解析文件名: {filename}")
                            continue

                        # RQA分析
                        rqa_result = self.analyzer.analyze_single_file(str(csv_file), params)

                        # 添加到结果
                        result_row = {
                            'subject_id': subject_id,
                            'task_id': task_id,
                            **rqa_result
                        }
                        results[group].append(result_row)
                        total_processed += 1

                    except Exception as e:
                        logger.error(f"处理文件失败: {csv_file} - {e}")
                        total_failed += 1

                # 保存该组结果
                df = pd.DataFrame(results[group])
                step1_dir = self.get_step_directory(params, 'step1_rqa_calculation')
                output_file = step1_dir / f'{group}_rqa_results.csv'
                df.to_csv(output_file, index=False)

                logger.info(f"保存 {group} 组结果: {output_file}, {len(results[group])} 条记录")

            # 保存元数据
            self.save_param_metadata(params, 1, {
                'files_processed': total_processed,
                'files_failed': total_failed
            })

            return {
                'success': True,
                'total_files_processed': total_processed,
                'files_failed': total_failed,
                'output_files': [
                    str(self.get_step_directory(params, 'step1_rqa_calculation') / f'{g}_rqa_results.csv')
                    for g in groups
                ]
            }

        except Exception as e:
            logger.error(f"Step 1 执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def step2_data_merging(self, params: Dict, groups: List[str]) -> Dict:
        """
        Step 2: 数据合并

        合并三组数据，添加分组标签

        Args:
            params: RQA参数
            groups: 分组列表

        Returns:
            {
                'success': True,
                'total_records': int,
                'output_file': str
            }
        """
        try:
            logger.info(f"开始Step 2: 数据合并, 参数={params}")

            step1_dir = self.get_step_directory(params, 'step1_rqa_calculation')

            # 读取三组数据
            all_data = []
            for group in groups:
                csv_file = step1_dir / f'{group}_rqa_results.csv'

                if not csv_file.exists():
                    logger.warning(f"文件不存在: {csv_file}")
                    continue

                df = pd.read_csv(csv_file)
                df['Group'] = group.capitalize()  # Control, Mci, Ad
                df['ID'] = df['subject_id'] + '_' + df['task_id']

                all_data.append(df)

            if not all_data:
                raise ValueError("没有找到Step 1的输出文件")

            # 合并数据
            merged = pd.concat(all_data, ignore_index=True)

            # 调整列顺序
            cols = ['ID', 'Group', 'subject_id', 'task_id',
                   'RR-1D-x', 'DET-1D-x', 'ENT-1D-x',
                   'RR-2D-xy', 'DET-2D-xy', 'ENT-2D-xy']
            merged = merged[cols]

            # 保存
            step2_dir = self.get_step_directory(params, 'step2_data_merging')
            output_file = step2_dir / 'merged_data.csv'
            merged.to_csv(output_file, index=False)

            logger.info(f"数据合并完成: {output_file}, {len(merged)} 条记录")

            # 保存元数据
            self.save_param_metadata(params, 2, {
                'total_records': len(merged)
            })

            return {
                'success': True,
                'total_records': len(merged),
                'output_file': str(output_file)
            }

        except Exception as e:
            logger.error(f"Step 2 执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_param_history(self) -> List[Dict]:
        """
        获取所有参数历史记录

        Returns:
            历史记录列表
        """
        history = []

        if not self.results_dir.exists():
            return history

        for param_folder in self.results_dir.iterdir():
            if not param_folder.is_dir():
                continue

            metadata_file = param_folder / 'metadata.json'

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    # 计算完成步骤数
                    completed_steps = sum(
                        1 for i in range(1, 6)
                        if metadata.get('steps_completed', {}).get(
                            f'step{i}_' + ['rqa_calculation', 'data_merging', 'feature_enrichment',
                                          'statistical_analysis', 'visualization'][i-1], {}
                        ).get('completed', False)
                    )

                    history.append({
                        'signature': metadata.get('signature', param_folder.name),
                        'params': metadata.get('parameters', {}),
                        'completed_steps': completed_steps,
                        'progress': (completed_steps / 5) * 100,
                        'last_updated': metadata.get('last_updated', '')
                    })

                except Exception as e:
                    logger.error(f"读取元数据失败: {metadata_file} - {e}")

        # 按最后更新时间排序
        history.sort(key=lambda x: x.get('last_updated', ''), reverse=True)

        return history
