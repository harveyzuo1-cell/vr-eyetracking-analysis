"""
Module04 事件分析API
"""

from flask import Blueprint, request, jsonify

from src.utils.logger import setup_logger
from .service import EventAnalysisService
from .utils import handle_api_errors, validate_params

logger = setup_logger(__name__)

m04_bp = Blueprint('m04', __name__, url_prefix='/api/m04')

# Service单例实例（懒加载）
_service_instance = None


def get_service() -> EventAnalysisService:
    """
    获取EventAnalysisService单例实例（懒加载模式）

    Returns:
        EventAnalysisService: Service实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = EventAnalysisService()
        logger.info("EventAnalysisService initialized (lazy loading)")
    return _service_instance


@m04_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'module': 'module04_event_analysis'})


@m04_bp.route('/analyze/single', methods=['POST'])
@validate_params('subject_id', 'group', 'task_id')
@handle_api_errors
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
    data = request.get_json()

    subject_id = data.get('subject_id')
    group = data.get('group')
    task_id = data.get('task_id')
    data_version = data.get('data_version', 'v1')

    service = get_service()
    result = service.analyze_single_file(subject_id, group, task_id, data_version)

    return jsonify(result)


@m04_bp.route('/analyze/subject', methods=['POST'])
@validate_params('subject_id', 'group')
@handle_api_errors
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
    data = request.get_json()

    subject_id = data.get('subject_id')
    group = data.get('group')
    data_version = data.get('data_version', 'v1')
    tasks = data.get('tasks')

    service = get_service()
    result = service.analyze_subject(subject_id, group, data_version, tasks)

    return jsonify(result)


@m04_bp.route('/analyze/batch', methods=['POST'])
@handle_api_errors
def analyze_batch():
    """
    批量分析

    Request Body:
        {
            "group": "control",  // 可选
            "data_version": "v1",
            "subject_ids": ["sub_001", "sub_002"],  // 可选
            "velocity_threshold": 40.0,  // IVT速度阈值 (deg/s)
            "min_fixation_duration": 100  // 最小注视时长 (ms)
        }
    """
    data = request.get_json() or {}

    group = data.get('group')
    data_version = data.get('data_version', 'v1')
    subject_ids = data.get('subject_ids')

    # IVT参数
    velocity_threshold = data.get('velocity_threshold', 40.0)
    min_fixation_duration = data.get('min_fixation_duration', 100)

    service = get_service()
    result = service.analyze_batch(
        group=group,
        data_version=data_version,
        subject_ids=subject_ids,
        velocity_threshold=velocity_threshold,
        min_fixation_duration=min_fixation_duration
    )

    return jsonify(result)


@m04_bp.route('/events', methods=['GET'])
@handle_api_errors
def get_events():
    """
    获取事件数据表格

    Query Parameters:
        - subject_id: 受试者ID (可选)
        - group: 分组 (可选)
        - task_id: 任务ID (可选)
        - event_type: 事件类型 fixation/saccade (可选)
    """
    subject_id = request.args.get('subject_id')
    group = request.args.get('group')
    task_id = request.args.get('task_id')
    event_type = request.args.get('event_type')

    service = get_service()
    result = service.get_events_table(subject_id, group, task_id, event_type)

    return jsonify(result)


@m04_bp.route('/roi/statistics', methods=['GET'])
@handle_api_errors
def get_roi_stats():
    """
    获取ROI统计数据

    Query Parameters:
        - group: 分组 (可选)
        - task_id: 任务ID (可选)
    """
    group = request.args.get('group')
    task_id = request.args.get('task_id')

    service = get_service()
    result = service.get_roi_statistics(group, task_id)

    return jsonify(result)

@m04_bp.route('/features', methods=['POST'])
@handle_api_errors
def get_features():
    """
    获取特征统计数据 (每个受试者-任务一行)

    Request Body:
        {
            "group": "control",  // 可选
            "data_version": "v1",
            "velocity_threshold": 40.0,
            "min_fixation_duration": 100
        }
    """
    data = request.get_json() or {}

    group = data.get('group')
    data_version = data.get('data_version', 'v1')
    velocity_threshold = data.get('velocity_threshold', 40.0)
    min_fixation_duration = data.get('min_fixation_duration', 100)

    service = get_service()
    result = service.get_feature_statistics(
        group=group,
        data_version=data_version,
        velocity_threshold=velocity_threshold,
        min_fixation_duration=min_fixation_duration
    )

    return jsonify(result)


@m04_bp.route('/cache', methods=['GET'])
@handle_api_errors
def get_cache():
    """
    获取缓存的分析结果

    Returns:
        {
            "success": true,
            "timestamp": "2025-10-07T12:00:00",
            "batch_result": {...},
            "features_result": {...}
        }
    """
    service = get_service()
    cache_data = service.load_cache()

    if cache_data:
        return jsonify({
            'success': True,
            'timestamp': cache_data.get('timestamp'),
            'batch_result': cache_data.get('batch_result'),
            'features_result': cache_data.get('features_result')
        })
    else:
        return jsonify({
            'success': False,
            'error': '没有缓存数据'
        })
