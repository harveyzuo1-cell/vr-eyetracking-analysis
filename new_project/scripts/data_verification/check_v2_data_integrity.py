"""
检查V2数据完整性
要求：84个受试者（Control 68, MCI 8, AD 8），每个都有5个完整任务
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# 设置工作目录为new_project
project_root = Path(__file__).parent

metadata_file = project_root / "data" / "01_raw" / "clinical" / "subject_metadata.json"

with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# 统计V2数据
v2_subjects = {s_id: s for s_id, s in metadata.items() if s.get('data_version') == 'v2'}

print("=== V2数据完整性检查 ===\n")

# 按组统计
v2_by_group = {}
for s_id, s in v2_subjects.items():
    group = s.get('group', 'unknown')
    if group not in v2_by_group:
        v2_by_group[group] = []
    v2_by_group[group].append(s_id)

print(f"V2受试者总数: {len(v2_subjects)}")
for group in ['control', 'mci', 'ad']:
    count = len(v2_by_group.get(group, []))
    print(f"  {group.upper()}: {count}")

# 检查任务完整性
print("\n=== 任务完整性检查 ===")
incomplete_subjects = []

for s_id, s in v2_subjects.items():
    tasks = s.get('tasks_available', [])
    if len(tasks) != 5:
        incomplete_subjects.append({
            'subject_id': s_id,
            'group': s.get('group'),
            'tasks': tasks,
            'task_count': len(tasks)
        })

if incomplete_subjects:
    print(f"\n⚠ 发现 {len(incomplete_subjects)} 个任务不完整的受试者：")
    for subj in incomplete_subjects[:10]:  # 只显示前10个
        print(f"  {subj['subject_id']} ({subj['group']}): {subj['task_count']} tasks - {subj['tasks']}")

    if len(incomplete_subjects) > 10:
        print(f"  ... 还有 {len(incomplete_subjects) - 10} 个")
else:
    print("✓ 所有V2受试者都有完整的5个任务")

# 期望的V2数据分布
expected = {
    'control': 68,
    'mci': 8,
    'ad': 8,
    'total': 84
}

print("\n=== 与预期对比 ===")
actual_total = len(v2_subjects)
print(f"预期总数: {expected['total']}, 实际总数: {actual_total}")

for group in ['control', 'mci', 'ad']:
    actual = len(v2_by_group.get(group, []))
    exp = expected[group]
    status = "✓" if actual == exp else "✗"
    print(f"  {status} {group.upper()}: 预期 {exp}, 实际 {actual}")

# 如果数量不符，需要过滤掉任务不完整的受试者
if actual_total != expected['total']:
    print(f"\n⚠ V2受试者总数不符合预期（{actual_total} != {expected['total']}）")

    # 检查是否是因为任务不完整导致的
    complete_v2 = {s_id: s for s_id, s in v2_subjects.items()
                   if len(s.get('tasks_available', [])) == 5}

    print(f"\n有完整任务的V2受试者数量: {len(complete_v2)}")

    if len(complete_v2) == expected['total']:
        print("✓ 移除任务不完整的受试者后，数量符合预期")
        print("\n建议操作：删除以下任务不完整的V2受试者：")
        for subj in incomplete_subjects:
            print(f"  - {subj['subject_id']}")
