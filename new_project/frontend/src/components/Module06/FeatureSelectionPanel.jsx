import React, { useState } from 'react';
import { Card, Button, Select, Space, Table, Tag, Statistic, Row, Col, message, InputNumber } from 'antd';
import { SelectOutlined, DatabaseOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

/**
 * 特征选择面板
 *
 * 功能:
 * - 查看 Module04 Top-K 特征
 * - 查看 Module05 Top-K RQA 特征
 * - 支持自定义 K 值
 */
const FeatureSelectionPanel = () => {
  const [module, setModule] = useState('m04');
  const [k, setK] = useState(4);
  const [dataVersion, setDataVersion] = useState('v1');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  // 获取 Top-K 特征
  const handleGetTopK = async () => {
    setLoading(true);
    try {
      const endpoint = module === 'm04'
        ? '/api/m06/features/m04/top-k'
        : '/api/m06/features/m05/top-k';

      const params = module === 'm04'
        ? { k, data_version: dataVersion }
        : { k, mode: 'cross_param' };

      const response = await axios.get(`http://127.0.0.1:9090${endpoint}`, { params });

      if (response.data.success) {
        setResults(response.data.data);
        message.success(`获取 Top-${k} 特征成功！`);
      } else {
        message.error(`获取失败: ${response.data.error}`);
      }
    } catch (error) {
      message.error(`请求失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank) => <Tag color="gold">Top-{rank}</Tag>,
    },
    {
      title: '特征名称',
      dataIndex: 'feature',
      key: 'feature',
      width: 200,
      render: (feature) => <strong>{feature}</strong>,
    },
    {
      title: '综合评分',
      dataIndex: 'score',
      key: 'score',
      width: 120,
      render: (score) => <Statistic value={score} precision={2} valueStyle={{ fontSize: 14 }} />,
    },
    {
      title: 'F 值',
      dataIndex: 'f_value',
      key: 'f_value',
      width: 100,
      render: (value) => value?.toFixed(4) || 'N/A',
    },
    {
      title: 'Eta²',
      dataIndex: 'eta_squared',
      key: 'eta_squared',
      width: 100,
      render: (value) => value?.toFixed(4) || 'N/A',
    },
    {
      title: "Cohen's d",
      dataIndex: 'cohens_d',
      key: 'cohens_d',
      width: 100,
      render: (value) => value?.toFixed(4) || 'N/A',
    },
    {
      title: 'p-value',
      dataIndex: 'p_value',
      key: 'p_value',
      width: 100,
      render: (value) => {
        const pValue = value || 0;
        const color = pValue < 0.001 ? 'green' : pValue < 0.05 ? 'orange' : 'red';
        return <Tag color={color}>{pValue.toExponential(2)}</Tag>;
      },
    },
  ];

  // 准备表格数据
  const tableData = module === 'm04'
    ? results?.top_k?.map((feature, index) => ({
        key: index,
        rank: index + 1,
        feature: feature,
        ...results?.details?.[feature],
      })) || []
    : results?.top_k_features?.map((item, index) => ({
        key: index,
        rank: index + 1,
        ...item,
      })) || [];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 控制区域 */}
      <Card>
        <Space size="middle" wrap>
          <span><DatabaseOutlined /> 选择模块:</span>
          <Select value={module} onChange={(val) => {
            setModule(val);
            setK(val === 'm04' ? 4 : 6);
          }} style={{ width: 150 }}>
            <Option value="m04">Module04 (眼动事件)</Option>
            <Option value="m05">Module05 (RQA)</Option>
          </Select>

          <span>Top-K:</span>
          <InputNumber
            min={1}
            max={module === 'm04' ? 9 : 6}
            value={k}
            onChange={setK}
            style={{ width: 80 }}
          />

          {module === 'm04' && (
            <>
              <span>数据版本:</span>
              <Select value={dataVersion} onChange={setDataVersion} style={{ width: 100 }}>
                <Option value="v1">V1</Option>
                <Option value="v2">V2</Option>
              </Select>
            </>
          )}

          <Button
            type="primary"
            icon={<SelectOutlined />}
            onClick={handleGetTopK}
            loading={loading}
          >
            获取 Top-{k} 特征
          </Button>
        </Space>
      </Card>

      {/* 特征统计摘要 */}
      {results && (
        <Card title="特征摘要">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="选中特征数"
                value={k}
                suffix="个"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="总特征池"
                value={results.total_features}
                suffix="个"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="模块"
                value={module.toUpperCase()}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="数据版本"
                value={results.data_version || 'N/A'}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 特征列表 */}
      {results ? (
        <Card title={`${module.toUpperCase()} Top-${k} 特征列表`}>
          <Table
            columns={columns}
            dataSource={tableData}
            pagination={false}
            size="small"
          />
        </Card>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            请选择模块和 K 值，然后点击"获取 Top-K 特征"
          </div>
        </Card>
      )}

      {/* 使用说明 */}
      <Card title="使用说明" size="small">
        <ul>
          <li><strong>Module04</strong>: 包含 9 个眼动事件特征，推荐 Top-4 用于 Strategy A（10维特征向量）</li>
          <li><strong>Module05</strong>: 包含 6 个 RQA 特征，推荐 Top-6 全部使用</li>
          <li><strong>Strategy A</strong>: 10维特征向量（4 Module04 + 6 Module05），样本特征比 30:1</li>
          <li><strong>Strategy B</strong>: 69维特征向量（9 Module04 + 60 Module05），样本特征比 4.3:1</li>
        </ul>
      </Card>
    </Space>
  );
};

export default FeatureSelectionPanel;
