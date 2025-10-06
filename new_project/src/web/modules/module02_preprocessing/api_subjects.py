"""
Module02 受试者管理 API

提供受试者信息的CRUD操作
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
from .api_utils import handle_errors, logger
from src.modules.module02_preprocessing.subject_manager import SubjectManager
from config.settings import Config
import io

# 初始化受试者管理器
SUBJECT_INFO_DIR = Config.DATA_ROOT / 'subject_info'
SUBJECT_INFO_DIR.mkdir(parents=True, exist_ok=True)
subject_manager = SubjectManager(SUBJECT_INFO_DIR)

# 创建子Blueprint
subjects_bp = Blueprint('subjects', __name__)


@subjects_bp.route('', methods=['GET'])
@handle_errors
def get_subjects():
    """
    获取受试者列表

    Query参数:
        group: 组别筛选 (control/mci/ad)，可选
        with_mmse: 是否包含MMSE信息，默认false
    """
    group = request.args.get('group')
    with_mmse = request.args.get('with_mmse', 'false').lower() == 'true'

    logger.info(f"Fetching subjects: group={group}, with_mmse={with_mmse}")
    subjects = subject_manager.get_all_subjects(group=group, with_mmse=with_mmse)

    return jsonify({
        'success': True,
        'data': subjects,
        'count': len(subjects)
    })


@subjects_bp.route('/<subject_id>', methods=['GET'])
@handle_errors
def get_subject(subject_id):
    """获取单个受试者详细信息"""
    logger.info(f"Fetching subject: {subject_id}")
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


@subjects_bp.route('', methods=['POST'])
@handle_errors
def create_subject():
    """创建新受试者"""
    data = request.get_json()

    subject_id = data.get('subject_id')
    group = data.get('group')
    demographics = data.get('demographics')
    mmse = data.get('mmse')

    logger.info(f"Creating subject: {subject_id}")

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

    logger.info(f"Subject created successfully: {subject_id}")
    return jsonify({
        'success': True,
        'data': subject,
        'message': '创建成功'
    })


@subjects_bp.route('/<subject_id>', methods=['PUT'])
@handle_errors
def update_subject(subject_id):
    """更新受试者信息"""
    data = request.get_json()

    demographics = data.get('demographics')
    mmse = data.get('mmse')

    logger.info(f"Updating subject: {subject_id}")
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

    logger.info(f"Subject updated successfully: {subject_id}")
    return jsonify({
        'success': True,
        'data': subject,
        'message': '更新成功'
    })


@subjects_bp.route('/<subject_id>', methods=['DELETE'])
@handle_errors
def delete_subject(subject_id):
    """删除受试者"""
    logger.info(f"Deleting subject: {subject_id}")
    success = subject_manager.delete_subject(subject_id)

    if not success:
        return jsonify({
            'success': False,
            'message': f'受试者 {subject_id} 不存在'
        }), 404

    logger.info(f"Subject deleted successfully: {subject_id}")
    return jsonify({
        'success': True,
        'message': '删除成功'
    })


@subjects_bp.route('/statistics', methods=['GET'])
@handle_errors
def get_statistics():
    """获取受试者统计信息"""
    logger.info("Fetching subject statistics")
    stats = subject_manager.get_statistics()
    logger.info(f"Statistics retrieved: {stats['total_subjects']} total subjects")

    return jsonify({
        'success': True,
        'data': stats
    })


@subjects_bp.route('/batch-import', methods=['POST'])
@handle_errors
def batch_import_subjects():
    """批量导入受试者（CSV格式）"""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '没有上传文件'
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '文件名为空'
        }), 400

    logger.info(f"Batch importing subjects from: {file.filename}")

    # 读取CSV
    import pandas as pd
    df = pd.read_csv(io.BytesIO(file.read()))

    success_count = 0
    failed_count = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            subject_id = str(row['subject_id'])

            # 跳过已存在的
            if subject_manager.get_subject(subject_id):
                continue

            subject_manager.create_subject(
                subject_id=subject_id,
                group=row['group'],
                demographics={
                    'gender': row['gender'],
                    'age': int(row['age']),
                    'education_level': row['education_level']
                }
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"行 {idx + 2}: {str(e)}")

    logger.info(f"Batch import completed: {success_count} success, {failed_count} failed")
    return jsonify({
        'success': True,
        'data': {
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors[:10]  # 只返回前10个错误
        }
    })


@subjects_bp.route('/export', methods=['GET'])
@handle_errors
def export_subjects():
    """导出受试者列表为CSV"""
    import pandas as pd
    from flask import send_file

    subjects = subject_manager.get_all_subjects(with_mmse=True)

    # 转换为DataFrame
    data = []
    for subject in subjects:
        row = {
            'subject_id': subject['subject_id'],
            'group': subject['group'],
            'gender': subject['demographics']['gender'],
            'age': subject['demographics']['age'],
            'education_level': subject['demographics']['education_level'],
        }

        # 添加MMSE数据
        if subject.get('mmse'):
            row['mmse_score'] = subject['mmse'].get('total_score', '')
            row['test_date'] = subject['mmse'].get('test_date', '')

        data.append(row)

    df = pd.DataFrame(data)

    # 保存到临时文件
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)

    logger.info(f"Exporting {len(subjects)} subjects to CSV")
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='subjects_export.csv'
    )
