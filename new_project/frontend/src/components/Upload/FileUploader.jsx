import React, { useState } from 'react';
import { Upload, message, Progress, Card } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import dataManagementService from '../../services/dataManagementService';

const { Dragger } = Upload;

const FileUploader = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const customRequest = async ({ file, onSuccess, onError }) => {
    try {
      setUploading(true);
      setProgress(0);

      const result = await dataManagementService.uploadFile(file, (percent) => {
        setProgress(percent);
      });

      if (result.success) {
        message.success(`${file.name} 上传成功`);
        onSuccess(result);

        // 调用父组件的回调
        if (onUploadSuccess) {
          onUploadSuccess(result);
        }
      } else {
        message.error(result.error || '上传失败');
        onError(new Error(result.error));
      }
    } catch (error) {
      const errorMsg = error.error || error.message || '上传失败';
      message.error(errorMsg);
      onError(error);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const beforeUpload = (file) => {
    const isCSVorTXT = file.type === 'text/csv' ||
                       file.type === 'text/plain' ||
                       file.name.endsWith('.csv') ||
                       file.name.endsWith('.txt');

    if (!isCSVorTXT) {
      message.error('只能上传 CSV 或 TXT 文件！');
      return Upload.LIST_IGNORE;
    }

    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('文件大小不能超过 10MB！');
      return Upload.LIST_IGNORE;
    }

    return true;
  };

  return (
    <Card>
      <Dragger
        name="file"
        multiple={false}
        customRequest={customRequest}
        beforeUpload={beforeUpload}
        showUploadList={false}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持CSV和TXT格式，单个文件不超过10MB
        </p>
      </Dragger>

      {uploading && (
        <div style={{ marginTop: 16 }}>
          <Progress percent={progress} status="active" />
          <p style={{ textAlign: 'center', marginTop: 8, color: '#666' }}>
            上传中... {progress}%
          </p>
        </div>
      )}
    </Card>
  );
};

export default FileUploader;
