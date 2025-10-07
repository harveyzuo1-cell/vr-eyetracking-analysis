"""
V2格式眼动数据管理器

负责V2版本眼动数据的扫描、导入、ID规范化
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class V2DataManager:
    """V2格式眼动数据管理器"""

    def __init__(self, data_dir: Path, subject_manager):
        """
        初始化V2数据管理器

        Args:
            data_dir: 数据根目录
            subject_manager: SubjectManager实例
        """
        self.data_dir = Path(data_dir)
        self.subject_manager = subject_manager
        self.v2_scan_dir = self.data_dir / 'v2_raw_data'  # V2原始数据扫描目录

        logger.info(f"初始化V2数据管理器: {self.v2_scan_dir}")

    def normalize_v2_subject_ids(
        self,
        v2_subjects: List[Dict],
        preview_only: bool = False
    ) -> Dict[str, str]:
        """
        为V2受试者生成规范ID

        ID格式: v2_{group}_{序号}
        例如: v2_control_001, v2_mci_002, v2_ad_003

        Args:
            v2_subjects: 扫描到的V2受试者列表
            preview_only: 仅预览，不真正分配（用于显示给用户）

        Returns:
            ID映射字典 {旧ID: 新ID}
            例: {'N_01': 'v2_control_001', 'M_03': 'v2_mci_001'}
        """
        logger.info(f"开始为 {len(v2_subjects)} 个V2受试者生成规范ID...")

        # 获取已存在的V2受试者，统计每组最大序号
        existing_subjects = self.subject_manager.get_all_subjects(data_version='v2')

        max_seq = {'control': 0, 'mci': 0, 'ad': 0}

        for subject in existing_subjects:
            # 解析已有ID，提取序号
            # v2_control_005 -> group=control, seq=5
            match = re.match(r'v2_(\w+)_(\d+)', subject['subject_id'])
            if match:
                group, seq = match.groups()
                if group in max_seq:
                    max_seq[group] = max(max_seq[group], int(seq))

        logger.debug(f"当前各组最大序号: {max_seq}")

        # 为新导入的V2受试者分配ID
        # 重要：使用 subject_id||timestamp 作为映射键，因为同一受试者可能有多次实验
        id_mapping = {}
        group_counters = max_seq.copy()

        for v2_subject in v2_subjects:
            old_id = v2_subject['subject_id']
            timestamp = v2_subject.get('timestamp', '')
            group = v2_subject['group']

            if group not in group_counters:
                logger.warning(f"未知组别: {group}, 跳过")
                continue

            # 递增序号
            group_counters[group] += 1
            seq = group_counters[group]

            # 生成新ID
            new_id = f"v2_{group}_{seq:03d}"

            # 使用 原始ID||时间戳 作为映射键，确保每条记录有唯一ID
            mapping_key = f"{old_id}||{timestamp}"
            id_mapping[mapping_key] = new_id

        logger.info(f"ID映射生成完成，共 {len(id_mapping)} 个")
        return id_mapping

    def batch_import_v2_subjects(
        self,
        v2_subjects: List[Dict],
        rename: bool = True,
        dry_run: bool = False
    ) -> Dict:
        """
        批量导入V2受试者

        Args:
            v2_subjects: V2受试者列表 [
                {
                    'subject_id': 'N_01',
                    'group': 'control',
                    'name': '张三',
                    'hospital_id': 'H001',
                    'timestamp': '2024-01-01 10:30:00'
                },
                ...
            ]
            rename: 是否自动重命名为规范ID
            dry_run: 试运行模式，仅返回映射不实际导入

        Returns:
            {
                'imported': 10,
                'failed': 0,
                'skipped': 0,
                'id_mapping': {'N_01': 'v2_control_001', ...},
                'errors': []
            }
        """
        logger.info(f"开始批量导入V2受试者，共 {len(v2_subjects)} 个，重命名={rename}，试运行={dry_run}")

        # 去重：按(subject_id + timestamp)去重，因为同一受试者可能有多次实验记录
        # 使用subject_id + timestamp作为唯一键
        seen_keys = set()
        unique_subjects = []
        for subj in v2_subjects:
            sid = subj['subject_id']
            timestamp = subj.get('timestamp', '')
            unique_key = f"{sid}||{timestamp}"

            if unique_key not in seen_keys:
                seen_keys.add(unique_key)
                unique_subjects.append(subj)
            else:
                logger.debug(f"跳过真正重复的记录: {sid} @ {timestamp}")

        if len(unique_subjects) < len(v2_subjects):
            logger.info(f"去重后剩余 {len(unique_subjects)} 条唯一记录（原始 {len(v2_subjects)} 条）")

        v2_subjects = unique_subjects  # 使用去重后的列表

        results = {
            'imported': 0,
            'failed': 0,
            'skipped': 0,
            'id_mapping': {},
            'errors': []
        }

        # 生成ID映射
        if rename:
            results['id_mapping'] = self.normalize_v2_subject_ids(v2_subjects)
            logger.info(f"ID映射: {results['id_mapping']}")
        else:
            # 不重命名，使用原ID
            results['id_mapping'] = {s['subject_id']: s['subject_id'] for s in v2_subjects}

        # 试运行模式，仅返回映射
        if dry_run:
            logger.info("试运行模式，不实际导入")
            return results

        # 逐个导入
        for v2_subject in v2_subjects:
            old_id = v2_subject['subject_id']
            timestamp = v2_subject.get('timestamp', '')
            mapping_key = f"{old_id}||{timestamp}"

            # 使用映射键获取新ID
            new_id = results['id_mapping'].get(mapping_key)

            if not new_id:
                logger.warning(f"无法获取新ID: {mapping_key}，跳过")
                results['skipped'] += 1
                continue

            # 检查是否已存在（检查新ID或通过timestamp查找）
            existing = self.subject_manager.get_subject(new_id)

            # 如果新ID不存在，检查是否有其他受试者使用了相同timestamp（防止重复导入）
            # 注意：timestamp在V2数据中是唯一的（每次实验有唯一的时间戳）
            if not existing and timestamp:
                # 检查所有V2受试者（不限group，因为timestamp全局唯一）
                all_v2_subjects = self.subject_manager.get_all_subjects(data_version='v2')
                for subj in all_v2_subjects:
                    meta = subj.get('metadata', {})
                    existing_timestamp = meta.get('timestamp', '')

                    # 只要timestamp相同，就认为是重复记录
                    if existing_timestamp == timestamp:
                        existing = subj
                        logger.info(f"发现已存在的记录（相同timestamp）: {timestamp} -> {subj['subject_id']}")
                        break

            if existing:
                logger.warning(f"受试者已存在: {old_id}@{timestamp} -> {existing['subject_id']}，跳过")
                results['skipped'] += 1
                results['errors'].append({
                    'subject_id': old_id,
                    'timestamp': timestamp,
                    'new_id': existing['subject_id'],
                    'error': '受试者已存在（timestamp重复）'
                })
                continue

            try:
                # V2数据任务验证：确定tasks_available
                # V2数据使用 level_1 ~ level_5 命名
                tasks_available = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5']

                # 如果提供了data_path，验证文件完整性
                data_path = v2_subject.get('data_path', '')
                if data_path:
                    from pathlib import Path as PathLib
                    data_dir = PathLib(data_path)

                    if data_dir.exists():
                        # 检查哪些level文件实际存在
                        available_tasks = []
                        for level in range(1, 6):
                            level_file = data_dir / f'level_{level}.txt'
                            if level_file.exists():
                                available_tasks.append(f'level_{level}')

                        # 只导入完整的数据（有5个level文件）
                        if len(available_tasks) != 5:
                            logger.warning(
                                f"V2受试者 {old_id} 数据不完整: "
                                f"只有 {len(available_tasks)}/5 个文件，跳过导入"
                            )
                            results['skipped'] += 1
                            results['errors'].append({
                                'subject_id': old_id,
                                'timestamp': timestamp,
                                'new_id': new_id,
                                'error': f'数据不完整: 只有 {len(available_tasks)}/5 个level文件'
                            })
                            continue

                        tasks_available = available_tasks

                # 创建受试者
                self.subject_manager.create_subject(
                    subject_id=new_id,
                    group=v2_subject['group'],
                    demographics={
                        'name': v2_subject.get('name', ''),
                        'hospital_id': v2_subject.get('hospital_id', ''),
                        'age': v2_subject.get('age'),  # 可能为None
                        'gender': v2_subject.get('gender'),
                        'education_level': v2_subject.get('education_level')
                    },
                    mmse=None,  # 初始无MMSE
                    data_version='v2',
                    metadata={
                        'original_id': old_id,  # 保留原始ID
                        'timestamp': v2_subject.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        'v2_import_date': datetime.now().isoformat(),
                        'data_path': data_path,
                        'tasks_verified': True  # 标记已验证文件完整性
                    }
                )

                # 手动更新tasks_available（因为create_subject默认为空）
                created_subject = self.subject_manager.get_subject(new_id)
                if created_subject:
                    created_subject['tasks_available'] = tasks_available
                    created_subject['task_count'] = len(tasks_available)
                    # 保存更新
                    self.subject_manager.update_subject(
                        subject_id=new_id,
                        demographics=created_subject.get('demographics'),
                        mmse=created_subject.get('mmse')
                    )

                results['imported'] += 1
                logger.debug(f"导入成功: {old_id} -> {new_id}")

            except Exception as e:
                logger.error(f"导入失败: {old_id} -> {new_id}, {e}")
                results['failed'] += 1
                results['errors'].append({
                    'subject_id': old_id,
                    'new_id': new_id,
                    'error': str(e)
                })

        logger.info(f"V2批量导入完成: 成功 {results['imported']}, 失败 {results['failed']}, 跳过 {results['skipped']}")
        return results

    def get_id_mapping_by_original_id(self, original_id: str) -> Optional[str]:
        """
        通过原始ID查找新ID

        Args:
            original_id: V2原始ID (如 'N_01')

        Returns:
            新ID (如 'v2_control_001')，不存在返回None
        """
        subjects = self.subject_manager.get_all_subjects(data_version='v2')

        for subject in subjects:
            if subject.get('metadata', {}).get('original_id') == original_id:
                return subject['subject_id']

        return None

    def scan_v2_subjects_from_directory(self, scan_dir: Optional[Path] = None) -> List[Dict]:
        """
        从目录扫描V2受试者数据

        V2目录结构示例:
        v2_raw_data/
        ├── control/
        │   ├── N_01/
        │   │   ├── info.json
        │   │   └── data.csv
        │   └── N_02/
        ├── mci/
        │   └── M_01/
        └── ad/
            └── A_01/

        Args:
            scan_dir: 扫描目录，默认使用self.v2_scan_dir

        Returns:
            V2受试者列表
        """
        scan_dir = scan_dir or self.v2_scan_dir

        if not scan_dir.exists():
            logger.warning(f"V2扫描目录不存在: {scan_dir}")
            return []

        logger.info(f"开始扫描V2目录: {scan_dir}")

        v2_subjects = []

        for group in ['control', 'mci', 'ad']:
            group_dir = scan_dir / group

            if not group_dir.exists():
                logger.debug(f"组别目录不存在: {group_dir}")
                continue

            for subject_dir in group_dir.iterdir():
                if not subject_dir.is_dir():
                    continue

                subject_id = subject_dir.name

                # 尝试读取info.json
                info = self._read_v2_info(subject_dir)

                v2_subjects.append({
                    'subject_id': subject_id,
                    'group': group,
                    'name': info.get('name', ''),
                    'hospital_id': info.get('hospital_id', ''),
                    'age': info.get('age'),
                    'gender': info.get('gender'),
                    'education_level': info.get('education_level'),
                    'timestamp': info.get('timestamp', self._get_dir_modified_time(subject_dir)),
                    'data_path': str(subject_dir),
                    'data_version': 'v2'
                })

        logger.info(f"扫描完成，找到 {len(v2_subjects)} 个V2受试者")
        return v2_subjects

    def _read_v2_info(self, subject_dir: Path) -> Dict:
        """
        读取V2受试者的info.json（如果存在）

        Args:
            subject_dir: 受试者目录

        Returns:
            信息字典
        """
        info_file = subject_dir / 'info.json'

        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取info.json失败: {info_file}, {e}")

        return {}

    def _get_dir_modified_time(self, dir_path: Path) -> str:
        """
        获取目录修改时间

        Args:
            dir_path: 目录路径

        Returns:
            ISO格式时间字符串
        """
        modified_time = dir_path.stat().st_mtime
        return datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')

    def migrate_existing_v2_ids(self) -> Dict:
        """
        迁移已存在的V2受试者ID到规范格式

        用于数据升级场景：将旧的V2 ID（如 N_01）迁移到新格式（v2_control_001）

        Returns:
            {
                'migrated': 10,
                'failed': 0,
                'id_mapping': {...}
            }
        """
        logger.info("开始迁移已存在的V2受试者ID...")

        # 获取所有未规范化的V2受试者（ID不符合v2_{group}_{seq}格式）
        all_v2_subjects = self.subject_manager.get_all_subjects(data_version='v2')

        # 筛选出需要迁移的（ID不符合规范）
        subjects_to_migrate = []
        for subject in all_v2_subjects:
            if not re.match(r'v2_\w+_\d{3}', subject['subject_id']):
                subjects_to_migrate.append(subject)

        if not subjects_to_migrate:
            logger.info("没有需要迁移的V2受试者")
            return {'migrated': 0, 'failed': 0, 'id_mapping': {}}

        logger.info(f"找到 {len(subjects_to_migrate)} 个需要迁移的V2受试者")

        # 生成ID映射
        id_mapping = self.normalize_v2_subject_ids(subjects_to_migrate)

        results = {'migrated': 0, 'failed': 0, 'id_mapping': id_mapping, 'errors': []}

        # 执行迁移（重命名文件）
        for subject in subjects_to_migrate:
            old_id = subject['subject_id']
            new_id = id_mapping.get(old_id)

            if not new_id:
                continue

            try:
                # 重命名文件
                group = subject['group']
                old_file = self.data_dir / group / f"{self.subject_manager._sanitize_filename(old_id)}.json"
                new_file = self.data_dir / group / f"{self.subject_manager._sanitize_filename(new_id)}.json"

                if old_file.exists():
                    # 更新subject_id
                    subject['subject_id'] = new_id
                    subject['metadata'] = subject.get('metadata', {})
                    subject['metadata']['original_id'] = old_id
                    subject['metadata']['id_migrated_at'] = datetime.now().isoformat()

                    # 保存到新文件
                    with open(new_file, 'w', encoding='utf-8') as f:
                        json.dump(subject, f, ensure_ascii=False, indent=2)

                    # 删除旧文件
                    old_file.unlink()

                    # 更新索引
                    self.subject_manager._update_index(old_id, group, action='remove')
                    self.subject_manager._update_index(new_id, group, action='add')

                    results['migrated'] += 1
                    logger.info(f"迁移成功: {old_id} -> {new_id}")

            except Exception as e:
                logger.error(f"迁移失败: {old_id} -> {new_id}, {e}")
                results['failed'] += 1
                results['errors'].append({'old_id': old_id, 'new_id': new_id, 'error': str(e)})

        logger.info(f"V2 ID迁移完成: 成功 {results['migrated']}, 失败 {results['failed']}")
        return results
