/**
 * ROI统计信息面板组件
 * ROI Statistics Panel Component
 */
import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Divider, Empty, Row, Col, Tag } from 'antd';
import PlotlyChart from './PlotlyChart';

const ROIStatsPanel = ({ roiStats, roiConfig }) => {
  const { t } = useTranslation(['module01']);
  const [selectedMetric, setSelectedMetric] = useState('fixation_time'); // 默认显示注视时长

  // 准备柱状图数据 - 必须在条件判断之前调用所有hooks
  const chartData = useMemo(() => {
    if (!roiStats || !roiConfig || !roiStats.stats || !roiConfig.regions) return null;

    const categories = ['keywords', 'instructions', 'background'];
    const labels = ['关键词', '指示语', '背景'];
    const colors = ['#1890ff', '#52c41a', '#faad14'];

    const values = categories.map(category => {
      const regions = roiConfig.regions[category] || [];
      let sum = 0;

      regions.forEach(roi => {
        const stats = roiStats.stats[roi.id];
        if (stats) {
          if (selectedMetric === 'fixation_time') {
            sum += stats.fixation_time || 0;
          } else if (selectedMetric === 'entry_count') {
            sum += stats.entry_count || 0;
          } else if (selectedMetric === 'coverage_ratio') {
            sum += stats.coverage_ratio || 0;
          }
        }
      });

      return sum;
    });

    return [{
      type: 'bar',
      x: labels,
      y: values,
      marker: {
        color: colors
      },
      text: values.map((v, idx) => {
        if (selectedMetric === 'fixation_time') return `${v.toFixed(2)}s`;
        if (selectedMetric === 'entry_count') return v;
        if (selectedMetric === 'coverage_ratio') return `${(v * 100).toFixed(1)}%`;
        return v;
      }),
      textposition: 'outside',
      hovertemplate: labels.map((label, idx) => {
        if (selectedMetric === 'fixation_time') return `${label}<br>注视时长: ${values[idx].toFixed(2)}s<extra></extra>`;
        if (selectedMetric === 'entry_count') return `${label}<br>进入次数: ${values[idx]}<extra></extra>`;
        if (selectedMetric === 'coverage_ratio') return `${label}<br>覆盖率: ${(values[idx] * 100).toFixed(1)}%<extra></extra>`;
        return `${label}<br>${values[idx]}<extra></extra>`;
      })
    }];
  }, [roiStats, roiConfig, selectedMetric]);

  const chartLayout = useMemo(() => ({
    height: 250,
    margin: { l: 40, r: 20, t: 20, b: 40 },
    xaxis: {
      title: 'ROI类型'
    },
    yaxis: {
      title: selectedMetric === 'fixation_time' ? '注视时长 (s)' :
             selectedMetric === 'entry_count' ? '进入次数' :
             selectedMetric === 'coverage_ratio' ? '覆盖率' : ''
    },
    showlegend: false
  }), [selectedMetric]);

  // 条件判断必须在所有hooks之后
  if (!roiStats || !roiConfig) {
    return (
      <Card
        title={t('roiStatistics') || 'ROI统计信息'}
        style={{ height: '100%' }}
      >
        <Empty description={t('loadDataToView') || '请加载数据后查看统计信息'} />
      </Card>
    );
  }

  return (
    <Card
      title={t('roiStatistics') || 'ROI统计信息'}
      style={{ height: '100%', maxHeight: '800px', overflowY: 'auto' }}
    >
      {/* 汇总信息 - 两列布局 */}
      {roiStats.summary && (
        <div style={{
          marginBottom: 16,
          padding: 12,
          background: '#f0f7ff',
          borderRadius: 4,
          borderLeft: '4px solid #1890ff'
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: 12, color: '#1890ff', fontSize: '14px' }}>
            {t('roiSummary') || '总体统计'}
          </div>
          <Row gutter={[8, 8]}>
            <Col span={12}>
              <div style={{ fontSize: '12px' }}>
                {t('roiTotalFixationTime') || '总注视时间'}:
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#1890ff' }}>
                {roiStats.summary.total_fixation_time?.toFixed(2) || 0}s
              </div>
            </Col>
            <Col span={12}>
              <div style={{ fontSize: '12px' }}>
                {t('roiTotalEntryCount') || '总进入次数'}:
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#1890ff' }}>
                {roiStats.summary.total_entry_count || 0}
              </div>
            </Col>
            <Col span={12}>
              <div style={{ fontSize: '12px' }}>
                {t('roiKeywordsFixationTime') || '关键词注视'}:
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '14px', color: '#52c41a' }}>
                {roiStats.summary.keywords_fixation_time?.toFixed(2) || 0}s
              </div>
            </Col>
            <Col span={12}>
              <div style={{ fontSize: '12px' }}>
                {t('roiInstructionsFixationTime') || '指示语注视'}:
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '14px', color: '#fa8c16' }}>
                {roiStats.summary.instructions_fixation_time?.toFixed(2) || 0}s
              </div>
            </Col>
          </Row>
        </div>
      )}

      {/* 指标选择Tag */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ marginBottom: 8, fontSize: '12px', color: '#666' }}>选择指标：</div>
        <div>
          <Tag.CheckableTag
            checked={selectedMetric === 'fixation_time'}
            onChange={() => setSelectedMetric('fixation_time')}
          >
            注视时长
          </Tag.CheckableTag>
          <Tag.CheckableTag
            checked={selectedMetric === 'entry_count'}
            onChange={() => setSelectedMetric('entry_count')}
          >
            进入次数
          </Tag.CheckableTag>
          <Tag.CheckableTag
            checked={selectedMetric === 'coverage_ratio'}
            onChange={() => setSelectedMetric('coverage_ratio')}
          >
            覆盖率
          </Tag.CheckableTag>
        </div>
      </div>

      {/* 柱状图可视化 */}
      {chartData && (
        <div style={{ marginBottom: 16 }}>
          <PlotlyChart
            data={chartData}
            layout={chartLayout}
            config={{ displayModeBar: false }}
          />
        </div>
      )}

      {/* 详细统计 - 按类型分组 */}
      {roiStats.stats && (
        <>
          {/* 关键词区域 */}
          {roiConfig.regions?.keywords && roiConfig.regions.keywords.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <Divider orientation="left" style={{ margin: '12px 0', fontSize: '13px', fontWeight: 'bold' }}>
                {t('roiKeywords') || '关键词区域'}
              </Divider>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 6 }}>
                {roiConfig.regions.keywords.map(roi => {
                  const stats = roiStats.stats[roi.id];
                  if (!stats) return null;

                  // 清理ROI名称：去掉受试者ID前缀（如 KW_n2q1_3 -> KW_q1_3）
                  const cleanName = (roi.name || roi.id).replace(/([A-Z]+_)[nma]\d+q/i, '$1q');

                  return (
                    <div
                      key={roi.id}
                      style={{
                        padding: 6,
                        background: '#fafafa',
                        borderRadius: 4,
                        borderLeft: `3px solid ${roi.color}`
                      }}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: 4, color: roi.color, fontSize: '12px' }}>
                        {cleanName}
                      </div>
                      <Row gutter={8} style={{ fontSize: 11, color: '#666' }}>
                        <Col span={12}>
                          <div>{t('roiEntryCount') || '进入'}: <strong>{stats.entry_count}</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiRegressionCount') || '回视'}: <strong>{stats.regression_count}</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiFixationTime') || '注视'}: <strong>{stats.fixation_time.toFixed(2)}s</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiCoverage') || '覆盖'}: <strong>{(stats.coverage_ratio * 100).toFixed(1)}%</strong></div>
                        </Col>
                      </Row>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 指示语区域 */}
          {roiConfig.regions?.instructions && roiConfig.regions.instructions.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <Divider orientation="left" style={{ margin: '12px 0', fontSize: '13px', fontWeight: 'bold' }}>
                {t('roiInstructions') || '指示语区域'}
              </Divider>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 6 }}>
                {roiConfig.regions.instructions.map(roi => {
                  const stats = roiStats.stats[roi.id];
                  if (!stats) return null;

                  // 清理ROI名称：去掉受试者ID前缀（如 INST_n2q1_1 -> INST_q1_1）
                  const cleanName = (roi.name || roi.id).replace(/([A-Z]+_)[nma]\d+q/i, '$1q');

                  return (
                    <div
                      key={roi.id}
                      style={{
                        padding: 6,
                        background: '#fafafa',
                        borderRadius: 4,
                        borderLeft: `3px solid ${roi.color}`
                      }}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: 4, color: roi.color, fontSize: '12px' }}>
                        {cleanName}
                      </div>
                      <Row gutter={8} style={{ fontSize: 11, color: '#666' }}>
                        <Col span={12}>
                          <div>{t('roiEntryCount') || '进入'}: <strong>{stats.entry_count}</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiRegressionCount') || '回视'}: <strong>{stats.regression_count}</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiFixationTime') || '注视'}: <strong>{stats.fixation_time.toFixed(2)}s</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiCoverage') || '覆盖'}: <strong>{(stats.coverage_ratio * 100).toFixed(1)}%</strong></div>
                        </Col>
                      </Row>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 背景区域 */}
          {roiConfig.regions?.background && roiConfig.regions.background.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <Divider orientation="left" style={{ margin: '12px 0', fontSize: '13px', fontWeight: 'bold' }}>
                {t('roiBackground') || '背景区域'}
              </Divider>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 6 }}>
                {roiConfig.regions.background.map(roi => {
                  const stats = roiStats.stats[roi.id];
                  if (!stats) return null;

                  // 清理ROI名称：去掉受试者ID前缀（如 BG_n2q1 -> BG_q1）
                  const cleanName = (roi.name || roi.id).replace(/([A-Z]+_)[nma]\d+q/i, '$1q');

                  return (
                    <div
                      key={roi.id}
                      style={{
                        padding: 6,
                        background: '#fafafa',
                        borderRadius: 4,
                        borderLeft: `3px solid ${roi.color}`
                      }}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: 4, color: roi.color, fontSize: '12px' }}>
                        {cleanName}
                      </div>
                      <Row gutter={8} style={{ fontSize: 11, color: '#666' }}>
                        <Col span={12}>
                          <div>{t('roiEntryCount') || '进入'}: <strong>{stats.entry_count}</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiRegressionCount') || '回视'}: <strong>{stats.regression_count}</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiFixationTime') || '注视'}: <strong>{stats.fixation_time.toFixed(2)}s</strong></div>
                        </Col>
                        <Col span={12}>
                          <div>{t('roiCoverage') || '覆盖'}: <strong>{(stats.coverage_ratio * 100).toFixed(1)}%</strong></div>
                        </Col>
                      </Row>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  );
};

export default ROIStatsPanel;
