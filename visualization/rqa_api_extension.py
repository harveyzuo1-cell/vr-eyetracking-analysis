"""
RQA递归量化分析API扩展模块
支持批量渲染、图片展示和筛选功能
"""

import os
import json
import base64
from flask import jsonify, request, send_file
from analysis.rqa_analyzer import create_rqa_analyzer
from analysis.rqa_batch_renderer import create_rqa_batch_renderer
import numpy as np

def add_rqa_routes(app, visualizer_instance):
    """添加RQA相关的API路由"""
    
    # 创建批量渲染器 - 修复路径问题，指向项目根目录的data文件夹
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_root = os.path.join(project_root, "data")
    batch_renderer = create_rqa_batch_renderer(data_root)
    
    @app.route('/api/rqa-analysis', methods=['POST'])
    def rqa_analysis():
        """执行RQA分析（保持向后兼容）"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "缺少请求数据"}), 400
            
            # 获取参数
            data_list = data.get('data_list', [])
            analysis_mode = data.get('analysis_mode', '1d_x')
            distance_metric = data.get('distance_metric', '1d_abs')
            embedding_dimension = int(data.get('embedding_dimension', 2))
            time_delay = int(data.get('time_delay', 1))
            recurrence_threshold = float(data.get('recurrence_threshold', 0.05))
            min_line_length = int(data.get('min_line_length', 2))
            
            if not data_list:
                return jsonify({"success": False, "message": "请选择要分析的数据"}), 400
            
            # 使用原有的RQA分析器
            analyzer = create_rqa_analyzer()
            
            # 分析参数
            analysis_params = {
                'analysis_mode': analysis_mode,
                'distance_metric': distance_metric,
                'embedding_dimension': embedding_dimension,
                'time_delay': time_delay,
                'recurrence_threshold': recurrence_threshold,
                'min_line_length': min_line_length
            }
            
            if len(data_list) == 1:
                # 单数据分析
                result = analyzer.analyze_data(data_list[0], analysis_params)
            else:
                # 多数据对比分析
                result = analyzer.compare_groups(data_list, analysis_params)
            
            if result is None:
                return jsonify({"success": False, "message": "RQA分析失败"}), 500
            
            return jsonify({
                "success": True,
                "data": result
            })
            
        except Exception as e:
            return jsonify({"success": False, "message": f"RQA分析出错: {str(e)}"}), 500
    
    @app.route('/api/rqa-comparison', methods=['POST'])
    def rqa_comparison():
        """RQA对比分析（保持向后兼容）"""
        return rqa_analysis()  # 复用相同逻辑
    
    @app.route('/api/rqa-parameters', methods=['GET'])
    def get_rqa_parameters():
        """获取RQA默认参数"""
        try:
            default_params = batch_renderer.default_params.copy()
            return jsonify({
                "success": True,
                "data": default_params
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"获取参数失败: {str(e)}"}), 500
    
    @app.route('/api/rqa-batch-render', methods=['POST'])
    def rqa_batch_render():
        """批量渲染RQA图"""
        try:
            data = request.get_json() or {}
            
            # 获取渲染参数
            params = {
                "analysis_mode": data.get('analysis_mode', '1d_x'),
                "distance_metric": data.get('distance_metric', '1d_abs'),
                "embedding_dimension": int(data.get('embedding_dimension', 2)),
                "time_delay": int(data.get('time_delay', 1)),
                "recurrence_threshold": float(data.get('recurrence_threshold', 0.05)),
                "min_line_length": int(data.get('min_line_length', 2))
            }
            
            color_theme = data.get('color_theme', 'grayscale')
            
            # 定义进度回调（可以通过WebSocket实现实时进度）
            progress_messages = []
            def progress_callback(progress, message):
                progress_messages.append(f"{progress:.1f}%: {message}")
            
            # 执行批量渲染
            result = batch_renderer.batch_render_all_groups(
                params=params,
                color_theme=color_theme,
                progress_callback=progress_callback
            )
            
            if result.get("success", False):
                return jsonify({
                    "success": True,
                    "data": {
                        "params": params,
                        "color_theme": color_theme,
                        "param_signature": result.get("param_signature", ""),
                        "progress_messages": progress_messages[-10:]  # 最后10条消息
                    },
                    "message": result.get("message", "渲染完成")
                })
            else:
                return jsonify({
                    "success": False,
                    "message": result.get("message", "渲染失败")
                }), 500
            
        except Exception as e:
            return jsonify({"success": False, "message": f"批量渲染失败: {str(e)}"}), 500
    
    @app.route('/api/rqa-rendered-results', methods=['GET'])
    def get_rqa_rendered_results():
        """获取已渲染的RQA结果"""
        try:
            # 获取筛选参数
            group_type = request.args.get('group', None)
            question = request.args.get('question', None)
            param_signature = request.args.get('param_signature', None)
            
            if question:
                question = int(question)
            
            # 获取渲染结果
            results = batch_renderer.get_rendered_results(group_type, question, param_signature)
            
            if not results:
                return jsonify({
                    "success": True,
                    "data": {
                        "results": [],
                        "layout_rows": [],
                        "param_combinations": []
                    },
                    "message": "尚未进行批量渲染"
                })
            
            # 按照要求的格式组织数据：一行5列，按组别排序
            organized_results = _organize_results_by_layout(results)
            
            # 获取所有可用的参数组合
            param_combinations = list(set([r.get('param_signature', '') for r in results if r.get('param_signature')]))
            
            return jsonify({
                "success": True,
                "data": {
                    "results": results,
                    "layout_rows": organized_results,
                    "param_combinations": param_combinations,
                    "total_count": len(results)
                }
            })
            
        except Exception as e:
            return jsonify({"success": False, "message": f"获取渲染结果失败: {str(e)}"}), 500
    
    @app.route('/api/rqa-image/<path:image_path>')
    def get_rqa_image(image_path):
        """获取RQA图片文件"""
        try:
            # 构建完整路径
            full_path = os.path.join(batch_renderer.rqa_results_dir, image_path)
            
            # 如果是旧的_rqa.png格式，重定向到amplitude图片
            if image_path.endswith('_rqa.png'):
                amplitude_path = image_path.replace('_rqa.png', '_amplitude.png')
                full_path = os.path.join(batch_renderer.rqa_results_dir, amplitude_path)
            
            if not os.path.exists(full_path):
                return jsonify({"success": False, "message": f"图片文件不存在: {image_path}"}), 404
            
            # 安全检查：确保路径在允许的目录内
            if not os.path.abspath(full_path).startswith(os.path.abspath(batch_renderer.rqa_results_dir)):
                return jsonify({"success": False, "message": "非法的文件路径"}), 403
            
            return send_file(full_path, mimetype='image/png')
            
        except Exception as e:
            app.logger.error(f"获取图片失败 {image_path}: {str(e)}")
            return jsonify({"success": False, "message": f"获取图片失败: {str(e)}"}), 500
    
    @app.route('/api/rqa-render-status', methods=['GET'])
    def get_rqa_render_status():
        """获取RQA渲染状态"""
        try:
            # 检查rqa_results目录是否存在参数化子目录
            if not os.path.exists(batch_renderer.rqa_results_dir):
                return jsonify({
                    "success": True,
                    "data": {
                        "rendered": False,
                        "message": "尚未进行批量渲染"
                    }
                })
            
            # 查找所有参数化目录
            param_dirs = []
            total_images = 0
            
            try:
                for item in os.listdir(batch_renderer.rqa_results_dir):
                    item_path = os.path.join(batch_renderer.rqa_results_dir, item)
                    if os.path.isdir(item_path) and item.startswith('mode_'):
                        # 读取该参数目录的索引文件
                        index_file = os.path.join(item_path, "render_index.json")
                        if os.path.exists(index_file):
                            with open(index_file, 'r', encoding='utf-8') as f:
                                index_data = json.load(f)
                            
                            param_dirs.append({
                                "param_signature": item,
                                "render_time": index_data.get("render_time"),
                                "params": index_data.get("params"),
                                "color_theme": index_data.get("color_theme"),
                                "results_summary": index_data.get("results_summary", {})
                            })
                            
                            # 统计图片数量
                            results_summary = index_data.get("results_summary", {})
                            if isinstance(results_summary, dict):
                                total_images += results_summary.get("total_images", 0)
                
                if not param_dirs:
                    return jsonify({
                        "success": True,
                        "data": {
                            "rendered": False,
                            "message": "尚未进行批量渲染"
                        }
                    })
                
                return jsonify({
                    "success": True,
                    "data": {
                        "rendered": True,
                        "total_images": total_images,
                        "param_combinations": len(param_dirs),
                        "param_dirs": param_dirs
                    }
                })
                
            except Exception as e:
                print(f"读取渲染状态时出错: {e}")
                return jsonify({
                    "success": True,
                    "data": {
                        "rendered": False,
                        "message": "渲染状态读取失败"
                    }
                })
            
        except Exception as e:
            return jsonify({"success": False, "message": f"获取渲染状态失败: {str(e)}"}), 500


def _organize_results_by_layout(results):
    """按照一行5列的布局组织结果"""
    organized = {
        "control": {},
        "mci": {},
        "ad": {}
    }
    
    # 按组别和问题组织
    for result in results:
        group = result["group"]
        question = result["question"]
        
        if question not in organized[group]:
            organized[group][question] = []
        
        # 直接使用结果中的三种图片路径
        organized[group][question].append({
            "data_id": result["data_id"],
            "amplitude_path": result.get("amplitude_path", result.get("relative_path", "")),
            "trajectory_path": result.get("trajectory_path", result.get("relative_path", "")),
            "recurrence_path": result.get("recurrence_path", result.get("relative_path", "")),
            "group": group,
            "question": question
        })
    
    # 转换为有序的布局格式
    layout_rows = []
    
    # 控制组
    for q in range(1, 6):
        if q in organized["control"]:
            row = {
                "group": "control",
                "question": q,
                "items": organized["control"][q]
            }
            layout_rows.append(row)
    
    # MCI组
    for q in range(1, 6):
        if q in organized["mci"]:
            row = {
                "group": "mci", 
                "question": q,
                "items": organized["mci"][q]
            }
            layout_rows.append(row)
    
    # AD组
    for q in range(1, 6):
        if q in organized["ad"]:
            row = {
                "group": "ad",
                "question": q, 
                "items": organized["ad"][q]
            }
            layout_rows.append(row)
    
    return layout_rows


def setup_rqa_integration(app, visualizer):
    """设置RQA功能集成"""
    try:
        add_rqa_routes(app, visualizer)
        print("✅ RQA功能已启用（含批量渲染）")
    except ImportError as e:
        print(f"⚠️  RQA功能不可用: {e}")


def extend_visualizer_for_rqa(visualizer_instance):
    """为可视化器扩展RQA功能"""
    def _find_data_file(data_id):
        """查找数据文件"""
        # 解析 data_id，例如: c1q1, m20q5, ad10q1
        import re
        match = re.match(r'^([a-z]+)(\d+)q(\d+)$', data_id)
        if not match:
            return None
            
        group_prefix = match.group(1)
        group_num = match.group(2)
        question_num = match.group(3)
        
        # 映射组别前缀到目录名
        if group_prefix == 'c':
            group_type = 'control'
            filename_prefix = 'n'
        elif group_prefix == 'm':
            group_type = 'mci'
            filename_prefix = 'm'
        elif group_prefix.startswith('ad'):
            group_type = 'ad'
            filename_prefix = 'ad'
        else:
            return None
        
        # 构建文件名
        if group_type == 'control':
            filename = f"n{group_num}q{question_num}_preprocessed_calibrated.csv"
        elif group_type == 'mci':
            filename = f"m{group_num}q{question_num}_preprocessed_calibrated.csv"
        else:  # ad
            filename = f"ad{group_num}q{question_num}_preprocessed_calibrated.csv"
        
        # 优先搜索 rqa_ready 目录
        for base_name in [f"{group_type}_rqa_ready", f"{group_type}_calibrated", f"{group_type}_processed"]:
            base_dir = os.path.join(visualizer_instance.data_root, base_name)
            if not os.path.exists(base_dir):
                continue
            
            # 查找包含该文件的子目录
            for subdir in os.listdir(base_dir):
                subdir_path = os.path.join(base_dir, subdir)
                if os.path.isdir(subdir_path):
                    file_path = os.path.join(subdir_path, filename)
                    if os.path.exists(file_path):
                        return file_path
        
        return None
    
    # 动态添加方法到可视化器实例
    visualizer_instance._find_data_file = _find_data_file 