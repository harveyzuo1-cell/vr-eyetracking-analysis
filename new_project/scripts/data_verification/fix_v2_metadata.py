"""
修复V2受试者metadata中的错误标记

问题：metadata中93个V2受试者都被标记为有5个完整任务，
但实际原始文件中只有84个有完整的level_1~5.txt文件
"""

import json
from pathlib import Path
from typing import Dict, List

def verify_v2_file_completeness(eye_tracking_data_dir: Path) -> Dict[str, Dict]:
    """
    验证eye_tracking_data中每个时间戳目录的文件完整性

    Returns:
        {timestamp: {'complete': bool, 'missing_files': [], 'metadata': {}}}
    """
    data_index_file = eye_tracking_data_dir / 'data_index.json'

    if not data_index_file.exists():
        raise FileNotFoundError(f"data_index.json not found: {data_index_file}")

    with open(data_index_file, 'r', encoding='utf-8') as f:
        data_index = json.load(f)

    results = {}

    for timestamp, metadata in data_index.items():
        timestamp_dir = eye_tracking_data_dir / timestamp

        if not timestamp_dir.exists():
            results[timestamp] = {
                'complete': False,
                'missing_files': ['directory_not_found'],
                'metadata': metadata
            }
            continue

        # 检查level_1.txt ~ level_5.txt
        required_files = [f'level_{i}.txt' for i in range(1, 6)]
        missing = [f for f in required_files if not (timestamp_dir / f).exists()]

        results[timestamp] = {
            'complete': len(missing) == 0,
            'missing_files': missing,
            'metadata': metadata
        }

    return results

def find_v2_subject_by_timestamp(metadata_all: Dict, timestamp: str, hospital_id: str) -> str:
    """
    通过timestamp和hospital_id找到对应的subject_id
    """
    for subject_id, subject_data in metadata_all.items():
        if subject_data.get('data_version') != 'v2':
            continue

        meta = subject_data.get('metadata', {})
        if meta.get('timestamp') == timestamp:
            # 优先匹配hospital_id
            if meta.get('original_id', '').endswith(hospital_id):
                return subject_id
            # 如果hospital_id是空的，可能匹配的是第一个
            if not hospital_id or hospital_id == 'None':
                return subject_id

    return None

def fix_v2_metadata(project_root: Path, dry_run: bool = True):
    """
    修复V2受试者metadata

    Args:
        project_root: 项目根目录
        dry_run: 是否试运行（不实际修改）
    """
    print("=" * 80)
    print("V2受试者Metadata修复工具")
    print("=" * 80)

    # 路径
    eye_tracking_data_dir = project_root.parent / 'eye_tracking_data'
    metadata_file = project_root / 'data' / '01_raw' / 'clinical' / 'subject_metadata.json'

    if not metadata_file.exists():
        raise FileNotFoundError(f"subject_metadata.json not found: {metadata_file}")

    # 1. 验证原始文件完整性
    print("\n[1/4] 验证eye_tracking_data中的文件完整性...")
    file_status = verify_v2_file_completeness(eye_tracking_data_dir)

    complete_count = sum(1 for s in file_status.values() if s['complete'])
    incomplete_count = len(file_status) - complete_count

    print(f"  - 总记录数: {len(file_status)}")
    print(f"  - 完整记录: {complete_count}")
    print(f"  - 不完整记录: {incomplete_count}")

    # 2. 读取metadata
    print("\n[2/4] 读取subject_metadata.json...")
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata_all = json.load(f)

    v2_subjects = {sid: data for sid, data in metadata_all.items()
                   if data.get('data_version') == 'v2'}

    print(f"  - metadata中V2受试者数: {len(v2_subjects)}")
    print(f"  - 标记为完整(5任务)的: {sum(1 for s in v2_subjects.values() if s.get('task_count') == 5)}")

    # 3. 匹配并修复
    print("\n[3/4] 匹配metadata与实际文件...")

    fixed_count = 0
    removed_count = 0
    correct_count = 0

    to_fix = []  # 需要修改tasks_available的
    to_remove = []  # 需要删除的（文件完全不存在）

    for subject_id, subject_data in v2_subjects.items():
        meta = subject_data.get('metadata', {})
        timestamp = meta.get('timestamp', '')

        if timestamp not in file_status:
            print(f"  ⚠ 警告: {subject_id} 的timestamp未在data_index中找到: {timestamp}")
            to_remove.append(subject_id)
            continue

        file_info = file_status[timestamp]
        current_task_count = subject_data.get('task_count', 0)

        if file_info['complete']:
            # 文件完整
            if current_task_count == 5:
                correct_count += 1
            else:
                # 需要修正为5个任务
                to_fix.append({
                    'subject_id': subject_id,
                    'current_count': current_task_count,
                    'correct_count': 5,
                    'tasks_available': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5']
                })
        else:
            # 文件不完整
            missing = file_info['missing_files']
            available_levels = [f'level_{i}' for i in range(1, 6)
                              if f'level_{i}.txt' not in missing]

            if current_task_count != len(available_levels) or current_task_count == 5:
                # 需要修正
                to_fix.append({
                    'subject_id': subject_id,
                    'current_count': current_task_count,
                    'correct_count': len(available_levels),
                    'tasks_available': available_levels,
                    'missing': missing
                })

    print(f"\n  统计结果:")
    print(f"  - 正确标记的: {correct_count}")
    print(f"  - 需要修正的: {len(to_fix)}")
    print(f"  - 需要删除的: {len(to_remove)}")

    # 4. 执行修复
    print(f"\n[4/4] {'[试运行] ' if dry_run else ''}执行修复...")

    if to_fix:
        print(f"\n  需要修正的受试者:")
        for item in to_fix:
            sid = item['subject_id']
            print(f"    {sid}: {item['current_count']} -> {item['correct_count']} 任务")
            if 'missing' in item:
                print(f"      缺失文件: {item['missing']}")

            if not dry_run:
                metadata_all[sid]['task_count'] = item['correct_count']
                metadata_all[sid]['tasks_available'] = item['tasks_available']
                fixed_count += 1

    if to_remove:
        print(f"\n  需要删除的受试者 (timestamp未找到):")
        for sid in to_remove:
            print(f"    {sid}")

            if not dry_run:
                del metadata_all[sid]
                removed_count += 1

    # 5. 保存
    if not dry_run and (to_fix or to_remove):
        print(f"\n保存修改到 {metadata_file}...")

        # 备份原文件
        backup_file = metadata_file.with_suffix('.json.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(v2_subjects, f, ensure_ascii=False, indent=2)
        print(f"  原V2数据已备份至: {backup_file}")

        # 保存修复后的数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_all, f, ensure_ascii=False, indent=2)

        print(f"✓ 修复完成!")
        print(f"  - 修正了 {fixed_count} 个受试者的任务标记")
        print(f"  - 删除了 {removed_count} 个无效受试者")
    else:
        print(f"\n{'[试运行完成] 未实际修改文件' if dry_run else '无需修改'}")

    # 统计最终结果
    if not dry_run:
        v2_final = {sid: data for sid, data in metadata_all.items()
                   if data.get('data_version') == 'v2'}
        complete_final = sum(1 for s in v2_final.values() if s.get('task_count') == 5)

        print(f"\n最终统计:")
        print(f"  V2受试者总数: {len(v2_final)}")
        print(f"  完整(5任务): {complete_final}")
        print(f"  不完整: {len(v2_final) - complete_final}")

if __name__ == '__main__':
    import sys

    project_root = Path(__file__).parent.parent.parent

    # 默认试运行
    dry_run = '--execute' not in sys.argv

    if dry_run:
        print("试运行模式 (添加 --execute 参数以实际执行修改)\n")

    try:
        fix_v2_metadata(project_root, dry_run=dry_run)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
