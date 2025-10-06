"""
从01_raw目录中的CSV文件恢复tasks_available
这个方法更准确，因为它基于实际导入的数据文件
"""
import json
from pathlib import Path
from collections import defaultdict

def restore_from_imported_csv():
    """从导入后的CSV文件恢复tasks"""

    project_root = Path(__file__).parent
    metadata_file = project_root / "new_project" / "data" / "01_raw" / "clinical" / "subject_metadata.json"

    # V1导入后的数据目录
    imported_dirs = {
        "control": project_root / "new_project" / "data" / "01_raw" / "control",
        "mci": project_root / "new_project" / "data" / "01_raw" / "mci",
        "ad": project_root / "new_project" / "data" / "01_raw" / "ad"
    }

    print("=== 从导入后的CSV文件恢复 tasks_available ===\n")

    # 加载metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # 扫描CSV文件
    subject_tasks = defaultdict(list)

    for group, imported_dir in imported_dirs.items():
        if not imported_dir.exists():
            print(f"警告: {imported_dir} 不存在")
            continue

        csv_files = list(imported_dir.glob("*_q[1-5].csv"))
        print(f"{group.upper()}组: 找到 {len(csv_files)} 个CSV文件")

        for csv_file in csv_files:
            # 文件名格式可能是:
            # - ad_001_q1.csv
            # - ad_legacy_3_q1.csv
            # - control_legacy_1_q1.csv
            filename = csv_file.stem
            parts = filename.rsplit('_q', 1)

            if len(parts) != 2:
                continue

            base_id = parts[0]
            task_num = parts[1]

            # 查找匹配的subject_id
            # 先尝试直接匹配
            if base_id in metadata:
                subject_id = base_id
            else:
                # 尝试legacy格式
                # ad_001 -> ad_legacy_1
                id_parts = base_id.split('_')
                if len(id_parts) >= 2 and id_parts[-1].isdigit():
                    # 去掉前导0
                    num = str(int(id_parts[-1]))
                    subject_id = f"{group}_legacy_{num}"

                    if subject_id not in metadata:
                        # 可能已经是legacy格式
                        subject_id = base_id

            if subject_id in metadata:
                subject_tasks[subject_id].append(f"q{task_num}")

    # 更新metadata
    updated_count = 0
    for subject_id, tasks in subject_tasks.items():
        if subject_id in metadata and metadata[subject_id].get('data_version') == 'v1':
            tasks_sorted = sorted(set(tasks))  # 去重并排序
            metadata[subject_id]['tasks_available'] = tasks_sorted
            metadata[subject_id]['task_count'] = len(tasks_sorted)
            updated_count += 1

    print(f"\n已更新 {updated_count} 个V1受试者的 tasks_available")

    # V2数据
    print("\n=== 处理V2数据 ===")
    v2_updated = 0
    for subject_id, meta in metadata.items():
        if meta.get('data_version') == 'v2':
            metadata[subject_id]['tasks_available'] = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5']
            metadata[subject_id]['task_count'] = 5
            v2_updated += 1

    print(f"已更新 {v2_updated} 个V2受试者的 tasks_available")

    # 保存
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n成功保存到 {metadata_file}")

    # 验证
    print("\n=== 验证结果 ===")
    v1_has_tasks = sum(1 for meta in metadata.values()
                       if meta.get('data_version') == 'v1' and
                       meta.get('tasks_available') and
                       len(meta.get('tasks_available')) > 0)

    v1_total = sum(1 for meta in metadata.values() if meta.get('data_version') == 'v1')

    print(f"V1受试者: {v1_has_tasks}/{v1_total} 有任务")
    print(f"V2受试者: {v2_updated} 个")

    # 检查ad_legacy_1
    if 'ad_legacy_1' in metadata:
        ad1_tasks = metadata['ad_legacy_1'].get('tasks_available', [])
        print(f"\nad_legacy_1: {len(ad1_tasks)} 个任务 - {ad1_tasks}")

if __name__ == "__main__":
    restore_from_imported_csv()
