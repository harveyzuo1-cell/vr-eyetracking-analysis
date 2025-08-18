"""
模块10-A特征构建器
负责从模块7的输出构建按任务分类的训练数据集
"""

import pandas as pd
import numpy as np
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import logging

from .settings import (
    MODULE7_ROOT, MODULE10_ROOT, FEATURE_NAMES, FEATURE_ALIAS, TASK_IDS,
    FILE_PATTERNS, DEFAULT_CONFIG
)
from .schema import DataValidator, validate_rqa_signature, ValidationError

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureBuilder:
    """特征数据构建器"""
    
    def __init__(self, rqa_sig: str, val_split: float = None, 
                 out_root: str = None, random_state: int = None):
        """
        初始化构建器
        
        Args:
            rqa_sig: RQA参数签名 (如: m2_tau1_eps0.06_lmin2)
            val_split: 验证集比例
            out_root: 输出根目录
            random_state: 随机种子
        """
        # 验证RQA签名格式
        if not validate_rqa_signature(rqa_sig):
            raise ValueError(f"无效的RQA签名格式: {rqa_sig}")
        
        self.rqa_sig = rqa_sig
        self.val_split = val_split or DEFAULT_CONFIG["val_split"]
        self.random_state = random_state or DEFAULT_CONFIG["random_state"]
        
        # 设置路径
        self.module7_dir = MODULE7_ROOT / rqa_sig
        self.output_dir = Path(out_root) / rqa_sig if out_root else MODULE10_ROOT / rqa_sig
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.validator = DataValidator()
        self.meta = None
        
        logger.info(f"初始化FeatureBuilder: RQA签名={rqa_sig}, 输出目录={self.output_dir}")
    
    def check_prerequisites(self) -> Dict[str, Any]:
        """
        检查前置条件：模块7输出是否就绪
        
        Returns:
            Dict: 检查结果报告
        """
        report = {
            "rqa_sig": self.rqa_sig,
            "module7_ready": False,
            "csv_files": [],
            "metadata_exists": False,
            "errors": []
        }
        
        try:
            # 检查模块7目录是否存在
            if not self.module7_dir.exists():
                report["errors"].append(f"模块7目录不存在: {self.module7_dir}")
                return report
            
            # 检查CSV文件
            csv_file = self.module7_dir / FILE_PATTERNS["module7_csv"]
            
            if not csv_file.exists():
                report["errors"].append(f"未找到CSV文件: {csv_file}")
                return report
            
            report["csv_files"] = [str(csv_file)]
            
            # 检查元数据文件
            meta_file = self.module7_dir / FILE_PATTERNS["module7_meta"]
            if meta_file.exists():
                report["metadata_exists"] = True
            else:
                report["errors"].append(f"元数据文件不存在: {meta_file}")
            
            if not report["errors"]:
                report["module7_ready"] = True
                logger.info(f"前置条件检查通过: 找到 {len(report['csv_files'])} 个CSV文件")
            
            return report
            
        except Exception as e:
            report["errors"].append(f"检查过程出错: {str(e)}")
            return report
    
    def load_raw(self) -> pd.DataFrame:
        """
        加载模块7的原始CSV数据
        
        Returns:
            pd.DataFrame: 合并后的数据框
            
        Raises:
            FileNotFoundError: 当找不到数据文件时
            ValidationError: 当数据格式不正确时
        """
        logger.info("开始加载模块7数据...")
        
        # 检查前置条件
        prereq_report = self.check_prerequisites()
        if not prereq_report["module7_ready"]:
            raise FileNotFoundError(f"模块7数据未就绪: {prereq_report['errors']}")
        
        # 加载所有CSV文件
        dataframes = []
        for csv_file in prereq_report["csv_files"]:
            try:
                df = pd.read_csv(csv_file)
                dataframes.append(df)
                logger.info(f"加载CSV文件: {Path(csv_file).name}, 记录数: {len(df)}")
            except Exception as e:
                logger.error(f"加载CSV文件失败 {csv_file}: {str(e)}")
                raise
        
        # 合并数据框
        if len(dataframes) == 1:
            combined_df = dataframes[0]
        else:
            combined_df = pd.concat(dataframes, ignore_index=True)
        
        logger.info(f"数据加载完成: 总记录数 {len(combined_df)}")
        
        # -------- 关键补丁：动态映射归一化列 --------
        norm_mappings = []
        for col in FEATURE_NAMES:
            norm_col = FEATURE_ALIAS[col]
            if norm_col in combined_df.columns:
                combined_df[col] = combined_df[norm_col]  # 覆盖为归一化值
                norm_mappings.append(f"'{col}' ← '{norm_col}'")
                logger.debug(f"特征映射: '{col}' ← '{norm_col}' (归一化)")
        
        if norm_mappings:
            logger.info(f"✅ 发现并使用归一化列，共 {len(norm_mappings)} 项")
            logger.debug(f"映射详情: {', '.join(norm_mappings)}")
        else:
            logger.warning("⚠️ 未发现*_norm列，使用原始列值")
        
        return combined_df
    
    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证数据质量
        
        Args:
            df: 待验证的数据框
            
        Returns:
            Dict: 验证报告
        """
        logger.info("开始数据验证...")
        validation_report = self.validator.validate_dataframe(df)
        logger.info("数据验证完成")
        return validation_report
    
    def to_class_level(self, df: pd.DataFrame) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        将数据转换为按任务分类的格式
        
        Args:
            df: 原始数据框
            
        Returns:
            Dict: 格式为 {'Q1': (X, y), 'Q2': (X, y), ...}
                  其中 X 是特征矩阵，y 是MMSE子分数数组
        """
        logger.info("开始数据转换为任务级别...")
        
        # 首先加载MMSE数据
        mmse_data = self._load_mmse_data()
        logger.info(f"加载了 {len(mmse_data)} 条MMSE记录")
        
        datasets = {}
        
        for task_id in TASK_IDS:
            # 筛选当前任务的数据
            task_data = df[df["task_id"] == task_id].copy()
            
            if len(task_data) == 0:
                logger.warning(f"任务 {task_id} 没有数据")
                continue
            
            # 按受试者分组并取均值（处理同一受试者多条记录的情况）
            subject_grouped = task_data.groupby("subject_id")[FEATURE_NAMES].mean().reset_index()
            
            # 合并MMSE分数
            merged_data = self._merge_with_mmse(subject_grouped, mmse_data, task_id)
            
            if len(merged_data) == 0:
                logger.warning(f"任务 {task_id} 没有匹配的MMSE数据")
                continue
            
            # 提取特征矩阵和MMSE子分数
            X = merged_data[FEATURE_NAMES].values
            y = merged_data[f"{task_id}_subscore_norm"].values  # 归一化的MMSE子分数
            
            # 验证数据质量
            if np.any(np.isnan(X)):
                logger.warning(f"任务 {task_id} 存在NaN值，将被填充为0")
                X = np.nan_to_num(X, nan=0.0)
            
            datasets[task_id] = (X, y)
            
            logger.info(f"任务 {task_id}: {len(X)} 个样本, 特征维度: {X.shape[1]}")
        
        logger.info(f"数据转换完成，共处理 {len(datasets)} 个任务")
        return datasets
    
    def _load_mmse_data(self) -> pd.DataFrame:
        """
        加载MMSE评分数据
        
        Returns:
            pd.DataFrame: 包含所有受试者MMSE分数的数据框
        """
        import os
        
        mmse_files = {
            'control': '控制组.csv',
            'mci': '轻度认知障碍组.csv', 
            'ad': '阿尔兹海默症组.csv'
        }
        
        all_mmse_data = []
        mmse_data_path = "data/MMSE_Score"
        
        for group_type, filename in mmse_files.items():
            file_path = os.path.join(mmse_data_path, filename)
            
            if not os.path.exists(file_path):
                logger.warning(f"MMSE文件不存在: {filename}")
                continue
            
            try:
                df = pd.read_csv(file_path)
                logger.debug(f"加载MMSE数据: {filename}, 记录数: {len(df)}")
                
                # 添加组别标识
                df['group_type'] = group_type
                
                # 处理受试者ID列（可能是'试者'或'受试者'）
                subject_col = None
                for col in ['试者', '受试者', 'Subject_ID']:
                    if col in df.columns:
                        subject_col = col
                        break
                
                if subject_col:
                    df['subject_id'] = df[subject_col].astype(str).str.lower()
                else:
                    logger.error(f"在{filename}中未找到受试者ID列")
                    continue
                
                # 计算各个任务的子分数
                df['Q1_subscore'] = (
                    df.get('年份', 0) + df.get('季节', 0) + 
                    df.get('月份', 0) + df.get('星期', 0)
                ).fillna(0)
                
                df['Q2_subscore'] = (
                    df.get('省市区', 0) + df.get('街道', 0) + 
                    df.get('建筑', 0) + df.get('楼层', 0)
                ).fillna(0)
                
                df['Q3_subscore'] = df.get('即刻记忆', 0).fillna(0)
                
                df['Q4_subscore'] = (
                    df.get('100-7', 0) + df.get('93-7', 0) + df.get('86-7', 0) + 
                    df.get('79-7', 0) + df.get('72-7', 0)
                ).fillna(0)
                
                df['Q5_subscore'] = (
                    df.get('词1', 0) + df.get('词2', 0) + df.get('词3', 0)
                ).fillna(0)
                
                # 归一化子分数到[0,1]范围
                max_scores = {'Q1': 5, 'Q2': 5, 'Q3': 3, 'Q4': 5, 'Q5': 3}
                for task_id, max_score in max_scores.items():
                    df[f'{task_id}_subscore_norm'] = df[f'{task_id}_subscore'] / max_score
                
                # 过滤掉无效行
                df = df[df['subject_id'].notna()]  # 移除NaN
                df = df[~df['subject_id'].isin(['平均', '标准差', 'nan', ''])]  # 移除统计行
                df = df[df['subject_id'].str.len() > 2]  # 移除太短的ID
                
                # 只保留前20行实际数据 (跳过可能的统计行)
                df = df.head(20)
                
                all_mmse_data.append(df)
                
            except Exception as e:
                logger.error(f"加载MMSE文件失败 {filename}: {str(e)}")
                continue
        
        if not all_mmse_data:
            raise FileNotFoundError("未找到任何MMSE数据文件")
        
        # 合并所有组的数据
        combined_mmse = pd.concat(all_mmse_data, ignore_index=True)
        logger.info(f"成功加载MMSE数据: {len(combined_mmse)} 条记录")
        
        return combined_mmse
    
    def _merge_with_mmse(self, subject_data: pd.DataFrame, mmse_data: pd.DataFrame, task_id: str) -> pd.DataFrame:
        """
        将受试者特征数据与MMSE分数合并
        
        Args:
            subject_data: 受试者特征数据
            mmse_data: MMSE分数数据
            task_id: 任务ID (Q1-Q5)
            
        Returns:
            pd.DataFrame: 合并后的数据
        """
        # 创建副本避免修改原数据
        subject_data = subject_data.copy()
        mmse_data = mmse_data.copy()
        
        # 标准化受试者ID格式
        def normalize_subject_id(subject_id):
            """
            标准化受试者ID格式
            处理多种情况：
            1. 移除任务后缀: 'm8q' → 'm8'
            2. 补零对齐: 'm8' → 'm08'
            3. AD组特殊映射: 'ad3-ad22' → 'ad01-ad20'
            """
            subject_id = str(subject_id).lower()
            
            # 先移除任务后缀
            core_id = subject_id
            for suffix in ['q1', 'q2', 'q3', 'q4', 'q5', 'q']:
                if core_id.endswith(suffix):
                    core_id = core_id[:-len(suffix)]
                    break
            
            # 解析ID格式
            import re
            match = re.match(r'^([a-z]+)(\d+)$', core_id)
            if match:
                prefix, number = match.groups()
                number_int = int(number)
                
                # AD组特殊映射: ad3-ad22 映射到 ad01-ad20
                if prefix == 'ad' and 3 <= number_int <= 22:
                    mapped_number = number_int - 2  # ad3→ad01, ad4→ad02, ..., ad22→ad20
                    return f"ad{mapped_number:02d}"
                else:
                    # 其他组正常补零对齐
                    return f"{prefix}{number_int:02d}"
            
            return core_id
        
        # 为模块7数据创建特殊的映射函数
        def normalize_module7_id(subject_id):
            """模块7专用的ID标准化，包含AD组映射"""
            return normalize_subject_id(subject_id)
        
        def normalize_mmse_id(subject_id):
            """MMSE专用的ID标准化，不包含AD组映射"""
            subject_id = str(subject_id).lower()
            
            # 先移除任务后缀
            core_id = subject_id
            for suffix in ['q1', 'q2', 'q3', 'q4', 'q5', 'q']:
                if core_id.endswith(suffix):
                    core_id = core_id[:-len(suffix)]
                    break
            
            # 解析ID格式 - MMSE侧不做AD组映射，只补零
            import re
            match = re.match(r'^([a-z]+)(\d+)$', core_id)
            if match:
                prefix, number = match.groups()
                number_int = int(number)
                return f"{prefix}{number_int:02d}"
            
            return core_id
        
        # 分别标准化两个数据集的subject_id
        subject_data['subject_id_norm'] = subject_data['subject_id'].apply(normalize_module7_id)
        mmse_data['subject_id_norm'] = mmse_data['subject_id'].apply(normalize_mmse_id)
        
        # 选择需要的MMSE列
        mmse_cols = ['subject_id_norm', 'group_type', f'{task_id}_subscore', f'{task_id}_subscore_norm']
        mmse_subset = mmse_data[mmse_cols].copy()
        
        # 基于标准化ID合并数据
        merged = pd.merge(
            subject_data, 
            mmse_subset, 
            on='subject_id_norm', 
            how='inner'
        )
        
        # 移除临时标准化列
        if 'subject_id_norm' in merged.columns:
            merged = merged.drop('subject_id_norm', axis=1)
        
        logger.debug(f"任务 {task_id}: 特征数据 {len(subject_data)} 条，MMSE数据 {len(mmse_subset)} 条，合并后 {len(merged)} 条")
        
        # 如果合并后数据为空，提供详细调试信息
        if len(merged) == 0:
            logger.warning(f"任务 {task_id} 合并结果为空")
            logger.debug(f"特征数据受试者ID示例: {subject_data['subject_id'].head(3).tolist()}")
            logger.debug(f"MMSE数据受试者ID示例: {mmse_data['subject_id'].head(3).tolist()}")
            logger.debug(f"标准化后特征ID示例: {subject_data['subject_id_norm'].head(3).tolist()}")
            logger.debug(f"标准化后MMSE ID示例: {mmse_subset['subject_id_norm'].head(3).tolist()}")
        else:
            # 记录匹配的详细信息，特别是ID范围不匹配的情况
            logger.debug(f"任务 {task_id} 成功匹配 {len(merged)} 个受试者")
            
            # 分析未匹配的ID
            subject_ids_norm = set(subject_data['subject_id_norm'])
            mmse_ids_norm = set(mmse_subset['subject_id_norm'])
            
            unmatched_subject = subject_ids_norm - mmse_ids_norm
            unmatched_mmse = mmse_ids_norm - subject_ids_norm
            
            if unmatched_subject:
                logger.debug(f"模块7中未匹配的ID: {sorted(list(unmatched_subject))[:5]}...")
            if unmatched_mmse:
                logger.debug(f"MMSE中未匹配的ID: {sorted(list(unmatched_mmse))[:5]}...")
        
        return merged
    
    def save(self, datasets: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> Dict[str, Any]:
        """
        保存数据集和元数据
        
        Args:
            datasets: 按任务分类的数据集
            
        Returns:
            Dict: 保存操作的元数据
        """
        logger.info("开始保存数据集...")
        
        # 准备元数据
        meta = {
            "rqa_sig": self.rqa_sig,
            "generated_at": datetime.now().isoformat(),
            "feature_names": FEATURE_NAMES,
            "samples": {},
            "val_split": self.val_split,
            "random_state": self.random_state,
            "feature_statistics": {}
        }
        
        # 保存每个任务的数据
        for task_id, (X, y) in datasets.items():
            # 保存为npz格式
            task_file = self.output_dir / FILE_PATTERNS["module10_task"].format(task_id=task_id)
            np.savez_compressed(
                task_file,
                X=X,
                y=y,
                feature_names=FEATURE_NAMES,
                task_id=task_id
            )
            
            # 记录样本数
            meta["samples"][task_id] = len(X)
            
            # 计算特征统计
            meta["feature_statistics"][task_id] = {
                "mean": X.mean(axis=0).tolist(),
                "std": X.std(axis=0).tolist(),
                "min": X.min(axis=0).tolist(),
                "max": X.max(axis=0).tolist()
            }
            
            logger.info(f"保存任务 {task_id}: {task_file}")
        
        # 保存元数据
        meta_file = self.output_dir / FILE_PATTERNS["module10_meta"]
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        
        self.meta = meta
        
        logger.info(f"数据集保存完成: {self.output_dir}")
        logger.info(f"总样本数: {sum(meta['samples'].values())}")
        
        return meta
    
    def run_all(self) -> Dict[str, Any]:
        """
        执行完整的构建流程
        
        Returns:
            Dict: 构建结果的元数据
        """
        logger.info(f"开始执行完整构建流程: {self.rqa_sig}")
        
        try:
            # 1. 加载原始数据
            df = self.load_raw()
            
            # 2. 验证数据
            validation_report = self.validate(df)
            
            # 3. 转换为任务级别数据
            datasets = self.to_class_level(df)
            
            # 4. 保存数据集
            meta = self.save(datasets)
            
            # 5. 添加验证报告到元数据
            meta["validation_report"] = validation_report
            
            logger.info("构建流程执行完成")
            return meta
            
        except Exception as e:
            logger.error(f"构建流程失败: {str(e)}")
            raise


def main():
    """命令行入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="模块10-A特征数据构建器")
    parser.add_argument("--config", required=True, help="RQA配置签名 (如: m2_tau1_eps0.06_lmin2)")
    parser.add_argument("--val_split", type=float, default=0.2, help="验证集比例")
    parser.add_argument("--out_root", help="输出根目录")
    parser.add_argument("--random_state", type=int, default=42, help="随机种子")
    
    args = parser.parse_args()
    
    try:
        builder = FeatureBuilder(
            rqa_sig=args.config,
            val_split=args.val_split,
            out_root=args.out_root,
            random_state=args.random_state
        )
        
        meta = builder.run_all()
        
        print(f"\n✅ 构建成功!")
        print(f"RQA签名: {meta['rqa_sig']}")
        print(f"输出目录: {builder.output_dir}")
        print(f"样本分布: {meta['samples']}")
        
    except Exception as e:
        print(f"\n❌ 构建失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()