/**
 * Module 00: 数据管理服务
 * Data Management Service
 */
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:9090/api/m00';

class DataManagementService {
  /**
   * 上传文件
   * @param {File} file - 文件对象
   * @param {Function} onProgress - 进度回调函数
   * @returns {Promise} 上传结果
   */
  async uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percent);
          }
        }
      });

      return response.data;
    } catch (error) {
      console.error('文件上传失败:', error);
      throw error.response?.data || { error: '文件上传失败' };
    }
  }

  /**
   * 获取已上传文件列表
   * @returns {Promise} 文件列表
   */
  async getFiles() {
    try {
      const response = await axios.get(`${API_BASE_URL}/files`);
      return response.data;
    } catch (error) {
      console.error('获取文件列表失败:', error);
      throw error.response?.data || { error: '获取文件列表失败' };
    }
  }

  /**
   * 保存文件到01_raw目录
   * @param {Object} data - 保存数据
   * @param {string} data.filename - 文件名
   * @param {string} data.group - 组别
   * @param {string} data.subject_id - 受试者ID
   * @param {string} data.task_id - 任务ID
   * @param {string} data.notes - 备注
   * @returns {Promise} 保存结果
   */
  async saveToRaw(data) {
    try {
      const response = await axios.post(`${API_BASE_URL}/save`, data);
      return response.data;
    } catch (error) {
      console.error('保存文件失败:', error);
      throw error.response?.data || { error: '保存文件失败' };
    }
  }

  /**
   * 删除已上传的文件
   * @param {string} filename - 文件名
   * @returns {Promise} 删除结果
   */
  async deleteFile(filename) {
    try {
      const response = await axios.delete(`${API_BASE_URL}/delete/${filename}`);
      return response.data;
    } catch (error) {
      console.error('删除文件失败:', error);
      throw error.response?.data || { error: '删除文件失败' };
    }
  }

  /**
   * 预览文件内容
   * @param {string} filename - 文件名
   * @param {number} rows - 预览行数
   * @returns {Promise} 预览数据
   */
  async previewFile(filename, rows = 100) {
    try {
      const response = await axios.get(`${API_BASE_URL}/preview/${filename}`, {
        params: { rows }
      });
      return response.data;
    } catch (error) {
      console.error('预览文件失败:', error);
      throw error.response?.data || { error: '预览文件失败' };
    }
  }

  /**
   * 验证文件数据质量
   * @param {string} filename - 文件名
   * @returns {Promise} 验证结果
   */
  async validateFile(filename) {
    try {
      const response = await axios.get(`${API_BASE_URL}/validate/${filename}`);
      return response.data;
    } catch (error) {
      console.error('验证文件失败:', error);
      throw error.response?.data || { error: '验证文件失败' };
    }
  }
}

export default new DataManagementService();
