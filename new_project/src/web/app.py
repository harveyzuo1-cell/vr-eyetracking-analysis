"""
Flask应用工厂

创建和配置Flask应用
"""
from flask import Flask
from flask_cors import CORS
import logging

from config.settings import get_config
from src.utils.logger import setup_logger
from src.utils.gpu_utils import GPUUtils


def create_app(env: str = None) -> Flask:
    """
    创建Flask应用

    Args:
        env: 环境名称 (development/production/testing)

    Returns:
        Flask: Flask应用实例
    """
    # 创建Flask应用
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    # 加载配置
    config = get_config(env)
    app.config.from_object(config)

    # 配置日志
    setup_logger(
        name='werkzeug',
        level=config.LOG_LEVEL
    )
    logger = setup_logger(
        name=__name__,
        level=config.LOG_LEVEL
    )

    logger.info(f"=" * 60)
    logger.info(f"启动 {config.PROJECT_NAME} v{config.VERSION}")
    logger.info(f"环境: {env or 'development'}")
    logger.info(f"=" * 60)

    # 初始化目录结构
    logger.info("初始化目录结构...")
    config.init_directories()

    # 检查GPU状态
    logger.info("检查GPU状态...")
    GPUUtils.log_gpu_status()

    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 注册中间件
    from .middleware import register_middleware
    register_middleware(app)

    # 注册路由
    from .routes import register_routes
    register_routes(app)

    # 注册错误处理
    register_error_handlers(app)

    logger.info(f"Flask应用创建成功")
    logger.info(f"访问地址: http://{config.HOST}:{config.PORT}")

    return app


def register_error_handlers(app: Flask):
    """
    注册错误处理器

    Args:
        app: Flask应用实例
    """
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': '请求的资源不存在',
            'status': 404
        }, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"服务器内部错误: {str(error)}")
        return {
            'success': False,
            'error': '服务器内部错误',
            'status': 500
        }, 500

    @app.errorhandler(400)
    def bad_request(error):
        return {
            'success': False,
            'error': '请求参数错误',
            'status': 400
        }, 400

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"未捕获的异常: {str(error)}", exc_info=True)
        return {
            'success': False,
            'error': f'处理请求时发生错误: {str(error)}',
            'status': 500
        }, 500
