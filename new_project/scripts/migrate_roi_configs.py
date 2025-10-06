"""
ROI配置数据迁移脚本
Migration Script for ROI Configurations

功能:
1. 将 config/roi_v1.json 拆分为 data/roi_configs/v1/q{1-5}_roi.json
2. 将 config/roi_v2.json 拆分为 data/roi_configs/v2/q{1-5}_roi.json
3. 转换旧格式到新格式（分层结构）
4. 备份原始文件

使用方法:
python scripts/migrate_roi_configs.py --backup --validate
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse


def backup_file(file_path: Path) -> Path:
    """备份文件"""
    if not file_path.exists():
        print(f"[SKIP] 文件不存在，跳过备份: {file_path}")
        return None

    backup_path = file_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    shutil.copy2(file_path, backup_path)
    print(f"[OK] 备份文件: {backup_path}")
    return backup_path


def convert_to_new_format(regions: List[Dict], version: str, task_id: str) -> Dict:
    """
    将旧格式转换为新格式

    旧格式: {"id": "KW_q1_1", "task": "q1", "type": "KW", "coords": [...]}
    新格式: {"regions": {"keywords": [...], "instructions": [...], "background": [...]}}
    """
    grouped_regions = {
        'keywords': [],
        'instructions': [],
        'background': []
    }

    for region in regions:
        region_type = region.get('type', '').upper()

        # 转换坐标格式
        region_copy = region.copy()
        if 'coords' in region_copy:
            region_copy['normalized_coords'] = region_copy.pop('coords')

        # 确保有必要字段
        if 'task_id' not in region_copy:
            region_copy['task_id'] = task_id
        if 'version' not in region_copy:
            region_copy['version'] = version

        # 分组
        if region_type == 'KW':
            grouped_regions['keywords'].append(region_copy)
        elif region_type == 'INST':
            grouped_regions['instructions'].append(region_copy)
        elif region_type == 'BG':
            grouped_regions['background'].append(region_copy)
        else:
            # 未知类型放入background
            grouped_regions['background'].append(region_copy)

    # 如果没有背景区域，添加一个默认的
    if not grouped_regions['background']:
        grouped_regions['background'].append({
            'id': f'BG_{task_id}',
            'type': 'BG',
            'normalized_coords': [0, 0, 1, 1],
            'task_id': task_id,
            'version': version
        })

    return {
        'version': version,
        'task_id': task_id,
        'task_name': task_id.upper(),
        'background_image': get_background_image_name(version, task_id),
        'regions': grouped_regions,
        'last_modified': datetime.now().isoformat()
    }


def get_background_image_name(version: str, task_id: str) -> str:
    """获取背景图片文件名"""
    if version == 'v1':
        num = task_id[1] if len(task_id) > 1 else '1'
        return f"Q{num}.jpg"
    else:
        # v2使用task{n}格式
        num = task_id[1] if len(task_id) > 1 else '1'
        return f"task{num}.png"


def migrate_roi_config(config_file: Path, output_dir: Path, version: str):
    """迁移单个ROI配置文件"""
    print(f"\n[MIGRATE] 处理配置文件: {config_file}")

    if not config_file.exists():
        print(f"[WARN] 配置文件不存在: {config_file}")
        return False

    # 读取原始配置
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    regions = data.get('regions', [])
    print(f"   找到 {len(regions)} 个ROI区域")

    # 按task分组
    tasks_regions = {}
    for region in regions:
        task = region.get('task', 'q1')
        if task not in tasks_regions:
            tasks_regions[task] = []
        tasks_regions[task].append(region)

    print(f"   分组为 {len(tasks_regions)} 个任务: {list(tasks_regions.keys())}")

    # 创建输出目录
    version_dir = output_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)

    # 为每个task创建独立配置文件
    for task_id, task_regions in tasks_regions.items():
        # 转换为新格式
        new_config = convert_to_new_format(task_regions, version, task_id)

        # 保存文件
        output_file = version_dir / f"{task_id}_roi.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, ensure_ascii=False, indent=2)

        print(f"   [OK] 创建: {output_file} ({len(task_regions)} regions)")

    return True


def validate_migration(output_dir: Path, version: str, expected_tasks: List[str]):
    """验证迁移结果"""
    print(f"\n[VALIDATE] 验证迁移结果: {version}")

    version_dir = output_dir / version
    if not version_dir.exists():
        print(f"   [ERROR] 输出目录不存在: {version_dir}")
        return False

    success = True
    for task_id in expected_tasks:
        config_file = version_dir / f"{task_id}_roi.json"

        if not config_file.exists():
            print(f"   [ERROR] 缺少配置文件: {config_file}")
            success = False
            continue

        # 读取并验证格式
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查必要字段
        required_fields = ['version', 'task_id', 'regions']
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            print(f"   [ERROR] {config_file.name} 缺少字段: {missing_fields}")
            success = False
        else:
            regions = data['regions']
            total_regions = (
                len(regions.get('keywords', [])) +
                len(regions.get('instructions', [])) +
                len(regions.get('background', []))
            )
            print(f"   [OK] {config_file.name}: {total_regions} regions")

    return success


def main():
    parser = argparse.ArgumentParser(description='迁移ROI配置文件')
    parser.add_argument('--backup', action='store_true', help='备份原始文件')
    parser.add_argument('--validate', action='store_true', help='验证迁移结果')
    parser.add_argument('--force', action='store_true', help='强制覆盖已存在的文件')

    args = parser.parse_args()

    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config_dir = project_root / 'config'
    data_dir = project_root / 'data'
    output_dir = data_dir / 'roi_configs'

    print("=" * 60)
    print("ROI配置迁移脚本")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print(f"配置目录: {config_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)

    # 备份原始文件
    if args.backup:
        print("\n[BACKUP] 备份原始文件...")
        for version in ['v1', 'v2']:
            config_file = config_dir / f"roi_{version}.json"
            backup_file(config_file)

    # 检查输出目录是否已存在文件
    if output_dir.exists() and not args.force:
        existing_files = list(output_dir.rglob('*_roi.json'))
        if existing_files:
            print(f"\n[WARN] 输出目录已存在 {len(existing_files)} 个配置文件")
            response = input("是否覆盖? (y/N): ")
            if response.lower() != 'y':
                print("[CANCEL] 取消迁移")
                return

    # 执行迁移
    print("\n[START] 开始迁移...")

    success = True
    for version in ['v1', 'v2']:
        config_file = config_dir / f"roi_{version}.json"
        if not migrate_roi_config(config_file, output_dir, version):
            success = False

    # 验证结果
    if args.validate:
        print("\n" + "=" * 60)
        expected_tasks = ['q1', 'q2', 'q3', 'q4', 'q5']

        v1_valid = validate_migration(output_dir, 'v1', expected_tasks)
        v2_valid = validate_migration(output_dir, 'v2', expected_tasks)

        if v1_valid and v2_valid:
            print("\n[SUCCESS] 验证通过！所有配置文件已成功迁移")
        else:
            print("\n[ERROR] 验证失败！请检查错误信息")
            success = False

    # 总结
    print("\n" + "=" * 60)
    if success:
        print("[DONE] 迁移完成！")
        print(f"\n新配置文件位置: {output_dir}")
        print("\n下一步:")
        print("1. 检查生成的配置文件")
        print("2. 更新Module01和ModuleEX使用新配置")
        print("3. 测试数据可视化和ROI配置功能")
    else:
        print("[ERROR] 迁移过程中出现错误，请检查日志")
    print("=" * 60)


if __name__ == '__main__':
    main()
