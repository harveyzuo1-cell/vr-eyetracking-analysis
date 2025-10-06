"""
MMSE数据加载器

从Legacy项目的MMSE CSV文件中读取MMSE评分数据
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class MMSELoader:
    """MMSE数据加载器"""

    # Legacy MMSE ID到新系统subject_id的映射规则
    ID_MAPPING = {
        'control': lambda n: f'control_legacy_{n}',  # n01 -> control_legacy_1
        'mci': lambda n: f'mci_legacy_{n}',          # M01 -> mci_legacy_1
        'ad': lambda n: f'ad_legacy_{n}'             # ad01 -> ad_legacy_1
    }

    # MMSE CSV列名定义
    MMSE_COLUMNS = {
        '受试者': 'subject_id',
        '年份': 'q1_year',
        '季节': 'q1_season',
        '月份': 'q1_month',
        '星期': 'q1_weekday',
        '省市区': 'q2_province',
        '街道': 'q2_street',
        '建筑': 'q2_building',
        '楼层': 'q2_floor',
        '即刻记忆': 'q3_immediate',
        '100-7': 'q4_100_7',
        '93-7': 'q4_93_7',
        '86-7': 'q4_86_7',
        '79-7': 'q4_79_7',
        '72-7': 'q4_72_7',
        '词1': 'q5_word1',
        '词2': 'q5_word2',
        '词3': 'q5_word3',
        '总分': 'total_score'
    }

    def __init__(self, legacy_mmse_dir: Optional[str] = None):
        """
        初始化MMSE加载器

        Args:
            legacy_mmse_dir: Legacy MMSE数据目录路径,默认为data/MMSE_Score/
        """
        if legacy_mmse_dir is None:
            # 默认使用旧项目的MMSE_Score目录 (在new_project的父目录)
            new_project_root = Path(__file__).parent.parent.parent.parent.parent.parent
            old_project_root = new_project_root.parent  # 上一级到 "az - 副本 (11)"
            legacy_mmse_dir = old_project_root / "data" / "MMSE_Score"

        self.legacy_mmse_dir = Path(legacy_mmse_dir)
        logger.info(f"MMSELoader initialized with directory: {self.legacy_mmse_dir}")

    def load_legacy_mmse(self) -> Dict[str, Dict]:
        """
        加载所有Legacy MMSE数据

        Returns:
            {
                "control_legacy_1": {
                    "subject_id": "control_legacy_1",
                    "group": "control",
                    "data_version": "v1",
                    "q1_year": 1, "q1_season": 1, ...,
                    "total_score": 21,
                    "import_date": "2025-10-02T10:40:00"
                },
                ...
            }
        """
        all_mmse_data = {}

        # 定义三个组的CSV文件名
        group_files = {
            'control': '控制组.csv',
            'mci': '轻度认知障碍组.csv',
            'ad': '阿尔兹海默症组.csv'
        }

        for group, filename in group_files.items():
            file_path = self.legacy_mmse_dir / filename
            if not file_path.exists():
                logger.warning(f"MMSE file not found: {file_path}")
                continue

            try:
                # 读取CSV文件
                df = pd.read_csv(file_path, encoding='utf-8-sig')  # utf-8-sig处理BOM
                logger.info(f"Loaded {len(df)} MMSE records from {filename}")

                # 处理每一行数据
                for _, row in df.iterrows():
                    mmse_record = self._parse_mmse_record(row, group)
                    if mmse_record:
                        subject_id = mmse_record['subject_id']
                        all_mmse_data[subject_id] = mmse_record

            except Exception as e:
                logger.error(f"Failed to load MMSE file {filename}: {e}", exc_info=True)

        logger.info(f"Loaded total {len(all_mmse_data)} MMSE records")
        return all_mmse_data

    def _parse_mmse_record(self, row: pd.Series, group: str) -> Optional[Dict]:
        """
        解析单条MMSE记录

        Args:
            row: CSV行数据
            group: 组别(control/mci/ad)

        Returns:
            MMSE记录字典,解析失败返回None
        """
        try:
            # 提取原始受试者ID (如 n01, M01, ad01)
            # 使用iloc[0]而不是列名,避免编码问题
            raw_subject_id = str(row.iloc[0]).strip()

            # 跳过无效行(平均、标准差、nan等统计行)
            if raw_subject_id in ['nan', '平均', '标准差', ''] or pd.isna(row.iloc[0]):
                return None

            # 转换为新系统的subject_id
            subject_id = self._convert_subject_id(raw_subject_id, group)
            if not subject_id:
                logger.warning(f"Invalid subject_id: {raw_subject_id} for group {group}")
                return None

            # 构建MMSE记录
            mmse_record = {
                'subject_id': subject_id,
                'group': group,
                'data_version': 'v1',
                'source': 'legacy_csv',
                'raw_id': raw_subject_id
            }

            # 添加所有MMSE字段
            # 使用列索引而不是列名,避免编码问题
            # CSV列顺序: 受试者,年份,季节,月份,星期,省市区,街道,建筑,楼层,即刻记忆,100-7,93-7,86-7,79-7,72-7,词1,词2,词3,总分
            column_indices = {
                'q1_year': 1, 'q1_season': 2, 'q1_month': 3, 'q1_weekday': 4,
                'q2_province': 5, 'q2_street': 6, 'q2_building': 7, 'q2_floor': 8,
                'q3_immediate': 9,
                'q4_100_7': 10, 'q4_93_7': 11, 'q4_86_7': 12, 'q4_79_7': 13, 'q4_72_7': 14,
                'q5_word1': 15, 'q5_word2': 16, 'q5_word3': 17,
                'total_score': 18
            }

            for english_col, col_idx in column_indices.items():
                value = row.iloc[col_idx]
                # 转换为整数(如果可能)
                try:
                    mmse_record[english_col] = int(value) if pd.notna(value) else None
                except (ValueError, TypeError):
                    mmse_record[english_col] = value

            return mmse_record

        except Exception as e:
            logger.error(f"Failed to parse MMSE record: {e}", exc_info=True)
            return None

    def _convert_subject_id(self, raw_id: str, group: str) -> Optional[str]:
        """
        将Legacy ID转换为新系统subject_id

        Args:
            raw_id: 原始ID (n01, M01, ad01)
            group: 组别

        Returns:
            新系统subject_id (control_legacy_1, mci_legacy_1, ad_legacy_1)
        """
        try:
            # 提取数字部分
            if raw_id.startswith('n'):
                # n01 -> 1
                num = int(raw_id[1:])
            elif raw_id.startswith('M'):
                # M01 -> 1
                num = int(raw_id[1:])
            elif raw_id.startswith('ad'):
                # ad01 -> 1
                num = int(raw_id[2:])
            else:
                logger.warning(f"Unknown ID format: {raw_id}")
                return None

            # 使用映射规则生成新ID
            mapper = self.ID_MAPPING.get(group)
            if mapper:
                return mapper(num)
            else:
                logger.warning(f"Unknown group: {group}")
                return None

        except (ValueError, IndexError) as e:
            logger.error(f"Failed to convert subject_id {raw_id}: {e}")
            return None

    def get_mmse_for_subject(self, subject_id: str) -> Optional[Dict]:
        """
        获取指定受试者的MMSE数据

        Args:
            subject_id: 受试者ID

        Returns:
            MMSE数据字典,如果不存在返回None
        """
        all_mmse = self.load_legacy_mmse()
        return all_mmse.get(subject_id)

    def get_statistics(self) -> Dict:
        """
        获取MMSE数据统计信息

        Returns:
            {
                "total": 60,
                "by_group": {
                    "control": 20,
                    "mci": 20,
                    "ad": 20
                },
                "missing": ["control_legacy_21", "control_legacy_22", ...]
            }
        """
        all_mmse = self.load_legacy_mmse()

        # 按组统计
        by_group = {'control': 0, 'mci': 0, 'ad': 0}
        for subject_id in all_mmse.keys():
            if subject_id.startswith('control_'):
                by_group['control'] += 1
            elif subject_id.startswith('mci_'):
                by_group['mci'] += 1
            elif subject_id.startswith('ad_'):
                by_group['ad'] += 1

        # 检测缺失的受试者(假设每组应有22/22/21人)
        missing = []
        expected_counts = {'control': 22, 'mci': 22, 'ad': 21}

        for group, expected in expected_counts.items():
            mapper = self.ID_MAPPING[group]
            for i in range(1, expected + 1):
                expected_id = mapper(i)
                if expected_id not in all_mmse:
                    missing.append(expected_id)

        return {
            'total': len(all_mmse),
            'by_group': by_group,
            'missing': missing,
            'missing_count': len(missing)
        }
