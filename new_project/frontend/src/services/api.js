/**
 * API服务基础封装
 */
import axios from 'axios';
import { message } from 'antd';
import { API_BASE_URL, REQUEST_TIMEOUT } from '../config/api';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }

    console.log('API请求:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    const { data } = response;

    // 统一处理响应格式
    if (data.success === false) {
      message.error(data.error || '请求失败');
      return Promise.reject(new Error(data.error || '请求失败'));
    }

    return data;
  },
  (error) => {
    // 处理各种错误情况
    if (error.response) {
      // 服务器返回了错误状态码
      const { status, data } = error.response;
      const url = error.config?.url || '';

      // 对于calibration API的404，静默处理（没有校准数据是正常情况）
      const isCalibrationNotFound = status === 404 && url.includes('/calibration/');

      switch (status) {
        case 400:
          message.error(data.error || '请求参数错误');
          break;
        case 404:
          if (!isCalibrationNotFound) {
            message.error(data.error || '请求的资源不存在');
          }
          break;
        case 500:
          message.error(data.error || '服务器内部错误');
          break;
        default:
          message.error(data.error || `请求失败: ${status}`);
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      message.error('网络错误，请检查网络连接');
    } else {
      // 其他错误
      message.error(error.message || '请求失败');
    }

    return Promise.reject(error);
  }
);

// 导出API方法
export const api = {
  /**
   * GET请求
   */
  get: (url, params = {}) => {
    return apiClient.get(url, { params });
  },

  /**
   * POST请求
   */
  post: (url, data = {}) => {
    return apiClient.post(url, data);
  },

  /**
   * PUT请求
   */
  put: (url, data = {}) => {
    return apiClient.put(url, data);
  },

  /**
   * DELETE请求
   */
  delete: (url, params = {}) => {
    return apiClient.delete(url, { params });
  },
};

export default apiClient;
