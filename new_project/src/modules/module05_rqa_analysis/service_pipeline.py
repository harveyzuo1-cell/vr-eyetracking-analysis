"""
Module05 RQA分析流水线 - 5步RQA处理流程
"""

import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from src.utils.logger import setup_logger
from .rqa_analyzer import RQAAnalyzer

logger = setup_logger(__name__)


class RQAPipeline:
    """RQA 5步分析流水线"""

    def __init__(self, service):
        """
        初始化RQA流水线

        Args:
            service: RQAAnalysisService实例,用于访问目录和配置
        """
        self.service = service
        self.analyzer = RQAAnalyzer()

    def step1_rqa_calculation(self, params: Dict, groups: List[str]) -> Dict:
        """
        Step 1: RQA计算 - 对所有CSV文件进行RQA特征提取

        Args:
            params: RQA参数 {'m': int, 'tau': int, 'eps': float, 'lmin': int}
            groups: 要处理的组列表,如 ['control', 'mci', 'ad']

        Returns:
            {
                'success': bool,
                'processed_files': int,
                'output_files': List[str],
                'params': Dict
            }
        """
        try:
            m = params['m']
            tau = params['tau']
            eps = params['eps']
            lmin = params['lmin']

            # 创建输出目录
            step_dir = self.service.get_step_directory(params, 'step1_rqa_features')
            step_dir.mkdir(parents=True, exist_ok=True)

            processed_files = 0
            output_files = []

            for group in groups:
                # 扫描该组的校准文件
                calibrated_files = self.service.scan_calibrated_files(group, self.service.current_data_version)

                # 为每个CSV文件计算RQA特征
                for csv_file in calibrated_files:
                    try:
                        # 加载数据
                        df = pd.read_csv(csv_file)

                        # 提取归一化坐标
                        x = df['x'].values if 'x' in df.columns else df['GazePointX_normalized'].values
                        y = df['y'].values if 'y' in df.columns else df['GazePointY_normalized'].values

                        # 1D RQA - X轴
                        embedded_x = self.analyzer.embed_signal_1d(x, m, tau)
                        rp_x = self.analyzer.compute_recurrence_matrix(embedded_x, eps, '1d_abs')
                        rqa_x = self.analyzer.compute_rqa_metrics(rp_x, lmin)

                        # 1D RQA - Y轴
                        embedded_y = self.analyzer.embed_signal_1d(y, m, tau)
                        rp_y = self.analyzer.compute_recurrence_matrix(embedded_y, eps, '1d_abs')
                        rqa_y = self.analyzer.compute_rqa_metrics(rp_y, lmin)

                        # 2D RQA - 联合分析
                        embedded_xy = self.analyzer.embed_signal_2d(x, y, m, tau)
                        rp_xy = self.analyzer.compute_recurrence_matrix(embedded_xy, eps, 'euclidean')
                        rqa_xy = self.analyzer.compute_rqa_metrics(rp_xy, lmin)

                        # 构造输出数据
                        result = {
                            'subject_id': csv_file.stem.replace('_calibrated', ''),
                            'group': group,
                            'x_RR': rqa_x['RR'], 'x_DET': rqa_x['DET'], 'x_LAM': rqa_x['LAM'],
                            'x_ENT': rqa_x['ENT'], 'x_Lmax': rqa_x['Lmax'],
                            'y_RR': rqa_y['RR'], 'y_DET': rqa_y['DET'], 'y_LAM': rqa_y['LAM'],
                            'y_ENT': rqa_y['ENT'], 'y_Lmax': rqa_y['Lmax'],
                            'combined_RR': rqa_xy['RR'], 'combined_DET': rqa_xy['DET'],
                            'combined_LAM': rqa_xy['LAM'], 'combined_ENT': rqa_xy['ENT'],
                            'combined_Lmax': rqa_xy['Lmax']
                        }

                        # 保存到CSV
                        output_file = step_dir / f"{result['subject_id']}_rqa.csv"
                        pd.DataFrame([result]).to_csv(output_file, index=False)

                        output_files.append(str(output_file))
                        processed_files += 1

                    except Exception as e:
                        logger.error(f"处理文件失败 {csv_file}: {e}")

            # 保存元数据
            self.service.save_param_metadata(params, step=1, data={
                'processed_files': processed_files,
                'groups': groups
            })

            return {
                'success': True,
                'processed_files': processed_files,
                'output_files': output_files,
                'params': params
            }

        except Exception as e:
            logger.error(f"Step 1执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def step2_data_merging(self, params: Dict, groups: List[str]) -> Dict:
        """
        Step 2: 数据合并 - 将所有组的RQA特征合并为一个DataFrame

        Args:
            params: RQA参数
            groups: 组列表

        Returns:
            {
                'success': bool,
                'merged_file': str,
                'total_records': int
            }
        """
        try:
            step1_dir = self.service.get_step_directory(params, 'step1_rqa_features')
            step2_dir = self.service.get_step_directory(params, 'step2_data_merging')
            step2_dir.mkdir(parents=True, exist_ok=True)

            # 读取所有RQA结果文件
            all_data = []
            for rqa_file in step1_dir.glob('*_rqa.csv'):
                df = pd.read_csv(rqa_file)
                all_data.append(df)

            if not all_data:
                return {
                    'success': False,
                    'error': 'No RQA feature files found in Step 1'
                }

            # 合并所有数据
            merged_df = pd.concat(all_data, ignore_index=True)

            # 保存合并后的数据
            merged_file = step2_dir / 'merged_rqa_features.csv'
            merged_df.to_csv(merged_file, index=False)

            # 保存元数据
            self.service.save_param_metadata(params, step=2, data={
                'total_records': len(merged_df),
                'groups': groups
            })

            return {
                'success': True,
                'merged_file': str(merged_file),
                'total_records': len(merged_df)
            }

        except Exception as e:
            logger.error(f"Step 2执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def step3_feature_enrichment(self, params: Dict) -> Dict:
        """
        Step 3: 特征增强 - 计算派生特征和统计量

        Args:
            params: RQA参数

        Returns:
            {
                'success': bool,
                'enriched_file': str,
                'new_features': List[str]
            }
        """
        try:
            step2_dir = self.service.get_step_directory(params, 'step2_data_merging')
            step3_dir = self.service.get_step_directory(params, 'step3_feature_enrichment')
            step3_dir.mkdir(parents=True, exist_ok=True)

            # 读取合并数据
            merged_file = step2_dir / 'merged_rqa_features.csv'
            if not merged_file.exists():
                return {'success': False, 'error': f'Merged file not found: {merged_file}'}

            df = pd.read_csv(merged_file)

            # 派生特征1: RQA对称性
            df['RR_symmetry'] = (df['x_RR'] + df['y_RR']) / 2 - df['combined_RR']
            df['DET_symmetry'] = (df['x_DET'] + df['y_DET']) / 2 - df['combined_DET']

            # 派生特征2: 维度差异
            df['RR_xy_diff'] = abs(df['x_RR'] - df['y_RR'])
            df['DET_xy_diff'] = abs(df['x_DET'] - df['y_DET'])
            df['ENT_xy_diff'] = abs(df['x_ENT'] - df['y_ENT'])

            # 派生特征3: 复杂度指标
            df['complexity_x'] = df['x_ENT'] / (df['x_RR'] + 1e-10)
            df['complexity_y'] = df['y_ENT'] / (df['y_RR'] + 1e-10)
            df['complexity_combined'] = df['combined_ENT'] / (df['combined_RR'] + 1e-10)

            # 保存增强后的数据
            enriched_file = step3_dir / 'enriched_features.csv'
            df.to_csv(enriched_file, index=False)

            new_features = ['RR_symmetry', 'DET_symmetry', 'RR_xy_diff', 'DET_xy_diff',
                           'ENT_xy_diff', 'complexity_x', 'complexity_y', 'complexity_combined']

            # 保存元数据
            self.service.save_param_metadata(params, step=3, data={
                'total_features': len(df.columns),
                'new_features': new_features
            })

            return {
                'success': True,
                'enriched_file': str(enriched_file),
                'new_features': new_features
            }

        except Exception as e:
            logger.error(f"Step 3执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def step4_statistical_analysis(self, params: Dict) -> Dict:
        """
        Step 4: 统计分析 - 组间差异检验

        Args:
            params: RQA参数

        Returns:
            {
                'success': bool,
                'comparison_file': str,
                'significant_features': List[str]
            }
        """
        try:
            step3_dir = self.service.get_step_directory(params, 'step3_feature_enrichment')
            step4_dir = self.service.get_step_directory(params, 'step4_statistical_analysis')
            step4_dir.mkdir(parents=True, exist_ok=True)

            # 读取增强特征
            enriched_file = step3_dir / 'enriched_features.csv'
            if not enriched_file.exists():
                return {'success': False, 'error': f'Enriched file not found: {enriched_file}'}

            df = pd.read_csv(enriched_file)

            # 标准化列名和组别值
            df.columns = df.columns.str.lower()
            if 'group' in df.columns:
                df['group'] = df['group'].str.lower()

            # 识别RQA特征列
            rqa_features = [col for col in df.columns if any(
                col.startswith(prefix) or 'rqa' in col or 'complexity' in col or 'symmetry' in col or 'diff' in col
                for prefix in ['x_', 'y_', 'combined_', 'rr', 'det', 'ent', 'lam']
            )]

            # 组间比较
            comparison_results = []
            for feature in rqa_features:
                try:
                    groups = df['group'].unique()
                    group_data = [df[df['group'] == g][feature].dropna() for g in groups]

                    # ANOVA
                    f_stat, p_value = stats.f_oneway(*group_data)

                    comparison_results.append({
                        'feature': feature,
                        'f_statistic': f_stat,
                        'p_value': p_value,
                        'significant': p_value < 0.05
                    })
                except Exception as e:
                    logger.warning(f"特征 {feature} 统计检验失败: {e}")

            # 保存比较结果
            comparison_df = pd.DataFrame(comparison_results)
            comparison_file = step4_dir / 'group_comparison.csv'
            comparison_df.to_csv(comparison_file, index=False)

            significant_features = comparison_df[comparison_df['significant']]['feature'].tolist()

            # 保存元数据
            self.service.save_param_metadata(params, step=4, data={
                'total_features_tested': len(rqa_features),
                'significant_features': len(significant_features)
            })

            return {
                'success': True,
                'comparison_file': str(comparison_file),
                'significant_features': significant_features,
                'total_tested': len(rqa_features)
            }

        except Exception as e:
            logger.error(f"Step 4执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def step5_visualization(self, params: Dict, max_samples: int = 10) -> Dict:
        """
        Step 5: 可视化 - 生成统计图表

        Args:
            params: RQA参数
            max_samples: 最大采样数量

        Returns:
            {
                'success': bool,
                'plot_files': List[str]
            }
        """
        try:
            step3_dir = self.service.get_step_directory(params, 'step3_feature_enrichment')
            step4_dir = self.service.get_step_directory(params, 'step4_statistical_analysis')
            step5_dir = self.service.get_step_directory(params, 'step5_visualization')
            plots_dir = step5_dir / 'statistical_plots'
            plots_dir.mkdir(parents=True, exist_ok=True)

            # 读取数据
            enriched_file = step3_dir / 'enriched_features.csv'
            comparison_file = step4_dir / 'group_comparison.csv'

            if not enriched_file.exists() or not comparison_file.exists():
                return {'success': False, 'error': 'Required files not found'}

            df = pd.read_csv(enriched_file)
            comparison_df = pd.read_csv(comparison_file)

            # 标准化
            df.columns = df.columns.str.lower()
            if 'group' in df.columns:
                df['group'] = df['group'].str.lower()

            # 选择显著特征
            significant = comparison_df[comparison_df['significant']].head(max_samples)

            plot_files = []

            # 箱线图
            if len(significant) > 0:
                fig, axes = plt.subplots(2, 5, figsize=(20, 8))
                axes = axes.flatten()

                for idx, row in significant.iterrows():
                    if idx >= 10:
                        break
                    feature = row['feature']
                    ax = axes[idx]
                    df.boxplot(column=feature, by='group', ax=ax)
                    ax.set_title(f"{feature}\n(p={row['p_value']:.4f})")
                    ax.set_xlabel('Group')
                    ax.set_ylabel(feature)

                plt.suptitle(f'Top {min(10, len(significant))} Significant Features')
                plt.tight_layout()
                boxplot_file = plots_dir / 'rqa_metrics_boxplot.png'
                plt.savefig(boxplot_file, dpi=150, bbox_inches='tight')
                plt.close()
                plot_files.append(str(boxplot_file))

            # 保存元数据
            self.service.save_param_metadata(params, step=5, data={
                'plot_count': len(plot_files)
            })

            return {
                'success': True,
                'plot_files': plot_files
            }

        except Exception as e:
            logger.error(f"Step 5执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
