"""
测试ROI统计bug - 为什么没有轨迹经过INST区域还有时长统计
"""
import sys
import json
import pandas as pd
import numpy as np

# 添加项目路径
sys.path.insert(0, 'new_project')

from src.web.modules.module01_data_visualization.roi_analyzer import ROIAnalyzer

def test_roi_boundary_issue():
    """测试ROI边界判断问题"""

    print("="*80)
    print("测试场景：y=-0.28的点是否会被错误判断为在INST区域内")
    print("="*80)

    # 1. 加载v2 task1的ROI配置
    with open('new_project/data/roi_configs/v2/task1_roi.json', 'r', encoding='utf-8') as f:
        roi_config = json.load(f)

    print("\n【ROI配置】")
    print(f"Keywords数量: {len(roi_config['regions']['keywords'])}")
    print(f"Instructions数量: {len(roi_config['regions']['instructions'])}")
    print(f"Background数量: {len(roi_config['regions']['background'])}")

    # 打印INST区域的范围
    if roi_config['regions']['instructions']:
        inst = roi_config['regions']['instructions'][0]
        coords = inst['normalized_coords']
        print(f"\nINST区域范围:")
        print(f"  ID: {inst['id']}")
        print(f"  x范围: [{coords[0]:.4f}, {coords[0]+coords[2]:.4f}]")
        print(f"  y范围: [{coords[1]:.4f}, {coords[1]+coords[3]:.4f}]")
        print(f"  原始坐标: {coords}")

    # 2. 创建分析器
    analyzer = ROIAnalyzer(roi_config['regions'])

    # 3. 测试点 y=-0.28
    test_points = [
        (0.2, -0.28, "测试点1: x=0.2, y=-0.28"),
        (0.5, -0.28, "测试点2: x=0.5, y=-0.28"),
        (0.1, -0.28, "测试点3: x=0.1, y=-0.28"),
        (0.0, -0.28, "测试点4: x=0.0, y=-0.28"),
        (0.2, 0.5, "测试点5: x=0.2, y=0.5 (正常范围)"),
    ]

    print("\n【点匹配测试】")
    for x, y, desc in test_points:
        roi_id = analyzer.find_roi_for_point(x, y)
        print(f"{desc} -> ROI: {roi_id}")

    # 4. 创建模拟数据 - 所有点都在y=-0.28
    print("\n【模拟数据统计测试】")
    n_points = 100
    gaze_data = pd.DataFrame({
        'x': np.linspace(0, 1, n_points),  # x从0到1均匀分布
        'y': np.full(n_points, -0.28),      # y全部是-0.28
        'timestamp': np.linspace(0, 10, n_points)  # 时间0-10秒
    })

    print(f"数据点数: {len(gaze_data)}")
    print(f"所有点的y坐标: {gaze_data['y'].unique()}")
    print(f"x范围: [{gaze_data['x'].min():.2f}, {gaze_data['x'].max():.2f}]")
    print(f"时间范围: [{gaze_data['timestamp'].min():.2f}, {gaze_data['timestamp'].max():.2f}]秒")

    # 5. 计算统计
    stats = analyzer.calculate_stats(gaze_data)

    print("\n【ROI统计结果】")
    for roi_id, st in stats.items():
        if st['fixation_time'] > 0 or st['points_inside'] > 0:
            print(f"\n{roi_id}:")
            print(f"  类型: {st['type']}")
            print(f"  停留时间: {st['fixation_time']:.2f}秒")
            print(f"  内部点数: {st['points_inside']}")
            print(f"  进入次数: {st['entry_count']}")

    # 6. 检查INST区域
    print("\n【问题诊断】")
    inst_regions = [roi_id for roi_id in stats.keys() if roi_id.startswith('INST')]
    for inst_id in inst_regions:
        st = stats[inst_id]
        if st['fixation_time'] > 0:
            print(f"❌ 错误！{inst_id} 有 {st['fixation_time']:.2f}秒 的停留时间")
            print(f"   但所有数据点的y=-0.28，不应该在INST区域内！")

            # 找到对应的region配置
            for region in analyzer.regions:
                if region['id'] == inst_id:
                    print(f"   INST区域y范围: [{region['y']:.4f}, {region['y']+region['height']:.4f}]")
                    print(f"   检查：-0.28是否在此范围内？")
                    if region['y'] <= -0.28 <= region['y'] + region['height']:
                        print(f"   ✓ 是的，-0.28在范围内！这就是bug！")
                    else:
                        print(f"   ✗ 不在范围内")
        else:
            print(f"✓ 正确！{inst_id} 没有停留时间")

def test_correct_roi_logic():
    """测试修复后的逻辑"""
    print("\n" + "="*80)
    print("测试修复方案：ROI坐标应该都在[0,1]范围内")
    print("="*80)

    # 加载v2 task1的ROI配置
    with open('new_project/data/roi_configs/v2/task1_roi.json', 'r', encoding='utf-8') as f:
        roi_config = json.load(f)

    print("\n检查所有ROI区域的坐标范围：")
    for region_type in ['keywords', 'instructions', 'background']:
        print(f"\n{region_type}:")
        for region in roi_config['regions'].get(region_type, []):
            coords = region['normalized_coords']
            x_min, y_min, w, h = coords
            x_max = x_min + w
            y_max = y_min + h

            # 检查是否超出[0,1]范围
            out_of_bounds = []
            if x_min < 0: out_of_bounds.append(f"x_min={x_min:.4f} < 0")
            if x_max > 1: out_of_bounds.append(f"x_max={x_max:.4f} > 1")
            if y_min < 0: out_of_bounds.append(f"y_min={y_min:.4f} < 0")
            if y_max > 1: out_of_bounds.append(f"y_max={y_max:.4f} > 1")

            status = "❌ " if out_of_bounds else "✓ "
            print(f"  {status}{region['id']}: x=[{x_min:.4f}, {x_max:.4f}], y=[{y_min:.4f}, {y_max:.4f}]")
            if out_of_bounds:
                print(f"    问题: {', '.join(out_of_bounds)}")

if __name__ == "__main__":
    test_roi_boundary_issue()
    test_correct_roi_logic()
