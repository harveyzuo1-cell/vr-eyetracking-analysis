"""
模块10-B: Flask API接口
====================================

提供训练相关的REST API端点，集成到主Flask应用中。
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import uuid

from flask import Blueprint, request, jsonify
import yaml

from .trainer import create_trainer_from_config, deep_update
import numpy as np
import torch

logger = logging.getLogger(__name__)

# 创建Blueprint
m10b_bp = Blueprint('m10b_training', __name__, url_prefix='/api/m10b')

# 训练任务状态管理
training_jobs = {}
training_lock = threading.Lock()


class TrainingJob:
    """训练任务类"""
    
    def __init__(self, job_id: str, config: Dict[str, Any]):
        self.job_id = job_id
        self.config = config
        self.status = "pending"  # pending, running, completed, failed
        self.progress = 0.0
        self.current_epoch = 0
        self.total_epochs = config.get("training", {}).get("epochs", 100)
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None
        self.logs = []
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error,
            "config": {
                "q_tag": self.config.get("q_tag"),
                "rqa_sig": self.config.get("rqa_sig"),
                "device": self.config.get("device", "cpu"),
                "epochs": self.total_epochs
            }
        }


def run_training_job(job: TrainingJob):
    """
    在后台线程中运行训练任务
    
    Args:
        job: 训练任务对象
    """
    try:
        with training_lock:
            job.status = "running"
            job.start_time = datetime.now()
        
        logger.info(f"开始训练任务: {job.job_id}")
        
        # 获取配置
        q_tag = job.config["q_tag"]
        rqa_sig = job.config["rqa_sig"]
        override_config = job.config.get("override", {})
        
        # 确定数据集路径
        data_root = Path("data/module10_datasets")
        npz_path = data_root / rqa_sig / f"{q_tag}.npz"
        
        if not npz_path.exists():
            raise FileNotFoundError(f"数据集文件不存在: {npz_path}")
        
        # 创建训练器
        config_path = Path(__file__).parent / "config.yaml"
        trainer = create_trainer_from_config(
            str(config_path),
            q_tag,
            rqa_sig,
            override_config
        )
        
        # 自定义训练器以更新进度
        original_fit = trainer.fit
        
        def progress_aware_fit(*args, **kwargs):
            """包装fit方法以更新进度"""
            
            # 重写train_epoch方法以更新进度
            original_train_epoch = trainer.train_epoch
            
            def progress_train_epoch(train_loader, epoch):
                result = original_train_epoch(train_loader, epoch)
                
                # 更新进度
                with training_lock:
                    job.current_epoch = epoch
                    job.progress = min(epoch / job.total_epochs, 1.0)
                
                return result
            
            trainer.train_epoch = progress_train_epoch
            return original_fit(*args, **kwargs)
        
        trainer.fit = progress_aware_fit
        
        # 开始训练
        result = trainer.fit(npz_path)
        
        # 更新最终状态
        with training_lock:
            job.status = "completed"
            job.progress = 1.0
            job.end_time = datetime.now()
            job.result = {
                "success": result["success"],
                "epochs_trained": result["epochs_trained"],
                "best_epoch": result["best_epoch"],
                "best_val_loss": result["best_val_loss"],
                "final_train_loss": result.get("final_train_loss"),
                "total_time": result["total_time"],
                "model_path": result["model_path"],
                "final_metrics": result["final_metrics"],
                "history": result.get("history", {})  # 添加训练历史数据
            }
        
        logger.info(f"训练任务完成: {job.job_id}")
        
    except Exception as e:
        logger.error(f"训练任务失败: {job.job_id}, 错误: {str(e)}")
        
        with training_lock:
            job.status = "failed"
            job.end_time = datetime.now()
            job.error = str(e)


@m10b_bp.route('/train', methods=['POST'])
def start_training():
    """
    启动训练任务
    
    POST /api/m10b/train
    Body: {
        "rqa_config": "m2_tau1_eps0.055_lmin2",
        "q_tag": "Q1",
        "override": {
            "training": {"epochs": 200},
            "device": "cuda:0"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        
        # 验证必需参数
        rqa_config = data.get("rqa_config")
        q_tag = data.get("q_tag")
        
        if not rqa_config:
            return jsonify({"error": "缺少参数: rqa_config"}), 400
        
        if not q_tag or q_tag not in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
            return jsonify({"error": "无效的q_tag，必须是Q1-Q5之一"}), 400
        
        # 检查数据集是否存在
        data_root = Path("data/module10_datasets")
        npz_path = data_root / rqa_config / f"{q_tag}.npz"
        
        if not npz_path.exists():
            return jsonify({
                "error": f"数据集文件不存在: {npz_path}",
                "suggestion": "请先运行模块10-A生成数据集"
            }), 404
        
        # 创建训练任务
        job_id = str(uuid.uuid4())
        
        job_config = {
            "q_tag": q_tag,
            "rqa_sig": rqa_config,
            "override": data.get("override", {})
        }
        
        job = TrainingJob(job_id, job_config)
        
        # 注册任务
        with training_lock:
            training_jobs[job_id] = job
        
        # 启动后台训练线程
        training_thread = threading.Thread(
            target=run_training_job,
            args=(job,),
            daemon=True
        )
        training_thread.start()
        
        logger.info(f"训练任务已启动: {job_id}")
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "训练任务已提交",
            "config": {
                "rqa_config": rqa_config,
                "q_tag": q_tag,
                "data_path": str(npz_path)
            }
        }), 202
        
    except Exception as e:
        logger.error(f"启动训练任务失败: {str(e)}")
        return jsonify({"error": f"启动训练失败: {str(e)}"}), 500


@m10b_bp.route('/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id: str):
    """
    获取训练任务状态
    
    GET /api/m10b/jobs/<job_id>/status
    """
    try:
        with training_lock:
            job = training_jobs.get(job_id)
        
        if not job:
            return jsonify({"error": "训练任务不存在"}), 404
        
        return jsonify(job.to_dict()), 200
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        return jsonify({"error": f"获取状态失败: {str(e)}"}), 500


@m10b_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """
    获取所有训练任务列表
    
    GET /api/m10b/jobs
    """
    try:
        # 查询参数
        status_filter = request.args.get('status')
        q_tag_filter = request.args.get('q_tag')
        limit = int(request.args.get('limit', 50))
        
        with training_lock:
            jobs = list(training_jobs.values())
        
        # 过滤
        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]
        
        if q_tag_filter:
            jobs = [job for job in jobs if job.config.get("q_tag") == q_tag_filter]
        
        # 排序（最新的在前）
        jobs.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
        
        # 限制数量
        jobs = jobs[:limit]
        
        return jsonify({
            "jobs": [job.to_dict() for job in jobs],
            "total": len(jobs)
        }), 200
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({"error": f"获取任务列表失败: {str(e)}"}), 500


@m10b_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id: str):
    """
    取消训练任务
    
    POST /api/m10b/jobs/<job_id>/cancel
    """
    try:
        with training_lock:
            job = training_jobs.get(job_id)
        
        if not job:
            return jsonify({"error": "训练任务不存在"}), 404
        
        if job.status not in ["pending", "running"]:
            return jsonify({
                "error": f"无法取消状态为'{job.status}'的任务"
            }), 400
        
        # 注意：这是一个简化的取消机制
        # 实际的PyTorch训练取消需要更复杂的实现
        with training_lock:
            job.status = "cancelled"
            job.end_time = datetime.now()
        
        logger.info(f"训练任务已取消: {job_id}")
        
        return jsonify({
            "message": "任务已标记为取消",
            "job_id": job_id,
            "status": "cancelled"
        }), 200
        
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        return jsonify({"error": f"取消任务失败: {str(e)}"}), 500


@m10b_bp.route('/models', methods=['GET'])
def list_models():
    """
    获取已训练的模型列表
    
    GET /api/m10b/models
    """
    try:
        models_dir = Path("models")
        
        if not models_dir.exists():
            return jsonify({"models": []}), 200
        
        models = []
        
        for rqa_dir in models_dir.iterdir():
            if not rqa_dir.is_dir():
                continue
                
            rqa_sig = rqa_dir.name
            
            for model_file in rqa_dir.glob("*_best.pt"):
                try:
                    # 提取Q标签
                    q_tag = model_file.stem.replace("_best", "")
                    
                    # 获取文件信息
                    stat = model_file.stat()
                    
                    # 尝试加载模型信息
                    model_info = {
                        "rqa_sig": rqa_sig,
                        "q_tag": q_tag,
                        "model_path": str(model_file),
                        "file_size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    
                    # 尝试加载训练历史
                    history_file = rqa_dir / f"{q_tag}_history.json"
                    if history_file.exists():
                        with open(history_file, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                            metadata = history.get("metadata", {})
                            model_info.update({
                                "epochs_trained": metadata.get("epochs_trained"),
                                "best_epoch": metadata.get("best_epoch"),
                                "best_val_loss": metadata.get("best_val_loss")
                            })
                    
                    models.append(model_info)
                    
                except Exception as e:
                    logger.warning(f"处理模型文件失败 {model_file}: {str(e)}")
                    continue
        
        # 按修改时间排序
        models.sort(key=lambda x: x["modified_at"], reverse=True)
        
        return jsonify({
            "models": models,
            "total": len(models)
        }), 200
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return jsonify({"error": f"获取模型列表失败: {str(e)}"}), 500


@m10b_bp.route('/config', methods=['GET'])
def get_default_config():
    """
    获取默认训练配置
    
    GET /api/m10b/config
    """
    try:
        config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return jsonify(config), 200
        
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({"error": f"获取配置失败: {str(e)}"}), 500


@m10b_bp.route('/config', methods=['POST'])
def update_default_config():
    """
    更新默认训练配置
    
    POST /api/m10b/config
    Body: {...}  # 新的配置
    """
    try:
        new_config = request.get_json()
        
        if not new_config:
            return jsonify({"error": "请求体不能为空"}), 400
        
        config_path = Path(__file__).parent / "config.yaml"
        
        # 加载现有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
        
        # 深度合并配置
        merged_config = deep_update(current_config, new_config)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(merged_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("默认配置已更新")
        
        return jsonify({
            "message": "配置已更新",
            "config": merged_config
        }), 200
        
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return jsonify({"error": f"更新配置失败: {str(e)}"}), 500


# 健康检查端点
@m10b_bp.route('/health', methods=['GET'])
def health_check():
    """模块10-B健康检查"""
    return jsonify({
        "status": "healthy",
        "module": "m10b_training",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len([job for job in training_jobs.values() if job.status == "running"])
    })


@m10b_bp.route('/prediction-analysis/<q_tag>', methods=['GET'])
def get_prediction_analysis(q_tag: str):
    """
    获取指定任务的预测准确性分析数据
    
    Args:
        q_tag: 任务标签 (Q1-Q5)
        
    Query Parameters:
        rqa_sig: RQA参数签名 (可选，默认使用default)
        
    Returns:
        预测vs真实值的分析数据，包括散点图数据、残差数据、统计指标等
    """
    try:
        # 这些常量在此处定义，避免循环导入
        MODELS_ROOT = Path("models")
        DATA_ROOT = Path("data/module10_datasets")
        from .dataset import make_loaders
        from .model import create_model_from_config
        
        # 获取参数
        rqa_sig = request.args.get('rqa_sig', 'm2_tau1_eps0.055_lmin2')
        
        # 验证任务标签
        valid_q_tags = ["Q1", "Q2", "Q3", "Q4", "Q5"]
        if q_tag not in valid_q_tags:
            return jsonify({
                "success": False,
                "error": f"无效的任务标签: {q_tag}",
                "valid_tags": valid_q_tags
            }), 400
        
        # 检查模型文件是否存在
        model_dir = MODELS_ROOT / rqa_sig
        model_path = model_dir / f"{q_tag}_best.pt"
        
        if not model_path.exists():
            return jsonify({
                "success": False,
                "error": f"模型文件不存在: {model_path}",
                "message": "请先训练模型"
            }), 404
        
        # 加载数据集
        npz_path = DATA_ROOT / rqa_sig / f"{q_tag}.npz"
        if not npz_path.exists():
            return jsonify({
                "success": False,
                "error": f"数据集文件不存在: {npz_path}"
            }), 404
        
        # 加载模型
        logger.info(f"加载模型进行预测分析: {model_path}")
        
        # 从配置重建模型
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 创建模型
        model = create_model_from_config(config)
        
        # 加载权重
        checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
        if isinstance(checkpoint, dict):
            if "model_state_dict" in checkpoint:
                model.load_state_dict(checkpoint["model_state_dict"])
            elif "model_state" in checkpoint:
                model.load_state_dict(checkpoint["model_state"])
            else:
                return jsonify({
                    "success": False,
                    "error": "无法从checkpoint中找到模型状态"
                }), 500
        else:
            return jsonify({
                "success": False,
                "error": "checkpoint格式不正确"
            }), 500
        
        model.eval()
        
        # 加载完整数据集
        from .dataset import create_full_loader
        data_loader = create_full_loader(npz_path, batch_size=32)
        
        # 进行预测
        predictions = []
        true_values = []
        sample_indices = []
        
        with torch.no_grad():
            for batch_idx, (features, targets) in enumerate(data_loader):
                batch_predictions = model(features)
                predictions.extend(batch_predictions.cpu().numpy().flatten())
                true_values.extend(targets.cpu().numpy().flatten())
                
                # 记录样本索引
                batch_size = features.size(0)
                batch_start = batch_idx * data_loader.batch_size
                sample_indices.extend(range(batch_start, batch_start + batch_size))
        
        # 转换为numpy数组
        predictions = np.array(predictions)
        true_values = np.array(true_values)
        
        # 计算统计指标
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        import numpy as np
        
        r2 = r2_score(true_values, predictions)
        rmse = np.sqrt(mean_squared_error(true_values, predictions))
        mae = mean_absolute_error(true_values, predictions)
        correlation = np.corrcoef(true_values, predictions)[0, 1]
        
        # 计算残差
        residuals = predictions - true_values
        
        # 分组分析（假设每组20个样本）
        n_samples_per_group = 20
        group_stats = {}
        group_names = ['Control', 'MCI', 'AD']
        
        for i, group_name in enumerate(group_names):
            start_idx = i * n_samples_per_group
            end_idx = min((i + 1) * n_samples_per_group, len(predictions))
            
            if start_idx < len(predictions):
                group_pred = predictions[start_idx:end_idx]
                group_true = true_values[start_idx:end_idx]
                
                if len(group_pred) > 1:
                    group_r2 = r2_score(group_true, group_pred)
                    group_stats[group_name.lower()] = {
                        "count": len(group_pred),
                        "r2": float(group_r2),
                        "predictions": group_pred.tolist(),
                        "true_values": group_true.tolist()
                    }
        
        # 准备响应数据
        response_data = {
            "success": True,
            "q_tag": q_tag,
            "rqa_sig": rqa_sig,
            "metrics": {
                "r2": float(r2),
                "rmse": float(rmse),
                "mae": float(mae),
                "correlation": float(correlation),
                "sample_count": len(predictions)
            },
            "scatter_data": {
                "predictions": predictions.tolist(),
                "true_values": true_values.tolist(),
                "sample_indices": sample_indices
            },
            "residual_data": {
                "residuals": residuals.tolist(),
                "predictions": predictions.tolist()
            },
            "group_analysis": group_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"预测分析完成: {q_tag}, R²={r2:.3f}, RMSE={rmse:.3f}")
        
        return jsonify(response_data)
        
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        return jsonify({
            "success": False,
            "error": "缺少必要的依赖模块",
            "message": str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"预测分析失败: {e}")
        return jsonify({
            "success": False,
            "error": "预测分析失败",
            "message": str(e)
        }), 500