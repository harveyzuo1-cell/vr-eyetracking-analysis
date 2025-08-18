#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR眼球追踪数据校准系统 - 主入口脚本
提供简单易用的校准功能接口
"""

import sys
import os
import argparse
from pathlib import Path

# 添加子模块到Python路径
sys.path.append(str(Path(__file__).parent))

def parse_range_string(range_str: str) -> list:
    """解析范围字符串，如 "1,2,3,5" 或 "13-22" """
    if not range_str:
        return None
    
    result = []
    parts = range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # 处理范围，如 "13-22"
            start, end = map(int, part.split('-'))
            result.extend(range(start, end + 1))
        else:
            # 处理单个数字
            result.append(int(part))
    
    return sorted(list(set(result)))  # 去重并排序

def parse_offset_string(offset_str: str) -> tuple:
    """解析偏移量字符串，如 "0.01,-0.09" """
    if not offset_str:
        return None, None
    
    try:
        parts = offset_str.split(',')
        if len(parts) != 2:
            raise ValueError("偏移量格式应为 'x_offset,y_offset'")
        
        x_offset = float(parts[0].strip())
        y_offset = float(parts[1].strip())
        return x_offset, y_offset
    except Exception as e:
        print(f"❌ 偏移量参数格式错误: {e}")
        return None, None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="VR眼球追踪数据校准系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python calibrate.py                    # 运行完整校准（所有三组）
  python calibrate.py --control-only     # 仅校准对照组
  python calibrate.py --mci-only         # 仅校准MCI组
  python calibrate.py --ad-only          # 仅校准AD组
  python calibrate.py --config custom.json  # 使用自定义配置文件
  python calibrate.py --summary          # 仅显示配置摘要
  
  就地覆盖校准模式:
  python calibrate.py --inplace          # 就地覆盖校准所有数据
  python calibrate.py --inplace --questions "1,2,3,5"  # 仅校准题目1,2,3,5
  python calibrate.py --inplace --folders "13-22"      # 仅校准文件夹13-22
  python calibrate.py --inplace --manual-offset "0.01,-0.09"  # 手动指定偏移量
  
  可视化模式:
  python calibrate.py --visualize        # 启动Web可视化界面
  python calibrate.py --visualize --vis-port 9000  # 指定可视化端口
        """
    )
    
    parser.add_argument(
        '--control-only', 
        action='store_true',
        help='仅校准对照组数据'
    )
    
    parser.add_argument(
        '--mci-only',
        action='store_true', 
        help='仅校准MCI组数据'
    )
    
    parser.add_argument(
        '--ad-only',
        action='store_true',
        help='仅校准AD组数据'
    )
    
    parser.add_argument(
        '--inplace',
        action='store_true',
        help='使用就地覆盖校准模式（直接修改原文件）'
    )
    
    parser.add_argument(
        '--questions',
        type=str,
        help='指定题号过滤，如 "1,2,3,5" 或 "3-5"'
    )
    
    parser.add_argument(
        '--folders',
        type=str,
        help='指定文件夹范围，如 "13,14,15" 或 "13-22"'
    )
    
    parser.add_argument(
        '--manual-offset',
        type=str,
        help='手动指定偏移量，格式: "x_offset,y_offset"，如 "0.01,-0.09"'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='启动Web可视化界面'
    )
    
    parser.add_argument(
        '--vis-port',
        type=int,
        default=8080,
        help='可视化服务器端口 (默认: 8080)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/calibration_config.json',
        help='校准配置文件路径 (默认: config/calibration_config.json)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='仅显示配置摘要，不执行校准'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出'
    )
    
    args = parser.parse_args()
    
    # 检查配置文件是否存在
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        print("   请检查文件路径或使用 --config 指定正确的配置文件")
        return 1
    
    try:
        print("🎯 VR眼球追踪数据校准系统")
        print("=" * 60)
        
        # 处理可视化模式
        if args.visualize:
            try:
                from visualization.enhanced_web_visualizer import EnhancedWebVisualizer
                
                print("🌐 启动Web可视化界面...")
                print(f"📡 服务地址: http://127.0.0.1:{args.vis_port}")
                
                # 初始化可视化器
                visualizer = EnhancedWebVisualizer(config_file=args.config)
                
                # 启动服务器
                visualizer.run_server(
                    host='127.0.0.1',
                    port=args.vis_port,
                    debug=args.verbose,
                    auto_open=True
                )
                
                return 0
                
            except ImportError as e:
                print(f"❌ 可视化模块导入失败: {e}")
                print("💡 请安装可视化依赖: pip install flask pillow opencv-python")
                return 1
            except Exception as e:
                print(f"❌ 启动可视化服务失败: {e}")
                return 1
        
        # 处理就地覆盖校准模式
        if args.inplace:
            from calibration.inplace_calibrator import InplaceCalibrator
            
            print("⚠️  注意：就地覆盖模式将直接修改原文件！")
            
            # 解析参数
            question_list = parse_range_string(args.questions)
            folder_list = parse_range_string(args.folders)
            manual_x, manual_y = parse_offset_string(args.manual_offset)
            
            # 初始化就地校准器
            inplace_calibrator = InplaceCalibrator(config_file=args.config)
            
            if args.verbose:
                print(f"🔢 题号过滤: {question_list if question_list else '所有题目'}")
                print(f"📁 文件夹范围: {folder_list if folder_list else '默认范围'}")
                if manual_x is not None and manual_y is not None:
                    print(f"⚙️  手动偏移: x{manual_x:+.3f}, y{manual_y:+.3f}")
            
            # 执行就地校准（这里需要根据实际数据路径调整）
            ctg_base = r"C:\Users\asino\entropy\ip\mci-dataprocessing\ctg"
            
            use_config_params = (manual_x is None or manual_y is None)
            
            total_processed = inplace_calibrator.calibrate_all_subfolders_inplace(
                base_dir=ctg_base,
                folder_range=folder_list,
                subfolder_name="adjustcsvfile",
                offset_x=manual_x if manual_x is not None else 0.0,
                offset_y=manual_y if manual_y is not None else 0.0,
                question_list=question_list,
                use_config_params=use_config_params
            )
            
            print(f"\n🎉 就地校准完成!")
            print(f"📊 总计处理: {total_processed} 个文件")
            return 0
        
        # 标准校准模式
        from calibration.advanced_calibrator import AdvancedCalibrator
        
        # 初始化校准器
        calibrator = AdvancedCalibrator(config_file=args.config)
        
        # 如果只是显示摘要
        if args.summary:
            calibrator.show_calibration_summary()
            return 0
        
        # 执行校准
        control_success = 0
        mci_success = 0
        ad_success = 0
        
        # 检查是否指定了特定组
        run_control = args.control_only or not any([args.control_only, args.mci_only, args.ad_only])
        run_mci = args.mci_only or not any([args.control_only, args.mci_only, args.ad_only])
        run_ad = args.ad_only or not any([args.control_only, args.mci_only, args.ad_only])
        
        if args.verbose:
            calibrator.show_calibration_summary()
        
        # 校准对照组
        if run_control:
            control_success = calibrator.calibrate_all_control_groups()
        
        # 校准MCI组
        if run_mci:
            mci_success = calibrator.calibrate_all_mci_groups()
        
        # 校准AD组
        if run_ad:
            ad_success = calibrator.calibrate_all_ad_groups()
        
        # 显示结果
        print("\n" + "=" * 60)
        print("🎉 校准完成！")
        
        if run_control:
            print(f"📊 对照组成功校准: {control_success} 个文件")
        if run_mci:
            print(f"🧠 MCI组成功校准: {mci_success} 个文件")
        if run_ad:
            print(f"🧬 AD组成功校准: {ad_success} 个文件")
        
        total_success = control_success + mci_success + ad_success
        print(f"📋 总计: {total_success} 个文件")
        
        if total_success > 0:
            print("\n💡 校准建议:")
            print("1. 检查校准后的数据质量")
            print("2. 根据分析结果调整个体参数")
            print("3. 在配置文件中记录调整原因")
            print("4. 推荐使用校准后的数据进行研究分析")
        
        return 0
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("   请确保所有必要的模块都在正确的位置")
        return 1
    except Exception as e:
        print(f"❌ 校准过程中出现错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 