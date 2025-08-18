import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './DataOrganization.css';

const DataOrganization = () => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  return (
    <div className="module-container data-organization-module">
      <div className="module-header">
        <h2 className="module-title">
          <i className="fas fa-database"></i>
          {texts.dataOrganization}
        </h2>
        <p className="module-subtitle">
          数据管理、组织和维护功能
        </p>
      </div>

      <div className="module-content">
        <div className="module-loading">
          <div className="loading-spinner"></div>
          <h4>数据整理模块开发中...</h4>
          <p>此模块将包含数据管理和组织功能</p>
        </div>
      </div>
    </div>
  );
};

export default DataOrganization;