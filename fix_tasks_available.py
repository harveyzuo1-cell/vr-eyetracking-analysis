"""
修复subject_metadata.json中的tasks_available字段
从subject_info目录的JSON文件中读取并恢复tasks_available信息
"""
import json
from pathlib import Path

def fix_tasks_available():
    """修复tasks_available字段"""

    project_root = Path(__file__).parent
    subject_info_dir = project_root / "new_project" / "data" / "subject_info"
    clinical_dir = project_root / "new_project" / "data" / "01_raw" / "clinical"
    metadata_file = clinical_dir / "subject_metadata.json"

    print("=== 修复subject_metadata.json中的tasks_available ===")

    # 加载当前的metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"当前metadata中有 {len(metadata)} 个受试者")

    # 从subject_info目录读取每个受试者的JSON并更新tasks_available
    fixed_count = 0

    for group in ["control", "mci", "ad"]:
        group_dir = subject_info_dir / group
        if not group_dir.exists():
            continue

        for json_file in group_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    subject_data = json.load(f)

                subject_id = subject_data.get("subject_id")
                tasks_available = subject_data.get("tasks_available", [])

                if not subject_id:
                    continue

                # 如果metadata中存在这个受试者，更新其tasks_available
                if subject_id in metadata:
                    metadata[subject_id]["tasks_available"] = tasks_available
                    fixed_count += 1

            except Exception as e:
                print(f"  错误: 处理 {json_file.name} 失败: {e}")

    print(f"已更新 {fixed_count} 个受试者的tasks_available字段")

    # 保存修复后的metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"成功保存到 {metadata_file}")

    # 验证修复结果
    print("\n=== 验证修复结果 ===")
    has_tasks = sum(1 for meta in metadata.values() if meta.get("tasks_available"))
    no_tasks = len(metadata) - has_tasks

    print(f"有任务的受试者: {has_tasks}")
    print(f"无任务的受试者: {no_tasks}")

    # 抽样检查
    print("\n抽样检查前5个受试者:")
    for i, (subject_id, meta) in enumerate(list(metadata.items())[:5]):
        tasks = meta.get("tasks_available", [])
        print(f"  {subject_id}: {len(tasks)} 个任务")

if __name__ == "__main__":
    fix_tasks_available()
