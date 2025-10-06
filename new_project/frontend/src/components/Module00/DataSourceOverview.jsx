import React from 'react';
import { Card, Row, Col, Statistic, Spin, Empty, Tag } from 'antd';
import {
  DatabaseOutlined,
  TeamOutlined,
  FolderOpenOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';

/**
 * 数据源概览组件
 * 展示Legacy v1和Eye Tracking v2的统计信息
 */
const DataSourceOverview = ({ scanData, loading }) => {
  if (loading) {
    return (
      <Card title="数据源概览">
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '16px', color: '#666' }}>扫描中...</div>
        </div>
      </Card>
    );
  }

  if (!scanData) {
    return (
      <Card title="数据源概览">
        <Empty description="点击下方扫描按钮开始扫描数据源" />
      </Card>
    );
  }

  const { legacy_data, eye_tracking_data, summary } = scanData;

  return (
    <Card
      title={
        <span>
          <DatabaseOutlined /> 数据源概览
        </span>
      }
    >
      <Row gutter={[16, 16]}>
        {/* Legacy数据 (v1) */}
        <Col xs={24} md={12}>
          <Card
            type="inner"
            title={
              <span>
                <FolderOpenOutlined style={{ color: '#52c41a' }} /> Legacy数据 (v1)
              </span>
            }
            extra={<Tag color="green">旧版</Tag>}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="总受试者"
                  value={legacy_data.total_subjects}
                  suffix="名"
                  prefix={<TeamOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="数据源"
                  value={legacy_data.source_dir}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: '16px' }}>
              <Col span={8}>
                <Statistic
                  title="Control"
                  value={legacy_data.control}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="MCI"
                  value={legacy_data.mci}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="AD"
                  value={legacy_data.ad}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* Eye Tracking数据 (v2) */}
        <Col xs={24} md={12}>
          <Card
            type="inner"
            title={
              <span>
                <FolderOpenOutlined style={{ color: '#1890ff' }} /> Eye Tracking数据 (v2)
              </span>
            }
            extra={<Tag color="blue">新版</Tag>}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="总受试者"
                  value={eye_tracking_data.total_subjects}
                  suffix="名"
                  prefix={<TeamOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="数据源"
                  value={eye_tracking_data.source_dir}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: '16px' }}>
              <Col span={8}>
                <Statistic
                  title="Control"
                  value={eye_tracking_data.control}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="MCI"
                  value={eye_tracking_data.mci}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="AD"
                  value={eye_tracking_data.ad}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
            </Row>
            {eye_tracking_data.details?.incomplete_count > 0 && (
              <div style={{ marginTop: '16px', color: '#999', fontSize: '12px' }}>
                <CheckCircleOutlined /> 已过滤{eye_tracking_data.details.incomplete_count}条不完整记录
              </div>
            )}
          </Card>
        </Col>

        {/* 汇总统计 */}
        <Col span={24}>
          <Card type="inner" style={{ background: '#fafafa' }}>
            <Row gutter={16} justify="center">
              <Col>
                <Statistic
                  title="总计有效受试者"
                  value={summary.total_subjects}
                  suffix="名"
                  prefix={<TeamOutlined />}
                  valueStyle={{ color: '#52c41a', fontSize: '28px' }}
                />
              </Col>
              <Col>
                <Statistic
                  title="数据源数量"
                  value={summary.sources}
                  suffix="个"
                  valueStyle={{ fontSize: '28px' }}
                />
              </Col>
              <Col>
                <Statistic
                  title="Legacy v1"
                  value={summary.legacy_v1_count}
                  suffix="名"
                  valueStyle={{ fontSize: '20px', color: '#52c41a' }}
                />
              </Col>
              <Col>
                <Statistic
                  title="Eye Tracking v2"
                  value={summary.eye_tracking_v2_count}
                  suffix="名"
                  valueStyle={{ fontSize: '20px', color: '#1890ff' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default DataSourceOverview;
