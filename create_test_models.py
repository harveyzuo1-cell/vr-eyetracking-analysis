#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建测试模型文件
===============

为了测试模块10-C的功能，创建一些模拟的模型文件。
"""

import os
import torch
import torch.nn as nn
import json
from pathlib import Path
from datetime import datetime


class SimpleEyeMLP(nn.Module):
    """简单的眼动MLP模型（用于测试）"""
    
    def __init__(self, input_dim=10, h1=32, h2=16, dropout=0.25, output_dim=1):
        super().__init__()
        
        self.layers = nn.Sequential(
            nn.Linear(input_dim, h1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(h1, h2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(h2, output_dim)
        )
    
    def forward(self, x):
        return self.layers(x)


def create_test_models():
    """创建测试模型文件"""
    
    # 配置
    sig = "m2_tau1_eps0.055_lmin2"
    models_dir = Path("models") / sig
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔧 创建测试模型目录: {models_dir}")
    
    # 为每个Q任务创建模型
    for q_tag in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        print(f"📦 创建 {q_tag} 模型...")
        
        # 创建模型
        model = SimpleEyeMLP()
        
        # 模拟训练后的权重
        with torch.no_grad():
            for param in model.parameters():
                param.data = torch.randn_like(param.data) * 0.1
        
        # 保存best版本
        best_path = models_dir / f"{q_tag}_best.pt"
        torch.save({
            "model_state": model.state_dict(),
            "epoch": 100,
            "loss": 0.15 + torch.rand(1).item() * 0.1,
            "config": {
                "input_dim": 10,
                "h1": 32,
                "h2": 16,
                "dropout": 0.25,
                "output_dim": 1
            }
        }, best_path)
        
        # 保存带时间戳的版本
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        timestamped_path = models_dir / f"{q_tag}_{timestamp}.pt"
        torch.save({
            "model_state": model.state_dict(),
            "epoch": 50,
            "loss": 0.18 + torch.rand(1).item() * 0.1,
            "config": {
                "input_dim": 10,
                "h1": 32,
                "h2": 16,
                "dropout": 0.25,
                "output_dim": 1
            }
        }, timestamped_path)
        
        # 创建TorchScript版本（用于测试直接加载）
        model.eval()
        scripted = torch.jit.script(model)
        ts_path = models_dir / f"{q_tag}_best.ts"
        scripted.save(ts_path)
        
        # 创建模拟的指标文件
        metrics = {
            "test_rmse": 0.12 + torch.rand(1).item() * 0.05,
            "test_r2": 0.80 + torch.rand(1).item() * 0.15,
            "test_mae": 0.08 + torch.rand(1).item() * 0.04,
            "best_epoch": 100,
            "train_time_seconds": 180.5,
            "val_loss_best": 0.13 + torch.rand(1).item() * 0.03,
            "learning_rate": 0.001,
            "timestamp": datetime.now().isoformat()
        }
        
        metrics_path = models_dir / f"{q_tag}_best_metrics.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ {best_path.name}")
        print(f"   ✅ {timestamped_path.name}")
        print(f"   ✅ {ts_path.name}")
        print(f"   ✅ {metrics_path.name}")
    
    print(f"\n🎉 测试模型创建完成!")
    print(f"📁 模型目录: {models_dir}")
    print(f"📊 共创建了 {len(list(models_dir.glob('*.pt')))} 个PyTorch模型文件")
    print(f"🚀 共创建了 {len(list(models_dir.glob('*.ts')))} 个TorchScript文件")
    print(f"📈 共创建了 {len(list(models_dir.glob('*_metrics.json')))} 个指标文件")


def create_logs():
    """创建模拟的TensorBoard日志"""
    sig = "m2_tau1_eps0.055_lmin2"
    logs_dir = Path("runs") / sig
    
    for q_tag in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        task_log_dir = logs_dir / q_tag
        task_log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建空的events文件（模拟）
        event_file = task_log_dir / "events.out.tfevents.1234567890.hostname"
        event_file.touch()
        
        print(f"📊 创建日志目录: {task_log_dir}")


if __name__ == "__main__":
    print("🚀 开始创建测试模型和日志...")
    
    create_test_models()
    create_logs()
    
    print("\n✅ 所有测试文件创建完成!")
    print("💡 现在可以测试模块10-C的功能了")