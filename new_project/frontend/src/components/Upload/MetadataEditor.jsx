import React from 'react';
import { Form, Select, Input, Card } from 'antd';

const { TextArea } = Input;

const MetadataEditor = ({ form, onChange }) => {
  const handleValuesChange = (changedValues, allValues) => {
    if (onChange) {
      onChange(allValues);
    }
  };

  return (
    <Card title="元数据编辑">
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        initialValues={{
          group: undefined,
          subject_id: '',
          task_id: undefined,
          notes: ''
        }}
      >
        <Form.Item
          label="组别"
          name="group"
          rules={[
            { required: true, message: '请选择组别' }
          ]}
        >
          <Select placeholder="请选择组别" size="large">
            <Select.Option value="control">对照组 (Control)</Select.Option>
            <Select.Option value="mci">轻度认知障碍组 (MCI)</Select.Option>
            <Select.Option value="ad">阿尔茨海默症组 (AD)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="受试者ID"
          name="subject_id"
          rules={[
            { required: true, message: '请输入受试者ID' },
            { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和连字符' }
          ]}
        >
          <Input
            placeholder="例如: s001, sub001"
            size="large"
            maxLength={20}
          />
        </Form.Item>

        <Form.Item
          label="任务ID"
          name="task_id"
          rules={[
            { required: true, message: '请选择任务' }
          ]}
        >
          <Select placeholder="请选择任务" size="large">
            <Select.Option value="q1">Q1 - 时间定向</Select.Option>
            <Select.Option value="q2">Q2 - 空间定向</Select.Option>
            <Select.Option value="q3">Q3 - 即刻记忆</Select.Option>
            <Select.Option value="q4">Q4 - 注意力与计算</Select.Option>
            <Select.Option value="q5">Q5 - 延迟回忆</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="备注"
          name="notes"
        >
          <TextArea
            rows={4}
            placeholder="可选：添加关于此次数据采集的备注信息"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>
    </Card>
  );
};

export default MetadataEditor;
