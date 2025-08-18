"""
模块10-D API接口
提供性能评估、数据导出等REST API
"""
import logging
from flask import Blueprint, request, jsonify, make_response
from typing import Dict, Any

from .evaluator import ModelEvaluator

# 设置日志
logger = logging.getLogger(__name__)

# 创建蓝图
evaluation_bp = Blueprint('m10d_evaluation', __name__)

# 全局评估器实例
evaluator = ModelEvaluator()

@evaluation_bp.route('/performance', methods=['GET'])
def get_performance_analysis():
    """
    获取模型性能分析
    
    Query Parameters:
        config: 模型配置ID (必需)
        include_groups: 是否包含分组分析 (可选，默认false)
    
    Returns:
        JSON格式的性能分析结果
    """
    try:
        # 获取参数
        config = request.args.get('config')
        include_groups = request.args.get('include_groups', 'false').lower() == 'true'
        
        if not config:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: config"
            }), 400
        
        logger.info(f"开始性能分析: config={config}, include_groups={include_groups}")
        
        # 执行评估
        results = evaluator.evaluate_model_set(config, include_groups)
        
        if results.get("success"):
            logger.info(f"性能分析完成: {config}")
            return jsonify(results)
        else:
            logger.error(f"性能分析失败: {results.get('error')}")
            return jsonify(results), 400
            
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}"
        }), 500

@evaluation_bp.route('/configs', methods=['GET'])
def get_available_configs():
    """
    获取可用的模型配置列表
    
    Returns:
        可用配置的JSON列表
    """
    try:
        configs = evaluator.get_available_configs()
        
        return jsonify({
            "success": True,
            "configs": configs,
            "total_count": len(configs)
        })
        
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@evaluation_bp.route('/task-analysis/<task>', methods=['GET'])
def get_task_analysis(task: str):
    """
    获取特定任务的详细分析
    
    Args:
        task: 任务ID (Q1-Q5)
        
    Query Parameters:
        config: 模型配置ID (必需)
    
    Returns:
        特定任务的详细分析结果
    """
    try:
        config = request.args.get('config')
        
        if not config:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: config"
            }), 400
        
        if task not in evaluator.tasks:
            return jsonify({
                "success": False,
                "error": f"无效任务: {task}，支持的任务: {', '.join(evaluator.tasks)}"
            }), 400
        
        # 获取完整评估结果
        results = evaluator.evaluate_model_set(config, include_groups=True)
        
        if not results.get("success"):
            return jsonify(results), 400
        
        # 提取特定任务的数据
        task_index = evaluator.tasks.index(task)
        task_results = {
            "success": True,
            "task": task,
            "config": config,
            "metrics": results["task_metrics"][task],
            "individual_errors": [row[task_index] for row in results["residual_data"]["individual_errors"]],
            "avg_error": results["residual_data"]["avg_errors"][task_index],
            "std_error": results["residual_data"]["std_errors"][task_index],
            "avg_actual": results["task_comparison"]["avg_actuals"][task_index]
        }
        
        # 添加分组数据
        if "group_analysis" in results:
            task_results["group_analysis"] = {
                group: {
                    "mean_error": stats["mean_errors"][task_index],
                    "std_error": stats["std_errors"][task_index],
                    "sample_count": stats["sample_count"]
                }
                for group, stats in results["group_analysis"].items()
            }
        
        return jsonify(task_results)
        
    except Exception as e:
        logger.error(f"任务分析失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@evaluation_bp.route('/export/data', methods=['GET'])
def export_evaluation_data():
    """
    导出评估数据
    
    Query Parameters:
        config: 模型配置ID (必需)
        format: 导出格式 (csv|json，默认csv)
    
    Returns:
        导出的数据文件
    """
    try:
        config = request.args.get('config')
        format_type = request.args.get('format', 'csv').lower()
        
        if not config:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: config"
            }), 400
        
        if format_type not in ['csv', 'json']:
            return jsonify({
                "success": False,
                "error": "不支持的导出格式，支持: csv, json"
            }), 400
        
        # 导出数据
        exported_data = evaluator.export_data(config, format_type)
        
        if exported_data is None:
            return jsonify({
                "success": False,
                "error": "数据导出失败"
            }), 500
        
        # 创建响应
        if format_type == 'csv':
            response = make_response(exported_data)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=performance_analysis_{config}.csv'
        else:  # json
            response = make_response(exported_data)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=performance_analysis_{config}.json'
        
        return response
        
    except Exception as e:
        logger.error(f"数据导出失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@evaluation_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 简单检查评估器状态
        configs = evaluator.get_available_configs()
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "available_configs": len(configs),
            "device": str(evaluator.device)
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500

# 错误处理
@evaluation_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "API端点未找到"
    }), 404

@evaluation_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500
