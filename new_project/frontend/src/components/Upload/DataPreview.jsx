import React from 'react';
import { Card, Table, Row, Col, Statistic, Tag, Alert, Divider } from 'antd';
import {
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';

const DataPreview = ({ uploadResult }) => {
  if (!uploadResult || !uploadResult.success) {
    return null;
  }

  const { filename, stats, validation, preview } = uploadResult;

  // 数据质量标签
  const getQualityTag = (score) => {
    if (score >= 90) {
      return <Tag color="success" icon={<CheckCircleOutlined />}>优秀</Tag>;
    } else if (score >= 75) {
      return <Tag color="processing" icon={<CheckCircleOutlined />}>良好</Tag>;
    } else if (score >= 60) {
      return <Tag color="warning" icon={<WarningOutlined />}>一般</Tag>;
    } else {
      return <Tag color="error" icon={<CloseCircleOutlined />}>较差</Tag>;
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'X坐标',
      dataIndex: 'x',
      key: 'x',
      width: 120,
      render: (val) => typeof val === 'number' ? val.toFixed(4) : val
    },
    {
      title: 'Y坐标',
      dataIndex: 'y',
      key: 'y',
      width: 120,
      render: (val) => typeof val === 'number' ? val.toFixed(4) : val
    },
    {
      title: '时间戳(ms)',
      dataIndex: 'time',
      key: 'time',
      width: 120,
      render: (val) => typeof val === 'number' ? val.toFixed(2) : val
    }
  ];

  // 添加额外的列（如果存在）
  if (preview && preview.length > 0) {
    const firstRow = preview[0];
    Object.keys(firstRow).forEach(key => {
      if (!['x', 'y', 'time'].includes(key)) {
        columns.push({
          title: key,
          dataIndex: key,
          key: key,
          width: 100,
          render: (val) => typeof val === 'number' ? val.toFixed(4) : String(val)
        });
      }
    });
  }

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="数据点数"
              value={stats.total_points}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="时长(秒)"
              value={stats.duration ? (stats.duration / 1000).toFixed(2) : 0}
              precision={2}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="采样率(Hz)"
              value={stats.sample_rate || '未知'}
              precision={1}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="数据质量"
              value={validation.quality_score}
              suffix="/ 100"
              valueStyle={{
                color: validation.quality_score >= 75 ? '#3f8600' : '#cf1322'
              }}
            />
            <div style={{ marginTop: 8 }}>
              {getQualityTag(validation.quality_score)}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 验证结果 */}
      {validation && (
        <Card title="数据验证结果" style={{ marginBottom: 16 }}>
          {validation.valid ? (
            <Alert
              message="数据验证通过"
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
            />
          ) : (
            <Alert
              message="数据验证失败"
              description={
                <div>
                  {validation.errors.map((error, index) => (
                    <div key={`error_${index}_${error.substring(0, 20)}`} style={{ color: '#cf1322' }}>
                      • {error}
                    </div>
                  ))}
                </div>
              }
              type="error"
              showIcon
              icon={<CloseCircleOutlined />}
            />
          )}

          {validation.warnings && validation.warnings.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <Alert
                message="警告信息"
                description={
                  <div>
                    {validation.warnings.map((warning, index) => (
                      <div key={`warning_${index}_${warning.substring(0, 20)}`} style={{ color: '#d48806' }}>
                        • {warning}
                      </div>
                    ))}
                  </div>
                }
                type="warning"
                showIcon
                icon={<WarningOutlined />}
              />
            </div>
          )}
        </Card>
      )}

      {/* 数据坐标范围 */}
      {stats.x_range && stats.y_range && (
        <Card title="坐标范围" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <p><strong>X坐标范围:</strong></p>
              <p>最小值: {stats.x_range[0].toFixed(4)}</p>
              <p>最大值: {stats.x_range[1].toFixed(4)}</p>
              {stats.x_mean && <p>平均值: {stats.x_mean.toFixed(4)}</p>}
            </Col>
            <Col span={12}>
              <p><strong>Y坐标范围:</strong></p>
              <p>最小值: {stats.y_range[0].toFixed(4)}</p>
              <p>最大值: {stats.y_range[1].toFixed(4)}</p>
              {stats.y_mean && <p>平均值: {stats.y_mean.toFixed(4)}</p>}
            </Col>
          </Row>
        </Card>
      )}

      <Divider />

      {/* 数据预览表格 */}
      <Card title={`数据预览 (前100行)`}>
        <Table
          dataSource={preview || []}
          columns={columns}
          rowKey={(record, index) => index}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条数据`
          }}
          size="small"
          scroll={{ x: 'max-content' }}
        />
      </Card>
    </div>
  );
};

export default DataPreview;
