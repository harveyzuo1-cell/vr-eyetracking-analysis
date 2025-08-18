import React, { useState } from 'react';
import { languageTexts } from '../../../utils/languages';
import useAppStore from '../../../store/useAppStore';
import './DataImport.css';

const DataImport = () => {
  const { currentLanguage } = useAppStore();
  const texts = languageTexts[currentLanguage];
  
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (files) => {
    // TODO: 实现文件上传逻辑
    console.log('上传文件:', files);
    setUploading(true);
    setUploadProgress(0);
    
    // 模拟上传进度
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress(progress);
      if (progress >= 100) {
        clearInterval(interval);
        setUploading(false);
        setUploadProgress(0);
      }
    }, 200);
  };

  return (
    <div className="module-container data-import-module">
      <div className="module-header">
        <h2 className="module-title">
          <i className="fas fa-upload"></i>
          {texts.dataImport}
        </h2>
        <p className="module-subtitle">
          支持批量上传眼动数据文件，自动处理和校准
        </p>
      </div>

      <div className="module-content">
        <div className="upload-section">
          <div
            className={`upload-area ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('fileInput').click()}
          >
            <input
              type="file"
              id="fileInput"
              multiple
              accept=".txt,.csv"
              onChange={handleChange}
              style={{ display: 'none' }}
            />
            
            {uploading ? (
              <div className="upload-progress">
                <div className="loading-spinner"></div>
                <h4>正在上传文件...</h4>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p>{uploadProgress}% 完成</p>
              </div>
            ) : (
              <div className="upload-placeholder">
                <i className="fas fa-cloud-upload-alt"></i>
                <h4>{texts.dragDropFiles}</h4>
                <p>支持 .txt 和 .csv 格式</p>
                <button className="upload-btn">
                  <i className="fas fa-folder-open"></i>
                  选择文件
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="upload-info">
          <h5>
            <i className="fas fa-info-circle"></i>
            上传说明
          </h5>
          <ul>
            <li>支持多文件同时上传</li>
            <li>支持的格式：.txt、.csv</li>
            <li>文件大小限制：最大 10MB</li>
            <li>系统将自动进行数据预处理和校准</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DataImport;