"""
中间件

请求/响应处理中间件
"""
import time
from flask import Flask, request, g
import logging

logger = logging.getLogger(__name__)


def register_middleware(app: Flask):
    """
    注册中间件

    Args:
        app: Flask应用实例
    """

    @app.before_request
    def before_request():
        """请求前处理"""
        g.start_time = time.time()
        logger.debug(f"收到请求: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        """请求后处理"""
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{elapsed:.3f}s"

            # 记录慢请求
            if elapsed > 1.0:
                logger.warning(
                    f"慢请求: {request.method} {request.path} "
                    f"耗时 {elapsed:.3f}s"
                )
            else:
                logger.debug(
                    f"请求完成: {request.method} {request.path} "
                    f"耗时 {elapsed:.3f}s, 状态 {response.status_code}"
                )

        # 添加CORS头
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

        return response

    @app.teardown_request
    def teardown_request(exception=None):
        """请求清理"""
        if exception:
            logger.error(f"请求处理异常: {str(exception)}", exc_info=True)

    logger.info("中间件注册完成")
