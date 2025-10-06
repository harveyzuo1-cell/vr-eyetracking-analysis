"""
数据API路由

提供数据查询和加载接口
"""
from flask import Blueprint, request, jsonify
import logging

from src.core.data_loader import DataLoader
from src.core.validators import DataValidator
from config.settings import Config

logger = logging.getLogger(__name__)

# 创建Blueprint
data_bp = Blueprint('data', __name__, url_prefix='/api/data')

# 初始化工具类
data_loader = DataLoader(Config)
validator = DataValidator(Config)


@data_bp.route('/groups', methods=['GET'])
def get_groups():
    """
    获取所有组别列表

    Returns:
        JSON: 组别列表
    """
    try:
        groups = Config.VALID_GROUPS

        # 统计每个组的受试者数量
        group_info = []
        for group in groups:
            subjects = data_loader.list_subjects(group, stage='raw')
            group_info.append({
                'id': group,
                'name': {
                    'control': '对照组 (Control)',
                    'mci': '轻度认知障碍 (MCI)',
                    'ad': '阿尔茨海默症 (AD)'
                }.get(group, group),
                'count': len(subjects)
            })

        return jsonify({
            'success': True,
            'data': group_info
        })

    except Exception as e:
        logger.error(f"获取组别列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'获取组别列表失败: {str(e)}'
        }), 500


@data_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """
    获取指定组别的受试者列表

    Query Params:
        group: 组别 (control/mci/ad)
        stage: 数据阶段，默认为raw

    Returns:
        JSON: 受试者列表
    """
    try:
        group = request.args.get('group', 'control')
        stage = request.args.get('stage', 'raw')

        # 验证组别
        if group not in Config.VALID_GROUPS:
            return jsonify({
                'success': False,
                'error': f'无效的组别: {group}'
            }), 400

        # 获取受试者列表
        subjects = data_loader.list_subjects(group, stage=stage)

        # 构建详细信息
        subject_info = []
        for subject_id in subjects:
            tasks = data_loader.list_tasks(group, subject_id, stage=stage)
            subject_info.append({
                'id': subject_id,
                'group': group,
                'task_count': len(tasks),
                'tasks': tasks
            })

        return jsonify({
            'success': True,
            'data': subject_info
        })

    except Exception as e:
        logger.error(f"获取受试者列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'获取受试者列表失败: {str(e)}'
        }), 500


@data_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    获取指定受试者的任务列表

    Query Params:
        group: 组别
        subject_id: 受试者ID
        stage: 数据阶段，默认为raw

    Returns:
        JSON: 任务列表
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        stage = request.args.get('stage', 'raw')

        if not group or not subject_id:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: group, subject_id'
            }), 400

        # 获取任务列表
        tasks = data_loader.list_tasks(group, subject_id, stage=stage)

        return jsonify({
            'success': True,
            'data': tasks
        })

    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'获取任务列表失败: {str(e)}'
        }), 500


@data_bp.route('/raw', methods=['GET'])
def load_raw_data():
    """
    加载原始眼动数据

    Query Params:
        group: 组别
        subject_id: 受试者ID
        task_id: 任务ID

    Returns:
        JSON: 眼动数据
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task_id = request.args.get('task_id')

        if not all([group, subject_id, task_id]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: group, subject_id, task_id'
            }), 400

        # 加载数据
        df = data_loader.load_raw_data(group, subject_id, task_id)

        # 验证数据
        is_valid, errors = validator.validate_eyetracking_data(df, stage='raw')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': '数据验证失败',
                'validation_errors': errors
            }), 400

        # 转换为JSON格式
        data_dict = df.to_dict('records')

        # 添加统计信息
        stats = {
            'total_points': len(df),
            'duration': df['time'].max() - df['time'].min() if 'time' in df.columns else 0,
            'x_range': [float(df['x'].min()), float(df['x'].max())] if 'x' in df.columns else [0, 0],
            'y_range': [float(df['y'].min()), float(df['y'].max())] if 'y' in df.columns else [0, 0]
        }

        return jsonify({
            'success': True,
            'data': data_dict,
            'stats': stats,
            'metadata': {
                'group': group,
                'subject_id': subject_id,
                'task_id': task_id
            }
        })

    except FileNotFoundError as e:
        logger.warning(f"数据文件不存在: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'数据文件不存在: {str(e)}'
        }), 404

    except Exception as e:
        logger.error(f"加载数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'加载数据失败: {str(e)}'
        }), 500


@data_bp.route('/processed', methods=['GET'])
def load_processed_data():
    """
    加载处理后的数据

    Query Params:
        group: 组别
        subject_id: 受试者ID
        task_id: 任务ID
        stage: 数据阶段 (preprocessed/calibrated)

    Returns:
        JSON: 处理后的数据
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task_id = request.args.get('task_id')
        stage = request.args.get('stage', 'preprocessed')

        if not all([group, subject_id, task_id]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: group, subject_id, task_id'
            }), 400

        # 加载数据
        df = data_loader.load_processed_data(group, subject_id, task_id, stage=stage)

        # 转换为JSON
        data_dict = df.to_dict('records')

        return jsonify({
            'success': True,
            'data': data_dict,
            'metadata': {
                'group': group,
                'subject_id': subject_id,
                'task_id': task_id,
                'stage': stage
            }
        })

    except FileNotFoundError as e:
        logger.warning(f"数据文件不存在: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'数据文件不存在: {str(e)}'
        }), 404

    except Exception as e:
        logger.error(f"加载数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'加载数据失败: {str(e)}'
        }), 500
