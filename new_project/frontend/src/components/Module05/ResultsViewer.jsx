/**
 * 结果查看器
 * 查看和浏览RQA分析结果
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card, Table, Button, message, Space, Select, Form, Alert
} from 'antd';
import { FileSearchOutlined, ReloadOutlined, FolderOpenOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const ResultsViewer = () => {
  const [results, setResults] = useState([]);
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);

  // 筛选条件
  const [filters, setFilters] = useState({
    m: null,
    tau: null,
    eps: null,
    lmin: null
  });

  const loadBatches = useCallback(async () => {
    try {
      const response = await axios.get('/api/m05/batches/list');
      if (response.data.success) {
        setBatches(response.data.batches);
      }
    } catch (error) {
      console.error('加载批次列表失败:', error);
    }
  }, []);

  const loadResults = useCallback(async (taskId = null) => {
    try {
      setLoading(true);
      const url = taskId
        ? `/api/m05/results/completed?task_id=${encodeURIComponent(taskId)}`
        : '/api/m05/results/completed';

      const response = await axios.get(url);

      if (response.data.success) {
        setResults(response.data.completed_results);
      } else {
        message.error('加载结果列表失败');
      }
    } catch (error) {
      console.error('加载结果列表失败:', error);
      message.error('加载结果列表失败: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBatches();
    loadResults();
  }, [loadBatches, loadResults]);

  const handleBatchChange = useCallback((taskId) => {
    setSelectedBatch(taskId);
    loadResults(taskId);
  }, [loadResults]);

  const handleRefresh = useCallback(() => {
    loadBatches();
    loadResults(selectedBatch);
  }, [loadBatches, loadResults, selectedBatch]);

  // 获取参数筛选范围
  const paramRanges = useMemo(() => {
    if (results.length === 0) return { m: [], tau: [], eps: [], lmin: [] };

    return {
      m: [...new Set(results.map(r => r.m))].sort((a, b) => a - b),
      tau: [...new Set(results.map(r => r.tau))].sort((a, b) => a - b),
      eps: [...new Set(results.map(r => r.eps))].sort((a, b) => a - b),
      lmin: [...new Set(results.map(r => r.lmin))].sort((a, b) => a - b)
    };
  }, [results]);

  // 筛选后的结果
  const filteredResults = useMemo(() => {
    return results.filter(result => {
      if (filters.m !== null && result.m !== filters.m) return false;
      if (filters.tau !== null && result.tau !== filters.tau) return false;
      if (filters.eps !== null && Math.abs(result.eps - filters.eps) > 0.0001) return false;
      if (filters.lmin !== null && result.lmin !== filters.lmin) return false;
      return true;
    });
  }, [results, filters]);

  const handleOpenResultFolder = useCallback((signature) => {
    message.info(`结果目录: data/05_rqa_analysis/results/${signature}`);
  }, []);

  const columns = useMemo(() => [
    {
      title: '参数签名',
      dataIndex: 'signature',
      key: 'signature',
      width: 250,
      fixed: 'left'
    },
    {
      title: 'm',
      dataIndex: 'm',
      key: 'm',
      width: 80,
      sorter: (a, b) => a.m - b.m
    },
    {
      title: 'τ',
      dataIndex: 'tau',
      key: 'tau',
      width: 80,
      sorter: (a, b) => a.tau - b.tau
    },
    {
      title: 'ε',
      dataIndex: 'eps',
      key: 'eps',
      width: 100,
      render: (val) => val.toFixed(3),
      sorter: (a, b) => a.eps - b.eps
    },
    {
      title: 'lmin',
      dataIndex: 'lmin',
      key: 'lmin',
      width: 80,
      sorter: (a, b) => a.lmin - b.lmin
    },
    {
      title: '创建时间',
      dataIndex: 'creation_time',
      key: 'creation_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN') : '-'
    },
    {
      title: '最后更新',
      dataIndex: 'last_updated',
      key: 'last_updated',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN') : '-',
      sorter: (a, b) => new Date(a.last_updated) - new Date(b.last_updated)
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<FolderOpenOutlined />}
            onClick={() => handleOpenResultFolder(record.signature)}
          >
            查看
          </Button>
        </Space>
      )
    }
  ], [handleOpenResultFolder]);

  return (
    <div>
      <Card
        title={
          <Space>
            <FileSearchOutlined />
            已完成的RQA分析结果
            <Select
              style={{ width: 400, marginLeft: 16 }}
              placeholder="选择批次 (默认显示全部)"
              allowClear
              value={selectedBatch}
              onChange={handleBatchChange}
            >
              {batches.map(batch => (
                <Option key={batch.task_id} value={batch.task_id}>
                  {batch.display_name}
                </Option>
              ))}
            </Select>
          </Space>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        {selectedBatch && (
          <Alert
            message={`当前批次: ${batches.find(b => b.task_id === selectedBatch)?.display_name || selectedBatch}`}
            type="info"
            closable
            onClose={() => handleBatchChange(null)}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form layout="inline" style={{ marginBottom: 16 }}>
          <Form.Item label="嵌入维度 m">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={filters.m}
              onChange={(value) => setFilters({ ...filters, m: value })}
            >
              {paramRanges.m.map(val => (
                <Option key={val} value={val}>{val}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="时间延迟 τ">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={filters.tau}
              onChange={(value) => setFilters({ ...filters, tau: value })}
            >
              {paramRanges.tau.map(val => (
                <Option key={val} value={val}>{val}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="递归阈值 ε">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={filters.eps}
              onChange={(value) => setFilters({ ...filters, eps: value })}
            >
              {paramRanges.eps.map(val => (
                <Option key={val} value={val}>{val.toFixed(3)}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="最小线长 lmin">
            <Select
              style={{ width: 120 }}
              placeholder="全部"
              allowClear
              value={filters.lmin}
              onChange={(value) => setFilters({ ...filters, lmin: value })}
            >
              {paramRanges.lmin.map(val => (
                <Option key={val} value={val}>{val}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <span style={{ color: '#666', fontSize: 13 }}>
                筛选结果: {filteredResults.length} / {results.length}
              </span>
              {(filters.m || filters.tau || filters.eps || filters.lmin) && (
                <Button
                  size="small"
                  onClick={() => setFilters({ m: null, tau: null, eps: null, lmin: null })}
                >
                  清空筛选
                </Button>
              )}
            </Space>
          </Form.Item>
        </Form>

        <Table
          columns={columns}
          dataSource={filteredResults}
          rowKey="signature"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条结果`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default ResultsViewer;
