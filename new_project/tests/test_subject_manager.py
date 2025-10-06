"""
SubjectManager 单元测试

测试覆盖:
- 文件名安全处理
- 受试者CRUD操作
- 数据验证
- 统计计算
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.modules.module02_preprocessing.subject_manager import SubjectManager, EDUCATION_LEVELS


class TestFilenameCleanup:
    """测试文件名安全处理"""

    def test_sanitize_basic_characters(self):
        """测试基本非法字符替换"""
        # 测试所有Windows非法字符
        test_cases = [
            ('control/N/A', 'control_N_A'),
            ('subject\\test', 'subject_test'),
            ('id:123', 'id_123'),
            ('file*name', 'file_name'),
            ('test?subject', 'test_subject'),
            ('quo"te', 'quo_te'),
            ('<test>', '_test_'),
            ('pipe|test', 'pipe_test'),
        ]

        for input_id, expected in test_cases:
            result = SubjectManager._sanitize_filename(input_id)
            assert result == expected, f"Failed for {input_id}: got {result}, expected {expected}"

    def test_sanitize_multiple_characters(self):
        """测试多个非法字符组合"""
        input_id = 'control/N\\A:test*file?name"<ok>|end'
        expected = 'control_N_A_test_file_name__ok__end'
        result = SubjectManager._sanitize_filename(input_id)
        assert result == expected

    def test_sanitize_no_change_needed(self):
        """测试不含非法字符的ID"""
        input_id = 'control_subject_001'
        result = SubjectManager._sanitize_filename(input_id)
        assert result == input_id


class TestSubjectCRUD:
    """测试受试者CRUD操作"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录用于测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """创建SubjectManager实例"""
        return SubjectManager(temp_dir)

    def test_create_subject_basic(self, manager):
        """测试创建基本受试者"""
        subject = manager.create_subject(
            subject_id='test_001',
            group='control',
            demographics={
                'gender': 'male',
                'age': 65,
                'education_level': 'undergraduate'
            }
        )

        assert subject['subject_id'] == 'test_001'
        assert subject['group'] == 'control'
        assert subject['demographics']['gender'] == 'male'
        assert subject['task_count'] == 0

    def test_create_subject_with_illegal_chars(self, manager, temp_dir):
        """测试创建包含非法字符的受试者ID"""
        subject_id = 'control/N/A'
        subject = manager.create_subject(
            subject_id=subject_id,
            group='control',
            demographics={
                'gender': 'male',
                'age': 70,
                'education_level': 'primary'
            }
        )

        # 验证创建成功
        assert subject['subject_id'] == subject_id

        # 验证文件名已清理
        safe_filename = 'control_N_A.json'
        file_path = temp_dir / 'control' / safe_filename
        assert file_path.exists()

    def test_get_subject(self, manager):
        """测试获取受试者"""
        # 先创建
        manager.create_subject(
            subject_id='test_002',
            group='mci',
            demographics={'gender': 'female', 'age': 68, 'education_level': 'senior_high'}
        )

        # 再获取
        subject = manager.get_subject('test_002')
        assert subject is not None
        assert subject['subject_id'] == 'test_002'
        assert subject['group'] == 'mci'

    def test_get_nonexistent_subject(self, manager):
        """测试获取不存在的受试者"""
        subject = manager.get_subject('nonexistent')
        assert subject is None

    def test_update_subject(self, manager):
        """测试更新受试者"""
        # 创建
        manager.create_subject(
            subject_id='test_003',
            group='ad',
            demographics={'gender': 'male', 'age': 75, 'education_level': 'junior_high'}
        )

        # 更新
        updated = manager.update_subject(
            subject_id='test_003',
            demographics={'gender': 'male', 'age': 76, 'education_level': 'senior_high'}
        )

        assert updated is not None
        assert updated['demographics']['age'] == 76
        assert updated['demographics']['education_level'] == 'senior_high'

    def test_delete_subject(self, manager, temp_dir):
        """测试删除受试者"""
        # 创建
        manager.create_subject(
            subject_id='test_004',
            group='control',
            demographics={'gender': 'female', 'age': 60, 'education_level': 'undergraduate'}
        )

        # 确认文件存在
        file_path = temp_dir / 'control' / 'test_004.json'
        assert file_path.exists()

        # 删除
        success = manager.delete_subject('test_004')
        assert success is True

        # 确认文件已删除
        assert not file_path.exists()

        # 确认无法获取
        subject = manager.get_subject('test_004')
        assert subject is None


class TestDataValidation:
    """测试数据验证"""

    def test_validate_valid_data(self):
        """测试有效数据验证"""
        valid_data = {
            'subject_id': 'test_001',
            'group': 'control',
            'demographics': {
                'gender': 'male',
                'age': 65,
                'education_level': 'undergraduate'
            }
        }

        errors = SubjectManager.validate_subject_data(valid_data)
        assert len(errors) == 0

    def test_validate_missing_subject_id(self):
        """测试缺少subject_id"""
        data = {
            'group': 'control',
            'demographics': {'gender': 'male', 'age': 65, 'education_level': 'undergraduate'}
        }

        errors = SubjectManager.validate_subject_data(data)
        assert any('subject_id' in err for err in errors)

    def test_validate_invalid_group(self):
        """测试无效的组别"""
        data = {
            'subject_id': 'test',
            'group': 'invalid_group',
            'demographics': {'gender': 'male', 'age': 65, 'education_level': 'undergraduate'}
        }

        errors = SubjectManager.validate_subject_data(data)
        assert any('group' in err for err in errors)

    def test_validate_invalid_gender(self):
        """测试无效的性别"""
        data = {
            'subject_id': 'test',
            'group': 'control',
            'demographics': {'gender': 'other', 'age': 65, 'education_level': 'undergraduate'}
        }

        errors = SubjectManager.validate_subject_data(data)
        assert any('性别' in err for err in errors)

    def test_validate_invalid_age(self):
        """测试无效的年龄"""
        test_cases = [
            {'gender': 'male', 'age': -5, 'education_level': 'undergraduate'},
            {'gender': 'male', 'age': 150, 'education_level': 'undergraduate'},
            {'gender': 'male', 'age': 'not_a_number', 'education_level': 'undergraduate'},
        ]

        for demographics in test_cases:
            data = {
                'subject_id': 'test',
                'group': 'control',
                'demographics': demographics
            }
            errors = SubjectManager.validate_subject_data(data)
            assert any('年龄' in err for err in errors)

    def test_validate_invalid_education(self):
        """测试无效的受教育程度"""
        data = {
            'subject_id': 'test',
            'group': 'control',
            'demographics': {'gender': 'male', 'age': 65, 'education_level': 'invalid_level'}
        }

        errors = SubjectManager.validate_subject_data(data)
        assert any('受教育程度' in err for err in errors)


class TestStatistics:
    """测试统计功能"""

    @pytest.fixture
    def manager_with_data(self):
        """创建包含测试数据的manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SubjectManager(Path(tmpdir))

            # 创建测试数据
            test_subjects = [
                {
                    'subject_id': 'control_1',
                    'group': 'control',
                    'demographics': {'gender': 'male', 'age': 60, 'education_level': 'undergraduate'},
                    'mmse': {'total_score': 28}
                },
                {
                    'subject_id': 'control_2',
                    'group': 'control',
                    'demographics': {'gender': 'female', 'age': 65, 'education_level': 'postgraduate'},
                    'mmse': {'total_score': 26}
                },
                {
                    'subject_id': 'mci_1',
                    'group': 'mci',
                    'demographics': {'gender': 'male', 'age': 70, 'education_level': 'senior_high'},
                    'mmse': {'total_score': 20}
                },
                {
                    'subject_id': 'ad_1',
                    'group': 'ad',
                    'demographics': {'gender': 'female', 'age': 75, 'education_level': 'junior_high'},
                    'mmse': {'total_score': 15}
                },
                {
                    'subject_id': 'ad_2',
                    'group': 'ad',
                    'demographics': {'gender': 'male', 'age': 80, 'education_level': 'primary'},
                    'mmse': None  # 测试None MMSE场景
                },
            ]

            for subj in test_subjects:
                manager.create_subject(
                    subject_id=subj['subject_id'],
                    group=subj['group'],
                    demographics=subj['demographics'],
                    mmse=subj.get('mmse')
                )

            yield manager

    def test_statistics_total_count(self, manager_with_data):
        """测试总数统计"""
        stats = manager_with_data.get_statistics()
        assert stats['total_subjects'] == 5

    def test_statistics_by_group(self, manager_with_data):
        """测试分组统计"""
        stats = manager_with_data.get_statistics()
        assert stats['by_group']['control'] == 2
        assert stats['by_group']['mci'] == 1
        assert stats['by_group']['ad'] == 2

    def test_statistics_by_gender(self, manager_with_data):
        """测试性别统计"""
        stats = manager_with_data.get_statistics()
        assert stats['by_gender']['male'] == 3
        assert stats['by_gender']['female'] == 2

    def test_statistics_age_distribution(self, manager_with_data):
        """测试年龄分布统计"""
        stats = manager_with_data.get_statistics()
        assert stats['age_distribution']['60-69'] == 2
        assert stats['age_distribution']['70-79'] == 2
        assert stats['age_distribution']['>=80'] == 1

    def test_statistics_mmse_distribution(self, manager_with_data):
        """测试MMSE分布统计"""
        stats = manager_with_data.get_statistics()
        # 28, 26: normal (>=24)
        # 20: moderate (18-23)
        # 15: severe (<18)
        # None: not_tested
        assert stats['mmse_distribution']['normal'] == 2
        assert stats['mmse_distribution']['moderate'] == 1
        assert stats['mmse_distribution']['severe'] == 1
        assert stats['mmse_distribution']['not_tested'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
