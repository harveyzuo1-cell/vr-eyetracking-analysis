"""
Module05 RQA分析服务层
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from config.settings import Config
from src.utils.logger import setup_logger
from .rqa_analyzer import RQAAnalyzer
from .utils import generate_param_signature
from src.modules.module02_preprocessing.subject_manager import SubjectManager

logger = setup_logger(__name__)


class RQAAnalysisService:
    """RQA分析服务"""

    def __init__(self):
        """初始化RQA分析服务"""
        self.data_root = Path(Config.DATA_ROOT)
        self.processed_dir = self.data_root / '02_processed'
        self.results_dir = self.data_root / '05_rqa_analysis' / 'results'
        self.cache_dir = self.data_root / '05_rqa_analysis' / 'cache'
        self.exports_dir = self.data_root / '05_rqa_analysis' / 'exports'

        # 创建目录
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        # RQA分析器
        self.analyzer = RQAAnalyzer()

        # 初始化SubjectManager
        subject_info_dir = self.data_root / 'subject_info'
        self.subject_manager = SubjectManager(subject_info_dir)

        logger.info("RQA分析服务初始化完成")

    def generate_param_combinations(self, m_range: Dict, tau_range: Dict,
                                    eps_range: Dict, lmin_range: Dict) -> Dict:
        """
        生成参数组合空间

        Args:
            m_range: {'start': 1, 'end': 10, 'step': 1}
            tau_range: {'start': 1, 'end': 10, 'step': 1}
            eps_range: {'start': 0.05, 'end': 0.1, 'step': 0.001}
            lmin_range: {'start': 2, 'end': 3, 'step': 1}

        Returns:
            {
                'success': True,
                'total_combinations': int,
                'combinations': List[Dict],
                'estimated_time_minutes': float
            }
        """
        try:
            combinations = []

            # 生成m值列表
            m_values = list(range(
                m_range['start'],
                m_range['end'] + 1,
                m_range['step']
            ))

            # 生成tau值列表
            tau_values = list(range(
                tau_range['start'],
                tau_range['end'] + 1,
                tau_range['step']
            ))

            # 生成eps值列表
            eps_start = eps_range['start']
            eps_end = eps_range['end']
            eps_step = eps_range['step']
            eps_values = []
            current_eps = eps_start
            # 使用小的容差来避免浮点精度问题
            while current_eps <= eps_end + eps_step * 0.01:
                eps_values.append(round(current_eps, 6))  # 避免浮点精度问题
                current_eps += eps_step

            # 生成lmin值列表
            lmin_values = list(range(
                lmin_range['start'],
                lmin_range['end'] + 1,
                lmin_range['step']
            ))

            # 生成所有组合
            for m in m_values:
                for tau in tau_values:
                    for eps in eps_values:
                        for lmin in lmin_values:
                            combinations.append({
                                'm': m,
                                'tau': tau,
                                'eps': eps,
                                'lmin': lmin
                            })

            total_combinations = len(combinations)

            # 估算处理时间（假设每个文件2秒，每组500个文件）
            estimated_time_minutes = (total_combinations * 500 * 2) / 60

            # 保存参数组合到缓存
            cache_file = self.cache_dir / 'param_combinations.json'
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'total_combinations': total_combinations,
                    'combinations': combinations,
                    'ranges': {
                        'm': m_range,
                        'tau': tau_range,
                        'eps': eps_range,
                        'lmin': lmin_range
                    }
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"生成参数组合完成: {total_combinations}个")

            return {
                'success': True,
                'total_combinations': total_combinations,
                'combinations': combinations,
                'estimated_time_minutes': estimated_time_minutes
            }

        except Exception as e:
            logger.error(f"生成参数组合失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_param_directory(self, params: Dict) -> Path:
        """获取参数对应的目录路径"""
        signature = generate_param_signature(params)
        param_dir = self.results_dir / signature
        param_dir.mkdir(parents=True, exist_ok=True)
        return param_dir

    def get_step_directory(self, params: Dict, step_name: str) -> Path:
        """获取特定步骤的目录路径"""
        param_dir = self.get_param_directory(params)
        step_dir = param_dir / step_name
        step_dir.mkdir(parents=True, exist_ok=True)
        return step_dir

    def save_param_metadata(self, params: Dict, step: int, data: Dict):
        """
        保存参数元数据

        Args:
            params: RQA参数
            step: 完成的步骤编号 (1-5)
            data: 步骤结果数据
        """
        param_dir = self.get_param_directory(params)
        metadata_file = param_dir / 'metadata.json'

        # 读取现有元数据
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                pass

        # 更新元数据
        if 'signature' not in metadata:
            metadata['signature'] = generate_param_signature(params)
            metadata['parameters'] = params
            metadata['creation_time'] = datetime.now().isoformat()

        metadata['last_updated'] = datetime.now().isoformat()

        # 更新步骤完成状态
        step_names = [
            'step1_rqa_calculation',
            'step2_data_merging',
            'step3_feature_enrichment',
            'step4_statistical_analysis',
            'step5_visualization'
        ]

        if 'steps_completed' not in metadata:
            metadata['steps_completed'] = {}

        step_name = step_names[step - 1]
        metadata['steps_completed'][step_name] = {
            'completed': True,
            'timestamp': datetime.now().isoformat(),
            **data
        }

        # 保存元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"保存元数据: {metadata_file}")

    def scan_calibrated_files(self, group: str) -> List[Path]:
        """
        扫描校准后的CSV文件

        Args:
            group: 分组名称 ('control', 'mci', 'ad')

        Returns:
            文件路径列表
        """
        group_dir = self.processed_dir / group

        if not group_dir.exists():
            logger.warning(f"分组目录不存在: {group_dir}")
            return []

        # 查找所有 *_calibrated.csv 文件
        csv_files = list(group_dir.glob('*_calibrated.csv'))

        logger.info(f"扫描到 {len(csv_files)} 个文件: {group}")

        return csv_files

    def step1_rqa_calculation(self, params: Dict, groups: List[str]) -> Dict:
        """
        Step 1: RQA计算

        对所有受试者的所有任务进行RQA计算

        Args:
            params: RQA参数
            groups: 分组列表 ['control', 'mci', 'ad']

        Returns:
            {
                'success': True,
                'total_files_processed': int,
                'files_failed': int,
                'output_files': List[str]
            }
        """
        try:
            logger.info(f"开始Step 1: RQA计算, 参数={params}")

            results = {group: [] for group in groups}
            total_processed = 0
            total_failed = 0

            for group in groups:
                # 扫描文件
                csv_files = self.scan_calibrated_files(group)

                logger.info(f"处理 {group} 组: {len(csv_files)} 个文件")

                # 处理每个文件
                for csv_file in csv_files:
                    try:
                        # 提取subject_id和task_id
                        filename = csv_file.stem  # 去掉.csv后缀
                        # 格式: control_legacy_1_q1_calibrated
                        parts = filename.replace('_calibrated', '').split('_')

                        if len(parts) >= 2:
                            # 重组subject_id (去掉最后的task_id)
                            task_id = parts[-1]  # q1, q2, etc.
                            subject_id = '_'.join(parts[:-1])  # control_legacy_1
                        else:
                            logger.warning(f"无法解析文件名: {filename}")
                            continue

                        # RQA分析
                        rqa_result = self.analyzer.analyze_single_file(str(csv_file), params)

                        # 添加到结果
                        result_row = {
                            'subject_id': subject_id,
                            'task_id': task_id,
                            **rqa_result
                        }
                        results[group].append(result_row)
                        total_processed += 1

                    except Exception as e:
                        logger.error(f"处理文件失败: {csv_file} - {e}")
                        total_failed += 1

                # 保存该组结果
                df = pd.DataFrame(results[group])
                step1_dir = self.get_step_directory(params, 'step1_rqa_calculation')
                output_file = step1_dir / f'{group}_rqa_results.csv'
                df.to_csv(output_file, index=False)

                logger.info(f"保存 {group} 组结果: {output_file}, {len(results[group])} 条记录")

            # 保存元数据
            self.save_param_metadata(params, 1, {
                'files_processed': total_processed,
                'files_failed': total_failed
            })

            return {
                'success': True,
                'total_files_processed': total_processed,
                'files_failed': total_failed,
                'output_files': [
                    str(self.get_step_directory(params, 'step1_rqa_calculation') / f'{g}_rqa_results.csv')
                    for g in groups
                ]
            }

        except Exception as e:
            logger.error(f"Step 1 执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def step2_data_merging(self, params: Dict, groups: List[str]) -> Dict:
        """
        Step 2: 数据合并

        合并三组数据，添加分组标签

        Args:
            params: RQA参数
            groups: 分组列表

        Returns:
            {
                'success': True,
                'total_records': int,
                'output_file': str
            }
        """
        try:
            logger.info(f"开始Step 2: 数据合并, 参数={params}")

            step1_dir = self.get_step_directory(params, 'step1_rqa_calculation')

            # 读取三组数据
            all_data = []
            for group in groups:
                csv_file = step1_dir / f'{group}_rqa_results.csv'

                if not csv_file.exists():
                    logger.warning(f"文件不存在: {csv_file}")
                    continue

                df = pd.read_csv(csv_file)
                df['Group'] = group.capitalize()  # Control, Mci, Ad
                df['ID'] = df['subject_id'] + '_' + df['task_id']

                all_data.append(df)

            if not all_data:
                raise ValueError("没有找到Step 1的输出文件")

            # 合并数据
            merged = pd.concat(all_data, ignore_index=True)

            # 调整列顺序
            cols = ['ID', 'Group', 'subject_id', 'task_id',
                   'RR-1D-x', 'DET-1D-x', 'ENT-1D-x',
                   'RR-2D-xy', 'DET-2D-xy', 'ENT-2D-xy']
            merged = merged[cols]

            # 保存
            step2_dir = self.get_step_directory(params, 'step2_data_merging')
            output_file = step2_dir / 'merged_data.csv'
            merged.to_csv(output_file, index=False)

            logger.info(f"数据合并完成: {output_file}, {len(merged)} 条记录")

            # 保存元数据
            self.save_param_metadata(params, 2, {
                'total_records': len(merged)
            })

            return {
                'success': True,
                'total_records': len(merged),
                'output_file': str(output_file)
            }

        except Exception as e:
            logger.error(f"Step 2 执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_param_history(self) -> List[Dict]:
        """
        获取所有参数历史记录

        Returns:
            历史记录列表
        """
        history = []

        if not self.results_dir.exists():
            return history

        for param_folder in self.results_dir.iterdir():
            if not param_folder.is_dir():
                continue

            metadata_file = param_folder / 'metadata.json'

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    # 计算完成步骤数
                    completed_steps = sum(
                        1 for i in range(1, 6)
                        if metadata.get('steps_completed', {}).get(
                            f'step{i}_' + ['rqa_calculation', 'data_merging', 'feature_enrichment',
                                          'statistical_analysis', 'visualization'][i-1], {}
                        ).get('completed', False)
                    )

                    history.append({
                        'signature': metadata.get('signature', param_folder.name),
                        'params': metadata.get('parameters', {}),
                        'completed_steps': completed_steps,
                        'progress': (completed_steps / 5) * 100,
                        'last_updated': metadata.get('last_updated', '')
                    })

                except Exception as e:
                    logger.error(f"读取元数据失败: {metadata_file} - {e}")

        # 按最后更新时间排序
        history.sort(key=lambda x: x.get('last_updated', ''), reverse=True)

        return history

    def step3_feature_enrichment(self, params: Dict) -> Dict:
        """
        Step 3: 特征增强

        整合Module04事件分析数据和受试者MMSE信息

        Args:
            params: RQA参数

        Returns:
            {
                'success': True,
                'features_added': int,
                'output_file': str
            }
        """
        try:
            logger.info(f"开始Step 3: 特征增强, 参数={params}")

            step2_dir = self.get_step_directory(params, 'step2_data_merging')
            merged_file = step2_dir / 'merged_data.csv'

            if not merged_file.exists():
                raise ValueError(f"Step 2输出文件不存在: {merged_file}")

            merged = pd.read_csv(merged_file)

            # 1. 尝试加载Module04事件特征（如果有缓存）
            try:
                m04_cache = self.data_root / '04_features' / 'cache' / 'latest_analysis.json'
                if m04_cache.exists():
                    with open(m04_cache, 'r', encoding='utf-8') as f:
                        m04_data = json.load(f)

                    if 'features_result' in m04_data and m04_data['features_result'].get('success'):
                        m04_features = pd.DataFrame(m04_data['features_result']['features'])

                        # 合并事件特征
                        # Module04的key是subject_id_task_id，需要创建ID列匹配
                        if 'subject_id' in m04_features.columns and 'task_id' in m04_features.columns:
                            m04_features['ID'] = m04_features['subject_id'] + '_' + m04_features['task_id']

                            # 选择要合并的列
                            event_cols = ['ID', 'fixation_count', 'saccade_count',
                                        'avg_fixation_duration', 'avg_saccade_amplitude']
                            available_cols = [col for col in event_cols if col in m04_features.columns]

                            if len(available_cols) > 1:  # 至少有ID和一个特征列
                                merged = merged.merge(
                                    m04_features[available_cols],
                                    on='ID',
                                    how='left'
                                )
                                logger.info(f"成功整合Module04事件特征: {len(available_cols)-1} 列")
            except Exception as e:
                logger.warning(f"加载Module04特征失败，跳过: {e}")

            # 2. 加载MMSE数据
            try:
                # 使用SubjectManager加载受试者信息
                subjects_data = []

                for _, row in merged.iterrows():
                    subject_id = row['subject_id']

                    # 从SubjectManager获取受试者信息
                    subject_info = self.subject_manager.get_subject(subject_id)

                    if subject_info:
                        subjects_data.append({
                            'subject_id': subject_id,
                            'age': subject_info.get('age'),
                            'education_level': subject_info.get('education_level'),
                            'mmse_total_score': subject_info.get('mmse_total_score'),
                            'mmse_orientation': subject_info.get('mmse_orientation'),
                            'mmse_memory': subject_info.get('mmse_memory'),
                            'mmse_attention': subject_info.get('mmse_attention'),
                            'mmse_language': subject_info.get('mmse_language'),
                            'mmse_visuospatial': subject_info.get('mmse_visuospatial')
                        })

                if subjects_data:
                    subjects_df = pd.DataFrame(subjects_data)
                    merged = merged.merge(subjects_df, on='subject_id', how='left')
                    logger.info(f"成功整合MMSE数据: {len(subjects_df)} 个受试者")

            except Exception as e:
                logger.warning(f"加载MMSE数据失败，跳过: {e}")

            # 3. 计算衍生特征
            # RQA复杂度指标
            merged['rqa_complexity_1d'] = merged['DET-1D-x'] * merged['ENT-1D-x']
            merged['rqa_complexity_2d'] = merged['DET-2D-xy'] * merged['ENT-2D-xy']

            # RQA差异指标（1D vs 2D）
            merged['rqa_diff_rr'] = merged['RR-2D-xy'] - merged['RR-1D-x']
            merged['rqa_diff_det'] = merged['DET-2D-xy'] - merged['DET-1D-x']
            merged['rqa_diff_ent'] = merged['ENT-2D-xy'] - merged['ENT-1D-x']

            # 保存增强后的特征
            step3_dir = self.get_step_directory(params, 'step3_feature_enrichment')
            output_file = step3_dir / 'enriched_features.csv'
            merged.to_csv(output_file, index=False)

            features_added = len(merged.columns) - 10  # 减去原始10列
            logger.info(f"特征增强完成: {output_file}, 新增 {features_added} 个特征")

            # 保存元数据
            self.save_param_metadata(params, 3, {
                'features_added': features_added,
                'total_features': len(merged.columns)
            })

            return {
                'success': True,
                'features_added': features_added,
                'output_file': str(output_file)
            }

        except Exception as e:
            logger.error(f"Step 3 执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def step4_statistical_analysis(self, params: Dict) -> Dict:
        """
        Step 4: 统计分析

        执行描述性统计和组间比较（ANOVA）

        Args:
            params: RQA参数

        Returns:
            {
                'success': True,
                'significant_features': int,
                'output_files': List[str]
            }
        """
        try:
            logger.info(f"开始Step 4: 统计分析, 参数={params}")

            step3_dir = self.get_step_directory(params, 'step3_feature_enrichment')
            enriched_file = step3_dir / 'enriched_features.csv'

            if not enriched_file.exists():
                raise ValueError(f"Step 3输出文件不存在: {enriched_file}")

            data = pd.read_csv(enriched_file)

            # 1. 描述性统计
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            desc_stats = data.groupby('Group')[numeric_cols].agg(['mean', 'std', 'min', 'max', 'count'])

            # 2. 组间比较（ANOVA）
            from scipy.stats import f_oneway

            comparison_results = []

            groups_list = data['Group'].unique()

            for col in numeric_cols:
                try:
                    # 提取各组数据
                    group_data = []
                    for group in groups_list:
                        vals = data[data['Group'] == group][col].dropna()
                        if len(vals) > 0:
                            group_data.append(vals)

                    # 至少需要2组数据
                    if len(group_data) >= 2:
                        f_stat, p_value = f_oneway(*group_data)

                        comparison_results.append({
                            'feature': col,
                            'f_statistic': f_stat,
                            'p_value': p_value,
                            'significant': p_value < 0.05,
                            'significance_level': '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'
                        })

                except Exception as e:
                    logger.warning(f"特征 {col} 的ANOVA计算失败: {e}")

            # 3. 相关性矩阵
            corr_matrix = data[numeric_cols].corr()

            # 保存结果
            step4_dir = self.get_step_directory(params, 'step4_statistical_analysis')

            desc_stats.to_csv(step4_dir / 'descriptive_stats.csv')
            pd.DataFrame(comparison_results).to_csv(step4_dir / 'group_comparison.csv', index=False)
            corr_matrix.to_csv(step4_dir / 'correlation_matrix.csv')

            significant_count = sum(1 for r in comparison_results if r['significant'])

            logger.info(f"统计分析完成: {significant_count}/{len(comparison_results)} 个特征显著")

            # 保存元数据
            self.save_param_metadata(params, 4, {
                'significant_features': significant_count,
                'total_features_tested': len(comparison_results)
            })

            return {
                'success': True,
                'significant_features': significant_count,
                'output_files': [
                    str(step4_dir / 'descriptive_stats.csv'),
                    str(step4_dir / 'group_comparison.csv'),
                    str(step4_dir / 'correlation_matrix.csv')
                ]
            }

        except Exception as e:
            logger.error(f"Step 4 执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def step5_visualization(self, params: Dict, max_samples: int = 10) -> Dict:
        """
        Step 5: 可视化

        生成统计图表

        Args:
            params: RQA参数
            max_samples: 递归图最大抽样数量

        Returns:
            {
                'success': True,
                'plots_generated': int,
                'output_dir': str
            }
        """
        try:
            logger.info(f"开始Step 5: 可视化, 参数={params}")

            import matplotlib.pyplot as plt
            import seaborn as sns

            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            step3_dir = self.get_step_directory(params, 'step3_feature_enrichment')
            step4_dir = self.get_step_directory(params, 'step4_statistical_analysis')
            step5_dir = self.get_step_directory(params, 'step5_visualization')

            enriched_file = step3_dir / 'enriched_features.csv'
            comparison_file = step4_dir / 'group_comparison.csv'
            corr_file = step4_dir / 'correlation_matrix.csv'

            if not enriched_file.exists():
                raise ValueError(f"特征文件不存在: {enriched_file}")

            data = pd.read_csv(enriched_file)
            plots_count = 0

            # 创建子目录
            stat_plots_dir = step5_dir / 'statistical_plots'
            stat_plots_dir.mkdir(parents=True, exist_ok=True)

            # 1. 组间比较箱线图（RQA核心指标）
            rqa_features = ['RR-1D-x', 'DET-1D-x', 'ENT-1D-x',
                           'RR-2D-xy', 'DET-2D-xy', 'ENT-2D-xy']

            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            axes = axes.flatten()

            for idx, feature in enumerate(rqa_features):
                if feature in data.columns:
                    sns.boxplot(data=data, x='Group', y=feature, ax=axes[idx])
                    axes[idx].set_title(f'{feature} by Group', fontsize=12, fontweight='bold')
                    axes[idx].set_xlabel('Group', fontsize=10)
                    axes[idx].set_ylabel(feature, fontsize=10)

            plt.tight_layout()
            plt.savefig(stat_plots_dir / 'rqa_metrics_boxplot.png', dpi=150, bbox_inches='tight')
            plt.close()
            plots_count += 1

            # 2. 相关性热力图
            if corr_file.exists():
                corr_matrix = pd.read_csv(corr_file, index_col=0)

                # 只显示RQA相关特征
                rqa_cols = [col for col in corr_matrix.columns if 'RR' in col or 'DET' in col or 'ENT' in col or 'rqa' in col.lower()]
                if len(rqa_cols) > 1:
                    corr_subset = corr_matrix.loc[rqa_cols, rqa_cols]

                    fig, ax = plt.subplots(figsize=(12, 10))
                    sns.heatmap(corr_subset, annot=True, fmt='.2f', cmap='coolwarm',
                               center=0, vmin=-1, vmax=1, ax=ax)
                    ax.set_title('RQA Features Correlation Matrix', fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    plt.savefig(stat_plots_dir / 'correlation_heatmap.png', dpi=150, bbox_inches='tight')
                    plt.close()
                    plots_count += 1

            # 3. 显著性特征柱状图
            if comparison_file.exists() and comparison_file.stat().st_size > 0:
                try:
                    comparison = pd.read_csv(comparison_file)
                    if len(comparison) == 0:
                        logger.warning("组间比较结果为空，跳过显著性特征图")
                    else:
                        significant = comparison[comparison['significant'] == True].sort_values('p_value')

                        if len(significant) > 0:
                            top_n = min(15, len(significant))
                            top_significant = significant.head(top_n)

                            fig, ax = plt.subplots(figsize=(12, 8))
                            bars = ax.barh(range(len(top_significant)), -np.log10(top_significant['p_value']))
                            ax.set_yticks(range(len(top_significant)))
                            ax.set_yticklabels(top_significant['feature'])
                            ax.set_xlabel('-log10(p-value)', fontsize=12)
                            ax.set_title('Top Significant Features (ANOVA)', fontsize=14, fontweight='bold')
                            ax.axvline(x=-np.log10(0.05), color='r', linestyle='--', label='p=0.05')
                            ax.legend()
                            plt.tight_layout()
                            plt.savefig(stat_plots_dir / 'significant_features.png', dpi=150, bbox_inches='tight')
                            plt.close()
                            plots_count += 1
                except Exception as e:
                    logger.warning(f"生成显著性特征图失败: {e}")

            # 4. 复杂度指标小提琴图
            if 'rqa_complexity_1d' in data.columns and 'rqa_complexity_2d' in data.columns:
                fig, axes = plt.subplots(1, 2, figsize=(14, 6))

                sns.violinplot(data=data, x='Group', y='rqa_complexity_1d', ax=axes[0])
                axes[0].set_title('RQA Complexity (1D)', fontsize=12, fontweight='bold')

                sns.violinplot(data=data, x='Group', y='rqa_complexity_2d', ax=axes[1])
                axes[1].set_title('RQA Complexity (2D)', fontsize=12, fontweight='bold')

                plt.tight_layout()
                plt.savefig(stat_plots_dir / 'complexity_violin.png', dpi=150, bbox_inches='tight')
                plt.close()
                plots_count += 1

            logger.info(f"可视化完成: 生成 {plots_count} 个图表")

            # 保存元数据
            self.save_param_metadata(params, 5, {
                'plots_generated': plots_count
            })

            return {
                'success': True,
                'plots_generated': plots_count,
                'output_dir': str(step5_dir)
            }

        except Exception as e:
            logger.error(f"Step 5 执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
