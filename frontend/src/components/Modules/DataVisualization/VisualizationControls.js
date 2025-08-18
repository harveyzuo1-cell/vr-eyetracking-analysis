import React from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './VisualizationControls.css';

const VisualizationControls = ({ params, onChange, onUpdate, isUpdating }) => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];

  const handleParamChange = (key, value) => {
    onChange({
      ...params,
      [key]: value
    });
  };

  const handleToggleChange = (key) => {
    onChange({
      ...params,
      [key]: !params[key]
    });
  };

  return (
    <div className="visualization-controls">
      {/* 尺寸控制 */}
      <div className="control-group">
        <label className="control-label">
          <i className="fas fa-dot-circle"></i>
          {texts.fixationSize}
        </label>
        <div className="control-input-group">
          <input
            type="range"
            min="3"
            max="15"
            value={params.fixationSize}
            onChange={(e) => handleParamChange('fixationSize', parseInt(e.target.value))}
            className="control-slider"
          />
          <span className="control-value">{params.fixationSize}</span>
        </div>
      </div>

      <div className="control-group">
        <label className="control-label">
          <i className="fas fa-minus"></i>
          {texts.trajectoryWidth}
        </label>
        <div className="control-input-group">
          <input
            type="range"
            min="1"
            max="8"
            value={params.trajectoryWidth}
            onChange={(e) => handleParamChange('trajectoryWidth', parseInt(e.target.value))}
            className="control-slider"
          />
          <span className="control-value">{params.trajectoryWidth}</span>
        </div>
      </div>

      <div className="control-group">
        <label className="control-label">
          <i className="fas fa-circle"></i>
          {texts.pointSize}
        </label>
        <div className="control-input-group">
          <input
            type="range"
            min="1"
            max="10"
            value={params.pointSize}
            onChange={(e) => handleParamChange('pointSize', parseInt(e.target.value))}
            className="control-slider"
          />
          <span className="control-value">{params.pointSize}</span>
        </div>
      </div>

      {/* 样式控制 */}
      <div className="control-group">
        <label className="control-label">
          <i className="fas fa-paint-brush"></i>
          {texts.trajectoryStyle}
        </label>
        <select
          value={params.trajectoryStyle}
          onChange={(e) => handleParamChange('trajectoryStyle', e.target.value)}
          className="control-select"
        >
          <option value="solid">{texts.solidLine}</option>
          <option value="dashed">{texts.dashedLine}</option>
          <option value="dotted">{texts.dottedLine}</option>
        </select>
      </div>

      {/* 开关控制 */}
      <div className="control-group">
        <label className="control-label">显示选项</label>
        
        <div className="control-toggles">
          <label className="control-toggle">
            <input
              type="checkbox"
              checked={params.showFixations}
              onChange={() => handleToggleChange('showFixations')}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">显示注视点</span>
          </label>
          
          <label className="control-toggle">
            <input
              type="checkbox"
              checked={params.showSaccades}
              onChange={() => handleToggleChange('showSaccades')}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">显示扫视</span>
          </label>
          
          <label className="control-toggle">
            <input
              type="checkbox"
              checked={params.roiHighlight}
              onChange={() => handleToggleChange('roiHighlight')}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">ROI高亮</span>
          </label>
        </div>
      </div>

      {/* 更新按钮 */}
      <div className="control-actions">
        <button
          onClick={onUpdate}
          disabled={isUpdating}
          className={`update-btn ${isUpdating ? 'updating' : ''}`}
        >
          {isUpdating ? (
            <>
              <div className="loading-spinner small"></div>
              更新中...
            </>
          ) : (
            <>
              <i className="fas fa-sync-alt"></i>
              {texts.updateVis}
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default VisualizationControls;