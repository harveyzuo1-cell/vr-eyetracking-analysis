import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('new_project/data/01_raw/clinical/subject_metadata.json', encoding='utf-8') as f:
    data = json.load(f)

ad_v1 = sorted([s_id for s_id, s in data.items() if s.get('data_version')=='v1' and s.get('group')=='ad'])

print(f'当前AD组V1受试者数量: {len(ad_v1)}')
print('\n受试者ID列表:')
for s_id in ad_v1:
    source_path = data[s_id].get('source_path', '')
    print(f'  {s_id} <- {source_path}')
