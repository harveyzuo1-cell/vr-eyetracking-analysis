"""
文件操作工具

提供统一的文件操作接口
"""
import os
import shutil
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileUtils:
    """文件操作工具类"""

    @staticmethod
    def ensure_dir(path: Path) -> None:
        """
        确保目录存在，不存在则创建

        Args:
            path: 目录路径
        """
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"确保目录存在: {path}")

    @staticmethod
    def list_files(
        directory: Path,
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索

        Returns:
            List[Path]: 文件路径列表
        """
        if not directory.exists():
            logger.warning(f"目录不存在: {directory}")
            return []

        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        # 只返回文件，不包括目录
        files = [f for f in files if f.is_file()]

        logger.debug(f"找到 {len(files)} 个文件在 {directory}")
        return files

    @staticmethod
    def read_csv(
        file_path: Path,
        encoding: str = 'utf-8'
    ) -> List[Dict[str, Any]]:
        """
        读取CSV文件

        Args:
            file_path: CSV文件路径
            encoding: 文件编码

        Returns:
            List[Dict]: CSV数据（每行一个字典）
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                data = list(reader)

            logger.debug(f"读取CSV文件: {file_path.name}, {len(data)} 行")
            return data

        except Exception as e:
            logger.error(f"读取CSV失败: {file_path}, 错误: {str(e)}")
            raise

    @staticmethod
    def write_csv(
        file_path: Path,
        data: List[Dict[str, Any]],
        encoding: str = 'utf-8'
    ) -> None:
        """
        写入CSV文件

        Args:
            file_path: CSV文件路径
            data: 要写入的数据
            encoding: 文件编码
        """
        if not data:
            logger.warning(f"数据为空，不写入文件: {file_path}")
            return

        try:
            # 确保目录存在
            FileUtils.ensure_dir(file_path.parent)

            # 获取字段名
            fieldnames = list(data[0].keys())

            with open(file_path, 'w', encoding=encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"写入CSV文件: {file_path.name}, {len(data)} 行")

        except Exception as e:
            logger.error(f"写入CSV失败: {file_path}, 错误: {str(e)}")
            raise

    @staticmethod
    def read_json(
        file_path: Path,
        encoding: str = 'utf-8'
    ) -> Dict[str, Any]:
        """
        读取JSON文件

        Args:
            file_path: JSON文件路径
            encoding: 文件编码

        Returns:
            Dict: JSON数据
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)

            logger.debug(f"读取JSON文件: {file_path.name}")
            return data

        except Exception as e:
            logger.error(f"读取JSON失败: {file_path}, 错误: {str(e)}")
            raise

    @staticmethod
    def write_json(
        file_path: Path,
        data: Dict[str, Any],
        encoding: str = 'utf-8',
        indent: int = 2
    ) -> None:
        """
        写入JSON文件

        Args:
            file_path: JSON文件路径
            data: 要写入的数据
            encoding: 文件编码
            indent: 缩进空格数
        """
        try:
            # 确保目录存在
            FileUtils.ensure_dir(file_path.parent)

            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)

            logger.info(f"写入JSON文件: {file_path.name}")

        except Exception as e:
            logger.error(f"写入JSON失败: {file_path}, 错误: {str(e)}")
            raise

    @staticmethod
    def copy_file(src: Path, dst: Path) -> None:
        """
        复制文件

        Args:
            src: 源文件路径
            dst: 目标文件路径
        """
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        try:
            # 确保目标目录存在
            FileUtils.ensure_dir(dst.parent)

            shutil.copy2(src, dst)
            logger.info(f"复制文件: {src.name} -> {dst}")

        except Exception as e:
            logger.error(f"复制文件失败: {src} -> {dst}, 错误: {str(e)}")
            raise

    @staticmethod
    def move_file(src: Path, dst: Path) -> None:
        """
        移动文件

        Args:
            src: 源文件路径
            dst: 目标文件路径
        """
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        try:
            # 确保目标目录存在
            FileUtils.ensure_dir(dst.parent)

            shutil.move(str(src), str(dst))
            logger.info(f"移动文件: {src.name} -> {dst}")

        except Exception as e:
            logger.error(f"移动文件失败: {src} -> {dst}, 错误: {str(e)}")
            raise

    @staticmethod
    def delete_file(file_path: Path) -> None:
        """
        删除文件

        Args:
            file_path: 文件路径
        """
        if not file_path.exists():
            logger.warning(f"文件不存在，无需删除: {file_path}")
            return

        try:
            file_path.unlink()
            logger.info(f"删除文件: {file_path.name}")

        except Exception as e:
            logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")
            raise

    @staticmethod
    def backup_file(file_path: Path, backup_dir: Optional[Path] = None) -> Path:
        """
        备份文件

        Args:
            file_path: 要备份的文件路径
            backup_dir: 备份目录，默认为文件所在目录

        Returns:
            Path: 备份文件路径
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 确定备份目录
            if backup_dir is None:
                backup_dir = file_path.parent
            else:
                FileUtils.ensure_dir(backup_dir)

            # 生成备份文件名（添加时间戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name

            # 复制文件
            shutil.copy2(file_path, backup_path)
            logger.info(f"备份文件: {file_path.name} -> {backup_name}")

            return backup_path

        except Exception as e:
            logger.error(f"备份文件失败: {file_path}, 错误: {str(e)}")
            raise

    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """
        获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            int: 文件大小（字节）
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        return file_path.stat().st_size

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        格式化文件大小

        Args:
            size_bytes: 文件大小（字节）

        Returns:
            str: 格式化后的大小（如 "1.5 MB"）
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
