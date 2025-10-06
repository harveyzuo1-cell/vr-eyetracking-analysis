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
from functools import wraps

# 从 src/modules 导入核心功能类
from src.modules.module02_preprocessing.subject_manager import SubjectManager, EDUCATION_LEVELS
from src.modules.module02_preprocessing.mmse_manager import MMSEManager
from src.modules.module02_preprocessing.v1_data_manager import V1DataManager
from src.modules.module02_preprocessing.v2_data_manager import V2DataManager
from config.settings import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# 错误处理装饰器
def handle_errors(f):
    """统一的错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except FileNotFoundError as e:
            logger.error(f"File not found in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': '文件未找到'
            }), 404
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': '服务器内部错误'
            }), 500
    return decorated_function

# 创建 Blueprint
m02_bp = Blueprint('module02', __name__, url_prefix='/api/m02')

# 初始化受试者管理器 - 使用 DATA_ROOT/subject_info 作为存储目录
SUBJECT_INFO_DIR = Config.DATA_ROOT / 'subject_info'
SUBJECT_INFO_DIR.mkdir(parents=True, exist_ok=True)  # 确保目录存在
subject_manager = SubjectManager(SUBJECT_INFO_DIR)

# 初始化MMSE管理器 - 使用 DATA_ROOT/01_raw/clinical 目录
CLINICAL_DIR = Config.DATA_ROOT / '01_raw' / 'clinical'
mmse_manager = MMSEManager(CLINICAL_DIR)

# 初始化V1/V2数据管理器
v1_manager = V1DataManager(Config.DATA_ROOT)
v2_manager = V2DataManager(Config.DATA_ROOT, subject_manager)

# 初始化预处理模块
from src.modules.module02_preprocessing import QualityChecker, DataCleaner, DataSmoother, Pipeline
import io

quality_checker = QualityChecker()
data_cleaner = DataCleaner()
data_smoother = DataSmoother()
pipeline = Pipeline()


# ==================== 受试者信息管理 API ====================

@m02_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """
    获取受试者列表（支持版本筛选）

    Query参数:
        group: 组别筛选 (control/mci/ad)，可选
        with_mmse: 是否包含MMSE信息，默认false
        data_version: 数据版本筛选 (v1/v2)，可选
    """
    try:
        group = request.args.get('group')
        with_mmse = request.args.get('with_mmse', 'false').lower() == 'true'
        data_version = request.args.get('data_version')  # 新增

        subjects = subject_manager.get_all_subjects(
            group=group,
            with_mmse=with_mmse,
            data_version=data_version
        )

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


# 旧的占位符API已迁移到 /preprocessing/* 路由


# ==================== MMSE数据导入 API ====================

@m02_bp.route('/mmse/clinical-data', methods=['GET'])
def get_clinical_mmse_data():
    """
    获取clinical目录中的所有MMSE数据

    Returns:
        所有受试者的MMSE数据（从clinical/mmse_scores.json）
    """
    try:
        all_mmse_data = mmse_manager.load_clinical_mmse_data()

        return jsonify({
            'success': True,
            'data': all_mmse_data,
            'count': len(all_mmse_data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/mmse/import-clinical/<subject_id>', methods=['POST'])
def import_clinical_mmse_for_subject(subject_id: str):
    """
    为指定受试者导入clinical中的MMSE数据

    Path参数:
        subject_id: clinical数据中的受试者ID（如 "control_legacy_1"）
    """
    try:
        # 从clinical导入MMSE数据
        mmse_data = mmse_manager.import_clinical_mmse_for_subject(subject_id)

        if mmse_data is None:
            return jsonify({
                'success': False,
                'message': f'未找到受试者 {subject_id} 的MMSE数据'
            }), 404

        # 更新对应受试者的MMSE数据（如果受试者已存在）
        subject = subject_manager.get_subject(subject_id)
        if subject:
            subject_manager.update_subject(
                subject_id=subject_id,
                mmse=mmse_data
            )
            message = f'成功导入并更新受试者 {subject_id} 的MMSE数据'
        else:
            message = f'成功导入受试者 {subject_id} 的MMSE数据（受试者不存在于系统中，仅返回数据）'

        return jsonify({
            'success': True,
            'data': mmse_data,
            'message': message
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/mmse/calculate-scores', methods=['POST'])
def calculate_mmse_scores():
    """
    计算MMSE分项得分和总分

    Request Body:
        MMSE详细题目数据（包含q1_year, q2_province等字段）

    Returns:
        计算后的分项得分和总分
    """
    try:
        mmse_data = request.get_json()

        # 验证数据
        errors = mmse_manager.validate_mmse_data(mmse_data)
        if errors:
            return jsonify({
                'success': False,
                'message': '数据验证失败',
                'errors': errors
            }), 400

        # 计算分项得分
        section_scores = mmse_manager.calculate_section_scores(mmse_data)

        # 计算总分
        total_score = mmse_manager.calculate_total_score(mmse_data)

        # 判断认知状态
        cognitive_status = mmse_manager.get_cognitive_status(total_score)

        return jsonify({
            'success': True,
            'data': {
                'section_scores': section_scores,
                'total_score': total_score,
                'cognitive_status': cognitive_status
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@m02_bp.route('/mmse/csv-template', methods=['GET'])
def download_mmse_csv_template():
    """
    下载MMSE批量导入CSV模板

    Returns:
        CSV模板文件
    """
    try:
        from flask import send_file
        import tempfile

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8', newline='')
        temp_path = Path(temp_file.name)
        temp_file.close()

        # 生成模板
        mmse_manager.generate_csv_template(temp_path)

        # 发送文件
        return send_file(
            str(temp_path),
            mimetype='text/csv',
            as_attachment=True,
            download_name='mmse_import_template.csv'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@m02_bp.route('/mmse/batch-import-csv', methods=['POST'])
def batch_import_mmse_from_csv():
    """
    批量导入MMSE数据（从CSV文件）

    Request:
        multipart/form-data with file upload
        - file: CSV文件
        - update_existing: 是否更新已存在的受试者 (true/false)

    Returns:
        导入结果统计
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未找到上传文件'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400

        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'message': '仅支持CSV文件'
            }), 400

        # 获取参数
        update_existing = request.form.get('update_existing', 'true').lower() == 'true'

        # 保存上传文件到临时位置
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv')
        temp_path = Path(temp_file.name)
        file.save(temp_path)
        temp_file.close()

        # 从CSV导入
        import_results = mmse_manager.import_from_csv(temp_path)

        # 删除临时文件
        temp_path.unlink()

        # 处理导入结果，更新受试者数据
        update_results = {
            'created': [],
            'updated': [],
            'failed': [],
            'skipped': []
        }

        for success_item in import_results['success']:
            subject_id = success_item['subject_id']
            mmse_data = success_item['data']

            try:
                # 检查受试者是否存在
                subject = subject_manager.get_subject(subject_id)

                if subject:
                    if update_existing:
                        # 更新MMSE数据
                        subject_manager.update_subject(
                            subject_id=subject_id,
                            mmse=mmse_data
                        )
                        update_results['updated'].append({
                            'subject_id': subject_id,
                            'row': success_item['row']
                        })
                    else:
                        update_results['skipped'].append({
                            'subject_id': subject_id,
                            'row': success_item['row'],
                            'reason': '受试者已存在，update_existing=false'
                        })
                else:
                    update_results['skipped'].append({
                        'subject_id': subject_id,
                        'row': success_item['row'],
                        'reason': '受试者不存在，请先创建受试者'
                    })

            except Exception as e:
                update_results['failed'].append({
                    'subject_id': subject_id,
                    'row': success_item['row'],
                    'error': str(e)
                })

        # 合并失败结果
        update_results['failed'].extend(import_results['failed'])

        return jsonify({
            'success': True,
            'data': {
                'total_rows': import_results['total'],
                'csv_parse_success': len(import_results['success']),
                'csv_parse_failed': len(import_results['failed']),
                'updated': len(update_results['updated']),
                'skipped': len(update_results['skipped']),
                'failed': len(update_results['failed']),
                'details': update_results
            },
            'message': f"成功更新 {len(update_results['updated'])} 条，跳过 {len(update_results['skipped'])} 条，失败 {len(update_results['failed'])} 条"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ==================== 数据预处理相关API ====================

@m02_bp.route('/preprocessing/quality-check', methods=['POST'])
def preprocessing_quality_check():
    """数据质量检测"""
    try:
        data = request.json
        if 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            return jsonify({'success': False, 'message': '缺少数据'}), 400
        config = data.get('config', {})
        report = quality_checker.check_quality(df, config)
        return jsonify({'success': True, 'data': report})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@m02_bp.route('/preprocessing/clean', methods=['POST'])
def preprocessing_clean_data():
    """数据清洗"""
    try:
        data = request.json
        if 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            return jsonify({'success': False, 'message': '缺少数据'}), 400
        config = data.get('config', {})
        df_cleaned, log = data_cleaner.clean(df, config)
        return jsonify({'success': True, 'data': {'cleaned_data': df_cleaned.to_dict('records'), 'log': log}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@m02_bp.route('/preprocessing/smooth', methods=['POST'])
def preprocessing_smooth_data():
    """数据平滑"""
    try:
        data = request.json
        if 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            return jsonify({'success': False, 'message': '缺少数据'}), 400
        config = data.get('config', {})
        df_smoothed, log = data_smoother.smooth(df, config)
        return jsonify({'success': True, 'data': {'smoothed_data': df_smoothed.to_dict('records'), 'log': log}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@m02_bp.route('/preprocessing/pipeline', methods=['POST'])
def preprocessing_run_pipeline():
    """运行完整预处理流水线"""
    try:
        data = request.json
        if 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            return jsonify({'success': False, 'message': '缺少数据'}), 400
        config = data.get('config', {})
        df_processed, log = pipeline.process(df, config)
        return jsonify({'success': True, 'data': {'processed_data': df_processed.to_dict('records'), 'log': log}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@m02_bp.route('/preprocessing/config/default', methods=['GET'])
def preprocessing_get_default_config():
    """获取默认预处理配置"""
    try:
        config = pipeline.get_default_config()
        return jsonify({'success': True, 'data': config})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@m02_bp.route('/subjects/import-from-clinical', methods=['POST'])
def import_subjects_from_clinical():
    """从clinical/mmse_scores.json批量导入受试者"""
    try:
        # 加载clinical MMSE数据
        all_mmse_data = mmse_manager.load_clinical_mmse_data()
        
        imported = []
        skipped = []
        failed = []
        
        for subject_id, mmse_data in all_mmse_data.items():
            try:
                # 检查是否已存在
                existing = subject_manager.get_subject(subject_id)
                if existing:
                    skipped.append({'subject_id': subject_id, 'reason': '已存在'})
                    continue
                
                # 准备人口统计学信息
                demographics = {
                    'gender': 'male',  # 默认值，需要后续补充
                    'age': 65,  # 默认值，需要后续补充
                    'education_level': 'undergraduate'  # 默认值，需要后续补充
                }

                # 准备MMSE数据并进行格式转换
                # clinical数据中q1_weekday和q2_province可能是1（布尔值）或2（实际得分）
                # 需要统一转换为实际得分格式（0或2）
                mmse_questions = {k: v for k, v in mmse_data.items() if k.startswith('q')}

                # 转换q1_weekday和q2_province：1→2, 0→0, 2→2
                for field in ['q1_weekday', 'q2_province']:
                    if field in mmse_questions and mmse_questions[field] == 1:
                        mmse_questions[field] = 2

                mmse = {
                    'total_score': mmse_data.get('total_score'),
                    'test_date': mmse_data.get('last_updated', '')[:10] if 'last_updated' in mmse_data else None,
                    **mmse_questions
                }

                # 创建受试者（使用单独参数而不是字典）
                result = subject_manager.create_subject(
                    subject_id=subject_id,
                    group=mmse_data.get('group', 'control'),
                    demographics=demographics,
                    mmse=mmse
                )
                imported.append(subject_id)
                
            except Exception as e:
                import traceback
                error_detail = {
                    'subject_id': subject_id,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                failed.append(error_detail)
                print(f"[DEBUG] 导入失败: {subject_id}, 错误: {str(e)}")
                print(f"[DEBUG] 堆栈: {traceback.format_exc()}")
        
        return jsonify({
            'success': True,
            'data': {
                'imported': imported,
                'skipped': skipped,
                'failed': failed,
                'total': len(all_mmse_data),
                'imported_count': len(imported),
                'skipped_count': len(skipped),
                'failed_count': len(failed)
            },
            'message': f"成功导入 {len(imported)} 个受试者，跳过 {len(skipped)} 个，失败 {len(failed)} 个"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量导入失败: {str(e)}'
        }), 500


@m02_bp.route('/subjects/get-v2-subjects', methods=['GET'])
def get_v2_subjects():
    """获取v2受试者列表（从scan_result_v2.json获取，并检查系统中是否已存在）"""
    try:
        import json
        from pathlib import Path

        # 读取scan_result_v2.json
        project_root = Path(__file__).parent.parent.parent.parent.parent
        scan_file = project_root / 'scan_result_v2.json'

        if not scan_file.exists():
            return jsonify({
                'success': False,
                'message': 'scan_result_v2.json文件不存在'
            }), 404

        with open(scan_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)

        # 提取v2受试者信息
        v2_subjects = []
        if 'eye_tracking_data' in scan_data and 'details' in scan_data['eye_tracking_data']:
            for entry in scan_data['eye_tracking_data']['details'].get('valid_entries', []):
                # 只处理data_version='v2'的数据
                if entry.get('data_version') != 'v2':
                    continue

                subject_id = entry.get('subject_id')
                timestamp = entry.get('timestamp')

                # 检查是否已在subject_info中存在（可能使用原始ID或规范化后的ID）
                existing = subject_manager.get_subject(subject_id)

                # 如果直接查不到，尝试通过original_id+timestamp反向查找
                if not existing:
                    # 遍历该分组下的所有受试者，查找original_id+timestamp匹配的
                    group = entry.get('group_code', 'control')
                    all_subjects = subject_manager.get_all_subjects(group=group, data_version='v2')
                    for subj in all_subjects:
                        meta = subj.get('metadata', {})
                        if (meta.get('original_id') == subject_id and
                            meta.get('timestamp') == timestamp):
                            existing = subj
                            break

                has_mmse = existing and existing.get('mmse') is not None

                # 使用实际存储的ID（可能是规范化后的）
                display_id = existing['subject_id'] if existing else subject_id
                age = existing.get('demographics', {}).get('age') if existing else None
                education = existing.get('demographics', {}).get('education_level') if existing else None

                v2_subjects.append({
                    'subject_id': display_id,  # 显示规范化后的ID
                    'original_id': subject_id,  # 保留原始ID用于追溯
                    'group': entry.get('group_code', 'control'),
                    'hospital_id': entry.get('hospital_id', 'N/A'),
                    'patient_name': entry.get('patient_name'),
                    'timestamp': entry.get('timestamp'),
                    'age': age,
                    'education_level': education,
                    'exists_in_system': existing is not None,
                    'has_mmse': has_mmse
                })

        return jsonify({
            'success': True,
            'data': {
                'subjects': v2_subjects,
                'total': len(v2_subjects)
            }
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@m02_bp.route('/subjects/import-v2-subjects', methods=['POST'])
def import_v2_subjects():
    """从scan_result_v2.json批量导入v2受试者（仅创建基础信息，不含MMSE）"""
    try:
        import json
        from pathlib import Path

        # 读取scan_result_v2.json
        project_root = Path(__file__).parent.parent.parent.parent.parent
        scan_file = project_root / 'scan_result_v2.json'

        if not scan_file.exists():
            return jsonify({
                'success': False,
                'message': 'scan_result_v2.json文件不存在'
            }), 404

        with open(scan_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)

        imported = []
        skipped = []
        failed = []

        # 处理v2受试者
        if 'eye_tracking_data' in scan_data and 'details' in scan_data['eye_tracking_data']:
            for entry in scan_data['eye_tracking_data']['details'].get('valid_entries', []):
                if entry.get('data_version') != 'v2':
                    continue

                subject_id = entry.get('subject_id')

                try:
                    # 检查是否已存在
                    existing = subject_manager.get_subject(subject_id)
                    if existing:
                        skipped.append({
                            'subject_id': subject_id,
                            'reason': '已存在'
                        })
                        continue

                    # 准备基础人口统计学信息（默认值，需要后续补充）
                    demographics = {
                        'gender': 'male',
                        'age': 65,
                        'education_level': 'undergraduate'
                    }

                    # 如果有患者姓名，添加到备注
                    if entry.get('patient_name'):
                        demographics['notes'] = f"患者姓名: {entry['patient_name']}, 医院ID: {entry.get('hospital_id', 'N/A')}, 时间戳: {entry.get('timestamp', '')}"

                    # 创建受试者（不含MMSE数据）
                    result = subject_manager.create_subject(
                        subject_id=subject_id,
                        group=entry.get('group_code', 'control'),
                        demographics=demographics,
                        mmse=None  # v2受试者暂无MMSE数据
                    )

                    imported.append(subject_id)

                except Exception as e:
                    import traceback
                    error_detail = {
                        'subject_id': subject_id,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                    failed.append(error_detail)
                    print(f"[V2 Import Error] {subject_id}: {str(e)}")
                    print(f"[V2 Import Traceback] {traceback.format_exc()}")

        return jsonify({
            'success': True,
            'message': f'导入完成：成功 {len(imported)} 个，跳过 {len(skipped)} 个，失败 {len(failed)} 个',
            'data': {
                'imported': imported,
                'skipped': skipped,
                'failed': failed
            }
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@m02_bp.route('/mmse/download-v2-template', methods=['GET'])
def download_v2_mmse_template():
    """下载V2受试者MMSE批量导入CSV模板"""
    try:
        import io
        import csv
        from flask import send_file
        from pathlib import Path

        # 读取scan_result_v2.json获取v2受试者列表
        project_root = Path(__file__).parent.parent.parent.parent.parent
        scan_file = project_root / 'scan_result_v2.json'

        v2_subject_ids = []
        if scan_file.exists():
            with open(scan_file, 'r', encoding='utf-8') as f:
                scan_data = json.load(f)
                if 'eye_tracking_data' in scan_data and 'details' in scan_data['eye_tracking_data']:
                    for entry in scan_data['eye_tracking_data']['details'].get('valid_entries', []):
                        if entry.get('data_version') == 'v2':
                            v2_subject_ids.append(entry.get('subject_id'))

        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头（包含所有MMSE字段）
        headers = [
            'subject_id',
            'test_date',
            'total_score',
            'q1_year', 'q1_season', 'q1_month', 'q1_weekday',
            'q2_province', 'q2_street', 'q2_building', 'q2_floor',
            'q3_immediate',
            'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
            'q5_word1', 'q5_word2', 'q5_word3'
        ]
        writer.writerow(headers)

        # 写入示例行（第一行）
        example_row = [
            'control_example',  # subject_id示例
            '2024-01-01',       # test_date示例
            '28',               # total_score示例
            '1', '1', '1', '1',  # Q1
            '1', '1', '1', '1',  # Q2
            '1',                 # Q3
            '1', '1', '1', '1', '1',  # Q4
            '1', '1', '1'        # Q5
        ]
        writer.writerow(example_row)

        # 为每个v2受试者添加空白行
        for subject_id in v2_subject_ids:
            row = [subject_id] + [''] * (len(headers) - 1)
            writer.writerow(row)

        # 转换为字节流
        output.seek(0)
        byte_output = io.BytesIO()
        byte_output.write(output.getvalue().encode('utf-8-sig'))  # 使用utf-8-sig以支持Excel
        byte_output.seek(0)

        return send_file(
            byte_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='v2_mmse_template.csv'
        )

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@m02_bp.route('/mmse/batch-import-v2', methods=['POST'])
def batch_import_v2_mmse():
    """从CSV批量导入V2受试者MMSE数据"""
    try:
        import csv
        import io

        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未找到上传文件'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400

        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'message': '只支持CSV文件'
            }), 400

        # 读取CSV
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
        csv_reader = csv.DictReader(stream)

        success_count = 0
        failed_count = 0
        errors = []

        # 逐行处理
        for row_num, row in enumerate(csv_reader, start=2):  # 从第2行开始（第1行是表头）
            try:
                subject_id = row.get('subject_id', '').strip()
                if not subject_id or subject_id == 'control_example':  # 跳过空行和示例行
                    continue

                # 检查受试者是否存在
                subject = subject_manager.get_subject(subject_id)
                if not subject:
                    errors.append({
                        'row': row_num,
                        'subject_id': subject_id,
                        'error': '受试者不存在，请先导入受试者基础信息'
                    })
                    failed_count += 1
                    continue

                # 构建MMSE数据
                mmse_data = {}

                # 测试日期和总分
                if row.get('test_date'):
                    mmse_data['test_date'] = row['test_date'].strip()
                if row.get('total_score'):
                    mmse_data['total_score'] = int(row['total_score'])

                # Q1-Q5各题分数
                mmse_fields = ['q1_year', 'q1_season', 'q1_month', 'q1_weekday',
                               'q2_province', 'q2_street', 'q2_building', 'q2_floor',
                               'q3_immediate',
                               'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
                               'q5_word1', 'q5_word2', 'q5_word3']

                for field in mmse_fields:
                    if row.get(field) and row[field].strip():
                        mmse_data[field] = int(row[field])

                # 如果没有任何MMSE数据，跳过
                if not mmse_data:
                    continue

                # 更新受试者MMSE数据
                subject['mmse'] = mmse_data
                subject_manager.update_subject(
                    subject_id=subject_id,
                    group=subject['group'],
                    demographics=subject['demographics'],
                    mmse=mmse_data
                )

                success_count += 1

            except Exception as e:
                errors.append({
                    'row': row_num,
                    'subject_id': row.get('subject_id', 'unknown'),
                    'error': str(e)
                })
                failed_count += 1

        return jsonify({
            'success': True,
            'message': f'批量导入完成：成功 {success_count} 个，失败 {failed_count} 个',
            'data': {
                'success': success_count,
                'failed': failed_count,
                'errors': errors
            }
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ==================== API文档端点 ====================

from src.web.modules.module02_preprocessing.api_docs import get_api_spec

@m02_bp.route('/docs', methods=['GET'])
def api_docs():
    """
    获取API文档（OpenAPI 3.0规范）
    
    访问此端点获取完整的API规范，可用于：
    - Swagger UI可视化
    - Postman导入
    - 自动生成客户端代码
    
    Returns:
        OpenAPI 3.0 JSON规范
    """
    return get_api_spec()

@m02_bp.route('/docs/ui', methods=['GET'])
def api_docs_ui():
    """
    Swagger UI界面
    
    提供交互式API文档界面
    """
    from flask import render_template_string
    
    swagger_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Module02 API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: '/api/m02/docs',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ]
                })
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(swagger_html)


# ==================== V1/V2数据管理 API ====================

@m02_bp.route('/v1/subjects', methods=['GET'])
@handle_errors
def get_v1_subjects():
    """扫描并获取V1受试者列表"""
    logger.info("Scanning V1 subjects...")
    v1_subjects = v1_manager.scan_v1_subjects()

    return jsonify({
        'success': True,
        'subjects': v1_subjects,
        'total': len(v1_subjects)
    })


@m02_bp.route('/v1/import', methods=['POST'])
@handle_errors
def import_v1_subject():
    """导入单个V1受试者"""
    data = request.get_json()

    subject_id = data.get('subject_id')
    demographics = data.get('demographics', {})

    logger.info(f"Importing V1 subject: {subject_id}")

    result = v1_manager.import_v1_subject(
        subject_id=subject_id,
        demographics=demographics,
        subject_manager=subject_manager
    )

    return jsonify({
        'success': True,
        'subject': result
    })


@m02_bp.route('/v2/batch-import', methods=['POST'])
@handle_errors
def batch_import_v2_subjects():
    """批量导入V2受试者（含ID规范化）"""
    data = request.get_json()

    v2_subjects = data.get('subjects', [])
    rename = data.get('rename', True)  # 默认启用ID规范化
    dry_run = data.get('dry_run', False)

    logger.info(f"Batch importing {len(v2_subjects)} V2 subjects, rename={rename}, dry_run={dry_run}")

    result = v2_manager.batch_import_v2_subjects(
        v2_subjects=v2_subjects,
        rename=rename,
        dry_run=dry_run
    )

    return jsonify({
        'success': True,
        **result
    })


@m02_bp.route('/v2/normalize-preview', methods=['POST'])
@handle_errors
def preview_v2_normalization():
    """预览V2 ID规范化映射"""
    data = request.get_json()
    v2_subjects = data.get('subjects', [])

    logger.info(f"Previewing ID normalization for {len(v2_subjects)} subjects")

    id_mapping = v2_manager.normalize_v2_subject_ids(
        v2_subjects=v2_subjects,
        preview_only=True
    )

    return jsonify({
        'success': True,
        'id_mapping': id_mapping,
        'count': len(id_mapping)
    })


@m02_bp.route('/v2/normalize-existing', methods=['POST'])
@handle_errors
def normalize_existing_v2_subjects():
    """批量规范化现有受试者ID（非规范化格式的）"""
    import re

    data = request.get_json()
    dry_run = data.get('dry_run', False)

    logger.info(f"Normalizing existing subjects (dry_run={dry_run})")

    # 获取所有V2受试者（只规范化V2数据，不处理V1 legacy数据）
    all_subjects = subject_manager.get_all_subjects(data_version='v2')

    # 筛选出非规范化格式的受试者（ID不符合 v2_{group}_{序号} 格式）
    pattern = re.compile(r'^v2_(control|mci|ad)_\d{3}$')

    subjects_to_normalize = [
        s for s in all_subjects
        if not pattern.match(s['subject_id'])
    ]

    if not subjects_to_normalize:
        return jsonify({
            'success': True,
            'message': '所有受试者ID已经是规范化格式',
            'updated': 0,
            'id_mapping': {}
        })

    logger.info(f"Found {len(subjects_to_normalize)} subjects to normalize")

    # 生成ID映射
    subjects_for_normalization = [
        {
            'subject_id': s['subject_id'],
            'group': s['group']
        }
        for s in subjects_to_normalize
    ]

    id_mapping = v2_manager.normalize_v2_subject_ids(
        v2_subjects=subjects_for_normalization,
        preview_only=True
    )

    if dry_run:
        return jsonify({
            'success': True,
            'message': f'预览：将规范化 {len(id_mapping)} 个受试者ID',
            'updated': 0,
            'id_mapping': id_mapping
        })

    # 执行ID重命名
    updated_count = 0
    errors = []

    for old_id, new_id in id_mapping.items():
        if old_id == new_id:
            continue  # 已经是规范化的ID，跳过

        try:
            # 重命名受试者
            subject_manager.rename_subject(old_id, new_id)
            updated_count += 1
            logger.info(f"Renamed subject: {old_id} -> {new_id}")
        except Exception as e:
            errors.append({
                'subject_id': old_id,
                'new_id': new_id,
                'error': str(e)
            })
            logger.error(f"Failed to rename {old_id}: {e}")

    return jsonify({
        'success': True,
        'message': f'成功规范化 {updated_count} 个受试者ID',
        'updated': updated_count,
        'id_mapping': id_mapping,
        'errors': errors
    })


@m02_bp.route('/mmse/batch-template', methods=['GET'])
@handle_errors
def download_mmse_batch_template():
    """下载MMSE批量导入模板（含已有V2数据）"""
    include_data = request.args.get('include_data', 'true').lower() == 'true'
    data_version = request.args.get('data_version', None)  # v1/v2/None

    logger.info(f"Generating MMSE template: include_data={include_data}, version={data_version}")

    csv_content = mmse_manager.generate_batch_import_template(
        subject_manager=subject_manager,
        include_existing_data=include_data,
        data_version=data_version
    )

    from flask import Response
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=mmse_batch_template.csv'}
    )


@m02_bp.route('/mmse/batch-import', methods=['POST'])
@handle_errors
def batch_import_mmse():
    """批量导入MMSE数据"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '未提供文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '文件名为空'}), 400

    # 保存临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        file.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        logger.info(f"Batch importing MMSE data from {file.filename}")
        result = mmse_manager.batch_import_clinical_data(
            csv_file_path=tmp_path,
            subject_manager=subject_manager
        )

        return jsonify({
            'success': True,
            **result
        })
    finally:
        # 删除临时文件
        tmp_path.unlink()


@m02_bp.route('/mmse/submit', methods=['POST'])
@handle_errors
def submit_mmse_data():
    """提交MMSE数据（含人口学信息，自动计算总分）"""
    data = request.get_json()

    subject_id = data.get('subject_id')
    demographics = data.get('demographics')
    mmse_data = data.get('mmse', {})

    logger.info(f"Submitting MMSE data for subject: {subject_id}")

    # 自动计算总分
    if mmse_data:
        mmse_data['total_score'] = mmse_manager.calculate_total_score(mmse_data)

    # 更新受试者
    updated_subject = subject_manager.update_subject(
        subject_id=subject_id,
        demographics=demographics,
        mmse=mmse_data if mmse_data else None
    )

    return jsonify({
        'success': True,
        'subject': updated_subject,
        'mmse_total_score': mmse_data.get('total_score') if mmse_data else None
    })


