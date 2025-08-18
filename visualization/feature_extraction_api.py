#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
综合特征提取与整合模块 (第六模块) - API接口
提供任务级别、ROI级别、RQA增强特征的提取和整合功能
"""

import os
import pandas as pd
import numpy as np
import json
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify
from scipy import stats
from scipy.spatial.distance import euclidean
from scipy.stats import entropy
import warnings
warnings.filterwarnings('ignore')

# 创建Blueprint
feature_extraction_bp = Blueprint('feature_extraction', __name__)

# 基础路径配置
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
FEATURE_RESULTS_DIR = os.path.join(BASE_DATA_DIR, 'feature_extraction_results')

# 确保结果目录存在
os.makedirs(FEATURE_RESULTS_DIR, exist_ok=True)

class FeatureExtractor:
    """综合特征提取器"""
    
    def __init__(self):
        self.base_data_dir = BASE_DATA_DIR
        self.results_dir = FEATURE_RESULTS_DIR
        
    def load_all_data(self):
        """加载所有必要的数据文件"""
        try:
            data = {}
            
            # 加载事件数据
            events_path = os.path.join(self.base_data_dir, 'event_analysis_results', 'All_Events.csv')
            if os.path.exists(events_path):
                data['events'] = pd.read_csv(events_path)
                print(f"✅ 加载事件数据: {len(data['events'])} 条记录")
            
            # 加载ROI汇总数据
            roi_path = os.path.join(self.base_data_dir, 'event_analysis_results', 'All_ROI_Summary.csv')
            if os.path.exists(roi_path):
                data['roi_summary'] = pd.read_csv(roi_path)
                print(f"✅ 加载ROI汇总数据: {len(data['roi_summary'])} 条记录")
            
            # 加载RQA数据（从最近的流程结果）
            rqa_dirs = [d for d in os.listdir(os.path.join(self.base_data_dir, 'rqa_pipeline_results')) 
                       if os.path.isdir(os.path.join(self.base_data_dir, 'rqa_pipeline_results', d))]
            
            if rqa_dirs:
                # 取最新的RQA结果
                latest_rqa_dir = sorted(rqa_dirs)[-1]
                rqa_file = os.path.join(self.base_data_dir, 'rqa_pipeline_results', 
                                      latest_rqa_dir, 'step2_data_merging', 
                                      'All_Subjects_RQA_EyeMetrics.csv')
                if os.path.exists(rqa_file):
                    data['rqa'] = pd.read_csv(rqa_file)
                    print(f"✅ 加载RQA数据: {len(data['rqa'])} 条记录")
            
            # 加载MMSE评分数据
            mmse_data = []
            mmse_dir = os.path.join(self.base_data_dir, 'MMSE_Score')
            if os.path.exists(mmse_dir):
                group_mapping = {
                    '控制组.csv': 'Control',
                    '轻度认知障碍组.csv': 'MCI', 
                    '阿尔兹海默症组.csv': 'AD'
                }
                
                for file_name, group in group_mapping.items():
                    file_path = os.path.join(mmse_dir, file_name)
                    if os.path.exists(file_path):
                        mmse_df = pd.read_csv(file_path)
                        mmse_df['Group'] = group
                        mmse_data.append(mmse_df)
                
                if mmse_data:
                    data['mmse'] = pd.concat(mmse_data, ignore_index=True)
                    print(f"✅ 加载MMSE数据: {len(data['mmse'])} 条记录")
            
            return data
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            traceback.print_exc()
            return {}
    
    def extract_task_level_features(self, data):
        """提取任务级别特征"""
        print("🔄 开始提取任务级别特征...")
        
        if 'events' not in data:
            raise ValueError("缺少事件数据")
        
        events_df = data['events']
        task_features = []
        
        # 按ADQ_ID分组处理每个任务
        for adq_id in events_df['ADQ_ID'].unique():
            task_data = events_df[events_df['ADQ_ID'] == adq_id]
            
            # 基本信息
            subject_id = adq_id[:-2]  # 如 n1q1 -> n1
            task_id = adq_id[-2:]     # 如 n1q1 -> q1
            group = task_data['Group'].iloc[0] if 'Group' in task_data.columns else 'Unknown'
            
            # 特征计算
            features = {
                'ADQ_ID': adq_id,
                'SubjectID': subject_id,
                'TaskID': task_id,
                'Group': group
            }
            
            # 1. 任务完成时间（基于事件的持续时间估算）
            fixations = task_data[task_data['EventType'] == 'fixation']
            if not fixations.empty:
                features['TaskCompletionTime'] = fixations['Duration_ms'].sum()
                
                # 2. 首次注视时延（第一个有效注视的开始时间）
                first_fixation = fixations.iloc[0]
                features['FirstFixationLatency'] = first_fixation.get('StartIndex', 0) * 10  # 假设10ms/sample
                
                # 3. 扫视路径长度（基于幅度累积）
                features['ScanpathLength'] = fixations['Amplitude_deg'].sum()
                
                # 4. 注视转移熵
                roi_sequence = fixations['ROI'].dropna().tolist()
                features['FixationTransitionEntropy'] = self._calculate_transition_entropy(roi_sequence)
                
                # 5. 注视和扫视统计
                features['TotalFixationCount'] = len(fixations)
                features['TotalSaccadeCount'] = len(task_data[task_data['EventType'] == 'saccade'])
                features['AverageFixationDuration'] = fixations['Duration_ms'].mean()
                
                # 6. 任务有效性评分（基于注视质量）
                valid_fixations = fixations[fixations['Duration_ms'] >= 100]  # 有效注视阈值
                features['TaskValidityScore'] = len(valid_fixations) / len(fixations) if len(fixations) > 0 else 0
            else:
                # 默认值
                for key in ['TaskCompletionTime', 'FirstFixationLatency', 'ScanpathLength', 
                           'FixationTransitionEntropy', 'TotalFixationCount', 'TotalSaccadeCount',
                           'AverageFixationDuration', 'TaskValidityScore']:
                    features[key] = 0
            
            task_features.append(features)
        
        task_features_df = pd.DataFrame(task_features)
        print(f"✅ 提取任务级别特征完成: {len(task_features_df)} 个任务")
        return task_features_df
    
    def extract_roi_level_features(self, data):
        """提取ROI级别特征"""
        print("🔄 开始提取ROI级别特征...")
        
        if 'roi_summary' not in data or 'events' not in data:
            raise ValueError("缺少ROI数据或事件数据")
        
        roi_df = data['roi_summary']
        events_df = data['events']
        roi_features = []
        
        # 按ADQ_ID和ROI分组处理
        for adq_id in roi_df['ADQ_ID'].unique():
            adq_data = roi_df[roi_df['ADQ_ID'] == adq_id]
            events_data = events_df[events_df['ADQ_ID'] == adq_id]
            
            subject_id = adq_id[:-2]
            task_id = adq_id[-2:]
            group = adq_data['Group'].iloc[0] if 'Group' in adq_data.columns else 'Unknown'
            
            # 计算总任务时间
            total_task_time = events_data[events_data['EventType'] == 'fixation']['Duration_ms'].sum()
            
            for _, roi_row in adq_data.iterrows():
                roi_name = roi_row['ROI']
                
                # 确定ROI类型
                roi_type = 'BG'  # 默认背景
                if 'INST' in roi_name:
                    roi_type = 'INST'
                elif 'KW' in roi_name:
                    roi_type = 'KW'
                
                features = {
                    'ADQ_ID': adq_id,
                    'SubjectID': subject_id,
                    'TaskID': task_id,
                    'Group': group,
                    'ROI_Name': roi_name,
                    'ROI_Type': roi_type
                }
                
                # 1. 注视时间百分比
                dwell_time = roi_row.get('FixTime', 0) * 1000  # 转换为ms
                features['DwellTimePercentage'] = (dwell_time / total_task_time * 100) if total_task_time > 0 else 0
                
                # 2. 访问次数和回视次数
                features['VisitCount'] = roi_row.get('EnterCount', 0)
                features['RevisitCount'] = roi_row.get('RegressionCount', 0)
                
                # 3. 平均访问持续时间
                visit_count = features['VisitCount']
                features['AverageVisitDuration'] = dwell_time / visit_count if visit_count > 0 else 0
                
                # 4. 首次进入时间（基于事件序列估算）
                roi_events = events_data[events_data['ROI'] == roi_name]
                if not roi_events.empty:
                    first_event = roi_events.iloc[0]
                    features['FirstEntryTime'] = first_event.get('StartIndex', 0) * 10  # 假设10ms/sample
                else:
                    features['FirstEntryTime'] = 0
                
                # 5. ROI重要性评分（基于注视时间和访问频率）
                time_score = min(features['DwellTimePercentage'] / 20, 1)  # 归一化到0-1
                visit_score = min(features['VisitCount'] / 10, 1)  # 归一化到0-1
                features['ROI_Importance_Score'] = (time_score + visit_score) / 2
                
                roi_features.append(features)
        
        roi_features_df = pd.DataFrame(roi_features)
        print(f"✅ 提取ROI级别特征完成: {len(roi_features_df)} 个ROI记录")
        return roi_features_df
    
    def extract_rqa_enhanced_features(self, data):
        """提取RQA增强特征"""
        print("🔄 开始提取RQA增强特征...")
        
        if 'rqa' not in data:
            raise ValueError("缺少RQA数据")
        
        rqa_df = data['rqa']
        rqa_features = []
        
        # 按被试分组处理
        for subject_id in rqa_df['ID'].str[:-2].unique():  # 去掉任务ID
            subject_data = rqa_df[rqa_df['ID'].str.startswith(subject_id)]
            
            if len(subject_data) < 2:  # 至少需要2个任务才能计算变异性
                continue
            
            group = subject_data['Group'].iloc[0]
            
            features = {
                'SubjectID': subject_id,
                'Group': group
            }
            
            # RQA指标
            rqa_metrics = ['RR-2D-xy', 'RR-1D-x', 'DET-2D-xy', 'DET-1D-x', 'ENT-2D-xy', 'ENT-1D-x']
            
            # 1. 跨任务RQA变异性（变异系数）
            for metric in rqa_metrics:
                if metric in subject_data.columns:
                    values = subject_data[metric].dropna()
                    if len(values) > 1:
                        cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 0
                        features[f'{metric}_CoV'] = cv
                    else:
                        features[f'{metric}_CoV'] = 0
            
            # 2. RQA时间演变趋势（线性斜率）
            tasks_order = sorted(subject_data['q'].unique())
            for metric in rqa_metrics:
                if metric in subject_data.columns:
                    values = []
                    for task in tasks_order:
                        task_data = subject_data[subject_data['q'] == task]
                        if not task_data.empty:
                            values.append(task_data[metric].iloc[0])
                    
                    if len(values) >= 3:  # 至少3个点才能计算趋势
                        x = np.arange(len(values))
                        slope, _ = np.polyfit(x, values, 1)
                        features[f'{metric}_Trend_Slope'] = slope
                    else:
                        features[f'{metric}_Trend_Slope'] = 0
            
            # 3. RQA稳定性指数（基于标准差）
            for metric in rqa_metrics:
                if metric in subject_data.columns:
                    values = subject_data[metric].dropna()
                    if len(values) > 1:
                        stability = 1 / (1 + np.std(values))  # 标准差越小，稳定性越高
                        features[f'{metric}_Stability_Index'] = stability
                    else:
                        features[f'{metric}_Stability_Index'] = 1
            
            # 4. 综合RQA变异性指标
            all_covs = [features.get(f'{metric}_CoV', 0) for metric in rqa_metrics]
            features['RQA_Overall_Variability'] = np.mean([cv for cv in all_covs if cv > 0])
            
            rqa_features.append(features)
        
        rqa_features_df = pd.DataFrame(rqa_features)
        print(f"✅ 提取RQA增强特征完成: {len(rqa_features_df)} 个被试")
        return rqa_features_df
    
    def integrate_features_with_mmse(self, task_features, roi_features, rqa_features, mmse_data):
        """整合所有特征并合并MMSE数据"""
        print("🔄 开始整合特征...")
        
        # 1. 创建主特征表（任务级别）
        master_features = task_features.copy()
        
        # 添加MMSE评分
        if mmse_data is not None and not mmse_data.empty:
            mmse_mapping = {}
            for _, row in mmse_data.iterrows():
                subject_id = row['受试者']
                mmse_score = row['总分']
                group = row['Group']
                mmse_mapping[subject_id] = {'MMSE_Score': mmse_score, 'MMSE_Group': group}
            
            master_features['MMSE_Score'] = master_features['SubjectID'].map(
                lambda x: mmse_mapping.get(x, {}).get('MMSE_Score', np.nan)
            )
            master_features['MMSE_Group'] = master_features['SubjectID'].map(
                lambda x: mmse_mapping.get(x, {}).get('MMSE_Group', 'Unknown')
            )
        
        # 2. 聚合ROI特征到任务级别
        roi_agg = roi_features.groupby(['ADQ_ID']).agg({
            'DwellTimePercentage': 'sum',
            'VisitCount': 'sum',
            'RevisitCount': 'sum',
            'ROI_Importance_Score': 'mean'
        }).reset_index()
        
        # 分别计算关键ROI和背景ROI的统计
        key_roi_stats = roi_features[roi_features['ROI_Type'].isin(['INST', 'KW'])].groupby('ADQ_ID').agg({
            'DwellTimePercentage': 'sum',
            'VisitCount': 'sum'
        }).reset_index()
        key_roi_stats.columns = ['ADQ_ID', 'KeyROI_DwellTime', 'KeyROI_VisitCount']
        
        bg_roi_stats = roi_features[roi_features['ROI_Type'] == 'BG'].groupby('ADQ_ID').agg({
            'DwellTimePercentage': 'sum',
            'VisitCount': 'sum'
        }).reset_index()
        bg_roi_stats.columns = ['ADQ_ID', 'BG_DwellTime', 'BG_VisitCount']
        
        # 合并ROI统计到主特征表
        master_features = master_features.merge(roi_agg, on='ADQ_ID', how='left')
        master_features = master_features.merge(key_roi_stats, on='ADQ_ID', how='left')
        master_features = master_features.merge(bg_roi_stats, on='ADQ_ID', how='left')
        
        # 计算关键ROI vs 背景ROI比率
        master_features['KeyBG_Ratio'] = master_features['KeyROI_DwellTime'] / (master_features['BG_DwellTime'] + 1)
        
        # 3. 添加RQA增强特征
        if rqa_features is not None and not rqa_features.empty:
            master_features = master_features.merge(rqa_features, on=['SubjectID', 'Group'], how='left')
        
        # 4. 创建被试汇总表
        subject_summary = master_features.groupby(['SubjectID', 'Group']).agg({
            'TaskCompletionTime': 'mean',
            'ScanpathLength': 'mean', 
            'FixationTransitionEntropy': 'mean',
            'TotalFixationCount': 'mean',
            'AverageFixationDuration': 'mean',
            'TaskValidityScore': 'mean',
            'KeyBG_Ratio': 'mean',
            'MMSE_Score': 'first'
        }).reset_index()
        
        # 添加任务表现分数
        for task_id in ['q1', 'q2', 'q3', 'q4', 'q5']:
            task_data = master_features[master_features['TaskID'] == task_id]
            task_scores = task_data.groupby('SubjectID')['TaskValidityScore'].first()
            subject_summary[f'Task{task_id[1:]}_Score'] = subject_summary['SubjectID'].map(task_scores)
        
        # 添加RQA汇总指标
        if rqa_features is not None and not rqa_features.empty:
            rqa_summary_cols = [col for col in rqa_features.columns 
                              if col.endswith('_CoV') or col.endswith('_Stability_Index') or 'Variability' in col]
            for col in rqa_summary_cols:
                if col in master_features.columns:
                    subject_summary[col] = master_features.groupby('SubjectID')[col].first()
        
        print(f"✅ 特征整合完成:")
        print(f"   - 主特征表: {len(master_features)} 条任务记录")
        print(f"   - 被试汇总表: {len(subject_summary)} 个被试")
        
        return master_features, subject_summary
    
    def _calculate_transition_entropy(self, sequence):
        """计算转移熵"""
        if len(sequence) < 2:
            return 0
        
        # 构建转移对
        transitions = [(sequence[i], sequence[i+1]) for i in range(len(sequence)-1)]
        
        # 计算转移概率
        transition_counts = {}
        for trans in transitions:
            transition_counts[trans] = transition_counts.get(trans, 0) + 1
        
        total_transitions = len(transitions)
        probs = [count / total_transitions for count in transition_counts.values()]
        
        # 计算Shannon熵
        return entropy(probs, base=2)
    
    def save_results(self, master_features, subject_summary, timestamp=None):
        """保存结果到文件"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 保存主特征表
            master_file = os.path.join(self.results_dir, f'Master_Features_{timestamp}.csv')
            master_features.to_csv(master_file, index=False, encoding='utf-8-sig')
            
            # 保存被试汇总表
            summary_file = os.path.join(self.results_dir, f'Subject_Features_Summary_{timestamp}.csv')
            subject_summary.to_csv(summary_file, index=False, encoding='utf-8-sig')
            
            # 保存元数据
            metadata = {
                'timestamp': timestamp,
                'master_features_shape': master_features.shape,
                'subject_summary_shape': subject_summary.shape,
                'feature_columns': master_features.columns.tolist(),
                'summary_columns': subject_summary.columns.tolist()
            }
            
            metadata_file = os.path.join(self.results_dir, f'metadata_{timestamp}.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return {
                'master_file': master_file,
                'summary_file': summary_file,
                'metadata_file': metadata_file
            }
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
            traceback.print_exc()
            return None

# 创建全局特征提取器实例
feature_extractor = FeatureExtractor()

# API路由定义
@feature_extraction_bp.route('/api/feature-extraction/extract', methods=['POST'])
def extract_features():
    """执行完整的特征提取流程"""
    try:
        print("🚀 开始综合特征提取...")
        
        # 加载数据
        data = feature_extractor.load_all_data()
        if not data:
            return jsonify({
                'success': False,
                'message': '数据加载失败'
            }), 500
        
        # 提取各类特征
        task_features = feature_extractor.extract_task_level_features(data)
        roi_features = feature_extractor.extract_roi_level_features(data)
        rqa_features = feature_extractor.extract_rqa_enhanced_features(data)
        
        # 整合特征
        mmse_data = data.get('mmse')
        master_features, subject_summary = feature_extractor.integrate_features_with_mmse(
            task_features, roi_features, rqa_features, mmse_data
        )
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = feature_extractor.save_results(master_features, subject_summary, timestamp)
        
        if files:
            return jsonify({
                'success': True,
                'message': '特征提取完成',
                'timestamp': timestamp,
                'files': files,
                'statistics': {
                    'total_subjects': len(subject_summary),
                    'total_tasks': len(master_features),
                    'feature_count': len(master_features.columns),
                    'summary_feature_count': len(subject_summary.columns)
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '结果保存失败'
            }), 500
            
    except Exception as e:
        print(f"❌ 特征提取错误: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'特征提取失败: {str(e)}'
        }), 500

@feature_extraction_bp.route('/api/feature-extraction/history', methods=['GET'])
def get_extraction_history():
    """获取特征提取历史"""
    try:
        history = []
        
        if os.path.exists(FEATURE_RESULTS_DIR):
            files = os.listdir(FEATURE_RESULTS_DIR)
            metadata_files = [f for f in files if f.startswith('metadata_') and f.endswith('.json')]
            
            for metadata_file in metadata_files:
                try:
                    with open(os.path.join(FEATURE_RESULTS_DIR, metadata_file), 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        history.append(metadata)
                except Exception as e:
                    print(f"读取元数据文件失败 {metadata_file}: {e}")
        
        # 按时间戳倒序排列
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"❌ 获取历史记录错误: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500

@feature_extraction_bp.route('/api/feature-extraction/download/<timestamp>', methods=['GET'])
def download_results(timestamp):
    """下载指定时间戳的结果文件"""
    try:
        file_type = request.args.get('type', 'master')  # master 或 summary
        
        if file_type == 'master':
            filename = f'Master_Features_{timestamp}.csv'
        elif file_type == 'summary':
            filename = f'Subject_Features_Summary_{timestamp}.csv'
        else:
            return jsonify({'success': False, 'message': '无效的文件类型'}), 400
        
        file_path = os.path.join(FEATURE_RESULTS_DIR, filename)
        
        if os.path.exists(file_path):
            from flask import send_file
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'success': False, 'message': '文件不存在'}), 404
            
    except Exception as e:
        print(f"❌ 文件下载错误: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'文件下载失败: {str(e)}'
        }), 500

@feature_extraction_bp.route('/api/feature-extraction/preview/<timestamp>', methods=['GET'])
def preview_results(timestamp):
    """预览指定时间戳的结果"""
    try:
        file_type = request.args.get('type', 'master')
        limit = int(request.args.get('limit', 20))
        
        if file_type == 'master':
            filename = f'Master_Features_{timestamp}.csv'
        elif file_type == 'summary':
            filename = f'Subject_Features_Summary_{timestamp}.csv'
        else:
            return jsonify({'success': False, 'message': '无效的文件类型'}), 400
        
        file_path = os.path.join(FEATURE_RESULTS_DIR, filename)
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            # 基本统计信息
            stats = {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
                'missing_values': {col: int(count) for col, count in df.isnull().sum().to_dict().items()}
            }
            
            # 数据预览 - 处理NaN值和数据类型
            preview_df = df.head(limit).fillna('')  # 将NaN替换为空字符串
            preview_data = preview_df.to_dict('records')
            
            return jsonify({
                'success': True,
                'statistics': stats,
                'preview': preview_data
            })
        else:
            return jsonify({'success': False, 'message': '文件不存在'}), 404
            
    except Exception as e:
        print(f"❌ 预览错误: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'预览失败: {str(e)}'
        }), 500

print("✅ 综合特征提取与整合模块已加载") 