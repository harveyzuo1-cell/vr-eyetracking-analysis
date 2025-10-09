"""
个体分析器 - 基于RQA的个体层面分析

功能:
1. 个体RQA轨迹分析（同一人在不同任务的RQA变化）
2. 个体vs组平均对比（偏离度分析）
3. 个体诊断风险评估
4. 个体复发图生成

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


class IndividualAnalyzer:
    """个体RQA分析器"""

    def __init__(self, results_dir: str):
        """
        初始化个体分析器

        Args:
            results_dir: RQA结果目录路径
        """
        self.results_dir = Path(results_dir)

    def get_individual_profile(
        self,
        subject_id: str,
        params: Dict,
        tasks: List[str] = ['q1', 'q2', 'q3', 'q4', 'q5']
    ) -> Dict:
        """
        获取个体的完整RQA档案

        Args:
            subject_id: 受试者ID (如 'control_legacy_1')
            params: RQA参数字典
            tasks: 任务列表

        Returns:
            个体档案字典
        """
        logger.info(f"获取个体档案: {subject_id}, 参数: {params}")

        # 1. 读取enriched_features.csv
        param_dir = self._get_param_dir(params)
        features_file = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'

        if not features_file.exists():
            raise FileNotFoundError(f"特征文件不存在: {features_file}")

        df = pd.read_csv(features_file)

        # 2. 筛选该个体的数据
        individual_df = df[df['subject_id'] == subject_id].copy()

        if len(individual_df) == 0:
            raise ValueError(f"未找到受试者: {subject_id}")

        # 提取组别信息
        group = individual_df['group'].iloc[0] if 'group' in individual_df.columns else 'unknown'

        # 3. 按任务排序
        individual_df['task_order'] = individual_df['task_id'].map({
            'q1': 1, 'q2': 2, 'q3': 3, 'q4': 4, 'q5': 5
        })
        individual_df = individual_df.sort_values('task_order')

        # 4. 提取RQA特征
        rqa_features = [col for col in df.columns if any(
            col.startswith(prefix) for prefix in ['x_', 'y_', 'combined_']
        )]

        # 5. 构建任务轨迹数据
        task_trajectories = {}
        for feature in rqa_features:
            task_trajectories[feature] = []
            for task in tasks:
                task_data = individual_df[individual_df['task_id'] == task]
                if len(task_data) > 0:
                    value = task_data[feature].iloc[0]
                    task_trajectories[feature].append({
                        'task': task,
                        'value': float(value) if pd.notna(value) else None
                    })

        # 6. 计算个体统计
        individual_stats = {}
        for feature in rqa_features:
            values = individual_df[feature].dropna()
            if len(values) > 0:
                individual_stats[feature] = {
                    'mean': float(values.mean()),
                    'std': float(values.std()),
                    'min': float(values.min()),
                    'max': float(values.max()),
                    'range': float(values.max() - values.min())
                }

        return {
            'subject_id': subject_id,
            'group': group,
            'params': params,
            'task_count': len(individual_df),
            'task_trajectories': task_trajectories,
            'individual_stats': individual_stats,
            'raw_data': individual_df[['task_id'] + rqa_features].to_dict('records')
        }

    def compare_to_group(
        self,
        subject_id: str,
        params: Dict
    ) -> Dict:
        """
        对比个体与组平均水平

        Args:
            subject_id: 受试者ID
            params: RQA参数

        Returns:
            对比结果
        """
        logger.info(f"对比个体与组平均: {subject_id}")

        # 1. 获取个体档案
        individual_profile = self.get_individual_profile(subject_id, params)
        group = individual_profile['group']

        # 2. 读取全组数据
        param_dir = self._get_param_dir(params)
        features_file = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'
        df = pd.read_csv(features_file)

        # 3. 筛选同组数据
        group_df = df[df['group'] == group].copy()

        # 4. 计算组平均和标准差
        rqa_features = [col for col in df.columns if any(
            col.startswith(prefix) for prefix in ['x_', 'y_', 'combined_']
        )]

        comparison_results = []

        for feature in rqa_features:
            # 个体值
            individual_values = individual_profile['individual_stats'].get(feature, {})
            individual_mean = individual_values.get('mean')

            if individual_mean is None:
                continue

            # 组统计
            group_values = group_df[feature].dropna()
            group_mean = float(group_values.mean())
            group_std = float(group_values.std())

            # 计算Z分数（偏离度）
            z_score = (individual_mean - group_mean) / group_std if group_std > 0 else 0

            # 判断是否异常（|Z| > 2）
            is_outlier = abs(z_score) > 2

            comparison_results.append({
                'feature': feature,
                'individual_mean': individual_mean,
                'group_mean': group_mean,
                'group_std': group_std,
                'z_score': float(z_score),
                'deviation_percentage': float((individual_mean - group_mean) / group_mean * 100) if group_mean != 0 else 0,
                'is_outlier': is_outlier
            })

        # 5. 统计异常特征数
        outlier_count = sum(1 for r in comparison_results if r['is_outlier'])

        return {
            'subject_id': subject_id,
            'group': group,
            'comparison': comparison_results,
            'outlier_count': outlier_count,
            'total_features': len(comparison_results),
            'outlier_ratio': outlier_count / len(comparison_results) if len(comparison_results) > 0 else 0
        }

    def assess_cognitive_risk(
        self,
        subject_id: str,
        params: Dict
    ) -> Dict:
        """
        基于RQA特征评估认知风险

        Args:
            subject_id: 受试者ID
            params: RQA参数

        Returns:
            风险评估结果
        """
        logger.info(f"评估认知风险: {subject_id}")

        # 1. 获取个体vs组对比
        comparison = self.compare_to_group(subject_id, params)
        group = comparison['group']

        # 2. 读取全量数据用于对比
        param_dir = self._get_param_dir(params)
        features_file = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'
        df = pd.read_csv(features_file)

        # 3. 获取个体RQA均值
        individual_profile = self.get_individual_profile(subject_id, params)
        individual_stats = individual_profile['individual_stats']

        # 4. 定义风险因子（基于临床研究的RQA特征）
        risk_factors = []

        # 风险因子1: RR（递归率）过低
        if 'combined_RR' in individual_stats:
            rr = individual_stats['combined_RR']['mean']
            # 获取control组的RR平均值作为基线
            control_rr = df[df['group'] == 'control']['combined_RR'].mean()

            if rr < control_rr * 0.7:  # 低于正常70%
                risk_factors.append({
                    'factor': 'RR过低',
                    'description': '递归率显著低于正常水平，提示注视模式简化',
                    'severity': 'high'
                })
            elif rr < control_rr * 0.85:
                risk_factors.append({
                    'factor': 'RR偏低',
                    'description': '递归率略低于正常水平',
                    'severity': 'medium'
                })

        # 风险因子2: DET（确定性）过低
        if 'combined_DET' in individual_stats:
            det = individual_stats['combined_DET']['mean']
            control_det = df[df['group'] == 'control']['combined_DET'].mean()

            if det < control_det * 0.7:
                risk_factors.append({
                    'factor': 'DET过低',
                    'description': '确定性显著降低，提示扫视模式不规律',
                    'severity': 'high'
                })

        # 风险因子3: ENT（熵）过低
        if 'combined_ENT' in individual_stats:
            ent = individual_stats['combined_ENT']['mean']
            control_ent = df[df['group'] == 'control']['combined_ENT'].mean()

            if ent < control_ent * 0.7:
                risk_factors.append({
                    'factor': 'ENT过低',
                    'description': '熵值过低，提示视觉探索策略简化',
                    'severity': 'high'
                })

        # 风险因子4: 异常特征比例过高
        if comparison['outlier_ratio'] > 0.3:
            risk_factors.append({
                'factor': f'异常特征过多({comparison["outlier_count"]}个)',
                'description': f'{comparison["outlier_ratio"]*100:.1f}% 的RQA特征显著偏离组平均',
                'severity': 'high' if comparison['outlier_ratio'] > 0.5 else 'medium'
            })

        # 5. 计算风险评分（0-100）
        risk_score = 0

        # 基础分：异常特征比例
        risk_score += comparison['outlier_ratio'] * 40

        # 附加分：高严重性风险因子
        high_severity_count = sum(1 for rf in risk_factors if rf['severity'] == 'high')
        risk_score += high_severity_count * 15

        # 附加分：中严重性风险因子
        medium_severity_count = sum(1 for rf in risk_factors if rf['severity'] == 'medium')
        risk_score += medium_severity_count * 10

        risk_score = min(risk_score, 100)  # 上限100

        # 6. 风险等级分类
        if risk_score >= 70:
            risk_level = 'high'
            risk_label = '高风险'
            recommendation = '强烈建议进行神经心理学详细评估，可能存在认知功能障碍'
        elif risk_score >= 40:
            risk_level = 'medium'
            risk_label = '中风险'
            recommendation = '建议定期随访监测，关注认知功能变化'
        else:
            risk_level = 'low'
            risk_label = '低风险'
            recommendation = '眼动模式正常，继续保持健康生活方式'

        return {
            'subject_id': subject_id,
            'group': group,
            'risk_score': float(risk_score),
            'risk_level': risk_level,
            'risk_label': risk_label,
            'risk_factors': risk_factors,
            'recommendation': recommendation,
            'outlier_count': comparison['outlier_count'],
            'total_features': comparison['total_features']
        }

    def get_task_progression_analysis(
        self,
        subject_id: str,
        params: Dict
    ) -> Dict:
        """
        分析个体在任务进程中的RQA变化趋势

        Args:
            subject_id: 受试者ID
            params: RQA参数

        Returns:
            任务进程分析结果
        """
        logger.info(f"分析任务进程: {subject_id}")

        # 1. 获取个体档案
        profile = self.get_individual_profile(subject_id, params)

        # 2. 分析关键特征的变化趋势
        key_features = ['combined_RR', 'combined_DET', 'combined_ENT']

        trends = {}
        for feature in key_features:
            if feature not in profile['task_trajectories']:
                continue

            trajectory = profile['task_trajectories'][feature]
            values = [t['value'] for t in trajectory if t['value'] is not None]

            if len(values) < 2:
                continue

            # 计算线性趋势（斜率）
            x = np.arange(len(values))
            y = np.array(values)

            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

                # 判断趋势方向
                if p_value < 0.05:
                    if slope > 0:
                        trend_direction = 'increasing'
                        trend_label = '上升'
                    else:
                        trend_direction = 'decreasing'
                        trend_label = '下降'
                else:
                    trend_direction = 'stable'
                    trend_label = '稳定'

                trends[feature] = {
                    'slope': float(slope),
                    'r_squared': float(r_value ** 2),
                    'p_value': float(p_value),
                    'direction': trend_direction,
                    'label': trend_label,
                    'values': values
                }

            except Exception as e:
                logger.warning(f"计算趋势失败 ({feature}): {e}")
                continue

        # 3. 综合评价
        interpretation = self._interpret_task_progression(trends, profile['group'])

        return {
            'subject_id': subject_id,
            'group': profile['group'],
            'trends': trends,
            'interpretation': interpretation
        }

    def _interpret_task_progression(self, trends: Dict, group: str) -> str:
        """解释任务进程趋势"""
        interpretations = []

        if 'combined_RR' in trends:
            rr_trend = trends['combined_RR']
            if rr_trend['direction'] == 'decreasing' and rr_trend['p_value'] < 0.05:
                interpretations.append('随任务进行，注视模式的递归性降低，提示视觉探索策略发生变化')
            elif rr_trend['direction'] == 'stable':
                interpretations.append('注视模式的递归性保持稳定')

        if 'combined_DET' in trends:
            det_trend = trends['combined_DET']
            if det_trend['direction'] == 'decreasing' and det_trend['p_value'] < 0.05:
                interpretations.append('扫视确定性下降，可能反映任务难度增加或疲劳效应')

        if 'combined_ENT' in trends:
            ent_trend = trends['combined_ENT']
            if ent_trend['direction'] == 'decreasing' and ent_trend['p_value'] < 0.05:
                interpretations.append('视觉探索复杂度降低，提示策略简化')

        if not interpretations:
            interpretations.append('各项RQA指标在任务进程中保持相对稳定')

        return ' | '.join(interpretations)

    def _get_param_dir(self, params: Dict) -> Path:
        """获取参数对应的目录路径"""
        dirname = f"m{params['m']}_tau{params['tau']}_eps{params['eps']}_lmin{params['lmin']}"
        return self.results_dir / dirname

    def get_all_subjects(self, params: Dict) -> List[Dict]:
        """
        获取所有受试者列表

        Args:
            params: RQA参数

        Returns:
            受试者列表
        """
        param_dir = self._get_param_dir(params)
        features_file = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'

        if not features_file.exists():
            return []

        df = pd.read_csv(features_file)

        subjects = []
        for subject_id in df['subject_id'].unique():
            group = df[df['subject_id'] == subject_id]['group'].iloc[0]
            subjects.append({
                'subject_id': subject_id,
                'group': group
            })

        return sorted(subjects, key=lambda x: (x['group'], x['subject_id']))


def main():
    """测试函数"""
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 结果目录
    results_dir = r"c:\Users\asino\Downloads\az - 副本 (11)\new_project\data\05_rqa_analysis\results"

    if not os.path.exists(results_dir):
        logger.error(f"结果目录不存在: {results_dir}")
        return

    # 创建分析器
    analyzer = IndividualAnalyzer(results_dir)

    # 测试参数
    test_params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}

    # 获取所有受试者
    print("\n--- 获取所有受试者 ---")
    subjects = analyzer.get_all_subjects(test_params)
    print(f"共 {len(subjects)} 名受试者")
    print(subjects[:5])  # 打印前5个

    # 测试个体档案
    test_subject = subjects[0]['subject_id'] if subjects else 'control_legacy_1'

    print(f"\n--- 个体档案分析: {test_subject} ---")
    try:
        profile = analyzer.get_individual_profile(test_subject, test_params)
        print(f"组别: {profile['group']}")
        print(f"任务数: {profile['task_count']}")
        print(f"RQA特征数: {len(profile['individual_stats'])}")

    except Exception as e:
        print(f"分析失败: {e}")

    # 测试个体vs组对比
    print(f"\n--- 个体vs组对比 ---")
    try:
        comparison = analyzer.compare_to_group(test_subject, test_params)
        print(f"异常特征数: {comparison['outlier_count']}/{comparison['total_features']}")
        print(f"异常比例: {comparison['outlier_ratio']*100:.1f}%")

    except Exception as e:
        print(f"对比失败: {e}")

    # 测试风险评估
    print(f"\n--- 认知风险评估 ---")
    try:
        risk = analyzer.assess_cognitive_risk(test_subject, test_params)
        print(f"风险评分: {risk['risk_score']:.1f}")
        print(f"风险等级: {risk['risk_label']}")
        print(f"建议: {risk['recommendation']}")
        print(f"风险因子数: {len(risk['risk_factors'])}")

    except Exception as e:
        print(f"评估失败: {e}")


if __name__ == '__main__':
    main()
