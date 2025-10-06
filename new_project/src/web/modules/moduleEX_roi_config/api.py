"""
ModuleEX ROI配置管理API
扩展模块：提供ROI配置相关的RESTful API接口
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os

from .service import ROIConfigService
from src.utils.logger import setup_logger


# 初始化日志
logger = setup_logger(__name__)

# 创建Blueprint
mex_bp = Blueprint('moduleEX', __name__, url_prefix='/api/config')

# 初始化服务
service = ROIConfigService()

# 文件大小限制 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


# ==================== 请求钩子 ====================

@mex_bp.before_request
def check_file_size():
    """检查上传文件大小"""
    if request.endpoint == 'moduleEX.upload_background_image':
        if request.content_length and request.content_length > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'message': f'文件过大，最大支持{MAX_FILE_SIZE // (1024*1024)}MB'
            }), 413


# ==================== 背景图片管理API ====================

@mex_bp.route('/background-images', methods=['GET'])
def get_background_images():
    """
    获取背景图片列表
    
    Query Parameters:
        version (str): 数据版本，默认v2
    
    Returns:
        {
            'success': bool,
            'data': [
                {
                    'filename': str,
                    'task_id': str,
                    'path': str,
                    'size': int,
                    'dimensions': {'width': int, 'height': int},
                    'modified_time': str
                }
            ],
            'message': str
        }
    """
    version = request.args.get('version', 'v2')
    result = service.list_background_images(version)
    return jsonify(result), 200 if result['success'] else 400


@mex_bp.route('/background-images/<task_id>', methods=['GET'])
def get_background_image(task_id):
    """
    获取指定背景图片信息或文件
    
    Path Parameters:
        task_id (str): 任务ID
    
    Query Parameters:
        version (str): 数据版本，默认v2
        download (bool): 是否下载文件，默认False（返回信息）
    
    Returns:
        JSON信息或图片文件
    """
    version = request.args.get('version', 'v2')
    download = request.args.get('download', 'false').lower() == 'true'
    
    result = service.get_background_image_info(version, task_id)
    
    if not result['success']:
        return jsonify(result), 404
    
    if download:
        # 返回图片文件
        file_path = result['data']['absolute_path']
        if os.path.exists(file_path):
            import mimetypes
            mimetype = mimetypes.guess_type(file_path)[0] or 'image/png'
            return send_file(file_path, mimetype=mimetype)
        else:
            return jsonify({'success': False, 'message': '文件不存在'}), 404
    else:
        # 返回图片信息
        return jsonify(result), 200


@mex_bp.route('/background-images', methods=['POST'])
def upload_background_image():
    """
    上传背景图片
    
    Request Body (multipart/form-data):
        file: 图片文件
        version: 数据版本
        task_id: 任务ID
    
    Returns:
        {
            'success': bool,
            'data': {...},
            'message': str
        }
    """
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未提供文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        # 获取参数
        version = request.form.get('version', 'v2')
        task_id = request.form.get('task_id')
        
        if not task_id:
            return jsonify({'success': False, 'message': '未提供task_id'}), 400
        
        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        filename = secure_filename(file.filename)
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({
                'success': False,
                'message': f'不支持的文件类型，仅支持: {", ".join(allowed_extensions)}'
            }), 400
        
        # 保存文件
        result = service.save_background_image(file, version, task_id, filename)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500


# ==================== ROI配置管理API ====================

@mex_bp.route('/roi', methods=['GET'])
def get_roi_config():
    """
    获取ROI配置
    
    Query Parameters:
        version (str): 数据版本，默认v2
        task_id (str): 任务ID，必需
    
    Returns:
        {
            'success': bool,
            'data': {...},  # ROI配置JSON
            'message': str
        }
    """
    version = request.args.get('version', 'v2')
    task_id = request.args.get('task_id')
    
    if not task_id:
        return jsonify({'success': False, 'message': '未提供task_id'}), 400
    
    result = service.load_roi_config(version, task_id)
    return jsonify(result), 200 if result['success'] else 400


@mex_bp.route('/roi', methods=['POST'])
def save_roi_config():
    """
    保存ROI配置
    
    Request Body (JSON):
        {
            'version': str,
            'task_id': str,
            'config': {...}  # ROI配置对象
        }
    
    Returns:
        {
            'success': bool,
            'data': {...},
            'message': str
        }
    """
    try:
        data = request.get_json()
        logger.debug(f"Received ROI config data: {data}")

        if not data:
            return jsonify({'success': False, 'message': '未提供数据'}), 400

        version = data.get('version', 'v2')
        task_id = data.get('task_id')
        config = data.get('config')

        logger.debug(f"ROI config params - version: {version}, task_id: {task_id}")
        logger.debug(f"ROI config content: {config}")

        if not task_id:
            return jsonify({'success': False, 'message': '未提供task_id'}), 400

        if not config:
            return jsonify({'success': False, 'message': '未提供config'}), 400

        result = service.save_roi_config(version, task_id, config)
        logger.info(f"ROI config saved - task_id: {task_id}, success: {result['success']}")
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@mex_bp.route('/roi/validate', methods=['POST'])
def validate_roi_config():
    """
    验证ROI配置
    
    Request Body (JSON):
        {
            'config': {...}  # ROI配置对象
        }
    
    Returns:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'config' not in data:
            return jsonify({
                'valid': False,
                'errors': ['未提供config'],
                'warnings': []
            }), 400
        
        config = data['config']
        result = service.validate_config(config)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'errors': [f'验证失败: {str(e)}'],
            'warnings': []
        }), 500


# ==================== ROI ID管理API ====================

@mex_bp.route('/roi/validate-id', methods=['POST'])
def validate_roi_id():
    """
    验证ROI ID格式
    
    Request Body (JSON):
        {
            'roi_id': str,
            'roi_type': str,  # KW/INST/BG
            'task_id': str
        }
    
    Returns:
        {
            'valid': bool,
            'message': str,
            'details': {...}
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'valid': False, 'message': '未提供数据'}), 400
        
        roi_id = data.get('roi_id')
        roi_type = data.get('roi_type')
        task_id = data.get('task_id')
        
        if not all([roi_id, roi_type, task_id]):
            return jsonify({
                'valid': False,
                'message': '缺少必需参数: roi_id, roi_type, task_id'
            }), 400
        
        result = service.validate_roi_id(roi_id, roi_type, task_id)
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f'验证失败: {str(e)}'
        }), 500


@mex_bp.route('/roi/generate-id', methods=['POST'])
def generate_roi_id():
    """
    生成下一个可用的ROI ID
    
    Request Body (JSON):
        {
            'roi_type': str,  # KW/INST/BG
            'task_id': str,
            'version': str    # v1/v2, 默认v2
        }
    
    Returns:
        {
            'success': bool,
            'data': {'roi_id': str},
            'message': str
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '未提供数据'}), 400
        
        roi_type = data.get('roi_type')
        task_id = data.get('task_id')
        version = data.get('version', 'v2')
        
        if not all([roi_type, task_id]):
            return jsonify({
                'success': False,
                'message': '缺少必需参数: roi_type, task_id'
            }), 400
        
        result = service.generate_roi_id(roi_type, task_id, version)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成失败: {str(e)}'
        }), 500


# ==================== 健康检查 ====================

@mex_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    Returns:
        {
            'status': 'ok',
            'module': 'module11_config_manager',
            'version': 'v1.0.0'
        }
    """
    return jsonify({
        'status': 'ok',
        'module': 'moduleEX_roi_config',
        'version': 'v1.0.0'
    }), 200


# ==================== 错误处理 ====================

@mex_bp.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@mex_bp.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


