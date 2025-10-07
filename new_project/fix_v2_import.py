"""
修复V2数据导入问题
1. 删除所有错误命名的V2文件 (control_s*, ad_s*, mci_s* 带 _q*.csv)
2. 清除V2的导入历史
3. 重新导入V2数据
"""
import json
import requests
from pathlib import Path
import time

# 配置
BASE_DIR = Path(__file__).parent / "data" / "01_raw"
METADATA_FILE = BASE_DIR / "clinical" / "subject_metadata.json"
IMPORT_HISTORY_FILE = BASE_DIR / "clinical" / "import_history.json"
API_URL = "http://127.0.0.1:9090/api/m00/import"

def load_metadata():
    """加载subject_metadata.json"""
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_v2_subject_ids():
    """获取所有V2受试者的hospital_id"""
    metadata = load_metadata()
    v2_hospital_ids = set()

    for subject_id, data in metadata.items():
        if data.get('data_version') == 'v2':
            # 从metadata中获取原始hospital_id
            hospital_id = data.get('metadata', {}).get('original_id', '')
            if hospital_id:
                v2_hospital_ids.add(hospital_id)

    return v2_hospital_ids

def delete_v2_files():
    """删除所有错误命名的V2文件"""
    v2_hospital_ids = get_v2_subject_ids()

    print(f"找到 {len(v2_hospital_ids)} 个V2受试者")
    print(f"V2 hospital_ids 示例: {list(v2_hospital_ids)[:5]}")

    deleted_count = 0

    # 遍历各个组别目录
    for group_dir in ['control', 'mci', 'ad']:
        group_path = BASE_DIR / group_dir
        if not group_path.exists():
            continue

        # 查找所有_q*.csv文件
        for csv_file in group_path.glob("*_q*.csv"):
            # 检查是否是V2文件 (通过hospital_id匹配)
            filename = csv_file.stem  # 例如: control_s001_q1
            parts = filename.split('_')

            # 提取hospital_id部分 (例如: control_s001)
            if len(parts) >= 3:
                hospital_id = '_'.join(parts[:-1])  # 例如: control_s001

                if hospital_id in v2_hospital_ids:
                    print(f"删除V2文件: {csv_file}")
                    csv_file.unlink()
                    deleted_count += 1

    print(f"\n总共删除了 {deleted_count} 个V2文件")
    return deleted_count

def clear_v2_import_history():
    """清除V2的导入历史"""
    with open(IMPORT_HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)

    # 清除eye_tracking的导入历史
    if 'eye_tracking' in history:
        old_count = len(history['eye_tracking'].get('source_timestamps', []))
        history['eye_tracking'] = {
            'last_import': None,
            'source_timestamps': [],
            'imported_count': 0
        }

        with open(IMPORT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        print(f"\n清除了 {old_count} 个V2导入历史记录")
        return old_count

    return 0

def reimport_v2_data():
    """重新导入V2数据"""
    print("\n开始重新导入V2数据...")

    try:
        response = requests.post(
            API_URL,
            json={
                'source': 'eye_tracking',
                'overwrite': True
            },
            timeout=300  # 5分钟超时
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                data = result.get('data', {})
                print(f"\n✅ V2数据导入成功!")
                print(f"导入数量: {data.get('imported_count', 0)}")
                print(f"跳过数量: {data.get('skipped_count', 0)}")
                print(f"失败数量: {data.get('failed_count', 0)}")

                if data.get('failed_subjects'):
                    print(f"\n失败的受试者:")
                    for subj in data['failed_subjects']:
                        print(f"  - {subj}")

                return True
            else:
                print(f"\n❌ 导入失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"\n❌ 导入异常: {e}")
        return False

def main():
    print("=" * 60)
    print("修复V2数据导入问题")
    print("=" * 60)

    # 步骤1: 删除错误的V2文件
    print("\n步骤1: 删除错误命名的V2文件")
    print("-" * 60)
    deleted = delete_v2_files()

    # 步骤2: 清除导入历史
    print("\n步骤2: 清除V2导入历史")
    print("-" * 60)
    cleared = clear_v2_import_history()

    # 步骤3: 重新导入
    print("\n步骤3: 重新导入V2数据")
    print("-" * 60)
    success = reimport_v2_data()

    print("\n" + "=" * 60)
    if success:
        print("✅ 修复完成!")
        print(f"  - 删除文件: {deleted} 个")
        print(f"  - 清除历史: {cleared} 条")
        print("  - 重新导入: 成功")
    else:
        print("❌ 修复失败，请检查日志")
    print("=" * 60)

if __name__ == '__main__':
    main()
