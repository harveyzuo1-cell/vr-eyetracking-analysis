"""
模拟数据生成器

为测试前端功能生成模拟的眼动追踪数据
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDataGenerator:
    """模拟数据生成器"""

    def __init__(self, output_dir: str):
        """
        初始化生成器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.groups = ['control', 'mci', 'ad']
        self.tasks = ['q1', 'q2', 'q3', 'q4', 'q5']

    def generate_gaze_trajectory(self,
                                 num_points: int = 1000,
                                 pattern: str = 'random_walk',
                                 noise_level: float = 0.02) -> pd.DataFrame:
        """
        生成眼动轨迹数据

        Args:
            num_points: 数据点数量
            pattern: 轨迹模式 ('random_walk', 'scanning', 'fixation')
            noise_level: 噪声水平

        Returns:
            DataFrame with columns: x, y, time
        """
        if pattern == 'random_walk':
            # 随机游走模式（模拟自然眼动）
            x = np.cumsum(np.random.randn(num_points) * 0.02)
            y = np.cumsum(np.random.randn(num_points) * 0.02)

            # 归一化到 [0, 1] 范围
            x = (x - x.min()) / (x.max() - x.min())
            y = (y - y.min()) / (y.max() - y.min())

        elif pattern == 'scanning':
            # 扫描模式（左右扫视）
            t = np.linspace(0, 4 * np.pi, num_points)
            x = (np.sin(t) + 1) / 2
            y = (np.cos(t * 0.5) + 1) / 2

        elif pattern == 'fixation':
            # 注视模式（集中在中心区域）
            center_x, center_y = 0.5, 0.5
            x = center_x + np.random.randn(num_points) * 0.05
            y = center_y + np.random.randn(num_points) * 0.05

        else:
            raise ValueError(f"Unknown pattern: {pattern}")

        # 添加噪声
        x += np.random.randn(num_points) * noise_level
        y += np.random.randn(num_points) * noise_level

        # 限制在 [0, 1] 范围内
        x = np.clip(x, 0, 1)
        y = np.clip(y, 0, 1)

        # 生成时间戳（假设采样率为 60Hz）
        time = np.arange(num_points) * (1000.0 / 60.0)  # 毫秒

        return pd.DataFrame({
            'x': x,
            'y': y,
            'time': time
        })

    def generate_group_data(self,
                           group: str,
                           num_subjects: int = 5,
                           subjects_start_id: int = 1):
        """
        为一个组别生成所有数据

        Args:
            group: 组别名称 ('control', 'mci', 'ad')
            num_subjects: 受试者数量
            subjects_start_id: 受试者ID起始编号
        """
        # 根据组别设置不同的数据特征
        if group == 'control':
            num_points_range = (1500, 2000)
            noise_level = 0.015
            pattern_weights = {'random_walk': 0.4, 'scanning': 0.4, 'fixation': 0.2}
        elif group == 'mci':
            num_points_range = (1200, 1800)
            noise_level = 0.025
            pattern_weights = {'random_walk': 0.5, 'scanning': 0.3, 'fixation': 0.2}
        elif group == 'ad':
            num_points_range = (800, 1500)
            noise_level = 0.035
            pattern_weights = {'random_walk': 0.6, 'scanning': 0.2, 'fixation': 0.2}
        else:
            raise ValueError(f"Unknown group: {group}")

        # 创建组别目录
        group_dir = self.output_dir / group
        group_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"生成 {group} 组数据...")

        # 为每个受试者生成数据
        for i in range(num_subjects):
            subject_id = f"s{subjects_start_id + i:03d}"

            # 为每个任务生成数据
            for task in self.tasks:
                # 随机选择轨迹模式
                pattern = np.random.choice(
                    list(pattern_weights.keys()),
                    p=list(pattern_weights.values())
                )

                # 随机选择数据点数量
                num_points = np.random.randint(*num_points_range)

                # 生成轨迹数据
                df = self.generate_gaze_trajectory(
                    num_points=num_points,
                    pattern=pattern,
                    noise_level=noise_level
                )

                # 保存文件
                filename = f"{group}_{subject_id}_{task}.csv"
                filepath = group_dir / filename
                df.to_csv(filepath, index=False)

                logger.info(f"  生成 {filename} ({num_points} 点, {pattern})")

    def generate_all_data(self):
        """生成所有组别的数据"""
        logger.info("=" * 60)
        logger.info("开始生成模拟数据")
        logger.info("=" * 60)

        # 为每个组别生成数据
        for idx, group in enumerate(self.groups):
            self.generate_group_data(
                group=group,
                num_subjects=5,
                subjects_start_id=idx * 10 + 1  # control: s001-s005, mci: s011-s015, ad: s021-s025
            )

        logger.info("=" * 60)
        logger.info("模拟数据生成完成！")
        logger.info("=" * 60)

        # 统计生成的文件
        total_files = sum(1 for _ in self.output_dir.rglob('*.csv'))
        logger.info(f"总计生成 {total_files} 个CSV文件")

        # 显示目录结构
        logger.info("\n目录结构:")
        for group in self.groups:
            group_dir = self.output_dir / group
            if group_dir.exists():
                file_count = len(list(group_dir.glob('*.csv')))
                logger.info(f"  {group}/: {file_count} 个文件")


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 设置输出目录
    output_dir = project_root / 'data' / '01_raw'

    # 创建生成器并生成数据
    generator = MockDataGenerator(output_dir)
    generator.generate_all_data()


if __name__ == '__main__':
    main()
