"""
Module04 工具函数和装饰器
"""

import functools
from flask import jsonify
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_api_errors(f):
    """
    统一错误处理装饰器

    自动捕获API函数中的异常并返回标准格式的错误响应

    Returns:
        JSON响应: {'success': False, 'error': 错误信息}, HTTP状态码500

    Example:
        @m04_bp.route('/test', methods=['GET'])
        @handle_api_errors
        def test_endpoint():
            # API逻辑
            return jsonify({'success': True, 'data': ...})
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"{f.__name__} 失败: {error_msg}", exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
    return wrapper


def validate_params(*required_params):
    """
    参数验证装饰器

    验证请求中是否包含所有必需参数

    Args:
        *required_params: 必需参数名称列表

    Returns:
        如果参数缺失，返回400错误响应
        如果参数完整，继续执行函数

    Example:
        @m04_bp.route('/analyze', methods=['POST'])
        @validate_params('subject_id', 'group', 'task_id')
        @handle_api_errors
        def analyze():
            data = request.get_json()
            # 参数已验证，直接使用
            return jsonify({'success': True})
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request

            # 根据HTTP方法获取参数
            if request.method == 'GET':
                params = request.args
            else:
                params = request.get_json() or {}

            # 检查必需参数
            missing = [p for p in required_params if not params.get(p)]

            if missing:
                error_msg = f"缺少必要参数: {', '.join(missing)}"
                logger.warning(f"{f.__name__}: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator
