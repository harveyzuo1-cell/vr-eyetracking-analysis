"""
Module04 事件分析服务层
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from config.settings import Config
from src.utils.logger import setup_logger
from .event_analyzer import EventAnalyzer

logger = setup_logger(__name__)


class EventAnalysisService:
    """事件分析服务"""

    def __init__(self):
        """初始化事件分析服务"""
        self.data_root = Path(Config.DATA_ROOT)
        self.processed_dir = self.data_root / '02_processed'
        self.roi_configs_dir = self.data_root / 'roi_configs'
        self.results_dir = self.data_root / '04_features' / 'events'
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # 默认分析器（使用默认IVT参数）
        self.analyzer = None

        logger.info(f"事件分析服务初始化完成")

    def load_roi_config(self, task_id: str, data_version: str = 'v1') -> Optional[Dict]:
        """
        加载ROI配置

        Args:
            task_id: 任务ID (q1-q5 or task1-task5)
            data_version: 数据版本 (v1/v2)

        Returns:
            ROI配置字典或None
        """
        try:
            # 规范化task_id
            if task_id.startswith('task'):
                task_num = task_id.replace('task', '')
                task_id = f'q{task_num}'
            elif not task_id.startswith('q'):
                task_id = f'q{task_id}'

            roi_file = self.roi_configs_dir / data_version / f'{task_id}_roi.json'

            if not roi_file.exists():
                logger.warning(f"ROI配置文件不存在: {roi_file}")
                return None

            with open(roi_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            return config.get('regions', {})

        except Exception as e:
            logger.error(f"加载ROI配置失败 {task_id}: {e}")
            return None

    def analyze_single_file(self, subject_id: str, group: str, task_id: str,
                           data_version: str = 'v1',
                           velocity_threshold: float = 40.0,
                           min_fixation_duration: float = 100) -> Dict:
        """
        分析单个受试者的单个任务

        Args:
            subject_id: 受试者ID
            group: 分组 (control/mci/ad)
            task_id: 任务ID
            data_version: 数据版本
            velocity_threshold: IVT速度阈值 (deg/s)
            min_fixation_duration: 最小注视时长 (ms)

        Returns:
            分析结果字典
        """
        try:
            # 初始化或更新分析器
            if self.analyzer is None or \
               self.analyzer.velocity_threshold != velocity_threshold or \
               self.analyzer.min_fixation_duration != min_fixation_duration:
                self.analyzer = EventAnalyzer(
                    velocity_threshold=velocity_threshold,
                    min_fixation_duration=min_fixation_duration
                )

            # 构建文件路径
            file_pattern = f'{subject_id}_{task_id}_calibrated.csv'
            file_path = self.processed_dir / group / file_pattern

            if not file_path.exists():
                # 尝试legacy格式
                file_pattern = f'{group}_{subject_id}_{task_id}_calibrated.csv'
                file_path = self.processed_dir / group / file_pattern

            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'文件不存在: {file_path.name}'
                }

            # 加载ROI配置
            roi_regions = self.load_roi_config(task_id, data_version)

            # 执行分析
            result = self.analyzer.analyze_file(file_path, roi_regions)

            # 添加元数据
            if result['success']:
                result['subject_id'] = subject_id
                result['group'] = group
                result['task_id'] = task_id
                result['data_version'] = data_version

            return result

        except Exception as e:
            logger.error(f"分析失败 {subject_id}/{task_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def analyze_subject(self, subject_id: str, group: str, data_version: str = 'v1',
                       tasks: Optional[List[str]] = None,
                       velocity_threshold: float = 40.0,
                       min_fixation_duration: float = 100) -> Dict:
        """
        分析单个受试者的所有任务

        Args:
            subject_id: 受试者ID
            group: 分组
            data_version: 数据版本
            tasks: 任务列表 (None表示分析全部5个任务)
            velocity_threshold: IVT速度阈值 (deg/s)
            min_fixation_duration: 最小注视时长 (ms)

        Returns:
            分析结果字典
        """
        if tasks is None:
            tasks = ['q1', 'q2', 'q3', 'q4', 'q5']

        results = []
        for task_id in tasks:
            result = self.analyze_single_file(
                subject_id, group, task_id, data_version,
                velocity_threshold, min_fixation_duration
            )
            results.append(result)

        # 统计
        success_count = sum(1 for r in results if r.get('success', False))

        return {
            'success': True,
            'subject_id': subject_id,
            'group': group,
            'data_version': data_version,
            'analyzed_tasks': len(tasks),
            'successful_tasks': success_count,
            'results': results
        }

    def analyze_batch(self, group: Optional[str] = None, data_version: str = 'v1',
                     subject_ids: Optional[List[str]] = None,
                     velocity_threshold: float = 40.0,
                     min_fixation_duration: float = 100) -> Dict:
        """
        批量分析

        Args:
            group: 分组筛选 (None表示全部)
            data_version: 数据版本
            subject_ids: 受试者ID列表 (None表示全部)
            velocity_threshold: IVT速度阈值 (deg/s)
            min_fixation_duration: 最小注视时长 (ms)

        Returns:
            批量分析结果
        """
        try:
            # 初始化分析器（使用指定的IVT参数）
            self.analyzer = EventAnalyzer(
                velocity_threshold=velocity_threshold,
                min_fixation_duration=min_fixation_duration
            )

            logger.info(f"批量分析开始: IVT参数 velocity_threshold={velocity_threshold}, min_fixation_duration={min_fixation_duration}")

            # 扫描可用文件
            groups_to_process = [group] if group else ['control', 'mci', 'ad']
            all_results = []

            for grp in groups_to_process:
                group_dir = self.processed_dir / grp
                if not group_dir.exists():
                    continue

                # 获取该组的所有受试者
                csv_files = list(group_dir.glob('*_calibrated.csv'))

                # 提取受试者ID
                subjects_in_group = set()
                for f in csv_files:
                    # 文件名格式: {group}_{subject_id}_{task_id}_calibrated.csv
                    # 例如: control_legacy_1_q1_calibrated.csv
                    # 需要从文件名中提取完整的subject_id

                    # 移除后缀 "_calibrated"
                    fname = f.stem.replace('_calibrated', '')
                    # 格式: control_legacy_1_q1

                    parts = fname.split('_')

                    if len(parts) < 3:
                        continue

                    # 提取subject_id: 去掉第一个部分(group)和最后一个部分(task_id)
                    # control_legacy_1_q1 -> legacy_1
                    if parts[0] == grp:
                        # 中间所有部分都是subject_id
                        sid = '_'.join(parts[1:-1])
                    else:
                        # 如果第一部分不是group，说明是非标准格式，跳过
                        continue

                    subjects_in_group.add(sid)

                # 过滤受试者
                if subject_ids:
                    subjects_in_group = subjects_in_group.intersection(set(subject_ids))

                # 分析每个受试者
                for sid in sorted(subjects_in_group):
                    result = self.analyze_subject(
                        sid, grp, data_version,
                        velocity_threshold=velocity_threshold,
                        min_fixation_duration=min_fixation_duration
                    )
                    all_results.append(result)

            return {
                'success': True,
                'total_subjects': len(all_results),
                'results': all_results
            }

        except Exception as e:
            logger.error(f"批量分析失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_events_table(self, subject_id: Optional[str] = None,
                        group: Optional[str] = None,
                        task_id: Optional[str] = None,
                        event_type: Optional[str] = None) -> Dict:
        """
        获取事件数据表格 (用于前端展示)

        Args:
            subject_id: 受试者ID筛选
            group: 分组筛选
            task_id: 任务筛选
            event_type: 事件类型筛选 (fixation/saccade)

        Returns:
            事件表格数据
        """
        # 首先执行批量分析获取数据
        batch_result = self.analyze_batch(group=group, subject_ids=[subject_id] if subject_id else None)

        if not batch_result['success']:
            return batch_result

        # 整理为表格格式
        events_list = []

        for subject_result in batch_result['results']:
            sid = subject_result['subject_id']
            grp = subject_result['group']

            for task_result in subject_result['results']:
                if not task_result.get('success', False):
                    continue

                tid = task_result['task_id']

                # 任务筛选
                if task_id and tid != task_id:
                    continue

                # 添加fixations
                for fix in task_result.get('fixations', []):
                    if event_type and event_type != 'fixation':
                        continue

                    events_list.append({
                        'subject_id': sid,
                        'group': grp,
                        'task_id': tid,
                        'event_type': 'fixation',
                        'start_idx': fix['start_idx'],
                        'end_idx': fix['end_idx'],
                        'duration_ms': fix['duration_ms'],
                        'centroid_x': fix['centroid_x'],
                        'centroid_y': fix['centroid_y'],
                        'dispersion': fix['dispersion'],
                        'roi': fix.get('roi')
                    })

                # 添加saccades
                for sacc in task_result.get('saccades', []):
                    if event_type and event_type != 'saccade':
                        continue

                    events_list.append({
                        'subject_id': sid,
                        'group': grp,
                        'task_id': tid,
                        'event_type': 'saccade',
                        'start_idx': sacc['start_idx'],
                        'end_idx': sacc['end_idx'],
                        'duration_ms': sacc['duration_ms'],
                        'amplitude': sacc['amplitude'],
                        'max_velocity': sacc['max_velocity'],
                        'mean_velocity': sacc['mean_velocity'],
                        'roi': None
                    })

        return {
            'success': True,
            'total_events': len(events_list),
            'events': events_list
        }

    def get_roi_statistics(self, group: Optional[str] = None,
                          task_id: Optional[str] = None) -> Dict:
        """
        获取ROI统计数据

        Args:
            group: 分组筛选
            task_id: 任务筛选

        Returns:
            ROI统计数据
        """
        # 获取事件表
        events_result = self.get_events_table(group=group, task_id=task_id, event_type='fixation')

        if not events_result['success']:
            return events_result

        events = events_result['events']

        # 按ROI统计
        roi_stats = {}

        for event in events:
            roi = event.get('roi')
            if not roi:
                continue

            if roi not in roi_stats:
                roi_stats[roi] = {
                    'roi': roi,
                    'fixation_count': 0,
                    'total_duration_ms': 0,
                    'subjects': set(),
                    'tasks': set()
                }

            roi_stats[roi]['fixation_count'] += 1
            roi_stats[roi]['total_duration_ms'] += event['duration_ms']
            roi_stats[roi]['subjects'].add(event['subject_id'])
            roi_stats[roi]['tasks'].add(event['task_id'])

        # 转换为列表并计算平均值
        roi_list = []
        for roi, stats in roi_stats.items():
            roi_list.append({
                'roi': roi,
                'fixation_count': stats['fixation_count'],
                'total_duration_ms': stats['total_duration_ms'],
                'avg_duration_ms': stats['total_duration_ms'] / stats['fixation_count'],
                'unique_subjects': len(stats['subjects']),
                'unique_tasks': len(stats['tasks'])
            })

        # 按fixation_count排序
        roi_list.sort(key=lambda x: x['fixation_count'], reverse=True)

        return {
            'success': True,
            'total_rois': len(roi_list),
            'roi_statistics': roi_list
        }
