/**
 * 统一打包导出组件
 */

import React, { useState } from 'react';
import {
  Card,
  Form,
  Select,
  Button,
  Space,
  Alert,
  Statistic,
  Row,
  Col,
  Typography,
  Divider,
  message,
  Spin
} from 'antd';
import {
  DownloadOutlined,
  DatabaseOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { Title, Text } = Typography;

const UnifiedExport = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [exportResult, setExportResult] = useState(null);

  // 执行统一导出
  const handleExport = async (values) => {
    setLoading(true);
    setExportResult(null);

    try {
      const response = await axios.post('/api/ex2/export/all', {
        data_version: values.data_version,
        subject_ids: null // 导出全部
      });

      if (response.data.success) {
        message.success('数据导出成功！');
        setExportResult(response.data);
      } else {
        message.error(response.data.message || '导出失败');
      }
    } catch (error) {
      message.error('导出请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 下载导出文件
  const handleDownload = () => {
    if (exportResult && exportResult.zip_path) {
      const filename = exportResult.zip_path.split('/').pop();
      window.open(`/api/ex2/download/${filename}`, '_blank');
    }
  };

  return (
    <div>
      {/* 说明卡片 */}
      <Alert
        message="统一打包导出"
        description="一键导出所有数据到ZIP包，包含：校准眼动数据、ROI配置、受试者信息+MMSE评分"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 导出表单 */}
      <Card title="导出设置" style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleExport}
          initialValues={{
            data_version: 'v1'
          }}
        >
          <Form.Item
            label="数据版本"
            name="data_version"
            rules={[{ required: true, message: '请选择数据版本' }]}
          >
            <Select size="large">
              <Option value="v1">V1 (旧数据)</Option>
              <Option value="v2">V2 (新数据)</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              size="large"
              htmlType="submit"
              icon={<DatabaseOutlined />}
              loading={loading}
              block
            >
              {loading ? '正在导出...' : '开始导出'}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 导出结果 */}
      {exportResult && (
        <Card
          title={
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <span>导出完成</span>
            </Space>
          }
          style={{ marginBottom: 24 }}
        >
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={8}>
              <Statistic
                title="导出文件数"
                value={exportResult.files_count}
                suffix="个"
              />
            </Col>
            <Col span={16}>
              <Statistic
                title="ZIP文件路径"
                value={exportResult.zip_path}
                valueStyle={{ fontSize: 14 }}
              />
            </Col>
          </Row>

          <Divider />

          <Space>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
              size="large"
            >
              下载ZIP包
            </Button>
            <Text type="secondary">{exportResult.message}</Text>
          </Space>
        </Card>
      )}
    </div>
  );
};

export default UnifiedExport;
