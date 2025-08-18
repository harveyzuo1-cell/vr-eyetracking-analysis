"""
模块10-C: 模型服务与管理API
================================

使命：把10-B训练得到的权重变成一个可在线推理、可多版本管理、
可被前端实时查询的Flask服务层。

功能特性：
- TorchScript优先推理
- 多版本模型管理
- 线程安全模型缓存
- 实时预测API
- 训练指标查询
"""

from flask import Blueprint
from .config import MODELS_ROOT, DEFAULT_SIG
from . import predict, versions, metrics, data_api

# 创建主蓝图
service_bp = Blueprint("m10_service", __name__)

# 注册子蓝图
service_bp.register_blueprint(predict.bp)
service_bp.register_blueprint(versions.bp) 
service_bp.register_blueprint(metrics.bp)
service_bp.register_blueprint(data_api.bp)  # 新增：数据表格API

# 启动时自动激活best模型
def initialize_models():
    """启动时自动激活所有Q任务的best模型"""
    from .loader import ModelManager
    
    print("[m10_service] 🚀 初始化模型服务...")
    activated_count = 0
    
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        try:
            ModelManager.activate(q, DEFAULT_SIG, "best")
            print(f"[m10_service] ✅ {q} best模型已激活")
            activated_count += 1
        except Exception as e:
            print(f"[m10_service] ⚠️ 无法激活 {q}: {e}")
    
    print(f"[m10_service] 🎯 模型服务初始化完成: {activated_count}/5 个模型已激活")
    return activated_count

# 在模块被导入时自动初始化（可选）
# initialize_models()

__all__ = ["service_bp", "initialize_models"]