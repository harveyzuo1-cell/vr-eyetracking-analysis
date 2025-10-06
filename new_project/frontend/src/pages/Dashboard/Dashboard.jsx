/**
 * Dashboard首页
 */
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Tag } from 'antd';
import {
  DatabaseOutlined,
  TeamOutlined,
  ExperimentOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { dataService } from '../../services/dataService';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [systemInfo, setSystemInfo] = useState(null);

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      setLoading(true);
      const result = await dataService.getSystemInfo();
      setSystemInfo(result.data);
    } catch (error) {
      console.error('加载系统信息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" spinning={true} tip="加载中...">
          <div style={{ padding: '50px' }} />
        </Spin>
      </div>
    );
  }

  return (
    <div>
      {/* 欢迎信息 */}
      <Card style={{ marginBottom: 24 }}>
        <h1 style={{ marginBottom: 16 }}>
          <RocketOutlined style={{ marginRight: 8 }} />
          欢迎使用VR眼球追踪数据分析平台
        </h1>
        <p style={{ fontSize: 16, color: '#666', marginBottom: 0 }}>
          基于VR环境的眼动数据分析，用于认知障碍早期筛查研究
        </p>
      </Card>

      {/* 系统信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平台版本"
              value={systemInfo?.version || 'v2.0.0'}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="运行环境"
              value={systemInfo?.environment || 'development'}
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="数据组别"
              value={3}
              suffix="组"
              prefix={<TeamOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="green">Control</Tag>
              <Tag color="orange">MCI</Tag>
              <Tag color="red">AD</Tag>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="功能模块"
              value={10}
              suffix="个"
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 功能模块卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card
            title="数据管理"
            extra={<DatabaseOutlined style={{ fontSize: 20 }} />}
            hoverable
          >
            <p>数据导入、预处理、校准等功能</p>
            <div style={{ marginTop: 16 }}>
              <Tag color="blue">模块1</Tag>
              <Tag color="blue">模块2</Tag>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card
            title="RQA分析"
            extra={<ExperimentOutlined style={{ fontSize: 20 }} />}
            hoverable
          >
            <p>递归量化分析，提取眼动数据的非线性动力学特征</p>
            <div style={{ marginTop: 16 }}>
              <Tag color="cyan">模块3</Tag>
              <Tag color="cyan">模块5</Tag>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card
            title="机器学习"
            extra={<RocketOutlined style={{ fontSize: 20 }} />}
            hoverable
          >
            <p>基于眼动特征的认知障碍预测与分类</p>
            <div style={{ marginTop: 16 }}>
              <Tag color="purple">模块9</Tag>
              <Tag color="purple">模块10</Tag>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 开发进度 */}
      <Card
        title={
          <>
            <ClockCircleOutlined style={{ marginRight: 8 }} />
            开发进度
          </>
        }
        style={{ marginTop: 24 }}
      >
        <Alert
          message="第2阶段：前端框架搭建"
          description={
            <div>
              <p>当前已完成：</p>
              <ul>
                <li>✅ React + Vite项目创建</li>
                <li>✅ Ant Design + Plotly.js集成</li>
                <li>✅ 主布局组件（侧边栏、导航栏）</li>
                <li>✅ API服务封装（Axios）</li>
                <li>✅ Dashboard首页</li>
                <li>⏳ 各功能模块开发中...</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
        />
      </Card>

      {/* 快速开始 */}
      <Card
        title={
          <>
            <RocketOutlined style={{ marginRight: 8 }} />
            快速开始
          </>
        }
        style={{ marginTop: 24 }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <h4>后端服务</h4>
            <p>后端Flask服务运行在：<code>http://127.0.0.1:9090</code></p>
            <p>API文档：<a href="http://127.0.0.1:9090/api/health" target="_blank" rel="noreferrer">健康检查</a></p>
          </Col>
          <Col xs={24} md={12}>
            <h4>前端服务</h4>
            <p>前端React应用运行在：<code>http://localhost:5173</code></p>
            <p>使用左侧导航栏选择功能模块开始使用</p>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default Dashboard;
