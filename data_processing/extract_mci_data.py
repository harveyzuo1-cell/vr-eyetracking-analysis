#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCI数据提取脚本
从MCI目录提取轻度认知障碍组的原始和处理后数据
"""

import os
import shutil
from pathlib import Path
from tqdm import tqdm

def extract_mci_data():
    """提取MCI数据到项目目录"""
    print("🧠 开始提取MCI（轻度认知障碍）组数据...")
    print("=" * 60)
    
    # MCI数据源路径
    mci_base = r"C:\Users\asino\entropy\ip\mci-dataprocessing\mci"
    
    # 检查MCI源目录是否存在
    if not os.path.exists(mci_base):
        print(f"❌ MCI源目录不存在: {mci_base}")
        print("请检查路径是否正确")
        return False
    
    # 创建MCI数据目录结构
    mci_directories = [
        "data/mci_raw",
        "data/mci_processed", 
        "data/mci_calibrated"
    ]
    
    for dir_path in mci_directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ 创建目录: {dir_path}")
    
    # 扫描MCI目录结构
    print(f"\n🔍 扫描MCI目录: {mci_base}")
    
    extracted_counts = {
        'raw': 0,
        'processed': 0,
        'total_folders': 0
    }
    
    # 遍历MCI目录下的所有子目录
    for item in os.listdir(mci_base):
        item_path = os.path.join(mci_base, item)
        if not os.path.isdir(item_path):
            continue
            
        extracted_counts['total_folders'] += 1
        print(f"\n=== 处理MCI组 {item} ===")
        
        # 提取原始数据
        raw_source = os.path.join(item_path, "rawdata")
        if os.path.exists(raw_source):
            raw_target = f"data/mci_raw/mci_group_{item}"
            raw_count = copy_files(raw_source, raw_target, "*.txt", "原始txt")
            extracted_counts['raw'] += raw_count
        else:
            print(f"  ⚠️  未找到rawdata目录: {raw_source}")
        
        # 提取处理后数据  
        processed_source = os.path.join(item_path, "csvfile")
        if os.path.exists(processed_source):
            processed_target = f"data/mci_processed/mci_group_{item}"
            processed_count = copy_files(processed_source, processed_target, "*.csv", "处理后csv")
            extracted_counts['processed'] += processed_count
        else:
            print(f"  ⚠️  未找到csvfile目录: {processed_source}")
    
    # 生成MCI数据概览
    generate_mci_summary(extracted_counts)
    
    # 显示结果
    print("\n" + "=" * 60)
    print("🎉 MCI数据提取完成！")
    print(f"  📁 处理的MCI组数: {extracted_counts['total_folders']}")
    print(f"  📄 原始文件: {extracted_counts['raw']} 个")
    print(f"  📊 处理后文件: {extracted_counts['processed']} 个")
    print("\n📂 MCI数据结构:")
    print("  data/")
    print("  ├── mci_raw/          # MCI原始数据")
    print("  ├── mci_processed/    # MCI处理后数据")
    print("  └── mci_calibrated/   # MCI校准后数据（待生成）")
    
    return True

def copy_files(source_dir, target_dir, pattern, file_type):
    """复制指定类型的文件"""
    import glob
    
    os.makedirs(target_dir, exist_ok=True)
    
    # 获取匹配的文件
    search_pattern = os.path.join(source_dir, pattern)
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"  - {file_type}: 未找到文件")
        return 0
    
    print(f"  - {file_type}: 复制 {len(files)} 个文件")
    
    copied_count = 0
    for file_path in files:
        filename = os.path.basename(file_path)
        target_path = os.path.join(target_dir, filename)
        
        try:
            shutil.copy2(file_path, target_path)
            copied_count += 1
        except Exception as e:
            print(f"    ❌ 复制失败: {filename} - {e}")
    
    print(f"    ✓ 成功复制 {copied_count}/{len(files)} 个文件")
    return copied_count

def generate_mci_summary(counts):
    """生成MCI数据概览文档"""
    print("\n📋 生成MCI数据概览...")
    
    summary_lines = [
        "# MCI（轻度认知障碍）数据概览\n\n",
        "## 数据说明\n",
        "- **MCI**: Mild Cognitive Impairment（轻度认知障碍）\n",
        "- **数据类型**: VR眼球追踪数据\n",
        "- **对比组**: Control Group（对照组）vs MCI Group（认知障碍组）\n\n",
        "## 文件夹结构\n",
        "```\n",
        "data/\n",
        "├── mci_raw/              # MCI原始txt文件\n",
        "│   ├── mci_group_XX/     # MCI第XX组数据\n",
        "│   └── ...\n",
        "├── mci_processed/        # MCI预处理csv文件\n",
        "│   ├── mci_group_XX/     # MCI第XX组处理结果\n",
        "│   └── ...\n",
        "└── mci_calibrated/       # MCI校准csv文件\n",
        "    ├── mci_group_XX/     # MCI第XX组校准结果\n",
        "    └── ...\n",
        "```\n\n",
        "## 数据统计\n",
        f"- **MCI组数**: {counts['total_folders']} 组\n",
        f"- **原始文件**: {counts['raw']} 个txt文件\n",
        f"- **处理后文件**: {counts['processed']} 个csv文件\n\n",
        "## 数据对比\n",
        "| 数据类型 | Control Group | MCI Group |\n",
        "|---------|---------------|----------|\n",
        "| 位置 | data/raw/, data/processed/, data/calibrated/ | data/mci_raw/, data/mci_processed/, data/mci_calibrated/ |\n",
        "| 命名格式 | control_group_{组号} | mci_group_{组号} |\n",
        "| 用途 | 健康对照组 | 认知障碍对比组 |\n\n",
        "## 校准建议\n",
        "- **Control Group**: 使用标准校准参数\n",
        "- **MCI Group**: 可能需要个体化校准参数\n",
        "- **个体差异**: 建议为不同个体设置不同的校准偏移量\n"
    ]
    
    # 统计实际的MCI文件
    if os.path.exists("data/mci_raw"):
        summary_lines.append("\n### MCI原始数据统计\n")
        for folder in sorted(os.listdir("data/mci_raw")):
            if folder.startswith("mci_group_"):
                folder_path = os.path.join("data/mci_raw", folder)
                if os.path.isdir(folder_path):
                    txt_count = len([f for f in os.listdir(folder_path) if f.endswith('.txt')])
                    summary_lines.append(f"- {folder}: {txt_count} 个txt文件\n")
    
    if os.path.exists("data/mci_processed"):
        summary_lines.append("\n### MCI处理后数据统计\n")
        for folder in sorted(os.listdir("data/mci_processed")):
            if folder.startswith("mci_group_"):
                folder_path = os.path.join("data/mci_processed", folder)
                if os.path.isdir(folder_path):
                    csv_count = len([f for f in os.listdir(folder_path) if f.endswith('.csv')])
                    summary_lines.append(f"- {folder}: {csv_count} 个csv文件\n")
    
    # 保存MCI概览
    os.makedirs("data", exist_ok=True)
    with open("data/MCI_SUMMARY.md", "w", encoding="utf-8") as f:
        f.writelines(summary_lines)
    
    print("   ✓ MCI数据概览文档已生成: data/MCI_SUMMARY.md")

def main():
    """主函数"""
    extract_mci_data()

if __name__ == "__main__":
    main() 