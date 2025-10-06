/**
 * ROI服务 - 获取ROI配置
 */
import { api } from './api';

export const roiService = {
  /**
   * 获取ROI配置 (简单版本)
   * @param {string} version - 数据版本 (v1/v2)
   * @param {string} task - 任务ID (q1/q2/q3/q4/q5/all)
   * @returns {Promise<Object>}
   */
  getROIConfig: async (version, task) => {
    try {
      const response = await api.get('/data/roi', { version, task });
      return response;
    } catch (error) {
      console.error('Failed to fetch ROI config:', error);
      return { success: false, data: null, error: error.message };
    }
  },

  /**
   * 获取增强版ROI配置 (支持多层ROI)
   * @param {string} version - 数据版本 (v1/v2)
   * @param {string} task - 任务ID (q1/q2/q3/q4/q5/all)
   * @returns {Promise<Object>}
   */
  getROIConfigEnhanced: async (version, task) => {
    try {
      const response = await api.get('/data/roi-enhanced', { version, task });
      return response;
    } catch (error) {
      console.error('Failed to fetch enhanced ROI config:', error);
      return { success: false, data: null, error: error.message };
    }
  },

  /**
   * 计算ROI统计信息
   * @param {string} version - 数据版本 (v1/v2)
   * @param {string} task - 任务ID (q1/q2/q3/q4/q5/all)
   * @param {Array<Object>} gazeData - 眼动数据 [{x, y, timestamp}, ...]
   * @returns {Promise<Object>}
   */
  calculateROIStats: async (version, task, gazeData) => {
    try {
      const response = await api.post('/data/roi-stats', {
        version,
        task,
        gaze_data: gazeData
      });
      return response;
    } catch (error) {
      console.error('Failed to calculate ROI stats:', error);
      return { success: false, data: null, error: error.message };
    }
  }
};

export default roiService;
