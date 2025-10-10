"""
Module05: RQA参数敏感性分析器

功能:
1. 计算参数敏感性评分 - 评估不同参数组合区分组别的能力
2. 生成3D参数空间可视化 - 使用Plotly交互式3D图表
3. 生成参数-特征热图
4. 生成组间对比图
5. 生成参数优选排序图

注意: 使用懒加载策略,重依赖库(scipy/plotly)只在函数调用时导入,避免启动时挂起
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ParameterSensitivityAnalyzer:
    """RQA参数敏感性分析器"""

    def __init__(self):
        """初始化分析器"""
        self.rqa_features = [
            'rr', 'det', 'lam', 'l_mean', 'l_max',
            'entropy', 'trend', 'combined_rr'
        ]
        logger.info("ParameterSensitivityAnalyzer initialized (lazy loading mode)")

    def compute_parameter_sensitivity_scores(self, results_by_params: List[Dict]) -> pd.DataFrame:
        """
        计算参数敏感性评分

        使用ANOVA F统计量评估每个参数组合对区分组别(control/MCI/AD)的敏感性

        Args:
            results_by_params: 参数组合结果列表
                [{
                    'params': {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2},
                    'enriched_features_path': '/path/to/enriched_features.csv'
                }, ...]

        Returns:
            敏感性评分DataFrame,包含:
                - param_signature: 参数签名 (e.g., 'm2_tau1_eps0.050_lmin2')
                - m, tau, eps, lmin: 参数值
                - feature: RQA特征名
                - f_statistic: F统计量 (组间差异/组内差异)
                - p_value: p值
                - effect_size: 效应量 (eta squared)
                - task_consistency: 任务一致性 (跨任务的稳定性)
                - overall_score: 综合评分
        """
        # 懒加载scipy - 只在需要时导入
        from scipy import stats

        logger.info(f"Computing sensitivity scores for {len(results_by_params)} parameter combinations")

        sensitivity_scores = []

        for param_result in results_by_params:
            params = param_result['params']
            enriched_path = Path(param_result['enriched_features_path'])

            if not enriched_path.exists():
                logger.warning(f"Enriched features file not found: {enriched_path}")
                continue

            # 读取enriched features
            df = pd.read_csv(enriched_path)

            # 标准化列名为小写（处理大小写不一致问题）
            df.columns = df.columns.str.lower()

            # 标准化group列的值为小写
            if 'group' in df.columns:
                df['group'] = df['group'].str.lower()

            # 参数签名
            param_sig = f"m{params['m']}_tau{params['tau']}_eps{params['eps']:.3f}_lmin{params['lmin']}"

            # 动态识别RQA特征列（匹配实际列名格式）
            rqa_feature_cols = self._identify_rqa_features(df)
            if len(rqa_feature_cols) == 0:
                logger.warning(f"No RQA features found in {enriched_path}")
                continue

            logger.debug(f"Identified {len(rqa_feature_cols)} RQA features for {param_sig}")

            # 对每个RQA特征计算敏感性
            for feature in rqa_feature_cols:
                if feature not in df.columns:
                    continue

                # 跨任务(q1-q5)计算F统计量
                task_f_stats = []
                task_p_values = []
                task_effect_sizes = []

                for task in ['q1', 'q2', 'q3', 'q4', 'q5']:
                    task_df = df[df['task_id'] == task]

                    if len(task_df) < 3:  # 至少需要3个样本
                        continue

                    # 按组别分组
                    groups = []
                    for group in ['control', 'mci', 'ad']:
                        group_data = task_df[task_df['group'] == group][feature].dropna()
                        if len(group_data) > 0:
                            groups.append(group_data)

                    if len(groups) >= 2:
                        # ANOVA F-test
                        f_stat, p_val = stats.f_oneway(*groups)

                        if not np.isnan(f_stat):
                            task_f_stats.append(f_stat)
                            task_p_values.append(p_val)

                            # 计算效应量 (eta squared)
                            # eta_squared = SS_between / SS_total
                            all_data = pd.concat(groups)
                            grand_mean = all_data.mean()
                            ss_total = ((all_data - grand_mean) ** 2).sum()
                            ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
                            eta_squared = ss_between / ss_total if ss_total > 0 else 0
                            task_effect_sizes.append(eta_squared)

                if len(task_f_stats) == 0:
                    continue

                # 聚合指标
                f_stat_mean = np.mean(task_f_stats)
                p_val_mean = np.mean(task_p_values)
                effect_size_mean = np.mean(task_effect_sizes)

                # 任务一致性: F统计量的变异系数(CV)的倒数
                # CV越小,一致性越高
                f_stat_std = np.std(task_f_stats)
                if f_stat_mean > 0:
                    cv = f_stat_std / f_stat_mean
                    task_consistency = 1 / (1 + cv)  # 归一化到[0, 1]
                else:
                    task_consistency = 0

                # 综合评分: 加权组合
                # 权重: F统计量(0.4) + 效应量(0.3) + 任务一致性(0.2) - p值惩罚(0.1)
                overall_score = (
                    0.4 * min(f_stat_mean / 100, 1.0) +  # 归一化F统计量
                    0.3 * effect_size_mean +
                    0.2 * task_consistency -
                    0.1 * p_val_mean
                )

                sensitivity_scores.append({
                    'param_signature': param_sig,
                    'm': params['m'],
                    'tau': params['tau'],
                    'eps': params['eps'],
                    'lmin': params['lmin'],
                    'feature': feature,
                    'f_statistic': f_stat_mean,
                    'p_value': p_val_mean,
                    'effect_size': effect_size_mean,
                    'task_consistency': task_consistency,
                    'overall_score': overall_score
                })

        sensitivity_df = pd.DataFrame(sensitivity_scores)
        logger.info(f"Computed {len(sensitivity_df)} sensitivity scores")

        return sensitivity_df

    def plot_3d_parameter_space(
        self,
        sensitivity_df: pd.DataFrame,
        feature: str,
        output_path: Path,
        x_param: str = 'm',
        y_param: str = 'tau',
        z_metric: str = 'f_statistic',
        color_param: str = 'eps'
    ):
        """
        生成3D参数空间图

        Args:
            sensitivity_df: 敏感性评分DataFrame
            feature: RQA特征名
            output_path: 输出HTML路径
            x_param: X轴参数
            y_param: Y轴参数
            z_metric: Z轴指标
            color_param: 颜色参数
        """
        # 懒加载plotly - 只在需要时导入
        import plotly.express as px

        # 筛选特定特征
        plot_df = sensitivity_df[sensitivity_df['feature'] == feature].copy()

        if len(plot_df) == 0:
            logger.warning(f"No data for feature: {feature}")
            return

        # 创建3D散点图
        fig = px.scatter_3d(
            plot_df,
            x=x_param,
            y=y_param,
            z=z_metric,
            color=color_param,
            hover_data=['param_signature', 'f_statistic', 'p_value', 'effect_size'],
            title=f'3D参数空间: {feature}',
            labels={
                x_param: x_param.upper(),
                y_param: y_param.upper(),
                z_metric: z_metric.replace('_', ' ').title(),
                color_param: color_param.upper()
            }
        )

        fig.update_traces(marker=dict(size=5))
        fig.write_html(str(output_path))
        logger.info(f"3D plot saved to: {output_path}")

    def plot_parameter_heatmap(
        self,
        sensitivity_df: pd.DataFrame,
        output_path: Path,
        metric: str = 'overall_score'
    ):
        """
        生成参数-特征敏感性热图

        Args:
            sensitivity_df: 敏感性评分DataFrame
            output_path: 输出HTML路径
            metric: 热图指标 ('overall_score', 'f_statistic', 'effect_size')
        """
        # 懒加载plotly
        import plotly.express as px

        # 创建透视表: 行=参数组合, 列=特征, 值=metric
        pivot_df = sensitivity_df.pivot_table(
            index='param_signature',
            columns='feature',
            values=metric,
            aggfunc='mean'
        )

        # 按metric总分排序
        pivot_df['_total'] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values('_total', ascending=False).drop('_total', axis=1)

        # 创建热图
        fig = px.imshow(
            pivot_df,
            labels=dict(x="RQA特征", y="参数组合", color=metric),
            title=f'参数-特征敏感性热图 ({metric})',
            aspect="auto",
            color_continuous_scale='RdYlGn'
        )

        fig.update_xaxes(side="bottom")
        fig.write_html(str(output_path))
        logger.info(f"Heatmap saved to: {output_path}")

    def plot_group_comparison_by_params(
        self,
        results_by_params: List[Dict],
        feature: str,
        task: str,
        output_path: Path
    ):
        """
        生成不同参数下的组间对比折线图

        Args:
            results_by_params: 参数组合结果列表
            feature: RQA特征名
            task: 任务ID (e.g., 'q1')
            output_path: 输出HTML路径
        """
        # 懒加载plotly
        import plotly.graph_objects as go

        fig = go.Figure()

        for param_result in results_by_params:
            params = param_result['params']
            enriched_path = Path(param_result['enriched_features_path'])

            if not enriched_path.exists():
                continue

            df = pd.read_csv(enriched_path)
            task_df = df[df['task_id'] == task]

            if len(task_df) == 0:
                continue

            # 计算各组均值
            group_means = []
            groups = ['control', 'mci', 'ad']

            for group in groups:
                group_data = task_df[task_df['group'] == group][feature]
                group_means.append(group_data.mean())

            param_sig = f"m{params['m']}_tau{params['tau']}_eps{params['eps']:.3f}_lmin{params['lmin']}"

            fig.add_trace(go.Scatter(
                x=groups,
                y=group_means,
                mode='lines+markers',
                name=param_sig
            ))

        fig.update_layout(
            title=f'组间对比: {feature} ({task})',
            xaxis_title='组别',
            yaxis_title=f'{feature} 均值',
            hovermode='x unified'
        )

        fig.write_html(str(output_path))
        logger.info(f"Group comparison plot saved to: {output_path}")

    def plot_parameter_ranking(
        self,
        sensitivity_df: pd.DataFrame,
        output_path: Path,
        top_n: int = 20,
        sort_by: str = 'overall_score'
    ):
        """
        生成参数优选排序图

        Args:
            sensitivity_df: 敏感性评分DataFrame
            output_path: 输出HTML路径
            top_n: 显示前N个参数组合
            sort_by: 排序依据 ('overall_score', 'f_statistic', 'effect_size')
        """
        # 懒加载plotly
        import plotly.express as px

        # 按参数组合聚合
        param_scores = sensitivity_df.groupby('param_signature').agg({
            sort_by: 'mean',
            'f_statistic': 'mean',
            'effect_size': 'mean',
            'task_consistency': 'mean'
        }).reset_index()

        # 排序并取Top N
        param_scores = param_scores.sort_values(sort_by, ascending=False).head(top_n)

        # 创建条形图
        fig = px.bar(
            param_scores,
            x=sort_by,
            y='param_signature',
            orientation='h',
            title=f'参数优选排序 (Top {top_n}, 按{sort_by})',
            labels={sort_by: sort_by.replace('_', ' ').title(), 'param_signature': '参数组合'},
            hover_data=['f_statistic', 'effect_size', 'task_consistency']
        )

        fig.update_yaxes(categoryorder='total ascending')
        fig.write_html(str(output_path))
        logger.info(f"Ranking plot saved to: {output_path}")

    def plot_task_sensitivity_comparison(
        self,
        results_by_params: List[Dict],
        feature: str,
        param_signature: str,
        output_path: Path
    ):
        """
        生成任务敏感性对比图

        展示同一参数组合在不同任务(q1-q5)下的敏感性

        Args:
            results_by_params: 参数组合结果列表
            feature: RQA特征名
            param_signature: 参数签名
            output_path: 输出HTML路径
        """
        # 懒加载plotly和scipy
        import plotly.graph_objects as go
        from scipy import stats

        # 找到对应的参数组合
        target_result = None
        for param_result in results_by_params:
            params = param_result['params']
            sig = f"m{params['m']}_tau{params['tau']}_eps{params['eps']:.3f}_lmin{params['lmin']}"
            if sig == param_signature:
                target_result = param_result
                break

        if not target_result:
            logger.warning(f"Parameter combination not found: {param_signature}")
            return

        enriched_path = Path(target_result['enriched_features_path'])
        if not enriched_path.exists():
            logger.warning(f"Enriched features file not found: {enriched_path}")
            return

        df = pd.read_csv(enriched_path)

        # 计算各任务的F统计量
        tasks = ['q1', 'q2', 'q3', 'q4', 'q5']
        f_statistics = []
        p_values = []

        for task in tasks:
            task_df = df[df['task_id'] == task]

            groups = []
            for group in ['control', 'mci', 'ad']:
                group_data = task_df[task_df['group'] == group][feature].dropna()
                if len(group_data) > 0:
                    groups.append(group_data)

            if len(groups) >= 2:
                f_stat, p_val = stats.f_oneway(*groups)
                f_statistics.append(f_stat if not np.isnan(f_stat) else 0)
                p_values.append(p_val if not np.isnan(p_val) else 1)
            else:
                f_statistics.append(0)
                p_values.append(1)

        # 创建双Y轴图
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=tasks,
            y=f_statistics,
            name='F统计量',
            yaxis='y',
            marker_color='lightblue'
        ))

        fig.add_trace(go.Scatter(
            x=tasks,
            y=p_values,
            name='P值',
            yaxis='y2',
            mode='lines+markers',
            marker_color='red'
        ))

        fig.update_layout(
            title=f'任务敏感性对比: {param_signature} - {feature}',
            xaxis=dict(title='任务'),
            yaxis=dict(title='F统计量', side='left'),
            yaxis2=dict(title='P值', side='right', overlaying='y'),
            hovermode='x unified'
        )

        fig.write_html(str(output_path))
        logger.info(f"Task sensitivity plot saved to: {output_path}")

    def _identify_rqa_features(self, df: pd.DataFrame) -> List[str]:
        """
        动态识别RQA特征列

        匹配模式：
        - rr-1d-x, det-1d-x, ent-1d-x, lam-1d-x
        - rr-1d-y, det-1d-y, ent-1d-y, lam-1d-y
        - rr-2d, det-2d, ent-2d, lam-2d
        - rqa_* (如 rqa_complexity_1d, rqa_complexity_2d)
        - x_*, y_*, combined_* (如 x_rr, y_det, combined_ent)
        - *_symmetry, *_diff (派生特征，如 rr_symmetry, det_xy_diff)

        Args:
            df: DataFrame with column names already lowercased

        Returns:
            List of RQA feature column names
        """
        rqa_features = []

        # RQA特征前缀模式
        rqa_prefixes = ['rr-', 'det-', 'ent-', 'lam-', 'x_', 'y_', 'combined_', 'rqa_']

        # RQA特征关键词
        rqa_keywords = ['symmetry', 'diff', 'complexity']

        for col in df.columns:
            col_lower = col.lower()

            # 匹配前缀模式
            if any(col_lower.startswith(prefix) for prefix in rqa_prefixes):
                rqa_features.append(col)
                continue

            # 匹配关键词模式
            if any(keyword in col_lower for keyword in rqa_keywords):
                rqa_features.append(col)
                continue

        return rqa_features
