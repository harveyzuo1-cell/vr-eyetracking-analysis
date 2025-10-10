# Module05 增强可视化分析设计文档
# Enhanced Visualization Analysis Design for Module05

**版本**: v1.0
**日期**: 2025-10-10
**状态**: 设计阶段 (Design Phase)

---

## 目录 (Table of Contents)

1. [背景与目标](#1-背景与目标)
2. [需求分析](#2-需求分析)
3. [技术架构设计](#3-技术架构设计)
4. [后端设计](#4-后端设计)
5. [前端设计](#5-前端设计)
6. [数据流设计](#6-数据流设计)
7. [实施计划](#7-实施计划)
8. [测试策略](#8-测试策略)

---

## 1. 背景与目标

### 1.1 背景 (Background)

当前 Module05 RQA 分析模块的 Step 3-5 实现较为简化，存在以下不足：

**现有功能:**
- ✅ Step 3: 计算派生特征（对称性、差异性、复杂度）
- ✅ Step 4: 组间 ANOVA 比较，输出 `group_comparison.csv`
- ✅ Step 5: 绘制显著特征的箱线图

**缺失功能:**
- ❌ 按组别的描述性统计（均值、标准差、中位数、四分位数）
- ❌ 特征相关性分析（Pearson/Spearman 相关性矩阵）
- ❌ 相关性热力图可视化
- ❌ 显著性特征柱状图
- ❌ 复杂度小提琴图
- ❌ 分组可视化（除了箱线图之外的其他图表类型）

### 1.2 设计目标 (Objectives)

1. **保持向后兼容**: 不修改现有 Step 1-5 的核心逻辑
2. **新增增强模块**: 创建独立的可视化分析模块，充分利用 Step 1-2 已有数据
3. **符合架构规范**: 遵循项目的 Backend Coding Standards 和分层架构
4. **科研可视化**: 提供专业的统计图表，符合科研论文要求
5. **前端集成**: 在"高级分析"面板中新增"可视化分析(新)"标签页

---

## 2. 需求分析

### 2.1 功能需求 (Functional Requirements)

#### FR1: 描述性统计分析
- **输入**: RQA 参数 signature
- **处理**: 读取 Step 3 的 `enriched_features.csv`，按 `group` 分组统计
- **输出**: `descriptive_stats_by_group.csv`
  - 每组的 mean, std, median, Q1, Q3, min, max
  - 每个 RQA 特征一行，包含所有统计量

#### FR2: 特征相关性分析
- **输入**: RQA 参数 signature, 相关性类型（pearson/spearman）
- **处理**: 计算所有 RQA 特征之间的相关性矩阵
- **输出**: `correlation_matrix.csv`
  - 对称矩阵，行列为特征名
  - 值为相关系数 (-1 到 1)

#### FR3: 相关性热力图
- **输入**: RQA 参数 signature, 相关性类型
- **处理**: 基于相关性矩阵生成热力图
- **输出**: `correlation_heatmap.png`
  - Seaborn heatmap
  - 颜色映射：蓝色(负相关) → 白色(0) → 红色(正相关)
  - 显示相关系数值

#### FR4: 显著性特征柱状图
- **输入**: RQA 参数 signature
- **处理**: 读取 Step 4 的 `group_comparison.csv`，按 F 统计量排序
- **输出**: `significant_features_barplot.png`
  - 横轴：特征名
  - 纵轴：F 统计量
  - 颜色编码：p < 0.001 (红), p < 0.01 (橙), p < 0.05 (黄), p >= 0.05 (灰)

#### FR5: 复杂度小提琴图
- **输入**: RQA 参数 signature
- **处理**: 提取复杂度特征（complexity_x, complexity_y, complexity_combined）
- **输出**: `complexity_violin.png`
  - 3 个子图（3 种复杂度指标）
  - 按 group 分组的小提琴图
  - 显示分布形状和统计量

#### FR6: 分组箱线图（增强版）
- **输入**: RQA 参数 signature, 特征列表
- **处理**: 为指定特征生成分组箱线图
- **输出**: `grouped_boxplots.png`
  - 支持自定义选择特征
  - 显示离群点
  - 包含统计检验结果标注

#### FR7: 分组密度图
- **输入**: RQA 参数 signature, 特征名
- **处理**: 绘制各组的核密度估计曲线
- **输出**: `density_plot_{feature}.png`
  - 叠加显示 control, mci, ad 三组的分布
  - 填充半透明颜色

### 2.2 非功能需求 (Non-Functional Requirements)

- **NFR1 性能**: 图表生成时间 < 5秒/图
- **NFR2 可扩展性**: 支持未来添加新的可视化类型
- **NFR3 可维护性**: 代码模块化，职责清晰
- **NFR4 用户体验**: 前端异步加载，显示进度条

---

## 3. 技术架构设计

### 3.1 架构原则

遵循项目现有的**分层架构**：

```
Frontend (React)
    ↓ HTTP Request
API Layer (api.py)
    ↓ Business Logic Call
Service Layer (visualization_service.py)
    ↓ Data Processing
Analyzer Layer (visualization_analyzer.py)
    ↓ File I/O
Data Files (CSV, PNG)
```

### 3.2 新增文件清单

#### 后端 (Backend)

```
src/modules/module05_rqa_analysis/
├── visualization_service.py      # 可视化服务层（新增）
├── visualization_analyzer.py     # 可视化分析器（新增）
├── api.py                        # 扩展API路由（修改）
└── tests/
    └── test_visualization.py     # 单元测试（新增）
```

#### 前端 (Frontend)

```
frontend/src/components/Module05/
├── AdvancedAnalysisPanel.jsx           # 新增标签页（修改）
└── EnhancedVisualizationPanel.jsx      # 可视化面板组件（新增）
```

### 3.3 技术栈

**后端:**
- Python 3.x
- pandas (数据处理)
- numpy (数值计算)
- scipy.stats (统计分析)
- matplotlib + seaborn (可视化)

**前端:**
- React 18
- Ant Design 5.x (UI组件)
- Recharts (交互式图表)
- axios (HTTP请求)

---

## 4. 后端设计

### 4.1 visualization_analyzer.py

**职责**: 核心算法实现（统计分析 + 图表生成）

```python
"""
Module05 可视化分析器
Visualization Analyzer for RQA Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class VisualizationAnalyzer:
    """RQA 可视化分析器"""

    def __init__(self):
        """初始化分析器"""
        # 设置绘图风格
        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.unicode_minus'] = False  # 支持负号显示

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
        feature_data = df[rqa_features]

        if method == 'pearson':
            corr_matrix = feature_data.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = feature_data.corr(method='spearman')
        else:
            raise ValueError(f"不支持的相关性方法: {method}")

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

        logger.info(f"相关性热力图已保存: {output_path}")

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
        from matplotlib.patches import Patch
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

        logger.info(f"显著性特征柱状图已保存: {output_path}")

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
        complexity_features = ['complexity_x', 'complexity_y', 'complexity_combined']

        # 检查特征是否存在
        existing_features = [f for f in complexity_features if f in df.columns]
        if not existing_features:
            raise ValueError("数据中不存在复杂度特征")

        fig, axes = plt.subplots(1, len(existing_features), figsize=(16, 5))
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

        logger.info(f"复杂度小提琴图已保存: {output_path}")

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

        logger.info(f"分组箱线图已保存: {output_path}")

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
        fig, ax = plt.subplots(figsize=(10, 6))

        groups = df[group_col].unique()
        colors = {'control': '#1f77b4', 'mci': '#ff7f0e', 'ad': '#d62728'}

        for group in groups:
            group_data = df[df[group_col] == group][feature].dropna()

            if len(group_data) > 0:
                group_data.plot.kde(
                    ax=ax,
                    label=group.upper(),
                    color=colors.get(group, '#333'),
                    linewidth=2,
                    alpha=0.7
                )
                ax.fill_between(
                    group_data.plot.kde().get_lines()[-1].get_data()[0],
                    group_data.plot.kde().get_lines()[-1].get_data()[1],
                    alpha=0.2,
                    color=colors.get(group, '#333')
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

        logger.info(f"密度图已保存: {output_path}")

    def _identify_rqa_features(self, df: pd.DataFrame) -> List[str]:
        """
        识别 RQA 特征列

        Args:
            df: DataFrame

        Returns:
            RQA 特征列名列表
        """
        rqa_prefixes = ['x_', 'y_', 'combined_', 'rr', 'det', 'ent', 'lam']
        rqa_keywords = ['rqa', 'complexity', 'symmetry', 'diff']

        features = []
        for col in df.columns:
            col_lower = col.lower()
            if any(col_lower.startswith(prefix) for prefix in rqa_prefixes):
                features.append(col)
            elif any(keyword in col_lower for keyword in rqa_keywords):
                features.append(col)

        return features
```

---

### 4.2 visualization_service.py

**职责**: 业务逻辑层（文件读取、流程控制、结果保存）

```python
"""
Module05 可视化服务层
Visualization Service for RQA Analysis
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json

from config.settings import Config
from src.utils.logger import setup_logger
from .visualization_analyzer import VisualizationAnalyzer
from .utils import generate_param_signature

logger = setup_logger(__name__)


class VisualizationService:
    """可视化服务"""

    def __init__(self):
        """初始化服务"""
        self.data_root = Path(Config.DATA_ROOT)
        self.results_dir = self.data_root / '05_rqa_analysis' / 'results'
        self.viz_dir = self.data_root / '05_rqa_analysis' / 'visualizations'
        self.viz_dir.mkdir(parents=True, exist_ok=True)

        self.analyzer = VisualizationAnalyzer()

        logger.info("可视化服务初始化完成")

    def get_step_directory(self, params: Dict, step_name: str) -> Path:
        """
        获取步骤目录

        Args:
            params: RQA 参数
            step_name: 步骤名称

        Returns:
            目录路径
        """
        signature = generate_param_signature(params)
        return self.results_dir / signature / step_name

    def get_visualization_directory(self, params: Dict) -> Path:
        """
        获取可视化目录

        Args:
            params: RQA 参数

        Returns:
            可视化目录路径
        """
        signature = generate_param_signature(params)
        viz_dir = self.viz_dir / signature
        viz_dir.mkdir(parents=True, exist_ok=True)
        return viz_dir

    def generate_descriptive_stats(self, params: Dict) -> Dict:
        """
        生成描述性统计

        Args:
            params: RQA 参数

        Returns:
            {
                'success': bool,
                'output_file': str,
                'total_features': int,
                'groups': List[str]
            }
        """
        try:
            # 读取 Step 3 增强特征数据
            step3_dir = self.get_step_directory(params, 'step3_feature_enrichment')
            enriched_file = step3_dir / 'enriched_features.csv'

            if not enriched_file.exists():
                return {
                    'success': False,
                    'error': f'增强特征文件不存在: {enriched_file}'
                }

            df = pd.read_csv(enriched_file)

            # 标准化列名
            df.columns = df.columns.str.lower()
            if 'group' in df.columns:
                df['group'] = df['group'].str.lower()

            # 计算描述性统计
            stats_df = self.analyzer.compute_descriptive_stats(df)

            # 保存结果
            viz_dir = self.get_visualization_directory(params)
            output_file = viz_dir / 'descriptive_stats_by_group.csv'
            stats_df.to_csv(output_file, index=False)

            logger.info(f"描述性统计已保存: {output_file}")

            return {
                'success': True,
                'output_file': str(output_file),
                'total_features': len(stats_df['feature'].unique()),
                'groups': stats_df['group'].unique().tolist()
            }

        except Exception as e:
            logger.error(f"生成描述性统计失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def generate_correlation_analysis(
        self,
        params: Dict,
        method: str = 'pearson'
    ) -> Dict:
        """
        生成相关性分析

        Args:
            params: RQA 参数
            method: 'pearson' 或 'spearman'

        Returns:
            {
                'success': bool,
                'correlation_matrix_file': str,
                'heatmap_file': str
            }
        """
        try:
            # 读取 Step 3 增强特征数据
            step3_dir = self.get_step_directory(params, 'step3_feature_enrichment')
            enriched_file = step3_dir / 'enriched_features.csv'

            if not enriched_file.exists():
                return {
                    'success': False,
                    'error': f'增强特征文件不存在: {enriched_file}'
                }

            df = pd.read_csv(enriched_file)
            df.columns = df.columns.str.lower()

            # 计算相关性矩阵
            corr_matrix = self.analyzer.compute_correlation_matrix(df, method)

            # 保存相关性矩阵
            viz_dir = self.get_visualization_directory(params)
            corr_file = viz_dir / f'correlation_matrix_{method}.csv'
            corr_matrix.to_csv(corr_file)

            # 绘制热力图
            heatmap_file = viz_dir / f'correlation_heatmap_{method}.png'
            self.analyzer.plot_correlation_heatmap(corr_matrix, heatmap_file)

            return {
                'success': True,
                'correlation_matrix_file': str(corr_file),
                'heatmap_file': str(heatmap_file)
            }

        except Exception as e:
            logger.error(f"生成相关性分析失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def generate_significance_barplot(self, params: Dict, top_n: int = 20) -> Dict:
        """
        生成显著性特征柱状图

        Args:
            params: RQA 参数
            top_n: 显示前 N 个特征

        Returns:
            {
                'success': bool,
                'plot_file': str
            }
        """
        try:
            # 读取 Step 4 组间比较结果
            step4_dir = self.get_step_directory(params, 'step4_statistical_analysis')
            comparison_file = step4_dir / 'group_comparison.csv'

            if not comparison_file.exists():
                return {
                    'success': False,
                    'error': f'组间比较文件不存在: {comparison_file}'
                }

            comparison_df = pd.read_csv(comparison_file)

            # 绘制柱状图
            viz_dir = self.get_visualization_directory(params)
            plot_file = viz_dir / f'significant_features_barplot_top{top_n}.png'
            self.analyzer.plot_significant_features_barplot(
                comparison_df, plot_file, top_n
            )

            return {
                'success': True,
                'plot_file': str(plot_file)
            }

        except Exception as e:
            logger.error(f"生成显著性柱状图失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def generate_complexity_violin(self, params: Dict) -> Dict:
        """
        生成复杂度小提琴图

        Args:
            params: RQA 参数

        Returns:
            {
                'success': bool,
                'plot_file': str
            }
        """
        try:
            # 读取 Step 3 增强特征数据
            step3_dir = self.get_step_directory(params, 'step3_feature_enrichment')
            enriched_file = step3_dir / 'enriched_features.csv'

            if not enriched_file.exists():
                return {
                    'success': False,
                    'error': f'增强特征文件不存在: {enriched_file}'
                }

            df = pd.read_csv(enriched_file)
            df.columns = df.columns.str.lower()
            if 'group' in df.columns:
                df['group'] = df['group'].str.lower()

            # 绘制小提琴图
            viz_dir = self.get_visualization_directory(params)
            plot_file = viz_dir / 'complexity_violin.png'
            self.analyzer.plot_complexity_violin(df, plot_file)

            return {
                'success': True,
                'plot_file': str(plot_file)
            }

        except Exception as e:
            logger.error(f"生成复杂度小提琴图失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def generate_grouped_boxplots(
        self,
        params: Dict,
        features: Optional[List[str]] = None
    ) -> Dict:
        """
        生成分组箱线图

        Args:
            params: RQA 参数
            features: 要可视化的特征列表（None 则使用显著特征）

        Returns:
            {
                'success': bool,
                'plot_file': str
            }
        """
        try:
            # 读取数据
            step3_dir = self.get_step_directory(params, 'step3_feature_enrichment')
            enriched_file = step3_dir / 'enriched_features.csv'

            if not enriched_file.exists():
                return {
                    'success': False,
                    'error': f'增强特征文件不存在: {enriched_file}'
                }

            df = pd.read_csv(enriched_file)
            df.columns = df.columns.str.lower()
            if 'group' in df.columns:
                df['group'] = df['group'].str.lower()

            # 如果未指定特征，使用显著特征
            if features is None:
                step4_dir = self.get_step_directory(params, 'step4_statistical_analysis')
                comparison_file = step4_dir / 'group_comparison.csv'

                if comparison_file.exists():
                    comparison_df = pd.read_csv(comparison_file)
                    significant = comparison_df[comparison_df['significant']]
                    features = significant.nlargest(9, 'f_statistic')['feature'].tolist()
                else:
                    # 默认使用前 9 个 RQA 特征
                    features = self.analyzer._identify_rqa_features(df)[:9]

            # 绘制箱线图
            viz_dir = self.get_visualization_directory(params)
            plot_file = viz_dir / 'grouped_boxplots.png'
            self.analyzer.plot_grouped_boxplots(df, features, plot_file)

            return {
                'success': True,
                'plot_file': str(plot_file)
            }

        except Exception as e:
            logger.error(f"生成分组箱线图失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def generate_all_visualizations(self, params: Dict) -> Dict:
        """
        一键生成所有可视化

        Args:
            params: RQA 参数

        Returns:
            {
                'success': bool,
                'results': Dict,
                'total_files': int
            }
        """
        try:
            results = {}

            # 1. 描述性统计
            results['descriptive_stats'] = self.generate_descriptive_stats(params)

            # 2. Pearson 相关性分析
            results['correlation_pearson'] = self.generate_correlation_analysis(
                params, method='pearson'
            )

            # 3. Spearman 相关性分析
            results['correlation_spearman'] = self.generate_correlation_analysis(
                params, method='spearman'
            )

            # 4. 显著性柱状图
            results['significance_barplot'] = self.generate_significance_barplot(params)

            # 5. 复杂度小提琴图
            results['complexity_violin'] = self.generate_complexity_violin(params)

            # 6. 分组箱线图
            results['grouped_boxplots'] = self.generate_grouped_boxplots(params)

            # 统计成功生成的文件数
            total_files = sum(
                1 for r in results.values()
                if r.get('success') and ('plot_file' in r or 'heatmap_file' in r)
            )

            return {
                'success': True,
                'results': results,
                'total_files': total_files
            }

        except Exception as e:
            logger.error(f"批量生成可视化失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
```

---

### 4.3 API 扩展 (api.py)

在现有 `api.py` 中新增以下路由：

```python
# 新增导入
from .visualization_service import VisualizationService

# 新增 Service 单例
_visualization_service = None

def get_visualization_service() -> VisualizationService:
    """获取可视化服务单例"""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService()
        logger.info("VisualizationService initialized (lazy loading)")
    return _visualization_service


# ========== 新增可视化分析 API 路由 ==========

@m05_bp.route('/visualization/descriptive-stats', methods=['POST'])
@validate_params('params')
@handle_api_errors
def generate_descriptive_stats() -> Response:
    """
    生成描述性统计

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "output_file": "...",
        "total_features": 23,
        "groups": ["control", "mci", "ad"]
    }
    """
    data = request.get_json()
    params = data['params']

    viz_service = get_visualization_service()
    result = viz_service.generate_descriptive_stats(params)

    return jsonify(result)


@m05_bp.route('/visualization/correlation-analysis', methods=['POST'])
@validate_params('params')
@handle_api_errors
def generate_correlation_analysis() -> Response:
    """
    生成相关性分析

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "method": "pearson"  // 可选: "pearson" 或 "spearman"
    }

    Response:
    {
        "success": true,
        "correlation_matrix_file": "...",
        "heatmap_file": "..."
    }
    """
    data = request.get_json()
    params = data['params']
    method = data.get('method', 'pearson')

    viz_service = get_visualization_service()
    result = viz_service.generate_correlation_analysis(params, method)

    return jsonify(result)


@m05_bp.route('/visualization/significance-barplot', methods=['POST'])
@validate_params('params')
@handle_api_errors
def generate_significance_barplot() -> Response:
    """
    生成显著性特征柱状图

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "top_n": 20  // 可选，默认 20
    }

    Response:
    {
        "success": true,
        "plot_file": "..."
    }
    """
    data = request.get_json()
    params = data['params']
    top_n = data.get('top_n', 20)

    viz_service = get_visualization_service()
    result = viz_service.generate_significance_barplot(params, top_n)

    return jsonify(result)


@m05_bp.route('/visualization/complexity-violin', methods=['POST'])
@validate_params('params')
@handle_api_errors
def generate_complexity_violin() -> Response:
    """
    生成复杂度小提琴图

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "plot_file": "..."
    }
    """
    data = request.get_json()
    params = data['params']

    viz_service = get_visualization_service()
    result = viz_service.generate_complexity_violin(params)

    return jsonify(result)


@m05_bp.route('/visualization/grouped-boxplots', methods=['POST'])
@validate_params('params')
@handle_api_errors
def generate_grouped_boxplots() -> Response:
    """
    生成分组箱线图

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2},
        "features": ["x_rr", "y_det", ...]  // 可选，默认使用显著特征
    }

    Response:
    {
        "success": true,
        "plot_file": "..."
    }
    """
    data = request.get_json()
    params = data['params']
    features = data.get('features')

    viz_service = get_visualization_service()
    result = viz_service.generate_grouped_boxplots(params, features)

    return jsonify(result)


@m05_bp.route('/visualization/generate-all', methods=['POST'])
@validate_params('params')
@handle_api_errors
def generate_all_visualizations() -> Response:
    """
    一键生成所有可视化

    Request Body:
    {
        "params": {"m": 2, "tau": 1, "eps": 0.05, "lmin": 2}
    }

    Response:
    {
        "success": true,
        "results": {
            "descriptive_stats": {...},
            "correlation_pearson": {...},
            ...
        },
        "total_files": 8
    }
    """
    data = request.get_json()
    params = data['params']

    viz_service = get_visualization_service()
    result = viz_service.generate_all_visualizations(params)

    return jsonify(result)


@m05_bp.route('/visualization/image/<path:filename>', methods=['GET'])
@handle_api_errors
def get_visualization_image(filename: str) -> Response:
    """
    获取可视化图片

    URL: /api/m05/visualization/image/{signature}/{filename}

    Response: 图片文件
    """
    viz_service = get_visualization_service()
    file_path = viz_service.viz_dir / filename

    if not file_path.exists():
        return jsonify({'success': False, 'error': '图片不存在'}), 404

    return send_file(file_path, mimetype='image/png')
```

---

## 5. 前端设计

### 5.1 EnhancedVisualizationPanel.jsx

新建独立组件，在 `AdvancedAnalysisPanel` 中作为新标签页集成。

```jsx
/**
 * Module05: 增强可视化分析面板
 *
 * 功能：
 * 1. 描述性统计表格
 * 2. 相关性热力图
 * 3. 显著性特征柱状图
 * 4. 复杂度小提琴图
 * 5. 分组箱线图
 * 6. 一键生成所有可视化
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Table, Select, Space, Spin, message,
  Statistic, Tag, Tabs, Image, Alert, Radio, Checkbox
} from 'antd';
import {
  BarChartOutlined, HeatMapOutlined, LineChartOutlined,
  BoxPlotOutlined, ThunderboltOutlined, DownloadOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { TabPane } = Tabs;

const EnhancedVisualizationPanel = () => {
  // ===== 状态管理 =====
  const [loading, setLoading] = useState(false);
  const [availableParams, setAvailableParams] = useState([]);
  const [selectedParam, setSelectedParam] = useState(null);
  const [activeVizTab, setActiveVizTab] = useState('overview');

  // 可视化结果状态
  const [descriptiveStats, setDescriptiveStats] = useState(null);
  const [correlationHeatmap, setCorrelationHeatmap] = useState(null);
  const [significanceBarplot, setSignificanceBarplot] = useState(null);
  const [complexityViolin, setComplexityViolin] = useState(null);
  const [groupedBoxplots, setGroupedBoxplots] = useState(null);

  // 配置选项
  const [correlationMethod, setCorrelationMethod] = useState('pearson');
  const [topNFeatures, setTopNFeatures] = useState(20);

  // ===== 初始化 =====
  useEffect(() => {
    fetchAvailableParams();
  }, []);

  // ===== API 调用函数 =====

  const fetchAvailableParams = async () => {
    try {
      const response = await axios.get('/api/m05/results/list');
      if (response.data.success) {
        setAvailableParams(response.data.results);
        if (response.data.results.length > 0) {
          setSelectedParam(response.data.results[0].params);
        }
      }
    } catch (error) {
      console.error('获取参数列表失败:', error);
    }
  };

  const generateDescriptiveStats = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/descriptive-stats', {
        params: selectedParam
      });

      if (response.data.success) {
        // 读取 CSV 数据并展示
        const csvResponse = await axios.get(response.data.output_file);
        setDescriptiveStats(csvResponse.data);
        message.success('描述性统计生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成描述性统计失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateCorrelationAnalysis = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/correlation-analysis', {
        params: selectedParam,
        method: correlationMethod
      });

      if (response.data.success) {
        setCorrelationHeatmap(response.data.heatmap_file);
        message.success(`${correlationMethod.toUpperCase()} 相关性分析完成！`);
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成相关性分析失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateSignificanceBarplot = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/significance-barplot', {
        params: selectedParam,
        top_n: topNFeatures
      });

      if (response.data.success) {
        setSignificanceBarplot(response.data.plot_file);
        message.success('显著性柱状图生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成显著性柱状图失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateComplexityViolin = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/complexity-violin', {
        params: selectedParam
      });

      if (response.data.success) {
        setComplexityViolin(response.data.plot_file);
        message.success('复杂度小提琴图生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成复杂度小提琴图失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateGroupedBoxplots = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/grouped-boxplots', {
        params: selectedParam
      });

      if (response.data.success) {
        setGroupedBoxplots(response.data.plot_file);
        message.success('分组箱线图生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成分组箱线图失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateAllVisualizations = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/generate-all', {
        params: selectedParam
      });

      if (response.data.success) {
        const results = response.data.results;

        // 更新所有状态
        if (results.correlation_pearson?.success) {
          setCorrelationHeatmap(results.correlation_pearson.heatmap_file);
        }
        if (results.significance_barplot?.success) {
          setSignificanceBarplot(results.significance_barplot.plot_file);
        }
        if (results.complexity_violin?.success) {
          setComplexityViolin(results.complexity_violin.plot_file);
        }
        if (results.grouped_boxplots?.success) {
          setGroupedBoxplots(results.grouped_boxplots.plot_file);
        }

        message.success(`所有可视化生成完成！共 ${response.data.total_files} 个文件`);
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('批量生成失败:', error);
      message.error('批量生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // ===== 渲染函数 =====

  const renderOverview = () => (
    <Card title="可视化概览" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Alert
          message="增强可视化分析模块"
          description="该模块提供专业的统计图表和分组可视化，支持描述性统计、相关性分析、显著性检验等多种科研可视化功能。"
          type="info"
          showIcon
        />

        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="可用参数组合"
              value={availableParams.length}
              prefix={<ThunderboltOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="可视化类型"
              value={6}
              prefix={<BarChartOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="当前参数"
              value={selectedParam ? 'm=' + selectedParam.m : 'N/A'}
            />
          </Col>
        </Row>

        <Space>
          <Select
            style={{ width: 300 }}
            placeholder="选择参数组合"
            value={selectedParam ? JSON.stringify(selectedParam) : undefined}
            onChange={(value) => setSelectedParam(JSON.parse(value))}
          >
            {availableParams.map((item, idx) => (
              <Option key={idx} value={JSON.stringify(item.params)}>
                m={item.params.m}, τ={item.params.tau}, ε={item.params.eps}, lmin={item.params.lmin}
              </Option>
            ))}
          </Select>

          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={generateAllVisualizations}
            loading={loading}
            size="large"
          >
            一键生成所有可视化
          </Button>
        </Space>
      </Space>
    </Card>
  );

  const renderCorrelationHeatmap = () => (
    <Card title="相关性热力图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Space>
          <Radio.Group
            value={correlationMethod}
            onChange={(e) => setCorrelationMethod(e.target.value)}
          >
            <Radio.Button value="pearson">Pearson</Radio.Button>
            <Radio.Button value="spearman">Spearman</Radio.Button>
          </Radio.Group>

          <Button
            type="primary"
            icon={<HeatMapOutlined />}
            onClick={generateCorrelationAnalysis}
            loading={loading}
          >
            生成热力图
          </Button>
        </Space>

        {correlationHeatmap && (
          <Image
            src={`/api/m05/visualization/image/${correlationHeatmap.split('visualizations/')[1]}`}
            alt="Correlation Heatmap"
            style={{ maxWidth: '100%' }}
          />
        )}
      </Space>
    </Card>
  );

  const renderSignificanceBarplot = () => (
    <Card title="显著性特征柱状图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Space>
          <span>显示前</span>
          <Select
            value={topNFeatures}
            onChange={setTopNFeatures}
            style={{ width: 80 }}
          >
            <Option value={10}>10</Option>
            <Option value={20}>20</Option>
            <Option value={30}>30</Option>
          </Select>
          <span>个特征</span>

          <Button
            type="primary"
            icon={<BarChartOutlined />}
            onClick={generateSignificanceBarplot}
            loading={loading}
          >
            生成柱状图
          </Button>
        </Space>

        {significanceBarplot && (
          <Image
            src={`/api/m05/visualization/image/${significanceBarplot.split('visualizations/')[1]}`}
            alt="Significance Barplot"
            style={{ maxWidth: '100%' }}
          />
        )}
      </Space>
    </Card>
  );

  const renderComplexityViolin = () => (
    <Card title="复杂度小提琴图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Button
          type="primary"
          icon={<LineChartOutlined />}
          onClick={generateComplexityViolin}
          loading={loading}
        >
          生成小提琴图
        </Button>

        {complexityViolin && (
          <Image
            src={`/api/m05/visualization/image/${complexityViolin.split('visualizations/')[1]}`}
            alt="Complexity Violin Plot"
            style={{ maxWidth: '100%' }}
          />
        )}
      </Space>
    </Card>
  );

  const renderGroupedBoxplots = () => (
    <Card title="分组箱线图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Button
          type="primary"
          icon={<BoxPlotOutlined />}
          onClick={generateGroupedBoxplots}
          loading={loading}
        >
          生成箱线图
        </Button>

        {groupedBoxplots && (
          <Image
            src={`/api/m05/visualization/image/${groupedBoxplots.split('visualizations/')[1]}`}
            alt="Grouped Boxplots"
            style={{ maxWidth: '100%' }}
          />
        )}
      </Space>
    </Card>
  );

  // ===== 主渲染 =====
  return (
    <Spin spinning={loading} tip="生成可视化中...">
      <Tabs activeKey={activeVizTab} onChange={setActiveVizTab}>
        <TabPane tab="概览" key="overview">
          {renderOverview()}
        </TabPane>

        <TabPane tab="相关性热力图" key="correlation">
          {renderCorrelationHeatmap()}
        </TabPane>

        <TabPane tab="显著性柱状图" key="significance">
          {renderSignificanceBarplot()}
        </TabPane>

        <TabPane tab="复杂度小提琴图" key="complexity">
          {renderComplexityViolin()}
        </TabPane>

        <TabPane tab="分组箱线图" key="boxplots">
          {renderGroupedBoxplots()}
        </TabPane>
      </Tabs>
    </Spin>
  );
};

export default EnhancedVisualizationPanel;
```

---

### 5.2 AdvancedAnalysisPanel 集成

在 `AdvancedAnalysisPanel.jsx` 中添加新标签页：

```jsx
import EnhancedVisualizationPanel from './EnhancedVisualizationPanel';

// 在主 Tabs 中添加新标签页
<Tabs activeKey={activeSubTab} onChange={setActiveSubTab}>
  <TabPane tab="参数优化评估" key="param-eval">
    {/* 现有内容 */}
  </TabPane>

  <TabPane tab="任务分层分析" key="task-analysis">
    {/* 现有内容 */}
  </TabPane>

  <TabPane tab="任务对比分析" key="task-compare">
    {/* 现有内容 */}
  </TabPane>

  {/* 新增标签页 */}
  <TabPane tab="可视化分析(新)" key="enhanced-viz">
    <EnhancedVisualizationPanel />
  </TabPane>

  <TabPane tab="单个查询" key="individual-query">
    {/* 现有内容 */}
  </TabPane>
</Tabs>
```

---

## 6. 数据流设计

### 6.1 数据流图

```
用户选择参数组合
    ↓
前端发送 POST 请求 (/api/m05/visualization/*)
    ↓
API 层接收请求，调用 VisualizationService
    ↓
VisualizationService 读取 Step 3/4 已有数据
    ↓
VisualizationAnalyzer 执行统计分析 + 绘图
    ↓
保存结果到 data/05_rqa_analysis/visualizations/{signature}/
    ↓
返回文件路径给前端
    ↓
前端通过 GET /api/m05/visualization/image/{path} 获取图片
    ↓
展示可视化结果
```

### 6.2 目录结构

```
data/
├── 05_rqa_analysis/
│   ├── results/
│   │   └── m2_tau1_eps0.05_lmin2/
│   │       ├── step1_rqa_features/
│   │       ├── step2_data_merging/
│   │       │   └── merged_rqa_features.csv
│   │       ├── step3_feature_enrichment/
│   │       │   └── enriched_features.csv          ← 新模块读取
│   │       ├── step4_statistical_analysis/
│   │       │   └── group_comparison.csv           ← 新模块读取
│   │       └── step5_visualization/
│   │
│   └── visualizations/                            ← 新模块输出
│       └── m2_tau1_eps0.05_lmin2/
│           ├── descriptive_stats_by_group.csv     ← FR1
│           ├── correlation_matrix_pearson.csv     ← FR2
│           ├── correlation_matrix_spearman.csv
│           ├── correlation_heatmap_pearson.png    ← FR3
│           ├── correlation_heatmap_spearman.png
│           ├── significant_features_barplot_top20.png  ← FR4
│           ├── complexity_violin.png              ← FR5
│           └── grouped_boxplots.png               ← FR6
```

---

## 7. 实施计划

### 7.1 开发阶段

| 阶段 | 任务 | 预估时间 | 负责人 |
|------|------|---------|--------|
| P1 | 后端 `visualization_analyzer.py` 开发 | 4h | - |
| P2 | 后端 `visualization_service.py` 开发 | 3h | - |
| P3 | 后端 API 路由扩展 | 1h | - |
| P4 | 前端 `EnhancedVisualizationPanel` 开发 | 4h | - |
| P5 | 前端集成到 `AdvancedAnalysisPanel` | 1h | - |
| P6 | 单元测试编写 | 2h | - |
| P7 | 集成测试 | 1h | - |
| P8 | 文档完善 | 1h | - |

**总计**: 约 17 小时

### 7.2 里程碑

- **M1 (P1-P3完成)**: 后端功能可用
- **M2 (P4-P5完成)**: 前后端集成完成
- **M3 (P6-P8完成)**: 测试通过，文档完善

---

## 8. 测试策略

### 8.1 单元测试

在 `tests/test_visualization.py` 中编写：

```python
import pytest
import pandas as pd
from pathlib import Path
from src.modules.module05_rqa_analysis.visualization_analyzer import VisualizationAnalyzer

class TestVisualizationAnalyzer:
    """测试可视化分析器"""

    @pytest.fixture
    def sample_data(self):
        """生成测试数据"""
        return pd.DataFrame({
            'subject_id': ['s1', 's2', 's3', 's4', 's5', 's6'],
            'group': ['control', 'control', 'mci', 'mci', 'ad', 'ad'],
            'x_rr': [0.5, 0.6, 0.4, 0.45, 0.3, 0.35],
            'y_det': [0.7, 0.75, 0.6, 0.65, 0.5, 0.55],
            'combined_ent': [1.2, 1.3, 1.0, 1.1, 0.8, 0.9],
            'complexity_x': [2.4, 2.6, 2.0, 2.2, 1.6, 1.8]
        })

    def test_compute_descriptive_stats(self, sample_data):
        """测试描述性统计计算"""
        analyzer = VisualizationAnalyzer()
        result = analyzer.compute_descriptive_stats(sample_data)

        assert len(result) == 12  # 4 features * 3 groups
        assert 'mean' in result.columns
        assert 'std' in result.columns
        assert result['group'].unique().tolist() == ['control', 'mci', 'ad']

    def test_compute_correlation_matrix(self, sample_data):
        """测试相关性矩阵计算"""
        analyzer = VisualizationAnalyzer()
        corr_matrix = analyzer.compute_correlation_matrix(sample_data, method='pearson')

        assert corr_matrix.shape == (4, 4)  # 4 features
        assert (corr_matrix.values.diagonal() == 1.0).all()  # 对角线为1

    # 更多测试...
```

### 8.2 集成测试

测试完整流程：

1. 准备测试数据（使用现有 Step 1-4 结果）
2. 调用 API 生成可视化
3. 验证文件生成
4. 验证图片可访问

---

## 9. 总结

本设计文档提供了 Module05 增强可视化分析模块的完整技术方案，包括：

✅ **保持向后兼容**: 不修改现有 Step 1-5 逻辑
✅ **架构规范**: 遵循分层架构（API → Service → Analyzer）
✅ **充分复用**: 利用 Step 3-4 已有数据
✅ **功能完善**: 补齐缺失的统计分析和可视化功能
✅ **科研导向**: 提供专业的统计图表（热力图、小提琴图、箱线图等）
✅ **用户友好**: 前端集成到"高级分析"面板，支持一键生成

该模块预计开发时间 **17 小时**，可独立开发和测试，不影响现有功能。
