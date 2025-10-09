"""
任务分层分析器 - 按任务(q1-q5)进行独立统计分析

功能:
1. 对指定任务的数据进行ANOVA分析
2. 生成任务特异性的统计报告
3. 支持任务间对比分析

作者: Module05 Advanced Analysis
日期: 2025-10-09
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class TaskAnalyzer:
    """任务分层分析器"""

    def __init__(self, results_dir: str):
        """
        初始化任务分析器

        Args:
            results_dir: RQA结果目录路径
        """
        self.results_dir = Path(results_dir)

    def analyze_single_task(
        self,
        params: Dict,
        task_id: str,
        groups: List[str] = ['control', 'mci', 'ad']
    ) -> Dict:
        """
        分析单个任务的RQA特征

        Args:
            params: RQA参数字典 {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}
            task_id: 任务ID (q1-q5)
            groups: 组别列表

        Returns:
            统计分析结果
        """
        logger.info(f"开始分析任务 {task_id}, 参数: {params}")

        # 1. 读取enriched_features.csv
        param_dir = self._get_param_dir(params)
        features_file = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'

        if not features_file.exists():
            raise FileNotFoundError(f"特征文件不存在: {features_file}")

        df = pd.read_csv(features_file)

        # 标准化列名（处理大小写问题）
        df.columns = df.columns.str.lower()

        # 标准化group列的值（处理大小写问题: Control -> control）
        if 'group' in df.columns:
            df['group'] = df['group'].str.lower()

        # 2. 筛选指定任务的数据
        task_df = df[df['task_id'] == task_id].copy()

        if len(task_df) == 0:
            raise ValueError(f"任务 {task_id} 没有数据")

        logger.info(f"任务 {task_id} 数据量: {len(task_df)} 条")

        # 3. 执行统计分析
        statistics = self._compute_statistics(task_df, groups)

        return {
            'task_id': task_id,
            'params': params,
            'sample_size': len(task_df),
            'statistics': statistics
        }

    def _get_param_dir(self, params: Dict) -> Path:
        """
        获取参数对应的目录路径

        Args:
            params: 参数字典

        Returns:
            目录路径
        """
        dirname = f"m{params['m']}_tau{params['tau']}_eps{params['eps']}_lmin{params['lmin']}"
        return self.results_dir / dirname

    def _compute_statistics(self, df: pd.DataFrame, groups: List[str]) -> List[Dict]:
        """
        计算统计指标

        Args:
            df: 数据DataFrame
            groups: 组别列表

        Returns:
            统计结果列表
        """
        # 识别RQA特征列（列名已小写化）
        rqa_features = [col for col in df.columns if any(
            col.startswith(prefix) or 'rqa_' in col
            for prefix in ['rr-', 'det-', 'ent-']
        )]

        logger.info(f"识别到 {len(rqa_features)} 个RQA特征")

        statistics = []

        for feature in rqa_features:
            stat_row = {'feature': feature}

            # 计算各组的描述性统计
            for group in groups:
                group_data = df[df['group'] == group][feature].dropna()

                stat_row[group] = {
                    'mean': float(group_data.mean()) if len(group_data) > 0 else None,
                    'std': float(group_data.std()) if len(group_data) > 0 else None,
                    'median': float(group_data.median()) if len(group_data) > 0 else None,
                    'count': len(group_data)
                }

            # 执行ANOVA检验
            group_samples = [
                df[df['group'] == group][feature].dropna().values
                for group in groups
            ]

            # 过滤空组
            group_samples = [g for g in group_samples if len(g) > 0]

            if len(group_samples) >= 2:
                try:
                    f_stat, p_value = stats.f_oneway(*group_samples)
                    stat_row['f_stat'] = float(f_stat)
                    stat_row['p_value'] = float(p_value)
                except Exception as e:
                    logger.warning(f"ANOVA失败 (特征={feature}): {e}")
                    stat_row['f_stat'] = None
                    stat_row['p_value'] = None
            else:
                stat_row['f_stat'] = None
                stat_row['p_value'] = None

            statistics.append(stat_row)

        return statistics

    def compare_tasks(
        self,
        params: Dict,
        tasks: List[str] = ['q1', 'q2', 'q3', 'q4', 'q5']
    ) -> Dict:
        """
        对比多个任务的RQA特征

        Args:
            params: RQA参数字典
            tasks: 任务列表

        Returns:
            对比结果
        """
        logger.info(f"开始对比任务: {tasks}, 参数: {params}")

        # 1. 读取enriched_features.csv
        param_dir = self._get_param_dir(params)
        features_file = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'

        if not features_file.exists():
            raise FileNotFoundError(f"特征文件不存在: {features_file}")

        df = pd.read_csv(features_file)

        # 标准化列名（处理大小写问题）
        df.columns = df.columns.str.lower()

        # 标准化group列的值（处理大小写问题: Control -> control）
        if 'group' in df.columns:
            df['group'] = df['group'].str.lower()

        # 2. 筛选指定任务
        task_df = df[df['task_id'].isin(tasks)].copy()

        if len(task_df) == 0:
            raise ValueError(f"没有找到任务数据: {tasks}")

        # 3. 识别RQA特征（匹配实际列名格式: RR-1D-x, DET-1D-x, rqa_*等）
        rqa_features = [col for col in df.columns if any([
            col.startswith(prefix) for prefix in ['x_', 'y_', 'combined_', 'rr-', 'det-', 'ent-', 'rqa_']
        ])]

        # 4. 对每个特征进行任务间比较
        comparison_results = []

        for feature in rqa_features:
            feature_comparison = {
                'feature': feature,
                'task_means': {}
            }

            # 计算各任务的均值
            for task in tasks:
                task_data = task_df[task_df['task_id'] == task][feature].dropna()
                feature_comparison['task_means'][task] = {
                    'mean': float(task_data.mean()) if len(task_data) > 0 else None,
                    'std': float(task_data.std()) if len(task_data) > 0 else None,
                    'count': len(task_data)
                }

            # 执行任务间ANOVA
            task_samples = [
                task_df[task_df['task_id'] == task][feature].dropna().values
                for task in tasks
            ]
            task_samples = [s for s in task_samples if len(s) > 0]

            if len(task_samples) >= 2:
                try:
                    f_stat, p_value = stats.f_oneway(*task_samples)
                    feature_comparison['f_stat'] = float(f_stat)
                    feature_comparison['p_value'] = float(p_value)
                    feature_comparison['significant'] = bool(p_value < 0.05)
                except Exception as e:
                    logger.warning(f"任务间ANOVA失败 (特征={feature}): {e}")
                    feature_comparison['f_stat'] = None
                    feature_comparison['p_value'] = None
                    feature_comparison['significant'] = False
            else:
                feature_comparison['f_stat'] = None
                feature_comparison['p_value'] = None
                feature_comparison['significant'] = False

            comparison_results.append(feature_comparison)

        # 5. 生成摘要
        significant_features = [
            r['feature'] for r in comparison_results
            if r.get('significant', False)
        ]

        summary = {
            'params': params,
            'tasks': tasks,
            'total_features': len(rqa_features),
            'significant_features': significant_features,
            'significant_count': len(significant_features),
            'comparison_details': comparison_results
        }

        logger.info(f"任务对比完成: {len(significant_features)} 个特征显著")

        return summary

    def get_best_task_for_classification(self, params: Dict) -> Dict:
        """
        找到最适合分类的任务

        Args:
            params: RQA参数字典

        Returns:
            最优任务信息
        """
        tasks = ['q1', 'q2', 'q3', 'q4', 'q5']
        task_scores = []

        for task in tasks:
            try:
                result = self.analyze_single_task(params, task)

                # 计算平均F统计量
                f_stats = [
                    s['f_stat'] for s in result['statistics']
                    if s['f_stat'] is not None
                ]

                avg_f = np.mean(f_stats) if f_stats else 0.0

                # 计算显著特征数
                sig_count = sum(
                    1 for s in result['statistics']
                    if s['p_value'] is not None and s['p_value'] < 0.05
                )

                task_scores.append({
                    'task_id': task,
                    'avg_f_stat': avg_f,
                    'significant_count': sig_count,
                    'score': avg_f * sig_count  # 综合得分
                })

            except Exception as e:
                logger.warning(f"分析任务 {task} 失败: {e}")
                continue

        # 排序
        task_scores.sort(key=lambda x: x['score'], reverse=True)

        return {
            'best_task': task_scores[0] if task_scores else None,
            'all_tasks': task_scores
        }


def main():
    """测试函数"""
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 结果目录
    results_dir = r"c:\Users\asino\Downloads\az - 副本 (11)\new_project\data\module05_rqa_results"

    if not os.path.exists(results_dir):
        logger.error(f"结果目录不存在: {results_dir}")
        return

    # 创建分析器
    analyzer = TaskAnalyzer(results_dir)

    # 测试参数
    test_params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}

    # 分析单个任务
    print("\n--- 分析任务q1 ---")
    try:
        result = analyzer.analyze_single_task(test_params, 'q1')
        print(f"样本数: {result['sample_size']}")
        print(f"特征数: {len(result['statistics'])}")

        # 打印前3个特征的统计
        for stat in result['statistics'][:3]:
            print(f"\n特征: {stat['feature']}")
            print(f"  Control: mean={stat['control']['mean']:.4f}, std={stat['control']['std']:.4f}")
            print(f"  MCI: mean={stat['mci']['mean']:.4f}, std={stat['mci']['std']:.4f}")
            print(f"  AD: mean={stat['ad']['mean']:.4f}, std={stat['ad']['std']:.4f}")
            print(f"  F统计量={stat['f_stat']:.2f}, p值={stat['p_value']:.4f}")

    except Exception as e:
        print(f"分析失败: {e}")

    # 对比所有任务
    print("\n\n--- 对比所有任务 ---")
    try:
        comparison = analyzer.compare_tasks(test_params)
        print(f"显著特征数: {comparison['significant_count']}")
        print(f"显著特征: {comparison['significant_features'][:5]}")  # 前5个

    except Exception as e:
        print(f"对比失败: {e}")

    # 找最优任务
    print("\n\n--- 找最优任务 ---")
    try:
        best = analyzer.get_best_task_for_classification(test_params)
        if best['best_task']:
            print(f"最优任务: {best['best_task']['task_id']}")
            print(f"  平均F统计量: {best['best_task']['avg_f_stat']:.2f}")
            print(f"  显著特征数: {best['best_task']['significant_count']}")

    except Exception as e:
        print(f"查找失败: {e}")


if __name__ == '__main__':
    main()
