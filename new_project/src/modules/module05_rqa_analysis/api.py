"""
Module05 RQA分析API
"""

from flask import Blueprint, request, jsonify, send_file
import base64
from pathlib import Path

from src.utils.logger import setup_logger
from .service import RQAAnalysisService
from .utils import handle_api_errors, validate_params, monitor_performance, validate_rqa_params
from .task_executor import RQATaskExecutor
from datetime import datetime

logger = setup_logger(__name__)

m05_bp = Blueprint('m05', __name__, url_prefix='/api/m05')

# Service单例实例（懒加载）
_service_instance = None

# TaskExecutor单例实例（懒加载）
_task_executor = None


def get_service() -> RQAAnalysisService:
    """
    获取RQAAnalysisService单例实例（懒加载模式）

    Returns:
        RQAAnalysisService: Service实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = RQAAnalysisService()
        logger.info("RQAAnalysisService initialized (lazy loading)")
    return _service_instance


def get_task_executor() -> RQATaskExecutor:
    """
    获取RQATaskExecutor单例实例（懒加载模式）

    Returns:
        RQATaskExecutor: TaskExecutor实例
    """
    global _task_executor
    if _task_executor is None:
        _task_executor = RQATaskExecutor()
        logger.info("RQATaskExecutor initialized (lazy loading)")
    return _task_executor


@m05_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'module': 'module05_rqa_analysis'})


@m05_bp.route('/params/generate', methods=['POST'])
@validate_params('m_range', 'tau_range', 'eps_range', 'lmin_range')
@handle_api_errors
def generate_param_combinations():
    """
    生成参数组合空间

    Request Body:
    {
        "m_range": {"start": 1, "end": 10, "step": 1},
        "tau_range": {"start": 1, "end": 10, "step": 1},
        "eps_range": {"start": 0.05, "end": 0.1, "step": 0.001},
        "lmin_range": {"start": 2, "end": 3, "step": 1},
        "data_version": "v1"  // 可选，默认v1
    }

    Response:
    {
        "success": true,
        "total_combinations": 10200,
        "combinations": [...],
        "estimated_time_minutes": 340,
        "data_version": "v1"
    }
    """
    data = request.get_json()

    service = get_service()
    result = service.generate_param_combinations(
        m_range=data['m_range'],
        tau_range=data['tau_range'],
        eps_range=data['eps_range'],
        lmin_range=data['lmin_range'],
        data_version=data.get('data_version', 'v1')
    )

    return jsonify(result)


@m05_bp.route('/params/history', methods=['GET'])
@handle_api_errors
def get_param_history():
    """
    获取参数历史记录和缓存的参数组合

    Response:
    {
        "success": true,
        "history": [...],
        "combinations": [...],  // 用于批量执行
        "data_version": "v1"
    }
    """
    service = get_service()
    history = service.get_param_history()

    # 读取缓存的参数组合
    cached_params = service.get_cached_param_combinations()

    return jsonify({
        'success': True,
        'history': history,
        'combinations': cached_params.get('combinations', []),
        'data_version': cached_params.get('data_version', 'v1'),
        'total_combinations': cached_params.get('total_combinations', 0)
    })


@m05_bp.route('/analyze/single', methods=['POST'])
@validate_params('params')
@handle_api_errors
def analyze_single():
    """
    分析单个参数组合（执行Step 1和Step 2）

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "groups": ["control", "mci", "ad"]
    }

    Response:
    {
        "success": true,
        "step1_result": {...},
        "step2_result": {...}
    }
    """
    data = request.get_json()
    params = data['params']
    groups = data.get('groups', ['control', 'mci', 'ad'])

    # 验证参数
    valid, error_msg = validate_rqa_params(params)
    if not valid:
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400

    service = get_service()

    # Step 1: RQA计算
    step1_result = service.step1_rqa_calculation(params, groups)
    if not step1_result['success']:
        return jsonify(step1_result), 500

    # Step 2: 数据合并
    step2_result = service.step2_data_merging(params, groups)
    if not step2_result['success']:
        return jsonify(step2_result), 500

    # Step 3: 特征增强
    step3_result = service.step3_feature_enrichment(params)
    if not step3_result['success']:
        logger.warning(f"Step 3失败: {step3_result.get('error')}")

    # Step 4: 统计分析
    step4_result = service.step4_statistical_analysis(params)
    if not step4_result['success']:
        logger.warning(f"Step 4失败: {step4_result.get('error')}")

    # Step 5: 可视化
    step5_result = service.step5_visualization(params)
    if not step5_result['success']:
        logger.warning(f"Step 5失败: {step5_result.get('error')}")

    return jsonify({
        'success': True,
        'step1_result': step1_result,
        'step2_result': step2_result,
        'step3_result': step3_result,
        'step4_result': step4_result,
        'step5_result': step5_result
    })


@m05_bp.route('/analyze/batch', methods=['POST'])
@handle_api_errors
@monitor_performance
def analyze_batch():
    """
    批量RQA分析（多个参数组合）

    注意：这是同步版本，适合小批量测试
    大规模批量分析需要异步任务队列（Week 2实现）

    Request Body:
    {
        "param_combinations": [
            {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
            {"m": 2, "tau": 1, "eps": 0.051, "lmin": 2},
            ...
        ],
        "groups": ["control", "mci", "ad"],
        "max_combinations": 10  // 限制最多处理的组合数
    }

    Response:
    {
        "success": true,
        "total_combinations": 10,
        "completed": 10,
        "failed": 0,
        "results": [...]
    }
    """
    data = request.get_json()
    param_combinations = data.get('param_combinations', [])
    groups = data.get('groups', ['control', 'mci', 'ad'])
    max_combinations = data.get('max_combinations', 10)

    # 限制批量数量（避免超时）
    if len(param_combinations) > max_combinations:
        return jsonify({
            'success': False,
            'error': f'参数组合数量超过限制（最多{max_combinations}个）'
        }), 400

    service = get_service()
    results = []
    completed = 0
    failed = 0

    for params in param_combinations:
        try:
            # 验证参数
            valid, error_msg = validate_rqa_params(params)
            if not valid:
                logger.warning(f"参数无效: {params} - {error_msg}")
                failed += 1
                continue

            # Step 1: RQA计算
            step1_result = service.step1_rqa_calculation(params, groups)
            if not step1_result['success']:
                failed += 1
                continue

            # Step 2: 数据合并
            step2_result = service.step2_data_merging(params, groups)
            if not step2_result['success']:
                failed += 1
                continue

            # Step 3: 特征增强
            step3_result = service.step3_feature_enrichment(params)
            if not step3_result['success']:
                logger.warning(f"Step 3失败: {step3_result.get('error')}")

            # Step 4: 统计分析
            step4_result = service.step4_statistical_analysis(params)
            if not step4_result['success']:
                logger.warning(f"Step 4失败: {step4_result.get('error')}")

            # Step 5: 可视化
            step5_result = service.step5_visualization(params)
            if not step5_result['success']:
                logger.warning(f"Step 5失败: {step5_result.get('error')}")

            results.append({
                'params': params,
                'step1_result': step1_result,
                'step2_result': step2_result,
                'step3_result': step3_result,
                'step4_result': step4_result,
                'step5_result': step5_result
            })
            completed += 1

        except Exception as e:
            logger.error(f"处理参数组合失败: {params} - {e}")
            failed += 1

    return jsonify({
        'success': True,
        'total_combinations': len(param_combinations),
        'completed': completed,
        'failed': failed,
        'results': results
    })


@m05_bp.route('/results/list', methods=['GET'])
@handle_api_errors
def list_results():
    """
    列出所有分析结果

    Query Parameters:
        - signature: 参数签名（可选，用于过滤）

    Response:
    {
        "success": true,
        "results": [
            {
                "signature": "m2_tau1_eps0.05_lmin2",
                "params": {...},
                "completed_steps": 2,
                "files": {
                    "step1_control": "...",
                    "step1_mci": "...",
                    "step2_merged": "..."
                }
            },
            ...
        ]
    }
    """
    signature = request.args.get('signature')

    service = get_service()
    history = service.get_param_history()

    # 过滤
    if signature:
        history = [h for h in history if h['signature'] == signature]

    return jsonify({
        'success': True,
        'results': history
    })


@m05_bp.route('/visualize/recurrence-plot', methods=['POST'])
@validate_params('subject_id', 'task_id', 'params')
@handle_api_errors
def generate_recurrence_plot():
    """
    生成递归图

    Request Body:
    {
        "subject_id": "control_legacy_1",
        "task_id": "q1",
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "mode": "1d"  // '1d' or '2d'
    }

    Response:
    {
        "success": true,
        "plot_base64": "iVBORw0KGgoAAAANSUh...",
        "metrics": {
            "RR": 0.234,
            "DET": 0.876,
            "ENT": 2.345
        }
    }
    """
    data = request.get_json()
    subject_id = data['subject_id']
    task_id = data['task_id']
    params = data['params']
    mode = data.get('mode', '1d')

    # 验证参数
    valid, error_msg = validate_rqa_params(params)
    if not valid:
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400

    service = get_service()

    # 查找CSV文件
    # 格式: {group}/{subject_id}_{task_id}_calibrated.csv
    # 需要从subject_id推断group
    group = None
    if subject_id.startswith('control'):
        group = 'control'
    elif subject_id.startswith('mci'):
        group = 'mci'
    elif subject_id.startswith('ad'):
        group = 'ad'

    if not group:
        return jsonify({
            'success': False,
            'error': f'无法从subject_id推断分组: {subject_id}'
        }), 400

    csv_file = service.processed_dir / group / f'{subject_id}_{task_id}_calibrated.csv'

    if not csv_file.exists():
        return jsonify({
            'success': False,
            'error': f'文件不存在: {csv_file}'
        }), 404

    # 分析并生成递归图
    from .rqa_analyzer import RQAAnalyzer
    import pandas as pd

    analyzer = RQAAnalyzer()

    # 加载数据
    df = pd.read_csv(csv_file)
    x = df['x'].values if 'x' in df.columns else df['GazePointX_normalized'].values
    y = df['y'].values if 'y' in df.columns else df['GazePointY_normalized'].values

    # 嵌入
    m = params['m']
    tau = params['tau']
    eps = params['eps']
    lmin = params['lmin']

    if mode == '1d':
        embedded = analyzer.embed_signal_1d(x, m, tau)
        metric = '1d_abs'
    else:
        embedded = analyzer.embed_signal_2d(x, y, m, tau)
        metric = 'euclidean'

    # 计算递归矩阵
    rp = analyzer.compute_recurrence_matrix(embedded, eps, metric)

    # 计算指标
    metrics = analyzer.compute_rqa_metrics(rp, lmin)

    # 生成递归图
    plot_bytes = analyzer.create_recurrence_plot(
        rp,
        title=f'Recurrence Plot - {subject_id} {task_id} ({mode.upper()})'
    )
    plot_base64 = base64.b64encode(plot_bytes).decode('utf-8')

    return jsonify({
        'success': True,
        'plot_base64': plot_base64,
        'metrics': metrics,
        'embedding_info': {
            'original_length': len(x),
            'embedded_length': embedded.shape[0],
            'embedding_dim': embedded.shape[1]
        }
    })


# ========== 异步任务API ==========

@m05_bp.route('/tasks/submit', methods=['POST'])
@validate_params('param_combinations')
@handle_api_errors
def submit_async_task():
    """
    提交异步批量RQA任务

    Request Body:
    {
        "param_combinations": [
            {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
            {"m": 2, "tau": 1, "eps": 0.051, "lmin": 2},
            ...
        ],
        "groups": ["control", "mci", "ad"]
    }

    Response:
    {
        "success": true,
        "task_id": "task_20250610_143025_abc123",
        "total_files": 933,
        "message": "任务已提交到后台执行"
    }
    """
    data = request.get_json()
    param_combinations = data['param_combinations']
    groups = data.get('groups', ['control', 'mci', 'ad'])

    # 验证参数
    for params in param_combinations:
        valid, error_msg = validate_rqa_params(params)
        if not valid:
            return jsonify({
                'success': False,
                'error': f'参数无效: {params} - {error_msg}'
            }), 400

    # 生成任务ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 获取executor和service
    executor = get_task_executor()
    service = get_service()

    # 提交任务
    executor.submit_batch_task(
        task_id=task_id,
        service=service,
        param_combinations=param_combinations,
        groups=groups
    )

    # 获取初始状态
    status = executor.get_task_status(task_id)

    return jsonify({
        'success': True,
        'task_id': task_id,
        'total_files': status['total_files'],
        'message': '任务已提交到后台执行'
    })


@m05_bp.route('/tasks/status/<task_id>', methods=['GET'])
@handle_api_errors
def get_task_status(task_id):
    """
    获取任务状态

    Response:
    {
        "success": true,
        "task": {
            "task_id": "task_20250610_143025",
            "status": "running",
            "progress": 45.2,
            "processed_files": 421,
            "total_files": 933,
            "current_step": 1,
            "eta_seconds": 120,
            ...
        }
    }
    """
    executor = get_task_executor()
    status = executor.get_task_status(task_id)

    if status is None:
        return jsonify({
            'success': False,
            'error': f'任务不存在: {task_id}'
        }), 404

    return jsonify({
        'success': True,
        'task': status
    })


@m05_bp.route('/tasks/list', methods=['GET'])
@handle_api_errors
def list_tasks():
    """
    列出所有任务

    Response:
    {
        "success": true,
        "tasks": [...]
    }
    """
    executor = get_task_executor()
    tasks = executor.get_all_tasks()

    return jsonify({
        'success': True,
        'tasks': tasks
    })


@m05_bp.route('/tasks/cancel/<task_id>', methods=['POST'])
@handle_api_errors
def cancel_task(task_id):
    """
    取消任务

    Response:
    {
        "success": true,
        "message": "任务已取消"
    }
    """
    executor = get_task_executor()
    cancelled = executor.cancel_task(task_id)

    if not cancelled:
        return jsonify({
            'success': False,
            'error': f'无法取消任务: {task_id}'
        }), 400

    return jsonify({
        'success': True,
        'message': '任务已取消'
    })


@m05_bp.route('/tasks/pause/<task_id>', methods=['POST'])
@handle_api_errors
def pause_task(task_id):
    """
    暂停任务

    Response:
    {
        "success": true,
        "message": "任务已暂停"
    }
    """
    executor = get_task_executor()
    paused = executor.pause_task(task_id)

    if not paused:
        return jsonify({
            'success': False,
            'error': f'无法暂停任务: {task_id}'
        }), 400

    return jsonify({
        'success': True,
        'message': '任务已暂停'
    })


@m05_bp.route('/tasks/resume/<task_id>', methods=['POST'])
@handle_api_errors
def resume_task(task_id):
    """
    恢复任务

    Response:
    {
        "success": true,
        "message": "任务已恢复"
    }
    """
    executor = get_task_executor()
    service = get_service()
    resumed = executor.resume_task(task_id, service)

    if not resumed:
        return jsonify({
            'success': False,
            'error': f'无法恢复任务: {task_id}'
        }), 400

    return jsonify({
        'success': True,
        'message': '任务已恢复'
    })


@m05_bp.route('/visualizations/<signature>/<filename>', methods=['GET'])
@handle_api_errors
def get_visualization(signature, filename):
    """
    获取可视化图片文件

    路径: /api/m05/visualizations/{signature}/{filename}

    例如: /api/m05/visualizations/m2_tau1_eps0.05_lmin2/rqa_metrics_boxplot.png

    Response: 图片文件 (PNG格式)
    """
    service = get_service()

    # 构建文件路径
    # data/05_rqa_analysis/results/{signature}/step5_visualization/statistical_plots/{filename}
    visualization_dir = service.results_dir / signature / 'step5_visualization' / 'statistical_plots'
    file_path = visualization_dir / filename

    if not file_path.exists():
        return jsonify({
            'success': False,
            'error': f'可视化文件不存在: {signature}/{filename}'
        }), 404

    # 返回图片文件
    return send_file(
        str(file_path),
        mimetype='image/png',
        as_attachment=False
    )


@m05_bp.route('/results/completed', methods=['GET'])
@handle_api_errors
def get_completed_results():
    """
    获取已完成的RQA分析结果列表

    Query Parameters:
        - task_id: 批次ID (可选，筛选指定批次的结果)

    Response:
    {
        "success": true,
        "completed_results": [
            {"m": 1, "tau": 1, "eps": 0.05, "lmin": 2, "task_id": "...", ...},
            ...
        ],
        "total_count": 704
    }
    """
    service = get_service()
    task_id = request.args.get('task_id')

    completed_results = service.scan_completed_results(task_id=task_id)

    return jsonify({
        'success': True,
        'completed_results': completed_results,
        'total_count': len(completed_results)
    })


@m05_bp.route('/batches/list', methods=['GET'])
@handle_api_errors
def get_batch_list():
    """
    获取批次列表

    Response:
    {
        "success": true,
        "batches": [
            {
                "task_id": "task_20251008_163415",
                "batch_time": "2025-10-08T16:34:15",
                "data_version": "v1",
                "param_count": 704,
                "display_name": "2025-10-08 16:34:15 (V1数据, 704个参数)"
            },
            ...
        ],
        "total_count": 10
    }
    """
    service = get_service()
    batches = service.get_batch_list()

    return jsonify({
        'success': True,
        'batches': batches,
        'total_count': len(batches)
    })


# ========== 高级分析API (新增) ==========

@m05_bp.route('/advanced/evaluate-params', methods=['POST'])
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
    from pathlib import Path

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


@m05_bp.route('/advanced/task-analysis', methods=['POST'])
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
    from config.settings import get_config

    data = request.get_json()
    params = data['params']
    task_id = data['task_id']
    groups = data.get('groups', ['control', 'mci', 'ad'])

    from config.settings import Config
    from pathlib import Path

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


@m05_bp.route('/advanced/task-compare', methods=['POST'])
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
    from config.settings import get_config

    data = request.get_json()
    params = data['params']
    tasks = data['tasks']

    from config.settings import Config
    from pathlib import Path

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = TaskAnalyzer(results_dir)
    comparison = analyzer.compare_tasks(params, tasks)

    return jsonify({
        'success': True,
        'comparison': comparison
    })


# ========== 个体查询API (新增) ==========

@m05_bp.route('/advanced/subjects/list', methods=['POST'])
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
    from config.settings import get_config

    data = request.get_json()
    params = data['params']

    from config.settings import Config
    from pathlib import Path

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    subjects = analyzer.get_all_subjects(params)

    return jsonify({
        'success': True,
        'subjects': subjects,
        'total_count': len(subjects)
    })


@m05_bp.route('/advanced/individual/profile', methods=['POST'])
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
    from config.settings import get_config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    from config.settings import Config
    from pathlib import Path

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    profile = analyzer.get_individual_profile(subject_id, params)

    return jsonify({
        'success': True,
        'profile': profile
    })


@m05_bp.route('/advanced/individual/compare-to-group', methods=['POST'])
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
    from config.settings import get_config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    from config.settings import Config
    from pathlib import Path

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    comparison = analyzer.compare_to_group(subject_id, params)

    return jsonify({
        'success': True,
        'comparison': comparison
    })


@m05_bp.route('/advanced/individual/risk-assessment', methods=['POST'])
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
    from config.settings import get_config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    from config.settings import Config
    from pathlib import Path

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    assessment = analyzer.assess_cognitive_risk(subject_id, params)

    return jsonify({
        'success': True,
        'assessment': assessment
    })


@m05_bp.route('/advanced/individual/task-progression', methods=['POST'])
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
    from config.settings import get_config

    data = request.get_json()
    subject_id = data['subject_id']
    params = data['params']

    from config.settings import Config
    from pathlib import Path

    data_root = Path(Config.DATA_ROOT)
    results_dir = data_root / '05_rqa_analysis' / 'results'

    analyzer = IndividualAnalyzer(results_dir)
    progression = analyzer.get_task_progression_analysis(subject_id, params)

    return jsonify({
        'success': True,
        'progression': progression
    })
