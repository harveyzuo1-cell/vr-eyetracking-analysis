import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './RQAAnalysis.css';

const RQAAnalysis = () => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  return (
    <div className="module-container rqa-analysis-module">
      <div className="module-header">
        <h2 className="module-title">
          <i className="fas fa-project-diagram"></i>
          {texts.rqaAnalysis}
        </h2>
        <p className="module-subtitle">
          递归量化分析，支持1D/2D模式和实时参数调整
        </p>
      </div>

      <div className="module-content">
        <div className="module-loading">
          <div className="loading-spinner"></div>
          <h4>RQA分析模块开发中...</h4>
          <p>此模块将包含完整的递归量化分析功能</p>
        </div>
      </div>
    </div>
  );
};

export default RQAAnalysis;