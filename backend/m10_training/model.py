"""
模块10-B: MLP网络结构
====================================

定义用于MMSE子分数预测的多层感知机模型。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EyeMLP(nn.Module):
    """
    眼动特征到MMSE子分数预测的多层感知机
    
    网络结构:
    - 输入层: 10个眼动特征
    - 隐藏层1: h1个神经元 + ReLU + Dropout
    - 隐藏层2: h2个神经元 + ReLU + Dropout (可选)
    - 输出层: 1个神经元 + Sigmoid (输出范围[0,1])
    """
    
    def __init__(
        self,
        input_dim: int = 10,
        h1: int = 32,
        h2: Optional[int] = 16,
        dropout: float = 0.25,
        output_dim: int = 1,
        activation: str = "relu",
        use_batch_norm: bool = False
    ):
        """
        初始化MLP模型
        
        Args:
            input_dim: 输入特征维度
            h1: 第一隐藏层神经元数
            h2: 第二隐藏层神经元数（None则为单隐藏层）
            dropout: Dropout比例
            output_dim: 输出维度
            activation: 激活函数类型
            use_batch_norm: 是否使用批归一化
        """
        super().__init__()
        
        self.input_dim = input_dim
        self.h1 = h1
        self.h2 = h2
        self.dropout = dropout
        self.output_dim = output_dim
        self.use_batch_norm = use_batch_norm
        
        # 激活函数选择
        if activation.lower() == "relu":
            self.activation = nn.ReLU()
        elif activation.lower() == "leaky_relu":
            self.activation = nn.LeakyReLU(0.1)
        elif activation.lower() == "elu":
            self.activation = nn.ELU()
        else:
            raise ValueError(f"不支持的激活函数: {activation}")
        
        # 构建网络层
        layers = []
        
        # 第一隐藏层
        layers.extend([
            nn.Linear(input_dim, h1),
            self.activation,
            nn.Dropout(dropout)
        ])
        
        if use_batch_norm:
            layers.insert(-1, nn.BatchNorm1d(h1))
        
        # 第二隐藏层（可选）
        if h2 is not None:
            layers.extend([
                nn.Linear(h1, h2),
                self.activation,
                nn.Dropout(dropout)
            ])
            
            if use_batch_norm:
                layers.insert(-1, nn.BatchNorm1d(h2))
            
            # 输出层
            layers.append(nn.Linear(h2, output_dim))
        else:
            # 直接从h1到输出
            layers.append(nn.Linear(h1, output_dim))
        
        # 输出激活（Sigmoid确保输出在[0,1]）
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
        
        # 权重初始化
        self._initialize_weights()
        
        logger.info(f"EyeMLP模型创建完成:")
        logger.info(f"  输入维度: {input_dim}")
        logger.info(f"  隐藏层: {h1}" + (f" -> {h2}" if h2 else ""))
        logger.info(f"  输出维度: {output_dim}")
        logger.info(f"  Dropout: {dropout}")
        logger.info(f"  参数总数: {self.count_parameters():,}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入特征张量 (batch_size, input_dim)
            
        Returns:
            预测输出 (batch_size, output_dim)
        """
        # 输入验证
        if x.dim() != 2:
            raise ValueError(f"期望2D输入张量，得到{x.dim()}D")
        if x.size(1) != self.input_dim:
            raise ValueError(f"期望输入维度{self.input_dim}，得到{x.size(1)}")
        
        # 前向传播
        output = self.network(x)
        
        # 如果输出维度为1，压缩最后一个维度
        if self.output_dim == 1:
            output = output.squeeze(-1)
            
        return output

    def _initialize_weights(self):
        """Xavier/Kaiming权重初始化"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                # Xavier初始化
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)

    def count_parameters(self) -> int:
        """计算模型可训练参数数量"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型详细信息
        
        Returns:
            包含模型架构和参数信息的字典
        """
        return {
            "architecture": {
                "input_dim": self.input_dim,
                "hidden_layers": [self.h1] + ([self.h2] if self.h2 else []),
                "output_dim": self.output_dim,
                "dropout": self.dropout,
                "batch_norm": self.use_batch_norm
            },
            "parameters": {
                "total": self.count_parameters(),
                "trainable": sum(p.numel() for p in self.parameters() if p.requires_grad),
                "non_trainable": sum(p.numel() for p in self.parameters() if not p.requires_grad)
            },
            "layer_info": [
                {
                    "name": name,
                    "type": type(module).__name__,
                    "parameters": sum(p.numel() for p in module.parameters()) if hasattr(module, 'parameters') else 0
                }
                for name, module in self.named_modules()
                if len(list(module.children())) == 0  # 只显示叶子模块
            ]
        }


class EyeMLPEnsemble(nn.Module):
    """
    多个EyeMLP模型的集成
    
    用于提高预测性能和鲁棒性
    """
    
    def __init__(self, models: list, weights: Optional[list] = None):
        """
        初始化模型集成
        
        Args:
            models: EyeMLP模型列表
            weights: 每个模型的权重（None则为等权重）
        """
        super().__init__()
        
        self.models = nn.ModuleList(models)
        self.n_models = len(models)
        
        if weights is None:
            self.weights = torch.ones(self.n_models) / self.n_models
        else:
            if len(weights) != self.n_models:
                raise ValueError("权重数量必须与模型数量相等")
            self.weights = torch.tensor(weights, dtype=torch.float32)
            self.weights = self.weights / self.weights.sum()  # 归一化
        
        logger.info(f"模型集成创建完成: {self.n_models}个模型")
        logger.info(f"权重: {self.weights.tolist()}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        集成前向传播
        
        Args:
            x: 输入特征张量
            
        Returns:
            加权平均预测结果
        """
        predictions = []
        
        for model in self.models:
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # 加权平均
        predictions = torch.stack(predictions, dim=0)  # (n_models, batch_size)
        weights = self.weights.to(predictions.device).view(-1, 1)
        
        ensemble_pred = torch.sum(predictions * weights, dim=0)
        
        return ensemble_pred


def create_model_from_config(config: Dict[str, Any]) -> EyeMLP:
    """
    从配置字典创建模型
    
    Args:
        config: 包含模型配置的字典
        
    Returns:
        初始化的EyeMLP模型
    """
    arch_config = config.get("arch", {})
    
    model = EyeMLP(
        input_dim=arch_config.get("input_dim", 10),
        h1=arch_config.get("h1", 32),
        h2=arch_config.get("h2", 16),
        dropout=arch_config.get("dropout", 0.25),
        output_dim=arch_config.get("output_dim", 1),
        activation=arch_config.get("activation", "relu"),
        use_batch_norm=arch_config.get("use_batch_norm", False)
    )
    
    return model


def save_model_checkpoint(
    model: EyeMLP,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    loss: float,
    filepath: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    保存模型检查点
    
    Args:
        model: 要保存的模型
        optimizer: 优化器
        epoch: 当前轮数
        loss: 当前损失
        filepath: 保存路径
        metadata: 额外元数据
    """
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "epoch": epoch,
        "loss": loss,
        "model_config": model.get_model_info(),
        "metadata": metadata or {}
    }
    
    torch.save(checkpoint, filepath)
    logger.info(f"模型检查点已保存: {filepath}")


def load_model_checkpoint(filepath: str, model: EyeMLP, optimizer: Optional[torch.optim.Optimizer] = None):
    """
    加载模型检查点
    
    Args:
        filepath: 检查点文件路径
        model: 要加载状态的模型
        optimizer: 可选的优化器
        
    Returns:
        包含检查点信息的字典
    """
    checkpoint = torch.load(filepath, map_location="cpu")
    
    model.load_state_dict(checkpoint["model_state_dict"])
    
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    
    logger.info(f"模型检查点已加载: {filepath}")
    logger.info(f"轮数: {checkpoint['epoch']}, 损失: {checkpoint['loss']:.4f}")
    
    return checkpoint