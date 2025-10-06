#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景图片导入工具
Background Image Import Tool

用途：
- 从老项目或外部目录导入背景图片到新项目
- 自动检测和验证图片格式
- 按版本组织图片文件（v1/v2）

使用方法：
    python scripts/import_background_images.py --source <源目录> --version <v1/v2>

示例：
    python scripts/import_background_images.py --source "D:/old_project/bg_images" --version v1
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from typing import List, Tuple
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 支持的图片格式
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}

# 预期的任务图片文件名（v1版本）
V1_EXPECTED_FILES = ['Q1.jpg', 'Q2.jpg', 'Q3.jpg', 'Q4.jpg', 'Q5.jpg']

# 预期的任务图片文件名（v2版本）
V2_EXPECTED_FILES = ['Q1.jpg', 'Q2.jpg', 'Q3.jpg', 'Q4.jpg', 'Q5.jpg']


def get_project_root() -> Path:
    """获取项目根目录"""
    # 脚本在 scripts/ 目录下，项目根目录是上一级
    return Path(__file__).parent.parent


def validate_source_directory(source_dir: Path) -> Tuple[bool, str]:
    """
    验证源目录

    Args:
        source_dir: 源目录路径

    Returns:
        (是否有效, 错误消息)
    """
    if not source_dir.exists():
        return False, f"源目录不存在: {source_dir}"

    if not source_dir.is_dir():
        return False, f"路径不是目录: {source_dir}"

    # 检查是否包含图片文件
    image_files = [f for f in source_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS]

    if not image_files:
        return False, f"源目录中没有找到支持的图片文件 {SUPPORTED_FORMATS}"

    return True, ""


def find_image_files(source_dir: Path, version: str) -> List[Path]:
    """
    查找图片文件

    Args:
        source_dir: 源目录
        version: 版本 (v1/v2)

    Returns:
        图片文件路径列表
    """
    expected_files = V1_EXPECTED_FILES if version == 'v1' else V2_EXPECTED_FILES
    found_files = []

    for expected_name in expected_files:
        # 尝试查找文件（不区分大小写）
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.name.lower() == expected_name.lower():
                found_files.append(file_path)
                break
        else:
            # 尝试不同的扩展名
            base_name = Path(expected_name).stem
            for ext in SUPPORTED_FORMATS:
                potential_file = source_dir / f"{base_name}{ext}"
                if potential_file.exists():
                    found_files.append(potential_file)
                    break

    return found_files


def import_images(source_dir: Path, version: str, dry_run: bool = False) -> Tuple[int, int]:
    """
    导入背景图片

    Args:
        source_dir: 源目录
        version: 版本 (v1/v2)
        dry_run: 是否只是模拟运行

    Returns:
        (成功导入数量, 失败数量)
    """
    project_root = get_project_root()
    target_dir = project_root / 'data' / 'background_images' / version

    # 创建目标目录
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"目标目录: {target_dir}")
    else:
        logger.info(f"[模拟] 将创建目标目录: {target_dir}")

    # 查找图片文件
    image_files = find_image_files(source_dir, version)

    if not image_files:
        logger.warning(f"在源目录中没有找到预期的图片文件")
        logger.info(f"预期文件: {V1_EXPECTED_FILES if version == 'v1' else V2_EXPECTED_FILES}")
        return 0, 0

    success_count = 0
    fail_count = 0

    for source_file in image_files:
        try:
            # 目标文件名（统一为 .jpg 扩展名）
            target_name = source_file.stem + '.jpg'
            target_path = target_dir / target_name

            if dry_run:
                logger.info(f"[模拟] {source_file.name} -> {target_path}")
                success_count += 1
            else:
                # 复制文件
                shutil.copy2(source_file, target_path)
                logger.info(f"✓ 导入成功: {source_file.name} -> {target_path.name}")
                success_count += 1

        except Exception as e:
            logger.error(f"✗ 导入失败: {source_file.name} - {str(e)}")
            fail_count += 1

    return success_count, fail_count


def list_existing_images(version: str):
    """列出已存在的背景图片"""
    project_root = get_project_root()
    target_dir = project_root / 'data' / 'background_images' / version

    if not target_dir.exists():
        logger.info(f"目录不存在: {target_dir}")
        return

    image_files = [f for f in target_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS]

    if not image_files:
        logger.info(f"目录中没有图片文件: {target_dir}")
        return

    logger.info(f"\n已存在的背景图片 ({version}):")
    logger.info("=" * 60)
    for img in sorted(image_files):
        size_kb = img.stat().st_size / 1024
        logger.info(f"  - {img.name:20s} ({size_kb:>8.1f} KB)")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='导入背景图片到项目',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 导入v1版本背景图片
  python scripts/import_background_images.py --source "D:/old_project/bg_images" --version v1

  # 模拟导入（不实际复制文件）
  python scripts/import_background_images.py --source "D:/old_project/bg_images" --version v1 --dry-run

  # 列出已存在的背景图片
  python scripts/import_background_images.py --list --version v1
        """
    )

    parser.add_argument(
        '--source', '-s',
        type=str,
        help='源目录路径（包含背景图片的目录）'
    )

    parser.add_argument(
        '--version', '-v',
        type=str,
        choices=['v1', 'v2'],
        required=True,
        help='目标版本 (v1: 旧数据, v2: 新数据)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际复制文件'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出已存在的背景图片'
    )

    args = parser.parse_args()

    # 列出已存在的图片
    if args.list:
        list_existing_images(args.version)
        return 0

    # 导入图片
    if not args.source:
        parser.error("必须指定 --source 参数（源目录）")

    source_dir = Path(args.source)

    # 验证源目录
    is_valid, error_msg = validate_source_directory(source_dir)
    if not is_valid:
        logger.error(error_msg)
        return 1

    logger.info(f"开始导入背景图片...")
    logger.info(f"源目录: {source_dir}")
    logger.info(f"版本: {args.version}")
    logger.info(f"模式: {'模拟运行' if args.dry_run else '实际导入'}")
    logger.info("")

    # 导入图片
    success, fail = import_images(source_dir, args.version, args.dry_run)

    logger.info("")
    logger.info(f"导入完成:")
    logger.info(f"  成功: {success}")
    logger.info(f"  失败: {fail}")

    if not args.dry_run and success > 0:
        logger.info("")
        list_existing_images(args.version)

    return 0 if fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
