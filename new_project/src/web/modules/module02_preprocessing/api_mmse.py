"""
Module02 MMSE管理 API

提供MMSE数据的导入、计算、批量操作等功能
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import io
import pandas as pd
from .api_utils import handle_errors, logger
from src.modules.module02_preprocessing.subject_manager import SubjectManager
from src.modules.module02_preprocessing.mmse_manager import MMSEManager
from config.settings import Config

# 初始化管理器
SUBJECT_INFO_DIR = Config.DATA_ROOT / 'subject_info'
CLINICAL_DIR = Config.DATA_ROOT / '01_raw' / 'clinical'

subject_manager = SubjectManager(SUBJECT_INFO_DIR)
mmse_manager = MMSEManager(CLINICAL_DIR)

# 创建子Blueprint
mmse_bp = Blueprint('mmse', __name__)


@mmse_bp.route('/clinical-data', methods=['GET'])
@handle_errors
def get_clinical_mmse_data():
    """获取clinical目录中的MMSE数据"""
    logger.info("Loading clinical MMSE data")
    data = mmse_manager.load_clinical_mmse_data()

    return jsonify({
        'success': True,
        'data': data,
        'count': len(data)
    })


@mmse_bp.route('/import-clinical/<subject_id>', methods=['POST'])
@handle_errors
def import_clinical_mmse(subject_id):
    """从clinical目录导入指定受试者的MMSE数据"""
    logger.info(f"Importing clinical MMSE for subject: {subject_id}")

    # 导入MMSE数据
    mmse_data = mmse_manager.import_clinical_mmse_for_subject(subject_id)

    if mmse_data is None:
        return jsonify({
            'success': False,
            'message': f'未找到受试者 {subject_id} 的MMSE数据'
        }), 404

    # 更新受试者记录
    subject = subject_manager.update_subject(subject_id, mmse=mmse_data)

    if subject is None:
        return jsonify({
            'success': False,
            'message': f'受试者 {subject_id} 不存在，请先创建受试者记录'
        }), 404

    logger.info(f"Clinical MMSE imported successfully for: {subject_id}")
    return jsonify({
        'success': True,
        'data': mmse_data,
        'message': 'MMSE数据导入成功'
    })


@mmse_bp.route('/calculate-scores', methods=['POST'])
@handle_errors
def calculate_mmse_scores():
    """计算MMSE得分"""
    data = request.get_json()

    # 计算分项得分
    section_scores = mmse_manager.calculate_section_scores(data)

    # 计算总分
    total_score = mmse_manager.calculate_total_score(data)

    # 获取认知状态
    cognitive_status = mmse_manager.get_cognitive_status(total_score)

    logger.info(f"MMSE scores calculated: total={total_score}, status={cognitive_status}")
    return jsonify({
        'success': True,
        'data': {
            'section_scores': section_scores,
            'total_score': total_score,
            'cognitive_status': cognitive_status
        }
    })


@mmse_bp.route('/csv-template', methods=['GET'])
@handle_errors
def download_csv_template():
    """下载MMSE批量导入CSV模板"""
    from tempfile import NamedTemporaryFile

    # 创建临时文件
    with NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        temp_path = Path(f.name)
        mmse_manager.generate_csv_template(temp_path)

    logger.info("MMSE CSV template generated")
    return send_file(
        temp_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name='mmse_template.csv'
    )


@mmse_bp.route('/batch-import-csv', methods=['POST'])
@handle_errors
def batch_import_mmse_csv():
    """从CSV批量导入MMSE数据"""
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

    logger.info(f"Batch importing MMSE from CSV: {file.filename}")

    # 保存到临时文件
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False, suffix='.csv') as f:
        file.save(f.name)
        temp_path = Path(f.name)

    # 导入数据
    results = mmse_manager.import_from_csv(temp_path)

    # 更新受试者记录
    updated_count = 0
    for item in results['success']:
        subject_id = item['subject_id']
        mmse_data = item['data']

        subject = subject_manager.update_subject(subject_id, mmse=mmse_data)
        if subject:
            updated_count += 1

    # 删除临时文件
    temp_path.unlink()

    logger.info(f"MMSE batch import completed: {updated_count} subjects updated")
    return jsonify({
        'success': True,
        'data': {
            'total': results['total'],
            'imported': len(results['success']),
            'updated': updated_count,
            'failed': len(results['failed']),
            'errors': results['failed'][:10]  # 只返回前10个错误
        }
    })


@mmse_bp.route('/download-v2-template', methods=['GET'])
@handle_errors
def download_v2_mmse_template():
    """下载V2受试者MMSE批量导入CSV模板"""
    import json

    # 读取V2受试者数据
    scan_result_file = Config.DATA_ROOT / '01_raw' / 'scan_result_v2.json'

    if not scan_result_file.exists():
        return jsonify({
            'success': False,
            'message': 'V2数据文件不存在，请先扫描V2数据'
        }), 404

    with open(scan_result_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)

    # 提取所有subject_id
    v2_subjects = []
    for group in ['control', 'mci', 'ad']:
        for subject in scan_data.get(group, []):
            v2_subjects.append(subject['subject_id'])

    # 创建CSV模板
    headers = [
        'subject_id', 'test_date',
        'q1_year', 'q1_season', 'q1_month', 'q1_weekday',
        'q2_province', 'q2_street', 'q2_building', 'q2_floor',
        'q3_immediate',
        'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
        'q5_word1', 'q5_word2', 'q5_word3',
        'total_score'
    ]

    # 创建DataFrame，subject_id列预填充
    data = [{'subject_id': sid} for sid in v2_subjects]
    df = pd.DataFrame(data, columns=headers)

    # 保存到BytesIO
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)

    logger.info(f"V2 MMSE template generated with {len(v2_subjects)} subjects")
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='v2_mmse_template.csv'
    )


@mmse_bp.route('/batch-import-v2', methods=['POST'])
@handle_errors
def batch_import_v2_mmse():
    """从CSV批量导入V2受试者MMSE数据"""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '没有上传文件'
        }), 400

    file = request.files['file']
    logger.info(f"Batch importing V2 MMSE from: {file.filename}")

    # 读取CSV
    df = pd.read_csv(io.BytesIO(file.read()))

    success_count = 0
    failed_count = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            subject_id = str(row['subject_id'])

            # 检查受试者是否存在
            subject = subject_manager.get_subject(subject_id)
            if not subject:
                failed_count += 1
                errors.append(f"{subject_id}: 受试者不存在")
                continue

            # 解析MMSE数据
            mmse_data = mmse_manager.parse_csv_row(row.to_dict())

            # 计算分数
            mmse_data['section_scores'] = mmse_manager.calculate_section_scores(mmse_data)
            if 'total_score' not in mmse_data or pd.isna(mmse_data['total_score']):
                mmse_data['total_score'] = mmse_manager.calculate_total_score(mmse_data)

            # 更新受试者
            subject_manager.update_subject(subject_id, mmse=mmse_data)
            success_count += 1

        except Exception as e:
            failed_count += 1
            errors.append(f"行 {idx + 2}: {str(e)}")

    logger.info(f"V2 MMSE batch import completed: {success_count} success, {failed_count} failed")
    return jsonify({
        'success': True,
        'data': {
            'success': success_count,
            'failed': failed_count,
            'errors': errors[:10]
        }
    })
