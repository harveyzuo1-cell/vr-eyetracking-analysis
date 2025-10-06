"""
Module 01: 数据可视化 - API路由
Data Visualization - API Routes

Provides endpoints for loading and visualizing eye-tracking data
"""
from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any

from .service import DataVisualizationService

logger = logging.getLogger(__name__)

# 创建Blueprint
m01_bp = Blueprint('module01', __name__, url_prefix='/api/data')

# 初始化服务
viz_service = DataVisualizationService()


@m01_bp.route('/groups', methods=['GET'])
def get_groups():
    """
    获取组别列表

    GET /api/data/groups?version=all|v1|v2

    Query Parameters:
        version: 数据版本筛选 (all/v1/v2)，默认all

    Returns:
        {
            "success": true,
            "data": [
                {"id": "control", "name": "对照组", "count": 65},
                {"id": "mci", "name": "MCI组", "count": 42},
                {"id": "ad", "name": "AD组", "count": 42}
            ]
        }
    """
    try:
        version = request.args.get('version', 'all')
        result = viz_service.get_groups(version)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting groups: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        }), 500


@m01_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """
    获取指定组别的受试者列表（支持版本筛选）

    GET /api/data/subjects?group=control&version=v1

    Query Parameters:
        group: 组别ID (control/mci/ad)
        version: 数据版本 (all/v1/v2)，可选，默认all

    Returns:
        {
            "success": true,
            "data": [
                {"id": "control_01", "task_count": 5, "data_version": "v1"},
                {"id": "control_02", "task_count": 5, "data_version": "v2"}
            ]
        }
    """
    try:
        group = request.args.get('group')
        version = request.args.get('version', 'all')  # 默认all

        if not group:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: group",
                "data": []
            }), 400

        result = viz_service.get_subjects(group, version)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting subjects: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        }), 500


@m01_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    获取指定受试者的任务列表

    GET /api/data/tasks?group=control&subject_id=control_01

    Query Parameters:
        group: 组别ID
        subject_id: 受试者ID

    Returns:
        {
            "success": true,
            "data": ["q1", "q2", "q3", "q4", "q5"]
        }
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')

        if not group or not subject_id:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: group, subject_id",
                "data": []
            }), 400

        result = viz_service.get_tasks(group, subject_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting tasks: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        }), 500


@m01_bp.route('/raw/all', methods=['GET'])
def get_all_tasks_data():
    """
    加载受试者的所有任务数据(Q1-Q5)

    GET /api/data/raw/all?group=control&subject_id=control_01

    Query Parameters:
        group: 组别ID
        subject_id: 受试者ID

    Returns:
        {
            "success": true,
            "data": [...],
            "stats": {...},
            "metadata": {...}
        }
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')

        if not all([group, subject_id]):
            return jsonify({
                "success": False,
                "error": "Missing required parameters: group, subject_id",
                "data": [],
                "stats": None,
                "metadata": None
            }), 400

        result = viz_service.load_all_tasks_data(group, subject_id)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error loading all tasks data: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": [],
            "stats": None,
            "metadata": None
        }), 500


@m01_bp.route('/raw', methods=['GET'])
def get_raw_data():
    """
    加载原始眼动数据

    GET /api/data/raw?group=control&subject_id=control_01&task_id=q1

    Query Parameters:
        group: 组别ID
        subject_id: 受试者ID
        task_id: 任务ID (q1-q5)

    Returns:
        {
            "success": true,
            "data": [
                {"timestamp": 0.0, "x": 0.5, "y": 0.5},
                ...
            ],
            "stats": {
                "total_points": 1000,
                "duration": 5000.0,
                "x_range": [0.0, 1.0],
                "y_range": [0.0, 1.0]
            },
            "metadata": {
                "group": "control",
                "subject_id": "control_01",
                "task": "q1"
            }
        }
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task_id = request.args.get('task_id')

        if not all([group, subject_id, task_id]):
            return jsonify({
                "success": False,
                "error": "Missing required parameters: group, subject_id, task_id",
                "data": [],
                "stats": None,
                "metadata": None
            }), 400

        result = viz_service.load_raw_data(group, subject_id, task_id)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error loading raw data: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": [],
            "stats": None,
            "metadata": None
        }), 500


@m01_bp.route('/roi', methods=['GET'])
def get_roi_config():
    """
    获取ROI配置

    GET /api/data/roi?version=v1&task=q1

    Query Parameters:
        version (required): 数据版本 (v1/v2)
        task (required): 任务ID (q1/q2/q3/q4/q5/all)

    Returns:
        {
            "success": true,
            "data": {
                "version": "v1",
                "layout": "legacy",
                "task": "q1",
                "regions": [...]
            }
        }
    """
    try:
        version = request.args.get('version')
        task = request.args.get('task')

        if not version or not task:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: version and task",
                "data": None
            }), 400

        result = viz_service.get_roi_config(version, task)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting ROI config: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@m01_bp.route('/background-image', methods=['GET'])
def get_background_image():
    """
    获取任务背景图片路径

    GET /api/data/background-image?version=v1&task=q1

    Query Parameters:
        version (required): 数据版本 (v1/v2)
        task (required): 任务ID (q1/q2/q3/q4/q5)

    Returns:
        {
            "success": true,
            "data": {
                "version": "v1",
                "task": "q1",
                "image_path": "/static/background_images/v1/Q1.jpg",
                "exists": true
            }
        }
    """
    try:
        version = request.args.get('version')
        task = request.args.get('task')

        if not version or not task:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: version and task",
                "data": None
            }), 400

        result = viz_service.get_background_image(version, task)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting background image: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@m01_bp.route('/roi-enhanced', methods=['GET'])
def get_roi_config_enhanced():
    """
    获取增强版ROI配置

    GET /api/data/roi-enhanced?version=v1&task=q1

    Query Parameters:
        version (required): 数据版本 (v1/v2)
        task (required): 任务ID (q1/q2/q3/q4/q5/all)

    Returns:
        {
            "success": true,
            "data": {
                "version": "v1",
                "task": "q1",
                "task_name": "时间定向",
                "background_image": "/static/background_images/v1/Q1.jpg",
                "regions": {
                    "keywords": [...],
                    "instructions": [...],
                    "background": [...]
                }
            }
        }
    """
    try:
        version = request.args.get('version')
        task = request.args.get('task')

        if not version or not task:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: version and task",
                "data": None
            }), 400

        result = viz_service.get_roi_config_enhanced(version, task)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting enhanced ROI config: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@m01_bp.route('/roi-stats', methods=['POST'])
def calculate_roi_stats():
    """
    计算ROI统计信息

    POST /api/data/roi-stats

    Body:
        {
            "version": "v1",
            "task": "q1",
            "gaze_data": [
                {"x": 0.5, "y": 0.5, "timestamp": 0.0},
                {"x": 0.51, "y": 0.52, "timestamp": 0.016},
                ...
            ]
        }

    Returns:
        {
            "success": true,
            "data": {
                "stats": {
                    "KW_q1_1": {
                        "fixation_time": 2.5,
                        "entry_count": 3,
                        "regression_count": 2,
                        ...
                    },
                    ...
                },
                "summary": {
                    "total_fixation_time": 10.5,
                    "keywords_fixation_time": 5.2,
                    ...
                }
            }
        }
    """
    try:
        data = request.get_json()
        version = data.get("version")
        task = data.get("task")
        gaze_data_list = data.get("gaze_data", [])

        if not version or not task:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: version and task",
                "data": None
            }), 400

        result = viz_service.calculate_roi_stats(version, task, gaze_data_list)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error calculating ROI stats: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500
