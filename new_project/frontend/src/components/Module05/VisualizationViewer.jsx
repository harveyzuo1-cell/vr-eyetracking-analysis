/**
 * Module05: 可视化查看器
 * 用于浏览、筛选和对比已生成的可视化图表
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Select, Space, Spin, message, Image, Empty,
  Tabs, Descriptions, Tag
} from 'antd';
import {
  PictureOutlined, FilterOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { TabPane } = Tabs;

const VisualizationViewer = () => {
  const [loading, setLoading] = useState(false);
  const [visualizations, setVisualizations] = useState([]);
  const [selectedSignature, setSelectedSignature] = useState(null);
  const [selectedVizType, setSelectedVizType] = useState('all');

  useEffect(() => {
    fetchVisualizations();
  }, []);

  const fetchVisualizations = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/m05/visualization/list');
      if (response.data.success) {
        setVisualizations(response.data.visualizations);
        if (response.data.visualizations.length > 0) {
          setSelectedSignature(response.data.visualizations[0].signature);
        }
      }
    } catch (error) {
      console.error('获取可视化列表失败:', error);
      message.error('获取可视化列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const currentViz = visualizations.find(v => v.signature === selectedSignature);

  const getVizTypeLabel = (type) => {
    const labels = {
      'correlation_heatmap': '相关性热力图',
      'significance_barplot': '显著性柱状图',
      'complexity_violin': '复杂度小提琴图',
      'grouped_boxplots': '分组箱线图'
    };
    return labels[type] || type;
  };

  const renderVisualization = () => {
    if (!currentViz) {
      return <Empty description="暂无可视化数据" />;
    }

    const vizTypes = currentViz.viz_types;
    const allImages = [];

    // 收集所有图片
    Object.entries(vizTypes).forEach(([type, images]) => {
      if (selectedVizType === 'all' || selectedVizType === type) {
        images.forEach(img => {
          allImages.push({
            ...img,
            type,
            typeLabel: getVizTypeLabel(type)
          });
        });
      }
    });

    if (allImages.length === 0) {
      return <Empty description="该参数组合暂无可视化" />;
    }

    return (
      <Row gutter={[16, 16]}>
        {allImages.map((img, idx) => (
          <Col span={12} key={idx}>
            <Card
              title={img.typeLabel}
              size="small"
              extra={img.method && <Tag color="blue">{img.method.toUpperCase()}</Tag>}
            >
              <Image
                src={`/api/m05/visualization/image/${img.path}`}
                alt={img.typeLabel}
                style={{ width: '100%' }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
              />
            </Card>
          </Col>
        ))}
      </Row>
    );
  };

  return (
    <Spin spinning={loading} tip="加载中...">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card title={<span><PictureOutlined /> 可视化浏览器</span>} size="small">
          <Descriptions column={3} bordered size="small">
            <Descriptions.Item label="已生成参数组合">
              {visualizations.length}
            </Descriptions.Item>
            <Descriptions.Item label="当前参数">
              {selectedSignature || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="图表数量">
              {currentViz ? currentViz.total_images : 0}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title={<span><FilterOutlined /> 筛选器</span>} size="small">
          <Space>
            <span>选择参数组合:</span>
            <Select
              style={{ width: 300 }}
              value={selectedSignature}
              onChange={setSelectedSignature}
              placeholder="选择参数"
            >
              {visualizations.map((viz, idx) => (
                <Option key={idx} value={viz.signature}>
                  {viz.signature} ({viz.total_images} 张图表)
                </Option>
              ))}
            </Select>

            <span>可视化类型:</span>
            <Select
              style={{ width: 200 }}
              value={selectedVizType}
              onChange={setSelectedVizType}
            >
              <Option value="all">全部</Option>
              <Option value="correlation_heatmap">相关性热力图</Option>
              <Option value="significance_barplot">显著性柱状图</Option>
              <Option value="complexity_violin">复杂度小提琴图</Option>
              <Option value="grouped_boxplots">分组箱线图</Option>
            </Select>
          </Space>
        </Card>

        <Card title="可视化展示">
          {renderVisualization()}
        </Card>
      </Space>
    </Spin>
  );
};

export default VisualizationViewer;
