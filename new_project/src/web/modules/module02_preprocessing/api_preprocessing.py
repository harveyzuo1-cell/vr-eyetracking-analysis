"""
Module02 数据预处理 API

提供数据质量检测、清洗、平滑等预处理功能
"""

from flask import Blueprint, request, jsonify
from .api_utils import handle_errors, logger
from src.modules.module02_preprocessing import QualityChecker, DataCleaner, DataSmoother, Pipeline

# 初始化预处理模块
quality_checker = QualityChecker()
data_cleaner = DataCleaner()
data_smoother = DataSmoother()
pipeline = Pipeline()

# 创建子Blueprint
preprocessing_bp = Blueprint('preprocessing', __name__)


@preprocessing_bp.route('/quality-check', methods=['POST'])
@handle_errors
def quality_check():
    """数据质量检测"""
    data = request.get_json()
    gaze_data = data.get('gaze_data', [])

    logger.info(f"Quality check requested for {len(gaze_data)} data points")
    result = quality_checker.check(gaze_data)

    return jsonify({
        'success': True,
        'data': result
    })


@preprocessing_bp.route('/clean', methods=['POST'])
@handle_errors
def clean_data():
    """数据清洗"""
    data = request.get_json()
    gaze_data = data.get('gaze_data', [])

    logger.info(f"Data cleaning requested for {len(gaze_data)} data points")
    cleaned_data = data_cleaner.clean(gaze_data)

    return jsonify({
        'success': True,
        'data': cleaned_data
    })


@preprocessing_bp.route('/smooth', methods=['POST'])
@handle_errors
def smooth_data():
    """数据平滑"""
    data = request.get_json()
    gaze_data = data.get('gaze_data', [])
    method = data.get('method', 'savgol')  # savgol, moving_average

    logger.info(f"Data smoothing requested: method={method}, {len(gaze_data)} points")
    smoothed_data = data_smoother.smooth(gaze_data, method=method)

    return jsonify({
        'success': True,
        'data': smoothed_data
    })


@preprocessing_bp.route('/pipeline', methods=['POST'])
@handle_errors
def run_pipeline():
    """运行完整预处理流水线"""
    data = request.get_json()
    gaze_data = data.get('gaze_data', [])
    config = data.get('config', {})

    logger.info(f"Running preprocessing pipeline for {len(gaze_data)} data points")
    result = pipeline.run(gaze_data, config=config)

    return jsonify({
        'success': True,
        'data': result
    })


@preprocessing_bp.route('/config/default', methods=['GET'])
@handle_errors
def get_default_config():
    """获取默认预处理配置"""
    default_config = {
        'quality_check': {
            'max_velocity': 1000,  # pixels/second
            'min_duration': 50,    # milliseconds
        },
        'cleaning': {
            'remove_outliers': True,
            'interpolate_missing': True,
        },
        'smoothing': {
            'method': 'savgol',
            'window_length': 5,
            'polyorder': 2,
        }
    }

    return jsonify({
        'success': True,
        'data': default_config
    })
