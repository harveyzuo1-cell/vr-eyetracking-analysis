"""
Module05 RQA分析服务层
"""

# Configure Matplotlib to use non-GUI backend for thread safety
# Must be set BEFORE importing pyplot to avoid GUI initialization in worker threads
import matplotlib
matplotlib.use('Agg')

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from config.settings import Config
from src.utils.logger import setup_logger
from .rqa_analyzer import RQAAnalyzer
from .service_pipeline import RQAPipeline
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

        # RQA流水线（composition pattern）
        self.pipeline = RQAPipeline(self)

        # 初始化SubjectManager
        subject_info_dir = self.data_root / 'subject_info'
        self.subject_manager = SubjectManager(subject_info_dir)

        # 当前批次信息（用于记录到metadata）
        self.current_task_id = None
        self.current_data_version = 'v1'

        logger.info("RQA分析服务初始化完成")

    def generate_param_combinations(self, m_range: Dict, tau_range: Dict,
                                    eps_range: Dict, lmin_range: Dict,
                                    data_version: str = 'v1') -> Dict:
        """
        生成参数组合空间

        Args:
            m_range: {'start': 1, 'end': 10, 'step': 1}
            tau_range: {'start': 1, 'end': 10, 'step': 1}
            eps_range: {'start': 0.05, 'end': 0.1, 'step': 0.001}
            lmin_range: {'start': 2, 'end': 3, 'step': 1}
            data_version: 数据版本 ('v1'/'v2'，默认'v1')

        Returns:
            {
                'success': True,
                'total_combinations': int,
                'combinations': List[Dict],
                'estimated_time_minutes': float,
                'data_version': str
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
            # 使用小的容差来避免浮点精度问题
            while current_eps <= eps_end + eps_step * 0.01:
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
                    'data_version': data_version,
                    'ranges': {
                        'm': m_range,
                        'tau': tau_range,
                        'eps': eps_range,
                        'lmin': lmin_range
                    }
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"生成参数组合完成: {total_combinations}个 ({data_version}数据)")

            return {
                'success': True,
                'total_combinations': total_combinations,
                'combinations': combinations,
                'estimated_time_minutes': estimated_time_minutes,
                'data_version': data_version
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

    def save_param_metadata(self, params: Dict, step: int, data: Dict,
                           task_id: Optional[str] = None,
                           data_version: Optional[str] = None):
        """
        保存参数元数据

        Args:
            params: RQA参数
            step: 完成的步骤编号 (1-5)
            data: 步骤结果数据
            task_id: 批量任务ID (可选)
            data_version: 数据版本 (可选，'v1'/'v2')
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

            # 记录批次信息（优先使用传入的task_id，其次使用current_task_id）
            batch_task_id = task_id or self.current_task_id
            if batch_task_id:
                metadata['task_id'] = batch_task_id
                metadata['batch_time'] = datetime.now().isoformat()

            # 记录数据版本（优先使用传入的data_version，其次使用current_data_version）
            version = data_version or self.current_data_version
            if version:
                metadata['data_version'] = version

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

    def scan_calibrated_files(self, group: str, data_version: str = 'v1') -> List[Path]:
        """
        扫描校准后的CSV文件(根据data_version筛选,且有MMSE分数的受试者)

        Args:
            group: 分组名称 ('control', 'mci', 'ad')
            data_version: 数据版本 ('v1'/'v2'，默认'v1')

        Returns:
            文件路径列表
        """
        group_dir = self.processed_dir / group

        if not group_dir.exists():
            logger.warning(f"分组目录不存在: {group_dir}")
            return []

        # 查找所有 *_calibrated.csv 文件
        all_files = list(group_dir.glob('*_calibrated.csv'))

        # 1. 根据data_version筛选文件
        if data_version == 'v1':
            # V1数据包含legacy前缀
            version_files = [f for f in all_files if 'legacy' in f.name]
        elif data_version == 'v2':
            # V2数据包含v2前缀
            version_files = [f for f in all_files if f.name.startswith('v2_')]
        else:
            logger.warning(f"未知的data_version: {data_version}, 使用全部文件")
            version_files = all_files

        # 2. 获取有MMSE分数的受试者列表
        subjects_with_mmse = self.subject_manager.get_all_subjects(
            group=group,
            with_mmse=True,
            data_version=data_version
        )

        # 提取有MMSE的subject_id集合(只要有mmse字段且total_score不为None)
        valid_subject_ids = set()
        for subj in subjects_with_mmse:
            mmse = subj.get('mmse', {})
            if mmse and mmse.get('total_score') is not None:
                valid_subject_ids.add(subj['subject_id'])

        # 3. 过滤文件:只保留有MMSE分数的受试者
        filtered_files = []
        for f in version_files:
            # 文件名格式:
            # V1: control_legacy_1_q1_calibrated.csv -> subject_id = control_legacy_1
            # V2: v2_control_025_level_1_calibrated.csv -> subject_id = v2_control_025
            parts = f.stem.replace('_calibrated', '').rsplit('_', 1)
            if len(parts) == 2:
                subject_id = parts[0]
                if subject_id in valid_subject_ids:
                    filtered_files.append(f)

        logger.info(
            f"扫描 {group} 组({data_version}): 总文件={len(all_files)}, "
            f"{data_version}文件={len(version_files)}, "
            f"有MMSE受试者={len(valid_subject_ids)}, "
            f"最终文件={len(filtered_files)}"
        )

        return filtered_files

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
        return self.pipeline.step1_rqa_calculation(params, groups)

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
        return self.pipeline.step2_data_merging(params, groups)

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

    def get_cached_param_combinations(self) -> Dict:
        """
        获取缓存的参数组合

        Returns:
            {
                'combinations': List[Dict],
                'total_combinations': int,
                'data_version': str,
                'timestamp': str
            }
        """
        cache_file = self.cache_dir / 'param_combinations.json'

        if not cache_file.exists():
            logger.warning("参数组合缓存文件不存在")
            return {
                'combinations': [],
                'total_combinations': 0,
                'data_version': 'v1',
                'timestamp': None
            }

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            return {
                'combinations': cached_data.get('combinations', []),
                'total_combinations': cached_data.get('total_combinations', 0),
                'data_version': cached_data.get('data_version', 'v1'),
                'timestamp': cached_data.get('timestamp', '')
            }

        except Exception as e:
            logger.error(f"读取参数组合缓存失败: {e}", exc_info=True)
            return {
                'combinations': [],
                'total_combinations': 0,
                'data_version': 'v1',
                'timestamp': None
            }

    def step3_feature_enrichment(self, params: Dict) -> Dict:
        """
        Step 3: 特征增强

        整合Module04事件分析数据和受试者MMSE信息

        Args:
            params: RQA参数

        Returns:
            {
                'success': True,
                'features_added': int,
                'output_file': str
            }
        """
        return self.pipeline.step3_feature_enrichment(params)

    def step4_statistical_analysis(self, params: Dict) -> Dict:
        """
        Step 4: 统计分析

        执行描述性统计和组间比较（ANOVA）

        Args:
            params: RQA参数

        Returns:
            {
                'success': True,
                'significant_features': int,
                'output_files': List[str]
            }
        """
        return self.pipeline.step4_statistical_analysis(params)

    def step5_visualization(self, params: Dict, max_samples: int = 10) -> Dict:
        """
        Step 5: 可视化

        生成统计图表

        Args:
            params: RQA参数
            max_samples: 递归图最大抽样数量

        Returns:
            {
                'success': True,
                'plots_generated': int,
                'output_dir': str
            }
        """
        return self.pipeline.step5_visualization(params, max_samples)

    def run_full_pipeline(self, params: Dict, groups: List[str] = None,
                         max_samples: int = 10) -> Dict:
        """
        执行完整的5步RQA分析流水线

        Args:
            params: RQA参数 {'m': int, 'tau': int, 'eps': float, 'lmin': int}
            groups: 分组列表,默认 ['control', 'mci', 'ad']
            max_samples: Step 5可视化最大抽样数量

        Returns:
            {
                'success': bool,
                'step1_result': Dict,
                'step2_result': Dict,
                'step3_result': Dict,
                'step4_result': Dict,
                'step5_result': Dict,
                'error': str (if failed)
            }
        """
        if groups is None:
            groups = ['control', 'mci', 'ad']

        results = {
            'success': True,
            'params': params,
            'groups': groups
        }

        try:
            # Step 1: RQA计算
            logger.info(f"执行 Step 1: RQA计算 - 参数: {params}")
            step1_result = self.step1_rqa_calculation(params, groups)
            results['step1_result'] = step1_result

            if not step1_result['success']:
                results['success'] = False
                results['error'] = f"Step 1失败: {step1_result.get('error', 'Unknown error')}"
                return results

            # Step 2: 数据合并
            logger.info(f"执行 Step 2: 数据合并")
            step2_result = self.step2_data_merging(params, groups)
            results['step2_result'] = step2_result

            if not step2_result['success']:
                results['success'] = False
                results['error'] = f"Step 2失败: {step2_result.get('error', 'Unknown error')}"
                return results

            # Step 3: 特征增强
            logger.info(f"执行 Step 3: 特征增强")
            step3_result = self.step3_feature_enrichment(params)
            results['step3_result'] = step3_result

            if not step3_result['success']:
                logger.warning(f"Step 3失败: {step3_result.get('error')}")

            # Step 4: 统计分析
            logger.info(f"执行 Step 4: 统计分析")
            step4_result = self.step4_statistical_analysis(params)
            results['step4_result'] = step4_result

            if not step4_result['success']:
                logger.warning(f"Step 4失败: {step4_result.get('error')}")

            # Step 5: 可视化
            logger.info(f"执行 Step 5: 可视化")
            step5_result = self.step5_visualization(params, max_samples)
            results['step5_result'] = step5_result

            if not step5_result['success']:
                logger.warning(f"Step 5失败: {step5_result.get('error')}")

            logger.info(f"完整流水线执行完成 - 参数: {params}")
            return results

        except Exception as e:
            logger.error(f"执行完整流水线失败: {e}", exc_info=True)
            results['success'] = False
            results['error'] = str(e)
            return results

    def scan_completed_results(self, task_id: Optional[str] = None) -> List[Dict]:
        """
        扫描已完成的RQA分析结果

        Args:
            task_id: 批次ID (可选，筛选指定批次的结果)

        Returns:
            List[Dict]: 已完成结果的参数列表
            [
                {
                    'm': 1, 'tau': 1, 'eps': 0.05, 'lmin': 2,
                    'signature': 'm1_tau1_eps0.05_lmin2',
                    'task_id': 'task_20251008_163415',
                    'data_version': 'v1',
                    'creation_time': '2025-10-08T16:23:10.278112',
                    'last_updated': '2025-10-08T16:34:32.529794'
                },
                ...
            ]
        """
        try:
            completed_results = []

            # 扫描results目录下的所有参数文件夹
            if not self.results_dir.exists():
                logger.warning(f"结果目录不存在: {self.results_dir}")
                return []

            for result_dir in self.results_dir.iterdir():
                if not result_dir.is_dir():
                    continue

                # 检查metadata.json是否存在
                metadata_file = result_dir / 'metadata.json'
                if not metadata_file.exists():
                    continue

                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    # 如果指定了task_id，进行筛选
                    if task_id:
                        result_task_id = metadata.get('task_id', '')
                        # 如果没有task_id，尝试从creation_time生成
                        if not result_task_id:
                            creation_time = metadata.get('creation_time', '')
                            if creation_time:
                                result_task_id = f"batch_{creation_time[:19].replace(':', '').replace('-', '').replace('T', '_')}"

                        if result_task_id != task_id:
                            continue

                    # 检查steps_completed字典，确保所有5个步骤都完成
                    steps_completed = metadata.get('steps_completed', {})
                    all_completed = all(
                        steps_completed.get(f'step{i}_{name}', {}).get('completed', False)
                        for i, name in [
                            (1, 'rqa_calculation'),
                            (2, 'data_merging'),
                            (3, 'feature_enrichment'),
                            (4, 'statistical_analysis'),
                            (5, 'visualization')
                        ]
                    )

                    if all_completed:
                        params = metadata.get('parameters', {})
                        if params:
                            # 添加额外信息
                            result_info = {
                                **params,
                                'signature': metadata.get('signature', result_dir.name),
                                'task_id': metadata.get('task_id', ''),
                                'data_version': metadata.get('data_version', 'v1'),
                                'creation_time': metadata.get('creation_time', ''),
                                'last_updated': metadata.get('last_updated', '')
                            }
                            completed_results.append(result_info)

                except Exception as e:
                    logger.warning(f"读取metadata失败 {metadata_file}: {e}")

            filter_msg = f"(批次: {task_id})" if task_id else ""
            logger.info(f"扫描到 {len(completed_results)} 个已完成的RQA分析结果{filter_msg}")
            return completed_results

        except Exception as e:
            logger.error(f"扫描已完成结果失败: {e}", exc_info=True)
            return []

    def get_batch_list(self) -> List[Dict]:
        """
        获取所有批次列表

        Returns:
            List[Dict]: 批次列表
            [
                {
                    'task_id': 'task_20251008_163415',
                    'batch_time': '2025-10-08T16:34:15',
                    'data_version': 'v1',
                    'param_count': 704,
                    'display_name': '2025-10-08 16:34:15 (V1数据, 704个参数)'
                },
                ...
            ]
        """
        try:
            batches_map = {}  # task_id -> batch_info

            # 扫描results目录
            if not self.results_dir.exists():
                return []

            for result_dir in self.results_dir.iterdir():
                if not result_dir.is_dir():
                    continue

                metadata_file = result_dir / 'metadata.json'
                if not metadata_file.exists():
                    continue

                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    task_id = metadata.get('task_id')
                    batch_time = metadata.get('batch_time')
                    data_version = metadata.get('data_version', 'v1')

                    # 如果没有task_id，使用创建时间作为唯一标识
                    if not task_id:
                        creation_time = metadata.get('creation_time', '')
                        if creation_time:
                            # 使用日期时间生成伪task_id
                            task_id = f"batch_{creation_time[:19].replace(':', '').replace('-', '').replace('T', '_')}"
                            batch_time = creation_time
                        else:
                            continue

                    if task_id not in batches_map:
                        batches_map[task_id] = {
                            'task_id': task_id,
                            'batch_time': batch_time or '',
                            'data_version': data_version,
                            'param_count': 0
                        }

                    batches_map[task_id]['param_count'] += 1

                except Exception as e:
                    logger.warning(f"读取metadata失败 {metadata_file}: {e}")

            # 转换为列表并添加显示名称
            batches = []
            for batch_info in batches_map.values():
                try:
                    # 格式化显示名称
                    batch_time_str = batch_info['batch_time']
                    if batch_time_str:
                        # 解析ISO格式时间
                        dt = datetime.fromisoformat(batch_time_str)
                        display_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        display_time = '未知时间'

                    version_label = {
                        'v1': 'V1数据',
                        'v2': 'V2数据'
                    }.get(batch_info['data_version'], batch_info['data_version'])

                    batch_info['display_name'] = (
                        f"{display_time} ({version_label}, "
                        f"{batch_info['param_count']}个参数)"
                    )

                    batches.append(batch_info)

                except Exception as e:
                    logger.warning(f"格式化批次显示名称失败: {e}")
                    batches.append(batch_info)

            # 按时间倒序排序
            batches.sort(key=lambda x: x['batch_time'], reverse=True)

            logger.info(f"找到 {len(batches)} 个批次")
            return batches

        except Exception as e:
            logger.error(f"获取批次列表失败: {e}", exc_info=True)
            return []
