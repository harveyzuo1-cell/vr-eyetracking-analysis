import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('new_project/data/01_raw/clinical/subject_metadata.json', encoding='utf-8') as f:
    data = json.load(f)

v1_subjects = [s for s_id, s in data.items() if s.get('data_version') == 'v1']
v1_with_tasks = [s for s in v1_subjects if s.get('tasks_available') and len(s['tasks_available']) > 0]
v2_subjects = [s_id for s_id, s in data.items() if s.get('data_version') == 'v2']
v2_with_tasks = [s_id for s_id in v2_subjects if data[s_id].get('tasks_available') and len(data[s_id]['tasks_available']) > 0]

print(f'V1受试者总数: {len(v1_subjects)}')
print(f'V1有任务的受试者: {len(v1_with_tasks)}')
print(f'V2受试者总数: {len(v2_subjects)}')
print(f'V2有任务的受试者: {len(v2_with_tasks)}')
print()

ad_v1 = [s['subject_id'] for s in v1_subjects if s['group'] == 'ad']
print(f'AD组V1受试者: {len(ad_v1)}')
for s_id in sorted(ad_v1)[:5]:
    s = data[s_id]
    print(f'  {s_id}: {len(s.get("tasks_available", []))} tasks - {s.get("tasks_available", [])}')
