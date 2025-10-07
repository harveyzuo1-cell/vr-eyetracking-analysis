"""
删除V2受试者中的重复记录

问题：同一个timestamp被导入了2次，导致metadata中有重复的V2受试者
解决：保留每个timestamp的第一条记录，删除后续重复的
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

def remove_v2_duplicates(project_root: Path, dry_run: bool = True):
    """
    删除V2受试者中的重复记录

    Args:
        project_root: 项目根目录
        dry_run: 是否试运行（不实际修改）
    """
    print("=" * 80)
    print("V2受试者重复记录删除工具")
    print("=" * 80)

    metadata_file = project_root / 'data' / '01_raw' / 'clinical' / 'subject_metadata.json'

    if not metadata_file.exists():
        raise FileNotFoundError(f"subject_metadata.json not found: {metadata_file}")

    # 读取metadata
    print("\n[1/3] 读取subject_metadata.json...")
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata_all = json.load(f)

    v2_subjects = {sid: data for sid, data in metadata_all.items()
                   if data.get('data_version') == 'v2'}

    print(f"  - metadata中V2受试者总数: {len(v2_subjects)}")

    # 按timestamp分组
    print("\n[2/3] 检测重复记录...")
    timestamp_groups = defaultdict(list)

    for subject_id, subject_data in v2_subjects.items():
        ts = subject_data.get('metadata', {}).get('timestamp', '')
        if ts:
            timestamp_groups[ts].append({
                'subject_id': subject_id,
                'created_at': subject_data.get('created_at', ''),
                'data': subject_data
            })

    # 找出重复的timestamp
    duplicates = {ts: subjects for ts, subjects in timestamp_groups.items()
                  if len(subjects) > 1}

    unique_timestamps = len(timestamp_groups)
    duplicate_count = len(duplicates)
    duplicate_records = sum(len(subjects) - 1 for subjects in duplicates.values())

    print(f"  - 不同timestamp数: {unique_timestamps}")
    print(f"  - 重复的timestamp数: {duplicate_count}")
    print(f"  - 需要删除的重复记录数: {duplicate_records}")

    if duplicates:
        print(f"\n  重复的timestamp详情:")
        to_delete = []

        for ts, subjects in sorted(duplicates.items()):
            print(f"\n    Timestamp: {ts}")

            # 按created_at排序，保留最早的
            subjects_sorted = sorted(subjects, key=lambda x: x['created_at'])

            for idx, subj in enumerate(subjects_sorted):
                sid = subj['subject_id']
                created = subj['created_at']
                orig_id = subj['data'].get('metadata', {}).get('original_id', '')

                if idx == 0:
                    print(f"      [KEEP] {sid} (created: {created}, original_id: {orig_id})")
                else:
                    print(f"      [DELETE] {sid} (created: {created}, original_id: {orig_id})")
                    to_delete.append(sid)

        # 执行删除
        print(f"\n[3/3] {'[试运行] ' if dry_run else ''}删除重复记录...")

        if not dry_run and to_delete:
            # 备份
            backup_file = metadata_file.with_suffix('.json.backup_before_dedup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_all, f, ensure_ascii=False, indent=2)
            print(f"  已备份至: {backup_file}")

            # 删除重复记录
            for sid in to_delete:
                del metadata_all[sid]

            # 保存
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_all, f, ensure_ascii=False, indent=2)

            print(f"\n[SUCCESS] 删除完成! 删除了 {len(to_delete)} 条重复记录")

            # 最终统计
            v2_final = {sid: data for sid, data in metadata_all.items()
                       if data.get('data_version') == 'v2'}

            print(f"\n最终统计:")
            print(f"  V2受试者总数: {len(v2_final)}")
            print(f"  不同timestamp数: {len(set(s.get('metadata', {}).get('timestamp') for s in v2_final.values()))}")

        elif dry_run:
            print(f"\n[试运行完成] 将删除 {len(to_delete)} 条重复记录")
            print(f"运行命令 'python {Path(__file__).name} --execute' 以实际执行删除")

    else:
        print("\n[OK] 未发现重复记录，无需删除")

if __name__ == '__main__':
    import sys

    project_root = Path(__file__).parent.parent.parent

    # 默认试运行
    dry_run = '--execute' not in sys.argv

    if dry_run:
        print("试运行模式 (添加 --execute 参数以实际执行删除)\n")

    try:
        remove_v2_duplicates(project_root, dry_run=dry_run)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
