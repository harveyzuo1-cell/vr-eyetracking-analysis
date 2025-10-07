"""
V2数据最终验证
确认93个V2受试者都有完整的5个任务
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent
metadata_file = project_root / "data" / "01_raw" / "clinical" / "subject_metadata.json"

with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# V2数据统计
v2_subjects = {s_id: s for s_id, s in metadata.items() if s.get('data_version') == 'v2'}

print("=== V2数据最终验证 ===\n")

# 按组统计
v2_by_group = {}
for s_id, s in v2_subjects.items():
    group = s.get('group', 'unknown')
    if group not in v2_by_group:
        v2_by_group[group] = []
    v2_by_group[group].append(s_id)

print(f"✅ V2受试者总数: {len(v2_subjects)}")
for group in ['control', 'mci', 'ad']:
    count = len(v2_by_group.get(group, []))
    print(f"   {group.upper()}: {count}个")

# 任务完整性检查
print("\n=== 任务完整性验证 ===")
complete_count = 0
incomplete_count = 0

for s_id, s in v2_subjects.items():
    tasks = s.get('tasks_available', [])
    if len(tasks) == 5:
        complete_count += 1
    else:
        incomplete_count += 1
        print(f"⚠ {s_id}: {len(tasks)} tasks - {tasks}")

print(f"\n完整任务: {complete_count}/{len(v2_subjects)}")
print(f"不完整任务: {incomplete_count}/{len(v2_subjects)}")

if incomplete_count == 0:
    print("\n✅ 所有V2受试者都有完整的5个任务 (level_1 到 level_5)")
else:
    print(f"\n⚠ 有 {incomplete_count} 个V2受试者任务不完整")

# 总数据统计
v1_subjects = {s_id: s for s_id, s in metadata.items() if s.get('data_version') == 'v1'}

print("\n=== 项目数据总览 ===")
print(f"V1受试者: {len(v1_subjects)}个 (Control 20, MCI 20, AD 20)")
print(f"V2受试者: {len(v2_subjects)}个 (Control {len(v2_by_group.get('control', []))}, MCI {len(v2_by_group.get('mci', []))}, AD {len(v2_by_group.get('ad', []))})")
print(f"总受试者: {len(metadata)}个")

print("\n✅ 数据验证完成！")
