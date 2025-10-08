"""
清理旧的AD数据并重新导入，建立正确映射
ad_group_3-22 -> ad_legacy_1-20
"""
import sys
import json
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent / 'new_project'))
sys.stdout.reconfigure(encoding='utf-8')

from src.web.modules.module00_data_management.importers.legacy_importer import LegacyDataImporter

def cleanup_and_reimport():
    project_root = Path(__file__).parent

    # 1. 清理旧的AD CSV文件
    print("=== 清理旧的AD CSV文件 ===")
    csv_dir = project_root / "new_project" / "data" / "01_raw" / "ad"
    deleted_csv = 0
    for csv_file in csv_dir.glob("ad_legacy_*.csv"):
        csv_file.unlink()
        deleted_csv += 1
    print(f"删除了 {deleted_csv} 个CSV文件\n")

    # 2. 清理旧的AD subject_info文件
    print("=== 清理旧的AD subject_info文件 ===")
    subject_info_dir = project_root / "new_project" / "data" / "subject_info" / "ad"
    deleted_json = 0
    for json_file in subject_info_dir.glob("ad_legacy_*.json"):
        json_file.unlink()
        deleted_json += 1
    print(f"删除了 {deleted_json} 个JSON文件\n")

    # 3. 从subject_metadata.json中删除所有AD V1记录
    print("=== 清理subject_metadata.json中的AD V1记录 ===")
    metadata_file = project_root / "new_project" / "data" / "01_raw" / "clinical" / "subject_metadata.json"
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    ad_v1_ids = [s_id for s_id, s in metadata.items()
                 if s.get('data_version') == 'v1' and s.get('group') == 'ad']

    for s_id in ad_v1_ids:
        del metadata[s_id]

    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"从metadata删除了 {len(ad_v1_ids)} 个AD V1记录\n")

    # 4. 重新导入AD组
    print("=== 重新导入AD组数据 ===")
    importer = LegacyDataImporter()
    scan_result = importer.scan_legacy_data()
    ad_subjects = scan_result.get('ad', [])

    print(f"找到 {len(ad_subjects)} 个AD受试者")
    print("\n原始目录 -> 新ID映射:")
    for subj in ad_subjects:
        print(f"  {subj['subject_dir'].name} -> {subj['subject_id']}")

    print("\n开始导入...")
    imported_count = 0
    failed_count = 0

    for subj_info in ad_subjects:
        try:
            result = importer.import_single_subject(subj_info)
            print(f"✓ {result['subject_id']}")
            imported_count += 1
        except Exception as e:
            print(f"✗ {subj_info['subject_id']}: {str(e)}")
            failed_count += 1

    print(f"\n=== 导入完成 ===")
    print(f"成功: {imported_count}")
    print(f"失败: {failed_count}")

    # 5. 验证结果
    print("\n=== 验证结果 ===")
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    v1_count = sum(1 for s in metadata.values() if s.get('data_version') == 'v1')
    ad_v1_new = sorted([s_id for s_id, s in metadata.items()
                        if s.get('data_version') == 'v1' and s.get('group') == 'ad'])

    print(f"V1受试者总数: {v1_count}")
    print(f"AD组V1受试者: {len(ad_v1_new)}")
    print(f"AD受试者ID: {ad_v1_new}")

if __name__ == "__main__":
    cleanup_and_reimport()
