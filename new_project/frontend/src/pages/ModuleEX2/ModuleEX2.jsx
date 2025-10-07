/**
 * ModuleEX2: 数据导出与固化
 *
 * 功能：
 * - 导出校准后的眼动数据
 * - 导出ROI配置
 * - 导出受试者+MMSE评分
 * - 统一打包导出
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Button,
  Space,
  Typography,
  Divider,
  message
} from 'antd';
import {
  ExportOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  AimOutlined,
  UserOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import EyetrackingExport from '../../components/ModuleEX2/EyetrackingExport';
import ROIExport from '../../components/ModuleEX2/ROIExport';
import SubjectsExport from '../../components/ModuleEX2/SubjectsExport';
import UnifiedExport from '../../components/ModuleEX2/UnifiedExport';
import ExportHistory from '../../components/ModuleEX2/ExportHistory';

const { Title, Paragraph } = Typography;
const { TabPane } = Tabs;

const ModuleEX2 = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('unified');

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <Card bordered={false} style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Title level={2} style={{ margin: 0 }}>
            <ExportOutlined style={{ marginRight: 12 }} />
            数据导出与固化 (ModuleEX2)
          </Title>
          <Paragraph type="secondary" style={{ margin: 0 }}>
            固化Module00-02和ModuleEX的处理结果，支持CSV/JSON/Excel/ZIP格式导出
          </Paragraph>
        </Space>
      </Card>

      {/* 功能标签页 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="large"
        >
          {/* 统一导出 */}
          <TabPane
            tab={
              <span>
                <DatabaseOutlined />
                统一导出
              </span>
            }
            key="unified"
          >
            <UnifiedExport />
          </TabPane>

          {/* 眼动数据导出 */}
          <TabPane
            tab={
              <span>
                <AimOutlined />
                眼动数据
              </span>
            }
            key="eyetracking"
          >
            <EyetrackingExport />
          </TabPane>

          {/* ROI配置导出 */}
          <TabPane
            tab={
              <span>
                <FileTextOutlined />
                ROI配置
              </span>
            }
            key="roi"
          >
            <ROIExport />
          </TabPane>

          {/* 受试者+MMSE导出 */}
          <TabPane
            tab={
              <span>
                <UserOutlined />
                受试者+MMSE
              </span>
            }
            key="subjects"
          >
            <SubjectsExport />
          </TabPane>

          {/* 导出历史 */}
          <TabPane
            tab={
              <span>
                <FileTextOutlined />
                导出历史
              </span>
            }
            key="history"
          >
            <ExportHistory />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default ModuleEX2;
