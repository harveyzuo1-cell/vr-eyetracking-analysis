/**
 * 数据校正面板组件
 * Data Calibration Panel Component
 *
 * 提供位置偏移和时间裁剪功能，支持实时预览
 * Provides position offset and time trimming with real-time preview
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Slider,
  InputNumber,
  Button,
  Space,
  Row,
  Col,
  message,
  Card,
  Divider,
  Tooltip,
  Select,
  Modal
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { debounce } from 'lodash';
import calibrationService from '../../services/calibrationService';

const CalibrationPanel = ({
  originalData = [],
  group,
  subjectId,
  task,
  onPreview,
  onSaveComplete,
  currentVersion = null,
  onVersionRestore = null
}) => {
  const { t } = useTranslation(['module01']);

  // 版本管理状态
  const [versions, setVersions] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [showVersionModal, setShowVersionModal] = useState(false);

  // 校正参数状态
  const [params, setParams] = useState({
    offsetX: 0,
    offsetY: 0,
    trimStart: 0,
    trimEnd: 0
  });

  // 保存状态
  const [isSaving, setIsSaving] = useState(false);

  // 防抖更新参数
  const debouncedUpdatePreview = useMemo(
    () => debounce((newParams) => {
      if (onPreview && originalData.length > 0) {
        const previewData = calibrationService.calculatePreview(originalData, newParams);
        onPreview(previewData, newParams);
      }
    }, 300),
    [originalData, onPreview]
  );

  // 更新单个参数
  const updateParam = useCallback((key, value) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);
    debouncedUpdatePreview(newParams);
  }, [params, debouncedUpdatePreview]);

  // 重置参数
  const handleReset = useCallback(() => {
    const resetParams = {
      offsetX: 0,
      offsetY: 0,
      trimStart: 0,
      trimEnd: 0
    };
    setParams(resetParams);
    if (onPreview) {
      onPreview(originalData, resetParams);
    }
    message.info(t('calibration.resetSuccess', '参数已重置'));
  }, [originalData, onPreview, t]);

  // 保存校正数据
  const handleSave = useCallback(async () => {
    // 参数验证
    const { valid, errors } = calibrationService.validateParams(params);
    if (!valid) {
      message.error(`${t('calibration.validationError', '参数验证失败')}: ${errors.join(', ')}`);
      return;
    }

    // 检查是否有实际变更
    if (params.offsetX === 0 && params.offsetY === 0 &&
        params.trimStart === 0 && params.trimEnd === 0) {
      message.warning(t('calibration.noChanges', '未检测到参数变更'));
      return;
    }

    setIsSaving(true);
    try {
      const result = await calibrationService.saveCalibration({
        group,
        subject_id: subjectId,
        task,
        params
      });

      if (result.success) {
        message.success(t('calibration.saveSuccess', '校正数据已保存'));
        if (onSaveComplete) {
          onSaveComplete(result.data);
        }
      } else {
        message.error(result.message || t('calibration.saveFailed', '保存失败'));
      }
    } catch (error) {
      message.error(`${t('calibration.saveFailed', '保存失败')}: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  }, [params, group, subjectId, task, onSaveComplete, t]);

  // 加载版本列表
  const loadVersions = useCallback(async () => {
    if (!group || !subjectId || !task) return;

    setLoadingVersions(true);
    try {
      const result = await calibrationService.getVersions(group, subjectId, task);
      if (result.success) {
        setVersions(result.data || []);
      } else {
        message.error('加载版本列表失败');
      }
    } catch (error) {
      console.error('加载版本列表错误:', error);
    } finally {
      setLoadingVersions(false);
    }
  }, [group, subjectId, task]);

  // 恢复到指定版本
  const handleRestoreVersion = useCallback(async (version) => {
    try {
      const result = await calibrationService.restoreVersion(group, subjectId, task, version);
      if (result.success) {
        message.success(`已恢复到版本 ${version}`);
        setShowVersionModal(false);
        if (onVersionRestore) {
          await onVersionRestore();
        }
      } else {
        message.error(result.message || '版本恢复失败');
      }
    } catch (error) {
      message.error(`版本恢复失败: ${error.message}`);
    }
  }, [group, subjectId, task, onVersionRestore]);

  // 计算剩余时间
  const remainingTime = useMemo(() => {
    if (!originalData || originalData.length === 0) return 0;
    const timestamps = originalData.map(d => d.timestamp || d.time || 0);
    const totalTime = Math.max(...timestamps) - Math.min(...timestamps);
    return Math.max(0, totalTime - params.trimStart - params.trimEnd);
  }, [originalData, params.trimStart, params.trimEnd]);

  return (
    <>
    <Card
      size="small"
      title={
        <Space>
          {t('calibration.title', '数据校正')}
          <Tooltip title={t('calibration.description', '调整眼动轨迹位置或裁剪时间范围')}>
            <InfoCircleOutlined style={{ fontSize: '14px', color: '#1890ff' }} />
          </Tooltip>
        </Space>
      }
      extra={
        <Space>
          <Button
            size="small"
            icon={<HistoryOutlined />}
            onClick={() => {
              loadVersions();
              setShowVersionModal(true);
            }}
            disabled={!group || !subjectId || !task}
          >
            版本历史
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={handleReset}
          >
            {t('calibration.reset', '重置')}
          </Button>
          <Button
            size="small"
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={isSaving}
            disabled={!group || !subjectId || !task}
          >
            {t('calibration.save', '保存')}
          </Button>
        </Space>
      }
      style={{ width: '100%' }}
    >
      {/* 位置偏移控制 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 500, marginBottom: 8 }}>
          {t('calibration.positionOffset', '位置偏移')}
        </div>

        {/* X轴偏移 */}
        <Row gutter={8} align="middle" style={{ marginBottom: 8 }}>
          <Col span={4}>
            <span style={{ fontSize: '12px' }}>
              {t('calibration.offsetX', 'X轴')}:
            </span>
          </Col>
          <Col span={14}>
            <Slider
              min={-0.4}
              max={0.4}
              step={0.01}
              value={params.offsetX}
              onChange={(value) => updateParam('offsetX', value)}
              marks={{ '-0.4': '-0.4', '0': '0', '0.4': '0.4' }}
            />
          </Col>
          <Col span={6}>
            <InputNumber
              size="small"
              min={-0.4}
              max={0.4}
              step={0.01}
              value={params.offsetX}
              onChange={(value) => updateParam('offsetX', value || 0)}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>

        {/* Y轴偏移 */}
        <Row gutter={8} align="middle">
          <Col span={4}>
            <span style={{ fontSize: '12px' }}>
              {t('calibration.offsetY', 'Y轴')}:
            </span>
          </Col>
          <Col span={14}>
            <Slider
              min={-0.4}
              max={0.4}
              step={0.01}
              value={params.offsetY}
              onChange={(value) => updateParam('offsetY', value)}
              marks={{ '-0.4': '-0.4', '0': '0', '0.4': '0.4' }}
            />
          </Col>
          <Col span={6}>
            <InputNumber
              size="small"
              min={-0.4}
              max={0.4}
              step={0.01}
              value={params.offsetY}
              onChange={(value) => updateParam('offsetY', value || 0)}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
      </div>

      <Divider style={{ margin: '12px 0' }} />

      {/* 时间裁剪控制 */}
      <div>
        <div style={{ fontWeight: 500, marginBottom: 8 }}>
          {t('calibration.timeTrim', '时间裁剪')}
          <span style={{ fontSize: '12px', color: '#888', marginLeft: 8 }}>
            ({t('calibration.remaining', '剩余')}: {remainingTime.toFixed(2)}s)
          </span>
        </div>

        {/* 起始裁剪 */}
        <Row gutter={8} align="middle" style={{ marginBottom: 8 }}>
          <Col span={4}>
            <span style={{ fontSize: '12px' }}>
              {t('calibration.trimStart', '起始')}:
            </span>
          </Col>
          <Col span={14}>
            <Slider
              min={0}
              max={60}
              step={0.1}
              value={params.trimStart}
              onChange={(value) => updateParam('trimStart', value)}
              marks={{ '0': '0s', '30': '30s', '60': '60s' }}
            />
          </Col>
          <Col span={6}>
            <InputNumber
              size="small"
              min={0}
              max={60}
              step={0.1}
              value={params.trimStart}
              onChange={(value) => updateParam('trimStart', value || 0)}
              style={{ width: '100%' }}
              addonAfter="s"
            />
          </Col>
        </Row>

        {/* 结束裁剪 */}
        <Row gutter={8} align="middle">
          <Col span={4}>
            <span style={{ fontSize: '12px' }}>
              {t('calibration.trimEnd', '结束')}:
            </span>
          </Col>
          <Col span={14}>
            <Slider
              min={0}
              max={60}
              step={0.1}
              value={params.trimEnd}
              onChange={(value) => updateParam('trimEnd', value)}
              marks={{ '0': '0s', '30': '30s', '60': '60s' }}
            />
          </Col>
          <Col span={6}>
            <InputNumber
              size="small"
              min={0}
              max={60}
              step={0.1}
              value={params.trimEnd}
              onChange={(value) => updateParam('trimEnd', value || 0)}
              style={{ width: '100%' }}
              addonAfter="s"
            />
          </Col>
        </Row>
      </div>
    </Card>

    {/* 版本历史Modal */}
    <Modal
      title="校正版本历史"
      open={showVersionModal}
      onCancel={() => setShowVersionModal(false)}
      footer={null}
      width={600}
    >
      {loadingVersions ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          加载中...
        </div>
      ) : versions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          暂无历史版本
        </div>
      ) : (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {versions.map((v) => (
            <Card
              key={`v${v.version}_${v.timestamp}`}
              size="small"
              style={{ marginBottom: 12 }}
              title={
                <Space>
                  <span style={{ fontWeight: 'bold' }}>版本 {v.version}</span>
                  {currentVersion && currentVersion.version === v.version && (
                    <span style={{ color: '#52c41a', fontSize: '12px' }}>(当前)</span>
                  )}
                </Space>
              }
              extra={
                <Button
                  size="small"
                  onClick={() => handleRestoreVersion(v.version)}
                  disabled={currentVersion && currentVersion.version === v.version}
                >
                  恢复此版本
                </Button>
              }
            >
              <div style={{ fontSize: '12px', color: '#666' }}>
                <div>保存时间: {v.calibrated_at || v.timestamp}</div>
                <div style={{ marginTop: 4 }}>
                  参数: X偏移={v.params?.offsetX || 0}, Y偏移={v.params?.offsetY || 0},
                  裁剪起始={v.params?.trimStart || 0}s, 裁剪结束={v.params?.trimEnd || 0}s
                </div>
                <div style={{ marginTop: 4 }}>
                  数据点数: {v.points_after || 'N/A'}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </Modal>
  </>
  );
};

export default CalibrationPanel;
