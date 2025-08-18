"""
模块10 Eye-Index 综合评估
实现综合眼动系数 S_eye 计算、可视化和分析
"""

from .api import register_eye_index_routes
from .utils import compute_s_eye, eye_index_report

__version__ = "1.0.0"
__author__ = "VR Eye-Tracking Analysis System"

__all__ = [
    'register_eye_index_routes',
    'compute_s_eye', 
    'eye_index_report'
]