/**
 * 可视化分析面板
 * 展示RQA分析结果的统计图表
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  Card, Row, Col, Image, Empty, Button, message, Space, Select
} from 'antd';
import { PictureOutlined, DownloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

const { Option } = Select;

const VisualizationPanel = () => {
  const [selectedSignature, setSelectedSignature] = useState('m2_tau1_eps0.05_lmin2');

  // 模拟可用的参数签名列表
  const signatures = useMemo(() => [
    'm2_tau1_eps0.05_lmin2',
    'm2_tau1_eps0.051_lmin2',
    'm3_tau2_eps0.05_lmin2'
  ], []);

  // 生成图片URL
  const getImageUrl = useCallback((filename) => {
    return `/api/m05/visualizations/${selectedSignature}/${filename}`;
  }, [selectedSignature]);

  const plots = useMemo(() => [
    {
      title: 'RQA指标箱线图',
      filename: 'rqa_metrics_boxplot.png',
      description: '各组别的RQA核心指标（RR, DET, ENT）分布对比'
    },
    {
      title: '相关性热力图',
      filename: 'correlation_heatmap.png',
      description: 'RQA特征之间的Pearson相关系数矩阵'
    },
    {
      title: '显著性特征',
      filename: 'significant_features.png',
      description: 'ANOVA分析中具有统计显著性的特征（p < 0.05）'
    },
    {
      title: '复杂度小提琴图',
      filename: 'complexity_violin.png',
      description: 'RQA复杂度指标（1D和2D）的分布密度'
    }
  ], []);

  const handleDownload = useCallback(async (filename) => {
    try {
      const url = getImageUrl(filename);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      message.success('下载成功');
    } catch (error) {
      console.error('下载失败:', error);
      message.error('下载失败: ' + (error.message || '未知错误'));
    }
  }, [getImageUrl]);

  return (
    <div>
      <Card
        title={
          <Space>
            <PictureOutlined />
            统计可视化
          </Space>
        }
        extra={
          <Space>
            <span>选择参数组合:</span>
            <Select
              style={{ width: 220 }}
              value={selectedSignature}
              onChange={setSelectedSignature}
            >
              {signatures.map(sig => (
                <Option key={sig} value={sig}>{sig}</Option>
              ))}
            </Select>
          </Space>
        }
      >
        <Row gutter={[24, 24]}>
          {plots.map((plot, index) => (
            <Col span={12} key={index}>
              <Card
                title={plot.title}
                extra={
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(plot.filename)}
                  >
                    下载
                  </Button>
                }
                styles={{
                  body: { padding: 0 }
                }}
              >
                <div style={{ padding: '16px', background: '#fafafa' }}>
                  <p style={{ margin: 0, fontSize: 13, color: '#666' }}>
                    {plot.description}
                  </p>
                </div>
                <Image
                  src={getImageUrl(plot.filename)}
                  alt={plot.title}
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                  placeholder={
                    <Empty
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                      description="暂无图片"
                    />
                  }
                  style={{
                    width: '100%',
                    maxHeight: 400,
                    objectFit: 'contain'
                  }}
                />
              </Card>
            </Col>
          ))}
        </Row>

        <Card
          title="数据文件"
          style={{ marginTop: 24 }}
          styles={{
            body: { background: '#fafafa' }
          }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <strong>Step 3 - 特征增强:</strong>
              <ul>
                <li>enriched_features.csv - 包含Module04事件特征、MMSE数据和衍生RQA特征</li>
              </ul>
            </div>
            <div>
              <strong>Step 4 - 统计分析:</strong>
              <ul>
                <li>descriptive_stats.csv - 各组别的描述性统计（均值、标准差等）</li>
                <li>group_comparison.csv - ANOVA组间比较结果（F统计量、p值）</li>
                <li>correlation_matrix.csv - 特征相关性矩阵</li>
              </ul>
            </div>
            <div>
              <strong>Step 5 - 可视化:</strong>
              <ul>
                <li>rqa_metrics_boxplot.png - RQA指标箱线图</li>
                <li>correlation_heatmap.png - 相关性热力图</li>
                <li>significant_features.png - 显著性特征柱状图</li>
                <li>complexity_violin.png - 复杂度小提琴图</li>
              </ul>
            </div>
          </Space>
        </Card>
      </Card>
    </div>
  );
};

export default VisualizationPanel;
