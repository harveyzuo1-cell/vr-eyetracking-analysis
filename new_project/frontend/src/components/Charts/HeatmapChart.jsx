/**
 * 眼动热力图组件
 *
 * 显示眼球追踪数据的热力分布
 */
import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import PlotlyChart from './PlotlyChart';

const HeatmapChart = ({
  data,
  loading = false,
  title = '眼动热力图',
  gridSize = 50,
  style = {}
}) => {
  const { t } = useTranslation(['module01']);

  // 计算热力图数据
  const plotData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return [];
    }

    // 创建网格
    const grid = Array(gridSize).fill().map(() => Array(gridSize).fill(0));

    // 统计每个网格的注视点数量
    data.forEach(point => {
      const gridX = Math.floor(point.x * (gridSize - 1));
      const gridY = Math.floor(point.y * (gridSize - 1));

      if (gridX >= 0 && gridX < gridSize && gridY >= 0 && gridY < gridSize) {
        grid[gridY][gridX] += 1;
      }
    });

    return [{
      type: 'heatmap',
      z: grid,
      colorscale: 'Hot',
      showscale: true,
      colorbar: {
        title: t('gazeDensity'),
        titleside: 'right'
      },
      hovertemplate: `${t('position')}: (%{x}, %{y})<br>${t('gazeDensity')}: %{z}<extra></extra>`
    }];
  }, [data, gridSize, t]);

  // 图表布局 - 使用useMemo确保语言切换时更新
  const layout = useMemo(() => ({
    title: {
      text: title,
      font: { size: 16, weight: 'bold' }
    },
    xaxis: {
      title: t('xCoordinateNormalized'),
      showgrid: false,
      range: [0, gridSize - 1],
      tickmode: 'array',
      tickvals: [0, (gridSize - 1) / 4, (gridSize - 1) / 2, 3 * (gridSize - 1) / 4, gridSize - 1],
      ticktext: ['0.00', '0.25', '0.50', '0.75', '1.00']
    },
    yaxis: {
      title: t('yCoordinateNormalized'),
      showgrid: false,
      scaleanchor: 'x',
      scaleratio: 1,
      range: [0, gridSize - 1],
      tickmode: 'array',
      tickvals: [0, (gridSize - 1) / 4, (gridSize - 1) / 2, 3 * (gridSize - 1) / 4, gridSize - 1],
      ticktext: ['0.00', '0.25', '0.50', '0.75', '1.00']
    },
    plot_bgcolor: 'white',
    paper_bgcolor: 'white'
  }), [title, gridSize, t]);

  // 图表配置
  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'gaze_heatmap',
      height: 800,
      width: 800,
      scale: 2
    }
  };

  return (
    <PlotlyChart
      data={plotData}
      layout={layout}
      config={config}
      loading={loading}
      style={{ height: '500px', ...style }}
    />
  );
};

export default HeatmapChart;
