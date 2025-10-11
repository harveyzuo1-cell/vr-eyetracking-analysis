import React, { useState } from 'react';
import { Card, Button, Select, Space, Table, Tag, Statistic, Row, Col, message, Spin } from 'antd';
import { PlayCircleOutlined, DatabaseOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

/**
 * 敏感度分析面板
 *
 * 功能:
 * - 运行 Module04/Module05 的敏感度分析
 * - 展示统计指标（F值、Eta²、Cohen's d、p-value、CV）
 * - 按综合评分排序显示特征
 */
const SensitivityAnalysisPanel = () => {
  const [module, setModule] = useState('m04');
  const [dataVersion, setDataVersion] = useState('v1');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  // 运行敏感度分析
  const handleRunAnalysis = async () => {
    setLoading(true);
    try {
      const endpoint = module === 'm04'
        ? '/api/m06/m04/sensitivity/compute'
        : '/api/m06/m05/sensitivity/compute';

      const params = module === 'm04'
        ? { data_version: dataVersion, use_cache: true }
        : { mode: 'cross_param', use_cache: true };

      const response = await axios.post(`http://127.0.0.1:9090${endpoint}`, params);

      if (response.data.success) {
        setResults(response.data.data);
        message.success(`${module.toUpperCase()} 敏感度分析完成！`);
      } else {
        message.error(`分析失败: ${response.data.error}`);
      }
    } catch (error) {
      message.error(`请求失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Module04 表格列定义
  const m04Columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank) => <Tag color={rank <= 4 ? 'gold' : 'default'}>{rank}</Tag>,
    },
    {
      title: '特征名称',
      dataIndex: 'feature',
      key: 'feature',
      width: 200,
      render: (feature, record) => (
        <Space direction="vertical" size={0}>
          <strong>{feature}</strong>
          {record.rank <= 4 && <Tag color="green">Top-4 已选择</Tag>}
        </Space>
      ),
    },
    {
      title: '综合评分',
      dataIndex: 'score',
      key: 'score',
      width: 120,
      sorter: (a, b) => a.score - b.score,
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
    {
      title: 'CV (%)',
      dataIndex: 'cv',
      key: 'cv',
      width: 100,
      render: (value) => value?.toFixed(2) || 'N/A',
    },
  ];

  // Module05 表格列定义
  const m05Columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank) => <Tag color={rank <= 6 ? 'gold' : 'default'}>{rank}</Tag>,
    },
    {
      title: 'RQA 特征',
      dataIndex: 'feature',
      key: 'feature',
      width: 180,
      render: (feature, record) => (
        <Space direction="vertical" size={0}>
          <strong>{feature}</strong>
          {record.rank <= 6 && <Tag color="green">Top-6 已选择</Tag>}
        </Space>
      ),
    },
    {
      title: '综合评分',
      dataIndex: 'score',
      key: 'score',
      width: 120,
      sorter: (a, b) => a.score - b.score,
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
    {
      title: 'CV (%)',
      dataIndex: 'cv',
      key: 'cv',
      width: 100,
      render: (value) => value?.toFixed(2) || 'N/A',
    },
  ];

  // 准备表格数据 - 转换后端字段到前端格式
  const tableData = results?.all_features?.map((item, index) => ({
    key: index,
    rank: item.rank || index + 1,
    feature: item.feature_name,
    score: item.sensitivity_score,
    f_value: item.f_statistic,
    eta_squared: item.eta_squared,
    cohens_d: item.avg_cohens_d,
    p_value: item.p_value,
    cv: item.avg_cv,
  })) || [];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 控制区域 */}
      <Card>
        <Space size="middle">
          <span><DatabaseOutlined /> 选择模块:</span>
          <Select value={module} onChange={setModule} style={{ width: 150 }}>
            <Option value="m04">Module04 (眼动事件)</Option>
            <Option value="m05">Module05 (RQA)</Option>
          </Select>

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
            icon={<PlayCircleOutlined />}
            onClick={handleRunAnalysis}
            loading={loading}
          >
            运行分析
          </Button>
        </Space>
      </Card>

      {/* 统计摘要 */}
      {results && (
        <Card title="分析摘要">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="总特征数"
                value={results.summary?.total_features_analyzed || results.total_features || 0}
                suffix="个"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="样本数量"
                value={results.summary?.total_samples || results.sample_count || 'N/A'}
                suffix="个"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="分析模式"
                value={results.mode || module.toUpperCase()}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="数据版本"
                value={results.params?.data_version || results.data_version || 'N/A'}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 敏感度分析结果表格 */}
      {loading ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" tip="正在分析特征敏感度..." />
          </div>
        </Card>
      ) : results ? (
        <Card title={`${module.toUpperCase()} 敏感度排序结果`}>
          <Table
            columns={module === 'm04' ? m04Columns : m05Columns}
            dataSource={tableData}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 1000 }}
            size="small"
          />
        </Card>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            请选择模块并点击"运行分析"开始敏感度分析
          </div>
        </Card>
      )}
    </Space>
  );
};

export default SensitivityAnalysisPanel;
