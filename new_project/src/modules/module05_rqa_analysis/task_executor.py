"""
RQA任务执行器 - CPU多线程并行处理

实现大规模批量RQA分析的任务调度和并行执行
"""

import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Dict, List, Callable, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from multiprocessing import cpu_count

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class TaskStatus:
    """任务状态"""
    task_id: str
    total_files: int
    processed_files: int
    failed_files: int
    current_step: int  # 1-5
    status: str  # 'pending', 'running', 'paused', 'completed', 'failed', 'cancelled'
    start_time: str
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    current_param: Optional[Dict] = None
    # 新增断点续传字段
    current_param_index: int = 0  # 当前处理到第几个参数组合
    param_combinations: Optional[List[Dict]] = None  # 参数组合列表
    groups: Optional[List[str]] = None  # 分组列表

    @property
    def progress(self) -> float:
        """进度百分比"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

    def to_dict(self) -> Dict:
        """转换为字典"""
        result = asdict(self)
        result['progress'] = self.progress

        # 计算预计剩余时间
        if self.status == 'running' and self.processed_files > 0:
            elapsed = (datetime.now() - datetime.fromisoformat(self.start_time)).total_seconds()
            avg_time = elapsed / self.processed_files
            remaining_files = self.total_files - self.processed_files
            eta_seconds = avg_time * remaining_files
            result['eta_seconds'] = int(eta_seconds)
        else:
            result['eta_seconds'] = None

        return result


class RQATaskExecutor:
    """RQA任务执行器 - CPU多线程"""

    def __init__(self, max_workers: int = None, tasks_dir: Path = None):
        """
        初始化任务执行器

        Args:
            max_workers: 最大线程数，默认为CPU核心数
            tasks_dir: 任务状态保存目录
        """
        self.max_workers = max_workers or cpu_count()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # 任务管理
        self.active_tasks: Dict[str, Future] = {}
        self.task_status: Dict[str, TaskStatus] = {}

        # 线程安全的进度计数器
        self.progress_lock = threading.Lock()

        # 任务取消和暂停标志
        self.cancel_flags: Dict[str, threading.Event] = {}
        self.pause_flags: Dict[str, threading.Event] = {}

        # 任务状态持久化目录
        self.tasks_dir = tasks_dir or Path(__file__).parent.parent.parent.parent / 'data' / '05_rqa_analysis' / 'tasks'
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        # 在初始化时恢复未完成的任务
        self._restore_tasks()

        logger.info(f"RQATaskExecutor初始化: max_workers={self.max_workers}, tasks_dir={self.tasks_dir}")

    def submit_batch_task(self, task_id: str, service,
                         param_combinations: List[Dict],
                         groups: List[str],
                         callback: Callable = None) -> str:
        """
        提交批量任务

        Args:
            task_id: 任务ID
            service: RQAAnalysisService实例
            param_combinations: 参数组合列表
            groups: 分组列表 ['control', 'mci', 'ad']
            callback: 完成回调函数

        Returns:
            task_id
        """
        # 统计总文件数
        total_files = 0
        for group in groups:
            csv_files = service.scan_calibrated_files(group)
            total_files += len(csv_files)

        total_files *= len(param_combinations)

        # 初始化任务状态
        self.task_status[task_id] = TaskStatus(
            task_id=task_id,
            total_files=total_files,
            processed_files=0,
            failed_files=0,
            current_step=1,
            status='pending',
            start_time=datetime.now().isoformat(),
            current_param=param_combinations[0] if param_combinations else None,
            current_param_index=0,
            param_combinations=param_combinations,
            groups=groups
        )

        # 创建取消和暂停标志
        self.cancel_flags[task_id] = threading.Event()
        self.pause_flags[task_id] = threading.Event()

        # 提交到线程池
        future = self.executor.submit(
            self._execute_batch_task,
            task_id,
            service,
            param_combinations,
            groups
        )

        # 添加完成回调
        if callback:
            future.add_done_callback(callback)

        self.active_tasks[task_id] = future
        self.task_status[task_id].status = 'running'
        self._save_task_state(task_id)

        logger.info(f"任务已提交: {task_id}, 总文件数={total_files}")

        return task_id

    def _execute_batch_task(self, task_id: str, service,
                           param_combinations: List[Dict],
                           groups: List[str]):
        """
        执行批量任务（在线程中运行）

        流程:
        1. 遍历所有参数组合
        2. 对每个组合，并行处理所有文件（Step 1）
        3. 执行Step 2-5（串行）
        4. 更新进度
        """
        try:
            # 设置当前批次task_id到service（用于metadata记录）
            service.current_task_id = task_id
            service.current_data_version = 'v1'  # 目前默认V1数据

            for param_idx, params in enumerate(param_combinations):
                # 检查是否取消
                if self.cancel_flags[task_id].is_set():
                    logger.info(f"任务已取消: {task_id}")
                    self.task_status[task_id].status = 'cancelled'
                    self.task_status[task_id].end_time = datetime.now().isoformat()
                    self._save_task_state(task_id)
                    return

                # 检查是否暂停
                if self.pause_flags[task_id].is_set():
                    logger.info(f"任务已暂停: {task_id}")
                    with self.progress_lock:
                        self.task_status[task_id].status = 'paused'
                        self.task_status[task_id].current_param_index = param_idx
                        self._save_task_state(task_id)
                    return

                logger.info(f"任务 {task_id}: 处理参数组合 {param_idx+1}/{len(param_combinations)}")

                # 更新当前参数和索引
                with self.progress_lock:
                    self.task_status[task_id].current_param = params
                    self.task_status[task_id].current_param_index = param_idx

                # Step 1: RQA计算（并行处理文件）
                self.task_status[task_id].current_step = 1
                step1_result = self._execute_step1_parallel(task_id, service, params, groups)

                if not step1_result['success']:
                    logger.error(f"Step 1失败: {step1_result.get('error')}")
                    continue

                # Step 2: 数据合并
                self.task_status[task_id].current_step = 2
                step2_result = service.step2_data_merging(params, groups)

                if not step2_result['success']:
                    logger.error(f"Step 2失败: {step2_result.get('error')}")
                    continue

                # Step 3: 特征增强
                self.task_status[task_id].current_step = 3
                step3_result = service.step3_feature_enrichment(params)

                if not step3_result['success']:
                    logger.error(f"Step 3失败: {step3_result.get('error')}")
                    continue

                # Step 4: 统计分析
                self.task_status[task_id].current_step = 4
                step4_result = service.step4_statistical_analysis(params)

                if not step4_result['success']:
                    logger.error(f"Step 4失败: {step4_result.get('error')}")
                    continue

                # Step 5: 可视化
                self.task_status[task_id].current_step = 5
                step5_result = service.step5_visualization(params)

                if not step5_result['success']:
                    logger.error(f"Step 5失败: {step5_result.get('error')}")
                    continue

                logger.info(f"参数组合完成: {params}")
                # 每完成一个参数组合就保存一次状态
                self._save_task_state(task_id)

            # 标记完成
            with self.progress_lock:
                self.task_status[task_id].status = 'completed'
                self.task_status[task_id].end_time = datetime.now().isoformat()
                self._save_task_state(task_id)

            logger.info(f"任务完成: {task_id}")

        except Exception as e:
            logger.error(f"任务失败: {task_id} - {e}", exc_info=True)
            with self.progress_lock:
                self.task_status[task_id].status = 'failed'
                self.task_status[task_id].error_message = str(e)
                self.task_status[task_id].end_time = datetime.now().isoformat()
                self._save_task_state(task_id)

    def _execute_step1_parallel(self, task_id: str, service,
                                params: Dict, groups: List[str]) -> Dict:
        """
        Step 1: 并行RQA计算

        策略:
        - 将所有CSV文件分成batch
        - 每个batch提交给线程池
        - 等待所有batch完成
        """
        results = {group: [] for group in groups}

        for group in groups:
            # 扫描文件
            csv_files = service.scan_calibrated_files(group)
            logger.info(f"任务 {task_id}: 处理 {group} 组, {len(csv_files)} 个文件")

            # 批量提交到线程池
            batch_size = max(1, len(csv_files) // (self.max_workers * 3))
            futures = []

            for i in range(0, len(csv_files), batch_size):
                batch = csv_files[i:i+batch_size]
                future = self.executor.submit(
                    self._process_file_batch,
                    task_id,
                    service,
                    batch,
                    params
                )
                futures.append((future, len(batch)))

            # 收集结果
            for future, batch_len in futures:
                # 检查取消标志
                if self.cancel_flags[task_id].is_set():
                    return {'success': False, 'error': '任务已取消'}

                try:
                    batch_results = future.result()
                    results[group].extend(batch_results)

                    # 更新进度
                    with self.progress_lock:
                        self.task_status[task_id].processed_files += len(batch_results)

                except Exception as e:
                    logger.error(f"批处理失败: {e}")
                    with self.progress_lock:
                        self.task_status[task_id].failed_files += batch_len

            # 保存该组结果
            import pandas as pd
            df = pd.DataFrame(results[group])
            output_dir = service.get_step_directory(params, 'step1_rqa_calculation')
            df.to_csv(output_dir / f'{group}_rqa_results.csv', index=False)
            logger.info(f"保存 {group} 组结果: {len(results[group])} 条记录")

        # 保存元数据
        total_processed = sum(len(r) for r in results.values())
        service.save_param_metadata(
            params, 1,
            {
                'files_processed': total_processed,
                'files_failed': self.task_status[task_id].failed_files
            },
            task_id=task_id,
            data_version='v1'  # 目前默认V1数据
        )

        return {
            'success': True,
            'total_files_processed': total_processed
        }

    def _process_file_batch(self, task_id: str, service,
                           files: List[Path], params: Dict) -> List[Dict]:
        """
        处理一批文件（在单个线程中）

        Args:
            task_id: 任务ID
            service: RQAAnalysisService实例
            files: 文件路径列表
            params: RQA参数

        Returns:
            结果列表
        """
        results = []

        for file_path in files:
            # 检查取消标志
            if self.cancel_flags[task_id].is_set():
                break

            try:
                # 提取subject_id和task_id
                filename = file_path.stem  # 去掉.csv后缀
                parts = filename.replace('_calibrated', '').split('_')

                if len(parts) >= 2:
                    task_id_str = parts[-1]
                    subject_id = '_'.join(parts[:-1])
                else:
                    logger.warning(f"无法解析文件名: {filename}")
                    continue

                # RQA分析
                rqa_result = service.analyzer.analyze_single_file(str(file_path), params)

                # 添加到结果
                result_row = {
                    'subject_id': subject_id,
                    'task_id': task_id_str,
                    **rqa_result
                }
                results.append(result_row)

            except Exception as e:
                logger.error(f"处理文件失败: {file_path} - {e}")
                # 继续处理下一个文件，不中断整个batch

        return results

    def _save_task_state(self, task_id: str):
        """保存任务状态到磁盘"""
        try:
            task_file = self.tasks_dir / f"{task_id}.json"
            with self.progress_lock:
                status_dict = self.task_status[task_id].to_dict()

            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(status_dict, f, ensure_ascii=False, indent=2)

            logger.debug(f"任务状态已保存: {task_id}")
        except Exception as e:
            logger.error(f"保存任务状态失败: {task_id} - {e}")

    def _restore_tasks(self):
        """从磁盘恢复未完成的任务"""
        try:
            for task_file in self.tasks_dir.glob("*.json"):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        status_dict = json.load(f)

                    # 只恢复未完成的任务
                    if status_dict['status'] in ['running', 'paused', 'pending']:
                        # 如果是running状态，改为paused（因为服务重启了）
                        if status_dict['status'] == 'running':
                            status_dict['status'] = 'paused'

                        # 重建TaskStatus对象
                        task_status = TaskStatus(
                            task_id=status_dict['task_id'],
                            total_files=status_dict['total_files'],
                            processed_files=status_dict['processed_files'],
                            failed_files=status_dict['failed_files'],
                            current_step=status_dict['current_step'],
                            status=status_dict['status'],
                            start_time=status_dict['start_time'],
                            end_time=status_dict.get('end_time'),
                            error_message=status_dict.get('error_message'),
                            current_param=status_dict.get('current_param'),
                            current_param_index=status_dict.get('current_param_index', 0),
                            param_combinations=status_dict.get('param_combinations'),
                            groups=status_dict.get('groups')
                        )

                        self.task_status[task_status.task_id] = task_status
                        self.cancel_flags[task_status.task_id] = threading.Event()
                        self.pause_flags[task_status.task_id] = threading.Event()
                        # 如果是paused状态，设置暂停标志
                        if task_status.status == 'paused':
                            self.pause_flags[task_status.task_id].set()

                        logger.info(f"已恢复任务: {task_status.task_id}, 状态={task_status.status}")

                except Exception as e:
                    logger.error(f"恢复任务失败: {task_file} - {e}")

        except Exception as e:
            logger.error(f"恢复任务列表失败: {e}")

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        if task_id not in self.task_status:
            logger.warning(f"任务不存在: {task_id}")
            return False

        with self.progress_lock:
            if self.task_status[task_id].status != 'running':
                logger.warning(f"任务不在运行中，无法暂停: {task_id}, 当前状态={self.task_status[task_id].status}")
                return False

            self.pause_flags[task_id].set()
            self.task_status[task_id].status = 'paused'
            self._save_task_state(task_id)

        logger.info(f"任务已暂停: {task_id}")
        return True

    def resume_task(self, task_id: str, service) -> bool:
        """恢复任务"""
        if task_id not in self.task_status:
            logger.warning(f"任务不存在: {task_id}")
            return False

        with self.progress_lock:
            if self.task_status[task_id].status != 'paused':
                logger.warning(f"任务不在暂停状态，无法恢复: {task_id}, 当前状态={self.task_status[task_id].status}")
                return False

            # 清除暂停标志
            self.pause_flags[task_id].clear()
            self.task_status[task_id].status = 'running'

            # 重新提交任务
            param_combinations = self.task_status[task_id].param_combinations
            groups = self.task_status[task_id].groups
            current_param_index = self.task_status[task_id].current_param_index

            # 从断点处继续
            remaining_params = param_combinations[current_param_index:]

            if not remaining_params:
                logger.warning(f"任务已完成所有参数组合: {task_id}")
                self.task_status[task_id].status = 'completed'
                self.task_status[task_id].end_time = datetime.now().isoformat()
                self._save_task_state(task_id)
                return False

            # 提交到线程池
            future = self.executor.submit(
                self._execute_batch_task,
                task_id,
                service,
                remaining_params,
                groups
            )

            self.active_tasks[task_id] = future
            self._save_task_state(task_id)

        logger.info(f"任务已恢复: {task_id}, 从参数组合 {current_param_index}/{len(param_combinations)} 继续")
        return True

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典，如果任务不存在返回None
        """
        if task_id not in self.task_status:
            return None

        return self.task_status[task_id].to_dict()

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id not in self.cancel_flags:
            return False

        # 设置取消标志
        self.cancel_flags[task_id].set()

        # 尝试取消Future
        if task_id in self.active_tasks:
            future = self.active_tasks[task_id]
            cancelled = future.cancel()

            if cancelled or self.task_status[task_id].status == 'running':
                self.task_status[task_id].status = 'cancelled'
                self.task_status[task_id].end_time = datetime.now().isoformat()
                logger.info(f"任务已取消: {task_id}")
                return True

        return False

    def get_all_tasks(self) -> List[Dict]:
        """
        获取所有任务状态

        Returns:
            任务状态列表
        """
        return [status.to_dict() for status in self.task_status.values()]

    def cleanup_completed_tasks(self, older_than_hours: int = 24):
        """
        清理已完成的任务

        Args:
            older_than_hours: 清理多少小时之前完成的任务
        """
        now = datetime.now()
        to_remove = []

        for task_id, status in self.task_status.items():
            if status.status in ['completed', 'failed', 'cancelled']:
                if status.end_time:
                    end_time = datetime.fromisoformat(status.end_time)
                    hours_ago = (now - end_time).total_seconds() / 3600

                    if hours_ago > older_than_hours:
                        to_remove.append(task_id)

        for task_id in to_remove:
            del self.task_status[task_id]
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            if task_id in self.cancel_flags:
                del self.cancel_flags[task_id]

        if to_remove:
            logger.info(f"清理了 {len(to_remove)} 个已完成任务")

    def shutdown(self, wait: bool = True):
        """
        关闭执行器

        Args:
            wait: 是否等待所有任务完成
        """
        logger.info("关闭RQATaskExecutor...")
        self.executor.shutdown(wait=wait)
