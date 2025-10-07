/**
 * ROI配置导出组件
 */

import React, { useState } from 'react';
import { Card, Form, Select, Button, Alert, message } from 'antd';
import { DownloadOutlined, FileTextOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const ROIExport = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleExport = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/ex2/export/roi', values);
      if (response.data.success) {
        message.success('ROI配置导出成功！');
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

  return (
    <div>
      <Alert message="ROI配置导出" description="导出ModuleEX中配置的ROI信息，支持JSON和CSV格式" type="info" showIcon style={{ marginBottom: 24 }} />
      <Card title="导出设置">
        <Form form={form} layout="vertical" onFinish={handleExport} initialValues={{ data_version: 'v1', output_format: 'json' }}>
          <Form.Item label="数据版本" name="data_version"><Select size="large"><Option value="v1">V1 (已实现)</Option><Option value="v2" disabled>V2 (保留接口)</Option></Select></Form.Item>
          <Form.Item label="输出格式" name="output_format"><Select size="large"><Option value="json">JSON (保留完整结构)</Option><Option value="csv">CSV (展开为表格)</Option></Select></Form.Item>
          <Form.Item><Button type="primary" size="large" htmlType="submit" icon={<FileTextOutlined />} loading={loading} block>{loading ? '正在导出...' : '开始导出'}</Button></Form.Item>
        </Form>
      </Card>
      {result && (
        <Card title="导出完成" style={{ marginTop: 24 }}>
          <p>导出了 {result.exported_count} 个任务的ROI配置</p>
          <Button type="primary" icon={<DownloadOutlined />} onClick={() => window.open(`/api/ex2/download/${result.file_path.split('/').pop()}`, '_blank')} size="large">下载文件</Button>
        </Card>
      )}
    </div>
  );
};

export default ROIExport;
