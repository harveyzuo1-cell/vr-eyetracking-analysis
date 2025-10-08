"""
修复被错误重命名为V1 legacy格式的V2受试者
根据original_id是否为v2_前缀来判断
"""
import json
from pathlib import Path

def fix_wrongly_renamed_subjects():
    """修复错误重命名的V2受试者"""

    project_root = Path(__file__).parent

    # subject_info目录
    subject_info_dir = project_root / "new_project" / "data" / "subject_info"

    # metadata文件
    metadata_file = project_root / "new_project" / "data" / "01_raw" / "clinical" / "subject_metadata.json"

    print("=== 修复被错误重命名的V2受试者 ===\n")

    # 加载metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    fixed_count = 0

    for group in ['control', 'mci', 'ad']:
        group_dir = subject_info_dir / group
        if not group_dir.exists():
            continue

        for json_file in group_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                subject_id = data.get('subject_id')
                data_version = data.get('data_version')
                original_id = data.get('metadata', {}).get('original_id', '')

                # 如果data_version=v1但original_id是v2_开头，需要修复
                if data_version == 'v1' and original_id.startswith('v2_'):
                    print(f"修复: {subject_id}")
                    print(f"  original_id: {original_id}")
                    print(f"  恢复为: {original_id}")

                    # 更新subject_info
                    data['subject_id'] = original_id
                    data['data_version'] = 'v2'
                    data['tasks_available'] = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5']
                    data['task_count'] = 5
                    if 'metadata' in data:
                        del data['metadata']['original_id']  # 清除original_id

                    # 保存到新文件名
                    new_file = group_dir / f"{original_id}.json"
                    with open(new_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    # 删除旧文件
                    if json_file != new_file:
                        json_file.unlink()

                    # 更新metadata
                    if subject_id in metadata:
                        del metadata[subject_id]

                    metadata[original_id] = data

                    fixed_count += 1

            except Exception as e:
                print(f"  错误: 处理 {json_file.name} 失败: {e}")

    print(f"\n已修复 {fixed_count} 个受试者")

    # 保存metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"已保存到 {metadata_file}")

    # 验证
    print("\n=== 验证结果 ===")
    v1_total = sum(1 for meta in metadata.values() if meta.get('data_version') == 'v1')
    v2_total = sum(1 for meta in metadata.values() if meta.get('data_version') == 'v2')

    print(f"V1受试者: {v1_total}")
    print(f"V2受试者: {v2_total}")

if __name__ == "__main__":
    fix_wrongly_renamed_subjects()
