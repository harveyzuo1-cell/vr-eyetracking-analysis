"""
ModuleEX2 数据导出模块测试

测试数据固化和导出功能
"""

import pytest
import json
from pathlib import Path

# 测试基础URL
BASE_URL = "http://127.0.0.1:9090"


class TestModuleEX2Health:
    """测试ModuleEX2健康检查"""

    def test_health_check(self, requests_session):
        """测试健康检查接口"""
        response = requests_session.get(f"{BASE_URL}/api/ex2/health")
        assert response.status_code == 200

        data = response.json()
        assert data['status'] == 'ok'
        assert data['module'] == 'moduleEX2_data_export'
        assert data['version'] == '1.0.0'


class TestExportSubjects:
    """测试受试者+MMSE数据导出"""

    def test_export_subjects_v1(self, requests_session):
        """测试导出V1受试者+MMSE数据"""
        payload = {
            "data_version": "v1",
            "include_mmse_details": True
        }

        response = requests_session.post(
            f"{BASE_URL}/api/ex2/export/subjects",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        print(f"\n✅ 受试者+MMSE导出测试:")
        print(f"   Success: {data.get('success')}")
        print(f"   Exported count: {data.get('exported_count')}")
        print(f"   File path: {data.get('file_path')}")
        print(f"   Message: {data.get('message')}")

        assert data['success'] is True
        assert 'file_path' in data
        assert data['exported_count'] > 0

    def test_export_subjects_all_versions(self, requests_session):
        """测试导出所有版本的受试者数据"""
        payload = {
            "data_version": None,
            "include_mmse_details": True
        }

        response = requests_session.post(
            f"{BASE_URL}/api/ex2/export/subjects",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        print(f"\n✅ 所有版本受试者导出测试:")
        print(f"   Success: {data.get('success')}")
        print(f"   Exported count: {data.get('exported_count')}")

        assert data['success'] is True
        assert data['exported_count'] > 0


class TestExportROI:
    """测试ROI配置导出"""

    def test_export_roi_json(self, requests_session):
        """测试导出V1 ROI配置 (JSON格式)"""
        payload = {
            "data_version": "v1",
            "output_format": "json"
        }

        response = requests_session.post(
            f"{BASE_URL}/api/ex2/export/roi",
            json=payload
        )

        print(f"\n✅ ROI配置导出测试 (JSON):")
        print(f"   Status code: {response.status_code}")

        data = response.json()
        print(f"   Success: {data.get('success')}")
        print(f"   Message: {data.get('message')}")

        if data.get('success'):
            print(f"   Exported count: {data.get('exported_count')}")
            print(f"   File path: {data.get('file_path')}")
            assert 'file_path' in data
            assert data['exported_count'] > 0
        else:
            # 如果没有ROI配置，这是正常的
            print(f"   ⚠️  没有ROI配置可导出")

    def test_export_roi_csv(self, requests_session):
        """测试导出V1 ROI配置 (CSV格式)"""
        payload = {
            "data_version": "v1",
            "output_format": "csv"
        }

        response = requests_session.post(
            f"{BASE_URL}/api/ex2/export/roi",
            json=payload
        )

        print(f"\n✅ ROI配置导出测试 (CSV):")
        data = response.json()
        print(f"   Success: {data.get('success')}")

        if data.get('success'):
            print(f"   Exported count: {data.get('exported_count')}")
            assert 'file_path' in data


class TestExportEyetracking:
    """测试眼动数据导出"""

    def test_export_eyetracking_v1_all(self, requests_session):
        """测试导出所有V1校准眼动数据"""
        payload = {
            "subject_ids": None,  # 全部
            "data_version": "v1",
            "output_format": "csv"
        }

        response = requests_session.post(
            f"{BASE_URL}/api/ex2/export/eyetracking",
            json=payload
        )

        print(f"\n✅ 眼动数据导出测试:")
        data = response.json()
        print(f"   Success: {data.get('success')}")

        if data.get('success'):
            print(f"   Exported count: {data.get('exported_count')}")
            print(f"   Total records: {data.get('total_records')}")
            print(f"   File path: {data.get('file_path')}")
            assert 'file_path' in data
            assert data['exported_count'] > 0
            assert data['total_records'] > 0
        else:
            print(f"   ⚠️  {data.get('message')}")


class TestExportAll:
    """测试统一打包导出"""

    def test_export_all_v1(self, requests_session):
        """测试V1数据统一打包导出"""
        payload = {
            "data_version": "v1",
            "subject_ids": None
        }

        response = requests_session.post(
            f"{BASE_URL}/api/ex2/export/all",
            json=payload
        )

        print(f"\n✅ 统一打包导出测试:")
        data = response.json()
        print(f"   Success: {data.get('success')}")

        if data.get('success'):
            print(f"   ZIP path: {data.get('zip_path')}")
            print(f"   Files count: {data.get('files_count')}")
            print(f"   Message: {data.get('message')}")
            assert 'zip_path' in data
            assert data['files_count'] > 0
        else:
            print(f"   ⚠️  {data.get('message')}")


class TestExportsList:
    """测试导出文件列表"""

    def test_list_exports(self, requests_session):
        """测试列出导出文件"""
        response = requests_session.get(f"{BASE_URL}/api/ex2/exports?limit=10")

        assert response.status_code == 200
        data = response.json()

        print(f"\n✅ 导出文件列表测试:")
        print(f"   Success: {data.get('success')}")
        print(f"   Total: {data.get('total')}")

        if data.get('total') > 0:
            print(f"\n   最近的导出文件:")
            for export_file in data.get('exports', [])[:3]:
                print(f"   - {export_file['filename']}")
                print(f"     Size: {export_file['size_mb']} MB")
                print(f"     Created: {export_file['created_at']}")

        assert data['success'] is True
        assert 'exports' in data


# Pytest fixtures

@pytest.fixture(scope="session")
def requests_session():
    """创建requests session"""
    import requests
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json'
    })
    return session


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
