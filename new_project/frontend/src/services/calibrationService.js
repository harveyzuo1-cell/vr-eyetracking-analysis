/**
 * 眼动数据校正服务
 * Gaze Data Calibration Service
 *
 * 提供校正数据的保存、加载和管理功能
 */
import axios from 'axios';

const API_BASE = '/api/module01/calibration';

// 创建自定义axios实例，静默处理404（没有校准数据是正常情况）
const calibrationAxios = axios.create({
  validateStatus: function (status) {
    // 将404视为成功，避免在console显示错误
    return (status >= 200 && status < 300) || status === 404;
  }
});

class CalibrationService {
  /**
   * 保存校正数据
   * @param {Object} payload - 校正数据
   * @param {string} payload.group - 组别 (control/mci/ad)
   * @param {string} payload.subject_id - 受试者ID
   * @param {string} payload.task - 任务ID
   * @param {Object} payload.params - 校正参数
   * @param {number} payload.params.offsetX - X轴偏移 (-0.4~0.4)
   * @param {number} payload.params.offsetY - Y轴偏移 (-0.4~0.4)
   * @param {number} payload.params.trimStart - 起始裁剪秒数 (0~60)
   * @param {number} payload.params.trimEnd - 结束裁剪秒数 (0~60)
   * @returns {Promise<Object>} 保存结果
   */
  async saveCalibration(payload) {
    try {
      const response = await axios.post(`${API_BASE}/save`, payload);
      return response.data;
    } catch (error) {
      console.error('Save calibration error:', error);
      throw this._handleError(error);
    }
  }

  /**
   * 获取已保存的校正参数
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   * @param {string} task - 任务ID
   * @returns {Promise<Object|null>} 校正参数，不存在返回null
   */
  async getCalibrationParams(group, subjectId, task) {
    try {
      const response = await axios.get(`${API_BASE}/params`, {
        params: { group, subject_id: subjectId, task }
      });
      return response.data.data;
    } catch (error) {
      console.error('Get calibration params error:', error);
      throw this._handleError(error);
    }
  }

  /**
   * 加载校正后的数据
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   * @param {string} task - 任务ID
   * @returns {Promise<Array>} 校正后的数据点数组
   */
  async loadCalibratedData(group, subjectId, task) {
    try {
      const response = await calibrationAxios.get(`${API_BASE}/data`, {
        params: { group, subject_id: subjectId, task }
      });
      // 404表示没有校正数据，这是正常情况
      if (response.status === 404) {
        return null;
      }
      return response.data.data;
    } catch (error) {
      // 其他错误才打印
      console.error('Load calibrated data error:', error);
      throw this._handleError(error);
    }
  }

  /**
   * 删除校正数据
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   * @param {string} task - 任务ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteCalibration(group, subjectId, task) {
    try {
      const response = await axios.delete(`${API_BASE}/delete`, {
        params: { group, subject_id: subjectId, task }
      });
      return response.data;
    } catch (error) {
      console.error('Delete calibration error:', error);
      throw this._handleError(error);
    }
  }

  /**
   * 获取校准版本列表
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   * @param {string} task - 任务ID
   * @returns {Promise<Array>} 版本列表
   */
  async getVersions(group, subjectId, task) {
    try {
      const response = await axios.get(`${API_BASE}/versions`, {
        params: { group, subject_id: subjectId, task }
      });
      return response.data;
    } catch (error) {
      console.error('Get versions error:', error);
      throw this._handleError(error);
    }
  }

  /**
   * 恢复到指定版本
   * @param {string} group - 组别
   * @param {string} subjectId - 受试者ID
   * @param {string} task - 任务ID
   * @param {number} version - 版本号
   * @returns {Promise<Object>} 恢复结果
   */
  async restoreVersion(group, subjectId, task, version) {
    try {
      const response = await axios.post(`${API_BASE}/restore`, {
        group,
        subject_id: subjectId,
        task,
        version
      });
      return response.data;
    } catch (error) {
      console.error('Restore version error:', error);
      throw this._handleError(error);
    }
  }

  /**
   * 健康检查
   * @returns {Promise<Object>} API健康状态
   */
  async healthCheck() {
    try {
      const response = await axios.get(`${API_BASE}/health`);
      return response.data;
    } catch (error) {
      console.error('Health check error:', error);
      throw this._handleError(error);
    }
  }

  /**
   * 处理错误
   * @private
   */
  _handleError(error) {
    if (error.response) {
      // 服务器返回错误状态
      const { status, data } = error.response;
      return new Error(data.message || `请求失败 (${status})`);
    } else if (error.request) {
      // 请求发送但没有响应
      return new Error('网络错误，请检查连接');
    } else {
      // 其他错误
      return new Error(error.message || '未知错误');
    }
  }

  /**
   * 前端计算预览数据
   * @param {Array} data - 原始数据
   * @param {Object} params - 校正参数
   * @returns {Array} 预览数据
   */
  calculatePreview(data, params) {
    if (!data || data.length === 0) {
      return [];
    }

    let processed = [...data];

    // 1. 应用位置偏移
    const offsetX = params.offsetX || 0;
    const offsetY = params.offsetY || 0;

    if (offsetX !== 0 || offsetY !== 0) {
      processed = processed.map(point => ({
        ...point,
        x: point.x + offsetX,
        y: point.y + offsetY
      }));
    }

    // 2. 应用时间裁剪
    const trimStart = params.trimStart || 0;
    const trimEnd = params.trimEnd || 0;

    if (trimStart > 0 || trimEnd > 0) {
      const timestamps = processed.map(p => p.timestamp);
      const minTime = Math.min(...timestamps);
      const maxTime = Math.max(...timestamps);

      const startThreshold = minTime + trimStart;
      const endThreshold = maxTime - trimEnd;

      processed = processed.filter(point =>
        point.timestamp >= startThreshold && point.timestamp <= endThreshold
      );

      // 重置timestamp从0开始
      if (processed.length > 0) {
        const newMinTime = Math.min(...processed.map(p => p.timestamp));
        processed = processed.map(point => ({
          ...point,
          timestamp: point.timestamp - newMinTime
        }));
      }
    }

    return processed;
  }

  /**
   * 验证校正参数
   * @param {Object} params - 校正参数
   * @returns {Object} 验证结果 {valid: boolean, errors: Array}
   */
  validateParams(params) {
    const errors = [];

    // 验证offsetX
    if (params.offsetX !== undefined) {
      if (typeof params.offsetX !== 'number') {
        errors.push('offsetX must be a number');
      } else if (params.offsetX < -0.4 || params.offsetX > 0.4) {
        errors.push('offsetX must be between -0.4 and 0.4');
      }
    }

    // 验证offsetY
    if (params.offsetY !== undefined) {
      if (typeof params.offsetY !== 'number') {
        errors.push('offsetY must be a number');
      } else if (params.offsetY < -0.4 || params.offsetY > 0.4) {
        errors.push('offsetY must be between -0.4 and 0.4');
      }
    }

    // 验证trimStart
    if (params.trimStart !== undefined) {
      if (typeof params.trimStart !== 'number') {
        errors.push('trimStart must be a number');
      } else if (params.trimStart < 0 || params.trimStart > 60) {
        errors.push('trimStart must be between 0 and 60');
      }
    }

    // 验证trimEnd
    if (params.trimEnd !== undefined) {
      if (typeof params.trimEnd !== 'number') {
        errors.push('trimEnd must be a number');
      } else if (params.trimEnd < 0 || params.trimEnd > 60) {
        errors.push('trimEnd must be between 0 and 60');
      }
    }

    // 验证组合
    if (params.trimStart && params.trimEnd) {
      if (params.trimStart + params.trimEnd > 60) {
        errors.push('Combined trim cannot exceed 60 seconds');
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

// 导出单例
const calibrationService = new CalibrationService();
export default calibrationService;
