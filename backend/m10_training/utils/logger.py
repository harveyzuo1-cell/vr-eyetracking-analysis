"""
模块10-B: 日志工具
====================================

提供统一的日志配置和TensorBoard集成。
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import torch
from torch.utils.tensorboard import SummaryWriter


class TrainingLogger:
    """
    训练日志管理器
    
    集成Python logging和TensorBoard，提供统一的日志接口。
    """
    
    def __init__(
        self,
        log_name: str,
        log_dir: Optional[Path] = None,
        tensorboard_dir: Optional[Path] = None,
        log_level: int = logging.INFO
    ):
        """
        初始化日志管理器
        
        Args:
            log_name: 日志器名称
            log_dir: 文本日志保存目录
            tensorboard_dir: TensorBoard日志目录
            log_level: 日志级别
        """
        self.log_name = log_name
        self.log_dir = log_dir
        self.tensorboard_dir = tensorboard_dir
        
        # 创建目录
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
        if tensorboard_dir:
            tensorboard_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置Python日志器
        self.logger = self._setup_python_logger(log_level)
        
        # 设置TensorBoard写入器
        self.tb_writer = None
        if tensorboard_dir:
            try:
                # 确保目录存在
                tb_dir_path = Path(tensorboard_dir)
                tb_dir_path.mkdir(parents=True, exist_ok=True)
                
                # 验证目录确实存在
                if not tb_dir_path.exists() or not tb_dir_path.is_dir():
                    raise RuntimeError(f"无法创建TensorBoard目录: {tb_dir_path}")
                
                # 使用字符串路径，让TensorBoard自己处理
                self.tb_writer = SummaryWriter(log_dir=str(tb_dir_path))
            except Exception as e:
                # 如果TensorBoard初始化失败，使用空的写入器
                import warnings
                warnings.warn(f"TensorBoard初始化失败，将禁用TensorBoard日志: {e}")
                self.tb_writer = None
        
        self.step_count = 0

    def _setup_python_logger(self, log_level: int) -> logging.Logger:
        """设置Python日志器"""
        logger = logging.getLogger(self.log_name)
        logger.setLevel(log_level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if self.log_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"{self.log_name}_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"日志文件: {log_file}")
        
        return logger

    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)

    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)

    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        记录指标到TensorBoard
        
        Args:
            metrics: 指标字典
            step: 步数（None则使用内部计数器）
        """
        if step is None:
            step = self.step_count
            self.step_count += 1
        
        if self.tb_writer:
            for key, value in metrics.items():
                self.tb_writer.add_scalar(key, value, step)
        
        # 同时记录到文本日志
        metrics_str = ", ".join([f"{k}={v:.4f}" for k, v in metrics.items()])
        self.logger.info(f"Step {step}: {metrics_str}")

    def log_scalars(self, tag: str, scalars: Dict[str, float], step: int):
        """
        记录多个标量到同一个图表
        
        Args:
            tag: 图表标签
            scalars: 标量字典
            step: 步数
        """
        if self.tb_writer:
            self.tb_writer.add_scalars(tag, scalars, step)

    def log_histogram(self, tag: str, values: torch.Tensor, step: int):
        """
        记录直方图
        
        Args:
            tag: 标签
            values: 张量值
            step: 步数
        """
        if self.tb_writer:
            self.tb_writer.add_histogram(tag, values, step)

    def log_model_graph(self, model: torch.nn.Module, input_sample: torch.Tensor):
        """
        记录模型图结构
        
        Args:
            model: PyTorch模型
            input_sample: 输入样本
        """
        if self.tb_writer:
            try:
                self.tb_writer.add_graph(model, input_sample)
                self.logger.info("模型图已记录到TensorBoard")
            except Exception as e:
                self.logger.warning(f"记录模型图失败: {str(e)}")

    def log_hyperparameters(self, hparams: Dict[str, Any], metrics: Dict[str, float]):
        """
        记录超参数和对应指标
        
        Args:
            hparams: 超参数字典
            metrics: 最终指标字典
        """
        if self.tb_writer:
            # 确保所有超参数值都是标量
            clean_hparams = {}
            for k, v in hparams.items():
                if isinstance(v, (int, float, str, bool)):
                    clean_hparams[k] = v
                else:
                    clean_hparams[k] = str(v)
            
            if self.tb_writer:
                self.tb_writer.add_hparams(clean_hparams, metrics)
                self.logger.info("超参数已记录到TensorBoard")
            else:
                self.logger.info("TensorBoard不可用，跳过超参数记录")

    def flush(self):
        """刷新TensorBoard缓冲区"""
        if self.tb_writer:
            self.tb_writer.flush()

    def close(self):
        """关闭日志器"""
        if self.tb_writer:
            self.tb_writer.close()
        
        # 移除所有处理器
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


def setup_training_logger(
    q_tag: str,
    rqa_sig: str,
    log_root: Path,
    tensorboard_root: Path
) -> TrainingLogger:
    """
    为特定任务设置训练日志器
    
    Args:
        q_tag: 任务标签 (Q1-Q5)
        rqa_sig: RQA配置签名
        log_root: 文本日志根目录
        tensorboard_root: TensorBoard根目录
        
    Returns:
        配置好的训练日志器
    """
    log_name = f"M10B_{rqa_sig}_{q_tag}"
    
    log_dir = log_root / rqa_sig / q_tag
    tb_dir = tensorboard_root / rqa_sig / q_tag
    
    logger = TrainingLogger(
        log_name=log_name,
        log_dir=log_dir,
        tensorboard_dir=tb_dir
    )
    
    logger.info(f"训练日志器初始化完成: {q_tag} @ {rqa_sig}")
    logger.info(f"文本日志: {log_dir}")
    logger.info(f"TensorBoard: {tb_dir}")
    
    return logger


class MetricsTracker:
    """
    训练指标跟踪器
    
    跟踪训练过程中的各种指标，并提供统计功能。
    """
    
    def __init__(self):
        self.metrics = {}
        self.best_metrics = {}
    
    def update(self, **kwargs):
        """更新指标"""
        for name, value in kwargs.items():
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(float(value))
    
    def get_latest(self, name: str) -> Optional[float]:
        """获取最新指标值"""
        if name in self.metrics and self.metrics[name]:
            return self.metrics[name][-1]
        return None
    
    def get_best(self, name: str, mode: str = "min") -> Optional[float]:
        """
        获取最佳指标值
        
        Args:
            name: 指标名称
            mode: "min" 或 "max"
        """
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        values = self.metrics[name]
        if mode == "min":
            return min(values)
        else:
            return max(values)
    
    def get_average(self, name: str, last_n: Optional[int] = None) -> Optional[float]:
        """
        获取平均值
        
        Args:
            name: 指标名称
            last_n: 最后N个值的平均（None则为全部）
        """
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        values = self.metrics[name]
        if last_n:
            values = values[-last_n:]
        
        return sum(values) / len(values)
    
    def is_improving(self, name: str, mode: str = "min", patience: int = 1) -> bool:
        """
        检查指标是否在改善
        
        Args:
            name: 指标名称
            mode: "min" 或 "max"
            patience: 容忍的停滞轮数
        """
        if name not in self.metrics or len(self.metrics[name]) < patience + 1:
            return True
        
        values = self.metrics[name]
        recent = values[-patience-1:]
        
        if mode == "min":
            return min(recent[1:]) < recent[0]
        else:
            return max(recent[1:]) > recent[0]
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """获取所有指标的汇总统计"""
        summary = {}
        
        for name, values in self.metrics.items():
            if values:
                summary[name] = {
                    "latest": values[-1],
                    "best_min": min(values),
                    "best_max": max(values),
                    "average": sum(values) / len(values),
                    "count": len(values)
                }
        
        return summary