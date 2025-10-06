# -*- coding: utf-8 -*-
"""
增强版VR眼动数据Web可视化器
提供更强大的可视化功能，包括ROI绘制、轨迹可视化、事件标记等
"""
import os
import sys
import json
import cv2
import math
import base64
import webbrowser
from io import BytesIO
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, jsonify, request, make_response
from typing import Dict, List, Optional, Tuple

# JSON序列化辅助函数
def convert_numpy_types(obj):
    """递归转换numpy数据类型为Python原生类型"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analysis.enhanced_eyetracking_analyzer import EnhancedEyetrackingAnalyzer

class EnhancedWebVisualizer:
    """增强版Web可视化器"""
    
    def __init__(self, config_file: str = "config/eyetracking_analysis_config.json"):
        """
        初始化增强版Web可视化器
        
        Args:
            config_file: 分析配置文件路径
        """
        self.analyzer = EnhancedEyetrackingAnalyzer(config_file)
        self.config = self.analyzer.config
        
        # Flask应用设置
        self.app = Flask(__name__, 
                        template_folder='templates', 
                        static_folder='static')
        self.setup_routes()
        
        # 初始化数据缓存
        self.group_data = {}
        self.background_images = []
        self.mmse_scores = {}  # 添加MMSE分数缓存
        
        # 加载背景图片和MMSE分数
        self._load_background_images()
        self._load_mmse_scores()  # 初始化时加载MMSE分数
        
        # 可视化设置 - 修复颜色配置合并问题
        self.visualization_config = self.config.get("visualization", {})
        
        # 正确合并颜色配置，确保ROI颜色不缺失
        default_colors = self.get_default_colors()
        config_colors = self.visualization_config.get("colors", {})
        self.colors = {**default_colors, **config_colors}
        
        # 正确合并尺寸配置
        default_sizes = self.get_default_sizes()
        config_sizes = self.visualization_config.get("sizes", {})
        self.sizes = {**default_sizes, **config_sizes}
        
        # 集成RQA分析功能
        try:
            # 尝试相对导入（用于包导入）
            try:
                from .rqa_api_extension import setup_rqa_integration
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from rqa_api_extension import setup_rqa_integration
            
            setup_rqa_integration(self.app, self)
            print("✅ RQA分析功能已启用")
        except ImportError as e:
            print(f"⚠️  RQA分析功能不可用: {e}")
        
        # 集成事件分析功能
        try:
            # 尝试相对导入（用于包导入）
            try:
                from .event_api_extension import setup_event_analysis_integration
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from event_api_extension import setup_event_analysis_integration
            
            setup_event_analysis_integration(self.app, self)
            print("✅ 事件分析功能已启用")
        except ImportError as e:
            print(f"⚠️  事件分析功能不可用: {e}")
        
        # 集成MMSE对比分析功能
        try:
            # 尝试相对导入（用于包导入）
            try:
                from .mmse_api_extension import register_mmse_routes
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from mmse_api_extension import register_mmse_routes
            
            register_mmse_routes(self.app)
            print("✅ MMSE对比分析功能已启用")
        except ImportError as e:
            print(f"⚠️  MMSE对比分析功能不可用: {e}")
        
        # 集成真实数据整合功能
        try:
            # 尝试相对导入（用于包导入）
            try:
                from .real_data_integration_api import register_real_data_routes
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from real_data_integration_api import register_real_data_routes
            
            register_real_data_routes(self.app)
            print("✅ 真实数据整合功能已启用")
        except ImportError as e:
            print(f"⚠️  真实数据整合功能不可用: {e}")
        
        # 🆕 集成机器学习预测功能 (模块9)
        try:
            # 尝试相对导入（用于包导入）
            try:
                from .ml_prediction_api import register_ml_prediction_routes
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from ml_prediction_api import register_ml_prediction_routes
            
            register_ml_prediction_routes(self.app)
            print("✅ 机器学习预测功能已启用 (模块9)")
        except ImportError as e:
            print(f"⚠️  机器学习预测功能不可用: {e}")
        
                # 集成RQA分析流程功能
        try:
            # 尝试相对导入（用于包导入）
            try:
                from .rqa_pipeline_api import rqa_pipeline_bp
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from rqa_pipeline_api import rqa_pipeline_bp

            self.app.register_blueprint(rqa_pipeline_bp)
            print("✅ RQA分析流程功能已启用")
        except ImportError as e:
            print(f"⚠️  RQA分析流程功能不可用: {e}")

        # 集成综合特征提取功能
        try:
            # 尝试相对导入（用于包导入）
            try:
                from .feature_extraction_api import feature_extraction_bp
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from feature_extraction_api import feature_extraction_bp

            self.app.register_blueprint(feature_extraction_bp)
            print("✅ 综合特征提取功能已启用")
        except ImportError as e:
            print(f"⚠️  综合特征提取功能不可用: {e}")
        
        # 集成模块10 Eye-Index 综合评估功能
        try:
            try:
                from .module10_eye_index.api import register_eye_index_routes
            except ImportError:
                # 尝试绝对导入（用于直接运行）
                from module10_eye_index.api import register_eye_index_routes

            register_eye_index_routes(self.app)
            
            # 添加模块10静态文件路由
            @self.app.route('/static/js/eye_index.js')
            def eye_index_js():
                try:
                    from flask import send_from_directory
                    return send_from_directory(
                        os.path.join(os.path.dirname(__file__), 'module10_eye_index', 'static', 'js'),
                        'eye_index.js'
                    )
                except Exception as e:
                    print(f"❌ 加载eye_index.js失败: {e}")
                    return "console.log('Eye-Index JS加载失败');", 404
            
            print("✅ 模块10 Eye-Index 综合评估功能已启用")
        except ImportError as e:
            print(f"⚠️  模块10 Eye-Index 综合评估功能不可用: {e}")
        
        # 集成模块10-C 模型服务与管理API
        try:
            import sys
            import os
            
            # 添加backend路径
            backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            # 尝试导入
            try:
                from backend.m10_service import service_bp, initialize_models
            except ImportError:
                try:
                    from m10_service import service_bp, initialize_models
                except ImportError:
                    # 最后尝试相对导入
                    from ..backend.m10_service import service_bp, initialize_models

            # 注册蓝图到 /api/m10 路径前缀
            self.app.register_blueprint(service_bp, url_prefix="/api/m10")
            
            # 初始化模型（激活best版本）
            activated_count = initialize_models()
            
            print(f"✅ 模块10-C 模型服务API已启用 ({activated_count} 个模型激活)")
        except ImportError as e:
            print(f"⚠️  模块10-C 模型服务API不可用: {e}")
        except Exception as e:
            print(f"⚠️  模块10-C 初始化失败: {e}")
        
        # 集成模块10-B PyTorch训练引擎API
        try:
            # 尝试导入模块10-B的Blueprint
            try:
                from backend.m10_training.api import m10b_bp
            except ImportError:
                try:
                    from m10_training.api import m10b_bp
                except ImportError:
                    # 最后尝试相对导入
                    from ..backend.m10_training.api import m10b_bp

            # 注册蓝图到 /api/m10b 路径前缀
            self.app.register_blueprint(m10b_bp)
            
            print("✅ 模块10-B PyTorch训练引擎API已启用")
        except ImportError as e:
            print(f"⚠️  模块10-B 训练引擎API不可用: {e}")
        except Exception as e:
            print(f"⚠️  模块10-B 初始化失败: {e}")
        
        # 集成模块10-D 模型性能评估API
        try:
            # 尝试导入模块10-D的Blueprint
            try:
                from backend.m10_evaluation.api import evaluation_bp
            except ImportError:
                try:
                    from m10_evaluation.api import evaluation_bp
                except ImportError:
                    # 最后尝试相对导入
                    from ..backend.m10_evaluation.api import evaluation_bp

            # 注册蓝图到 /api/m10d 路径前缀
            self.app.register_blueprint(evaluation_bp, url_prefix="/api/m10d")
            
            print("✅ 模块10-D 模型性能评估API已启用")
        except ImportError as e:
            print(f"⚠️  模块10-D 性能评估API不可用: {e}")
        except Exception as e:
            print(f"⚠️  模块10-D 初始化失败: {e}")
        
        # 集成模块10-E 关联性深度可视化API
        try:
            # 尝试导入模块10-E的Blueprint
            try:
                from backend.m10e_correlation.api import correlation_bp
            except ImportError:
                try:
                    from m10e_correlation.api import correlation_bp
                except ImportError:
                    # 最后尝试相对导入
                    from ..backend.m10e_correlation.api import correlation_bp

            # 注册蓝图到 /api/m10e 路径前缀
            self.app.register_blueprint(correlation_bp, url_prefix="/api/m10e")
            
            print("✅ 模块10-E 关联性深度可视化API已启用")
        except ImportError as e:
            print(f"⚠️  模块10-E 关联性分析API不可用: {e}")
        except Exception as e:
            print(f"⚠️  模块10-E 初始化失败: {e}")
    
    def get_default_colors(self) -> Dict:
        """获取默认颜色配置"""
        return {
            'trajectory': (200, 80, 255),
            'fixation': (0, 0, 255),
            'saccade': (255, 100, 100),
            'start_point': (0, 255, 0),
            'end_point': (255, 0, 0),
            'roi_background': (0, 128, 255),
            'roi_instructions': (255, 165, 0),
            'roi_keywords': (255, 0, 0),
            'sequence_enter': (255, 0, 0),
            'sequence_exit': (0, 255, 0)
        }
    
    def get_default_sizes(self) -> Dict:
        """获取默认尺寸配置"""
        return {
            'trajectory_width': 2,
            'fixation_radius': 1,
            'saccade_radius': 1,
            'start_end_radius': 3,
            'roi_alpha_bg': 60,     # 背景ROI透明度
            'roi_alpha_inst': 80,   # 指令ROI透明度
            'roi_alpha_kw': 100,    # 关键词ROI透明度
            'font_size': 16
        }
        
    def setup_routes(self):
        """设置Flask路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('enhanced_index.html')
            
        @self.app.route('/test_frontend_params.html')
        def test_params():
            """参数配置测试页面"""
            try:
                with open('test_frontend_params.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>测试页面未找到</h1><p>请确保test_frontend_params.html文件存在</p>"
        
        @self.app.route('/api/groups')
        def get_groups():
            """获取所有组的信息"""
            return jsonify(self.get_groups_overview())
        
        @self.app.route('/api/group/<group_type>/data')
        def get_group_data(group_type):
            """获取指定组的数据列表"""
            return jsonify(self.get_group_data(group_type))
        
        @self.app.route('/api/visualize/<group_type>/<data_id>')
        def visualize_data(group_type, data_id):
            """生成增强版数据可视化"""
            # 获取可视化参数
            fixation_size = request.args.get('fixationSize', 3, type=int)
            trajectory_width = request.args.get('trajectoryWidth', 2, type=int)
            trajectory_style = request.args.get('trajectoryStyle', 'solid')
            point_size = request.args.get('pointSize', 1, type=int)
            
            # 获取校准偏移量参数（用于预览）
            x_offset = request.args.get('xOffset', 0, type=float)
            y_offset = request.args.get('yOffset', 0, type=float)
            preview_mode = request.args.get('preview', False, type=bool)
            
            # 获取时间范围参数（用于时间校准）
            time_start = request.args.get('timeStart', 0, type=float)  # 百分比
            time_end = request.args.get('timeEnd', 100, type=float)    # 百分比
            
            vis_params = {
                'fixation_size': fixation_size,
                'trajectory_width': trajectory_width,
                'trajectory_style': trajectory_style,
                'point_size': point_size,
                'x_offset': x_offset,
                'y_offset': y_offset,
                'preview_mode': preview_mode,
                'time_start': time_start,
                'time_end': time_end
            }
            
            return jsonify(self.generate_enhanced_visualization(group_type, data_id, vis_params))
        
        @self.app.route('/api/statistics/<group_type>')
        def get_statistics(group_type):
            """获取组统计信息"""
            return jsonify(self.get_group_statistics(group_type))
        
        @self.app.route('/api/process/<group_type>/<data_id>')
        def process_single_data(group_type, data_id):
            """处理单个数据文件并生成详细分析"""
            return jsonify(self.process_single_adq(group_type, data_id))

        @self.app.route('/api/upload-group', methods=['POST'])
        def upload_file_group():
            """批量上传数据文件组"""
            try:
                if 'files' not in request.files:
                    return jsonify({'success': False, 'error': '没有选择文件'})
                
                files = request.files.getlist('files')
                group = request.form.get('group')
                
                if len(files) == 0:
                    return jsonify({'success': False, 'error': '文件列表为空'})
                
                if not group or group not in ['control', 'mci', 'ad']:
                    return jsonify({'success': False, 'error': '无效的分组'})
                
                # 验证文件数量和名称
                if len(files) != 5:
                    return jsonify({'success': False, 'error': f'必须上传5个文件，当前上传了{len(files)}个'})
                
                # 支持两种文件名格式：1.txt-5.txt 或 level_1.txt-level_5.txt
                standard_names = {'1.txt', '2.txt', '3.txt', '4.txt', '5.txt'}
                level_names = {'level_1.txt', 'level_2.txt', 'level_3.txt', 'level_4.txt', 'level_5.txt'}
                uploaded_names = {f.filename for f in files}
                
                if uploaded_names != standard_names and uploaded_names != level_names:
                    return jsonify({'success': False, 'error': '文件名必须是1.txt到5.txt或level_1.txt到level_5.txt'})
                
                # 调用文件组上传处理方法
                result = self.handle_file_group_upload(files, group)
                return jsonify(result)
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/process-group/<group_id>', methods=['POST'])
        def process_file_group(group_id):
            """处理上传的文件组"""
            try:
                # 调用文件组处理方法
                result = self.process_uploaded_file_group(group_id)
                return jsonify(result)
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
 
        @self.app.route('/api/save-calibration', methods=['POST'])
        def save_calibration():
             """保存校准偏移量到数据文件"""
             try:
                 data = request.get_json()
                 
                 group_type = data.get('groupType')
                 data_id = data.get('dataId')
                 x_offset = data.get('xOffset', 0)
                 y_offset = data.get('yOffset', 0)
                 time_start = data.get('timeStart', 0)
                 time_end = data.get('timeEnd', 100)
                 
                 if not group_type or not data_id:
                     return jsonify({'success': False, 'error': '缺少必要参数'})
                 
                 # 调用校准保存方法
                 result = self.save_data_calibration(group_type, data_id, x_offset, y_offset, time_start, time_end)
                 return jsonify(result)
                 
             except Exception as e:
                 return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/time-info/<group_type>/<data_id>')
        def get_time_info(group_type, data_id):
            """获取数据的时间信息"""
            try:
                result = self.get_data_time_info(group_type, data_id)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/data/<data_id>', methods=['DELETE'])
        def delete_data(data_id):
            """删除数据文件（整组）"""
            try:
                result = self.delete_data_group(data_id)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/data/<data_id>/move', methods=['POST'])
        def move_data(data_id):
            """移动数据到不同组别"""
            try:
                data = request.get_json()
                from_group = data.get('fromGroup')
                to_group = data.get('toGroup')
                
                if not from_group or not to_group:
                    return jsonify({'success': False, 'error': '缺少必要参数'})
                
                result = self.move_data_between_groups(data_id, from_group, to_group)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/fix-data-files', methods=['POST'])
        def fix_data_files():
            """修复现有数据文件，添加缺失的milliseconds列"""
            try:
                data = request.get_json() or {}
                group_type = data.get('groupType')  # 可选，指定要修复的组类型
                
                result = self.fix_existing_data_files(group_type)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/mmse-scores/<group_type>/<int:group_num>')
        def get_mmse_score_api(group_type, group_num):
            """获取指定组的MMSE分数"""
            try:
                mmse_data = self.get_mmse_score(group_type, group_num)
                if mmse_data:
                    # 添加评估等级信息
                    assessment = self.get_mmse_assessment_level(mmse_data['total_score'])
                    mmse_data['assessment'] = assessment
                    return jsonify({'success': True, 'data': mmse_data})
                else:
                    return jsonify({'success': False, 'error': '未找到MMSE分数数据'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/mmse-scores/<group_type>')
        def get_group_mmse_scores(group_type):
            """获取指定组类型的所有MMSE分数"""
            try:
                group_scores = self.mmse_scores.get(group_type, {})
                result = {}
                for group_num, mmse_data in group_scores.items():
                    assessment = self.get_mmse_assessment_level(mmse_data['total_score'])
                    result[group_num] = {
                        **mmse_data,
                        'assessment': assessment
                    }
                return jsonify({'success': True, 'data': result})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/mmse-statistics')
        def get_mmse_statistics():
            """获取所有组的MMSE分数统计"""
            try:
                stats = {
                    'control': {'count': 0, 'avg_score': 0, 'min_score': 30, 'max_score': 0, 'scores': []},
                    'mci': {'count': 0, 'avg_score': 0, 'min_score': 30, 'max_score': 0, 'scores': []},
                    'ad': {'count': 0, 'avg_score': 0, 'min_score': 30, 'max_score': 0, 'scores': []}
                }
                
                for group_type, group_scores in self.mmse_scores.items():
                    if group_scores:
                        scores = [data['total_score'] for data in group_scores.values()]
                        stats[group_type].update({
                            'count': len(scores),
                            'avg_score': sum(scores) / len(scores),
                            'min_score': min(scores),
                            'max_score': max(scores),
                            'scores': scores
                        })
                
                return jsonify({'success': True, 'data': stats})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/static/modules/<path:filename>')
        def serve_module_file(filename):
            """提供模块HTML文件"""
            try:
                from flask import send_from_directory
                module_dir = os.path.join(self.app.static_folder, 'modules')
                return send_from_directory(module_dir, filename)
            except Exception as e:
                return f"模块文件加载失败: {str(e)}", 404
        
        @self.app.route('/static/normalized_features/<path:filename>')
        def serve_normalized_features(filename):
            """提供归一化特征数据文件（增强调试版本）"""
            import time
            start_time = time.time()
            
            print(f"🌐 === 收到归一化特征文件请求 ===")
            print(f"📝 请求文件: {filename}")
            print(f"🕐 请求时间: {time.strftime('%H:%M:%S')}")
            
            try:
                from flask import send_from_directory, Response, request
                
                # 获取正确的数据目录路径（相对于项目根目录）
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                features_dir = os.path.join(project_root, 'data', 'normalized_features')
                
                print(f"📁 项目根目录: {project_root}")
                print(f"📁 特征数据目录: {features_dir}")
                print(f"📁 目录是否存在: {os.path.exists(features_dir)}")
                
                if os.path.exists(features_dir):
                    files_in_dir = os.listdir(features_dir)
                    print(f"📂 目录中的文件: {files_in_dir}")
                
                # 检查文件是否存在
                file_path = os.path.join(features_dir, filename)
                print(f"📄 完整文件路径: {file_path}")
                print(f"📄 文件是否存在: {os.path.exists(file_path)}")
                
                if not os.path.exists(file_path):
                    print(f"❌ 文件不存在: {file_path}")
                    return f"归一化特征文件不存在: {filename}", 404
                
                # 获取文件信息
                file_size = os.path.getsize(file_path)
                print(f"📏 文件大小: {file_size} 字节")
                
                print(f"📖 开始读取文件...")
                read_start = time.time()
                
                # 读取并返回CSV文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                read_time = time.time() - read_start
                print(f"📖 文件读取完成，用时: {read_time:.3f}秒")
                print(f"📊 内容长度: {len(content)} 字符")
                print(f"📊 内容前100字符: {content[:100]}")
                
                response = Response(content, mimetype='text/csv', headers={
                    'Content-Disposition': f'inline; filename="{filename}"',
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'no-cache'
                })
                
                total_time = time.time() - start_time
                print(f"✅ 文件提供成功，总用时: {total_time:.3f}秒")
                print(f"🌐 === 请求处理完成 ===")
                
                return response
                
            except Exception as e:
                error_time = time.time() - start_time
                print(f"❌ 提供CSV文件失败: {str(e)}")
                print(f"❌ 错误类型: {type(e).__name__}")
                print(f"❌ 失败用时: {error_time:.3f}秒")
                print(f"❌ 错误堆栈: {str(e)}")
                print(f"🌐 === 请求失败 ===")
                return f"归一化特征文件加载失败: {str(e)}", 500
    
    def get_groups_overview(self) -> Dict:
        """获取所有组的概览信息"""
        groups = {
            'control': {
                'name': '健康对照组',
                'color': '#28a745',
                'description': '健康人群对照数据',
                'data_count': self.count_available_data('control')
            },
            'mci': {
                'name': 'MCI组',
                'color': '#ffc107', 
                'description': '轻度认知障碍数据',
                'data_count': self.count_available_data('mci')
            },
            'ad': {
                'name': 'AD组',
                'color': '#dc3545',
                'description': '阿尔茨海默病数据',
                'data_count': self.count_available_data('ad')
            }
        }
        
        print(f"📊 数据统计: Control({groups['control']['data_count']}) MCI({groups['mci']['data_count']}) AD({groups['ad']['data_count']})")
        return groups
    
    def count_available_data(self, group_type: str) -> int:
        """统计可用数据数量"""
        data_sources = self.config.get("data_sources", {})
        group_dir = data_sources.get(f"{group_type}_calibrated", "")
        
        if not os.path.exists(group_dir):
            return 0
        
        count = 0
        for root, dirs, files in os.walk(group_dir):
            count += len([f for f in files if f.endswith('_calibrated.csv')])
        
        return count
    
    def get_group_data(self, group_type: str) -> List[Dict]:
        """获取指定组的数据列表"""
        data_list = []
        data_sources = self.config.get("data_sources", {})
        group_dir = data_sources.get(f"{group_type}_calibrated", "")
        
        if not os.path.exists(group_dir):
            print(f"⚠️  数据目录不存在: {group_dir}")
            return data_list
        
        # 用于去重的集合
        seen_data_ids = set()
        
        # 遍历目录查找数据文件
        for root, dirs, files in os.walk(group_dir):
            for file in files:
                if file.endswith('_calibrated.csv'):
                    # 解析文件名获取信息
                    data_info = self.parse_data_filename(file, group_type)
                    if data_info:
                        data_id = data_info['data_id']
                        # 检查是否已经存在相同的data_id
                        if data_id not in seen_data_ids:
                            data_info['file_path'] = os.path.join(root, file)
                            data_list.append(data_info)
                            seen_data_ids.add(data_id)
                            print(f"✅ 加载数据: {group_type} - {data_id} ({file})")
        
        # 按组号和问题号排序
        data_list.sort(key=lambda x: (x.get('group_num', 0), x.get('question_num', 0)))
        
        print(f"📊 {group_type}组共加载 {len(data_list)} 个数据文件")
        return data_list
    
    def parse_data_filename(self, filename: str, group_type: str) -> Optional[Dict]:
        """解析数据文件名"""
        import re
        
        # 匹配不同的文件名模式
        patterns = {
            'control': r'n(\d+)q(\d+)_preprocessed_calibrated\.csv',
            'mci': r'm(\d+)q(\d+)_preprocessed_calibrated\.csv',
            'ad': r'ad(\d+)q(\d+)_preprocessed_calibrated\.csv'
        }
        
        pattern = patterns.get(group_type)
        if not pattern:
            return None
        
        match = re.match(pattern, filename)
        if match:
            group_num = int(match.group(1))
            question_num = int(match.group(2))
            
            data_id = f"{group_type[0]}{group_num}q{question_num}"
            if group_type == 'ad':
                data_id = f"ad{group_num}q{question_num}"
            
            return {
                'data_id': data_id,
                'group_num': group_num,
                'question_num': question_num,
                'filename': filename,
                'display_name': f"Group {group_num} - Question {question_num}"
            }
        
        return None
    
    def generate_enhanced_visualization(self, group_type: str, data_id: str, vis_params: Dict = None) -> Dict:
        """
        生成增强版数据可视化
        
        Args:
            group_type: 组类型
            data_id: 数据ID
            
        Returns:
            可视化结果
        """
        try:
            # 获取数据文件路径
            data_list = self.get_group_data(group_type)
            target_data = None
            
            for data_item in data_list:
                if data_item['data_id'] == data_id:
                    target_data = data_item
                    break
            
            if not target_data:
                return {'error': f'数据不存在: {data_id}'}
            
            # 检查是否为校准预览模式
            preview_mode = vis_params.get('preview_mode', False) if vis_params else False
            x_offset = vis_params.get('x_offset', 0) if vis_params else 0
            y_offset = vis_params.get('y_offset', 0) if vis_params else 0
            time_start = vis_params.get('time_start', 0) if vis_params else 0
            time_end = vis_params.get('time_end', 100) if vis_params else 100
            
            file_path = target_data['file_path']
            
            # 如果是预览模式，创建临时校准数据
            if preview_mode and (x_offset != 0 or y_offset != 0 or time_start > 0 or time_end < 100):
                file_path = self.create_preview_calibrated_data(target_data['file_path'], x_offset, y_offset, time_start, time_end)
                if not file_path:
                    return {'error': '无法创建预览数据'}
            
            # 增强版分析
            question = f"q{target_data['question_num']}"
            analysis_result = self.analyzer.analyze_eyetracking_data(
                file_path, 
                question,
                debug=True
            )
            
            if 'error' in analysis_result:
                return analysis_result
            
            # 生成增强版可视化图像
            visualization_image = self.create_enhanced_trajectory_visualization(
                analysis_result, question, vis_params
            )
            
            if visualization_image:
                # 转换为base64
                img_buffer = BytesIO()
                visualization_image.save(img_buffer, format='PNG')
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                
                result = {
                    'success': True,
                    'data_id': data_id,
                    'question': question,
                    'image': img_str,  # 直接返回base64字符串，不包含前缀
                    'roi_statistics': analysis_result['roi_statistics'],
                    'overall_statistics': analysis_result['overall_statistics'],
                    'fixations': analysis_result['fixations'],
                    'saccades': analysis_result['saccades'],
                    'roi_sequence_count': analysis_result['overall_statistics']['roi_sequence_count']
                }
                return convert_numpy_types(result)
            else:
                return {'error': '无法生成可视化图像'}
            
        except Exception as e:
            return {'error': f'可视化生成失败: {str(e)}'}
    
    def load_background_image(self, question: str, maintain_aspect: bool = True) -> Optional[Image.Image]:
        """
        加载背景图像
        
        Args:
            question: 问题编号
            maintain_aspect: 是否保持1:1比例
            
        Returns:
            PIL图像对象
        """
        try:
            background_dir = self.analyzer.background_img_dir
            # 匹配Q1.jpg, Q2.jpg等格式
            q_num = question[1:]  # 去掉'q'前缀
            img_filename = f"Q{q_num}.jpg"
            img_path = os.path.join(background_dir, img_filename)
            
            if os.path.exists(img_path):
                # 使用OpenCV加载图像
                bgr_img = cv2.imread(img_path)
                if bgr_img is not None:
                    # 转换颜色格式
                    rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
                    # 转换为PIL图像，保持原始尺寸比例
                    pil_img = Image.fromarray(rgb_img)
                    return pil_img
                    
        except Exception as e:
            print(f"⚠️  无法加载背景图像: {e}")
        
        return None
    
    def draw_rois_on_image(self, pil_img: Image.Image, roi_kw: List, roi_inst: List, roi_bg: List) -> Image.Image:
        """
        在图像上绘制ROI区域
        
        Args:
            pil_img: PIL图像对象
            roi_kw: 关键词ROI列表
            roi_inst: 指令ROI列表
            roi_bg: 背景ROI列表
            
        Returns:
            绘制了ROI的图像
        """
        # 标准化ROI坐标
        roi_kw = self.analyzer.normalize_roi(roi_kw)
        roi_inst = self.analyzer.normalize_roi(roi_inst)
        roi_bg = self.analyzer.normalize_roi(roi_bg)
        
        base = pil_img.convert("RGBA")
        w, h = base.size
        roi_layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        text_layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        d_roi = ImageDraw.Draw(roi_layer)
        d_txt = ImageDraw.Draw(text_layer)
        
        # 尝试加载字体
        try:
            font_ = ImageFont.truetype("msyh.ttc", 18)
        except:
            font_ = ImageFont.load_default()
        
        def measure_text(txt):
            try:
                bbox = font_.getbbox(txt)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except:
                return (len(txt) * 10, 18)  # 简单估算
        
        def draw_ones(roi_list, color, alpha_):
            """绘制一组ROI"""
            for (rn, xmn, ymn, xmx, ymy) in roi_list:
                try:
                    X1 = int(xmn * w)
                    X2 = int(xmx * w)
                    # Y坐标转换（PIL的Y坐标向下递增）
                    Ytop = int((1 - ymn) * h)
                    Ybot = int((1 - ymy) * h)
                    y1, y2 = min(Ytop, Ybot), max(Ytop, Ybot)
                    
                    # 绘制填充矩形 - 半透明效果
                    fill_color = (*color, alpha_)
                    outline_color = (*color, 255)
                    d_roi.rectangle([(X1, y1), (X2, y2)],
                                   fill=fill_color, outline=outline_color, width=1)
                    
                    # 绘制标签
                    tw, th = measure_text(rn)
                    tx, ty = X1 + 2, y2 + 2  # 标签在矩形下方
                    if tx + tw > w:
                        tx = w - tw
                    if ty + th > h:
                        ty = h - th
                    
                    # 标签背景 - 半透明白色
                    d_txt.rectangle([(tx, ty), (tx + tw, ty + th)],
                                   fill=(255, 255, 255, 180))
                    # 标签文字 - 黑色
                    d_txt.text((tx, ty), rn, fill=(0, 0, 0, 255), font=font_)
                except Exception as e:
                    print(f"⚠️  绘制ROI {rn} 失败: {e}")
                    continue
        
        # 按层次绘制（背景 -> 指令 -> 关键词）
        try:
            bg_color = self.colors.get('roi_background', (0, 128, 255))
            inst_color = self.colors.get('roi_instructions', (255, 165, 0))
            kw_color = self.colors.get('roi_keywords', (255, 0, 0))
            
            draw_ones(roi_bg, bg_color, self.sizes['roi_alpha_bg'])
            draw_ones(roi_inst, inst_color, self.sizes['roi_alpha_inst'])
            draw_ones(roi_kw, kw_color, self.sizes['roi_alpha_kw'])
        except Exception as e:
            print(f"⚠️  绘制ROI层时出错: {e}")
        
        # 合并图层
        combined = Image.alpha_composite(base, roi_layer)
        combined = Image.alpha_composite(combined, text_layer)
        return combined.convert("RGB")
     
    def draw_trajectory_with_sequence(self, pil_img: Image.Image, df: pd.DataFrame, vis_params: Dict = None) -> Image.Image:
        """
        绘制带序列标记的眼动轨迹
        
        Args:
            pil_img: PIL图像对象
            df: 眼动数据DataFrame
            vis_params: 可视化参数
            
        Returns:
            绘制了轨迹的图像
        """
        w, h = pil_img.size
        traj_layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        d = ImageDraw.Draw(traj_layer)
        
        # 获取可视化参数
        if vis_params is None:
            vis_params = {}
        
        fixation_size = vis_params.get('fixation_size', 3)
        trajectory_width = vis_params.get('trajectory_width', 2)
        trajectory_style = vis_params.get('trajectory_style', 'solid')
        point_size = vis_params.get('point_size', 1)
        
        # 尝试加载字体
        try:
            font_ = ImageFont.truetype("arial.ttf", self.sizes['font_size'])
        except:
            font_ = ImageFont.load_default()
        
        # 转换坐标点
        pts = []
        for i in range(len(df)):
            px = int(df.at[i, "x"] * w)
            py = int((1 - df.at[i, "y"]) * h)  # Y坐标翻转
            pts.append((px, py))
        
        # 绘制轨迹线
        if len(pts) > 1:
            for i in range(len(pts) - 1):
                d.line([pts[i], pts[i + 1]], 
                       fill=(200, 80, 255, 160),  
                       width=trajectory_width)
        
        # 绘制数据点
        for pt in pts:
            d.ellipse((pt[0] - point_size, pt[1] - point_size, 
                      pt[0] + point_size, pt[1] + point_size),
                     fill=(0, 0, 255, 160))
        
        # 绘制起始点和结束点
        if pts:
            # 起始点 - 绿色
            start_pt = pts[0]
            d.ellipse((start_pt[0] - fixation_size, start_pt[1] - fixation_size,
                      start_pt[0] + fixation_size, start_pt[1] + fixation_size),
                     fill=(0, 255, 0, 200))
            
            # 结束点 - 红色
            if len(pts) > 1:
                end_pt = pts[-1]
                d.ellipse((end_pt[0] - fixation_size, end_pt[1] - fixation_size,
                          end_pt[0] + fixation_size, end_pt[1] + fixation_size),
                         fill=(255, 0, 0, 200))
        
        # 绘制ROI序列标记
        if "SequenceID" in df.columns and "EnterExitFlag" in df.columns:
            for i in range(len(df)):
                seq_id = df.at[i, "SequenceID"]
                flag = df.at[i, "EnterExitFlag"]
                if seq_id > 0 and flag in ("Enter", "Exit"):
                    label = ("E" if flag == "Enter" else "X") + str(seq_id)
                    
                    # 绘制标记
                    px, py = pts[i]
                    d.text((px + 3, py - 15), label, 
                           fill=(255, 0, 0, 255), font=font_)
        
        # 合并图层
        final = Image.alpha_composite(pil_img.convert("RGBA"), traj_layer)
        return final.convert("RGB")
    
    def create_enhanced_trajectory_visualization(self, analysis_result: Dict, question: str, vis_params: Dict = None) -> Optional[Image.Image]:
        """
        创建增强版轨迹可视化图像
        
        Args:
            analysis_result: 分析结果
            question: 问题编号
            
        Returns:
            PIL图像对象
        """
        try:
            df = analysis_result['data']
            roi_defs = analysis_result['roi_definitions']
            
            # 加载背景图像
            background_img = self.load_background_image(question)
            if background_img:
                img = background_img.copy()
            else:
                # 创建默认白色背景
                img = Image.new('RGB', (800, 600), 'white')
            
            # 绘制ROI区域
            img = self.draw_rois_on_image(img, 
                                         roi_defs['keywords'],
                                         roi_defs['instructions'], 
                                         roi_defs['background'])
            
            # 绘制眼动轨迹
            img = self.draw_trajectory_with_sequence(img, df, vis_params)
            
            return img
            
        except Exception as e:
            print(f"❌ 创建增强版可视化图像失败: {e}")
            return None
    
    def process_single_adq(self, group_type: str, data_id: str) -> Dict:
        """
        处理单个数据文件
        
        Args:
            group_type: 组类型
            data_id: 数据ID
            
        Returns:
            处理结果
        """
        try:
            # 获取数据文件
            data_list = self.get_group_data(group_type)
            target_data = None
            
            for data_item in data_list:
                if data_item['data_id'] == data_id:
                    target_data = data_item
                    break
            
            if not target_data:
                return {'error': f'数据不存在: {data_id}'}
            
            # 执行增强版分析
            question = f"q{target_data['question_num']}"
            analysis_result = self.analyzer.analyze_eyetracking_data(
                target_data['file_path'], 
                question,
                debug=True
            )
            
            if 'error' in analysis_result:
                return analysis_result
            
            # 生成可视化
            visualization_image = self.create_enhanced_trajectory_visualization(
                analysis_result, question
            )
            
            result = {
                'success': True,
                'data_id': data_id,
                'question': question,
                'analysis': analysis_result,
                'has_visualization': visualization_image is not None
            }
            
            # 如果成功生成可视化，添加base64编码
            if visualization_image:
                img_buffer = BytesIO()
                visualization_image.save(img_buffer, format='PNG')
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                result['image'] = img_str
            
            return result
            
        except Exception as e:
            return {'error': f'处理失败: {str(e)}'}
    
    def get_group_statistics(self, group_type: str) -> Dict:
        """获取组统计信息"""
        try:
            data_list = self.get_group_data(group_type)
            
            stats = {
                'total_files': len(data_list),
                'questions': {},
                'groups': {}
            }
            
            # 按问题统计
            for data_item in data_list:
                question = data_item['question_num']
                if question not in stats['questions']:
                    stats['questions'][question] = 0
                stats['questions'][question] += 1
            
            # 按组统计
            for data_item in data_list:
                group = data_item['group_num']
                if group not in stats['groups']:
                    stats['groups'][group] = 0
                stats['groups'][group] += 1
            
            return stats
            
        except Exception as e:
            return {'error': f'获取统计信息失败: {str(e)}'}
    
    def handle_file_group_upload(self, files, group: str) -> Dict:
        """
        处理文件组上传
        
        Args:
            files: 上传的文件列表
            group: 目标分组
            
        Returns:
            处理结果
        """
        import uuid
        import tempfile
        import shutil
        from datetime import datetime
        
        try:
            # 生成唯一组ID
            group_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 创建临时存储目录
            upload_dir = os.path.join("temp_uploads", group_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            # 保存所有文件
            file_info_list = []
            for file in files:
                filename = file.filename
                temp_file_path = os.path.join(upload_dir, filename)
                file.save(temp_file_path)
                
                file_info_list.append({
                    'filename': filename,
                    'temp_path': temp_file_path
                })
            
            # 存储组信息
            group_info = {
                'group_id': group_id,
                'group': group,
                'upload_time': timestamp,
                'files': file_info_list,
                'status': 'uploaded'
            }
            
            # 保存组信息到临时文件
            info_file = os.path.join(upload_dir, 'group_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(group_info, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 文件组上传成功: {[f.filename for f in files]} -> {group_id}")
            
            return {
                'success': True,
                'groupId': group_id,
                'group': group,
                'fileCount': len(files),
                'message': '文件组上传成功'
            }
            
        except Exception as e:
            print(f"❌ 文件组上传失败: {str(e)}")
            return {
                'success': False,
                'error': f'文件组上传失败: {str(e)}'
            }
    
    def process_uploaded_file_group(self, group_id: str) -> Dict:
        """
        处理上传的文件组
        
        Args:
            group_id: 文件组ID
            
        Returns:
            处理结果
        """
        try:
            # 读取组信息
            upload_dir = os.path.join("temp_uploads", group_id)
            info_file = os.path.join(upload_dir, 'group_info.json')
            
            if not os.path.exists(info_file):
                return {'success': False, 'error': '找不到文件组信息'}
            
            with open(info_file, 'r', encoding='utf-8') as f:
                group_info = json.load(f)
            
            group = group_info['group']
            files = group_info['files']
            
            print(f"🔄 开始处理文件组: {[f['filename'] for f in files]}")
            
            # 第1步：获取唯一的组编号（关键：只调用一次）
            group_num = self._get_next_group_number(group)
            target_group_name = f"{group}_group_{group_num}"
            
            # 第2步：创建目标目录结构
            raw_dir = f"data/{group}_raw/{target_group_name}"
            processed_dir = f"data/{group}_processed/{target_group_name}"
            calibrated_dir = f"data/{group}_calibrated/{target_group_name}"
            
            for dir_path in [raw_dir, processed_dir, calibrated_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            print(f"✅ 创建目标组目录: {target_group_name}")
            
            # 第3步：复制原始文件到目标目录
            for file_info in files:
                source_path = file_info['temp_path']
                filename = file_info['filename']
                target_raw_file = os.path.join(raw_dir, filename)
                
                # 检查源文件
                if os.path.exists(source_path):
                    source_size = os.path.getsize(source_path)
                    print(f"📁 源文件 {filename}: {source_size} bytes")
                else:
                    print(f"❌ 源文件不存在: {source_path}")
                    continue
                
                import shutil
                shutil.copy2(source_path, target_raw_file)
                
                # 验证复制结果
                if os.path.exists(target_raw_file):
                    target_size = os.path.getsize(target_raw_file)
                    print(f"✅ 复制原始文件: {filename} ({target_size} bytes)")
                else:
                    print(f"❌ 复制失败: {filename}")
            
            # 第4步：预处理所有文件
            processed_files = []
            for file_info in files:
                filename = file_info['filename']
                raw_file_path = os.path.join(raw_dir, filename)
                
                processed_result = self._process_raw_file_with_naming(
                    raw_file_path, processed_dir, group, group_num, filename
                )
                if not processed_result['success']:
                    return {
                        'success': False,
                        'error': f'预处理文件{filename}失败: {processed_result["error"]}'
                    }
                
                processed_files.append(processed_result['processed_file'])
                print(f"✅ 预处理完成: {filename}")
            
            # 第5步：校准所有文件
            calibrated_files = []
            for processed_file in processed_files:
                calibrated_result = self._calibrate_processed_file(
                    processed_file, 
                    calibrated_dir, 
                    group
                )
                if not calibrated_result['success']:
                    filename = os.path.basename(processed_file)
                    return {
                        'success': False,
                        'error': f'校准文件{filename}失败: {calibrated_result["error"]}'
                    }
                
                calibrated_files.append(calibrated_result['calibrated_file'])
                print(f"✅ 校准完成: {os.path.basename(processed_file)}")
            
            # 第6步：清理临时文件
            import shutil
            shutil.rmtree(upload_dir)
            
            print(f"🎉 文件组处理完成: {target_group_name}")
            
            return {
                'success': True,
                'message': '文件组处理完成',
                'group': group,
                'group_num': group_num,
                'target_group_name': target_group_name,
                'processed_files': len(processed_files),
                'calibrated_files': len(calibrated_files)
            }
            
        except Exception as e:
            print(f"❌ 文件组处理失败: {str(e)}")
            return {
                'success': False,
                'error': f'文件组处理失败: {str(e)}'
            }
    
    def _get_next_group_number(self, group: str) -> int:
        """获取下一个组编号"""
        try:
            base_dir = f"data/{group}_raw"
            if not os.path.exists(base_dir):
                return 1
            
            existing_groups = []
            for item in os.listdir(base_dir):
                if item.startswith(f"{group}_group_"):
                    try:
                        num = int(item.split('_')[-1])
                        existing_groups.append(num)
                    except ValueError:
                        continue
            
            return max(existing_groups) + 1 if existing_groups else 1
            
        except Exception:
            return 1
    
    def _process_raw_file_with_naming(self, raw_file: str, output_dir: str, group: str, group_num: int, original_filename: str) -> Dict:
        """处理原始文件（使用正确的命名格式）"""
        try:
            print(f"🔍 开始处理原始文件: {raw_file}")
            
            # 检查文件是否存在
            if not os.path.exists(raw_file):
                error_msg = f"原始文件不存在: {raw_file}"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # 检查文件大小
            file_size = os.path.getsize(raw_file)
            print(f"📁 文件大小: {file_size} bytes")
            
            # 检查文件内容样本
            try:
                with open(raw_file, 'r', encoding='utf-8') as f:
                    first_lines = []
                    for i, line in enumerate(f):
                        if i < 5:  # 读取前5行
                            first_lines.append(line.strip())
                        else:
                            break
                print(f"📄 文件前5行内容:")
                for i, line in enumerate(first_lines):
                    print(f"   {i+1}: {line}")
            except Exception as e:
                print(f"⚠️  无法读取文件内容: {e}")
            
            # 首先尝试自定义格式解析器
            from data_processing.custom_vr_parser import process_custom_vr_file
            
            # 根据原始文件名确定问题编号
            # 支持两种格式：1.txt -> q1, 2.txt -> q2, etc. 或 level_1.txt -> q1, level_2.txt -> q2, etc.
            base_name = os.path.splitext(original_filename)[0]
            
            try:
                # 尝试直接解析为整数 (1.txt, 2.txt, etc.)
                question_num = int(base_name)
                print(f"📝 使用标准格式解析问题编号: {original_filename} -> q{question_num}")
            except ValueError:
                # 如果直接解析失败，尝试 level_X 格式
                import re
                level_match = re.match(r'level_(\d+)', base_name)
                if level_match:
                    question_num = int(level_match.group(1))
                    print(f"📝 使用level格式解析问题编号: {original_filename} -> q{question_num}")
                else:
                    raise ValueError(f"无法从文件名解析问题编号: {original_filename}")
            
            # 验证问题编号范围
            if question_num < 1 or question_num > 5:
                raise ValueError(f"问题编号超出范围 (1-5): {question_num}")
            
            # 生成符合现有格式的输出文件名
            if group == 'control':
                prefix = 'n'
            elif group == 'mci':
                prefix = 'm'
            elif group == 'ad':
                prefix = 'ad'
            else:
                prefix = group[0]
            
            output_filename = f"{prefix}{group_num}q{question_num}_preprocessed.csv"
            output_file = os.path.join(output_dir, output_filename)
            print(f"📤 输出文件路径: {output_file}")
            
            # 调用自定义处理函数
            print(f"🔄 调用自定义VR格式处理器...")
            success = process_custom_vr_file(raw_file, output_file)
            print(f"✅ 自定义处理器返回结果: {success}")
            
            # 如果自定义格式处理失败，尝试标准格式
            if not success:
                print(f"🔄 尝试标准格式处理器...")
                from data_processing.vr_eyetracking_processor import process_txt_file
                success = process_txt_file(raw_file, output_file)
                print(f"✅ 标准处理器返回结果: {success}")
            
            if success:
                # 检查输出文件是否成功创建
                if os.path.exists(output_file):
                    output_size = os.path.getsize(output_file)
                    print(f"📤 输出文件创建成功，大小: {output_size} bytes")
                    
                    # 读取输出文件的前几行验证
                    try:
                        import pandas as pd
                        df = pd.read_csv(output_file, nrows=3)  # 读取前3行
                        print(f"📊 输出文件验证:")
                        print(f"   列名: {list(df.columns)}")
                        print(f"   数据行数: {len(df)}")
                        if len(df) > 0:
                            print(f"   第一行数据: {df.iloc[0].to_dict()}")
                    except Exception as e:
                        print(f"⚠️  输出文件验证失败: {e}")
                        
                    return {
                        'success': True,
                        'processed_file': output_file
                    }
                else:
                    error_msg = "处理成功但输出文件未创建"
                    print(f"❌ {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = "数据预处理失败"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f'数据预处理错误: {str(e)}'
            print(f"❌ {error_msg}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return {'success': False, 'error': error_msg}
    
    def _process_raw_file(self, raw_file: str, output_dir: str) -> Dict:
        """处理原始文件"""
        try:
            print(f"🔍 开始处理原始文件: {raw_file}")
            
            # 检查文件是否存在
            if not os.path.exists(raw_file):
                error_msg = f"原始文件不存在: {raw_file}"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # 检查文件大小
            file_size = os.path.getsize(raw_file)
            print(f"📁 文件大小: {file_size} bytes")
            
            # 检查文件内容样本
            try:
                with open(raw_file, 'r', encoding='utf-8') as f:
                    first_lines = []
                    for i, line in enumerate(f):
                        if i < 5:  # 读取前5行
                            first_lines.append(line.strip())
                        else:
                            break
                print(f"📄 文件前5行内容:")
                for i, line in enumerate(first_lines):
                    print(f"   {i+1}: {line}")
            except Exception as e:
                print(f"⚠️  无法读取文件内容: {e}")
            
            # 首先尝试自定义格式解析器
            from data_processing.custom_vr_parser import process_custom_vr_file
            
            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(raw_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}_preprocessed.csv")
            print(f"📤 输出文件路径: {output_file}")
            
            # 调用自定义处理函数
            print(f"🔄 调用自定义VR格式处理器...")
            success = process_custom_vr_file(raw_file, output_file)
            print(f"✅ 自定义处理器返回结果: {success}")
            
            # 如果自定义格式处理失败，尝试标准格式
            if not success:
                print(f"🔄 尝试标准格式处理器...")
                from data_processing.vr_eyetracking_processor import process_txt_file
                success = process_txt_file(raw_file, output_file)
                print(f"✅ 标准处理器返回结果: {success}")
            
            if success:
                # 检查输出文件是否成功创建
                if os.path.exists(output_file):
                    output_size = os.path.getsize(output_file)
                    print(f"📤 输出文件创建成功，大小: {output_size} bytes")
                    
                    # 读取输出文件的前几行验证
                    try:
                        import pandas as pd
                        df = pd.read_csv(output_file, nrows=3)  # 读取前3行
                        print(f"📊 输出文件验证:")
                        print(f"   列名: {list(df.columns)}")
                        print(f"   数据行数: {len(df)}")
                        if len(df) > 0:
                            print(f"   第一行数据: {df.iloc[0].to_dict()}")
                    except Exception as e:
                        print(f"⚠️  输出文件验证失败: {e}")
                        
                    return {
                        'success': True,
                        'processed_file': output_file
                    }
                else:
                    error_msg = "处理成功但输出文件未创建"
                    print(f"❌ {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = "数据预处理失败"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f'数据预处理错误: {str(e)}'
            print(f"❌ {error_msg}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return {'success': False, 'error': error_msg}
    
    def _calibrate_processed_file(self, processed_file: str, output_dir: str, group: str) -> Dict:
        """校准处理后的文件"""
        try:
            print(f"🔍 开始校准处理后的文件: {processed_file}")
            
            # 检查处理后的文件是否存在
            if not os.path.exists(processed_file):
                error_msg = f"预处理文件不存在: {processed_file}"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
                
            # 检查文件大小
            file_size = os.path.getsize(processed_file)
            print(f"📁 预处理文件大小: {file_size} bytes")
            
            from calibration.advanced_calibrator import AdvancedCalibrator
            
            # 创建校准器
            print(f"🔧 创建校准器...")
            calibrator = AdvancedCalibrator()
            
            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(processed_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}_calibrated.csv")
            print(f"📤 校准输出文件路径: {output_file}")
            
            # 获取校准参数
            group_name = os.path.basename(os.path.dirname(processed_file))
            print(f"🏷️  组名: {group_name}")
            
            x_offset, y_offset, method = calibrator.get_calibration_params(group_name)
            print(f"⚙️  校准参数: x_offset={x_offset}, y_offset={y_offset}, method={method}")
            
            # 执行校准
            print(f"🔄 执行校准...")
            success = calibrator.calibrate_csv_file(
                processed_file, 
                output_file, 
                x_offset, 
                y_offset
            )
            print(f"✅ 校准返回结果: {success}")
            
            if success:
                # 检查输出文件是否成功创建
                if os.path.exists(output_file):
                    output_size = os.path.getsize(output_file)
                    print(f"📤 校准文件创建成功，大小: {output_size} bytes")
                    
                    # 读取输出文件的前几行验证
                    try:
                        import pandas as pd
                        df = pd.read_csv(output_file, nrows=3)  # 读取前3行
                        print(f"📊 校准文件验证:")
                        print(f"   列名: {list(df.columns)}")
                        print(f"   数据行数: {len(df)}")
                        if len(df) > 0:
                            print(f"   第一行数据: {df.iloc[0].to_dict()}")
                    except Exception as e:
                        print(f"⚠️  校准文件验证失败: {e}")
                        
                    return {
                        'success': True,
                        'calibrated_file': output_file,
                        'calibration_method': method
                    }
                else:
                    error_msg = "校准成功但输出文件未创建"
                    print(f"❌ {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = "数据校准失败"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f'数据校准错误: {str(e)}'
            print(f"❌ {error_msg}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return {'success': False, 'error': error_msg}
    
    def save_data_calibration(self, group_type: str, data_id: str, x_offset: float, y_offset: float, time_start: float = 0, time_end: float = 100) -> Dict:
        """
        保存校准偏移量到数据文件
        
        Args:
            group_type: 组类型 (control, mci, ad)
            data_id: 数据ID
            x_offset: X轴偏移量
            y_offset: Y轴偏移量
            
        Returns:
            操作结果字典
        """
        try:
            print(f"🎯 开始保存校准偏移量: {group_type}/{data_id}")
            print(f"📊 偏移量: X={x_offset:.3f}, Y={y_offset:.3f}")
            
            # 参数验证
            if not isinstance(x_offset, (int, float)) or not isinstance(y_offset, (int, float)):
                return {'success': False, 'error': '偏移量参数类型无效'}
            
            if abs(x_offset) > 1.0 or abs(y_offset) > 1.0:
                return {'success': False, 'error': '偏移量超出安全范围 [-1.0, 1.0]'}
            
            # 检查是否有任何修改（坐标偏移或时间范围修改）
            has_coordinate_change = x_offset != 0 or y_offset != 0
            has_time_change = time_start > 0 or time_end < 100
            
            if not has_coordinate_change and not has_time_change:
                return {'success': False, 'error': '没有检测到校准修改，无需保存'}
            
            # 查找对应的校准文件
            calibrated_dir = f"data/{group_type}_calibrated"
            if not os.path.exists(calibrated_dir):
                return {'success': False, 'error': f'校准目录不存在: {calibrated_dir}'}
            
            # 查找匹配的文件
            target_file = None
            print(f"🔍 正在查找文件，data_id: '{data_id}'")
            print(f"📂 搜索目录: {calibrated_dir}")
            
            for root, dirs, files in os.walk(calibrated_dir):
                print(f"📁 检查目录: {root}")
                print(f"📄 目录中的文件: {files}")
                for file in files:
                    if file.endswith('_calibrated.csv'):
                        # 使用 parse_data_filename 方法正确解析文件名
                        parsed = self.parse_data_filename(file, group_type)
                        if parsed and parsed['data_id'] == data_id:
                            target_file = os.path.join(root, file)
                            print(f"✅ 找到匹配文件: {target_file} (解析得到的data_id: {parsed['data_id']})")
                            break
                        else:
                            parsed_id = parsed['data_id'] if parsed else 'N/A'
                            print(f"   检查文件: '{file}' -> 解析data_id: '{parsed_id}' != 目标data_id: '{data_id}'")
                if target_file:
                    break
            
            if not target_file:
                print(f"❌ 未找到匹配文件，data_id: '{data_id}'")
                # 列出所有可能的文件供调试
                all_files = []
                for root, dirs, files in os.walk(calibrated_dir):
                    for file in files:
                        if file.endswith('_calibrated.csv'):
                            all_files.append(file)
                print(f"📋 可用的校准文件: {all_files[:10]}...")  # 只显示前10个
                return {'success': False, 'error': f'未找到对应的校准文件: {data_id}。可用文件数: {len(all_files)}'}
            
            print(f"📁 目标文件: {target_file}")
            
            # 读取现有数据
            try:
                df = pd.read_csv(target_file, encoding='utf-8')
                print(f"📊 读取数据: {len(df)} 行")
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                return {'success': False, 'error': f'读取文件失败: {str(e)}'}

            # 检查必要的列，支持两种列名格式
            if 'x' in df.columns and 'y' in df.columns:
                pass  # 已经是标准列名
            elif 'GazePointX_normalized' in df.columns and 'GazePointY_normalized' in df.columns:
                # 重命名为标准列名
                df = df.rename(columns={
                    'GazePointX_normalized': 'x',
                    'GazePointY_normalized': 'y'
                })
                print(f"✅ 已将列名从 GazePointX/Y_normalized 重命名为 x/y")
            else:
                return {'success': False, 'error': '文件缺少x,y或GazePointX_normalized,GazePointY_normalized坐标列'}
            
            original_count = len(df)
            
            # 应用时间范围过滤
            if has_time_change and 'milliseconds' in df.columns:
                min_time = df['milliseconds'].min()
                max_time = df['milliseconds'].max()
                total_duration = max_time - min_time
                
                # 计算实际的时间范围
                actual_start_time = min_time + (total_duration * time_start / 100)
                actual_end_time = min_time + (total_duration * time_end / 100)
                
                # 过滤数据
                df = df[
                    (df['milliseconds'] >= actual_start_time) & 
                    (df['milliseconds'] <= actual_end_time)
                ]
                filtered_count = len(df)
                
                print(f"🎯 时间过滤: {original_count} → {filtered_count} 行 "
                      f"(时间范围: {time_start:.1f}% - {time_end:.1f}%)")
            
            # 应用坐标偏移量
            original_x_mean = df['x'].mean()
            original_y_mean = df['y'].mean()
            
            if has_coordinate_change:
                df['x'] = df['x'] + x_offset
                df['y'] = df['y'] + y_offset
            
            new_x_mean = df['x'].mean()
            new_y_mean = df['y'].mean()
            
            if has_coordinate_change:
                print(f"📈 X坐标变化: {original_x_mean:.3f} → {new_x_mean:.3f} (偏移: {x_offset:.3f})")
                print(f"📈 Y坐标变化: {original_y_mean:.3f} → {new_y_mean:.3f} (偏移: {y_offset:.3f})")
            else:
                print(f"📊 保持原始坐标: X={new_x_mean:.3f}, Y={new_y_mean:.3f}")
            
            # 保存校准后的文件
            try:
                df.to_csv(target_file, index=False, encoding='utf-8')
                print(f"✅ 校准文件已保存: {target_file}")
            except Exception as e:
                print(f"❌ 保存文件失败: {e}")
                return {'success': False, 'error': f'保存文件失败: {str(e)}'}
            
            # 验证保存结果
            try:
                df_verify = pd.read_csv(target_file, encoding='utf-8')
                if len(df_verify) == len(df):
                    print(f"✅ 文件验证通过: {len(df_verify)} 行数据")
                else:
                    print(f"⚠️  数据行数不匹配: 原始{len(df)}, 保存后{len(df_verify)}")
            except Exception as e:
                print(f"⚠️  文件验证失败: {e}")
            
            return {
                'success': True,
                'message': '校准已成功保存',
                'file': target_file,
                'changes': {
                    'x_offset': x_offset,
                    'y_offset': y_offset,
                    'original_x_mean': round(original_x_mean, 3),
                    'original_y_mean': round(original_y_mean, 3),
                    'new_x_mean': round(new_x_mean, 3),
                    'new_y_mean': round(new_y_mean, 3)
                }
            }
            
        except Exception as e:
            error_msg = f'保存校准失败: {str(e)}'
            print(f"❌ {error_msg}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return {'success': False, 'error': error_msg}
    
    def get_data_time_info(self, group_type: str, data_id: str) -> Dict:
        """
        获取数据的时间信息
        
        Args:
            group_type: 组类型 (control, mci, ad)
            data_id: 数据ID
            
        Returns:
            时间信息字典
        """
        try:
            print(f"🕐 获取时间信息: {group_type}/{data_id}")
            
            # 获取数据文件路径
            data_list = self.get_group_data(group_type)
            target_data = None
            
            for data_item in data_list:
                if data_item['data_id'] == data_id:
                    target_data = data_item
                    break
            
            if not target_data:
                return {'success': False, 'error': f'数据不存在: {data_id}'}
            
            file_path = target_data['file_path']
            
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'文件不存在: {file_path}'}
            
            # 读取数据文件
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                print(f"📊 读取数据: {len(df)} 行")
            except Exception as e:
                return {'success': False, 'error': f'读取文件失败: {str(e)}'}
            
            # 检查必要的列
            if 'milliseconds' not in df.columns:
                return {'success': False, 'error': '文件缺少时间列'}
            
            # 计算时间信息
            min_time = df['milliseconds'].min()
            max_time = df['milliseconds'].max()
            total_duration = max_time - min_time
            total_points = len(df)
            
            time_info = {
                'totalDuration': float(total_duration),  # 总时长（毫秒）
                'totalPoints': int(total_points),        # 总数据点数
                'minTime': float(min_time),              # 最小时间戳
                'maxTime': float(max_time),              # 最大时间戳
                'avgInterval': float(total_duration / max(total_points - 1, 1))  # 平均间隔
            }
            
            print(f"⏱️  时间信息: 总时长={total_duration:.1f}ms, 点数={total_points}, 间隔={time_info['avgInterval']:.1f}ms")
            
            return {
                'success': True,
                'data': time_info
            }
            
        except Exception as e:
            error_msg = f'获取时间信息失败: {str(e)}'
            print(f"❌ {error_msg}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return {'success': False, 'error': error_msg}
    
    def create_preview_calibrated_data(self, original_file: str, x_offset: float, y_offset: float,
                                     time_start: float = 0, time_end: float = 100) -> Optional[str]:
        """
        创建预览用的临时校准数据文件
        
        Args:
            original_file: 原始数据文件路径
            x_offset: X轴偏移量
            y_offset: Y轴偏移量
            
        Returns:
            临时文件路径，如果失败返回None
        """
        try:
            print(f"🔍 创建预览校准数据: {original_file}")
            print(f"📊 偏移量: X={x_offset:.3f}, Y={y_offset:.3f}")
            print(f"⏰ 时间范围: {time_start:.1f}% - {time_end:.1f}%")
            print(f"⏰ 时间范围: {time_start:.1f}% - {time_end:.1f}%")
            
            # 读取原始数据
            if not os.path.exists(original_file):
                print(f"❌ 原始文件不存在: {original_file}")
                return None
            
            try:
                df = pd.read_csv(original_file, encoding='utf-8')
                print(f"📊 读取数据: {len(df)} 行")
            except Exception as e:
                print(f"❌ 读取原始文件失败: {e}")
                return None
            
            # 检查必要的列
            if 'x' not in df.columns or 'y' not in df.columns:
                print(f"❌ 文件缺少x,y坐标列")
                return None
            
            # 创建数据副本
            df_preview = df.copy()
            
            # 应用时间范围过滤
            if 'milliseconds' in df_preview.columns and (time_start > 0 or time_end < 100):
                min_time = df_preview['milliseconds'].min()
                max_time = df_preview['milliseconds'].max()
                total_duration = max_time - min_time
                
                # 计算实际的时间范围
                actual_start_time = min_time + (total_duration * time_start / 100)
                actual_end_time = min_time + (total_duration * time_end / 100)
                
                # 过滤数据
                original_count = len(df_preview)
                df_preview = df_preview[
                    (df_preview['milliseconds'] >= actual_start_time) & 
                    (df_preview['milliseconds'] <= actual_end_time)
                ]
                filtered_count = len(df_preview)
                
                print(f"🎯 时间过滤: {original_count} → {filtered_count} 行 "
                      f"(时间范围: {actual_start_time:.1f}ms - {actual_end_time:.1f}ms)")
            
            # 应用坐标偏移
            df_preview['x'] = df_preview['x'] + x_offset
            df_preview['y'] = df_preview['y'] + y_offset
            
            # 创建临时文件路径
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_filename = f"preview_calibrated_{os.path.basename(original_file)}"
            temp_file = os.path.join(temp_dir, temp_filename)
            
            # 保存临时文件
            try:
                df_preview.to_csv(temp_file, index=False, encoding='utf-8')
                print(f"✅ 临时文件已创建: {temp_file}")
            except Exception as e:
                print(f"❌ 保存临时文件失败: {e}")
                return None
            
            return temp_file
            
        except Exception as e:
            print(f"❌ 创建预览数据失败: {e}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return None
    
    def delete_data_group(self, data_id: str) -> Dict:
        """删除数据组（包含该data_id的整个组）"""
        try:
            # 解析data_id以获取组信息
            if data_id.startswith('ad'):
                group_type = 'ad'
                group_num = data_id[2:data_id.find('q')]  # 从ad3q1中提取3
            elif data_id.startswith('m'):
                group_type = 'mci'
                group_num = data_id[1:data_id.find('q')]  # 从m3q1中提取3
            elif data_id.startswith('c'):
                group_type = 'control'
                group_num = data_id[1:data_id.find('q')]  # 从c3q1中提取3
            else:
                return {'success': False, 'error': '无效的data_id格式'}
            
            # 确定要删除的目录
            data_sources = self.config.get("data_sources", {})
            
            # 要删除的目录列表
            dirs_to_delete = []
            
            # 添加calibrated目录
            calibrated_dir = data_sources.get(f"{group_type}_calibrated", "")
            if calibrated_dir:
                group_dir = os.path.join(calibrated_dir, f"{group_type}_group_{group_num}")
                if os.path.exists(group_dir):
                    dirs_to_delete.append(group_dir)
            
            # 添加processed目录
            processed_dir = data_sources.get(f"{group_type}_processed", "")
            if processed_dir:
                group_dir = os.path.join(processed_dir, f"{group_type}_group_{group_num}")
                if os.path.exists(group_dir):
                    dirs_to_delete.append(group_dir)
            
            # 添加raw目录
            raw_dir = data_sources.get(f"{group_type}_raw", "")
            if raw_dir:
                group_dir = os.path.join(raw_dir, f"{group_type}_group_{group_num}")
                if os.path.exists(group_dir):
                    dirs_to_delete.append(group_dir)
            
            if not dirs_to_delete:
                return {'success': False, 'error': '未找到要删除的数据'}
            
            # 删除目录
            deleted_dirs = []
            for dir_path in dirs_to_delete:
                try:
                    import shutil
                    shutil.rmtree(dir_path)
                    deleted_dirs.append(dir_path)
                    print(f"🗑️ 已删除目录: {dir_path}")
                except Exception as e:
                    print(f"❌ 删除目录失败 {dir_path}: {e}")
            
            if deleted_dirs:
                return {
                    'success': True, 
                    'message': f'成功删除{len(deleted_dirs)}个目录',
                    'deleted_dirs': deleted_dirs
                }
            else:
                return {'success': False, 'error': '删除操作失败'}
                
        except Exception as e:
            print(f"❌ 删除数据组失败: {e}")
            return {'success': False, 'error': str(e)}

    def move_data_between_groups(self, data_id: str, from_group: str, to_group: str) -> Dict:
        """在不同组别之间移动数据"""
        try:
            # 解析data_id以获取组号和题目号
            if data_id.startswith('ad'):
                old_group_num = data_id[2:data_id.find('q')]
                question_num = data_id[data_id.find('q')+1:]
            elif data_id.startswith('m'):
                old_group_num = data_id[1:data_id.find('q')]
                question_num = data_id[data_id.find('q')+1:]
            elif data_id.startswith('c'):
                old_group_num = data_id[1:data_id.find('q')]
                question_num = data_id[data_id.find('q')+1:]
            else:
                return {'success': False, 'error': '无效的data_id格式'}
            
            # 获取新的组号
            new_group_num = self._get_next_group_number(to_group)
            
            # 构建新的data_id
            if to_group == 'ad':
                new_data_id = f"ad{new_group_num}q{question_num}"
            elif to_group == 'mci':
                new_data_id = f"m{new_group_num}q{question_num}"
            elif to_group == 'control':
                new_data_id = f"c{new_group_num}q{question_num}"
            else:
                return {'success': False, 'error': '无效的目标组别'}
            
            data_sources = self.config.get("data_sources", {})
            moved_files = []
            
            # 移动每种类型的数据
            for data_type in ['calibrated', 'processed', 'raw']:
                # 源目录
                src_dir_key = f"{from_group}_{data_type}"
                src_base_dir = data_sources.get(src_dir_key, "")
                if not src_base_dir:
                    continue
                
                src_group_dir = os.path.join(src_base_dir, f"{from_group}_group_{old_group_num}")
                
                # 目标目录
                dst_dir_key = f"{to_group}_{data_type}"
                dst_base_dir = data_sources.get(dst_dir_key, "")
                if not dst_base_dir:
                    continue
                
                dst_group_dir = os.path.join(dst_base_dir, f"{to_group}_group_{new_group_num}")
                
                # 如果源目录存在，则移动整个目录
                if os.path.exists(src_group_dir):
                    # 确保目标目录不存在（避免覆盖）
                    if os.path.exists(dst_group_dir):
                        import shutil
                        shutil.rmtree(dst_group_dir)
                    
                    # 创建目标目录的父目录
                    os.makedirs(os.path.dirname(dst_group_dir), exist_ok=True)
                    
                    # 移动目录
                    import shutil
                    shutil.move(src_group_dir, dst_group_dir)
                    moved_files.append(f"{data_type}: {src_group_dir} -> {dst_group_dir}")
                    print(f"📁 移动目录: {src_group_dir} -> {dst_group_dir}")
                    
                    # 重命名目录内的文件（更新文件名中的组别标识）
                    self._rename_files_in_moved_directory(dst_group_dir, old_data_id=data_id, new_data_id=new_data_id, from_group=from_group, to_group=to_group)
            
            if moved_files:
                return {
                    'success': True,
                    'message': f'成功将数据从{from_group}组移动到{to_group}组',
                    'new_data_id': new_data_id,
                    'moved_files': moved_files
                }
            else:
                return {'success': False, 'error': '未找到要移动的数据'}
                
        except Exception as e:
            print(f"❌ 移动数据失败: {e}")
            return {'success': False, 'error': str(e)}

    def _rename_files_in_moved_directory(self, directory: str, old_data_id: str, new_data_id: str, from_group: str, to_group: str):
        """重命名移动后目录中的文件"""
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    # 生成新文件名
                    new_filename = self._generate_new_filename(filename, old_data_id, new_data_id, from_group, to_group)
                    if new_filename != filename:
                        new_file_path = os.path.join(directory, new_filename)
                        os.rename(file_path, new_file_path)
                        print(f"📄 重命名文件: {filename} -> {new_filename}")
        except Exception as e:
            print(f"❌ 重命名文件失败: {e}")

    def _generate_new_filename(self, filename: str, old_data_id: str, new_data_id: str, from_group: str, to_group: str) -> str:
        """生成新的文件名"""
        try:
            # 从filename中提取组号和问题号
            parsed_old = self.parse_data_filename(filename, from_group)
            if not parsed_old:
                print(f"⚠️ 无法解析文件名: {filename}")
                return filename
            
            old_group_num = parsed_old['group_num']
            question_num = parsed_old['question_num']
            
            # 从new_data_id中提取新的组号
            if new_data_id.startswith('ad'):
                new_group_num = new_data_id[2:].split('q')[0]
            else:
                new_group_num = new_data_id[1:].split('q')[0]
            
            # 根据目标组确定新的文件前缀
            if to_group == 'control':
                new_prefix = 'n'
            elif to_group == 'mci':
                new_prefix = 'm'
            elif to_group == 'ad':
                new_prefix = 'ad'
            else:
                return filename
            
            # 构建新的文件名前缀
            new_file_prefix = f"{new_prefix}{new_group_num}q{question_num}"
            
            # 找到原文件名中的旧前缀部分
            if from_group == 'control':
                old_file_prefix = f"n{old_group_num}q{question_num}"
            elif from_group == 'mci':
                old_file_prefix = f"m{old_group_num}q{question_num}"
            elif from_group == 'ad':
                old_file_prefix = f"ad{old_group_num}q{question_num}"
            else:
                return filename
            
            # 替换文件名中的前缀部分
            if old_file_prefix in filename:
                new_filename = filename.replace(old_file_prefix, new_file_prefix)
                print(f"📄 重命名文件: {filename} -> {new_filename}")
                return new_filename
            else:
                # 如果直接替换不行，返回原文件名
                print(f"⚠️ 无法在文件名 {filename} 中找到前缀 {old_file_prefix}，保持原名")
                return filename
                
        except Exception as e:
            print(f"❌ 文件重命名错误: {e}")
            return filename

    def run_server(self, host: str = '127.0.0.1', port: int = 8080, 
                   debug: bool = False, open_browser: bool = True):
        """
        运行Web服务器
        
        Args:
            host: 主机地址
            port: 端口号
            debug: 调试模式
            open_browser: 是否自动打开浏览器
        """
        print(f"🌐 启动增强版Web可视化服务器")
        print(f"📍 地址: http://{host}:{port}")
        print(f"🔍 ROI定义数量: {len(self.analyzer.roi_definitions)}")
        print(f"🎨 可视化功能: ROI绘制、轨迹分析、序列标记")
        print("=" * 60)
        
        if open_browser:
            # 延迟打开浏览器
            import threading
            import time
            def open_browser_delayed():
                time.sleep(1.5)
                webbrowser.open(f'http://{host}:{port}')
            
            threading.Thread(target=open_browser_delayed, daemon=True).start()
        
        try:
            self.app.run(host=host, port=port, debug=debug)
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")

    def fix_existing_data_files(self, group_type: str = None) -> Dict:
        """
        修复现有数据文件，为缺少milliseconds列的数据添加该列
        
        Args:
            group_type: 指定组类型，如果为None则处理所有组
            
        Returns:
            修复结果统计
        """
        try:
            print(f"🔧 开始修复现有数据文件...")
            
            stats = {
                'total_files': 0,
                'fixed_files': 0,
                'already_ok_files': 0,
                'error_files': 0,
                'details': []
            }
            
            # 确定要处理的组类型
            if group_type:
                group_types = [group_type]
            else:
                group_types = ['control', 'mci', 'ad']
            
            for gt in group_types:
                print(f"\n📁 处理 {gt} 组数据...")
                
                # 获取该组的所有数据
                data_list = self.get_group_data(gt)
                
                for data_item in data_list:
                    stats['total_files'] += 1
                    file_path = data_item['file_path']
                    data_id = data_item['data_id']
                    
                    try:
                        # 读取文件
                        if not os.path.exists(file_path):
                            print(f"⚠️  文件不存在: {file_path}")
                            stats['error_files'] += 1
                            continue
                        
                        df = pd.read_csv(file_path, encoding='utf-8')
                        
                        # 检查是否已经有milliseconds列
                        if 'milliseconds' in df.columns:
                            print(f"✅ {data_id}: 已有milliseconds列，跳过")
                            stats['already_ok_files'] += 1
                            continue
                        
                        print(f"🔧 {data_id}: 添加milliseconds列...")
                        
                        # 检查是否有timestamp列
                        if 'timestamp' not in df.columns:
                            print(f"❌ {data_id}: 缺少timestamp列，无法修复")
                            stats['error_files'] += 1
                            stats['details'].append(f"{data_id}: 缺少timestamp列")
                            continue
                        
                        # 添加milliseconds列
                        max_timestamp = df['timestamp'].max()
                        
                        if max_timestamp < 10000:  # 相对时间值（秒）
                            # 转换为毫秒时间戳
                            import time
                            current_time_ms = int(time.time() * 1000)
                            df['milliseconds'] = current_time_ms + (df['timestamp'] * 1000).astype(int)
                            print(f"   转换相对时间戳: {df['timestamp'].min():.3f}s-{df['timestamp'].max():.3f}s -> {df['milliseconds'].min()}-{df['milliseconds'].max()}")
                        else:
                            # 直接使用作为毫秒时间戳
                            df['milliseconds'] = df['timestamp'].astype(int)
                            print(f"   使用现有时间戳: {df['milliseconds'].min()}-{df['milliseconds'].max()}")
                        
                        # 检查是否缺少其他兼容性列
                        added_columns = []
                        
                        # 添加度数列（如果缺少）
                        if 'x_deg' not in df.columns and 'x' in df.columns:
                            fov_deg = 110.0  # 默认视场角
                            df['x_deg'] = (df['x'] - 0.5) * fov_deg
                            added_columns.append('x_deg')
                        
                        if 'y_deg' not in df.columns and 'y' in df.columns:
                            fov_deg = 110.0  # 默认视场角
                            df['y_deg'] = (df['y'] - 0.5) * fov_deg
                            added_columns.append('y_deg')
                        
                        # 添加角速度列（如果缺少）
                        if 'velocity_deg_s' not in df.columns:
                            df['velocity_deg_s'] = 0.0
                            
                            # 如果有时间差列，计算角速度
                            if 'time_diff' in df.columns and 'x_deg' in df.columns and 'y_deg' in df.columns:
                                for i in range(1, len(df)):
                                    dt = df.iloc[i]['time_diff'] / 1000.0  # 转换为秒
                                    if dt > 0:
                                        dx_deg = df.iloc[i]['x_deg'] - df.iloc[i-1]['x_deg']
                                        dy_deg = df.iloc[i]['y_deg'] - df.iloc[i-1]['y_deg']
                                        
                                        import math
                                        angular_distance = math.sqrt(dx_deg**2 + dy_deg**2)
                                        velocity_deg_s = angular_distance / dt
                                        
                                        df.iloc[i, df.columns.get_loc('velocity_deg_s')] = velocity_deg_s
                            
                            added_columns.append('velocity_deg_s')
                        
                        if added_columns:
                            print(f"   添加的列: {', '.join(added_columns)}")
                        
                        # 保存修复后的文件
                        df.to_csv(file_path, index=False, encoding='utf-8')
                        print(f"✅ {data_id}: 修复完成")
                        stats['fixed_files'] += 1
                        stats['details'].append(f"{data_id}: 成功添加 {', '.join(['milliseconds'] + added_columns)}")
                        
                    except Exception as e:
                        print(f"❌ {data_id}: 修复失败 - {str(e)}")
                        stats['error_files'] += 1
                        stats['details'].append(f"{data_id}: 错误 - {str(e)}")
                        continue
            
            print(f"\n📊 修复完成统计:")
            print(f"   总文件数: {stats['total_files']}")
            print(f"   修复文件数: {stats['fixed_files']}")
            print(f"   已正常文件数: {stats['already_ok_files']}")
            print(f"   错误文件数: {stats['error_files']}")
            
            if stats['details']:
                print(f"\n📋 详细信息:")
                for detail in stats['details']:
                    print(f"   {detail}")
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            error_msg = f'修复数据文件失败: {str(e)}'
            print(f"❌ {error_msg}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return {'success': False, 'error': error_msg}

    def _load_background_images(self):
        """加载背景图片列表"""
        try:
            background_dir = "data/background_images"
            if os.path.exists(background_dir):
                self.background_images = [f for f in os.listdir(background_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
                print(f"📷 加载了 {len(self.background_images)} 个背景图片")
            else:
                print(f"⚠️  背景图片目录不存在: {background_dir}")
                self.background_images = []
        except Exception as e:
            print(f"❌ 加载背景图片失败: {e}")
            self.background_images = []

    def _load_mmse_scores(self):
        """加载MMSE分数数据"""
        try:
            mmse_dir = "data/MMSE_Score"
            self.mmse_scores = {
                'control': {},
                'mci': {},
                'ad': {}
            }
            
            # 文件映射
            mmse_files = {
                'control': '控制组.csv',
                'mci': '轻度认知障碍组.csv', 
                'ad': '阿尔兹海默症组.csv'
            }
            
            for group_type, filename in mmse_files.items():
                file_path = os.path.join(mmse_dir, filename)
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path, encoding='utf-8')
                    for _, row in df.iterrows():
                        # 处理列名差异：有些文件用"受试者"，有些用"试者"
                        if '受试者' in df.columns:
                            subject_id = row['受试者']
                        elif '试者' in df.columns:
                            subject_id = row['试者']
                        else:
                            print(f"⚠️  {filename} 文件中找不到受试者列")
                            continue
                        # 解析组编号
                        group_num = self.parse_subject_id(subject_id)
                        if group_num:
                            self.mmse_scores[group_type][group_num] = {
                                'subject_id': subject_id,
                                'total_score': row['总分'],
                                'details': {
                                    # Q1: 时间定向 (年份,季节,月份,星期)
                                    'q1_orientation_time': {
                                        '年份': row['年份'],
                                        '季节': row['季节'], 
                                        '月份': row['月份'],
                                        '星期': row['星期']
                                    },
                                    # Q2: 地点定向 (省市区,街道,建筑,楼层)
                                    'q2_orientation_place': {
                                        '省市区': row['省市区'],
                                        '街道': row['街道'],
                                        '建筑': row['建筑'],
                                        '楼层': row['楼层']
                                    },
                                    # Q3: 即刻记忆
                                    'q3_immediate_memory': row['即刻记忆'],
                                    # Q4: 计算能力 (100-7,93-7,86-7,79-7,72-7)
                                    'q4_calculation': {
                                        '100-7': row['100-7'],
                                        '93-7': row['93-7'],
                                        '86-7': row['86-7'],
                                        '79-7': row['79-7'],
                                        '72-7': row['72-7']
                                    },
                                    # Q5: 延迟回忆 (词1,词2,词3)
                                    'q5_delayed_recall': {
                                        '词1': row['词1'],
                                        '词2': row['词2'],
                                        '词3': row['词3']
                                    }
                                }
                            }
                    print(f"📊 加载了 {len(self.mmse_scores[group_type])} 个{group_type}组MMSE分数")
                else:
                    print(f"⚠️  MMSE文件不存在: {file_path}")
            
            total_scores = sum(len(scores) for scores in self.mmse_scores.values())
            print(f"🧠 总共加载了 {total_scores} 个MMSE分数记录")
            
        except Exception as e:
            print(f"❌ 加载MMSE分数失败: {e}")
            import traceback
            traceback.print_exc()
            self.mmse_scores = {'control': {}, 'mci': {}, 'ad': {}}

    def parse_subject_id(self, subject_id: str) -> Optional[int]:
        """
        解析受试者ID获取组编号
        
        Args:
            subject_id: 受试者ID (如 n01, M01, ad01)
            
        Returns:
            组编号 (如 1, 2, 3...)
        """
        try:
            import re
            # 匹配 n01, M01, ad01 等格式
            match = re.match(r'[a-zA-Z]+(\d+)', subject_id)
            if match:
                return int(match.group(1))
            return None
        except:
            return None

    def get_mmse_score(self, group_type: str, group_num: int) -> Optional[Dict]:
        """
        获取指定组的MMSE分数
        
        Args:
            group_type: 组类型 (control, mci, ad)
            group_num: 组编号
            
        Returns:
            MMSE分数信息
        """
        try:
            return self.mmse_scores.get(group_type, {}).get(group_num)
        except:
            return None

    def get_mmse_assessment_level(self, score: int) -> Dict:
        """
        根据VR-MMSE分数获取认知评估等级
        
        VR-MMSE分类标准:
        - 正常组：19.1±1.6 (约17.5-20.7)
        - MCI组：18.0±1.9 (约16.1-19.9)  
        - AD组：13.5±2.7 (约10.8-16.2)
        
        Args:
            score: VR-MMSE总分
            
        Returns:
            评估等级信息
        """
        if score >= 20:
            return {'level': '正常', 'color': '#28a745', 'description': '认知功能正常'}
        elif score >= 19:
            return {'level': '正常范围', 'color': '#17a2b8', 'description': '认知功能正常范围'}
        elif score >= 16:
            return {'level': '轻度认知障碍', 'color': '#ffc107', 'description': '轻度认知障碍(MCI)'}
        elif score >= 11:
            return {'level': '阿尔兹海默症', 'color': '#fd7e14', 'description': '阿尔兹海默症(AD)'}
        else:
            return {'level': '重度认知障碍', 'color': '#dc3545', 'description': '重度认知障碍'}



def main():
    """主函数 - 用于测试"""
    visualizer = EnhancedWebVisualizer()
    print("🌐 增强版Web可视化器")
    print("=" * 50)
    print("功能特性:")
    print("  - 多层ROI绘制 (keywords, instructions, background)")
    print("  - 事件类型可视化 (固视/扫视)")
    print("  - ROI序列标记 (Enter/Exit)")
    print("  - 增强统计面板")
    print("  - 背景图像支持")
    print("\n使用示例:")
    print("visualizer = EnhancedWebVisualizer()")
    print("visualizer.run_server(port=8080)")

if __name__ == "__main__":
    main() 