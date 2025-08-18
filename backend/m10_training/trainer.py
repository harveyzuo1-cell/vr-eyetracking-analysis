"""
模块10-B: 核心训练器
====================================

提供完整的PyTorch模型训练流程，包括数据加载、模型训练、验证和保存。
"""

import torch
import torch.nn as nn
import numpy as np
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import time
from datetime import datetime
import logging

from .model import EyeMLP, create_model_from_config
from .dataset import make_loaders, create_full_loader
from .callbacks import CallbackManager, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from .utils.logger import TrainingLogger, setup_training_logger
from .utils.metrics import MetricsCalculator, calculate_regression_metrics, evaluate_model_on_loader

logger = logging.getLogger(__name__)


class QTrainer:
    """
    MMSE子任务训练器
    
    负责单个Q任务（Q1-Q5）的模型训练、验证和保存。
    """
    
    def __init__(
        self,
        q_tag: str,
        rqa_sig: str,
        config: Dict[str, Any],
        device: Optional[str] = None
    ):
        """
        初始化训练器
        
        Args:
            q_tag: 任务标签 (Q1-Q5)
            rqa_sig: RQA配置签名
            config: 训练配置字典
            device: 计算设备
        """
        self.q_tag = q_tag
        self.rqa_sig = rqa_sig
        self.config = config
        
        # 设备配置
        if device is None:
            device = config.get("device", "cpu")
        
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA不可用，回退到CPU")
            device = "cpu"
        elif device.startswith("cuda:") and not torch.cuda.is_available():
            logger.warning("CUDA不可用，回退到CPU")
            device = "cpu"
            
        self.device = torch.device(device)
        logger.info(f"使用设备: {self.device}")
        
        # 路径配置
        self.save_root = Path(config.get("save_root", "models"))
        self.log_root = Path(config.get("log_root", "logs"))
        self.model_dir = self.save_root / rqa_sig
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建模型
        self.model = create_model_from_config(config)
        self.model.to(self.device)
        
        # 创建优化器
        training_config = config.get("training", {})
        lr = training_config.get("lr", 1e-3)
        weight_decay = config.get("regularization", {}).get("weight_decay", 1e-4)
        
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=lr,
            weight_decay=weight_decay
        )
        
        # 损失函数
        self.criterion = nn.MSELoss()
        
        # 学习率调度器
        self.scheduler = None
        lr_config = config.get("lr_scheduler", {})
        if lr_config.get("enable", False):
            self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode="min",
                factor=lr_config.get("factor", 0.5),
                patience=lr_config.get("patience", 8),
                min_lr=lr_config.get("min_lr", 1e-6)
            )
        
        # 训练日志器
        self.training_logger = setup_training_logger(
            q_tag, rqa_sig, self.log_root, self.log_root
        )
        
        # 指标跟踪器
        self.metrics_tracker = MetricsCalculator("regression")
        
        # 训练状态
        self.current_epoch = 0
        self.best_val_loss = float('inf')
        self.best_epoch = 0
        self.training_history = {
            "epochs": [],
            "train_loss": [],
            "val_loss": [],
            "train_metrics": [],
            "val_metrics": []
        }
        
        logger.info(f"QTrainer初始化完成: {q_tag} @ {rqa_sig}")
        logger.info(f"模型参数量: {self.model.count_parameters():,}")

    def setup_callbacks(self) -> CallbackManager:
        """
        设置训练回调
        
        Returns:
            配置好的回调管理器
        """
        callbacks = []
        
        training_config = self.config.get("training", {})
        
        # 早停回调
        early_stop_patience = training_config.get("early_stop_patience", 20)
        if early_stop_patience > 0:
            early_stop = EarlyStopping(
                monitor="val_loss",
                patience=early_stop_patience,
                mode="min",
                restore_best_weights=True,
                verbose=True
            )
            callbacks.append(early_stop)
        
        # 模型检查点回调
        checkpoint_path = str(self.model_dir / f"{self.q_tag}_best.pt")
        checkpoint = ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=True
        )
        callbacks.append(checkpoint)
        
        # 学习率调度回调
        lr_config = self.config.get("lr_scheduler", {})
        if lr_config.get("enable", False) and self.scheduler is None:
            # 如果没有使用PyTorch内置调度器，使用自定义回调
            lr_callback = ReduceLROnPlateau(
                optimizer=self.optimizer,
                monitor="val_loss",
                factor=lr_config.get("factor", 0.5),
                patience=lr_config.get("patience", 8),
                mode="min",
                verbose=True
            )
            callbacks.append(lr_callback)
        
        return CallbackManager(callbacks)

    def train_epoch(self, train_loader, epoch: int) -> Dict[str, float]:
        """
        训练一个epoch
        
        Args:
            train_loader: 训练数据加载器
            epoch: 当前epoch数
            
        Returns:
            训练指标字典
        """
        self.model.train()
        
        running_loss = 0.0
        self.metrics_tracker.reset()
        
        batch_count = 0
        start_time = time.time()
        
        for batch_idx, (batch_x, batch_y) in enumerate(train_loader):
            batch_x = batch_x.to(self.device)
            batch_y = batch_y.to(self.device)
            
            # 前向传播
            self.optimizer.zero_grad()
            predictions = self.model(batch_x)
            loss = self.criterion(predictions, batch_y)
            
            # 反向传播
            loss.backward()
            
            # 梯度裁剪
            grad_clip = self.config.get("regularization", {}).get("grad_clip_norm")
            if grad_clip:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), grad_clip)
            
            self.optimizer.step()
            
            # 更新统计
            running_loss += loss.item()
            self.metrics_tracker.update(batch_y, predictions)
            batch_count += 1
            
            # 记录batch级别日志
            if batch_idx % 10 == 0:  # 每10个batch记录一次
                self.training_logger.log_metrics({
                    "batch_loss": loss.item(),
                    "lr": self.optimizer.param_groups[0]['lr']
                }, step=epoch * len(train_loader) + batch_idx)
        
        # 计算epoch级别指标
        avg_loss = running_loss / batch_count
        train_metrics = self.metrics_tracker.compute()
        
        epoch_time = time.time() - start_time
        
        # 记录epoch级别日志
        log_metrics = {
            "train_loss": avg_loss,
            "train_rmse": train_metrics.get("rmse", 0),
            "train_mae": train_metrics.get("mae", 0),
            "train_r2": train_metrics.get("r2", 0),
            "epoch_time": epoch_time,
            "lr": self.optimizer.param_groups[0]['lr']
        }
        
        self.training_logger.log_metrics(log_metrics, step=epoch)
        
        return {
            "loss": avg_loss,
            "metrics": train_metrics,
            "time": epoch_time
        }

    def validate_epoch(self, val_loader, epoch: int) -> Dict[str, float]:
        """
        验证一个epoch
        
        Args:
            val_loader: 验证数据加载器
            epoch: 当前epoch数
            
        Returns:
            验证指标字典
        """
        self.model.eval()
        
        val_metrics, val_loss = evaluate_model_on_loader(
            self.model, val_loader, self.device, self.criterion
        )
        
        # 记录验证日志
        log_metrics = {
            "val_loss": val_loss,
            "val_rmse": val_metrics.get("rmse", 0),
            "val_mae": val_metrics.get("mae", 0),
            "val_r2": val_metrics.get("r2", 0)
        }
        
        self.training_logger.log_metrics(log_metrics, step=epoch)
        
        return {
            "loss": val_loss,
            "metrics": val_metrics
        }

    def fit(
        self,
        npz_path: Path,
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        val_split: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        训练模型
        
        Args:
            npz_path: 数据集文件路径
            epochs: 训练轮数（None则使用配置）
            batch_size: 批大小（None则使用配置）
            val_split: 验证集比例（None则使用配置）
            
        Returns:
            训练结果字典
        """
        # 使用配置或参数
        training_config = self.config.get("training", {})
        epochs = epochs or training_config.get("epochs", 100)
        batch_size = batch_size or training_config.get("batch_size", 16)
        val_split = val_split or training_config.get("val_split", 0.2)
        seed = self.config.get("seed", 42)
        
        logger.info(f"开始训练 {self.q_tag}:")
        logger.info(f"  数据集: {npz_path}")
        logger.info(f"  轮数: {epochs}")
        logger.info(f"  批大小: {batch_size}")
        logger.info(f"  验证集比例: {val_split}")
        
        # 创建数据加载器
        try:
            train_loader, val_loader = make_loaders(
                npz_path, batch_size, val_split, seed
            )
        except Exception as e:
            logger.error(f"创建数据加载器失败: {str(e)}")
            raise
        
        # 设置回调
        callback_manager = self.setup_callbacks()
        
        # 记录模型结构
        try:
            sample_input = torch.randn(1, 10).to(self.device)
            self.training_logger.log_model_graph(self.model, sample_input)
        except Exception as e:
            logger.warning(f"记录模型图失败: {str(e)}")
        
        # 开始训练
        start_time = time.time()
        callback_manager.on_train_begin({
            "model": self.model,
            "optimizer": self.optimizer
        })
        
        try:
            for epoch in range(1, epochs + 1):
                self.current_epoch = epoch
                
                # Epoch开始
                callback_manager.on_epoch_begin(epoch)
                
                # 训练
                train_result = self.train_epoch(train_loader, epoch)
                
                # 验证
                val_result = self.validate_epoch(val_loader, epoch)
                
                # 更新历史记录
                self.training_history["epochs"].append(epoch)
                self.training_history["train_loss"].append(train_result["loss"])
                self.training_history["val_loss"].append(val_result["loss"])
                self.training_history["train_metrics"].append(train_result["metrics"])
                self.training_history["val_metrics"].append(val_result["metrics"])
                
                # 更新最佳记录
                if val_result["loss"] < self.best_val_loss:
                    self.best_val_loss = val_result["loss"]
                    self.best_epoch = epoch
                
                # 学习率调度
                if self.scheduler:
                    self.scheduler.step(val_result["loss"])
                
                # 记录对比指标
                self.training_logger.log_scalars(
                    "Loss",
                    {
                        "train": train_result["loss"],
                        "val": val_result["loss"]
                    },
                    epoch
                )
                
                # Epoch结束
                logs = {
                    "model": self.model,
                    "optimizer": self.optimizer,
                    "train_loss": train_result["loss"],
                    "val_loss": val_result["loss"],
                    **train_result["metrics"],
                    **{f"val_{k}": v for k, v in val_result["metrics"].items()}
                }
                callback_manager.on_epoch_end(epoch, logs)
                
                # 打印进度
                if epoch % 10 == 0 or epoch == 1:
                    logger.info(
                        f"Epoch {epoch}/{epochs}: "
                        f"训练损失={train_result['loss']:.4f}, "
                        f"验证损失={val_result['loss']:.4f}, "
                        f"RMSE={val_result['metrics'].get('rmse', 0):.4f}, "
                        f"R²={val_result['metrics'].get('r2', 0):.4f}"
                    )
                
                # 检查早停
                if callback_manager.should_stop_training():
                    logger.info(f"早停触发，在第{epoch}轮停止训练")
                    break
                    
        except Exception as e:
            logger.error(f"训练过程出错: {str(e)}")
            raise
        finally:
            # 训练结束
            callback_manager.on_train_end({
                "model": self.model,
                "optimizer": self.optimizer
            })
        
        total_time = time.time() - start_time
        
        # 最终评估
        final_metrics = self._final_evaluation(npz_path)
        
        # 保存训练历史
        self._save_training_history()
        
        # 记录超参数
        self.training_logger.log_hyperparameters(
            self._get_hyperparameters(),
            {"final_val_loss": self.best_val_loss}
        )
        
        # 关闭日志器
        self.training_logger.close()
        
        logger.info(f"训练完成！")
        logger.info(f"总用时: {total_time:.2f}秒")
        logger.info(f"最佳验证损失: {self.best_val_loss:.6f} (epoch {self.best_epoch})")
        
        return {
            "success": True,
            "epochs_trained": self.current_epoch,
            "best_epoch": self.best_epoch,
            "best_val_loss": self.best_val_loss,
            "total_time": total_time,
            "final_metrics": final_metrics,
            "model_path": str(self.model_dir / f"{self.q_tag}_best.pt"),
            "history": self.training_history
        }

    def _final_evaluation(self, npz_path: Path) -> Dict[str, float]:
        """
        在完整数据集上进行最终评估
        
        Args:
            npz_path: 数据集路径
            
        Returns:
            最终评估指标
        """
        logger.info("进行最终评估...")
        
        # 加载最佳模型
        best_model_path = self.model_dir / f"{self.q_tag}_best.pt"
        if best_model_path.exists():
            checkpoint = torch.load(best_model_path, map_location=self.device, weights_only=False)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            logger.info(f"已加载最佳模型: epoch {checkpoint.get('epoch', 'unknown')}")
        
        # 在完整数据集上评估
        full_loader = create_full_loader(npz_path, batch_size=32)
        final_metrics, final_loss = evaluate_model_on_loader(
            self.model, full_loader, self.device, self.criterion
        )
        
        logger.info("最终评估结果:")
        for name, value in final_metrics.items():
            logger.info(f"  {name}: {value:.6f}")
        
        return final_metrics

    def _save_training_history(self):
        """保存训练历史"""
        history_path = self.model_dir / f"{self.q_tag}_history.json"
        
        # 转换为可序列化格式
        serializable_history = {}
        for key, values in self.training_history.items():
            if key.endswith("_metrics"):
                # 指标列表需要特殊处理
                serializable_history[key] = [
                    {k: float(v) if isinstance(v, (int, float)) else str(v) 
                     for k, v in metrics.items()}
                    for metrics in values
                ]
            else:
                serializable_history[key] = [float(v) for v in values]
        
        # 添加元数据
        serializable_history["metadata"] = {
            "q_tag": self.q_tag,
            "rqa_sig": self.rqa_sig,
            "epochs_trained": self.current_epoch,
            "best_epoch": self.best_epoch,
            "best_val_loss": float(self.best_val_loss),
            "saved_at": datetime.now().isoformat()
        }
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_history, f, indent=2, ensure_ascii=False)
        
        logger.info(f"训练历史已保存: {history_path}")
        
        # 同时保存单独的指标文件（供API查询）
        self._save_best_metrics()

    def _save_best_metrics(self):
        """保存最佳模型的指标文件（供API查询使用）"""
        metrics_path = self.model_dir / f"{self.q_tag}_best_metrics.json"
        
        # 从训练历史中提取最佳指标
        best_metrics = {
            "best_epoch": self.best_epoch,
            "train_time_seconds": float(self.training_history.get("total_time", 0)),
            "model_params": sum(p.numel() for p in self.model.parameters()),
            "created_at": datetime.now().isoformat()
        }
        
        # 添加最佳验证指标
        if hasattr(self, 'best_val_metrics') and self.best_val_metrics:
            for key, value in self.best_val_metrics.items():
                if isinstance(value, (int, float)):
                    best_metrics[f"val_{key}"] = float(value)
        
        # 从训练历史中提取测试指标（如果有最终评估的话）
        if "final_test_metrics" in self.training_history:
            test_metrics = self.training_history["final_test_metrics"]
            for key, value in test_metrics.items():
                if isinstance(value, (int, float)):
                    best_metrics[f"test_{key}"] = float(value)
        
        # 添加配置信息
        arch_config = self.config.get("arch", {})
        training_config = self.config.get("training", {})
        best_metrics["config"] = {
            "arch": {
                "h1": arch_config.get("h1", 32),
                "h2": arch_config.get("h2", 16),
                "dropout": arch_config.get("dropout", 0.25)
            },
            "training": {
                "lr": training_config.get("lr", 0.001),
                "epochs": training_config.get("epochs", 200)
            },
            "device": str(self.device)
        }
        
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(best_metrics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"最佳模型指标已保存: {metrics_path}")

    def _get_hyperparameters(self) -> Dict[str, Any]:
        """获取超参数字典"""
        training_config = self.config.get("training", {})
        arch_config = self.config.get("arch", {})
        
        return {
            "q_tag": self.q_tag,
            "rqa_sig": self.rqa_sig,
            "device": str(self.device),
            "lr": training_config.get("lr", 1e-3),
            "batch_size": training_config.get("batch_size", 16),
            "val_split": training_config.get("val_split", 0.2),
            "h1": arch_config.get("h1", 32),
            "h2": arch_config.get("h2", 16),
            "dropout": arch_config.get("dropout", 0.25),
            "weight_decay": self.config.get("regularization", {}).get("weight_decay", 1e-4),
            "early_stop_patience": training_config.get("early_stop_patience", 20)
        }


def create_trainer_from_config(
    config_path: str,
    q_tag: str,
    rqa_sig: str,
    override_config: Optional[Dict] = None
) -> QTrainer:
    """
    从配置文件创建训练器
    
    Args:
        config_path: 配置文件路径
        q_tag: 任务标签
        rqa_sig: RQA签名
        override_config: 覆盖配置
        
    Returns:
        训练器实例
    """
    # 加载基础配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 应用覆盖配置
    if override_config:
        config = deep_update(config, override_config)
    
    return QTrainer(q_tag, rqa_sig, config)


def deep_update(base_dict: Dict, update_dict: Dict) -> Dict:
    """
    深度更新字典
    
    Args:
        base_dict: 基础字典
        update_dict: 更新字典
        
    Returns:
        更新后的字典
    """
    result = base_dict.copy()
    
    for key, value in update_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_update(result[key], value)
        else:
            result[key] = value
    
    return result