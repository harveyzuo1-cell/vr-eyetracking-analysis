#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VR眼动数据分析系统 - 一键启动脚本
功能：数据处理、校准、分析、Web可视化
"""

import os
import sys
import webbrowser
import threading
import time
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def start_web_server():
    """启动Web可视化服务器"""
    try:
        # 导入Flask应用
        from visualization.enhanced_web_visualizer import EnhancedWebVisualizer
        
        print("🌐 VR眼动数据分析系统")
        print("=" * 50)
        print(f"🌐 启动Web可视化服务器")
        print(f"📍 地址: http://127.0.0.1:8080")
        print(f"🎨 功能: 眼动轨迹可视化、ROI分析、三组数据对比")
        print("=" * 50)
        
        # 创建可视化器
        visualizer = EnhancedWebVisualizer()
        
        # 延迟打开浏览器
        def open_browser_delayed():
            time.sleep(1.5)
            webbrowser.open('http://127.0.0.1:8080')
        threading.Thread(target=open_browser_delayed, daemon=True).start()
        
        # 启动服务器
        visualizer.run_server(host='127.0.0.1', port=8080, debug=False, open_browser=False)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保安装了所有依赖: pip install -r requirements.txt")
        input("按回车键退出...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    start_web_server() 