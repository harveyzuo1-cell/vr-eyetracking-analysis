"""
Module04 事件分析API
"""

from flask import Blueprint, request, jsonify

from src.utils.logger import setup_logger
from .service import EventAnalysisService

logger = setup_logger(__name__)

m04_bp = Blueprint('m04', __name__, url_prefix='/api/m04')

# 初始化服务
service = EventAnalysisService()


@m04_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'module': 'module04_event_analysis'})


@m04_bp.route('/analyze/single', methods=['POST'])
def analyze_single():
    """
    分析单个受试者的单个任务

    Request Body:
        {
            "subject_id": "subject_001",
            "group": "control",
            "task_id": "q1",
            "data_version": "v1"
        }
    """
    try:
        data = request.get_json()

        subject_id = data.get('subject_id')
        group = data.get('group')
        task_id = data.get('task_id')
        data_version = data.get('data_version', 'v1')

        if not all([subject_id, group, task_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数: subject_id, group, task_id'
            }), 400

        result = service.analyze_single_file(subject_id, group, task_id, data_version)

        return jsonify(result)

    except Exception as e:
        logger.error(f"分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@m04_bp.route('/analyze/subject', methods=['POST'])
def analyze_subject():
    """
    分析单个受试者的所有任务

    Request Body:
        {
            "subject_id": "subject_001",
            "group": "control",
            "data_version": "v1",
            "tasks": ["q1", "q2", "q3", "q4", "q5"]  // 可选
        }
    """
    try:
        data = request.get_json()

        subject_id = data.get('subject_id')
        group = data.get('group')
        data_version = data.get('data_version', 'v1')
        tasks = data.get('tasks')

        if not all([subject_id, group]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数: subject_id, group'
            }), 400

        result = service.analyze_subject(subject_id, group, data_version, tasks)

        return jsonify(result)

    except Exception as e:
        logger.error(f"分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@m04_bp.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    """
    批量分析

    Request Body:
        {
            "group": "control",  // 可选
            "data_version": "v1",
            "subject_ids": ["sub_001", "sub_002"]  // 可选
        }
    """
    try:
        data = request.get_json() or {}

        group = data.get('group')
        data_version = data.get('data_version', 'v1')
        subject_ids = data.get('subject_ids')

        result = service.analyze_batch(group, data_version, subject_ids)

        return jsonify(result)

    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@m04_bp.route('/events', methods=['GET'])
def get_events():
    """
    获取事件数据表格

    Query Parameters:
        - subject_id: 受试者ID (可选)
        - group: 分组 (可选)
        - task_id: 任务ID (可选)
        - event_type: 事件类型 fixation/saccade (可选)
    """
    try:
        subject_id = request.args.get('subject_id')
        group = request.args.get('group')
        task_id = request.args.get('task_id')
        event_type = request.args.get('event_type')

        result = service.get_events_table(subject_id, group, task_id, event_type)

        return jsonify(result)

    except Exception as e:
        logger.error(f"获取事件数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@m04_bp.route('/roi/statistics', methods=['GET'])
def get_roi_stats():
    """
    获取ROI统计数据

    Query Parameters:
        - group: 分组 (可选)
        - task_id: 任务ID (可选)
    """
    try:
        group = request.args.get('group')
        task_id = request.args.get('task_id')

        result = service.get_roi_statistics(group, task_id)

        return jsonify(result)

    except Exception as e:
        logger.error(f"获取ROI统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
