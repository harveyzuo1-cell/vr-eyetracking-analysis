"""
重新导入AD组数据，建立正确的映射关系
ad_group_3-22 -> ad_legacy_1-20
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'new_project'))

from src.web.modules.module00_data_management.importers.legacy_importer import LegacyDataImporter

def reimport_ad_group():
    importer = LegacyDataImporter()

    # 扫描AD组数据
    print("=== 扫描AD组数据 ===")
    scan_result = importer.scan_legacy_data()
    ad_subjects = scan_result.get('ad', [])

    print(f"找到 {len(ad_subjects)} 个AD受试者")
    print("\n原始目录 -> 新ID映射:")
    for subj in ad_subjects:
        print(f"  {subj['subject_dir'].name} -> {subj['subject_id']}")

    # 重新导入（覆盖现有数据）
    print("\n=== 重新导入AD组数据 ===")

    imported_count = 0
    failed_count = 0

    for subj_info in ad_subjects:
        try:
            result = importer.import_single_subject(subj_info)
            print(f"✓ 导入成功: {result['subject_id']}")
            imported_count += 1
        except Exception as e:
            print(f"✗ 导入失败: {subj_info['subject_id']} - {str(e)}")
            failed_count += 1

    print(f"\n=== 导入完成 ===")
    print(f"成功: {imported_count}")
    print(f"失败: {failed_count}")
    print(f"总计: {len(ad_subjects)}")

if __name__ == "__main__":
    reimport_ad_group()
