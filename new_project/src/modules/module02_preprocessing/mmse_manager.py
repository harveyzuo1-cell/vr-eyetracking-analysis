"""
MMSE评分数据管理器

功能:
- 管理简化版MMSE评分（19题版本）
- 从clinical/mmse_scores.json导入数据
- 计算分项得分和总分
- 数据验证
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# MMSE题目定义（简化版，满分21分）
# 特殊计分：q1_weekday=2分，q2_province=2分，其他题目1分或3分
MMSE_QUESTIONS = {
    # Q1: 时间定向 (Time Orientation) - 满分5分
    # q1_year(1) + q1_season(1) + q1_month(1) + q1_weekday(2) = 5分
    'time_orientation': {
        'fields': ['q1_year', 'q1_season', 'q1_month', 'q1_weekday'],
        'field_scores': {'q1_year': 1, 'q1_season': 1, 'q1_month': 1, 'q1_weekday': 2},
        'max_score': 5,
        'name_zh': '时间定向',
        'name_en': 'Time Orientation'
    },
    # Q2: 地点定向 (Place Orientation) - 满分5分
    # q2_province(2) + q2_street(1) + q2_building(1) + q2_floor(1) = 5分
    'place_orientation': {
        'fields': ['q2_province', 'q2_street', 'q2_building', 'q2_floor'],
        'field_scores': {'q2_province': 2, 'q2_street': 1, 'q2_building': 1, 'q2_floor': 1},
        'max_score': 5,
        'name_zh': '地点定向',
        'name_en': 'Place Orientation'
    },
    # Q3: 即刻记忆 (Immediate Recall) - 满分3分
    # 注意：q3_immediate不在field_scores中，所以会直接使用字段值(0-3)作为得分
    'immediate_recall': {
        'fields': ['q3_immediate'],
        'field_scores': {},  # 空字典：q3_immediate不在此处定义，直接使用字段值
        'max_score': 3,
        'name_zh': '即刻记忆',
        'name_en': 'Immediate Recall'
    },
    # Q4: 注意力与计算 (Attention & Calculation) - 满分5分
    'attention_calculation': {
        'fields': ['q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7'],
        'field_scores': {'q4_100_7': 1, 'q4_93_7': 1, 'q4_86_7': 1, 'q4_79_7': 1, 'q4_72_7': 1},
        'max_score': 5,
        'name_zh': '注意力与计算',
        'name_en': 'Attention & Calculation'
    },
    # Q5: 延迟回忆 (Delayed Recall) - 满分3分
    'delayed_recall': {
        'fields': ['q5_word1', 'q5_word2', 'q5_word3'],
        'field_scores': {'q5_word1': 1, 'q5_word2': 1, 'q5_word3': 1},
        'max_score': 3,
        'name_zh': '延迟回忆',
        'name_en': 'Delayed Recall'
    }
}

# MMSE总分范围：0-21分
MMSE_MAX_SCORE = 21


class MMSEManager:
    """MMSE数据管理器"""

    def __init__(self, clinical_data_dir: Path):
        """
        初始化MMSE管理器

        Args:
            clinical_data_dir: clinical数据目录路径
        """
        self.clinical_dir = Path(clinical_data_dir)
        self.mmse_file = self.clinical_dir / 'mmse_scores.json'

    def load_clinical_mmse_data(self) -> Dict:
        """
        从clinical目录加载MMSE数据

        Returns:
            MMSE数据字典，key为subject_id
        """
        if not self.mmse_file.exists():
            return {}

        with open(self.mmse_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _get_field_score(field: str, field_value: int, field_scores: Dict) -> int:
        """
        计算单个字段的得分（统一处理特殊计分规则）

        计分规则：
        - 未在field_scores中定义的字段：直接使用字段值（如q3_immediate可以是0-3）
        - max_score=1的字段：值即得分（0或1）
        - max_score>1的字段：值为1时得max_score分，值为0时得0分（如q1_weekday值为1时得2分）

        Args:
            field: 字段名
            field_value: 字段值
            field_scores: 字段分值定义

        Returns:
            该字段的得分
        """
        if field not in field_scores:
            # q3_immediate等可变分数字段，直接使用字段值
            return field_value

        max_score = field_scores[field]
        if max_score > 1:
            # q1_weekday, q2_province等特殊字段：值为1时得max_score分
            return field_value * max_score
        else:
            # 普通字段：值即得分
            return field_value

    @staticmethod
    def calculate_section_scores(mmse_data: Dict) -> Dict:
        """
        计算MMSE各部分得分（支持不同分值的题目）

        Args:
            mmse_data: 包含详细题目得分的MMSE数据

        Returns:
            各部分得分字典
        """
        section_scores = {}

        for section_key, section_info in MMSE_QUESTIONS.items():
            score = 0
            field_scores = section_info.get('field_scores', {})

            for field in section_info['fields']:
                field_value = mmse_data.get(field, 0)
                score += MMSEManager._get_field_score(field, field_value, field_scores)

            section_scores[section_key] = {
                'score': score,
                'max_score': section_info['max_score'],
                'name_zh': section_info['name_zh'],
                'name_en': section_info['name_en']
            }

        return section_scores

    @staticmethod
    def calculate_total_score(mmse_data: Dict) -> int:
        """
        计算MMSE总分（支持不同分值的题目）

        Args:
            mmse_data: 包含详细题目得分的MMSE数据

        Returns:
            总分 (0-21)
        """
        total = 0
        for section_info in MMSE_QUESTIONS.values():
            field_scores = section_info.get('field_scores', {})

            for field in section_info['fields']:
                field_value = mmse_data.get(field, 0)
                total += MMSEManager._get_field_score(field, field_value, field_scores)

        return total

    @staticmethod
    def validate_mmse_data(mmse_data: Dict) -> List[str]:
        """
        验证MMSE数据

        Args:
            mmse_data: MMSE数据

        Returns:
            错误信息列表
        """
        errors = []

        # 验证每个题目的分数范围（根据field_scores定义）
        for section_info in MMSE_QUESTIONS.values():
            for field in section_info['fields']:
                if field in mmse_data:
                    score = mmse_data[field]
                    max_score = section_info['field_scores'].get(field, 1)
                    valid_scores = list(range(0, max_score + 1))
                    if not isinstance(score, int) or score not in valid_scores:
                        errors.append(f"{field}得分必须是{valid_scores}中的一个（值为{max_score}时得{max_score}分）")

        # 验证总分
        if 'total_score' in mmse_data:
            total = mmse_data['total_score']
            if not isinstance(total, int) or total < 0 or total > MMSE_MAX_SCORE:
                errors.append(f"total_score必须在0-{MMSE_MAX_SCORE}之间")

        return errors

    def convert_clinical_to_standard_format(self, clinical_data: Dict) -> Dict:
        """
        将clinical格式的MMSE数据转换为标准格式

        Args:
            clinical_data: clinical目录中的MMSE数据（包含所有详细题目）

        Returns:
            标准格式的MMSE数据
        """
        # 提取基本信息
        standard_data = {
            'raw_id': clinical_data.get('raw_id'),
            'source': clinical_data.get('source', 'clinical_import'),
            'test_date': clinical_data.get('last_updated', datetime.now().isoformat()),
            'data_version': clinical_data.get('data_version', 'v1')
        }

        # 复制所有题目得分
        for section_info in MMSE_QUESTIONS.values():
            for field in section_info['fields']:
                if field in clinical_data:
                    standard_data[field] = clinical_data[field]

        # 计算分项得分
        standard_data['section_scores'] = self.calculate_section_scores(clinical_data)

        # 使用原始total_score或重新计算
        if 'total_score' in clinical_data:
            standard_data['total_score'] = clinical_data['total_score']
        else:
            standard_data['total_score'] = self.calculate_total_score(clinical_data)

        return standard_data

    def import_clinical_mmse_for_subject(self, subject_id: str) -> Optional[Dict]:
        """
        为指定受试者导入clinical中的MMSE数据

        Args:
            subject_id: 受试者ID（如 "control_legacy_1"）

        Returns:
            标准格式的MMSE数据，如果不存在则返回None
        """
        all_clinical_data = self.load_clinical_mmse_data()

        if subject_id not in all_clinical_data:
            return None

        clinical_data = all_clinical_data[subject_id]
        return self.convert_clinical_to_standard_format(clinical_data)

    def import_all_clinical_mmse(self) -> Dict[str, Dict]:
        """
        导入所有clinical中的MMSE数据

        Returns:
            字典，key为subject_id，value为标准格式MMSE数据
        """
        all_clinical_data = self.load_clinical_mmse_data()
        result = {}

        for subject_id, clinical_data in all_clinical_data.items():
            result[subject_id] = self.convert_clinical_to_standard_format(clinical_data)

        return result

    @staticmethod
    def get_cognitive_status(total_score: int) -> str:
        """
        根据总分判断认知状态（仅供参考，实际分界线需根据研究确定）

        Args:
            total_score: MMSE总分 (0-21)

        Returns:
            认知状态描述
        """
        if total_score >= 19:
            return 'normal'  # 正常 (19-21分)
        elif total_score >= 15:
            return 'mild'    # 轻度损伤 (15-18分)
        elif total_score >= 11:
            return 'moderate'  # 中度损伤 (11-14分)
        else:
            return 'severe'  # 重度损伤 (0-10分)

    @staticmethod
    def create_mmse_summary(mmse_data: Dict) -> Dict:
        """
        创建MMSE摘要信息（用于列表显示）

        Args:
            mmse_data: 完整的MMSE数据

        Returns:
            摘要信息
        """
        total_score = mmse_data.get('total_score', 0)

        return {
            'total_score': total_score,
            'test_date': mmse_data.get('test_date'),
            'cognitive_status': MMSEManager.get_cognitive_status(total_score),
            'source': mmse_data.get('source', 'manual_input')
        }

    @staticmethod
    def parse_csv_row(row: Dict) -> Dict:
        """
        解析CSV行数据为MMSE数据格式

        Args:
            row: CSV行数据（字典格式）

        Returns:
            MMSE数据
        """
        mmse_data = {}

        # 基本信息
        if 'subject_id' in row:
            mmse_data['subject_id'] = str(row['subject_id']).strip()
        if 'test_date' in row:
            mmse_data['test_date'] = str(row['test_date']).strip()

        # 时间定向题目 (Q1)
        for field in ['q1_year', 'q1_season', 'q1_month', 'q1_weekday']:
            if field in row:
                mmse_data[field] = int(row[field])

        # 地点定向题目 (Q2)
        for field in ['q2_province', 'q2_street', 'q2_building', 'q2_floor']:
            if field in row:
                mmse_data[field] = int(row[field])

        # 即刻记忆 (Q3)
        if 'q3_immediate' in row:
            mmse_data['q3_immediate'] = int(row['q3_immediate'])

        # 注意力与计算 (Q4)
        for field in ['q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7']:
            if field in row:
                mmse_data[field] = int(row[field])

        # 延迟回忆 (Q5)
        for field in ['q5_word1', 'q5_word2', 'q5_word3']:
            if field in row:
                mmse_data[field] = int(row[field])

        # 如果CSV中有total_score，使用它；否则会在后续计算
        if 'total_score' in row and row['total_score']:
            mmse_data['total_score'] = int(row['total_score'])

        return mmse_data

    @staticmethod
    def import_from_csv(csv_file_path: Path) -> Dict:
        """
        从CSV文件批量导入MMSE数据

        CSV格式：
            subject_id,test_date,q1_year,q1_season,q1_month,q1_weekday,
            q2_province,q2_street,q2_building,q2_floor,q3_immediate,
            q4_100_7,q4_93_7,q4_86_7,q4_79_7,q4_72_7,
            q5_word1,q5_word2,q5_word3,total_score

        Args:
            csv_file_path: CSV文件路径

        Returns:
            导入结果字典，包含成功和失败的记录
        """
        import csv

        results = {
            'success': [],
            'failed': [],
            'total': 0
        }

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是标题）
                    results['total'] += 1

                    try:
                        # 解析CSV行
                        mmse_data = MMSEManager.parse_csv_row(row)

                        # 验证数据
                        errors = MMSEManager.validate_mmse_data(mmse_data)
                        if errors:
                            results['failed'].append({
                                'row': row_num,
                                'subject_id': mmse_data.get('subject_id', 'unknown'),
                                'errors': errors
                            })
                            continue

                        # 计算分项得分
                        mmse_data['section_scores'] = MMSEManager.calculate_section_scores(mmse_data)

                        # 计算总分（如果CSV中没有提供）
                        if 'total_score' not in mmse_data:
                            mmse_data['total_score'] = MMSEManager.calculate_total_score(mmse_data)

                        # 添加来源信息
                        mmse_data['source'] = 'csv_import'
                        mmse_data['data_version'] = 'v1'

                        # 如果没有test_date，使用当前时间
                        if 'test_date' not in mmse_data or not mmse_data['test_date']:
                            mmse_data['test_date'] = datetime.now().isoformat()

                        results['success'].append({
                            'row': row_num,
                            'subject_id': mmse_data.get('subject_id'),
                            'data': mmse_data
                        })

                    except Exception as e:
                        results['failed'].append({
                            'row': row_num,
                            'subject_id': row.get('subject_id', 'unknown'),
                            'error': str(e)
                        })

        except Exception as e:
            results['file_error'] = str(e)

        return results

    @staticmethod
    def generate_csv_template(output_path: Path):
        """
        生成CSV模板文件

        Args:
            output_path: 输出文件路径
        """
        import csv

        # CSV列标题
        headers = [
            'subject_id',
            'test_date',
            # Q1: 时间定向
            'q1_year', 'q1_season', 'q1_month', 'q1_weekday',
            # Q2: 地点定向
            'q2_province', 'q2_street', 'q2_building', 'q2_floor',
            # Q3: 即刻记忆
            'q3_immediate',
            # Q4: 注意力与计算
            'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
            # Q5: 延迟回忆
            'q5_word1', 'q5_word2', 'q5_word3',
            # 总分（可选，会自动计算）
            'total_score'
        ]

        # 示例数据
        example_rows = [
            {
                'subject_id': 'control_1',
                'test_date': '2024-03-15',
                'q1_year': 1, 'q1_season': 1, 'q1_month': 1, 'q1_weekday': 1,
                'q2_province': 1, 'q2_street': 1, 'q2_building': 1, 'q2_floor': 1,
                'q3_immediate': 3,
                'q4_100_7': 1, 'q4_93_7': 1, 'q4_86_7': 1, 'q4_79_7': 1, 'q4_72_7': 1,
                'q5_word1': 1, 'q5_word2': 1, 'q5_word3': 1,
                'total_score': 19
            },
            {
                'subject_id': 'mci_1',
                'test_date': '2024-03-16',
                'q1_year': 1, 'q1_season': 1, 'q1_month': 0, 'q1_weekday': 1,
                'q2_province': 1, 'q2_street': 1, 'q2_building': 1, 'q2_floor': 0,
                'q3_immediate': 2,
                'q4_100_7': 1, 'q4_93_7': 1, 'q4_86_7': 0, 'q4_79_7': 0, 'q4_72_7': 0,
                'q5_word1': 1, 'q5_word2': 0, 'q5_word3': 0,
                'total_score': 14
            }
        ]

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(example_rows)

    def generate_batch_import_template(
        self,
        subject_manager,
        include_existing_data: bool = True,
        data_version: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> bytes:
        """
        生成MMSE批量导入模板（包含已有V2受试者信息）

        Args:
            subject_manager: SubjectManager实例
            include_existing_data: 是否包含已有受试者的数据
            data_version: 筛选数据版本 ('v1'/'v2'/None表示全部)
            output_path: 输出路径（可选，不提供则返回bytes）

        Returns:
            CSV文件内容（bytes）
        """
        import csv
        import io

        # CSV列定义（新增人口学字段）
        headers = [
            'subject_id',      # 受试者ID（不可修改）
            'group',           # 分组
            'name',            # 患者姓名
            'hospital_id',     # 医院ID
            'age',             # 年龄
            'gender',          # 性别
            'education_level', # 受教育程度
            'timestamp',       # 时间戳（不可修改）
            # Q1: 时间定向 (5分)
            'q1_year', 'q1_season', 'q1_month', 'q1_weekday',
            # Q2: 地点定向 (5分)
            'q2_province', 'q2_street', 'q2_building', 'q2_floor',
            # Q3: 即刻记忆 (3分)
            'q3_immediate',
            # Q4: 注意力与计算 (5分)
            'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
            # Q5: 延迟回忆 (3分)
            'q5_word1', 'q5_word2', 'q5_word3',
            # 注意: 不包含total_score，后端自动计算
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        if include_existing_data:
            # 获取受试者（根据data_version筛选）
            subjects = subject_manager.get_all_subjects(
                data_version=data_version,
                with_mmse=True
            )

            for subject in subjects:
                row = {
                    'subject_id': subject['subject_id'],
                    'group': subject['group'],
                    'name': subject.get('demographics', {}).get('name', ''),
                    'hospital_id': subject.get('demographics', {}).get('hospital_id', ''),
                    'age': subject.get('demographics', {}).get('age', ''),
                    'gender': subject.get('demographics', {}).get('gender', ''),
                    'education_level': subject.get('demographics', {}).get('education_level', ''),
                    'timestamp': subject.get('metadata', {}).get('timestamp', ''),
                }

                # 如果已有MMSE数据，也填充进去
                if subject.get('mmse'):
                    mmse = subject['mmse']
                    mmse_fields = [
                        'q1_year', 'q1_season', 'q1_month', 'q1_weekday',
                        'q2_province', 'q2_street', 'q2_building', 'q2_floor',
                        'q3_immediate',
                        'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
                        'q5_word1', 'q5_word2', 'q5_word3'
                    ]
                    for key in mmse_fields:
                        if key in mmse:
                            row[key] = mmse[key]

                writer.writerow(row)

        csv_content = output.getvalue()

        # 如果提供了输出路径，写入文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(csv_content)

        return csv_content.encode('utf-8-sig')  # BOM for Excel

    def batch_import_clinical_data(
        self,
        csv_file_path: Path,
        subject_manager
    ) -> Dict:
        """
        批量导入MMSE临床数据（支持更新已有受试者）

        导入规则:
        1. subject_id和timestamp不可修改（作为查找依据）
        2. 其他字段可更新（demographics和mmse）
        3. 如果subject_id不存在，报错（必须先导入V2数据）

        Args:
            csv_file_path: CSV文件路径
            subject_manager: SubjectManager实例

        Returns:
            {
                'updated': 10,
                'skipped': 0,
                'errors': []
            }
        """
        import csv

        results = {'updated': 0, 'skipped': 0, 'errors': []}

        with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                subject_id = row.get('subject_id', '').strip()

                if not subject_id:
                    results['errors'].append({
                        'row': row_num,
                        'subject_id': '',
                        'error': '受试者ID为空'
                    })
                    continue

                # 检查受试者是否存在
                existing_subject = subject_manager.get_subject(subject_id)

                if not existing_subject:
                    results['errors'].append({
                        'row': row_num,
                        'subject_id': subject_id,
                        'error': '受试者不存在，请先导入V2数据'
                    })
                    continue

                try:
                    # 准备更新数据
                    demographics_update = {}
                    for field in ['name', 'hospital_id', 'age', 'gender', 'education_level']:
                        if row.get(field):
                            value = row[field].strip()
                            if value:
                                if field == 'age':
                                    demographics_update[field] = int(value)
                                else:
                                    demographics_update[field] = value

                    # 准备MMSE数据
                    mmse_update = {}
                    mmse_fields = ['q1_year', 'q1_season', 'q1_month', 'q1_weekday',
                                   'q2_province', 'q2_floor', 'q3_immediate']

                    for field in mmse_fields:
                        if row.get(field):
                            try:
                                mmse_update[field] = int(row[field])
                            except ValueError:
                                pass

                    # 计算总分
                    if mmse_update:
                        mmse_update['total_score'] = self.calculate_total_score(mmse_update)

                    # 更新受试者
                    subject_manager.update_subject(
                        subject_id=subject_id,
                        demographics=demographics_update if demographics_update else None,
                        mmse=mmse_update if mmse_update else None
                    )

                    results['updated'] += 1

                except Exception as e:
                    results['errors'].append({
                        'row': row_num,
                        'subject_id': subject_id,
                        'error': str(e)
                    })

        return results
