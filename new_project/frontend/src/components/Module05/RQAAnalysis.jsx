/**
 * Module05: RQA递归量化分析
 * 完整的5步RQA分析流程
 */
import React, { useState } from 'react';
import { Tabs, Card } from 'antd';
import {
  SettingOutlined,
  ThunderboltOutlined,
  FileSearchOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import ParamConfigPanel from './ParamConfigPanel';
import BatchExecutionPanel from './BatchExecutionPanel';
import ResultsViewer from './ResultsViewer';
import VisualizationPanel from './VisualizationPanel';

const RQAAnalysis = () => {
  const [activeTab, setActiveTab] = useState('1');

  const tabItems = [
    {
      key: '1',
      label: (
        <span>
          <SettingOutlined />
          参数配置
        </span>
      ),
      children: <ParamConfigPanel />
    },
    {
      key: '2',
      label: (
        <span>
          <ThunderboltOutlined />
          批量执行
        </span>
      ),
      children: <BatchExecutionPanel />
    },
    {
      key: '3',
      label: (
        <span>
          <FileSearchOutlined />
          结果查看
        </span>
      ),
      children: <ResultsViewer />
    },
    {
      key: '4',
      label: (
        <span>
          <BarChartOutlined />
          可视化分析
        </span>
      ),
      children: <VisualizationPanel />
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div>
            <h2 style={{ margin: 0 }}>
              <BarChartOutlined style={{ marginRight: 8 }} />
              Module05: RQA递归量化分析
            </h2>
            <p style={{ margin: '8px 0 0', fontSize: 14, fontWeight: 'normal', color: '#666' }}>
              完整的5步RQA分析流程：计算 → 合并 → 特征增强 → 统计分析 → 可视化
            </p>
          </div>
        }
        bordered={false}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="large"
        />
      </Card>
    </div>
  );
};

export default RQAAnalysis;
