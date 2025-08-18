import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './FeatureExtraction.css';

const FeatureExtraction = () => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  return (
    <div className="module-container feature-extraction-module">
      <div className="module-header">
        <h2 className="module-title">
          <i className="fas fa-brain"></i>
          {texts.featureExtraction}
        </h2>
        <p className="module-subtitle">
          多数据源特征整合、批量特征提取和数据源状态检查
        </p>
      </div>

      <div className="module-content">
        <div className="module-loading">
          <div className="loading-spinner"></div>
          <h4>综合特征提取模块开发中...</h4>
          <p>此模块将包含多维度特征的批量提取和整合功能</p>
        </div>
      </div>
    </div>
  );
};

export default FeatureExtraction;