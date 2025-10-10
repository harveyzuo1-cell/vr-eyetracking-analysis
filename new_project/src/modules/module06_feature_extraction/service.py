"""
Module06 Feature Extraction Service
特征提取与选择服务层
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logger import setup_logger
from .sensitivity_analyzer import SensitivityAnalyzer
from .utils import validate_strategy, validate_groups, validate_data_version

logger = setup_logger(__name__)


class FeatureExtractionService:
    """
    特征提取与选择服务

    负责协调Module04和Module05的特征选择与提取
    """

    def __init__(self):
        """初始化服务"""
        self.base_dir = Path(__file__).parent.parent.parent.parent
        self.cache_dir = self.base_dir / 'data' / '06_features' / 'sensitivity_scores'
        self.export_dir = self.base_dir / 'data' / '06_features' / 'extracted'

        # 确保目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        logger.info("FeatureExtractionService initialized")

    # ========================================
    # Module04 敏感度分析
    # ========================================

    def compute_m04_sensitivity(self, data_version: str = 'v1',
                                groups: Optional[List[str]] = None,
                                velocity_threshold: float = 40.0,
                                min_fixation_duration: int = 100) -> Dict:
        """
        计算Module04特征敏感度分析

        Args:
            data_version: 数据版本
            groups: 分组列表
            velocity_threshold: IVT速度阈值
            min_fixation_duration: 最小注视时长

        Returns:
            敏感度分析完整报告
        """
        logger.info(f"开始Module04敏感度分析 (data_version={data_version})")

        # 验证参数
        data_version = validate_data_version(data_version)
        groups = validate_groups(groups) if groups else ['control', 'mci', 'ad']

        # 1. 获取Module04特征数据
        features_df = self._load_m04_features(
            data_version=data_version,
            groups=groups,
            velocity_threshold=velocity_threshold,
            min_fixation_duration=min_fixation_duration
        )

        # 2. 执行敏感度分析
        analyzer = SensitivityAnalyzer(features_df)
        report = analyzer.generate_report()

        # 3. 缓存结果
        cache_file = self.cache_dir / f'm04_sensitivity_{data_version}.json'
        report['timestamp'] = datetime.now().isoformat()
        report['params'] = {
            'data_version': data_version,
            'groups': groups,
            'velocity_threshold': velocity_threshold,
            'min_fixation_duration': min_fixation_duration
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Module04敏感度分析完成，Top-4特征: {[f['feature_name'] for f in report['top_4_features']]}")

        return report

    def get_m04_top_k(self, k: int = 4, data_version: str = 'v1') -> Dict:
        """
        获取Module04 Top-K敏感特征

        Args:
            k: 选择特征数量
            data_version: 数据版本

        Returns:
            Top-K特征列表及元信息
        """
        # 尝试从缓存加载
        cache_file = self.cache_dir / f'm04_sensitivity_{data_version}.json'

        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_report = json.load(f)

            top_k_features = [f['feature_name'] for f in cached_report['all_features'][:k]]

            return {
                'top_k': top_k_features,
                'k': k,
                'data_version': data_version,
                'cached': True,
                'timestamp': cached_report.get('timestamp')
            }
        else:
            # 缓存不存在，需要先计算
            logger.warning(f"Module04敏感度分析缓存不存在，需要先调用 /m04/sensitivity/compute")
            raise FileNotFoundError(
                f"Module04敏感度分析结果不存在。请先调用 POST /api/m06/m04/sensitivity/compute"
            )

    def get_m04_report(self, data_version: str = 'v1',
                       include_pairwise: bool = False) -> Dict:
        """
        获取Module04敏感度分析详细报告

        Args:
            data_version: 数据版本
            include_pairwise: 是否包含成对检验详情

        Returns:
            完整报告
        """
        cache_file = self.cache_dir / f'm04_sensitivity_{data_version}.json'

        if not cache_file.exists():
            raise FileNotFoundError(
                f"Module04敏感度分析结果不存在。请先调用 POST /api/m06/m04/sensitivity/compute"
            )

        with open(cache_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        # 如果不需要成对检验详情，移除以减少响应大小
        if not include_pairwise:
            for feature in report.get('all_features', []):
                feature.pop('pairwise_results', None)

        return {
            'report': report,
            'timestamp': report.get('timestamp'),
            'cached': True
        }

    def _load_m04_features(self, data_version: str, groups: List[str],
                          velocity_threshold: float,
                          min_fixation_duration: int) -> pd.DataFrame:
        """
        加载Module04特征数据

        调用Module04的特征提取API获取数据

        Args:
            data_version: 数据版本
            groups: 分组列表
            velocity_threshold: IVT速度阈值
            min_fixation_duration: 最小注视时长

        Returns:
            特征DataFrame
        """
        from src.modules.module04_event_analysis.service import EventAnalysisService

        logger.info(f"加载Module04特征数据 (data_version={data_version})")

        m04_service = EventAnalysisService()

        # 调用Module04批量分析
        result = m04_service.get_feature_statistics(
            group=None,  # 获取所有分组
            data_version=data_version,
            velocity_threshold=velocity_threshold,
            min_fixation_duration=min_fixation_duration
        )

        if not result.get('success'):
            raise ValueError(f"Module04特征提取失败: {result.get('error')}")

        features_data = result['features']

        # 转换为DataFrame
        df = pd.DataFrame(features_data)

        # 过滤指定分组
        df = df[df['group'].isin(groups)]

        # 移除MMSE相关列（不作为特征）
        columns_to_drop = [col for col in df.columns if 'mmse' in col.lower()]
        df = df.drop(columns=columns_to_drop, errors='ignore')

        logger.info(f"加载完成，共 {len(df)} 条记录")

        return df

    # ========================================
    # Module05 敏感度分析
    # ========================================

    def compute_m05_sensitivity(self, groups: List[str],
                                top_k_params: int = 10) -> Dict:
        """
        触发Module05 RQA敏感度分析（异步任务）

        Args:
            groups: 分组列表
            top_k_params: 选择Top-K参数组合

        Returns:
            任务信息
        """
        from src.modules.module05_rqa_analysis.service import RQAAnalysisService

        logger.info(f"触发Module05敏感度分析任务 (groups={groups}, top_k_params={top_k_params})")

        # Module05已有敏感度分析功能，直接调用
        m05_service = RQAAnalysisService()

        # 调用Module05的敏感度计算API
        # 注意：Module05的compute_sensitivity_scores是同步的，这里需要异步化处理
        # 暂时返回任务ID，实际计算在后台进行

        task_id = f"m05_sensitivity_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 将任务信息存储到任务队列（简化版本：直接存文件）
        task_file = self.cache_dir / f'{task_id}.json'
        task_info = {
            'task_id': task_id,
            'status': 'submitted',
            'groups': groups,
            'top_k_params': top_k_params,
            'created_at': datetime.now().isoformat()
        }

        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)

        logger.info(f"Module05敏感度分析任务已提交: {task_id}")

        return {
            'task_id': task_id,
            'message': 'Module05敏感度分析任务已提交',
            'estimated_time_minutes': 15
        }

    def get_m05_top_k(self, k: int = 6, mode: str = 'cross_param') -> Dict:
        """
        获取Module05 Top-K敏感RQA特征

        Args:
            k: 选择RQA特征数量
            mode: 聚合模式 (cross_param/single_param)

        Returns:
            Top-K RQA特征
        """
        from src.modules.module05_rqa_analysis.service import RQAAnalysisService

        logger.info(f"获取Module05 Top-{k} RQA特征 (mode={mode})")

        m05_service = RQAAnalysisService()

        # 检查是否有敏感度分析缓存
        sensitivity_cache = self.cache_dir / 'm05_sensitivity_latest.json'

        if not sensitivity_cache.exists():
            logger.warning("Module05敏感度分析结果不存在，需要先运行敏感度分析")
            raise FileNotFoundError(
                "Module05敏感度分析结果不存在。请先调用 POST /api/m06/m05/sensitivity/compute"
            )

        with open(sensitivity_cache, 'r', encoding='utf-8') as f:
            sensitivity_result = json.load(f)

        # 根据mode提取Top-K特征
        if mode == 'cross_param':
            # 跨参数聚合：选择6个核心RQA指标
            strategy_a = sensitivity_result.get('strategy_a', {})
            top_k_features = strategy_a.get('features', [])[:k]
        else:
            # 单参数：选择Top-K参数组合
            strategy_b = sensitivity_result.get('strategy_b', {})
            top_k_features = strategy_b.get('top_params', [])[:k]

        return {
            'top_k_features': top_k_features,
            'k': k,
            'mode': mode,
            'cached': True,
            'timestamp': sensitivity_result.get('timestamp')
        }

    def get_m05_sensitivity_status(self, task_id: Optional[str] = None) -> Dict:
        """
        查询Module05敏感度分析任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        if task_id:
            task_file = self.cache_dir / f'{task_id}.json'
        else:
            # 获取最新任务
            task_files = list(self.cache_dir.glob('m05_sensitivity_*.json'))
            if not task_files:
                raise FileNotFoundError("没有找到Module05敏感度分析任务")

            task_file = max(task_files, key=lambda f: f.stat().st_mtime)
            with open(task_file, 'r', encoding='utf-8') as f:
                task_info = json.load(f)
                task_id = task_info['task_id']

        if not task_file.exists():
            raise FileNotFoundError(f"任务不存在: {task_id}")

        with open(task_file, 'r', encoding='utf-8') as f:
            task_info = json.load(f)

        return {
            'task_id': task_id,
            'status': task_info.get('status', 'unknown'),
            'progress': task_info.get('progress', 0),
            'message': task_info.get('message', ''),
            'result_available': task_info.get('status') == 'completed'
        }

    # ========================================
    # 特征提取
    # ========================================

    def extract_single_subject(self, subject_id: str, group: str,
                               data_version: str = 'v1',
                               strategy: str = 'A') -> Dict:
        """
        提取单个受试者的特征向量

        Args:
            subject_id: 受试者ID
            group: 分组
            data_version: 数据版本
            strategy: 特征选择策略 (A/B)

        Returns:
            特征向量及元信息
        """
        strategy = validate_strategy(strategy)

        logger.info(f"提取特征: subject_id={subject_id}, strategy={strategy}")

        # 获取选定的特征名称
        selected_features = self._get_selected_features(strategy, data_version)

        # 提取Module04特征
        m04_features = self._extract_m04_features_for_subject(
            subject_id, group, data_version, selected_features['m04']
        )

        # 提取Module05特征
        m05_features = self._extract_m05_features_for_subject(
            subject_id, group, selected_features['m05']
        )

        # 合并特征
        combined_features = {**m04_features, **m05_features}

        return {
            'subject_id': subject_id,
            'group': group,
            'features': combined_features,
            'strategy': strategy,
            'dimension': len(combined_features)
        }

    def extract_batch(self, groups: Optional[List[str]] = None,
                     data_version: str = 'v1',
                     strategy: str = 'A',
                     export_format: str = 'csv') -> Dict:
        """
        批量提取特征向量（优化版本：预加载数据以提升性能）

        Args:
            groups: 分组列表
            data_version: 数据版本
            strategy: 特征选择策略
            export_format: 导出格式 (csv/json)

        Returns:
            批量提取结果摘要
        """
        strategy = validate_strategy(strategy)
        groups = validate_groups(groups) if groups else ['control', 'mci', 'ad']

        logger.info(f"批量特征提取: groups={groups}, strategy={strategy}")

        # OPTIMIZATION: 预加载所有组的Module04数据（一次性）
        from src.modules.module04_event_analysis.service import EventAnalysisService

        m04_service = EventAnalysisService()
        all_m04_data = {}  # {group: DataFrame}
        all_subjects = []

        logger.info("预加载Module04特征数据...")
        for group in groups:
            result = m04_service.get_feature_statistics(
                group=group,
                data_version=data_version,
                velocity_threshold=40.0,
                min_fixation_duration=100
            )

            if result.get('success'):
                features_df = pd.DataFrame(result['features'])
                all_m04_data[group] = features_df

                # 获取唯一的受试者ID
                unique_subjects = features_df['subject_id'].unique()
                for subject_id in unique_subjects:
                    all_subjects.append({
                        'subject_id': subject_id,
                        'group': group
                    })

        logger.info(f"找到 {len(all_subjects)} 个受试者，Module04数据已缓存")

        # OPTIMIZATION: 预加载Module05数据（一次性）
        selected_features = self._get_selected_features(strategy, data_version)
        m05_feature_names = selected_features['m05']
        m04_feature_names = selected_features['m04']

        logger.info("预加载Module05特征数据...")
        param_sig = "m1_tau1_eps0.051_lmin2"
        enriched_file = self.base_dir / f"data/05_rqa_analysis/results/{param_sig}/step3_feature_enrichment/enriched_features.csv"

        m05_data = None
        if enriched_file.exists():
            m05_data = pd.read_csv(enriched_file)
            m05_data.columns = m05_data.columns.str.lower()
            logger.info(f"Module05数据已加载: {len(m05_data)} 行")
        else:
            logger.warning(f"Module05数据文件不存在: {enriched_file}")

        # 2. 遍历提取特征（使用预加载的数据）
        features_list = []
        success_count = 0
        failed_subjects = []

        for subject_info in all_subjects:
            try:
                # 使用优化后的内部方法，传入预加载的数据
                result = self._extract_single_subject_optimized(
                    subject_id=subject_info['subject_id'],
                    group=subject_info['group'],
                    m04_data=all_m04_data[subject_info['group']],
                    m05_data=m05_data,
                    m04_feature_names=m04_feature_names,
                    m05_feature_names=m05_feature_names
                )
                features_list.append(result)
                success_count += 1

            except Exception as e:
                logger.error(f"提取失败: {subject_info['subject_id']}, 错误: {e}")
                failed_subjects.append(subject_info['subject_id'])

        logger.info(f"成功提取 {success_count}/{len(all_subjects)} 个受试者的特征")

        # 3. 导出为CSV/JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if export_format == 'csv':
            export_path = self._export_to_csv(features_list, strategy, timestamp)
        else:
            export_path = self._export_to_json(features_list, strategy, timestamp)

        return {
            'total_subjects': len(all_subjects),
            'success_count': success_count,
            'failed_count': len(failed_subjects),
            'failed_subjects': failed_subjects,
            'export_path': export_path,
            'export_format': export_format,
            'strategy': strategy,
            'dimension': 10 if strategy == 'A' else 69
        }

    def get_features_summary(self, strategy: str = 'A') -> Dict:
        """
        获取特征提取统计摘要

        Args:
            strategy: 策略 (A/B)

        Returns:
            特征摘要信息
        """
        strategy = validate_strategy(strategy)

        selected_features = self._get_selected_features(strategy, 'v1')

        return {
            'strategy': strategy,
            'selected_features': selected_features,
            'dimension': len(selected_features['m04']) + len(selected_features['m05']),
            'sample_count': 300,
            'sample_ratio': 300 / (len(selected_features['m04']) + len(selected_features['m05']))
        }

    def _get_selected_features(self, strategy: str, data_version: str) -> Dict:
        """
        根据策略获取选定的特征列表

        Args:
            strategy: 策略 (A/B)
            data_version: 数据版本

        Returns:
            {'m04': [...], 'm05': [...]}
        """
        if strategy == 'A':
            # Strategy A: Top-10 (4 + 6)
            m04_top4 = self.get_m04_top_k(k=4, data_version=data_version)
            m05_top6 = self.get_m05_top_k(k=6, mode='cross_param')

            return {
                'm04': m04_top4['top_k'],
                'm05': [f['feature'] for f in m05_top6['top_k_features']]
            }
        else:
            # Strategy B: Top-69 (9 + 60)
            # Module04: 所有9个特征
            m04_all = SensitivityAnalyzer.AVAILABLE_FEATURES

            # Module05: Top-10参数 × 6 RQA = 60特征
            # TODO: 实现Top-10参数选择逻辑

            return {
                'm04': m04_all,
                'm05': []  # TODO
            }

    def _extract_m04_features_for_subject(self, subject_id: str, group: str,
                                          data_version: str,
                                          feature_names: List[str]) -> Dict:
        """
        提取单个受试者的Module04特征

        Args:
            subject_id: 受试者ID (例如: "control_legacy_1")
            group: 分组
            data_version: 数据版本
            feature_names: 要提取的特征名称列表

        Returns:
            特征字典 {feature_name: value}
        """
        from src.modules.module04_event_analysis.service import EventAnalysisService

        logger.info(f"提取Module04特征: subject={subject_id}, features={feature_names}")

        # 调用Module04 Service获取特征统计
        m04_service = EventAnalysisService()

        # Module04的get_feature_statistics返回所有受试者的特征
        # 我们需要从中筛选出指定subject_id的数据
        result = m04_service.get_feature_statistics(
            group=group,
            data_version=data_version,
            velocity_threshold=40.0,
            min_fixation_duration=100
        )

        if not result.get('success'):
            raise ValueError(f"Module04特征提取失败: {result.get('error')}")

        # 转换为DataFrame便于查询
        features_df = pd.DataFrame(result['features'])

        # 筛选指定受试者的数据
        subject_data = features_df[features_df['subject_id'] == subject_id]

        if len(subject_data) == 0:
            logger.warning(f"未找到受试者 {subject_id} 的Module04数据")
            return {f"m04_{name}": None for name in feature_names}

        # 提取指定特征的平均值(跨5个任务)
        extracted_features = {}
        for feature_name in feature_names:
            if feature_name in subject_data.columns:
                # 计算该受试者在所有任务中的平均值
                mean_value = subject_data[feature_name].mean()
                extracted_features[f"m04_{feature_name}"] = round(float(mean_value), 4)
            else:
                logger.warning(f"特征 {feature_name} 不存在于Module04数据中")
                extracted_features[f"m04_{feature_name}"] = None

        logger.debug(f"提取的Module04特征: {extracted_features}")
        return extracted_features

    def _extract_m05_features_for_subject(self, subject_id: str, group: str,
                                          feature_names: List[str]) -> Dict:
        """
        提取单个受试者的Module05 RQA特征

        从Module05的enriched_features.csv中提取Top-6 RQA特征
        特征名称格式: RR-2D-XY, RR-1D-X等

        Args:
            subject_id: 受试者ID
            group: 分组
            feature_names: 要提取的RQA特征名称列表 (大写格式)

        Returns:
            特征字典 {m05_feature_name: value}
        """
        logger.info(f"提取Module05特征: subject={subject_id}, features={feature_names}")

        # 从缓存读取Top-6特征对应的最佳参数组合
        # 简化实现:使用第一个参数组合的数据(m1_tau1_eps0.051_lmin2)
        # TODO: 未来可以优化为使用每个特征的最佳参数

        # 使用一个代表性的参数组合
        param_sig = "m1_tau1_eps0.051_lmin2"
        enriched_file = self.base_dir / f"data/05_rqa_analysis/results/{param_sig}/step3_feature_enrichment/enriched_features.csv"

        if not enriched_file.exists():
            logger.warning(f"Module05 enriched features文件不存在: {enriched_file}")
            return {f"m05_{name.lower().replace('-', '_')}": None for name in feature_names}

        # 读取enriched features
        df = pd.read_csv(enriched_file)

        # 标准化列名为小写
        df.columns = df.columns.str.lower()

        # 筛选指定受试者
        subject_data = df[df['subject_id'].str.lower() == subject_id.lower()]

        if len(subject_data) == 0:
            logger.warning(f"未找到受试者 {subject_id} 的Module05数据")
            return {f"m05_{name.lower().replace('-', '_')}": None for name in feature_names}

        # 提取指定特征
        extracted_features = {}
        for feature_name in feature_names:
            # 将特征名转换为CSV文件中的列名格式
            # RR-2D-XY -> rr-2d-xy
            col_name = feature_name.lower()

            if col_name in subject_data.columns:
                # 计算该受试者在所有任务中的平均值
                mean_value = subject_data[col_name].mean()
                # 使用下划线格式存储: m05_rr_2d_xy
                key_name = f"m05_{col_name.replace('-', '_')}"
                extracted_features[key_name] = round(float(mean_value), 4)
            else:
                logger.warning(f"特征 {feature_name} 不存在于Module05数据中")
                key_name = f"m05_{col_name.replace('-', '_')}"
                extracted_features[key_name] = None

        logger.debug(f"提取的Module05特征: {extracted_features}")
        return extracted_features

    # ========================================
    # 导出功能
    # ========================================

    def _export_to_csv(self, features_list: List[Dict], strategy: str, timestamp: str) -> str:
        """
        导出特征向量到CSV文件

        Args:
            features_list: 特征列表
            strategy: 策略
            timestamp: 时间戳

        Returns:
            导出文件路径
        """
        filename = f'features_strategy{strategy}_{timestamp}.csv'
        filepath = self.export_dir / filename

        # 构建DataFrame
        rows = []
        for item in features_list:
            row = {
                'subject_id': item['subject_id'],
                'group': item['group'],
                **item['features']
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        # 保存CSV
        df.to_csv(filepath, index=False, encoding='utf-8')

        logger.info(f"CSV已导出: {filepath}, 共 {len(df)} 行")
        return str(filepath)

    def _export_to_json(self, features_list: List[Dict], strategy: str, timestamp: str) -> str:
        """
        导出特征向量到JSON文件

        Args:
            features_list: 特征列表
            strategy: 策略
            timestamp: 时间戳

        Returns:
            导出文件路径
        """
        filename = f'features_strategy{strategy}_{timestamp}.json'
        filepath = self.export_dir / filename

        # 构建导出数据
        export_data = {
            'metadata': {
                'strategy': strategy,
                'dimension': 10 if strategy == 'A' else 69,
                'total_subjects': len(features_list),
                'timestamp': timestamp
            },
            'features': features_list
        }

        # 保存JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON已导出: {filepath}, 共 {len(features_list)} 个受试者")
        return str(filepath)

    def _extract_single_subject_optimized(self, subject_id: str, group: str,
                                          m04_data: pd.DataFrame,
                                          m05_data: Optional[pd.DataFrame],
                                          m04_feature_names: List[str],
                                          m05_feature_names: List[str]) -> Dict:
        """
        优化版单受试者特征提取（使用预加载的数据，避免重复加载）

        Args:
            subject_id: 受试者ID
            group: 分组
            m04_data: Module04预加载数据 (DataFrame)
            m05_data: Module05预加载数据 (DataFrame)
            m04_feature_names: Module04特征名称列表
            m05_feature_names: Module05特征名称列表

        Returns:
            特征提取结果
        """
        # 1. 提取Module04特征（从预加载数据中）
        m04_features = {}
        subject_data = m04_data[m04_data['subject_id'] == subject_id]

        if len(subject_data) > 0:
            for feature_name in m04_feature_names:
                if feature_name in subject_data.columns:
                    mean_value = subject_data[feature_name].mean()
                    m04_features[f"m04_{feature_name}"] = round(float(mean_value), 4)
                else:
                    m04_features[f"m04_{feature_name}"] = None
        else:
            m04_features = {f"m04_{name}": None for name in m04_feature_names}

        # 2. 提取Module05特征（从预加载数据中）
        m05_features = {}
        if m05_data is not None:
            subject_m05_data = m05_data[m05_data['subject_id'].str.lower() == subject_id.lower()]

            if len(subject_m05_data) > 0:
                for feature_name in m05_feature_names:
                    col_name = feature_name.lower()
                    if col_name in subject_m05_data.columns:
                        mean_value = subject_m05_data[col_name].mean()
                        key_name = f"m05_{col_name.replace('-', '_')}"
                        m05_features[key_name] = round(float(mean_value), 4)
                    else:
                        key_name = f"m05_{col_name.replace('-', '_')}"
                        m05_features[key_name] = None
            else:
                m05_features = {f"m05_{name.lower().replace('-', '_')}": None for name in m05_feature_names}
        else:
            m05_features = {f"m05_{name.lower().replace('-', '_')}": None for name in m05_feature_names}

        # 3. 合并特征
        combined_features = {**m04_features, **m05_features}

        return {
            'subject_id': subject_id,
            'group': group,
            'features': combined_features
        }

    # ========================================
    # 缓存管理
    # ========================================

    def clear_cache(self, module: str = 'all') -> Dict:
        """
        清除缓存的敏感度分析结果

        Args:
            module: 要清除的模块 (m04/m05/all)

        Returns:
            清除结果信息
        """
        cleared_files = []

        if module in ['m04', 'all']:
            m04_files = list(self.cache_dir.glob('m04_sensitivity_*.json'))
            for f in m04_files:
                f.unlink()
                cleared_files.append(str(f.name))

        if module in ['m05', 'all']:
            m05_files = list(self.cache_dir.glob('m05_sensitivity_*.json'))
            for f in m05_files:
                f.unlink()
                cleared_files.append(str(f.name))

        logger.info(f"缓存已清除: {cleared_files}")

        return {
            'message': f'已清除 {len(cleared_files)} 个缓存文件',
            'cleared_files': cleared_files
        }
