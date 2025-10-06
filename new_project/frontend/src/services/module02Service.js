/**
 * Module02 API服务
 * 提供受试者管理和数据预处理相关的API调用
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:9090/api/m02';

/**
 * 受试者管理相关API
 */
export const subjectService = {
  // 获取所有受试者
  getAllSubjects: async () => {
    const response = await axios.get(`${API_BASE_URL}/subjects`);
    return response.data;
  },

  // 获取单个受试者
  getSubject: async (subjectId) => {
    const response = await axios.get(`${API_BASE_URL}/subjects/${subjectId}`);
    return response.data;
  },

  // 创建受试者
  createSubject: async (data) => {
    const response = await axios.post(`${API_BASE_URL}/subjects`, data);
    return response.data;
  },

  // 更新受试者
  updateSubject: async (subjectId, data) => {
    const response = await axios.put(`${API_BASE_URL}/subjects/${subjectId}`, data);
    return response.data;
  },

  // 删除受试者
  deleteSubject: async (subjectId) => {
    const response = await axios.delete(`${API_BASE_URL}/subjects/${subjectId}`);
    return response.data;
  },

  // 更新受试者MMSE
  updateMMSE: async (subjectId, mmseData) => {
    const response = await axios.put(`${API_BASE_URL}/subjects/${subjectId}/mmse`, mmseData);
    return response.data;
  },

  // 获取统计信息
  getStatistics: async () => {
    const response = await axios.get(`${API_BASE_URL}/subjects/statistics`);
    return response.data;
  },

  // 获取教育程度选项
  getEducationLevels: async () => {
    const response = await axios.get(`${API_BASE_URL}/education-levels`);
    return response.data;
  },

  // 从Clinical批量导入受试者
  importFromClinical: async () => {
    const response = await axios.post(`${API_BASE_URL}/subjects/import-from-clinical`);
    return response.data;
  },
};

/**
 * MMSE数据管理相关API
 */
export const mmseService = {
  // 获取clinical目录中的所有MMSE数据
  getClinicalData: async () => {
    const response = await axios.get(`${API_BASE_URL}/mmse/clinical-data`);
    return response.data;
  },

  // 为指定受试者导入clinical中的MMSE数据
  importClinicalData: async (subjectId) => {
    const response = await axios.post(`${API_BASE_URL}/mmse/import-clinical/${subjectId}`);
    return response.data;
  },

  // 下载MMSE批量导入CSV模板
  downloadTemplate: () => {
    window.open(`${API_BASE_URL}/mmse/csv-template`, '_blank');
  },

  // 批量导入MMSE数据（从CSV文件）
  batchImport: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/mmse/batch-import-csv`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
};

/**
 * 数据预处理相关API
 */
export const preprocessingService = {
  // 质量检测
  qualityCheck: async (data, config = {}) => {
    const response = await axios.post(`${API_BASE_URL}/preprocessing/quality-check`, {
      data,
      config
    });
    return response.data;
  },

  // 数据清洗
  cleanData: async (data, config = {}) => {
    const response = await axios.post(`${API_BASE_URL}/preprocessing/clean`, {
      data,
      config
    });
    return response.data;
  },

  // 数据平滑
  smoothData: async (data, config = {}) => {
    const response = await axios.post(`${API_BASE_URL}/preprocessing/smooth`, {
      data,
      config
    });
    return response.data;
  },

  // 运行完整预处理流水线
  runPipeline: async (data, config = {}) => {
    const response = await axios.post(`${API_BASE_URL}/preprocessing/pipeline`, {
      data,
      config
    });
    return response.data;
  },

  // 获取默认配置
  getDefaultConfig: async () => {
    const response = await axios.get(`${API_BASE_URL}/preprocessing/config/default`);
    return response.data;
  },
};

export default {
  subject: subjectService,
  mmse: mmseService,
  preprocessing: preprocessingService,
};
