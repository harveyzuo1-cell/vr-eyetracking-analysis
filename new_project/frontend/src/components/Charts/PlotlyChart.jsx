/**
 * Plotly.js 基础封装组件
 *
 * 提供统一的Plotly图表接口
 */
import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist';
import { Spin } from 'antd';

const PlotlyChart = ({
  data,
  layout = {},
  config = {},
  style = {},
  loading = false,
  onInitialized,
  onUpdate,
  onHover,
  onClick
}) => {
  const plotRef = useRef(null);
  const plotDivRef = useRef(null);

  // 默认配置
  const defaultConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d'],
    ...config
  };

  // 默认布局
  const defaultLayout = {
    autosize: true,
    margin: { l: 50, r: 50, t: 50, b: 50 },
    font: {
      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif',
      size: 12
    },
    ...layout
  };

  useEffect(() => {
    if (!plotDivRef.current || !data || loading) return;

    // 创建或更新图表
    if (!plotRef.current) {
      // 首次创建
      Plotly.newPlot(plotDivRef.current, data, defaultLayout, defaultConfig)
        .then((gd) => {
          plotRef.current = gd;

          // 绑定事件
          if (onHover) {
            gd.on('plotly_hover', onHover);
          }
          if (onClick) {
            gd.on('plotly_click', onClick);
          }
          if (onInitialized) {
            onInitialized(gd);
          }
        })
        .catch((error) => {
          console.error('Plotly图表创建失败:', error);
        });
    } else {
      // 更新数据
      Plotly.react(plotDivRef.current, data, defaultLayout, defaultConfig)
        .then(() => {
          if (onUpdate) {
            onUpdate(plotRef.current);
          }
        })
        .catch((error) => {
          console.error('Plotly图表更新失败:', error);
        });
    }

    // 清理函数
    return () => {
      if (plotRef.current && plotDivRef.current) {
        Plotly.purge(plotDivRef.current);
        plotRef.current = null;
      }
    };
  }, [data, layout, config, loading]);

  // 窗口大小变化时调整图表
  useEffect(() => {
    const handleResize = () => {
      if (plotRef.current && plotDivRef.current) {
        Plotly.Plots.resize(plotDivRef.current);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: style.height || '400px',
        ...style
      }}>
        <Spin size="large" spinning={true} tip="加载图表中...">
          <div style={{ padding: '50px' }} />
        </Spin>
      </div>
    );
  }

  return (
    <div
      ref={plotDivRef}
      style={{
        width: '100%',
        height: '400px',
        ...style
      }}
    />
  );
};

export default PlotlyChart;
