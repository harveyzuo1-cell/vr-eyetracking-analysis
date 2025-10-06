import React, { useState } from 'react';
import { Card, Row, Col, Typography, Divider, Space } from 'antd';
import { DatabaseOutlined, SyncOutlined } from '@ant-design/icons';
import DataSourceOverview from '../../components/Module00/DataSourceOverview';
import DataScanner from '../../components/Module00/DataScanner';
import DataImporter from '../../components/Module00/DataImporter';
import SubjectList from '../../components/Module00/SubjectList';

const { Title, Paragraph } = Typography;

/**
 * Module 00: 数据管理中心
 * Data Management Center
 *
 * 功能：
 * - 扫描双数据源（Legacy v1 + Eye Tracking v2）
 * - 展示数据统计
 * - 查看受试者列表
 * - 批量导入数据
 */
const Module00 = () => {
  const [scanData, setScanData] = useState(null);
  const [loading, setLoading] = useState(false);

  // 处理扫描完成
  const handleScanComplete = (data) => {
    setScanData(data);
  };

  // 处理扫描状态变化
  const handleScanStateChange = (isLoading) => {
    setLoading(isLoading);
  };

  // 处理导入完成
  const handleImportComplete = (result) => {
    // 导入完成后可以重新扫描或刷新数据
    console.log('Import completed:', result);
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space>
            <DatabaseOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
            <div>
              <Title level={2} style={{ margin: 0 }}>
                Module 00: 数据管理中心
              </Title>
              <Paragraph type="secondary" style={{ margin: 0 }}>
                Data Management Center - 双数据源统一管理
              </Paragraph>
            </div>
          </Space>
        </Card>

        {/* 数据源概览 */}
        <DataSourceOverview scanData={scanData} loading={loading} />

        <Divider />

        {/* 扫描控制区 */}
        <DataScanner
          onScanComplete={handleScanComplete}
          onScanStateChange={handleScanStateChange}
        />

        <Divider />

        {/* 导入控制区 */}
        <DataImporter
          scanData={scanData}
          onImportComplete={handleImportComplete}
        />

        <Divider />

        {/* 受试者列表 */}
        {scanData && (
          <SubjectList scanData={scanData} />
        )}
      </Space>
    </div>
  );
};

export default Module00;
