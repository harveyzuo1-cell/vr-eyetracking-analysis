// 多语言文本配置
export const languageTexts = {
  zh: {
    // 基础界面
    title: 'VR眼球追踪数据可视化平台',
    subtitle: '三组认知功能评估的VR眼球追踪数据分析与可视化平台',
    restart: '重启',
    confirmRestart: '确定要重启应用程序吗？',
    
    // 统计标签
    totalData: '数据总数',
    researchGroups: '研究组别',
    controlGroup: '健康对照组',
    mciGroup: '轻度认知障碍组',
    adGroup: '阿尔茨海默组',
    
    // 导航模块
    dataVisualization: '数据可视化',
    dataImport: '数据导入',
    rqaAnalysis: 'RQA分析',
    eventAnalysis: '事件分析',
    rqaPipeline: 'RQA分析流程',
    featureExtraction: '综合特征提取',
    dataOrganization: '数据整理',
    
    // 过滤器
    taskFilter: '任务过滤',
    all: '全部',
    task1: '任务1',
    task2: '任务2',
    task3: '任务3',
    task4: '任务4',
    task5: '任务5',
    
    // 数据列表
    dataList: '数据列表',
    loading: '加载中...',
    refresh: '刷新',
    noData: '暂无数据',
    loadFailed: '加载失败',
    dataItems: '个数据',
    
    // 可视化相关
    selectDataTitle: '选择数据开始分析',
    selectDataSubtitle: '点击左侧的数据项来生成专业的眼动轨迹可视化分析',
    eyeTrackingVis: '眼动轨迹可视化',
    visControls: '可视化控制',
    fixationSize: '注视点大小:',
    trajectoryWidth: '轨迹线宽:',
    pointSize: '数据点大小:',
    trajectoryStyle: '轨迹样式:',
    solidLine: '实线',
    dashedLine: '虚线',
    dottedLine: '点线',
    updateVis: '更新可视化',
    generatingVis: '正在生成可视化...',
    
    // 统计信息
    overallStats: '整体统计',
    duration: '持续时间',
    totalFixations: '总注视次数',
    totalSaccades: '总扫视次数',
    avgFixationDuration: '平均注视时长',
    avgSaccadeAmplitude: '平均扫视幅度',
    roiStatistics: 'ROI统计',
    
    // 通用按钮和操作
    edit: '编辑',
    delete: '删除',
    save: '保存',
    cancel: '取消',
    confirm: '确认',
    upload: '上传',
    download: '下载',
    export: '导出',
    import: '导入',
    
    // 错误和提示信息
    error: '错误',
    success: '成功',
    warning: '警告',
    info: '信息',
    deleteDataConfirm: '确定要删除数据 "{0}" 吗？',
    deleteDataSuccess: '数据删除成功',
    deleteDataFailed: '数据删除失败',
    
    // RQA相关
    rqaParameters: 'RQA参数',
    embeddingDim: '嵌入维度',
    timeDelay: '时间延迟',
    recurrenceThreshold: '递归阈值',
    minLineLength: '最小线长',
    analysisMode: '分析模式',
    distanceMetric: '距离度量',
    colorTheme: '颜色主题',
    
    // 事件分析相关
    eventType: '事件类型',
    fixation: '注视',
    saccade: '扫视',
    roiFilter: 'ROI过滤',
    regenerateAnalysis: '重新生成分析',
    
    // 特征提取相关
    dataSource: '数据源',
    extractionStatus: '提取状态',
    available: '可用',
    notAvailable: '不可用',
    extractFeatures: '提取特征',
    extractionHistory: '提取历史',
    
    // 文件上传相关
    dragDropFiles: '拖拽文件到此处或点击选择',
    supportedFormats: '支持的格式',
    uploadProgress: '上传进度',
    processingFiles: '处理文件中...',
    uploadComplete: '上传完成',
    uploadFailed: '上传失败'
  },
  
  en: {
    // Basic interface
    title: 'VR Eye Tracking Data Visualization Platform',
    subtitle: 'VR Eye Tracking Data Analysis and Visualization Platform for Three Cognitive Assessment Groups',
    restart: 'Restart',
    confirmRestart: 'Are you sure you want to restart the application?',
    
    // Statistics labels
    totalData: 'Total Data',
    researchGroups: 'Research Groups',
    controlGroup: 'Control Group',
    mciGroup: 'MCI Group',
    adGroup: 'AD Group',
    
    // Navigation modules
    dataVisualization: 'Data Visualization',
    dataImport: 'Data Import',
    rqaAnalysis: 'RQA Analysis',
    eventAnalysis: 'Event Analysis',
    rqaPipeline: 'RQA Pipeline',
    featureExtraction: 'Feature Extraction',
    dataOrganization: 'Data Organization',
    
    // Filters
    taskFilter: 'Task Filter',
    all: 'All',
    task1: 'Task 1',
    task2: 'Task 2',
    task3: 'Task 3',
    task4: 'Task 4',
    task5: 'Task 5',
    
    // Data list
    dataList: 'Data List',
    loading: 'Loading...',
    refresh: 'Refresh',
    noData: 'No Data',
    loadFailed: 'Load Failed',
    dataItems: ' items',
    
    // Visualization
    selectDataTitle: 'Select Data to Start Analysis',
    selectDataSubtitle: 'Click on the data items on the left to generate professional eye movement trajectory visualization analysis',
    eyeTrackingVis: 'Eye Tracking Visualization',
    visControls: 'Visualization Controls',
    fixationSize: 'Fixation Size:',
    trajectoryWidth: 'Trajectory Width:',
    pointSize: 'Point Size:',
    trajectoryStyle: 'Trajectory Style:',
    solidLine: 'Solid',
    dashedLine: 'Dashed',
    dottedLine: 'Dotted',
    updateVis: 'Update Visualization',
    generatingVis: 'Generating visualization...',
    
    // Statistics
    overallStats: 'Overall Statistics',
    duration: 'Duration',
    totalFixations: 'Total Fixations',
    totalSaccades: 'Total Saccades',
    avgFixationDuration: 'Avg Fixation Duration',
    avgSaccadeAmplitude: 'Avg Saccade Amplitude',
    roiStatistics: 'ROI Statistics',
    
    // Common buttons and operations
    edit: 'Edit',
    delete: 'Delete',
    save: 'Save',
    cancel: 'Cancel',
    confirm: 'Confirm',
    upload: 'Upload',
    download: 'Download',
    export: 'Export',
    import: 'Import',
    
    // Error and prompt messages
    error: 'Error',
    success: 'Success',
    warning: 'Warning',
    info: 'Info',
    deleteDataConfirm: 'Are you sure you want to delete data "{0}"?',
    deleteDataSuccess: 'Data deleted successfully',
    deleteDataFailed: 'Failed to delete data',
    
    // RQA related
    rqaParameters: 'RQA Parameters',
    embeddingDim: 'Embedding Dimension',
    timeDelay: 'Time Delay',
    recurrenceThreshold: 'Recurrence Threshold',
    minLineLength: 'Min Line Length',
    analysisMode: 'Analysis Mode',
    distanceMetric: 'Distance Metric',
    colorTheme: 'Color Theme',
    
    // Event analysis related
    eventType: 'Event Type',
    fixation: 'Fixation',
    saccade: 'Saccade',
    roiFilter: 'ROI Filter',
    regenerateAnalysis: 'Regenerate Analysis',
    
    // Feature extraction related
    dataSource: 'Data Source',
    extractionStatus: 'Extraction Status',
    available: 'Available',
    notAvailable: 'Not Available',
    extractFeatures: 'Extract Features',
    extractionHistory: 'Extraction History',
    
    // File upload related
    dragDropFiles: 'Drag files here or click to select',
    supportedFormats: 'Supported Formats',
    uploadProgress: 'Upload Progress',
    processingFiles: 'Processing files...',
    uploadComplete: 'Upload Complete',
    uploadFailed: 'Upload Failed'
  }
};