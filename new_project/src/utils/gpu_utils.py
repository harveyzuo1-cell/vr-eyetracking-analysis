"""
GPU工具

提供GPU检测和管理功能
"""
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class GPUUtils:
    """GPU工具类"""

    _gpu_available = None
    _cupy_module = None

    @classmethod
    def is_gpu_available(cls) -> bool:
        """
        检查GPU是否可用

        Returns:
            bool: GPU是否可用
        """
        if cls._gpu_available is not None:
            return cls._gpu_available

        try:
            import cupy as cp
            cls._cupy_module = cp
            cls._gpu_available = True
            logger.info("✓ GPU可用 (CuPy)")
            return True
        except ImportError:
            cls._gpu_available = False
            logger.warning("✗ GPU不可用 (CuPy未安装)")
            return False
        except Exception as e:
            cls._gpu_available = False
            logger.warning(f"✗ GPU不可用: {str(e)}")
            return False

    @classmethod
    def get_cupy(cls):
        """
        获取CuPy模块

        Returns:
            module: CuPy模块，如果不可用则返回None
        """
        if cls._cupy_module is None:
            cls.is_gpu_available()
        return cls._cupy_module

    @classmethod
    def get_gpu_info(cls) -> Optional[Dict]:
        """
        获取GPU信息

        Returns:
            Dict: GPU信息字典，如果不可用则返回None
        """
        if not cls.is_gpu_available():
            return None

        try:
            cp = cls.get_cupy()
            device = cp.cuda.Device()

            info = {
                'device_id': device.id,
                'device_name': device.compute_capability,
                'total_memory': device.mem_info[1],
                'free_memory': device.mem_info[0],
                'used_memory': device.mem_info[1] - device.mem_info[0],
            }

            logger.debug(f"GPU信息: {info}")
            return info

        except Exception as e:
            logger.error(f"获取GPU信息失败: {str(e)}")
            return None

    @classmethod
    def format_memory_size(cls, size_bytes: int) -> str:
        """
        格式化内存大小

        Args:
            size_bytes: 字节数

        Returns:
            str: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    @classmethod
    def log_gpu_status(cls):
        """记录GPU状态到日志"""
        if cls.is_gpu_available():
            info = cls.get_gpu_info()
            if info:
                total_mem = cls.format_memory_size(info['total_memory'])
                free_mem = cls.format_memory_size(info['free_memory'])
                used_mem = cls.format_memory_size(info['used_memory'])

                logger.info(f"GPU状态:")
                logger.info(f"  设备ID: {info['device_id']}")
                logger.info(f"  总内存: {total_mem}")
                logger.info(f"  已用内存: {used_mem}")
                logger.info(f"  可用内存: {free_mem}")
        else:
            logger.warning("GPU不可用，将使用CPU模式")

    @classmethod
    def to_gpu(cls, array):
        """
        将数组转移到GPU

        Args:
            array: NumPy数组或CuPy数组

        Returns:
            CuPy数组或NumPy数组（如果GPU不可用）
        """
        if not cls.is_gpu_available():
            return array

        cp = cls.get_cupy()
        try:
            if isinstance(array, cp.ndarray):
                return array
            else:
                return cp.asarray(array)
        except Exception as e:
            logger.warning(f"转移到GPU失败: {str(e)}, 使用CPU模式")
            return array

    @classmethod
    def to_cpu(cls, array):
        """
        将数组转移到CPU

        Args:
            array: CuPy数组或NumPy数组

        Returns:
            NumPy数组
        """
        if not cls.is_gpu_available():
            return array

        cp = cls.get_cupy()
        try:
            if isinstance(array, cp.ndarray):
                return cp.asnumpy(array)
            else:
                return array
        except Exception as e:
            logger.warning(f"转移到CPU失败: {str(e)}")
            return array

    @classmethod
    def clear_memory(cls):
        """清理GPU内存"""
        if not cls.is_gpu_available():
            return

        try:
            cp = cls.get_cupy()
            mempool = cp.get_default_memory_pool()
            mempool.free_all_blocks()
            logger.debug("GPU内存已清理")
        except Exception as e:
            logger.warning(f"清理GPU内存失败: {str(e)}")
