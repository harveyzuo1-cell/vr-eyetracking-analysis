"""
测试ROI统计API - 使用实际的API请求
"""
import requests
import json
import numpy as np

BASE_URL = "http://127.0.0.1:9090"

def test_roi_stats_with_negative_y():
    """测试y坐标为负数时的ROI统计"""

    print("="*80)
    print("测试：发送y=-0.28的眼动数据，检查INST区域是否错误统计")
    print("="*80)

    # 创建测试数据 - 所有点y=-0.28
    n_points = 100
    gaze_data = []
    for i in range(n_points):
        gaze_data.append({
            'x': i / n_points,  # x从0到1
            'y': -0.28,         # y全部是-0.28
            'timestamp': i * 0.1  # 时间间隔0.1秒
        })

    # 发送到API
    url = f"{BASE_URL}/api/data/roi-stats"
    payload = {
        'version': 'v2',
        'task': 'q1',
        'gaze_data': gaze_data
    }

    print(f"\n发送请求到: {url}")
    print(f"数据点数: {len(gaze_data)}")
    print(f"y坐标: {gaze_data[0]['y']}")
    print(f"x范围: [{gaze_data[0]['x']:.2f}, {gaze_data[-1]['x']:.2f}]")

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"\n错误! 状态码: {response.status_code}")
        print(response.text)
        return

    data = response.json()

    if not data.get('success'):
        print(f"\n错误! API返回失败: {data.get('message')}")
        return

    print("\n【API响应成功】")
    stats = data['data']['stats']
    summary = data['data']['summary']

    print(f"\n总停留时间: {summary.get('total_fixation_time', 0):.2f}秒")
    print(f"Keywords停留时间: {summary.get('keywords_fixation_time', 0):.2f}秒")
    print(f"Instructions停留时间: {summary.get('instructions_fixation_time', 0):.2f}秒")
    print(f"Background停留时间: {summary.get('background_fixation_time', 0):.2f}秒")

    # 检查INST区域
    print("\n【INST区域统计】")
    inst_found = False
    for roi_id, st in stats.items():
        if roi_id.startswith('INST'):
            inst_found = True
            print(f"\n{roi_id}:")
            print(f"  停留时间: {st['fixation_time']:.2f}秒")
            print(f"  内部点数: {st['points_inside']}")
            print(f"  进入次数: {st['entry_count']}")

            if st['fixation_time'] > 0:
                print(f"  ❌ 错误！y=-0.28不应该在INST区域内！")
            else:
                print(f"  ✓ 正确！没有停留时间")

    if not inst_found:
        print("未找到INST区域统计")

    # 打印所有有停留时间的区域
    print("\n【所有有停留时间的区域】")
    for roi_id, st in stats.items():
        if st['fixation_time'] > 0:
            print(f"{roi_id}: {st['fixation_time']:.2f}秒 ({st['points_inside']}点)")

def test_roi_stats_with_mixed_y():
    """测试混合y坐标的数据"""

    print("\n" + "="*80)
    print("测试：发送混合y坐标的数据（部分在INST区域内，部分不在）")
    print("="*80)

    # 创建测试数据
    gaze_data = []

    # 前50个点：y=-0.28（不在INST内）
    for i in range(50):
        gaze_data.append({
            'x': 0.2,
            'y': -0.28,
            'timestamp': i * 0.1
        })

    # 后50个点：y=0.3（在INST内，INST y范围约0.245-0.395）
    for i in range(50, 100):
        gaze_data.append({
            'x': 0.2,
            'y': 0.3,
            'timestamp': i * 0.1
        })

    url = f"{BASE_URL}/api/data/roi-stats"
    payload = {
        'version': 'v2',
        'task': 'q1',
        'gaze_data': gaze_data
    }

    print(f"\n数据点数: {len(gaze_data)}")
    print(f"前50点 y=-0.28")
    print(f"后50点 y=0.3")

    response = requests.post(url, json=payload)
    data = response.json()

    if not data.get('success'):
        print(f"\n错误! {data.get('message')}")
        return

    print("\n【API响应成功】")
    stats = data['data']['stats']

    # 检查INST区域
    for roi_id, st in stats.items():
        if roi_id.startswith('INST'):
            print(f"\n{roi_id}:")
            print(f"  停留时间: {st['fixation_time']:.2f}秒")
            print(f"  内部点数: {st['points_inside']}")

            # 预期：50个点在INST内（后50个），时间约5秒
            expected_points = 50
            if st['points_inside'] == expected_points:
                print(f"  ✓ 正确！内部点数={expected_points}")
            else:
                print(f"  ❌ 错误！预期{expected_points}个点，实际{st['points_inside']}个")

if __name__ == "__main__":
    try:
        test_roi_stats_with_negative_y()
        test_roi_stats_with_mixed_y()
    except requests.exceptions.ConnectionError:
        print("\n错误：无法连接到后端服务器")
        print("请确保后端服务器运行在 http://127.0.0.1:9090")
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
