"""
Module05 可视化分析器
Visualization Analyzer for RQA Analysis

功能:
1. 计算按组别的描述性统计
2. 计算特征相关性矩阵
3. 绘制相关性热力图
4. 绘制显著性特征柱状图
5. 绘制复杂度小提琴图
6. 绘制分组箱线图
7. 绘制分组密度图

注意: 使用懒加载策略,重依赖库(matplotlib/seaborn)只在函数调用时导入
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class VisualizationAnalyzer:
    """RQA 可视化分析器"""

    def __init__(self):
        """初始化分析器"""
        logger.info("VisualizationAnalyzer initialized (lazy loading mode)")

    def compute_descriptive_stats(
        self,
        df: pd.DataFrame,
        group_col: str = 'group'
    ) -> pd.DataFrame:
        """
        计算按组别的描述性统计

        Args:
            df: 增强特征数据 (enriched_features.csv)
            group_col: 分组列名，默认 'group'

        Returns:
            描述性统计 DataFrame
            Columns: feature, group, mean, std, median, q1, q3, min, max, count
        """
        # 识别 RQA 特征列
        rqa_features = self._identify_rqa_features(df)

        if not rqa_features:
            logger.warning("No RQA features found in DataFrame")
            return pd.DataFrame()

        results = []
        groups = df[group_col].unique()

        for feature in rqa_features:
            for group in groups:
                group_data = df[df[group_col] == group][feature].dropna()

                if len(group_data) == 0:
                    continue

                results.append({
                    'feature': feature,
                    'group': group,
                    'mean': group_data.mean(),
                    'std': group_data.std(),
                    'median': group_data.median(),
                    'q1': group_data.quantile(0.25),
                    'q3': group_data.quantile(0.75),
                    'min': group_data.min(),
                    'max': group_data.max(),
                    'count': len(group_data)
                })

        logger.info(f"Computed descriptive stats for {len(rqa_features)} features across {len(groups)} groups")
        return pd.DataFrame(results)

    def compute_correlation_matrix(
        self,
        df: pd.DataFrame,
        method: str = 'pearson'
    ) -> pd.DataFrame:
        """
        计算 RQA 特征相关性矩阵

        Args:
            df: 增强特征数据
            method: 'pearson' 或 'spearman'

        Returns:
            相关性矩阵 DataFrame (对称矩阵)
        """
        rqa_features = self._identify_rqa_features(df)

        if not rqa_features:
            logger.warning("No RQA features found for correlation analysis")
            return pd.DataFrame()

        feature_data = df[rqa_features]

        if method == 'pearson':
            corr_matrix = feature_data.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = feature_data.corr(method='spearman')
        else:
            raise ValueError(f"不支持的相关性方法: {method}")

        logger.info(f"Computed {method} correlation matrix for {len(rqa_features)} features")
        return corr_matrix

    def plot_correlation_heatmap(
        self,
        corr_matrix: pd.DataFrame,
        output_path: Path,
        figsize: Tuple[int, int] = (16, 14)
    ) -> None:
        """
        绘制相关性热力图

        Args:
            corr_matrix: 相关性矩阵
            output_path: 输出文件路径
            figsize: 图表尺寸
        """
        # 懒加载绘图库
        import matplotlib.pyplot as plt
        import seaborn as sns

        # 设置绘图风格
        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.unicode_minus'] = False

        fig, ax = plt.subplots(figsize=figsize)

        # 绘制热力图
        sns.heatmap(
            corr_matrix,
            annot=True,        # 显示数值
            fmt='.2f',         # 保留2位小数
            cmap='RdBu_r',     # 红蓝渐变（红=正相关，蓝=负相关）
            center=0,          # 中心为0
            vmin=-1,
            vmax=1,
            square=True,       # 正方形单元格
            linewidths=0.5,
            cbar_kws={"shrink": 0.8, "label": "Correlation Coefficient"},
            ax=ax
        )

        ax.set_title('RQA Feature Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Correlation heatmap saved: {output_path}")

    def plot_significant_features_barplot(
        self,
        comparison_df: pd.DataFrame,
        output_path: Path,
        top_n: int = 20
    ) -> None:
        """
        绘制显著性特征柱状图

        Args:
            comparison_df: 组间比较结果 (group_comparison.csv)
            output_path: 输出文件路径
            top_n: 显示前N个特征
        """
        # 懒加载绘图库
        import matplotlib.pyplot as plt
        import seaborn as sns
        from matplotlib.patches import Patch

        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['font.size'] = 10

        # 按 F 统计量排序，取前 top_n
        top_features = comparison_df.nlargest(top_n, 'f_statistic')

        # 颜色编码
        def get_color(p_value):
            if p_value < 0.001:
                return '#cf1322'  # 红色 ***
            elif p_value < 0.01:
                return '#fa8c16'  # 橙色 **
            elif p_value < 0.05:
                return '#faad14'  # 黄色 *
            else:
                return '#d9d9d9'  # 灰色 ns

        colors = [get_color(p) for p in top_features['p_value']]

        fig, ax = plt.subplots(figsize=(12, 8))

        bars = ax.barh(
            range(len(top_features)),
            top_features['f_statistic'],
            color=colors
        )

        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features['feature'].str.upper(), fontsize=9)
        ax.set_xlabel('F-statistic', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {top_n} Significant RQA Features (ANOVA)',
                     fontsize=14, fontweight='bold')

        # 添加图例
        legend_elements = [
            Patch(facecolor='#cf1322', label='p < 0.001 ***'),
            Patch(facecolor='#fa8c16', label='p < 0.01 **'),
            Patch(facecolor='#faad14', label='p < 0.05 *'),
            Patch(facecolor='#d9d9d9', label='p ≥ 0.05 (ns)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Significance barplot saved: {output_path}")

    def plot_complexity_violin(
        self,
        df: pd.DataFrame,
        output_path: Path,
        group_col: str = 'group'
    ) -> None:
        """
        绘制复杂度小提琴图

        Args:
            df: 增强特征数据
            output_path: 输出文件路径
            group_col: 分组列名
        """
        # 懒加载绘图库
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['font.size'] = 10

        complexity_features = ['rqa_complexity_1d', 'rqa_complexity_2d']

        # 检查特征是否存在
        existing_features = [f for f in complexity_features if f in df.columns]
        if not existing_features:
            raise ValueError("数据中不存在复杂度特征")

        fig, axes = plt.subplots(1, len(existing_features), figsize=(8 * len(existing_features), 6))
        if len(existing_features) == 1:
            axes = [axes]

        for idx, feature in enumerate(existing_features):
            ax = axes[idx]

            # 绘制小提琴图
            sns.violinplot(
                data=df,
                x=group_col,
                y=feature,
                palette='Set2',
                inner='box',  # 显示箱线图
                ax=ax
            )

            ax.set_title(f'{feature.replace("_", " ").title()}',
                        fontsize=12, fontweight='bold')
            ax.set_xlabel('Group', fontsize=10)
            ax.set_ylabel('Complexity Score', fontsize=10)

        plt.suptitle('Complexity Metrics Distribution by Group',
                     fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Complexity violin plot saved: {output_path}")

    def plot_grouped_boxplots(
        self,
        df: pd.DataFrame,
        features: List[str],
        output_path: Path,
        group_col: str = 'group'
    ) -> None:
        """
        绘制分组箱线图（增强版）

        Args:
            df: 增强特征数据
            features: 要可视化的特征列表
            output_path: 输出文件路径
            group_col: 分组列名
        """
        # 懒加载绘图库
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['font.size'] = 10

        n_features = len(features)
        ncols = 3
        nrows = (n_features + ncols - 1) // ncols

        fig, axes = plt.subplots(nrows, ncols, figsize=(15, 5 * nrows))
        axes = axes.flatten() if n_features > 1 else [axes]

        for idx, feature in enumerate(features):
            ax = axes[idx]

            # 绘制箱线图
            sns.boxplot(
                data=df,
                x=group_col,
                y=feature,
                palette='pastel',
                showfliers=True,  # 显示离群点
                ax=ax
            )

            # 叠加散点图（抖动）
            sns.stripplot(
                data=df,
                x=group_col,
                y=feature,
                color='black',
                alpha=0.3,
                size=3,
                ax=ax
            )

            ax.set_title(f'{feature.upper()}', fontsize=11, fontweight='bold')
            ax.set_xlabel('Group', fontsize=9)
            ax.set_ylabel(feature, fontsize=9)

        # 隐藏多余子图
        for idx in range(n_features, len(axes)):
            axes[idx].axis('off')

        plt.suptitle('RQA Features by Group (Boxplots)',
                     fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Grouped boxplots saved: {output_path}")

    def plot_density_plot(
        self,
        df: pd.DataFrame,
        feature: str,
        output_path: Path,
        group_col: str = 'group'
    ) -> None:
        """
        绘制分组密度图

        Args:
            df: 增强特征数据
            feature: 特征名
            output_path: 输出文件路径
            group_col: 分组列名
        """
        # 懒加载绘图库
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['font.size'] = 10

        fig, ax = plt.subplots(figsize=(10, 6))

        groups = df[group_col].unique()
        colors = {'control': '#1f77b4', 'mci': '#ff7f0e', 'ad': '#d62728'}

        for group in groups:
            group_data = df[df[group_col] == group][feature].dropna()

            if len(group_data) > 0:
                sns.kdeplot(
                    data=group_data,
                    ax=ax,
                    label=group.upper(),
                    color=colors.get(group, '#333'),
                    linewidth=2,
                    fill=True,
                    alpha=0.3
                )

        ax.set_xlabel(feature.upper(), fontsize=12, fontweight='bold')
        ax.set_ylabel('Density', fontsize=12, fontweight='bold')
        ax.set_title(f'Kernel Density Estimation: {feature.upper()}',
                     fontsize=14, fontweight='bold')
        ax.legend(title='Group', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Density plot saved: {output_path}")

    def _identify_rqa_features(self, df: pd.DataFrame) -> List[str]:
        """
        识别 RQA 特征列

        Args:
            df: DataFrame

        Returns:
            RQA 特征列名列表
        """
        rqa_prefixes = ['rr-', 'det-', 'ent-', 'lam-', 'x_', 'y_', 'combined_', 'rqa_']
        rqa_keywords = ['complexity', 'symmetry', 'diff']

        features = []
        for col in df.columns:
            col_lower = col.lower()
            if any(col_lower.startswith(prefix) for prefix in rqa_prefixes):
                features.append(col)
            elif any(keyword in col_lower for keyword in rqa_keywords):
                features.append(col)

        return features
