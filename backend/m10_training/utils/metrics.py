"""
模块10-B: 评价指标
====================================

提供机器学习评价指标的计算函数。
"""

import numpy as np
import torch
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, List, Tuple, Any, Union
import logging

logger = logging.getLogger(__name__)


def calculate_regression_metrics(
    y_true: Union[np.ndarray, torch.Tensor, List],
    y_pred: Union[np.ndarray, torch.Tensor, List]
) -> Dict[str, float]:
    """
    计算回归任务的评价指标
    
    Args:
        y_true: 真实值
        y_pred: 预测值
        
    Returns:
        包含各种指标的字典
    """
    # 转换为numpy数组
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()
    if isinstance(y_pred, torch.Tensor):
        y_pred = y_pred.detach().cpu().numpy()
    
    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()
    
    # 基本检查
    if len(y_true) != len(y_pred):
        raise ValueError(f"真实值和预测值长度不匹配: {len(y_true)} vs {len(y_pred)}")
    
    if len(y_true) == 0:
        raise ValueError("输入为空")
    
    # 计算各种指标
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    
    # R²分数
    try:
        r2 = r2_score(y_true, y_pred)
    except:
        r2 = float('nan')
    
    # 平均绝对百分比误差 (MAPE)
    # 避免除零错误
    non_zero_mask = np.abs(y_true) > 1e-8
    if np.any(non_zero_mask):
        mape = np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100
    else:
        mape = float('nan')
    
    # 相关系数
    try:
        correlation = np.corrcoef(y_true, y_pred)[0, 1]
    except:
        correlation = float('nan')
    
    # 最大绝对误差
    max_error = np.max(np.abs(y_true - y_pred))
    
    # 标准化RMSE（如果真实值有变化）
    y_std = np.std(y_true)
    nrmse = rmse / y_std if y_std > 1e-8 else float('nan')
    
    return {
        "mse": float(mse),
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2),
        "mape": float(mape),
        "correlation": float(correlation),
        "max_error": float(max_error),
        "nrmse": float(nrmse)
    }


def calculate_classification_metrics(
    y_true: Union[np.ndarray, torch.Tensor, List],
    y_pred: Union[np.ndarray, torch.Tensor, List],
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    计算二分类指标（将回归问题转换为分类）
    
    Args:
        y_true: 真实值
        y_pred: 预测值
        threshold: 分类阈值
        
    Returns:
        包含分类指标的字典
    """
    # 转换为numpy数组
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()
    if isinstance(y_pred, torch.Tensor):
        y_pred = y_pred.detach().cpu().numpy()
    
    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()
    
    # 转换为二分类
    y_true_bin = (y_true >= threshold).astype(int)
    y_pred_bin = (y_pred >= threshold).astype(int)
    
    # 计算混淆矩阵元素
    tp = np.sum((y_true_bin == 1) & (y_pred_bin == 1))
    tn = np.sum((y_true_bin == 0) & (y_pred_bin == 0))
    fp = np.sum((y_true_bin == 0) & (y_pred_bin == 1))
    fn = np.sum((y_true_bin == 1) & (y_pred_bin == 0))
    
    # 计算指标
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "specificity": float(specificity),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn)
    }


class MetricsCalculator:
    """
    指标计算器类
    
    提供批量计算和跟踪多种指标的功能。
    """
    
    def __init__(self, task_type: str = "regression"):
        """
        初始化指标计算器
        
        Args:
            task_type: 任务类型，"regression" 或 "classification"
        """
        self.task_type = task_type
        self.history = {
            "y_true": [],
            "y_pred": [],
            "metrics": []
        }
    
    def update(self, y_true: Union[np.ndarray, torch.Tensor], y_pred: Union[np.ndarray, torch.Tensor]):
        """
        添加新的预测结果
        
        Args:
            y_true: 真实值
            y_pred: 预测值
        """
        # 转换为numpy并展平
        if isinstance(y_true, torch.Tensor):
            y_true = y_true.detach().cpu().numpy()
        if isinstance(y_pred, torch.Tensor):
            y_pred = y_pred.detach().cpu().numpy()
        
        y_true = np.array(y_true).flatten()
        y_pred = np.array(y_pred).flatten()
        
        self.history["y_true"].extend(y_true.tolist())
        self.history["y_pred"].extend(y_pred.tolist())
    
    def compute(self) -> Dict[str, float]:
        """
        计算累积的指标
        
        Returns:
            指标字典
        """
        if not self.history["y_true"]:
            return {}
        
        y_true = np.array(self.history["y_true"])
        y_pred = np.array(self.history["y_pred"])
        
        if self.task_type == "regression":
            metrics = calculate_regression_metrics(y_true, y_pred)
        else:
            metrics = calculate_classification_metrics(y_true, y_pred)
        
        self.history["metrics"].append(metrics)
        return metrics
    
    def reset(self):
        """重置历史记录"""
        self.history = {
            "y_true": [],
            "y_pred": [],
            "metrics": []
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取完整的计算结果摘要
        
        Returns:
            包含指标历史和统计的字典
        """
        current_metrics = self.compute()
        
        return {
            "current_metrics": current_metrics,
            "sample_count": len(self.history["y_true"]),
            "prediction_stats": {
                "y_true_mean": float(np.mean(self.history["y_true"])),
                "y_true_std": float(np.std(self.history["y_true"])),
                "y_pred_mean": float(np.mean(self.history["y_pred"])),
                "y_pred_std": float(np.std(self.history["y_pred"])),
                "y_true_range": [float(np.min(self.history["y_true"])), float(np.max(self.history["y_true"]))],
                "y_pred_range": [float(np.min(self.history["y_pred"])), float(np.max(self.history["y_pred"]))]
            }
        }


def evaluate_model_on_loader(
    model: torch.nn.Module,
    data_loader: torch.utils.data.DataLoader,
    device: torch.device,
    criterion: torch.nn.Module = None
) -> Tuple[Dict[str, float], float]:
    """
    在数据加载器上评估模型
    
    Args:
        model: PyTorch模型
        data_loader: 数据加载器
        device: 计算设备
        criterion: 损失函数（可选）
        
    Returns:
        (metrics, avg_loss): 指标字典和平均损失
    """
    model.eval()
    calculator = MetricsCalculator("regression")
    total_loss = 0.0
    n_batches = 0
    
    with torch.no_grad():
        for batch_x, batch_y in data_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            
            # 前向传播
            predictions = model(batch_x)
            
            # 计算损失
            if criterion is not None:
                loss = criterion(predictions, batch_y)
                total_loss += loss.item()
            
            # 更新指标
            calculator.update(batch_y, predictions)
            n_batches += 1
    
    # 计算最终指标
    metrics = calculator.compute()
    avg_loss = total_loss / n_batches if n_batches > 0 and criterion is not None else 0.0
    
    return metrics, avg_loss


def compare_models(
    models_metrics: Dict[str, Dict[str, float]],
    primary_metric: str = "rmse",
    ascending: bool = True
) -> List[Tuple[str, Dict[str, float]]]:
    """
    比较多个模型的性能
    
    Args:
        models_metrics: 模型名称到指标字典的映射
        primary_metric: 主要比较指标
        ascending: 是否升序排序（True表示越小越好）
        
    Returns:
        按性能排序的模型列表
    """
    if not models_metrics:
        return []
    
    # 检查主要指标是否存在
    available_metrics = set()
    for metrics in models_metrics.values():
        available_metrics.update(metrics.keys())
    
    if primary_metric not in available_metrics:
        logger.warning(f"主要指标 '{primary_metric}' 不存在，使用第一个可用指标")
        primary_metric = list(available_metrics)[0] if available_metrics else None
    
    if primary_metric is None:
        return list(models_metrics.items())
    
    # 按主要指标排序
    sorted_models = sorted(
        models_metrics.items(),
        key=lambda x: x[1].get(primary_metric, float('inf') if ascending else float('-inf')),
        reverse=not ascending
    )
    
    return sorted_models


def format_metrics_table(metrics: Dict[str, float], precision: int = 4) -> str:
    """
    格式化指标为表格字符串
    
    Args:
        metrics: 指标字典
        precision: 小数位数
        
    Returns:
        格式化的表格字符串
    """
    if not metrics:
        return "无指标数据"
    
    # 计算最长的指标名称
    max_name_length = max(len(name) for name in metrics.keys())
    
    lines = []
    lines.append("=" * (max_name_length + 20))
    lines.append(f"{'指标':<{max_name_length}} | {'数值':>10}")
    lines.append("-" * (max_name_length + 20))
    
    for name, value in metrics.items():
        if isinstance(value, float) and not np.isnan(value):
            formatted_value = f"{value:.{precision}f}"
        else:
            formatted_value = str(value)
        
        lines.append(f"{name:<{max_name_length}} | {formatted_value:>10}")
    
    lines.append("=" * (max_name_length + 20))
    
    return "\n".join(lines)