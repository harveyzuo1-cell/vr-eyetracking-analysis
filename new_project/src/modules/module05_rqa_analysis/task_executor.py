"""
RQA任务执行器 - CPU多线程并行处理

实现大规模批量RQA分析的任务调度和并行执行
"""

import threading
import time
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
    status: str  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    start_time: str
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    current_param: Optional[Dict] = None

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

    def __init__(self, max_workers: int = None):
        """
        初始化任务执行器

        Args:
            max_workers: 最大线程数，默认为CPU核心数
        """
        self.max_workers = max_workers or cpu_count()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # 任务管理
        self.active_tasks: Dict[str, Future] = {}
        self.task_status: Dict[str, TaskStatus] = {}

        # 线程安全的进度计数器
        self.progress_lock = threading.Lock()

        # 任务取消标志
        self.cancel_flags: Dict[str, threading.Event] = {}

        logger.info(f"RQATaskExecutor初始化: max_workers={self.max_workers}")

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
            current_param=param_combinations[0] if param_combinations else None
        )

        # 创建取消标志
        self.cancel_flags[task_id] = threading.Event()

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
            for param_idx, params in enumerate(param_combinations):
                # 检查是否取消
                if self.cancel_flags[task_id].is_set():
                    logger.info(f"任务已取消: {task_id}")
                    self.task_status[task_id].status = 'cancelled'
                    self.task_status[task_id].end_time = datetime.now().isoformat()
                    return

                logger.info(f"任务 {task_id}: 处理参数组合 {param_idx+1}/{len(param_combinations)}")

                # 更新当前参数
                with self.progress_lock:
                    self.task_status[task_id].current_param = params

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

            # 标记完成
            with self.progress_lock:
                self.task_status[task_id].status = 'completed'
                self.task_status[task_id].end_time = datetime.now().isoformat()

            logger.info(f"任务完成: {task_id}")

        except Exception as e:
            logger.error(f"任务失败: {task_id} - {e}", exc_info=True)
            with self.progress_lock:
                self.task_status[task_id].status = 'failed'
                self.task_status[task_id].error_message = str(e)
                self.task_status[task_id].end_time = datetime.now().isoformat()

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
        service.save_param_metadata(params, 1, {
            'files_processed': total_processed,
            'files_failed': self.task_status[task_id].failed_files
        })

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
