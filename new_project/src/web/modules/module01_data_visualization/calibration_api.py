"""
眼动数据校正API
Gaze Data Calibration API

提供RESTful API接口用于眼动数据校正
"""
from flask import Blueprint, request, jsonify
from src.utils.logger import setup_logger
from .calibration_service import CalibrationService
from .calibration_validator import CalibrationValidator

logger = setup_logger(__name__)

# 创建Blueprint
calibration_bp = Blueprint('calibration', __name__, url_prefix='/api/module01/calibration')

# 初始化服务和验证器
calibration_service = CalibrationService()
validator = CalibrationValidator()


@calibration_bp.route('/save', methods=['POST'])
def save_calibration():
    """
    保存校正数据

    Request Body:
    {
        "group": "control",
        "subject_id": "S001",
        "task": "q1",
        "params": {
            "offsetX": 0.01,
            "offsetY": -0.02,
            "trimStart": 0.1,
            "trimEnd": 0.2
        }
    }

    Response:
    {
        "success": true,
        "message": "校正数据已保存",
        "data": {
            "output_file": "path/to/calibrated.csv",
            "params_file": "path/to/params.json",
            "points_before": 1000,
            "points_after": 950,
            "duration_before": 10.5,
            "duration_after": 10.2
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400

        # 验证参数
        is_valid, errors = validator.validate_calibration_request(data)
        if not is_valid:
            logger.warning(f"Invalid calibration request: {errors}")
            return jsonify({
                'success': False,
                'message': 'Invalid parameters',
                'errors': errors
            }), 400

        # 执行校正并保存
        result = calibration_service.save_calibrated_data(
            group=data['group'],
            subject_id=data['subject_id'],
            task=data['task'],
            params=data['params']
        )

        logger.info(
            f"Calibration saved: {data['group']}/{data['subject_id']}_{data['task']}, "
            f"points: {result['points_before']} -> {result['points_after']}"
        )

        return jsonify({
            'success': True,
            'message': '校正数据已保存',
            'data': result
        }), 200

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return jsonify({
            'success': False,
            'message': '原始数据文件不存在',
            'error': str(e)
        }), 404

    except ValueError as e:
        logger.error(f"Value error: {e}")
        return jsonify({
            'success': False,
            'message': '数据格式错误',
            'error': str(e)
        }), 400

    except Exception as e:
        logger.error(f"Save calibration error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@calibration_bp.route('/params', methods=['GET'])
def get_calibration_params():
    """
    获取已保存的校正参数

    Query Parameters:
        group: 组别
        subject_id: 受试者ID
        task: 任务ID

    Response:
    {
        "success": true,
        "data": {
            "params": {...},
            "metadata": {...}
        }
    }
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task = request.args.get('task')

        # 验证参数
        is_valid, errors = validator.validate_get_params_request(group, subject_id, task)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid parameters',
                'errors': errors
            }), 400

        # 获取参数
        params = calibration_service.get_saved_params(group, subject_id, task)

        if params is None:
            return jsonify({
                'success': True,
                'data': None,
                'message': '未找到校正参数'
            }), 200

        logger.info(f"Retrieved calibration params: {group}/{subject_id}_{task}")

        return jsonify({
            'success': True,
            'data': params
        }), 200

    except Exception as e:
        logger.error(f"Get params error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@calibration_bp.route('/data', methods=['GET'])
def get_calibrated_data():
    """
    加载校正后的数据

    Query Parameters:
        group: 组别
        subject_id: 受试者ID
        task: 任务ID

    Response:
    {
        "success": true,
        "data": [
            {"x": 0.11, "y": 0.08, "timestamp": 0},
            {"x": 0.21, "y": 0.18, "timestamp": 0.1},
            ...
        ]
    }
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task = request.args.get('task')

        # 验证参数
        is_valid, errors = validator.validate_get_params_request(group, subject_id, task)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid parameters',
                'errors': errors
            }), 400

        # 加载数据
        data = calibration_service.load_calibrated_data(group, subject_id, task)

        logger.info(f"Loaded calibrated data: {group}/{subject_id}_{task}, points: {len(data)}")

        return jsonify({
            'success': True,
            'data': data
        }), 200

    except FileNotFoundError as e:
        logger.warning(f"Calibrated data not found: {e}")
        return jsonify({
            'success': False,
            'message': '校正数据不存在',
            'error': str(e)
        }), 404

    except Exception as e:
        logger.error(f"Load calibrated data error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@calibration_bp.route('/delete', methods=['DELETE'])
def delete_calibration():
    """
    删除校正数据

    Query Parameters:
        group: 组别
        subject_id: 受试者ID
        task: 任务ID

    Response:
    {
        "success": true,
        "message": "校正数据已删除"
    }
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task = request.args.get('task')

        # 验证参数
        is_valid, errors = validator.validate_get_params_request(group, subject_id, task)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid parameters',
                'errors': errors
            }), 400

        # 删除校正
        deleted = calibration_service.delete_calibration(group, subject_id, task)

        if deleted:
            logger.info(f"Deleted calibration: {group}/{subject_id}_{task}")
            return jsonify({
                'success': True,
                'message': '校正数据已删除'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '校正数据不存在'
            }), 404

    except Exception as e:
        logger.error(f"Delete calibration error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@calibration_bp.route('/versions', methods=['GET'])
def get_versions():
    """
    获取校准版本列表

    Query Parameters:
        - group: 组别
        - subject_id: 受试者ID
        - task: 任务ID

    Returns:
        - 200: 版本列表
        - 400: 参数错误
        - 500: 服务器错误
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task = request.args.get('task')

        if not all([group, subject_id, task]):
            return jsonify({
                'success': False,
                'message': '缺少必需参数'
            }), 400

        versions = calibration_service.get_calibration_versions(
            group=group,
            subject_id=subject_id,
            task=task
        )

        return jsonify({
            'success': True,
            'data': versions,
            'count': len(versions)
        }), 200

    except Exception as e:
        logger.error(f"Get versions error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@calibration_bp.route('/restore', methods=['POST'])
def restore_version():
    """
    恢复到指定版本

    Request Body:
        - group: 组别
        - subject_id: 受试者ID
        - task: 任务ID
        - version: 版本号

    Returns:
        - 200: 恢复成功
        - 400: 参数错误
        - 404: 版本不存在
        - 500: 服务器错误
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400

        group = data.get('group')
        subject_id = data.get('subject_id')
        task = data.get('task')
        version = data.get('version')

        if not all([group, subject_id, task, version]):
            return jsonify({
                'success': False,
                'message': '缺少必需参数'
            }), 400

        result = calibration_service.restore_calibration_version(
            group=group,
            subject_id=subject_id,
            task=task,
            version=version
        )

        logger.info(f"Restored to version {version}: {group}/{subject_id}_{task}")

        return jsonify({
            'success': True,
            'message': f'已恢复到版本 {version}',
            'data': result
        }), 200

    except FileNotFoundError as e:
        logger.warning(f"Version not found: {e}")
        return jsonify({
            'success': False,
            'message': '指定版本不存在',
            'error': str(e)
        }), 404

    except Exception as e:
        logger.error(f"Restore version error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@calibration_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'success': True,
        'message': 'Calibration API is healthy',
        'service': 'calibration',
        'endpoints': [
            'POST /api/module01/calibration/save',
            'GET /api/module01/calibration/params',
            'GET /api/module01/calibration/data',
            'DELETE /api/module01/calibration/delete',
            'GET /api/module01/calibration/versions',
            'POST /api/module01/calibration/restore',
            'GET /api/module01/calibration/health'
        ]
    }), 200
