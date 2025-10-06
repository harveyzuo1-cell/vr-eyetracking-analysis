"""
GPU批处理API测试脚本

测试配置:
- 小规模: 2x1x2x1 = 4个组合 (~15秒)
- 中规模: 3x2x3x1 = 18个组合 (~60秒)
- 大规模: 5x5x6x2 = 300个组合 (~15分钟)
"""

import requests
import json
import time

# 服务器地址
BASE_URL = "http://127.0.0.1:8080"

def test_small_batch():
    """小规模测试 (4个组合)"""
    print("="*60)
    print("Small Batch Test (4 combinations)")
    print("="*60)

    batch_config = {
        "m_range": {"start": 2, "end": 3, "step": 1},  # 2个值: 2, 3
        "tau_range": {"start": 1, "end": 1, "step": 1},  # 1个值: 1
        "eps_range": {"start": 0.05, "end": 0.06, "step": 0.01},  # 2个值: 0.05, 0.06
        "lmin_range": {"start": 2, "end": 2, "step": 1}  # 1个值: 2
    }

    payload = {
        "batch_config": batch_config,
        "n_workers": 2
    }

    print(f"\nSending request to {BASE_URL}/api/rqa-pipeline/batch-execute-gpu")
    print(f"Configuration: {json.dumps(batch_config, indent=2)}")
    print(f"Total combinations: 2 x 1 x 2 x 1 = 4")
    print(f"Workers: 2")
    print(f"Estimated time: ~15 seconds\n")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/api/rqa-pipeline/batch-execute-gpu",
            json=payload,
            timeout=300  # 5分钟超时
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"\n{'='*60}")
            print(f"SUCCESS")
            print(f"{'='*60}")
            print(f"Elapsed time: {elapsed:.1f}s")
            print(f"\nStats:")
            print(json.dumps(result.get('stats', {}), indent=2))

            return True
        else:
            print(f"\n{'='*60}")
            print(f"FAILED - HTTP {response.status_code}")
            print(f"{'='*60}")
            print(f"Response: {response.text}")
            return False

    except requests.Timeout:
        print(f"\n{'='*60}")
        print(f"TIMEOUT after {time.time() - start_time:.1f}s")
        print(f"{'='*60}")
        return False
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR: {e}")
        print(f"{'='*60}")
        return False


def test_medium_batch():
    """中规模测试 (18个组合)"""
    print("\n\n")
    print("="*60)
    print("Medium Batch Test (18 combinations)")
    print("="*60)

    batch_config = {
        "m_range": {"start": 2, "end": 4, "step": 1},  # 3个值
        "tau_range": {"start": 1, "end": 2, "step": 1},  # 2个值
        "eps_range": {"start": 0.05, "end": 0.07, "step": 0.01},  # 3个值
        "lmin_range": {"start": 2, "end": 2, "step": 1}  # 1个值
    }

    payload = {
        "batch_config": batch_config,
        "n_workers": 4
    }

    print(f"\nConfiguration: {json.dumps(batch_config, indent=2)}")
    print(f"Total combinations: 3 x 2 x 3 x 1 = 18")
    print(f"Workers: 4")
    print(f"Estimated time: ~60 seconds\n")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/api/rqa-pipeline/batch-execute-gpu",
            json=payload,
            timeout=600  # 10分钟超时
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"\n{'='*60}")
            print(f"SUCCESS")
            print(f"{'='*60}")
            print(f"Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
            print(f"Average per task: {elapsed/18:.1f}s")
            print(f"\nStats:")
            print(json.dumps(result.get('stats', {}), indent=2))

            return True
        else:
            print(f"\n{'='*60}")
            print(f"FAILED - HTTP {response.status_code}")
            print(f"{'='*60}")
            return False

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR: {e}")
        print(f"{'='*60}")
        return False


def monitor_gpu():
    """启动GPU监控 (需要在另一个终端运行)"""
    print("\n" + "="*60)
    print("GPU Monitoring Command")
    print("="*60)
    print("Run this in another terminal:")
    print("  nvidia-smi dmon -s u -d 1")
    print("="*60 + "\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("GPU Batch Processing API Test Suite")
    print("="*60)

    # 显示GPU监控命令
    monitor_gpu()

    # 等待用户确认
    input("Press Enter to start small batch test (4 combinations)...")

    # 小规模测试
    success_small = test_small_batch()

    if success_small:
        choice = input("\nSmall test passed! Run medium test (18 combinations)? [y/N]: ")
        if choice.lower() == 'y':
            success_medium = test_medium_batch()

            if success_medium:
                print("\n" + "="*60)
                print("All tests PASSED!")
                print("="*60)
        else:
            print("\nMedium test skipped.")
    else:
        print("\nSmall test failed, skipping medium test.")

    print("\nTest complete.")
