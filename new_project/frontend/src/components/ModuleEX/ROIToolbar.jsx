/**
 * ROI工具栏组件
 * 
 * 功能：
 * - 切换ROI绘制模式（关键词、指示语、背景）
 * - 显示当前绘制模式
 */
import React from 'react';
import { Space, Button, Tag } from 'antd';
import { BorderOutlined, PushpinOutlined, BgColorsOutlined, StopOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const ROIToolbar = ({ drawingMode, onModeChange, style }) => {
  const { t } = useTranslation(['module11']);

  const tools = [
    {
      key: 'KW',
      label: t('roiType_KW'),
      icon: <PushpinOutlined />,
      color: '#ff4d4f'
    },
    {
      key: 'INST',
      label: t('roiType_INST'),
      icon: <BorderOutlined />,
      color: '#1890ff'
    }
    // BG ROI自动创建，不需要手动绘制
  ];

  return (
    <div style={style}>
      <Space>
        <span style={{ fontWeight: 500 }}>{t('drawingTools')}:</span>
        
        {tools.map(tool => (
          <Button
            key={tool.key}
            type={drawingMode === tool.key ? 'primary' : 'default'}
            icon={tool.icon}
            onClick={() => onModeChange(tool.key)}
            style={{
              borderColor: drawingMode === tool.key ? tool.color : undefined,
              backgroundColor: drawingMode === tool.key ? tool.color : undefined
            }}
          >
            {tool.label}
          </Button>
        ))}

        {drawingMode && (
          <Button
            icon={<StopOutlined />}
            onClick={() => onModeChange(null)}
            danger
          >
            {t('cancelDrawing')}
          </Button>
        )}

        {drawingMode && (
          <Tag color="blue">
            {t('drawingModeHint')}
          </Tag>
        )}
      </Space>

      <div style={{ marginTop: '8px', color: '#666', fontSize: '12px' }}>
        {t('drawingInstructions')}
      </div>
    </div>
  );
};

export default ROIToolbar;


