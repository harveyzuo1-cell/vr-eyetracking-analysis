import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './VisualizationDisplay.css';

const VisualizationDisplay = ({ visualization, isGenerating }) => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  if (isGenerating) {
    return (
      <div className="visualization-loading">
        <div className="loading-spinner"></div>
        <h4>{texts.generatingVis}</h4>
        <p>正在生成专业的眼动轨迹可视化分析...</p>
      </div>
    );
  }

  if (!visualization) {
    return (
      <div className="visualization-empty">
        <i className="fas fa-chart-line"></i>
        <h4>{texts.selectDataTitle}</h4>
        <p>{texts.selectDataSubtitle}</p>
      </div>
    );
  }

  const { data, dataId, groupType } = visualization;

  return (
    <div className="visualization-display">
      {/* 可视化标题 */}
      <div className="visualization-header">
        <h4 className="visualization-title">
          <i className="fas fa-eye"></i>
          {texts.eyeTrackingVis} - {dataId}
        </h4>
        <div className="visualization-meta">
          <span className={`group-badge ${groupType}`}>
            {groupType.toUpperCase()}
          </span>
        </div>
      </div>

      {/* 可视化图像 */}
      <div className="visualization-image-container">
        {data.image && (
          <img
            src={`data:image/png;base64,${data.image}`}
            alt={`眼动轨迹可视化 - ${dataId}`}
            className="visualization-image"
            onClick={() => openImageModal(data.image, `眼动轨迹 - ${dataId}`)}
          />
        )}
      </div>

      {/* 统计信息 */}
      {data.statistics && (
        <div className="visualization-stats">
          <h5 className="stats-title">
            <i className="fas fa-chart-bar"></i>
            {texts.overallStats}
          </h5>
          
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">{texts.duration}</div>
              <div className="stat-value">
                {(data.statistics.duration_ms / 1000).toFixed(1)}s
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-label">{texts.totalFixations}</div>
              <div className="stat-value">
                {data.statistics.total_fixations || 0}
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-label">{texts.totalSaccades}</div>
              <div className="stat-value">
                {data.statistics.total_saccades || 0}
              </div>
            </div>
            
            {data.statistics.avg_fixation_duration && (
              <div className="stat-card">
                <div className="stat-label">{texts.avgFixationDuration}</div>
                <div className="stat-value">
                  {data.statistics.avg_fixation_duration.toFixed(0)}ms
                </div>
              </div>
            )}
          </div>

          {/* ROI统计 */}
          {data.statistics.roi_statistics && (
            <div className="roi-stats">
              <h6 className="roi-stats-title">{texts.roiStatistics}</h6>
              <div className="roi-stats-grid">
                {Object.entries(data.statistics.roi_statistics).map(([roi, stats]) => (
                  <div key={roi} className="roi-stat-card">
                    <div className="roi-name">{roi}</div>
                    <div className="roi-details">
                      <span>注视: {stats.count || 0}次</span>
                      <span>时长: {((stats.duration || 0) / 1000).toFixed(1)}s</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 图片放大函数（临时实现，后续可以用Modal组件）
const openImageModal = (imageSrc, title) => {
  const modal = document.createElement('div');
  modal.className = 'image-modal-overlay';
  modal.innerHTML = `
    <div class="image-modal-content">
      <div class="image-modal-header">
        <h5>${title}</h5>
        <button class="image-modal-close">&times;</button>
      </div>
      <div class="image-modal-body">
        <img src="data:image/png;base64,${imageSrc}" alt="${title}" />
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // 关闭模态框
  const closeModal = () => {
    document.body.removeChild(modal);
    document.body.style.overflow = 'auto';
  };
  
  modal.querySelector('.image-modal-close').onclick = closeModal;
  modal.onclick = (e) => {
    if (e.target === modal) closeModal();
  };
  
  document.body.style.overflow = 'hidden';
  
  // ESC键关闭
  const handleEsc = (e) => {
    if (e.key === 'Escape') {
      closeModal();
      document.removeEventListener('keydown', handleEsc);
    }
  };
  document.addEventListener('keydown', handleEsc);
};

export default VisualizationDisplay;