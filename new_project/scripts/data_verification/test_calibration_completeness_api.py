"""测试校正完成度API"""
import requests
import json

BASE_URL = "http://localhost:9090"

def test_completeness_api(version='all'):
    """测试校正完成度API"""
    url = f"{BASE_URL}/api/module01/calibration/completeness"
    params = {'version': version}

    print(f"\n=== 测试校正完成度API (version={version}) ===")
    print(f"URL: {url}")
    print(f"Params: {params}")

    try:
        response = requests.get(url, params=params, timeout=10)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data['success']:
                result = data['data']
                summary = result['summary']

                print(f"\n总结:")
                print(f"  数据版本: {summary['data_version']}")
                print(f"  总受试者: {summary['total_subjects']}")
                print(f"  总任务数: {summary['total_tasks']}")
                print(f"  已校正: {summary['calibrated_tasks']}")
                print(f"  未校正: {summary['missing_tasks']}")
                print(f"  完成率: {summary['completion_rate']}%")

                print(f"\n分组统计:")
                for group, stats in result['by_group'].items():
                    print(f"  {group}:")
                    print(f"    受试者: {stats['subjects']}")
                    print(f"    任务数: {stats['total_tasks']}")
                    print(f"    已校正: {stats['calibrated']}")
                    print(f"    未校正: {stats['missing']}")
                    print(f"    完成率: {stats['completion_rate']:.2f}%")

                # 显示缺失详情(前10个)
                missing_details = result['missing_details']
                if missing_details:
                    print(f"\n缺失任务详情 (显示前10个，共{len(missing_details)}个):")
                    for item in missing_details[:10]:
                        print(f"  {item['subject_id']} ({item['group']}, {item['data_version']})")
                        print(f"    缺失: {item['missing_tasks']}")
                else:
                    print(f"\n✓ 所有任务都已校正!")
            else:
                print(f"请求失败: {data.get('message', 'Unknown error')}")
        else:
            print(f"HTTP错误: {response.text}")

    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请确保后端服务正在运行。")
        print("运行命令: python run.py")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    import sys

    # 测试所有版本
    test_completeness_api('all')

    # 测试V1
    test_completeness_api('v1')

    # 测试V2
    test_completeness_api('v2')
