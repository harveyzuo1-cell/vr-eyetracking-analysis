/**
 * ROI列表组件
 *
 * 功能：
 * - 显示所有ROI的列表（按类型分组）
 * - 支持选中ROI
 * - 支持删除ROI
 * - 支持内联编辑ROI坐标
 */
import React, { useState } from 'react';
import { Card, List, Button, Tag, Empty, Collapse, InputNumber, Space, Row, Col } from 'antd';
import { DeleteOutlined, EyeOutlined, EditOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const ROIList = ({ rois, selectedRoi, onSelectRoi, onDeleteRoi, onUpdateRoi, imageDimensions, style }) => {
  const { t } = useTranslation(['module11']);
  const [editingId, setEditingId] = useState(null);
  const [editValues, setEditValues] = useState({});

  const roiTypes = [
    { key: 'keywords', label: t('roiType_KW'), color: '#1890ff' },
    { key: 'instructions', label: t('roiType_INST'), color: '#52c41a' },
    { key: 'background', label: t('roiType_BG'), color: '#faad14' }
  ];

  const getTotalCount = () => {
    return (rois.keywords?.length || 0) +
           (rois.instructions?.length || 0) +
           (rois.background?.length || 0);
  };

  const handleEdit = (roi, e) => {
    e.stopPropagation();
    const coords = roi.normalized_coords || [roi.x, roi.y, roi.width, roi.height];
    setEditingId(roi.id);
    setEditValues({
      x: coords[0],
      y: coords[1],
      width: coords[2],
      height: coords[3]
    });
  };

  const handleSaveEdit = (roi, e) => {
    e.stopPropagation();
    const updatedRoi = {
      ...roi,
      normalized_coords: [editValues.x, editValues.y, editValues.width, editValues.height]
    };
    onUpdateRoi(roi.id, updatedRoi);
    setEditingId(null);
    setEditValues({});
  };

  const handleCancelEdit = (e) => {
    e.stopPropagation();
    setEditingId(null);
    setEditValues({});
  };

  const handleValueChange = (roi, field, value) => {
    const newValues = { ...editValues, [field]: value };
    setEditValues(newValues);

    // 实时预览
    const updatedRoi = {
      ...roi,
      normalized_coords: [newValues.x, newValues.y, newValues.width, newValues.height]
    };
    onUpdateRoi(roi.id, updatedRoi);
  };

  const renderRoiItem = (roi, color) => {
    const isSelected = selectedRoi?.id === roi.id;
    const isEditing = editingId === roi.id;
    const coords = roi.normalized_coords || [roi.x, roi.y, roi.width, roi.height];

    // 计算像素坐标
    const pixelCoords = imageDimensions?.width > 0 ? {
      x: Math.round(coords[0] * imageDimensions.width),
      y: Math.round(coords[1] * imageDimensions.height),
      w: Math.round(coords[2] * imageDimensions.width),
      h: Math.round(coords[3] * imageDimensions.height)
    } : null;

    return (
      <List.Item
        key={roi.id}
        style={{
          display: 'block',
          padding: '8px',
          cursor: 'pointer',
          backgroundColor: isSelected ? '#e6f7ff' : 'transparent',
          borderLeft: isSelected ? `3px solid ${color}` : '3px solid transparent',
          transition: 'all 0.3s'
        }}
        onClick={() => !isEditing && onSelectRoi(roi)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Tag color={color} style={{ margin: 0 }}>
                {roi.id}
              </Tag>
              {isSelected && <EyeOutlined style={{ color: '#1890ff' }} />}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {pixelCoords && `${pixelCoords.x}×${pixelCoords.y} (${pixelCoords.w}×${pixelCoords.h}px)`}
            </div>
          </div>
          <Space size="small">
            {!isEditing ? (
              <>
                <Button
                  type="text"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={(e) => handleEdit(roi, e)}
                />
                <Button
                  type="text"
                  size="small"
                  icon={<DeleteOutlined />}
                  danger
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteRoi(roi.id);
                  }}
                />
              </>
            ) : (
              <>
                <Button
                  type="text"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={(e) => handleSaveEdit(roi, e)}
                  style={{ color: '#52c41a' }}
                />
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined />}
                  danger
                  onClick={handleCancelEdit}
                />
              </>
            )}
          </Space>
        </div>

        {isEditing && (
          <div
            style={{
              marginTop: '12px',
              padding: '12px',
              background: '#f5f5f5',
              borderRadius: '4px'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <Row gutter={[8, 8]}>
              <Col span={6}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>X</div>
                <InputNumber
                  size="small"
                  value={editValues.x}
                  onChange={(v) => handleValueChange(roi, 'x', v)}
                  min={0}
                  max={1}
                  step={0.001}
                  precision={4}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={6}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Y</div>
                <InputNumber
                  size="small"
                  value={editValues.y}
                  onChange={(v) => handleValueChange(roi, 'y', v)}
                  min={0}
                  max={1}
                  step={0.001}
                  precision={4}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={6}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>W</div>
                <InputNumber
                  size="small"
                  value={editValues.width}
                  onChange={(v) => handleValueChange(roi, 'width', v)}
                  min={0}
                  max={1}
                  step={0.001}
                  precision={4}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={6}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>H</div>
                <InputNumber
                  size="small"
                  value={editValues.height}
                  onChange={(v) => handleValueChange(roi, 'height', v)}
                  min={0}
                  max={1}
                  step={0.001}
                  precision={4}
                  style={{ width: '100%' }}
                />
              </Col>
            </Row>
          </div>
        )}
      </List.Item>
    );
  };

  return (
    <Card
      title={t('roiList')}
      extra={<Tag color="blue">{t('total')}: {getTotalCount()}</Tag>}
      style={style}
    >
      {getTotalCount() === 0 ? (
        <Empty description={t('noRoiDefined')} />
      ) : (
        <Collapse
          defaultActiveKey={['keywords', 'instructions', 'background']}
          ghost
          items={roiTypes.map(type => ({
            key: type.key,
            label: (
              <span>
                <Tag color={type.color}>{type.label}</Tag>
                <span style={{ marginLeft: '8px', color: '#666' }}>
                  ({rois[type.key]?.length || 0})
                </span>
              </span>
            ),
            children: (
              <List
                size="small"
                dataSource={rois[type.key] || []}
                renderItem={roi => renderRoiItem(roi, type.color)}
                style={{ maxHeight: '400px', overflowY: 'auto' }}
              />
            )
          }))}
        />
      )}
    </Card>
  );
};

export default ROIList;
