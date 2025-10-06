/**
 * V1DataManagement: V1受试者数据查看
 *
 * 功能：
 * - 显示已导入的V1受试者列表（从subject_info读取）
 * - 查看V1受试者详细信息（包括MMSE评分）
 *
 * 注意：V1数据通过"受试者管理"页面的"从临床数据导入"功能导入
 */
import React, { useState, useEffect } from 'react';
import { Table, Button, message, Tag, Space } from 'antd';
import { ScanOutlined } from '@ant-design/icons';
import axios from 'axios';

const V1DataManagement = () => {
  const [v1Subjects, setV1Subjects] = useState([]);
  const [loading, setLoading] = useState(false);

  // 扫描V1受试者
  const handleScanV1 = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/m02/v1/subjects');
      if (response.data.success) {
        setV1Subjects(response.data.subjects);
        message.success(`扫描成功，找到 ${response.data.subjects.length} 个V1受试者`);
      } else {
        message.error(response.data.message || '扫描失败');
      }
    } catch (error) {
      message.error('扫描V1受试者失败：' + error.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    handleScanV1();
  }, []);

  // V1数据都是通过"受试者管理"页面的"从临床数据导入"功能导入的
  // 这里只提供查看功能，不需要批量导入

  const columns = [
    {
      title: '受试者ID',
      dataIndex: 'subject_id',
      key: 'subject_id',
      width: 200,
    },
    {
      title: '分组',
      dataIndex: 'group',
      key: 'group',
      width: 100,
      render: (group) => {
        const colorMap = {
          control: 'green',
          mci: 'orange',
          ad: 'red',
        };
        return <Tag color={colorMap[group] || 'blue'}>{group.toUpperCase()}</Tag>;
      },
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '年龄',
      dataIndex: 'age',
      key: 'age',
      width: 80,
    },
    {
      title: '性别',
      dataIndex: 'gender',
      key: 'gender',
      width: 80,
      render: (gender) => {
        const map = { male: '男', female: '女' };
        return map[gender] || gender;
      },
    },
    {
      title: 'MMSE评分',
      dataIndex: 'mmse_score',
      key: 'mmse_score',
      width: 100,
      render: (score, record) => (
        record.has_mmse ? (
          <Tag color={score >= 27 ? 'green' : score >= 21 ? 'orange' : 'red'}>
            {score} 分
          </Tag>
        ) : (
          <Tag color="default">未评估</Tag>
        )
      ),
    },
    {
      title: '导入时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: () => <Tag color="blue">已导入</Tag>,
    },
  ];

  const stats = {
    total: v1Subjects.length,
    withMMSE: v1Subjects.filter(s => s.has_mmse).length,
    avgScore: v1Subjects.filter(s => s.has_mmse).length > 0
      ? (v1Subjects.filter(s => s.has_mmse).reduce((sum, s) => sum + (s.mmse_score || 0), 0) / v1Subjects.filter(s => s.has_mmse).length).toFixed(1)
      : 0,
  };

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 统计信息 */}
        <div style={{ background: '#f0f2f5', padding: '16px', borderRadius: '8px' }}>
          <Space size="large">
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                {stats.total}
              </div>
              <div>V1受试者总数</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                {stats.withMMSE}
              </div>
              <div>已有MMSE评分</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
                {stats.avgScore}
              </div>
              <div>平均MMSE评分</div>
            </div>
          </Space>
        </div>

        {/* 操作按钮 */}
        <Space wrap>
          <Button
            icon={<ScanOutlined />}
            onClick={handleScanV1}
            loading={loading}
          >
            刷新V1数据
          </Button>
          <div style={{ color: '#666', fontSize: '14px' }}>
            V1数据通过"受试者管理"页面的"从临床数据导入"功能导入
          </div>
        </Space>

        {/* V1受试者列表 */}
        <Table
          columns={columns}
          dataSource={v1Subjects}
          rowKey={(record) => `${record.subject_id}_${record.timestamp}`}
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Space>
    </div>
  );
};

export default V1DataManagement;
