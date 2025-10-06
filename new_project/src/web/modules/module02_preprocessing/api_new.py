"""
Module 02 API 主路由

整合所有子模块的API端点:
- 受试者管理 (api_subjects.py)
- MMSE数据管理 (api_mmse.py)
- 数据预处理 (api_preprocessing.py)
"""

from flask import Blueprint, jsonify, request
from .api_utils import handle_errors, logger
from .api_subjects import subjects_bp
from .api_mmse import mmse_bp
from .api_preprocessing import preprocessing_bp

# 导入其他需要的模块
from src.modules.module02_preprocessing.subject_manager import EDUCATION_LEVELS
from config.settings import Config
import json

# 创建主 Blueprint
m02_bp = Blueprint('module02', __name__, url_prefix='/api/m02')

# 注册子Blueprint
m02_bp.register_blueprint(subjects_bp, url_prefix='/subjects')
m02_bp.register_blueprint(mmse_bp, url_prefix='/mmse')
m02_bp.register_blueprint(preprocessing_bp, url_prefix='/preprocessing')


# ==================== 辅助端点 ====================

@m02_bp.route('/education-levels', methods=['GET'])
@handle_errors
def get_education_levels():
    """获取教育程度枚举值"""
    return jsonify({
        'success': True,
        'data': EDUCATION_LEVELS
    })


@m02_bp.route('/load-data', methods=['GET'])
@handle_errors
def load_preprocessed_data():
    """加载预处理后的数据"""
    subject_id = request.args.get('subject_id')
    task = request.args.get('task')

    if not subject_id or not task:
        return jsonify({
            'success': False,
            'message': '缺少subject_id或task参数'
        }), 400

    # 构建文件路径
    data_file = Config.DATA_ROOT / '02_preprocessed' / subject_id / f'{task}.json'

    if not data_file.exists():
        return jsonify({
            'success': False,
            'message': f'未找到数据文件: {data_file}'
        }), 404

    # 读取数据
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded preprocessed data: {subject_id}/{task}")
    return jsonify({
        'success': True,
        'data': data
    })


@m02_bp.route('/subjects/import-from-clinical', methods=['POST'])
@handle_errors
def import_subjects_from_clinical():
    """从clinical目录批量导入受试者基础信息"""
    from src.modules.module02_preprocessing.subject_manager import SubjectManager

    SUBJECT_INFO_DIR = Config.DATA_ROOT / 'subject_info'
    subject_manager = SubjectManager(SUBJECT_INFO_DIR)

    # 读取clinical/subjects.json
    clinical_subjects_file = Config.DATA_ROOT / '01_raw' / 'clinical' / 'subjects.json'

    if not clinical_subjects_file.exists():
        return jsonify({
            'success': False,
            'message': 'clinical/subjects.json 不存在'
        }), 404

    with open(clinical_subjects_file, 'r', encoding='utf-8') as f:
        clinical_data = json.load(f)

    success_count = 0
    failed_count = 0
    skipped_count = 0
    errors = []

    for subject_id, info in clinical_data.items():
        try:
            # 检查是否已存在
            if subject_manager.get_subject(subject_id):
                skipped_count += 1
                continue

            # 创建受试者
            subject_manager.create_subject(
                subject_id=subject_id,
                group=info['group'],
                demographics={
                    'gender': info['demographics']['gender'],
                    'age': info['demographics']['age'],
                    'education_level': info['demographics']['education_level']
                }
            )
            success_count += 1

        except Exception as e:
            failed_count += 1
            errors.append({
                'subject_id': subject_id,
                'error': str(e)
            })

    logger.info(f"Clinical import completed: {success_count} success, {skipped_count} skipped, {failed_count} failed")
    return jsonify({
        'success': True,
        'data': {
            'success': success_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'errors': errors[:10]
        }
    })


@m02_bp.route('/subjects/get-v2-subjects', methods=['GET'])
@handle_errors
def get_v2_subjects():
    """获取V2眼动数据的受试者列表"""
    scan_result_file = Config.DATA_ROOT / '01_raw' / 'scan_result_v2.json'

    if not scan_result_file.exists():
        return jsonify({
            'success': False,
            'message': 'scan_result_v2.json 不存在，请先扫描V2数据'
        }), 404

    with open(scan_result_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)

    # 整合所有组别的受试者
    all_subjects = []
    for group in ['control', 'mci', 'ad']:
        for subject in scan_data.get(group, []):
            subject['group'] = group
            all_subjects.append(subject)

    logger.info(f"Retrieved {len(all_subjects)} V2 subjects")
    return jsonify({
        'success': True,
        'data': all_subjects
    })


@m02_bp.route('/subjects/import-v2-subjects', methods=['POST'])
@handle_errors
def import_v2_subjects():
    """从V2眼动数据导入受试者基础信息"""
    from src.modules.module02_preprocessing.subject_manager import SubjectManager

    SUBJECT_INFO_DIR = Config.DATA_ROOT / 'subject_info'
    subject_manager = SubjectManager(SUBJECT_INFO_DIR)

    scan_result_file = Config.DATA_ROOT / '01_raw' / 'scan_result_v2.json'

    if not scan_result_file.exists():
        return jsonify({
            'success': False,
            'message': 'scan_result_v2.json 不存在'
        }), 404

    with open(scan_result_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)

    success_count = 0
    failed_count = 0
    skipped_count = 0
    errors = []

    for group in ['control', 'mci', 'ad']:
        for subject in scan_data.get(group, []):
            try:
                subject_id = subject['subject_id']

                # 检查是否已存在
                if subject_manager.get_subject(subject_id):
                    skipped_count += 1
                    continue

                # 创建受试者（V2数据没有demographics，使用默认值）
                subject_manager.create_subject(
                    subject_id=subject_id,
                    group=group,
                    demographics={
                        'gender': 'male',  # 默认值
                        'age': 65,  # 默认值
                        'education_level': 'undergraduate'  # 默认值
                    }
                )
                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append({
                    'subject_id': subject_id,
                    'error': str(e)
                })

    logger.info(f"V2 import completed: {success_count} success, {skipped_count} skipped, {failed_count} failed")
    return jsonify({
        'success': True,
        'data': {
            'success': success_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'errors': errors[:10]
        }
    })


# ==================== 健康检查 ====================

@m02_bp.route('/health', methods=['GET'])
def health_check():
    """API健康检查"""
    return jsonify({
        'success': True,
        'module': 'module02',
        'status': 'healthy',
        'endpoints': {
            'subjects': f'{m02_bp.url_prefix}/subjects',
            'mmse': f'{m02_bp.url_prefix}/mmse',
            'preprocessing': f'{m02_bp.url_prefix}/preprocessing'
        }
    })
