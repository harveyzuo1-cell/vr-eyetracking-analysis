# -*- coding: utf-8 -*-
"""
增强版VR眼动数据分析器
提供完整的眼动数据分析功能，包括IVT算法、ROI分析、统计计算等
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import cv2
from scipy import ndimage

class EnhancedEyetrackingAnalyzer:
    """增强版眼动数据分析器"""
    
    def __init__(self, config_file: str = "config/eyetracking_analysis_config.json"):
        """
        初始化增强版分析器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.load_config()
        
        # 设置数据路径
        self.data_sources = self.config.get("data_sources", {})
        self.background_img_dir = self.config.get("background_images", {}).get("base_path", "data/background_images")
        
        # IVT算法参数
        self.ivt_params = self.config.get("ivt_parameters", {})
        self.velocity_threshold = self.ivt_params.get("velocity_threshold", 40.0)
        self.min_fixation_duration = self.ivt_params.get("min_fixation_duration", 100)
        self.velocity_max_limit = self.ivt_params.get("velocity_max_limit", 1000.0)
        
        # ROI定义
        self.roi_definitions = self.config.get("roi_definitions", {})
        
        print(f"✅ 增强版眼动分析器已初始化")
        print(f"📁 数据源: {len(self.data_sources)} 个")
        print(f"🎯 ROI定义: {len(self.roi_definitions)} 个问题")
        print(f"🔬 IVT速度阈值: {self.velocity_threshold}°/s")
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"⚠️  配置文件不存在: {self.config_file}")
            self.config = self.get_default_config()
        except json.JSONDecodeError as e:
            print(f"⚠️  配置文件格式错误: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "data_sources": {
                "control_calibrated": "data/control_calibrated",
                "mci_calibrated": "data/mci_calibrated", 
                "ad_calibrated": "data/ad_calibrated"
            },
            "background_images": {
                "base_path": "data/background_images"
            },
            "ivt_parameters": {
                "velocity_threshold": 40.0,
                "min_fixation_duration": 100,
                "velocity_max_limit": 1000.0
            },
            "roi_definitions": {}
        }
    
    def analyze_eyetracking_data(self, file_path: str, question: str, debug: bool = False) -> Dict:
        """
        分析眼动数据文件
        
        Args:
            file_path: 数据文件路径
            question: 问题编号 (如 'q1', 'q2')
            debug: 是否开启调试模式
            
        Returns:
            分析结果字典
        """
        try:
            if debug:
                print(f"🔍 开始分析: {file_path}")
            
            # 加载数据
            df = pd.read_csv(file_path)
            if debug:
                print(f"📊 数据点数: {len(df)}")

            # 支持两种列名格式
            if 'GazePointX_normalized' in df.columns and 'GazePointY_normalized' in df.columns:
                df = df.rename(columns={
                    'GazePointX_normalized': 'x',
                    'GazePointY_normalized': 'y'
                })
                if debug:
                    print(f"✅ 已将列名从 GazePointX/Y_normalized 重命名为 x/y")

            # 数据预处理
            df = self.preprocess_data(df, debug)
            
            # IVT算法分析
            df = self.apply_ivt_algorithm(df, debug)
            
            # ROI分析
            roi_stats, df = self.analyze_roi(df, question, debug)
            
            # 计算整体统计
            overall_stats = self.calculate_overall_statistics(df, debug)
            
            # 提取事件
            fixations = self.extract_fixations(df)
            saccades = self.extract_saccades(df)
            
            result = {
                'success': True,
                'data': df,
                'roi_statistics': roi_stats,
                'overall_statistics': overall_stats,
                'fixations': fixations,
                'saccades': saccades,
                'roi_definitions': self.get_roi_definition(question),
                'question': question,
                'file_path': file_path
            }
            
            if debug:
                print(f"✅ 分析完成: {len(fixations)}个注视, {len(saccades)}个扫视")
            
            return result
            
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {'error': error_msg}
    
    def preprocess_data(self, df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
        """数据预处理"""
        # 确保基本列存在
        required_cols = ['x', 'y']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"缺少必要列: {col}")
        
        # 过滤无效数据
        df = df.dropna(subset=['x', 'y'])
        df = df[(df['x'] >= 0) & (df['x'] <= 1) & (df['y'] >= 0) & (df['y'] <= 1)]
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        if debug:
            print(f"📊 预处理后数据点: {len(df)}")
        
        return df
    
    def apply_ivt_algorithm(self, df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
        """应用IVT(速度阈值)算法分类注视和扫视"""
        if len(df) < 2:
            df['event_type'] = 'fixation'
            df['velocity'] = 0.0
            return df
        
        # 计算速度
        velocities = []
        for i in range(len(df)):
            if i == 0:
                velocities.append(0.0)
            else:
                # 计算角速度 (简化处理)
                dx = (df.iloc[i]['x'] - df.iloc[i-1]['x']) * 110  # 假设110度视场角
                dy = (df.iloc[i]['y'] - df.iloc[i-1]['y']) * 110
                dt = 1/60.0  # 假设60Hz采样率
                
                velocity = np.sqrt(dx**2 + dy**2) / dt
                velocity = min(velocity, self.velocity_max_limit)  # 限制最大速度
                velocities.append(velocity)
        
        df['velocity'] = velocities
        
        # 基于速度阈值分类
        df['event_type'] = df['velocity'].apply(
            lambda v: 'saccade' if v > self.velocity_threshold else 'fixation'
        )
        
        if debug:
            fixation_count = len(df[df['event_type'] == 'fixation'])
            saccade_count = len(df[df['event_type'] == 'saccade'])
            print(f"🎯 IVT分类: {fixation_count}个注视点, {saccade_count}个扫视点")
        
        return df
    
    def analyze_roi(self, df: pd.DataFrame, question: str, debug: bool = False) -> Tuple[Dict, pd.DataFrame]:
        """分析ROI区域统计"""
        roi_def = self.get_roi_definition(question)
        roi_stats = {}
        
        # 初始化ROI列
        df['current_roi'] = 'None'
        df['SequenceID'] = 0
        df['EnterExitFlag'] = ''
        
        sequence_id = 0
        
        # 分析每个ROI类型
        for roi_type in ['keywords', 'instructions', 'background']:
            rois = roi_def.get(roi_type, [])
            
            for roi in rois:
                roi_name = roi[0]
                x_min, y_min, x_max, y_max = roi[1], roi[2], roi[3], roi[4]
                
                # 标准化坐标
                x_min, x_max = min(x_min, x_max), max(x_min, x_max)
                y_min, y_max = min(y_min, y_max), max(y_min, y_max)
                
                # 计算在ROI内的点
                in_roi = (
                    (df['x'] >= x_min) & (df['x'] <= x_max) &
                    (df['y'] >= y_min) & (df['y'] <= y_max)
                )
                
                # 更新当前ROI
                df.loc[in_roi, 'current_roi'] = roi_name
                
                # 检测进入和退出事件
                prev_in_roi = False
                for i, is_in_roi in enumerate(in_roi):
                    if is_in_roi and not prev_in_roi:
                        # 进入ROI
                        sequence_id += 1
                        df.at[i, 'SequenceID'] = sequence_id
                        df.at[i, 'EnterExitFlag'] = 'Enter'
                    elif not is_in_roi and prev_in_roi:
                        # 退出ROI
                        if i > 0:
                            df.at[i-1, 'SequenceID'] = sequence_id
                            df.at[i-1, 'EnterExitFlag'] = 'Exit'
                    
                    prev_in_roi = is_in_roi
                
                # 计算ROI统计
                roi_points = df[in_roi]
                fixation_points = roi_points[roi_points['event_type'] == 'fixation']
                
                roi_stats[roi_name] = {
                    'TotalPoints': len(roi_points),
                    'FixationPoints': len(fixation_points),
                    'FixTime': len(fixation_points) / 60.0,  # 假设60Hz
                    'AvgVelocity': roi_points['velocity'].mean() if len(roi_points) > 0 else 0.0,
                    'EnterCount': len(df[(df['current_roi'] == roi_name) & (df['EnterExitFlag'] == 'Enter')])
                }
        
        if debug:
            print(f"🎯 ROI分析: {len([k for k, v in roi_stats.items() if v['TotalPoints'] > 0])}个活跃ROI")
        
        return roi_stats, df
    
    def calculate_overall_statistics(self, df: pd.DataFrame, debug: bool = False) -> Dict:
        """计算整体统计信息"""
        fixations = df[df['event_type'] == 'fixation']
        saccades = df[df['event_type'] == 'saccade']
        
        stats = {
            'total_points': len(df),
            'total_duration': len(df) / 60.0 * 1000,  # 转换为毫秒
            'fixation_count': len(fixations),
            'saccade_count': len(saccades),
            'avg_velocity': df['velocity'].mean(),
            'max_velocity': df['velocity'].max(),
            'roi_sequence_count': df['SequenceID'].max() if 'SequenceID' in df.columns else 0
        }
        
        return stats
    
    def extract_fixations(self, df: pd.DataFrame) -> List[Dict]:
        """提取注视事件"""
        fixations = []
        fixation_data = df[df['event_type'] == 'fixation']
        
        if len(fixation_data) == 0:
            return fixations
        
        # 简化处理：每个连续的注视点组成一个注视事件
        current_fixation = []
        
        for i, row in fixation_data.iterrows():
            if len(current_fixation) == 0:
                current_fixation = [row]
            else:
                # 检查是否连续
                if i - current_fixation[-1].name <= 5:  # 允许小间隙
                    current_fixation.append(row)
                else:
                    # 保存当前注视事件
                    if len(current_fixation) >= 3:  # 最少3个点
                        fixations.append({
                            'start_time': current_fixation[0].name / 60.0 * 1000,
                            'duration': len(current_fixation) / 60.0 * 1000,
                            'x': np.mean([p['x'] for p in current_fixation]),
                            'y': np.mean([p['y'] for p in current_fixation]),
                            'point_count': len(current_fixation)
                        })
                    current_fixation = [row]
        
        # 处理最后一个注视事件
        if len(current_fixation) >= 3:
            fixations.append({
                'start_time': current_fixation[0].name / 60.0 * 1000,
                'duration': len(current_fixation) / 60.0 * 1000,
                'x': np.mean([p['x'] for p in current_fixation]),
                'y': np.mean([p['y'] for p in current_fixation]),
                'point_count': len(current_fixation)
            })
        
        return fixations
    
    def extract_saccades(self, df: pd.DataFrame) -> List[Dict]:
        """提取扫视事件"""
        saccades = []
        saccade_data = df[df['event_type'] == 'saccade']
        
        for i, row in saccade_data.iterrows():
            saccades.append({
                'time': i / 60.0 * 1000,
                'x': row['x'],
                'y': row['y'],
                'velocity': row['velocity']
            })
        
        return saccades
    
    def get_roi_definition(self, question: str) -> Dict:
        """获取指定问题的ROI定义"""
        return self.roi_definitions.get(question, {
            'keywords': [],
            'instructions': [],
            'background': []
        })
    
    def normalize_roi(self, roi_list: List) -> List:
        """标准化ROI坐标"""
        normalized = []
        for roi in roi_list:
            if len(roi) >= 5:
                name, x1, y1, x2, y2 = roi[0], roi[1], roi[2], roi[3], roi[4]
                # 确保坐标在[0,1]范围内
                x1, x2 = max(0, min(1, x1)), max(0, min(1, x2))
                y1, y2 = max(0, min(1, y1)), max(0, min(1, y2))
                normalized.append([name, x1, y1, x2, y2])
        return normalized 