"""
紧急修复：将所有original_id为v2_*的受试者恢复为V1数据版本
这些受试者的data_version应该是v1，不是v2
"""
import json
import sys
from pathlib import Path

# 设置UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

def urgent_fix_v1_data():
    """恢复所有被错误改成V2的V1数据"""

    project_root = Path(__file__).parent
    metadata_file = project_root / "new_project" / "data" / "01_raw" / "clinical" / "subject_metadata.json"

    print("=== 紧急修复V1数据 ===\n")

    # 加载metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"加载了 {len(metadata)} 个受试者的元数据")

    # 统计需要修复的受试者
    need_fix = []

    for subject_id, meta in metadata.items():
        original_id = meta.get('metadata', {}).get('original_id', '')
        data_version = meta.get('data_version', '')

        # 如果original_id是v2_*格式，说明这是被重命名过的V1数据
        # 它们的data_version应该是v1，不是v2
        if original_id and original_id.startswith('v2_'):
            if data_version != 'v1':
                need_fix.append({
                    'subject_id': subject_id,
                    'current_version': data_version,
                    'original_id': original_id
                })

    print(f"\n发现 {len(need_fix)} 个需要修复的受试者（data_version应为v1但不是）\n")

    if not need_fix:
        print("✓ 没有需要修复的数据")
        return

    # 显示需要修复的受试者
    for item in need_fix[:10]:  # 只显示前10个
        print(f"  {item['subject_id']}: {item['current_version']} -> v1 (original_id: {item['original_id']})")

    if len(need_fix) > 10:
        print(f"  ... 还有 {len(need_fix) - 10} 个")

    # 执行修复
    print("\n开始修复...")
    fixed_count = 0

    for item in need_fix:
        subject_id = item['subject_id']

        # 恢复为V1
        metadata[subject_id]['data_version'] = 'v1'

        # 清空tasks_available，等待从CSV重新扫描
        metadata[subject_id]['tasks_available'] = []
        metadata[subject_id]['task_count'] = 0

        fixed_count += 1

    # 保存修复后的metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 已修复 {fixed_count} 个受试者的data_version为v1")
    print(f"✓ 已保存到 {metadata_file}")

    # 验证修复结果
    print("\n=== 验证修复结果 ===")

    v1_with_v2_original = 0
    v2_with_v2_original = 0

    for subject_id, meta in metadata.items():
        original_id = meta.get('metadata', {}).get('original_id', '')
        data_version = meta.get('data_version', '')

        if original_id and original_id.startswith('v2_'):
            if data_version == 'v1':
                v1_with_v2_original += 1
            else:
                v2_with_v2_original += 1

    print(f"data_version=v1 且 original_id=v2_*: {v1_with_v2_original} (正确)")
    print(f"data_version=v2 且 original_id=v2_*: {v2_with_v2_original} (错误，应为0)")

    if v2_with_v2_original > 0:
        print("\n⚠ 警告：仍有受试者的data_version不正确！")
    else:
        print("\n✓ 所有受试者的data_version已正确")

if __name__ == "__main__":
    urgent_fix_v1_data()
