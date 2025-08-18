"""
模块10-B: 训练回调函数
====================================

提供早停、学习率调度等训练过程控制功能。
"""

import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Callback(ABC):
    """
    训练回调基类
    
    定义训练过程中的钩子函数接口。
    """
    
    @abstractmethod
    def on_train_begin(self, logs: Optional[Dict] = None):
        """训练开始时调用"""
        pass
    
    @abstractmethod
    def on_train_end(self, logs: Optional[Dict] = None):
        """训练结束时调用"""
        pass
    
    @abstractmethod
    def on_epoch_begin(self, epoch: int, logs: Optional[Dict] = None):
        """每个epoch开始时调用"""
        pass
    
    @abstractmethod
    def on_epoch_end(self, epoch: int, logs: Optional[Dict] = None):
        """每个epoch结束时调用"""
        pass
    
    @abstractmethod
    def on_batch_begin(self, batch: int, logs: Optional[Dict] = None):
        """每个batch开始时调用"""
        pass
    
    @abstractmethod
    def on_batch_end(self, batch: int, logs: Optional[Dict] = None):
        """每个batch结束时调用"""
        pass


class BaseCallback(Callback):
    """
    基础回调实现
    
    提供空的默认实现，子类只需重写需要的方法。
    """
    
    def on_train_begin(self, logs: Optional[Dict] = None):
        pass
    
    def on_train_end(self, logs: Optional[Dict] = None):
        pass
    
    def on_epoch_begin(self, epoch: int, logs: Optional[Dict] = None):
        pass
    
    def on_epoch_end(self, epoch: int, logs: Optional[Dict] = None):
        pass
    
    def on_batch_begin(self, batch: int, logs: Optional[Dict] = None):
        pass
    
    def on_batch_end(self, batch: int, logs: Optional[Dict] = None):
        pass


class EarlyStopping(BaseCallback):
    """
    早停回调
    
    监控指定指标，当性能不再改善时提前停止训练。
    """
    
    def __init__(
        self,
        monitor: str = "val_loss",
        patience: int = 10,
        mode: str = "min",
        min_delta: float = 0.0,
        restore_best_weights: bool = True,
        verbose: bool = True
    ):
        """
        初始化早停回调
        
        Args:
            monitor: 监控的指标名称
            patience: 容忍的停滞轮数
            mode: "min" 或 "max"，指标改善的方向
            min_delta: 最小改善幅度
            restore_best_weights: 是否恢复最佳权重
            verbose: 是否打印信息
        """
        self.monitor = monitor
        self.patience = patience
        self.mode = mode
        self.min_delta = abs(min_delta)
        self.restore_best_weights = restore_best_weights
        self.verbose = verbose
        
        # 状态变量
        self.best_value = None
        self.best_epoch = 0
        self.wait = 0
        self.stopped_epoch = 0
        self.best_weights = None
        self.should_stop = False
        
        # 比较函数
        if mode == "min":
            self.monitor_op = lambda current, best: current < (best - self.min_delta)
        else:
            self.monitor_op = lambda current, best: current > (best + self.min_delta)
        
        logger.info(f"EarlyStopping初始化: 监控'{monitor}', 耐心值{patience}, 模式'{mode}'")

    def on_train_begin(self, logs: Optional[Dict] = None):
        """训练开始时重置状态"""
        self.best_value = float('inf') if self.mode == "min" else float('-inf')
        self.best_epoch = 0
        self.wait = 0
        self.stopped_epoch = 0
        self.best_weights = None
        self.should_stop = False

    def on_epoch_end(self, epoch: int, logs: Optional[Dict] = None):
        """检查是否需要早停"""
        if logs is None:
            logs = {}
        
        current_value = logs.get(self.monitor)
        
        if current_value is None:
            if self.verbose:
                logger.warning(f"早停监控指标 '{self.monitor}' 不可用")
            return
        
        # 检查是否有改善
        if self.best_value is None or self.monitor_op(current_value, self.best_value):
            self.best_value = current_value
            self.best_epoch = epoch
            self.wait = 0
            
            # 保存最佳权重
            if self.restore_best_weights and "model" in logs:
                import copy
                self.best_weights = copy.deepcopy(logs["model"].state_dict())
            
            if self.verbose:
                logger.info(f"Epoch {epoch}: {self.monitor} 改善至 {current_value:.6f}")
        else:
            self.wait += 1
            
            if self.verbose and self.wait >= self.patience:
                logger.info(f"Epoch {epoch}: {self.monitor} 未改善，等待 {self.wait}/{self.patience}")
        
        # 检查是否需要停止
        if self.wait >= self.patience:
            self.stopped_epoch = epoch
            self.should_stop = True
            
            if self.verbose:
                logger.info(f"Early stopping triggered at epoch {epoch}")
                logger.info(f"最佳 {self.monitor}: {self.best_value:.6f} (epoch {self.best_epoch})")

    def on_train_end(self, logs: Optional[Dict] = None):
        """训练结束时恢复最佳权重"""
        if self.stopped_epoch > 0 and self.verbose:
            logger.info(f"训练在第 {self.stopped_epoch} 轮提前停止")
        
        # 恢复最佳权重
        if self.restore_best_weights and self.best_weights is not None and "model" in (logs or {}):
            if self.verbose:
                logger.info(f"恢复第 {self.best_epoch} 轮的最佳权重")
            logs["model"].load_state_dict(self.best_weights)


class ModelCheckpoint(BaseCallback):
    """
    模型检查点回调
    
    定期保存模型，或在指标改善时保存最佳模型。
    """
    
    def __init__(
        self,
        filepath: str,
        monitor: str = "val_loss",
        mode: str = "min",
        save_best_only: bool = True,
        save_freq: int = 1,
        verbose: bool = True
    ):
        """
        初始化模型检查点回调
        
        Args:
            filepath: 保存路径（可包含格式化占位符）
            monitor: 监控的指标名称
            mode: "min" 或 "max"
            save_best_only: 是否只保存最佳模型
            save_freq: 保存频率（每N个epoch）
            verbose: 是否打印信息
        """
        self.filepath = filepath
        self.monitor = monitor
        self.mode = mode
        self.save_best_only = save_best_only
        self.save_freq = save_freq
        self.verbose = verbose
        
        # 状态变量
        self.best_value = None
        
        # 比较函数
        if mode == "min":
            self.monitor_op = lambda current, best: current < best
        else:
            self.monitor_op = lambda current, best: current > best
        
        # 确保保存目录存在
        save_dir = Path(filepath).parent
        save_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ModelCheckpoint初始化: 路径'{filepath}', 监控'{monitor}', 模式'{mode}'")

    def on_train_begin(self, logs: Optional[Dict] = None):
        """训练开始时重置状态"""
        self.best_value = float('inf') if self.mode == "min" else float('-inf')

    def on_epoch_end(self, epoch: int, logs: Optional[Dict] = None):
        """检查是否需要保存模型"""
        if logs is None or "model" not in logs:
            return
        
        current_value = logs.get(self.monitor)
        should_save = False
        
        if self.save_best_only:
            if current_value is None:
                if self.verbose:
                    logger.warning(f"检查点监控指标 '{self.monitor}' 不可用")
                return
            
            # 检查是否是最佳模型
            if self.best_value is None or self.monitor_op(current_value, self.best_value):
                self.best_value = current_value
                should_save = True
                
                if self.verbose:
                    logger.info(f"发现更好的模型: {self.monitor} = {current_value:.6f}")
        else:
            # 按频率保存
            should_save = epoch % self.save_freq == 0
        
        if should_save:
            # 格式化文件路径
            filepath = self.filepath.format(
                epoch=epoch,
                **logs
            )
            
            # 保存模型
            self._save_model(logs["model"], filepath, epoch, logs)

    def _save_model(
        self,
        model: torch.nn.Module,
        filepath: str,
        epoch: int,
        logs: Dict
    ):
        """保存模型到文件"""
        try:
            # 准备保存的数据
            save_data = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "monitor_value": logs.get(self.monitor),
                "logs": logs
            }
            
            # 如果有优化器，也保存
            if "optimizer" in logs:
                save_data["optimizer_state_dict"] = logs["optimizer"].state_dict()
            
            # 保存
            torch.save(save_data, filepath)
            
            if self.verbose:
                logger.info(f"模型已保存: {filepath}")
                
        except Exception as e:
            logger.error(f"保存模型失败: {str(e)}")


class ReduceLROnPlateau(BaseCallback):
    """
    学习率递减回调
    
    当指标停止改善时减少学习率。
    """
    
    def __init__(
        self,
        optimizer: torch.optim.Optimizer,
        monitor: str = "val_loss",
        factor: float = 0.5,
        patience: int = 5,
        mode: str = "min",
        min_lr: float = 1e-7,
        verbose: bool = True
    ):
        """
        初始化学习率递减回调
        
        Args:
            optimizer: PyTorch优化器
            monitor: 监控的指标名称
            factor: 学习率衰减因子
            patience: 容忍的停滞轮数
            mode: "min" 或 "max"
            min_lr: 最小学习率
            verbose: 是否打印信息
        """
        self.optimizer = optimizer
        self.monitor = monitor
        self.factor = factor
        self.patience = patience
        self.mode = mode
        self.min_lr = min_lr
        self.verbose = verbose
        
        # 状态变量
        self.best_value = None
        self.wait = 0
        
        # 比较函数
        if mode == "min":
            self.monitor_op = lambda current, best: current < best
        else:
            self.monitor_op = lambda current, best: current > best
        
        logger.info(f"ReduceLROnPlateau初始化: 监控'{monitor}', 因子{factor}, 耐心值{patience}")

    def on_train_begin(self, logs: Optional[Dict] = None):
        """训练开始时重置状态"""
        self.best_value = float('inf') if self.mode == "min" else float('-inf')
        self.wait = 0

    def on_epoch_end(self, epoch: int, logs: Optional[Dict] = None):
        """检查是否需要调整学习率"""
        if logs is None:
            logs = {}
        
        current_value = logs.get(self.monitor)
        
        if current_value is None:
            if self.verbose:
                logger.warning(f"学习率调度监控指标 '{self.monitor}' 不可用")
            return
        
        # 检查是否有改善
        if self.best_value is None or self.monitor_op(current_value, self.best_value):
            self.best_value = current_value
            self.wait = 0
        else:
            self.wait += 1
        
        # 检查是否需要调整学习率
        if self.wait >= self.patience:
            self._reduce_lr()
            self.wait = 0

    def _reduce_lr(self):
        """减少学习率"""
        for param_group in self.optimizer.param_groups:
            old_lr = param_group['lr']
            new_lr = max(old_lr * self.factor, self.min_lr)
            
            if new_lr < old_lr:
                param_group['lr'] = new_lr
                
                if self.verbose:
                    logger.info(f"学习率调整: {old_lr:.2e} -> {new_lr:.2e}")
            else:
                if self.verbose:
                    logger.info(f"学习率已达到最小值: {self.min_lr:.2e}")


class CallbackManager:
    """
    回调管理器
    
    管理多个回调函数的执行。
    """
    
    def __init__(self, callbacks: list = None):
        """
        初始化回调管理器
        
        Args:
            callbacks: 回调函数列表
        """
        self.callbacks = callbacks or []

    def add_callback(self, callback: Callback):
        """添加回调函数"""
        self.callbacks.append(callback)

    def on_train_begin(self, logs: Optional[Dict] = None):
        """调用所有回调的训练开始钩子"""
        for callback in self.callbacks:
            callback.on_train_begin(logs)

    def on_train_end(self, logs: Optional[Dict] = None):
        """调用所有回调的训练结束钩子"""
        for callback in self.callbacks:
            callback.on_train_end(logs)

    def on_epoch_begin(self, epoch: int, logs: Optional[Dict] = None):
        """调用所有回调的epoch开始钩子"""
        for callback in self.callbacks:
            callback.on_epoch_begin(epoch, logs)

    def on_epoch_end(self, epoch: int, logs: Optional[Dict] = None):
        """调用所有回调的epoch结束钩子"""
        for callback in self.callbacks:
            callback.on_epoch_end(epoch, logs)

    def on_batch_begin(self, batch: int, logs: Optional[Dict] = None):
        """调用所有回调的batch开始钩子"""
        for callback in self.callbacks:
            callback.on_batch_begin(batch, logs)

    def on_batch_end(self, batch: int, logs: Optional[Dict] = None):
        """调用所有回调的batch结束钩子"""
        for callback in self.callbacks:
            callback.on_batch_end(batch, logs)

    def should_stop_training(self) -> bool:
        """检查是否应该停止训练"""
        for callback in self.callbacks:
            if hasattr(callback, 'should_stop') and callback.should_stop:
                return True
        return False