#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据范围分析器 - 分析各指标的数值范围以设计归一化方案
"""

import pandas as pd
import numpy as np
import os
import glob
from typing import Dict, List, Tuple
import json

class DataRangeAnalyzer:
    """数据范围分析器"""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = data_root
        self.stats = {}
        
    def analyze_game_duration(self) -> Dict:
        """分析游戏总时长"""
        print("📊 分析游戏总时长...")
        
        durations = []
        groups = ['ad_calibrated', 'mci_calibrated', 'control_calibrated']
        
        for group in groups:
            group_path = os.path.join(self.data_root, group)
            if not os.path.exists(group_path):
                continue
                
            # 遍历所有组文件夹
            for group_folder in os.listdir(group_path):
                folder_path = os.path.join(group_path, group_folder)
                if not os.path.isdir(folder_path):
                    continue
                    
                # 遍历每个文件
                for file in os.listdir(folder_path):
                    if file.endswith('_preprocessed_calibrated.csv'):
                        file_path = os.path.join(folder_path, file)
                        try:
                            df = pd.read_csv(file_path)
                            if 'milliseconds' in df.columns and len(df) > 0:
                                duration_ms = df['milliseconds'].max() - df['milliseconds'].min()
                                duration_s = duration_ms / 1000.0
                                durations.append(duration_s)
                                print(f"  {file}: {duration_s:.2f}s")
                        except Exception as e:
                            print(f"  ❌ 无法读取 {file}: {e}")
        
        if durations:
            stats = {
                'count': len(durations),
                'min': min(durations),
                'max': max(durations), 
                'mean': np.mean(durations),
                'std': np.std(durations),
                'median': np.median(durations),
                'q25': np.percentile(durations, 25),
                'q75': np.percentile(durations, 75)
            }
        else:
            stats = {'error': '未找到有效的时长数据'}
            
        self.stats['game_duration'] = stats
        return stats
    
    def analyze_roi_fixation_time(self) -> Dict:
        """分析ROI注视时间"""
        print("📊 分析ROI注视时间...")
        
        roi_file = os.path.join(self.data_root, 'event_analysis_results', 'All_ROI_Summary.csv')
        if not os.path.exists(roi_file):
            return {'error': f'文件不存在: {roi_file}'}
        
        try:
            df = pd.read_csv(roi_file)
            
            # 分析FixTime列
            fix_times = df['FixTime'].dropna()
            
            # 按任务分组分析
            task_stats = {}
            for i in range(1, 6):  # Q1-Q5
                task_data = df[df['ADQ_ID'].str.contains(f'q{i}', na=False)]['FixTime'].dropna()
                if len(task_data) > 0:
                    task_stats[f'Q{i}'] = {
                        'count': len(task_data),
                        'min': task_data.min(),
                        'max': task_data.max(),
                        'mean': task_data.mean(),
                        'std': task_data.std(),
                        'median': task_data.median()
                    }
            
            # 按ROI类型分析
            roi_type_stats = {}
            for roi_type in ['KW', 'INST', 'BG']:
                roi_data = df[df['ROI'].str.contains(roi_type, na=False)]['FixTime'].dropna()
                if len(roi_data) > 0:
                    roi_type_stats[roi_type] = {
                        'count': len(roi_data),
                        'min': roi_data.min(),
                        'max': roi_data.max(),
                        'mean': roi_data.mean(),
                        'std': roi_data.std(),
                        'median': roi_data.median()
                    }
            
            overall_stats = {
                'overall': {
                    'count': len(fix_times),
                    'min': fix_times.min(),
                    'max': fix_times.max(),
                    'mean': fix_times.mean(),
                    'std': fix_times.std(),
                    'median': fix_times.median(),
                    'q25': np.percentile(fix_times, 25),
                    'q75': np.percentile(fix_times, 75),
                    'q95': np.percentile(fix_times, 95),
                    'q99': np.percentile(fix_times, 99)
                },
                'by_task': task_stats,
                'by_roi_type': roi_type_stats
            }
            
        except Exception as e:
            overall_stats = {'error': f'分析ROI数据失败: {e}'}
        
        self.stats['roi_fixation_time'] = overall_stats
        return overall_stats
    
    def analyze_rqa_metrics(self) -> Dict:
        """分析RQA指标"""
        print("📊 分析RQA指标...")
        
        rqa_path = os.path.join(self.data_root, 'rqa_pipeline_results', 'm2_tau1_eps0.055_lmin2', 'step1_rqa_calculation')
        if not os.path.exists(rqa_path):
            return {'error': f'RQA路径不存在: {rqa_path}'}
        
        rqa_metrics = ['RR-2D-xy', 'RR-1D-x', 'DET-2D-xy', 'DET-1D-x', 'ENT-2D-xy', 'ENT-1D-x']
        all_stats = {}
        
        # 读取所有RQA文件
        all_data = []
        for group in ['ad', 'control', 'mci']:
            file_path = os.path.join(rqa_path, f'RQA_1D2D_summary_{group}.csv')
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path)
                    df['group'] = group
                    all_data.append(df)
                except Exception as e:
                    print(f"  ❌ 无法读取 {file_path}: {e}")
        
        if not all_data:
            return {'error': '未找到有效的RQA数据'}
        
        # 合并所有数据
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 分析每个指标
        for metric in rqa_metrics:
            if metric in combined_df.columns:
                values = combined_df[metric].dropna()
                if len(values) > 0:
                    # 按任务分组
                    task_stats = {}
                    for q in range(1, 6):
                        task_data = combined_df[combined_df['q'] == q][metric].dropna()
                        if len(task_data) > 0:
                            task_stats[f'Q{q}'] = {
                                'count': len(task_data),
                                'min': task_data.min(),
                                'max': task_data.max(),
                                'mean': task_data.mean(),
                                'std': task_data.std(),
                                'median': task_data.median()
                            }
                    
                    # 按组分组
                    group_stats = {}
                    for group in ['ad', 'control', 'mci']:
                        group_data = combined_df[combined_df['group'] == group][metric].dropna()
                        if len(group_data) > 0:
                            group_stats[group] = {
                                'count': len(group_data),
                                'min': group_data.min(),
                                'max': group_data.max(),
                                'mean': group_data.mean(),
                                'std': group_data.std(),
                                'median': group_data.median()
                            }
                    
                    all_stats[metric] = {
                        'overall': {
                            'count': len(values),
                            'min': values.min(),
                            'max': values.max(),
                            'mean': values.mean(),
                            'std': values.std(),
                            'median': values.median(),
                            'q25': np.percentile(values, 25),
                            'q75': np.percentile(values, 75),
                            'q95': np.percentile(values, 95),
                            'q99': np.percentile(values, 99)
                        },
                        'by_task': task_stats,
                        'by_group': group_stats
                    }
        
        self.stats['rqa_metrics'] = all_stats
        return all_stats
    
    def calculate_roi_time_percentage(self) -> Dict:
        """计算ROI时间占比的理论范围"""
        print("📊 分析ROI时间占比...")
        
        # 基于已有数据估算
        roi_stats = self.stats.get('roi_fixation_time', {})
        duration_stats = self.stats.get('game_duration', {})
        
        if not roi_stats or not duration_stats:
            return {'error': '需要先分析ROI时间和游戏时长'}
        
        # ROI时间占比 = ROI注视时间 / 总游戏时间
        # 理论最小值：0% (没有注视ROI)
        # 理论最大值：100% (全程都在注视同一个ROI，不现实)
        # 实际最大值：通常不超过80-90%
        
        roi_min = roi_stats['overall']['min']
        roi_max = roi_stats['overall']['max']
        duration_min = duration_stats['min']
        duration_max = duration_stats['max']
        
        # 计算可能的占比范围
        percentage_stats = {
            'theoretical_min': 0.0,  # 0%
            'theoretical_max': 1.0,  # 100%
            'practical_min': roi_min / duration_max,  # 最小ROI时间 / 最大游戏时间
            'practical_max': roi_max / duration_min,  # 最大ROI时间 / 最小游戏时间
            'estimated_typical_max': 0.8,  # 典型最大值80%
            'note': 'ROI时间占比 = ROI注视时间 / 总游戏时间'
        }
        
        self.stats['roi_time_percentage'] = percentage_stats
        return percentage_stats
    
    def generate_normalization_config(self) -> Dict:
        """生成归一化配置"""
        print("📊 生成归一化配置...")
        
        config = {
            'version': '1.0',
            'description': '眼动数据归一化配置',
            'features': {}
        }
        
        # 游戏总时长归一化 (0-180秒 -> 0-1)
        config['features']['game_duration'] = {
            'name': '游戏总时长',
            'unit': '秒',
            'min_value': 0.0,
            'max_value': 180.0,  # 3分钟
            'normalization_method': 'min_max',
            'formula': '(value - min) / (max - min)',
            'note': '每个任务最长3分钟'
        }
        
        # ROI注视时间归一化
        roi_stats = self.stats.get('roi_fixation_time', {}).get('overall', {})
        config['features']['roi_fixation_time'] = {
            'name': 'ROI注视总时间',
            'unit': '秒',
            'min_value': 0.0,
            'max_value': roi_stats.get('q99', 25.0),  # 使用99分位数或默认25秒
            'normalization_method': 'min_max_clipped',
            'formula': 'clip((value - min) / (max - min), 0, 1)',
            'note': '超过最大值的截断为1'
        }
        
        # ROI时间占比归一化 (0-1，已经是比例)
        config['features']['roi_time_percentage'] = {
            'name': 'ROI时间占比',
            'unit': '比例',
            'min_value': 0.0,
            'max_value': 1.0,
            'normalization_method': 'direct',
            'formula': 'value',
            'note': '已经是0-1的比例，无需归一化'
        }
        
        # RQA指标归一化
        rqa_stats = self.stats.get('rqa_metrics', {})
        rqa_configs = {
            'RR-2D-xy': {'min': 0.0, 'max': 0.15, 'typical_range': '0.01-0.05'},
            'RR-1D-x': {'min': 0.0, 'max': 0.20, 'typical_range': '0.03-0.10'},
            'DET-2D-xy': {'min': 0.0, 'max': 1.0, 'typical_range': '0.60-0.95'},
            'DET-1D-x': {'min': 0.0, 'max': 1.0, 'typical_range': '0.60-0.90'},
            'ENT-2D-xy': {'min': 0.0, 'max': 5.0, 'typical_range': '1.0-3.5'},
            'ENT-1D-x': {'min': 0.0, 'max': 5.0, 'typical_range': '1.0-3.0'}
        }
        
        for metric, ranges in rqa_configs.items():
            actual_stats = rqa_stats.get(metric, {}).get('overall', {})
            config['features'][metric] = {
                'name': f'RQA指标-{metric}',
                'unit': '无量纲',
                'min_value': ranges['min'],
                'max_value': actual_stats.get('q99', ranges['max']),
                'normalization_method': 'min_max_clipped',
                'formula': 'clip((value - min) / (max - min), 0, 1)',
                'typical_range': ranges['typical_range'],
                'actual_range': f"{actual_stats.get('min', 'N/A'):.4f}-{actual_stats.get('max', 'N/A'):.4f}" if actual_stats else 'N/A'
            }
        
        return config
    
    def run_full_analysis(self) -> Dict:
        """运行完整分析"""
        print("🚀 开始完整数据范围分析...")
        
        # 1. 分析游戏时长
        duration_stats = self.analyze_game_duration()
        print(f"✅ 游戏时长分析完成: {duration_stats.get('count', 0)} 个文件")
        
        # 2. 分析ROI注视时间
        roi_stats = self.analyze_roi_fixation_time()
        print(f"✅ ROI时间分析完成")
        
        # 3. 分析RQA指标
        rqa_stats = self.analyze_rqa_metrics()
        print(f"✅ RQA指标分析完成")
        
        # 4. 计算ROI时间占比
        percentage_stats = self.calculate_roi_time_percentage()
        print(f"✅ ROI占比分析完成")
        
        # 5. 生成归一化配置
        norm_config = self.generate_normalization_config()
        print(f"✅ 归一化配置生成完成")
        
        # 保存结果
        results = {
            'analysis_summary': {
                'game_duration': duration_stats,
                'roi_fixation_time': roi_stats,
                'rqa_metrics': rqa_stats,
                'roi_time_percentage': percentage_stats
            },
            'normalization_config': norm_config,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        return results
    
    def save_results(self, results: Dict, output_path: str):
        """保存分析结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"📁 结果已保存到: {output_path}")

def main():
    """主函数"""
    analyzer = DataRangeAnalyzer()
    results = analyzer.run_full_analysis()
    
    # 保存结果
    os.makedirs('analysis_results', exist_ok=True)
    analyzer.save_results(results, 'analysis_results/data_range_analysis.json')
    
    # 打印摘要
    print("\n📊 数据范围分析摘要:")
    print("=" * 50)
    
    if 'game_duration' in results['analysis_summary']:
        duration = results['analysis_summary']['game_duration']
        if 'min' in duration:
            print(f"🎮 游戏时长: {duration['min']:.1f}s - {duration['max']:.1f}s (平均: {duration['mean']:.1f}s)")
    
    if 'roi_fixation_time' in results['analysis_summary']:
        roi = results['analysis_summary']['roi_fixation_time'].get('overall', {})
        if 'min' in roi:
            print(f"👁️ ROI注视时间: {roi['min']:.3f}s - {roi['max']:.3f}s (平均: {roi['mean']:.3f}s)")
    
    if 'rqa_metrics' in results['analysis_summary']:
        rqa = results['analysis_summary']['rqa_metrics']
        for metric, stats in rqa.items():
            if 'overall' in stats:
                overall = stats['overall']
                print(f"🔄 {metric}: {overall['min']:.4f} - {overall['max']:.4f}")
    
    print("\n✅ 分析完成！请查看 analysis_results/data_range_analysis.json 获取详细结果")

if __name__ == "__main__":
    main()