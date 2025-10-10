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

    def batch_generate_visualizations(self, param_list: List[Dict]) -> Dict:
        """
        批量生成多个参数组合的可视化

        Args:
            param_list: RQA 参数列表 [{"m": 2, "tau": 1, ...}, ...]

        Returns:
            {
                'success': bool,
                'total_params': int,
                'completed': int,
                'failed': int,
                'results': List[Dict]
            }
        """
        try:
            results = []
            completed = 0
            failed = 0

            for idx, params in enumerate(param_list):
                logger.info(f"批量可视化进度: {idx + 1}/{len(param_list)} - 参数: {params}")

                try:
                    # 生成该参数组合的所有可视化
                    result = self.generate_all_visualizations(params)

                    if result['success']:
                        completed += 1
                        results.append({
                            'params': params,
                            'success': True,
                            'total_files': result['total_files']
                        })
                    else:
                        failed += 1
                        results.append({
                            'params': params,
                            'success': False,
                            'error': result.get('error', 'Unknown error')
                        })

                except Exception as e:
                    failed += 1
                    logger.error(f"参数 {params} 可视化失败: {e}", exc_info=True)
                    results.append({
                        'params': params,
                        'success': False,
                        'error': str(e)
                    })

            return {
                'success': True,
                'total_params': len(param_list),
                'completed': completed,
                'failed': failed,
                'results': results
            }

        except Exception as e:
            logger.error(f"批量可视化失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def list_all_visualizations(self) -> Dict:
        """
        列出所有已生成的可视化

        Returns:
            {
                'success': bool,
                'visualizations': List[Dict]
            }
        """
        try:
            visualizations = []

            # 遍历所有参数目录
            if not self.viz_dir.exists():
                return {'success': True, 'visualizations': []}

            for param_dir in self.viz_dir.iterdir():
                if not param_dir.is_dir():
                    continue

                signature = param_dir.name

                # 扫描该目录下的所有图片文件
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_files.extend(param_dir.glob(ext))

                if len(image_files) == 0:
                    continue

                # 分类图片
                viz_types = {
                    'correlation_heatmap': [],
                    'significance_barplot': [],
                    'complexity_violin': [],
                    'grouped_boxplots': []
                }

                for img_file in image_files:
                    filename = img_file.name
                    if 'correlation_heatmap' in filename:
                        viz_types['correlation_heatmap'].append({
                            'filename': filename,
                            'path': f"{signature}/{filename}",
                            'method': 'pearson' if 'pearson' in filename else 'spearman'
                        })
                    elif 'significant_features_barplot' in filename:
                        viz_types['significance_barplot'].append({
                            'filename': filename,
                            'path': f"{signature}/{filename}"
                        })
                    elif 'complexity_violin' in filename:
                        viz_types['complexity_violin'].append({
                            'filename': filename,
                            'path': f"{signature}/{filename}"
                        })
                    elif 'grouped_boxplots' in filename:
                        viz_types['grouped_boxplots'].append({
                            'filename': filename,
                            'path': f"{signature}/{filename}"
                        })

                visualizations.append({
                    'signature': signature,
                    'total_images': len(image_files),
                    'viz_types': viz_types
                })

            return {
                'success': True,
                'visualizations': visualizations,
                'total_params': len(visualizations)
            }

        except Exception as e:
            logger.error(f"列出可视化失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
