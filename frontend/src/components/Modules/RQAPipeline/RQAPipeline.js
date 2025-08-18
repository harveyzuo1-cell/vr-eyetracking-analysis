import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './RQAPipeline.css';

const RQAPipeline = () => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  return (
    <div className="module-container rqa-pipeline-module">
      <div className="module-header">
        <h2 className="module-title">
          <i className="fas fa-cogs"></i>
          {texts.rqaPipeline}
        </h2>
        <p className="module-subtitle">
          完整的5步RQA分析流程：计算→合并→特征补充→统计分析→可视化
        </p>
      </div>

      <div className="module-content">
        <div className="module-loading">
          <div className="loading-spinner"></div>
          <h4>RQA分析流程模块开发中...</h4>
          <p>此模块将包含参数化的完整RQA分析管道</p>
        </div>
      </div>
    </div>
  );
};

export default RQAPipeline;