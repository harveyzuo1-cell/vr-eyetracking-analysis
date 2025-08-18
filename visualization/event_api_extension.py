#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件分析API扩展模块
为enhanced_web_visualizer.py添加事件分析数据查询功能
"""

import os
import pandas as pd
import numpy as np
from flask import request, jsonify
from typing import Dict, Any

def clean_nan_values(obj):
    """
    递归清理对象中的NaN值，将其替换为None（JSON中的null）
    """
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, (float, np.float64, np.float32)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    else:
        return obj

def add_event_analysis_routes(app, visualizer_instance):
    """
    为Flask应用添加事件分析路由
    
    Args:
        app: Flask应用实例
        visualizer_instance: EnhancedWebVisualizer实例
    """
    
    @app.route('/api/event-analysis/data', methods=['GET'])
    def get_event_analysis_data():
        """获取事件分析数据"""
        try:
            data_type = request.args.get('type', 'events')  # 'events' or 'roi'
            group = request.args.get('group', 'all')  # 'all', 'control', 'mci', 'ad'
            event_type = request.args.get('event_type', 'all')  # 'all', 'fixation', 'saccade'
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 100))
            
            # 确定数据文件路径
            data_dir = "data/event_analysis_results"
            
            if data_type == 'events':
                if group == 'all':
                    file_path = os.path.join(data_dir, "All_Events.csv")
                else:
                    file_path = os.path.join(data_dir, f"{group}_All_Events.csv")
            else:  # roi
                if group == 'all':
                    file_path = os.path.join(data_dir, "All_ROI_Summary.csv")
                else:
                    file_path = os.path.join(data_dir, f"{group}_All_ROI_Summary.csv")
            
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'error': f'数据文件不存在: {file_path}'
                }), 404
            
            # 读取数据
            df = pd.read_csv(file_path)
            
            # 应用筛选
            if data_type == 'events' and event_type != 'all':
                df = df[df['EventType'] == event_type]
            
            # 分页
            total_count = len(df)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_df = df.iloc[start_idx:end_idx]
            
            # 转换为字典格式
            data_list = paginated_df.to_dict('records')
            
            # 统计信息
            stats = {}
            if data_type == 'events':
                if 'EventType' in df.columns:
                    stats['event_counts'] = df['EventType'].value_counts().to_dict()
                if 'Group' in df.columns:
                    stats['group_counts'] = df['Group'].value_counts().to_dict()
                if 'ROI' in df.columns:
                    roi_counts = df.dropna(subset=['ROI'])['ROI'].value_counts().head(10).to_dict()
                    stats['top_rois'] = roi_counts
            else:  # roi
                if 'Group' in df.columns:
                    stats['group_counts'] = df['Group'].value_counts().to_dict()
                if 'ROI' in df.columns:
                    stats['unique_rois'] = df['ROI'].nunique()
                    total_fix_time = df['FixTime'].sum()
                    avg_fix_time = df['FixTime'].mean()
                    stats['total_fix_time'] = total_fix_time if not pd.isna(total_fix_time) else 0
                    stats['avg_fix_time'] = avg_fix_time if not pd.isna(avg_fix_time) else 0
            
            # 清理所有NaN值
            response_data = {
                'success': True,
                'data': clean_nan_values(data_list),
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'stats': clean_nan_values(stats)
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            print(f"事件分析数据查询错误: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }), 500
    
    @app.route('/api/event-analysis/summary', methods=['GET'])
    def get_event_analysis_summary():
        """获取事件分析数据摘要"""
        try:
            data_dir = "data/event_analysis_results"
            
            summary = {
                'groups': ['control', 'mci', 'ad'],
                'data_files': [],
                'stats': {}
            }
            
            # 检查数据文件是否存在
            for group in summary['groups']:
                events_file = os.path.join(data_dir, f"{group}_All_Events.csv")
                roi_file = os.path.join(data_dir, f"{group}_All_ROI_Summary.csv")
                
                file_info = {
                    'group': group,
                    'events_file_exists': os.path.exists(events_file),
                    'roi_file_exists': os.path.exists(roi_file)
                }
                
                # 如果文件存在，获取基本统计
                if file_info['events_file_exists']:
                    df_events = pd.read_csv(events_file)
                    file_info['event_count'] = len(df_events)
                    file_info['fixation_count'] = len(df_events[df_events['EventType'] == 'fixation'])
                    file_info['saccade_count'] = len(df_events[df_events['EventType'] == 'saccade'])
                
                if file_info['roi_file_exists']:
                    df_roi = pd.read_csv(roi_file)
                    file_info['roi_count'] = len(df_roi)
                    file_info['unique_roi_count'] = df_roi['ROI'].nunique()
                
                summary['data_files'].append(file_info)
            
            # 全局统计
            all_events_file = os.path.join(data_dir, "All_Events.csv")
            all_roi_file = os.path.join(data_dir, "All_ROI_Summary.csv")
            
            if os.path.exists(all_events_file):
                df_all_events = pd.read_csv(all_events_file)
                summary['stats']['total_events'] = len(df_all_events)
                summary['stats']['total_fixations'] = len(df_all_events[df_all_events['EventType'] == 'fixation'])
                summary['stats']['total_saccades'] = len(df_all_events[df_all_events['EventType'] == 'saccade'])
                
                if 'Group' in df_all_events.columns:
                    summary['stats']['group_distribution'] = df_all_events['Group'].value_counts().to_dict()
            
            if os.path.exists(all_roi_file):
                df_all_roi = pd.read_csv(all_roi_file)
                summary['stats']['total_roi_records'] = len(df_all_roi)
                summary['stats']['unique_rois'] = df_all_roi['ROI'].nunique()
                total_fix_time = df_all_roi['FixTime'].sum()
                summary['stats']['total_fixation_time'] = total_fix_time if not pd.isna(total_fix_time) else 0
            
            # 清理NaN值后返回
            return jsonify({
                'success': True,
                'summary': clean_nan_values(summary)
            })
            
        except Exception as e:
            print(f"事件分析摘要查询错误: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }), 500
    
    @app.route('/api/event-analysis/regenerate', methods=['POST'])
    def regenerate_event_analysis_data():
        """重新生成事件分析数据"""
        try:
            # 运行数据生成脚本
            import subprocess
            import sys
            
            result = subprocess.run([
                sys.executable, 'generate_event_analysis_data.py'
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': '事件分析数据重新生成完成',
                    'output': result.stdout
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '数据生成失败',
                    'details': result.stderr
                }), 500
                
        except Exception as e:
            print(f"重新生成事件分析数据错误: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }), 500


def setup_event_analysis_integration(app, visualizer):
    """
    设置事件分析集成
    
    使用方法:
    在enhanced_web_visualizer.py中添加:
    
    try:
        from .event_api_extension import setup_event_analysis_integration
        setup_event_analysis_integration(app, self)
        print("✅ 事件分析功能已启用")
    except ImportError:
        print("⚠️  事件分析功能不可用")
    """
    # 添加路由
    add_event_analysis_routes(app, visualizer)
    
    print("📊 事件分析API路由已添加:")
    print("  - GET  /api/event-analysis/data")
    print("  - GET  /api/event-analysis/summary") 
    print("  - POST /api/event-analysis/regenerate") 