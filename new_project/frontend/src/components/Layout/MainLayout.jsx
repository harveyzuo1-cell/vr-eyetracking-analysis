/**
 * 主布局组件
 */
import React, { useState } from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  EyeOutlined,
  DashboardOutlined,
  LineChartOutlined,
  ImportOutlined,
  FundOutlined,
  BulbOutlined,
  DatabaseOutlined,
  MergeCellsOutlined,
  ExperimentOutlined,
  RobotOutlined,
  RadarChartOutlined,
  UploadOutlined,
  SettingOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import LanguageSwitcher from '../LanguageSwitcher';
import './MainLayout.css';

const { Header, Content, Sider } = Layout;

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 菜单项配置
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '首页',
    },
    {
      key: '/module00',
      icon: <UploadOutlined />,
      label: '模块0: 数据管理中心',
    },
    {
      key: '/module01',
      icon: <LineChartOutlined />,
      label: '模块1: 数据可视化',
    },
    {
      key: '/module02',
      icon: <ImportOutlined />,
      label: '模块2: 数据导入',
    },
    {
      key: '/module03',
      icon: <FundOutlined />,
      label: '模块3: RQA分析',
    },
    {
      key: '/module04',
      icon: <BulbOutlined />,
      label: '模块4: 事件检测',
    },
    {
      key: '/module05',
      icon: <DatabaseOutlined />,
      label: '模块5: RQA批处理',
    },
    {
      key: '/module06',
      icon: <MergeCellsOutlined />,
      label: '模块6: 特征提取',
    },
    {
      key: '/module07',
      icon: <ExperimentOutlined />,
      label: '模块7: 数据整合',
    },
    {
      key: '/module08',
      icon: <RadarChartOutlined />,
      label: '模块8: MMSE分析',
    },
    {
      key: '/module09',
      icon: <RobotOutlined />,
      label: '模块9: 机器学习',
    },
    {
      key: '/module10',
      icon: <EyeOutlined />,
      label: '模块10: Eye-Index',
    },
    {
      key: '/moduleEX',
      icon: <SettingOutlined />,
      label: 'ModuleEX: ROI配置',
    },
    {
      key: '/moduleEX2',
      icon: <ExportOutlined />,
      label: 'ModuleEX2: 数据导出',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={250}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div className="logo">
          <EyeOutlined style={{ fontSize: '24px', color: '#fff' }} />
          {!collapsed && <span>VR眼动分析</span>}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      {/* 主体内容区域 */}
      <Layout style={{ marginLeft: collapsed ? 80 : 250, transition: 'all 0.2s' }}>
        {/* 顶部导航栏 */}
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            position: 'sticky',
            top: 0,
            zIndex: 1,
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
          }}
        >
          <div style={{ fontSize: '18px', fontWeight: 600 }}>
            VR眼球追踪数据分析平台 v2.0.0
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <div style={{ color: '#666' }}>
              认知障碍早期筛查研究
            </div>
            <LanguageSwitcher />
          </div>
        </Header>

        {/* 内容区域 */}
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
