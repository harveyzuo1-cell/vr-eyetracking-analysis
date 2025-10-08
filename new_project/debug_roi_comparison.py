"""
调试脚本: 对比Module01和Module04的ROI匹配结果
"""
import pandas as pd
import json
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.web.modules.module01_data_visualization.roi_analyzer import ROIAnalyzer
from src.modules.module04_event_analysis.event_analyzer import EventAnalyzer

# 测试数据
subject = "control_legacy_18"
task = "q4"

# 加载校准后的数据
data_file = project_root / "data" / "02_processed" / "control" / f"{subject}_{task}_calibrated.csv"
print(f"加载数据: {data_file}")
df = pd.read_csv(data_file)
print(f"数据点数: {len(df)}")
print(f"数据列: {df.columns.tolist()}")
print(f"前5行:\n{df.head()}")

# 加载ROI配置
roi_file = project_root / "data" / "roi_configs" / "v1" / f"{task}_roi.json"
print(f"\n加载ROI配置: {roi_file}")
with open(roi_file, 'r', encoding='utf-8') as f:
    roi_config = json.load(f)

# 提取regions
roi_regions = roi_config.get("regions", {})
print(f"ROI区域类型: {list(roi_regions.keys())}")

# 统计每个类型的ROI数量
for roi_type in ["keywords", "instructions", "background"]:
    if roi_type in roi_regions:
        print(f"  {roi_type}: {len(roi_regions[roi_type])} 个区域")

# ============================================================
# 方法1: Module01的ROIAnalyzer (逐帧分析原始数据点)
# ============================================================
print("\n" + "="*60)
print("方法1: Module01 ROIAnalyzer (逐帧分析)")
print("="*60)

analyzer1 = ROIAnalyzer(roi_regions)
stats1 = analyzer1.calculate_stats(df)
summary1 = analyzer1.get_summary(stats1)

print(f"总停留时间: {summary1['total_fixation_time']:.2f}秒")
print(f"  Keywords: {summary1['keywords_fixation_time']:.2f}秒 ({summary1['keywords_fixation_time']/summary1['total_fixation_time']*100:.2f}%)")
print(f"  Instructions: {summary1['instructions_fixation_time']:.2f}秒 ({summary1['instructions_fixation_time']/summary1['total_fixation_time']*100:.2f}%)")
print(f"  Background: {summary1['background_fixation_time']:.2f}秒 ({summary1['background_fixation_time']/summary1['total_fixation_time']*100:.2f}%)")

# ============================================================
# 方法2: Module04的EventAnalyzer (先IVT分段,然后匹配fixation质心)
# ============================================================
print("\n" + "="*60)
print("方法2: Module04 EventAnalyzer (IVT+质心匹配)")
print("="*60)

# 需要转换为milliseconds列
df['milliseconds'] = (df['timestamp'] - df['timestamp'].iloc[0]) * 1000

analyzer2 = EventAnalyzer(velocity_threshold=40, min_fixation_duration=100)
result2 = analyzer2.analyze_file(data_file, roi_regions)

if result2['success']:
    fixations = result2['fixations']
    print(f"检测到的fixation数量: {len(fixations)}")

    # 统计每个ROI的fixation时长
    roi_time = {'bg': 0, 'inst': 0, 'kw': 0, 'no_roi': 0}

    for fix in fixations:
        duration_ms = fix['duration_ms']
        roi = fix.get('roi')

        if roi:
            if roi.startswith('BG_'):
                roi_time['bg'] += duration_ms
            elif roi.startswith('INST_'):
                roi_time['inst'] += duration_ms
            elif roi.startswith('KW_'):
                roi_time['kw'] += duration_ms
        else:
            roi_time['no_roi'] += duration_ms

    total_fixation_time = sum(roi_time.values())
    print(f"总fixation时长: {total_fixation_time/1000:.2f}秒")
    print(f"  Keywords: {roi_time['kw']/1000:.2f}秒 ({roi_time['kw']/total_fixation_time*100:.2f}%)")
    print(f"  Instructions: {roi_time['inst']/1000:.2f}秒 ({roi_time['inst']/total_fixation_time*100:.2f}%)")
    print(f"  Background: {roi_time['bg']/1000:.2f}秒 ({roi_time['bg']/total_fixation_time*100:.2f}%)")
    print(f"  无ROI标注: {roi_time['no_roi']/1000:.2f}秒 ({roi_time['no_roi']/total_fixation_time*100:.2f}%)")

    # 输出前10个fixation的详细信息
    print("\n前10个fixation的详细信息:")
    for i, fix in enumerate(fixations[:10]):
        print(f"  Fixation {i+1}:")
        print(f"    质心: ({fix['centroid_x']:.4f}, {fix['centroid_y']:.4f})")
        print(f"    时长: {fix['duration_ms']:.2f}ms")
        print(f"    ROI: {fix.get('roi', 'None')}")

        # 手动测试Y轴翻转前后的ROI匹配
        x, y = fix['centroid_x'], fix['centroid_y']
        y_flipped = 1 - y

        # 找到匹配的ROI
        matched_roi_original = None
        matched_roi_flipped = None

        for priority in ["keywords", "instructions", "background"]:
            if priority in roi_regions:
                for region in roi_regions[priority]:
                    coords = region.get("normalized_coords", [])
                    if len(coords) == 4:
                        x_min, y_min, width, height = coords
                        x_max = x_min + width
                        y_max = y_min + height

                        # 测试原始Y坐标
                        if x_min <= x <= x_max and y_min <= y <= y_max:
                            matched_roi_original = region.get("id", "unknown")

                        # 测试翻转后的Y坐标
                        if x_min <= x <= x_max and y_min <= y_flipped <= y_max:
                            matched_roi_flipped = region.get("id", "unknown")

        print(f"    手动测试 - 原始Y: {matched_roi_original}")
        print(f"    手动测试 - 翻转Y: {matched_roi_flipped}")

else:
    print(f"分析失败: {result2.get('error')}")

# ============================================================
# 结论
# ============================================================
print("\n" + "="*60)
print("结论")
print("="*60)
print("如果两种方法的ROI占比差异很大,说明:")
print("1. IVT算法的fixation检测可能过滤掉了一些数据点")
print("2. Fixation质心可能与原始数据点分布不同")
print("3. 或者Y轴翻转逻辑仍然有问题")
