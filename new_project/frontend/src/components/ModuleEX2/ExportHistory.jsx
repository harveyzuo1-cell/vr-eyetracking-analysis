/**
 * 导出历史组件
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, message } from 'antd';
import { DownloadOutlined, ReloadOutlined, FileZipOutlined, FileTextOutlined } from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const ExportHistory = () => {
  const [loading, setLoading] = useState(false);
  const [exports, setExports] = useState([]);

  const fetchExports = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/ex2/exports?limit=20');
      if (response.data.success) {
        setExports(response.data.exports);
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('获取导出列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExports();
  }, []);

  const handleDownload = (filename) => {
    window.open(`/api/ex2/download/${filename}`, '_blank');
  };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (text) => (
        <Space>
          {text.endsWith('.zip') ? <FileZipOutlined /> : <FileTextOutlined />}
          {text}
        </Space>
      )
    },
    {
      title: '大小',
      dataIndex: 'size_mb',
      key: 'size_mb',
      render: (size) => `${size} MB`,
      sorter: (a, b) => a.size_mb - b.size_mb
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      defaultSortOrder: 'descend'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="primary"
          size="small"
          icon={<DownloadOutlined />}
          onClick={() => handleDownload(record.filename)}
        >
          下载
        </Button>
      )
    }
  ];

  return (
    <Card
      title="导出历史"
      extra={
        <Button icon={<ReloadOutlined />} onClick={fetchExports}>
          刷新
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={exports}
        rowKey="filename"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

export default ExportHistory;
