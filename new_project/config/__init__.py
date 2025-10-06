"""
配置模块

提供全局配置访问
"""
from .settings import Config, DevelopmentConfig, ProductionConfig

__all__ = ['Config', 'DevelopmentConfig', 'ProductionConfig']
