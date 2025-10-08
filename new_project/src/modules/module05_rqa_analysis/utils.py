"""
Module05 工具函数和装饰器
"""

import functools
import time
from flask import jsonify, request
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_api_errors(f):
    """
    统一错误处理装饰器

    自动捕获API函数中的异常并返回标准格式的错误响应

    Returns:
        JSON响应: {'success': False, 'error': 错误信息}, HTTP状态码500

    Example:
        @m05_bp.route('/test', methods=['GET'])
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
        @m05_bp.route('/analyze', methods=['POST'])
        @validate_params('subject_id', 'params')
        @handle_api_errors
        def analyze():
            data = request.get_json()
            # 参数已验证，直接使用
            return jsonify({'success': True})
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
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


def monitor_performance(f):
    """
    性能监控装饰器

    记录API端点的执行时间

    Example:
        @m05_bp.route('/analyze/batch', methods=['POST'])
        @monitor_performance
        @handle_api_errors
        def analyze_batch():
            # API逻辑
            return jsonify({'success': True})
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        duration = time.time() - start_time

        logger.info(f"{f.__name__} 执行时间: {duration:.2f}s")

        # 如果执行时间超过5秒，记录警告
        if duration > 5.0:
            logger.warning(f"{f.__name__} 执行时间过长: {duration:.2f}s")

        return result
    return wrapper


def generate_param_signature(params: dict) -> str:
    """
    生成参数签名

    Args:
        params: RQA参数字典 {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}

    Returns:
        参数签名字符串，如 'm2_tau1_eps0.05_lmin2'
    """
    m = params.get('m', 2)
    tau = params.get('tau', 1)
    eps = params.get('eps', 0.05)
    lmin = params.get('lmin', 2)

    return f"m{m}_tau{tau}_eps{eps}_lmin{lmin}"


def validate_rqa_params(params: dict) -> tuple[bool, str]:
    """
    验证RQA参数的有效性

    Args:
        params: RQA参数字典

    Returns:
        (是否有效, 错误信息)
    """
    # 检查必需参数
    required = ['m', 'tau', 'eps', 'lmin']
    for key in required:
        if key not in params:
            return False, f"缺少参数: {key}"

    # 验证参数范围
    m = params['m']
    tau = params['tau']
    eps = params['eps']
    lmin = params['lmin']

    if not isinstance(m, int) or m < 1 or m > 20:
        return False, "嵌入维度 m 必须是1-20的整数"

    if not isinstance(tau, int) or tau < 1 or tau > 20:
        return False, "时间延迟 tau 必须是1-20的整数"

    if not isinstance(eps, (int, float)) or eps <= 0 or eps > 1:
        return False, "递归阈值 eps 必须是0-1之间的数值"

    if not isinstance(lmin, int) or lmin < 2 or lmin > 10:
        return False, "最小线长 lmin 必须是2-10的整数"

    return True, ""
