"""
重命名已导入的V2数据文件为规范化格式
从 {group}_{hospital_id}_level_X.csv -> v2_{group}_{序号}_level_X.csv
"""
import json
from pathlib import Path

def main():
    base_dir = Path(__file__).parent
    raw_dir = base_dir / "data" / "01_raw"
    metadata_file = raw_dir / "clinical" / "subject_metadata.json"

    # 加载metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        all_metadata = json.load(f)

    print("=" * 80)
    print("重命名V2数据文件为规范化格式")
    print("=" * 80)

    renamed_count = 0
    error_count = 0

    # 遍历所有V2受试者
    for subject_id, meta in all_metadata.items():
        if meta.get('data_version') != 'v2':
            continue

        # 获取原始ID和组别
        original_id = meta.get('metadata', {}).get('original_id', '')
        group = meta.get('group', 'control')

        if not original_id:
            print(f"WARN Skip {subject_id}: no original_id")
            continue

        # 检查文件是否存在
        group_dir = raw_dir / group
        tasks = meta.get('tasks_available', [])

        for task in tasks:
            # 旧文件名: control_1234_level_1.csv
            old_file = group_dir / f"{original_id}_{task}.csv"

            # 新文件名: v2_control_001_level_1.csv
            new_file = group_dir / f"{subject_id}_{task}.csv"

            if old_file.exists():
                if new_file.exists() and new_file != old_file:
                    print(f"ERROR Conflict: {new_file.name} exists")
                    error_count += 1
                else:
                    # 重命名
                    old_file.rename(new_file)
                    print(f"OK {old_file.name} -> {new_file.name}")
                    renamed_count += 1
            else:
                # 检查新文件是否已经存在（可能之前已经重命名过）
                if new_file.exists():
                    print(f"  Exists: {new_file.name}")
                else:
                    print(f"WARN File not found: {old_file.name}")

    print("\n" + "=" * 80)
    print(f"完成！")
    print(f"  重命名: {renamed_count} 个文件")
    print(f"  错误: {error_count} 个")
    print("=" * 80)

if __name__ == '__main__':
    main()
