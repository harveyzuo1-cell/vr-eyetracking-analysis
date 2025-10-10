"""临时脚本:添加sensitivity API端点到api.py"""

api_file = 'src/modules/module05_rqa_analysis/api.py'

sensitivity_code = """
# ============================================================================
# 参数敏感性分析API (Parameter Sensitivity Analysis)
# ============================================================================

@m05_bp.route('/sensitivity/scan-results', methods=['GET'])
@handle_api_errors
def scan_rqa_results() -> Response:
    \"\"\"
    扫描磁盘上所有RQA分析结果

    直接从data/05_rqa_analysis/results目录扫描,不依赖任务状态

    Returns:
        JSON response with list of parameter combinations and their enriched_features paths
    \"\"\"
    results_base_dir = Path('data/05_rqa_analysis/results')

    if not results_base_dir.exists():
        return jsonify({
            'success': False,
            'message': '结果目录不存在'
        }), 404

    results_by_params = []

    for param_dir in results_base_dir.iterdir():
        if not param_dir.is_dir():
            continue

        enriched_path = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'

        if enriched_path.exists():
            try:
                # Parse parameter directory name: m2_tau1_eps0.050_lmin2
                dir_name = param_dir.name
                parts = dir_name.split('_')
                params = {
                    'm': int(parts[0][1:]),
                    'tau': int(parts[1][3:]),
                    'eps': float(parts[2][3:]),
                    'lmin': int(parts[3][4:])
                }

                results_by_params.append({
                    'params': params,
                    'enriched_features_path': str(enriched_path),
                    'param_signature': dir_name
                })
            except (IndexError, ValueError) as e:
                logger.warning(f"无法解析参数目录名: {dir_name}, 错误: {e}")
                continue

    return jsonify({
        'success': True,
        'results': results_by_params,
        'total': len(results_by_params)
    })


@m05_bp.route('/sensitivity/compute-scores', methods=['POST'])
@handle_api_errors
def compute_sensitivity_scores() -> Response:
    \"\"\"
    计算参数敏感性评分

    使用磁盘扫描获取所有参数组合的RQA结果,计算敏感性评分

    Returns:
        JSON response with sensitivity scores
    \"\"\"
    # 扫描磁盘获取所有参数组合
    results_base_dir = Path('data/05_rqa_analysis/results')

    if not results_base_dir.exists():
        return jsonify({
            'success': False,
            'message': '结果目录不存在,请先运行RQA分析'
        }), 400

    results_by_params = []

    for param_dir in results_base_dir.iterdir():
        if not param_dir.is_dir():
            continue

        enriched_path = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'

        if enriched_path.exists():
            try:
                dir_name = param_dir.name
                parts = dir_name.split('_')
                params = {
                    'm': int(parts[0][1:]),
                    'tau': int(parts[1][3:]),
                    'eps': float(parts[2][3:]),
                    'lmin': int(parts[3][4:])
                }

                results_by_params.append({
                    'params': params,
                    'enriched_features_path': str(enriched_path)
                })
            except (IndexError, ValueError) as e:
                logger.warning(f"无法解析参数目录名: {dir_name}, 错误: {e}")
                continue

    if not results_by_params:
        return jsonify({
            'success': False,
            'message': '未找到可用的RQA分析结果'
        }), 400

    # 计算敏感性评分
    analyzer = get_sensitivity_analyzer()
    sensitivity_df = analyzer.compute_parameter_sensitivity_scores(results_by_params)

    return jsonify({
        'success': True,
        'sensitivity_scores': sensitivity_df.to_dict('records'),
        'total_params': len(sensitivity_df['param_signature'].unique()),
        'total_features': len(sensitivity_df['feature'].unique())
    })


@m05_bp.route('/sensitivity/plot-3d-space', methods=['POST'])
@handle_api_errors
def plot_3d_parameter_space() -> Response:
    \"\"\"
    生成3D参数空间图
    \"\"\"
    data = request.get_json()
    feature = data['feature']
    x_param = data.get('x_param', 'm')
    y_param = data.get('y_param', 'tau')
    z_metric = data.get('z_metric', 'f_statistic')
    color_param = data.get('color_param', 'eps')

    # 先计算敏感性评分
    results_base_dir = Path('data/05_rqa_analysis/results')
    results_by_params = []

    for param_dir in results_base_dir.iterdir():
        if not param_dir.is_dir():
            continue
        enriched_path = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'
        if enriched_path.exists():
            try:
                dir_name = param_dir.name
                parts = dir_name.split('_')
                params = {
                    'm': int(parts[0][1:]),
                    'tau': int(parts[1][3:]),
                    'eps': float(parts[2][3:]),
                    'lmin': int(parts[3][4:])
                }
                results_by_params.append({
                    'params': params,
                    'enriched_features_path': str(enriched_path)
                })
            except (IndexError, ValueError):
                continue

    analyzer = get_sensitivity_analyzer()
    sensitivity_df = analyzer.compute_parameter_sensitivity_scores(results_by_params)

    # 生成3D图
    output_dir = Path('data/05_rqa_analysis/sensitivity_plots')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'3d_space_{feature}.html'

    analyzer.plot_3d_parameter_space(
        sensitivity_df,
        feature,
        output_path,
        x_param,
        y_param,
        z_metric,
        color_param
    )

    return jsonify({
        'success': True,
        'html_path': f'/api/m05/sensitivity/html/{output_path.name}'
    })


@m05_bp.route('/sensitivity/plot-heatmap', methods=['POST'])
@handle_api_errors
def plot_parameter_heatmap() -> Response:
    \"\"\"
    生成参数-特征敏感性热图
    \"\"\"
    data = request.get_json()
    metric = data.get('metric', 'overall_score')

    # 计算敏感性评分
    results_base_dir = Path('data/05_rqa_analysis/results')
    results_by_params = []

    for param_dir in results_base_dir.iterdir():
        if not param_dir.is_dir():
            continue
        enriched_path = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'
        if enriched_path.exists():
            try:
                dir_name = param_dir.name
                parts = dir_name.split('_')
                params = {
                    'm': int(parts[0][1:]),
                    'tau': int(parts[1][3:]),
                    'eps': float(parts[2][3:]),
                    'lmin': int(parts[3][4:])
                }
                results_by_params.append({
                    'params': params,
                    'enriched_features_path': str(enriched_path)
                })
            except (IndexError, ValueError):
                continue

    analyzer = get_sensitivity_analyzer()
    sensitivity_df = analyzer.compute_parameter_sensitivity_scores(results_by_params)

    # 生成热图
    output_dir = Path('data/05_rqa_analysis/sensitivity_plots')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'heatmap_{metric}.html'

    analyzer.plot_parameter_heatmap(sensitivity_df, output_path, metric)

    return jsonify({
        'success': True,
        'html_path': f'/api/m05/sensitivity/html/{output_path.name}'
    })


@m05_bp.route('/sensitivity/html/<path:filename>', methods=['GET'])
def serve_sensitivity_html(filename: str) -> Response:
    \"\"\"
    提供敏感性分析HTML文件
    \"\"\"
    html_dir = Path('data/05_rqa_analysis/sensitivity_plots')
    file_path = html_dir / filename

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path, mimetype='text/html')
"""

# Append to file
with open(api_file, 'a', encoding='utf-8') as f:
    f.write(sensitivity_code)

print('Successfully added sensitivity API endpoints to api.py')
