"""
ModuleEX2 数据导出服务

提供数据固化和导出功能
"""

import json
import csv
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from config.settings import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataExportService:
    """数据导出服务"""

    def __init__(self):
        """初始化数据导出服务"""
        self.data_root = Path(Config.DATA_ROOT)
        self.export_dir = self.data_root / 'exports'
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # 数据源目录
        self.processed_dir = self.data_root / '02_processed'
        self.subject_info_dir = self.data_root / 'subject_info'
        self.roi_configs_dir = self.data_root / 'roi_configs'

        logger.info(f"数据导出服务初始化完成: {self.export_dir}")

    # ==================== 校准眼动数据导出 ====================

    def export_calibrated_eyetracking(
        self,
        subject_ids: Optional[List[str]] = None,
        data_version: str = 'v1',
        output_format: str = 'csv'
    ) -> Dict:
        """
        导出校准后的眼动数据

        Args:
            subject_ids: 受试者ID列表，None表示导出全部
            data_version: 数据版本 (v1/v2)
            output_format: 输出格式 (csv/excel)

        Returns:
            {
                'success': bool,
                'file_path': str,
                'exported_count': int,
                'message': str
            }
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_filename = f"calibrated_eyetracking_{data_version}_{timestamp}"

            # 如果没有指定subject_ids，扫描所有受试者
            if subject_ids is None:
                subject_ids = self._get_all_subjects_with_calibrated_data(data_version)

            if not subject_ids:
                return {
                    'success': False,
                    'message': f'未找到{data_version}的校准数据'
                }

            # 收集所有校准数据
            all_data = []
            exported_count = 0

            for subject_id in subject_ids:
                # 获取受试者组别
                group = self._get_subject_group(subject_id)
                if not group:
                    logger.warning(f"无法确定受试者组别: {subject_id}")
                    continue

                # 查找该受试者的所有校准文件
                subject_dir = self.processed_dir / group
                calibrated_files = list(subject_dir.glob(f"{subject_id}_*_calibrated.csv"))

                for cal_file in calibrated_files:
                    try:
                        # 读取校准数据
                        df = pd.read_csv(cal_file)

                        # 添加元数据列
                        df['subject_id'] = subject_id
                        df['group'] = group
                        df['data_version'] = data_version

                        # 提取任务ID
                        task_id = cal_file.stem.replace(f"{subject_id}_", "").replace("_calibrated", "")
                        df['task_id'] = task_id

                        all_data.append(df)
                        exported_count += 1
                        logger.debug(f"已导出: {subject_id}/{task_id}")

                    except Exception as e:
                        logger.error(f"读取校准文件失败 {cal_file}: {e}")
                        continue

            if not all_data:
                return {
                    'success': False,
                    'message': '没有可导出的数据'
                }

            # 合并所有数据
            merged_df = pd.concat(all_data, ignore_index=True)

            # 保存文件
            if output_format == 'csv':
                output_path = self.export_dir / f"{export_filename}.csv"
                merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif output_format == 'excel':
                output_path = self.export_dir / f"{export_filename}.xlsx"
                merged_df.to_excel(output_path, index=False)
            else:
                return {
                    'success': False,
                    'message': f'不支持的输出格式: {output_format}'
                }

            logger.info(f"眼动数据导出成功: {output_path}, {exported_count}个文件")

            return {
                'success': True,
                'file_path': str(output_path.relative_to(self.data_root)),
                'exported_count': exported_count,
                'total_records': len(merged_df),
                'message': f'成功导出{exported_count}个任务的校准数据'
            }

        except Exception as e:
            logger.error(f"导出校准眼动数据失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}'
            }

    # ==================== ROI配置导出 ====================

    def export_roi_configs(
        self,
        data_version: str = 'v1',
        output_format: str = 'json'
    ) -> Dict:
        """
        导出ROI配置信息

        Args:
            data_version: 数据版本 (v1/v2)
            output_format: 输出格式 (json/csv)

        Returns:
            {
                'success': bool,
                'file_path': str,
                'exported_count': int,
                'message': str
            }
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            roi_config_dir = self.roi_configs_dir / data_version

            if not roi_config_dir.exists():
                return {
                    'success': False,
                    'message': f'{data_version} ROI配置目录不存在'
                }

            roi_files = list(roi_config_dir.glob('*_roi.json'))

            if not roi_files:
                return {
                    'success': False,
                    'message': f'未找到{data_version}的ROI配置文件'
                }

            if output_format == 'json':
                # JSON格式：保存为单个JSON文件，包含所有任务的ROI
                all_roi_configs = {}

                for roi_file in roi_files:
                    task_id = roi_file.stem.replace('_roi', '')
                    with open(roi_file, 'r', encoding='utf-8') as f:
                        all_roi_configs[task_id] = json.load(f)

                output_path = self.export_dir / f"roi_configs_{data_version}_{timestamp}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_roi_configs, f, ensure_ascii=False, indent=2)

            elif output_format == 'csv':
                # CSV格式：展开为表格，每个ROI一行
                roi_data = []

                for roi_file in roi_files:
                    task_id = roi_file.stem.replace('_roi', '')

                    with open(roi_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)

                    # 遍历所有区域类型
                    for region_type, regions in config.get('regions', {}).items():
                        for roi in regions:
                            coords = roi.get('normalized_coords', [])
                            if len(coords) >= 4:
                                roi_data.append({
                                    'task_id': task_id,
                                    'region_type': region_type,
                                    'roi_id': roi.get('id', ''),
                                    'name': roi.get('name', ''),
                                    'description': roi.get('description', ''),
                                    'x': coords[0],
                                    'y': coords[1],
                                    'width': coords[2],
                                    'height': coords[3],
                                    'color': roi.get('color', ''),
                                    'data_version': data_version
                                })

                df = pd.DataFrame(roi_data)
                output_path = self.export_dir / f"roi_configs_{data_version}_{timestamp}.csv"
                df.to_csv(output_path, index=False, encoding='utf-8-sig')

            else:
                return {
                    'success': False,
                    'message': f'不支持的输出格式: {output_format}'
                }

            logger.info(f"ROI配置导出成功: {output_path}, {len(roi_files)}个任务")

            return {
                'success': True,
                'file_path': str(output_path.relative_to(self.data_root)),
                'exported_count': len(roi_files),
                'message': f'成功导出{len(roi_files)}个任务的ROI配置'
            }

        except Exception as e:
            logger.error(f"导出ROI配置失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}'
            }

    # ==================== 受试者信息+MMSE导出 ====================

    def export_subjects_with_mmse(
        self,
        data_version: Optional[str] = None,
        include_mmse_details: bool = True
    ) -> Dict:
        """
        导出受试者信息和MMSE评分

        Args:
            data_version: 数据版本筛选 (v1/v2/None表示全部)
            include_mmse_details: 是否包含MMSE子题目详情

        Returns:
            {
                'success': bool,
                'file_path': str,
                'exported_count': int,
                'message': str
            }
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            subjects_data = []

            # 遍历所有组别
            for group in ['control', 'mci', 'ad']:
                group_dir = self.subject_info_dir / group

                if not group_dir.exists():
                    continue

                # 读取所有受试者文件
                for subject_file in group_dir.glob('*.json'):
                    if subject_file.name == 'index.json':
                        continue

                    try:
                        with open(subject_file, 'r', encoding='utf-8') as f:
                            subject_data = json.load(f)

                        # 版本筛选
                        if data_version and subject_data.get('data_version') != data_version:
                            continue

                        # 基本信息
                        demographics = subject_data.get('demographics', {})
                        row = {
                            'subject_id': subject_data.get('subject_id'),
                            'group': subject_data.get('group'),
                            'data_version': subject_data.get('data_version', 'v1'),
                            'gender': demographics.get('gender', ''),
                            'age': demographics.get('age', ''),
                            'education_level': demographics.get('education_level', ''),
                            'task_count': subject_data.get('task_count', 0)
                        }

                        # MMSE信息
                        mmse = subject_data.get('mmse', {})
                        if mmse:
                            row['mmse_total_score'] = mmse.get('total_score')
                            row['mmse_test_date'] = mmse.get('test_date', '')

                            # MMSE子题目详情 (19题，满分21分)
                            if include_mmse_details:
                                # Q1: 定向力-时间 (5题, q1_weekday 2分, 其他1分, 共6分)
                                row['q1_year'] = mmse.get('q1_year', '')
                                row['q1_season'] = mmse.get('q1_season', '')
                                row['q1_month'] = mmse.get('q1_month', '')
                                row['q1_weekday'] = mmse.get('q1_weekday', '')  # 2分

                                # Q2: 定向力-地点 (5题, q2_province 2分, 其他1分, 共6分)
                                row['q2_province'] = mmse.get('q2_province', '')  # 2分
                                row['q2_street'] = mmse.get('q2_street', '')
                                row['q2_building'] = mmse.get('q2_building', '')
                                row['q2_floor'] = mmse.get('q2_floor', '')

                                # Q3: 即刻记忆 (1题, 0-3分)
                                row['q3_immediate'] = mmse.get('q3_immediate', '')

                                # Q4: 注意力和计算 (5题, 各1分, 共5分)
                                row['q4_100_7'] = mmse.get('q4_100_7', '')
                                row['q4_93_7'] = mmse.get('q4_93_7', '')
                                row['q4_86_7'] = mmse.get('q4_86_7', '')
                                row['q4_79_7'] = mmse.get('q4_79_7', '')
                                row['q4_72_7'] = mmse.get('q4_72_7', '')

                                # Q5: 延迟回忆 (3题, 各1分, 共3分)
                                row['q5_word1'] = mmse.get('q5_word1', '')
                                row['q5_word2'] = mmse.get('q5_word2', '')
                                row['q5_word3'] = mmse.get('q5_word3', '')
                        else:
                            row['mmse_total_score'] = None
                            row['mmse_test_date'] = ''

                        subjects_data.append(row)

                    except Exception as e:
                        logger.error(f"读取受试者文件失败 {subject_file}: {e}")
                        continue

            if not subjects_data:
                return {
                    'success': False,
                    'message': '没有可导出的受试者数据'
                }

            # 保存为CSV
            df = pd.DataFrame(subjects_data)
            version_suffix = f"_{data_version}" if data_version else "_all"
            output_path = self.export_dir / f"subjects_mmse{version_suffix}_{timestamp}.csv"
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

            logger.info(f"受试者+MMSE数据导出成功: {output_path}, {len(subjects_data)}个受试者")

            return {
                'success': True,
                'file_path': str(output_path.relative_to(self.data_root)),
                'exported_count': len(subjects_data),
                'message': f'成功导出{len(subjects_data)}个受试者的信息和MMSE评分'
            }

        except Exception as e:
            logger.error(f"导出受试者+MMSE数据失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}'
            }

    # ==================== 统一打包导出 ====================

    def export_all(
        self,
        data_version: str = 'v1',
        subject_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        统一打包导出所有数据

        Args:
            data_version: 数据版本 (v1/v2)
            subject_ids: 受试者ID列表，None表示全部

        Returns:
            {
                'success': bool,
                'zip_path': str,
                'message': str
            }
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f"export_package_{data_version}_{timestamp}.zip"
            zip_path = self.export_dir / zip_filename

            # 临时存储导出结果
            export_results = {}

            # 1. 导出校准眼动数据
            result = self.export_calibrated_eyetracking(
                subject_ids=subject_ids,
                data_version=data_version,
                output_format='csv'
            )
            if result['success']:
                export_results['eyetracking'] = self.data_root / result['file_path']

            # 2. 导出ROI配置
            result = self.export_roi_configs(
                data_version=data_version,
                output_format='csv'
            )
            if result['success']:
                export_results['roi_configs'] = self.data_root / result['file_path']

            # 3. 导出受试者+MMSE
            result = self.export_subjects_with_mmse(
                data_version=data_version,
                include_mmse_details=True
            )
            if result['success']:
                export_results['subjects_mmse'] = self.data_root / result['file_path']

            if not export_results:
                return {
                    'success': False,
                    'message': '没有可导出的数据'
                }

            # 打包成ZIP
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for name, file_path in export_results.items():
                    if file_path.exists():
                        zipf.write(file_path, file_path.name)
                        logger.debug(f"已添加到ZIP: {file_path.name}")

                # 添加导出元数据
                metadata = {
                    'export_time': timestamp,
                    'data_version': data_version,
                    'exported_files': list(export_results.keys()),
                    'module_versions': {
                        'module00': 'data_import',
                        'module01': 'calibration',
                        'moduleEX': 'roi_config',
                        'module02': 'mmse_management'
                    }
                }
                zipf.writestr('export_metadata.json', json.dumps(metadata, indent=2, ensure_ascii=False))

            logger.info(f"统一导出包创建成功: {zip_path}")

            return {
                'success': True,
                'zip_path': str(zip_path.relative_to(self.data_root)),
                'files_count': len(export_results),
                'message': f'成功打包导出{len(export_results)}个数据文件'
            }

        except Exception as e:
            logger.error(f"统一打包导出失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}'
            }

    # ==================== 辅助方法 ====================

    def _get_all_subjects_with_calibrated_data(self, data_version: str) -> List[str]:
        """获取所有有校准数据的受试者ID"""
        subject_ids = []

        for group in ['control', 'mci', 'ad']:
            group_dir = self.processed_dir / group
            if not group_dir.exists():
                continue

            # 查找所有校准文件
            calibrated_files = list(group_dir.glob('*_calibrated.csv'))

            for cal_file in calibrated_files:
                # 提取subject_id
                subject_id = cal_file.stem.split('_')[0]
                if '_' in cal_file.stem:
                    # 处理类似 v2_control_001_level_1_calibrated.csv 的格式
                    parts = cal_file.stem.split('_')
                    if data_version == 'v2' and parts[0] == 'v2':
                        subject_id = '_'.join(parts[:3])  # v2_control_001
                    elif data_version == 'v1' and parts[0] != 'v2':
                        subject_id = '_'.join(parts[:2])  # control_legacy_1

                    if subject_id not in subject_ids:
                        subject_ids.append(subject_id)

        return subject_ids

    def _get_subject_group(self, subject_id: str) -> Optional[str]:
        """从subject_id推断组别"""
        subject_id_lower = subject_id.lower()

        # 从subject_info查找
        for group in ['control', 'mci', 'ad']:
            subject_file = self.subject_info_dir / group / f'{subject_id}.json'
            if subject_file.exists():
                return group

        # 从ID前缀推断
        if 'control' in subject_id_lower or subject_id_lower.startswith('n'):
            return 'control'
        elif 'mci' in subject_id_lower or subject_id_lower.startswith('m'):
            return 'mci'
        elif 'ad' in subject_id_lower or subject_id_lower.startswith('a'):
            return 'ad'

        return None

    # ==================== 导出记录管理 ====================

    def list_exports(self, limit: int = 20) -> Dict:
        """
        列出最近的导出文件

        Args:
            limit: 返回数量限制

        Returns:
            {
                'success': bool,
                'exports': List[Dict],
                'message': str
            }
        """
        try:
            export_files = []

            for file_path in sorted(self.export_dir.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
                if file_path.is_file():
                    stat = file_path.stat()
                    export_files.append({
                        'filename': file_path.name,
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'path': str(file_path.relative_to(self.data_root))
                    })

            return {
                'success': True,
                'exports': export_files,
                'total': len(export_files),
                'message': f'找到{len(export_files)}个导出文件'
            }

        except Exception as e:
            logger.error(f"列出导出文件失败: {e}")
            return {
                'success': False,
                'message': f'获取导出列表失败: {str(e)}'
            }
