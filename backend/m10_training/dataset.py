"""
模块10-B: 数据加载模块
====================================

自定义PyTorch数据集和数据加载器，用于处理模块10-A生成的眼动特征数据。
"""

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class EyeDataset(Dataset):
    """
    眼动特征数据集
    
    加载模块10-A生成的npz文件，包含：
    - X: 眼动特征矩阵 (N, 10)
    - y: MMSE子分数标签 (N,)
    """
    
    def __init__(self, npz_path: Path, normalize_targets: bool = True):
        """
        初始化数据集
        
        Args:
            npz_path: .npz文件路径
            normalize_targets: 是否归一化目标值到[0,1]
        """
        if not npz_path.exists():
            raise FileNotFoundError(f"数据集文件不存在: {npz_path}")
            
        # 加载数据
        try:
            data = np.load(npz_path, allow_pickle=True)
            self.X = torch.from_numpy(data["X"]).float()
            self.y = torch.from_numpy(data["y"]).float()
        except Exception as e:
            logger.error(f"加载数据集失败 {npz_path}: {str(e)}")
            raise
            
        # 数据验证
        if self.X.shape[0] != self.y.shape[0]:
            raise ValueError(f"特征和标签样本数不匹配: {self.X.shape[0]} vs {self.y.shape[0]}")
            
        if self.X.shape[1] != 10:
            raise ValueError(f"特征维度应为10，实际为: {self.X.shape[1]}")
            
        # 目标值归一化处理（如果需要）
        self.normalize_targets = normalize_targets
        if normalize_targets:
            # 假设MMSE子分数已经在模块10-A中归一化到[0,1]
            # 这里进行额外的检查和确保
            if self.y.min() < 0 or self.y.max() > 1:
                logger.warning(f"目标值可能未正确归一化: min={self.y.min():.3f}, max={self.y.max():.3f}")
                # 强制归一化到[0,1]
                self.y = (self.y - self.y.min()) / (self.y.max() - self.y.min() + 1e-8)
                
        self.n_samples = self.X.shape[0]
        logger.info(f"数据集加载完成: {self.n_samples} 样本, 特征维度 {self.X.shape[1]}")
        logger.debug(f"特征统计: 最小值={self.X.min():.3f}, 最大值={self.X.max():.3f}, 均值={self.X.mean():.3f}")
        logger.debug(f"标签统计: 最小值={self.y.min():.3f}, 最大值={self.y.max():.3f}, 均值={self.y.mean():.3f}")

    def __len__(self) -> int:
        """返回数据集大小"""
        return self.n_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        获取单个样本
        
        Args:
            idx: 样本索引
            
        Returns:
            (features, target): 特征张量和目标值
        """
        return self.X[idx], self.y[idx]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据集统计信息
        
        Returns:
            包含数据集统计信息的字典
        """
        return {
            "n_samples": self.n_samples,
            "feature_dim": self.X.shape[1],
            "features": {
                "mean": self.X.mean(dim=0).tolist(),
                "std": self.X.std(dim=0).tolist(),
                "min": self.X.min(dim=0)[0].tolist(),
                "max": self.X.max(dim=0)[0].tolist()
            },
            "targets": {
                "mean": self.y.mean().item(),
                "std": self.y.std().item(),
                "min": self.y.min().item(),
                "max": self.y.max().item()
            }
        }


def make_loaders(
    npz_path: Union[str, Path], 
    batch_size: int, 
    val_split: Optional[float] = None, 
    seed: int = 42,
    num_workers: int = 0
) -> Tuple[DataLoader, DataLoader]:
    """
    创建训练和验证数据加载器
    
    Args:
        npz_path: 数据集文件路径
        batch_size: 批大小
        val_split: 验证集比例 (0-1)
        seed: 随机种子
        num_workers: 数据加载器工作进程数
        
    Returns:
        (train_loader, val_loader): 训练和验证数据加载器
    """
    # 确保路径是Path对象
    npz_path = Path(npz_path)
    
    # 创建数据集
    dataset = EyeDataset(npz_path)
    
    # 处理val_split为None的情况
    if val_split is None:
        val_split = 0.2
        logger.warning(f"val_split为None，使用默认值: {val_split}")
    
    # 计算分割大小
    n_total = len(dataset)
    n_val = int(n_total * val_split)
    n_train = n_total - n_val
    
    if n_train <= 0 or n_val <= 0:
        raise ValueError(f"数据分割无效: 训练集{n_train}样本, 验证集{n_val}样本")
    
    # 随机分割数据集
    generator = torch.Generator().manual_seed(seed)
    train_dataset, val_dataset = random_split(
        dataset, [n_train, n_val], generator=generator
    )
    
    # 创建数据加载器
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        drop_last=True,  # 丢弃最后不完整的批次以保持一致性
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()  # GPU加速
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        drop_last=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )
    
    logger.info(f"数据加载器创建完成:")
    logger.info(f"  训练集: {n_train} 样本, {len(train_loader)} 批次")
    logger.info(f"  验证集: {n_val} 样本, {len(val_loader)} 批次")
    logger.info(f"  批大小: {batch_size}")
    
    return train_loader, val_loader


def create_full_loader(npz_path: Path, batch_size: int = 32) -> DataLoader:
    """
    创建完整数据集的加载器（用于最终评估）
    
    Args:
        npz_path: 数据集文件路径
        batch_size: 批大小
        
    Returns:
        完整数据集的加载器
    """
    dataset = EyeDataset(npz_path)
    
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        drop_last=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available()
    )
    
    logger.info(f"完整数据集加载器: {len(dataset)} 样本, {len(loader)} 批次")
    
    return loader