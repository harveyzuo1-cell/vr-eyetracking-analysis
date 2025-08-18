import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Layout from './components/Layout/Layout';
import DataVisualization from './components/Modules/DataVisualization/DataVisualization';
import DataImport from './components/Modules/DataImport/DataImport';
import RQAAnalysis from './components/Modules/RQAAnalysis/RQAAnalysis';
import EventAnalysis from './components/Modules/EventAnalysis/EventAnalysis';
import RQAPipeline from './components/Modules/RQAPipeline/RQAPipeline';
import FeatureExtraction from './components/Modules/FeatureExtraction/FeatureExtraction';
import DataOrganization from './components/Modules/DataOrganization/DataOrganization';

import './App.css';

function App() {
  return (
    <div className="App">
      <Layout>
        <Routes>
          {/* 默认重定向到数据可视化 */}
          <Route path="/" element={<Navigate to="/visualization" replace />} />
          
          {/* 7个主要模块路由 */}
          <Route path="/visualization" element={<DataVisualization />} />
          <Route path="/import" element={<DataImport />} />
          <Route path="/rqa-analysis" element={<RQAAnalysis />} />
          <Route path="/event-analysis" element={<EventAnalysis />} />
          <Route path="/rqa-pipeline" element={<RQAPipeline />} />
          <Route path="/feature-extraction" element={<FeatureExtraction />} />
          <Route path="/data-organization" element={<DataOrganization />} />
          
          {/* 404页面 */}
          <Route path="*" element={<Navigate to="/visualization" replace />} />
        </Routes>
      </Layout>
    </div>
  );
}

export default App;