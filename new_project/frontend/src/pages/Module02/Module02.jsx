/**
 * Module02: 数据预处理与质量控制
 *
 * 功能：
 * - 受试者信息管理
 * - MMSE数据管理
 * - 数据质量检测
 * - 数据清洗与平滑
 */
import React, { useState } from 'react';
import { Tabs, Card } from 'antd';
import { UserOutlined, ExperimentOutlined, DatabaseOutlined, FolderOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import SubjectManagement from '../../components/Module02/SubjectManagement';
import DataPreprocessing from '../../components/Module02/DataPreprocessing';
import V1DataManagement from '../../components/Module02/V1DataManagement';
import V2DataManagement from '../../components/Module02/V2DataManagement';

const Module02 = () => {
  const { t } = useTranslation('module02');
  const [activeTab, setActiveTab] = useState('subjects');

  const tabItems = [
    {
      key: 'subjects',
      label: (
        <span>
          <UserOutlined />
          {t('tabs.subjectManagement')}
        </span>
      ),
      children: <SubjectManagement />,
    },
    {
      key: 'v1-data',
      label: (
        <span>
          <FolderOutlined />
          {t('tabs.v1DataManagement')}
        </span>
      ),
      children: <V1DataManagement />,
    },
    {
      key: 'v2-data',
      label: (
        <span>
          <DatabaseOutlined />
          {t('tabs.v2DataManagement')}
        </span>
      ),
      children: <V2DataManagement />,
    },
    {
      key: 'preprocessing',
      label: (
        <span>
          <ExperimentOutlined />
          {t('tabs.dataPreprocessing')}
        </span>
      ),
      children: <DataPreprocessing />,
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card title={t('title')}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="large"
          items={tabItems}
        />
      </Card>
    </div>
  );
};

export default Module02;
