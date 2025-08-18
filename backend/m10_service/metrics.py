"""
模型指标查询API路由
================

提供训练指标、TensorBoard事件、模型评估等数据查询功能。
"""

from flask import Blueprint, request, jsonify, send_file, abort
from pathlib import Path
import json
import logging
from typing import Dict, List, Any, Optional

from .config import MODELS_ROOT, LOGS_ROOT, DEFAULT_SIG, VALID_Q_TAGS

logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint("m10_metrics", __name__)


@bp.route("/metrics", methods=["GET"])
def get_model_metrics():
    """
    获取模型的离线评估指标
    
    请求参数:
    - q: 任务标签 (Q1-Q5)
    - sig: RQA参数签名 (可选，默认使用DEFAULT_SIG)
    - version: 模型版本 (可选，默认best)
    
    响应：直接返回JSON文件内容或404
    """
    try:
        q_tag = request.args.get('q')
        sig = request.args.get('sig', DEFAULT_SIG)
        version = request.args.get('version', 'best')
        
        if not q_tag:
            return jsonify({
                "success": False,
                "error": "缺少参数q"
            }), 400
            
        if q_tag not in VALID_Q_TAGS:
            return jsonify({
                "success": False,
                "error": "无效的任务标签",
                "valid_tags": VALID_Q_TAGS
            }), 400
        
        # 查找指标文件
        metrics_path = MODELS_ROOT / sig / f"{q_tag}_{version}_metrics.json"
        
        if not metrics_path.exists():
            logger.warning(f"指标文件不存在: {metrics_path}")
            abort(404, f"指标文件不存在: {q_tag}_{version}")
        
        logger.info(f"返回指标文件: {metrics_path}")
        return send_file(metrics_path, mimetype='application/json')
        
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取指标失败",
            "message": str(e)
        }), 500


@bp.route("/metrics/summary", methods=["GET"])
def get_metrics_summary():
    """
    获取模型指标摘要（所有任务的关键指标）
    
    请求参数:
    - sig: RQA参数签名 (可选)
    - version: 模型版本 (可选)
    
    响应格式:
    {
        "success": true,
        "summary": {
            "Q1": {"rmse": 0.15, "r2": 0.85, "mae": 0.12},
            "Q2": {...}
        },
        "sig": "...",
        "version": "best"
    }
    """
    try:
        sig = request.args.get('sig', DEFAULT_SIG)
        version = request.args.get('version', 'best')
        
        summary = {}
        
        for q_tag in VALID_Q_TAGS:
            metrics_path = MODELS_ROOT / sig / f"{q_tag}_{version}_metrics.json"
            
            if metrics_path.exists():
                try:
                    with open(metrics_path, 'r', encoding='utf-8') as f:
                        metrics = json.load(f)
                    
                    # 提取关键指标
                    summary[q_tag] = {
                        "rmse": metrics.get("test_rmse", 0.0),
                        "r2": metrics.get("test_r2", 0.0),
                        "mae": metrics.get("test_mae", 0.0),
                        "best_epoch": metrics.get("best_epoch", 0),
                        "train_time": metrics.get("train_time_seconds", 0.0)
                    }
                    
                except Exception as e:
                    logger.warning(f"解析指标文件失败 {q_tag}: {e}")
                    summary[q_tag] = None
            else:
                summary[q_tag] = None
        
        return jsonify({
            "success": True,
            "summary": summary,
            "sig": sig,
            "version": version,
            "available_tasks": [q for q, data in summary.items() if data is not None]
        })
        
    except Exception as e:
        logger.error(f"获取指标摘要失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取指标摘要失败",
            "message": str(e)
        }), 500


@bp.route("/events", methods=["GET"])
def get_training_events():
    """
    获取TensorBoard训练事件数据（简化版）
    
    请求参数:
    - q: 任务标签
    - sig: RQA参数签名 (可选)
    - metric: 指标名称 (可选，默认'loss/val')
    - limit: 返回点数限制 (可选，默认100)
    
    响应格式:
    {
        "success": true,
        "data": [
            {"step": 10, "value": 0.5, "timestamp": 1234567890},
            {"step": 20, "value": 0.4, "timestamp": 1234567891}
        ],
        "metric": "loss/val",
        "count": 100
    }
    """
    try:
        q_tag = request.args.get('q')
        sig = request.args.get('sig', DEFAULT_SIG)
        metric = request.args.get('metric', 'loss/val')
        limit = int(request.args.get('limit', 100))
        
        if not q_tag:
            return jsonify({
                "success": False,
                "error": "缺少参数q"
            }), 400
            
        if q_tag not in VALID_Q_TAGS:
            return jsonify({
                "success": False,
                "error": "无效的任务标签"
            }), 400
        
        # TensorBoard日志目录
        tb_dir = LOGS_ROOT / sig / q_tag
        
        if not tb_dir.exists():
            logger.warning(f"TensorBoard目录不存在: {tb_dir}")
            return jsonify({
                "success": False,
                "error": "训练日志不存在",
                "tb_dir": str(tb_dir)
            }), 404
        
        # 尝试解析TensorBoard事件
        try:
            data = _parse_tensorboard_events(tb_dir, metric, limit)
            
            return jsonify({
                "success": True,
                "data": data,
                "metric": metric,
                "count": len(data),
                "q_tag": q_tag,
                "sig": sig
            })
            
        except ImportError:
            # 如果没有tensorboard，返回模拟数据
            logger.warning("TensorBoard未安装，返回模拟数据")
            return jsonify({
                "success": True,
                "data": [],
                "metric": metric,
                "count": 0,
                "warning": "TensorBoard未安装，无法解析事件数据"
            })
        
    except Exception as e:
        logger.error(f"获取训练事件失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取训练事件失败",
            "message": str(e)
        }), 500


@bp.route("/events/available", methods=["GET"])
def get_available_metrics():
    """
    获取可用的训练指标列表
    
    请求参数:
    - q: 任务标签
    - sig: RQA参数签名 (可选)
    
    响应格式:
    {
        "success": true,
        "metrics": ["loss/train", "loss/val", "rmse/train", "rmse/val"],
        "q_tag": "Q1"
    }
    """
    try:
        q_tag = request.args.get('q')
        sig = request.args.get('sig', DEFAULT_SIG)
        
        if not q_tag:
            return jsonify({
                "success": False,
                "error": "缺少参数q"
            }), 400
        
        tb_dir = LOGS_ROOT / sig / q_tag
        
        if not tb_dir.exists():
            return jsonify({
                "success": True,
                "metrics": [],
                "q_tag": q_tag,
                "warning": "训练日志不存在"
            })
        
        try:
            metrics = _get_available_metrics(tb_dir)
            
            return jsonify({
                "success": True,
                "metrics": metrics,
                "q_tag": q_tag,
                "sig": sig,
                "tb_dir": str(tb_dir)
            })
            
        except ImportError:
            # 返回常见的指标名称
            return jsonify({
                "success": True,
                "metrics": ["loss/train", "loss/val", "rmse/train", "rmse/val", "r2/val"],
                "q_tag": q_tag,
                "warning": "TensorBoard未安装，返回默认指标列表"
            })
        
    except Exception as e:
        logger.error(f"获取可用指标失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取可用指标失败",
            "message": str(e)
        }), 500


# ==================== 私有辅助函数 ====================

def _parse_tensorboard_events(tb_dir: Path, metric: str, limit: int) -> List[Dict[str, Any]]:
    """解析TensorBoard事件文件"""
    try:
        from tensorboard.backend.event_processing import event_accumulator
        
        # 创建事件累加器
        ea = event_accumulator.EventAccumulator(str(tb_dir))
        ea.Reload()
        
        # 获取指定指标的标量数据
        if metric not in ea.Tags().get('scalars', []):
            logger.warning(f"指标 {metric} 不存在，可用指标: {ea.Tags().get('scalars', [])}")
            return []
        
        scalar_events = ea.Scalars(metric)
        
        # 转换为标准格式，取最后limit个点
        data = []
        for event in scalar_events[-limit:]:
            data.append({
                "step": event.step,
                "value": float(event.value),
                "timestamp": float(event.wall_time)
            })
        
        return data
        
    except ImportError as e:
        logger.warning(f"TensorBoard依赖未安装: {e}")
        raise
    except Exception as e:
        logger.error(f"解析TensorBoard事件失败: {e}")
        return []


def _get_available_metrics(tb_dir: Path) -> List[str]:
    """获取可用的指标名称列表"""
    try:
        from tensorboard.backend.event_processing import event_accumulator
        
        ea = event_accumulator.EventAccumulator(str(tb_dir))
        ea.Reload()
        
        return list(ea.Tags().get('scalars', []))
        
    except ImportError:
        raise
    except Exception as e:
        logger.error(f"获取指标列表失败: {e}")
        return []


@bp.route("/compare", methods=["GET"])
def compare_models():
    """
    比较不同版本模型的性能
    
    请求参数:
    - q: 任务标签
    - sig: RQA参数签名 (可选)
    - versions: 逗号分隔的版本列表 (可选，默认比较所有版本)
    
    响应格式:
    {
        "success": true,
        "comparison": {
            "best": {"rmse": 0.15, "r2": 0.85},
            "20250806_1203": {"rmse": 0.18, "r2": 0.82}
        },
        "q_tag": "Q1"
    }
    """
    try:
        q_tag = request.args.get('q')
        sig = request.args.get('sig', DEFAULT_SIG)
        versions_str = request.args.get('versions', '')
        
        if not q_tag:
            return jsonify({
                "success": False,
                "error": "缺少参数q"
            }), 400
        
        # 解析版本列表
        if versions_str:
            versions = [v.strip() for v in versions_str.split(',')]
        else:
            # 自动发现所有版本
            model_dir = MODELS_ROOT / sig
            versions = []
            if model_dir.exists():
                for metrics_file in model_dir.glob(f"{q_tag}_*_metrics.json"):
                    version = metrics_file.stem.replace(f"{q_tag}_", "").replace("_metrics", "")
                    versions.append(version)
        
        # 收集各版本的指标
        comparison = {}
        for version in versions:
            metrics_path = MODELS_ROOT / sig / f"{q_tag}_{version}_metrics.json"
            
            if metrics_path.exists():
                try:
                    with open(metrics_path, 'r', encoding='utf-8') as f:
                        metrics = json.load(f)
                    
                    comparison[version] = {
                        "rmse": metrics.get("test_rmse", 0.0),
                        "r2": metrics.get("test_r2", 0.0),
                        "mae": metrics.get("test_mae", 0.0),
                        "best_epoch": metrics.get("best_epoch", 0)
                    }
                    
                except Exception as e:
                    logger.warning(f"读取指标失败 {version}: {e}")
                    comparison[version] = None
        
        return jsonify({
            "success": True,
            "comparison": comparison,
            "q_tag": q_tag,
            "sig": sig,
            "available_versions": list(comparison.keys())
        })
        
    except Exception as e:
        logger.error(f"模型比较失败: {e}")
        return jsonify({
            "success": False,
            "error": "模型比较失败",
            "message": str(e)
        }), 500