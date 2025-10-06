/**
 * 眼动轨迹图组件
 *
 * 显示眼球追踪的轨迹路径
 */
import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import PlotlyChart from './PlotlyChart';
import { calculateAllROIStats } from '../../utils/roiAnalyzer';

const GazeTrajectoryChart = ({
  data,
  roiConfig = null,  // 新增: ROI配置
  loading = false,
  title = '眼动轨迹图',
  showColorbar = true,
  style = {}
}) => {
  const { t } = useTranslation(['module01']);

  // 计算ROI统计信息
  const roiStats = useMemo(() => {
    if (!roiConfig || !roiConfig.regions || !data || data.length === 0) {
      return null;
    }
    return calculateAllROIStats(data, roiConfig.regions);
  }, [data, roiConfig]);

  // 处理数据并生成Plotly图表数据
  const plotData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return [];
    }

    // 提取x, y, timestamp数据
    const x = data.map(d => d.x);
    const y = data.map(d => d.y);
    const time = data.map(d => d.timestamp || d.time || 0); // 支持timestamp和time字段

    return [
      {
        type: 'scatter',
        mode: 'lines+markers',
        x: x,
        y: y,
        marker: {
          size: 6,
          color: time,
          colorscale: 'Viridis',
          showscale: showColorbar,
          colorbar: {
            title: t('timeSeconds'),
            titleside: 'right'
          },
          line: {
            color: 'white',
            width: 1
          }
        },
        line: {
          color: 'rgba(100, 100, 100, 0.3)',
          width: 1
        },
        text: time.map((timeValue, i) => `${t('point')} ${i + 1}<br>${t('timeSeconds')}: ${timeValue.toFixed(2)}<br>${t('position')}: (${x[i].toFixed(3)}, ${y[i].toFixed(3)})`),
        hoverinfo: 'text',
        name: t('trajectoryChart')
      },
      // 添加起点标记
      {
        type: 'scatter',
        mode: 'markers',
        x: [x[0]],
        y: [y[0]],
        marker: {
          size: 15,
          color: 'green',
          symbol: 'star',
          line: {
            color: 'white',
            width: 2
          }
        },
        text: [t('startPoint')],
        hoverinfo: 'text',
        name: t('startPoint'),
        showlegend: true
      },
      // 添加终点标记
      {
        type: 'scatter',
        mode: 'markers',
        x: [x[x.length - 1]],
        y: [y[y.length - 1]],
        marker: {
          size: 15,
          color: 'red',
          symbol: 'square',
          line: {
            color: 'white',
            width: 2
          }
        },
        text: [t('endPoint')],
        hoverinfo: 'text',
        name: t('endPoint'),
        showlegend: true
      }
    ];
  }, [data, showColorbar, t]);

  // 图表布局配置 - 使用useMemo确保语言切换时更新
  const layout = useMemo(() => {
    const baseLayout = {
      title: {
        text: title,
        font: { size: 16, weight: 'bold' }
      },
      xaxis: {
        title: t('xCoordinateNormalized'),
        range: [0, 1],
        showgrid: true,
        gridcolor: '#e0e0e0',
        zeroline: false
      },
      yaxis: {
        title: t('yCoordinateNormalized'),
        range: [0, 1],
        showgrid: true,
        gridcolor: '#e0e0e0',
        zeroline: false,
        scaleanchor: 'x',
        scaleratio: 1
      },
      hovermode: 'closest',
      showlegend: true,
      legend: {
        x: 1,
        xanchor: 'right',
        y: 1,
        bgcolor: 'rgba(255, 255, 255, 0.8)',
        bordercolor: '#ccc',
        borderwidth: 1
      },
      plot_bgcolor: '#f9f9f9',
      paper_bgcolor: 'white'
    };

    // 添加ROI矩形框和标签
    if (roiConfig && roiConfig.regions && roiConfig.regions.length > 0) {
      // ROI矩形
      baseLayout.shapes = roiConfig.regions.map(roi => ({
        type: 'rect',
        xref: 'x',
        yref: 'y',
        x0: roi.x,
        y0: roi.y,
        x1: roi.x + roi.width,
        y1: roi.y + roi.height,
        fillcolor: roi.color,
        opacity: 0.25,  // 半透明
        line: {
          color: roi.color,
          width: 2
        }
      }));

      // ROI标签
      baseLayout.annotations = roiConfig.regions.map(roi => ({
        x: roi.x + roi.width / 2,
        y: roi.y + roi.height / 2,
        text: roi.name,
        showarrow: false,
        font: {
          size: 10,
          color: '#333',
          weight: 'bold'
        },
        bgcolor: 'rgba(255, 255, 255, 0.7)',
        borderpad: 2
      }));
    }

    return baseLayout;
  }, [title, t, roiConfig]);

  // 图表配置
  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d', 'autoScale2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'gaze_trajectory',
      height: 800,
      width: 800,
      scale: 2
    }
  };

  return (
    <div>
      <PlotlyChart
        data={plotData}
        layout={layout}
        config={config}
        loading={loading}
        style={{ height: '500px', ...style }}
      />

      {/* ROI统计信息 */}
      {roiStats && roiConfig && (
        <div style={{
          marginTop: 16,
          padding: 12,
          background: '#f5f5f5',
          borderRadius: 4,
          border: '1px solid #d9d9d9'
        }}>
          <h4 style={{ marginBottom: 12, fontWeight: 'bold' }}>{t('roiStatistics')}</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12 }}>
            {roiConfig.regions.map(roi => {
              const stats = roiStats[roi.id];
              if (!stats) return null;

              return (
                <div
                  key={roi.id}
                  style={{
                    padding: 8,
                    background: 'white',
                    borderRadius: 4,
                    borderLeft: `4px solid ${roi.color}`
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: 4, color: roi.color }}>
                    {roi.name}
                  </div>
                  <div style={{ fontSize: 12, color: '#666', lineHeight: 1.6 }}>
                    <div>{t('roiEntryCount')}: <strong>{stats.entry_count}</strong></div>
                    <div>{t('roiExitCount')}: <strong>{stats.exit_count}</strong></div>
                    <div>{t('roiPointsInside')}: <strong>{stats.points_inside}</strong> / {stats.total_points}</div>
                    <div>{t('roiDuration')}: <strong>{stats.duration_inside.toFixed(2)}{t('seconds')}</strong></div>
                    <div>{t('roiCoverage')}: <strong>{(stats.inside_ratio * 100).toFixed(1)}%</strong></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default GazeTrajectoryChart;
