/**
 * Module05: 高级分析面板
 *
 * 功能：
 * 1. 参数优化评估 - 自动评估3264个参数组合的性能
 * 2. 任务分层分析 - 按任务(q1-q5)分别进行统计分析
 * 3. 任务对比分析 - 对比不同任务的RQA特征差异
 * 4. ROI粒度分析准备 - 为未来ROI分析预留接口
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card, Row, Col, Button, Table, Select, Space, Spin, message,
  Descriptions, Tag, Tabs, Statistic, Progress, Checkbox, Radio,
  Tooltip, Alert
} from 'antd';
import {
  ThunderboltOutlined, LineChartOutlined, BarChartOutlined,
  FundOutlined, InfoCircleOutlined, RocketOutlined,
  FireOutlined, ExperimentOutlined, UserOutlined, RiseOutlined, PictureOutlined
} from '@ant-design/icons';
import axios from 'axios';
import {
  ResponsiveContainer, BarChart, ScatterChart, Bar, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Cell, ReferenceLine
} from 'recharts';
import IndividualQueryPanel from './IndividualQueryPanel';
import ParameterSensitivityPanel from './ParameterSensitivityPanel';
import EnhancedVisualizationPanel from './EnhancedVisualizationPanel';

const { Option } = Select;
const { TabPane } = Tabs;

const AdvancedAnalysisPanel = () => {
  // ===== 状态管理 =====
  const [activeSubTab, setActiveSubTab] = useState('param-eval');

  // 参数评估相关状态
  const [paramEvalLoading, setParamEvalLoading] = useState(false);
  const [paramEvalResults, setParamEvalResults] = useState(null);
  const [sortBy, setSortBy] = useState('f_stat_mean'); // 排序依据
  const [topN, setTopN] = useState(10); // 显示Top N

  // 参数筛选器状态
  const [paramFilters, setParamFilters] = useState({
    m: 'all',           // 'all' | 'exclude_1' | specific value
    tau: 'all',
    eps: 'all',
    lmin: 'all'
  });

  // 任务分层分析相关状态
  const [taskAnalysisLoading, setTaskAnalysisLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState('q1');
  const [selectedParam, setSelectedParam] = useState(null);
  const [availableParams, setAvailableParams] = useState([]);
  const [taskStats, setTaskStats] = useState(null);

  // 任务对比相关状态
  const [taskCompareLoading, setTaskCompareLoading] = useState(false);
  const [selectedTasks, setSelectedTasks] = useState(['q1', 'q2', 'q3', 'q4', 'q5']);
  const [compareResults, setCompareResults] = useState(null);

  // ===== 组件挂载时加载可用参数 =====
  useEffect(() => {
    fetchAvailableParams();
  }, []);

  // ===== API调用函数 =====

  /**
   * 获取所有可用的参数组合
   */
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

  /**
   * 执行参数评估
   */
  const handleParamEvaluation = async () => {
    setParamEvalLoading(true);
    try {
      const response = await axios.post('/api/m05/advanced/evaluate-params', {
        metric: sortBy
      });

      if (response.data.success) {
        setParamEvalResults(response.data.results);
        message.success(`参数评估完成！共评估 ${response.data.results.length} 个参数组合`);
      } else {
        message.error('参数评估失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('参数评估失败:', error);
      message.error('参数评估失败: ' + error.message);
    } finally {
      setParamEvalLoading(false);
    }
  };

  // ===== 参数筛选逻辑 =====

  /**
   * 从评估结果中提取各参数的唯一值
   */
  const getUniqueParamValues = useMemo(() => {
    if (!paramEvalResults || paramEvalResults.length === 0) {
      return { m: [], tau: [], eps: [], lmin: [] };
    }

    const unique = {
      m: [...new Set(paramEvalResults.map(r => r.params.m))].sort((a,b) => a-b),
      tau: [...new Set(paramEvalResults.map(r => r.params.tau))].sort((a,b) => a-b),
      eps: [...new Set(paramEvalResults.map(r => r.params.eps))].sort((a,b) => a-b),
      lmin: [...new Set(paramEvalResults.map(r => r.params.lmin))].sort((a,b) => a-b)
    };

    return unique;
  }, [paramEvalResults]);

  /**
   * 应用参数筛选
   */
  const filteredResults = useMemo(() => {
    if (!paramEvalResults) return [];

    let filtered = [...paramEvalResults];

    // 筛选 m
    if (paramFilters.m === 'exclude_1') {
      filtered = filtered.filter(r => r.params.m !== 1);
    } else if (paramFilters.m !== 'all') {
      filtered = filtered.filter(r => r.params.m === Number(paramFilters.m));
    }

    // 筛选 tau
    if (paramFilters.tau !== 'all') {
      filtered = filtered.filter(r => r.params.tau === Number(paramFilters.tau));
    }

    // 筛选 eps
    if (paramFilters.eps !== 'all') {
      filtered = filtered.filter(r => r.params.eps === Number(paramFilters.eps));
    }

    // 筛选 lmin
    if (paramFilters.lmin !== 'all') {
      filtered = filtered.filter(r => r.params.lmin === Number(paramFilters.lmin));
    }

    return filtered.slice(0, topN);
  }, [paramEvalResults, paramFilters, topN]);

  /**
   * 执行任务分层分析
   */
  const handleTaskAnalysis = async () => {
    if (!selectedParam) {
      message.warning('请先选择一个参数组合');
      return;
    }

    setTaskAnalysisLoading(true);
    try {
      const response = await axios.post('/api/m05/advanced/task-analysis', {
        params: selectedParam,
        task_id: selectedTask
      });

      if (response.data.success) {
        setTaskStats(response.data.statistics);
        message.success(`任务 ${selectedTask} 分析完成`);
      } else {
        message.error('任务分析失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('任务分析失败:', error);
      message.error('任务分析失败: ' + error.message);
    } finally {
      setTaskAnalysisLoading(false);
    }
  };

  /**
   * 执行任务对比分析
   */
  const handleTaskComparison = async () => {
    if (!selectedParam) {
      message.warning('请先选择一个参数组合');
      return;
    }

    if (selectedTasks.length < 2) {
      message.warning('请至少选择2个任务进行对比');
      return;
    }

    setTaskCompareLoading(true);
    try {
      const response = await axios.post('/api/m05/advanced/task-compare', {
        params: selectedParam,
        tasks: selectedTasks
      });

      if (response.data.success) {
        setCompareResults(response.data.comparison);
        message.success('任务对比分析完成');
      } else {
        message.error('对比分析失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('对比分析失败:', error);
      message.error('对比分析失败: ' + error.message);
    } finally {
      setTaskCompareLoading(false);
    }
  };

  // ===== 参数评估表格列定义 =====
  const paramEvalColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 70,
      render: (rank) => {
        let color = 'default';
        if (rank === 1) color = 'gold';
        else if (rank === 2) color = 'silver';
        else if (rank === 3) color = '#cd7f32';

        return rank <= 3 ? (
          <Tag color={color} style={{ fontWeight: 'bold' }}>#{rank}</Tag>
        ) : (
          <span>#{rank}</span>
        );
      }
    },
    {
      title: 'RQA参数',
      key: 'params',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <span><strong>m:</strong> {record.params.m} | <strong>tau:</strong> {record.params.tau}</span>
          <span><strong>eps:</strong> {record.params.eps} | <strong>lmin:</strong> {record.params.lmin}</span>
        </Space>
      )
    },
    {
      title: '平均F统计量',
      dataIndex: 'f_stat_mean',
      key: 'f_stat_mean',
      sorter: (a, b) => a.f_stat_mean - b.f_stat_mean,
      render: (val) => val?.toFixed(2) || 'N/A'
    },
    {
      title: '显著特征数',
      dataIndex: 'significant_count',
      key: 'significant_count',
      sorter: (a, b) => a.significant_count - b.significant_count,
      render: (count) => (
        <Tag color={count >= 10 ? 'green' : count >= 5 ? 'orange' : 'default'}>
          {count} 个
        </Tag>
      )
    },
    {
      title: '最大F值',
      dataIndex: 'f_stat_max',
      key: 'f_stat_max',
      sorter: (a, b) => a.f_stat_max - b.f_stat_max,
      render: (val) => val?.toFixed(2) || 'N/A'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => setSelectedParam(record.params)}
        >
          选择此参数
        </Button>
      )
    }
  ];

  // ===== 任务统计表格列定义 =====
  const taskStatsColumns = [
    {
      title: '特征名称',
      dataIndex: 'feature',
      key: 'feature',
      fixed: 'left',
      width: 150
    },
    {
      title: 'Control组',
      children: [
        {
          title: '均值',
          dataIndex: ['control', 'mean'],
          key: 'control_mean',
          render: (val) => val?.toFixed(4) || 'N/A'
        },
        {
          title: '标准差',
          dataIndex: ['control', 'std'],
          key: 'control_std',
          render: (val) => val?.toFixed(4) || 'N/A'
        }
      ]
    },
    {
      title: 'MCI组',
      children: [
        {
          title: '均值',
          dataIndex: ['mci', 'mean'],
          key: 'mci_mean',
          render: (val) => val?.toFixed(4) || 'N/A'
        },
        {
          title: '标准差',
          dataIndex: ['mci', 'std'],
          key: 'mci_std',
          render: (val) => val?.toFixed(4) || 'N/A'
        }
      ]
    },
    {
      title: 'AD组',
      children: [
        {
          title: '均值',
          dataIndex: ['ad', 'mean'],
          key: 'ad_mean',
          render: (val) => val?.toFixed(4) || 'N/A'
        },
        {
          title: '标准差',
          dataIndex: ['ad', 'std'],
          key: 'ad_std',
          render: (val) => val?.toFixed(4) || 'N/A'
        }
      ]
    },
    {
      title: 'ANOVA',
      children: [
        {
          title: 'F值',
          dataIndex: 'f_stat',
          key: 'f_stat',
          render: (val) => val?.toFixed(2) || 'N/A'
        },
        {
          title: 'p值',
          dataIndex: 'p_value',
          key: 'p_value',
          render: (val) => {
            if (!val) return 'N/A';
            const isSignificant = val < 0.05;
            return (
              <Tag color={isSignificant ? 'green' : 'default'}>
                {val < 0.001 ? '<0.001' : val.toFixed(3)}
              </Tag>
            );
          }
        }
      ]
    }
  ];

  // ===== 渲染函数 =====

  /**
   * 渲染参数评估Tab
   */
  const renderParamEvaluation = () => (
    <Card
      title={
        <Space>
          <RocketOutlined />
          参数性能评估
        </Space>
      }
      extra={
        <Space>
          <Select
            value={sortBy}
            onChange={setSortBy}
            style={{ width: 150 }}
            disabled={paramEvalLoading}
          >
            <Option value="f_stat_mean">平均F统计量</Option>
            <Option value="significant_count">显著特征数</Option>
            <Option value="f_stat_max">最大F值</Option>
          </Select>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={handleParamEvaluation}
            loading={paramEvalLoading}
          >
            开始评估
          </Button>
        </Space>
      }
    >
      <Alert
        message="参数评估说明"
        description={
          <div>
            <p>此功能将自动评估所有已计算的RQA参数组合的分类性能，帮助您找到最优参数。</p>
            <ul>
              <li><strong>平均F统计量：</strong>所有RQA特征的ANOVA F值的平均值（越大越好）</li>
              <li><strong>显著特征数：</strong>通过ANOVA检验(p &lt; 0.05)的特征数量</li>
              <li><strong>最大F值：</strong>所有特征中最大的F统计量</li>
            </ul>
            <p style={{ color: '#1890ff', marginBottom: 0 }}>
              <InfoCircleOutlined /> 提示：评估基于300条记录（3组×20人×5任务）的混合数据
            </p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {paramEvalLoading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16, color: '#666' }}>
            正在评估参数性能，请稍候...
          </p>
        </div>
      ) : paramEvalResults ? (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="评估参数总数"
                  value={paramEvalResults.length}
                  suffix="个"
                  prefix={<ExperimentOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="最优参数F值"
                  value={paramEvalResults[0]?.f_stat_mean.toFixed(2)}
                  prefix={<FireOutlined />}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="最多显著特征"
                  value={Math.max(...paramEvalResults.map(r => r.significant_count))}
                  suffix="个"
                  prefix={<FundOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="显示Top"
                  value={topN}
                  suffix={
                    <Select
                      value={topN}
                      onChange={setTopN}
                      size="small"
                      style={{ width: 70, marginLeft: 8 }}
                    >
                      <Option value={5}>5</Option>
                      <Option value={10}>10</Option>
                      <Option value={20}>20</Option>
                      <Option value={50}>50</Option>
                    </Select>
                  }
                />
              </Card>
            </Col>
          </Row>

          {/* 参数筛选器 */}
          <Card title="参数筛选" style={{ marginBottom: 16 }} size="small">
            <Row gutter={16}>
              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <label>嵌入维度 (m):</label>
                  <Select
                    value={paramFilters.m}
                    onChange={(val) => setParamFilters({...paramFilters, m: val})}
                    style={{ width: '100%' }}
                  >
                    <Option value="all">全部</Option>
                    <Option value="exclude_1">排除 m=1</Option>
                    {getUniqueParamValues.m.map(v => (
                      <Option key={v} value={v}>m = {v}</Option>
                    ))}
                  </Select>
                </Space>
              </Col>
              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <label>时间延迟 (tau):</label>
                  <Select
                    value={paramFilters.tau}
                    onChange={(val) => setParamFilters({...paramFilters, tau: val})}
                    style={{ width: '100%' }}
                  >
                    <Option value="all">全部</Option>
                    {getUniqueParamValues.tau.map(v => (
                      <Option key={v} value={v}>tau = {v}</Option>
                    ))}
                  </Select>
                </Space>
              </Col>
              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <label>递归阈值 (eps):</label>
                  <Select
                    value={paramFilters.eps}
                    onChange={(val) => setParamFilters({...paramFilters, eps: val})}
                    style={{ width: '100%' }}
                  >
                    <Option value="all">全部</Option>
                    {getUniqueParamValues.eps.map(v => (
                      <Option key={v} value={v}>eps = {v}</Option>
                    ))}
                  </Select>
                </Space>
              </Col>
              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <label>最小线长 (lmin):</label>
                  <Select
                    value={paramFilters.lmin}
                    onChange={(val) => setParamFilters({...paramFilters, lmin: val})}
                    style={{ width: '100%' }}
                  >
                    <Option value="all">全部</Option>
                    {getUniqueParamValues.lmin.map(v => (
                      <Option key={v} value={v}>lmin = {v}</Option>
                    ))}
                  </Select>
                </Space>
              </Col>
            </Row>
            <div style={{ marginTop: 12, color: '#888', fontSize: 12 }}>
              当前筛选结果: <strong>{filteredResults.length}</strong> 个参数组合
              {paramFilters.m === 'exclude_1' && <Tag color="orange" style={{ marginLeft: 8 }}>已排除 m=1</Tag>}
            </div>
          </Card>

          <Table
            columns={paramEvalColumns}
            dataSource={filteredResults.map((item, idx) => ({
              ...item,
              rank: idx + 1,
              key: `${item.params.m}_${item.params.tau}_${item.params.eps}_${item.params.lmin}`
            }))}
            pagination={false}
            scroll={{ x: 1000 }}
            size="small"
          />

          {selectedParam && (
            <Alert
              message="已选择参数"
              description={
                <span>
                  m={selectedParam.m}, tau={selectedParam.tau},
                  eps={selectedParam.eps}, lmin={selectedParam.lmin}
                  {' '}→ 可切换到"任务分层分析"或"任务对比"进行进一步分析
                </span>
              }
              type="success"
              showIcon
              closable
              onClose={() => setSelectedParam(null)}
              style={{ marginTop: 16 }}
            />
          )}
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
          <RocketOutlined style={{ fontSize: 48, marginBottom: 16 }} />
          <p>点击"开始评估"按钮开始参数性能评估</p>
        </div>
      )}
    </Card>
  );

  /**
   * 渲染任务分层分析Tab
   */
  const renderTaskAnalysis = () => (
    <Card
      title={
        <Space>
          <LineChartOutlined />
          任务分层统计分析
        </Space>
      }
      extra={
        <Space>
          <span>选择任务:</span>
          <Select
            value={selectedTask}
            onChange={setSelectedTask}
            style={{ width: 120 }}
          >
            <Option value="q1">任务1 (q1)</Option>
            <Option value="q2">任务2 (q2)</Option>
            <Option value="q3">任务3 (q3)</Option>
            <Option value="q4">任务4 (q4)</Option>
            <Option value="q5">任务5 (q5)</Option>
          </Select>
          <Button
            type="primary"
            icon={<BarChartOutlined />}
            onClick={handleTaskAnalysis}
            loading={taskAnalysisLoading}
            disabled={!selectedParam}
          >
            分析
          </Button>
        </Space>
      }
    >
      <Alert
        message="任务分层分析说明"
        description={
          <div>
            <p>此功能将对指定任务的数据进行独立统计分析，帮助您发现任务特异性模式。</p>
            <p style={{ marginBottom: 0 }}>
              <InfoCircleOutlined /> 分析基于60条记录（3组×20人）的单任务数据
            </p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {!selectedParam && (
        <Alert
          message="请先选择参数"
          description='请先在"参数评估"Tab中选择一个参数组合，或从下拉框手动选择'
          type="warning"
          showIcon
          action={
            <Select
              placeholder="手动选择参数"
              style={{ width: 300 }}
              onChange={(value) => {
                const param = availableParams.find(p =>
                  `${p.params.m}_${p.params.tau}_${p.params.eps}_${p.params.lmin}` === value
                );
                if (param) setSelectedParam(param.params);
              }}
            >
              {availableParams && availableParams.length > 0 ? (
                availableParams.slice(0, 20).map(p => (
                  <Option
                    key={`${p.params.m}_${p.params.tau}_${p.params.eps}_${p.params.lmin}`}
                    value={`${p.params.m}_${p.params.tau}_${p.params.eps}_${p.params.lmin}`}
                  >
                    m={p.params.m}, tau={p.params.tau}, eps={p.params.eps}, lmin={p.params.lmin}
                  </Option>
                ))
              ) : (
                <Option disabled>暂无参数</Option>
              )}
            </Select>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {taskAnalysisLoading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16, color: '#666' }}>
            正在分析任务 {selectedTask}，请稍候...
          </p>
        </div>
      ) : taskStats ? (
        <>
          <Descriptions bordered size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label="分析任务">{selectedTask}</Descriptions.Item>
            <Descriptions.Item label="样本数">60条 (3组 × 20人)</Descriptions.Item>
            <Descriptions.Item label="RQA参数">
              m={selectedParam.m}, tau={selectedParam.tau}, eps={selectedParam.eps}, lmin={selectedParam.lmin}
            </Descriptions.Item>
          </Descriptions>

          <Table
            columns={taskStatsColumns}
            dataSource={taskStats}
            rowKey="feature"
            pagination={false}
            scroll={{ x: 1200 }}
            size="small"
          />
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
          <LineChartOutlined style={{ fontSize: 48, marginBottom: 16 }} />
          <p>选择参数和任务后，点击"分析"按钮开始</p>
        </div>
      )}
    </Card>
  );

  /**
   * 渲染任务对比分析Tab
   */
  const renderTaskComparison = () => (
    <Card
      title={
        <Space>
          <BarChartOutlined />
          任务对比分析
        </Space>
      }
      extra={
        <Space>
          <Button
            type="primary"
            icon={<FundOutlined />}
            onClick={handleTaskComparison}
            loading={taskCompareLoading}
            disabled={!selectedParam || selectedTasks.length < 2}
          >
            开始对比
          </Button>
        </Space>
      }
    >
      <Alert
        message="任务对比分析说明"
        description="此功能将对比不同任务在相同参数下的RQA特征差异，帮助您发现任务难度对眼动模式的影响。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card size="small" title="选择对比任务" style={{ marginBottom: 16 }}>
        <Checkbox.Group
          value={selectedTasks}
          onChange={setSelectedTasks}
          style={{ width: '100%' }}
        >
          <Row>
            <Col span={8}><Checkbox value="q1">任务1 (q1)</Checkbox></Col>
            <Col span={8}><Checkbox value="q2">任务2 (q2)</Checkbox></Col>
            <Col span={8}><Checkbox value="q3">任务3 (q3)</Checkbox></Col>
            <Col span={8}><Checkbox value="q4">任务4 (q4)</Checkbox></Col>
            <Col span={8}><Checkbox value="q5">任务5 (q5)</Checkbox></Col>
          </Row>
        </Checkbox.Group>
      </Card>

      {!selectedParam && (
        <Alert
          message="请先选择参数"
          description='请先在"参数评估"Tab中选择一个参数组合'
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {taskCompareLoading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16, color: '#666' }}>
            正在对比任务，请稍候...
          </p>
        </div>
      ) : compareResults ? (
        <div>
          {/* 统计摘要 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="对比任务数"
                  value={compareResults.tasks?.length || 0}
                  suffix="个"
                  prefix={<BarChartOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总特征数"
                  value={compareResults.total_features || 0}
                  prefix={<FundOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="显著特征数"
                  value={compareResults.significant_count || 0}
                  prefix={<FireOutlined />}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="显著率"
                  value={compareResults.total_features > 0
                    ? ((compareResults.significant_count / compareResults.total_features) * 100).toFixed(1)
                    : 0}
                  suffix="%"
                  prefix={<RiseOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
          </Row>

          {/* RQA参数信息 */}
          <Card title="RQA参数配置" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="嵌入维度 (m)">{compareResults.params?.m}</Descriptions.Item>
                </Descriptions>
              </Col>
              <Col span={6}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="时间延迟 (tau)">{compareResults.params?.tau}</Descriptions.Item>
                </Descriptions>
              </Col>
              <Col span={6}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="递归阈值 (eps)">{compareResults.params?.eps}</Descriptions.Item>
                </Descriptions>
              </Col>
              <Col span={6}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="最小线长 (lmin)">{compareResults.params?.lmin}</Descriptions.Item>
                </Descriptions>
              </Col>
            </Row>
          </Card>

          {/* 显著特征列表 */}
          {compareResults.significant_features && compareResults.significant_features.length > 0 && (
            <Card title={`显著特征列表 (p < 0.05)`} size="small" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {compareResults.significant_features.map(feature => (
                  <Tag key={feature} color="red" style={{ marginBottom: 4 }}>
                    {feature.toUpperCase()}
                  </Tag>
                ))}
              </div>
            </Card>
          )}

          {/* 任务对比详细表格 */}
          <Card title="任务间特征对比 (Task-wise Feature Comparison)" style={{ marginBottom: 16 }}>
            <Table
              dataSource={compareResults.comparison_details?.map((item, idx) => ({
                key: idx,
                ...item
              }))}
              columns={[
                {
                  title: 'RQA特征',
                  dataIndex: 'feature',
                  key: 'feature',
                  fixed: 'left',
                  width: 120,
                  render: (text) => (
                    <span style={{ fontWeight: 500, fontFamily: 'monospace' }}>
                      {text.toUpperCase()}
                    </span>
                  )
                },
                {
                  title: 'F统计量',
                  dataIndex: 'f_stat',
                  key: 'f_stat',
                  width: 100,
                  sorter: (a, b) => a.f_stat - b.f_stat,
                  render: (val) => (
                    <span style={{ fontWeight: 500, color: val > 50 ? '#cf1322' : val > 20 ? '#fa8c16' : '#000' }}>
                      {val?.toFixed(2)}
                    </span>
                  )
                },
                {
                  title: 'p值',
                  dataIndex: 'p_value',
                  key: 'p_value',
                  width: 100,
                  sorter: (a, b) => a.p_value - b.p_value,
                  render: (val) => {
                    if (val < 0.001) return <span style={{ color: '#cf1322', fontWeight: 'bold' }}>{'< 0.001 ***'}</span>;
                    if (val < 0.01) return <span style={{ color: '#fa8c16', fontWeight: 'bold' }}>{val.toFixed(4)} **</span>;
                    if (val < 0.05) return <span style={{ color: '#faad14', fontWeight: 500 }}>{val.toFixed(4)} *</span>;
                    return <span>{val.toFixed(4)}</span>;
                  }
                },
                {
                  title: '显著性',
                  dataIndex: 'significant',
                  key: 'significant',
                  width: 80,
                  filters: [
                    { text: '显著', value: true },
                    { text: '不显著', value: false }
                  ],
                  onFilter: (value, record) => record.significant === value,
                  render: (val) => (
                    val ?
                      <Tag color="red">显著</Tag> :
                      <Tag color="default">不显著</Tag>
                  )
                },
                ...compareResults.tasks?.map(task => ({
                  title: `${task.toUpperCase()}`,
                  key: `task_${task}`,
                  width: 140,
                  children: [
                    {
                      title: '均值',
                      dataIndex: ['task_means', task, 'mean'],
                      key: `${task}_mean`,
                      width: 70,
                      render: (val) => val?.toFixed(4) || '-'
                    },
                    {
                      title: '标准差',
                      dataIndex: ['task_means', task, 'std'],
                      key: `${task}_std`,
                      width: 70,
                      render: (val) => val ? `±${val.toFixed(4)}` : '-'
                    }
                  ]
                })) || []
              ]}
              scroll={{ x: 'max-content' }}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 个特征`
              }}
              size="small"
              bordered
            />
          </Card>

          {/* 可视化图表部分 */}
          <Row gutter={16}>
            {/* F统计量分布图 */}
            <Col span={12}>
              <Card title="F统计量分布 (F-statistic Distribution)" size="small">
                <div style={{ height: 300 }}>
                  {(() => {
                    const sortedData = [...(compareResults.comparison_details || [])]
                      .sort((a, b) => b.f_stat - a.f_stat)
                      .slice(0, 15); // Top 15特征

                    return (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={sortedData} layout="vertical" margin={{ left: 100, right: 20, top: 10, bottom: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" />
                          <YAxis
                            type="category"
                            dataKey="feature"
                            tickFormatter={(val) => val.toUpperCase()}
                            style={{ fontSize: 12 }}
                          />
                          <Tooltip
                            formatter={(value) => value.toFixed(2)}
                            contentStyle={{ fontSize: 12 }}
                          />
                          <Bar dataKey="f_stat" name="F统计量">
                            {sortedData.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={entry.significant ? '#cf1322' : '#d9d9d9'}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    );
                  })()}
                </div>
              </Card>
            </Col>

            {/* p值分布图 */}
            <Col span={12}>
              <Card title="p值分布 (p-value Distribution)" size="small">
                <div style={{ height: 300 }}>
                  {(() => {
                    const data = compareResults.comparison_details?.map(item => ({
                      feature: item.feature,
                      negLogP: -Math.log10(item.p_value), // 转换为-log10(p)
                      significant: item.significant
                    })).sort((a, b) => b.negLogP - a.negLogP).slice(0, 15) || [];

                    return (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} layout="vertical" margin={{ left: 100, right: 20, top: 10, bottom: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" label={{ value: '-log₁₀(p)', position: 'insideBottom', offset: -5 }} />
                          <YAxis
                            type="category"
                            dataKey="feature"
                            tickFormatter={(val) => val.toUpperCase()}
                            style={{ fontSize: 12 }}
                          />
                          <Tooltip
                            formatter={(value) => `${value.toFixed(2)} (-log10 scale)`}
                            contentStyle={{ fontSize: 12 }}
                          />
                          <ReferenceLine x={1.3} stroke="#faad14" strokeDasharray="3 3" label="p=0.05" />
                          <Bar dataKey="negLogP" name="-log₁₀(p)">
                            {data.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={entry.significant ? '#1890ff' : '#d9d9d9'}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    );
                  })()}
                </div>
              </Card>
            </Col>
          </Row>

          {/* 任务均值热力图 */}
          <Card title="任务均值热力图 (Task Mean Heatmap)" style={{ marginTop: 16 }} size="small">
            <div style={{ height: 400, overflowY: 'auto' }}>
              {(() => {
                // 准备热力图数据
                const heatmapData = [];
                compareResults.comparison_details?.forEach(item => {
                  compareResults.tasks?.forEach(task => {
                    const mean = item.task_means?.[task]?.mean;
                    if (mean !== undefined && mean !== null) {
                      heatmapData.push({
                        feature: item.feature.toUpperCase(),
                        task: task.toUpperCase(),
                        value: mean
                      });
                    }
                  });
                });

                // 按显著性排序特征
                const sortedFeatures = [...new Set(heatmapData.map(d => d.feature))];

                return (
                  <ResponsiveContainer width="100%" height={Math.max(400, sortedFeatures.length * 25)}>
                    <ScatterChart margin={{ left: 100, right: 50, top: 20, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="category"
                        dataKey="task"
                        name="任务"
                        allowDuplicatedCategory={false}
                      />
                      <YAxis
                        type="category"
                        dataKey="feature"
                        name="特征"
                        allowDuplicatedCategory={false}
                      />
                      <Tooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        content={({ active, payload }) => {
                          if (active && payload && payload[0]) {
                            const data = payload[0].payload;
                            return (
                              <div style={{
                                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                padding: '8px 12px',
                                border: '1px solid #d9d9d9',
                                borderRadius: 4,
                                fontSize: 12
                              }}>
                                <p style={{ margin: 0, fontWeight: 'bold' }}>{data.feature}</p>
                                <p style={{ margin: '4px 0 0 0' }}>任务: {data.task}</p>
                                <p style={{ margin: '4px 0 0 0' }}>均值: {data.value.toFixed(4)}</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Scatter data={heatmapData} fill="#8884d8">
                        {heatmapData.map((entry, index) => {
                          // 根据值的大小设置颜色
                          const maxVal = Math.max(...heatmapData.map(d => d.value));
                          const minVal = Math.min(...heatmapData.map(d => d.value));
                          const normalized = (entry.value - minVal) / (maxVal - minVal);
                          const color = `rgb(${Math.floor(255 * (1 - normalized))}, ${Math.floor(100 + 155 * normalized)}, ${Math.floor(255 * (1 - normalized))})`;
                          return <Cell key={`cell-${index}`} fill={color} />;
                        })}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                );
              })()}
            </div>
          </Card>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
          <BarChartOutlined style={{ fontSize: 48, marginBottom: 16 }} />
          <p>选择参数和至少2个任务后，点击&quot;开始对比&quot;按钮</p>
        </div>
      )}
    </Card>
  );

  // ===== 主渲染 =====
  return (
    <div style={{ padding: '0px' }}>
      <Tabs
        activeKey={activeSubTab}
        onChange={setActiveSubTab}
        items={[
          {
            key: 'param-eval',
            label: (
              <span>
                <RocketOutlined />
                参数优化
              </span>
            ),
            children: renderParamEvaluation()
          },
          {
            key: 'task-analysis',
            label: (
              <span>
                <LineChartOutlined />
                任务分层分析
              </span>
            ),
            children: renderTaskAnalysis()
          },
          {
            key: 'task-compare',
            label: (
              <span>
                <BarChartOutlined />
                任务对比
              </span>
            ),
            children: renderTaskComparison()
          },
          {
            key: 'param-sensitivity',
            label: (
              <span>
                <ExperimentOutlined />
                参数敏感性分析
              </span>
            ),
            children: <ParameterSensitivityPanel />
          },
          {
            key: 'enhanced-viz',
            label: (
              <span>
                <PictureOutlined />
                可视化分析(新)
              </span>
            ),
            children: <EnhancedVisualizationPanel />
          },
          {
            key: 'individual-query',
            label: (
              <span>
                <UserOutlined />
                个体查询
              </span>
            ),
            children: <IndividualQueryPanel selectedParam={selectedParam} />
          }
        ]}
      />
    </div>
  );
};

export default AdvancedAnalysisPanel;
