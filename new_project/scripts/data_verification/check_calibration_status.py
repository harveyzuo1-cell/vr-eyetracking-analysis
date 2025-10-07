"""检查校正数据完成状态"""
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
calibrated_dir = project_root / 'data' / '03_calibrated'
metadata_file = project_root / 'data' / '01_raw' / 'clinical' / 'subject_metadata.json'

# 读取metadata
with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# 检查03_calibrated目录结构
print("=== 03_calibrated目录结构 ===")
if calibrated_dir.exists():
    groups = [d.name for d in calibrated_dir.iterdir() if d.is_dir()]
    print(f"Groups: {groups}")

    for group in sorted(groups)[:1]:  # 只看第一个组
        group_dir = calibrated_dir / group
        files = list(group_dir.glob('*.csv'))
        print(f"\n{group}组 示例文件 (前5个):")
        for f in files[:5]:
            print(f"  {f.name}")
else:
    print("目录不存在")

# 检查V1和V2受试者的任务
print("\n\n=== 受试者任务统计 ===")
v1_subjects = {sid: data for sid, data in metadata.items() if data.get('data_version') == 'v1'}
v2_subjects = {sid: data for sid, data in metadata.items() if data.get('data_version') == 'v2'}

print(f"V1受试者: {len(v1_subjects)} 个")
print(f"V2受试者: {len(v2_subjects)} 个")

# V1任务命名
print("\nV1任务示例:")
if v1_subjects:
    sample_v1 = list(v1_subjects.values())[0]
    print(f"  tasks_available: {sample_v1.get('tasks_available', [])}")

# V2任务命名
print("\nV2任务示例:")
if v2_subjects:
    sample_v2 = list(v2_subjects.values())[0]
    print(f"  tasks_available: {sample_v2.get('tasks_available', [])}")
