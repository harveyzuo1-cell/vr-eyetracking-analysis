"""
模型版本管理API路由
================

提供模型版本列表、激活、切换等功能。
"""

from flask import Blueprint, request, jsonify
from typing import Optional, Literal
import logging

from .loader import ModelManager
from .config import DEFAULT_SIG, VALID_Q_TAGS

logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint("m10_versions", __name__)

# 尝试导入Pydantic，如果失败则使用简单验证
try:
    from pydantic import BaseModel, ValidationError
    
    class ActivateRequest(BaseModel):
        """激活模型请求"""
        q_tag: Literal["Q1", "Q2", "Q3", "Q4", "Q5"]
        version: str
        sig: Optional[str] = DEFAULT_SIG

    class DeactivateRequest(BaseModel):
        """取消激活请求"""
        q_tag: Literal["Q1", "Q2", "Q3", "Q4", "Q5"]
    
    PYDANTIC_AVAILABLE = True
    
except ImportError:
    # 如果没有Pydantic，使用简单的字典验证
    class ValidationError(Exception):
        def __init__(self, errors):
            self.errors = lambda: errors
            super().__init__(str(errors))
    
    class ActivateRequest:
        def __init__(self, q_tag, version, sig=None):
            if q_tag not in VALID_Q_TAGS:
                raise ValidationError([{"msg": "无效的任务标签"}])
            if not version:
                raise ValidationError([{"msg": "版本不能为空"}])
            self.q_tag = q_tag
            self.version = version
            self.sig = sig or DEFAULT_SIG
        
        @classmethod
        def parse_raw(cls, data):
            import json
            obj = json.loads(data)
            return cls(obj["q_tag"], obj["version"], obj.get("sig"))
    
    class DeactivateRequest:
        def __init__(self, q_tag):
            if q_tag not in VALID_Q_TAGS:
                raise ValidationError([{"msg": "无效的任务标签"}])
            self.q_tag = q_tag
        
        @classmethod
        def parse_raw(cls, data):
            import json
            obj = json.loads(data)
            return cls(obj["q_tag"])
    
    PYDANTIC_AVAILABLE = False


@bp.route("/models", methods=["GET"])
def list_models():
    """
    获取所有可用模型列表
    
    响应格式:
    {
        "success": true,
        "models": [
            {
                "q": "Q1",
                "sig": "m2_tau1_eps0.055_lmin2", 
                "versions": ["best", "20250806_1203", "20250805_1503"],
                "active": "best"
            }
        ],
        "count": 5
    }
    """
    try:
        models = ModelManager.list_models()
        
        logger.info(f"模型列表查询成功，共 {len(models)} 个任务")
        
        return jsonify({
            "success": True,
            "models": models,
            "count": len(models),
            "default_sig": DEFAULT_SIG
        })
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取模型列表失败",
            "message": str(e)
        }), 500


@bp.route("/activate", methods=["POST"]) 
def activate_model():
    """
    激活指定版本的模型
    
    请求格式:
    {
        "q_tag": "Q1",
        "version": "best",
        "sig": "m2_tau1_eps0.055_lmin2"  # 可选，默认使用DEFAULT_SIG
    }
    
    响应格式:
    {
        "success": true,
        "message": "模型激活成功",
        "q_tag": "Q1",
        "version": "best",
        "sig": "m2_tau1_eps0.055_lmin2"
    }
    """
    try:
        # 解析请求
        req_data = ActivateRequest.parse_raw(request.data)
        
        # 激活模型
        success = ModelManager.activate(req_data.q_tag, req_data.sig, req_data.version)
        
        if success:
            logger.info(f"模型激活成功: {req_data.q_tag} -> {req_data.sig}/{req_data.version}")
            
            return jsonify({
                "success": True,
                "message": "模型激活成功",
                "q_tag": req_data.q_tag,
                "version": req_data.version,
                "sig": req_data.sig
            })
        else:
            return jsonify({
                "success": False,
                "error": "模型激活失败",
                "q_tag": req_data.q_tag
            }), 500
            
    except ValidationError as e:
        logger.warning(f"激活请求验证失败: {e}")
        return jsonify({
            "success": False,
            "error": "请求格式错误",
            "details": e.errors()
        }), 400
        
    except FileNotFoundError as e:
        logger.error(f"模型文件不存在: {e}")
        return jsonify({
            "success": False,
            "error": "模型文件不存在",
            "message": str(e)
        }), 404
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return jsonify({
            "success": False,
            "error": "参数错误",
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"模型激活异常: {e}")
        return jsonify({
            "success": False,
            "error": "模型激活失败",
            "message": str(e)
        }), 500


@bp.route("/deactivate", methods=["POST"])
def deactivate_model():
    """
    取消激活指定任务的模型
    
    请求格式:
    {
        "q_tag": "Q1"
    }
    """
    try:
        req_data = DeactivateRequest.parse_raw(request.data)
        
        # 清理指定任务的缓存
        cleared_count = ModelManager.clear_cache(req_data.q_tag)
        
        logger.info(f"模型取消激活: {req_data.q_tag}, 清理了 {cleared_count} 个缓存")
        
        return jsonify({
            "success": True,
            "message": "模型已取消激活",
            "q_tag": req_data.q_tag,
            "cleared_count": cleared_count
        })
        
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": "请求格式错误",
            "details": e.errors()
        }), 400
        
    except Exception as e:
        logger.error(f"取消激活失败: {e}")
        return jsonify({
            "success": False,
            "error": "取消激活失败",
            "message": str(e)
        }), 500


@bp.route("/active", methods=["GET"])
def get_active_models():
    """
    获取当前激活的模型信息
    
    响应格式:
    {
        "success": true,
        "active_models": {
            "Q1": {
                "sig": "m2_tau1_eps0.055_lmin2",
                "version": "best",
                "load_time": "2025-08-06T00:00:00"
            }
        },
        "count": 5
    }
    """
    try:
        active_models = ModelManager.get_active_models()
        
        return jsonify({
            "success": True,
            "active_models": active_models,
            "count": len(active_models)
        })
        
    except Exception as e:
        logger.error(f"获取激活模型失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取激活模型失败",
            "message": str(e)
        }), 500


@bp.route("/cache/clear", methods=["POST"])
def clear_cache():
    """
    清理模型缓存
    
    请求参数:
    - q_tag (可选): 清理指定任务的缓存
    
    响应格式:
    {
        "success": true,
        "message": "缓存清理完成",
        "cleared_count": 3
    }
    """
    try:
        q_tag = request.args.get('q_tag')
        
        if q_tag and q_tag not in VALID_Q_TAGS:
            return jsonify({
                "success": False,
                "error": "无效的任务标签",
                "valid_tags": VALID_Q_TAGS
            }), 400
        
        cleared_count = ModelManager.clear_cache(q_tag)
        
        message = f"已清理 {q_tag} 的缓存" if q_tag else "已清理所有缓存"
        logger.info(f"缓存清理: {message}, 数量: {cleared_count}")
        
        return jsonify({
            "success": True,
            "message": message,
            "cleared_count": cleared_count,
            "q_tag": q_tag
        })
        
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        return jsonify({
            "success": False,
            "error": "清理缓存失败",
            "message": str(e)
        }), 500


@bp.route("/reload", methods=["POST"])
def reload_models():
    """
    重新扫描可用模型（用于发现新训练的模型）
    
    响应格式:
    {
        "success": true,
        "message": "模型列表已更新",
        "models": [...],
        "count": 5
    }
    """
    try:
        # 重新扫描模型目录
        models = ModelManager.list_models()
        
        logger.info(f"模型列表重新加载，发现 {len(models)} 个任务")
        
        return jsonify({
            "success": True,
            "message": "模型列表已更新",
            "models": models,
            "count": len(models),
            "timestamp": ModelManager._load_times
        })
        
    except Exception as e:
        logger.error(f"重新加载模型失败: {e}")
        return jsonify({
            "success": False,
            "error": "重新加载模型失败",
            "message": str(e)
        }), 500