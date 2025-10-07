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
from src.modules.module02_preprocessing.subject_manager import SubjectManager

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

        # 缓存目录
        self.cache_dir = self.data_root / '04_features' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 默认分析器（使用默认IVT参数）
        self.analyzer = None

        # 初始化SubjectManager用于获取MMSE数据
        subject_info_dir = self.data_root / 'subject_info'
        self.subject_manager = SubjectManager(subject_info_dir)

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

    def get_feature_statistics(self, group: Optional[str] = None,
                               data_version: str = 'v1',
                               velocity_threshold: float = 40.0,
                               min_fixation_duration: float = 100) -> Dict:
        """
        获取特征统计数据（每个受试者-任务一行）
        
        特征包括：
        - 受试者信息 (subject_id, group)
        - 任务信息 (task_id)
        - ROI占比 (bg_ratio, inst_ratio, kw_ratio)
        - 事件统计 (total_fixation_time, total_fixations, avg_fixation_duration,
                   total_saccades, avg_saccade_amplitude, task_total_time)
        - MMSE分数 (mmse_total_score, mmse_task_score)
        
        Args:
            group: 分组筛选
            data_version: 数据版本
            velocity_threshold: IVT速度阈值
            min_fixation_duration: 最小注视时长
            
        Returns:
            特征统计数据列表
        """
        try:
            # 执行批量分析
            batch_result = self.analyze_batch(
                group=group,
                data_version=data_version,
                velocity_threshold=velocity_threshold,
                min_fixation_duration=min_fixation_duration
            )
            
            if not batch_result['success']:
                return batch_result
            
            features_list = []
            
            for subject_result in batch_result['results']:
                subject_id = subject_result['subject_id']
                grp = subject_result['group']

                # 获取该受试者的MMSE数据
                # subject_id格式: legacy_1, 需要构建完整ID: control_legacy_1
                full_subject_id = f"{grp}_{subject_id}"
                subject_data = self.subject_manager.get_subject(full_subject_id)
                mmse_total_score = None
                if subject_data and 'mmse' in subject_data:
                    mmse_total_score = subject_data['mmse'].get('total_score')
                
                # 遍历每个任务
                for task_result in subject_result['results']:
                    if not task_result.get('success', False):
                        continue

                    task_id = task_result['task_id']
                    fixations = task_result.get('fixations', [])
                    saccades = task_result.get('saccades', [])

                    # 方法1: 使用ROIAnalyzer逐帧分析法计算ROI占比(与Module01一致)
                    bg_ratio_frame = 0
                    inst_ratio_frame = 0
                    kw_ratio_frame = 0

                    try:
                        # 加载校准后的数据文件
                        calibrated_file = self.processed_dir / grp / f"{full_subject_id}_{task_id}_calibrated.csv"
                        logger.info(f"逐帧分析法: 检查文件 {calibrated_file}, exists={calibrated_file.exists()}")

                        if calibrated_file.exists():
                            import pandas as pd
                            from src.web.modules.module01_data_visualization.roi_analyzer import ROIAnalyzer
                            from src.services.roi_service import UnifiedROIService

                            # 读取校准数据
                            gaze_df = pd.read_csv(calibrated_file)
                            logger.info(f"逐帧分析法: 读取校准数据 {len(gaze_df)} 行")

                            # 获取ROI配置
                            roi_service = UnifiedROIService()  # 使用默认单例
                            roi_result = roi_service.get_roi_config(data_version, task_id)
                            logger.info(f"逐帧分析法: ROI配置获取结果 success={roi_result.get('success') if roi_result else False}")

                            if roi_result and roi_result.get('success') and 'data' in roi_result:
                                roi_config = roi_result['data']
                                if 'regions' in roi_config:
                                    # 使用ROIAnalyzer计算统计
                                    roi_analyzer = ROIAnalyzer(roi_config['regions'])
                                    roi_stats = roi_analyzer.calculate_stats(gaze_df)
                                    roi_summary = roi_analyzer.get_summary(roi_stats)
                                    logger.info(f"逐帧分析法: ROI summary = {roi_summary}")

                                    # 计算总时间和占比
                                    total_roi_time = roi_summary['total_fixation_time']
                                    if total_roi_time > 0:
                                        bg_ratio_frame = (roi_summary['background_fixation_time'] / total_roi_time * 100)
                                        inst_ratio_frame = (roi_summary['instructions_fixation_time'] / total_roi_time * 100)
                                        kw_ratio_frame = (roi_summary['keywords_fixation_time'] / total_roi_time * 100)

                                    logger.info(f"逐帧分析法ROI占比: {full_subject_id}_{task_id} - BG:{bg_ratio_frame:.2f}% INST:{inst_ratio_frame:.2f}% KW:{kw_ratio_frame:.2f}%")
                        else:
                            logger.warning(f"未找到校准数据文件: {calibrated_file}")
                    except Exception as e:
                        logger.error(f"逐帧分析法ROI占比计算失败: {full_subject_id}_{task_id} - {e}", exc_info=True)

                    # 方法2: 使用IVT fixation质心匹配法计算ROI占比
                    bg_ratio_ivt = 0
                    inst_ratio_ivt = 0
                    kw_ratio_ivt = 0
                    total_fixation_time = 0

                    for fix in fixations:
                        duration = fix['duration_ms']
                        total_fixation_time += duration

                        roi = fix.get('roi', '')
                        if roi:
                            # 根据ROI ID前缀判断类型
                            if roi.startswith('BG_'):
                                bg_ratio_ivt += duration
                            elif roi.startswith('INST_'):
                                inst_ratio_ivt += duration
                            elif roi.startswith('KW_'):
                                kw_ratio_ivt += duration
                        else:
                            # 没有ROI标注,计入背景
                            bg_ratio_ivt += duration

                    # 计算IVT方法的占比
                    if total_fixation_time > 0:
                        bg_ratio_ivt = (bg_ratio_ivt / total_fixation_time * 100)
                        inst_ratio_ivt = (inst_ratio_ivt / total_fixation_time * 100)
                        kw_ratio_ivt = (kw_ratio_ivt / total_fixation_time * 100)

                    logger.debug(f"IVT质心法ROI占比: {full_subject_id}_{task_id} - BG:{bg_ratio_ivt:.2f}% INST:{inst_ratio_ivt:.2f}% KW:{kw_ratio_ivt:.2f}%")
                    
                    # 计算平均Fixation时长
                    avg_fixation_duration = total_fixation_time / len(fixations) if fixations else 0
                    
                    # 计算平均Saccade幅度
                    total_saccade_amplitude = sum([sacc['amplitude'] for sacc in saccades])
                    avg_saccade_amplitude = total_saccade_amplitude / len(saccades) if saccades else 0
                    
                    # 任务总时间 = 所有fixation时间 + 所有saccade时间
                    total_saccade_time = sum([sacc['duration_ms'] for sacc in saccades])
                    task_total_time = total_fixation_time + total_saccade_time
                    
                    # 获取对应任务的MMSE分项分数
                    mmse_task_score = None
                    if subject_data and 'mmse' in subject_data:
                        mmse = subject_data['mmse']
                        # 根据task_id计算对应的MMSE分项总分
                        # q1: 时间定向 (year, season, month, weekday)
                        # q2: 地点定向 (province, street, building, floor)
                        # q3: 即时记忆 (immediate)
                        # q4: 计算能力 (100_7, 93_7, 86_7, 79_7, 72_7)
                        # q5: 延迟回忆 (word1, word2, word3)

                        if task_id == 'q1':
                            # 时间定向总分
                            mmse_task_score = sum([
                                mmse.get('q1_year', 0),
                                mmse.get('q1_season', 0),
                                mmse.get('q1_month', 0),
                                mmse.get('q1_weekday', 0)
                            ])
                        elif task_id == 'q2':
                            # 地点定向总分
                            mmse_task_score = sum([
                                mmse.get('q2_province', 0),
                                mmse.get('q2_street', 0),
                                mmse.get('q2_building', 0),
                                mmse.get('q2_floor', 0)
                            ])
                        elif task_id == 'q3':
                            # 即时记忆总分
                            mmse_task_score = mmse.get('q3_immediate', 0)
                        elif task_id == 'q4':
                            # 计算能力总分
                            mmse_task_score = sum([
                                mmse.get('q4_100_7', 0),
                                mmse.get('q4_93_7', 0),
                                mmse.get('q4_86_7', 0),
                                mmse.get('q4_79_7', 0),
                                mmse.get('q4_72_7', 0)
                            ])
                        elif task_id == 'q5':
                            # 延迟回忆总分
                            mmse_task_score = sum([
                                mmse.get('q5_word1', 0),
                                mmse.get('q5_word2', 0),
                                mmse.get('q5_word3', 0)
                            ])
                    
                    features_list.append({
                        'subject_id': full_subject_id,  # 使用完整ID (含组别前缀)
                        'group': grp,
                        'task_id': task_id,
                        # 逐帧分析法ROI占比 (与Module01一致)
                        'bg_ratio_frame': round(bg_ratio_frame, 2),
                        'inst_ratio_frame': round(inst_ratio_frame, 2),
                        'kw_ratio_frame': round(kw_ratio_frame, 2),
                        # IVT质心匹配法ROI占比
                        'bg_ratio_ivt': round(bg_ratio_ivt, 2),
                        'inst_ratio_ivt': round(inst_ratio_ivt, 2),
                        'kw_ratio_ivt': round(kw_ratio_ivt, 2),
                        # 其他特征
                        'total_fixation_time': round(total_fixation_time, 2),
                        'total_fixations': len(fixations),
                        'avg_fixation_duration': round(avg_fixation_duration, 2),
                        'total_saccades': len(saccades),
                        'avg_saccade_amplitude': round(avg_saccade_amplitude, 4),
                        'task_total_time': round(task_total_time, 2),
                        'mmse_total_score': mmse_total_score,
                        'mmse_task_score': mmse_task_score
                    })
            
            features_result = {
                'success': True,
                'total_records': len(features_list),
                'features': features_list
            }

            # 保存缓存
            self.save_cache(batch_result, features_result)

            return features_result

        except Exception as e:
            logger.error(f"特征统计失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def save_cache(self, batch_result: Dict, features_result: Dict):
        """
        保存分析结果到缓存

        Args:
            batch_result: analyze_batch的结果
            features_result: get_feature_statistics的结果
        """
        try:
            from datetime import datetime
            cache_file = self.cache_dir / 'latest_analysis.json'

            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'batch_result': batch_result,
                'features_result': features_result
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"缓存保存成功: {cache_file}")
            return True
        except Exception as e:
            logger.error(f"缓存保存失败: {e}")
            return False

    def load_cache(self) -> Optional[Dict]:
        """
        加载最近一次的分析结果缓存

        Returns:
            缓存数据字典或None
        """
        try:
            cache_file = self.cache_dir / 'latest_analysis.json'

            if not cache_file.exists():
                logger.info("没有找到缓存文件")
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            logger.info(f"缓存加载成功: {cache_data.get('timestamp')}")
            return cache_data
        except Exception as e:
            logger.error(f"缓存加载失败: {e}")
            return None
