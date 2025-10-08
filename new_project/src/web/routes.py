"""
路由注册

注册所有模块的路由
"""
from flask import Flask, render_template, jsonify, send_from_directory
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def register_routes(app: Flask):
    """
    注册所有路由

    Args:
        app: Flask应用实例
    """

    # 主页路由
    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    # 健康检查
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            'success': True,
            'status': 'healthy',
            'version': app.config.get('VERSION', '2.0.0')
        })

    # API信息
    @app.route('/api/info', methods=['GET'])
    def api_info():
        """API信息接口"""
        return jsonify({
            'success': True,
            'data': {
                'project_name': app.config.get('PROJECT_NAME'),
                'version': app.config.get('VERSION'),
                'environment': 'development' if app.config.get('DEBUG') else 'production'
            }
        })

    # 注册数据API - DEPRECATED: Module01替代
    # Module01提供完整的数据可视化API,包含metadata和v1/v2版本信息
    # from src.web.data_api import data_bp
    # app.register_blueprint(data_bp)

    # 注册Module00: 数据管理中心
    from src.web.modules.module00_data_management.api import m00_bp
    app.register_blueprint(m00_bp)

    # 注册Module01: 数据可视化 (替代旧的data_api.py)
    from src.web.modules.module01_data_visualization.api import m01_bp
    app.register_blueprint(m01_bp)

    # 注册ModuleEX: ROI配置管理(扩展模块)
    from src.web.modules.moduleEX_roi_config.api import mex_bp
    app.register_blueprint(mex_bp)

    # 注册任务配置API
    from src.web.modules.moduleEX_roi_config.task_config_api import task_config_bp
    app.register_blueprint(task_config_bp)

    # 注册校正API (Module01的子功能)
    from src.web.modules.module01_data_visualization.calibration_api import calibration_bp
    app.register_blueprint(calibration_bp)

    # 注册Module02: 数据预处理与质量控制
    from src.web.modules.module02_preprocessing.api import m02_bp
    app.register_blueprint(m02_bp)

    # 注册ModuleEX2: 数据导出与固化
    from src.web.modules.moduleEX2_data_export.api import ex2_bp
    app.register_blueprint(ex2_bp)

    # 注册Module04: 眼动事件分析
    from src.modules.module04_event_analysis.api import m04_bp
    app.register_blueprint(m04_bp)

    # 注册Module05: RQA递归量化分析
    from src.modules.module05_rqa_analysis.api import m05_bp
    app.register_blueprint(m05_bp)

    # 静态文件服务: 背景图片
    @app.route('/static/background_images/<version>/<filename>')
    def serve_background_image(version, filename):
        """提供背景图片静态文件服务"""
        try:
            project_root = Path(app.root_path).parent.parent
            background_dir = project_root / "data" / "background_images" / version
            return send_from_directory(background_dir, filename)
        except Exception as e:
            logger.error(f"Error serving background image: {e}")
            return jsonify({"success": False, "error": str(e)}), 404

    # TODO: 注册其他模块路由
    # 模块路由将在后续阶段逐个添加

    logger.info("路由注册完成")
