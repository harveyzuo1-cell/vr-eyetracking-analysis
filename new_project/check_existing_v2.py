import json
from pathlib import Path

subject_dir = Path('data/subject_info')

print("=== 已存在的V2受试者 ===\n")

for group in ['control', 'mci', 'ad']:
    group_path = subject_dir / group
    if not group_path.exists():
        continue

    v2_subjects = []
    for json_file in group_path.glob('*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data.get('data_version') == 'v2':
                v2_subjects.append({
                    'subject_id': data['subject_id'],
                    'original_id': data.get('metadata', {}).get('original_id'),
                    'timestamp': data.get('metadata', {}).get('timestamp')
                })

    if v2_subjects:
        print(f"{group.upper()} ({len(v2_subjects)}个):")
        for s in v2_subjects:
            print(f"  {s['subject_id']} <- {s['original_id']}||{s['timestamp']}")
        print()
