import React from 'react';
import useAppStore from '../../../store/useAppStore';
import { languageTexts } from '../../../utils/languages';
import './GroupFilter.css';

const GroupFilter = () => {
  const { 
    currentGroup, 
    setCurrentGroup, 
    currentLanguage,
    getGroupStats 
  } = useAppStore();
  
  const texts = languageTexts[currentLanguage];
  const stats = getGroupStats();

  const groupOptions = [
    {
      value: 'all',
      label: texts.all,
      count: stats?.total || 0,
      color: '#6b7280'
    },
    {
      value: 'control',
      label: texts.controlGroup,
      count: stats?.control || 0,
      color: '#22c55e'
    },
    {
      value: 'mci',
      label: texts.mciGroup,
      count: stats?.mci || 0,
      color: '#f97316'
    },
    {
      value: 'ad',
      label: texts.adGroup,
      count: stats?.ad || 0,
      color: '#ef4444'
    }
  ];

  return (
    <div className="group-filter">
      <div className="filter-title">
        <i className="fas fa-users"></i>
        {texts.researchGroups}
      </div>
      
      <div className="group-options">
        {groupOptions.map((option) => (
          <button
            key={option.value}
            className={`group-option ${currentGroup === option.value ? 'active' : ''}`}
            onClick={() => setCurrentGroup(option.value)}
            style={{ '--group-color': option.color }}
          >
            <div className="group-option-content">
              <div className="group-label">{option.label}</div>
              <div className="group-count">{option.count}</div>
            </div>
            <div className="group-indicator"></div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default GroupFilter;