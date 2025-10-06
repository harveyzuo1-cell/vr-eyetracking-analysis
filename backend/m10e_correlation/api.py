"""
模块10-E API接口
提供MMSE预测关联性深度可视化分析的REST API
"""
import logging
import numpy as np
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from .correlation_analyzer import CorrelationAnalyzer

# 设置日志
logger = logging.getLogger(__name__)

# 创建蓝图
correlation_bp = Blueprint('m10e_correlation', __name__)

# 全局分析器实例
analyzer = CorrelationAnalyzer()

@correlation_bp.route('/correlation-analysis', methods=['POST'])
def perform_correlation_analysis():
    """
    执行关联性分析
    
    Request Body:
        {
            "config": "m2_tau1_eps0.055_lmin2",
            "analysis_type": "correlation|agreement|diagnostic|comprehensive",
            "include_3d": true
        }
    
    Returns:
        JSON格式的关联性分析结果
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        config = data.get('config')
        dataset_id = data.get('dataset_id')  # 支持dataset_id参数
        analysis_type = data.get('analysis_type', 'correlation')
        include_3d = data.get('include_3d', False)
        
        # 如果config是60位成员数据集的ID，使用dataset_id参数
        if config in ['sim_60_members', 'default']:
            dataset_id = config
            config = 'default'  # 使用默认配置
        
        if not config and not dataset_id:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: config 或 dataset_id"
            }), 400
        
        logger.info(f"开始关联性分析: config={config}, dataset={dataset_id}, type={analysis_type}, 3d={include_3d}")
        
        # 执行分析
        results = analyzer.analyze_correlation(
            rqa_sig=config,
            analysis_type=analysis_type,
            include_3d=include_3d,
            dataset_id=dataset_id  # 传递dataset_id
        )
        
        if results.get("success"):
            logger.info(f"关联性分析完成: {config}")
            return jsonify(results)
        else:
            logger.error(f"关联性分析失败: {results.get('error')}")
            return jsonify(results), 400
            
    except Exception as e:
        logger.error(f"关联性分析API错误: {e}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}"
        }), 500

@correlation_bp.route('/available-configs', methods=['GET'])
def get_available_configs():
    """
    获取可用的配置列表（复用模块10-D的配置）
    """
    try:
        configs = analyzer.get_available_configs()
        
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

@correlation_bp.route('/model-configs', methods=['GET'])
def get_model_configs():
    """
    获取可用的模型配置（包括60位成员数据集）
    """
    try:
        # 获取可用模型列表
        models = analyzer.get_available_models()
        
        # 转换为前端需要的格式
        configs = []
        for model in models:
            configs.append({
                "id": model["id"],
                "name": model["name"],
                "description": model.get("description", ""),
                "model_count": 5 if model["status"] == "available" else 0,
                "complete": model["status"] == "available",
                "status": model["status"]
            })
        
        return jsonify({
            "success": True,
            "configs": configs,
            "total_count": len(configs)
        })
        
    except Exception as e:
        logger.error(f"获取模型配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "configs": []
        }), 500

@correlation_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "m10e-correlation-analysis"
    })
