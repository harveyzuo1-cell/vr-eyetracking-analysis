# -*- coding: utf-8 -*-
"""
基础眼动数据校准器
提供简单的X,Y坐标偏移校准功能
"""
import os
import sys
import pandas as pd
from tqdm import tqdm
from typing import Tuple

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import *

def calibrate_csv_file(input_file: str, output_file: str, 
                      x_offset: float = -0.030, y_offset: float = -0.140) -> bool:
    """
    校准单个CSV文件的坐标
    
    Args:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径
        x_offset: X坐标偏移量
        y_offset: Y坐标偏移量
        
    Returns:
        校准是否成功
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(input_file)
        
        if 'x' not in df.columns or 'y' not in df.columns:
            print(f"  ❌ 文件缺少x或y列: {input_file}")
            return False
        
        # 记录原始范围
        original_x_range = f"[{df['x'].min():.3f}, {df['x'].max():.3f}]"
        original_y_range = f"[{df['y'].min():.3f}, {df['y'].max():.3f}]"
        
        # 应用偏移
        df['x'] = df['x'] + x_offset
        df['y'] = df['y'] + y_offset
        
        # 记录校准后范围
        calibrated_x_range = f"[{df['x'].min():.3f}, {df['x'].max():.3f}]"
        calibrated_y_range = f"[{df['y'].min():.3f}, {df['y'].max():.3f}]"
        
        # 保存结果
        df.to_csv(output_file, index=False, encoding=OUTPUT_ENCODING)
        
        print(f"    校准参数: x{x_offset:+.3f}, y{y_offset:+.3f}")
        print(f"    原始范围: x{original_x_range}, y{original_y_range}")
        print(f"    校准范围: x{calibrated_x_range}, y{calibrated_y_range}")
        print(f"    数据行数: {len(df)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 校准文件时出错: {e}")
        return False

def calibrate_directory(input_dir: str, output_dir: str,
                       x_offset: float = -0.030, y_offset: float = -0.140,
                       file_pattern: str = "*_preprocessed.csv") -> dict:
    """
    批量校准目录中的CSV文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        x_offset: X坐标偏移量
        y_offset: Y坐标偏移量
        file_pattern: 文件匹配模式
        
    Returns:
        校准统计信息
    """
    import glob
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找匹配的文件
    search_pattern = os.path.join(input_dir, file_pattern)
    csv_files = glob.glob(search_pattern)
    
    if not csv_files:
        print(f"⚠️  在 {input_dir} 中未找到匹配 {file_pattern} 的文件")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    print(f"🔧 校准目录: {input_dir}")
    print(f"📁 输出目录: {output_dir}")
    print(f"📄 找到 {len(csv_files)} 个文件")
    print(f"⚙️  校准参数: x{x_offset:+.3f}, y{y_offset:+.3f}")
    print("=" * 50)
    
    success_count = 0
    failed_count = 0
    
    # 处理每个文件
    for csv_file in tqdm(csv_files, desc="校准文件"):
        filename = os.path.basename(csv_file)
        
        # 生成输出文件名
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_calibrated{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\n  处理: {filename}")
        
        if calibrate_csv_file(csv_file, output_path, x_offset, y_offset):
            print(f"  ✓ 已保存: {output_filename}")
            success_count += 1
        else:
            failed_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ 校准完成!")
    print(f"📊 成功: {success_count}, 失败: {failed_count}, 总计: {len(csv_files)}")
    
    return {
        'total': len(csv_files),
        'success': success_count,
        'failed': failed_count
    }

def calibrate_all_control_groups(x_offset: float = -0.030, y_offset: float = -0.140) -> dict:
    """
    校准所有控制组数据
    
    Args:
        x_offset: X坐标偏移量
        y_offset: Y坐标偏移量
        
    Returns:
        校准统计信息
    """
    processed_dir = "data/control_processed"
    calibrated_dir = "data/control_calibrated"
    
    print("🎯 批量校准所有控制组数据")
    print("=" * 60)
    
    if not os.path.exists(processed_dir):
        print(f"❌ 预处理数据目录不存在: {processed_dir}")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    # 校准每个控制组
    total_stats = {'total': 0, 'success': 0, 'failed': 0}
    
    for group_num in range(CONTROL_GROUP_START, CONTROL_GROUP_END + 1):
        group_dir = os.path.join(processed_dir, f"control_group_{group_num}")
        
        if not os.path.exists(group_dir):
            print(f"⚠️  跳过不存在的目录: {group_dir}")
            continue
        
        print(f"\n=== 校准 control_group_{group_num} ===")
        
        # 为每个组创建输出目录
        group_output_dir = os.path.join(calibrated_dir, f"control_group_{group_num}")
        
        # 校准这个组
        stats = calibrate_directory(group_dir, group_output_dir, x_offset, y_offset)
        
        # 累计统计
        total_stats['total'] += stats['total']
        total_stats['success'] += stats['success']
        total_stats['failed'] += stats['failed']
    
    print("\n" + "=" * 60)
    print("🎉 所有控制组校准完成!")
    print(f"📊 总计: 成功 {total_stats['success']}, 失败 {total_stats['failed']}, 总共 {total_stats['total']} 个文件")
    
    return total_stats

def main():
    """主函数 - 用于测试和独立运行"""
    if validate_config():
        print("✓ Configuration validation passed")
    else:
        print("✗ Configuration validation failed")
        return
    
    print("\n🔧 基础眼动数据校准器")
    print("=" * 50)
    print("使用示例:")
    print("from calibration.basic_calibrator import calibrate_directory")
    print("calibrate_directory('data/processed', 'data/calibrated')")
    print("\n或批量校准所有控制组:")
    print("from calibration.basic_calibrator import calibrate_all_control_groups")
    print("calibrate_all_control_groups()")

if __name__ == "__main__":
    main() 