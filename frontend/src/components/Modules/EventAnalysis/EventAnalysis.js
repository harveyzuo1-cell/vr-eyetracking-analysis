import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './EventAnalysis.css';

const EventAnalysis = () => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  return (
    <div className="module-container event-analysis-module">
      <div className="module-header">
        <h2 className="module-title">
          <i className="fas fa-table"></i>
          {texts.eventAnalysis}
        </h2>
        <p className="module-subtitle">
          眼动事件提取、ROI区域统计和事件序列分析
        </p>
      </div>

      <div className="module-content">
        <div className="module-loading">
          <div className="loading-spinner"></div>
          <h4>事件分析模块开发中...</h4>
          <p>此模块将包含注视、扫视等眼动事件的提取和统计功能</p>
        </div>
      </div>
    </div>
  );
};

export default EventAnalysis;