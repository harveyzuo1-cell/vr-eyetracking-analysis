import React, { useState } from 'react';
import { Card, Button, Space, message } from 'antd';
import { SyncOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const DataScanner = ({ onScanComplete, onScanStateChange }) => {
  const { t } = useTranslation('module00');
  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    setScanning(true);
    onScanStateChange?.(true);

    try {
      const response = await axios.get('/api/m00/scan-all');
      if (response.data.success) {
        message.success(t('scanner.success'));
        onScanComplete?.(response.data);
      } else {
        message.error(t('scanner.error') + ': ' + response.data.error);
      }
    } catch (error) {
      message.error(t('scanner.error') + ': ' + error.message);
    } finally {
      setScanning(false);
      onScanStateChange?.(false);
    }
  };

  return (
    <Card title={<span><SyncOutlined /> {t('scanner.title')}</span>}>
      <Space>
        <Button
          type="primary"
          size="large"
          icon={<ReloadOutlined />}
          onClick={handleScan}
          loading={scanning}
        >
          {scanning ? t('scanner.scanning') : t('scanner.button')}
        </Button>
        <span style={{ color: '#666' }}>
          扫描 Legacy数据(v1) 和 Eye Tracking数据(v2)
        </span>
      </Space>
    </Card>
  );
};

export default DataScanner;
