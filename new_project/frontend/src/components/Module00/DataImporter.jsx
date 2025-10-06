/**
 * Module 00 - 数据导入组件
 * Data Importer Component
 */
import React, { useState } from 'react';
import { Card, Button, Space, message, Modal, Radio, Checkbox, Alert } from 'antd';
import { ImportOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const DataImporter = ({ scanData, onImportComplete }) => {
  const { t } = useTranslation('module00');
  const [importing, setImporting] = useState(false);
  const [source, setSource] = useState('all');
  const [overwrite, setOverwrite] = useState(false);

  const handleImport = () => {
    if (!scanData) {
      message.warning('请先扫描数据源');
      return;
    }

    Modal.confirm({
      title: '确认导入',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>您将要导入以下数据：</p>
          <ul>
            {(source === 'all' || source === 'legacy') && (
              <li>Legacy数据 (v1): {scanData.legacy_data?.total_subjects || 0} 名受试者</li>
            )}
            {(source === 'all' || source === 'eye_tracking') && (
              <li>Eye Tracking数据 (v2): {scanData.eye_tracking_data?.total_subjects || 0} 名受试者</li>
            )}
          </ul>
          {overwrite && (
            <Alert
              message="警告：覆盖模式已开启"
              description="已存在的数据将被覆盖"
              type="warning"
              showIcon
              style={{ marginTop: 8 }}
            />
          )}
        </div>
      ),
      okText: '确认导入',
      cancelText: '取消',
      onOk: async () => {
        setImporting(true);

        try {
          const response = await axios.post('/api/m00/import', {
            source,
            overwrite
          });

          if (response.data.success) {
            const { imported_count, legacy_imported, eye_tracking_imported, errors } = response.data;

            if (imported_count > 0) {
              message.success(t('importer.success', { count: imported_count }));

              // 显示详细信息
              Modal.success({
                title: '导入完成',
                content: (
                  <div>
                    <p>总计导入: {imported_count} 名受试者</p>
                    {legacy_imported > 0 && <p>Legacy数据 (v1): {legacy_imported} 名</p>}
                    {eye_tracking_imported > 0 && <p>Eye Tracking数据 (v2): {eye_tracking_imported} 名</p>}
                    {errors && errors.length > 0 && (
                      <Alert
                        message="部分导入失败"
                        description={errors.join(', ')}
                        type="warning"
                        showIcon
                        style={{ marginTop: 8 }}
                      />
                    )}
                  </div>
                ),
              });

              onImportComplete?.(response.data);
            } else {
              message.warning('未导入任何数据，可能数据已存在或没有可导入的数据');

              if (errors && errors.length > 0) {
                Modal.error({
                  title: '导入失败',
                  content: errors.join('\n'),
                });
              }
            }
          } else {
            message.error('导入失败：' + response.data.error);
          }
        } catch (error) {
          message.error('导入失败：' + error.message);
        } finally {
          setImporting(false);
        }
      },
    });
  };

  return (
    <Card title={<span><ImportOutlined /> {t('importer.title')}</span>}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <span style={{ marginRight: 16 }}>选择数据源:</span>
          <Radio.Group value={source} onChange={(e) => setSource(e.target.value)}>
            <Radio value="all">全部导入</Radio>
            <Radio value="legacy">仅Legacy (v1)</Radio>
            <Radio value="eye_tracking">仅Eye Tracking (v2)</Radio>
          </Radio.Group>
        </div>

        <div>
          <Checkbox checked={overwrite} onChange={(e) => setOverwrite(e.target.checked)}>
            覆盖已存在数据
          </Checkbox>
          {overwrite && (
            <Alert
              message="警告：开启覆盖模式将替换已存在的受试者数据"
              type="warning"
              showIcon
              style={{ marginTop: 8 }}
            />
          )}
        </div>

        <Button
          type="primary"
          size="large"
          icon={<ImportOutlined />}
          onClick={handleImport}
          loading={importing}
          disabled={!scanData}
        >
          {importing ? t('importer.importing') : t('importer.button')}
        </Button>

        {!scanData && (
          <Alert
            message="请先扫描数据源后再进行导入"
            type="info"
            showIcon
          />
        )}
      </Space>
    </Card>
  );
};

export default DataImporter;
