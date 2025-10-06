"""
重建subject_metadata.json
从subject_info目录读取所有受试者信息，重新生成干净的metadata文件
"""
import json
from pathlib import Path
from datetime import datetime

def rebuild_metadata():
    """重建subject_metadata.json"""

    # 路径配置
    project_root = Path(__file__).parent
    subject_info_dir = project_root / "new_project" / "data" / "subject_info"
    clinical_dir = project_root / "new_project" / "data" / "01_raw" / "clinical"
    metadata_file = clinical_dir / "subject_metadata.json"

    # 确保目录存在
    clinical_dir.mkdir(parents=True, exist_ok=True)

    print("=== 重建subject_metadata.json ===")
    print(f"从目录读取: {subject_info_dir}")
    print(f"输出文件: {metadata_file}")
    print()

    # 收集所有受试者
    all_subjects = {}
    stats = {"v1": 0, "v2": 0, "control": 0, "mci": 0, "ad": 0}

    for group in ["control", "mci", "ad"]:
        group_dir = subject_info_dir / group
        if not group_dir.exists():
            print(f"警告: 组别目录不存在 {group_dir}")
            continue

        # 读取所有JSON文件
        json_files = list(group_dir.glob("*.json"))
        print(f"处理 {group} 组: {len(json_files)} 个受试者")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                subject_id = data.get("subject_id")
                data_version = data.get("data_version", "v1")

                if not subject_id:
                    print(f"  警告: {json_file.name} 缺少subject_id")
                    continue

                # 检查重复
                if subject_id in all_subjects:
                    print(f"  警告: 重复的subject_id: {subject_id}")
                    continue

                # 添加到集合
                all_subjects[subject_id] = data

                # 统计
                stats[data_version] += 1
                stats[group] += 1

            except Exception as e:
                print(f"  错误: 处理 {json_file.name} 失败: {e}")

    print()
    print("=== 统计信息 ===")
    print(f"总受试者数: {len(all_subjects)}")
    print(f"V1数据: {stats['v1']}")
    print(f"V2数据: {stats['v2']}")
    print(f"Control组: {stats['control']}")
    print(f"MCI组: {stats['mci']}")
    print(f"AD组: {stats['ad']}")
    print()

    # 保存metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(all_subjects, f, indent=2, ensure_ascii=False)

    print(f"✓ 成功保存 {metadata_file}")
    print()

    # 验证V2数据
    print("=== V2数据验证 ===")
    v2_subjects = {sid: meta for sid, meta in all_subjects.items()
                   if meta.get("data_version") == "v2"}

    for group in ["control", "mci", "ad"]:
        group_v2 = [sid for sid, meta in v2_subjects.items()
                    if meta.get("group") == group]
        print(f"{group.upper()} V2: {len(group_v2)} 个受试者")
        if group_v2:
            print(f"  示例: {sorted(group_v2)[:5]}")

if __name__ == "__main__":
    rebuild_metadata()
