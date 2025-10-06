"""
Pipeline诊断脚本 - 找出失败原因
"""
import os
import sys

print("="*60)
print("Pipeline Diagnostic Tool")
print("="*60)

# 1. 检查数据路径
print("\n[1] Checking data paths...")

base_path = r"c:\Users\asino\Downloads\az - 副本 (11)"
os.chdir(base_path)

# 检查预处理数据路径
preprocessed_path = os.path.join(base_path, "data", "preprocessed_calibrated")
print(f"Preprocessed path: {preprocessed_path}")
print(f"Exists: {os.path.exists(preprocessed_path)}")

if os.path.exists(preprocessed_path):
    for group in ['control', 'mci', 'ad']:
        group_path = os.path.join(preprocessed_path, group)
        if os.path.exists(group_path):
            files = [f for f in os.listdir(group_path) if f.endswith('.csv')]
            print(f"  {group}: {len(files)} files")
        else:
            print(f"  {group}: PATH NOT FOUND")
else:
    print("  ERROR: Preprocessed data directory not found!")

# 2. 测试单个文件加载
print("\n[2] Testing single file load...")
try:
    test_file = os.path.join(preprocessed_path, "control", "n1q1_preprocessed_calibrated.csv")
    if os.path.exists(test_file):
        import pandas as pd
        df = pd.read_csv(test_file)
        print(f"  SUCCESS: Loaded {len(df)} rows")
        print(f"  Columns: {list(df.columns)[:5]}...")

        if 'GazePointX_normalized' in df.columns:
            print(f"  GazePointX_normalized: OK")
        else:
            print(f"  ERROR: Missing GazePointX_normalized column")
    else:
        print(f"  ERROR: Test file not found: {test_file}")
except Exception as e:
    print(f"  ERROR: {e}")

# 3. 测试GPU RQA核心
print("\n[3] Testing GPU RQA core...")
try:
    from analysis.rqa_analyzer_gpu import RQAAnalyzerGPU
    import numpy as np

    analyzer = RQAAnalyzerGPU()

    # 生成测试数据
    traj_x = np.random.randn(1000).astype(np.float32)
    traj_y = np.random.randn(1000).astype(np.float32)
    params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}

    result = analyzer.analyze_trajectory_gpu(traj_x, traj_y, params)

    if result['success']:
        print(f"  SUCCESS: GPU RQA working")
        print(f"  Time: {result['total_time']:.3f}s")
        print(f"  Memory: {result['gpu_memory']['used_gb']:.2f} GB")
    else:
        print(f"  ERROR: {result.get('error', 'Unknown')}")

except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试load_group_data_for_rqa函数
print("\n[4] Testing load_group_data_for_rqa...")
try:
    sys.path.insert(0, base_path)
    from visualization.rqa_pipeline_api import load_group_data_for_rqa

    group_data = load_group_data_for_rqa('control')
    print(f"  Loaded {len(group_data)} subjects")

    if len(group_data) > 0:
        first_subject = list(group_data.keys())[0]
        print(f"  First subject: {first_subject}")
        print(f"  Data keys: {list(group_data[first_subject].keys())}")
        print(f"  X points: {len(group_data[first_subject]['x'])}")
        print(f"  SUCCESS")
    else:
        print(f"  WARNING: No data loaded!")

except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试完整Pipeline函数
print("\n[5] Testing execute_full_pipeline_internal_gpu...")
try:
    from visualization.rqa_pipeline_api import execute_full_pipeline_internal_gpu

    test_params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}

    print(f"  Running with params: {test_params}")
    result = execute_full_pipeline_internal_gpu(test_params)

    print(f"  Success: {result.get('success', False)}")
    if not result.get('success'):
        print(f"  Error: {result.get('error', 'Unknown')}")
    else:
        print(f"  Param signature: {result.get('param_signature')}")

except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Diagnostic Complete")
print("="*60)
