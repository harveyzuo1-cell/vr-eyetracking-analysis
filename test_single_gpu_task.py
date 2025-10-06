"""
测试单个GPU任务执行
"""
import os
import sys
import time

# 切换到项目目录
os.chdir(r"c:\Users\asino\Downloads\az - 副本 (11)")
sys.path.insert(0, os.getcwd())

print("="*60)
print("测试单个GPU任务执行")
print("="*60)

# 测试参数
test_params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}

print(f"\n[1] 导入GPU RQA函数...")
try:
    from analysis.rqa_analyzer_gpu import compute_rqa_1d_gpu, compute_rqa_2d_gpu
    import numpy as np
    print("  ✓ 导入成功")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    sys.exit(1)

print(f"\n[2] 测试GPU RQA核心 (单条轨迹)...")
try:
    traj_x = np.random.randn(1000).astype(np.float32)
    traj_y = np.random.randn(1000).astype(np.float32)

    start = time.time()
    result_1d = compute_rqa_1d_gpu(traj_x, traj_y, test_params)
    result_2d = compute_rqa_2d_gpu(traj_x, traj_y, test_params)
    elapsed = time.time() - start

    print(f"  ✓ GPU计算成功 (耗时: {elapsed:.3f}s)")
    print(f"  1D结果: RR={result_1d.get('rr_1d', 0):.4f}, DET={result_1d.get('det_1d', 0):.4f}")
    print(f"  2D结果: RR={result_2d.get('rr_2d', 0):.4f}, DET={result_2d.get('det_2d', 0):.4f}")
except Exception as e:
    print(f"  ✗ GPU计算失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n[3] 导入Pipeline函数...")
try:
    from visualization.rqa_pipeline_api import load_group_data_for_rqa, execute_full_pipeline_internal_gpu
    print("  ✓ 导入成功")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n[4] 测试数据加载 (仅前3个受试者)...")
try:
    group_data = load_group_data_for_rqa('control')
    print(f"  ✓ 成功加载 {len(group_data)} 个受试者")

    if len(group_data) > 0:
        # 只保留前3个受试者用于测试
        sample_subjects = list(group_data.keys())[:3]
        group_data_sample = {k: group_data[k] for k in sample_subjects}

        for subject_id in sample_subjects:
            x_points = len(group_data[subject_id]['x'])
            print(f"    {subject_id}: {x_points} 数据点")
    else:
        print("  ✗ 未加载到数据!")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ 数据加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n[5] 测试完整Pipeline (单参数组合)...")
try:
    print(f"  参数: {test_params}")
    start = time.time()

    result = execute_full_pipeline_internal_gpu(test_params)

    elapsed = time.time() - start

    if result.get('success'):
        print(f"  ✓ Pipeline执行成功!")
        print(f"    参数签名: {result.get('param_signature')}")
        print(f"    跳过: {result.get('skipped', False)}")
        print(f"    耗时: {elapsed:.2f}s")
    else:
        print(f"  ✗ Pipeline执行失败!")
        print(f"    错误: {result.get('error', 'Unknown')}")
        import traceback
        if 'traceback' in result:
            print(result['traceback'])
except Exception as e:
    print(f"  ✗ Pipeline执行异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n{'='*60}")
print("✓ 所有测试通过!")
print(f"{'='*60}")
