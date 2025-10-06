"""
修复V1数据被错误地命名为V2格式的问题

将data_version='v1'但subject_id格式为v2_xxx的受试者重命名回原始ID
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
    subject_dir = Path('new_project/data/subject_info')

    renamed_count = 0

    for group in ['control', 'mci', 'ad']:
        logger.info(f"Processing {group} group...")
        group_path = subject_dir / group

        if not group_path.exists():
            logger.warning(f"Group directory not found: {group_path}")
            continue

        for json_file in group_path.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                subject_id = data.get('subject_id')
                data_version = data.get('data_version')
                original_id = data.get('metadata', {}).get('original_id')

                # 检查是否是V1数据但使用了V2格式的ID
                if data_version == 'v1' and subject_id.startswith('v2_'):
                    if original_id:
                        logger.info(f"Found V1 data with V2 ID: {subject_id} (original: {original_id})")

                        # 重命名回原始ID
                        try:
                            result = subject_manager.rename_subject(subject_id, original_id)
                            if result:
                                logger.info(f"✓ Renamed: {subject_id} -> {original_id}")
                                renamed_count += 1
                            else:
                                logger.error(f"✗ Failed to rename: {subject_id} -> {original_id}")
                        except Exception as e:
                            logger.error(f"✗ Error renaming {subject_id}: {str(e)}")
                    else:
                        logger.warning(f"Subject {subject_id} has no original_id in metadata, skipping")

            except Exception as e:
                logger.error(f"Error processing {json_file}: {str(e)}")

    logger.info(f"\n{'='*60}")
    logger.info(f"Renaming complete: {renamed_count} subjects renamed")
    logger.info(f"{'='*60}\n")

    # 验证结果
    logger.info("Verifying results...")
    for group in ['control', 'mci', 'ad']:
        all_subjects = subject_manager.get_all_subjects(group=group, data_version='v1')
        v2_format_count = sum(1 for s in all_subjects if s['subject_id'].startswith('v2_'))
        logger.info(f"{group.upper()}: {v2_format_count} V1 subjects still have V2 format IDs")

if __name__ == '__main__':
    main()
