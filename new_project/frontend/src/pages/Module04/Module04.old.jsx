/**
 * Module04: 眼动事件分析模块
 *
 * 功能:
 * - IVT算法事件检测 (注视/扫视)
 * - 事件数据表格展示
 * - ROI统计分析
 */

import React, { useState } from 'react';
import { Card, Tabs, Form, Select, Button, Table, message, Statistic, Row, Col } from 'antd';
import { EyeOutlined, TableOutlined, BarChartOutlined, PlayCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;
const { Option } = Select;

const Module04 = () => {
  const [loading, setLoading] = useState(false);
  const [eventsData, setEventsData] = useState([]);
  const [roiStats, setRoiStats] = useState([]);
  const [summary, setSummary] = useState(null);

  // 分析单个受试者
  const handleAnalyzeSubject = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/m04/analyze/subject', values);

      if (response.data.success) {
        message.success(`分析完成! 成功分析 ${response.data.successful_tasks} 个任务`);
        setSummary(response.data);

        // 刷新事件表格
        loadEventsTable(values.subject_id, values.group);
      } else {
        message.error(response.data.error || '分析失败');
      }
    } catch (error) {
      message.error('分析请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 加载事件数据表格
  const loadEventsTable = async (subjectId, group) => {
    try {
      const params = {};
      if (subjectId) params.subject_id = subjectId;
      if (group) params.group = group;

      const response = await axios.get('/api/m04/events', { params });

      if (response.data.success) {
        setEventsData(response.data.events);
      }
    } catch (error) {
      message.error('加载事件数据失败: ' + error.message);
    }
  };

  // 加载ROI统计
  const loadROIStats = async (group, taskId) => {
    try {
      const params = {};
      if (group) params.group = group;
      if (taskId) params.task_id = taskId;

      const response = await axios.get('/api/m04/roi/statistics', { params });

      if (response.data.success) {
        setRoiStats(response.data.roi_statistics);
      }
    } catch (error) {
      message.error('加载ROI统计失败: ' + error.message);
    }
  };

  // 事件表格列定义
  const eventsColumns = [
    { title: '受试者ID', dataIndex: 'subject_id', key: 'subject_id', width: 120 },
    { title: '分组', dataIndex: 'group', key: 'group', width: 80 },
    { title: '任务', dataIndex: 'task_id', key: 'task_id', width: 80 },
    {
      title: '事件类型',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 100,
      render: (type) => type === 'fixation' ? '注视' : '扫视'
    },
    {
      title: '时长(ms)',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (val) => val?.toFixed(2)
    },
    {
      title: '中心X',
      dataIndex: 'centroid_x',
      key: 'centroid_x',
      width: 100,
      render: (val) => val?.toFixed(3)
    },
    {
      title: '中心Y',
      dataIndex: 'centroid_y',
      key: 'centroid_y',
      width: 100,
      render: (val) => val?.toFixed(3)
    },
    { title: 'ROI区域', dataIndex: 'roi', key: 'roi', width: 150 },
  ];

  // ROI统计表格列定义
  const roiStatsColumns = [
    { title: 'ROI区域', dataIndex: 'roi', key: 'roi' },
    { title: '注视次数', dataIndex: 'fixation_count', key: 'fixation_count' },
    {
      title: '总时长(ms)',
      dataIndex: 'total_duration_ms',
      key: 'total_duration_ms',
      render: (val) => val?.toFixed(2)
    },
    {
      title: '平均时长(ms)',
      dataIndex: 'avg_duration_ms',
      key: 'avg_duration_ms',
      render: (val) => val?.toFixed(2)
    },
    { title: '受试者数', dataIndex: 'unique_subjects', key: 'unique_subjects' },
    { title: '任务数', dataIndex: 'unique_tasks', key: 'unique_tasks' },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card title={<><EyeOutlined /> Module04: 眼动事件分析</>}>
        <Tabs defaultActiveKey="1">
          {/* Tab 1: 事件分析 */}
          <TabPane tab={<><PlayCircleOutlined /> 事件分析</>} key="1">
            <Card title="分析配置" style={{ marginBottom: 16 }}>
              <Form
                layout="inline"
                onFinish={handleAnalyzeSubject}
              >
                <Form.Item
                  label="受试者ID"
                  name="subject_id"
                  rules={[{ required: true, message: '请输入受试者ID' }]}
                >
                  <input placeholder="例如: legacy_1" style={{ width: 200 }} />
                </Form.Item>

                <Form.Item
                  label="分组"
                  name="group"
                  rules={[{ required: true, message: '请选择分组' }]}
                >
                  <Select style={{ width: 120 }}>
                    <Option value="control">Control</Option>
                    <Option value="mci">MCI</Option>
                    <Option value="ad">AD</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  label="数据版本"
                  name="data_version"
                  initialValue="v1"
                >
                  <Select style={{ width: 100 }}>
                    <Option value="v1">V1</Option>
                    <Option value="v2">V2</Option>
                  </Select>
                </Form.Item>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading} icon={<PlayCircleOutlined />}>
                    开始分析
                  </Button>
                </Form.Item>
              </Form>
            </Card>

            {summary && (
              <Card title="分析摘要" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic title="分析任务数" value={summary.analyzed_tasks} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="成功任务数" value={summary.successful_tasks} />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="总注视事件"
                      value={summary.results?.reduce((sum, r) => sum + (r.summary?.total_fixations || 0), 0)}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="总扫视事件"
                      value={summary.results?.reduce((sum, r) => sum + (r.summary?.total_saccades || 0), 0)}
                    />
                  </Col>
                </Row>
              </Card>
            )}
          </TabPane>

          {/* Tab 2: 事件数据表格 */}
          <TabPane tab={<><TableOutlined /> 事件数据</>} key="2">
            <Card
              title="事件数据表格"
              extra={
                <Button onClick={() => loadEventsTable()}>
                  刷新全部数据
                </Button>
              }
            >
              <Table
                dataSource={eventsData}
                columns={eventsColumns}
                rowKey={(record, index) => `${record.subject_id}_${record.task_id}_${index}`}
                pagination={{ pageSize: 50 }}
                size="small"
                scroll={{ x: 1000 }}
              />
            </Card>
          </TabPane>

          {/* Tab 3: ROI统计 */}
          <TabPane tab={<><BarChartOutlined /> ROI统计</>} key="3">
            <Card
              title="ROI停留统计"
              extra={
                <Button onClick={() => loadROIStats()}>
                  刷新统计
                </Button>
              }
            >
              <Table
                dataSource={roiStats}
                columns={roiStatsColumns}
                rowKey="roi"
                pagination={{ pageSize: 20 }}
                size="small"
              />
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Module04;
