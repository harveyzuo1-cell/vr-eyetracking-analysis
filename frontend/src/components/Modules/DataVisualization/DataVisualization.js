import React, { useState, useEffect } from 'react';
import useAppStore from '../../../store/useAppStore';
import { apiService } from '../../../services/api';
import { languageTexts } from '../../../utils/languages';
import DataList from './DataList';
import VisualizationDisplay from './VisualizationDisplay';
import VisualizationControls from './VisualizationControls';
import GroupFilter from './GroupFilter';
import QuestionFilter from './QuestionFilter';
import toast from 'react-hot-toast';
import './DataVisualization.css';

const DataVisualization = () => {
  const { 
    currentLanguage, 
    currentGroup, 
    currentQuestion,
    currentVisualization,
    setCurrentVisualization,
    getFilteredData,
    isLoading 
  } = useAppStore();
  
  const texts = languageTexts[currentLanguage];
  const [visualizing, setVisualizing] = useState(false);
  const [visParams, setVisParams] = useState({
    fixationSize: 8,
    trajectoryWidth: 2,
    pointSize: 3,
    trajectoryStyle: 'solid',
    showFixations: true,
    showSaccades: true,
    roiHighlight: true
  });

  const filteredData = getFilteredData();

  const handleDataSelect = async (groupType, dataId) => {
    try {
      setVisualizing(true);
      
      const response = await apiService.generateVisualization(
        groupType, 
        dataId, 
        visParams
      );
      
      setCurrentVisualization({
        groupType,
        dataId,
        data: response,
        params: visParams
      });
      
      toast.success('可视化生成成功');
    } catch (error) {
      console.error('可视化生成失败:', error);
      toast.error('可视化生成失败: ' + error.message);
    } finally {
      setVisualizing(false);
    }
  };

  const handleUpdateVisualization = async () => {
    if (!currentVisualization) return;
    
    try {
      setVisualizing(true);
      
      const response = await apiService.generateVisualization(
        currentVisualization.groupType,
        currentVisualization.dataId,
        visParams
      );
      
      setCurrentVisualization({
        ...currentVisualization,
        data: response,
        params: visParams
      });
      
      toast.success('可视化更新成功');
    } catch (error) {
      console.error('可视化更新失败:', error);
      toast.error('可视化更新失败: ' + error.message);
    } finally {
      setVisualizing(false);
    }
  };

  return (
    <div className="module-container data-visualization-module">
      {/* 模块标题 */}
      <div className="module-header">
        <h2 className="module-title">
          <i className="fas fa-chart-line"></i>
          {texts.dataVisualization}
        </h2>
        <p className="module-subtitle">
          {texts.selectDataSubtitle}
        </p>
      </div>

      <div className="visualization-layout">
        {/* 左侧控制面板 */}
        <div className="visualization-sidebar">
          {/* 数据过滤器 */}
          <div className="filter-section">
            <h5 className="filter-title">
              <i className="fas fa-filter"></i>
              数据过滤
            </h5>
            
            <GroupFilter />
            <QuestionFilter />
          </div>

          {/* 数据列表 */}
          <div className="data-list-section">
            <h5 className="list-title">
              <i className="fas fa-list"></i>
              {texts.dataList}
              <span className="data-count">({filteredData.length})</span>
            </h5>
            
            <DataList 
              data={filteredData}
              onDataSelect={handleDataSelect}
              isLoading={isLoading}
              selectedDataId={currentVisualization?.dataId}
            />
          </div>

          {/* 可视化控制 */}
          {currentVisualization && (
            <div className="controls-section">
              <h5 className="controls-title">
                <i className="fas fa-sliders-h"></i>
                {texts.visControls}
              </h5>
              
              <VisualizationControls
                params={visParams}
                onChange={setVisParams}
                onUpdate={handleUpdateVisualization}
                isUpdating={visualizing}
              />
            </div>
          )}
        </div>

        {/* 右侧可视化显示区域 */}
        <div className="visualization-content">
          <VisualizationDisplay
            visualization={currentVisualization}
            isGenerating={visualizing}
          />
        </div>
      </div>
    </div>
  );
};

export default DataVisualization;