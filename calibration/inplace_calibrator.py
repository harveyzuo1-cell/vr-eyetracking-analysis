# -*- coding: utf-8 -*-
"""
就地眼动数据校准器
支持直接修改原文件的校准操作，包括问题过滤和文件夹范围选择
"""
import os
import sys
import json
import math
import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import List, Optional, Dict

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import OUTPUT_ENCODING

class InplaceCalibrator:
    """就地校准器 - 直接修改原文件"""
    
    def __init__(self, config_file: str = "config/calibration_config.json"):
        """
        初始化就地校准器
        
        Args:
            config_file: 校准配置文件路径
        """
        self.config_file = config_file
        self.config = self.load_config()
        
        # 获取就地校准设置
        self.inplace_settings = self.config.get("inplace_calibration", {})
        self.enabled = self.inplace_settings.get("enabled", True)
        self.backup_before_overwrite = self.inplace_settings.get("backup_before_overwrite", True)
        
    def load_config(self) -> dict:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✓ 已加载校准配置: {self.config_file}")
            return config
        except Exception as e:
            print(f"❌ 无法加载校准配置: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "default_profiles": {
                "default_control": {"offset_x": -0.030, "offset_y": -0.140},
                "default_mci": {"offset_x": -0.035, "offset_y": -0.145},
                "default_ad": {"offset_x": -0.025, "offset_y": -0.130}
            },
            "group_specific_overrides": {},
            "file_specific_overrides": {},
            "inplace_calibration": {
                "enabled": True,
                "backup_before_overwrite": True,
                "default_question_filter": [],
                "supported_filename_formats": [
                    "nXXqY_preprocessed.csv",
                    "mXXqY_preprocessed.csv",
                    "adXXqY_preprocessed.csv"
                ]
            }
        }
    
    def parse_question_from_filename(self, filename: str) -> Optional[int]:
        """
        从文件名中解析问题编号
        
        Args:
            filename: 文件名，如 "n1q3_preprocessed.csv"
            
        Returns:
            问题编号，如 3
        """
        import re
        
        # 匹配模式：nXXqY, mXXqY, adXXqY
        patterns = [
            r'n\d+q(\d+)',  # nXXqY
            r'm\d+q(\d+)',  # mXXqY  
            r'ad\d+q(\d+)'  # adXXqY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))
        
        return None
    
    def get_group_from_directory(self, file_path: str) -> str:
        """
        从目录路径推断组类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            组类型 ('control', 'mci', 'ad')
        """
        path_lower = file_path.lower()
        
        if 'control' in path_lower:
            return 'control'
        elif 'mci' in path_lower:
            return 'mci'
        elif 'ad' in path_lower:
            return 'ad'
        else:
            # 根据文件名前缀判断
            filename = os.path.basename(file_path)
            if filename.startswith('n'):
                return 'control'
            elif filename.startswith('m'):
                return 'mci'
            elif filename.startswith('ad'):
                return 'ad'
            
        return 'control'  # 默认为控制组
    
    def get_calibration_params(self, group_type: str, file_path: str = "") -> tuple:
        """
        获取校准参数
        
        Args:
            group_type: 组类型
            file_path: 文件路径（用于文件特定配置）
            
        Returns:
            (x_offset, y_offset)
        """
        filename = os.path.basename(file_path) if file_path else ""
        
        # 1. 文件特定配置（最高优先级）
        file_overrides = self.config.get("file_specific_overrides", {})
        if filename in file_overrides:
            override = file_overrides[filename]
            return (override["offset_x"], override["offset_y"])
        
        # 2. 组特定配置
        group_overrides = self.config.get("group_specific_overrides", {})
        # 这里需要从文件路径推断具体的组名
        for group_name, override in group_overrides.items():
            if group_type in group_name:
                return (override["offset_x"], override["offset_y"])
        
        # 3. 默认配置
        defaults = self.config.get("default_profiles", {})
        if group_type == 'control':
            default = defaults.get("default_control", {"offset_x": -0.030, "offset_y": -0.140})
        elif group_type == 'mci':
            default = defaults.get("default_mci", {"offset_x": -0.035, "offset_y": -0.145})
        elif group_type == 'ad':
            default = defaults.get("default_ad", {"offset_x": -0.025, "offset_y": -0.130})
        else:
            default = {"offset_x": -0.030, "offset_y": -0.140}
        
        return (default["offset_x"], default["offset_y"])
    
    def calibrate_csv_xy_inplace(self, csv_file_path: str, 
                                x_offset: Optional[float] = None,
                                y_offset: Optional[float] = None) -> bool:
        """
        就地校准CSV文件的X,Y坐标
        
        Args:
            csv_file_path: CSV文件路径
            x_offset: X偏移量（可选，如果不提供则从配置获取）
            y_offset: Y偏移量（可选，如果不提供则从配置获取）
            
        Returns:
            校准是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(csv_file_path):
                print(f"❌ 文件不存在: {csv_file_path}")
                return False
            
            # 备份原文件
            if self.backup_before_overwrite:
                backup_path = csv_file_path + ".backup"
                if not os.path.exists(backup_path):
                    import shutil
                    shutil.copy2(csv_file_path, backup_path)
                    print(f"📋 已备份: {backup_path}")
            
            # 读取数据
            df = pd.read_csv(csv_file_path)
            
            if 'x' not in df.columns or 'y' not in df.columns:
                print(f"❌ 文件缺少x或y列: {csv_file_path}")
                return False
            
            # 获取校准参数
            if x_offset is None or y_offset is None:
                group_type = self.get_group_from_directory(csv_file_path)
                auto_x_offset, auto_y_offset = self.get_calibration_params(group_type, csv_file_path)
                
                if x_offset is None:
                    x_offset = auto_x_offset
                if y_offset is None:
                    y_offset = auto_y_offset
            
            # 记录原始范围
            original_x_range = f"[{df['x'].min():.3f}, {df['x'].max():.3f}]"
            original_y_range = f"[{df['y'].min():.3f}, {df['y'].max():.3f}]"
            
            # 应用校准
            df['x'] = df['x'] + x_offset
            df['y'] = df['y'] + y_offset
            
            # 记录校准后范围
            calibrated_x_range = f"[{df['x'].min():.3f}, {df['x'].max():.3f}]"
            calibrated_y_range = f"[{df['y'].min():.3f}, {df['y'].max():.3f}]"
            
            # 保存回原文件
            df.to_csv(csv_file_path, index=False, encoding=OUTPUT_ENCODING)
            
            print(f"  ✓ 就地校准: {os.path.basename(csv_file_path)}")
            print(f"    校准参数: x{x_offset:+.3f}, y{y_offset:+.3f}")
            print(f"    原始范围: x{original_x_range}, y{calibrated_y_range}")
            print(f"    校准范围: x{calibrated_x_range}, y{calibrated_y_range}")
            print(f"    数据行数: {len(df)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 校准失败: {e}")
            return False
    
    def calibrate_all_subfolders_inplace(self, base_directory: str,
                                       question_filter: Optional[List[int]] = None,
                                       folder_range: Optional[List[int]] = None,
                                       manual_offsets: Optional[tuple] = None) -> Dict[str, int]:
        """
        就地校准所有子文件夹中的CSV文件
        
        Args:
            base_directory: 基础目录路径
            question_filter: 问题过滤列表，如 [1, 2, 3]
            folder_range: 文件夹范围列表，如 [13, 14, 15]
            manual_offsets: 手动偏移量 (x_offset, y_offset)
            
        Returns:
            校准统计信息
        """
        if not self.enabled:
            print("❌ 就地校准功能已禁用")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        if not os.path.exists(base_directory):
            print(f"❌ 目录不存在: {base_directory}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        print(f"🔧 就地校准: {base_directory}")
        if question_filter:
            print(f"📋 问题过滤: {question_filter}")
        if folder_range:
            print(f"📁 文件夹范围: {folder_range}")
        if manual_offsets:
            print(f"⚙️  手动偏移: x{manual_offsets[0]:+.3f}, y{manual_offsets[1]:+.3f}")
        
        print("=" * 60)
        
        total_files = 0
        success_count = 0
        failed_count = 0
        
        # 遍历目录
        for root, dirs, files in os.walk(base_directory):
            # 文件夹过滤
            if folder_range:
                folder_name = os.path.basename(root)
                # 尝试提取文件夹编号
                import re
                folder_num_match = re.search(r'(\d+)', folder_name)
                if folder_num_match:
                    folder_num = int(folder_num_match.group(1))
                    if folder_num not in folder_range:
                        continue
            
            # 查找CSV文件
            csv_files = [f for f in files if f.endswith('.csv') and 'preprocessed' in f]
            
            if not csv_files:
                continue
            
            print(f"\n📂 处理目录: {root}")
            print(f"   找到 {len(csv_files)} 个文件")
            
            for csv_file in tqdm(csv_files, desc="校准文件"):
                file_path = os.path.join(root, csv_file)
                
                # 问题过滤
                if question_filter:
                    question_num = self.parse_question_from_filename(csv_file)
                    if question_num is None or question_num not in question_filter:
                        print(f"  ⏭️  跳过 (问题过滤): {csv_file}")
                        continue
                
                total_files += 1
                
                # 执行校准
                x_offset = manual_offsets[0] if manual_offsets else None
                y_offset = manual_offsets[1] if manual_offsets else None
                
                if self.calibrate_csv_xy_inplace(file_path, x_offset, y_offset):
                    success_count += 1
                else:
                    failed_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ 就地校准完成!")
        print(f"📊 成功: {success_count}, 失败: {failed_count}, 总计: {total_files}")
        
        return {
            'total': total_files,
            'success': success_count,
            'failed': failed_count
        }

def main():
    """主函数 - 用于测试"""
    calibrator = InplaceCalibrator()
    
    print("🔧 就地校准器")
    print("=" * 50)
    print(f"状态: {'启用' if calibrator.enabled else '禁用'}")
    print(f"自动备份: {'是' if calibrator.backup_before_overwrite else '否'}")
    
    print("\n使用示例:")
    print("calibrator = InplaceCalibrator()")
    print("calibrator.calibrate_csv_xy_inplace('data.csv')")
    print("calibrator.calibrate_all_subfolders_inplace('data/processed')")

if __name__ == "__main__":
    main() 