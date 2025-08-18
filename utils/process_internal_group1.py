# -*- coding: utf-8 -*-
"""
控制组第1组数据专用处理器
专门处理项目内的第1组数据（原第21组数据）
"""
import os
import sys
import re
import math
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from scipy import stats

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import *

def parse_new_format(content: str) -> List[Dict]:
    """
    解析新格式的眼动数据
    
    Args:
        content: 原始文件内容
        
    Returns:
        解析后的数据记录列表
    """
    records = []
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # 匹配数据行格式: timestamp x y
        match = re.match(r'(\d+(?:\.\d+)?)\s+([0-9.]+)\s+([0-9.]+)', line)
        if match:
            timestamp_str, x_str, y_str = match.groups()
            
            try:
                timestamp = float(timestamp_str)
                x = float(x_str)
                y = float(y_str)
                
                # 验证坐标范围
                if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                    records.append({
                        'timestamp': timestamp,
                        'x': x,
                        'y': y
                    })
                    
            except ValueError:
                continue
                
    return records

def preprocess_vr_eyetracking(records: List[Dict], fov_deg: float = 110.0, 
                            velocity_threshold: float = 1000.0, 
                            z_score_threshold: float = 3.0) -> pd.DataFrame:
    """
    预处理VR眼动数据
    
    Args:
        records: 原始数据记录
        fov_deg: 视场角度数
        velocity_threshold: 速度过滤阈值 (deg/s)
        z_score_threshold: Z-score过滤阈值
        
    Returns:
        预处理后的DataFrame
    """
    if not records:
        return pd.DataFrame()
        
    # 转换为DataFrame
    df = pd.DataFrame(records)
    
    if len(df) < 2:
        print(f"  平均速度: {0:.2f} deg/s")
        print(f"  最大速度: {0:.2f} deg/s")
        print(f"  最小速度: {0:.2f} deg/s")
        return df
        
    # 排序确保时间顺序
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"  X范围: {df['x'].min():.3f} ~ {df['x'].max():.3f}, "
          f"Y范围: {df['y'].min():.3f} ~ {df['y'].max():.3f}")
    
    # 计算时间差
    df['time_diff'] = df['timestamp'].diff().fillna(0) * 1000  # 转换为毫秒
    
    print(f"  time_diff范围: {df['time_diff'].min():.2f} ms ~ {df['time_diff'].max():.2f} ms")
    
    # 坐标转换为视场角度
    half_fov = fov_deg / 2.0
    df['x_deg'] = (df['x'] - 0.5) * fov_deg  # -55 to +55 度
    df['y_deg'] = (df['y'] - 0.5) * fov_deg  # -55 to +55 度
    
    print(f"\n[映射到视场角] ±{half_fov}°:")
    print(f"  x_deg: {df['x_deg'].min():.3f} to {df['x_deg'].max():.3f}")
    print(f"  y_deg: {df['y_deg'].min():.3f} to {df['y_deg'].max():.3f}")
    
    # 计算角速度
    df['velocity_deg_s'] = 0.0
    
    for i in range(1, len(df)):
        dt = df.iloc[i]['time_diff'] / 1000.0  # 转换为秒
        
        if dt > 0:
            dx_deg = df.iloc[i]['x_deg'] - df.iloc[i-1]['x_deg']
            dy_deg = df.iloc[i]['y_deg'] - df.iloc[i-1]['y_deg']
            
            # 计算欧几里得距离的角度变化
            angular_distance = math.sqrt(dx_deg**2 + dy_deg**2)
            velocity = angular_distance / dt
            
            df.iloc[i, df.columns.get_loc('velocity_deg_s')] = velocity
    
    # 显示速度统计
    print(f"\n[速度统计] velocity_deg_s:")
    print(f"  平均速度: {df['velocity_deg_s'].mean():.2f} deg/s")
    print(f"  最大速度: {df['velocity_deg_s'].max():.2f} deg/s")
    print(f"  最小速度: {df['velocity_deg_s'].min():.2f} deg/s")
    
    # 速度过滤
    initial_count = len(df)
    df = df[df['velocity_deg_s'] <= velocity_threshold]
    after_velocity_filter = len(df)
    
    print(f"\n速度过滤: {initial_count} -> {after_velocity_filter} 行 (阈值: {velocity_threshold} deg/s)")
    
    if len(df) < 2:
        return df
        
    # Z-score过滤异常值
    velocity_z_scores = np.abs(stats.zscore(df['velocity_deg_s']))
    df = df[velocity_z_scores <= z_score_threshold]
    after_z_score_filter = len(df)
    
    print(f"Z-score过滤: {after_velocity_filter} -> {after_z_score_filter} 行 (阈值: {z_score_threshold})")
    
    # 计算扫视速度统计
    saccade_velocities = df[df['velocity_deg_s'] > 30]['velocity_deg_s']  # 认为>30 deg/s为扫视
    if len(saccade_velocities) > 0:
        print(f"平均扫视速度: {saccade_velocities.mean():.2f} deg/s")
    
    # 重新索引
    df = df.reset_index(drop=True)
    
    return df

def main():
    """处理控制组第1组数据"""
    if validate_config():
        print("✓ Configuration validation passed")
    else:
        print("✗ Configuration validation failed")
        return
    
    print("🔄 处理项目内第1组数据 (原第21组)")
    print("=" * 50)
    
    # 定义路径
    raw_dir = "data/control_raw/control_group_1/rawdata"
    processed_dir = "data/control_processed"  # 输出直接到processed
    
    # 确保输出目录存在
    os.makedirs(processed_dir, exist_ok=True)
    
    # 查找TXT文件
    txt_files = []
    for file in os.listdir(raw_dir):
        if file.endswith('.txt'):
            txt_files.append(file)
    
    txt_files.sort()  # 按文件名排序
    
    if not txt_files:
        print(f"⚠️  在 {raw_dir} 中未找到TXT文件")
        return
    
    success_count = 0
    failed_count = 0
    
    # 处理每个文件
    for txt_file in tqdm(txt_files, desc="处理文件"):
        input_path = os.path.join(raw_dir, txt_file)
        
        # 生成输出文件名: n1q1_preprocessed.csv, n1q2_preprocessed.csv, ...
        base_name = os.path.splitext(txt_file)[0]
        output_filename = f"n1q{base_name}_preprocessed.csv"
        output_path = os.path.join(processed_dir, output_filename)
        
        print(f"\n=== 处理: {input_path} ===")
        
        try:
            # 读取文件
            with open(input_path, 'r', encoding=INPUT_ENCODING) as f:
                content = f.read()
            
            # 解析数据
            records = parse_new_format(content)
            print(f"  解析到 {len(records)} 条记录.")
            
            if not records:
                print("  ⚠️  未找到有效数据")
                failed_count += 1
                continue
                
            # 预处理数据
            df = preprocess_vr_eyetracking(
                records, 
                fov_deg=FOV_DEGREE,
                velocity_threshold=VELOCITY_THRESHOLD,
                z_score_threshold=STATISTICS_CONFIG['z_score_threshold']
            )
            
            if df.empty:
                print("  ⚠️  预处理后数据为空")
                failed_count += 1
                continue
            
            # 保存结果
            df.to_csv(output_path, index=False, encoding=OUTPUT_ENCODING)
            print(f"\n最终记录数= {len(df)}")
            print(f"  => 已保存: {output_path}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 处理文件时出错: {e}")
            failed_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ 第1组数据处理完成！")
    print(f"📂 输出目录: {processed_dir}")
    print(f"📊 成功: {success_count}, 失败: {failed_count}, 总计: {len(txt_files)}")

if __name__ == "__main__":
    main() 