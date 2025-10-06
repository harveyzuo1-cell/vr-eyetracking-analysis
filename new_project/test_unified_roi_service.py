"""
测试统一ROI服务
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.services.roi_service import get_unified_roi_service

def test_roi_service():
    print("=" * 60)
    print("测试统一ROI服务")
    print("=" * 60)

    service = get_unified_roi_service()

    # 测试1: Task ID映射
    print("\n[测试1] Task ID映射")
    test_ids = ['q1', 'task1', 'Q2', 'TASK3']
    for task_id in test_ids:
        legacy, new = service.normalize_task_id(task_id)
        print(f"  {task_id:10} -> legacy={legacy:5}, new={new:5}")

    # 测试2: 获取v1 ROI配置
    print("\n[测试2] 获取v1配置 (q1)")
    result = service.get_roi_config('v1', 'q1')
    if result['success']:
        data = result['data']
        print(f"  [OK] version: {data.get('version')}")
        print(f"  [OK] task_id: {data.get('task_id')}")
        print(f"  [OK] task_id_alt: {data.get('task_id_alt')}")
        regions = data.get('regions', {})
        print(f"  [OK] keywords: {len(regions.get('keywords', []))}")
        print(f"  [OK] instructions: {len(regions.get('instructions', []))}")
        print(f"  [OK] background: {len(regions.get('background', []))}")
    else:
        print(f"  [ERROR] {result['error']}")

    # 测试3: 获取v2 ROI配置
    print("\n[测试3] 获取v2配置 (q3)")
    result = service.get_roi_config('v2', 'q3')
    if result['success']:
        data = result['data']
        print(f"  [OK] version: {data.get('version')}")
        print(f"  [OK] task_id: {data.get('task_id')}")
        regions = data.get('regions', {})
        print(f"  [OK] keywords: {len(regions.get('keywords', []))}")
        print(f"  [OK] instructions: {len(regions.get('instructions', []))}")
        print(f"  [OK] background: {len(regions.get('background', []))}")
    else:
        print(f"  [ERROR] {result['error']}")

    # 测试4: 使用task ID访问v2
    print("\n[测试4] 使用task1访问v2配置")
    result = service.get_roi_config('v2', 'task1')
    if result['success']:
        data = result['data']
        print(f"  [OK] task_id: {data.get('task_id')}")
        print(f"  [OK] task_id_alt: {data.get('task_id_alt')}")
    else:
        print(f"  [ERROR] {result['error']}")

    # 测试5: Enhanced配置
    print("\n[测试5] 获取v1 Enhanced配置 (q1)")
    result = service.get_roi_config_enhanced('v1', 'q1')
    if result['success']:
        data = result['data']
        print(f"  [OK] task_name: {data.get('task_name')}")
        print(f"  [OK] background_image: {data.get('background_image')}")
    else:
        print(f"  [ERROR] {result['error']}")

    # 测试6: 列出可用任务
    print("\n[测试6] 列出可用任务")
    for version in ['v1', 'v2']:
        tasks = service.list_available_tasks(version)
        print(f"  {version}: {tasks}")

    # 测试7: 检查配置文件路径
    print("\n[测试7] 配置文件路径")
    test_cases = [
        ('v1', 'q1'),
        ('v2', 'q3'),
        ('v2', 'task1'),
    ]
    for version, task in test_cases:
        path = service.get_roi_config_path(version, task)
        if path:
            print(f"  {version}/{task:5} -> {path.name}")
        else:
            print(f"  {version}/{task:5} -> NOT FOUND")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_roi_service()
