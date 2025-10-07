"""
严格验证实际导入的数据数量
检查CSV文件和metadata的一致性
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent.parent

# 1. 检查metadata中的数据
print("=== 1. 检查subject_metadata.json ===")
metadata_file = project_root / "data" / "01_raw" / "clinical" / "subject_metadata.json"

with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

v1_subjects = {}
v2_subjects = {}

for subject_id, meta in metadata.items():
    version = meta.get('data_version')
    group = meta.get('group')
    tasks = meta.get('tasks_available', [])

    if version == 'v1':
        v1_subjects[subject_id] = {
            'group': group,
            'tasks': tasks,
            'task_count': len(tasks)
        }
    elif version == 'v2':
        v2_subjects[subject_id] = {
            'group': group,
            'tasks': tasks,
            'task_count': len(tasks)
        }

print(f"V1受试者数量: {len(v1_subjects)}")
print(f"V2受试者数量: {len(v2_subjects)}")

# 2. 检查V1 CSV文件
print("\n=== 2. 检查V1 CSV文件 (q1-q5) ===")
v1_csv_dir = project_root / "data" / "01_raw"

v1_csv_subjects = defaultdict(set)

for group in ['control', 'mci', 'ad']:
    group_dir = v1_csv_dir / group
    if group_dir.exists():
        for csv_file in group_dir.glob("*_q*.csv"):
            # 解析文件名：subject_id_task.csv
            parts = csv_file.stem.split('_')
            if len(parts) >= 2 and parts[-1].startswith('q'):
                task = parts[-1]  # q1, q2, q3, q4, q5
                subject_id = '_'.join(parts[:-1])  # 去掉最后的任务部分

                # 只统计q1-q5的文件
                if task in ['q1', 'q2', 'q3', 'q4', 'q5']:
                    v1_csv_subjects[subject_id].add(task)

# 统计有完整5个任务的V1受试者
v1_complete = {sid: tasks for sid, tasks in v1_csv_subjects.items() if len(tasks) == 5}

print(f"V1 CSV文件中的受试者数: {len(v1_csv_subjects)}")
print(f"V1 有完整5个任务的受试者: {len(v1_complete)}")

# 按组统计
v1_by_group = defaultdict(int)
for sid in v1_complete.keys():
    if sid in v1_subjects:
        group = v1_subjects[sid]['group']
        v1_by_group[group] += 1

print("V1按组统计（CSV完整）:")
for group in sorted(v1_by_group.keys()):
    print(f"  {group}: {v1_by_group[group]}")

# 3. 检查V2 CSV文件
print("\n=== 3. 检查V2 CSV文件 (level_1-5) ===")

v2_csv_subjects = defaultdict(set)

for group in ['control', 'mci', 'ad']:
    group_dir = v1_csv_dir / group
    if group_dir.exists():
        for csv_file in group_dir.glob("v2_*_level_*.csv"):
            # 解析文件名：v2_group_id_level_N.csv
            parts = csv_file.stem.split('_')
            if len(parts) >= 4 and parts[-2] == 'level':
                level = f"level_{parts[-1]}"  # level_1, level_2, etc.
                subject_id = '_'.join(parts[:-2])  # v2_group_id

                # 只统计level_1-5的文件
                if level in ['level_1', 'level_2', 'level_3', 'level_4', 'level_5']:
                    v2_csv_subjects[subject_id].add(level)

# 统计有完整5个任务的V2受试者
v2_complete = {sid: tasks for sid, tasks in v2_csv_subjects.items() if len(tasks) == 5}

print(f"V2 CSV文件中的受试者数: {len(v2_csv_subjects)}")
print(f"V2 有完整5个任务的受试者: {len(v2_complete)}")

# 按组统计
v2_by_group = defaultdict(int)
for sid in v2_complete.keys():
    if sid in v2_subjects:
        group = v2_subjects[sid]['group']
        v2_by_group[group] += 1

print("V2按组统计（CSV完整）:")
for group in sorted(v2_by_group.keys()):
    print(f"  {group}: {v2_by_group[group]}")

# 4. 对比metadata和CSV文件
print("\n=== 4. metadata vs CSV文件对比 ===")

print("\nV1对比:")
print(f"  metadata中: {len(v1_subjects)}")
print(f"  CSV文件中（完整）: {len(v1_complete)}")

v1_only_meta = set(v1_subjects.keys()) - set(v1_complete.keys())
v1_only_csv = set(v1_complete.keys()) - set(v1_subjects.keys())

if v1_only_meta:
    print(f"  只在metadata中: {len(v1_only_meta)} 个")
    for sid in list(v1_only_meta)[:3]:
        print(f"    - {sid}")
if v1_only_csv:
    print(f"  只在CSV中: {len(v1_only_csv)} 个")
    for sid in list(v1_only_csv)[:3]:
        print(f"    - {sid}")

print("\nV2对比:")
print(f"  metadata中: {len(v2_subjects)}")
print(f"  CSV文件中（完整）: {len(v2_complete)}")

v2_only_meta = set(v2_subjects.keys()) - set(v2_complete.keys())
v2_only_csv = set(v2_complete.keys()) - set(v2_subjects.keys())

if v2_only_meta:
    print(f"  只在metadata中: {len(v2_only_meta)} 个")
    for sid in list(v2_only_meta)[:3]:
        print(f"    - {sid}")
if v2_only_csv:
    print(f"  只在CSV中: {len(v2_only_csv)} 个")
    for sid in list(v2_only_csv)[:3]:
        print(f"    - {sid}")

# 5. 最终结论
print("\n=== 5. 最终结论 ===")
print(f"✓ V1实际有效数据: {len(v1_complete)} 个（有完整q1-q5 CSV文件）")
print(f"✓ V2实际有效数据: {len(v2_complete)} 个（有完整level_1-5 CSV文件）")
print(f"✓ 总计: {len(v1_complete) + len(v2_complete)} 个")
