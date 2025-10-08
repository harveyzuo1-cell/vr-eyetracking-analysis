"""
Module05 RQA分析API
"""

from flask import Blueprint, request, jsonify
import base64

from src.utils.logger import setup_logger
from .service import RQAAnalysisService
from .utils import handle_api_errors, validate_params, monitor_performance, validate_rqa_params

logger = setup_logger(__name__)

m05_bp = Blueprint('m05', __name__, url_prefix='/api/m05')

# Service单例实例（懒加载）
_service_instance = None


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
        "lmin_range": {"start": 2, "end": 3, "step": 1}
    }

    Response:
    {
        "success": true,
        "total_combinations": 10200,
        "combinations": [...],
        "estimated_time_minutes": 340
    }
    """
    data = request.get_json()

    service = get_service()
    result = service.generate_param_combinations(
        m_range=data['m_range'],
        tau_range=data['tau_range'],
        eps_range=data['eps_range'],
        lmin_range=data['lmin_range']
    )

    return jsonify(result)


@m05_bp.route('/params/history', methods=['GET'])
@handle_api_errors
def get_param_history():
    """
    获取参数历史记录

    Response:
    {
        "success": true,
        "history": [
            {
                "signature": "m2_tau1_eps0.05_lmin2",
                "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
                "completed_steps": 2,
                "progress": 40.0,
                "last_updated": "2025-10-07T15:30:45"
            },
            ...
        ]
    }
    """
    service = get_service()
    history = service.get_param_history()

    return jsonify({
        'success': True,
        'history': history
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

    return jsonify({
        'success': True,
        'step1_result': step1_result,
        'step2_result': step2_result
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

            results.append({
                'params': params,
                'step1_result': step1_result,
                'step2_result': step2_result
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
