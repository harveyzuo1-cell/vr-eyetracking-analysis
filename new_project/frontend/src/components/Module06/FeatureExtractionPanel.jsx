import React, { useState } from 'react';
import { Card, Tabs, Typography, Space, Alert, Row, Col } from 'antd';
import { ExperimentOutlined, BarChartOutlined, DownloadOutlined } from '@ant-design/icons';
import SensitivityAnalysisPanel from './SensitivityAnalysisPanel';
import FeatureSelectionPanel from './FeatureSelectionPanel';
import BatchExtractionPanel from './BatchExtractionPanel';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

/**
 * Module06: 特征提取与选择主面板
 *
 * 功能模块:
 * 1. 敏感度分析 - 计算 Module04/Module05 特征的统计显著性
 * 2. 特征选择 - 基于敏感度分数选择 Top-K 特征
 * 3. 批量提取 - 批量提取特征向量并导出
 */
const FeatureExtractionPanel = () => {
  const [activeTab, setActiveTab] = useState('1');

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 标题区域 */}
        <Card>
          <Space direction="vertical" size="small">
            <Title level={3} style={{ margin: 0 }}>
              <ExperimentOutlined /> Module06: 特征提取与选择
            </Title>
            <Text type="secondary">
              基于统计显著性的特征选择与批量特征向量提取系统
            </Text>
          </Space>
        </Card>

        {/* 系统说明 */}
        <Alert
          message="系统功能"
          description={
            <div>
              <p><strong>Phase 1: 敏感度分析</strong> - 使用 ANOVA、Eta Squared、Cohen's d、Bonferroni 校正、变异系数等统计指标评估特征显著性</p>
              <p><strong>Phase 2: 特征选择</strong> - 基于综合评分选择最具区分力的 Top-K 特征（Strategy A: 10维 / Strategy B: 69维）</p>
              <p><strong>Phase 3: 批量提取</strong> - 批量提取所有受试者的特征向量，导出为 CSV/JSON 格式供机器学习使用</p>
            </div>
          }
          type="info"
          showIcon
        />

        {/* 核心统计指标说明 */}
        <Card title="统计指标说明" size="small">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card type="inner" size="small">
                <Space direction="vertical" size="small">
                  <Text strong>Module04 特征池（9个）</Text>
                  <Text type="secondary">眼动事件分析特征</Text>
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    <li>扫视相关: total_saccades, avg_saccade_amplitude, avg_saccade_velocity</li>
                    <li>注视相关: total_fixations, avg_fixation_duration</li>
                    <li>ROI相关: kw_ratio_frame, inst_ratio_frame, bg_ratio_frame, total_roi_fixations</li>
                  </ul>
                </Space>
              </Card>
            </Col>
            <Col span={12}>
              <Card type="inner" size="small">
                <Space direction="vertical" size="small">
                  <Text strong>Module05 特征池（11个 RQA 指标）</Text>
                  <Text type="secondary">递归量化分析特征 → 选择 Top-6</Text>
                  <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
                    <li><strong>基础RQA（6个）:</strong> RR-1D-x, DET-1D-x, ENT-1D-x, RR-2D-xy, DET-2D-xy, ENT-2D-xy</li>
                    <li><strong>衍生特征（5个）:</strong> rqa_complexity_1d, rqa_complexity_2d, rqa_diff_rr, rqa_diff_det, rqa_diff_ent</li>
                    <li style={{ color: '#ff4d4f', marginTop: 4 }}><strong>策略A:</strong> 通过敏感度分析从11个特征中选择最显著的6个</li>
                  </ul>
                </Space>
              </Card>
            </Col>
          </Row>
        </Card>

        {/* 功能标签页 */}
        <Card>
          <Tabs activeKey={activeTab} onChange={setActiveTab} size="large">
            <TabPane
              tab={<span><BarChartOutlined /> 敏感度分析</span>}
              key="1"
            >
              <SensitivityAnalysisPanel />
            </TabPane>

            <TabPane
              tab={<span><ExperimentOutlined /> 特征选择</span>}
              key="2"
            >
              <FeatureSelectionPanel />
            </TabPane>

            <TabPane
              tab={<span><DownloadOutlined /> 批量提取</span>}
              key="3"
            >
              <BatchExtractionPanel />
            </TabPane>
          </Tabs>
        </Card>
      </Space>
    </div>
  );
};

export default FeatureExtractionPanel;
