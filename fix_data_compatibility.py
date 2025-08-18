#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据兼容性修复脚本
修复现有数据文件，添加时间校准所需的milliseconds列和其他缺失的列
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from visualization.enhanced_web_visualizer import EnhancedWebVisualizer

def main():
    """主函数"""
    print("🔧 数据兼容性修复工具")
    print("=" * 50)
    print("该工具将修复现有数据文件，确保其与时间校准功能兼容")
    print("主要修复内容：")
    print("  1. 添加 milliseconds 列（时间校准必需）")
    print("  2. 添加 x_deg, y_deg 度数列（如果缺失）")
    print("  3. 添加 velocity_deg_s 角速度列（如果缺失）")
    print("=" * 50)
    
    # 确认是否继续
    response = input("是否继续执行修复？(y/n): ").lower().strip()
    if response not in ['y', 'yes', '是', '是的']:
        print("取消修复")
        return
    
    try:
        # 创建可视化器实例
        print("\n📊 初始化可视化器...")
        visualizer = EnhancedWebVisualizer()
        
        print("\n🔧 开始修复所有数据文件...")
        
        # 执行修复
        result = visualizer.fix_existing_data_files()
        
        if result['success']:
            stats = result['stats']
            print(f"\n✅ 修复完成！")
            print(f"📊 统计结果：")
            print(f"   总文件数: {stats['total_files']}")
            print(f"   成功修复: {stats['fixed_files']}")
            print(f"   已正常文件: {stats['already_ok_files']}")
            print(f"   错误文件: {stats['error_files']}")
            
            if stats['details']:
                print(f"\n📋 详细信息：")
                for detail in stats['details']:
                    print(f"   {detail}")
            
            if stats['fixed_files'] > 0:
                print(f"\n🎉 成功修复了 {stats['fixed_files']} 个文件！")
                print("这些文件现在应该可以正常进行时间校准了。")
            else:
                print(f"\n✅ 所有文件都已经是兼容的格式，无需修复。")
        else:
            print(f"\n❌ 修复失败: {result['error']}")
            return 1
        
    except Exception as e:
        print(f"\n❌ 执行修复时出错: {e}")
        import traceback
        print(f"\n📋 详细错误信息:\n{traceback.format_exc()}")
        return 1
    
    print(f"\n🔧 修复工具执行完成")
    return 0

if __name__ == "__main__":
    exit(main()) 