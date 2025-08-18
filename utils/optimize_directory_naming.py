#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录命名优化脚本
统一data目录下的命名规则，解决Control Group和MCI Group命名不一致的问题
"""

import os
import shutil
from pathlib import Path

def analyze_current_structure():
    """分析当前目录结构"""
    print("🔍 分析当前目录结构...")
    print("=" * 60)
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        print("❌ data目录不存在")
        return {}
    
    current_dirs = {}
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path):
            file_count = sum(1 for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)))
            subdir_count = sum(1 for f in os.listdir(item_path) if os.path.isdir(os.path.join(item_path, f)))
            current_dirs[item] = {
                'files': file_count,
                'subdirs': subdir_count,
                'path': item_path
            }
            print(f"📁 {item:20} - {subdir_count}个子目录, {file_count}个文件")
    
    return current_dirs

def propose_new_structure():
    """提出新的目录结构方案"""
    print("\n💡 新的统一命名方案:")
    print("=" * 60)
    
    new_structure = {
        # 方案：统一使用前缀
        'control_raw': '对照组原始数据',
        'control_processed': '对照组预处理数据', 
        'control_calibrated': '对照组校准数据',
        'mci_raw': 'MCI组原始数据',
        'mci_processed': 'MCI组预处理数据',
        'mci_calibrated': 'MCI组校准数据'
    }
    
    print("新结构:")
    for new_name, description in new_structure.items():
        print(f"📁 {new_name:20} - {description}")
    
    print("\n✅ 优势:")
    print("   • 命名规则统一一致")
    print("   • 一眼区分Control Group vs MCI Group")
    print("   • 避免混淆和误操作")
    print("   • 便于批量操作和脚本处理")
    
    return new_structure

def create_rename_mapping():
    """创建重命名映射"""
    rename_mapping = {
        # 旧名称 -> 新名称
        'raw': 'control_raw',
        'processed': 'control_processed',
        'calibrated': 'control_calibrated',
        'mci_raw': 'mci_raw',  # 保持不变
        'mci_processed': 'mci_processed',  # 保持不变
        'mci_calibrated': 'mci_calibrated'  # 保持不变
    }
    
    print("\n🔄 重命名映射:")
    print("=" * 60)
    for old_name, new_name in rename_mapping.items():
        if old_name != new_name:
            print(f"📁 {old_name:15} -> {new_name}")
        else:
            print(f"📁 {old_name:15} -> {new_name} (保持不变)")
    
    return rename_mapping

def execute_rename(rename_mapping, dry_run=True):
    """执行重命名操作"""
    print(f"\n{'🔍 预演模式' if dry_run else '🚀 执行重命名'}:")
    print("=" * 60)
    
    data_dir = "data"
    success_count = 0
    error_count = 0
    
    for old_name, new_name in rename_mapping.items():
        old_path = os.path.join(data_dir, old_name)
        new_path = os.path.join(data_dir, new_name)
        
        if not os.path.exists(old_path):
            print(f"⚠️  源目录不存在: {old_name}")
            continue
            
        if old_name == new_name:
            print(f"➡️  跳过: {old_name} (无需重命名)")
            continue
            
        if os.path.exists(new_path):
            print(f"❌ 目标目录已存在: {new_name}")
            error_count += 1
            continue
        
        try:
            if not dry_run:
                # 执行重命名
                shutil.move(old_path, new_path)
                print(f"✅ 成功: {old_name} -> {new_name}")
            else:
                # 预演模式
                print(f"🔄 将重命名: {old_name} -> {new_name}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 重命名失败: {old_name} -> {new_name}, 错误: {e}")
            error_count += 1
    
    print(f"\n📊 操作统计:")
    print(f"   成功: {success_count}")
    print(f"   失败: {error_count}")
    
    return success_count > 0 and error_count == 0

def update_config_files():
    """更新配置文件中的路径引用"""
    print("\n⚙️ 更新配置文件...")
    print("=" * 60)
    
    # 需要更新的文件和路径映射
    files_to_update = {
        'advanced_calibrator.py': {
            'data/processed/': 'data/control_processed/',
            'data/calibrated/': 'data/control_calibrated/'
        },
        'csv_calibrator.py': {
            'data/processed': 'data/control_processed',
            'data/calibrated': 'data/control_calibrated'
        },
        'extract_mci_data.py': {
            # MCI相关路径保持不变，因为已经有正确的前缀
        },
        'update_control_group_data.py': {
            'data/raw': 'data/control_raw',
            'data/processed': 'data/control_processed',
            'data/calibrated': 'data/control_calibrated'
        }
    }
    
    updated_files = []
    
    for filename, replacements in files_to_update.items():
        if not os.path.exists(filename):
            print(f"⚠️  文件不存在: {filename}")
            continue
            
        if not replacements:  # 空字典，跳过
            continue
        
        try:
            # 读取文件
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 应用替换
            original_content = content
            for old_path, new_path in replacements.items():
                content = content.replace(old_path, new_path)
            
            # 检查是否有变化
            if content != original_content:
                # 写回文件
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files.append(filename)
                print(f"✅ 已更新: {filename}")
                
                # 显示替换详情
                for old_path, new_path in replacements.items():
                    if old_path in original_content:
                        print(f"   📝 {old_path} -> {new_path}")
            else:
                print(f"➡️  无需更新: {filename}")
                
        except Exception as e:
            print(f"❌ 更新失败: {filename}, 错误: {e}")
    
    return updated_files

def generate_updated_summary():
    """生成更新后的数据概览"""
    print("\n📋 生成更新后的数据概览...")
    
    summary_lines = [
        "# VR眼球追踪数据概览 (统一命名)\n",
        f"更新时间: {Path().absolute()}\n",
        "\n## 统一命名说明\n",
        "- **命名规则**: 统一使用 `{组类型}_{数据阶段}` 格式\n",
        "- **Control Group**: control_raw, control_processed, control_calibrated\n",
        "- **MCI Group**: mci_raw, mci_processed, mci_calibrated\n",
        "- **优势**: 命名一致、清晰明确、避免误解\n",
        "\n## 优化后的目录结构\n",
        "```\n",
        "data/\n",
        "├── control_raw/              # 对照组原始数据\n",
        "│   ├── control_group_1/      # 第1组对照数据\n",
        "│   ├── control_group_2/      # 第2组对照数据\n",
        "│   └── ...                   # 第3-20组\n",
        "├── control_processed/        # 对照组预处理数据\n",
        "│   ├── control_group_1/      # 第1组处理结果\n",
        "│   └── ...                   # 其他组处理结果\n",
        "├── control_calibrated/       # 对照组校准数据\n",
        "│   ├── control_group_1/      # 第1组校准结果\n",
        "│   └── ...                   # 其他组校准结果\n",
        "├── mci_raw/                  # MCI组原始数据\n",
        "│   ├── mci_group_XX/         # MCI第XX组数据\n",
        "│   └── ...\n",
        "├── mci_processed/            # MCI组预处理数据\n",
        "│   ├── mci_group_XX/         # MCI第XX组处理结果\n",
        "│   └── ...\n",
        "└── mci_calibrated/           # MCI组校准数据\n",
        "    ├── mci_group_XX/         # MCI第XX组校准结果\n",
        "    └── ...\n",
        "```\n",
        "\n## 命名优化前后对比\n",
        "| 数据类型 | 优化前 | 优化后 |\n",
        "|---------|--------|--------|\n",
        "| 对照组原始 | raw/ | control_raw/ |\n",
        "| 对照组处理 | processed/ | control_processed/ |\n",
        "| 对照组校准 | calibrated/ | control_calibrated/ |\n",
        "| MCI组原始 | mci_raw/ | mci_raw/ (保持) |\n",
        "| MCI组处理 | mci_processed/ | mci_processed/ (保持) |\n",
        "| MCI组校准 | mci_calibrated/ | mci_calibrated/ (保持) |\n",
        "\n## 使用建议\n",
        "1. **清晰识别**: 一眼区分对照组vs认知障碍组数据\n",
        "2. **批量操作**: 便于使用通配符进行批量处理\n",
        "3. **脚本兼容**: 所有处理脚本已自动更新路径\n",
        "4. **扩展性好**: 便于未来添加新的数据组类型\n"
    ]
    
    # 统计实际文件数量
    for prefix in ['control', 'mci']:
        if os.path.exists(f"data/{prefix}_raw"):
            summary_lines.append(f"\n### {prefix.upper()} Group数据统计\n")
            
            for stage in ['raw', 'processed', 'calibrated']:
                dir_path = f"data/{prefix}_{stage}"
                if os.path.exists(dir_path):
                    total_files = 0
                    group_count = 0
                    for folder in sorted(os.listdir(dir_path)):
                        if folder.startswith(f"{prefix}_group_"):
                            folder_path = os.path.join(dir_path, folder)
                            if os.path.isdir(folder_path):
                                file_count = len([f for f in os.listdir(folder_path) 
                                                if f.endswith('.txt') or f.endswith('.csv')])
                                total_files += file_count
                                group_count += 1
                    
                    summary_lines.append(f"- **{stage}**: {group_count}组, {total_files}个文件\n")
    
    # 保存概览
    with open("data/DATA_SUMMARY.md", "w", encoding="utf-8") as f:
        f.writelines(summary_lines)
    
    print("   ✓ 数据概览文档已更新: data/DATA_SUMMARY.md")

def main():
    """主函数"""
    print("🎯 目录命名优化工具")
    print("解决Control Group和MCI Group命名不一致问题")
    print("=" * 60)
    
    # 1. 分析当前结构
    current_dirs = analyze_current_structure()
    
    # 2. 提出新方案
    new_structure = propose_new_structure()
    
    # 3. 创建重命名映射
    rename_mapping = create_rename_mapping()
    
    # 4. 预演重命名
    print("\n" + "="*60)
    can_proceed = execute_rename(rename_mapping, dry_run=True)
    
    if not can_proceed:
        print("\n❌ 发现问题，无法继续。请检查错误信息。")
        return
    
    # 5. 确认执行
    print("\n" + "="*60)
    print("🤔 确认要执行重命名操作吗？这将:")
    print("   • 重命名data目录下的文件夹")
    print("   • 更新相关脚本中的路径引用")
    print("   • 生成新的数据概览文档")
    
    user_input = input("\n输入 'yes' 确认执行: ").strip().lower()
    
    if user_input == 'yes':
        print("\n🚀 开始执行重命名...")
        
        # 6. 执行重命名
        success = execute_rename(rename_mapping, dry_run=False)
        
        if success:
            # 7. 更新配置文件
            updated_files = update_config_files()
            
            # 8. 生成新概览
            generate_updated_summary()
            
            print("\n" + "="*60)
            print("🎉 目录命名优化完成！")
            print(f"✅ 已重命名目录结构")
            if updated_files:
                print(f"✅ 已更新脚本文件: {', '.join(updated_files)}")
            print(f"✅ 已生成新的数据概览")
            
            print("\n📁 新的目录结构:")
            print("data/")
            for new_name, description in new_structure.items():
                if os.path.exists(f"data/{new_name}"):
                    print(f"├── {new_name:20} # {description}")
        else:
            print("\n❌ 重命名过程中出现错误，请检查。")
    else:
        print("\n🚫 操作已取消")

if __name__ == "__main__":
    main() 