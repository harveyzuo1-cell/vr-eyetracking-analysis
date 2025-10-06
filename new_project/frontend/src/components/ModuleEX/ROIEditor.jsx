/**
 * ROI编辑器 - 主容器组件
 * 
 * 功能：
 * 1. 背景图片选择
 * 2. ROI可视化绘制
 * 3. ROI列表管理
 * 4. 配置保存/加载
 */
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, message, Modal, Space, Select } from 'antd';
import { SaveOutlined, FolderOpenOutlined, PlusOutlined, DeleteOutlined, PictureOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

import BackgroundImageSelector from './BackgroundImageSelector';
import ROICanvas from './ROICanvas';
import ROIToolbar from './ROIToolbar';
import ROIList from './ROIList';
import ROIPropertyPanel from './ROIPropertyPanel';

const ROIEditor = () => {
  const { t } = useTranslation(['module11', 'common']);

  // 状态管理
  const [version, setVersion] = useState('v2'); // 数据版本
  const [selectedTaskId, setSelectedTaskId] = useState(null); // 选中的任务ID
  const [backgroundImage, setBackgroundImage] = useState(null); // 背景图片信息
  const [imageUrl, setImageUrl] = useState(null); // 背景图片URL
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 }); // 图片尺寸

  const [roiConfig, setRoiConfig] = useState(null); // ROI配置
  const [rois, setRois] = useState({ keywords: [], instructions: [], background: [] }); // ROI列表
  const [selectedRoi, setSelectedRoi] = useState(null); // 选中的ROI
  const [drawingMode, setDrawingMode] = useState(null); // 绘制模式: 'KW', 'INST', 'BG', null

  const [loading, setLoading] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // 加载背景图片
  const loadBackgroundImage = async (taskId) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/config/background-images/${taskId}`, {
        params: { version }
      });

      if (response.data.success) {
        const imgInfo = response.data.data;
        setBackgroundImage(imgInfo);
        setImageDimensions(imgInfo.dimensions);
        setSelectedTaskId(taskId);

        // 构建图片URL
        const imgUrl = `/static/background_images/${version}/${imgInfo.filename}`;
        setImageUrl(imgUrl);

        // 加载对应的ROI配置
        await loadRoiConfig(taskId);

        message.success(t('backgroundImageLoaded'));
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      console.error('Load background image error:', error);
      message.error(t('loadBackgroundImageFailed'));
    } finally {
      setLoading(false);
    }
  };

  // 加载ROI配置
  const loadRoiConfig = async (taskId) => {
    try {
      const response = await axios.get(`/api/config/roi`, {
        params: { version, task_id: taskId }
      });

      if (response.data.success) {
        const config = response.data.data;
        setRoiConfig(config);

        const regions = config.regions || { keywords: [], instructions: [], background: [] };
        let bgAutoCreated = false;

        // 如果没有BG ROI，自动创建一个覆盖整个图片的BG ROI
        if (!regions.background || regions.background.length === 0) {
          regions.background = [{
            id: `BG_${taskId}`,  // BG类型不需要索引
            type: 'BG',
            task_id: taskId,
            normalized_coords: [0, 0, 1, 1], // 整个图片区域
            version: version,
            color: '#faad14',  // 橙色 - 背景区域
            description: '背景区域',
            name: `BG_${taskId}`
          }];
          bgAutoCreated = true;
        }

        setRois(regions);
        setHasUnsavedChanges(bgAutoCreated);
        message.success(t('roiConfigLoaded') + (bgAutoCreated ? ' - BG ROI自动创建' : ''));
      } else {
        // 如果没有配置，创建默认配置（包含BG ROI）
        const defaultRois = {
          keywords: [],
          instructions: [],
          background: [{
            id: `BG_${taskId}`,  // BG类型不需要索引
            type: 'BG',
            task_id: taskId,
            normalized_coords: [0, 0, 1, 1],
            version: version,
            color: '#faad14',  // 橙色 - 背景区域
            description: '背景区域',
            name: `BG_${taskId}`
          }]
        };
        setRois(defaultRois);
        setHasUnsavedChanges(true); // 标记有未保存的更改
        message.info(response.data.message + ' - ' + t('bgRoiAutoCreated'));
      }
    } catch (error) {
      console.error('Load ROI config error:', error);
      message.error(t('loadRoiConfigFailed'));
    }
  };

  // 保存ROI配置
  const saveRoiConfig = async () => {
    if (!selectedTaskId) {
      message.warning(t('pleaseSelectTask'));
      return;
    }

    try {
      setLoading(true);

      // 确保task_id是小写（后端验证要求小写 q1-5 或 task1-5）
      const normalizedTaskId = selectedTaskId.toLowerCase();

      // 标准化所有ROI对象中的ID和task_id为小写，并确保有颜色字段
      const normalizeRois = (roiObj) => {
        // 默认颜色映射
        const defaultColors = {
          'KW': '#1890ff',   // 蓝色 - Keywords
          'INST': '#52c41a', // 绿色 - Instructions
          'BG': '#faad14'    // 橙色 - Background
        };

        const normalized = {};
        for (const [type, roiList] of Object.entries(roiObj)) {
          normalized[type] = roiList.map(roi => {
            // 确保有颜色字段，如果没有则根据类型添加默认颜色
            const roiType = roi.type || roi.id.split('_')[0]; // 从ID中提取类型
            const color = roi.color || defaultColors[roiType] || '#999999';

            return {
              ...roi,
              id: roi.id.replace(/_(Q|q)(\d+)/i, `_q$2`).replace(/_(Q|q)(\d+)_/i, `_q$2_`),  // Q4 -> q4, Q4_ -> q4_
              task_id: normalizedTaskId,
              color: color,  // 确保每个ROI都有颜色
              description: roi.description || {
                'KW': '关键区域',
                'INST': '指令区域',
                'BG': '背景区域'
              }[roiType],
              name: roi.name || roi.id  // 确保有name字段
            };
          });
        }
        return normalized;
      };

      const normalizedRois = normalizeRois(rois);

      const config = {
        version,
        task_id: normalizedTaskId,
        task_name: normalizedTaskId,
        background_image: backgroundImage?.filename || `${normalizedTaskId}.png`,
        regions: normalizedRois
      };

      console.log('📤 Saving ROI config:', {
        version,
        task_id: normalizedTaskId,
        config,
        regions_type: typeof rois,
        regions_keys: Object.keys(rois),
        regions_values: Object.entries(rois).map(([k, v]) => ({ key: k, isArray: Array.isArray(v), length: v?.length }))
      });
      console.log('📦 Full rois object:', JSON.stringify(rois, null, 2));
      console.log('📦 Full config object:', JSON.stringify(config, null, 2));

      const response = await axios.post(`/api/config/roi`, {
        version,
        task_id: normalizedTaskId,
        config
      });

      if (response.data.success) {
        setHasUnsavedChanges(false);
        message.success(t('roiConfigSaved'));
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      console.error('Save ROI config error:', error);
      message.error(t('saveRoiConfigFailed'));
    } finally {
      setLoading(false);
    }
  };

  // 添加ROI
  const addRoi = (newRoi) => {
    const typeMap = {
      'KW': 'keywords',
      'INST': 'instructions',
      'BG': 'background'
    };

    // 默认颜色映射
    const defaultColors = {
      'KW': '#1890ff',   // 蓝色 - Keywords
      'INST': '#52c41a', // 绿色 - Instructions
      'BG': '#faad14'    // 橙色 - Background
    };

    const regionType = typeMap[newRoi.type];

    setRois(prev => {
      // 生成ROI ID: {TYPE}_{TASK}_{INDEX}
      const existingRois = prev[regionType] || [];
      const index = existingRois.length + 1;
      const roiWithId = {
        ...newRoi,
        id: `${newRoi.type}_${newRoi.task_id}_${index}`,
        color: newRoi.color || defaultColors[newRoi.type] || '#999999',  // 确保有颜色
        description: newRoi.description || {
          'KW': '关键区域',
          'INST': '指令区域',
          'BG': '背景区域'
        }[newRoi.type],
        name: newRoi.name || `${newRoi.type}_${newRoi.task_id}_${index}`  // 确保有name字段
      };

      return {
        ...prev,
        [regionType]: [...existingRois, roiWithId]
      };
    });
    setHasUnsavedChanges(true);
    message.success(t('roiAdded'));
  };

  // 更新ROI
  const updateRoi = (roiId, updates) => {
    const updateRegion = (regionList) =>
      regionList.map(roi => roi.id === roiId ? { ...roi, ...updates } : roi);

    setRois(prev => ({
      keywords: updateRegion(prev.keywords),
      instructions: updateRegion(prev.instructions),
      background: updateRegion(prev.background)
    }));
    setHasUnsavedChanges(true);
  };

  // 删除ROI
  const deleteRoi = (roiId) => {
    Modal.confirm({
      title: t('confirmDeleteRoi'),
      content: t('confirmDeleteRoiMessage'),
      okText: t('common:delete'),
      cancelText: t('common:cancel'),
      okType: 'danger',
      onOk: () => {
        const filterRegion = (regionList) => regionList.filter(roi => roi.id !== roiId);

        setRois(prev => ({
          keywords: filterRegion(prev.keywords),
          instructions: filterRegion(prev.instructions),
          background: filterRegion(prev.background)
        }));

        if (selectedRoi?.id === roiId) {
          setSelectedRoi(null);
        }

        setHasUnsavedChanges(true);
        message.success(t('roiDeleted'));
      }
    });
  };

  // 选中ROI
  const selectRoi = (roi) => {
    setSelectedRoi(roi);
  };

  // 切换绘制模式
  const toggleDrawingMode = (mode) => {
    if (drawingMode === mode) {
      setDrawingMode(null);
    } else {
      setDrawingMode(mode);
      message.info(t('drawingModeActive', { mode: t(`roiType_${mode}`) }));
    }
  };

  return (
    <div>
      {/* 顶部工具栏 */}
      <Card style={{ marginBottom: '16px' }}>
        <Space>
          <Select
            value={version}
            onChange={setVersion}
            style={{ width: 120 }}
            options={[
              { value: 'v1', label: 'V1 (Legacy)' },
              { value: 'v2', label: 'V2 (Eye Tracking)' }
            ]}
          />

          <BackgroundImageSelector
            version={version}
            onSelect={loadBackgroundImage}
            selectedTaskId={selectedTaskId}
          />

          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={saveRoiConfig}
            disabled={!selectedTaskId || !hasUnsavedChanges}
            loading={loading}
          >
            {t('common:save')}
          </Button>

          <Button
            icon={<FolderOpenOutlined />}
            onClick={() => selectedTaskId && loadRoiConfig(selectedTaskId)}
            disabled={!selectedTaskId}
          >
            {t('common:reload')}
          </Button>

          {hasUnsavedChanges && (
            <span style={{ color: '#ff4d4f' }}>
              {t('hasUnsavedChanges')}
            </span>
          )}
        </Space>
      </Card>

      {/* 主编辑区域 */}
      <Row gutter={16}>
        {/* 左侧：画布 + 工具栏 */}
        <Col span={12}>
          <Card title={t('roiCanvas')}>
            {imageUrl ? (
              <>
                <ROIToolbar
                  drawingMode={drawingMode}
                  onModeChange={toggleDrawingMode}
                  style={{ marginBottom: '16px' }}
                />
                <ROICanvas
                  imageUrl={imageUrl}
                  imageDimensions={imageDimensions}
                  rois={rois}
                  selectedRoi={selectedRoi}
                  drawingMode={drawingMode}
                  onAddRoi={addRoi}
                  onUpdateRoi={updateRoi}
                  onSelectRoi={selectRoi}
                  taskId={selectedTaskId}
                  version={version}
                />
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
                <PictureOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <p>{t('pleaseSelectBackgroundImage')}</p>
              </div>
            )}
          </Card>
        </Col>

        {/* 右侧：ROI列表（带内联编辑） */}
        <Col span={12}>
          <ROIList
            rois={rois}
            selectedRoi={selectedRoi}
            onSelectRoi={selectRoi}
            onDeleteRoi={deleteRoi}
            onUpdateRoi={updateRoi}
            imageDimensions={imageDimensions}
            style={{ marginBottom: '16px' }}
          />
        </Col>
      </Row>
    </div>
  );
};

export default ROIEditor;


