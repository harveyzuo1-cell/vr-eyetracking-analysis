"""
模块10-A: Eye-Index数据准备模块
负责从模块7的输出数据构建用于训练的特征数据集
"""

__version__ = "1.0.0"
__author__ = "Eye-tracking Analysis System"

from .builder import FeatureBuilder
from .schema import DataValidator
from .settings import *

__all__ = ['FeatureBuilder', 'DataValidator']