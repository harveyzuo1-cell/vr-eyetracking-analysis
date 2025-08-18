# -*- coding: utf-8 -*-
"""
真实数据整合API扩展
从校准数据、ROI事件、RQA结果中提取并整合10个归一化属性
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Blueprint, jsonify, request
import glob

# 创建Blueprint
real_data_bp = Blueprint('real_data', __name__)

class RealDataIntegrator:
    """真实数据整合器"""
    
    def __init__(self):
        self.base_path = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.output_path = os.path.join(self.base_path, 'module7_integrated_results')
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """确保输出目录存在"""
        os.makedirs(self.output_path, exist_ok=True)
    
    def get_available_rqa_configs(self):
        """获取可用的RQA配置"""
        rqa_path = os.path.join(self.base_path, 'rqa_pipeline_results')
        configs = []
        
        if os.path.exists(rqa_path):
            for config_dir in os.listdir(rqa_path):
                metadata_file = os.path.join(rqa_path, config_dir, 'metadata.json')
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        configs.append({
                            'signature': metadata['signature'],
                            'parameters': metadata['parameters'],
                            'last_updated': metadata.get('last_updated'),
                            'completed': all([
                                metadata.get('step_1_completed', False),
                                metadata.get('step_2_completed', False),
                                metadata.get('step_3_completed', False),
                                metadata.get('step_4_completed', False),
                                metadata.get('step_5_completed', False)
                            ])
                        })
                    except Exception as e:
                        print(f"⚠️ 读取配置失败 {config_dir}: {e}")
        
        return configs
    
    def load_calibrated_data(self):
        """加载校准数据以计算游戏时长"""
        print("📊 加载校准数据...")
        game_durations = {}
        
        # 遍历所有组别的校准数据
        for group in ['control', 'mci', 'ad']:
            calibrated_path = os.path.join(self.base_path, f'{group}_calibrated')
            if not os.path.exists(calibrated_path):
                continue
                
            for group_dir in os.listdir(calibrated_path):
                group_path = os.path.join(calibrated_path, group_dir)
                if not os.path.isdir(group_path):
                    continue
                    
                # 读取该组的所有CSV文件
                csv_files = glob.glob(os.path.join(group_path, '*_preprocessed_calibrated.csv'))
                for csv_file in csv_files:
                    try:
                        # 从文件名提取受试者和任务信息
                        filename = os.path.basename(csv_file)
                        # 例如: n1q1_preprocessed_calibrated.csv -> n1q1
                        session_id = filename.replace('_preprocessed_calibrated.csv', '')
                        
                        # 读取CSV计算时长
                        df = pd.read_csv(csv_file)
                        if len(df) > 0 and 'time_diff' in df.columns:
                            # 游戏时长 = 最大时间差 (毫秒转秒)
                            duration_ms = df['time_diff'].max()
                            duration_s = duration_ms / 1000.0 if duration_ms > 0 else 0
                            game_durations[session_id] = duration_s
                            
                    except Exception as e:
                        print(f"⚠️ 处理校准文件失败 {csv_file}: {e}")
        
        print(f"✅ 加载了 {len(game_durations)} 个会话的游戏时长")
        return game_durations
    
    def load_roi_features(self):
        """加载ROI特征数据"""
        print("📊 加载ROI特征数据...")
        roi_features = {}
        
        roi_file = os.path.join(self.base_path, 'event_analysis_results', 'All_ROI_Summary.csv')
        if not os.path.exists(roi_file):
            print(f"❌ ROI文件不存在: {roi_file}")
            return roi_features
        
        try:
            df = pd.read_csv(roi_file)
            
            # 按ADQ_ID分组聚合ROI数据
            for session_id in df['ADQ_ID'].unique():
                session_data = df[df['ADQ_ID'] == session_id]
                
                # 按ROI类型聚合FixTime
                roi_times = {
                    'KW': 0,    # 关键词
                    'INST': 0,  # 指示  
                    'BG': 0     # 背景
                }
                
                for _, row in session_data.iterrows():
                    roi_name = row['ROI']
                    fix_time = row['FixTime']
                    
                    if roi_name.startswith('KW_'):
                        roi_times['KW'] += fix_time
                    elif roi_name.startswith('INST_'):
                        roi_times['INST'] += fix_time
                    elif roi_name.startswith('BG_'):
                        roi_times['BG'] += fix_time
                
                roi_features[session_id] = roi_times
                
        except Exception as e:
            print(f"❌ 处理ROI文件失败: {e}")
        
        print(f"✅ 加载了 {len(roi_features)} 个会话的ROI特征")
        return roi_features
    
    def load_rqa_features(self, rqa_config):
        """加载RQA特征数据"""
        print(f"📊 加载RQA特征数据 ({rqa_config})...")
        rqa_features = {}
        
        rqa_path = os.path.join(self.base_path, 'rqa_pipeline_results', rqa_config, 'step1_rqa_calculation')
        
        # 读取三个组别的RQA结果
        for group in ['control', 'mci', 'ad']:
            rqa_file = os.path.join(rqa_path, f'RQA_1D2D_summary_{group}.csv')
            if not os.path.exists(rqa_file):
                print(f"⚠️ RQA文件不存在: {rqa_file}")
                continue
                
            try:
                df = pd.read_csv(rqa_file)
                
                for _, row in df.iterrows():
                    # 从filename提取session_id
                    filename = row['filename']
                    session_id = filename.replace('_preprocessed_calibrated.csv', '')
                    
                    rqa_features[session_id] = {
                        'rr_2d': row['RR-2D-xy'],
                        'rr_1d': row['RR-1D-x'], 
                        'det_2d': row['DET-2D-xy'],
                        'det_1d': row['DET-1D-x'],
                        'ent_2d': row['ENT-2D-xy'],
                        'ent_1d': row['ENT-1D-x'],
                        'group': group
                    }
                    
            except Exception as e:
                print(f"❌ 处理RQA文件失败 {rqa_file}: {e}")
        
        print(f"✅ 加载了 {len(rqa_features)} 个会话的RQA特征")
        return rqa_features
    
    def normalize_features(self, integrated_data):
        """归一化所有特征 - 使用优化的归一化策略"""
        print("📊 归一化特征数据...")
        
        df = pd.DataFrame(integrated_data)
        
        # 定义特征归一化策略
        normalization_strategies = {
            # 游戏时长: 使用95百分位数截断，避免极端异常值影响
            'game_duration': {'method': 'percentile_clip', 'percentile': 95},
            
            # ROI时间: 使用标准Min-Max，但设置合理上限
            'roi_kw_time': {'method': 'percentile_clip', 'percentile': 98},
            'roi_inst_time': {'method': 'percentile_clip', 'percentile': 98}, 
            'roi_bg_time': {'method': 'percentile_clip', 'percentile': 98},
            
            # RQA特征: 理论上有固定范围，使用标准Min-Max
            'rr_1d': {'method': 'minmax'},
            'det_1d': {'method': 'minmax'},
            'ent_1d': {'method': 'minmax'},
            'rr_2d': {'method': 'minmax'},
            'det_2d': {'method': 'minmax'},
            'ent_2d': {'method': 'minmax'}
        }
        
        # 应用归一化策略
        for feature, strategy in normalization_strategies.items():
            if feature in df.columns:
                if strategy['method'] == 'percentile_clip':
                    # 百分位数截断归一化
                    percentile = strategy['percentile']
                    min_val = df[feature].quantile(0.05)  # 使用5%分位数作为最小值
                    max_val = df[feature].quantile(percentile / 100)  # 使用指定分位数作为最大值
                    
                    # 截断异常值
                    clipped_values = df[feature].clip(min_val, max_val)
                    
                    if max_val > min_val:
                        df[f'{feature}_norm'] = (clipped_values - min_val) / (max_val - min_val)
                    else:
                        df[f'{feature}_norm'] = 0.5  # 如果值都相同，设为中间值
                        
                elif strategy['method'] == 'minmax':
                    # 标准Min-Max归一化
                    min_val = df[feature].min()
                    max_val = df[feature].max()
                    if max_val > min_val:
                        df[f'{feature}_norm'] = (df[feature] - min_val) / (max_val - min_val)
                    else:
                        df[f'{feature}_norm'] = 0.0
                        
        return df.to_dict('records')
    
    def integrate_features(self, rqa_config='m2_tau1_eps0.055_lmin2'):
        """整合所有特征数据"""
        print(f"🔄 开始整合真实数据特征 ({rqa_config})...")
        
        try:
            # 1. 加载各类数据
            game_durations = self.load_calibrated_data()
            roi_features = self.load_roi_features() 
            rqa_features = self.load_rqa_features(rqa_config)
            
            # 2. 合并数据
            integrated_data = []
            all_session_ids = set(game_durations.keys()) | set(roi_features.keys()) | set(rqa_features.keys())
            
            for session_id in all_session_ids:
                # 解析subject_id和task_id
                if 'q' in session_id:
                    # 例如: n1q1 -> subject_id=n1q, task_id=Q1
                    parts = session_id.split('q')
                    if len(parts) == 2:
                        subject_id = f"{parts[0]}q"
                        task_id = f"Q{parts[1]}"
                    else:
                        continue
                else:
                    # 例如: m10 -> 需要从其他数据源推断任务
                    # 这种情况比较复杂，先跳过
                    continue
                
                # 确定组别
                if session_id.startswith('n'):
                    group_type = 'control'
                elif session_id.startswith('m'):
                    group_type = 'mci'
                elif session_id.startswith('ad'):
                    group_type = 'ad'
                else:
                    continue
                
                # 整合特征
                record = {
                    'session_id': session_id,
                    'subject_id': subject_id,
                    'task_id': task_id,
                    'group_type': group_type,
                    
                    # 游戏时长
                    'game_duration': game_durations.get(session_id, 0),
                    
                    # ROI特征
                    'roi_kw_time': roi_features.get(session_id, {}).get('KW', 0),
                    'roi_inst_time': roi_features.get(session_id, {}).get('INST', 0),
                    'roi_bg_time': roi_features.get(session_id, {}).get('BG', 0),
                    
                    # RQA特征
                    'rr_1d': rqa_features.get(session_id, {}).get('rr_1d', 0),
                    'det_1d': rqa_features.get(session_id, {}).get('det_1d', 0),
                    'ent_1d': rqa_features.get(session_id, {}).get('ent_1d', 0),
                    'rr_2d': rqa_features.get(session_id, {}).get('rr_2d', 0),
                    'det_2d': rqa_features.get(session_id, {}).get('det_2d', 0),
                    'ent_2d': rqa_features.get(session_id, {}).get('ent_2d', 0)
                }
                
                integrated_data.append(record)
            
            # 3. 归一化
            normalized_data = self.normalize_features(integrated_data)
            
            # 4. 保存结果
            self.save_integrated_results(normalized_data, rqa_config)
            
            print(f"✅ 特征整合完成: {len(normalized_data)} 条记录")
            return normalized_data
            
        except Exception as e:
            print(f"❌ 特征整合失败: {e}")
            raise e
    
    def save_integrated_results(self, data, rqa_config):
        """保存整合结果"""
        config_dir = os.path.join(self.output_path, rqa_config)
        os.makedirs(config_dir, exist_ok=True)
        
        # 保存数据
        df = pd.DataFrame(data)
        data_file = os.path.join(config_dir, 'integrated_features_summary.csv')
        df.to_csv(data_file, index=False, encoding='utf-8')
        
        # 保存元数据
        metadata = {
            'rqa_config': rqa_config,
            'generated_at': datetime.now().isoformat(),
            'record_count': len(data),
            'features': list(df.columns),
            'data_sources': {
                'calibrated_data': 'game_duration',
                'roi_events': 'roi_*_time',
                'rqa_results': 'rr_*, det_*, ent_*'
            }
        }
        
        metadata_file = os.path.join(config_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 结果已保存到: {config_dir}")
    
    def load_cached_results(self, rqa_config):
        """加载缓存的整合结果"""
        config_dir = os.path.join(self.output_path, rqa_config)
        data_file = os.path.join(config_dir, 'integrated_features_summary.csv')
        
        if os.path.exists(data_file):
            try:
                df = pd.read_csv(data_file)
                return df.to_dict('records')
            except Exception as e:
                print(f"❌ 加载缓存失败: {e}")
        
        return None
    
    def get_available_rqa_configs(self):
        """获取所有可用的RQA配置"""
        configs = []
        rqa_results_path = os.path.join('data', 'rqa_pipeline_results')
        
        if not os.path.exists(rqa_results_path):
            return configs
        
        try:
            # 扫描所有RQA配置目录
            config_dirs = [d for d in os.listdir(rqa_results_path) 
                          if os.path.isdir(os.path.join(rqa_results_path, d))]
            
            for config_dir in config_dirs:
                # 检查是否有RQA结果文件
                config_path = os.path.join(rqa_results_path, config_dir, 'step1_rqa_calculation')
                if os.path.exists(config_path):
                    rqa_files = glob.glob(os.path.join(config_path, 'RQA_1D2D_summary_*.csv'))
                    if rqa_files:
                        # 解析配置参数
                        config_info = self.parse_rqa_config(config_dir)
                        config_info['id'] = config_dir
                        config_info['file_count'] = len(rqa_files)
                        configs.append(config_info)
        
        except Exception as e:
            print(f"❌ 扫描RQA配置失败: {e}")
        
        return configs
    
    def parse_rqa_config(self, config_str):
        """解析RQA配置字符串"""
        # 例如: m2_tau1_eps0.055_lmin2
        parts = config_str.split('_')
        config = {
            'name': config_str,
            'display_name': config_str,
            'm': 'Unknown',
            'tau': 'Unknown', 
            'eps': 'Unknown',
            'lmin': 'Unknown'
        }
        
        try:
            display_parts = []
            for part in parts:
                if part.startswith('m') and len(part) > 1 and part[1:].isdigit():
                    config['m'] = part[1:]
                    display_parts.append(f"m={part[1:]}")
                elif part.startswith('tau') and len(part) > 3:
                    config['tau'] = part[3:]
                    display_parts.append(f"τ={part[3:]}")
                elif part.startswith('eps') and len(part) > 3:
                    config['eps'] = part[3:]
                    display_parts.append(f"ε={part[3:]}")
                elif part.startswith('lmin') and len(part) > 4 and part[4:].isdigit():
                    config['lmin'] = part[4:]
                    display_parts.append(f"l_min={part[4:]}")
            
            if display_parts:
                config['display_name'] = ', '.join(display_parts)
        
        except Exception as e:
            print(f"❌ 解析RQA配置失败 {config_str}: {e}")
        
        return config
    
    def get_data_statistics(self):
        """获取数据统计信息"""
        stats = {
            'total_subjects': 0,
            'total_sessions': 0,
            'total_tasks': 5,  # Q1-Q5
            'normalized_features': 0
        }
        
        try:
            subjects = set()
            sessions = 0
            
            # 统计校准数据
            for group in ['control_calibrated', 'mci_calibrated', 'ad_calibrated']:
                group_path = os.path.join('data', group)
                if os.path.exists(group_path):
                    for subject_dir in os.listdir(group_path):
                        subject_path = os.path.join(group_path, subject_dir)
                        if os.path.isdir(subject_path):
                            # 提取受试者ID
                            if group.startswith('control'):
                                subject_id = subject_dir.replace('control_group_', 'n')
                            elif group.startswith('mci'):
                                subject_id = subject_dir.replace('mci_group_', 'm')
                            elif group.startswith('ad'):
                                subject_id = subject_dir.replace('ad_group_', 'ad')
                            
                            subjects.add(subject_id)
                            
                            # 统计会话数（CSV文件数）
                            csv_files = [f for f in os.listdir(subject_path) if f.endswith('.csv')]
                            sessions += len(csv_files)
            
            stats['total_subjects'] = len(subjects)
            stats['total_sessions'] = sessions
            
            # 统计归一化特征数（原始+归一化）
            feature_names = [
                'game_duration', 'roi_kw_time', 'roi_inst_time', 'roi_bg_time',
                'rr_1d', 'det_1d', 'ent_1d', 'rr_2d', 'det_2d', 'ent_2d'
            ]
            # 原始特征 + 归一化特征 + 标识字段
            stats['normalized_features'] = len(feature_names) * 2 + 4  # session_id, subject_id, task_id, group_type
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
        
        return stats

# 创建全局整合器实例
integrator = RealDataIntegrator()

@real_data_bp.route('/api/available-rqa-configs', methods=['GET'])
def get_available_rqa_configs():
    """获取可用的RQA配置"""
    try:
        configs = integrator.get_available_rqa_configs()
        return jsonify({
            'success': True,
            'configs': configs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@real_data_bp.route('/api/data-statistics', methods=['GET'])
def get_data_statistics():
    """获取数据统计信息"""
    try:
        stats = integrator.get_data_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@real_data_bp.route('/api/integrated-features/<rqa_config>', methods=['GET'])
def get_integrated_features(rqa_config):
    """获取指定RQA配置的整合特征数据"""
    try:
        data = integrator.load_cached_results(rqa_config)
        
        if data is None:
            return jsonify({
                'success': False,
                'error': '缓存数据不存在，请先运行数据整合'
            }), 404
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@real_data_bp.route('/api/integrate-real-features', methods=['POST'])
def integrate_real_features():
    """整合真实特征数据"""
    try:
        data = request.get_json()
        rqa_config = data.get('rqa_config', 'm2_tau1_eps0.055_lmin2')
        
        # 执行整合
        integrated_data = integrator.integrate_features(rqa_config)
        
        return jsonify(integrated_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@real_data_bp.route('/api/save-module8-results', methods=['POST'])
def save_module8_results():
    """保存模块8分析结果"""
    try:
        data = request.get_json()
        
        # 获取参数
        csv_content = data.get('data', '')
        rqa_config = data.get('rqa_config', '')
        filename = data.get('filename', '')
        content_type = data.get('content_type', 'text/csv')
        
        if not csv_content or not rqa_config or not filename:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: data, rqa_config, filename'
            }), 400
        
        # 创建保存目录
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'module8_analysis_results')
        rqa_dir = os.path.join(base_dir, rqa_config)
        os.makedirs(rqa_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(rqa_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        print(f"✅ 模块8文件已保存: {file_path}")
        
        return jsonify({
            'success': True,
            'message': f'文件已保存: {filename}',
            'file_path': file_path
        })
        
    except Exception as e:
        print(f"❌ 保存模块8文件失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def register_real_data_routes(app):
    """注册真实数据整合路由"""
    app.register_blueprint(real_data_bp)
    print("✅ 真实数据整合API路由已注册")