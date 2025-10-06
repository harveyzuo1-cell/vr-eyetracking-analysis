"""
Module02 SubjectManager扩展测试 - 提升覆盖率到80%+

覆盖缺失的功能：
- get_all_subjects with filters
- update_subject functionality
- delete_subject functionality
- _update_index method
- export functionality
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from src.modules.module02_preprocessing.subject_manager import SubjectManager


class TestSubjectManagerExtended:
    """扩展测试类 - 覆盖更多SubjectManager功能"""

    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_data_dir):
        """创建SubjectManager实例"""
        return SubjectManager(temp_data_dir)

    @pytest.fixture
    def sample_subjects(self, manager):
        """创建示例受试者数据"""
        subjects = []

        # 创建3个对照组受试者
        for i in range(3):
            subject = manager.create_subject(
                subject_id=f'control_{i}',
                group='control',
                demographics={
                    'gender': 'male' if i % 2 == 0 else 'female',
                    'age': 60 + i * 5,
                    'education_level': 'undergraduate'
                },
                mmse={
                    'q1_weekday': 2, 'q1_month': 1, 'q1_year': 1, 'q1_season': 1,
                    'q2_province': 2, 'q2_floor': 1,
                    'q3_immediate': 3,
                    'total_score': 10
                }
            )
            subjects.append(subject)

        # 创建2个MCI组受试者
        for i in range(2):
            subject = manager.create_subject(
                subject_id=f'mci_{i}',
                group='mci',
                demographics={
                    'gender': 'female',
                    'age': 70 + i * 3,
                    'education_level': 'senior_high'
                },
                mmse={
                    'q1_weekday': 2, 'q1_month': 1, 'q1_year': 0, 'q1_season': 1,
                    'q2_province': 0, 'q2_floor': 0,
                    'q3_immediate': 2,
                    'total_score': 6
                }
            )
            subjects.append(subject)

        return subjects

    def test_get_all_subjects_by_group(self, manager, sample_subjects):
        """测试按组别筛选受试者"""
        # 获取对照组受试者
        control_subjects = manager.get_all_subjects(group='control')
        assert len(control_subjects) == 3
        assert all(s['group'] == 'control' for s in control_subjects)

        # 获取MCI组受试者
        mci_subjects = manager.get_all_subjects(group='mci')
        assert len(mci_subjects) == 2
        assert all(s['group'] == 'mci' for s in mci_subjects)

    def test_get_all_subjects_with_mmse(self, manager, sample_subjects):
        """测试获取包含MMSE数据的受试者"""
        subjects_with_mmse = manager.get_all_subjects(with_mmse=True)

        assert len(subjects_with_mmse) == 5
        for subject in subjects_with_mmse:
            assert 'mmse' in subject
            assert subject['mmse'] is not None
            assert 'total_score' in subject['mmse']

    def test_update_subject_demographics(self, manager, sample_subjects):
        """测试更新受试者人口学信息"""
        subject_id = 'control_0'

        # 更新年龄和性别
        updated = manager.update_subject(
            subject_id=subject_id,
            demographics={
                'gender': 'female',
                'age': 68,
                'education_level': 'postgraduate'
            }
        )

        assert updated is not None
        assert updated['demographics']['gender'] == 'female'
        assert updated['demographics']['age'] == 68
        assert updated['demographics']['education_level'] == 'postgraduate'

        # 验证文件已更新
        retrieved = manager.get_subject(subject_id)
        assert retrieved['demographics']['age'] == 68

    def test_update_subject_mmse(self, manager, sample_subjects):
        """测试更新受试者MMSE数据"""
        subject_id = 'mci_0'

        # 更新MMSE分数
        new_mmse = {
            'q1_weekday': 2, 'q1_month': 1, 'q1_year': 1, 'q1_season': 1,
            'q2_province': 2, 'q2_floor': 1,
            'q3_immediate': 3,
            'total_score': 11
        }

        updated = manager.update_subject(subject_id=subject_id, mmse=new_mmse)

        assert updated is not None
        assert updated['mmse']['total_score'] == 11

    def test_update_nonexistent_subject(self, manager):
        """测试更新不存在的受试者"""
        result = manager.update_subject(
            subject_id='nonexistent',
            demographics={'age': 70}
        )

        assert result is None

    def test_delete_subject(self, manager, sample_subjects):
        """测试删除受试者"""
        subject_id = 'control_1'

        # 确认受试者存在
        assert manager.get_subject(subject_id) is not None

        # 删除受试者
        result = manager.delete_subject(subject_id)
        assert result is True

        # 确认已删除
        assert manager.get_subject(subject_id) is None

        # 验证索引已更新
        all_subjects = manager.get_all_subjects()
        assert len(all_subjects) == 4  # 5 - 1
        assert subject_id not in [s['subject_id'] for s in all_subjects]

    def test_delete_nonexistent_subject(self, manager):
        """测试删除不存在的受试者"""
        result = manager.delete_subject('nonexistent')
        assert result is False

    def test_get_statistics_comprehensive(self, manager, sample_subjects):
        """测试完整的统计功能"""
        stats = manager.get_statistics()

        # 验证总数
        assert stats['total_subjects'] == 5

        # 验证按组别统计
        assert stats['by_group']['control'] == 3
        assert stats['by_group']['mci'] == 2
        assert stats['by_group']['ad'] == 0

        # 验证按性别统计
        assert stats['by_gender']['male'] == 2  # control_0, control_2
        assert stats['by_gender']['female'] == 3  # control_1, mci_0, mci_1

        # 验证年龄分布
        # Ages: control_0=60, control_1=65, control_2=70, mci_0=70, mci_1=73
        assert stats['age_distribution']['60-69'] == 2  # 60, 65
        assert stats['age_distribution']['70-79'] == 3  # 70, 70, 73

        # 验证MMSE分布
        # All subjects have score<18, so all are "severe"
        # control: 10分 (< 18), mci: 6分 (< 18)
        assert stats['mmse_distribution']['severe'] == 5  # All subjects score<18
        assert stats['mmse_distribution']['moderate'] == 0
        assert stats['mmse_distribution']['normal'] == 0

    def test_index_integrity(self, manager, sample_subjects):
        """测试索引文件完整性"""
        # 读取索引文件
        index_file = manager.data_dir / 'subjects.json'
        assert index_file.exists()

        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        # 验证索引结构
        assert 'total_subjects' in index
        assert 'groups' in index
        assert index['total_subjects'] == 5

        # 验证组别计数
        assert index['groups']['control']['count'] == 3
        assert index['groups']['mci']['count'] == 2

        # 验证受试者列表
        control_ids = index['groups']['control']['subjects']
        assert 'control_0' in control_ids
        assert 'control_1' in control_ids
        assert 'control_2' in control_ids


class TestSubjectManagerEdgeCases:
    """边界情况测试"""

    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_data_dir):
        return SubjectManager(temp_data_dir)

    def test_create_subject_with_special_chars_in_id(self, manager):
        """测试包含特殊字符的subject_id"""
        subject_id = 'test/subject:with*special?chars'

        subject = manager.create_subject(
            subject_id=subject_id,
            group='control',
            demographics={'gender': 'male', 'age': 65, 'education_level': 'undergraduate'}
        )

        assert subject is not None
        assert subject['subject_id'] == subject_id

        # 验证文件名已被清理
        safe_filename = manager._sanitize_filename(subject_id)
        assert '/' not in safe_filename
        assert ':' not in safe_filename
        assert '*' not in safe_filename
        assert '?' not in safe_filename

    def test_statistics_with_empty_data(self, manager):
        """测试空数据的统计"""
        stats = manager.get_statistics()

        assert stats['total_subjects'] == 0
        assert all(count == 0 for count in stats['by_group'].values())
        assert all(count == 0 for count in stats['by_gender'].values())

    def test_create_subject_without_mmse(self, manager):
        """测试创建不含MMSE的受试者"""
        subject = manager.create_subject(
            subject_id='test_no_mmse',
            group='control',
            demographics={'gender': 'male', 'age': 65, 'education_level': 'undergraduate'},
            mmse=None
        )

        assert subject is not None
        assert subject['mmse'] is None

        # 获取时验证
        retrieved = manager.get_subject('test_no_mmse')
        assert retrieved['mmse'] is None

    def test_multiple_updates_preserve_data(self, manager):
        """测试多次更新保持数据完整性"""
        subject_id = 'test_multi_update'

        # 创建初始受试者
        manager.create_subject(
            subject_id=subject_id,
            group='control',
            demographics={'gender': 'male', 'age': 60, 'education_level': 'undergraduate'}
        )

        # 第一次更新：只更新年龄
        manager.update_subject(subject_id, demographics={'age': 65})
        subject1 = manager.get_subject(subject_id)
        assert subject1['demographics']['age'] == 65
        assert subject1['demographics']['gender'] == 'male'  # 保持不变

        # 第二次更新：只更新性别
        manager.update_subject(subject_id, demographics={'gender': 'female'})
        subject2 = manager.get_subject(subject_id)
        assert subject2['demographics']['gender'] == 'female'
        assert subject2['demographics']['age'] == 65  # 保持第一次更新的值
