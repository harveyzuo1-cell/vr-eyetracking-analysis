import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('new_project/data/01_raw/clinical/subject_metadata.json', encoding='utf-8') as f:
    data = json.load(f)

# 统计V1和V2数据
v1_subjects = {s_id: s for s_id, s in data.items() if s.get('data_version') == 'v1'}
v2_subjects = {s_id: s for s_id, s in data.items() if s.get('data_version') == 'v2'}

print("=== 最终验证结果 ===\n")

# V1数据统计
print(f"V1受试者总数: {len(v1_subjects)}")
v1_by_group = {}
for s_id, s in v1_subjects.items():
    group = s.get('group', 'unknown')
    if group not in v1_by_group:
        v1_by_group[group] = []
    v1_by_group[group].append(s_id)

for group in ['control', 'mci', 'ad']:
    subjects = sorted(v1_by_group.get(group, []))
    print(f"  {group.upper()}: {len(subjects)}个")
    # 检查任务数
    with_tasks = sum(1 for s_id in subjects if len(data[s_id].get('tasks_available', [])) > 0)
    print(f"    有任务: {with_tasks}/{len(subjects)}")

# V2数据统计
print(f"\nV2受试者总数: {len(v2_subjects)}")
v2_with_tasks = sum(1 for s in v2_subjects.values() if len(s.get('tasks_available', [])) > 0)
print(f"  有任务: {v2_with_tasks}/{len(v2_subjects)}")

# AD组详细映射
print("\n=== AD组映射关系 ===")
ad_v1 = sorted([s_id for s_id, s in v1_subjects.items() if s.get('group') == 'ad'])
for s_id in ad_v1[:5]:  # 只显示前5个
    s = data[s_id]
    source = s.get('source_path', 'N/A')
    tasks = len(s.get('tasks_available', []))
    print(f"{s_id}: {tasks} tasks (source: {source})")

print(f"... 共{len(ad_v1)}个AD受试者")

print("\n✅ 数据修复完成！")
print(f"总计: {len(data)} 个受试者 (V1: {len(v1_subjects)}, V2: {len(v2_subjects)})")
