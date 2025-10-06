"""
测试ROI版本问题
Test ROI version loading issue
"""
import requests
import json

BASE_URL = "http://127.0.0.1:9090"

def test_roi_v1_q1():
    """测试v1 Q1的ROI配置"""
    print("\n========== 测试 v1 Q1 ROI ==========")
    url = f"{BASE_URL}/api/data/roi"
    params = {"version": "v1", "task": "q1"}

    response = requests.get(url, params=params)
    print(f"请求URL: {response.url}")
    print(f"状态码: {response.status_code}")

    data = response.json()
    print(f"\n返回数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # 验证version字段
    assert data['success'] == True, "API调用失败"
    assert data['data']['version'] == 'v1', f"预期version=v1, 实际={data['data']['version']}"

    # 验证regions中的version
    for region_type in ['keywords', 'instructions', 'background']:
        if region_type in data['data']['regions']:
            for region in data['data']['regions'][region_type]:
                assert region['version'] == 'v1', f"{region_type}中的region {region['id']} version不是v1: {region['version']}"

    print("\n✅ v1 Q1 ROI测试通过")
    return data

def test_roi_v2_q1():
    """测试v2 Q1的ROI配置"""
    print("\n========== 测试 v2 Q1 ROI ==========")
    url = f"{BASE_URL}/api/data/roi"
    params = {"version": "v2", "task": "q1"}

    response = requests.get(url, params=params)
    print(f"请求URL: {response.url}")
    print(f"状态码: {response.status_code}")

    data = response.json()
    print(f"\n返回数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # 验证version字段
    assert data['success'] == True, "API调用失败"
    assert data['data']['version'] == 'v2', f"预期version=v2, 实际={data['data']['version']}"

    # 验证regions中的version
    for region_type in ['keywords', 'instructions', 'background']:
        if region_type in data['data']['regions']:
            for region in data['data']['regions'][region_type]:
                assert region['version'] == 'v2', f"{region_type}中的region {region['id']} version不是v2: {region['version']}"

    print("\n✅ v2 Q1 ROI测试通过")
    return data

def test_roi_v2_q3():
    """测试v2 Q3的ROI配置"""
    print("\n========== 测试 v2 Q3 ROI ==========")
    url = f"{BASE_URL}/api/data/roi"
    params = {"version": "v2", "task": "q3"}

    response = requests.get(url, params=params)
    print(f"请求URL: {response.url}")
    print(f"状态码: {response.status_code}")

    data = response.json()
    print(f"\n返回数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # 验证version字段
    assert data['success'] == True, "API调用失败"
    assert data['data']['version'] == 'v2', f"预期version=v2, 实际={data['data']['version']}"

    # 验证regions中的version
    for region_type in ['keywords', 'instructions', 'background']:
        if region_type in data['data']['regions']:
            for region in data['data']['regions'][region_type]:
                assert region['version'] == 'v2', f"{region_type}中的region {region['id']} version不是v2: {region['version']}"

    print("\n✅ v2 Q3 ROI测试通过")
    return data

def test_roi_enhanced_v2_q1():
    """测试v2 Q1的增强版ROI配置"""
    print("\n========== 测试 v2 Q1 增强版ROI ==========")
    url = f"{BASE_URL}/api/data/roi-enhanced"
    params = {"version": "v2", "task": "q1"}

    response = requests.get(url, params=params)
    print(f"请求URL: {response.url}")
    print(f"状态码: {response.status_code}")

    data = response.json()
    print(f"\n返回数据摘要:")
    print(f"  success: {data.get('success')}")
    print(f"  version: {data.get('data', {}).get('version')}")
    print(f"  task: {data.get('data', {}).get('task')}")

    # 验证version字段
    assert data['success'] == True, "API调用失败"
    assert data['data']['version'] == 'v2', f"预期version=v2, 实际={data['data']['version']}"

    print("\n✅ v2 Q1 增强版ROI测试通过")
    return data

def compare_v1_v2_roi():
    """对比v1和v2的ROI配置是否不同"""
    print("\n========== 对比 v1 vs v2 ROI Q1 ==========")

    v1_data = test_roi_v1_q1()
    v2_data = test_roi_v2_q1()

    # 对比keywords数量
    v1_keywords = len(v1_data['data']['regions'].get('keywords', []))
    v2_keywords = len(v2_data['data']['regions'].get('keywords', []))

    print(f"\nv1 keywords数量: {v1_keywords}")
    print(f"v2 keywords数量: {v2_keywords}")

    # 对比第一个keyword的坐标
    if v1_keywords > 0 and v2_keywords > 0:
        v1_kw1 = v1_data['data']['regions']['keywords'][0]
        v2_kw1 = v2_data['data']['regions']['keywords'][0]

        print(f"\nv1 第一个keyword ID: {v1_kw1['id']}")
        print(f"v1 第一个keyword 坐标: {v1_kw1['normalized_coords']}")
        print(f"\nv2 第一个keyword ID: {v2_kw1['id']}")
        print(f"v2 第一个keyword 坐标: {v2_kw1['normalized_coords']}")

        # 如果坐标完全相同，可能有问题
        if v1_kw1['normalized_coords'] == v2_kw1['normalized_coords']:
            print("\n⚠️  警告: v1和v2的ROI坐标完全相同!")
        else:
            print("\n✅ v1和v2的ROI坐标不同，配置正确")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("ROI版本问题诊断测试")
        print("=" * 60)

        # 测试后端API
        test_roi_v1_q1()
        test_roi_v2_q1()
        test_roi_v2_q3()
        test_roi_enhanced_v2_q1()
        compare_v1_v2_roi()

        print("\n" + "=" * 60)
        print("✅ 所有后端测试通过")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务器 (http://127.0.0.1:9090)")
        print("请确保后端服务器正在运行")
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
