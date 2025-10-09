"""
Module05 高级分析API - 参数评估和任务分析
"""

from flask import Blueprint, request, jsonify
from pathlib import Path

from src.utils.logger import setup_logger
from .utils import handle_api_errors, validate_params

logger = setup_logger(__name__)

m05_advanced_bp = Blueprint('m05_advanced', __name__, url_prefix='/api/m05/advanced')


@m05_advanced_bp.route('/evaluate-params', methods=['POST'])
@handle_api_errors
def evaluate_parameters():
    """
    参数性能评估 - 自动评估所有参数组合的性能

    Request Body:
    {
        "metric": "f_stat_mean"  // 可选: f_stat_mean, significant_count, f_stat_max
    }

    Response:
    {
        "success": true,
        "results": [
            {
                "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
                "f_stat_mean": 42.3,
                "f_stat_max": 85.6,
                "significant_count": 10,
                "significant_ratio": 0.4
            },
            ...
        ],
        "total_evaluated": 955
    }
    """
    from .param_evaluator import ParamEvaluator
    from config.settings import Config

    data = request.get_json() or {}
    metric = data.get('metric', 'f_stat_mean')

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    evaluator = ParamEvaluator(results_dir)
    results = evaluator.evaluate_all_params(metric=metric)

    return jsonify({
        'success': True,
        'results': results,
        'total_evaluated': len(results)
    })


@m05_advanced_bp.route('/task-analysis', methods=['POST'])
@validate_params('params', 'task_id')
@handle_api_errors
def task_layer_analysis():
    """
    任务分层分析 - 对指定任务进行独立统计分析

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "task_id": "q1",
        "groups": ["control", "mci", "ad"]  // 可选
    }

    Response:
    {
        "success": true,
        "statistics": [
            {
                "feature": "x_RR",
                "control": {"mean": 0.45, "std": 0.12},
                "mci": {"mean": 0.42, "std": 0.15},
                "ad": {"mean": 0.38, "std": 0.18},
                "f_stat": 3.45,
                "p_value": 0.034
            },
            ...
        ]
    }
    """
    from .task_analyzer import TaskAnalyzer
    from config.settings import Config

    data = request.get_json()
    params = data['params']
    task_id = data['task_id']
    groups = data.get('groups', ['control', 'mci', 'ad'])

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = TaskAnalyzer(results_dir)
    result = analyzer.analyze_single_task(params, task_id, groups)

    return jsonify({
        'success': True,
        'task_id': result['task_id'],
        'sample_size': result['sample_size'],
        'statistics': result['statistics']
    })


@m05_advanced_bp.route('/task-compare', methods=['POST'])
@validate_params('params', 'tasks')
@handle_api_errors
def task_comparison():
    """
    任务对比分析 - 对比多个任务的RQA特征差异

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "tasks": ["q1", "q2", "q3", "q4", "q5"]
    }

    Response:
    {
        "success": true,
        "comparison": {
            "params": {...},
            "tasks": ["q1", "q2", ...],
            "significant_features": ["x_RR", "combined_DET", ...],
            "significant_count": 8,
            "comparison_details": [...]
        }
    }
    """
    from .task_analyzer import TaskAnalyzer
    from config.settings import Config

    data = request.get_json()
    params = data['params']
    tasks = data['tasks']

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = TaskAnalyzer(results_dir)
    comparison = analyzer.compare_tasks(params, tasks)

    return jsonify({
        'success': True,
        'comparison': comparison
    })


@m05_advanced_bp.route('/subjects/list', methods=['POST'])
@validate_params('params')
@handle_api_errors
def list_subjects():
    """
    获取所有受试者列表

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "subjects": [
            {"subject_id": "control_legacy_1", "group": "control"},
            ...
        ]
    }
    """
    from .individual_analyzer import IndividualAnalyzer
    from config.settings import Config

    data = request.get_json()
    params = data['params']

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    subjects = analyzer.get_all_subjects(params)

    return jsonify({
        'success': True,
        'subjects': subjects,
        'total_count': len(subjects)
    })
