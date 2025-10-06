/**
 * 任务配置服务
 * Task Configuration Service
 *
 * 提供动态任务配置查询功能
 */
import { API_BASE_URL } from '../config/api';

const TASK_CONFIG_API = `${API_BASE_URL}/task-config`;

/**
 * 任务配置服务类
 */
class TaskConfigService {
  /**
   * 获取所有数据集列表
   * @returns {Promise<Object>} API响应
   */
  async getDatasets() {
    try {
      const response = await fetch(`${TASK_CONFIG_API}/datasets`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching datasets:', error);
      return {
        success: false,
        error: error.message,
        data: []
      };
    }
  }

  /**
   * 获取特定数据集的详细配置
   * @param {string} datasetId - 数据集ID
   * @returns {Promise<Object>} API响应
   */
  async getDataset(datasetId) {
    try {
      const response = await fetch(`${TASK_CONFIG_API}/datasets/${datasetId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching dataset ${datasetId}:`, error);
      return {
        success: false,
        error: error.message,
        data: null
      };
    }
  }

  /**
   * 获取数据集的任务列表
   * @param {string} datasetId - 数据集ID
   * @returns {Promise<Object>} API响应
   */
  async getTasks(datasetId) {
    try {
      const response = await fetch(`${TASK_CONFIG_API}/tasks?dataset_id=${datasetId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching tasks for ${datasetId}:`, error);
      return {
        success: false,
        error: error.message,
        data: null
      };
    }
  }

  /**
   * 获取特定任务的配置
   * @param {string} datasetId - 数据集ID
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} API响应
   */
  async getTask(datasetId, taskId) {
    try {
      const response = await fetch(`${TASK_CONFIG_API}/tasks/${taskId}?dataset_id=${datasetId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching task ${taskId}:`, error);
      return {
        success: false,
        error: error.message,
        data: null
      };
    }
  }

  /**
   * 根据任务列表推断数据集类型
   * @param {Array<string>} tasks - 任务ID列表
   * @returns {Promise<Object>} API响应
   */
  async inferDataset(tasks) {
    try {
      const response = await fetch(`${TASK_CONFIG_API}/infer-dataset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tasks })
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error inferring dataset:', error);
      return {
        success: false,
        error: error.message,
        data: null
      };
    }
  }

  /**
   * 标准化任务ID (将备用ID转换为主ID)
   * @param {string} datasetId - 数据集ID
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} API响应
   */
  async normalizeTaskId(datasetId, taskId) {
    try {
      const response = await fetch(
        `${TASK_CONFIG_API}/normalize-task-id?dataset_id=${datasetId}&task_id=${taskId}`
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error normalizing task ID:', error);
      return {
        success: false,
        error: error.message,
        data: null
      };
    }
  }

  /**
   * 健康检查
   * @returns {Promise<Object>} API响应
   */
  async healthCheck() {
    try {
      const response = await fetch(`${TASK_CONFIG_API}/health`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// 导出单例实例
export const taskConfigService = new TaskConfigService();
