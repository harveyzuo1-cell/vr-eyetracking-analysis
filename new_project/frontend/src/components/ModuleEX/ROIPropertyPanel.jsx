/**
 * ROI属性面板组件
 * 
 * 功能：
 * - 显示选中ROI的属性
 * - 支持编辑ROI属性（标签、坐标等）
 */
import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Button, Space, Divider } from 'antd';
import { EditOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const ROIPropertyPanel = ({ roi, onUpdate, imageDimensions }) => {
  const { t } = useTranslation(['module11', 'common']);
  const [form] = Form.useForm();
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (roi) {
      // 支持两种格式：{x, y, width, height} 或 {normalized_coords: [x, y, w, h]}
      const coords = roi.normalized_coords || [roi.x, roi.y, roi.width, roi.height];

      form.setFieldsValue({
        id: roi.id,
        label: roi.label || '',
        x: coords[0],
        y: coords[1],
        width: coords[2],
        height: coords[3]
      });
      setEditing(false);
    }
  }, [roi, form]);

  // 实时预览：当表单值改变时更新ROI
  const handleValuesChange = (changedValues, allValues) => {
    if (editing && roi && (allValues.x !== undefined && allValues.y !== undefined && allValues.width !== undefined && allValues.height !== undefined)) {
      const updatedRoi = {
        ...roi,
        normalized_coords: [allValues.x, allValues.y, allValues.width, allValues.height],
        label: allValues.label
      };
      // 实时更新预览
      onUpdate(roi.id, updatedRoi);
    }
  };

  const handleSave = () => {
    form.validateFields().then(values => {
      // 将编辑后的坐标转换回normalized_coords格式
      const updatedRoi = {
        ...roi,
        normalized_coords: [values.x, values.y, values.width, values.height],
        label: values.label
      };
      onUpdate(roi.id, updatedRoi);
      setEditing(false);
    });
  };

  const handleCancel = () => {
    form.resetFields();
    setEditing(false);
  };

  if (!roi) {
    return null;
  }

  // 计算像素坐标
  const coords = roi.normalized_coords || [roi.x, roi.y, roi.width, roi.height];
  const pixelCoords = imageDimensions.width > 0 && coords[0] !== undefined ? {
    x: Math.round(coords[0] * imageDimensions.width),
    y: Math.round(coords[1] * imageDimensions.height),
    width: Math.round(coords[2] * imageDimensions.width),
    height: Math.round(coords[3] * imageDimensions.height)
  } : null;

  return (
    <Card
      title={t('roiProperties')}
      extra={
        !editing ? (
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => setEditing(true)}
          >
            {t('common:edit')}
          </Button>
        ) : (
          <Space>
            <Button
              type="link"
              size="small"
              icon={<CheckOutlined />}
              onClick={handleSave}
            >
              {t('common:save')}
            </Button>
            <Button
              type="link"
              size="small"
              icon={<CloseOutlined />}
              onClick={handleCancel}
              danger
            >
              {t('common:cancel')}
            </Button>
          </Space>
        )
      }
    >
      <Form
        form={form}
        layout="vertical"
        size="small"
        onValuesChange={handleValuesChange}
      >
        <Form.Item
          label={t('roiId')}
          name="id"
        >
          <Input disabled />
        </Form.Item>

        <Form.Item
          label={t('roiLabel')}
          name="label"
        >
          <Input disabled={!editing} placeholder={t('optional')} />
        </Form.Item>

        <Divider>{t('normalizedCoordinates')}</Divider>

        <Form.Item
          label="X"
          name="x"
        >
          <InputNumber
            disabled={!editing}
            min={0}
            max={1}
            step={0.001}
            precision={4}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label="Y"
          name="y"
        >
          <InputNumber
            disabled={!editing}
            min={0}
            max={1}
            step={0.001}
            precision={4}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label={t('width')}
          name="width"
        >
          <InputNumber
            disabled={!editing}
            min={0}
            max={1}
            step={0.001}
            precision={4}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label={t('height')}
          name="height"
        >
          <InputNumber
            disabled={!editing}
            min={0}
            max={1}
            step={0.001}
            precision={4}
            style={{ width: '100%' }}
          />
        </Form.Item>

        {pixelCoords && (
          <>
            <Divider>{t('pixelCoordinates')}</Divider>
            <div style={{ fontSize: '12px', color: '#666' }}>
              <p>X: {pixelCoords.x}px</p>
              <p>Y: {pixelCoords.y}px</p>
              <p>{t('width')}: {pixelCoords.width}px</p>
              <p>{t('height')}: {pixelCoords.height}px</p>
            </div>
          </>
        )}
      </Form>
    </Card>
  );
};

export default ROIPropertyPanel;


