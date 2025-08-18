"""
模块10-D: 模型性能评估与差异可视化
提供批量模型评估、残差分析、任务级性能对比等功能
"""

from .evaluator import ModelEvaluator
from .api import evaluation_bp

__all__ = ['ModelEvaluator', 'evaluation_bp']
