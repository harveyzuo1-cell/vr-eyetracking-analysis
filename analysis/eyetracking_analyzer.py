# -*- coding: utf-8 -*-
"""
VR眼动数据分析器
提供IVT分析、ROI分析、统计计算等功能
"""
import os
import sys
import cv2
import math
import json
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from scipy import stats
from typing import Dict, List, Tuple, Optional

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class EyetrackingAnalyzer:
    """眼动数据分析器"""
    
    def __init__(self, config_file: str = "config/eyetracking_analysis_config.json"):
        """
        初始化分析器
        
        Args:
            config_file: 分析配置文件路径
        """
        self.config_file = config_file
        self.config = self.load_config()
        
        # 加载关键参数
        self.ivt_velocity_threshold = self.config.get("ivt_parameters", {}).get("velocity_threshold", 30.0)
        self.ivt_min_fixation_duration = self.config.get("ivt_parameters", {}).get("min_fixation_duration", 100)
        self.velocity_max_limit = self.config.get("ivt_parameters", {}).get("velocity_max_limit", 500.0)
        
        # 数据源路径
        self.data_sources = self.config.get("data_sources", {})
        self.background_img_dir = self.data_sources.get("background_images", "data/background_images")
        
        # ROI定义
        self.roi_definitions = self.config.get("roi_definitions", {})
        
    def load_config(self) -> dict:
        """加载分析配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"❌ 无法加载分析配置: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "ivt_parameters": {
                "velocity_threshold": 30.0,
                "min_fixation_duration": 100,
                "velocity_max_limit": 500.0
            },
            "data_sources": {
                "control_calibrated": "data/control_calibrated",
                "mci_calibrated": "data/mci_calibrated",
                "ad_calibrated": "data/ad_calibrated",
                "background_images": "data/background_images"
            },
            "roi_definitions": {}
        }
    
    def compute_velocity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算眼动速度
        
        Args:
            df: 眼动数据DataFrame
            
        Returns:
            包含速度的DataFrame
        """
        result_df = df.copy()
        
        if len(result_df) < 2:
            result_df['velocity'] = 0.0
            return result_df
        
        velocities = []
        
        for i in range(len(result_df)):
            if i == 0:
                velocities.append(0.0)
            else:
                # 计算时间差
                dt = result_df.iloc[i]['time_diff'] / 1000.0  # 转换为秒
                
                if dt > 0:
                    # 计算坐标差值
                    dx = result_df.iloc[i]['x'] - result_df.iloc[i-1]['x']
                    dy = result_df.iloc[i]['y'] - result_df.iloc[i-1]['y']
                    
                    # 计算像素距离
                    pixel_distance = math.sqrt(dx**2 + dy**2)
                    
                    # 转换为角速度 (假设屏幕视角)
                    # 这里使用简化的转换，实际应用中需要根据具体的VR设备参数调整
                    angular_distance = pixel_distance * 110.0  # 假设110度视场角
                    velocity = angular_distance / dt
                    
                    # 限制最大速度
                    velocity = min(velocity, self.velocity_max_limit)
                    velocities.append(velocity)
                else:
                    velocities.append(0.0)
        
        result_df['velocity'] = velocities
        return result_df
    
    def ivt_segmentation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        IVT (Velocity-Threshold) 眼动事件分割
        
        Args:
            df: 包含速度的眼动数据DataFrame
            
        Returns:
            包含事件标签的DataFrame
        """
        result_df = df.copy()
        
        if 'velocity' not in result_df.columns:
            result_df = self.compute_velocity(result_df)
        
        # 基于速度阈值分类事件
        result_df['event_type'] = 'fixation'
        result_df.loc[result_df['velocity'] > self.ivt_velocity_threshold, 'event_type'] = 'saccade'
        
        # 后处理：合并短暂的固视和扫视
        events = []
        current_event = None
        current_start = 0
        
        for i, row in result_df.iterrows():
            if current_event is None:
                current_event = row['event_type']
                current_start = i
            elif current_event != row['event_type']:
                # 事件类型变化
                duration = result_df.iloc[i-1]['time_diff'] if i > 0 else 0
                
                # 检查是否需要合并短暂事件
                if current_event == 'fixation' and duration < self.ivt_min_fixation_duration:
                    # 短暂固视标记为扫视
                    for j in range(current_start, i):
                        result_df.iloc[j, result_df.columns.get_loc('event_type')] = 'saccade'
                
                current_event = row['event_type']
                current_start = i
        
        return result_df
    
    def extract_question_from_id(self, data_id: str) -> str:
        """
        从数据ID中提取问题编号，用于ROI复用
        
        Args:
            data_id: 数据ID，如 "n2q3" 或 "m15q2"
            
        Returns:
            问题编号，如 "q3" 或 "q2"
        """
        # 匹配模式：nXXqY, mXXqY, adXXqY
        import re
        match = re.search(r'q(\d+)', data_id)
        if match:
            return f"q{match.group(1)}"
        return "q1"  # 默认返回q1
    
    def label_roi_sequence(self, df: pd.DataFrame, question: str) -> pd.DataFrame:
        """
        标记ROI序列
        
        Args:
            df: 眼动数据DataFrame
            question: 问题编号，如 "q1"
            
        Returns:
            包含ROI标签的DataFrame
        """
        result_df = df.copy()
        
        # 获取ROI定义
        roi_def = self.roi_definitions.get(question, {})
        regions = roi_def.get('regions', [])
        
        if not regions:
            result_df['roi'] = 'unknown'
            return result_df
        
        # 为每个数据点分配ROI
        roi_labels = []
        
        for _, row in result_df.iterrows():
            x, y = row['x'], row['y']
            roi_label = self.find_roi_label_for_point(x, y, regions)
            roi_labels.append(roi_label)
        
        result_df['roi'] = roi_labels
        return result_df
    
    def find_roi_label_for_point(self, x: float, y: float, regions: List[Dict]) -> str:
        """
        找到点所属的ROI区域
        
        Args:
            x, y: 坐标点
            regions: ROI区域定义列表
            
        Returns:
            ROI标签
        """
        for region in regions:
            if region['type'] == 'rectangle':
                x1, y1, x2, y2 = region['coordinates']
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return region['name']
        
        return 'outside'
    
    def calculate_roi_statistics(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        计算ROI统计信息
        
        Args:
            df: 包含ROI标签的眼动数据DataFrame
            
        Returns:
            ROI统计字典
        """
        if 'roi' not in df.columns:
            return {}
        
        stats_dict = {}
        
        # 按ROI分组统计
        for roi in df['roi'].unique():
            roi_data = df[df['roi'] == roi]
            
            if len(roi_data) == 0:
                continue
            
            # 基本统计
            total_time = roi_data['time_diff'].sum()
            visit_count = self._count_roi_visits(df, roi)
            
            # 固视统计
            fixations = roi_data[roi_data.get('event_type', 'fixation') == 'fixation']
            fixation_time = fixations['time_diff'].sum() if len(fixations) > 0 else 0
            fixation_count = len(fixations)
            
            # 平均固视时长
            avg_fixation_duration = fixation_time / fixation_count if fixation_count > 0 else 0
            
            stats_dict[roi] = {
                'total_time': total_time,
                'visit_count': visit_count,
                'fixation_time': fixation_time,
                'fixation_count': fixation_count,
                'avg_fixation_duration': avg_fixation_duration,
                'time_percentage': (total_time / df['time_diff'].sum() * 100) if df['time_diff'].sum() > 0 else 0
            }
        
        return stats_dict
    
    def _count_roi_visits(self, df: pd.DataFrame, target_roi: str) -> int:
        """
        计算ROI访问次数（进入次数）
        
        Args:
            df: 眼动数据DataFrame
            target_roi: 目标ROI名称
            
        Returns:
            访问次数
        """
        if 'roi' not in df.columns:
            return 0
        
        visit_count = 0
        prev_roi = None
        
        for roi in df['roi']:
            if roi == target_roi and prev_roi != target_roi:
                visit_count += 1
            prev_roi = roi
        
        return visit_count
    
    def get_roi_definition(self, question: str) -> Dict:
        """
        获取指定问题的ROI定义
        
        Args:
            question: 问题编号，如 "q1"
            
        Returns:
            ROI定义字典
        """
        return self.roi_definitions.get(question, {})
    
    def analyze_eyetracking_data(self, data_file: str, question: str) -> Dict:
        """
        完整的眼动数据分析
        
        Args:
            data_file: 数据文件路径
            question: 问题编号
            
        Returns:
            分析结果字典
        """
        try:
            # 读取数据
            df = pd.read_csv(data_file)
            
            if len(df) == 0:
                return {'error': '数据文件为空'}
            
            # 确保必要列存在
            required_cols = ['x', 'y', 'time_diff']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {'error': f'缺少必要列: {missing_cols}'}
            
            # 步骤1：计算速度
            df = self.compute_velocity(df)
            
            # 步骤2：IVT分割
            df = self.ivt_segmentation(df)
            
            # 步骤3：ROI标记
            df = self.label_roi_sequence(df, question)
            
            # 步骤4：计算统计
            roi_stats = self.calculate_roi_statistics(df)
            
            # 步骤5：整体统计
            total_duration = df['time_diff'].sum()
            fixation_data = df[df['event_type'] == 'fixation']
            saccade_data = df[df['event_type'] == 'saccade']
            
            overall_stats = {
                'total_duration': total_duration,
                'total_points': len(df),
                'fixation_count': len(fixation_data),
                'saccade_count': len(saccade_data),
                'fixation_time': fixation_data['time_diff'].sum() if len(fixation_data) > 0 else 0,
                'saccade_time': saccade_data['time_diff'].sum() if len(saccade_data) > 0 else 0,
                'avg_velocity': df['velocity'].mean(),
                'max_velocity': df['velocity'].max()
            }
            
            return {
                'success': True,
                'data': df,
                'roi_statistics': roi_stats,
                'overall_statistics': overall_stats,
                'question': question
            }
            
        except Exception as e:
            return {'error': f'分析过程中出错: {str(e)}'}

def main():
    """主函数 - 用于测试"""
    analyzer = EyetrackingAnalyzer()
    print("🔍 眼动数据分析器")
    print("=" * 50)
    print("配置已加载:")
    print(f"  IVT速度阈值: {analyzer.ivt_velocity_threshold} deg/s")
    print(f"  最小固视时长: {analyzer.ivt_min_fixation_duration} ms")
    print(f"  ROI定义数量: {len(analyzer.roi_definitions)}")
    print("\n使用示例:")
    print("analyzer = EyetrackingAnalyzer()")
    print("result = analyzer.analyze_eyetracking_data('data.csv', 'q1')")

if __name__ == "__main__":
    main() 