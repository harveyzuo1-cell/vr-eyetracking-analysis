"""
Module06: 特征提取与选择模块

功能：
1. Module04特征敏感度分析
2. Module05 RQA特征敏感度分析
3. 特征选择（Top-4 + Top-6）
4. 特征向量提取
"""

from .api import m06_bp
from .service import FeatureExtractionService
from .sensitivity_analyzer import SensitivityAnalyzer

__all__ = ['m06_bp', 'FeatureExtractionService', 'SensitivityAnalyzer']
