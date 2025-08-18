"""
模型管理器 - ModelManager
========================

负责模型的加载、缓存、版本管理和推理。
线程安全，支持多并发请求。
"""

import threading
import torch
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

from .config import (
    MODELS_ROOT, CACHE_LIMIT, DEFAULT_SIG, PREDICTION_DEVICE,
    TORCH_THREADS, VALID_Q_TAGS, MODEL_LOAD_TIMEOUT
)

# 配置torch线程数
torch.set_num_threads(TORCH_THREADS)

logger = logging.getLogger(__name__)


class ModelManager:
    """
    模型管理器
    
    功能：
    - 枚举可用模型版本
    - 按q_tag加载/缓存/卸载TorchScript  
    - 线程安全的模型激活和切换
    - 提供推理接口
    """
    
    # 类变量：模型缓存和状态
    _cache: Dict[Tuple[str, str, str], torch.jit.ScriptModule] = {}  # {(sig, q_tag, ver): model}
    _active: Dict[str, Tuple[str, str, str]] = {}  # {q_tag: (sig, q_tag, ver)}
    _lock = threading.Lock()
    _load_times: Dict[str, datetime] = {}  # 记录加载时间
    
    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        """
        列出所有可用的模型版本
        
        Returns:
            [{'q': 'Q1', 'sig': '...', 'versions': ['20250805_1503', 'best']}, ...]
        """
        result = []
        
        if not MODELS_ROOT.exists():
            logger.warning(f"模型根目录不存在: {MODELS_ROOT}")
            return result
            
        try:
            # 遍历所有RQA签名目录
            for sig_dir in MODELS_ROOT.iterdir():
                if not sig_dir.is_dir():
                    continue
                    
                sig = sig_dir.name
                
                # 为每个Q任务查找可用版本
                for q_tag in VALID_Q_TAGS:
                    versions = []
                    
                    # 查找该Q任务的所有模型文件
                    for model_file in sig_dir.glob(f"{q_tag}_*.pt"):
                        # 从文件名提取版本号
                        version = model_file.stem.replace(f"{q_tag}_", "")
                        versions.append(version)
                    
                    # 检查是否有TorchScript文件
                    for ts_file in sig_dir.glob(f"{q_tag}_*.ts"):
                        version = ts_file.stem.replace(f"{q_tag}_", "")
                        if version not in versions:
                            versions.append(version)
                    
                    if versions:
                        # 排序：best优先，然后按时间戳降序
                        versions.sort(key=lambda v: (v != "best", v), reverse=True)
                        
                        result.append({
                            "q": q_tag,
                            "sig": sig,
                            "versions": versions,
                            "active": cls._active.get(q_tag, [None, None, None])[2]  # 当前激活版本
                        })
                        
        except Exception as e:
            logger.error(f"列举模型时出错: {e}")
            
        return result
    
    @classmethod
    def activate(cls, q_tag: str, sig: str, version: str) -> bool:
        """
        激活指定版本的模型
        
        Args:
            q_tag: 任务标签 (Q1-Q5)
            sig: RQA参数签名
            version: 模型版本
            
        Returns:
            是否激活成功
            
        Raises:
            ValueError: 参数无效
            FileNotFoundError: 模型文件不存在
            RuntimeError: 模型加载失败
        """
        if q_tag not in VALID_Q_TAGS:
            raise ValueError(f"无效的任务标签: {q_tag}")
            
        with cls._lock:
            try:
                key = (sig, q_tag, version)
                
                # 如果模型未缓存，则加载
                if key not in cls._cache:
                    logger.info(f"加载模型: {sig}/{q_tag}_{version}")
                    model = cls._load_script(sig, q_tag, version)
                    cls._cache[key] = model
                    cls._load_times[f"{sig}_{q_tag}_{version}"] = datetime.now()
                
                # 激活模型
                old_active = cls._active.get(q_tag)
                cls._active[q_tag] = key
                
                # 强制缓存限制
                cls._enforce_limit()
                
                logger.info(f"模型已激活: {q_tag} -> {sig}/{version}")
                if old_active and old_active != key:
                    logger.info(f"替换旧模型: {old_active[0]}/{old_active[2]}")
                    
                return True
                
            except Exception as e:
                logger.error(f"激活模型失败 {sig}/{q_tag}_{version}: {e}")
                raise
    
    @classmethod
    def predict(cls, q_tag: str, features: List[float]) -> float:
        """
        使用激活的模型进行预测
        
        Args:
            q_tag: 任务标签
            features: 输入特征向量 (长度=10)
            
        Returns:
            预测的MMSE子分数 (0-1范围)
            
        Raises:
            RuntimeError: 模型未激活或预测失败
            ValueError: 特征向量长度不正确
        """
        if len(features) != 10:
            raise ValueError(f"特征向量长度必须为10，实际为{len(features)}")
            
        # 获取激活的模型
        key = cls._active.get(q_tag)
        if not key:
            raise RuntimeError(f"任务 {q_tag} 未激活模型，请先调用activate()")
            
        model = cls._cache.get(key)
        if not model:
            raise RuntimeError(f"模型缓存异常，{q_tag} 对应的模型不存在")
            
        try:
            # 执行推理
            with torch.no_grad():
                # 转换输入格式
                x = torch.tensor(features, dtype=torch.float32, device=PREDICTION_DEVICE)
                x = x.unsqueeze(0)  # 添加batch维度: [1, 10]
                
                # 模型推理
                output = model(x)
                score = output.item()
                
                # 确保输出在合理范围内 (0-1)
                score = max(0.0, min(1.0, score))
                
                logger.debug(f"预测完成: {q_tag} -> {score:.4f}")
                return score
                
        except Exception as e:
            logger.error(f"预测失败 {q_tag}: {e}")
            raise RuntimeError(f"预测失败: {e}")
    
    @classmethod
    def get_active_models(cls) -> Dict[str, Dict[str, str]]:
        """获取当前激活的模型信息"""
        result = {}
        for q_tag, key in cls._active.items():
            if key:
                sig, _, version = key
                result[q_tag] = {
                    "sig": sig,
                    "version": version,
                    "load_time": cls._load_times.get(f"{sig}_{q_tag}_{version}", "未知").isoformat() if isinstance(cls._load_times.get(f"{sig}_{q_tag}_{version}"), datetime) else "未知"
                }
        return result
    
    @classmethod
    def clear_cache(cls, q_tag: Optional[str] = None) -> int:
        """
        清理模型缓存
        
        Args:
            q_tag: 如果指定，只清理该任务的缓存；否则清理所有
            
        Returns:
            清理的模型数量
        """
        with cls._lock:
            if q_tag:
                # 清理指定任务
                to_remove = [key for key in cls._cache.keys() if key[1] == q_tag]
                for key in to_remove:
                    del cls._cache[key]
                    cls._load_times.pop(f"{key[0]}_{key[1]}_{key[2]}", None)
                
                # 取消激活
                if q_tag in cls._active:
                    del cls._active[q_tag]
                    
                logger.info(f"已清理 {q_tag} 的 {len(to_remove)} 个模型缓存")
                return len(to_remove)
            else:
                # 清理所有
                count = len(cls._cache)
                cls._cache.clear()
                cls._active.clear()
                cls._load_times.clear()
                logger.info(f"已清理所有 {count} 个模型缓存")
                return count
    
    # ==================== 私有方法 ====================
    
    @staticmethod
    def _load_script(sig: str, q_tag: str, version: str) -> torch.jit.ScriptModule:
        """
        加载TorchScript模型
        
        支持两种格式：
        1. 直接的TorchScript文件 (.ts)
        2. PyTorch state_dict文件 (.pt) - 会自动转换为TorchScript
        """
        model_dir = MODELS_ROOT / sig
        
        # 优先查找TorchScript文件
        ts_path = model_dir / f"{q_tag}_{version}.ts"
        if ts_path.exists():
            try:
                logger.debug(f"加载TorchScript: {ts_path}")
                return torch.jit.load(ts_path, map_location=PREDICTION_DEVICE)
            except Exception as e:
                logger.warning(f"TorchScript加载失败，尝试重新转换: {e}")
        
        # 查找PyTorch文件并转换
        pt_path = model_dir / f"{q_tag}_{version}.pt"
        if not pt_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {pt_path}")
        
        try:
            logger.debug(f"加载PyTorch模型: {pt_path}")
            checkpoint = torch.load(pt_path, map_location=PREDICTION_DEVICE, weights_only=False)
            
            # 判断文件格式
            if isinstance(checkpoint, torch.jit.ScriptModule):
                # 已经是TorchScript
                return checkpoint
            elif isinstance(checkpoint, dict) and ("model_state" in checkpoint or "model_state_dict" in checkpoint):
                # state_dict格式，需要转换
                return ModelManager._convert_to_script(checkpoint, ts_path)
            else:
                raise ValueError(f"未知的模型文件格式: {type(checkpoint)}")
                
        except Exception as e:
            raise RuntimeError(f"模型加载失败 {pt_path}: {e}")
    
    @staticmethod
    def _convert_to_script(checkpoint: Dict, ts_path: Path) -> torch.jit.ScriptModule:
        """将state_dict转换为TorchScript"""
        try:
            # 动态导入模型类
            from backend.m10_training.model import EyeMLP
            
            # 重建模型
            model = EyeMLP(
                input_dim=10,
                h1=32,
                h2=16, 
                dropout=0.25,
                output_dim=1
            )
            
            # 加载权重 - 支持不同的键名
            if "model_state" in checkpoint:
                state_dict = checkpoint["model_state"]
            elif "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
            else:
                raise KeyError("无法找到模型状态字典键")
            
            model.load_state_dict(state_dict)
            model.eval()
            
            # 转换为TorchScript
            with torch.no_grad():
                scripted = torch.jit.script(model)
                
                # 保存TorchScript以供下次使用
                try:
                    ts_path.parent.mkdir(parents=True, exist_ok=True)
                    scripted.save(ts_path)
                    logger.info(f"TorchScript已保存: {ts_path}")
                except Exception as e:
                    logger.warning(f"TorchScript保存失败: {e}")
                
                return scripted
                
        except Exception as e:
            raise RuntimeError(f"state_dict转换失败: {e}")
    
    @classmethod
    def _enforce_limit(cls):
        """强制执行缓存数量限制，FIFO清理"""
        if len(cls._cache) <= CACHE_LIMIT:
            return
            
        # 计算需要清理的数量
        to_remove_count = len(cls._cache) - CACHE_LIMIT
        
        # 获取最旧的缓存项（基于加载时间）
        cache_items = list(cls._cache.keys())
        
        # 按加载时间排序，最旧的在前
        def get_load_time(key):
            sig, q_tag, version = key
            time_key = f"{sig}_{q_tag}_{version}"
            return cls._load_times.get(time_key, datetime.min)
        
        cache_items.sort(key=get_load_time)
        
        # 清理最旧的项目，但保留激活的模型
        removed_count = 0
        for key in cache_items:
            if removed_count >= to_remove_count:
                break
                
            # 检查是否为激活模型
            if key not in cls._active.values():
                sig, q_tag, version = key
                del cls._cache[key]
                cls._load_times.pop(f"{sig}_{q_tag}_{version}", None)
                removed_count += 1
                logger.debug(f"缓存清理: {sig}/{q_tag}_{version}")
        
        logger.info(f"缓存清理完成，移除了 {removed_count} 个模型")