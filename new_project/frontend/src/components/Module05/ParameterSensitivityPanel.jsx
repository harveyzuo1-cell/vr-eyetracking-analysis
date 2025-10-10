/**
 * Module05: 参数敏感性分析面板
 *
 * 功能:
 * 1. 计算并显示RQA参数敏感性评分表
 * 2. 生成3D参数空间可视化
 * 3. 生成参数-特征热图
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Button, Table, Space, Spin, message, Tabs,
  Select, InputNumber, Alert, Statistic, Row, Col, Progress
} from 'antd';
import {
  ExperimentOutlined, BarChartOutlined, HeatMapOutlined,
  ThunderboltOutlined, FundOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const ParameterSensitivityPanel = () => {
  const [loading, setLoading] = useState(false);
  const [sensitivityScores, setSensitivityScores] = useState([]);
  const [activeTab, setActiveTab] = useState('scores');

  // Async task tracking
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState('');
  const [pollingInterval, setPollingInterval] = useState(null);

  // 3D plot controls
  const [selectedFeature, setSelectedFeature] = useState('combined_rr');
  const [xParam, setXParam] = useState('m');
  const [yParam, setYParam] = useState('tau');
  const [zMetric, setZMetric] = useState('f_statistic');
  const [colorParam, setColorParam] = useState('eps');
  const [plotHtml, setPlotHtml] = useState(null);

  // Heatmap controls
  const [heatmapMetric, setHeatmapMetric] = useState('overall_score');
  const [heatmapHtml, setHeatmapHtml] = useState(null);

  const rqaFeatures = [
    'rr', 'det', 'lam', 'l_mean', 'l_max',
    'entropy', 'trend', 'combined_rr'
  ];

  const paramOptions = ['m', 'tau', 'eps', 'lmin'];
  const metricOptions = [
    { value: 'f_statistic', label: 'F统计量' },
    { value: 'p_value', label: 'P值' },
    { value: 'effect_size', label: '效应量' },
    { value: 'task_consistency', label: '任务一致性' },
    { value: 'overall_score', label: '综合评分' }
  ];

  // 计算敏感性评分（异步任务）
  const computeSensitivityScores = async () => {
    // 清理之前的轮询
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }

    setLoading(true);
    setProgress(0);
    setProgressStatus('');
    setSensitivityScores([]);

    try {
      // 提交任务
      const response = await axios.post('/api/m05/sensitivity/compute-scores', {});

      if (response.data.success) {
        const newTaskId = response.data.data.task_id;
        setTaskId(newTaskId);
        message.info(`任务已提交: ${newTaskId}`);

        // 开始轮询任务状态
        pollTaskStatus(newTaskId);
      } else {
        message.error(response.data.error || '任务提交失败');
        setLoading(false);
      }
    } catch (error) {
      console.error('提交敏感性分析任务失败:', error);
      message.error('任务提交失败: ' + (error.response?.data?.error || error.message));
      setLoading(false);
    }
  };

  // 轮询任务状态
  const pollTaskStatus = async (taskIdToPoll) => {
    const interval = setInterval(async () => {
      try {
        const statusResponse = await axios.get(`/api/m05/sensitivity/status/${taskIdToPoll}`);

        if (statusResponse.data.success) {
          const taskData = statusResponse.data.data;

          // 更新进度
          if (taskData.progress) {
            const percentage = taskData.progress.percentage || 0;
            setProgress(percentage);
            setProgressStatus(taskData.progress.status || '');
          }

          // 检查任务是否完成
          if (taskData.task && taskData.task.status === 'completed') {
            clearInterval(interval);
            setPollingInterval(null);
            setLoading(false);
            setProgress(100);

            // 加载结果
            if (taskData.sensitivity_scores) {
              setSensitivityScores(taskData.sensitivity_scores);
              message.success(`成功计算 ${taskData.total_params} 个参数组合的敏感性评分`);
            }
          } else if (taskData.task && taskData.task.status === 'failed') {
            clearInterval(interval);
            setPollingInterval(null);
            setLoading(false);
            message.error('任务执行失败: ' + (taskData.task.error_message || '未知错误'));
          }
        }
      } catch (error) {
        console.error('轮询任务状态失败:', error);
        clearInterval(interval);
        setPollingInterval(null);
        setLoading(false);
        message.error('获取任务状态失败');
      }
    }, 1000); // 每秒轮询一次

    // 保存interval引用
    setPollingInterval(interval);
  };

  // 清理effect - 防止组件卸载时仍在轮询
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // 生成3D参数空间图
  const generate3DPlot = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/m05/sensitivity/plot-3d-space', {
        feature: selectedFeature,
        x_param: xParam,
        y_param: yParam,
        z_metric: zMetric,
        color_param: colorParam
      });

      if (response.data.success) {
        setPlotHtml(response.data.html_path);
        message.success('3D图表生成成功');
      } else {
        message.error('生成失败');
      }
    } catch (error) {
      console.error('生成3D图表失败:', error);
      message.error('生成3D图表失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 生成热图
  const generateHeatmap = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/m05/sensitivity/plot-heatmap', {
        metric: heatmapMetric
      });

      if (response.data.success) {
        setHeatmapHtml(response.data.html_path);
        message.success('热图生成成功');
      } else {
        message.error('生成失败');
      }
    } catch (error) {
      console.error('生成热图失败:', error);
      message.error('生成热图失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '参数组合',
      dataIndex: 'param_signature',
      key: 'param_signature',
      fixed: 'left',
      width: 200,
      sorter: (a, b) => a.param_signature.localeCompare(b.param_signature)
    },
    {
      title: 'RQA特征',
      dataIndex: 'feature',
      key: 'feature',
      width: 120,
      filters: rqaFeatures.map(f => ({ text: f, value: f })),
      onFilter: (value, record) => record.feature === value
    },
    {
      title: 'F统计量',
      dataIndex: 'f_statistic',
      key: 'f_statistic',
      width: 120,
      sorter: (a, b) => a.f_statistic - b.f_statistic,
      render: val => val.toFixed(3)
    },
    {
      title: 'P值',
      dataIndex: 'p_value',
      key: 'p_value',
      width: 100,
      sorter: (a, b) => a.p_value - b.p_value,
      render: val => val.toFixed(4)
    },
    {
      title: '效应量',
      dataIndex: 'effect_size',
      key: 'effect_size',
      width: 100,
      sorter: (a, b) => a.effect_size - b.effect_size,
      render: val => val.toFixed(3)
    },
    {
      title: '任务一致性',
      dataIndex: 'task_consistency',
      key: 'task_consistency',
      width: 120,
      sorter: (a, b) => a.task_consistency - b.task_consistency,
      render: val => val.toFixed(3)
    },
    {
      title: '综合评分',
      dataIndex: 'overall_score',
      key: 'overall_score',
      width: 120,
      sorter: (a, b) => a.overall_score - b.overall_score,
      render: val => val.toFixed(3),
      defaultSortOrder: 'descend'
    }
  ];

  // 计算统计信息
  const stats = React.useMemo(() => {
    if (sensitivityScores.length === 0) return null;

    const uniqueParams = new Set(sensitivityScores.map(s => s.param_signature)).size;
    const uniqueFeatures = new Set(sensitivityScores.map(s => s.feature)).size;
    const avgFStat = sensitivityScores.reduce((sum, s) => sum + s.f_statistic, 0) / sensitivityScores.length;
    const avgScore = sensitivityScores.reduce((sum, s) => sum + s.overall_score, 0) / sensitivityScores.length;

    return { uniqueParams, uniqueFeatures, avgFStat, avgScore };
  }, [sensitivityScores]);

  const tabItems = [
    {
      key: 'scores',
      label: <span><FundOutlined />敏感性评分表</span>,
      children: (
        <div>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="参数敏感性分析"
              description="评估不同RQA参数组合在区分control/MCI/AD组别时的敏感性。F统计量越大、P值越小、效应量越大，说明该参数组合的区分能力越强。"
              type="info"
              showIcon
            />

            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={computeSensitivityScores}
              loading={loading}
              size="large"
            >
              计算敏感性评分
            </Button>

            {loading && (
              <Card>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>任务ID: {taskId}</div>
                  <Progress
                    percent={progress}
                    status={progressStatus === 'completed' ? 'success' : 'active'}
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                  <div>状态: {progressStatus || '处理中...'}</div>
                </Space>
              </Card>
            )}

            {stats && (
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic title="参数组合数" value={stats.uniqueParams} />
                </Col>
                <Col span={6}>
                  <Statistic title="RQA特征数" value={stats.uniqueFeatures} />
                </Col>
                <Col span={6}>
                  <Statistic title="平均F统计量" value={stats.avgFStat} precision={3} />
                </Col>
                <Col span={6}>
                  <Statistic title="平均综合评分" value={stats.avgScore} precision={3} />
                </Col>
              </Row>
            )}

            <Table
              columns={columns}
              dataSource={sensitivityScores}
              rowKey={(record, index) => `${record.param_signature}_${record.feature}_${index}`}
              loading={loading}
              pagination={{ pageSize: 20, showSizeChanger: true, showTotal: total => `共 ${total} 条` }}
              scroll={{ x: 1200, y: 600 }}
              size="small"
            />
          </Space>
        </div>
      )
    },
    {
      key: '3d',
      label: <span><BarChartOutlined />3D参数空间</span>,
      children: (
        <div>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="3D参数空间可视化"
              description="使用Plotly交互式3D图表展示参数空间。可以旋转、缩放、查看数据点详情。"
              type="info"
              showIcon
            />

            <Card title="参数配置">
              <Space wrap>
                <span>RQA特征:</span>
                <Select value={selectedFeature} onChange={setSelectedFeature} style={{ width: 150 }}>
                  {rqaFeatures.map(f => <Option key={f} value={f}>{f}</Option>)}
                </Select>

                <span>X轴:</span>
                <Select value={xParam} onChange={setXParam} style={{ width: 100 }}>
                  {paramOptions.map(p => <Option key={p} value={p}>{p}</Option>)}
                </Select>

                <span>Y轴:</span>
                <Select value={yParam} onChange={setYParam} style={{ width: 100 }}>
                  {paramOptions.map(p => <Option key={p} value={p}>{p}</Option>)}
                </Select>

                <span>Z轴:</span>
                <Select value={zMetric} onChange={setZMetric} style={{ width: 150 }}>
                  {metricOptions.map(m => <Option key={m.value} value={m.value}>{m.label}</Option>)}
                </Select>

                <span>颜色:</span>
                <Select value={colorParam} onChange={setColorParam} style={{ width: 100 }}>
                  {paramOptions.map(p => <Option key={p} value={p}>{p}</Option>)}
                </Select>

                <Button type="primary" onClick={generate3DPlot} loading={loading}>
                  生成3D图表
                </Button>
              </Space>
            </Card>

            {plotHtml && (
              <Card title="3D参数空间图">
                <iframe
                  src={plotHtml}
                  style={{ width: '100%', height: '700px', border: 'none' }}
                  title="3D Parameter Space"
                />
              </Card>
            )}
          </Space>
        </div>
      )
    },
    {
      key: 'heatmap',
      label: <span><HeatMapOutlined />参数-特征热图</span>,
      children: (
        <div>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="参数-特征热图"
              description="热图展示不同参数组合对各RQA特征的敏感性。颜色越深表示敏感性越高。"
              type="info"
              showIcon
            />

            <Card title="热图配置">
              <Space>
                <span>评分指标:</span>
                <Select value={heatmapMetric} onChange={setHeatmapMetric} style={{ width: 150 }}>
                  {metricOptions.map(m => <Option key={m.value} value={m.value}>{m.label}</Option>)}
                </Select>

                <Button type="primary" onClick={generateHeatmap} loading={loading}>
                  生成热图
                </Button>
              </Space>
            </Card>

            {heatmapHtml && (
              <Card title="参数-特征敏感性热图">
                <iframe
                  src={heatmapHtml}
                  style={{ width: '100%', height: '700px', border: 'none' }}
                  title="Parameter-Feature Heatmap"
                />
              </Card>
            )}
          </Space>
        </div>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card
        title={
          <span>
            <ExperimentOutlined style={{ marginRight: 8 }} />
            参数敏感性分析
          </span>
        }
        bordered={false}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  );
};

export default ParameterSensitivityPanel;
