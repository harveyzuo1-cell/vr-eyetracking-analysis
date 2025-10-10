"""
Module06工具函数
"""

from functools import wraps
from flask import request, jsonify
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_api_errors(func):
    """
    API错误处理装饰器

    统一处理所有API的异常，返回标准错误格式
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'数据验证失败: {str(e)}'
            }), 400
        except FileNotFoundError as e:
            logger.warning(f"File not found in {func.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'文件未找到: {str(e)}'
            }), 404
        except PermissionError as e:
            logger.warning(f"Permission error in {func.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'权限不足: {str(e)}'
            }), 403
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }), 500

    return wrapper


def validate_params(*required_params):
    """
    参数验证装饰器

    Args:
        *required_params: 必需的参数名称列表

    Usage:
        @validate_params('subject_id', 'group')
        def my_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}

            missing_params = [param for param in required_params if param not in data or not data[param]]

            if missing_params:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需参数: {", ".join(missing_params)}'
                }), 400

            return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_strategy(strategy: str) -> str:
    """
    验证特征提取策略

    Args:
        strategy: 策略标识 (A/B)

    Returns:
        标准化的策略标识

    Raises:
        ValueError: 如果策略无效
    """
    strategy = strategy.upper()
    if strategy not in ['A', 'B']:
        raise ValueError(f"无效的策略: {strategy}。支持的策略: A (Top-10), B (Top-69)")
    return strategy


def validate_groups(groups: list) -> list:
    """
    验证分组列表

    Args:
        groups: 分组列表

    Returns:
        验证后的分组列表

    Raises:
        ValueError: 如果分组无效
    """
    valid_groups = ['control', 'mci', 'ad']

    if not groups:
        return valid_groups

    invalid_groups = set(groups) - set(valid_groups)
    if invalid_groups:
        raise ValueError(f"无效的分组: {invalid_groups}。支持的分组: {valid_groups}")

    return groups


def validate_data_version(data_version: str) -> str:
    """
    验证数据版本

    Args:
        data_version: 数据版本标识

    Returns:
        验证后的数据版本

    Raises:
        ValueError: 如果版本无效
    """
    valid_versions = ['v1', 'v2']

    if data_version not in valid_versions:
        raise ValueError(f"无效的数据版本: {data_version}。支持的版本: {valid_versions}")

    return data_version
