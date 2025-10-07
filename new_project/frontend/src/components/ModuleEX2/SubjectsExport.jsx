/**
 * 受试者+MMSE导出组件
 */

import React, { useState } from 'react';
import { Card, Form, Select, Switch, Button, Alert, message, Typography } from 'antd';
import { DownloadOutlined, UserOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { Text } = Typography;

const SubjectsExport = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleExport = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/ex2/export/subjects', values);
      if (response.data.success) {
        message.success('受试者数据导出成功！');
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
      <Alert message="受试者信息+MMSE评分导出" description="导出受试者基本信息和MMSE评分 (19题，满分21分)，包含所有子题目详情" type="info" showIcon style={{ marginBottom: 24 }} />
      <Card title="导出设置">
        <Form form={form} layout="vertical" onFinish={handleExport} initialValues={{ data_version: 'v1', include_mmse_details: true }}>
          <Form.Item label="数据版本" name="data_version">
            <Select size="large">
              <Option value="v1">V1 (旧数据)</Option>
              <Option value="v2">V2 (新数据)</Option>
              <Option value={null}>全部版本</Option>
            </Select>
          </Form.Item>
          <Form.Item label="包含MMSE子题目详情" name="include_mmse_details" valuePropName="checked">
            <Switch checkedChildren="包含" unCheckedChildren="不包含" />
          </Form.Item>
          <Alert
            message="MMSE子题目说明"
            description={
              <div>
                <Text>• Q1: 定向力-时间 (5题, q1_weekday 2分, 其他1分)</Text><br/>
                <Text>• Q2: 定向力-地点 (5题, q2_province 2分, 其他1分)</Text><br/>
                <Text>• Q3: 即刻记忆 (1题, 0-3分)</Text><br/>
                <Text>• Q4: 注意力和计算 (5题, 各1分)</Text><br/>
                <Text>• Q5: 延迟回忆 (3题, 各1分)</Text><br/>
                <Text strong>总分: 21分</Text>
              </div>
            }
            type="info"
            style={{ marginBottom: 16 }}
          />
          <Form.Item>
            <Button type="primary" size="large" htmlType="submit" icon={<UserOutlined />} loading={loading} block>
              {loading ? '正在导出...' : '开始导出'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
      {result && (
        <Card title="导出完成" style={{ marginTop: 24 }}>
          <p>成功导出 {result.exported_count} 个受试者的信息和MMSE评分</p>
          <Button type="primary" icon={<DownloadOutlined />} onClick={() => window.open(`/api/ex2/download/${result.file_path.split('/').pop()}`, '_blank')} size="large">下载CSV文件</Button>
        </Card>
      )}
    </div>
  );
};

export default SubjectsExport;
