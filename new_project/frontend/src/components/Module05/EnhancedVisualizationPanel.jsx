/**
 * Module05: 增强可视化分析面板
 *
 * 功能：
 * 1. 描述性统计表格
 * 2. 相关性热力图
 * 3. 显著性特征柱状图
 * 4. 复杂度小提琴图
 * 5. 分组箱线图
 * 6. 一键生成所有可视化
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Table, Select, Space, Spin, message,
  Statistic, Tag, Tabs, Image, Alert, Radio
} from 'antd';
import {
  BarChartOutlined, HeatMapOutlined, LineChartOutlined,
  BoxPlotOutlined, ThunderboltOutlined, PictureOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const EnhancedVisualizationPanel = () => {
  // ===== 状态管理 =====
  const [loading, setLoading] = useState(false);
  const [availableParams, setAvailableParams] = useState([]);
  const [selectedParam, setSelectedParam] = useState(null);
  const [activeVizTab, setActiveVizTab] = useState('overview');

  // 可视化结果状态
  const [descriptiveStats, setDescriptiveStats] = useState(null);
  const [correlationHeatmap, setCorrelationHeatmap] = useState(null);
  const [significanceBarplot, setSignificanceBarplot] = useState(null);
  const [complexityViolin, setComplexityViolin] = useState(null);
  const [groupedBoxplots, setGroupedBoxplots] = useState(null);

  // 配置选项
  const [correlationMethod, setCorrelationMethod] = useState('pearson');
  const [topNFeatures, setTopNFeatures] = useState(20);

  // ===== 初始化 =====
  useEffect(() => {
    fetchAvailableParams();
  }, []);

  // ===== API 调用函数 =====

  const fetchAvailableParams = async () => {
    try {
      const response = await axios.get('/api/m05/results/list');
      if (response.data && response.data.data && response.data.data.results) {
        const results = response.data.data.results;
        setAvailableParams(results);
        if (results.length > 0) {
          setSelectedParam(results[0].params);
        }
      } else {
        setAvailableParams([]);
      }
    } catch (error) {
      console.error('获取参数列表失败:', error);
      setAvailableParams([]);
    }
  };

  const generateDescriptiveStats = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/descriptive-stats', {
        params: selectedParam
      });

      if (response.data.success) {
        // 读取 CSV 数据并展示
        const csvResponse = await axios.get(response.data.output_file);
        setDescriptiveStats(csvResponse.data);
        message.success('描述性统计生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成描述性统计失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateCorrelationAnalysis = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/correlation-analysis', {
        params: selectedParam,
        method: correlationMethod
      });

      if (response.data.success) {
        setCorrelationHeatmap(response.data.heatmap_file);
        message.success(`${correlationMethod.toUpperCase()} 相关性分析完成！`);
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成相关性分析失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateSignificanceBarplot = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/significance-barplot', {
        params: selectedParam,
        top_n: topNFeatures
      });

      if (response.data.success) {
        setSignificanceBarplot(response.data.plot_file);
        message.success('显著性柱状图生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成显著性柱状图失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateComplexityViolin = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/complexity-violin', {
        params: selectedParam
      });

      if (response.data.success) {
        setComplexityViolin(response.data.plot_file);
        message.success('复杂度小提琴图生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成复杂度小提琴图失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateGroupedBoxplots = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/grouped-boxplots', {
        params: selectedParam
      });

      if (response.data.success) {
        setGroupedBoxplots(response.data.plot_file);
        message.success('分组箱线图生成成功！');
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('生成分组箱线图失败:', error);
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateAllVisualizations = async () => {
    if (!selectedParam) {
      message.warning('请先选择参数组合');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/m05/visualization/generate-all', {
        params: selectedParam
      });

      if (response.data.success) {
        const results = response.data.results;

        // 更新所有状态 - 只在有有效文件路径时才更新
        if (results.correlation_pearson?.success && results.correlation_pearson.heatmap_file) {
          setCorrelationHeatmap(results.correlation_pearson.heatmap_file);
        }
        if (results.significance_barplot?.success && results.significance_barplot.plot_file) {
          setSignificanceBarplot(results.significance_barplot.plot_file);
        }
        if (results.complexity_violin?.success && results.complexity_violin.plot_file) {
          setComplexityViolin(results.complexity_violin.plot_file);
        }
        if (results.grouped_boxplots?.success && results.grouped_boxplots.plot_file) {
          setGroupedBoxplots(results.grouped_boxplots.plot_file);
        }

        message.success(`所有可视化生成完成！共 ${response.data.total_files} 个文件`);
      } else {
        message.error('生成失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('批量生成失败:', error);
      message.error('批量生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // ===== 渲染函数 =====

  const renderOverview = () => (
    <Card title="可视化概览" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Alert
          message="增强可视化分析模块"
          description="该模块提供专业的统计图表和分组可视化，支持描述性统计、相关性分析、显著性检验等多种科研可视化功能。"
          type="info"
          showIcon
        />

        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="可用参数组合"
              value={availableParams.length}
              prefix={<ThunderboltOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="可视化类型"
              value={5}
              prefix={<BarChartOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="当前参数"
              value={selectedParam ? 'm=' + selectedParam.m : 'N/A'}
            />
          </Col>
        </Row>

        <Space>
          <Select
            style={{ width: 400 }}
            placeholder="选择参数组合"
            value={selectedParam ? JSON.stringify(selectedParam) : undefined}
            onChange={(value) => setSelectedParam(JSON.parse(value))}
          >
            {availableParams.map((item, idx) => (
              <Option key={idx} value={JSON.stringify(item.params)}>
                m={item.params.m}, τ={item.params.tau}, ε={item.params.eps}, lmin={item.params.lmin}
              </Option>
            ))}
          </Select>

          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={generateAllVisualizations}
            loading={loading}
            size="large"
          >
            一键生成所有可视化
          </Button>
        </Space>
      </Space>
    </Card>
  );

  const renderCorrelationHeatmap = () => (
    <Card title="相关性热力图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Space>
          <Radio.Group
            value={correlationMethod}
            onChange={(e) => setCorrelationMethod(e.target.value)}
          >
            <Radio.Button value="pearson">Pearson</Radio.Button>
            <Radio.Button value="spearman">Spearman</Radio.Button>
          </Radio.Group>

          <Button
            type="primary"
            icon={<HeatMapOutlined />}
            onClick={generateCorrelationAnalysis}
            loading={loading}
          >
            生成热力图
          </Button>
        </Space>

        {correlationHeatmap ? (
          <Image
            src={`/api/m05/visualization/image/${correlationHeatmap.split(/visualizations[\\/]/)[1]}`}
            alt="Correlation Heatmap"
            style={{ maxWidth: '100%' }}
          />
        ) : (
          <Alert
            message="暂无图片"
            description="请先点击生成热力图按钮生成可视化图表"
            type="info"
            showIcon
          />
        )}
      </Space>
    </Card>
  );

  const renderSignificanceBarplot = () => (
    <Card title="显著性特征柱状图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Space>
          <span>显示前</span>
          <Select
            value={topNFeatures}
            onChange={setTopNFeatures}
            style={{ width: 80 }}
          >
            <Option value={10}>10</Option>
            <Option value={20}>20</Option>
            <Option value={30}>30</Option>
          </Select>
          <span>个特征</span>

          <Button
            type="primary"
            icon={<BarChartOutlined />}
            onClick={generateSignificanceBarplot}
            loading={loading}
          >
            生成柱状图
          </Button>
        </Space>

        {significanceBarplot ? (
          <Image
            src={`/api/m05/visualization/image/${significanceBarplot.split(/visualizations[\\/]/)[1]}`}
            alt="Significance Barplot"
            style={{ maxWidth: '100%' }}
          />
        ) : (
          <Alert
            message="暂无图片"
            description="请先点击生成柱状图按钮生成可视化图表"
            type="info"
            showIcon
          />
        )}
      </Space>
    </Card>
  );

  const renderComplexityViolin = () => (
    <Card title="复杂度小提琴图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Button
          type="primary"
          icon={<LineChartOutlined />}
          onClick={generateComplexityViolin}
          loading={loading}
        >
          生成小提琴图
        </Button>

        {complexityViolin ? (
          <Image
            src={`/api/m05/visualization/image/${complexityViolin.split(/visualizations[\\/]/)[1]}`}
            alt="Complexity Violin Plot"
            style={{ maxWidth: '100%' }}
          />
        ) : (
          <Alert
            message="暂无图片"
            description="请先点击生成小提琴图按钮生成可视化图表"
            type="info"
            showIcon
          />
        )}
      </Space>
    </Card>
  );

  const renderGroupedBoxplots = () => (
    <Card title="分组箱线图" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Button
          type="primary"
          icon={<BoxPlotOutlined />}
          onClick={generateGroupedBoxplots}
          loading={loading}
        >
          生成箱线图
        </Button>

        {groupedBoxplots ? (
          <Image
            src={`/api/m05/visualization/image/${groupedBoxplots.split(/visualizations[\\/]/)[1]}`}
            alt="Grouped Boxplots"
            style={{ maxWidth: '100%' }}
          />
        ) : (
          <Alert
            message="暂无图片"
            description="请先点击生成箱线图按钮生成可视化图表"
            type="info"
            showIcon
          />
        )}
      </Space>
    </Card>
  );

  // ===== 主渲染 =====
  const tabItems = [
    {
      key: 'overview',
      label: '概览',
      children: renderOverview()
    },
    {
      key: 'correlation',
      label: '相关性热力图',
      children: renderCorrelationHeatmap()
    },
    {
      key: 'significance',
      label: '显著性柱状图',
      children: renderSignificanceBarplot()
    },
    {
      key: 'complexity',
      label: '复杂度小提琴图',
      children: renderComplexityViolin()
    },
    {
      key: 'boxplots',
      label: '分组箱线图',
      children: renderGroupedBoxplots()
    }
  ];

  return (
    <Spin spinning={loading} tip="生成可视化中...">
      <Tabs
        activeKey={activeVizTab}
        onChange={setActiveVizTab}
        items={tabItems}
      />
    </Spin>
  );
};

export default EnhancedVisualizationPanel;
