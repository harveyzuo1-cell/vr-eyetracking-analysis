"""
Module05 个体查询API - 4种个体分析查询
"""

from flask import Blueprint, request, jsonify
from pathlib import Path

from src.utils.logger import setup_logger
from .utils import handle_api_errors, validate_params

logger = setup_logger(__name__)

m05_individual_bp = Blueprint('m05_individual', __name__, url_prefix='/api/m05/advanced/individual')


@m05_individual_bp.route('/profile', methods=['POST'])
@validate_params('subject_id', 'params')
@handle_api_errors
def get_individual_profile():
    """
    获取个体RQA档案

    Request Body:
    {
        "subject_id": "control_legacy_1",
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "profile": {
            "subject_id": "control_legacy_1",
            "group": "control",
            "task_count": 5,
            "task_trajectories": {...},
            "individual_stats": {...}
        }
    }
    """
    from .individual_analyzer import IndividualAnalyzer
    from config.settings import Config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    profile = analyzer.get_individual_profile(subject_id, params)

    return jsonify({
        'success': True,
        'profile': profile
    })


@m05_individual_bp.route('/compare-to-group', methods=['POST'])
@validate_params('subject_id', 'params')
@handle_api_errors
def compare_individual_to_group():
    """
    个体vs组平均对比

    Request Body:
    {
        "subject_id": "control_legacy_1",
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "comparison": {
            "subject_id": "control_legacy_1",
            "group": "control",
            "outlier_count": 3,
            "total_features": 25,
            "comparison": [...]
        }
    }
    """
    from .individual_analyzer import IndividualAnalyzer
    from config.settings import Config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    comparison = analyzer.compare_to_group(subject_id, params)

    return jsonify({
        'success': True,
        'comparison': comparison
    })


@m05_individual_bp.route('/risk-assessment', methods=['POST'])
@validate_params('subject_id', 'params')
@handle_api_errors
def assess_individual_risk():
    """
    个体认知风险评估

    Request Body:
    {
        "subject_id": "control_legacy_1",
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "assessment": {
            "subject_id": "control_legacy_1",
            "group": "control",
            "risk_score": 25.5,
            "risk_level": "low",
            "risk_label": "低风险",
            "risk_factors": [...],
            "recommendation": "..."
        }
    }
    """
    from .individual_analyzer import IndividualAnalyzer
    from config.settings import Config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    assessment = analyzer.assess_cognitive_risk(subject_id, params)

    return jsonify({
        'success': True,
        'assessment': assessment
    })


@m05_individual_bp.route('/task-progression', methods=['POST'])
@validate_params('subject_id', 'params')
@handle_api_errors
def analyze_task_progression():
    """
    个体任务进程分析

    Request Body:
    {
        "subject_id": "control_legacy_1",
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "progression": {
            "subject_id": "control_legacy_1",
            "group": "control",
            "trends": {...},
            "interpretation": "..."
        }
    }
    """
    from .individual_analyzer import IndividualAnalyzer
    from config.settings import Config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    progression = analyzer.get_task_progression_analysis(subject_id, params)

    return jsonify({
        'success': True,
        'progression': progression
    })
