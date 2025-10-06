"""
Module02 API 共享工具

包含错误处理装饰器和通用功能
"""

from flask import jsonify
from functools import wraps
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# 错误处理装饰器
def handle_errors(f):
    """统一的错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except FileNotFoundError as e:
            logger.error(f"File not found in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': '文件未找到'
            }), 404
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': '服务器内部错误'
            }), 500
    return decorated_function
