/**
 * Module04: 眼动事件分析模块 (优化版 - 批量分析)
 */

import React, { useState } from 'react';
import { Card, Tabs, Form, Select, Button, Table, message, Statistic, Row, Col, InputNumber, Alert } from 'antd';
import { EyeOutlined, PlayCircleOutlined, SettingOutlined, TableOutlined, BarChartOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;
const { Option } = Select;

const Module04 = () => {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [eventsData, setEventsData] = useState([]);
  const [statistics, setStatistics] = useState(null);

  // 批量分析
  const handleBatchAnalysis = async (values) => {
    setLoading(true);
    try {
      const payload = {
        data_version: values.data_version,
        group: values.group,
        ivt_params: {
          velocity_threshold: values.velocity_threshold || 40.0,
          min_fixation_duration: values.min_fixation_duration || 100
        }
      };

      message.info('开始批量分析，请稍候...');
      const response = await axios.post('/api/m04/analyze/batch', payload);

      if (response.data.success) {
        setAnalysisResult(response.data);

        // 计算统计信息
        const totalFix = response.data.results?.reduce((sum, r) =>
          sum + r.results?.reduce((s, t) => s + (t.summary?.total_fixations || 0), 0), 0);
        const totalSacc = response.data.results?.reduce((sum, r) =>
          sum + r.results?.reduce((s, t) => s + (t.summary?.total_saccades || 0), 0), 0);

        setStatistics({
          totalSubjects: response.data.total_subjects,
          totalFixations: totalFix,
          totalSaccades: totalSacc,
          totalEvents: totalFix + totalSacc
        });

        message.success(`分析完成！处理了 ${response.data.total_subjects} 个受试者`);

        // 加载事件表格
        loadEventsFromResult(response.data);
      } else {
        message.error(response.data.error || '批量分析失败');
      }
    } catch (error) {
      message.error('分析请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 从分析结果加载事件数据
  const loadEventsFromResult = (result) => {
    const events = [];
    result.results?.forEach(subjectResult => {
      const sid = subjectResult.subject_id;
      const grp = subjectResult.group;

      subjectResult.results?.forEach(taskResult => {
        if (!taskResult.success) return;
        const tid = taskResult.task_id;

        // Fixations
        taskResult.fixations?.forEach((fix, idx) => {
          events.push({
            key: `${sid}_${tid}_fix_${idx}`,
            subject_id: sid,
            group: grp,
            task_id: tid,
            event_type: 'fixation',
            duration_ms: fix.duration_ms,
            centroid_x: fix.centroid_x,
            centroid_y: fix.centroid_y,
            dispersion: fix.dispersion,
            roi: fix.roi
          });
        });

        // Saccades
        taskResult.saccades?.forEach((sacc, idx) => {
          events.push({
            key: `${sid}_${tid}_sacc_${idx}`,
            subject_id: sid,
            group: grp,
            task_id: tid,
            event_type: 'saccade',
            duration_ms: sacc.duration_ms,
            amplitude: sacc.amplitude,
            max_velocity: sacc.max_velocity,
            mean_velocity: sacc.mean_velocity
          });
        });
      });
    });

    setEventsData(events);
  };

  // 事件表格列
  const eventColumns = [
    { title: '受试者', dataIndex: 'subject_id', key: 'subject_id', width: 120, fixed: 'left' },
    { title: '组别', dataIndex: 'group', key: 'group', width: 80 },
    { title: '任务', dataIndex: 'task_id', key: 'task_id', width: 80 },
    {
      title: '事件类型',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 100,
      render: (type) => type === 'fixation' ? '注视' : '扫视',
      filters: [
        { text: '注视', value: 'fixation' },
        { text: '扫视', value: 'saccade' }
      ],
      onFilter: (value, record) => record.event_type === value
    },
    {
      title: '时长(ms)',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (val) => val?.toFixed(2),
      sorter: (a, b) => a.duration_ms - b.duration_ms
    },
    { title: 'X坐标', dataIndex: 'centroid_x', key: 'centroid_x', width: 90, render: (v) => v?.toFixed(3) },
    { title: 'Y坐标', dataIndex: 'centroid_y', key: 'centroid_y', width: 90, render: (v) => v?.toFixed(3) },
    { title: 'ROI区域', dataIndex: 'roi', key: 'roi', width: 150 },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card title={<><EyeOutlined /> Module04: 眼动事件分析 (IVT算法)</>}>
        <Tabs defaultActiveKey="1">
          {/* Tab 1: 批量分析 */}
          <TabPane tab={<><PlayCircleOutlined /> 批量分析</>} key="1">
            <Alert
              message="批量分析说明"
              description={
                <div>
                  <p>• 选择数据版本（V1/V2）自动分析所有受试者数据</p>
                  <p>• 可配置IVT算法参数：速度阈值和最小注视时长</p>
                  <p>• V2数据接口已保留，待数据整理完成后启用</p>
                </div>
              }
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Card title="分析配置" size="small" style={{ marginBottom: 16 }}>
              <Form
                layout="horizontal"
                labelCol={{ span: 6 }}
                wrapperCol={{ span: 18 }}
                onFinish={handleBatchAnalysis}
                initialValues={{
                  data_version: 'v1',
                  velocity_threshold: 40.0,
                  min_fixation_duration: 100
                }}
              >
                <Row gutter={24}>
                  <Col span={12}>
                    <Form.Item
                      label="数据版本"
                      name="data_version"
                      rules={[{ required: true, message: '请选择数据版本' }]}
                    >
                      <Select>
                        <Option value="v1">V1 (可用)</Option>
                        <Option value="v2" disabled>V2 (待整理)</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      label="分组筛选"
                      name="group"
                      extra="不选择则分析全部组别"
                    >
                      <Select allowClear placeholder="全部组别">
                        <Option value="control">Control</Option>
                        <Option value="mci">MCI</Option>
                        <Option value="ad">AD</Option>
                      </Select>
                    </Form.Item>
                  </Col>

                  <Col span={12}>
                    <Form.Item
                      label={<><SettingOutlined /> 速度阈值</>}
                      name="velocity_threshold"
                      extra="deg/s，用于区分注视和扫视"
                    >
                      <InputNumber min={10} max={100} step={5} style={{ width: '100%' }} />
                    </Form.Item>

                    <Form.Item
                      label={<><SettingOutlined /> 最小注视时长</>}
                      name="min_fixation_duration"
                      extra="ms，短于此时长的注视被归类为扫视"
                    >
                      <InputNumber min={50} max={500} step={50} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item wrapperCol={{ span: 24 }}>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<PlayCircleOutlined />}
                    loading={loading}
                    size="large"
                    block
                  >
                    {loading ? '分析中...' : '开始批量分析'}
                  </Button>
                </Form.Item>
              </Form>
            </Card>

            {statistics && (
              <Card title="分析统计" size="small">
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic title="受试者数" value={statistics.totalSubjects} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="总事件数" value={statistics.totalEvents} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="注视事件" value={statistics.totalFixations} valueStyle={{ color: '#3f8600' }} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="扫视事件" value={statistics.totalSaccades} valueStyle={{ color: '#cf1322' }} />
                  </Col>
                </Row>
              </Card>
            )}
          </TabPane>

          {/* Tab 2: 事件数据表格 */}
          <TabPane tab={<><TableOutlined /> 事件数据 ({eventsData.length})</>} key="2">
            <Table
              dataSource={eventsData}
              columns={eventColumns}
              pagination={{ pageSize: 100, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
              size="small"
              scroll={{ x: 1000, y: 600 }}
              loading={loading}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Module04;
