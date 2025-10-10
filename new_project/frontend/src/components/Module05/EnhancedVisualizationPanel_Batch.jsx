/**
 * Module05: 批量可视化分析面板
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Space, Spin, message,
  Statistic, Table, Progress, Tag, Checkbox
} from 'antd';
import {
  BarChartOutlined, RocketOutlined, ThunderboltOutlined,
  CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const EnhancedVisualizationPanelBatch = () => {
  const [availableParams, setAvailableParams] = useState([]);
  const [selectedParams, setSelectedParams] = useState([]);
  const [batchResults, setBatchResults] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);

  useEffect(() => {
    fetchAvailableParams();
  }, []);

  const fetchAvailableParams = async () => {
    try {
      const response = await axios.get('/api/m05/results/list');
      if (response.data.success) {
        setAvailableParams(response.data.results);
      }
    } catch (error) {
      console.error('获取参数列表失败:', error);
    }
  };

  const handleBatchGenerate = async () => {
    if (selectedParams.length === 0) {
      message.warning('请至少选择一个参数组合');
      return;
    }

    setBatchLoading(true);
    setBatchResults(null);

    try {
      const param_list = selectedParams.map(idx => availableParams[idx].params);
      const response = await axios.post('/api/m05/visualization/batch-generate', {
        param_list
      });

      if (response.data.success) {
        setBatchResults(response.data);
        message.success(
          `批量生成完成！总计 ${response.data.total_params} 个参数，` +
          `成功 ${response.data.completed} 个，失败 ${response.data.failed} 个`
        );
      } else {
        message.error('批量生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('批量生成失败:', error);
      message.error('批量生成失败: ' + error.message);
    } finally {
      setBatchLoading(false);
    }
  };

  const columns = [
    {
      title: '选择',
      key: 'select',
      width: 60,
      render: (_, record, index) => (
        <Checkbox
          checked={selectedParams.includes(index)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedParams([...selectedParams, index]);
            } else {
              setSelectedParams(selectedParams.filter(i => i !== index));
            }
          }}
        />
      )
    },
    {
      title: '参数组合',
      dataIndex: 'params',
      key: 'params',
      render: (params) => `m=${params.m}, τ=${params.tau}, ε=${params.eps}, lmin=${params.lmin}`
    },
    {
      title: 'Signature',
      dataIndex: 'signature',
      key: 'signature',
      ellipsis: true
    }
  ];

  const resultColumns = [
    {
      title: '参数组合',
      dataIndex: 'params',
      key: 'params',
      render: (params) => `m=${params.m}, τ=${params.tau}, ε=${params.eps}, lmin=${params.lmin}`
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'status',
      width: 100,
      render: (success) => success ? (
        <Tag icon={<CheckCircleOutlined />} color="success">成功</Tag>
      ) : (
        <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>
      )
    },
    {
      title: '生成文件数',
      dataIndex: 'total_files',
      key: 'total_files',
      width: 120,
      render: (files, record) => record.success ? files : '-'
    },
    {
      title: '错误信息',
      dataIndex: 'error',
      key: 'error',
      ellipsis: true,
      render: (error) => error || '-'
    }
  ];

  return (
    <Spin spinning={batchLoading} tip="批量生成中...">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="可用参数组合"
              value={availableParams.length}
              prefix={<ThunderboltOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="已选择"
              value={selectedParams.length}
              prefix={<RocketOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="每组生成图表数"
              value={6}
              prefix={<BarChartOutlined />}
            />
          </Col>
        </Row>

        <Card title="选择参数组合" size="small">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space>
              <Checkbox
                checked={selectedParams.length === availableParams.length}
                indeterminate={selectedParams.length > 0 && selectedParams.length < availableParams.length}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedParams(availableParams.map((_, idx) => idx));
                  } else {
                    setSelectedParams([]);
                  }
                }}
              >
                全选/取消全选
              </Checkbox>
              <span style={{ marginLeft: 16, color: '#999' }}>
                已选择 {selectedParams.length} / {availableParams.length} 个参数组合
              </span>
            </Space>

            <Table
              dataSource={availableParams}
              columns={columns}
              rowKey={(_, index) => index}
              pagination={{ pageSize: 10 }}
              size="small"
            />

            <Button
              type="primary"
              icon={<RocketOutlined />}
              size="large"
              onClick={handleBatchGenerate}
              loading={batchLoading}
              disabled={selectedParams.length === 0}
            >
              批量生成可视化 ({selectedParams.length} 个参数)
            </Button>
          </Space>
        </Card>

        {batchLoading && (
          <Card title="生成进度">
            <Progress percent={100} status="active" format={() => '正在生成...'} />
          </Card>
        )}

        {batchResults && (
          <Card title="批量生成结果">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic title="总计" value={batchResults.total_params} />
                </Col>
                <Col span={6}>
                  <Statistic title="成功" value={batchResults.completed} valueStyle={{ color: '#3f8600' }} />
                </Col>
                <Col span={6}>
                  <Statistic title="失败" value={batchResults.failed} valueStyle={{ color: '#cf1322' }} />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="成功率"
                    value={(batchResults.completed / batchResults.total_params * 100).toFixed(1)}
                    suffix="%"
                  />
                </Col>
              </Row>

              <Table
                dataSource={batchResults.results}
                columns={resultColumns}
                rowKey={(_, index) => index}
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </Space>
          </Card>
        )}
      </Space>
    </Spin>
  );
};

export default EnhancedVisualizationPanelBatch;
