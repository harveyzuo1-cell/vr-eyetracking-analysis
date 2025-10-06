/**
 * App主组件 - 配置路由
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard/Dashboard';
import Module00 from './pages/Module00';
import Module01 from './pages/Module01/Module01';
import Module02 from './pages/Module02/Module02';
import ModuleEX from './pages/ModuleEX';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="module00" element={<Module00 />} />
            <Route path="module01" element={<Module01 />} />
            <Route path="module02" element={<Module02 />} />
            <Route path="module03" element={<div>模块3开发中...</div>} />
            <Route path="module04" element={<div>模块4开发中...</div>} />
            <Route path="module05" element={<div>模块5开发中...</div>} />
            <Route path="module06" element={<div>模块6开发中...</div>} />
            <Route path="module07" element={<div>模块7开发中...</div>} />
            <Route path="module08" element={<div>模块8开发中...</div>} />
            <Route path="module09" element={<div>模块9开发中...</div>} />
            <Route path="module10" element={<div>模块10开发中...</div>} />
            <Route path="moduleEX" element={<ModuleEX />} />
          </Route>
        </Routes>
      </Router>
    </ConfigProvider>
  );
}

export default App;
