/**
 * 可视化分析面板
 * 展示RQA分析结果的统计图表
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  Card, Row, Col, Image, Empty, Button, message, Space, Select, InputNumber, Form,
  Descriptions, Table, Checkbox, Tag
} from 'antd';
import { PictureOutlined, DownloadOutlined, InfoCircleOutlined, BarChartOutlined } from '@ant-design/icons';
import axios from 'axios';
import PropTypes from 'prop-types';

const { Option } = Select;

const VisualizationPanel = () => {
  const [selectedSignature, setSelectedSignature] = useState('m2_tau1_eps0.05_lmin2');
  const [availableParams, setAvailableParams] = useState([]);

  // RQA参数筛选
  const [paramFilters, setParamFilters] = useState({
    m: null,
    tau: null,
    eps: null,
    lmin: null
  });

  // 数据筛选 - 组别和任务
  const [selectedGroups, setSelectedGroups] = useState(['Control', 'MCI', 'AD']);
  const [selectedTasks, setSelectedTasks] = useState(['q1', 'q2', 'q3', 'q4', 'q5']);

  // 从缓存加载可用参数
  useEffect(() => {
    loadAvailableParams();
  }, []);

  const loadAvailableParams = async () => {
    try {
      const response = await axios.get('/api/m05/results/completed');

      // 支持两种响应格式：
      // 1. { data: { completed_results: [...] } }
      // 2. { completed_results: [...] }
      const results = response.data?.data?.completed_results || response.data?.completed_results;

      if (Array.isArray(results) && results.length > 0) {
        setAvailableParams(results);

        // 如果有已完成的结果，默认选择第一个
        const firstParam = results[0];
        const signature = `m${firstParam.m}_tau${firstParam.tau}_eps${firstParam.eps}_lmin${firstParam.lmin}`;
        setSelectedSignature(signature);
      } else {
        setAvailableParams([]);
        console.warn('没有找到已完成的RQA分析结果');
      }
    } catch (error) {
      console.error('加载已完成结果失败:', error);
      setAvailableParams([]);
    }
  };

  // 根据筛选条件过滤参数组合
  const filteredSignatures = useMemo(() => {
    if (availableParams.length === 0) return [];

    return availableParams
      .filter(param => {
        if (paramFilters.m !== null && param.m !== paramFilters.m) return false;
        if (paramFilters.tau !== null && param.tau !== paramFilters.tau) return false;
        if (paramFilters.eps !== null && Math.abs(param.eps - paramFilters.eps) > 0.0001) return false;
        if (paramFilters.lmin !== null && param.lmin !== paramFilters.lmin) return false;
        return true;
      })
      .map(param => `m${param.m}_tau${param.tau}_eps${param.eps}_lmin${param.lmin}`);
  }, [availableParams, paramFilters]);

  // 获取每个参数的可选值范围
  const paramRanges = useMemo(() => {
    if (availableParams.length === 0) return { m: [], tau: [], eps: [], lmin: [] };

    const ranges = {
      m: [...new Set(availableParams.map(p => p.m))].sort((a, b) => a - b),
      tau: [...new Set(availableParams.map(p => p.tau))].sort((a, b) => a - b),
      eps: [...new Set(availableParams.map(p => p.eps))].sort((a, b) => a - b),
      lmin: [...new Set(availableParams.map(p => p.lmin))].sort((a, b) => a - b)
    };

    return ranges;
  }, [availableParams]);

  // 生成图片URL
  const getImageUrl = useCallback((filename) => {
    return `/api/m05/visualizations/${selectedSignature}/${filename}`;
  }, [selectedSignature]);

  const plots = useMemo(() => [
    {
      title: 'RQA指标箱线图',
      filename: 'rqa_metrics_boxplot.png',
      description: '各组别的RQA核心指标（RR, DET, ENT）分布对比'
    },
    {
      title: '相关性热力图',
      filename: 'correlation_heatmap.png',
      description: 'RQA特征之间的Pearson相关系数矩阵'
    },
    {
      title: '显著性特征',
      filename: 'significant_features.png',
      description: 'ANOVA分析中具有统计显著性的特征（p < 0.05）'
    },
    {
      title: '复杂度小提琴图',
      filename: 'complexity_violin.png',
      description: 'RQA复杂度指标（1D和2D）的分布密度'
    }
  ], []);

  const handleDownload = useCallback(async (filename) => {
    try {
      const url = getImageUrl(filename);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      message.success('下载成功');
    } catch (error) {
      console.error('下载失败:', error);
      message.error('下载失败: ' + (error.message || '未知错误'));
    }
  }, [getImageUrl]);

  return (
    <div>
      {/* 参数筛选卡片 */}
      <Card
        title="参数筛选"
        style={{ marginBottom: 24 }}
      >
        <Form layout="inline">
          <Form.Item label="嵌入维度 m">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={paramFilters.m}
              onChange={(value) => setParamFilters({ ...paramFilters, m: value })}
            >
              {paramRanges.m.map(val => (
                <Option key={val} value={val}>{val}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="时间延迟 τ">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={paramFilters.tau}
              onChange={(value) => setParamFilters({ ...paramFilters, tau: value })}
            >
              {paramRanges.tau.map(val => (
                <Option key={val} value={val}>{val}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="递归阈值 ε">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={paramFilters.eps}
              onChange={(value) => setParamFilters({ ...paramFilters, eps: value })}
            >
              {paramRanges.eps.map(val => (
                <Option key={val} value={val}>{val.toFixed(3)}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="最小线长 lmin">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={paramFilters.lmin}
              onChange={(value) => setParamFilters({ ...paramFilters, lmin: value })}
            >
              {paramRanges.lmin.map(val => (
                <Option key={val} value={val}>{val}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <span style={{ color: '#666', fontSize: 13 }}>
                筛选结果: {filteredSignatures.length} 个参数组合
              </span>
              {(paramFilters.m || paramFilters.tau || paramFilters.eps || paramFilters.lmin) && (
                <Button
                  size="small"
                  onClick={() => setParamFilters({ m: null, tau: null, eps: null, lmin: null })}
                >
                  清空筛选
                </Button>
              )}
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* 数据统计与筛选卡片 */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            数据结构说明
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="总样本数" span={2}>
            <Tag color="blue">300条记录</Tag>
            <span style={{ marginLeft: 8, color: '#666' }}>
              = 3组 × 20人 × 5任务
            </span>
          </Descriptions.Item>
          <Descriptions.Item label="组别分布">
            Control: 100 | MCI: 100 | AD: 100
          </Descriptions.Item>
          <Descriptions.Item label="任务分布">
            每个任务60条 (20人 × 3组)
          </Descriptions.Item>
          <Descriptions.Item label="受试者构成">
            Control组: 20人 | MCI组: 20人 | AD组: 20人
          </Descriptions.Item>
          <Descriptions.Item label="任务类型">
            q1, q2, q3, q4, q5 (共5个VR任务)
          </Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div>
              <strong style={{ marginRight: 12 }}>
                <BarChartOutlined /> 组别筛选:
              </strong>
              <Checkbox.Group
                options={[
                  { label: 'Control (控制组)', value: 'Control' },
                  { label: 'MCI (轻度认知障碍)', value: 'MCI' },
                  { label: 'AD (阿尔茨海默症)', value: 'AD' }
                ]}
                value={selectedGroups}
                onChange={setSelectedGroups}
              />
            </div>

            <div>
              <strong style={{ marginRight: 12 }}>
                <BarChartOutlined /> 任务筛选:
              </strong>
              <Checkbox.Group
                options={[
                  { label: '任务1 (q1)', value: 'q1' },
                  { label: '任务2 (q2)', value: 'q2' },
                  { label: '任务3 (q3)', value: 'q3' },
                  { label: '任务4 (q4)', value: 'q4' },
                  { label: '任务5 (q5)', value: 'q5' }
                ]}
                value={selectedTasks}
                onChange={setSelectedTasks}
              />
            </div>

            <div style={{ padding: '12px', background: '#f0f5ff', borderRadius: 4 }}>
              <strong>当前筛选统计:</strong>
              <div style={{ marginTop: 8, color: '#666' }}>
                选中 {selectedGroups.length} 个组别, {selectedTasks.length} 个任务
                {' '}→ 预计 {selectedGroups.length * 20 * selectedTasks.length} 条数据
                {selectedGroups.length === 0 || selectedTasks.length === 0 && (
                  <Tag color="warning" style={{ marginLeft: 8 }}>请至少选择一个组别和一个任务</Tag>
                )}
              </div>
            </div>
          </Space>
        </div>

        {/* 任务-组别分布表 */}
        <Table
          style={{ marginTop: 16 }}
          size="small"
          pagination={false}
          rowKey="task"
          dataSource={[
            { task: 'q1', control: 20, mci: 20, ad: 20, total: 60 },
            { task: 'q2', control: 20, mci: 20, ad: 20, total: 60 },
            { task: 'q3', control: 20, mci: 20, ad: 20, total: 60 },
            { task: 'q4', control: 20, mci: 20, ad: 20, total: 60 },
            { task: 'q5', control: 20, mci: 20, ad: 20, total: 60 },
            { task: '合计', control: 100, mci: 100, ad: 100, total: 300 }
          ]}
          columns={[
            {
              title: '任务',
              dataIndex: 'task',
              key: 'task',
              width: 80,
              render: (text) => text === '合计' ? <strong>{text}</strong> : text
            },
            {
              title: 'Control',
              dataIndex: 'control',
              key: 'control',
              align: 'center',
              render: (text, record) => record.task === '合计' ? <strong>{text}</strong> : text
            },
            {
              title: 'MCI',
              dataIndex: 'mci',
              key: 'mci',
              align: 'center',
              render: (text, record) => record.task === '合计' ? <strong>{text}</strong> : text
            },
            {
              title: 'AD',
              dataIndex: 'ad',
              key: 'ad',
              align: 'center',
              render: (text, record) => record.task === '合计' ? <strong>{text}</strong> : text
            },
            {
              title: '小计',
              dataIndex: 'total',
              key: 'total',
              align: 'center',
              render: (text, record) => <strong>{text}</strong>
            }
          ]}
        />
      </Card>

      <Card
        title={
          <Space>
            <PictureOutlined />
            统计可视化
          </Space>
        }
        extra={
          <Space>
            <span>选择参数组合:</span>
            <Select
              style={{ width: 280 }}
              value={selectedSignature}
              onChange={setSelectedSignature}
              showSearch
              optionFilterProp="children"
            >
              {filteredSignatures.map(sig => (
                <Option key={sig} value={sig}>{sig}</Option>
              ))}
            </Select>
          </Space>
        }
      >
        <Row gutter={[24, 24]}>
          {plots.map((plot, index) => (
            <Col span={12} key={index}>
              <Card
                title={plot.title}
                extra={
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(plot.filename)}
                  >
                    下载
                  </Button>
                }
                styles={{
                  body: { padding: 0 }
                }}
              >
                <div style={{ padding: '16px', background: '#fafafa' }}>
                  <p style={{ margin: 0, fontSize: 13, color: '#666' }}>
                    {plot.description}
                  </p>
                </div>
                <Image
                  src={getImageUrl(plot.filename)}
                  alt={plot.title}
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                  placeholder={
                    <Empty
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                      description="暂无图片"
                    />
                  }
                  style={{
                    width: '100%',
                    maxHeight: 400,
                    objectFit: 'contain'
                  }}
                />
              </Card>
            </Col>
          ))}
        </Row>

        <Card
          title="数据文件"
          style={{ marginTop: 24 }}
          styles={{
            body: { background: '#fafafa' }
          }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <strong>Step 3 - 特征增强:</strong>
              <ul>
                <li>enriched_features.csv - 包含Module04事件特征、MMSE数据和衍生RQA特征</li>
              </ul>
            </div>
            <div>
              <strong>Step 4 - 统计分析:</strong>
              <ul>
                <li>descriptive_stats.csv - 各组别的描述性统计（均值、标准差等）</li>
                <li>group_comparison.csv - ANOVA组间比较结果（F统计量、p值）</li>
                <li>correlation_matrix.csv - 特征相关性矩阵</li>
              </ul>
            </div>
            <div>
              <strong>Step 5 - 可视化:</strong>
              <ul>
                <li>rqa_metrics_boxplot.png - RQA指标箱线图</li>
                <li>correlation_heatmap.png - 相关性热力图</li>
                <li>significant_features.png - 显著性特征柱状图</li>
                <li>complexity_violin.png - 复杂度小提琴图</li>
              </ul>
            </div>
          </Space>
        </Card>
      </Card>
    </div>
  );
};

export default VisualizationPanel;
