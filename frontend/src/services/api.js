import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.data || error.message);
    
    // 统一错误处理
    const errorMessage = error.response?.data?.message || 
                        error.response?.statusText || 
                        error.message || 
                        '网络请求失败';
    
    return Promise.reject(new Error(errorMessage));
  }
);

// API方法封装
export const apiService = {
  // 数据管理相关
  async getGroups() {
    const response = await api.get('/api/groups');
    return response.data;
  },

  async getGroupData(groupType) {
    const response = await api.get(`/api/group/${groupType}/data`);
    return response.data;
  },

  async getDataInfo(dataId) {
    const response = await api.get(`/api/data/${dataId}/info`);
    return response.data;
  },

  async deleteData(dataId) {
    const response = await api.delete(`/api/data/${dataId}`);
    return response.data;
  },

  // 可视化相关
  async generateVisualization(groupType, dataId, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const response = await api.get(
      `/api/visualize/${groupType}/${dataId}?${queryString}`
    );
    return response.data;
  },

  async generateHeatmap(dataIds, params = {}) {
    const response = await api.post('/api/generate-heatmap', {
      data_ids: dataIds,
      ...params
    });
    return response.data;
  },

  // RQA分析相关
  async startRQABatchRender(params) {
    const response = await api.post('/api/rqa-batch-render', params);
    return response.data;
  },

  async getRQARenderStatus(paramSignature) {
    const params = paramSignature ? { param_signature: paramSignature } : {};
    const response = await api.get('/api/rqa-render-status', { params });
    return response.data;
  },

  async getRQARenderedResults(filters = {}) {
    const response = await api.get('/api/rqa-rendered-results', { 
      params: filters 
    });
    return response.data;
  },

  async getRQAParameterPresets() {
    const response = await api.get('/api/rqa-parameters/presets');
    return response.data;
  },

  // RQA流程相关
  async runRQAPipelineStep(stepName, params) {
    const response = await api.post(`/api/rqa-pipeline/${stepName}`, {
      parameters: params
    });
    return response.data;
  },

  async getRQAPipelineStatus(params) {
    const response = await api.get('/api/rqa-pipeline/status', { params });
    return response.data;
  },

  async getRQAPipelineHistory() {
    const response = await api.get('/api/rqa-pipeline/param-history');
    return response.data;
  },

  async getRQAPipelineResults(signature) {
    const response = await api.get(`/api/rqa-pipeline/results/${signature}`);
    return response.data;
  },

  async deleteRQAPipelineResults(signature) {
    const response = await api.delete(`/api/rqa-pipeline/delete/${signature}`);
    return response.data;
  },

  // 事件分析相关
  async getEventAnalysisData(params = {}) {
    const response = await api.get('/api/event-analysis/data', { params });
    return response.data;
  },

  async getEventAnalysisROISummary(params = {}) {
    const response = await api.get('/api/event-analysis/roi-summary', { params });
    return response.data;
  },

  async regenerateEventAnalysis(params = {}) {
    const response = await api.post('/api/event-analysis/regenerate', params);
    return response.data;
  },

  // 特征提取相关
  async checkDataSources() {
    const response = await api.get('/api/feature-extraction/check-sources');
    return response.data;
  },

  async extractFeatures(params) {
    const response = await api.post('/api/feature-extraction/extract', params);
    return response.data;
  },

  async getExtractionHistory() {
    const response = await api.get('/api/feature-extraction/history');
    return response.data;
  },

  // 文件上传相关
  async uploadFiles(files, onProgress) {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file_${index}`, file);
    });

    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  // 系统相关
  async getSystemStatus() {
    const response = await api.get('/api/system/status');
    return response.data;
  },

  async getSystemConfig() {
    const response = await api.get('/api/system/config');
    return response.data;
  },
};

export default api;