/**
 * 增强版眼动轨迹图组件
 * Enhanced Gaze Trajectory Chart Component
 *
 * 支持多层ROI和背景图片叠加
 * Supports multi-layer ROI and background image overlay
 */
import React, { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Slider, Switch, Divider, message, Collapse } from 'antd';
import PlotlyChart from './PlotlyChart';
import CalibrationPanel from '../Calibration/CalibrationPanel';
import calibrationService from '../../services/calibrationService';

const GazeTrajectoryChartEnhanced = ({
  data,
  roiConfig = null,  // 增强版ROI配置 (multi-layer)
  loading = false,
  title = '眼动轨迹图',
  showColorbar = true,
  style = {},
  // 校正功能相关props
  enableCalibration = false,
  group = null,
  subjectId = null,
  task = null,
  onDataChange = null  // 当显示的数据变化时的回调
}) => {
  const { t } = useTranslation(['module01']);

  // 背景图片透明度控制
  const [bgOpacity, setBgOpacity] = useState(0.3);

  // ROI显示控制
  const [showKeywords, setShowKeywords] = useState(true);
  const [showInstructions, setShowInstructions] = useState(true);
  const [showBackground, setShowBackground] = useState(false);

  // 校正相关状态
  const [originalData, setOriginalData] = useState([]);
  const [calibratedData, setCalibratedData] = useState(null);
  const [currentParams, setCurrentParams] = useState(null);
  const [currentVersion, setCurrentVersion] = useState(null); // 当前版本信息
  const [isLoadingCalibration, setIsLoadingCalibration] = useState(false);

  // 当group/subjectId/task变化时，重置状态
  useEffect(() => {
    // 重置所有状态
    setCalibratedData(null);
    setCurrentParams(null);
    setCurrentVersion(null);
    setOriginalData([]);
  }, [group, subjectId, task]);

  // 加载最新的校正数据 (定义在useEffect之前避免hoisting问题)
  const loadLatestCalibration = useCallback(async () => {
    if (!group || !subjectId || !task) return;

    setIsLoadingCalibration(true);
    try {
      // 尝试加载已保存的校正数据
      const calibratedData = await calibrationService.loadCalibratedData(group, subjectId, task);
      if (calibratedData && calibratedData.length > 0) {
        setCalibratedData(calibratedData);

        // 加载参数
        const paramsResult = await calibrationService.getCalibrationParams(group, subjectId, task);
        if (paramsResult) {
          setCurrentParams(paramsResult.params);
          setCurrentVersion({
            version: paramsResult.version,
            calibrated_at: paramsResult.metadata?.calibrated_at,
            restored_from_version: paramsResult.metadata?.restored_from_version
          });
        }
      }
    } catch (error) {
      // 没有校正数据是正常情况，不需要报错
      console.log('No calibration data found, using original data');
    } finally {
      setIsLoadingCalibration(false);
    }
  }, [group, subjectId, task]);

  // 当原始数据加载完成时，更新originalData并尝试加载校正数据
  useEffect(() => {
    if (data && data.length > 0) {
      setOriginalData(data);

      // 如果启用校正且有必要的参数，尝试加载最新的校正数据
      if (enableCalibration && group && subjectId && task) {
        loadLatestCalibration();
      }
    }
  }, [data, enableCalibration, group, subjectId, task, loadLatestCalibration]);

  // 处理预览回调
  const handleCalibrationPreview = useCallback((previewData, params) => {
    setCalibratedData(previewData);
    setCurrentParams(params);
  }, []);

  // 处理保存完成回调
  const handleSaveComplete = useCallback(async (result) => {
    // 保存成功后重新加载最新的校正数据
    await loadLatestCalibration();
    message.success('校正数据已应用');
  }, [loadLatestCalibration]);

  // 处理版本恢复回调
  const handleVersionRestore = useCallback(async () => {
    // 版本恢复后重新加载数据
    await loadLatestCalibration();
  }, [loadLatestCalibration]);

  // 确定要显示的数据：校正后的数据优先，否则使用原始数据
  const displayData = useMemo(() => calibratedData || data, [calibratedData, data]);

  // 使用ref跟踪上次调用时的数据，避免重复调用
  const lastDataRef = useRef(null);

  // 当显示的数据变化时，通知父组件重新计算ROI统计
  useEffect(() => {
    // 只在数据真正变化时才调用（比较第一个点来判断是否是同一份数据）
    if (onDataChange && displayData && displayData.length > 0) {
      const currentDataKey = `${displayData.length}_${displayData[0]?.x}_${displayData[0]?.y}`;
      if (lastDataRef.current !== currentDataKey) {
        lastDataRef.current = currentDataKey;
        onDataChange(displayData);
      }
    }
  }, [displayData, onDataChange]);

  // 处理数据并生成Plotly图表数据
  const plotData = useMemo(() => {
    if (!displayData || !Array.isArray(displayData) || displayData.length === 0) {
      return [];
    }

    // 提取x, y, timestamp数据
    const x = displayData.map(d => d.x);
    const y = displayData.map(d => d.y);
    const time = displayData.map(d => d.timestamp || d.time || 0);

    return [
      // 轨迹线
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
        text: time.map((timeValue, i) =>
          `${t('point')} ${i + 1}<br>${t('timeSeconds')}: ${timeValue.toFixed(2)}<br>${t('position')}: (${x[i].toFixed(3)}, ${y[i].toFixed(3)})`
        ),
        hoverinfo: 'text',
        name: t('trajectoryChart')
      },
      // 起点
      {
        type: 'scatter',
        mode: 'markers',
        x: [x[0]],
        y: [y[0]],
        marker: {
          size: 15,
          color: 'green',
          symbol: 'star',
          line: { color: 'white', width: 2 }
        },
        text: [t('startPoint')],
        hoverinfo: 'text',
        name: t('startPoint'),
        showlegend: true
      },
      // 终点
      {
        type: 'scatter',
        mode: 'markers',
        x: [x[x.length - 1]],
        y: [y[y.length - 1]],
        marker: {
          size: 15,
          color: 'red',
          symbol: 'square',
          line: { color: 'white', width: 2 }
        },
        text: [t('endPoint')],
        hoverinfo: 'text',
        name: t('endPoint'),
        showlegend: true
      }
    ];
  }, [displayData, showColorbar, t]);

  // 图表布局配置
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
      paper_bgcolor: 'white',
      images: [],
      shapes: [],
      annotations: []
    };

    // 添加背景图片
    if (roiConfig && roiConfig.background_image && bgOpacity > 0) {
      // 构建完整的图片URL (Plotly需要完整HTTP URL)
      const imageUrl = roiConfig.background_image.startsWith('http')
        ? roiConfig.background_image
        : `${window.location.origin}${roiConfig.background_image}`;

      baseLayout.images = [{
        source: imageUrl,
        xref: 'x',
        yref: 'y',
        x: 0,
        y: 1,
        sizex: 1,
        sizey: 1,
        sizing: 'stretch',
        opacity: bgOpacity,
        layer: 'below'
      }];
    }

    // 添加多层ROI矩形框和标签
    if (roiConfig && roiConfig.regions) {
      const allRegions = [];

      // 收集需要显示的区域
      if (showKeywords && roiConfig.regions.keywords) {
        allRegions.push(...roiConfig.regions.keywords);
      }
      if (showInstructions && roiConfig.regions.instructions) {
        allRegions.push(...roiConfig.regions.instructions);
      }
      if (showBackground && roiConfig.regions.background) {
        allRegions.push(...roiConfig.regions.background);
      }

      // 生成矩形框（Y轴翻转以匹配Plotly坐标系）
      baseLayout.shapes = allRegions.map(roi => {
        // 支持两种格式: normalized_coords数组 或 x/y/width/height对象
        const [x, y, width, height] = roi.normalized_coords || [roi.x, roi.y, roi.width, roi.height];

        return {
          type: 'rect',
          xref: 'x',
          yref: 'y',
          x0: x,
          y0: 1 - y - height,  // Y轴翻转以匹配Plotly坐标系
          x1: x + width,
          y1: 1 - y,  // Y轴翻转以匹配Plotly坐标系
          fillcolor: roi.color || '#999',
          opacity: 0.25,
          line: {
            color: roi.color || '#999',
            width: 2
          }
        };
      });

      // 生成标签（Y轴翻转）
      baseLayout.annotations = allRegions.map(roi => {
        // 支持两种格式: normalized_coords数组 或 x/y/width/height对象
        const [x, y, width, height] = roi.normalized_coords || [roi.x, roi.y, roi.width, roi.height];

        // 清理ROI名称：去掉受试者ID前缀（如 KW_n2q1_3 -> KW_q1_3）
        const cleanName = (roi.name || roi.id).replace(/([A-Z]+_)[nma]\d+q/i, '$1q');

        return {
          x: x + width / 2,
          y: 1 - y - height / 2,  // Y轴翻转以匹配Plotly坐标系
          text: cleanName,
          showarrow: false,
          font: {
            size: 10,
            color: '#333',
            weight: 'bold'
          },
          bgcolor: 'rgba(255, 255, 255, 0.7)',
          borderpad: 2
        };
      });
    }

    return baseLayout;
  }, [title, t, roiConfig, bgOpacity, showKeywords, showInstructions, showBackground]);

  // 图表配置
  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d', 'autoScale2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'gaze_trajectory_enhanced',
      height: 800,
      width: 800,
      scale: 2
    }
  };

  return (
    <div>
      {/* 校正面板 - 默认收起 */}
      {enableCalibration && (
        <Collapse
          style={{ marginBottom: 16 }}
          ghost
          items={[
            {
              key: 'calibration',
              label: '数据校正',
              children: (
                <CalibrationPanel
                  originalData={originalData}
                  group={group}
                  subjectId={subjectId}
                  task={task}
                  currentVersion={currentVersion}
                  onPreview={handleCalibrationPreview}
                  onSaveComplete={handleSaveComplete}
                  onVersionRestore={handleVersionRestore}
                />
              )
            }
          ]}
        />
      )}

      {/* 控制面板 */}
      {roiConfig && (
        <div style={{
          marginBottom: 16,
          padding: 12,
          background: '#fafafa',
          borderRadius: 4,
          border: '1px solid #d9d9d9'
        }}>
          <div style={{ display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
            {/* 背景图片透明度 */}
            {roiConfig.background_image && (
              <div style={{ flex: '1 1 200px', minWidth: 200 }}>
                <div style={{ marginBottom: 4, fontWeight: 500 }}>
                  {t('backgroundOpacity') || '背景透明度'}: {(bgOpacity * 100).toFixed(0)}%
                </div>
                <Slider
                  min={0}
                  max={1}
                  step={0.1}
                  value={bgOpacity}
                  onChange={setBgOpacity}
                  marks={{ 0: '0%', 0.5: '50%', 1: '100%' }}
                />
              </div>
            )}

            {/* ROI图层控制 */}
            <div style={{ flex: '1 1 auto', display: 'flex', gap: 16, alignItems: 'center' }}>
              {roiConfig.regions?.keywords && (
                <div>
                  <Switch
                    checked={showKeywords}
                    onChange={setShowKeywords}
                    size="small"
                  />
                  <span style={{ marginLeft: 8 }}>{t('roiKeywords') || '关键词'}</span>
                </div>
              )}
              {roiConfig.regions?.instructions && (
                <div>
                  <Switch
                    checked={showInstructions}
                    onChange={setShowInstructions}
                    size="small"
                  />
                  <span style={{ marginLeft: 8 }}>{t('roiInstructions') || '指示语'}</span>
                </div>
              )}
              {roiConfig.regions?.background && (
                <div>
                  <Switch
                    checked={showBackground}
                    onChange={setShowBackground}
                    size="small"
                  />
                  <span style={{ marginLeft: 8 }}>{t('roiBackground') || '背景区域'}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 轨迹图 */}
      <PlotlyChart
        data={plotData}
        layout={layout}
        config={config}
        loading={loading}
        style={{ height: '600px', ...style }}
      />
    </div>
  );
};

export default GazeTrajectoryChartEnhanced;
