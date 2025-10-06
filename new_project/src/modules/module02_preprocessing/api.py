"""
Module 02 API 路由

提供以下功能的 API 接口:
- 受试者信息管理 (CRUD)
- MMSE 数据管理
- 数据质量检测
- 数据预处理
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import pandas as pd

from .subject_manager import SubjectManager, EDUCATION_LEVELS
from config.settings import Config

# 创建 Blueprint
m02_bp = Blueprint('module02', __name__, url_prefix='/api/m02')

# 初始化受试者管理器
subject_manager = SubjectManager(Config.DATA_DIR)


# ==================== 受试者信息管理 API ====================

@m02_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """
    获取受试者列表

    Query参数:
        group: 组别筛选 (control/mci/ad)，可选
        with_mmse: 是否包含MMSE信息，默认false
    """
    try:
        group = request.args.get('group')
        with_mmse = request.args.get('with_mmse', 'false').lower() == 'true'

        subjects = subject_manager.get_all_subjects(group=group, with_mmse=with_mmse)

        return jsonify({
            'success': True,
            'data': subjects,
            'count': len(subjects)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects/<subject_id>', methods=['GET'])
def get_subject(subject_id):
    """获取单个受试者详细信息"""
    try:
        subject = subject_manager.get_subject(subject_id)

        if subject is None:
            return jsonify({
                'success': False,
                'message': f'受试者 {subject_id} 不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': subject
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects', methods=['POST'])
def create_subject():
    """
    创建新受试者

    请求体:
    {
        "subject_id": "n1",
        "group": "control",
        "demographics": {
            "gender": "male",
            "age": 65,
            "education_level": "undergraduate"
        },
        "mmse": {  // 可选
            "total_score": 28,
            "test_date": "2024-03-15",
            "sub_scores": {
                "orientation": 10,
                "registration": 3,
                "attention": 5,
                "recall": 3,
                "language": 7
            }
        }
    }
    """
    try:
        data = request.get_json()

        subject_id = data.get('subject_id')
        group = data.get('group')
        demographics = data.get('demographics')
        mmse = data.get('mmse')

        # 检查是否已存在
        if subject_manager.get_subject(subject_id):
            return jsonify({
                'success': False,
                'message': f'受试者 {subject_id} 已存在'
            }), 400

        # 创建受试者
        subject = subject_manager.create_subject(
            subject_id=subject_id,
            group=group,
            demographics=demographics,
            mmse=mmse
        )

        return jsonify({
            'success': True,
            'data': subject,
            'message': '受试者创建成功'
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects/<subject_id>', methods=['PUT'])
def update_subject(subject_id):
    """
    更新受试者信息

    请求体:
    {
        "demographics": {  // 可选
            "gender": "male",
            "age": 65,
            "education_level": "undergraduate"
        },
        "mmse": {  // 可选
            "total_score": 28,
            "test_date": "2024-03-15",
            "sub_scores": {...}
        }
    }
    """
    try:
        data = request.get_json()

        demographics = data.get('demographics')
        mmse = data.get('mmse')

        subject = subject_manager.update_subject(
            subject_id=subject_id,
            demographics=demographics,
            mmse=mmse
        )

        if subject is None:
            return jsonify({
                'success': False,
                'message': f'受试者 {subject_id} 不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': subject,
            'message': '更新成功'
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects/<subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    """删除受试者"""
    try:
        success = subject_manager.delete_subject(subject_id)

        if not success:
            return jsonify({
                'success': False,
                'message': f'受试者 {subject_id} 不存在'
            }), 404

        return jsonify({
            'success': True,
            'message': '删除成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects/<subject_id>/mmse', methods=['PUT'])
def update_mmse(subject_id):
    """
    更新受试者的MMSE数据

    请求体:
    {
        "total_score": 28,
        "test_date": "2024-03-15",
        "sub_scores": {
            "orientation": 10,
            "registration": 3,
            "attention": 5,
            "recall": 3,
            "language": 7
        }
    }
    """
    try:
        mmse_data = request.get_json()

        subject = subject_manager.update_subject(
            subject_id=subject_id,
            mmse=mmse_data
        )

        if subject is None:
            return jsonify({
                'success': False,
                'message': f'受试者 {subject_id} 不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': subject.get('mmse'),
            'message': 'MMSE数据更新成功'
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects/statistics', methods=['GET'])
def get_statistics():
    """获取受试者统计信息"""
    try:
        stats = subject_manager.get_statistics()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects/batch-import', methods=['POST'])
def batch_import_subjects():
    """
    批量导入受试者信息

    请求体:
    {
        "subjects": [
            {
                "subject_id": "n1",
                "group": "control",
                "demographics": {...},
                "mmse": {...}
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        subjects_data = data.get('subjects', [])

        results = {
            'success': [],
            'failed': []
        }

        for subject_data in subjects_data:
            try:
                subject_id = subject_data.get('subject_id')

                # 如果已存在，跳过
                if subject_manager.get_subject(subject_id):
                    results['failed'].append({
                        'subject_id': subject_id,
                        'error': '受试者已存在'
                    })
                    continue

                subject_manager.create_subject(
                    subject_id=subject_id,
                    group=subject_data.get('group'),
                    demographics=subject_data.get('demographics'),
                    mmse=subject_data.get('mmse')
                )

                results['success'].append(subject_id)

            except Exception as e:
                results['failed'].append({
                    'subject_id': subject_data.get('subject_id', 'unknown'),
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'data': results,
            'message': f'成功导入 {len(results["success"])} 个受试者，失败 {len(results["failed"])} 个'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/subjects/export', methods=['GET'])
def export_subjects():
    """
    导出受试者信息

    Query参数:
        group: 组别筛选，可选
        format: 格式 (json/csv)，默认json
    """
    try:
        group = request.args.get('group')
        format_type = request.args.get('format', 'json')

        subjects = subject_manager.get_all_subjects(group=group, with_mmse=True)

        if format_type == 'csv':
            # 转换为CSV格式
            rows = []
            for subject in subjects:
                row = {
                    'subject_id': subject['subject_id'],
                    'group': subject['group'],
                    'gender': subject['demographics'].get('gender'),
                    'age': subject['demographics'].get('age'),
                    'education_level': subject['demographics'].get('education_level'),
                    'mmse_total': subject.get('mmse', {}).get('total_score'),
                    'mmse_date': subject.get('mmse', {}).get('test_date'),
                }

                # 添加MMSE子分数
                sub_scores = subject.get('mmse', {}).get('sub_scores', {})
                row.update({
                    'mmse_orientation': sub_scores.get('orientation'),
                    'mmse_registration': sub_scores.get('registration'),
                    'mmse_attention': sub_scores.get('attention'),
                    'mmse_recall': sub_scores.get('recall'),
                    'mmse_language': sub_scores.get('language')
                })

                rows.append(row)

            df = pd.DataFrame(rows)
            csv_data = df.to_csv(index=False)

            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=subjects.csv'
            }
        else:
            # JSON格式
            return jsonify({
                'success': True,
                'data': subjects
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/education-levels', methods=['GET'])
def get_education_levels():
    """获取教育程度选项"""
    return jsonify({
        'success': True,
        'data': EDUCATION_LEVELS
    })


# ==================== 数据预处理 API ====================
# 这些API将在后续实现其他算法类后添加

@m02_bp.route('/load-data', methods=['GET'])
def load_data():
    """
    加载原始数据用于预处理

    Query参数:
        group: 组别
        subject_id: 受试者ID
        task: 任务ID
        version: 数据版本
    """
    try:
        group = request.args.get('group')
        subject_id = request.args.get('subject_id')
        task = request.args.get('task')
        version = request.args.get('version', 'v1')

        # TODO: 实现数据加载逻辑
        # 目前返回占位响应

        return jsonify({
            'success': True,
            'message': '数据加载功能开发中',
            'data': {
                'group': group,
                'subject_id': subject_id,
                'task': task,
                'version': version
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/quality-check', methods=['POST'])
def quality_check():
    """数据质量检测 - 待实现"""
    return jsonify({
        'success': True,
        'message': '质量检测功能开发中'
    })


@m02_bp.route('/clean-data', methods=['POST'])
def clean_data():
    """数据清洗 - 待实现"""
    return jsonify({
        'success': True,
        'message': '数据清洗功能开发中'
    })


@m02_bp.route('/smooth-data', methods=['POST'])
def smooth_data():
    """数据平滑 - 待实现"""
    return jsonify({
        'success': True,
        'message': '数据平滑功能开发中'
    })
