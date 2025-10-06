"""
日志工具

提供统一的日志配置和管理
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from config.settings import Config


def setup_logger(
    name: str = None,
    level: str = None,
    log_file: Optional[Path] = None,
    log_format: str = None
) -> logging.Logger:
    """
    配置并返回logger

    Args:
        name: logger名称，默认为root logger
        level: 日志级别，默认从Config读取
        log_file: 日志文件路径，默认从Config读取
        log_format: 日志格式，默认从Config读取

    Returns:
        logging.Logger: 配置好的logger
    """
    # 使用默认配置
    if level is None:
        level = Config.LOG_LEVEL
    if log_file is None:
        log_file = Config.LOG_FILE
    if log_format is None:
        log_format = Config.LOG_FORMAT

    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # 清除已有的handlers
    logger.handlers.clear()

    # 创建formatter
    formatter = logging.Formatter(log_format)

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件handler
    if log_file is not None:
        # 确保日志目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger

    Args:
        name: logger名称

    Returns:
        logging.Logger: logger实例
    """
    return logging.getLogger(name)


class LoggerContext:
    """Logger上下文管理器，用于临时修改日志级别"""

    def __init__(self, logger: logging.Logger, level: str):
        """
        初始化上下文管理器

        Args:
            logger: logger实例
            level: 临时日志级别
        """
        self.logger = logger
        self.new_level = getattr(logging, level)
        self.old_level = None

    def __enter__(self):
        """进入上下文"""
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.logger.setLevel(self.old_level)
