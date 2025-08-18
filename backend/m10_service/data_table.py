"""
NPZ数据表格化服务
==================

将训练用的NPZ文件转换为可视化表格，支持数据分析、统计和导出功能。
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

from .loader import ModelManager
from .config import DEFAULT_SIG, MODELS_ROOT

logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """递归转换NumPy数据类型为Python原生类型"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj

# 特征名称映射（与模块10-A保持一致）
FEATURE_NAMES = [
    "game_duration",    # 游戏时长
    "roi_kw_time",      # 关键词ROI时间
    "roi_inst_time",    # 指令ROI时间  
    "roi_bg_time",      # 背景ROI时间
    "rr_1d",           # 1D递归率
    "det_1d",          # 1D确定性
    "ent_1d",          # 1D熵值
    "rr_2d",           # 2D递归率
    "det_2d",          # 2D确定性
    "ent_2d"           # 2D熵值
]

FEATURE_DISPLAY_NAMES = {
    "game_duration": "游戏时长",
    "roi_kw_time": "关键词ROI时间",
    "roi_inst_time": "指令ROI时间",
    "roi_bg_time": "背景ROI时间",
    "rr_1d": "1D递归率",
    "det_1d": "1D确定性",
    "ent_1d": "1D熵值",
    "rr_2d": "2D递归率",
    "det_2d": "2D确定性",
    "ent_2d": "2D熵值"
}


class DataTableService:
    """NPZ数据表格化服务类"""
    
    @staticmethod
    def npz_to_dataframe(npz_path: str, include_predictions: bool = True) -> Dict[str, Any]:
        """
        将NPZ文件转换为表格数据
        
        Args:
            npz_path: NPZ文件路径
            include_predictions: 是否包含模型预测结果
            
        Returns:
            完整的表格数据和统计信息
        """
        try:
            # 验证文件存在
            path = Path(npz_path)
            if not path.exists():
                raise FileNotFoundError(f"NPZ文件不存在: {npz_path}")
            
            logger.info(f"加载NPZ文件: {npz_path}")
            
            # 加载NPZ数据
            data = np.load(npz_path, allow_pickle=True)
            
            # 提取基础数据
            X = data["X"]  # (N, 10) 特征矩阵
            y = data["y"]  # (N,) MMSE标签
            feature_names = data.get("feature_names", FEATURE_NAMES)
            task_id = data.get("task_id", path.stem)
            
            logger.info(f"数据加载成功: {len(X)}个样本, {X.shape[1]}个特征")
            
            # 创建基础DataFrame
            df = pd.DataFrame(X, columns=feature_names[:X.shape[1]])
            df["MMSE_Score"] = y
            df["Sample_ID"] = range(1, len(df) + 1)
            df["Task"] = task_id
            
            # 重新排序列，将重要信息放在前面
            feature_cols = feature_names[:X.shape[1]].tolist() if hasattr(feature_names, 'tolist') else list(feature_names[:X.shape[1]])
            column_order = ["Sample_ID", "Task", "MMSE_Score"] + feature_cols
            df = df[column_order]
            
            # 添加预测结果（如果需要且模型可用）
            if include_predictions:
                predictions, prediction_stats = DataTableService._get_predictions(X, task_id)
                if predictions is not None:
                    df["Predicted_Score"] = predictions
                    df["Prediction_Error"] = df["Predicted_Score"] - df["MMSE_Score"]
                    df["Error_Percentage"] = (df["Prediction_Error"].abs() / (df["MMSE_Score"] + 1e-8)) * 100
                    
                    # 更新列顺序
                    prediction_cols = ["Predicted_Score", "Prediction_Error", "Error_Percentage"]
                    other_cols = [col for col in df.columns if col not in prediction_cols]
                    df = df[other_cols + prediction_cols]
            
            # 添加数据质量评估
            df["Data_Quality"] = DataTableService._assess_data_quality(X)
            
            # 计算统计信息
            summary_stats = DataTableService._calculate_summary(df, include_predictions)
            correlation_matrix = DataTableService._calculate_correlations(df)
            
            # 确保DataFrame中的数据是JSON可序列化的
            table_data = []
            for record in df.to_dict("records"):
                clean_record = {}
                for key, value in record.items():
                    if isinstance(value, (np.integer, np.floating)):
                        clean_record[key] = float(value)
                    elif isinstance(value, np.ndarray):
                        clean_record[key] = value.tolist()
                    elif pd.isna(value):
                        clean_record[key] = None
                    else:
                        clean_record[key] = value
                table_data.append(clean_record)
            
            result = {
                "task_id": task_id,
                "npz_path": str(path),
                "total_samples": len(df),
                "feature_names": feature_cols,
                "feature_display_names": FEATURE_DISPLAY_NAMES,
                "table_data": table_data,
                "summary_stats": summary_stats,
                "correlation_matrix": correlation_matrix,
                "has_predictions": include_predictions and "Predicted_Score" in df.columns,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"表格数据转换完成: {len(df)}行 × {len(df.columns)}列")
            
            # 确保所有数据都是JSON可序列化的
            result = convert_numpy_types(result)
            
            return result
            
        except Exception as e:
            logger.error(f"NPZ转表格失败: {str(e)}")
            raise
    
    @staticmethod
    def _get_predictions(X: np.ndarray, task_id: str) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """
        获取模型预测结果
        
        Args:
            X: 特征矩阵
            task_id: 任务ID
            
        Returns:
            (预测结果数组, 预测统计信息)
        """
        try:
            # 检查是否有激活的模型
            active_models = ModelManager.get_active_models()
            if task_id not in active_models:
                logger.warning(f"任务 {task_id} 没有激活的模型，跳过预测")
                return None, None
            
            logger.info(f"为 {task_id} 生成预测结果...")
            
            # 批量预测
            predictions = []
            failed_count = 0
            
            for i, features in enumerate(X):
                try:
                    # 确保features是Python list格式
                    feature_list = features.tolist() if hasattr(features, 'tolist') else list(features)
                    pred = ModelManager.predict(task_id, feature_list)
                    predictions.append(pred)
                except Exception as e:
                    logger.warning(f"样本 {i} 预测失败: {e}")
                    predictions.append(np.nan)
                    failed_count += 1
            
            predictions = np.array(predictions)
            
            # 统计预测质量
            valid_predictions = predictions[~np.isnan(predictions)]
            prediction_stats = {
                "total_samples": len(predictions),
                "successful_predictions": len(valid_predictions),
                "failed_predictions": failed_count,
                "success_rate": len(valid_predictions) / len(predictions) if len(predictions) > 0 else 0,
                "prediction_range": {
                    "min": float(valid_predictions.min()) if len(valid_predictions) > 0 else None,
                    "max": float(valid_predictions.max()) if len(valid_predictions) > 0 else None,
                    "mean": float(valid_predictions.mean()) if len(valid_predictions) > 0 else None,
                    "std": float(valid_predictions.std()) if len(valid_predictions) > 0 else None
                }
            }
            
            logger.info(f"预测完成: {len(valid_predictions)}/{len(predictions)} 成功")
            return predictions, prediction_stats
            
        except Exception as e:
            logger.error(f"获取预测结果失败: {e}")
            return None, None
    
    @staticmethod
    def _assess_data_quality(X: np.ndarray) -> List[str]:
        """
        评估数据质量
        
        Args:
            X: 特征矩阵 (N, feature_count)
            
        Returns:
            每个样本的质量评级列表
        """
        quality_labels = []
        
        for i, sample in enumerate(X):
            # 检查缺失值
            if np.any(np.isnan(sample)) or np.any(np.isinf(sample)):
                quality_labels.append("异常")
                continue
            
            # 检查数值范围（假设特征已归一化到[0,1]）
            if np.any(sample < 0) or np.any(sample > 1):
                quality_labels.append("警告")
                continue
                
            # 检查是否有异常的零值或极值
            zero_count = np.sum(sample == 0)
            one_count = np.sum(sample == 1)
            feature_count = len(sample)
            
            if zero_count > feature_count * 0.5:  # 超过50%的特征为0
                quality_labels.append("可疑")
            elif one_count > feature_count * 0.5:  # 超过50%的特征为1
                quality_labels.append("可疑")
            elif zero_count + one_count > feature_count * 0.8:  # 超过80%为极值
                quality_labels.append("一般")
            else:
                quality_labels.append("良好")
        
        return quality_labels
    
    @staticmethod
    def _calculate_summary(df: pd.DataFrame, has_predictions: bool = False) -> Dict[str, Any]:
        """
        计算数据统计摘要
        
        Args:
            df: 数据框
            has_predictions: 是否包含预测结果
            
        Returns:
            统计摘要字典
        """
        # 基础统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        feature_cols = [col for col in numeric_cols if col in FEATURE_NAMES]
        
        summary = {
            "total_samples": len(df),
            "feature_count": len(feature_cols),
            "missing_values": int(df.isnull().sum().sum()),
            
            # MMSE分数统计
            "mmse_stats": {
                "mean": float(df["MMSE_Score"].mean()),
                "std": float(df["MMSE_Score"].std()),
                "min": float(df["MMSE_Score"].min()),
                "max": float(df["MMSE_Score"].max()),
                "median": float(df["MMSE_Score"].median()),
                "quartiles": {
                    "q25": float(df["MMSE_Score"].quantile(0.25)),
                    "q75": float(df["MMSE_Score"].quantile(0.75))
                }
            },
            
            # 特征统计
            "feature_stats": {},
            
            # 数据质量分布
            "quality_distribution": df["Data_Quality"].value_counts().to_dict()
        }
        
        # 每个特征的详细统计
        for col in feature_cols:
            if col in df.columns:
                col_data = df[col]
                summary["feature_stats"][col] = {
                    "mean": float(col_data.mean()) if len(col_data) > 0 else 0.0,
                    "std": float(col_data.std()) if len(col_data) > 0 else 0.0,
                    "min": float(col_data.min()) if len(col_data) > 0 else 0.0,
                    "max": float(col_data.max()) if len(col_data) > 0 else 0.0,
                    "zero_count": int((col_data == 0).sum()),
                    "one_count": int((col_data == 1).sum())
                }
        
        # 预测准确性统计（如果有预测结果）
        if has_predictions and "Predicted_Score" in df.columns:
            pred_df = df.dropna(subset=["Predicted_Score"])
            if len(pred_df) > 0:
                errors = pred_df["Prediction_Error"]
                
                # 计算回归指标
                from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
                
                try:
                    rmse = np.sqrt(mean_squared_error(pred_df["MMSE_Score"], pred_df["Predicted_Score"]))
                    mae = mean_absolute_error(pred_df["MMSE_Score"], pred_df["Predicted_Score"])
                    r2 = r2_score(pred_df["MMSE_Score"], pred_df["Predicted_Score"])
                    
                    summary["prediction_accuracy"] = {
                        "rmse": float(rmse),
                        "mae": float(mae),
                        "r2": float(r2),
                        "mean_error": float(errors.mean()),
                        "std_error": float(errors.std()),
                        "min_error": float(errors.min()),
                        "max_error": float(errors.max()),
                        "successful_predictions": len(pred_df),
                        "prediction_rate": len(pred_df) / len(df)
                    }
                except Exception as e:
                    logger.warning(f"计算预测准确性失败: {e}")
                    summary["prediction_accuracy"] = None
        
        return summary
    
    @staticmethod
    def _calculate_correlations(df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算特征相关性矩阵
        
        Args:
            df: 数据框
            
        Returns:
            相关性矩阵和分析结果
        """
        try:
            # 选择数值型特征列
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            feature_cols = [col for col in numeric_cols if col in FEATURE_NAMES]
            
            if "MMSE_Score" in df.columns:
                analysis_cols = feature_cols + ["MMSE_Score"]
            else:
                analysis_cols = feature_cols
            
            # 计算相关性矩阵
            corr_matrix = df[analysis_cols].corr()
            
            # 找出与MMSE分数最相关的特征
            mmse_correlations = {}
            if "MMSE_Score" in corr_matrix.columns:
                mmse_corr = corr_matrix["MMSE_Score"].drop("MMSE_Score")
                mmse_correlations = {
                    "top_positive": mmse_corr.nlargest(3).to_dict(),
                    "top_negative": mmse_corr.nsmallest(3).to_dict(),
                    "all_correlations": mmse_corr.to_dict()
                }
            
            # 找出特征间的强相关性
            feature_correlations = []
            for i, col1 in enumerate(feature_cols):
                for col2 in feature_cols[i+1:]:
                    if col1 in corr_matrix.columns and col2 in corr_matrix.columns:
                        corr_value = corr_matrix.loc[col1, col2]
                        if abs(corr_value) > 0.7:  # 强相关性阈值
                            feature_correlations.append({
                                "feature1": col1,
                                "feature2": col2,
                                "correlation": float(corr_value),
                                "strength": "强" if abs(corr_value) > 0.8 else "中等"
                            })
            
            # 转换为JSON可序列化的格式
            corr_dict = {}
            for col in corr_matrix.columns:
                corr_dict[col] = {}
                for idx in corr_matrix.index:
                    corr_dict[col][idx] = float(corr_matrix.loc[idx, col])
            
            # 确保MMSE相关性也是可序列化的
            if mmse_correlations:
                for key in ["top_positive", "top_negative", "all_correlations"]:
                    if key in mmse_correlations:
                        mmse_correlations[key] = {k: float(v) for k, v in mmse_correlations[key].items()}
            
            return {
                "correlation_matrix": corr_dict,
                "mmse_correlations": mmse_correlations,
                "feature_correlations": feature_correlations,
                "matrix_size": list(corr_matrix.shape)
            }
            
        except Exception as e:
            logger.error(f"计算相关性矩阵失败: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def paginate_data(table_data: Dict[str, Any], page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        数据分页处理
        
        Args:
            table_data: 完整表格数据
            page: 页码（从1开始）
            page_size: 每页大小
            
        Returns:
            分页后的数据
        """
        data_list = table_data["table_data"]
        total_items = len(data_list)
        total_pages = (total_items + page_size - 1) // page_size
        
        # 计算分页范围
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        
        paginated_data = data_list[start_idx:end_idx]
        
        result = table_data.copy()
        result["table_data"] = paginated_data
        result["pagination"] = {
            "current_page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "start_index": start_idx + 1,
            "end_index": end_idx,
            "has_previous": page > 1,
            "has_next": page < total_pages
        }
        
        return result
    
    @staticmethod
    def to_csv(table_data: Dict[str, Any]) -> str:
        """
        转换为CSV格式
        
        Args:
            table_data: 表格数据
            
        Returns:
            CSV字符串
        """
        df = pd.DataFrame(table_data["table_data"])
        return df.to_csv(index=False, encoding='utf-8-sig')  # 使用UTF-8 BOM确保中文正确显示
    
    @staticmethod
    def to_excel(table_data: Dict[str, Any]) -> bytes:
        """
        转换为Excel格式
        
        Args:
            table_data: 表格数据
            
        Returns:
            Excel文件字节数据
        """
        import io
        
        # 创建Excel writer
        output = io.BytesIO()
        df = pd.DataFrame(table_data["table_data"])
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 主数据表
            df.to_excel(writer, sheet_name='训练数据', index=False)
            
            # 统计摘要表
            if "summary_stats" in table_data:
                stats = table_data["summary_stats"]
                summary_data = []
                
                # MMSE统计
                if "mmse_stats" in stats:
                    mmse = stats["mmse_stats"]
                    summary_data.extend([
                        ["MMSE分数统计", ""],
                        ["均值", mmse.get("mean", "")],
                        ["标准差", mmse.get("std", "")],
                        ["最小值", mmse.get("min", "")],
                        ["最大值", mmse.get("max", "")],
                        ["中位数", mmse.get("median", "")],
                        ["", ""]
                    ])
                
                # 数据质量分布
                if "quality_distribution" in stats:
                    summary_data.append(["数据质量分布", ""])
                    for quality, count in stats["quality_distribution"].items():
                        summary_data.append([quality, count])
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data, columns=["指标", "数值"])
                    summary_df.to_excel(writer, sheet_name='统计摘要', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def compare_datasets(datasets: List[Dict[str, str]], comparison_type: str = "statistics") -> Dict[str, Any]:
        """
        对比多个数据集
        
        Args:
            datasets: 数据集列表，每个包含q_tag和rqa_sig
            comparison_type: 对比类型 (statistics/distributions/correlations)
            
        Returns:
            对比结果
        """
        try:
            comparison_data = []
            
            for dataset_info in datasets:
                q_tag = dataset_info.get("q_tag")
                rqa_sig = dataset_info.get("rqa_sig", DEFAULT_SIG)
                
                # 构建NPZ路径
                npz_path = f"data/module10_datasets/{rqa_sig}/{q_tag}.npz"
                
                if Path(npz_path).exists():
                    data = DataTableService.npz_to_dataframe(npz_path, include_predictions=False)
                    comparison_data.append({
                        "dataset_id": f"{rqa_sig}_{q_tag}",
                        "q_tag": q_tag,
                        "rqa_sig": rqa_sig,
                        "data": data
                    })
            
            if comparison_type == "statistics":
                return DataTableService._compare_statistics(comparison_data)
            elif comparison_type == "distributions":
                return DataTableService._compare_distributions(comparison_data)
            elif comparison_type == "correlations":
                return DataTableService._compare_correlations(comparison_data)
            else:
                raise ValueError(f"不支持的对比类型: {comparison_type}")
                
        except Exception as e:
            logger.error(f"数据集对比失败: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _compare_statistics(comparison_data: List[Dict]) -> Dict[str, Any]:
        """对比统计信息"""
        result = {
            "comparison_type": "statistics",
            "datasets": [],
            "summary": {}
        }
        
        for item in comparison_data:
            dataset_id = item["dataset_id"]
            stats = item["data"]["summary_stats"]
            
            result["datasets"].append({
                "dataset_id": dataset_id,
                "q_tag": item["q_tag"],
                "rqa_sig": item["rqa_sig"],
                "sample_count": stats["total_samples"],
                "mmse_mean": stats["mmse_stats"]["mean"],
                "mmse_std": stats["mmse_stats"]["std"],
                "quality_good_ratio": stats["quality_distribution"].get("良好", 0) / stats["total_samples"]
            })
        
        # 计算汇总信息
        if result["datasets"]:
            sample_counts = [d["sample_count"] for d in result["datasets"]]
            mmse_means = [d["mmse_mean"] for d in result["datasets"]]
            
            result["summary"] = {
                "total_datasets": len(result["datasets"]),
                "total_samples": sum(sample_counts),
                "sample_count_range": {"min": min(sample_counts), "max": max(sample_counts)},
                "mmse_mean_range": {"min": min(mmse_means), "max": max(mmse_means)}
            }
        
        return result
    
    @staticmethod
    def _compare_distributions(comparison_data: List[Dict]) -> Dict[str, Any]:
        """对比数据分布"""
        # 简化实现，返回每个数据集的分布摘要
        result = {
            "comparison_type": "distributions",
            "datasets": []
        }
        
        for item in comparison_data:
            dataset_id = item["dataset_id"]
            data = item["data"]
            
            # 计算特征分布
            feature_distributions = {}
            if "table_data" in data and data["table_data"]:
                df = pd.DataFrame(data["table_data"])
                for feature in FEATURE_NAMES:
                    if feature in df.columns:
                        feature_distributions[feature] = {
                            "mean": float(df[feature].mean()),
                            "std": float(df[feature].std()),
                            "skewness": float(df[feature].skew()),
                            "kurtosis": float(df[feature].kurtosis())
                        }
            
            result["datasets"].append({
                "dataset_id": dataset_id,
                "q_tag": item["q_tag"],
                "feature_distributions": feature_distributions
            })
        
        return result
    
    @staticmethod
    def _compare_correlations(comparison_data: List[Dict]) -> Dict[str, Any]:
        """对比相关性"""
        result = {
            "comparison_type": "correlations",
            "datasets": []
        }
        
        for item in comparison_data:
            dataset_id = item["dataset_id"]
            corr_data = item["data"]["correlation_matrix"]
            
            result["datasets"].append({
                "dataset_id": dataset_id,
                "q_tag": item["q_tag"],
                "mmse_correlations": corr_data.get("mmse_correlations", {}),
                "strong_correlations": len(corr_data.get("feature_correlations", []))
            })
        
        return result
