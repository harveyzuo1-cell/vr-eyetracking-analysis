"""
清理重复的AD受试者记录
删除 ad_legacy_1 和 ad_legacy_2，因为它们是V2数据的错误副本
"""
import json
import sys
from pathlib import Path

# 设置UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

def cleanup_duplicate_ad_records():
    """删除ad_legacy_1和ad_legacy_2（它们是v2_ad_001和v2_ad_002的错误副本）"""

    project_root = Path(__file__).parent
    metadata_file = project_root / "new_project" / "data" / "01_raw" / "clinical" / "subject_metadata.json"
    subject_info_dir = project_root / "new_project" / "data" / "subject_info" / "ad"

    print("=== 清理重复的AD受试者记录 ===\n")

    # 1. 从subject_metadata.json中删除
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    removed_from_metadata = []
    for subject_id in ['ad_legacy_1', 'ad_legacy_2']:
        if subject_id in metadata:
            original_id = metadata[subject_id].get('metadata', {}).get('original_id')
            print(f"从subject_metadata.json删除: {subject_id} (original_id: {original_id})")
            del metadata[subject_id]
            removed_from_metadata.append(subject_id)

    if removed_from_metadata:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"✓ 已从subject_metadata.json删除 {len(removed_from_metadata)} 条记录\n")
    else:
        print("subject_metadata.json中没有找到ad_legacy_1或ad_legacy_2\n")

    # 2. 删除subject_info JSON文件
    removed_files = []
    for subject_id in ['ad_legacy_1', 'ad_legacy_2']:
        json_file = subject_info_dir / f"{subject_id}.json"
        if json_file.exists():
            print(f"删除subject_info文件: {json_file.name}")
            json_file.unlink()
            removed_files.append(json_file.name)

    if removed_files:
        print(f"✓ 已删除 {len(removed_files)} 个subject_info文件\n")
    else:
        print("没有找到需要删除的subject_info文件\n")

    # 3. 验证v2_ad_001和v2_ad_002仍然存在
    print("=== 验证V2数据完整性 ===")
    for v2_id in ['v2_ad_001', 'v2_ad_002']:
        v2_json = subject_info_dir / f"{v2_id}.json"
        if v2_json.exists():
            with open(v2_json, 'r', encoding='utf-8') as f:
                v2_data = json.load(f)
            print(f"✓ {v2_id} 存在 (data_version: {v2_data['data_version']})")
        else:
            print(f"⚠ 警告: {v2_id} 不存在！")

        if v2_id in metadata:
            print(f"✓ {v2_id} 在subject_metadata.json中存在")
        else:
            print(f"⚠ 警告: {v2_id} 不在subject_metadata.json中！")

    print("\n=== 清理完成 ===")
    print("已删除ad_legacy_1和ad_legacy_2（它们是V2数据的错误副本）")
    print("V2数据(v2_ad_001, v2_ad_002)保持完整")

if __name__ == "__main__":
    cleanup_duplicate_ad_records()
