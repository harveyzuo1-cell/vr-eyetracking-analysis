"""
数据表格API路由
===============

提供NPZ数据的表格化查看、导出和分析接口。
"""

from flask import Blueprint, request, jsonify, Response
from pathlib import Path
from typing import List, Literal, Optional
import logging
import json
from datetime import datetime

from .data_table import DataTableService
from .config import DEFAULT_SIG, VALID_Q_TAGS

logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint("m10_data", __name__)

# 数据集根目录
DATA_ROOT = Path("data/module10_datasets")


@bp.route("/data/table/<q_tag>", methods=["GET"])
def get_data_table(q_tag: str):
    """
    获取指定任务的数据表格
    
    GET /api/m10/data/table/Q1?rqa_sig=m2_tau1_eps0.055_lmin2&format=json&include_predictions=true&page=1&page_size=50
    
    查询参数:
    - rqa_sig: RQA配置签名（默认使用当前默认配置）
    - format: 返回格式 (json/csv/excel)，默认json
    - include_predictions: 是否包含预测结果 (true/false)，默认true
    - page: 分页页码 (可选)，默认1
    - page_size: 每页大小 (可选)，默认50
    
    响应格式:
    {
        "success": true,
        "task_id": "Q1",
        "total_samples": 60,
        "table_data": [...],
        "summary_stats": {...},
        "pagination": {...}
    }
    """
    try:
        # 验证任务标签
        if q_tag not in VALID_Q_TAGS:
            return jsonify({
                "success": False,
                "error": f"无效的任务标签: {q_tag}，支持的任务: {VALID_Q_TAGS}"
            }), 400
        
        # 获取查询参数
        rqa_sig = request.args.get("rqa_sig", DEFAULT_SIG)
        format_type = request.args.get("format", "json").lower()
        include_predictions = request.args.get("include_predictions", "true").lower() == "true"
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 1000:
            page_size = 50
        
        # 构建NPZ文件路径
        npz_path = DATA_ROOT / rqa_sig / f"{q_tag}.npz"
        
        if not npz_path.exists():
            return jsonify({
                "success": False,
                "error": f"数据文件不存在: {npz_path}",
                "suggested_action": "请先运行模块10-A生成数据集"
            }), 404
        
        logger.info(f"获取数据表格: {q_tag}, RQA={rqa_sig}, 格式={format_type}")
        
        # 转换为表格数据
        table_data = DataTableService.npz_to_dataframe(str(npz_path), include_predictions)
        
        # 根据格式返回不同响应
        if format_type == "json":
            # JSON格式：返回分页数据
            paginated_data = DataTableService.paginate_data(table_data, page, page_size)
            
            response_data = {
                "success": True,
                "task_id": table_data["task_id"],
                "npz_path": table_data["npz_path"],
                "total_samples": table_data["total_samples"],
                "feature_names": table_data["feature_names"],
                "feature_display_names": table_data["feature_display_names"],
                "table_data": paginated_data["table_data"],
                "summary_stats": table_data["summary_stats"],
                "correlation_matrix": table_data["correlation_matrix"],
                "has_predictions": table_data["has_predictions"],
                "pagination": paginated_data["pagination"],
                "generated_at": table_data["generated_at"]
            }
            
            return jsonify(response_data)
        
        elif format_type == "csv":
            # CSV格式：返回文件下载
            csv_data = DataTableService.to_csv(table_data)
            filename = f"{q_tag}_{rqa_sig}_training_data.csv"
            
            return Response(
                csv_data,
                mimetype="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/csv; charset=utf-8"
                }
            )
        
        elif format_type == "excel":
            # Excel格式：返回文件下载
            excel_data = DataTableService.to_excel(table_data)
            filename = f"{q_tag}_{rqa_sig}_training_data.xlsx"
            
            return Response(
                excel_data,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        
        else:
            return jsonify({
                "success": False,
                "error": f"不支持的格式: {format_type}，支持的格式: json, csv, excel"
            }), 400
        
    except ValueError as e:
        logger.warning(f"请求参数错误: {e}")
        return jsonify({
            "success": False,
            "error": "请求参数错误",
            "details": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"获取数据表格失败: {e}")
        return jsonify({
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500


@bp.route("/data/list", methods=["GET"])
def list_available_datasets():
    """
    列出可用的数据集
    
    GET /api/m10/data/list
    
    响应格式:
    {
        "success": true,
        "datasets": [
            {
                "rqa_sig": "m2_tau1_eps0.055_lmin2",
                "tasks": ["Q1", "Q2", "Q3", "Q4", "Q5"],
                "sample_counts": {"Q1": 60, "Q2": 60, ...},
                "created_at": "2025-01-01T12:00:00"
            }
        ]
    }
    """
    try:
        datasets = []
        
        if DATA_ROOT.exists():
            for rqa_dir in DATA_ROOT.iterdir():
                if not rqa_dir.is_dir():
                    continue
                
                rqa_sig = rqa_dir.name
                tasks = []
                sample_counts = {}
                created_times = []
                
                # 检查每个任务的NPZ文件
                for q_tag in VALID_Q_TAGS:
                    npz_file = rqa_dir / f"{q_tag}.npz"
                    if npz_file.exists():
                        tasks.append(q_tag)
                        created_times.append(npz_file.stat().st_mtime)
                        
                        # 快速获取样本数量
                        try:
                            import numpy as np
                            data = np.load(npz_file, allow_pickle=True)
                            sample_counts[q_tag] = len(data["X"])
                        except Exception as e:
                            logger.warning(f"读取 {npz_file} 失败: {e}")
                            sample_counts[q_tag] = 0
                
                if tasks:
                    from datetime import datetime
                    created_at = datetime.fromtimestamp(max(created_times)).isoformat()
                    
                    datasets.append({
                        "rqa_sig": rqa_sig,
                        "tasks": sorted(tasks),
                        "sample_counts": sample_counts,
                        "total_samples": sum(sample_counts.values()),
                        "created_at": created_at,
                        "dataset_path": str(rqa_dir)
                    })
        
        logger.info(f"发现 {len(datasets)} 个可用数据集")
        
        return jsonify({
            "success": True,
            "datasets": sorted(datasets, key=lambda x: x["created_at"], reverse=True),
            "total_datasets": len(datasets)
        })
        
    except Exception as e:
        logger.error(f"列出数据集失败: {e}")
        return jsonify({
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500


@bp.route("/data/compare", methods=["POST"])
def compare_datasets():
    """
    对比多个数据集
    
    POST /api/m10/data/compare
    {
        "datasets": [
            {"q_tag": "Q1", "rqa_sig": "m2_tau1_eps0.055_lmin2"},
            {"q_tag": "Q2", "rqa_sig": "m2_tau1_eps0.055_lmin2"}
        ],
        "comparison_type": "statistics"  // 或 "distributions" 或 "correlations"
    }
    
    响应格式:
    {
        "success": true,
        "comparison_type": "statistics",
        "datasets": [...],
        "summary": {...}
    }
    """
    try:
        req_data = request.get_json()
        
        if not req_data:
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        datasets = req_data.get("datasets", [])
        comparison_type = req_data.get("comparison_type", "statistics")
        
        # 验证输入
        if not datasets:
            return jsonify({
                "success": False,
                "error": "至少需要指定一个数据集"
            }), 400
        
        if len(datasets) > 10:
            return jsonify({
                "success": False,
                "error": "最多支持对比10个数据集"
            }), 400
        
        if comparison_type not in ["statistics", "distributions", "correlations"]:
            return jsonify({
                "success": False,
                "error": f"不支持的对比类型: {comparison_type}"
            }), 400
        
        # 验证数据集存在性
        for dataset in datasets:
            q_tag = dataset.get("q_tag")
            rqa_sig = dataset.get("rqa_sig", DEFAULT_SIG)
            
            if q_tag not in VALID_Q_TAGS:
                return jsonify({
                    "success": False,
                    "error": f"无效的任务标签: {q_tag}"
                }), 400
            
            npz_path = DATA_ROOT / rqa_sig / f"{q_tag}.npz"
            if not npz_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"数据集不存在: {rqa_sig}/{q_tag}"
                }), 404
        
        logger.info(f"对比数据集: {len(datasets)}个数据集, 类型={comparison_type}")
        
        # 执行对比
        comparison_result = DataTableService.compare_datasets(datasets, comparison_type)
        
        if "error" in comparison_result:
            return jsonify({
                "success": False,
                "error": comparison_result["error"]
            }), 500
        
        response_data = {
            "success": True,
            "comparison_type": comparison_type,
            "requested_datasets": datasets,
            **comparison_result
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"数据集对比失败: {e}")
        return jsonify({
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500


@bp.route("/data/summary/<q_tag>", methods=["GET"])
def get_data_summary(q_tag: str):
    """
    获取数据集简要统计信息（轻量级接口）
    
    GET /api/m10/data/summary/Q1?rqa_sig=m2_tau1_eps0.055_lmin2
    
    响应格式:
    {
        "success": true,
        "task_id": "Q1",
        "summary": {
            "total_samples": 60,
            "mmse_mean": 0.75,
            "feature_count": 10,
            "quality_score": 0.85
        }
    }
    """
    try:
        # 验证任务标签
        if q_tag not in VALID_Q_TAGS:
            return jsonify({
                "success": False,
                "error": f"无效的任务标签: {q_tag}"
            }), 400
        
        rqa_sig = request.args.get("rqa_sig", DEFAULT_SIG)
        npz_path = DATA_ROOT / rqa_sig / f"{q_tag}.npz"
        
        if not npz_path.exists():
            return jsonify({
                "success": False,
                "error": f"数据文件不存在: {npz_path}"
            }), 404
        
        # 快速加载基础信息
        import numpy as np
        data = np.load(npz_path, allow_pickle=True)
        X = data["X"]
        y = data["y"]
        
        # 计算简要统计
        quality_labels = DataTableService._assess_data_quality(X)
        good_count = sum(1 for label in quality_labels if label == "良好")
        quality_score = good_count / len(quality_labels) if quality_labels else 0
        
        summary = {
            "total_samples": len(X),
            "feature_count": X.shape[1],
            "mmse_mean": float(y.mean()),
            "mmse_std": float(y.std()),
            "mmse_range": [float(y.min()), float(y.max())],
            "quality_score": quality_score,
            "file_size_mb": npz_path.stat().st_size / (1024 * 1024),
            "last_modified": datetime.fromtimestamp(npz_path.stat().st_mtime).isoformat()
        }
        
        return jsonify({
            "success": True,
            "task_id": q_tag,
            "rqa_sig": rqa_sig,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"获取数据摘要失败: {e}")
        return jsonify({
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500


@bp.route("/data/health", methods=["GET"])
def data_health_check():
    """
    数据服务健康检查
    
    GET /api/m10/data/health
    
    响应格式:
    {
        "success": true,
        "status": "healthy",
        "checks": {
            "data_directory": true,
            "sample_datasets": true,
            "dependencies": true
        }
    }
    """
    try:
        checks = {
            "data_directory": DATA_ROOT.exists(),
            "numpy_available": True,
            "pandas_available": True,
            "sklearn_available": True
        }
        
        # 检查依赖库
        try:
            import numpy as np
            import pandas as pd
        except ImportError:
            checks["numpy_available"] = False
            checks["pandas_available"] = False
        
        try:
            from sklearn.metrics import mean_squared_error
        except ImportError:
            checks["sklearn_available"] = False
        
        # 检查是否有示例数据集
        sample_count = 0
        if DATA_ROOT.exists():
            for rqa_dir in DATA_ROOT.iterdir():
                if rqa_dir.is_dir():
                    for q_tag in VALID_Q_TAGS:
                        if (rqa_dir / f"{q_tag}.npz").exists():
                            sample_count += 1
                            break
        
        checks["sample_datasets"] = sample_count > 0
        
        # 总体健康状态
        all_healthy = all(checks.values())
        status = "healthy" if all_healthy else "degraded"
        
        return jsonify({
            "success": True,
            "status": status,
            "checks": checks,
            "available_datasets": sample_count,
            "data_root": str(DATA_ROOT),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "success": False,
            "status": "error",
            "error": str(e)
        }), 500


# 错误处理器
@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "接口不存在",
        "message": "请检查API路径是否正确"
    }), 404


@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误",
        "message": "请稍后重试或联系管理员"
    }), 500
