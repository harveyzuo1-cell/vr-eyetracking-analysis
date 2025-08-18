import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './DataList.css';

const DataList = ({ data, onDataSelect, isLoading, selectedDataId }) => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  const getGroupType = (dataId) => {
    if (dataId.startsWith('ad')) return 'ad';
    if (dataId.startsWith('m')) return 'mci';
    return 'control';
  };

  const getGroupPrefix = (dataId) => {
    if (dataId.startsWith('ad')) return 'AD';
    if (dataId.startsWith('m')) return 'MCI';
    return 'Control';
  };

  if (isLoading) {
    return (
      <div className="data-list-loading">
        <div className="loading-spinner"></div>
        <div>{texts.loading}</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="data-list-empty">
        <i className="fas fa-inbox"></i>
        <div>{texts.noData}</div>
      </div>
    );
  }

  return (
    <div className="data-list">
      {data.map((item) => {
        const groupType = getGroupType(item.data_id);
        const groupPrefix = getGroupPrefix(item.data_id);
        const isSelected = selectedDataId === item.data_id;
        
        return (
          <div
            key={item.data_id}
            className={`data-item ${isSelected ? 'selected' : ''}`}
            onClick={() => onDataSelect(groupType, item.data_id)}
          >
            <div className="data-item-content">
              <div className="data-item-header">
                <div className="data-item-name">
                  {groupPrefix} - {item.display_name}
                </div>
                <span className={`question-badge q${item.question_num}`}>
                  Q{item.question_num}
                </span>
              </div>
              
              <div className="data-item-filename">
                {item.filename}
              </div>
              
              {item.file_info && (
                <div className="data-item-stats">
                  <span className="stat-item">
                    <i className="fas fa-clock"></i>
                    {(item.file_info.duration_ms / 1000).toFixed(1)}s
                  </span>
                  <span className="stat-item">
                    <i className="fas fa-table"></i>
                    {item.file_info.rows}
                  </span>
                </div>
              )}
            </div>
            
            <div className="data-item-indicator">
              <i className="fas fa-chevron-right"></i>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DataList;