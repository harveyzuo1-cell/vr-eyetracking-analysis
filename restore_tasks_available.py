"""
从原始数据目录恢复 subject_metadata.json 中的 tasks_available 字段
不破坏任何现有数据，只更新 tasks_available 字段
"""
import json
from pathlib import Path

def restore_tasks_from_raw_data():
    """从原始数据恢复 tasks_available"""

    project_root = Path(__file__).parent

    # V1 原始数据目录
    raw_dirs = {
        "control": project_root / "data" / "control_raw",
        "mci": project_root / "data" / "mci_raw",
        "ad": project_root / "data" / "ad_raw"
    }

    # 元数据文件
    metadata_file = project_root / "new_project" / "data" / "01_raw" / "clinical" / "subject_metadata.json"

    print("=== 从原始数据恢复 tasks_available ===")

    # 加载当前 metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"当前 metadata: {len(metadata)} 个受试者")

    # 扫描原始数据并构建 tasks_available 映射
    tasks_map = {}

    for group, raw_dir in raw_dirs.items():
        if not raw_dir.exists():
            print(f"警告: {raw_dir} 不存在")
            continue

        # 查找所有 {group}_group_* 目录
        pattern = f"{group}_group_*"
        subject_dirs = sorted(raw_dir.glob(pattern))

        print(f"\n{group.upper()}组: {len(subject_dirs)} 个受试者目录")

        for subject_dir in subject_dirs:
            # 提取组号
            parts = subject_dir.name.split('_')
            if len(parts) >= 3:
                group_number = parts[-1]
            else:
                continue

            # 生成 subject_id (与 legacy_importer 一致)
            subject_id = f"{group}_legacy_{group_number}"

            # 检查哪些任务文件存在 (1.txt ~ 5.txt)
            available_tasks = []
            for i in range(1, 6):
                task_file = subject_dir / f"{i}.txt"
                if task_file.exists():
                    available_tasks.append(f"q{i}")

            if available_tasks:
                tasks_map[subject_id] = available_tasks
                print(f"  {subject_id}: {available_tasks}")

    print(f"\n找到 {len(tasks_map)} 个V1受试者的任务数据")

    # 更新 metadata 中的 tasks_available
    updated_count = 0

    for subject_id, tasks in tasks_map.items():
        if subject_id in metadata:
            metadata[subject_id]["tasks_available"] = tasks
            metadata[subject_id]["task_count"] = len(tasks)
            updated_count += 1

    print(f"已更新 {updated_count} 个受试者的 tasks_available")

    # 保存更新后的 metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n成功保存到 {metadata_file}")

    # 验证
    print("\n=== 验证结果 ===")
    has_tasks = sum(1 for meta in metadata.values()
                    if meta.get("tasks_available") and len(meta.get("tasks_available")) > 0)
    no_tasks = len(metadata) - has_tasks

    print(f"有任务的受试者: {has_tasks}")
    print(f"无任务的受试者: {no_tasks}")

    # 抽样检查
    print("\n抽样检查:")
    sample_count = 0
    for subject_id, meta in metadata.items():
        if meta.get("data_version") == "v1" and sample_count < 5:
            tasks = meta.get("tasks_available", [])
            print(f"  {subject_id}: {len(tasks)} 个任务 - {tasks}")
            sample_count += 1

if __name__ == "__main__":
    restore_tasks_from_raw_data()
