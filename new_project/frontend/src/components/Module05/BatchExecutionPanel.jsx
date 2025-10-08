/**
 * 批量执行面板
 * 提交异步批量RQA任务，监控进度
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card, Button, Progress, Statistic, message, Row, Col, Space, Alert, Checkbox, Tag, Descriptions
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import axios from 'axios';

const BatchExecutionPanel = () => {
  const [taskStatus, setTaskStatus] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedGroups, setSelectedGroups] = useState(['control', 'mci', 'ad']);
  const [paramCombinations, setParamCombinations] = useState([]);

  // 加载缓存的参数组合
  useEffect(() => {
    loadParamCombinations();
  }, []);

  const loadParamCombinations = async () => {
    try {
      const response = await axios.get('/api/m05/params/history');
      if (response.data.success && response.data.combinations) {
        setParamCombinations(response.data.combinations);
      }
    } catch (error) {
      console.error('加载参数组合失败:', error);
    }
  };

  // 轮询任务状态
  useEffect(() => {
    let interval;
    if (isRunning && taskStatus?.task_id) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/m05/tasks/status/${taskStatus.task_id}`);

          if (response.data.success) {
            setTaskStatus(response.data.task);

            // 任务完成或失败时停止轮询
            if (response.data.task.status === 'completed' || response.data.task.status === 'failed') {
              setIsRunning(false);
              clearInterval(interval);

              if (response.data.task.status === 'completed') {
                message.success('批量分析任务完成！');
              } else {
                message.error('批量分析任务失败: ' + response.data.task.error_message);
              }
            }
          }
        } catch (error) {
          console.error('获取任务状态失败:', error);
        }
      }, 2000); // 每2秒更新一次
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isRunning, taskStatus?.task_id]);

  const handleStartAnalysis = async () => {
    if (paramCombinations.length === 0) {
      message.warning('请先在「参数配置」页面生成参数组合');
      return;
    }

    if (selectedGroups.length === 0) {
      message.warning('请至少选择一个分析组别');
      return;
    }

    try {
      setLoading(true);

      // 提交异步任务，使用缓存的参数组合
      const response = await axios.post('/api/m05/tasks/submit', {
        param_combinations: paramCombinations,
        groups: selectedGroups
      });

      if (response.data.success) {
        setTaskStatus(response.data);
        setIsRunning(true);
        message.success(`批量分析任务已提交：${paramCombinations.length} 个参数组合 × ${selectedGroups.length} 个组别`);
      } else {
        message.error('提交任务失败');
      }
    } catch (error) {
      console.error('提交任务失败:', error);
      message.error('提交任务失败: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCancelTask = async () => {
    if (!taskStatus?.task_id) return;

    try {
      const response = await axios.post(`/api/m05/tasks/cancel/${taskStatus.task_id}`);

      if (response.data.success) {
        setIsRunning(false);
        message.info('任务已取消');
      } else {
        message.error('取消任务失败');
      }
    } catch (error) {
      console.error('取消任务失败:', error);
      message.error('取消任务失败: ' + error.message);
    }
  };

  const getStatusTag = (status) => {
    const statusMap = {
      'pending': { color: 'default', text: '等待中' },
      'running': { color: 'processing', text: '运行中' },
      'completed': { color: 'success', text: '已完成' },
      'failed': { color: 'error', text: '失败' },
      'cancelled': { color: 'warning', text: '已取消' }
    };
    const config = statusMap[status] || statusMap['pending'];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getStepName = (step) => {
    const steps = {
      1: 'Step 1: RQA计算',
      2: 'Step 2: 数据合并',
      3: 'Step 3: 特征增强',
      4: 'Step 4: 统计分析',
      5: 'Step 5: 可视化'
    };
    return steps[step] || `Step ${step}`;
  };

  return (
    <div>
      <Card title="分析配置" style={{ marginBottom: 16 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <h4>选择分析组别</h4>
            <Checkbox.Group
              options={[
                { label: '控制组 (Control)', value: 'control' },
                { label: '轻度认知障碍 (MCI)', value: 'mci' },
                { label: '阿尔茨海默症 (AD)', value: 'ad' }
              ]}
              value={selectedGroups}
              onChange={setSelectedGroups}
            />
          </div>

          {paramCombinations.length > 0 ? (
            <Alert
              message={`已加载 ${paramCombinations.length} 个参数组合`}
              description={`选中 ${selectedGroups.length} 个组别，预计处理 ${paramCombinations.length * selectedGroups.length} 个任务`}
              type="success"
              showIcon
            />
          ) : (
            <Alert
              message="尚未生成参数组合"
              description="请先在「参数配置」页面生成参数组合后再执行批量分析"
              type="warning"
              showIcon
            />
          )}
        </Space>
      </Card>

      {!isRunning && !taskStatus ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={handleStartAnalysis}
              loading={loading}
              disabled={selectedGroups.length === 0}
            >
              开始批量分析
            </Button>
            {selectedGroups.length === 0 && (
              <p style={{ marginTop: 16, color: '#999' }}>
                请至少选择一个分析组别
              </p>
            )}
          </div>
        </Card>
      ) : (
        <Card title="任务进度">
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="任务ID">{taskStatus?.task_id}</Descriptions.Item>
              <Descriptions.Item label="状态">{getStatusTag(taskStatus?.status)}</Descriptions.Item>
              <Descriptions.Item label="当前步骤">{getStepName(taskStatus?.current_step)}</Descriptions.Item>
              <Descriptions.Item label="当前参数">
                {taskStatus?.current_param && (
                  <span>
                    m={taskStatus.current_param.m}, τ={taskStatus.current_param.tau},
                    ε={taskStatus.current_param.eps}, lmin={taskStatus.current_param.lmin}
                  </span>
                )}
              </Descriptions.Item>
            </Descriptions>

            <div>
              <h4>总体进度</h4>
              <Progress
                percent={Number((taskStatus?.progress || 0).toFixed(2))}
                status={
                  taskStatus?.status === 'failed'
                    ? 'exception'
                    : taskStatus?.status === 'completed'
                    ? 'success'
                    : 'active'
                }
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </div>

            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="已处理文件"
                  value={taskStatus?.processed_files || 0}
                  suffix={`/ ${taskStatus?.total_files || 0}`}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="失败文件"
                  value={taskStatus?.failed_files || 0}
                  valueStyle={{ color: taskStatus?.failed_files > 0 ? '#cf1322' : '#3f8600' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="预计剩余时间"
                  value={taskStatus?.eta_seconds || 0}
                  suffix="秒"
                  precision={0}
                />
              </Col>
            </Row>

            {taskStatus?.error_message && (
              <Alert
                message="错误信息"
                description={taskStatus.error_message}
                type="error"
                showIcon
              />
            )}

            <div style={{ textAlign: 'center' }}>
              <Space>
                {isRunning && (
                  <Button
                    danger
                    icon={<PauseCircleOutlined />}
                    onClick={handleCancelTask}
                  >
                    取消任务
                  </Button>
                )}
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    setTaskStatus(null);
                    setIsRunning(false);
                  }}
                  disabled={isRunning}
                >
                  重置
                </Button>
              </Space>
            </div>
          </Space>
        </Card>
      )}
    </div>
  );
};

export default BatchExecutionPanel;
