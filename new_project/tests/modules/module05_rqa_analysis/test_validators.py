"""
Module05 RQA分析单元测试 - Validators模块 (扩展版)
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.modules.module05_rqa_analysis.validators import (
    RQADataValidator,
    RQAPathManager
)


class TestRQADataValidator:
    """RQADataValidator单元测试 - 完整覆盖"""

    # ========== validate_rqa_params测试 ==========

    def test_validate_rqa_params_valid(self):
        """测试有效的RQA参数"""
        params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is True
        assert error is None

    def test_validate_rqa_params_boundary_values(self):
        """测试边界值"""
        # m=1 (最小值)
        params = {'m': 1, 'tau': 1, 'eps': 0.05, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is True

        # m=20 (最大值)
        params = {'m': 20, 'tau': 20, 'eps': 0.999, 'lmin': 10}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is True

    def test_validate_rqa_params_missing_keys(self):
        """测试缺少必需参数"""
        # Missing m
        params = {'tau': 1, 'eps': 0.05, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        assert 'm' in error

        # Missing tau
        params = {'m': 2, 'eps': 0.05, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        assert 'tau' in error

        # Missing eps
        params = {'m': 2, 'tau': 1, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        assert 'eps' in error

        # Missing lmin
        params = {'m': 2, 'tau': 1, 'eps': 0.05}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        assert 'lmin' in error

    @pytest.mark.parametrize("m", [0, -1, 21, 100, 'invalid'])
    def test_validate_rqa_params_invalid_m(self, m):
        """测试无效的m值"""
        params = {'m': m, 'tau': 1, 'eps': 0.05, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        if isinstance(m, int):
            assert 'm' in error

    @pytest.mark.parametrize("tau", [0, -1, 21, 100])
    def test_validate_rqa_params_invalid_tau(self, tau):
        """测试无效的tau值"""
        params = {'m': 2, 'tau': tau, 'eps': 0.05, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        assert 'tau' in error

    @pytest.mark.parametrize("eps", [0, -0.1, 1.5, 2.0])
    def test_validate_rqa_params_invalid_eps(self, eps):
        """测试无效的eps值"""
        params = {'m': 2, 'tau': 1, 'eps': eps, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False

    @pytest.mark.parametrize("lmin", [1, 0, -1, 11, 100])
    def test_validate_rqa_params_invalid_lmin(self, lmin):
        """测试无效的lmin值"""
        params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': lmin}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        assert 'lmin' in error

    # ========== validate_groups测试 ==========

    def test_validate_groups_valid(self):
        """测试有效的分组列表"""
        groups = ['control', 'mci', 'ad']
        is_valid, error = RQADataValidator.validate_groups(groups)
        assert is_valid is True
        assert error is None

    def test_validate_groups_single(self):
        """测试单个分组"""
        for group in ['control', 'mci', 'ad']:
            is_valid, error = RQADataValidator.validate_groups([group])
            assert is_valid is True

    def test_validate_groups_empty(self):
        """测试空分组列表"""
        is_valid, error = RQADataValidator.validate_groups([])
        assert is_valid is False
        assert '不能为空' in error

    @pytest.mark.parametrize("invalid_group", ['invalid', 'test', 'Control', 'MCI', 'AD'])
    def test_validate_groups_invalid(self, invalid_group):
        """测试无效的分组名称"""
        groups = ['control', invalid_group]
        is_valid, error = RQADataValidator.validate_groups(groups)
        assert is_valid is False
        assert invalid_group in error

    # ========== validate_data_version测试 ==========

    @pytest.mark.parametrize("version", ['v1', 'v2'])
    def test_validate_data_version_valid(self, version):
        """测试有效的数据版本"""
        is_valid, error = RQADataValidator.validate_data_version(version)
        assert is_valid is True
        assert error is None

    @pytest.mark.parametrize("version", ['v0', 'v3', 'V1', 'V2', '', 'invalid'])
    def test_validate_data_version_invalid(self, version):
        """测试无效的数据版本"""
        is_valid, error = RQADataValidator.validate_data_version(version)
        assert is_valid is False
        assert version in error

    # ========== standardize_dataframe测试 ==========

    def test_standardize_dataframe_columns(self):
        """测试列名标准化"""
        df = pd.DataFrame({
            'Subject_ID': ['s1'],
            'Group': ['Control'],
            'X_RR': [0.5],
            'Y_DET': [0.6],
            'COMBINED_ENT': [0.7]
        })
        df_std = RQADataValidator.standardize_dataframe(df)

        assert 'subject_id' in df_std.columns
        assert 'group' in df_std.columns
        assert 'x_rr' in df_std.columns
        assert 'y_det' in df_std.columns
        assert 'combined_ent' in df_std.columns

    def test_standardize_dataframe_group_values(self):
        """测试group列值标准化"""
        df = pd.DataFrame({
            'Group': ['Control', 'Mci', 'Ad', 'CONTROL', 'MCI', 'AD']
        })
        df_std = RQADataValidator.standardize_dataframe(df)

        expected = ['control', 'mci', 'ad', 'control', 'mci', 'ad']
        assert all(df_std['group'] == expected)

    def test_standardize_dataframe_subject_id(self):
        """测试subject_id标准化"""
        df = pd.DataFrame({
            'Subject_ID': ['Control_Legacy_1', 'MCI_LEGACY_2', 'Ad_Legacy_3']
        })
        df_std = RQADataValidator.standardize_dataframe(df)

        expected = ['control_legacy_1', 'mci_legacy_2', 'ad_legacy_3']
        assert all(df_std['subject_id'] == expected)

    def test_standardize_dataframe_no_group(self):
        """测试没有group列的情况"""
        df = pd.DataFrame({
            'Subject_ID': ['s1'],
            'X_RR': [0.5]
        })
        df_std = RQADataValidator.standardize_dataframe(df)

        assert 'subject_id' in df_std.columns
        assert 'x_rr' in df_std.columns

    def test_standardize_dataframe_empty(self):
        """测试空DataFrame"""
        df = pd.DataFrame()
        df_std = RQADataValidator.standardize_dataframe(df)

        assert len(df_std) == 0
        assert len(df_std.columns) == 0

    # ========== validate_rqa_features_dataframe测试 ==========

    def test_validate_rqa_features_valid(self):
        """测试有效的RQA特征DataFrame"""
        df = pd.DataFrame({
            'subject_id': ['control_1', 'mci_1', 'ad_1'],
            'group': ['control', 'mci', 'ad'],
            'x_RR': [0.5, 0.6, 0.7],
            'y_DET': [0.7, 0.8, 0.9],
            'combined_ENT': [2.1, 2.3, 2.5]
        })
        is_valid, error = RQADataValidator.validate_rqa_features_dataframe(df)
        assert is_valid is True
        assert error is None

    def test_validate_rqa_features_missing_subject_id(self):
        """测试缺少subject_id列"""
        df = pd.DataFrame({
            'group': ['control'],
            'x_RR': [0.5]
        })
        is_valid, error = RQADataValidator.validate_rqa_features_dataframe(df)
        assert is_valid is False
        assert 'subject_id' in error

    def test_validate_rqa_features_missing_group(self):
        """测试缺少group列"""
        df = pd.DataFrame({
            'subject_id': ['s1'],
            'x_RR': [0.5]
        })
        is_valid, error = RQADataValidator.validate_rqa_features_dataframe(df)
        assert is_valid is False
        assert 'group' in error

    def test_validate_rqa_features_no_rqa_columns(self):
        """测试缺少RQA特征列"""
        df = pd.DataFrame({
            'subject_id': ['s1'],
            'group': ['control'],
            'age': [25],
            'gender': ['M']
        })
        is_valid, error = RQADataValidator.validate_rqa_features_dataframe(df)
        assert is_valid is False
        assert 'RQA特征列' in error

    @pytest.mark.parametrize("invalid_group", ['invalid', 'test', 'unknown'])
    def test_validate_rqa_features_invalid_groups(self, invalid_group):
        """测试无效的分组值"""
        df = pd.DataFrame({
            'subject_id': ['s1'],
            'group': [invalid_group],
            'x_RR': [0.5]
        })
        is_valid, error = RQADataValidator.validate_rqa_features_dataframe(df)
        assert is_valid is False
        assert invalid_group in error

    def test_validate_rqa_features_uppercase_groups(self):
        """测试大写分组值会被标准化"""
        df = pd.DataFrame({
            'subject_id': ['s1'],
            'group': ['Control'],  # 大写会被标准化为小写
            'x_RR': [0.5]
        })
        is_valid, error = RQADataValidator.validate_rqa_features_dataframe(df)
        # 应该通过，因为会被标准化为control
        assert is_valid is True

    def test_validate_rqa_features_with_rqa_prefix(self):
        """测试带rqa_前缀的特征列"""
        df = pd.DataFrame({
            'subject_id': ['s1'],
            'group': ['control'],
            'rqa_metric1': [0.5],
            'rqa_metric2': [0.6]
        })
        is_valid, error = RQADataValidator.validate_rqa_features_dataframe(df)
        assert is_valid is True

    # ========== get_step_file_path测试 ==========

    def test_get_step_file_path_all_steps(self):
        """测试所有步骤的文件路径"""
        param_dir = Path('/test/params')

        # Step 1
        result = RQADataValidator.get_step_file_path(param_dir, 1, 'test.csv')
        assert result == param_dir / 'step1_rqa_features' / 'test.csv'

        # Step 2
        result = RQADataValidator.get_step_file_path(param_dir, 2, 'test.csv')
        assert result == param_dir / 'step2_data_merging' / 'test.csv'

        # Step 3
        result = RQADataValidator.get_step_file_path(param_dir, 3, 'test.csv')
        assert result == param_dir / 'step3_feature_enrichment' / 'test.csv'

        # Step 4
        result = RQADataValidator.get_step_file_path(param_dir, 4, 'test.csv')
        assert result == param_dir / 'step4_statistical_analysis' / 'test.csv'

        # Step 5
        result = RQADataValidator.get_step_file_path(param_dir, 5, 'test.csv')
        assert result == param_dir / 'step5_visualization' / 'test.csv'

    @pytest.mark.parametrize("invalid_step", [0, 6, -1, 100])
    def test_get_step_file_path_invalid_step(self, invalid_step):
        """测试无效的步骤编号"""
        param_dir = Path('/test/params')
        with pytest.raises(ValueError, match='无效的步骤编号'):
            RQADataValidator.get_step_file_path(param_dir, invalid_step, 'test.csv')


class TestRQAPathManager:
    """RQAPathManager单元测试 - 完整覆盖"""

    @pytest.fixture
    def path_manager(self, tmp_path):
        """创建临时路径管理器"""
        return RQAPathManager(tmp_path)

    def test_init(self, path_manager, tmp_path):
        """测试初始化"""
        assert path_manager.data_root == tmp_path
        assert path_manager.results_dir == tmp_path / '05_rqa_analysis' / 'results'

    def test_get_enriched_features_file(self, path_manager):
        """测试获取enriched_features文件路径"""
        param_dir = Path('/test/params')
        expected = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'
        result = path_manager.get_enriched_features_file(param_dir)
        assert result == expected

    def test_get_merged_features_file(self, path_manager):
        """测试获取merged_features文件路径"""
        param_dir = Path('/test/params')
        expected = param_dir / 'step2_data_merging' / 'merged_rqa_features.csv'
        result = path_manager.get_merged_features_file(param_dir)
        assert result == expected

    def test_get_group_comparison_file(self, path_manager):
        """测试获取group_comparison文件路径"""
        param_dir = Path('/test/params')
        expected = param_dir / 'step4_statistical_analysis' / 'group_comparison.csv'
        result = path_manager.get_group_comparison_file(param_dir)
        assert result == expected

    def test_get_visualization_dir(self, path_manager):
        """测试获取可视化目录路径"""
        param_dir = Path('/test/params')
        expected = param_dir / 'step5_visualization' / 'statistical_plots'
        result = path_manager.get_visualization_dir(param_dir)
        assert result == expected

    def test_ensure_step_directories(self, path_manager, tmp_path):
        """测试确保步骤目录存在"""
        param_dir = tmp_path / 'test_params'
        param_dir.mkdir()

        path_manager.ensure_step_directories(param_dir)

        # 验证所有步骤目录已创建
        for step_num in range(1, 6):
            step_file = RQADataValidator.get_step_file_path(param_dir, step_num, 'dummy')
            assert step_file.parent.exists()


@pytest.mark.integration
class TestValidatorsIntegration:
    """Validators模块集成测试"""

    def test_full_workflow(self, tmp_path):
        """测试完整的验证工作流"""
        # 1. 验证参数
        params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}
        is_valid, _ = RQADataValidator.validate_rqa_params(params)
        assert is_valid

        # 2. 验证分组
        groups = ['control', 'mci', 'ad']
        is_valid, _ = RQADataValidator.validate_groups(groups)
        assert is_valid

        # 3. 创建和验证DataFrame
        df = pd.DataFrame({
            'Subject_ID': ['Control_1', 'Mci_2', 'Ad_3'],
            'Group': ['Control', 'Mci', 'Ad'],
            'X_RR': [0.5, 0.6, 0.7],
            'Y_DET': [0.8, 0.85, 0.9]
        })

        # 4. 标准化DataFrame
        df_std = RQADataValidator.standardize_dataframe(df)

        # 5. 验证标准化后的DataFrame
        is_valid, _ = RQADataValidator.validate_rqa_features_dataframe(df_std)
        assert is_valid

        # 6. 使用路径管理器
        path_manager = RQAPathManager(tmp_path)
        param_dir = tmp_path / 'test_param'
        param_dir.mkdir()

        enriched_file = path_manager.get_enriched_features_file(param_dir)
        assert 'enriched_features.csv' in str(enriched_file)
