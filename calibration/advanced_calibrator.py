# -*- coding: utf-8 -*-
"""
高级眼动数据校准器
支持多级校准系统（文件 > 组 > 默认）
"""
import os
import sys
import json
import pandas as pd
from tqdm import tqdm
from typing import Dict, Tuple, Optional

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import OUTPUT_ENCODING

class AdvancedCalibrator:
    """高级校准器 - 支持多级校准策略"""
    
    def __init__(self, config_file: str = "config/calibration_config.json"):
        """
        初始化校准器
        
        Args:
            config_file: 校准配置文件路径
        """
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> dict:
        """加载校准配置"""
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
                "default_control": {
                    "offset_x": -0.030,
                    "offset_y": -0.140,
                    "description": "控制组默认校准参数"
                },
                "default_mci": {
                    "offset_x": -0.035,
                    "offset_y": -0.145,
                    "description": "MCI组默认校准参数"
                },
                "default_ad": {
                    "offset_x": -0.025,
                    "offset_y": -0.130,
                    "description": "AD组默认校准参数"
                }
            },
            "group_specific_overrides": {
                "control_group_13": {
                    "offset_x": -0.035,
                    "offset_y": -0.150,
                    "reason": "该组设备偏移较大，需要额外校准"
                },
                "control_group_20": {
                    "offset_x": -0.025,
                    "offset_y": -0.130,
                    "reason": "该组数据质量较好，需要轻微校准"
                }
            },
            "file_specific_overrides": {}
        }
    
    def get_calibration_params(self, group_name: str, filename: str = "") -> Tuple[float, float, str]:
        """
        获取校准参数（多级查找）
        
        Args:
            group_name: 组名 (如 control_group_1, mci_group_1, ad_group_1)
            filename: 文件名 (可选)
            
        Returns:
            (x_offset, y_offset, reason)
        """
        # 1. 文件特定配置（最高优先级）
        if filename and filename in self.config.get("file_specific_overrides", {}):
            override = self.config["file_specific_overrides"][filename]
            return (
                override["offset_x"],
                override["offset_y"],
                f"文件特定校准: {override.get('reason', '特定偏移')}"
            )
        
        # 2. 组特定配置
        if group_name in self.config.get("group_specific_overrides", {}):
            override = self.config["group_specific_overrides"][group_name]
            return (
                override["offset_x"],
                override["offset_y"],
                f"组级校准: {group_name}"
            )
        
        # 3. 默认配置（按组类型）
        defaults = self.config.get("default_profiles", {})
        
        if group_name.startswith("control_group"):
            default = defaults.get("default_control", {"offset_x": -0.030, "offset_y": -0.140})
            return (default["offset_x"], default["offset_y"], "默认对照组校准")
        elif group_name.startswith("mci_group"):
            default = defaults.get("default_mci", {"offset_x": -0.035, "offset_y": -0.145})
            return (default["offset_x"], default["offset_y"], "默认MCI组校准")
        elif group_name.startswith("ad_group"):
            default = defaults.get("default_ad", {"offset_x": -0.025, "offset_y": -0.130})
            return (default["offset_x"], default["offset_y"], "默认AD组校准")
        else:
            # 通用默认值
            return (-0.030, -0.140, "通用默认校准")
    
    def calibrate_csv_file(self, input_file: str, output_file: str,
                          x_offset: float, y_offset: float) -> bool:
        """
        校准单个CSV文件
        
        Args:
            input_file: 输入文件
            output_file: 输出文件
            x_offset: X偏移量
            y_offset: Y偏移量
            
        Returns:
            校准是否成功
        """
        try:
            # 读取数据
            df = pd.read_csv(input_file)
            
            if 'x' not in df.columns or 'y' not in df.columns:
                print(f"  ❌ 文件缺少x或y列: {input_file}")
                return False
            
            # 记录原始范围
            original_x_range = f"[{df['x'].min():.3f}, {df['x'].max():.3f}]"
            original_y_range = f"[{df['y'].min():.3f}, {df['y'].max():.3f}]"
            
            # 应用校准
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
            print(f"  ❌ 校准失败: {e}")
            return False
    
    def calibrate_group(self, group_type: str, group_num: int) -> Dict[str, int]:
        """
        校准单个组的数据
        
        Args:
            group_type: 组类型 ('control', 'mci', 'ad')
            group_num: 组编号
            
        Returns:
            校准统计信息
        """
        # 构建路径
        group_name = f"{group_type}_group_{group_num}"
        
        if group_type == "control":
            processed_dir = f"data/control_processed/{group_name}"
            calibrated_dir = f"data/control_calibrated/{group_name}"
        elif group_type == "mci":
            processed_dir = f"data/mci_processed/{group_name}"
            calibrated_dir = f"data/mci_calibrated/{group_name}"
        elif group_type == "ad":
            processed_dir = f"data/ad_processed/{group_name}"
            calibrated_dir = f"data/ad_calibrated/{group_name}"
        else:
            print(f"❌ 未知组类型: {group_type}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        # 检查输入目录
        if not os.path.exists(processed_dir):
            print(f"⚠️  目录不存在: {processed_dir}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        # 创建输出目录
        os.makedirs(calibrated_dir, exist_ok=True)
        
        # 查找CSV文件
        csv_files = []
        for file in os.listdir(processed_dir):
            if file.endswith('_preprocessed.csv'):
                csv_files.append(file)
        
        if not csv_files:
            print(f"⚠️  在 {processed_dir} 中未找到预处理文件")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        csv_files.sort()
        print(f"发现 {len(csv_files)} 个文件")
        
        # 校准每个文件
        success_count = 0
        failed_count = 0
        
        pbar = tqdm(csv_files, desc=f"校准{group_name}")
        
        for csv_file in pbar:
            input_path = os.path.join(processed_dir, csv_file)
            
            # 生成输出文件名
            name, ext = os.path.splitext(csv_file)
            output_filename = f"{name}_calibrated{ext}"
            output_path = os.path.join(calibrated_dir, output_filename)
            
            print(f"\n  处理: {csv_file}")
            
            # 获取校准参数
            x_offset, y_offset, reason = self.get_calibration_params(group_name, csv_file)
            
            # 显示校准信息
            if "默认" in reason:
                print(f"  📋 使用{reason}")
            else:
                print(f"  🎯 使用{reason}")
                if "原因:" not in reason:
                    # 查找原因
                    group_config = self.config.get("group_specific_overrides", {}).get(group_name, {})
                    if "reason" in group_config:
                        print(f"     原因: {group_config['reason']}")
            
            # 执行校准
            if self.calibrate_csv_file(input_path, output_path, x_offset, y_offset):
                print(f"  ✓ 已保存: {output_filename}")
                success_count += 1
            else:
                failed_count += 1
        
        print(f"\n✓ {group_name} 校准完成: {success_count}/{len(csv_files)} 个文件")
        
        return {
            'total': len(csv_files),
            'success': success_count,
            'failed': failed_count
        }
    
    def calibrate_all_control_groups(self) -> Dict[str, int]:
        """校准所有控制组"""
        from config.config import CONTROL_GROUP_START, CONTROL_GROUP_END
        
        print("🎯 校准所有控制组数据")
        print("=" * 60)
        
        total_stats = {'total': 0, 'success': 0, 'failed': 0}
        
        for group_num in range(CONTROL_GROUP_START, CONTROL_GROUP_END + 1):
            print(f"\n=== 校准 control_group_{group_num} ===")
            
            stats = self.calibrate_group("control", group_num)
            
            # 累计统计
            total_stats['total'] += stats['total']
            total_stats['success'] += stats['success']
            total_stats['failed'] += stats['failed']
        
        return total_stats
    
    def calibrate_all_mci_groups(self) -> Dict[str, int]:
        """校准所有MCI组"""
        print("🎯 校准所有MCI组数据")
        print("=" * 60)
        
        total_stats = {'total': 0, 'success': 0, 'failed': 0}
        
        # MCI组通常从1开始，具体范围可以从配置中读取
        for group_num in range(1, 21):  # 假设1-20
            mci_dir = f"data/mci_processed/mci_group_{group_num}"
            if os.path.exists(mci_dir):
                print(f"\n=== 校准 mci_group_{group_num} ===")
                
                stats = self.calibrate_group("mci", group_num)
                
                # 累计统计
                total_stats['total'] += stats['total']
                total_stats['success'] += stats['success']
                total_stats['failed'] += stats['failed']
        
        return total_stats
    
    def calibrate_all_ad_groups(self) -> Dict[str, int]:
        """校准所有AD组"""
        print("🎯 校准所有AD组数据")
        print("=" * 60)
        
        total_stats = {'total': 0, 'success': 0, 'failed': 0}
        
        # AD组通常从1开始，具体范围可以从配置中读取
        for group_num in range(1, 21):  # 假设1-20
            ad_dir = f"data/ad_processed/ad_group_{group_num}"
            if os.path.exists(ad_dir):
                print(f"\n=== 校准 ad_group_{group_num} ===")
                
                stats = self.calibrate_group("ad", group_num)
                
                # 累计统计
                total_stats['total'] += stats['total']
                total_stats['success'] += stats['success']
                total_stats['failed'] += stats['failed']
        
        return total_stats
    
    def show_calibration_summary(self):
        """显示校准配置摘要"""
        print("=" * 60)
        print("📋 校准配置摘要")
        print("=" * 60)
        
        # 默认配置
        defaults = self.config.get("default_profiles", {})
        print("🎯 默认配置:")
        for profile_name, profile in defaults.items():
            print(f"  {profile_name}: x{profile['offset_x']:+.3f}, y{profile['offset_y']:+.3f}")
            print(f"    {profile.get('description', '')}")
        
        # 组特定配置
        group_overrides = self.config.get("group_specific_overrides", {})
        if group_overrides:
            print("\n🔧 组特定配置:")
            for group_name, override in group_overrides.items():
                print(f"  {group_name}: x{override['offset_x']:+.3f}, y{override['offset_y']:+.3f}")
                print(f"    原因: {override.get('reason', '未指定')}")
        
        # 文件特定配置
        file_overrides = self.config.get("file_specific_overrides", {})
        if file_overrides:
            print("\n📄 文件特定配置:")
            for filename, override in file_overrides.items():
                print(f"  {filename}: x{override['offset_x']:+.3f}, y{override['offset_y']:+.3f}")
                print(f"    原因: {override.get('reason', '未指定')}")
        
        print("=" * 60)

def main():
    """主函数 - 用于测试"""
    calibrator = AdvancedCalibrator()
    calibrator.show_calibration_summary()
    
    print("\n🔧 高级校准器使用示例:")
    print("calibrator = AdvancedCalibrator()")
    print("calibrator.calibrate_all_control_groups()")

if __name__ == "__main__":
    main() 