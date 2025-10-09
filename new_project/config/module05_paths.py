"""
Module05 RQA分析路径配置
集中管理所有路径构建逻辑，消除硬编码
"""

from pathlib import Path
from typing import Dict
from .settings import Config


class Module05Paths:
    """Module05路径管理器"""

    def __init__(self):
        """初始化路径管理器"""
        self.data_root = Path(Config.DATA_ROOT)

        # 数据目录
        self.processed_dir = self.data_root / '02_processed'
        self.results_dir = self.data_root / '05_rqa_analysis' / 'results'
        self.cache_dir = self.data_root / '05_rqa_analysis' / 'cache'
        self.exports_dir = self.data_root / '05_rqa_analysis' / 'exports'

        # 确保目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保所有必需目录存在"""
        for directory in [self.results_dir, self.cache_dir, self.exports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_param_directory(self, params: Dict) -> Path:
        """
        获取参数组合的结果目录

        Args:
            params: RQA参数 {'m': int, 'tau': int, 'eps': float, 'lmin': int}

        Returns:
            参数目录路径
        """
        from src.modules.module05_rqa_analysis.utils import generate_param_signature
        signature = generate_param_signature(params)
        return self.results_dir / signature

    def get_step_directory(self, params: Dict, step_name: str) -> Path:
        """
        获取指定步骤的目录

        Args:
            params: RQA参数
            step_name: 步骤名称 (如 'step1_rqa_features')

        Returns:
            步骤目录路径
        """
        param_dir = self.get_param_directory(params)
        return param_dir / step_name

    # ========== 标准化文件路径方法 ==========

    def get_step1_rqa_file(self, params: Dict, subject_id: str) -> Path:
        """获取Step1 RQA特征文件路径"""
        step_dir = self.get_step_directory(params, 'step1_rqa_features')
        return step_dir / f"{subject_id}_rqa.csv"

    def get_step2_merged_file(self, params: Dict) -> Path:
        """获取Step2合并特征文件路径"""
        step_dir = self.get_step_directory(params, 'step2_data_merging')
        return step_dir / 'merged_rqa_features.csv'

    def get_step3_enriched_file(self, params: Dict) -> Path:
        """获取Step3增强特征文件路径"""
        step_dir = self.get_step_directory(params, 'step3_feature_enrichment')
        return step_dir / 'enriched_features.csv'

    def get_step4_comparison_file(self, params: Dict) -> Path:
        """获取Step4组间比较文件路径"""
        step_dir = self.get_step_directory(params, 'step4_statistical_analysis')
        return step_dir / 'group_comparison.csv'

    def get_step5_plots_directory(self, params: Dict) -> Path:
        """获取Step5可视化图表目录"""
        step_dir = self.get_step_directory(params, 'step5_visualization')
        return step_dir / 'statistical_plots'

    def get_metadata_file(self, params: Dict) -> Path:
        """获取参数元数据文件路径"""
        param_dir = self.get_param_directory(params)
        return param_dir / 'metadata.json'

    # ========== 校准数据路径 ==========

    def get_calibrated_file(self, group: str, subject_id: str, task_id: str,
                           data_version: str = 'v1') -> Path:
        """
        获取校准后的CSV文件路径

        Args:
            group: 组别 ('control', 'mci', 'ad')
            subject_id: 受试者ID
            task_id: 任务ID
            data_version: 数据版本

        Returns:
            校准文件路径
        """
        return self.processed_dir / group / f'{subject_id}_{task_id}_calibrated.csv'

    def scan_calibrated_files(self, group: str, data_version: str = 'v1') -> list:
        """
        扫描组内所有校准文件

        Args:
            group: 组别
            data_version: 数据版本

        Returns:
            校准文件路径列表
        """
        group_dir = self.processed_dir / group
        if not group_dir.exists():
            return []

        return list(group_dir.glob('*_calibrated.csv'))

    # ========== 缓存路径 ==========

    def get_param_combinations_cache(self) -> Path:
        """获取参数组合缓存文件路径"""
        return self.cache_dir / 'param_combinations.json'

    def get_param_history_cache(self) -> Path:
        """获取参数历史缓存文件路径"""
        return self.cache_dir / 'param_history.json'

    # ========== 导出路径 ==========

    def get_export_file(self, export_id: str, format: str = 'csv') -> Path:
        """
        获取导出文件路径

        Args:
            export_id: 导出ID (时间戳)
            format: 文件格式

        Returns:
            导出文件路径
        """
        return self.exports_dir / f'export_{export_id}.{format}'


# 全局单例实例
_module05_paths_instance = None


def get_module05_paths() -> Module05Paths:
    """
    获取Module05Paths单例实例

    Returns:
        Module05Paths实例
    """
    global _module05_paths_instance
    if _module05_paths_instance is None:
        _module05_paths_instance = Module05Paths()
    return _module05_paths_instance
