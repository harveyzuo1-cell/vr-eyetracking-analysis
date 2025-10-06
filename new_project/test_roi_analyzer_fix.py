"""
测试ROIAnalyzer格式兼容性修复
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.web.modules.module01_data_visualization.roi_analyzer import ROIAnalyzer

# 测试新格式（分层结构）
new_format = {
    "keywords": [
        {
            "id": "KW_q1_1",
            "normalized_coords": [0.1, 0.2, 0.3, 0.4],
            "task_id": "q1",
            "type": "KW",
            "version": "v2"
        }
    ],
    "instructions": [
        {
            "id": "INST_q1_1",
            "normalized_coords": [0.5, 0.6, 0.2, 0.1],
            "task_id": "q1",
            "type": "INST",
            "version": "v2"
        }
    ],
    "background": [
        {
            "id": "BG_q1",
            "normalized_coords": [0, 0, 1, 1],
            "task_id": "q1",
            "type": "BG",
            "version": "v2"
        }
    ]
}

# 测试旧格式（扁平列表）
old_format = [
    {
        "id": "KW_q1_1",
        "x": 0.1,
        "y": 0.2,
        "width": 0.3,
        "height": 0.4,
        "name": "KW_q1_1",
        "type": "keyword"
    },
    {
        "id": "BG_q1",
        "x": 0,
        "y": 0,
        "width": 1,
        "height": 1,
        "name": "BG_q1",
        "type": "background"
    }
]

print("=" * 60)
print("测试ROIAnalyzer格式兼容性")
print("=" * 60)

print("\n[测试1] 新格式（分层结构）")
try:
    analyzer1 = ROIAnalyzer(new_format)
    print(f"  [OK] 初始化成功，共 {len(analyzer1.regions)} 个区域")
    for r in analyzer1.regions:
        print(f"       - {r['id']}: x={r['x']}, y={r['y']}, w={r['width']}, h={r['height']}")
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n[测试2] 旧格式（扁平列表）")
try:
    analyzer2 = ROIAnalyzer(old_format)
    print(f"  [OK] 初始化成功，共 {len(analyzer2.regions)} 个区域")
    for r in analyzer2.regions:
        print(f"       - {r['id']}: x={r['x']}, y={r['y']}, w={r['width']}, h={r['height']}")
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n[测试3] 查找ROI点")
try:
    analyzer = ROIAnalyzer(new_format)
    test_points = [
        (0.2, 0.3),  # 应该在KW_q1_1内
        (0.6, 0.65), # 应该在INST_q1_1内
        (0.9, 0.9),  # 应该在BG_q1内
    ]
    for x, y in test_points:
        roi_id = analyzer.find_roi_for_point(x, y)
        print(f"  点({x}, {y}) -> {roi_id}")
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
