"""
校正服务单元测试
Calibration Service Unit Tests
"""
import pytest
import pandas as pd
import tempfile
import json
from pathlib import Path

from src.web.modules.module01_data_visualization.calibration_service import CalibrationService
from src.web.modules.module01_data_visualization.calibration_validator import CalibrationValidator


@pytest.fixture
def temp_data_root(tmp_path):
    """创建临时数据目录"""
    raw_dir = tmp_path / "01_raw" / "control"
    raw_dir.mkdir(parents=True)

    processed_dir = tmp_path / "02_processed"
    processed_dir.mkdir(parents=True)

    return tmp_path


@pytest.fixture
def service(temp_data_root, monkeypatch):
    """创建测试用CalibrationService实例"""
    # Mock Config.DATA_ROOT
    monkeypatch.setattr('config.settings.Config.DATA_ROOT', str(temp_data_root))

    return CalibrationService()


@pytest.fixture
def sample_data():
    """示例眼动数据"""
    return pd.DataFrame({
        'x': [0.1, 0.2, 0.3, 0.4, 0.5],
        'y': [0.1, 0.2, 0.3, 0.4, 0.5],
        'timestamp': [0, 0.1, 0.2, 0.3, 0.4]
    })


@pytest.fixture
def sample_raw_file(temp_data_root, sample_data):
    """创建示例原始数据文件"""
    raw_file = temp_data_root / "01_raw" / "control" / "S001_q1.csv"
    sample_data.to_csv(raw_file, index=False)
    return raw_file


class TestCalibrationService:
    """CalibrationService单元测试"""

    def test_init(self, service, temp_data_root):
        """测试初始化"""
        assert service.data_root == temp_data_root
        assert service.raw_dir == temp_data_root / '01_raw'
        assert service.processed_dir == temp_data_root / '02_processed'
        assert service.processed_dir.exists()

    def test_apply_position_offset_x(self, service, sample_data):
        """测试X轴位置偏移"""
        result = service.apply_position_offset(sample_data, offset_x=0.01, offset_y=0)

        assert result['x'].iloc[0] == pytest.approx(0.11)
        assert result['y'].iloc[0] == pytest.approx(0.1)

    def test_apply_position_offset_y(self, service, sample_data):
        """测试Y轴位置偏移"""
        result = service.apply_position_offset(sample_data, offset_x=0, offset_y=-0.02)

        assert result['x'].iloc[0] == pytest.approx(0.1)
        assert result['y'].iloc[0] == pytest.approx(0.08)

    def test_apply_position_offset_both(self, service, sample_data):
        """测试同时X和Y轴偏移"""
        result = service.apply_position_offset(
            sample_data,
            offset_x=0.05,
            offset_y=0.03
        )

        assert result['x'].iloc[0] == pytest.approx(0.15)
        assert result['y'].iloc[0] == pytest.approx(0.13)

    def test_apply_position_offset_empty_data(self, service):
        """测试空数据"""
        empty_df = pd.DataFrame()
        result = service.apply_position_offset(empty_df, 0.01, 0.02)

        assert result.empty

    def test_apply_time_trim_start(self, service, sample_data):
        """测试起始时间裁剪"""
        result = service.apply_time_trim(sample_data, trim_start=0.1, trim_end=0)

        # 裁剪掉第一个点（timestamp=0），剩余4个点
        assert len(result) == 4
        assert result['timestamp'].min() == pytest.approx(0)  # 重置后从0开始

    def test_apply_time_trim_end(self, service, sample_data):
        """测试结束时间裁剪"""
        result = service.apply_time_trim(sample_data, trim_start=0, trim_end=0.1)

        # 裁剪掉最后一个点（timestamp=0.4），剩余4个点
        assert len(result) == 4
        assert result['timestamp'].max() <= 0.3

    def test_apply_time_trim_both(self, service, sample_data):
        """测试同时裁剪起始和结束"""
        result = service.apply_time_trim(sample_data, trim_start=0.1, trim_end=0.1)

        # 裁剪掉第一个和最后一个，剩余3个点
        assert len(result) == 3
        assert result['timestamp'].min() == pytest.approx(0)
        assert result['timestamp'].max() <= 0.2

    def test_apply_time_trim_no_trim(self, service, sample_data):
        """测试不裁剪"""
        result = service.apply_time_trim(sample_data, trim_start=0, trim_end=0)

        assert len(result) == len(sample_data)
        pd.testing.assert_frame_equal(result, sample_data)

    def test_save_calibrated_data(self, service, sample_raw_file):
        """测试保存校正数据"""
        params = {
            'offsetX': 0.01,
            'offsetY': -0.02,
            'trimStart': 0.1,
            'trimEnd': 0.1
        }

        result = service.save_calibrated_data(
            group='control',
            subject_id='S001',
            task='q1',
            params=params
        )

        # 验证返回结果
        assert 'output_file' in result
        assert 'params_file' in result
        assert result['points_before'] == 5
        assert result['points_after'] == 3  # 裁剪后3个点

        # 验证文件存在
        assert Path(result['output_file']).exists()
        assert Path(result['params_file']).exists()

        # 验证保存的数据
        calibrated_data = pd.read_csv(result['output_file'])
        assert len(calibrated_data) == 3
        assert calibrated_data['x'].iloc[0] == pytest.approx(0.21)  # 0.2 + 0.01

        # 验证保存的参数
        with open(result['params_file'], 'r') as f:
            saved_params = json.load(f)

        assert saved_params['params'] == params
        assert saved_params['metadata']['subject_id'] == 'S001'
        assert saved_params['metadata']['task'] == 'q1'

    def test_save_calibrated_data_file_not_found(self, service):
        """测试原始文件不存在"""
        with pytest.raises(FileNotFoundError):
            service.save_calibrated_data(
                group='control',
                subject_id='NONEXISTENT',
                task='q1',
                params={}
            )

    def test_get_saved_params(self, service, sample_raw_file):
        """测试获取已保存的参数"""
        # 先保存
        params = {'offsetX': 0.01, 'offsetY': -0.02}
        service.save_calibrated_data(
            group='control',
            subject_id='S001',
            task='q1',
            params=params
        )

        # 获取
        saved = service.get_saved_params('control', 'S001', 'q1')

        assert saved is not None
        assert saved['params'] == params

    def test_get_saved_params_not_found(self, service):
        """测试获取不存在的参数"""
        result = service.get_saved_params('control', 'NONEXISTENT', 'q1')

        assert result is None

    def test_load_calibrated_data(self, service, sample_raw_file):
        """测试加载校正数据"""
        # 先保存
        service.save_calibrated_data(
            group='control',
            subject_id='S001',
            task='q1',
            params={'offsetX': 0.01}
        )

        # 加载
        data = service.load_calibrated_data('control', 'S001', 'q1')

        assert isinstance(data, list)
        assert len(data) == 5
        assert data[0]['x'] == pytest.approx(0.11)  # 0.1 + 0.01

    def test_load_calibrated_data_not_found(self, service):
        """测试加载不存在的数据"""
        with pytest.raises(FileNotFoundError):
            service.load_calibrated_data('control', 'NONEXISTENT', 'q1')

    def test_delete_calibration(self, service, sample_raw_file):
        """测试删除校正数据"""
        # 先保存
        service.save_calibrated_data(
            group='control',
            subject_id='S001',
            task='q1',
            params={}
        )

        # 删除
        result = service.delete_calibration('control', 'S001', 'q1')

        assert result is True

        # 验证文件已删除
        with pytest.raises(FileNotFoundError):
            service.load_calibrated_data('control', 'S001', 'q1')

    def test_delete_calibration_not_exists(self, service):
        """测试删除不存在的校正"""
        result = service.delete_calibration('control', 'NONEXISTENT', 'q1')

        assert result is False


class TestCalibrationValidator:
    """CalibrationValidator单元测试"""

    def test_validate_calibration_request_valid(self):
        """测试有效请求"""
        data = {
            'group': 'control',
            'subject_id': 'S001',
            'task': 'q1',
            'params': {
                'offsetX': 0.01,
                'offsetY': -0.02,
                'trimStart': 0.1,
                'trimEnd': 0.2
            }
        }

        is_valid, errors = CalibrationValidator.validate_calibration_request(data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_fields(self):
        """测试缺少必需字段"""
        data = {'group': 'control'}

        is_valid, errors = CalibrationValidator.validate_calibration_request(data)

        assert is_valid is False
        assert len(errors) >= 3

    def test_validate_invalid_group(self):
        """测试无效组别"""
        data = {
            'group': 'invalid_group',
            'subject_id': 'S001',
            'task': 'q1',
            'params': {}
        }

        is_valid, errors = CalibrationValidator.validate_calibration_request(data)

        assert is_valid is False
        assert any('group' in err.lower() for err in errors)

    def test_validate_offset_out_of_range(self):
        """测试偏移超出范围"""
        data = {
            'group': 'control',
            'subject_id': 'S001',
            'task': 'q1',
            'params': {
                'offsetX': 1.0,  # 超出 [-0.1, 0.1]
                'offsetY': 0.0
            }
        }

        is_valid, errors = CalibrationValidator.validate_calibration_request(data)

        assert is_valid is False
        assert any('offsetX' in err for err in errors)

    def test_validate_trim_negative(self):
        """测试负数裁剪"""
        data = {
            'group': 'control',
            'subject_id': 'S001',
            'task': 'q1',
            'params': {
                'trimStart': -1.0
            }
        }

        is_valid, errors = CalibrationValidator.validate_calibration_request(data)

        assert is_valid is False
        assert any('trimStart' in err for err in errors)

    def test_validate_trim_excessive_combined(self):
        """测试组合裁剪过度"""
        data = {
            'group': 'control',
            'subject_id': 'S001',
            'task': 'q1',
            'params': {
                'trimStart': 40.0,
                'trimEnd': 30.0  # 合计70 > 60
            }
        }

        is_valid, errors = CalibrationValidator.validate_calibration_request(data)

        assert is_valid is False
        assert any('combined' in err.lower() for err in errors)

    def test_validate_get_params_request(self):
        """测试获取参数请求验证"""
        is_valid, errors = CalibrationValidator.validate_get_params_request(
            'control', 'S001', 'q1'
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_get_params_request_missing(self):
        """测试获取参数请求缺少字段"""
        is_valid, errors = CalibrationValidator.validate_get_params_request(
            '', 'S001', ''
        )

        assert is_valid is False
        assert len(errors) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
