"""
模块10-A数据校验模块
负责验证从模块7加载的数据格式和质量
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from .settings import (
    FEATURE_NAMES, TASK_IDS, GROUP_TYPES, 
    VALIDATION_CONFIG
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """数据验证错误异常"""
    pass


class DataValidator:
    """数据验证器"""
    
    def __init__(self, tolerance: float = None):
        """
        初始化验证器
        
        Args:
            tolerance: 数值容差，默认使用配置文件中的值
        """
        self.tolerance = tolerance or VALIDATION_CONFIG["tolerance"]
        self.feature_range = VALIDATION_CONFIG["feature_range"]
        self.required_columns = VALIDATION_CONFIG["required_columns"]
        self.min_samples_per_task = VALIDATION_CONFIG["min_samples_per_task"]
    
    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证DataFrame的完整性和质量
        
        Args:
            df: 待验证的DataFrame
            
        Returns:
            Dict: 验证结果报告
            
        Raises:
            ValidationError: 当数据不符合要求时
        """
        report = {
            "total_records": len(df),
            "validation_passed": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        try:
            # 1. 检查必需列
            self._check_required_columns(df, report)
            
            # 2. 检查特征值范围
            self._check_feature_ranges(df, report)
            
            # 3. 检查任务ID有效性
            self._check_task_ids(df, report)
            
            # 4. 检查组别有效性
            self._check_group_types(df, report)
            
            # 5. 检查每个任务的样本数
            self._check_sample_counts(df, report)
            
            # 6. 生成统计信息
            self._generate_statistics(df, report)
            
            # 判断整体验证结果
            if report["errors"]:
                report["validation_passed"] = False
                error_msg = f"数据验证失败: {'; '.join(report['errors'])}"
                logger.error(error_msg)
                raise ValidationError(error_msg)
            
            if report["warnings"]:
                for warning in report["warnings"]:
                    logger.warning(warning)
            
            logger.info(f"数据验证通过: {report['total_records']} 条记录")
            return report
            
        except Exception as e:
            report["validation_passed"] = False
            report["errors"].append(str(e))
            raise ValidationError(f"数据验证过程出错: {str(e)}")
    
    def _check_required_columns(self, df: pd.DataFrame, report: Dict[str, Any]):
        """检查必需列是否存在"""
        missing_columns = set(self.required_columns) - set(df.columns)
        if missing_columns:
            report["errors"].append(f"缺少必需列: {list(missing_columns)}")
    
    def _check_feature_ranges(self, df: pd.DataFrame, report: Dict[str, Any]):
        """检查特征值是否在有效范围内"""
        feature_issues = []
        
        for feature in FEATURE_NAMES:
            if feature not in df.columns:
                continue
                
            values = df[feature].values
            
            # 检查是否有NaN值
            nan_count = np.isnan(values).sum()
            if nan_count > 0:
                feature_issues.append(f"{feature}: {nan_count} 个NaN值")
            
            # 检查数值范围
            valid_values = values[~np.isnan(values)]
            if len(valid_values) > 0:
                min_val, max_val = valid_values.min(), valid_values.max()
                
                if min_val < self.feature_range[0] - self.tolerance:
                    feature_issues.append(f"{feature}: 最小值 {min_val:.6f} 小于下限 {self.feature_range[0]}")
                
                if max_val > self.feature_range[1] + self.tolerance:
                    feature_issues.append(f"{feature}: 最大值 {max_val:.6f} 大于上限 {self.feature_range[1]}")
        
        if feature_issues:
            report["errors"].extend(feature_issues)
    
    def _check_task_ids(self, df: pd.DataFrame, report: Dict[str, Any]):
        """检查任务ID有效性"""
        if "task_id" in df.columns:
            invalid_tasks = set(df["task_id"].unique()) - set(TASK_IDS)
            if invalid_tasks:
                report["errors"].append(f"无效的任务ID: {list(invalid_tasks)}")
    
    def _check_group_types(self, df: pd.DataFrame, report: Dict[str, Any]):
        """检查组别有效性"""
        if "group_type" in df.columns:
            invalid_groups = set(df["group_type"].unique()) - set(GROUP_TYPES)
            if invalid_groups:
                report["errors"].append(f"无效的组别: {list(invalid_groups)}")
    
    def _check_sample_counts(self, df: pd.DataFrame, report: Dict[str, Any]):
        """检查每个任务的样本数"""
        if "task_id" in df.columns:
            task_counts = df["task_id"].value_counts()
            
            for task_id in TASK_IDS:
                count = task_counts.get(task_id, 0)
                if count == 0:
                    report["warnings"].append(f"任务 {task_id} 没有样本")
                elif count < self.min_samples_per_task:
                    report["warnings"].append(f"任务 {task_id} 样本数过少: {count} < {self.min_samples_per_task}")
    
    def _generate_statistics(self, df: pd.DataFrame, report: Dict[str, Any]):
        """生成数据统计信息"""
        stats = {}
        
        # 基本统计
        if "task_id" in df.columns:
            stats["task_distribution"] = df["task_id"].value_counts().to_dict()
        
        if "group_type" in df.columns:
            stats["group_distribution"] = df["group_type"].value_counts().to_dict()
        
        # 特征统计
        feature_stats = {}
        for feature in FEATURE_NAMES:
            if feature in df.columns:
                values = df[feature].dropna()
                if len(values) > 0:
                    feature_stats[feature] = {
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "valid_count": len(values)
                    }
        
        stats["feature_statistics"] = feature_stats
        report["statistics"] = stats


def validate_rqa_signature(rqa_sig: str) -> bool:
    """
    验证RQA签名格式
    
    Args:
        rqa_sig: RQA参数签名 (如: m2_tau1_eps0.06_lmin2)
        
    Returns:
        bool: 是否为有效格式
    """
    import re
    pattern = r'^m\d+_tau\d+_eps[\d.]+_lmin\d+$'
    return bool(re.match(pattern, rqa_sig))