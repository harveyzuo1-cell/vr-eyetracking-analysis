/**
 * 眼动数据导出组件
 */

import React, { useState } from 'react';
import { Card, Form, Select, Button, Alert, Statistic, Row, Col, message } from 'antd';
import { DownloadOutlined, AimOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const EyetrackingExport = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleExport = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/ex2/export/eyetracking', {
        subject_ids: null,
        data_version: values.data_version,
        output_format: values.output_format
      });

      if (response.data.success) {
        message.success('眼动数据导出成功！');
        setResult(response.data);
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('导出失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (result && result.file_path) {
      const filename = result.file_path.split('/').pop();
      window.open(`/api/ex2/download/${filename}`, '_blank');
    }
  };

  return (
    <div>
      <Alert
        message="校准眼动数据导出"
        description="导出Module01校准后的眼动数据，支持CSV和Excel格式"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card title="导出设置">
        <Form form={form} layout="vertical" onFinish={handleExport} initialValues={{ data_version: 'v1', output_format: 'csv' }}>
          <Form.Item label="数据版本" name="data_version" rules={[{ required: true }]}>
            <Select size="large">
              <Option value="v1">V1 (旧数据)</Option>
              <Option value="v2">V2 (新数据)</Option>
            </Select>
          </Form.Item>

          <Form.Item label="输出格式" name="output_format" rules={[{ required: true }]}>
            <Select size="large">
              <Option value="csv">CSV</Option>
              <Option value="excel">Excel</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" size="large" htmlType="submit" icon={<AimOutlined />} loading={loading} block>
              {loading ? '正在导出...' : '开始导出'}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {result && (
        <Card title="导出完成" style={{ marginTop: 24 }}>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}><Statistic title="导出任务数" value={result.exported_count} /></Col>
            <Col span={8}><Statistic title="总记录数" value={result.total_records} /></Col>
          </Row>
          <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload} size="large">下载文件</Button>
        </Card>
      )}
    </div>
  );
};

export default EyetrackingExport;
