# VR眼动数据MMSE预测 - 训练环节核心实现

## 项目概述

本文档详细介绍了VR眼动数据MMSE预测系统的训练环节核心实现，包括训练循环、数据加载、优化器配置、回调机制等关键组件。

## 1. 训练器架构

### 1.1 QTrainer类结构

```python
class QTrainer:
    """
    MMSE子任务训练器
    
    负责单个Q任务（Q1-Q5）的模型训练、验证和保存。
    """
    
    def __init__(self, q_tag: str, rqa_sig: str, config: Dict[str, Any], device: str = "cpu"):
        self.q_tag = q_tag          # Q1-Q5任务标签
        self.rqa_sig = rqa_sig      # RQA配置签名
        self.config = config        # 训练配置
        self.device = torch.device(device)
        
        # 创建模型
        self.model = create_model_from_config(config).to(self.device)
        
        # 优化器配置
        training_config = config.get("training", {})
        lr = training_config.get("lr", 1e-3)
        weight_decay = config.get("regularization", {}).get("weight_decay", 1e-4)
        
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=lr, weight_decay=weight_decay
        )
        
        # 损失函数
        self.criterion = nn.MSELoss()
        
        # 学习率调度器
        lr_config = config.get("lr_scheduler", {})
        if lr_config.get("enable", False):
            self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode="min",
                factor=lr_config.get("factor", 0.5),
                patience=lr_config.get("patience", 8),
                min_lr=lr_config.get("min_lr", 1e-6)
            )
        
        # 训练状态追踪
        self.training_history = {
            "epochs": [], "train_loss": [], "val_loss": [],
            "train_metrics": [], "val_metrics": []
        }
        self.best_val_loss = float('inf')
        self.current_epoch = 0
```

## 2. 核心训练循环

### 2.1 单个Epoch训练

```python
def train_epoch(self, train_loader, epoch: int) -> Dict[str, float]:
    """
    训练一个epoch
    
    Args:
        train_loader: 训练数据加载器
        epoch: 当前epoch数
        
    Returns:
        训练指标字典
    """
    self.model.train()  # 设置为训练模式
    
    running_loss = 0.0
    self.metrics_tracker.reset()
    batch_count = 0
    start_time = time.time()
    
    for batch_idx, (batch_x, batch_y) in enumerate(train_loader):
        # 数据移动到设备
        batch_x = batch_x.to(self.device)
        batch_y = batch_y.to(self.device)
        
        # 前向传播
        self.optimizer.zero_grad()
        predictions = self.model(batch_x)
        loss = self.criterion(predictions, batch_y)
        
        # 反向传播
        loss.backward()
        
        # 梯度裁剪（防止梯度爆炸）
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
```

### 2.2 验证阶段

```python
def validate_epoch(self, val_loader, epoch: int) -> Dict[str, float]:
    """
    验证一个epoch
    
    Args:
        val_loader: 验证数据加载器
        epoch: 当前epoch数
        
    Returns:
        验证指标字典
    """
    self.model.eval()  # 设置为评估模式
    
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
```

### 2.3 完整训练流程

```python
def fit(self, npz_path: Path, epochs: int = None, batch_size: int = None, 
        val_split: float = None) -> Dict[str, Any]:
    """
    完整的模型训练流程
    
    Args:
        npz_path: 数据集文件路径
        epochs: 训练轮数
        batch_size: 批大小
        val_split: 验证集比例
        
    Returns:
        训练结果字典
    """
    # 配置参数
    training_config = self.config.get("training", {})
    epochs = epochs or training_config.get("epochs", 100)
    batch_size = batch_size or training_config.get("batch_size", 16)
    val_split = val_split or training_config.get("val_split", 0.2)
    seed = self.config.get("seed", 42)
    
    # 创建数据加载器
    train_loader, val_loader = make_loaders(npz_path, batch_size, val_split, seed)
    
    # 设置回调管理器
    callback_manager = self.setup_callbacks()
    
    # 主训练循环
    start_time = time.time()
    callback_manager.on_train_begin({"model": self.model, "optimizer": self.optimizer})
    
    try:
        for epoch in range(1, epochs + 1):
            self.current_epoch = epoch
            
            # Epoch开始
            callback_manager.on_epoch_begin(epoch)
            
            # 训练阶段
            train_result = self.train_epoch(train_loader, epoch)
            
            # 验证阶段
            val_result = self.validate_epoch(val_loader, epoch)
            
            # 更新训练历史
            self.training_history["epochs"].append(epoch)
            self.training_history["train_loss"].append(train_result["loss"])
            self.training_history["val_loss"].append(val_result["loss"])
            self.training_history["train_metrics"].append(train_result["metrics"])
            self.training_history["val_metrics"].append(val_result["metrics"])
            
            # 最佳模型检查和保存
            if val_result["loss"] < self.best_val_loss:
                self.best_val_loss = val_result["loss"]
                self.save_best_model()
            
            # 学习率调度
            if self.scheduler:
                self.scheduler.step(val_result["loss"])
            
            # 回调处理（早停、检查点等）
            epoch_logs = {
                "epoch": epoch,
                "train_loss": train_result["loss"],
                "val_loss": val_result["loss"],
                "train_metrics": train_result["metrics"],
                "val_metrics": val_result["metrics"]
            }
            
            callback_manager.on_epoch_end(epoch, epoch_logs)
            
            # 检查是否需要早停
            if callback_manager.should_stop():
                logger.info(f"早停触发，在第 {epoch} 轮停止训练")
                break
    
    except KeyboardInterrupt:
        logger.info("训练被用户中断")
    except Exception as e:
        logger.error(f"训练过程中出现错误: {str(e)}")
        raise
    finally:
        callback_manager.on_train_end()
    
    total_time = time.time() - start_time
    
    # 最终评估
    final_metrics = self._final_evaluation(val_loader)
    
    return {
        "success": True,
        "total_time": total_time,
        "best_val_loss": self.best_val_loss,
        "final_epoch": self.current_epoch,
        "final_metrics": final_metrics,
        "history": self.training_history
    }
```

## 3. 数据加载管道

### 3.1 自定义数据集

```python
class EyeDataset(Dataset):
    """眼动特征数据集"""
    
    def __init__(self, npz_path: Path, normalize_targets: bool = True):
        """
        加载模块10-A生成的npz文件
        
        Args:
            npz_path: 数据文件路径
            normalize_targets: 是否归一化目标值
        """
        if not npz_path.exists():
            raise FileNotFoundError(f"数据集文件不存在: {npz_path}")
            
        # 加载数据
        data = np.load(npz_path, allow_pickle=True)
        self.X = torch.from_numpy(data["X"]).float()  # (N, 10) 特征矩阵
        self.y = torch.from_numpy(data["y"]).float()  # (N,) MMSE标签
        
        # 数据验证
        if self.X.shape[0] != self.y.shape[0]:
            raise ValueError("特征和标签样本数不匹配")
        if self.X.shape[1] != 10:
            raise ValueError(f"特征维度应为10，实际为: {self.X.shape[1]}")
            
        # 目标值归一化
        if normalize_targets and (self.y.min() < 0 or self.y.max() > 1):
            self.y = (self.y - self.y.min()) / (self.y.max() - self.y.min() + 1e-8)
                
        self.n_samples = self.X.shape[0]

    def __len__(self) -> int:
        return self.n_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]
```

### 3.2 数据加载器创建

```python
def make_loaders(
    npz_path: Union[str, Path], 
    batch_size: int, 
    val_split: Optional[float] = None, 
    seed: int = 42
) -> Tuple[DataLoader, DataLoader]:
    """
    创建训练和验证数据加载器
    
    Args:
        npz_path: 数据集文件路径
        batch_size: 批大小
        val_split: 验证集比例
        seed: 随机种子
        
    Returns:
        (train_loader, val_loader): 数据加载器元组
    """
    npz_path = Path(npz_path)
    dataset = EyeDataset(npz_path)
    
    if val_split is None:
        val_split = 0.2
    
    # 计算分割大小
    n_total = len(dataset)
    n_val = int(n_total * val_split)
    n_train = n_total - n_val
    
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
        drop_last=True,  # 保持批次大小一致
        pin_memory=torch.cuda.is_available()  # GPU内存固定
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        drop_last=False,
        pin_memory=torch.cuda.is_available()
    )
    
    return train_loader, val_loader
```

## 4. 回调机制

### 4.1 早停回调

```python
class EarlyStopping:
    """早停回调类"""
    
    def __init__(self, patience: int = 10, min_delta: float = 0.001, restore_best: bool = True):
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best = restore_best
        self.best_loss = float('inf')
        self.wait = 0
        self.best_weights = None
        
    def on_epoch_end(self, epoch: int, logs: Dict[str, Any]):
        """每个epoch结束时调用"""
        current_loss = logs.get('val_loss', float('inf'))
        
        if current_loss < self.best_loss - self.min_delta:
            self.best_loss = current_loss
            self.wait = 0
            if self.restore_best:
                self.best_weights = copy.deepcopy(logs['model'].state_dict())
        else:
            self.wait += 1
            
    def should_stop(self) -> bool:
        """检查是否应该停止训练"""
        return self.wait >= self.patience
        
    def restore_model(self, model):
        """恢复最佳模型权重"""
        if self.restore_best and self.best_weights:
            model.load_state_dict(self.best_weights)
```

### 4.2 模型检查点回调

```python
class ModelCheckpoint:
    """模型检查点保存回调"""
    
    def __init__(self, filepath: str, monitor: str = 'val_loss', save_best_only: bool = True):
        self.filepath = filepath
        self.monitor = monitor
        self.save_best_only = save_best_only
        self.best_score = float('inf')
        
    def on_epoch_end(self, epoch: int, logs: Dict[str, Any]):
        """保存模型检查点"""
        current_score = logs.get(self.monitor, float('inf'))
        
        if not self.save_best_only or current_score < self.best_score:
            self.best_score = current_score
            
            # 保存模型状态
            torch.save({
                'epoch': epoch,
                'model_state_dict': logs['model'].state_dict(),
                'optimizer_state_dict': logs['optimizer'].state_dict(),
                'loss': current_score,
                'config': logs.get('config', {})
            }, self.filepath.format(epoch=epoch))
```

## 5. 评价指标计算

### 5.1 回归指标

```python
def calculate_regression_metrics(y_true: torch.Tensor, y_pred: torch.Tensor) -> Dict[str, float]:
    """
    计算回归任务的评价指标
    
    Args:
        y_true: 真实标签
        y_pred: 预测值
        
    Returns:
        指标字典
    """
    y_true_np = y_true.detach().cpu().numpy()
    y_pred_np = y_pred.detach().cpu().numpy()
    
    # 基础回归指标
    mse = mean_squared_error(y_true_np, y_pred_np)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true_np, y_pred_np)
    r2 = r2_score(y_true_np, y_pred_np)
    
    # 附加指标
    mape = np.mean(np.abs((y_true_np - y_pred_np) / (y_true_np + 1e-8))) * 100
    explained_var = explained_variance_score(y_true_np, y_pred_np)
    
    return {
        "mse": mse,
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "mape": mape,
        "explained_variance": explained_var
    }

class MetricsCalculator:
    """指标计算器"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """重置累积统计"""
        self.y_true_list = []
        self.y_pred_list = []
        
    def update(self, y_true: torch.Tensor, y_pred: torch.Tensor):
        """更新累积统计"""
        self.y_true_list.append(y_true.detach().cpu())
        self.y_pred_list.append(y_pred.detach().cpu())
        
    def compute(self) -> Dict[str, float]:
        """计算最终指标"""
        if not self.y_true_list:
            return {}
            
        y_true = torch.cat(self.y_true_list)
        y_pred = torch.cat(self.y_pred_list)
        
        return calculate_regression_metrics(y_true, y_pred)
```

## 6. 学习率调度

### 6.1 ReduceLROnPlateau调度器

```python
# 配置学习率调度器
lr_config = config.get("lr_scheduler", {})
if lr_config.get("enable", False):
    self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        self.optimizer,
        mode="min",                              # 监控指标的模式（最小化）
        factor=lr_config.get("factor", 0.5),    # 学习率衰减因子
        patience=lr_config.get("patience", 8),   # 等待轮数
        min_lr=lr_config.get("min_lr", 1e-6),   # 最小学习率
        threshold=1e-4,                          # 改善阈值
        cooldown=2                               # 冷却期
    )

# 在训练循环中使用
if self.scheduler:
    self.scheduler.step(val_result["loss"])  # 根据验证损失调整学习率
```

## 7. 关键训练技术

### 7.1 梯度裁剪
```python
# 防止梯度爆炸
grad_clip = self.config.get("regularization", {}).get("grad_clip_norm", 1.0)
if grad_clip:
    torch.nn.utils.clip_grad_norm_(self.model.parameters(), grad_clip)
```

### 7.2 权重衰减（L2正则化）
```python
# 在优化器中添加权重衰减
weight_decay = config.get("regularization", {}).get("weight_decay", 1e-4)
self.optimizer = torch.optim.Adam(
    self.model.parameters(), 
    lr=lr, 
    weight_decay=weight_decay
)
```

### 7.3 Dropout控制
```python
# 在模型中动态控制Dropout
arch_config = config.get("arch", {})
dropout_rate = arch_config.get("dropout", 0.25)

# 如果dropout_rate为0，则关闭Dropout
if dropout_rate == 0:
    # 模型会自动处理，不添加Dropout层
    pass
```

### 7.4 批归一化
```python
# 可选的批归一化
use_batch_norm = arch_config.get("use_batch_norm", False)
if use_batch_norm:
    # 在每个线性层后添加BatchNorm1d
    layers.append(nn.BatchNorm1d(hidden_dim))
```

## 8. 日志和监控

### 8.1 TensorBoard集成
```python
# 创建TensorBoard写入器
from torch.utils.tensorboard import SummaryWriter

self.tb_writer = SummaryWriter(log_dir=f"runs/{rqa_sig}/{q_tag}")

# 记录训练指标
self.tb_writer.add_scalars('Loss', {
    'train': train_loss,
    'val': val_loss
}, epoch)

# 记录学习率
self.tb_writer.add_scalar('Learning_Rate', 
                         self.optimizer.param_groups[0]['lr'], epoch)

# 记录模型图
sample_input = torch.randn(1, 10).to(self.device)
self.tb_writer.add_graph(self.model, sample_input)
```

### 8.2 文件日志
```python
import logging

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/training_{self.q_tag}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

## 9. 技术特色与优势

### 9.1 模块化设计
- **回调机制**: 可插拔的训练回调（早停、检查点、日志等）
- **配置驱动**: YAML配置文件统一管理所有超参数
- **指标追踪**: 完整的训练历史和实时监控

### 9.2 稳定性保证
- **梯度裁剪**: 防止梯度爆炸，提高训练稳定性
- **学习率调度**: 自适应学习率调整，优化收敛效果
- **早停机制**: 防止过拟合，提高泛化能力

### 9.3 GPU优化
- **设备自适应**: 自动检测并使用GPU加速
- **内存固定**: Pin memory优化数据传输效率
- **批处理优化**: 充分利用GPU并行计算能力

### 9.4 实验跟踪
- **版本管理**: 模型版本和配置的完整追踪
- **指标对比**: 多维度评价指标的全面比较
- **可视化监控**: TensorBoard实时训练状态监控

## 10. 使用示例

### 10.1 基础训练
```python
# 创建训练器
trainer = QTrainer(
    q_tag="Q1",
    rqa_sig="m2_tau1_eps0.055_lmin2", 
    config=yaml.safe_load(open("config.yaml")),
    device="cuda:0"
)

# 开始训练
result = trainer.fit(
    npz_path=Path("data/module10_datasets/m2_tau1_eps0.055_lmin2/Q1.npz"),
    epochs=100,
    batch_size=16,
    val_split=0.3
)

print(f"训练完成! 最佳验证损失: {result['best_val_loss']:.4f}")
```

### 10.2 自定义配置训练
```python
# 自定义配置
custom_config = {
    "arch": {
        "h1": 64, "h2": 32, 
        "dropout": 0.3, 
        "use_batch_norm": True
    },
    "training": {
        "lr": 0.0005, 
        "batch_size": 32
    },
    "lr_scheduler": {
        "enable": True,
        "factor": 0.7,
        "patience": 15
    }
}

trainer = QTrainer("Q2", "custom_config", custom_config)
result = trainer.fit(npz_path, epochs=200)
```

这个训练系统为VR眼动数据的MMSE预测提供了完整、高效、可扩展的解决方案，具备工业级的稳定性和性能。
