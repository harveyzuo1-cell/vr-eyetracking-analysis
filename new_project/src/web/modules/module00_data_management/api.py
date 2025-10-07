"""
Module 00: 数据管理中心 - API路由
Data Management Center - API Routes

Provides endpoints for dual-source data import (legacy v1 + eye_tracking v2)
"""
from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any
from datetime import datetime

from .service import DataManagementService

logger = logging.getLogger(__name__)

# 创建Blueprint
m00_bp = Blueprint('module00', __name__, url_prefix='/api/m00')

# 初始化服务
data_service = DataManagementService()


@m00_bp.route('/scan-all', methods=['GET'])
def scan_all():
    """
    扫描所有数据源 (Legacy v1 + EyeTracking v2)
    注意：这是扫描原始数据源，不是已导入的数据
    要获取已导入数据统计，请使用 /api/m00/imported-stats

    Returns:
        JSON response with scan results from both sources
        {
            "success": true,
            "legacy_data": {
                "source_dir": "data/*_raw/",
                "control": 20,
                "mci": 20,
                "ad": 20,
                "total_subjects": 60
            },
            "eye_tracking_data": {
                "source_dir": "eye_tracking_data/",
                "control": 77,
                "mci": 8,
                "ad": 8,
                "total_subjects": 93
            },
            "summary": {
                "total_subjects": 153,
                "sources": 2
            }
        }
    """
    try:
        result = data_service.scan_all_sources()
        return jsonify({
            'success': True,
            **result
        }), 200

    except Exception as e:
        logger.error(f"扫描数据源失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'扫描失败: {str(e)}'
        }), 500


@m00_bp.route('/imported-stats', methods=['GET'])
def get_imported_stats():
    """
    获取已导入数据的统计信息（从metadata读取实际数据）

    Returns:
        JSON response with imported data statistics
        {
            "success": true,
            "v1_data": {
                "control": 20,
                "mci": 20,
                "ad": 20,
                "total": 60
            },
            "v2_data": {
                "control": 77,
                "mci": 8,
                "ad": 8,
                "total": 93
            },
            "summary": {
                "total_subjects": 153,
                "v1_count": 60,
                "v2_count": 93
            }
        }
    """
    try:
        result = data_service.get_imported_data_stats()
        return jsonify({
            'success': True,
            **result
        }), 200

    except Exception as e:
        logger.error(f"获取已导入数据统计失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'查询失败: {str(e)}'
        }), 500


@m00_bp.route('/preview', methods=['GET'])
def preview_import():
    """
    预览待导入数据

    Query params:
        source: 'legacy' | 'eye_tracking' | 'all' (default: 'all')
        limit: 预览数量限制 (default: 10)

    Returns:
        JSON response with preview data
    """
    try:
        source = request.args.get('source', 'all')
        limit = request.args.get('limit', 10, type=int)

        result = data_service.preview_import_data(source=source, limit=limit)
        return jsonify({
            'success': True,
            **result
        }), 200

    except Exception as e:
        logger.error(f"预览数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'预览失败: {str(e)}'
        }), 500


@m00_bp.route('/import', methods=['POST'])
def batch_import():
    """
    批量导入数据

    Request JSON:
        {
            "source": "legacy" | "eye_tracking" | "all",
            "overwrite": false  // 是否覆盖已存在数据
        }

    Returns:
        JSON response with import results
        {
            "success": true,
            "imported_count": 159,
            "legacy_imported": 65,
            "eye_tracking_imported": 94,
            "skipped_count": 0,
            "errors": []
        }
    """
    try:
        data = request.get_json() or {}
        source = data.get('source', 'all')
        overwrite = data.get('overwrite', False)

        # 验证source参数
        valid_sources = ['legacy', 'eye_tracking', 'all']
        if source not in valid_sources:
            return jsonify({
                'success': False,
                'error': f'无效的source参数: {source}，必须是 {valid_sources} 之一'
            }), 400

        result = data_service.batch_import(source=source, overwrite=overwrite)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"批量导入失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'导入失败: {str(e)}'
        }), 500


@m00_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """
    获取受试者列表

    Query params:
        data_version: 'v1' | 'v2' | 'all' (default: 'all')
        group: 'control' | 'mci' | 'ad' | 'all' (default: 'all')
        page: 页码 (default: 1)
        page_size: 每页数量 (default: 50)

    Returns:
        JSON response with subjects list
        {
            "success": true,
            "subjects": [
                {
                    "subject_id": "control_legacy_1",
                    "data_version": "v1",
                    "roi_layout": "v1",
                    "group": "control",
                    "source_type": "legacy",
                    "import_date": "2025-10-02 00:00:00"
                },
                ...
            ],
            "total_count": 159,
            "page": 1,
            "page_size": 50,
            "total_pages": 4
        }
    """
    try:
        data_version = request.args.get('data_version', 'all')
        group = request.args.get('group', 'all')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)

        result = data_service.get_subjects(
            data_version=data_version,
            group=group,
            page=page,
            page_size=page_size
        )

        return jsonify({
            'success': True,
            **result
        }), 200

    except Exception as e:
        logger.error(f"获取受试者列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'查询失败: {str(e)}'
        }), 500


@m00_bp.route('/import-history', methods=['GET'])
def get_import_history():
    """
    获取导入历史记录

    Query params:
        limit: 返回数量限制 (default: 20)

    Returns:
        JSON response with import history
        {
            "success": true,
            "history": [
                {
                    "timestamp": "2025-10-02 00:00:00",
                    "source": "legacy",
                    "imported_count": 65,
                    "subjects": ["control_legacy_1", ...],
                    "source_timestamps": []
                },
                ...
            ],
            "total_imports": 2
        }
    """
    try:
        limit = request.args.get('limit', 20, type=int)

        result = data_service.get_import_history(limit=limit)
        return jsonify({
            'success': True,
            **result
        }), 200

    except Exception as e:
        logger.error(f"获取导入历史失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'查询失败: {str(e)}'
        }), 500


# ==================== MMSE管理端点 ====================

@m00_bp.route('/mmse/import-legacy', methods=['POST'])
def import_legacy_mmse():
    """
    导入Legacy MMSE数据

    从旧项目的MMSE_Score目录读取CSV文件并导入到mmse_scores.json

    Returns:
        {
            "success": true,
            "imported": 40,
            "skipped": 0,
            "failed": 20,
            "details": [...],
            "statistics": {
                "total": 40,
                "by_group": {"control": 20, "mci": 20, "ad": 0}
            }
        }
    """
    try:
        from .mmse import MMSELoader, MMSEStorage

        # 使用正确的Legacy MMSE路径
        mmse_dir = r'c:\Users\asino\Downloads\az - 副本 (11)\data\MMSE_Score'
        loader = MMSELoader(legacy_mmse_dir=mmse_dir)
        storage = MMSEStorage()

        # 加载Legacy MMSE数据
        mmse_data = loader.load_legacy_mmse()

        if not mmse_data:
            return jsonify({
                'success': False,
                'error': '未找到Legacy MMSE数据'
            }), 404

        # 批量导入
        result = storage.batch_import_mmse(mmse_data)

        # 获取统计信息
        stats = loader.get_statistics()
        result['statistics'] = stats

        logger.info(f"Legacy MMSE导入完成: {result['imported']}条成功, {result['failed']}条失败")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"导入Legacy MMSE失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'导入失败: {str(e)}'
        }), 500


@m00_bp.route('/mmse/stats', methods=['GET'])
def get_mmse_stats():
    """
    获取MMSE统计信息

    Returns:
        {
            "success": true,
            "statistics": {
                "total": 40,
                "by_group": {"control": 20, "mci": 20, "ad": 0},
                "by_version": {"v1": 40, "v2": 0}
            },
            "analysis": {
                "mean": 24.5,
                "median": 25,
                "by_group": {
                    "control": {"mean": 28.5, "count": 20},
                    "mci": {"mean": 23.2, "count": 20}
                }
            }
        }
    """
    try:
        from .mmse import MMSEStorage, MMSEValidator

        storage = MMSEStorage()

        # 获取存储统计
        storage_stats = storage.get_statistics()

        # 加载MMSE数据进行分析
        mmse_data = storage.load_mmse_scores()
        analysis = MMSEValidator.analyze_scores(mmse_data)

        return jsonify({
            'success': True,
            'statistics': storage_stats,
            'analysis': analysis
        }), 200

    except Exception as e:
        logger.error(f"获取MMSE统计失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'查询失败: {str(e)}'
        }), 500


@m00_bp.route('/mmse/<subject_id>', methods=['GET'])
def get_mmse_by_subject(subject_id: str):
    """
    获取指定受试者的MMSE数据

    Path params:
        subject_id: 受试者ID (如 control_legacy_1)

    Returns:
        {
            "success": true,
            "data": {
                "subject_id": "control_legacy_1",
                "group": "control",
                "total_score": 28,
                "q1_year": 1,
                ...
            }
        }
    """
    try:
        from .mmse import MMSEStorage

        storage = MMSEStorage()
        mmse_data = storage.get_mmse_for_subject(subject_id)

        if mmse_data:
            return jsonify({
                'success': True,
                'data': mmse_data
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'未找到受试者 {subject_id} 的MMSE数据'
            }), 404

    except Exception as e:
        logger.error(f"获取MMSE数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'查询失败: {str(e)}'
        }), 500


@m00_bp.route('/import-v2', methods=['POST'])
def import_eye_tracking_v2():
    """
    导入Eye Tracking V2数据

    从eye_tracking_data目录导入v2眼球追踪数据

    Returns:
        JSON response with import results
        {
            "success": true,
            "imported": 120,  # 成功导入的任务数
            "failed": 0,
            "subjects_imported": 28,
            "statistics": {
                "by_group": {
                    "control": {"subjects": 14, "tasks": 70},
                    "mci": {"subjects": 6, "tasks": 30},
                    "ad": {"subjects": 6, "tasks": 30}
                },
                "total_subjects": 28,
                "total_tasks": 120
            },
            "details": [...]
        }
    """
    try:
        from .eye_tracking_v2_importer import EyeTrackingV2Importer
        from .metadata_manager import MetadataManager

        logger.info("Starting Eye Tracking V2 data import...")

        # Initialize importer
        v2_importer = EyeTrackingV2Importer()

        # Load v2 data
        subjects_data = v2_importer.load_v2_data()

        if not subjects_data:
            return jsonify({
                'success': False,
                'error': '未找到可导入的v2数据'
            }), 400

        # Save to CSV
        import_result = v2_importer.save_to_csv(subjects_data)

        # Update metadata
        metadata_mgr = MetadataManager()

        for subject_id, subject_info in subjects_data.items():
            group = subject_info['group']
            tasks = subject_info['tasks']
            hospital_id = subject_info['hospital_id']

            # Create metadata entry
            metadata = {
                'subject_id': subject_id,
                'group': group,
                'data_version': 'v2',
                'task_count': len(tasks),
                'tasks_available': list(tasks.keys()),
                'raw_identifier': hospital_id,
                'has_mmse': False,  # v2 data has no MMSE
                'import_date': datetime.now().isoformat()
            }
            metadata_mgr.save_subject_metadata(metadata)

        # Calculate statistics
        stats = {
            'by_group': {},
            'total_subjects': len(subjects_data),
            'total_tasks': import_result['imported']
        }

        for subject_id, subject_info in subjects_data.items():
            group = subject_info['group']
            if group not in stats['by_group']:
                stats['by_group'][group] = {'subjects': 0, 'tasks': 0}

            stats['by_group'][group]['subjects'] += 1
            stats['by_group'][group]['tasks'] += len(subject_info['tasks'])

        logger.info(f"V2 import completed: {import_result['imported']} tasks from {len(subjects_data)} subjects")

        return jsonify({
            'success': import_result['success'],
            'imported': import_result['imported'],
            'failed': import_result['failed'],
            'subjects_imported': len(subjects_data),
            'statistics': stats,
            'details': import_result['details']
        }), 200

    except Exception as e:
        logger.error(f"V2数据导入失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'导入失败: {str(e)}'
        }), 500
