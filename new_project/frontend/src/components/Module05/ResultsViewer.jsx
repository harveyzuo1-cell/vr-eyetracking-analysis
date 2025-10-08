/**
 * 结果查看器
 * 查看和浏览RQA分析结果
 */
import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, message, Space, Tag, Descriptions, Drawer
} from 'antd';
import { FileSearchOutlined, EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const ResultsViewer = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/m05/tasks/list');

      if (response.data.success) {
        setTasks(response.data.tasks);
      } else {
        message.error('加载任务列表失败');
      }
    } catch (error) {
      console.error('加载任务列表失败:', error);
      message.error('加载任务列表失败: ' + error.message);
    } finally {
      setLoading(false);
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

  const handleViewDetails = (task) => {
    setSelectedTask(task);
    setDrawerVisible(true);
  };

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status)
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress) => `${Number(progress || 0).toFixed(1)}%`
    },
    {
      title: '已处理/总文件数',
      key: 'files',
      width: 150,
      render: (_, record) => `${record.processed_files || 0} / ${record.total_files || 0}`
    },
    {
      title: '失败文件',
      dataIndex: 'failed_files',
      key: 'failed_files',
      width: 100,
      render: (failed) => (
        <span style={{ color: failed > 0 ? '#cf1322' : '#3f8600' }}>
          {failed || 0}
        </span>
      )
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN') : '-'
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN') : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetails(record)}
        >
          详情
        </Button>
      )
    }
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <FileSearchOutlined />
            任务历史
          </Space>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={loadTasks}
            loading={loading}
          >
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="task_id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个任务`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Drawer
        title="任务详情"
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedTask && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Descriptions title="基本信息" bordered column={1}>
              <Descriptions.Item label="任务ID">{selectedTask.task_id}</Descriptions.Item>
              <Descriptions.Item label="状态">{getStatusTag(selectedTask.status)}</Descriptions.Item>
              <Descriptions.Item label="进度">{Number(selectedTask.progress || 0).toFixed(2)}%</Descriptions.Item>
              <Descriptions.Item label="当前步骤">Step {selectedTask.current_step}</Descriptions.Item>
            </Descriptions>

            <Descriptions title="文件处理统计" bordered column={1}>
              <Descriptions.Item label="总文件数">{selectedTask.total_files || 0}</Descriptions.Item>
              <Descriptions.Item label="已处理文件">{selectedTask.processed_files || 0}</Descriptions.Item>
              <Descriptions.Item label="失败文件">
                <span style={{ color: selectedTask.failed_files > 0 ? '#cf1322' : '#3f8600' }}>
                  {selectedTask.failed_files || 0}
                </span>
              </Descriptions.Item>
            </Descriptions>

            <Descriptions title="时间信息" bordered column={1}>
              <Descriptions.Item label="开始时间">
                {selectedTask.start_time ? new Date(selectedTask.start_time).toLocaleString('zh-CN') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="结束时间">
                {selectedTask.end_time ? new Date(selectedTask.end_time).toLocaleString('zh-CN') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="预计剩余时间">
                {selectedTask.eta_seconds ? `${selectedTask.eta_seconds} 秒` : '-'}
              </Descriptions.Item>
            </Descriptions>

            {selectedTask.current_param && (
              <Descriptions title="当前参数" bordered column={1}>
                <Descriptions.Item label="嵌入维度 (m)">{selectedTask.current_param.m}</Descriptions.Item>
                <Descriptions.Item label="时间延迟 (τ)">{selectedTask.current_param.tau}</Descriptions.Item>
                <Descriptions.Item label="递归阈值 (ε)">{selectedTask.current_param.eps}</Descriptions.Item>
                <Descriptions.Item label="最小线长 (lmin)">{selectedTask.current_param.lmin}</Descriptions.Item>
              </Descriptions>
            )}

            {selectedTask.error_message && (
              <Card title="错误信息" size="small" style={{ borderColor: '#ff4d4f' }}>
                <pre style={{ color: '#cf1322', whiteSpace: 'pre-wrap' }}>
                  {selectedTask.error_message}
                </pre>
              </Card>
            )}
          </Space>
        )}
      </Drawer>
    </div>
  );
};

export default ResultsViewer;
