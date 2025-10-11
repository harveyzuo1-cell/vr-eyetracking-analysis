"""
Module06 特征提取与选择 API
"""

from flask import Blueprint, request, jsonify
from src.utils.logger import setup_logger
from .service import FeatureExtractionService
from .utils import handle_api_errors, validate_params

logger = setup_logger(__name__)

m06_bp = Blueprint('m06', __name__, url_prefix='/api/m06')

# Service单例实例（懒加载）
_service_instance = None


def get_service() -> FeatureExtractionService:
    """
    获取FeatureExtractionService单例实例（懒加载模式）

    Returns:
        FeatureExtractionService: Service实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = FeatureExtractionService()
        logger.info("FeatureExtractionService initialized (lazy loading)")
    return _service_instance


@m06_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'module': 'module06_feature_extraction'})


# ============================
# Module04 敏感度分析 API
# ============================

@m06_bp.route('/m04/sensitivity/compute', methods=['POST'])
@handle_api_errors
def compute_m04_sensitivity():
    """
    计算Module04所有特征的敏感度分析

    Request Body:
        {
            "data_version": "v1",
            "groups": ["control", "mci", "ad"],  // 可选，默认全部三组
            "velocity_threshold": 40.0,
            "min_fixation_duration": 100
        }

    Response:
        {
            "success": true,
            "data": {
                "summary": {...},
                "top_4_features": [...],
                "all_features": [...],
                "interpretation": {...}
            }
        }
    """
    data = request.get_json() or {}

    data_version = data.get('data_version', 'v1')
    groups = data.get('groups')
    velocity_threshold = data.get('velocity_threshold', 40.0)
    min_fixation_duration = data.get('min_fixation_duration', 100)

    service = get_service()
    result = service.compute_m04_sensitivity(
        data_version=data_version,
        groups=groups,
        velocity_threshold=velocity_threshold,
        min_fixation_duration=min_fixation_duration
    )

    return jsonify({
        'success': True,
        'data': result
    })


@m06_bp.route('/m04/sensitivity/top-k', methods=['GET'])
@handle_api_errors
def get_m04_top_k():
    """
    获取Module04 Top-K敏感特征列表

    Query Parameters:
        - k: 选择的特征数量，默认4
        - data_version: 数据版本，默认v1

    Response:
        {
            "success": true,
            "data": {
                "top_k": ["avg_fixation_duration", "kw_ratio_frame", ...],
                "k": 4,
                "data_version": "v1",
                "cached": true/false
            }
        }
    """
    k = request.args.get('k', default=4, type=int)
    data_version = request.args.get('data_version', default='v1', type=str)

    service = get_service()
    result = service.get_m04_top_k(k=k, data_version=data_version)

    return jsonify({
        'success': True,
        'data': result
    })


@m06_bp.route('/m04/sensitivity/report', methods=['GET'])
@handle_api_errors
def get_m04_report():
    """
    获取Module04敏感度分析详细报告

    Query Parameters:
        - data_version: 数据版本，默认v1
        - include_pairwise: 是否包含成对检验详情，默认false

    Response:
        {
            "success": true,
            "data": {
                "report": {...},
                "timestamp": "2025-10-10T12:00:00",
                "cached": true/false
            }
        }
    """
    data_version = request.args.get('data_version', default='v1', type=str)
    include_pairwise = request.args.get('include_pairwise', default='false', type=str).lower() == 'true'

    service = get_service()
    result = service.get_m04_report(
        data_version=data_version,
        include_pairwise=include_pairwise
    )

    return jsonify({
        'success': True,
        'data': result
    })


# ============================
# Module05 敏感度分析 API
# ============================

@m06_bp.route('/m05/sensitivity/compute', methods=['POST'])
@handle_api_errors
def compute_m05_sensitivity():
    """
    触发Module05 RQA敏感度分析计算（异步任务）

    Request Body:
        {
            "groups": ["control", "mci", "ad"],  // 可选
            "top_k_params": 10  // 选择Top-K参数组合，默认10
        }

    Response:
        {
            "success": true,
            "task_id": "m05_sensitivity_20251010_120000",
            "message": "Module05敏感度分析任务已提交",
            "estimated_time_minutes": 15
        }
    """
    data = request.get_json() or {}

    groups = data.get('groups', ['control', 'mci', 'ad'])
    top_k_params = data.get('top_k_params', 10)

    service = get_service()
    result = service.compute_m05_sensitivity(
        groups=groups,
        top_k_params=top_k_params
    )

    return jsonify({
        'success': True,
        'task_id': result['task_id'],
        'message': result['message'],
        'estimated_time_minutes': result.get('estimated_time_minutes', 15)
    })


@m06_bp.route('/m05/sensitivity/top-k', methods=['GET'])
@handle_api_errors
def get_m05_top_k():
    """
    获取Module05 Top-K敏感RQA特征

    Query Parameters:
        - k: 选择的RQA特征数量，默认6
        - mode: 聚合模式 (cross_param/single_param)，默认cross_param

    Response:
        {
            "success": true,
            "data": {
                "top_k_features": [
                    {"feature": "RR-2D-xy", "avg_score": 0.85, ...},
                    ...
                ],
                "k": 6,
                "mode": "cross_param"
            }
        }
    """
    k = request.args.get('k', default=6, type=int)
    mode = request.args.get('mode', default='cross_param', type=str)

    service = get_service()
    result = service.get_m05_top_k(k=k, mode=mode)

    return jsonify({
        'success': True,
        'data': result
    })


@m06_bp.route('/m05/sensitivity/status', methods=['GET'])
@handle_api_errors
def get_m05_sensitivity_status():
    """
    查询Module05敏感度分析任务状态

    Query Parameters:
        - task_id: 任务ID (可选，不提供则返回最新任务状态)

    Response:
        {
            "success": true,
            "data": {
                "task_id": "m05_sensitivity_20251010_120000",
                "status": "completed/running/failed",
                "progress": 85,
                "message": "...",
                "result_available": true/false
            }
        }
    """
    task_id = request.args.get('task_id')

    service = get_service()
    result = service.get_m05_sensitivity_status(task_id=task_id)

    return jsonify({
        'success': True,
        'data': result
    })


# ============================
# 特征提取 API
# ============================

@m06_bp.route('/extract/single', methods=['POST'])
@validate_params('subject_id', 'group')
@handle_api_errors
def extract_single_subject():
    """
    提取单个受试者的特征向量

    Request Body:
        {
            "subject_id": "control_legacy_1",
            "group": "control",
            "data_version": "v1",
            "strategy": "A"  // A (Top-10) or B (Top-69)
        }

    Response:
        {
            "success": true,
            "data": {
                "subject_id": "control_legacy_1",
                "group": "control",
                "features": {...},  // 特征向量
                "strategy": "A",
                "dimension": 10
            }
        }
    """
    data = request.get_json()

    subject_id = data.get('subject_id')
    group = data.get('group')
    data_version = data.get('data_version', 'v1')
    strategy = data.get('strategy', 'A')

    service = get_service()
    result = service.extract_single_subject(
        subject_id=subject_id,
        group=group,
        data_version=data_version,
        strategy=strategy
    )

    return jsonify({
        'success': True,
        'data': result
    })


@m06_bp.route('/extract/batch', methods=['POST'])
@handle_api_errors
def extract_batch():
    """
    批量提取特征向量

    Request Body:
        {
            "groups": ["control", "mci", "ad"],  // 可选
            "data_version": "v1",
            "strategy": "A",
            "export_format": "csv"  // csv/json
        }

    Response:
        {
            "success": true,
            "data": {
                "total_subjects": 60,
                "features_extracted": 300,  // 60 subjects × 5 tasks
                "export_path": "data/06_features/extracted/...",
                "strategy": "A",
                "dimension": 10
            }
        }
    """
    data = request.get_json() or {}

    groups = data.get('groups')
    data_version = data.get('data_version', 'v1')
    strategy = data.get('strategy', 'A')
    export_format = data.get('export_format', 'csv')

    service = get_service()
    result = service.extract_batch(
        groups=groups,
        data_version=data_version,
        strategy=strategy,
        export_format=export_format
    )

    return jsonify({
        'success': True,
        'data': result
    })


@m06_bp.route('/features/summary', methods=['GET'])
@handle_api_errors
def get_features_summary():
    """
    获取特征提取统计摘要

    Query Parameters:
        - strategy: 策略 (A/B)，默认A

    Response:
        {
            "success": true,
            "data": {
                "strategy": "A",
                "selected_features": {
                    "m04": ["avg_fixation_duration", ...],
                    "m05": ["RR-2D-xy", ...]
                },
                "dimension": 10,
                "sample_count": 300,
                "sample_ratio": 30.0
            }
        }
    """
    strategy = request.args.get('strategy', default='A', type=str)

    service = get_service()
    result = service.get_features_summary(strategy=strategy)

    return jsonify({
        'success': True,
        'data': result
    })


# ============================
# 缓存管理 API
# ============================

@m06_bp.route('/cache/clear', methods=['POST'])
@handle_api_errors
def clear_cache():
    """
    清除缓存的敏感度分析结果

    Request Body:
        {
            "module": "m04"  // m04/m05/all
        }

    Response:
        {
            "success": true,
            "message": "缓存已清除",
            "cleared_files": [...]
        }
    """
    data = request.get_json() or {}
    module = data.get('module', 'all')

    service = get_service()
    result = service.clear_cache(module=module)

    return jsonify({
        'success': True,
        'message': result['message'],
        'cleared_files': result.get('cleared_files', [])
    })


# ============================
# 混合特征选择 API
# ============================

@m06_bp.route('/hybrid/run', methods=['POST'])
@handle_api_errors
def run_hybrid_selection():
    """
    运行混合特征选择（三阶段）

    Request Body:
        {
            "data_version": "v1",
            "mode": "fast",  // 'fast' (阶段1+2, ~2分钟) or 'precise' (完整三阶段, ~10分钟)
            "groups": ["control", "mci", "ad"]  // 可选
        }

    Response:
        {
            "success": true,
            "data": {
                "mode": "fast",
                "data_version": "v1",
                "sample_count": 300,
                "initial_feature_count": 27,
                "stage1_filter": {
                    "top_features": [...],
                    "execution_time": 60.5
                },
                "stage2_validation": {
                    "filtered_features": [...],
                    "execution_time": 30.2
                },
                "stage3_wrapper": {
                    "final_features": [...],
                    "best_method": "RFE",
                    "execution_time": 600.5
                },
                "final_features": [...],
                "baseline_comparison": {
                    "baseline_method": "ANOVA",
                    "baseline_r2_mean": 0.45,
                    "hybrid_r2_mean": 0.52,
                    "improvement": {
                        "absolute": 0.07,
                        "relative_pct": 15.6
                    }
                },
                "total_execution_time": 690.8,
                "timestamp": "2025-10-12T..."
            }
        }
    """
    data = request.get_json() or {}

    data_version = data.get('data_version', 'v1')
    mode = data.get('mode', 'fast')
    groups = data.get('groups')

    service = get_service()
    result = service.compute_hybrid_selection(
        data_version=data_version,
        mode=mode,
        groups=groups
    )

    return jsonify({
        'success': True,
        'data': result
    })


@m06_bp.route('/hybrid/compare', methods=['GET'])
@handle_api_errors
def compare_methods():
    """
    对比不同特征选择方法（ANOVA vs Hybrid）

    Query Parameters:
        - data_version: 数据版本，默认v1
        - mode: 混合模式 (fast/precise)，默认fast

    Response:
        {
            "success": true,
            "data": {
                "baseline": {
                    "method": "ANOVA",
                    "features": [...],
                    "r2_mean": 0.45,
                    "r2_std": 0.08
                },
                "hybrid": {
                    "method": "Hybrid (Filter+Validation+Wrapper)",
                    "features": [...],
                    "r2_mean": 0.52,
                    "r2_std": 0.07
                },
                "improvement": {
                    "absolute": 0.07,
                    "relative_pct": 15.6
                }
            }
        }
    """
    data_version = request.args.get('data_version', default='v1', type=str)
    mode = request.args.get('mode', default='fast', type=str)

    service = get_service()

    # 从缓存加载混合特征选择结果
    import json
    from pathlib import Path

    cache_file = service.cache_dir / f'hybrid_selection_{mode}_{data_version}.json'

    if not cache_file.exists():
        return jsonify({
            'success': False,
            'error': f'混合特征选择结果不存在。请先调用 POST /api/m06/hybrid/run',
            'hint': f'curl -X POST http://127.0.0.1:9090/api/m06/hybrid/run -H "Content-Type: application/json" -d \'{{"mode":"{mode}","data_version":"{data_version}"}}\''
        }), 404

    with open(cache_file, 'r', encoding='utf-8') as f:
        hybrid_report = json.load(f)

    baseline_comparison = hybrid_report.get('baseline_comparison', {})

    return jsonify({
        'success': True,
        'data': {
            'baseline': {
                'method': baseline_comparison.get('baseline_method', 'ANOVA'),
                'features': baseline_comparison.get('baseline_features', []),
                'r2_mean': baseline_comparison.get('baseline_r2_mean', 0.0),
                'r2_std': baseline_comparison.get('baseline_r2_std', 0.0)
            },
            'hybrid': {
                'method': 'Hybrid (Filter+Validation+Wrapper)',
                'features': baseline_comparison.get('hybrid_features', []),
                'r2_mean': baseline_comparison.get('hybrid_r2_mean', 0.0),
                'r2_std': baseline_comparison.get('hybrid_r2_std', 0.0)
            },
            'improvement': baseline_comparison.get('improvement', {}),
            'mode': mode,
            'data_version': data_version,
            'timestamp': hybrid_report.get('timestamp')
        }
    })
