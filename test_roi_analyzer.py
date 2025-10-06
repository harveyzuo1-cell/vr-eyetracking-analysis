"""
测试ROI分析器的准确性
"""

# 模拟前端的ROI分析器逻辑
def is_point_in_roi(x, y, roi):
    return (
        x >= roi['x'] and
        x <= roi['x'] + roi['width'] and
        y >= roi['y'] and
        y <= roi['y'] + roi['height']
    )

def calculate_roi_stats(gaze_data, roi):
    if not gaze_data or len(gaze_data) == 0:
        return {
            'entry_count': 0,
            'exit_count': 0,
            'points_inside': 0,
            'total_points': 0,
            'inside_ratio': 0,
            'duration_inside': 0
        }

    entry_count = 0
    exit_count = 0
    points_inside = 0
    duration_inside = 0
    was_inside = False

    for i in range(len(gaze_data)):
        point = gaze_data[i]
        is_inside = is_point_in_roi(point['x'], point['y'], roi)

        # 状态机: 跟踪进出
        if is_inside and not was_inside:
            entry_count += 1  # 进入ROI
        elif not is_inside and was_inside:
            exit_count += 1   # 离开ROI

        if is_inside:
            points_inside += 1
            if i < len(gaze_data) - 1:
                time_diff = gaze_data[i + 1]['timestamp'] - point['timestamp']
                duration_inside += time_diff

        was_inside = is_inside

    total_points = len(gaze_data)
    inside_ratio = points_inside / total_points if total_points > 0 else 0

    return {
        'entry_count': entry_count,
        'exit_count': exit_count,
        'points_inside': points_inside,
        'total_points': total_points,
        'inside_ratio': inside_ratio,
        'duration_inside': duration_inside
    }


# 测试用例
def test_roi_analyzer():
    print("=" * 60)
    print("ROI分析器测试")
    print("=" * 60)

    # 测试ROI配置
    roi = {
        'id': 'test_roi',
        'name': '测试ROI',
        'x': 0.2,
        'y': 0.2,
        'width': 0.3,
        'height': 0.3,
        'color': '#FF6B6B'
    }

    print(f"\nROI配置: x={roi['x']}, y={roi['y']}, width={roi['width']}, height={roi['height']}")
    print(f"ROI范围: X=[{roi['x']}, {roi['x'] + roi['width']}], Y=[{roi['y']}, {roi['y'] + roi['height']}]")

    # 测试数据: 模拟眼动轨迹
    # 轨迹: 外部(0.1, 0.1) -> 进入(0.3, 0.3) -> 内部(0.4, 0.4) -> 离开(0.6, 0.6) -> 再进入(0.3, 0.3) -> 内部(0.35, 0.35)
    gaze_data = [
        {'x': 0.1, 'y': 0.1, 'timestamp': 0.0},    # 外部
        {'x': 0.3, 'y': 0.3, 'timestamp': 0.5},    # 进入ROI (entry #1)
        {'x': 0.4, 'y': 0.4, 'timestamp': 1.0},    # 内部
        {'x': 0.6, 'y': 0.6, 'timestamp': 1.5},    # 离开ROI (exit #1)
        {'x': 0.3, 'y': 0.3, 'timestamp': 2.0},    # 再次进入 (entry #2)
        {'x': 0.35, 'y': 0.35, 'timestamp': 2.5},  # 内部
    ]

    print(f"\n眼动轨迹数据 ({len(gaze_data)}个点):")
    for i, point in enumerate(gaze_data):
        in_roi = is_point_in_roi(point['x'], point['y'], roi)
        status = "内部" if in_roi else "外部"
        print(f"  点{i+1}: ({point['x']:.2f}, {point['y']:.2f}) @ {point['timestamp']:.1f}s - {status}")

    # 计算统计
    stats = calculate_roi_stats(gaze_data, roi)

    print(f"\n统计结果:")
    print(f"  进入次数: {stats['entry_count']}")
    print(f"  离开次数: {stats['exit_count']}")
    print(f"  内部点数: {stats['points_inside']} / {stats['total_points']}")
    print(f"  覆盖率: {stats['inside_ratio']*100:.1f}%")
    print(f"  停留时间: {stats['duration_inside']:.2f}秒")

    # 验证预期结果
    print(f"\n验证:")
    expected = {
        'entry_count': 2,  # 进入了2次
        'exit_count': 1,   # 离开了1次（最后一次还在内部，没有离开）
        'points_inside': 4, # 点2,3,5,6在内部
        'inside_ratio': 4/6,
    }

    passed = True
    if stats['entry_count'] != expected['entry_count']:
        print(f"  ❌ 进入次数错误: 期望{expected['entry_count']}, 实际{stats['entry_count']}")
        passed = False
    else:
        print(f"  ✅ 进入次数正确: {stats['entry_count']}")

    if stats['exit_count'] != expected['exit_count']:
        print(f"  ❌ 离开次数错误: 期望{expected['exit_count']}, 实际{stats['exit_count']}")
        passed = False
    else:
        print(f"  ✅ 离开次数正确: {stats['exit_count']}")

    if stats['points_inside'] != expected['points_inside']:
        print(f"  ❌ 内部点数错误: 期望{expected['points_inside']}, 实际{stats['points_inside']}")
        passed = False
    else:
        print(f"  ✅ 内部点数正确: {stats['points_inside']}")

    if abs(stats['inside_ratio'] - expected['inside_ratio']) > 0.001:
        print(f"  ❌ 覆盖率错误: 期望{expected['inside_ratio']*100:.1f}%, 实际{stats['inside_ratio']*100:.1f}%")
        passed = False
    else:
        print(f"  ✅ 覆盖率正确: {stats['inside_ratio']*100:.1f}%")

    print(f"\n{'='*60}")
    if passed:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败!")
    print(f"{'='*60}")


if __name__ == '__main__':
    test_roi_analyzer()
