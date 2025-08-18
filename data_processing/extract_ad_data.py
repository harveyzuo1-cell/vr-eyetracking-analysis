#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿尔兹海默症组(AD Group)数据提取脚本
从原始目录提取AD组的原始数据和预处理数据到项目的统一目录结构中
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def extract_ad_data():
    """提取AD组数据到项目目录"""
    print("🧠 开始提取阿尔兹海默症组(AD Group)数据...")
    print("=" * 60)
    
    # AD组数据源路径
    ad_base = r"C:\Users\asino\entropy\ip\mci-dataprocessing\trans_ad"
    
    # 项目目录路径
    project_dirs = {
        'ad_raw': 'data/ad_raw',
        'ad_processed': 'data/ad_processed', 
        'ad_calibrated': 'data/ad_calibrated'
    }
    
    # 创建目录结构
    for dir_name, dir_path in project_dirs.items():
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ 创建目录: {dir_path}")
    
    # 统计信息
    stats = {
        'total_groups': 0,
        'raw_files': 0,
        'processed_files': 0,
        'groups_with_raw': [],
        'groups_with_processed': [],
        'groups_missing_data': []
    }
    
    print(f"\n🔍 扫描AD组数据源: {ad_base}")
    
    # 获取所有AD组目录
    if not os.path.exists(ad_base):
        print(f"❌ AD组数据源目录不存在: {ad_base}")
        return
    
    # 扫描所有数字目录
    for item in os.listdir(ad_base):
        if item.isdigit():
            group_num = item
            group_path = os.path.join(ad_base, group_num)
            
            if os.path.isdir(group_path):
                stats['total_groups'] += 1
                group_name = f"ad_group_{group_num}"
                
                print(f"\n--- 处理 {group_name} ---")
                
                # 检查并复制原始数据
                rawdata_path = os.path.join(group_path, "rawdata")
                if os.path.exists(rawdata_path):
                    raw_files = copy_files(
                        rawdata_path,
                        os.path.join(project_dirs['ad_raw'], group_name),
                        file_pattern="*.txt",
                        description="原始数据"
                    )
                    stats['raw_files'] += raw_files
                    if raw_files > 0:
                        stats['groups_with_raw'].append(group_name)
                else:
                    print(f"  ⚠️  rawdata目录不存在")
                
                # 检查并复制预处理数据
                csvfile_path = os.path.join(group_path, "csvfile")
                if os.path.exists(csvfile_path):
                    processed_files = copy_files(
                        csvfile_path,
                        os.path.join(project_dirs['ad_processed'], group_name),
                        file_pattern="*.csv",
                        description="预处理数据"
                    )
                    stats['processed_files'] += processed_files
                    if processed_files > 0:
                        stats['groups_with_processed'].append(group_name)
                else:
                    print(f"  ⚠️  csvfile目录不存在")
                
                # 记录缺失数据的组
                if group_name not in stats['groups_with_raw'] and group_name not in stats['groups_with_processed']:
                    stats['groups_missing_data'].append(group_name)
    
    # 生成AD组数据摘要
    generate_ad_summary(stats)
    
    # 打印提取结果
    print("\n" + "=" * 60)
    print("🎉 AD组数据提取完成!")
    print(f"📊 总计扫描: {stats['total_groups']} 个AD组")
    print(f"📁 原始文件: {stats['raw_files']} 个")
    print(f"📄 预处理文件: {stats['processed_files']} 个")
    print(f"✅ 有原始数据的组: {len(stats['groups_with_raw'])} 个")
    print(f"✅ 有预处理数据的组: {len(stats['groups_with_processed'])} 个")
    
    if stats['groups_missing_data']:
        print(f"⚠️  缺失数据的组: {len(stats['groups_missing_data'])} 个")
        print(f"   {', '.join(stats['groups_missing_data'])}")

def copy_files(source_dir, target_dir, file_pattern="*", description="文件"):
    """复制文件到目标目录
    
    Args:
        source_dir: 源目录
        target_dir: 目标目录  
        file_pattern: 文件模式
        description: 文件描述
        
    Returns:
        int: 复制的文件数量
    """
    if not os.path.exists(source_dir):
        return 0
    
    # 创建目标目录
    os.makedirs(target_dir, exist_ok=True)
    
    # 获取匹配的文件
    from glob import glob
    files = glob(os.path.join(source_dir, file_pattern))
    
    if not files:
        print(f"  ❌ 未找到{description}: {file_pattern}")
        return 0
    
    copied_count = 0
    for file_path in files:
        if os.path.isfile(file_path):
            file_name = os.path.basename(file_path)
            target_file = os.path.join(target_dir, file_name)
            
            try:
                shutil.copy2(file_path, target_file)
                copied_count += 1
            except Exception as e:
                print(f"  ❌ 复制失败 {file_name}: {e}")
    
    print(f"  ✓ {description}: {copied_count} 个文件")
    return copied_count

def generate_ad_summary(stats):
    """生成AD组数据摘要文档"""
    print("\n📋 生成AD组数据摘要...")
    
    summary_lines = [
        "# 阿尔兹海默症组(AD Group)数据概览\n",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"提取自: C:\\Users\\asino\\entropy\\ip\\mci-dataprocessing\\trans_ad\n",
        "\n## 数据概况\n",
        f"- **总组数**: {stats['total_groups']} 个AD组\n",
        f"- **原始文件**: {stats['raw_files']} 个.txt文件\n", 
        f"- **预处理文件**: {stats['processed_files']} 个.csv文件\n",
        f"- **有原始数据的组**: {len(stats['groups_with_raw'])} 个\n",
        f"- **有预处理数据的组**: {len(stats['groups_with_processed'])} 个\n",
        "\n## 目录结构\n",
        "```\n",
        "data/\n",
        "├── ad_raw/                   # AD组原始数据\n",
        "│   ├── ad_group_1/           # AD第1组数据\n",
        "│   │   ├── 1.txt             # 任务1原始数据\n",
        "│   │   ├── 2.txt             # 任务2原始数据\n",
        "│   │   ├── 3.txt             # 任务3原始数据\n",
        "│   │   ├── 4.txt             # 任务4原始数据\n",
        "│   │   └── 5.txt             # 任务5原始数据\n",
        "│   └── ...\n",
        "├── ad_processed/             # AD组预处理数据\n",
        "│   ├── ad_group_1/           # AD第1组处理结果\n",
        "│   │   ├── ad1q1_preprocessed.csv  # 任务1预处理结果\n",
        "│   │   ├── ad1q2_preprocessed.csv  # 任务2预处理结果\n",
        "│   │   ├── ad1q3_preprocessed.csv  # 任务3预处理结果\n",
        "│   │   ├── ad1q4_preprocessed.csv  # 任务4预处理结果\n",
        "│   │   └── ad1q5_preprocessed.csv  # 任务5预处理结果\n",
        "│   └── ...\n",
        "└── ad_calibrated/            # AD组校准数据\n",
        "    ├── ad_group_1/           # AD第1组校准结果\n",
        "    │   ├── ad1q1_preprocessed_calibrated.csv\n",
        "    │   ├── ad1q2_preprocessed_calibrated.csv\n",
        "    │   ├── ad1q3_preprocessed_calibrated.csv\n",
        "    │   ├── ad1q4_preprocessed_calibrated.csv\n",
        "    │   └── ad1q5_preprocessed_calibrated.csv\n",
        "    └── ...\n",
        "```\n",
        "\n## 文件命名规范\n",
        "- **原始数据**: `1.txt`, `2.txt`, `3.txt`, `4.txt`, `5.txt`\n",
        "- **预处理数据**: `ad{组号}q{任务编号}_preprocessed.csv`\n",
        "- **校准数据**: `ad{组号}q{任务编号}_preprocessed_calibrated.csv`\n",
        "- **组名格式**: `ad_group_{组号}`\n",
        "\n## 数据完整性\n"
    ]
    
    # 添加详细的组数据统计
    if stats['groups_with_raw']:
        summary_lines.append("### 有原始数据的组\n")
        for group in sorted(stats['groups_with_raw']):
            summary_lines.append(f"- {group}\n")
        summary_lines.append("\n")
    
    if stats['groups_with_processed']:
        summary_lines.append("### 有预处理数据的组\n")
        for group in sorted(stats['groups_with_processed']):
            summary_lines.append(f"- {group}\n")
        summary_lines.append("\n")
    
    if stats['groups_missing_data']:
        summary_lines.append("### 缺失数据的组\n")
        for group in sorted(stats['groups_missing_data']):
            summary_lines.append(f"- {group} ⚠️\n")
        summary_lines.append("\n")
    
    summary_lines.extend([
        "## 与其他组的对比\n",
        "| 数据组 | 组数 | 原始文件 | 预处理文件 | 命名前缀 |\n",
        "|--------|------|----------|------------|----------|\n",
        "| Control Group | 20 | ~95 | 100 | n | \n",
        "| MCI Group | 21 | ~105 | 105 | m |\n",
        f"| AD Group | {len(stats['groups_with_processed'])} | {stats['raw_files']} | {stats['processed_files']} | ad |\n",
        "\n## 研究意义\n",
        "- **对照组**: 健康对照\n", 
        "- **MCI组**: 轻度认知障碍\n",
        "- **AD组**: 阿尔兹海默症患者\n",
        "- **研究价值**: 支持认知障碍疾病进展的眼球追踪对比研究\n",
    ])
    
    # 保存AD组摘要
    with open("data/AD_SUMMARY.md", "w", encoding="utf-8") as f:
        f.writelines(summary_lines)
    
    print("   ✓ AD组数据摘要已生成: data/AD_SUMMARY.md")

def main():
    """主函数"""
    try:
        extract_ad_data()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
    except Exception as e:
        print(f"\n❌ 提取过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main() 