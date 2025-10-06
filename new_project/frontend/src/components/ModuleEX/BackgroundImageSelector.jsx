/**
 * 背景图片选择器组件
 * 
 * 功能：
 * - 显示可用背景图片列表
 * - 支持选择任务对应的背景图
 * - 支持上传新的背景图片
 */
import React, { useState, useEffect } from 'react';
import { Select, Button, Upload, message, Modal } from 'antd';
import { PictureOutlined, UploadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const BackgroundImageSelector = ({ version, onSelect, selectedTaskId }) => {
  const { t } = useTranslation(['module11', 'common']);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);

  // 加载背景图片列表
  useEffect(() => {
    loadImages();
  }, [version]);

  const loadImages = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/config/background-images', {
        params: { version }
      });

      if (response.data.success) {
        setImages(response.data.data);
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      console.error('Load images error:', error);
      message.error(t('loadImagesFailed'));
    } finally {
      setLoading(false);
    }
  };

  // 处理图片选择
  const handleSelect = (taskId) => {
    if (onSelect) {
      onSelect(taskId);
    }
  };

  // 处理图片上传
  const handleUpload = async ({ file, onSuccess, onError }) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('version', version);
    formData.append('task_id', file.name.split('.')[0]); // 使用文件名作为task_id

    try {
      const response = await axios.post('/api/config/background-images', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        message.success(t('uploadSuccess'));
        loadImages(); // 重新加载列表
        setUploadModalVisible(false);
        onSuccess();
      } else {
        message.error(response.data.message);
        onError();
      }
    } catch (error) {
      console.error('Upload error:', error);
      message.error(t('uploadFailed'));
      onError();
    }
  };

  return (
    <>
      <Select
        value={selectedTaskId}
        onChange={handleSelect}
        placeholder={t('selectBackgroundImage')}
        style={{ width: 200 }}
        loading={loading}
        suffixIcon={<PictureOutlined />}
        options={images.map(img => ({
          value: img.task_id,
          label: `${img.task_id} (${img.dimensions.width}x${img.dimensions.height})`
        }))}
      />

      <Button
        icon={<UploadOutlined />}
        onClick={() => setUploadModalVisible(true)}
      >
        {t('uploadImage')}
      </Button>

      <Modal
        title={t('uploadBackgroundImage')}
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
      >
        <Upload.Dragger
          name="file"
          multiple={false}
          customRequest={handleUpload}
          accept="image/png,image/jpeg,image/jpg"
        >
          <p className="ant-upload-drag-icon">
            <PictureOutlined />
          </p>
          <p className="ant-upload-text">{t('clickOrDragToUpload')}</p>
          <p className="ant-upload-hint">
            {t('supportPngJpg')}
          </p>
        </Upload.Dragger>
      </Modal>
    </>
  );
};

export default BackgroundImageSelector;


