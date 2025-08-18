import React from 'react';
import useAppStore from '../../store/useAppStore';
import LanguageSwitch from '../Common/LanguageSwitch';
import { languageTexts } from '../../utils/languages';
import './Header.css';

const Header = () => {
  const { 
    currentLanguage, 
    toggleSidebar,
    getGroupStats 
  } = useAppStore();
  
  const texts = languageTexts[currentLanguage];
  const stats = getGroupStats();

  const handleRestart = () => {
    if (window.confirm(texts.confirmRestart || '确定要重启应用程序吗？')) {
      window.location.reload();
    }
  };

  return (
    <div className="header-banner">
      <div className="header-left">
        <button 
          className="sidebar-toggle-btn"
          onClick={toggleSidebar}
          title="切换侧边栏"
        >
          <i className="fas fa-bars"></i>
        </button>
        <div className="header-title-section">
          <h1>
            <i className="fas fa-eye"></i>
            {texts.title}
          </h1>
          <p className="subtitle">{texts.subtitle}</p>
        </div>
      </div>
      
      <div className="header-controls">
        {/* 数据统计 */}
        <div className="header-stats">
          <div className="number">{stats?.total || 0}</div>
          <div className="label">{texts.totalData}</div>
        </div>
        
        {/* 组别统计 */}
        <div className="header-stats">
          <div className="number">{stats?.control || 0}</div>
          <div className="label">{texts.controlGroup}</div>
        </div>
        
        <div className="header-stats">
          <div className="number">{stats?.mci || 0}</div>
          <div className="label">{texts.mciGroup}</div>
        </div>
        
        <div className="header-stats">
          <div className="number">{stats?.ad || 0}</div>
          <div className="label">{texts.adGroup}</div>
        </div>
        
        {/* 语言切换 */}
        <LanguageSwitch />
        
        {/* 重启按钮 */}
        <button 
          className="restart-btn"
          onClick={handleRestart}
          title={texts.restart}
        >
          <i className="fas fa-redo-alt"></i>
          {texts.restart}
        </button>
      </div>
    </div>
  );
};

export default Header;