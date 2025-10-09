"""
为现有RQA分析结果添加统一的批次ID

这个脚本会:
1. 扫描所有已完成的RQA结果目录
2. 为所有没有task_id的metadata.json添加统一的批次ID
3. 使它们能被正确分组显示
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
RESULTS_DIR = Path(__file__).parent.parent / 'data' / '05_rqa_analysis' / 'results'
BATCH_ID = 'task_20251008_initial_batch'  # 统一的批次ID
DATA_VERSION = 'v1'

def main():
    if not RESULTS_DIR.exists():
        print(f"❌ 结果目录不存在: {RESULTS_DIR}")
        return

    updated_count = 0
    skipped_count = 0
    error_count = 0

    # 遍历所有结果目录
    for result_dir in RESULTS_DIR.iterdir():
        if not result_dir.is_dir():
            continue

        metadata_file = result_dir / 'metadata.json'

        if not metadata_file.exists():
            print(f"⚠️  metadata.json不存在: {result_dir.name}")
            skipped_count += 1
            continue

        try:
            # 读取metadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 检查是否已有task_id
            if 'task_id' in metadata and metadata['task_id']:
                print(f"⏭️  已有task_id: {result_dir.name} -> {metadata['task_id']}")
                skipped_count += 1
                continue

            # 添加批次信息
            metadata['task_id'] = BATCH_ID
            metadata['data_version'] = DATA_VERSION

            # 如果没有batch_time，使用创建时间
            if 'batch_time' not in metadata:
                creation_time = metadata.get('creation_time', datetime.now().isoformat())
                metadata['batch_time'] = creation_time

            # 写回文件
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"✅ 已更新: {result_dir.name}")
            updated_count += 1

        except Exception as e:
            print(f"❌ 处理失败 {result_dir.name}: {e}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"✅ 成功更新: {updated_count} 个结果")
    print(f"⏭️  跳过: {skipped_count} 个结果")
    print(f"❌ 失败: {error_count} 个结果")
    print(f"{'='*60}")
    print(f"\n批次ID: {BATCH_ID}")
    print(f"数据版本: {DATA_VERSION}")

if __name__ == '__main__':
    main()
