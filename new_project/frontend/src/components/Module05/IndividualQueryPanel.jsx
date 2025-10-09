/**
 * 个体查询面板 - 基于RQA的个体分析
 *
 * 功能:
 * 1. 个体RQA档案查询
 * 2. 个体vs组平均对比
 * 3. 认知风险评估
 * 4. 任务进程趋势分析
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Select, Button, Spin, Alert, Descriptions, Table,
  Row, Col, Statistic, Tag, Progress, Divider, Empty, message, Space
} from 'antd';
import {
  UserOutlined, LineChartOutlined, WarningOutlined,
  CheckCircleOutlined, InfoCircleOutlined, TrophyOutlined
} from '@ant-design/icons';
import Plot from 'react-plotly.js';
import axios from 'axios';

const { Option } = Select;

const IndividualQueryPanel = ({ selectedParam }) => {
  // ===== 状态管理 =====
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [loading, setLoading] = useState(false);

  // 分析结果
  const [profile, setProfile] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [taskProgression, setTaskProgression] = useState(null);

  // ===== 组件挂载时加载受试者列表 =====
  useEffect(() => {
    if (selectedParam) {
      fetchSubjects();
    }
  }, [selectedParam]);

  // ===== API调用函数 =====

  /**
   * 获取受试者列表
   */
  const fetchSubjects = async () => {
    if (!selectedParam) return;

    try {
      const response = await axios.post('/api/m05/advanced/subjects/list', {
        params: selectedParam
      });

      if (response.data.success) {
        setSubjects(response.data.subjects);
      }
    } catch (error) {
      console.error('获取受试者列表失败:', error);
      message.error('获取受试者列表失败: ' + error.message);
    }
  };

  /**
   * 查询个体档案
   */
  const handleQuery = async () => {
    if (!selectedSubject || !selectedParam) {
      message.warning('请先选择受试者和参数');
      return;
    }

    setLoading(true);

    try {
      // 并行请求所有分析
      const [profileRes, comparisonRes, riskRes, progressionRes] = await Promise.all([
        axios.post('/api/m05/advanced/individual/profile', {
          subject_id: selectedSubject,
          params: selectedParam
        }),
        axios.post('/api/m05/advanced/individual/compare-to-group', {
          subject_id: selectedSubject,
          params: selectedParam
        }),
        axios.post('/api/m05/advanced/individual/risk-assessment', {
          subject_id: selectedSubject,
          params: selectedParam
        }),
        axios.post('/api/m05/advanced/individual/task-progression', {
          subject_id: selectedSubject,
          params: selectedParam
        })
      ]);

      if (profileRes.data.success) {
        setProfile(profileRes.data.profile);
      }
      if (comparisonRes.data.success) {
        setComparison(comparisonRes.data.comparison);
      }
      if (riskRes.data.success) {
        setRiskAssessment(riskRes.data.assessment);
      }
      if (progressionRes.data.success) {
        setTaskProgression(progressionRes.data.progression);
      }

      message.success(`个体分析完成: ${selectedSubject}`);

    } catch (error) {
      console.error('查询失败:', error);
      message.error('查询失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // ===== 渲染风险评分卡片 =====
  const renderRiskCard = () => {
    if (!riskAssessment) return null;

    const { risk_score, risk_level, risk_label, recommendation, risk_factors } = riskAssessment;

    // 风险颜色映射
    const riskColor = {
      'low': '#52c41a',
      'medium': '#faad14',
      'high': '#f5222d'
    };

    return (
      <Card
        title={
          <Space>
            <WarningOutlined />
            认知风险评估
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Row gutter={16}>
          <Col span={8}>
            <Card>
              <Statistic
                title="风险评分"
                value={risk_score}
                suffix="/ 100"
                valueStyle={{ color: riskColor[risk_level] }}
              />
              <Progress
                percent={risk_score}
                strokeColor={riskColor[risk_level]}
                showInfo={false}
                style={{ marginTop: 8 }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="风险等级"
                value={risk_label}
                valueStyle={{ color: riskColor[risk_level] }}
                prefix={risk_level === 'low' ? <CheckCircleOutlined /> : <WarningOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="风险因子数"
                value={risk_factors.length}
                suffix="个"
              />
            </Card>
          </Col>
        </Row>

        <Divider />

        <Descriptions title="临床建议" bordered column={1} size="small">
          <Descriptions.Item label="建议">
            {recommendation}
          </Descriptions.Item>
        </Descriptions>

        {risk_factors.length > 0 && (
          <>
            <Divider />
            <h4>识别到的风险因子：</h4>
            <ul>
              {risk_factors.map((factor, idx) => (
                <li key={idx}>
                  <Tag color={factor.severity === 'high' ? 'red' : 'orange'}>
                    {factor.severity === 'high' ? '高' : '中'}
                  </Tag>
                  <strong>{factor.factor}</strong>: {factor.description}
                </li>
              ))}
            </ul>
          </>
        )}
      </Card>
    );
  };

  // ===== 渲染任务轨迹图 =====
  const renderTaskTrajectory = () => {
    if (!profile || !profile.task_trajectories) return null;

    // 提取关键特征的轨迹数据并转换为Plotly格式
    const key_features = [
      { key: 'combined_RR', name: 'RR (递归率)', color: '#8884d8' },
      { key: 'combined_DET', name: 'DET (确定性)', color: '#82ca9d' },
      { key: 'combined_ENT', name: 'ENT (熵)', color: '#ffc658' }
    ];
    const tasks = ['q1', 'q2', 'q3', 'q4', 'q5'];

    // 构建Plotly traces
    const traces = key_features.map(feature => {
      const yValues = tasks.map(task => {
        if (profile.task_trajectories[feature.key]) {
          const point = profile.task_trajectories[feature.key].find(p => p.task === task);
          return point && point.value !== null ? point.value : null;
        }
        return null;
      });

      return {
        x: tasks,
        y: yValues,
        type: 'scatter',
        mode: 'lines+markers',
        name: feature.name,
        line: { color: feature.color, width: 2 },
        marker: { size: 8 }
      };
    });

    if (traces.length === 0) return null;

    const layout = {
      title: '',
      xaxis: { title: '任务' },
      yaxis: { title: 'RQA值' },
      hovermode: 'closest',
      height: 400,
      margin: { l: 50, r: 50, t: 20, b: 50 }
    };

    const config = {
      displayModeBar: true,
      displaylogo: false,
      toImageButtonOptions: {
        format: 'png',
        filename: `rqa_trajectory_${profile.subject_id}`
      }
    };

    return (
      <Card
        title={
          <Space>
            <LineChartOutlined />
            RQA任务轨迹
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Plot
          data={traces}
          layout={layout}
          config={config}
          style={{ width: '100%' }}
          useResizeHandler
        />

        {taskProgression && taskProgression.interpretation && (
          <Alert
            message="趋势解读"
            description={taskProgression.interpretation}
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
    );
  };

  // ===== 渲染个体vs组对比表格 =====
  const renderComparisonTable = () => {
    if (!comparison || !comparison.comparison) return null;

    const columns = [
      {
        title: 'RQA特征',
        dataIndex: 'feature',
        key: 'feature',
        fixed: 'left',
        width: 150
      },
      {
        title: '个体均值',
        dataIndex: 'individual_mean',
        key: 'individual_mean',
        render: (val) => val?.toFixed(4) || 'N/A'
      },
      {
        title: '组平均',
        dataIndex: 'group_mean',
        key: 'group_mean',
        render: (val) => val?.toFixed(4) || 'N/A'
      },
      {
        title: 'Z分数',
        dataIndex: 'z_score',
        key: 'z_score',
        render: (val) => {
          const color = Math.abs(val) > 2 ? 'red' : Math.abs(val) > 1 ? 'orange' : 'green';
          return <Tag color={color}>{val?.toFixed(2)}</Tag>;
        },
        sorter: (a, b) => Math.abs(b.z_score) - Math.abs(a.z_score)
      },
      {
        title: '偏离(%)',
        dataIndex: 'deviation_percentage',
        key: 'deviation_percentage',
        render: (val) => `${val?.toFixed(1)}%`,
        sorter: (a, b) => Math.abs(b.deviation_percentage) - Math.abs(a.deviation_percentage)
      },
      {
        title: '是否异常',
        dataIndex: 'is_outlier',
        key: 'is_outlier',
        render: (isOutlier) => isOutlier ? (
          <Tag color="red">异常</Tag>
        ) : (
          <Tag color="green">正常</Tag>
        ),
        filters: [
          { text: '异常', value: true },
          { text: '正常', value: false }
        ],
        onFilter: (value, record) => record.is_outlier === value
      }
    ];

    return (
      <Card
        title={
          <Space>
            <TrophyOutlined />
            个体vs组平均对比
          </Space>
        }
        extra={
          <Space>
            <Tag color="red">异常: {comparison.outlier_count}</Tag>
            <Tag color="green">正常: {comparison.total_features - comparison.outlier_count}</Tag>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Alert
          message="对比说明"
          description={`Z分数 > 2 表示该特征显著偏离组平均水平。当前异常比例: ${(comparison.outlier_ratio * 100).toFixed(1)}%`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Table
          columns={columns}
          dataSource={comparison.comparison.map((item, idx) => ({ ...item, key: idx }))}
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: 1000 }}
        />
      </Card>
    );
  };

  // ===== 主渲染 =====
  return (
    <div>
      {/* 查询控制面板 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Space>
              <UserOutlined />
              <span>选择受试者:</span>
              <Select
                value={selectedSubject}
                onChange={setSelectedSubject}
                style={{ width: 250 }}
                placeholder="请选择受试者"
                showSearch
                filterOption={(input, option) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
              >
                {subjects.map(s => (
                  <Option key={s.subject_id} value={s.subject_id}>
                    {s.subject_id} ({s.group})
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>
          <Col span={16}>
            <Button
              type="primary"
              icon={<LineChartOutlined />}
              onClick={handleQuery}
              loading={loading}
              disabled={!selectedSubject || !selectedParam}
            >
              查询分析
            </Button>

            {selectedParam && (
              <Tag color="blue" style={{ marginLeft: 16 }}>
                参数: m={selectedParam.m}, tau={selectedParam.tau}, eps={selectedParam.eps}, lmin={selectedParam.lmin}
              </Tag>
            )}
          </Col>
        </Row>
      </Card>

      {!selectedParam && (
        <Alert
          message="请先选择参数"
          description='请在"参数优化"Tab中选择一个参数组合，或在上方手动选择'
          type="warning"
          showIcon
        />
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16 }}>正在分析个体数据，请稍候...</p>
        </div>
      )}

      {!loading && profile && (
        <>
          {/* 基本信息卡片 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Descriptions title="基本信息" bordered column={4} size="small">
              <Descriptions.Item label="受试者ID">{profile.subject_id}</Descriptions.Item>
              <Descriptions.Item label="组别">
                <Tag color={profile.group === 'control' ? 'green' : profile.group === 'mci' ? 'orange' : 'red'}>
                  {profile.group.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="任务数">{profile.task_count}</Descriptions.Item>
              <Descriptions.Item label="RQA特征数">{Object.keys(profile.individual_stats).length}</Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 风险评估卡片 */}
          {renderRiskCard()}

          {/* 任务轨迹图 */}
          {renderTaskTrajectory()}

          {/* 个体vs组对比表 */}
          {renderComparisonTable()}
        </>
      )}

      {!loading && !profile && selectedSubject && (
        <Empty
          description="请点击'查询分析'按钮开始分析"
          style={{ marginTop: 60 }}
        />
      )}
    </div>
  );
};

export default IndividualQueryPanel;
