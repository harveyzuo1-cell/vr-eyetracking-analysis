"""
ModuleEX2 数据导出 API

提供RESTful API接口
"""

from flask import Blueprint, request, jsonify, send_file
from functools import wraps

from .service import DataExportService
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# 创建Blueprint
ex2_bp = Blueprint('moduleEX2', __name__, url_prefix='/api/ex2')

# 初始化服务
export_service = DataExportService()


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
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'服务器内部错误: {str(e)}'
            }), 500
    return decorated_function


# ==================== 校准眼动数据导出 API ====================

@ex2_bp.route('/export/eyetracking', methods=['POST'])
@handle_errors
def export_eyetracking():
    """
    导出校准后的眼动数据

    Request Body:
        {
            "subject_ids": ["control_legacy_1", ...] or null (全部),
            "data_version": "v1" or "v2",
            "output_format": "csv" or "excel"
        }

    Returns:
        {
            "success": true,
            "file_path": "exports/calibrated_eyetracking_v1_20231207_143000.csv",
            "exported_count": 20,
            "total_records": 5000,
            "message": "成功导出20个任务的校准数据"
        }
    """
    data = request.get_json() or {}

    subject_ids = data.get('subject_ids')
    data_version = data.get('data_version', 'v1')
    output_format = data.get('output_format', 'csv')

    logger.info(f"导出眼动数据请求: version={data_version}, format={output_format}, subjects={len(subject_ids) if subject_ids else 'all'}")

    result = export_service.export_calibrated_eyetracking(
        subject_ids=subject_ids,
        data_version=data_version,
        output_format=output_format
    )

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ==================== ROI配置导出 API ====================

@ex2_bp.route('/export/roi', methods=['POST'])
@handle_errors
def export_roi():
    """
    导出ROI配置

    Request Body:
        {
            "data_version": "v1" or "v2",
            "output_format": "json" or "csv"
        }

    Returns:
        {
            "success": true,
            "file_path": "exports/roi_configs_v1_20231207_143000.csv",
            "exported_count": 5,
            "message": "成功导出5个任务的ROI配置"
        }
    """
    data = request.get_json() or {}

    data_version = data.get('data_version', 'v1')
    output_format = data.get('output_format', 'json')

    logger.info(f"导出ROI配置请求: version={data_version}, format={output_format}")

    result = export_service.export_roi_configs(
        data_version=data_version,
        output_format=output_format
    )

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ==================== 受试者+MMSE导出 API ====================

@ex2_bp.route('/export/subjects', methods=['POST'])
@handle_errors
def export_subjects():
    """
    导出受试者信息和MMSE评分

    Request Body:
        {
            "data_version": "v1" or "v2" or null (全部),
            "include_mmse_details": true or false
        }

    Returns:
        {
            "success": true,
            "file_path": "exports/subjects_mmse_v1_20231207_143000.csv",
            "exported_count": 60,
            "message": "成功导出60个受试者的信息和MMSE评分"
        }
    """
    data = request.get_json() or {}

    data_version = data.get('data_version')
    include_mmse_details = data.get('include_mmse_details', True)

    logger.info(f"导出受试者+MMSE请求: version={data_version or 'all'}, include_details={include_mmse_details}")

    result = export_service.export_subjects_with_mmse(
        data_version=data_version,
        include_mmse_details=include_mmse_details
    )

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ==================== 统一打包导出 API ====================

@ex2_bp.route('/export/all', methods=['POST'])
@handle_errors
def export_all():
    """
    统一打包导出所有数据

    Request Body:
        {
            "data_version": "v1" or "v2",
            "subject_ids": ["control_legacy_1", ...] or null (全部)
        }

    Returns:
        {
            "success": true,
            "zip_path": "exports/export_package_v1_20231207_143000.zip",
            "files_count": 3,
            "message": "成功打包导出3个数据文件"
        }
    """
    data = request.get_json() or {}

    data_version = data.get('data_version', 'v1')
    subject_ids = data.get('subject_ids')

    logger.info(f"统一打包导出请求: version={data_version}, subjects={len(subject_ids) if subject_ids else 'all'}")

    result = export_service.export_all(
        data_version=data_version,
        subject_ids=subject_ids
    )

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ==================== 导出文件列表 API ====================

@ex2_bp.route('/exports', methods=['GET'])
@handle_errors
def list_exports():
    """
    列出最近的导出文件

    Query Parameters:
        limit: 返回数量限制，默认20

    Returns:
        {
            "success": true,
            "exports": [
                {
                    "filename": "export_package_v1_20231207_143000.zip",
                    "size": 1024000,
                    "size_mb": 1.02,
                    "created_at": "2023-12-07T14:30:00",
                    "path": "exports/export_package_v1_20231207_143000.zip"
                },
                ...
            ],
            "total": 5,
            "message": "找到5个导出文件"
        }
    """
    limit = request.args.get('limit', 20, type=int)

    logger.info(f"列出导出文件请求: limit={limit}")

    result = export_service.list_exports(limit=limit)

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ==================== 下载导出文件 API ====================

@ex2_bp.route('/download/<path:filename>', methods=['GET'])
@handle_errors
def download_export(filename):
    """
    下载导出文件

    Path Parameters:
        filename: 文件名

    Returns:
        文件内容 (二进制流)
    """
    from pathlib import Path
    from config.settings import Config

    logger.info(f"下载导出文件请求: {filename}")

    export_dir = Path(Config.DATA_ROOT) / 'exports'
    file_path = export_dir / filename

    if not file_path.exists():
        return jsonify({
            'success': False,
            'message': '文件不存在'
        }), 404

    # 安全检查: 确保文件在exports目录内
    if not str(file_path.resolve()).startswith(str(export_dir.resolve())):
        return jsonify({
            'success': False,
            'message': '非法的文件路径'
        }), 403

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


# ==================== 健康检查 API ====================

@ex2_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口

    Returns:
        {
            "status": "ok",
            "module": "moduleEX2_data_export",
            "version": "1.0.0"
        }
    """
    return jsonify({
        'status': 'ok',
        'module': 'moduleEX2_data_export',
        'version': '1.0.0'
    }), 200


# ==================== 错误处理 ====================

@ex2_bp.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@ex2_bp.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500
