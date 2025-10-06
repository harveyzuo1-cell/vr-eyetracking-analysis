/**
 * 数据预处理组件
 * 功能：数据质量检测、数据清洗、数据平滑
 */
import React, { useState, useEffect } from 'react';
import {
  Card, Button, Select, Form, InputNumber, Switch, message,
  Row, Col, Statistic, Progress, Descriptions, Alert, Space, Divider
} from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, ExperimentOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { preprocessingService } from '../../services/module02Service';
import { dataService } from '../../services/dataService';

const { Option } = Select;

const DataPreprocessing = () => {
  const [groups, setGroups] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [tasks, setTasks] = useState([]);

  const [selectedGroup, setSelectedGroup] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);

  const [gazeData, setGazeData] = useState(null);
  const [qualityReport, setQualityReport] = useState(null);
  const [processedData, setProcessedData] = useState(null);
  const [pipelineLog, setPipelineLog] = useState(null);

  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState(null);
  const [form] = Form.useForm();

  // 加载默认配置
  useEffect(() => {
    loadDefaultConfig();
    loadGroups();
  }, []);

  // 加载组别
  useEffect(() => {
    if (selectedGroup) {
      loadSubjects();
    }
  }, [selectedGroup]);

  // 加载任务
  useEffect(() => {
    if (selectedGroup && selectedSubject) {
      loadTasks();
    }
  }, [selectedSubject]);

  const loadDefaultConfig = async () => {
    try {
      const response = await preprocessingService.getDefaultConfig();
      if (response.success) {
        setConfig(response.data);
        form.setFieldsValue({
          enable_quality_check: response.data.enable_quality_check,
          enable_cleaning: response.data.enable_cleaning,
          enable_smoothing: response.data.enable_smoothing,
          outlier_threshold: response.data.quality_check_config.outlier_threshold,
          missing_method: response.data.cleaning_config.missing_method,
          outlier_action: response.data.cleaning_config.outlier_action,
          smooth_method: response.data.smoothing_config.method,
          window_size: response.data.smoothing_config.window_size,
          sigma: response.data.smoothing_config.sigma,
        });
      }
    } catch (error) {
      message.error('加载配置失败');
    }
  };

  const loadGroups = async () => {
    try {
      const response = await dataService.getGroups();
      if (response.success) {
        setGroups(response.data);
      }
    } catch (error) {
      console.error('加载组别失败', error);
    }
  };

  const loadSubjects = async () => {
    try {
      const response = await dataService.getSubjects(selectedGroup);
      if (response.success) {
        setSubjects(response.data);
      }
    } catch (error) {
      console.error('加载受试者失败', error);
    }
  };

  const loadTasks = async () => {
    try {
      const response = await dataService.getTasks(selectedGroup, selectedSubject);
      if (response.success) {
        setTasks(response.data);
      }
    } catch (error) {
      console.error('加载任务失败', error);
    }
  };

  // 加载眼动数据
  const handleLoadData = async () => {
    if (!selectedGroup || !selectedSubject || !selectedTask) {
      message.warning('请先选择组别、受试者和任务');
      return;
    }

    setLoading(true);
    try {
      const response = await dataService.getGazeData(selectedGroup, selectedSubject, selectedTask);
      if (response.success && response.data.gaze_data) {
        setGazeData(response.data.gaze_data);
        message.success('数据加载成功');

        // 自动进行质量检测
        await handleQualityCheck(response.data.gaze_data);
      }
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 质量检测
  const handleQualityCheck = async (data = gazeData) => {
    if (!data) {
      message.warning('请先加载数据');
      return;
    }

    setLoading(true);
    try {
      const values = form.getFieldsValue();
      const checkConfig = {
        outlier_method: '3sigma',
        outlier_threshold: values.outlier_threshold || 3.0,
      };

      const response = await preprocessingService.qualityCheck(data, checkConfig);
      if (response.success) {
        setQualityReport(response.data);
        message.success('质量检测完成');
      }
    } catch (error) {
      message.error('质量检测失败');
    } finally {
      setLoading(false);
    }
  };

  // 运行预处理流水线
  const handleRunPipeline = async () => {
    if (!gazeData) {
      message.warning('请先加载数据');
      return;
    }

    setLoading(true);
    try {
      const values = form.getFieldsValue();

      const pipelineConfig = {
        enable_quality_check: values.enable_quality_check,
        enable_cleaning: values.enable_cleaning,
        enable_smoothing: values.enable_smoothing,
        quality_check_config: {
          outlier_method: '3sigma',
          outlier_threshold: values.outlier_threshold || 3.0,
        },
        cleaning_config: {
          missing_method: values.missing_method || 'interpolate',
          outlier_action: values.outlier_action || 'interpolate',
        },
        smoothing_config: {
          method: values.smooth_method || 'gaussian',
          window_size: values.window_size || 5,
          sigma: values.sigma || 1.5,
        },
      };

      const response = await preprocessingService.runPipeline(gazeData, pipelineConfig);
      if (response.success) {
        setProcessedData(response.data.processed_data);
        setPipelineLog(response.data.log);
        message.success('预处理完成');
      }
    } catch (error) {
      message.error('预处理失败');
    } finally {
      setLoading(false);
    }
  };

  // 渲染质量分数
  const renderQualityScore = (score) => {
    let status = 'success';
    let color = '#52c41a';

    if (score < 60) {
      status = 'exception';
      color = '#ff4d4f';
    } else if (score < 80) {
      status = 'normal';
      color = '#faad14';
    }

    return <Progress type="circle" percent={score} status={status} strokeColor={color} />;
  };

  return (
    <div>
      {/* 数据选择 */}
      <Card title="1. 选择数据" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item label="组别">
              <Select value={selectedGroup} onChange={setSelectedGroup} placeholder="选择组别">
                {groups.map(g => (
                  <Option key={g.group} value={g.group}>{g.group}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label="受试者">
              <Select
                value={selectedSubject}
                onChange={setSelectedSubject}
                placeholder="选择受试者"
                disabled={!selectedGroup}
              >
                {subjects.map(s => (
                  <Option key={s.subject} value={s.subject}>{s.subject}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label="任务">
              <Select
                value={selectedTask}
                onChange={setSelectedTask}
                placeholder="选择任务"
                disabled={!selectedSubject}
              >
                {tasks.map(t => (
                  <Option key={t.task} value={t.task}>{t.task}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label=" " colon={false}>
              <Button
                type="primary"
                onClick={handleLoadData}
                loading={loading}
                disabled={!selectedTask}
              >
                加载数据
              </Button>
            </Form.Item>
          </Col>
        </Row>

        {gazeData && (
          <Alert
            message={`已加载数据: ${gazeData.length} 个数据点`}
            type="success"
            showIcon
          />
        )}
      </Card>

      {/* 质量检测结果 */}
      {qualityReport && (
        <Card title="2. 质量检测结果" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6} style={{ textAlign: 'center' }}>
              {renderQualityScore(qualityReport.quality_score)}
              <div style={{ marginTop: 8 }}>质量分数</div>
            </Col>
            <Col span={18}>
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="总数据点">
                  {qualityReport.total_points}
                </Descriptions.Item>
                <Descriptions.Item label="缺失值">
                  {qualityReport.missing_values.total_missing}
                </Descriptions.Item>
                <Descriptions.Item label="异常值">
                  {qualityReport.outliers.total_outliers}
                </Descriptions.Item>
                <Descriptions.Item label="范围违规">
                  {qualityReport.range_violations.total}
                </Descriptions.Item>
                <Descriptions.Item label="采样率">
                  {qualityReport.sampling_issues.actual_rate || 'N/A'} Hz
                </Descriptions.Item>
                <Descriptions.Item label="采样稳定性">
                  {qualityReport.sampling_issues.is_stable ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                  )}
                </Descriptions.Item>
              </Descriptions>
            </Col>
          </Row>
        </Card>
      )}

      {/* 预处理配置 */}
      <Card title="3. 预处理配置" style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="enable_quality_check" label="启用质量检测" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="enable_cleaning" label="启用数据清洗" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="enable_smoothing" label="启用数据平滑" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider>质量检测配置</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="outlier_threshold" label="异常值阈值 (σ)">
                <InputNumber min={1} max={5} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>清洗配置</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="missing_method" label="缺失值处理">
                <Select>
                  <Option value="interpolate">插值</Option>
                  <Option value="ffill">前向填充</Option>
                  <Option value="drop">删除</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="outlier_action" label="异常值处理">
                <Select>
                  <Option value="interpolate">插值</Option>
                  <Option value="clip">裁剪</Option>
                  <Option value="drop">删除</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>平滑配置</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="smooth_method" label="平滑方法">
                <Select>
                  <Option value="moving_average">移动平均</Option>
                  <Option value="gaussian">高斯滤波</Option>
                  <Option value="median">中值滤波</Option>
                  <Option value="savgol">Savitzky-Golay</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="window_size" label="窗口大小">
                <InputNumber min={3} max={21} step={2} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sigma" label="Sigma (高斯)">
                <InputNumber min={0.1} max={5} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Button
            type="primary"
            size="large"
            icon={<ThunderboltOutlined />}
            onClick={handleRunPipeline}
            loading={loading}
            disabled={!gazeData}
            block
          >
            运行预处理流水线
          </Button>
        </Form>
      </Card>

      {/* 处理结果 */}
      {pipelineLog && (
        <Card title="4. 处理结果">
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="原始数据点"
                value={pipelineLog.original_points}
                prefix={<ExperimentOutlined />}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="处理后数据点"
                value={pipelineLog.final_points}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="处理步骤"
                value={pipelineLog.steps.length}
                suffix="步"
              />
            </Col>
          </Row>

          <Descriptions title="处理步骤详情" bordered column={1} size="small">
            {pipelineLog.steps.map((step, index) => (
              <Descriptions.Item key={index} label={`步骤 ${index + 1}: ${step.step}`}>
                {step.step === 'quality_check' && (
                  <div>质量分数: {step.report.quality_score.toFixed(2)}/100</div>
                )}
                {step.step === 'cleaning' && (
                  <div>删除点数: {step.log.points_removed}</div>
                )}
                {step.step === 'smoothing' && (
                  <div>平滑列: {step.log.columns_smoothed.join(', ')}</div>
                )}
              </Descriptions.Item>
            ))}
          </Descriptions>

          {processedData && (
            <Alert
              style={{ marginTop: 16 }}
              message="预处理完成"
              description={`成功处理 ${processedData.length} 个数据点，可以进行后续分析`}
              type="success"
              showIcon
            />
          )}
        </Card>
      )}
    </div>
  );
};

export default DataPreprocessing;
