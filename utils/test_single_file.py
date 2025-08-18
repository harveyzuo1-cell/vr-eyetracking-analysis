#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件测试脚本 - VR眼球追踪数据处理工具
用于测试单个txt文件的处理功能
"""

import os
import sys
from vr_eyetracking_processor import preprocess_vr_eyetracking
from config import *


def test_single_file(txt_file_path):
    """
    测试单个txt文件的处理
    
    Args:
        txt_file_path: txt文件的完整路径
    """
    if not os.path.exists(txt_file_path):
        print(f"错误：文件不存在 - {txt_file_path}")
        return
    
    if not txt_file_path.endswith('.txt'):
        print(f"错误：不是txt文件 - {txt_file_path}")
        return
    
    print(f"开始处理单个文件: {txt_file_path}")
    print("=" * 60)
    
    # 调用预处理函数
    df_result = preprocess_vr_eyetracking(
        txt_file=txt_file_path,
        velocity_threshold_deg_s=VELOCITY_THRESHOLD,
        z_score_threshold=Z_SCORE_THRESHOLD,
        fov_deg=FOV_DEGREE
    )
    
    if len(df_result) > 0:
        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(txt_file_path))[0]
        output_dir = os.path.dirname(txt_file_path)
        output_file = os.path.join(output_dir, f"test_{base_name}_preprocessed.csv")
        
        # 保存结果
        df_result.to_csv(output_file, index=False, encoding=OUTPUT_ENCODING)
        print(f"\n✓ 处理成功！结果已保存到: {output_file}")
        
        # 显示基本统计信息
        print(f"\n数据统计:")
        print(f"  总记录数: {len(df_result)}")
        print(f"  时间跨度: {df_result['milliseconds'].max():.2f} ms")
        if 'velocity_deg_s' in df_result.columns:
            print(f"  平均速度: {df_result['velocity_deg_s'].mean():.2f} deg/s")
            print(f"  最大速度: {df_result['velocity_deg_s'].max():.2f} deg/s")
    else:
        print("✗ 处理失败或没有有效数据")


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法:")
        print(f"  python {sys.argv[0]} <txt文件路径>")
        print("\n例如:")
        print(f"  python {sys.argv[0]} C:\\path\\to\\your\\file.txt")
        sys.exit(1)
    
    txt_file_path = sys.argv[1]
    test_single_file(txt_file_path)


if __name__ == "__main__":
    main() 