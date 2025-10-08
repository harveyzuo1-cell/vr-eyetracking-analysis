/**
 * RQA参数配置面板
 * 配置 m, tau, eps, lmin 参数范围
 */
import React, { useState, useMemo, useCallback } from 'react';
import {
  Card, Row, Col, Form, InputNumber, Button, Statistic, message, Space, Divider, Alert
} from 'antd';
import { ThunderboltOutlined, CalculatorOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import axios from 'axios';

const ParamConfigPanel = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [paramRanges, setParamRanges] = useState({
    m: { start: 1, end: 4, step: 1 },
    tau: { start: 1, end: 8, step: 1 },
    eps: { start: 0.050, end: 0.100, step: 0.005 },
    lmin: { start: 2, end: 3, step: 1 }
  });

  // 使用useMemo计算参数组合总数
  const totalCombinations = useMemo(() => {
    const { m, tau, eps, lmin } = paramRanges;

    const mCount = Math.floor((m.end - m.start) / m.step) + 1;
    const tauCount = Math.floor((tau.end - tau.start) / tau.step) + 1;
    const epsCount = Math.round((eps.end - eps.start) / eps.step) + 1;
    const lminCount = Math.floor((lmin.end - lmin.start) / lmin.step) + 1;

    return mCount * tauCount * epsCount * lminCount;
  }, [paramRanges]);

  // 使用useCallback优化事件处理
  const handleValuesChange = useCallback((changedValues) => {
    setParamRanges(prev => {
      const newRanges = { ...prev };
      Object.keys(changedValues).forEach(key => {
        const [param, field] = key.split('_');
        if (newRanges[param]) {
          newRanges[param] = { ...newRanges[param], [field]: changedValues[key] };
        }
      });
      return newRanges;
    });
  }, []);

  const handleGenerate = useCallback(async () => {
    try {
      setLoading(true);

      const response = await axios.post('/api/m05/params/generate', {
        m_range: paramRanges.m,
        tau_range: paramRanges.tau,
        eps_range: paramRanges.eps,
        lmin_range: paramRanges.lmin
      });

      if (response.data.success) {
        message.success(`成功生成 ${response.data.total_combinations} 个参数组合`);
      } else {
        message.error('生成参数组合失败: ' + (response.data.error || '未知错误'));
      }
    } catch (error) {
      console.error('生成参数组合失败:', error);
      message.error('生成参数组合失败: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  }, [paramRanges]);

  const ParamRangeInput = useCallback(({ label, param }) => (
    <Card size="small" title={label} style={{ height: '100%' }}>
      <Form.Item
        label="起始值"
        name={`${param}_start`}
        initialValue={paramRanges[param].start}
      >
        <InputNumber style={{ width: '100%' }} step={param === 'eps' ? 0.001 : 1} />
      </Form.Item>
      <Form.Item
        label="结束值"
        name={`${param}_end`}
        initialValue={paramRanges[param].end}
      >
        <InputNumber style={{ width: '100%' }} step={param === 'eps' ? 0.001 : 1} />
      </Form.Item>
      <Form.Item
        label="步长"
        name={`${param}_step`}
        initialValue={paramRanges[param].step}
      >
        <InputNumber style={{ width: '100%' }} step={param === 'eps' ? 0.001 : 1} min={0.001} />
      </Form.Item>
    </Card>
  ), [paramRanges]);

  ParamRangeInput.propTypes = {
    label: PropTypes.string.isRequired,
    param: PropTypes.string.isRequired
  };

  return (
    <div>
      <Alert
        message="RQA参数说明"
        description={
          <div>
            <p><strong>m (嵌入维度)</strong>: 时间延迟嵌入的维度，通常取 1-20</p>
            <p><strong>τ (时间延迟)</strong>: 时间序列的延迟步数，通常取 1-20</p>
            <p><strong>ε (递归阈值)</strong>: 判定两点是否递归的距离阈值，通常取 0.01-1.0</p>
            <p><strong>lmin (最小线长)</strong>: 计算 DET 和 ENT 的最小对角线长度，通常取 2-10</p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
      >
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <ParamRangeInput label="嵌入维度 (m)" param="m" />
          </Col>
          <Col span={6}>
            <ParamRangeInput label="时间延迟 (τ)" param="tau" />
          </Col>
          <Col span={6}>
            <ParamRangeInput label="递归阈值 (ε)" param="eps" />
          </Col>
          <Col span={6}>
            <ParamRangeInput label="最小线长 (lmin)" param="lmin" />
          </Col>
        </Row>
      </Form>

      <Divider />

      <div style={{ textAlign: 'center', padding: '24px 0' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Statistic
            title="预计生成参数组合数量"
            value={totalCombinations}
            prefix={<CalculatorOutlined />}
            valueStyle={{ color: '#1890ff', fontSize: 48 }}
          />

          <Alert
            message={`当前配置将生成 ${totalCombinations.toLocaleString()} 个参数组合`}
            description={
              totalCombinations > 1000
                ? '⚠️ 参数组合数量较大，建议适当减少范围或增加步长'
                : '✅ 参数组合数量合理'
            }
            type={totalCombinations > 1000 ? 'warning' : 'success'}
            showIcon
          />

          <Button
            type="primary"
            size="large"
            icon={<ThunderboltOutlined />}
            onClick={handleGenerate}
            loading={loading}
          >
            生成参数组合
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default ParamConfigPanel;
