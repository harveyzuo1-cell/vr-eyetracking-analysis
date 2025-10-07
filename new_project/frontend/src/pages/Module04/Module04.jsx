/**
 * Module04: 眼动事件分析模块 (批量分析 + 特征统计)
 */

import React, { useState } from 'react';
import { Card, Tabs, Form, Select, Button, Table, message, Statistic, Row, Col, InputNumber, Alert, Spin } from 'antd';
import { EyeOutlined, PlayCircleOutlined, TableOutlined, BarChartOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;
const { Option } = Select;

const Module04 = () => {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [eventsData, setEventsData] = useState([]);
  const [featuresData, setFeaturesData] = useState([]);
  const [statistics, setStatistics] = useState(null);

  // 批量分析
  const handleBatchAnalysis = async (values) => {
    setLoading(true);
    try {
      const payload = {
        data_version: values.data_version,
        velocity_threshold: values.velocity_threshold || 40.0,
        min_fixation_duration: values.min_fixation_duration || 100
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

        // 加载基本事件表格数据
        loadEventsFromResult(response.data);

        // 加载特征统计数据
        await loadFeaturesData(values);
      } else {
        message.error(response.data.error || '批量分析失败');
      }
    } catch (error) {
      message.error('分析请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 从分析结果加载基本事件数据
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

  // 加载特征统计数据
  const loadFeaturesData = async (values) => {
    try {
      const payload = {
        data_version: values.data_version,
        velocity_threshold: values.velocity_threshold || 40.0,
        min_fixation_duration: values.min_fixation_duration || 100
      };

      const response = await axios.post('/api/m04/features', payload);

      if (response.data.success) {
        const features = response.data.features.map((f, idx) => ({
          ...f,
          key: `${f.subject_id}_${f.task_id}`
        }));
        setFeaturesData(features);
      } else {
        message.error('获取特征统计失败: ' + response.data.error);
      }
    } catch (error) {
      message.error('特征统计请求失败: ' + error.message);
    }
  };

  // 基本事件表格列
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

  // 特征统计表格列
  const featureColumns = [
    { title: '受试者', dataIndex: 'subject_id', key: 'subject_id', width: 120, fixed: 'left' },
    { title: '组别', dataIndex: 'group', key: 'group', width: 80, fixed: 'left' },
    { title: '任务', dataIndex: 'task_id', key: 'task_id', width: 80, fixed: 'left' },
    { title: 'BG占比(%)', dataIndex: 'bg_ratio', key: 'bg_ratio', width: 100, render: (v) => v?.toFixed(2), sorter: (a, b) => a.bg_ratio - b.bg_ratio },
    { title: 'INST占比(%)', dataIndex: 'inst_ratio', key: 'inst_ratio', width: 110, render: (v) => v?.toFixed(2), sorter: (a, b) => a.inst_ratio - b.inst_ratio },
    { title: 'KW占比(%)', dataIndex: 'kw_ratio', key: 'kw_ratio', width: 100, render: (v) => v?.toFixed(2), sorter: (a, b) => a.kw_ratio - b.kw_ratio },
    { title: 'Fixation总时长(ms)', dataIndex: 'total_fixation_time', key: 'total_fixation_time', width: 150, render: (v) => v?.toFixed(2), sorter: (a, b) => a.total_fixation_time - b.total_fixation_time },
    { title: 'Fixation总次数', dataIndex: 'total_fixations', key: 'total_fixations', width: 130, sorter: (a, b) => a.total_fixations - b.total_fixations },
    { title: '平均Fixation时长(ms)', dataIndex: 'avg_fixation_duration', key: 'avg_fixation_duration', width: 170, render: (v) => v?.toFixed(2), sorter: (a, b) => a.avg_fixation_duration - b.avg_fixation_duration },
    { title: 'Saccade总次数', dataIndex: 'total_saccades', key: 'total_saccades', width: 130, sorter: (a, b) => a.total_saccades - b.total_saccades },
    { title: '平均Saccade幅度(deg)', dataIndex: 'avg_saccade_amplitude', key: 'avg_saccade_amplitude', width: 180, render: (v) => v?.toFixed(4), sorter: (a, b) => a.avg_saccade_amplitude - b.avg_saccade_amplitude },
    { title: '任务总时长(ms)', dataIndex: 'task_total_time', key: 'task_total_time', width: 130, render: (v) => v?.toFixed(2), sorter: (a, b) => a.task_total_time - b.task_total_time },
    { title: 'MMSE总分', dataIndex: 'mmse_total_score', key: 'mmse_total_score', width: 100, render: (v) => v !== null ? v : '-' },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card title={<><EyeOutlined /> Module04: 眼动事件分析 (IVT算法)</>}>
        <Tabs defaultActiveKey="1">
          {/* Tab 1: 批量分析 */}
          <TabPane tab={<><PlayCircleOutlined /> 批量分析</>} key="1">
            <Alert
              message="批量分析说明"
              description="选择数据版本（V1/V2）自动分析所有受试者数据。可配置IVT算法参数：速度阈值和最小注视时长。"
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
                    <Form.Item label="数据版本" name="data_version" rules={[{ required: true, message: '请选择数据版本' }]}>
                      <Select placeholder="选择数据版本">
                        <Option value="v1">V1 (可用)</Option>
                        <Option value="v2" disabled>V2 (待整理)</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item label="速度阈值" name="velocity_threshold" extra="deg/s，用于区分注视和扫视">
                      <InputNumber min={10} max={100} step={5} style={{ width: '100%' }} />
                    </Form.Item>

                    <Form.Item label="最小注视时长" name="min_fixation_duration" extra="ms，短于此时长的注视被归类为扫视">
                      <InputNumber min={50} max={500} step={50} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />} loading={loading}>
                    开始分析
                  </Button>
                </Form.Item>
              </Form>
            </Card>

            {/* 分析统计 */}
            {statistics && (
              <Card title="分析统计" size="small" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={6}><Statistic title="受试者数" value={statistics.totalSubjects} /></Col>
                  <Col span={6}><Statistic title="总事件数" value={statistics.totalEvents} /></Col>
                  <Col span={6}><Statistic title="注视事件" value={statistics.totalFixations} /></Col>
                  <Col span={6}><Statistic title="扫视事件" value={statistics.totalSaccades} /></Col>
                </Row>
              </Card>
            )}
          </TabPane>

          {/* Tab 2: 基本事件数据 */}
          <TabPane tab={<><TableOutlined /> 基本事件数据</>} key="2">
            <Spin spinning={loading}>
              <Table
                dataSource={eventsData}
                columns={eventColumns}
                pagination={{ pageSize: 100, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
                scroll={{ x: 1200, y: 600 }}
                size="small"
              />
            </Spin>
          </TabPane>

          {/* Tab 3: 特征统计 */}
          <TabPane tab={<><BarChartOutlined /> 特征统计</>} key="3">
            <Alert
              message="特征说明"
              description="每行代表一个受试者-任务组合。包含ROI占比（BG/INST/KW）、事件统计（Fixation和Saccade）、MMSE分数等。"
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Spin spinning={loading}>
              <Table
                dataSource={featuresData}
                columns={featureColumns}
                pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
                scroll={{ x: 2000, y: 600 }}
                size="small"
              />
            </Spin>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Module04;
