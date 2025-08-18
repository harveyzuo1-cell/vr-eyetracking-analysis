#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征归一化处理器 - 生成归一化特征数据表格
"""

import pandas as pd
import numpy as np
import os
import json
from typing import Dict, List, Tuple
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeatureNormalizer:
    """特征归一化处理器"""
    
    def __init__(self, data_root: str = "data", output_dir: str = "data/normalized_features"):
        self.data_root = data_root
        self.output_dir = output_dir
        self.normalization_config = None
        self.load_normalization_config()
        
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def load_normalization_config(self):
        """加载归一化配置"""
        config_file = "analysis_results/data_range_analysis.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.normalization_config = data.get('normalization_config', {})
        else:
            logger.warning(f"归一化配置文件不存在: {config_file}")
            self.normalization_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认归一化配置"""
        return {
            'features': {
                'game_duration': {'min_value': 0.0, 'max_value': 180.0},
                'roi_fixation_time': {'min_value': 0.0, 'max_value': 67.23},
                'RR-2D-xy': {'min_value': 0.0096, 'max_value': 0.2422},
                'RR-1D-x': {'min_value': 0.0298, 'max_value': 0.2870},
                'DET-2D-xy': {'min_value': 0.5808, 'max_value': 0.9655},
                'DET-1D-x': {'min_value': 0.5319, 'max_value': 0.9556},
                'ENT-2D-xy': {'min_value': 0.7219, 'max_value': 3.8210},
                'ENT-1D-x': {'min_value': 0.8879, 'max_value': 3.5615}
            }
        }
    
    def normalize_value(self, value: float, feature_name: str) -> float:
        """归一化单个值"""
        config = self.normalization_config['features'].get(feature_name, {})
        min_val = config.get('min_value', 0.0)
        max_val = config.get('max_value', 1.0)
        
        if max_val == min_val:
            return 0.0
        
        normalized = (value - min_val) / (max_val - min_val)
        return np.clip(normalized, 0.0, 1.0)
    
    def extract_subjects_info(self) -> pd.DataFrame:
        """提取受试者基本信息"""
        logger.info("📊 提取受试者基本信息...")
        
        subjects = []
        
        # 扫描校准数据目录
        groups = ['ad_calibrated', 'mci_calibrated', 'control_calibrated']
        group_mappings = {
            'ad_calibrated': 'ad',
            'mci_calibrated': 'mci', 
            'control_calibrated': 'control'
        }
        
        for group_dir in groups:
            group_path = os.path.join(self.data_root, group_dir)
            if not os.path.exists(group_path):
                continue
                
            group_type = group_mappings[group_dir]
            
            for group_folder in os.listdir(group_path):
                folder_path = os.path.join(group_path, group_folder)
                if not os.path.isdir(folder_path):
                    continue
                
                # 从文件夹名提取组号
                try:
                    if group_type == 'ad':
                        group_number = group_folder.replace('ad_group_', '')
                        subject_id = f'ad{group_number.zfill(2)}'
                    elif group_type == 'mci':
                        group_number = group_folder.replace('mci_group_', '')
                        subject_id = f'm{group_number.zfill(2)}'
                    else:  # control
                        group_number = group_folder.replace('control_group_', '')
                        subject_id = f'n{group_number.zfill(2)}'
                    
                    # 验证group_number是数字
                    group_num_int = int(group_number)
                    
                    subjects.append({
                        'subject_id': subject_id,
                        'group_type': group_type,
                        'group_number': group_num_int,
                        'original_id': subject_id
                    })
                except ValueError:
                    logger.warning(f"跳过无效的文件夹名: {group_folder}")
                    continue
        
        subjects_df = pd.DataFrame(subjects)
        subjects_df = subjects_df.sort_values(['group_type', 'group_number'])
        
        logger.info(f"✅ 提取了 {len(subjects_df)} 个受试者信息")
        return subjects_df
    
    def create_tasks_info(self) -> pd.DataFrame:
        """创建任务信息表"""
        logger.info("📊 创建任务信息表...")
        
        tasks = [
            {'task_id': 'Q1', 'task_name': '第一题', 'max_duration_seconds': 180.0, 'description': 'VR-MMSE任务1'},
            {'task_id': 'Q2', 'task_name': '第二题', 'max_duration_seconds': 180.0, 'description': 'VR-MMSE任务2'},
            {'task_id': 'Q3', 'task_name': '第三题', 'max_duration_seconds': 180.0, 'description': 'VR-MMSE任务3'},
            {'task_id': 'Q4', 'task_name': '第四题', 'max_duration_seconds': 180.0, 'description': 'VR-MMSE任务4'},
            {'task_id': 'Q5', 'task_name': '第五题', 'max_duration_seconds': 180.0, 'description': 'VR-MMSE任务5'}
        ]
        
        tasks_df = pd.DataFrame(tasks)
        logger.info(f"✅ 创建了 {len(tasks_df)} 个任务记录")
        return tasks_df
    
    def calculate_game_sessions(self, subjects_df: pd.DataFrame) -> pd.DataFrame:
        """计算游戏会话信息"""
        logger.info("📊 计算游戏会话信息...")
        
        sessions = []
        
        # 扫描所有校准数据文件
        groups = ['ad_calibrated', 'mci_calibrated', 'control_calibrated']
        
        for group_dir in groups:
            group_path = os.path.join(self.data_root, group_dir)
            if not os.path.exists(group_path):
                continue
            
            for group_folder in os.listdir(group_path):
                folder_path = os.path.join(group_path, group_folder)
                if not os.path.isdir(folder_path):
                    continue
                
                for file_name in os.listdir(folder_path):
                    if not file_name.endswith('_preprocessed_calibrated.csv'):
                        continue
                    
                    file_path = os.path.join(folder_path, file_name)
                    
                    try:
                        # 从文件名提取session_id
                        session_id = file_name.replace('_preprocessed_calibrated.csv', '')
                        
                        # 提取subject_id和task_id
                        if session_id.startswith('ad'):
                            subject_id = session_id[:4]  # ad01, ad02, etc.
                            task_num = session_id[4:]
                        elif session_id.startswith('m'):
                            subject_id = session_id[:3]   # m01, m02, etc.
                            task_num = session_id[3:]
                        elif session_id.startswith('n'):
                            subject_id = session_id[:3]   # n01, n02, etc.
                            task_num = session_id[3:]
                        else:
                            continue
                        
                        task_id = f'Q{task_num.replace("q", "")}'
                        
                        # 读取数据文件计算时长
                        df = pd.read_csv(file_path)
                        if 'milliseconds' in df.columns and len(df) > 0:
                            duration_ms = df['milliseconds'].max() - df['milliseconds'].min()
                            duration_s = duration_ms / 1000.0
                            
                            # 归一化游戏时长
                            duration_norm = self.normalize_value(duration_s, 'game_duration')
                            
                            sessions.append({
                                'session_id': session_id,
                                'subject_id': subject_id,
                                'task_id': task_id,
                                'game_duration_seconds': round(duration_s, 2),
                                'game_duration_normalized': round(duration_norm, 4),
                                'data_points_count': len(df),
                                'file_path': file_path.replace(self.data_root + os.sep, '')
                            })
                            
                    except Exception as e:
                        logger.warning(f"处理会话文件失败 {file_path}: {e}")
        
        sessions_df = pd.DataFrame(sessions)
        sessions_df = sessions_df.sort_values(['subject_id', 'task_id'])
        
        logger.info(f"✅ 计算了 {len(sessions_df)} 个游戏会话")
        return sessions_df
    
    def aggregate_roi_features(self, sessions_df: pd.DataFrame) -> pd.DataFrame:
        """聚合ROI特征"""
        logger.info("📊 聚合ROI特征...")
        
        roi_file = os.path.join(self.data_root, 'event_analysis_results', 'All_ROI_Summary.csv')
        if not os.path.exists(roi_file):
            logger.warning(f"ROI文件不存在: {roi_file}")
            return pd.DataFrame()
        
        try:
            roi_df = pd.read_csv(roi_file)
            
            roi_features = []
            
            # 创建session_id到时长的映射
            session_durations = dict(zip(sessions_df['session_id'], sessions_df['game_duration_seconds']))
            
            for session_id in sessions_df['session_id'].unique():
                session_data = roi_df[roi_df['ADQ_ID'] == session_id]
                game_duration = session_durations.get(session_id, 1.0)
                
                # 按ROI类型聚合
                roi_types = ['KW', 'INST', 'BG']
                
                for roi_type in roi_types:
                    roi_type_data = session_data[session_data['ROI'].str.contains(roi_type, na=False)]
                    
                    if len(roi_type_data) > 0:
                        total_fixation_time = roi_type_data['FixTime'].sum()
                        total_enter_count = roi_type_data['EnterCount'].sum()
                        total_regression_count = roi_type_data['RegressionCount'].sum()
                    else:
                        total_fixation_time = 0.0
                        total_enter_count = 0
                        total_regression_count = 0
                    
                    # 计算时间占比
                    fixation_time_percentage = total_fixation_time / game_duration if game_duration > 0 else 0.0
                    fixation_time_percentage = min(fixation_time_percentage, 1.0)  # 限制在100%以内
                    
                    # 归一化
                    total_fixation_time_norm = self.normalize_value(total_fixation_time, 'roi_fixation_time')
                    fixation_time_percentage_norm = fixation_time_percentage  # 已经是0-1范围
                    
                    roi_features.append({
                        'session_id': session_id,
                        'roi_type': roi_type,
                        'total_fixation_time_seconds': round(total_fixation_time, 3),
                        'total_fixation_time_normalized': round(total_fixation_time_norm, 4),
                        'fixation_time_percentage': round(fixation_time_percentage, 4),
                        'fixation_time_percentage_normalized': round(fixation_time_percentage_norm, 4),
                        'enter_count': int(total_enter_count),
                        'regression_count': int(total_regression_count)
                    })
            
            roi_features_df = pd.DataFrame(roi_features)
            logger.info(f"✅ 聚合了 {len(roi_features_df)} 个ROI特征记录")
            return roi_features_df
            
        except Exception as e:
            logger.error(f"聚合ROI特征失败: {e}")
            return pd.DataFrame()
    
    def normalize_rqa_features(self, sessions_df: pd.DataFrame) -> pd.DataFrame:
        """归一化RQA特征"""
        logger.info("📊 归一化RQA特征...")
        
        rqa_path = os.path.join(self.data_root, 'rqa_pipeline_results', 'm2_tau1_eps0.055_lmin2', 'step1_rqa_calculation')
        if not os.path.exists(rqa_path):
            logger.warning(f"RQA路径不存在: {rqa_path}")
            return pd.DataFrame()
        
        try:
            # 读取所有RQA文件
            all_rqa_data = []
            for group in ['ad', 'control', 'mci']:
                file_path = os.path.join(rqa_path, f'RQA_1D2D_summary_{group}.csv')
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df['group'] = group
                    all_rqa_data.append(df)
            
            if not all_rqa_data:
                logger.warning("未找到有效的RQA数据")
                return pd.DataFrame()
            
            combined_rqa_df = pd.concat(all_rqa_data, ignore_index=True)
            
            rqa_features = []
            
            for _, row in combined_rqa_df.iterrows():
                filename = row['filename']
                session_id = filename.replace('_preprocessed_calibrated.csv', '')
                
                # 检查session_id是否在会话列表中
                if session_id not in sessions_df['session_id'].values:
                    continue
                
                # 原始值
                rr_2d_xy = row.get('RR-2D-xy', 0.0)
                rr_1d_x = row.get('RR-1D-x', 0.0)
                det_2d_xy = row.get('DET-2D-xy', 0.0)
                det_1d_x = row.get('DET-1D-x', 0.0)
                ent_2d_xy = row.get('ENT-2D-xy', 0.0)
                ent_1d_x = row.get('ENT-1D-x', 0.0)
                
                # 归一化
                rr_2d_xy_norm = self.normalize_value(rr_2d_xy, 'RR-2D-xy')
                rr_1d_x_norm = self.normalize_value(rr_1d_x, 'RR-1D-x')
                det_2d_xy_norm = self.normalize_value(det_2d_xy, 'DET-2D-xy')
                det_1d_x_norm = self.normalize_value(det_1d_x, 'DET-1D-x')
                ent_2d_xy_norm = self.normalize_value(ent_2d_xy, 'ENT-2D-xy')
                ent_1d_x_norm = self.normalize_value(ent_1d_x, 'ENT-1D-x')
                
                rqa_features.append({
                    'session_id': session_id,
                    'rr_2d_xy': round(rr_2d_xy, 6),
                    'rr_2d_xy_normalized': round(rr_2d_xy_norm, 4),
                    'rr_1d_x': round(rr_1d_x, 6),
                    'rr_1d_x_normalized': round(rr_1d_x_norm, 4),
                    'det_2d_xy': round(det_2d_xy, 6),
                    'det_2d_xy_normalized': round(det_2d_xy_norm, 4),
                    'det_1d_x': round(det_1d_x, 6),
                    'det_1d_x_normalized': round(det_1d_x_norm, 4),
                    'ent_2d_xy': round(ent_2d_xy, 6),
                    'ent_2d_xy_normalized': round(ent_2d_xy_norm, 4),
                    'ent_1d_x': round(ent_1d_x, 6),
                    'ent_1d_x_normalized': round(ent_1d_x_norm, 4)
                })
            
            rqa_features_df = pd.DataFrame(rqa_features)
            logger.info(f"✅ 归一化了 {len(rqa_features_df)} 个RQA特征记录")
            return rqa_features_df
            
        except Exception as e:
            logger.error(f"归一化RQA特征失败: {e}")
            return pd.DataFrame()
    
    def generate_summary_table(self, sessions_df: pd.DataFrame, roi_features_df: pd.DataFrame, 
                             rqa_features_df: pd.DataFrame) -> pd.DataFrame:
        """生成归一化特征汇总表"""
        logger.info("📊 生成归一化特征汇总表...")
        
        summary_data = []
        
        for _, session in sessions_df.iterrows():
            session_id = session['session_id']
            subject_id = session['subject_id']
            task_id = session['task_id']
            
            # 从subject_id推断group_type
            if subject_id.startswith('ad'):
                group_type = 'ad'
            elif subject_id.startswith('m'):
                group_type = 'mci'
            elif subject_id.startswith('n'):
                group_type = 'control'
            else:
                group_type = 'unknown'
            
            # 初始化汇总记录
            summary_record = {
                'session_id': session_id,
                'subject_id': subject_id,
                'task_id': task_id,
                'group_type': group_type,
                'game_duration_norm': session['game_duration_normalized']
            }
            
            # 添加ROI特征
            session_roi = roi_features_df[roi_features_df['session_id'] == session_id]
            for roi_type in ['KW', 'INST', 'BG']:
                roi_data = session_roi[session_roi['roi_type'] == roi_type]
                if len(roi_data) > 0:
                    summary_record[f'roi_{roi_type.lower()}_time_norm'] = roi_data.iloc[0]['total_fixation_time_normalized']
                    summary_record[f'roi_{roi_type.lower()}_percentage_norm'] = roi_data.iloc[0]['fixation_time_percentage_normalized']
                else:
                    summary_record[f'roi_{roi_type.lower()}_time_norm'] = 0.0
                    summary_record[f'roi_{roi_type.lower()}_percentage_norm'] = 0.0
            
            # 添加RQA特征
            session_rqa = rqa_features_df[rqa_features_df['session_id'] == session_id]
            if len(session_rqa) > 0:
                rqa_data = session_rqa.iloc[0]
                summary_record.update({
                    'rr_2d_norm': rqa_data['rr_2d_xy_normalized'],
                    'rr_1d_norm': rqa_data['rr_1d_x_normalized'],
                    'det_2d_norm': rqa_data['det_2d_xy_normalized'],
                    'det_1d_norm': rqa_data['det_1d_x_normalized'],
                    'ent_2d_norm': rqa_data['ent_2d_xy_normalized'],
                    'ent_1d_norm': rqa_data['ent_1d_x_normalized']
                })
            else:
                summary_record.update({
                    'rr_2d_norm': 0.0,
                    'rr_1d_norm': 0.0,
                    'det_2d_norm': 0.0,
                    'det_1d_norm': 0.0,
                    'ent_2d_norm': 0.0,
                    'ent_1d_norm': 0.0
                })
            
            summary_data.append(summary_record)
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values(['group_type', 'subject_id', 'task_id'])
        
        logger.info(f"✅ 生成了 {len(summary_df)} 个汇总记录")
        return summary_df
    
    def save_all_tables(self, subjects_df: pd.DataFrame, tasks_df: pd.DataFrame, 
                       sessions_df: pd.DataFrame, roi_features_df: pd.DataFrame, 
                       rqa_features_df: pd.DataFrame, summary_df: pd.DataFrame):
        """保存所有表格"""
        logger.info("💾 保存所有表格...")
        
        tables = {
            'subjects.csv': subjects_df,
            'tasks.csv': tasks_df,
            'game_sessions.csv': sessions_df,
            'roi_features.csv': roi_features_df,
            'rqa_features.csv': rqa_features_df,
            'normalized_features_summary.csv': summary_df
        }
        
        for filename, df in tables.items():
            if df is not None and not df.empty:
                output_path = os.path.join(self.output_dir, filename)
                df.to_csv(output_path, index=False, encoding='utf-8')
                logger.info(f"✅ 保存 {filename}: {len(df)} 行")
            else:
                logger.warning(f"⚠️ 跳过空表格: {filename}")
    
    def run_full_normalization(self):
        """运行完整的归一化流程"""
        logger.info("🚀 开始完整的特征归一化流程...")
        
        try:
            # 1. 提取受试者信息
            subjects_df = self.extract_subjects_info()
            
            # 2. 创建任务信息
            tasks_df = self.create_tasks_info()
            
            # 3. 计算游戏会话
            sessions_df = self.calculate_game_sessions(subjects_df)
            
            # 4. 聚合ROI特征
            roi_features_df = self.aggregate_roi_features(sessions_df)
            
            # 5. 归一化RQA特征
            rqa_features_df = self.normalize_rqa_features(sessions_df)
            
            # 6. 生成汇总表
            summary_df = self.generate_summary_table(sessions_df, roi_features_df, rqa_features_df)
            
            # 7. 保存所有表格
            self.save_all_tables(subjects_df, tasks_df, sessions_df,
                                roi_features_df, rqa_features_df, summary_df)
            
            logger.info("🎉 归一化流程完成！")
            
        except Exception as e:
            logger.error(f"❌ 归一化流程失败: {e}")
            raise

def main():
    """主函数"""
    normalizer = FeatureNormalizer()
    normalizer.run_full_normalization()
    
    print("\\n🎉 特征归一化完成！")
    print("📁 输出文件位置: data/normalized_features/")
    print("📊 生成的表格:")
    print("   - subjects.csv: 受试者基本信息")
    print("   - tasks.csv: 任务信息")
    print("   - game_sessions.csv: 游戏会话信息")
    print("   - roi_features.csv: ROI特征")
    print("   - rqa_features.csv: RQA特征")
    print("   - normalized_features_summary.csv: 归一化特征汇总")

if __name__ == "__main__":
    main()