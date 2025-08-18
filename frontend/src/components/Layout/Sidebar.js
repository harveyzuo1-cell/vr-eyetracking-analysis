import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import useAppStore from '../../store/useAppStore';
import { languageTexts } from '../../utils/languages';
import './Sidebar.css';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const { 
    sidebarExpanded, 
    setSidebarExpanded, 
    currentLanguage, 
    setCurrentView 
  } = useAppStore();
  
  const texts = languageTexts[currentLanguage];

  const menuItems = [
    {
      path: '/visualization',
      icon: 'fas fa-chart-line',
      labelKey: 'dataVisualization',
      label: texts.dataVisualization || '数据可视化'
    },
    {
      path: '/import',
      icon: 'fas fa-upload',
      labelKey: 'dataImport',
      label: texts.dataImport || '数据导入'
    },
    {
      path: '/rqa-analysis',
      icon: 'fas fa-project-diagram',
      labelKey: 'rqaAnalysis',
      label: texts.rqaAnalysis || 'RQA分析'
    },
    {
      path: '/event-analysis',
      icon: 'fas fa-table',
      labelKey: 'eventAnalysis',
      label: texts.eventAnalysis || '事件分析'
    },
    {
      path: '/rqa-pipeline',
      icon: 'fas fa-cogs',
      labelKey: 'rqaPipeline',
      label: texts.rqaPipeline || 'RQA分析流程'
    },
    {
      path: '/feature-extraction',
      icon: 'fas fa-brain',
      labelKey: 'featureExtraction',
      label: texts.featureExtraction || '综合特征提取'
    },
    {
      path: '/data-organization',
      icon: 'fas fa-database',
      labelKey: 'dataOrganization',
      label: texts.dataOrganization || '数据整理'
    }
  ];

  const handleNavigation = (path, view) => {
    navigate(path);
    setCurrentView(view);
    
    // 在移动端点击后收缩侧边栏
    if (window.innerWidth <= 768) {
      setSidebarExpanded(false);
    }
  };

  const toggleSidebar = () => {
    setSidebarExpanded(!sidebarExpanded);
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <>
      <div className={`sidebar ${sidebarExpanded ? 'expanded' : ''}`}>
        <button 
          className="sidebar-toggle"
          onClick={toggleSidebar}
          title={sidebarExpanded ? "收缩侧边栏" : "展开侧边栏"}
        >
          <i className={`fas ${sidebarExpanded ? 'fa-times' : 'fa-chevron-right'}`}></i>
        </button>
        
        <div className="sidebar-content">
          <ul className="sidebar-nav">
            {menuItems.map((item, index) => (
              <li key={item.path}>
                <div 
                  className={`sidebar-nav-item ${isActive(item.path) ? 'active' : ''}`}
                  onClick={() => handleNavigation(item.path, item.labelKey)}
                  title={!sidebarExpanded ? item.label : ''}
                >
                  <i className={`${item.icon} sidebar-nav-icon`}></i>
                  <span className="sidebar-nav-text">
                    {item.label}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
      
      {/* 移动端遮罩层 */}
      {sidebarExpanded && (
        <div 
          className="sidebar-overlay"
          onClick={() => setSidebarExpanded(false)}
        ></div>
      )}
    </>
  );
};

export default Sidebar;