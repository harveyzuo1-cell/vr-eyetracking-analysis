"""
任务配置API
Task Configuration API

提供任务配置查询的RESTful API接口
"""
from flask import Blueprint, request, jsonify
import logging

from src.services.task_config_service import get_task_config_service

logger = logging.getLogger(__name__)

# 创建Blueprint
task_config_bp = Blueprint('task_config', __name__, url_prefix='/api/task-config')

# 获取服务实例
task_service = get_task_config_service()


@task_config_bp.route('/datasets', methods=['GET'])
def get_datasets():
    """
    获取所有数据集列表

    GET /api/task-config/datasets

    Returns:
        {
            "success": True,
            "data": [
                {
                    "id": "mmse_v1",
                    "name": "MMSE认知评估 (V1版本)",
                    "data_version": "v1",
                    "task_count": 5
                },
                ...
            ]
        }
    """
    try:
        datasets = task_service.get_all_datasets()

        # 添加任务数量统计
        result_datasets = []
        for dataset in datasets:
            dataset_info = {
                "id": dataset["id"],
                "name": dataset["name"],
                "name_en": dataset.get("name_en", ""),
                "description": dataset.get("description", ""),
                "data_version": dataset["data_version"],
                "task_count": len(dataset.get("tasks", [])),
                "created_date": dataset.get("created_date", "")
            }
            result_datasets.append(dataset_info)

        return jsonify({
            "success": True,
            "data": result_datasets,
            "message": f"Found {len(result_datasets)} datasets"
        })

    except Exception as e:
        logger.error(f"Error getting datasets: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        }), 500


@task_config_bp.route('/datasets/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """
    获取特定数据集的详细配置

    GET /api/task-config/datasets/mmse_v1

    Returns:
        {
            "success": True,
            "data": {
                "id": "mmse_v1",
                "name": "MMSE认知评估 (V1版本)",
                "data_version": "v1",
                "tasks": [...]
            }
        }
    """
    try:
        dataset = task_service.get_dataset_config(dataset_id)

        if dataset is None:
            return jsonify({
                "success": False,
                "error": f"Dataset '{dataset_id}' not found",
                "data": None
            }), 404

        return jsonify({
            "success": True,
            "data": dataset
        })

    except Exception as e:
        logger.error(f"Error getting dataset {dataset_id}: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@task_config_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    获取数据集的任务列表

    GET /api/task-config/tasks?dataset_id=mmse_v1

    Query Parameters:
        dataset_id (required): 数据集ID

    Returns:
        {
            "success": True,
            "data": {
                "dataset_id": "mmse_v1",
                "dataset_name": "MMSE认知评估 (V1版本)",
                "tasks": [
                    {
                        "id": "q1",
                        "name": "时间定向",
                        "order": 1,
                        ...
                    },
                    ...
                ]
            }
        }
    """
    try:
        dataset_id = request.args.get('dataset_id')

        if not dataset_id:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: dataset_id",
                "data": None
            }), 400

        dataset = task_service.get_dataset_config(dataset_id)
        if dataset is None:
            return jsonify({
                "success": False,
                "error": f"Dataset '{dataset_id}' not found",
                "data": None
            }), 404

        tasks = task_service.get_tasks(dataset_id)

        return jsonify({
            "success": True,
            "data": {
                "dataset_id": dataset_id,
                "dataset_name": dataset["name"],
                "tasks": tasks
            }
        })

    except Exception as e:
        logger.error(f"Error getting tasks: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@task_config_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """
    获取特定任务的配置

    GET /api/task-config/tasks/q1?dataset_id=mmse_v1

    Query Parameters:
        dataset_id (required): 数据集ID

    Returns:
        {
            "success": True,
            "data": {
                "id": "q1",
                "name": "时间定向",
                ...
            }
        }
    """
    try:
        dataset_id = request.args.get('dataset_id')

        if not dataset_id:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: dataset_id",
                "data": None
            }), 400

        task = task_service.get_task_by_id(dataset_id, task_id)

        if task is None:
            return jsonify({
                "success": False,
                "error": f"Task '{task_id}' not found in dataset '{dataset_id}'",
                "data": None
            }), 404

        return jsonify({
            "success": True,
            "data": task
        })

    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@task_config_bp.route('/infer-dataset', methods=['POST'])
def infer_dataset():
    """
    根据任务列表推断数据集类型

    POST /api/task-config/infer-dataset
    Body: {
        "tasks": ["q1", "q2", "q3", "q4", "q5"]
    }

    Returns:
        {
            "success": True,
            "data": {
                "dataset_id": "mmse_v1",
                "confidence": 1.0,
                "matched_tasks": 5,
                "total_tasks": 5
            }
        }
    """
    try:
        data = request.get_json()

        if not data or 'tasks' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: tasks",
                "data": None
            }), 400

        available_tasks = data['tasks']

        dataset_id, score = task_service.infer_dataset_from_data(available_tasks)

        if dataset_id is None:
            return jsonify({
                "success": False,
                "error": "Could not infer dataset from provided tasks",
                "data": {
                    "dataset_id": None,
                    "confidence": score,
                    "available_tasks": available_tasks
                }
            }), 404

        # 获取匹配的任务数量
        dataset = task_service.get_dataset_config(dataset_id)
        total_tasks = len(dataset.get("tasks", []))

        return jsonify({
            "success": True,
            "data": {
                "dataset_id": dataset_id,
                "dataset_name": dataset["name"],
                "confidence": score,
                "total_tasks": total_tasks
            }
        })

    except Exception as e:
        logger.error(f"Error inferring dataset: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@task_config_bp.route('/normalize-task-id', methods=['GET'])
def normalize_task_id():
    """
    标准化任务ID (将备用ID转换为主ID)

    GET /api/task-config/normalize-task-id?dataset_id=mmse_v1&task_id=task1

    Returns:
        {
            "success": True,
            "data": {
                "original_id": "task1",
                "normalized_id": "q1"
            }
        }
    """
    try:
        dataset_id = request.args.get('dataset_id')
        task_id = request.args.get('task_id')

        if not dataset_id or not task_id:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: dataset_id, task_id",
                "data": None
            }), 400

        normalized_id = task_service.normalize_task_id(dataset_id, task_id)

        if normalized_id is None:
            return jsonify({
                "success": False,
                "error": f"Task '{task_id}' not found in dataset '{dataset_id}'",
                "data": None
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "original_id": task_id,
                "normalized_id": normalized_id
            }
        })

    except Exception as e:
        logger.error(f"Error normalizing task ID: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500


@task_config_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查

    GET /api/task-config/health
    """
    try:
        datasets = task_service.get_all_datasets()

        return jsonify({
            "success": True,
            "status": "healthy",
            "data": {
                "dataset_count": len(datasets),
                "config_file": str(task_service.config_file),
                "config_version": task_service._config_cache.get("version", "unknown")
            }
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500
