/**
 * API配置
 */

// API基础URL
export const API_BASE_URL = 'http://127.0.0.1:9090/api';

// API端点
export const API_ENDPOINTS = {
  // 系统信息
  health: '/health',
  info: '/info',

  // 数据管理
  dataGroups: '/data/groups',
  dataSubjects: '/data/subjects',
  dataTasks: '/data/tasks',
  dataRaw: '/data/raw',
  dataImport: '/data/import',

  // MMSE
  mmseScores: '/mmse/scores',
  mmseGroups: '/mmse/groups',

  // RQA分析
  rqaAnalyze: '/rqa/analyze',
  rqaResults: '/rqa/results',
  rqaBatch: '/rqa/batch',

  // 机器学习
  mlTrain: '/ml/train',
  mlPredict: '/ml/predict',
  mlModels: '/ml/models',

  // 校正管理
  calibrationCompleteness: '/module01/calibration/completeness',
};

// 请求超时时间（毫秒）
export const REQUEST_TIMEOUT = 30000;

// 分页配置
export const PAGINATION = {
  defaultPageSize: 20,
  pageSizeOptions: [10, 20, 50, 100],
};
