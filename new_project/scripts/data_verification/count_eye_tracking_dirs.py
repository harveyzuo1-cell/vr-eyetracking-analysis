import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
et_dir = project_root / 'eye_tracking_data'

groups = {}
all_dirs = []

for d in et_dir.iterdir():
    if d.is_dir():
        parts = d.name.split('_')
        if len(parts) >= 2:
            group = parts[0]
            groups[group] = groups.get(group, 0) + 1
            all_dirs.append(d.name)

print('eye_tracking_data 原始目录统计:')
print(f'总目录数: {len(all_dirs)}')
for g in sorted(groups.keys()):
    print(f'  {g}: {groups[g]}个')

# 检查每个目录是否有完整的5个任务文件
print('\n检查任务文件完整性:')
incomplete_dirs = []

for d in et_dir.iterdir():
    if d.is_dir():
        task_files = list(d.glob('*.csv'))
        if len(task_files) != 5:
            incomplete_dirs.append({
                'dir': d.name,
                'task_count': len(task_files)
            })

if incomplete_dirs:
    print(f'发现 {len(incomplete_dirs)} 个任务不完整的目录:')
    for item in incomplete_dirs[:10]:
        print(f'  {item["dir"]}: {item["task_count"]} 个任务文件')
else:
    print('✓ 所有目录都有完整的5个任务文件')
