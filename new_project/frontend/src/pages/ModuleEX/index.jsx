/**
 * ModuleEX - ROI配置管理中心
 * 扩展模块：ROI可视化配置工具主页面
 */
import React, { useState, useEffect } from 'react';
import { Card, Tabs, message, Spin } from 'antd';
import { SettingOutlined, PictureOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

import ROIEditor from '../../components/ModuleEX/ROIEditor';

const ModuleEX = () => {
  const { t } = useTranslation(['moduleEX', 'common']);
  const [loading, setLoading] = useState(false);

  const tabItems = [
    {
      key: 'roi-config',
      label: (
        <span>
          <PictureOutlined />
          {t('roiConfigEditor')}
        </span>
      ),
      children: <ROIEditor />
    },
    {
      key: 'settings',
      label: (
        <span>
          <SettingOutlined />
          {t('systemSettings')}
        </span>
      ),
      children: (
        <Card>
          <p>{t('comingSoon')}</p>
        </Card>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1>{t('configManagement')}</h1>
      <p style={{ color: '#666', marginBottom: '24px' }}>
        {t('configManagementDescription')}
      </p>

      <Spin spinning={loading}>
        <Tabs defaultActiveKey="roi-config" items={tabItems} />
      </Spin>
    </div>
  );
};

export default ModuleEX;


