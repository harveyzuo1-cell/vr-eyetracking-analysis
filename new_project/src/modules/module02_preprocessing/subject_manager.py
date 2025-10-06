"""
受试者信息管理器

功能:
- 管理受试者基本信息(性别、年龄、受教育程度)
- 管理MMSE评分数据
- 批量导入/导出
- 数据验证
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# 教育程度枚举
EDUCATION_LEVELS = {
    'primary': '小学',
    'junior_high': '初中',
    'senior_high': '高中',
    'vocational': '中专/职高',
    'junior_college': '大专',
    'undergraduate': '本科',
    'postgraduate': '研究生及以上'
}


class SubjectManager:
    """受试者信息管理"""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.subjects_file = self.data_dir / 'subjects.json'
        self._ensure_directories()
        self._init_index_if_needed()

    @staticmethod
    def _sanitize_filename(subject_id: str) -> str:
        """
        清理subject_id以用作安全的文件名

        移除所有Windows和Unix文件系统中的非法字符：
        / \\ : * ? " < > |

        Args:
            subject_id: 原始受试者ID

        Returns:
            安全的文件名
        """
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        safe_id = subject_id
        for char in illegal_chars:
            safe_id = safe_id.replace(char, '_')
        return safe_id

    def _ensure_directories(self):
        """确保目录存在"""
        for group in ['control', 'mci', 'ad']:
            (self.data_dir / group).mkdir(parents=True, exist_ok=True)

    def _init_index_if_needed(self):
        """初始化索引文件(如果不存在)"""
        if not self.subjects_file.exists():
            index = {
                'last_updated': datetime.now().isoformat(),
                'total_subjects': 0,
                'groups': {
                    'control': {'count': 0, 'subjects': []},
                    'mci': {'count': 0, 'subjects': []},
                    'ad': {'count': 0, 'subjects': []}
                }
            }
            with open(self.subjects_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)

    def get_all_subjects(
        self,
        group: Optional[str] = None,
        with_mmse: bool = False,
        data_version: Optional[str] = None
    ) -> List[Dict]:
        """
        获取所有受试者列表

        Args:
            group: 组别筛选 (control/mci/ad)，None表示全部
            with_mmse: 是否包含MMSE信息
            data_version: 数据版本筛选 ('v1'/'v2'/None表示全部)

        Returns:
            受试者列表
        """
        if not self.subjects_file.exists():
            return []

        with open(self.subjects_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        subjects = []
        groups_to_scan = [group] if group else ['control', 'mci', 'ad']

        for grp in groups_to_scan:
            for subject_id in data['groups'].get(grp, {}).get('subjects', []):
                subject_data = self.get_subject(subject_id)
                if subject_data:
                    # 只返回摘要信息
                    summary = {
                        'subject_id': subject_data['subject_id'],
                        'group': subject_data['group'],
                        'demographics': subject_data['demographics'],
                        'task_count': subject_data.get('task_count', 0),
                        'data_version': subject_data.get('data_version', 'v1')
                    }

                    if with_mmse or subject_data.get('mmse'):
                        # 返回完整的MMSE数据（包括所有子题目）
                        summary['mmse'] = subject_data.get('mmse', {})

                    # 添加metadata字段（包含timestamp等）
                    if subject_data.get('metadata'):
                        summary['metadata'] = subject_data['metadata']

                    subjects.append(summary)

        # 版本筛选
        if data_version:
            subjects = [s for s in subjects if s.get('data_version') == data_version]

        return subjects

    def get_subject(self, subject_id: str) -> Optional[Dict]:
        """
        获取单个受试者详细信息

        Args:
            subject_id: 受试者ID

        Returns:
            受试者详细信息，不存在则返回None
        """
        # 确定组别
        group = self._get_group_from_id(subject_id)
        if not group:
            return None

        # 清理subject_id中的非法文件名字符
        safe_subject_id = self._sanitize_filename(subject_id)
        subject_file = self.data_dir / group / f'{safe_subject_id}.json'
        if not subject_file.exists():
            return None

        with open(subject_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_subject(
        self,
        subject_id: str,
        group: str,
        demographics: Dict,
        mmse: Optional[Dict] = None,
        data_version: str = 'v1',
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        创建新受试者

        Args:
            subject_id: 受试者ID
            group: 组别 (control/mci/ad)
            demographics: 人口学信息 {gender, age, education_level}
            mmse: MMSE评分 (可选)
            data_version: 数据版本 ('v1'/'v2'，默认'v1')
            metadata: 元数据 (可选，包含timestamp、data_path等)

        Returns:
            创建的受试者信息
        """
        # 验证数据
        errors = self.validate_subject_data({
            'subject_id': subject_id,
            'group': group,
            'demographics': demographics,
            'mmse': mmse
        })

        if errors:
            raise ValueError(f"数据验证失败: {', '.join(errors)}")

        subject_data = {
            'subject_id': subject_id,
            'group': group,
            'demographics': demographics,
            'mmse': mmse,
            'data_version': data_version,
            'task_count': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        # 保存受试者文件
        safe_subject_id = self._sanitize_filename(subject_id)
        group_dir = self.data_dir / group
        group_dir.mkdir(parents=True, exist_ok=True)  # 确保组目录存在
        subject_file = group_dir / f'{safe_subject_id}.json'

        logger.debug(f"Creating subject file: {subject_file}")
        with open(subject_file, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

        # 更新主索引
        self._update_index(subject_id, group, action='add')

        return subject_data

    def update_subject(self, subject_id: str, demographics: Optional[Dict] = None, mmse: Optional[Dict] = None) -> Optional[Dict]:
        """
        更新受试者信息

        Args:
            subject_id: 受试者ID
            demographics: 人口学信息 (可选)
            mmse: MMSE评分 (可选)

        Returns:
            更新后的受试者信息，不存在则返回None
        """
        subject_data = self.get_subject(subject_id)
        if not subject_data:
            return None

        if demographics:
            # Merge demographics instead of replacing
            subject_data['demographics'].update(demographics)

        if mmse is not None:
            # Allow explicit None to clear MMSE, otherwise merge
            if isinstance(mmse, dict):
                if subject_data.get('mmse'):
                    subject_data['mmse'].update(mmse)
                else:
                    subject_data['mmse'] = mmse
            else:
                subject_data['mmse'] = mmse

        subject_data['updated_at'] = datetime.now().isoformat()

        # 验证数据
        errors = self.validate_subject_data(subject_data)
        if errors:
            raise ValueError(f"数据验证失败: {', '.join(errors)}")

        # 保存
        group = subject_data['group']
        safe_subject_id = self._sanitize_filename(subject_id)
        subject_file = self.data_dir / group / f'{safe_subject_id}.json'
        with open(subject_file, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

        return subject_data

    def delete_subject(self, subject_id: str) -> bool:
        """
        删除受试者

        Args:
            subject_id: 受试者ID

        Returns:
            是否删除成功
        """
        subject_data = self.get_subject(subject_id)
        if not subject_data:
            return False

        group = subject_data['group']
        safe_subject_id = self._sanitize_filename(subject_id)
        subject_file = self.data_dir / group / f'{safe_subject_id}.json'

        # 删除文件
        subject_file.unlink()

        # 更新索引
        self._update_index(subject_id, group, action='remove')

        return True

    def rename_subject(self, old_id: str, new_id: str) -> bool:
        """
        重命名受试者ID

        Args:
            old_id: 原受试者ID
            new_id: 新受试者ID

        Returns:
            是否重命名成功
        """
        # 检查旧ID是否存在
        subject_data = self.get_subject(old_id)
        if not subject_data:
            raise ValueError(f"受试者 {old_id} 不存在")

        # 检查新ID是否已存在
        if self.get_subject(new_id):
            raise ValueError(f"受试者 {new_id} 已存在")

        group = subject_data['group']

        # 更新受试者数据中的ID
        subject_data['subject_id'] = new_id

        # 如果有metadata，保留原始ID信息
        if 'metadata' not in subject_data:
            subject_data['metadata'] = {}
        subject_data['metadata']['original_id'] = old_id
        subject_data['updated_at'] = datetime.now().isoformat()

        # 删除旧文件
        old_safe_id = self._sanitize_filename(old_id)
        old_file = self.data_dir / group / f'{old_safe_id}.json'
        if old_file.exists():
            old_file.unlink()

        # 创建新文件
        new_safe_id = self._sanitize_filename(new_id)
        new_file = self.data_dir / group / f'{new_safe_id}.json'
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

        # 更新索引
        self._update_index(old_id, group, action='remove')
        self._update_index(new_id, group, action='add')

        logger.info(f"Renamed subject: {old_id} -> {new_id}")
        return True

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        try:
            subjects = self.get_all_subjects(with_mmse=True)
            logger.info(f"Calculating statistics for {len(subjects)} subjects")
        except Exception as e:
            logger.error(f"Failed to load subjects for statistics: {str(e)}", exc_info=True)
            raise

        stats = {
            'total_subjects': len(subjects),
            'by_group': {'control': 0, 'mci': 0, 'ad': 0},
            'by_gender': {'male': 0, 'female': 0},
            'by_education': {level: 0 for level in EDUCATION_LEVELS.keys()},
            'age_distribution': {
                '<60': 0,
                '60-69': 0,
                '70-79': 0,
                '>=80': 0
            },
            'mmse_distribution': {
                'not_tested': 0,
                'severe': 0,      # <18
                'moderate': 0,     # 18-23
                'normal': 0        # >=24
            }
        }

        for subject in subjects:
            # Skip None subjects (file read failures)
            if subject is None:
                continue

            # 按组别统计
            group = subject.get('group')
            if group in stats['by_group']:
                stats['by_group'][group] += 1

            # 按性别统计
            gender = subject['demographics'].get('gender')
            if gender in stats['by_gender']:
                stats['by_gender'][gender] += 1

            # 按教育程度统计
            education = subject['demographics'].get('education_level')
            if education in stats['by_education']:
                stats['by_education'][education] += 1

            # 按年龄统计
            age = subject['demographics'].get('age')
            if age is not None and isinstance(age, (int, float)):
                if age < 60:
                    stats['age_distribution']['<60'] += 1
                elif age < 70:
                    stats['age_distribution']['60-69'] += 1
                elif age < 80:
                    stats['age_distribution']['70-79'] += 1
                else:
                    stats['age_distribution']['>=80'] += 1

            # 按MMSE统计
            mmse_data = subject.get('mmse')
            if mmse_data is None or not isinstance(mmse_data, dict):
                mmse_score = None
            else:
                mmse_score = mmse_data.get('total_score')

            if mmse_score is None:
                stats['mmse_distribution']['not_tested'] += 1
            elif mmse_score < 18:
                stats['mmse_distribution']['severe'] += 1
            elif mmse_score < 24:
                stats['mmse_distribution']['moderate'] += 1
            else:
                stats['mmse_distribution']['normal'] += 1

        return stats

    def _get_group_from_id(self, subject_id: str) -> Optional[str]:
        """从ID推断组别"""
        # 首先尝试从索引文件查找
        if self.subjects_file.exists():
            with open(self.subjects_file, 'r', encoding='utf-8') as f:
                index = json.load(f)

            for group in ['control', 'mci', 'ad']:
                if subject_id in index['groups'][group]['subjects']:
                    return group

        # 如果索引中找不到,尝试从ID前缀推断
        subject_id_lower = subject_id.lower()
        if subject_id_lower.startswith('control') or subject_id_lower.startswith('n'):
            return 'control'
        elif subject_id_lower.startswith('mci') or subject_id_lower.startswith('m'):
            return 'mci'
        elif subject_id_lower.startswith('ad') or subject_id_lower.startswith('a'):
            return 'ad'
        return None

    def _update_index(self, subject_id: str, group: str, action: str = 'add'):
        """更新主索引文件"""
        # 读取现有索引
        with open(self.subjects_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        # 更新索引
        if action == 'add':
            if subject_id not in index['groups'][group]['subjects']:
                index['groups'][group]['subjects'].append(subject_id)
                index['groups'][group]['count'] += 1
                index['total_subjects'] += 1
        elif action == 'remove':
            if subject_id in index['groups'][group]['subjects']:
                index['groups'][group]['subjects'].remove(subject_id)
                index['groups'][group]['count'] -= 1
                index['total_subjects'] -= 1

        index['last_updated'] = datetime.now().isoformat()

        # 保存索引
        with open(self.subjects_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    @staticmethod
    def validate_subject_data(data: Dict) -> List[str]:
        """
        验证受试者数据

        Args:
            data: 受试者数据

        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []

        # 验证subject_id
        if not data.get('subject_id'):
            errors.append('缺少subject_id')

        # 验证group
        if data.get('group') not in ['control', 'mci', 'ad']:
            errors.append('无效的group值，必须是control/mci/ad之一')

        # 验证demographics（允许字段为空或None，V2数据可能缺失这些信息）
        demographics = data.get('demographics', {})

        # 只在有值时验证gender
        gender = demographics.get('gender')
        if gender is not None and gender not in ['male', 'female', 'N/A', '']:
            errors.append('无效的性别，必须是male或female')

        # 只在有值时验证age
        age = demographics.get('age')
        if age is not None and age != 'N/A' and age != '':
            if not isinstance(age, int) or not (0 <= age <= 120):
                errors.append('年龄必须是0-120之间的整数')

        # 只在有值时验证education_level
        education_level = demographics.get('education_level')
        if education_level is not None and education_level not in EDUCATION_LEVELS and education_level not in ['N/A', '']:
            errors.append(f'无效的受教育程度，必须是: {", ".join(EDUCATION_LEVELS.keys())}')

        # 验证MMSE（简化版，满分21分）
        # q1_weekday和q2_province各2分，其他单选题1分，q3_immediate可得0-3分
        if 'mmse' in data and data['mmse']:
            mmse = data['mmse']
            total_score = mmse.get('total_score')
            if total_score is not None and (not isinstance(total_score, int) or not (0 <= total_score <= 21)):
                errors.append('MMSE总分必须是0-21之间的整数')

            # 验证各题得分
            # q1_weekday和q2_province特殊：值为1时得2分，值为0时得0分
            # 其他单选题：值为0或1
            # q3_immediate特殊：可以得0-3分
            question_fields_1pt = [
                'q1_year', 'q1_season', 'q1_month',  # Q1前3题：各1分
                'q2_street', 'q2_building', 'q2_floor',  # Q2后3题：各1分
                'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',  # Q4: 各1分
                'q5_word1', 'q5_word2', 'q5_word3'  # Q5: 各1分
            ]
            question_fields_2pt = ['q1_weekday', 'q2_province']  # 特殊题目：各2分

            for field in question_fields_1pt:
                if field in mmse:
                    score = mmse[field]
                    if not isinstance(score, int) or score not in [0, 1]:
                        errors.append(f'{field}得分必须是0或1')

            for field in question_fields_2pt:
                if field in mmse:
                    score = mmse[field]
                    if not isinstance(score, int) or score not in [0, 2]:
                        errors.append(f'{field}得分必须是0或2')

            if 'q3_immediate' in mmse:
                score = mmse['q3_immediate']
                if not isinstance(score, int) or not (0 <= score <= 3):
                    errors.append('q3_immediate得分范围: 0-3')

        return errors
