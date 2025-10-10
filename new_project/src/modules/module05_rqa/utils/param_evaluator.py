"""
参数评估器 - 用于评估RQA参数组合的性能

功能:
1. 评估所有已计算的参数组合的分类性能
2. 计算平均F统计量、显著特征数等指标
3. 生成参数排名列表

作者: Module05 Advanced Analysis
日期: 2025-10-09
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class ParamEvaluator:
    """RQA参数性能评估器"""

    def __init__(self, results_dir: str):
        """
        初始化参数评估器

        Args:
            results_dir: RQA结果目录路径
        """
        self.results_dir = Path(results_dir)

    def evaluate_all_params(self, metric: str = 'f_stat_mean') -> List[Dict]:
        """
        评估所有参数组合的性能

        Args:
            metric: 评估指标 ('f_stat_mean', 'significant_count', 'f_stat_max')

        Returns:
            参数评估结果列表,按指定指标降序排列
        """
        logger.info(f"开始评估所有参数组合,评估指标: {metric}")

        results = []

        # 遍历所有参数组合目录
        for param_dir in self.results_dir.iterdir():
            if not param_dir.is_dir():
                continue

            # 解析参数组合
            try:
                params = self._parse_params_from_dirname(param_dir.name)
                if not params:
                    continue
            except Exception as e:
                logger.warning(f"解析参数失败: {param_dir.name}, 错误: {e}")
                continue

            # 读取group_comparison.csv
            comparison_file = param_dir / 'group_comparison.csv'
            if not comparison_file.exists():
                logger.debug(f"跳过(无comparison文件): {param_dir.name}")
                continue

            try:
                # 计算性能指标
                metrics = self._calculate_metrics(comparison_file)

                results.append({
                    'params': params,
                    'f_stat_mean': metrics['f_stat_mean'],
                    'f_stat_max': metrics['f_stat_max'],
                    'f_stat_min': metrics['f_stat_min'],
                    'significant_count': metrics['significant_count'],
                    'total_features': metrics['total_features'],
                    'significant_ratio': metrics['significant_ratio']
                })

                logger.debug(f"评估完成: {param_dir.name}, F均值={metrics['f_stat_mean']:.2f}")

            except Exception as e:
                logger.warning(f"评估失败: {param_dir.name}, 错误: {e}")
                continue

        # 按指定指标排序
        results.sort(key=lambda x: x.get(metric, 0), reverse=True)

        logger.info(f"参数评估完成,共评估 {len(results)} 个参数组合")

        return results

    def _parse_params_from_dirname(self, dirname: str) -> Optional[Dict]:
        """
        从目录名解析参数

        Args:
            dirname: 目录名,格式如 "m2_tau1_eps0.05_lmin2"

        Returns:
            参数字典
        """
        try:
            parts = dirname.split('_')
            params = {}

            for part in parts:
                if part.startswith('m'):
                    params['m'] = int(part[1:])
                elif part.startswith('tau'):
                    params['tau'] = int(part[3:])
                elif part.startswith('eps'):
                    params['eps'] = float(part[3:])
                elif part.startswith('lmin'):
                    params['lmin'] = int(part[4:])

            # 验证所有必需参数都存在
            if all(k in params for k in ['m', 'tau', 'eps', 'lmin']):
                return params
            else:
                return None

        except Exception as e:
            logger.warning(f"解析参数失败: {dirname}, 错误: {e}")
            return None

    def _calculate_metrics(self, comparison_file: Path) -> Dict:
        """
        计算参数组合的性能指标

        Args:
            comparison_file: group_comparison.csv文件路径

        Returns:
            性能指标字典
        """
        # 读取ANOVA结果
        df = pd.read_csv(comparison_file)

        # 提取F统计量和p值
        if 'F-statistic' in df.columns:
            f_stats = df['F-statistic'].dropna()
        elif 'f_statistic' in df.columns:
            f_stats = df['f_statistic'].dropna()
        else:
            raise ValueError("未找到F统计量列")

        if 'p-value' in df.columns:
            p_values = df['p-value'].dropna()
        elif 'p_value' in df.columns:
            p_values = df['p_value'].dropna()
        else:
            raise ValueError("未找到p值列")

        # 计算指标
        metrics = {
            'f_stat_mean': float(f_stats.mean()) if len(f_stats) > 0 else 0.0,
            'f_stat_max': float(f_stats.max()) if len(f_stats) > 0 else 0.0,
            'f_stat_min': float(f_stats.min()) if len(f_stats) > 0 else 0.0,
            'significant_count': int((p_values < 0.05).sum()),
            'total_features': len(p_values),
            'significant_ratio': float((p_values < 0.05).sum() / len(p_values)) if len(p_values) > 0 else 0.0
        }

        return metrics

    def get_top_params(self, n: int = 10, metric: str = 'f_stat_mean') -> List[Dict]:
        """
        获取Top N最优参数组合

        Args:
            n: 返回前N个参数
            metric: 评估指标

        Returns:
            Top N参数列表
        """
        all_results = self.evaluate_all_params(metric=metric)
        return all_results[:n]

    def compare_params(self, params_list: List[Dict]) -> pd.DataFrame:
        """
        对比多个参数组合的性能

        Args:
            params_list: 参数组合列表

        Returns:
            对比结果DataFrame
        """
        comparison_data = []

        for params in params_list:
            # 构造目录名
            dirname = f"m{params['m']}_tau{params['tau']}_eps{params['eps']}_lmin{params['lmin']}"
            param_dir = self.results_dir / dirname

            comparison_file = param_dir / 'group_comparison.csv'
            if not comparison_file.exists():
                logger.warning(f"参数组合无结果: {dirname}")
                continue

            try:
                metrics = self._calculate_metrics(comparison_file)
                comparison_data.append({
                    **params,
                    **metrics
                })
            except Exception as e:
                logger.warning(f"计算指标失败: {dirname}, 错误: {e}")
                continue

        return pd.DataFrame(comparison_data)

    def find_optimal_params_by_task(self, task_id: str) -> Optional[Dict]:
        """
        找到指定任务的最优参数组合

        注意: 当前实现使用全局数据,未来可扩展为任务特异性评估

        Args:
            task_id: 任务ID (q1-q5)

        Returns:
            最优参数字典
        """
        # TODO: 实现基于任务的参数优化
        # 目前返回全局最优参数
        top_params = self.get_top_params(n=1)
        return top_params[0] if top_params else None

    def generate_report(self, output_path: str = None) -> str:
        """
        生成参数评估报告

        Args:
            output_path: 报告保存路径(可选)

        Returns:
            报告文本
        """
        all_results = self.evaluate_all_params()

        report_lines = [
            "=" * 80,
            "RQA参数性能评估报告",
            "=" * 80,
            f"\n总评估参数数: {len(all_results)}",
            f"\n--- Top 10 参数组合 (按平均F统计量排序) ---\n"
        ]

        for idx, result in enumerate(all_results[:10], 1):
            params = result['params']
            report_lines.append(
                f"{idx}. m={params['m']}, tau={params['tau']}, eps={params['eps']}, lmin={params['lmin']}\n"
                f"   F均值={result['f_stat_mean']:.2f}, "
                f"显著特征数={result['significant_count']}, "
                f"显著率={result['significant_ratio']:.2%}\n"
            )

        report_text = "\n".join(report_lines)

        # 保存报告
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"报告已保存: {output_path}")

        return report_text


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

    # 创建评估器
    evaluator = ParamEvaluator(results_dir)

    # 评估所有参数
    print("\n正在评估所有参数组合...")
    results = evaluator.evaluate_all_params()

    # 生成报告
    print("\n生成评估报告...")
    report = evaluator.generate_report()
    print(report)

    # 获取Top 5参数
    print("\n--- Top 5 参数组合详情 ---")
    top_5 = evaluator.get_top_params(n=5)
    for idx, result in enumerate(top_5, 1):
        print(f"\n{idx}. {result}")


if __name__ == '__main__':
    main()
