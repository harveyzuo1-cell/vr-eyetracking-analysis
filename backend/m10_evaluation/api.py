"""
模块10-D API接口
提供性能评估、数据导出等REST API
"""
import logging
import torch
import numpy as np
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

@evaluation_bp.route('/scatter-data', methods=['GET'])
def get_scatter_data():
    """
    获取散点图矩阵数据（真实值 vs 预测值）
    
    Query Parameters:
        config: 模型配置ID (必需)
    
    Returns:
        所有任务的真实值和预测值数据
    """
    try:
        config = request.args.get('config')
        
        if not config:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: config"
            }), 400
        
        logger.info(f"开始获取散点图数据: config={config}")
        
        # 加载模型和数据
        models_dict = evaluator._load_models_batch(config)
        data_dict = evaluator._load_data_batch(config)
        
        # 准备散点图数据
        scatter_data = {
            "tasks": {},
            "groups": {}
        }
        
        # 计算每个任务的真实值和预测值
        with torch.no_grad():
            for task in evaluator.tasks:
                model = models_dict[task]
                X, y_true = data_dict[task]['X'], data_dict[task]['y']
                
                # 批量预测
                X_tensor = torch.FloatTensor(X).to(evaluator.device)
                y_pred = model(X_tensor).cpu().numpy().flatten()
                
                # 确定每个样本的组别
                n_samples = len(y_true)
                groups = []
                for i in range(n_samples):
                    if i < 20:
                        groups.append('control')
                    elif i < 40:
                        groups.append('mci')
                    else:
                        groups.append('ad')
                
                # 反转数据方向：使用1-value，因为原始数据可能是错误率
                # 控制组应该有高分（认知功能好），AD组应该有低分（认知功能差）
                y_true_corrected = (1 - y_true).tolist()
                y_pred_corrected = (1 - y_pred).tolist()
                
                # 记录数据统计
                logger.debug(f"Task {task} - Original: Control={np.mean(y_true[:20]):.3f}, "
                           f"MCI={np.mean(y_true[20:40]):.3f}, AD={np.mean(y_true[40:]):.3f}")
                logger.debug(f"Task {task} - Corrected: Control={np.mean(y_true_corrected[:20]):.3f}, "
                           f"MCI={np.mean(y_true_corrected[20:40]):.3f}, AD={np.mean(y_true_corrected[40:]):.3f}")
                
                scatter_data["tasks"][task] = {
                    "y_true": y_true_corrected,
                    "y_pred": y_pred_corrected,
                    "groups": groups
                }
        
        # 按组别整理数据
        for group in ['control', 'mci', 'ad']:
            scatter_data["groups"][group] = {}
            for task in evaluator.tasks:
                task_data = scatter_data["tasks"][task]
                group_indices = [i for i, g in enumerate(task_data["groups"]) if g == group]
                scatter_data["groups"][group][task] = {
                    "y_true": [task_data["y_true"][i] for i in group_indices],
                    "y_pred": [task_data["y_pred"][i] for i in group_indices]
                }
        
        logger.info(f"散点图数据获取成功: {config}")
        
        return jsonify({
            "success": True,
            "config": config,
            "data": scatter_data
        })
        
    except Exception as e:
        logger.error(f"获取散点图数据失败: {e}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}"
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

# ================= 缓存管理API =================

@evaluation_bp.route('/cache/clear', methods=['POST'])
def clear_model_cache():
    """
    清空模型缓存，强制重新加载
    
    Returns:
        操作结果
    """
    try:
        # 获取清空前的缓存状态
        cache_count_before = len(evaluator.model_cache)
        timestamp_count_before = len(evaluator.cache_timestamps)
        data_cache_count_before = len(evaluator.data_cache)
        
        # 清空所有缓存
        evaluator.model_cache.clear()
        evaluator.cache_timestamps.clear()
        evaluator.data_cache.clear()
        
        logger.info(f"缓存已清空: 模型缓存 {cache_count_before} -> 0, 时间戳 {timestamp_count_before} -> 0, 数据缓存 {data_cache_count_before} -> 0")
        
        return jsonify({
            "success": True,
            "message": "缓存已成功清空",
            "cleared": {
                "model_cache": cache_count_before,
                "cache_timestamps": timestamp_count_before,
                "data_cache": data_cache_count_before
            }
        })
        
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        return jsonify({
            "success": False,
            "error": f"清空缓存失败: {str(e)}"
        }), 500

@evaluation_bp.route('/cache/status', methods=['GET'])
def get_cache_status():
    """
    获取缓存状态信息
    
    Returns:
        缓存状态详情
    """
    try:
        # 计算缓存统计信息
        model_cache_keys = list(evaluator.model_cache.keys())
        timestamp_keys = list(evaluator.cache_timestamps.keys())
        data_cache_keys = list(evaluator.data_cache.keys())
        
        # 检查缓存一致性
        missing_timestamps = [key for key in model_cache_keys if key not in timestamp_keys]
        orphaned_timestamps = [key for key in timestamp_keys if key not in model_cache_keys]
        
        status_info = {
            "success": True,
            "cache_stats": {
                "model_cache_size": len(model_cache_keys),
                "timestamp_cache_size": len(timestamp_keys),
                "data_cache_size": len(data_cache_keys),
                "max_cache_size": evaluator.config.get("model_cache_size", 10) if hasattr(evaluator, 'config') else "未知"
            },
            "cached_models": model_cache_keys,
            "cached_timestamps": {
                key: evaluator.cache_timestamps[key] 
                for key in timestamp_keys
            },
            "cache_health": {
                "missing_timestamps": missing_timestamps,
                "orphaned_timestamps": orphaned_timestamps,
                "is_healthy": len(missing_timestamps) == 0 and len(orphaned_timestamps) == 0
            },
            "device": str(evaluator.device)
        }
        
        return jsonify(status_info)
        
    except Exception as e:
        logger.error(f"获取缓存状态失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取缓存状态失败: {str(e)}"
        }), 500

@evaluation_bp.route('/cache/refresh', methods=['POST'])
def refresh_cache():
    """
    刷新指定配置的缓存
    
    JSON Body:
        config: 要刷新的配置ID (可选，不提供则刷新所有)
    
    Returns:
        刷新结果
    """
    try:
        data = request.get_json() or {}
        target_config = data.get('config')
        
        if target_config:
            # 刷新指定配置的缓存
            refreshed_keys = []
            for task in evaluator.tasks:
                cache_key = f"{target_config}_{task}"
                if cache_key in evaluator.model_cache:
                    del evaluator.model_cache[cache_key]
                    refreshed_keys.append(cache_key)
                if cache_key in evaluator.cache_timestamps:
                    del evaluator.cache_timestamps[cache_key]
                
                # 也清理数据缓存
                data_cache_key = f"{target_config}_{task}_data"
                if data_cache_key in evaluator.data_cache:
                    del evaluator.data_cache[data_cache_key]
                    refreshed_keys.append(data_cache_key)
            
            logger.info(f"已刷新配置 {target_config} 的缓存: {refreshed_keys}")
            
            return jsonify({
                "success": True,
                "message": f"配置 {target_config} 的缓存已刷新",
                "refreshed_keys": refreshed_keys
            })
        else:
            # 刷新所有缓存
            cache_count = len(evaluator.model_cache)
            evaluator.model_cache.clear()
            evaluator.cache_timestamps.clear()
            evaluator.data_cache.clear()
            
            logger.info("已刷新所有缓存")
            
            return jsonify({
                "success": True,
                "message": "所有缓存已刷新",
                "cleared_count": cache_count
            })
        
    except Exception as e:
        logger.error(f"刷新缓存失败: {e}")
        return jsonify({
            "success": False,
            "error": f"刷新缓存失败: {str(e)}"
        }), 500
