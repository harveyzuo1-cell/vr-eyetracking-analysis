import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.web.modules.module00_data_management.importers.eye_tracking_importer import EyeTrackingDataImporter

importer = EyeTrackingDataImporter()
scan_result = importer.scan_new_data()

print("=== scan_new_data() 结果 ===")
print(f"total_dirs: {scan_result['total_dirs']}")
print(f"indexed_entries: {scan_result['indexed_entries']}")
print(f"valid_entries (files_complete=True): {len(scan_result['valid_entries'])}")
print(f"incomplete_count: {scan_result.get('incomplete_count', 0)}")

# 按组统计valid_entries
groups = {}
for entry in scan_result['valid_entries']:
    g = entry['group_code']
    groups[g] = groups.get(g, 0) + 1

print("\nvalid_entries按组统计:")
for g, count in sorted(groups.items()):
    print(f"  {g}: {count}")

print(f"\nvalid_entries总数: {len(scan_result['valid_entries'])}")
