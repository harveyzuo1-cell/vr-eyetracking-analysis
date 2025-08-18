"""
预测API路由
==========

提供模型推理接口，支持单次预测和批量预测。
"""

from flask import Blueprint, request, jsonify
from typing import List, Literal
import logging

from .loader import ModelManager
from .config import VALID_Q_TAGS

logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint("m10_predict", __name__)

# 尝试导入Pydantic，如果失败则使用简单验证
try:
    from pydantic import BaseModel, ValidationError, conlist
    
    class PredictRequest(BaseModel):
        """预测请求模型"""
        q_tag: Literal["Q1", "Q2", "Q3", "Q4", "Q5"]
        features: List[float]  # 10个特征
        
        def __post_init__(self):
            if len(self.features) != 10:
                raise ValueError("特征数量必须为10")

    class BatchPredictRequest(BaseModel):
        """批量预测请求模型"""
        q_tag: Literal["Q1", "Q2", "Q3", "Q4", "Q5"] 
        samples: List[List[float]]  # 多个样本
        
        def __post_init__(self):
            for i, sample in enumerate(self.samples):
                if len(sample) != 10:
                    raise ValueError(f"样本{i}特征数量必须为10")

    PYDANTIC_AVAILABLE = True
    
except ImportError:
    # 如果没有Pydantic，使用简单的字典验证
    class ValidationError(Exception):
        def __init__(self, errors):
            self.errors = lambda: errors
            super().__init__(str(errors))
    
    class PredictRequest:
        def __init__(self, q_tag, features):
            if q_tag not in VALID_Q_TAGS:
                raise ValidationError([{"msg": "无效的任务标签"}])
            if not isinstance(features, list) or len(features) != 10:
                raise ValidationError([{"msg": "特征必须为长度为10的列表"}])
            self.q_tag = q_tag
            self.features = features
        
        @classmethod
        def parse_raw(cls, data):
            import json
            obj = json.loads(data)
            return cls(obj["q_tag"], obj["features"])
    
    class BatchPredictRequest:
        def __init__(self, q_tag, samples):
            if q_tag not in VALID_Q_TAGS:
                raise ValidationError([{"msg": "无效的任务标签"}])
            if not isinstance(samples, list):
                raise ValidationError([{"msg": "samples必须为列表"}])
            for i, sample in enumerate(samples):
                if not isinstance(sample, list) or len(sample) != 10:
                    raise ValidationError([{"msg": f"样本{i}必须为长度为10的列表"}])
            self.q_tag = q_tag
            self.samples = samples
        
        @classmethod
        def parse_raw(cls, data):
            import json
            obj = json.loads(data)
            return cls(obj["q_tag"], obj["samples"])
    
    PYDANTIC_AVAILABLE = False


@bp.route("/predict", methods=["POST"])
def predict():
    """
    单次MMSE子分数预测
    
    请求格式:
    {
        "q_tag": "Q1",
        "features": [0.1, 0.4, 0.3, 0.2, 0.5, 0.6, 0.3, 0.7, 0.2, 0.8]
    }
    
    响应格式:
    {
        "success": true,
        "score": 0.85,
        "q_tag": "Q1",
        "model_info": {
            "sig": "m2_tau1_eps0.055_lmin2",
            "version": "best"
        }
    }
    """
    try:
        # 解析请求数据
        req_data = PredictRequest.parse_raw(request.data)
        
        # 执行预测
        score = ModelManager.predict(req_data.q_tag, req_data.features)
        
        # 获取当前激活的模型信息
        active_models = ModelManager.get_active_models()
        model_info = active_models.get(req_data.q_tag, {})
        
        logger.info(f"预测完成: {req_data.q_tag} -> {score:.4f}")
        
        return jsonify({
            "success": True,
            "score": score,
            "q_tag": req_data.q_tag,
            "model_info": model_info
        })
        
    except ValidationError as e:
        logger.warning(f"请求验证失败: {e}")
        return jsonify({
            "success": False,
            "error": "请求格式错误",
            "details": e.errors()
        }), 400
        
    except RuntimeError as e:
        logger.error(f"预测失败: {e}")
        return jsonify({
            "success": False,
            "error": "预测失败",
            "message": str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"预测异常: {e}")
        return jsonify({
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500


@bp.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    批量MMSE子分数预测
    
    请求格式:
    {
        "q_tag": "Q1",
        "samples": [
            [0.1, 0.4, 0.3, 0.2, 0.5, 0.6, 0.3, 0.7, 0.2, 0.8],
            [0.2, 0.3, 0.4, 0.1, 0.6, 0.5, 0.4, 0.8, 0.1, 0.9]
        ]
    }
    
    响应格式:
    {
        "success": true,
        "results": [0.85, 0.72],
        "q_tag": "Q1",
        "count": 2,
        "model_info": {...}
    }
    """
    try:
        # 解析请求数据
        req_data = BatchPredictRequest.parse_raw(request.data)
        
        # 批量预测
        results = []
        for i, features in enumerate(req_data.samples):
            try:
                score = ModelManager.predict(req_data.q_tag, features)
                results.append(score)
            except Exception as e:
                logger.error(f"样本 {i} 预测失败: {e}")
                results.append(None)  # 标记失败
        
        # 获取模型信息
        active_models = ModelManager.get_active_models()
        model_info = active_models.get(req_data.q_tag, {})
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"批量预测完成: {req_data.q_tag}, {success_count}/{len(results)} 成功")
        
        return jsonify({
            "success": True,
            "results": results,
            "q_tag": req_data.q_tag,
            "count": len(results),
            "success_count": success_count,
            "model_info": model_info
        })
        
    except ValidationError as e:
        logger.warning(f"批量请求验证失败: {e}")
        return jsonify({
            "success": False,
            "error": "请求格式错误",
            "details": e.errors()
        }), 400
        
    except Exception as e:
        logger.error(f"批量预测异常: {e}")
        return jsonify({
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500


@bp.route("/predict/status", methods=["GET"])
def predict_status():
    """
    获取预测服务状态
    
    响应格式:
    {
        "success": true,
        "active_models": {
            "Q1": {"sig": "...", "version": "best", "load_time": "..."},
            "Q2": {...}
        },
        "cache_size": 3,
        "available_tasks": ["Q1", "Q2", "Q3", "Q4", "Q5"]
    }
    """
    try:
        active_models = ModelManager.get_active_models()
        
        return jsonify({
            "success": True,
            "active_models": active_models,
            "cache_size": len(ModelManager._cache),
            "available_tasks": VALID_Q_TAGS,
            "service_status": "running"
        })
        
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取状态失败",
            "message": str(e)
        }), 500


@bp.route("/predict/health", methods=["GET"])
def predict_health():
    """
    健康检查接口
    
    响应格式:
    {
        "status": "healthy",
        "timestamp": "2025-08-06T00:00:00Z",
        "active_models_count": 5
    }
    """
    from datetime import datetime
    
    try:
        active_count = len(ModelManager.get_active_models())
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "active_models_count": active_count,
            "service": "m10_service_predict"
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
            "service": "m10_service_predict"
        }), 503