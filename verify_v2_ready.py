"""
验证V2数据导入准备情况
"""
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'new_project'))

from src.modules.module02_preprocessing.subject_manager import SubjectManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    subject_manager = SubjectManager(data_dir='new_project/data/subject_info')

    print("\n" + "="*60)
    print("V2数据导入准备状态检查")
    print("="*60 + "\n")

    for group in ['control', 'mci', 'ad']:
        # V1数据统计
        v1_subjects = subject_manager.get_all_subjects(group=group, data_version='v1')
        v1_with_v2_ids = [s for s in v1_subjects if s['subject_id'].startswith('v2_')]

        # V2数据统计
        v2_subjects = subject_manager.get_all_subjects(group=group, data_version='v2')

        print(f"{group.upper()}组:")
        print(f"  V1数据: {len(v1_subjects)}个")
        print(f"    - 使用V2格式ID的V1数据: {len(v1_with_v2_ids)}个")
        print(f"  V2数据: {len(v2_subjects)}个")

        if v1_with_v2_ids:
            print(f"  警告: 仍有{len(v1_with_v2_ids)}个V1数据使用V2格式ID!")
            for s in v1_with_v2_ids[:5]:  # 显示前5个
                print(f"    - {s['subject_id']}")
        else:
            print(f"  状态: 准备就绪，可以导入V2数据")
        print()

    print("="*60)

if __name__ == '__main__':
    main()
