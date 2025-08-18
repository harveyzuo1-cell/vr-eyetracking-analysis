"""
模型性能评估器
提供批量模型加载、性能计算、残差分析等功能
"""
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from functools import lru_cache

from .config import (
    EVALUATION_CONFIG, 
    get_model_path, 
    get_data_path, 
    get_metrics_path
)

# 设置日志
logger = logging.getLogger(__name__)

class ModelEvaluator:
    """模型性能评估器"""
    
    def __init__(self):
        """初始化评估器"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tasks = EVALUATION_CONFIG["tasks"]
        self.model_cache = {}  # 模型缓存
        self.data_cache = {}   # 数据缓存
        
        logger.info(f"模型评估器初始化完成，使用设备: {self.device}")
    
    def evaluate_model_set(self, rqa_sig: str, include_groups: bool = False) -> Dict[str, Any]:
        """
        批量评估指定配置下的所有任务模型
        
        Args:
            rqa_sig: RQA配置签名
            include_groups: 是否包含分组分析
            
        Returns:
            完整的性能分析结果
        """
        logger.info(f"开始评估模型集: {rqa_sig}")
        
        try:
            # 检查所有必需的文件是否存在
            missing_files = self._check_required_files(rqa_sig)
            if missing_files:
                return {
                    "success": False,
                    "error": f"缺少必需文件: {', '.join(missing_files)}"
                }
            
            # 批量加载模型和数据
            models_dict = self._load_models_batch(rqa_sig)
            data_dict = self._load_data_batch(rqa_sig)
            
            # 计算残差和指标
            residual_matrix, metrics_dict = self._calculate_residuals_optimized(
                models_dict, data_dict
            )
            
            # 构建结果
            results = {
                "success": True,
                "rqa_config": rqa_sig,
                "task_metrics": metrics_dict,
                "residual_data": {
                    "individual_errors": residual_matrix.tolist(),
                    "avg_errors": np.mean(np.abs(residual_matrix), axis=0).tolist(),
                    "std_errors": np.std(residual_matrix, axis=0).tolist()
                },
                "task_comparison": {
                    "avg_actuals": [np.mean(data_dict[task]['y']) for task in self.tasks],
                    "avg_abs_errors": np.mean(np.abs(residual_matrix), axis=0).tolist()
                },
                "sample_count": residual_matrix.shape[0],
                "task_count": len(self.tasks)
            }
            
            # 添加分组分析
            if include_groups:
                group_analysis = self._analyze_group_performance(residual_matrix)
                results["group_analysis"] = group_analysis
            
            logger.info(f"模型集评估完成: {rqa_sig}")
            return results
            
        except Exception as e:
            logger.error(f"模型评估失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_required_files(self, rqa_sig: str) -> List[str]:
        """检查必需文件是否存在"""
        missing_files = []
        
        for task in self.tasks:
            model_path = get_model_path(rqa_sig, task)
            data_path = get_data_path(rqa_sig, task)
            
            if not model_path.exists():
                missing_files.append(f"模型文件: {model_path}")
            if not data_path.exists():
                missing_files.append(f"数据文件: {data_path}")
        
        return missing_files
    
    def _load_models_batch(self, rqa_sig: str) -> Dict[str, torch.nn.Module]:
        """批量加载模型"""
        models_dict = {}
        
        for task in self.tasks:
            cache_key = f"{rqa_sig}_{task}"
            
            if cache_key in self.model_cache:
                models_dict[task] = self.model_cache[cache_key]
                continue
            
            model_path = get_model_path(rqa_sig, task)
            try:
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                
                # 处理不同的模型保存格式
                if isinstance(checkpoint, dict):
                    if 'model_state_dict' in checkpoint:
                        # 需要重新构建模型架构
                        try:
                            from backend.m10_training.model import create_model_from_config
                        except ImportError:
                            import sys
                            import os
                            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
                            from backend.m10_training.model import create_model_from_config
                        
                        # 加载配置 - 使用简化的配置
                        config = {
                            'arch': {
                                'input_dim': 10,
                                'h1': 32,
                                'h2': 16,
                                'dropout': 0.25,
                                'use_batch_norm': False,
                                'activation': 'relu',
                                'output_dim': 1
                            }
                        }
                        
                        # 创建模型
                        model = create_model_from_config(config)
                        model.load_state_dict(checkpoint['model_state_dict'])
                    else:
                        # 假设整个字典就是state_dict - 手动创建模型
                        import torch.nn as nn
                        
                        class SimpleEyeMLP(nn.Module):
                            def __init__(self):
                                super().__init__()
                                self.network = nn.Sequential(
                                    nn.Linear(10, 32),
                                    nn.ReLU(),
                                    nn.Dropout(0.25),
                                    nn.Linear(32, 16),
                                    nn.ReLU(),
                                    nn.Dropout(0.25),
                                    nn.Linear(16, 1),
                                    nn.Sigmoid()
                                )
                            
                            def forward(self, x):
                                return self.network(x)
                        
                        model = SimpleEyeMLP()
                        model.load_state_dict(checkpoint)
                else:
                    # 直接是模型对象
                    model = checkpoint
                
                model = model.to(self.device)
                model.eval()
                
                # 缓存模型
                if len(self.model_cache) < EVALUATION_CONFIG["model_cache_size"]:
                    self.model_cache[cache_key] = model
                
                models_dict[task] = model
                logger.info(f"模型加载成功: {task}")
                
            except Exception as e:
                logger.error(f"模型加载失败 {task}: {e}")
                raise
        
        return models_dict
    
    def _load_data_batch(self, rqa_sig: str) -> Dict[str, Dict[str, np.ndarray]]:
        """批量加载数据"""
        data_dict = {}
        
        for task in self.tasks:
            cache_key = f"{rqa_sig}_{task}_data"
            
            if cache_key in self.data_cache:
                data_dict[task] = self.data_cache[cache_key]
                continue
            
            data_path = get_data_path(rqa_sig, task)
            try:
                data = np.load(data_path)
                task_data = {
                    'X': data['X'],
                    'y': data['y'],
                    'feature_names': data.get('feature_names', [])
                }
                
                # 缓存数据
                self.data_cache[cache_key] = task_data
                data_dict[task] = task_data
                logger.info(f"数据加载成功: {task} ({len(task_data['y'])} 样本)")
                
            except Exception as e:
                logger.error(f"数据加载失败 {task}: {e}")
                raise
        
        return data_dict
    
    def _calculate_residuals_optimized(self, models_dict: Dict, data_dict: Dict) -> Tuple[np.ndarray, Dict]:
        """优化的残差计算"""
        n_samples = len(data_dict[self.tasks[0]]['y'])
        n_tasks = len(self.tasks)
        
        # 预分配结果矩阵
        residual_matrix = np.zeros((n_samples, n_tasks))
        metrics_dict = {}
        
        with torch.no_grad():
            for i, task in enumerate(self.tasks):
                model = models_dict[task]
                X, y_true = data_dict[task]['X'], data_dict[task]['y']
                
                # 批量预测
                X_tensor = torch.FloatTensor(X).to(self.device)
                y_pred = model(X_tensor).cpu().numpy().flatten()
                
                # 计算残差
                residuals = y_pred - y_true
                residual_matrix[:, i] = residuals
                
                # 计算指标
                metrics_dict[task] = {
                    'r2': float(r2_score(y_true, y_pred)),
                    'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
                    'mae': float(mean_absolute_error(y_true, y_pred)),
                    'correlation': float(np.corrcoef(y_true, y_pred)[0, 1])
                }
                
                logger.info(f"任务 {task} 评估完成: R²={metrics_dict[task]['r2']:.3f}")
        
        return residual_matrix, metrics_dict
    
    def _analyze_group_performance(self, residual_matrix: np.ndarray) -> Dict[str, Any]:
        """分组性能分析"""
        n_samples = residual_matrix.shape[0]
        group_mapping = EVALUATION_CONFIG["group_mapping"]
        
        group_stats = {}
        
        for group_name, (start_idx, end_idx) in group_mapping.items():
            # 确保索引不超出范围
            start_idx = max(0, min(start_idx, n_samples))
            end_idx = max(start_idx, min(end_idx, n_samples))
            
            if start_idx >= end_idx:
                continue
            
            group_residuals = residual_matrix[start_idx:end_idx]
            abs_residuals = np.abs(group_residuals)
            
            group_stats[group_name] = {
                'mean_errors': np.mean(abs_residuals, axis=0).tolist(),
                'std_errors': np.std(abs_residuals, axis=0).tolist(),
                'median_errors': np.median(abs_residuals, axis=0).tolist(),
                'max_errors': np.max(abs_residuals, axis=0).tolist(),
                'sample_count': len(group_residuals),
                'sample_range': [start_idx, end_idx]
            }
        
        return group_stats
    
    def get_available_configs(self) -> List[Dict[str, Any]]:
        """获取可用的模型配置列表"""
        from .config import MODELS_ROOT
        
        configs = []
        
        if not MODELS_ROOT.exists():
            return configs
        
        for config_dir in MODELS_ROOT.iterdir():
            if not config_dir.is_dir():
                continue
            
            # 检查是否有完整的Q1-Q5模型
            model_files = []
            missing_tasks = []
            
            for task in self.tasks:
                model_path = config_dir / f"{task}_best.pt"
                if model_path.exists():
                    model_files.append(task)
                else:
                    missing_tasks.append(task)
            
            configs.append({
                'id': config_dir.name,
                'name': config_dir.name,
                'available_tasks': model_files,
                'missing_tasks': missing_tasks,
                'complete': len(missing_tasks) == 0,
                'model_count': len(model_files)
            })
        
        # 按完整性和名称排序
        configs.sort(key=lambda x: (x['complete'], x['model_count'], x['name']), reverse=True)
        
        return configs
    
    def export_data(self, rqa_sig: str, format_type: str = "csv") -> Optional[str]:
        """导出评估数据"""
        try:
            results = self.evaluate_model_set(rqa_sig, include_groups=True)
            
            if not results.get("success"):
                return None
            
            if format_type == "json":
                return json.dumps(results, indent=2, ensure_ascii=False)
            elif format_type == "csv":
                return self._export_to_csv(results)
            else:
                return None
                
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            return None
    
    def _export_to_csv(self, results: Dict) -> str:
        """导出为CSV格式"""
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题
        writer.writerow(['模型配置', results['rqa_config']])
        writer.writerow(['样本数量', results['sample_count']])
        writer.writerow([])
        
        # 写入任务指标
        writer.writerow(['任务指标'])
        writer.writerow(['任务', 'R²', 'RMSE', 'MAE', '相关系数'])
        
        for task, metrics in results['task_metrics'].items():
            writer.writerow([
                task,
                f"{metrics['r2']:.4f}",
                f"{metrics['rmse']:.4f}",
                f"{metrics['mae']:.4f}",
                f"{metrics['correlation']:.4f}"
            ])
        
        writer.writerow([])
        
        # 写入任务平均误差
        writer.writerow(['任务平均误差'])
        writer.writerow(['任务'] + self.tasks)
        writer.writerow(['平均绝对误差'] + [f"{err:.4f}" for err in results['task_comparison']['avg_abs_errors']])
        writer.writerow(['真实平均值'] + [f"{val:.4f}" for val in results['task_comparison']['avg_actuals']])
        
        return output.getvalue()
