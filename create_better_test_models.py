#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建改进的测试模型文件
===================

创建能够正常输出0-1范围内预测结果的测试模型。
"""

import os
import torch
import torch.nn as nn
import json
from pathlib import Path
from datetime import datetime


class BetterEyeMLP(nn.Module):
    """改进的眼动MLP模型（用于测试）"""
    
    def __init__(self, input_dim=10, h1=32, h2=16, dropout=0.25, output_dim=1):
        super().__init__()
        
        self.layers = nn.Sequential(
            nn.Linear(input_dim, h1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(h1, h2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(h2, output_dim),
            nn.Sigmoid()  # 添加Sigmoid确保输出在0-1范围
        )
    
    def forward(self, x):
        return self.layers(x)


def create_better_test_models():
    """创建改进的测试模型文件"""
    
    # 配置
    sig = "m2_tau1_eps0.055_lmin2"
    models_dir = Path("models") / sig
    
    print(f"🔧 更新测试模型目录: {models_dir}")
    
    # 为每个Q任务创建模型
    for q_tag in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        print(f"📦 更新 {q_tag} 模型...")
        
        # 创建模型
        model = BetterEyeMLP()
        
        # 设置更合理的权重，确保有意义的输出
        with torch.no_grad():
            for name, param in model.named_parameters():
                if 'weight' in name:
                    # 对权重使用Xavier初始化
                    nn.init.xavier_uniform_(param)
                    # 为不同Q任务添加一些变化
                    q_num = int(q_tag[1])  # Q1->1, Q2->2, etc.
                    param.data *= (0.5 + q_num * 0.1)  # Q1最小，Q5最大
                elif 'bias' in name:
                    # 偏置设为小的正值
                    nn.init.constant_(param, 0.1 * q_num / 5)
        
        # 验证模型输出
        model.eval()
        with torch.no_grad():
            test_input = torch.randn(1, 10)
            test_output = model(test_input)
            print(f"   {q_tag} 测试输出: {test_output.item():.4f}")
        
        # 保存best版本（覆盖旧的）
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
        
        # 更新TorchScript版本
        scripted = torch.jit.script(model)
        ts_path = models_dir / f"{q_tag}_best.ts"
        scripted.save(ts_path)
        
        # 更新模拟的指标文件
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
        
        print(f"   ✅ {best_path.name} (更新)")
        print(f"   ✅ {timestamped_path.name} (新建)")
        print(f"   ✅ {ts_path.name} (更新)")
        print(f"   ✅ {metrics_path.name} (更新)")
    
    print(f"\n🎉 测试模型更新完成!")
    print(f"📁 模型目录: {models_dir}")
    print(f"💡 模型现在应该能输出有意义的0-1范围内的值")


if __name__ == "__main__":
    print("🚀 开始更新测试模型...")
    create_better_test_models()
    print("\n✅ 测试模型更新完成!")
    print("💡 现在可以重新测试模块10-C的功能了")