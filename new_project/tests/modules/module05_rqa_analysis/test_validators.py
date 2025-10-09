"""
Module05 RQA分析单元测试 - Validators模块
"""

import pytest
import pandas as pd
from pathlib import Path

from src.modules.module05_rqa_analysis.validators import (
    RQADataValidator,
    RQAPathManager
)


class TestRQADataValidator:
    """RQADataValidator单元测试"""

    def test_validate_rqa_params_valid(self):
        """测试有效的RQA参数"""
        params = {'m': 2, 'tau': 1, 'eps': 0.05, 'lmin': 2}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is True
        assert error is None

    def test_validate_rqa_params_missing_key(self):
        """测试缺少必需参数"""
        params = {'m': 2, 'tau': 1, 'eps': 0.05}
        is_valid, error = RQADataValidator.validate_rqa_params(params)
        assert is_valid is False
        assert 'lmin' in error

    def test_validate_groups_valid(self):
        """测试有效的分组列表"""
        groups = ['control', 'mci', 'ad']
        is_valid, error = RQADataValidator.validate_groups(groups)
        assert is_valid is True
        assert error is None

    def test_standardize_dataframe(self):
        """测试DataFrame标准化"""
        df = pd.DataFrame({
            'Subject_ID': ['s1'],
            'Group': ['Control'],
            'X_RR': [0.5]
        })
        df_std = RQADataValidator.standardize_dataframe(df)
        
        assert 'subject_id' in df_std.columns
        assert 'group' in df_std.columns
        assert all(df_std['group'] == ['control'])


class TestRQAPathManager:
    """RQAPathManager单元测试"""

    @pytest.fixture
    def path_manager(self, tmp_path):
        """创建临时路径管理器"""
        return RQAPathManager(tmp_path)

    def test_get_enriched_features_file(self, path_manager):
        """测试获取enriched_features文件路径"""
        param_dir = Path('/test/params')
        expected = param_dir / 'step3_feature_enrichment' / 'enriched_features.csv'
        result = path_manager.get_enriched_features_file(param_dir)
        assert result == expected
