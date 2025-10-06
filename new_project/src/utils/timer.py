"""
计时工具

提供性能计时功能
"""
import time
import logging
from typing import Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class Timer:
    """计时器类"""

    def __init__(self, name: str = "Timer", auto_log: bool = True):
        """
        初始化计时器

        Args:
            name: 计时器名称
            auto_log: 是否自动记录日志
        """
        self.name = name
        self.auto_log = auto_log
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        if self.auto_log:
            logger.debug(f"[{self.name}] 开始计时")

    def stop(self) -> float:
        """
        停止计时

        Returns:
            float: 经过的时间（秒）
        """
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time

        if self.auto_log:
            logger.info(f"[{self.name}] 耗时: {self.format_time(self.elapsed)}")

        return self.elapsed

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()

    @staticmethod
    def format_time(seconds: float) -> str:
        """
        格式化时间

        Args:
            seconds: 秒数

        Returns:
            str: 格式化后的时间字符串
        """
        if seconds < 1:
            return f"{seconds * 1000:.2f} ms"
        elif seconds < 60:
            return f"{seconds:.2f} s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes} min {remaining_seconds:.2f} s"


def timing(name: Optional[str] = None, log_level: str = "INFO"):
    """
    函数计时装饰器

    Args:
        name: 计时器名称，默认使用函数名
        log_level: 日志级别

    Example:
        @timing("处理数据")
        def process_data():
            # 函数内容
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            timer_name = name or func.__name__
            timer = Timer(timer_name, auto_log=False)

            timer.start()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = timer.stop()
                log_func = getattr(logger, log_level.lower())
                log_func(f"[{timer_name}] 执行完成，耗时: {Timer.format_time(elapsed)}")

        return wrapper
    return decorator


class StepTimer:
    """多步骤计时器"""

    def __init__(self, name: str = "StepTimer"):
        """
        初始化多步骤计时器

        Args:
            name: 计时器名称
        """
        self.name = name
        self.steps = []
        self.start_time = None
        self.last_step_time = None

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.last_step_time = self.start_time
        logger.debug(f"[{self.name}] 开始计时")

    def step(self, step_name: str):
        """
        记录一个步骤

        Args:
            step_name: 步骤名称
        """
        current_time = time.time()
        step_elapsed = current_time - self.last_step_time
        total_elapsed = current_time - self.start_time

        self.steps.append({
            'name': step_name,
            'step_time': step_elapsed,
            'total_time': total_elapsed
        })

        logger.info(
            f"[{self.name}] {step_name}: "
            f"{Timer.format_time(step_elapsed)} "
            f"(总计: {Timer.format_time(total_elapsed)})"
        )

        self.last_step_time = current_time

    def summary(self) -> str:
        """
        生成计时摘要

        Returns:
            str: 计时摘要字符串
        """
        if not self.steps:
            return f"[{self.name}] 无步骤记录"

        lines = [f"[{self.name}] 计时摘要:"]
        for i, step in enumerate(self.steps, 1):
            lines.append(
                f"  {i}. {step['name']}: {Timer.format_time(step['step_time'])}"
            )

        total_time = self.steps[-1]['total_time']
        lines.append(f"  总计: {Timer.format_time(total_time)}")

        return "\n".join(lines)

    def log_summary(self):
        """记录计时摘要到日志"""
        logger.info("\n" + self.summary())
