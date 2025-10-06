"""
生成测试用眼动数据 - 用于GPU Pipeline测试
基于60个受试者的模拟数据
"""

import os
import numpy as np
import pandas as pd

# 项目根目录
BASE_DIR = r"c:\Users\asino\Downloads\az - 副本 (11)"
DATA_DIR = os.path.join(BASE_DIR, "data")

# 输出目录
OUTPUT_DIRS = {
    'control': os.path.join(DATA_DIR, 'control_calibrated'),
    'mci': os.path.join(DATA_DIR, 'mci_calibrated'),
    'ad': os.path.join(DATA_DIR, 'ad_calibrated')
}

# 确保目录存在
for d in OUTPUT_DIRS.values():
    os.makedirs(d, exist_ok=True)

def generate_eyetracking_trajectory(n_points=5000, difficulty=0.5):
    """
    生成模拟的眼动轨迹数据

    Args:
        n_points: 数据点数量
        difficulty: 难度系数 (0=简单，1=困难)
            - Control: 0.2-0.4 (轨迹平滑，注视稳定)
            - MCI: 0.4-0.6 (中等噪声)
            - AD: 0.6-0.8 (高噪声，不稳定)

    Returns:
        DataFrame with columns: GazePointX_normalized, GazePointY_normalized
    """
    t = np.linspace(0, 10*np.pi, n_points)

    # 基础轨迹 (螺旋+漂移)
    base_x = 0.5 + 0.3 * np.cos(t) * (1 - t/(10*np.pi))
    base_y = 0.5 + 0.3 * np.sin(t) * (1 - t/(10*np.pi))

    # 根据难度添加噪声
    noise_scale = difficulty * 0.15
    noise_x = np.random.randn(n_points) * noise_scale
    noise_y = np.random.randn(n_points) * noise_scale

    # 添加微颤抖 (高频噪声)
    tremor_scale = difficulty * 0.05
    tremor_x = np.random.randn(n_points) * tremor_scale
    tremor_y = np.random.randn(n_points) * tremor_scale

    # 合成最终轨迹
    x = np.clip(base_x + noise_x + tremor_x, 0, 1)
    y = np.clip(base_y + noise_y + tremor_y, 0, 1)

    return pd.DataFrame({
        'GazePointX_normalized': x,
        'GazePointY_normalized': y
    })

# 生成数据配置
GROUP_CONFIG = {
    'control': {
        'prefix': 'n',
        'count': 20,
        'difficulty_range': (0.2, 0.4)
    },
    'mci': {
        'prefix': 'm',
        'count': 20,
        'difficulty_range': (0.4, 0.6)
    },
    'ad': {
        'prefix': 'ad',
        'count': 20,
        'difficulty_range': (0.6, 0.8)
    }
}

# Q任务配置 (不同任务有不同难度)
TASK_DIFFICULTY_MULTIPLIERS = {
    1: 0.8,  # Q1最简单
    2: 0.9,
    3: 1.0,  # Q3中等
    4: 1.1,
    5: 1.2   # Q5最难
}

print("="*60)
print("生成测试眼动数据 - 60个受试者 × 5个任务 = 300个文件")
print("="*60)

total_files = 0

for group_name, config in GROUP_CONFIG.items():
    prefix = config['prefix']
    count = config['count']
    diff_min, diff_max = config['difficulty_range']

    print(f"\n处理 {group_name.upper()} 组 (prefix={prefix}, count={count}):")

    for subject_num in range(1, count + 1):
        # 每个受试者有固定的基础难度
        base_difficulty = diff_min + (diff_max - diff_min) * (subject_num / count)

        for q_num in range(1, 6):  # Q1-Q5
            # 任务难度 = 基础难度 × 任务系数
            task_difficulty = base_difficulty * TASK_DIFFICULTY_MULTIPLIERS[q_num]
            task_difficulty = np.clip(task_difficulty, 0, 1)

            # 生成轨迹
            df = generate_eyetracking_trajectory(n_points=5000, difficulty=task_difficulty)

            # 文件名格式: n1q1_preprocessed_calibrated.csv
            filename = f"{prefix}{subject_num}q{q_num}_preprocessed_calibrated.csv"
            filepath = os.path.join(OUTPUT_DIRS[group_name], filename)

            # 保存
            df.to_csv(filepath, index=False)
            total_files += 1

            if subject_num <= 2:  # 只显示前2个受试者的日志
                print(f"  OK {filename} (difficulty={task_difficulty:.2f}, points={len(df)})")

print(f"\n{'='*60}")
print(f"[OK] Complete! Generated {total_files} files")
print(f"{'='*60}")

# 验证数据
print("\n数据验证:")
for group_name, output_dir in OUTPUT_DIRS.items():
    files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    print(f"  {group_name}: {len(files)} 个文件")

    if files:
        # 读取一个样本
        sample_file = os.path.join(output_dir, files[0])
        df = pd.read_csv(sample_file)
        print(f"    示例: {files[0]}")
        print(f"    列: {list(df.columns)}")
        print(f"    数据点: {len(df)}")
        print(f"    X范围: [{df['GazePointX_normalized'].min():.3f}, {df['GazePointX_normalized'].max():.3f}]")
        print(f"    Y范围: [{df['GazePointY_normalized'].min():.3f}, {df['GazePointY_normalized'].max():.3f}]")

print("\n[OK] All test data generated! Ready for GPU pipeline testing.")
