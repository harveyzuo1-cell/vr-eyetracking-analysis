/**
 * 数据相关API服务
 */
import { api } from './api';
import { API_ENDPOINTS } from '../config/api';

export const dataService = {
  /**
   * 获取系统信息
   */
  getSystemInfo: () => {
    return api.get(API_ENDPOINTS.info);
  },

  /**
   * 健康检查
   */
  healthCheck: () => {
    return api.get(API_ENDPOINTS.health);
  },

  /**
   * 获取组别列表
   * @param {string} version - 数据版本 (all/v1/v2)，可选
   */
  getGroups: (version = 'all') => {
    return api.get(API_ENDPOINTS.dataGroups, { version });
  },

  /**
   * 获取受试者列表
   * @param {string} group - 组别 (control/mci/ad)
   * @param {string} version - 数据版本 (all/v1/v2)，可选
   */
  getSubjects: (group, version = 'all') => {
    return api.get(API_ENDPOINTS.dataSubjects, { group, version });
  },

  /**
   * 获取任务列表
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   */
  getTasks: (group, subjectId) => {
    return api.get(API_ENDPOINTS.dataTasks, { group, subject_id: subjectId });
  },

  /**
   * 加载原始数据
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   * @param {string} taskId - 任务ID
   */
  loadRawData: (group, subjectId, taskId) => {
    return api.get(API_ENDPOINTS.dataRaw, {
      group,
      subject_id: subjectId,
      task_id: taskId,
    });
  },

  /**
   * 加载受试者的所有任务数据(Q1-Q5)
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   */
  loadAllTasksData: (group, subjectId) => {
    return api.get(`${API_ENDPOINTS.dataRaw}/all`, {
      group,
      subject_id: subjectId,
    });
  },

  /**
   * 导入数据
   * @param {Object} data - 导入数据
   */
  importData: (data) => {
    return api.post(API_ENDPOINTS.dataImport, data);
  },

  /**
   * 检查校正完成度
   * @param {string} version - 数据版本 (v1/v2/all)
   */
  checkCalibrationCompleteness: (version = 'all') => {
    return api.get(API_ENDPOINTS.calibrationCompleteness, { version });
  },
};

export default dataService;
