#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR眼球追踪数据可视化系统主入口
启动Web可视化服务器
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="VR眼球追踪数据可视化系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python visualize.py                    # 启动默认配置的可视化服务器
  python visualize.py --port 9000       # 指定端口启动
  python visualize.py --host 0.0.0.0    # 允许外部访问
  python visualize.py --no-browser       # 不自动打开浏览器
  python visualize.py --debug            # 开启调试模式
        """
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Web服务器端口 (默认: 8080)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Web服务器主机地址 (默认: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='不自动打开浏览器'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='开启调试模式'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/eyetracking_analysis_config.json',
        help='分析配置文件路径'
    )
    
    args = parser.parse_args()
    
    try:
        print("🎯 VR眼球追踪数据可视化系统")
        print("=" * 60)
        
        # 导入并启动可视化器
        from visualization.enhanced_web_visualizer import EnhancedWebVisualizer
        
        # 初始化可视化器
        visualizer = EnhancedWebVisualizer(config_file=args.config)
        
        print(f"📊 系统信息:")
        print(f"  - 配置文件: {args.config}")
        print(f"  - 服务地址: http://{args.host}:{args.port}")
        print(f"  - 调试模式: {'开启' if args.debug else '关闭'}")
        print(f"  - 自动打开浏览器: {'否' if args.no_browser else '是'}")
        
        # 启动服务器
        visualizer.run_server(
            host=args.host,
            port=args.port,
            debug=args.debug,
            open_browser=not args.no_browser
        )
        
    except ImportError as e:
        print(f"❌ 依赖库导入失败: {e}")
        print("💡 请安装所需依赖: pip install -r requirements.txt")
        return 1
    
    except Exception as e:
        print(f"❌ 启动可视化系统失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 