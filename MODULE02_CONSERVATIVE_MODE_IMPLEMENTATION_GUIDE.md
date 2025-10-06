# Module02 保守模式预处理实施指南

## 文档信息
- **版本**: 1.0
- **日期**: 2025-10-06
- **目标**: 将保守模式预处理集成到Module02现有架构中

---

## 目录
1. [架构设计](#1-架构设计)
2. [文件结构变更](#2-文件结构变更)
3. [核心组件开发](#3-核心组件开发)
4. [API接口设计](#4-api接口设计)
5. [前端界面改造](#5-前端界面改造)
6. [数据库Schema变更](#6-数据库schema变更)
7. [测试计划](#7-测试计划)
8. [部署与迁移](#8-部署与迁移)

---

## 1. 架构设计

### 1.1 设计原则

```
原则1: 向后兼容 - 不破坏现有功能
原则2: 可配置性 - 用户可选择预处理模式
原则3: 可追溯性 - 记录所有处理决策
原则4: 模块化 - 各阶段独立可测试
```

### 1.2 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Module02 预处理系统                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐        ┌──────────────┐                    │
│  │  前端UI      │───────>│  API Gateway  │                    │
│  │ (配置选择)   │        │  /api/m02/... │                    │
│  └─────────────┘        └──────┬───────┘                    │
│                                 │                             │
│                                 v                             │
│         ┌───────────────────────────────────┐                │
│         │   PreprocessingOrchestrator       │                │
│         │   (预处理协调器 - 新增)            │                │
│         └───────────┬───────────────────────┘                │
│                     │                                         │
│         ┌───────────┴───────────┐                            │
│         │                       │                            │
│         v                       v                            │
│  ┌─────────────┐        ┌─────────────┐                     │
│  │ Legacy Mode │        │Conservative │                     │
│  │  (兼容模式)  │        │    Mode     │                     │
│  └──────┬──────┘        └──────┬──────┘                     │
│         │                      │                             │
│         v                      v                             │
│  ┌─────────────────────────────────────────┐                │
│  │        预处理阶段 (Stage Pipeline)       │                │
│  ├─────────────────────────────────────────┤                │
│  │ Stage1: QualityAssessment (质量评估)     │                │
│  │ Stage2: DataCleaning (数据清理)          │                │
│  │ Stage3: NoiseReduction (降噪-可选)       │                │
│  │ Stage4: EventDetection (事件检测-IVT)    │                │
│  └─────────────────────────────────────────┘                │
│                     │                                         │
│                     v                                         │
│         ┌───────────────────────┐                            │
│         │  ProcessingReport     │                            │
│         │  (处理报告生成器)      │                            │
│         └───────────────────────┘                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 数据流

```
原始CSV数据
    │
    ├─> [读取 & 验证]
    │
    ├─> [模式选择: Legacy | Conservative]
    │
    ├─> [Stage1: 质量评估]
    │     ├─ 采样率检查
    │     ├─ 有效数据率
    │     ├─ 眨眼检测
    │     └─ 生成质量报告
    │
    ├─> [Stage2: 数据清理]
    │     ├─ Legacy: 插值缺失值
    │     └─ Conservative: 仅标记
    │
    ├─> [Stage3: 噪声降低]
    │     ├─ Legacy: 强制高斯滤波
    │     └─ Conservative: 条件中值滤波
    │
    ├─> [Stage4: IVT事件检测]
    │     ├─ 速度计算
    │     ├─ 注视/扫视分类
    │     └─ 事件序列生成
    │
    └─> [输出]
          ├─ processed_data.csv (处理后数据)
          ├─ events.json (事件序列)
          ├─ quality_report.json (质量报告)
          └─ processing_log.json (处理日志)
```

---

## 2. 文件结构变更

### 2.1 新增文件

```
new_project/src/modules/module02_preprocessing/
│
├── orchestrator.py                    # 新增: 预处理协调器
├── stages/                            # 新增: 预处理阶段目录
│   ├── __init__.py
│   ├── base_stage.py                 # 新增: 阶段基类
│   ├── quality_assessment.py         # 新增: Stage1 质量评估
│   ├── data_cleaning_conservative.py # 新增: Stage2 保守清理
│   ├── noise_reduction.py            # 新增: Stage3 噪声降低
│   └── ivt_detection.py              # 新增: Stage4 IVT检测
│
├── events/                            # 新增: 事件处理目录
│   ├── __init__.py
│   ├── event_detector.py             # 新增: IVT事件检测器
│   └── event_types.py                # 新增: 事件类型定义
│
├── reports/                           # 新增: 报告生成目录
│   ├── __init__.py
│   ├── quality_report_generator.py   # 新增: 质量报告
│   └── processing_report_generator.py # 新增: 处理报告
│
├── configs/                           # 新增: 配置模板目录
│   ├── __init__.py
│   ├── conservative_mode.py          # 新增: 保守模式配置
│   ├── legacy_mode.py                # 新增: 兼容模式配置
│   └── adaptive_params.py            # 新增: 自适应参数
│
└── utils/                             # 新增: 工具函数
    ├── __init__.py
    ├── velocity_calculator.py        # 新增: 速度计算
    ├── blink_detector.py             # 新增: 眨眼检测
    └── quality_metrics.py            # 新增: 质量指标计算
```

### 2.2 修改文件

```
需要修改的现有文件:
├── api.py                            # 修改: 新增预处理接口
├── pipeline.py                       # 修改: 集成新协调器
└── __init__.py                       # 修改: 导出新组件
```

---

## 3. 核心组件开发

### 3.1 预处理协调器 (Orchestrator)

**文件**: `orchestrator.py`

```python
"""
预处理协调器

统一管理预处理流程，支持多种预处理模式
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from enum import Enum

from .stages.quality_assessment import QualityAssessmentStage
from .stages.data_cleaning_conservative import DataCleaningConservativeStage
from .stages.noise_reduction import NoiseReductionStage
from .stages.ivt_detection import IVTDetectionStage
from .reports.quality_report_generator import QualityReportGenerator
from .reports.processing_report_generator import ProcessingReportGenerator
from .configs.conservative_mode import get_conservative_config
from .configs.legacy_mode import get_legacy_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PreprocessingMode(Enum):
    """预处理模式枚举"""
    CONSERVATIVE = "conservative"  # 保守模式(推荐)
    LEGACY = "legacy"              # 兼容模式(旧行为)
    CUSTOM = "custom"              # 自定义模式


class PreprocessingOrchestrator:
    """
    预处理协调器

    职责:
    1. 管理预处理流程
    2. 协调各个阶段
    3. 生成处理报告
    4. 支持多种预处理模式
    """

    def __init__(self, mode: PreprocessingMode = PreprocessingMode.CONSERVATIVE):
        """
        初始化协调器

        Args:
            mode: 预处理模式
        """
        self.mode = mode
        self.config = self._load_config(mode)

        # 初始化各阶段
        self.stages = self._initialize_stages()

        # 报告生成器
        self.quality_reporter = QualityReportGenerator()
        self.processing_reporter = ProcessingReportGenerator()

    def _load_config(self, mode: PreprocessingMode) -> Dict:
        """加载配置"""
        if mode == PreprocessingMode.CONSERVATIVE:
            return get_conservative_config()
        elif mode == PreprocessingMode.LEGACY:
            return get_legacy_config()
        else:
            # 自定义模式使用保守配置作为基础
            return get_conservative_config()

    def _initialize_stages(self) -> List:
        """
        初始化处理阶段

        Returns:
            阶段列表
        """
        stages = []

        # Stage 1: 质量评估(所有模式都需要)
        stages.append(QualityAssessmentStage(
            config=self.config.get('quality_assessment', {})
        ))

        # Stage 2: 数据清理
        if self.mode == PreprocessingMode.CONSERVATIVE:
            stages.append(DataCleaningConservativeStage(
                config=self.config.get('cleaning', {})
            ))
        else:
            # Legacy模式使用旧的DataCleaner
            from .data_cleaner import DataCleaner
            stages.append(DataCleaner())

        # Stage 3: 噪声降低(可选)
        if self.config.get('noise_reduction', {}).get('enabled', False):
            stages.append(NoiseReductionStage(
                config=self.config.get('noise_reduction', {})
            ))

        # Stage 4: IVT事件检测(仅保守模式)
        if self.mode == PreprocessingMode.CONSERVATIVE:
            stages.append(IVTDetectionStage(
                config=self.config.get('ivt', {})
            ))

        return stages

    def process(
        self,
        df: pd.DataFrame,
        subject_id: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict, Dict]:
        """
        执行完整预处理流程

        Args:
            df: 原始数据DataFrame
            subject_id: 受试者ID
            metadata: 元数据(年龄、任务类型等)

        Returns:
            (处理后DataFrame, 事件数据, 完整报告)
        """
        logger.info(f"开始预处理 subject={subject_id}, mode={self.mode.value}")

        # 初始化报告
        report = {
            'subject_id': subject_id,
            'mode': self.mode.value,
            'start_time': datetime.now().isoformat(),
            'metadata': metadata or {},
            'stages': [],
            'original_data_points': len(df)
        }

        # 执行预处理阶段
        df_current = df.copy()
        events_data = None

        for i, stage in enumerate(self.stages, 1):
            logger.info(f"执行阶段 {i}/{len(self.stages)}: {stage.__class__.__name__}")

            try:
                # 执行阶段
                stage_result = stage.process(df_current, metadata)

                # 更新数据
                if isinstance(stage_result, tuple):
                    if len(stage_result) == 2:
                        df_current, stage_log = stage_result
                    elif len(stage_result) == 3:
                        df_current, stage_log, events_data = stage_result
                else:
                    df_current = stage_result
                    stage_log = {'status': 'completed'}

                # 记录阶段日志
                report['stages'].append({
                    'stage': i,
                    'name': stage.__class__.__name__,
                    'status': 'success',
                    'log': stage_log,
                    'data_points_after': len(df_current)
                })

            except Exception as e:
                logger.error(f"阶段 {i} 执行失败: {str(e)}")
                report['stages'].append({
                    'stage': i,
                    'name': stage.__class__.__name__,
                    'status': 'failed',
                    'error': str(e)
                })
                raise

        # 完成报告
        report['end_time'] = datetime.now().isoformat()
        report['final_data_points'] = len(df_current)
        report['processing_success'] = True

        logger.info(f"预处理完成 subject={subject_id}")

        return df_current, events_data or {}, report

    def process_file(
        self,
        input_path: str,
        output_dir: str,
        subject_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        处理单个文件

        Args:
            input_path: 输入文件路径
            output_dir: 输出目录
            subject_id: 受试者ID(可选,从文件名推断)
            metadata: 元数据

        Returns:
            处理结果字典
        """
        try:
            input_path = Path(input_path)
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 推断subject_id
            if subject_id is None:
                subject_id = input_path.stem

            # 读取数据
            logger.info(f"读取文件: {input_path}")
            df = pd.read_csv(input_path)

            # 执行预处理
            df_processed, events_data, report = self.process(
                df, subject_id, metadata
            )

            # 保存结果
            output_files = self._save_results(
                subject_id=subject_id,
                df_processed=df_processed,
                events_data=events_data,
                report=report,
                output_dir=output_dir
            )

            return {
                'success': True,
                'subject_id': subject_id,
                'input_file': str(input_path),
                'output_files': output_files,
                'report': report
            }

        except Exception as e:
            logger.error(f"处理文件失败 {input_path}: {str(e)}")
            return {
                'success': False,
                'subject_id': subject_id,
                'input_file': str(input_path),
                'error': str(e)
            }

    def _save_results(
        self,
        subject_id: str,
        df_processed: pd.DataFrame,
        events_data: Dict,
        report: Dict,
        output_dir: Path
    ) -> Dict[str, str]:
        """
        保存处理结果

        Returns:
            输出文件路径字典
        """
        output_files = {}

        # 1. 保存处理后的数据
        data_file = output_dir / f"{subject_id}_processed.csv"
        df_processed.to_csv(data_file, index=False)
        output_files['processed_data'] = str(data_file)
        logger.info(f"已保存: {data_file}")

        # 2. 保存事件数据(如果有)
        if events_data and self.mode == PreprocessingMode.CONSERVATIVE:
            events_file = output_dir / f"{subject_id}_events.json"
            with open(events_file, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, ensure_ascii=False, indent=2)
            output_files['events'] = str(events_file)
            logger.info(f"已保存: {events_file}")

        # 3. 保存处理报告
        report_file = output_dir / f"{subject_id}_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        output_files['report'] = str(report_file)
        logger.info(f"已保存: {report_file}")

        # 4. 生成质量报告(如果有质量评估数据)
        quality_stage = next(
            (s for s in report['stages'] if 'QualityAssessment' in s['name']),
            None
        )
        if quality_stage:
            quality_report = self.quality_reporter.generate(
                subject_id=subject_id,
                quality_data=quality_stage['log']
            )
            quality_file = output_dir / f"{subject_id}_quality.json"
            with open(quality_file, 'w', encoding='utf-8') as f:
                json.dump(quality_report, f, ensure_ascii=False, indent=2)
            output_files['quality_report'] = str(quality_file)
            logger.info(f"已保存: {quality_file}")

        return output_files

    def update_config(self, config: Dict):
        """更新配置"""
        self.config.update(config)
        self.stages = self._initialize_stages()
        logger.info("配置已更新，重新初始化处理阶段")
```

**关键设计点**:
1. ✅ 支持多种模式切换
2. ✅ 阶段化处理,易于测试和扩展
3. ✅ 完整的日志和报告
4. ✅ 错误处理和回滚机制

---

### 3.2 阶段基类 (Base Stage)

**文件**: `stages/base_stage.py`

```python
"""
预处理阶段基类

定义所有预处理阶段的通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Union
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseStage(ABC):
    """
    预处理阶段基类

    所有预处理阶段必须继承此类
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化阶段

        Args:
            config: 阶段配置
        """
        self.config = config or {}
        self.stage_name = self.__class__.__name__

    @abstractmethod
    def process(
        self,
        df: pd.DataFrame,
        metadata: Optional[Dict] = None
    ) -> Union[pd.DataFrame, Tuple]:
        """
        处理数据

        Args:
            df: 输入数据
            metadata: 元数据

        Returns:
            处理后的数据 或 (数据, 日志) 或 (数据, 日志, 额外输出)
        """
        pass

    def validate_input(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        验证输入数据

        Args:
            df: 输入数据

        Returns:
            (是否有效, 错误信息)
        """
        if df is None or df.empty:
            return False, "数据为空"

        return True, ""

    def log(self, message: str, level: str = 'info'):
        """
        记录日志

        Args:
            message: 日志消息
            level: 日志级别
        """
        log_msg = f"[{self.stage_name}] {message}"

        if level == 'info':
            logger.info(log_msg)
        elif level == 'warning':
            logger.warning(log_msg)
        elif level == 'error':
            logger.error(log_msg)
        elif level == 'debug':
            logger.debug(log_msg)
```

---

### 3.3 Stage1: 质量评估

**文件**: `stages/quality_assessment.py`

```python
"""
Stage 1: 质量评估阶段

评估眼动数据质量,检测眨眼,计算质量指标
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from .base_stage import BaseStage
from ..utils.blink_detector import BlinkDetector
from ..utils.quality_metrics import QualityMetrics


class QualityAssessmentStage(BaseStage):
    """
    质量评估阶段

    执行:
    1. 采样率检查
    2. 有效数据率计算
    3. 眨眼检测
    4. 噪声水平评估
    5. 生成质量评分
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.blink_detector = BlinkDetector(config.get('blink_detection', {}))
        self.quality_metrics = QualityMetrics()

    def process(
        self,
        df: pd.DataFrame,
        metadata: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        执行质量评估

        Returns:
            (添加标记列的DataFrame, 质量报告)
        """
        self.log("开始质量评估")

        # 验证输入
        valid, error = self.validate_input(df)
        if not valid:
            raise ValueError(f"输入数据无效: {error}")

        df_result = df.copy()
        quality_report = {}

        # 1. 采样率检查
        sampling_metrics = self._check_sampling_rate(df_result)
        quality_report['sampling'] = sampling_metrics
        self.log(f"采样率: {sampling_metrics['actual_rate']:.2f} Hz")

        # 2. 有效数据率
        validity_metrics = self._calculate_validity(df_result)
        quality_report['validity'] = validity_metrics
        self.log(f"有效数据率: {validity_metrics['valid_rate']:.2%}")

        # 3. 眨眼检测
        df_result, blink_metrics = self._detect_blinks(df_result)
        quality_report['blinks'] = blink_metrics
        self.log(f"检测到 {blink_metrics['blink_count']} 次眨眼")

        # 4. 噪声评估
        noise_metrics = self._assess_noise(df_result)
        quality_report['noise'] = noise_metrics
        self.log(f"噪声水平: {noise_metrics['noise_level']:.4f}°")

        # 5. 综合质量评分
        quality_score = self._calculate_quality_score(quality_report)
        quality_report['quality_score'] = quality_score
        quality_report['quality_grade'] = self._grade_quality(quality_score)

        self.log(f"质量评分: {quality_score:.2f}/100 ({quality_report['quality_grade']})")

        return df_result, quality_report

    def _check_sampling_rate(self, df: pd.DataFrame) -> Dict:
        """检查采样率"""
        if 'timestamp' not in df.columns:
            return {
                'status': 'error',
                'message': '缺少timestamp列'
            }

        # 计算实际采样率
        time_diffs = df['timestamp'].diff().dropna()
        mean_interval = time_diffs.mean()  # 秒
        actual_rate = 1.0 / mean_interval if mean_interval > 0 else 0

        # 采样抖动
        sampling_jitter = time_diffs.std() * 1000  # ms

        # 期望采样率
        expected_rate = self.config.get('expected_sampling_rate', 60)
        tolerance = self.config.get('sampling_rate_tolerance', 10)

        # 判断是否在容差范围内
        rate_ok = abs(actual_rate - expected_rate) <= tolerance

        return {
            'expected_rate': expected_rate,
            'actual_rate': actual_rate,
            'sampling_jitter': sampling_jitter,
            'rate_ok': rate_ok,
            'mean_interval_ms': mean_interval * 1000,
            'std_interval_ms': time_diffs.std() * 1000
        }

    def _calculate_validity(self, df: pd.DataFrame) -> Dict:
        """计算有效数据率"""
        total_points = len(df)

        # 检查是否有validity列
        if 'validity' in df.columns:
            valid_points = (df['validity'] == 1).sum()
        else:
            # 如果没有validity列,检查x,y是否为NaN
            valid_points = (~df[['x', 'y']].isna().any(axis=1)).sum()

        valid_rate = valid_points / total_points if total_points > 0 else 0

        # 判断是否达标
        min_rate = self.config.get('min_valid_data_rate', 0.75)
        rate_ok = valid_rate >= min_rate

        return {
            'total_points': total_points,
            'valid_points': valid_points,
            'invalid_points': total_points - valid_points,
            'valid_rate': valid_rate,
            'rate_ok': rate_ok,
            'min_required_rate': min_rate
        }

    def _detect_blinks(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        检测眨眼

        添加列:
        - is_blink: bool, 是否为眨眼样本
        - blink_id: int, 眨眼事件ID(-1表示非眨眼)
        """
        df_result = df.copy()

        # 使用BlinkDetector检测
        blink_segments = self.blink_detector.detect(df_result)

        # 标记眨眼样本
        df_result['is_blink'] = False
        df_result['blink_id'] = -1

        for blink_id, segment in enumerate(blink_segments):
            start_idx = segment['start_index']
            end_idx = segment['end_index']
            df_result.loc[start_idx:end_idx, 'is_blink'] = True
            df_result.loc[start_idx:end_idx, 'blink_id'] = blink_id

        # 统计指标
        blink_count = len(blink_segments)
        blink_durations = [s['duration_ms'] for s in blink_segments]

        metrics = {
            'blink_count': blink_count,
            'blink_segments': blink_segments,
            'mean_duration_ms': np.mean(blink_durations) if blink_durations else 0,
            'total_blink_time_ms': sum(blink_durations),
            'blink_rate_per_minute': blink_count / (df_result['timestamp'].iloc[-1] - df_result['timestamp'].iloc[0]) * 60 if len(df_result) > 1 else 0
        }

        return df_result, metrics

    def _assess_noise(self, df: pd.DataFrame) -> Dict:
        """评估噪声水平"""
        # 排除眨眼片段
        if 'is_blink' in df.columns:
            df_clean = df[~df['is_blink']].copy()
        else:
            df_clean = df.copy()

        if len(df_clean) < 10:
            return {
                'noise_level': np.nan,
                'message': '有效数据点太少,无法评估噪声'
            }

        # 计算位置波动(点对点距离的标准差)
        dx = df_clean['x'].diff().dropna()
        dy = df_clean['y'].diff().dropna()
        distances = np.sqrt(dx**2 + dy**2)

        noise_level = distances.std()

        # 判断噪声是否过高
        noise_threshold = self.config.get('noise_threshold', 0.1)  # 度
        noise_high = noise_level > noise_threshold

        return {
            'noise_level': noise_level,
            'noise_threshold': noise_threshold,
            'noise_high': noise_high,
            'rms_noise': np.sqrt((dx**2 + dy**2).mean()),
            'mean_displacement': distances.mean()
        }

    def _calculate_quality_score(self, quality_report: Dict) -> float:
        """
        计算综合质量评分 (0-100)

        评分权重:
        - 采样率: 20%
        - 有效数据率: 40%
        - 眨眼率: 20%
        - 噪声水平: 20%
        """
        score = 0.0

        # 1. 采样率评分(20分)
        if quality_report['sampling']['rate_ok']:
            score += 20
        else:
            # 部分得分
            rate_diff = abs(
                quality_report['sampling']['actual_rate'] -
                quality_report['sampling']['expected_rate']
            )
            tolerance = quality_report['sampling'].get('tolerance', 10)
            score += max(0, 20 * (1 - rate_diff / (2 * tolerance)))

        # 2. 有效数据率评分(40分)
        valid_rate = quality_report['validity']['valid_rate']
        score += 40 * valid_rate

        # 3. 眨眼率评分(20分)
        blink_rate = quality_report['blinks']['blink_rate_per_minute']
        # 正常眨眼率: 15-20次/分钟
        if 10 <= blink_rate <= 25:
            score += 20
        elif blink_rate < 10:
            score += 20 * (blink_rate / 10)
        else:
            score += max(0, 20 * (1 - (blink_rate - 25) / 25))

        # 4. 噪声评分(20分)
        if not quality_report['noise']['noise_high']:
            score += 20
        else:
            noise = quality_report['noise']['noise_level']
            threshold = quality_report['noise']['noise_threshold']
            score += max(0, 20 * (1 - (noise - threshold) / threshold))

        return round(score, 2)

    def _grade_quality(self, score: float) -> str:
        """质量等级"""
        if score >= 90:
            return "优秀(Excellent)"
        elif score >= 75:
            return "良好(Good)"
        elif score >= 60:
            return "及格(Fair)"
        else:
            return "较差(Poor)"
```

---

### 3.4 Stage2: 保守数据清理

**文件**: `stages/data_cleaning_conservative.py`

```python
"""
Stage 2: 保守数据清理阶段

最小干预原则:仅标记异常,不修改原始数据
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from .base_stage import BaseStage


class DataCleaningConservativeStage(BaseStage):
    """
    保守数据清理阶段

    执行:
    1. 范围裁剪(硬件限制)
    2. 移除明显无效样本(validity=0)
    3. 标记缺失值(不插值!)
    4. 标记极端异常值(不插值!)
    5. 标记眨眼片段(不插值!)
    """

    def process(
        self,
        df: pd.DataFrame,
        metadata: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        执行保守清理

        Returns:
            (添加标记列的DataFrame, 清理日志)
        """
        self.log("开始保守数据清理")

        df_result = df.copy()
        cleaning_log = {
            'original_points': len(df),
            'steps': []
        }

        # 1. 范围裁剪
        if self.config.get('clip_range', True):
            df_result, clip_log = self._clip_coordinates(df_result)
            cleaning_log['steps'].append(clip_log)

        # 2. 移除明显无效样本
        if self.config.get('remove_invalid_samples', True):
            df_result, invalid_log = self._remove_invalid(df_result)
            cleaning_log['steps'].append(invalid_log)

        # 3. 标记缺失值
        df_result, missing_log = self._mark_missing(df_result)
        cleaning_log['steps'].append(missing_log)

        # 4. 标记极端异常值
        if self.config.get('extreme_outlier_removal', {}).get('enabled', True):
            df_result, outlier_log = self._mark_extreme_outliers(df_result)
            cleaning_log['steps'].append(outlier_log)

        # 5. 标记眨眼片段(如果还没标记)
        if 'is_blink' not in df_result.columns:
            df_result['is_blink'] = False
            df_result['blink_id'] = -1

        cleaning_log['final_points'] = len(df_result)
        cleaning_log['points_removed'] = cleaning_log['original_points'] - cleaning_log['final_points']

        self.log(f"清理完成: 移除 {cleaning_log['points_removed']} 个点")

        return df_result, cleaning_log

    def _clip_coordinates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        裁剪坐标到有效范围

        注意: 这是基于硬件物理限制的硬裁剪,不是数据修改
        """
        df_result = df.copy()

        x_range = self.config.get('x_range', [0, 1])
        y_range = self.config.get('y_range', [0, 1])

        # 统计超出范围的点
        x_out_of_range = ((df_result['x'] < x_range[0]) | (df_result['x'] > x_range[1])).sum()
        y_out_of_range = ((df_result['y'] < y_range[0]) | (df_result['y'] > y_range[1])).sum()

        # 裁剪
        df_result['x'] = df_result['x'].clip(x_range[0], x_range[1])
        df_result['y'] = df_result['y'].clip(y_range[0], y_range[1])

        return df_result, {
            'step': 'clip_coordinates',
            'x_range': x_range,
            'y_range': y_range,
            'x_clipped': int(x_out_of_range),
            'y_clipped': int(y_out_of_range)
        }

    def _remove_invalid(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        移除明显无效的样本(validity=0)

        注意: 这不是"清理",而是移除硬件标记为无效的数据
        """
        if 'validity' not in df.columns:
            return df, {
                'step': 'remove_invalid',
                'removed': 0,
                'message': '没有validity列,跳过'
            }

        original_len = len(df)
        df_result = df[df['validity'] != 0].copy()
        removed = original_len - len(df_result)

        return df_result, {
            'step': 'remove_invalid',
            'removed': removed,
            'remaining': len(df_result)
        }

    def _mark_missing(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        标记缺失值

        重要: 不插值! 仅添加标记列
        """
        df_result = df.copy()

        # 检查x,y缺失
        x_missing = df_result['x'].isna()
        y_missing = df_result['y'].isna()
        any_missing = x_missing | y_missing

        # 添加标记列
        df_result['is_missing'] = any_missing

        missing_count = any_missing.sum()

        # 根据策略处理
        strategy = self.config.get('missing_value_strategy', 'mark_only')

        if strategy == 'remove':
            df_result = df_result[~any_missing].copy()
            self.log(f"移除 {missing_count} 个缺失样本")
        else:
            self.log(f"标记 {missing_count} 个缺失样本(保留)")

        return df_result, {
            'step': 'mark_missing',
            'strategy': strategy,
            'missing_count': int(missing_count),
            'x_missing': int(x_missing.sum()),
            'y_missing': int(y_missing.sum())
        }

    def _mark_extreme_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        标记极端异常值

        基于生理极限:
        - 最大扫视速度: ~900°/s
        - 配置中使用更保守的1000°/s

        重要: 不移除! 仅标记
        """
        df_result = df.copy()

        outlier_config = self.config.get('extreme_outlier_removal', {})
        max_velocity = outlier_config.get('max_velocity_threshold', 1000)  # °/s

        # 计算点对点速度
        dx = df_result['x'].diff()
        dy = df_result['y'].diff()
        dt = df_result['timestamp'].diff()

        # 角距离(假设x,y已是归一化坐标,需转换为角度)
        # 简化: 直接使用欧氏距离
        distance = np.sqrt(dx**2 + dy**2)
        velocity = distance / dt

        # 标记极端速度
        extreme_velocity = velocity > max_velocity
        df_result['is_extreme_outlier'] = False
        df_result.loc[extreme_velocity, 'is_extreme_outlier'] = True

        outlier_count = extreme_velocity.sum()

        action = outlier_config.get('action', 'mark')
        if action == 'remove':
            df_result = df_result[~extreme_velocity].copy()
            self.log(f"移除 {outlier_count} 个极端异常值")
        else:
            self.log(f"标记 {outlier_count} 个极端异常值(保留)")

        return df_result, {
            'step': 'mark_extreme_outliers',
            'max_velocity_threshold': max_velocity,
            'outlier_count': int(outlier_count),
            'action': action,
            'max_velocity_detected': float(velocity.max()) if len(velocity) > 0 else 0
        }
```

**关键设计点**:
- ✅ **不插值**: 所有异常仅标记,保留原始数据
- ✅ **可追溯**: 每个标记都有对应的列
- ✅ **可选移除**: 通过配置控制是否移除

---

### 3.5 Stage3: 噪声降低(可选)

**文件**: `stages/noise_reduction.py`

```python
"""
Stage 3: 噪声降低阶段(可选)

仅在数据噪声过高时启用
使用中值滤波而非高斯滤波
"""
import pandas as pd
import numpy as np
from scipy.signal import medfilt, savgol_filter
from typing import Dict, Optional, Tuple
from .base_stage import BaseStage


class NoiseReductionStage(BaseStage):
    """
    噪声降低阶段

    特点:
    1. 默认关闭,仅在需要时启用
    2. 使用中值滤波(推荐)或Savgol滤波
    3. 小窗口(w=3)保留瞬态特征
    4. 不处理瞳孔数据
    """

    def process(
        self,
        df: pd.DataFrame,
        metadata: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        执行噪声降低

        Returns:
            (滤波后DataFrame, 降噪日志)
        """
        self.log("开始噪声降低")

        # 检查是否应该启用
        if not self._should_enable(df):
            self.log("噪声水平在可接受范围内,跳过降噪")
            return df, {
                'enabled': False,
                'reason': '噪声水平低'
            }

        df_result = df.copy()
        noise_log = {
            'enabled': True,
            'method': self.config.get('method', 'median'),
            'columns_filtered': []
        }

        # 获取滤波方法
        method = self.config.get('method', 'median')

        # 只滤波x,y,不处理瞳孔
        apply_to = self.config.get(f'{method}_filter', {}).get('apply_to', ['x', 'y'])

        for col in apply_to:
            if col not in df_result.columns:
                continue

            # 排除标记为异常的点
            mask = self._get_valid_mask(df_result)

            if mask.sum() < 10:
                self.log(f"列 {col} 有效点太少,跳过")
                continue

            # 应用滤波
            if method == 'median':
                df_result.loc[mask, col] = self._median_filter(
                    df_result.loc[mask, col].values
                )
            elif method == 'savgol':
                df_result.loc[mask, col] = self._savgol_filter(
                    df_result.loc[mask, col].values
                )
            else:
                self.log(f"未知滤波方法: {method}", level='warning')
                continue

            noise_log['columns_filtered'].append(col)
            self.log(f"已滤波列: {col}")

        self.log(f"降噪完成,滤波了 {len(noise_log['columns_filtered'])} 列")

        return df_result, noise_log

    def _should_enable(self, df: pd.DataFrame) -> bool:
        """
        判断是否应该启用降噪

        基于:
        1. 配置中的auto_enable_if条件
        2. 实际数据噪声水平
        """
        auto_enable = self.config.get('auto_enable_if', {})

        # 计算噪声水平
        mask = self._get_valid_mask(df)
        if mask.sum() < 10:
            return False

        dx = df.loc[mask, 'x'].diff().dropna()
        dy = df.loc[mask, 'y'].diff().dropna()
        noise_level = np.sqrt((dx**2 + dy**2).mean())

        # 检查阈值
        if 'noise_level' in auto_enable:
            if noise_level > auto_enable['noise_level']:
                self.log(f"噪声水平 {noise_level:.4f} 超过阈值 {auto_enable['noise_level']}")
                return True

        # 检查采样抖动
        if 'sampling_jitter' in auto_enable:
            dt = df['timestamp'].diff().dropna()
            jitter = dt.std() * 1000  # ms
            if jitter > auto_enable['sampling_jitter']:
                self.log(f"采样抖动 {jitter:.2f}ms 超过阈值 {auto_enable['sampling_jitter']}ms")
                return True

        return False

    def _get_valid_mask(self, df: pd.DataFrame) -> pd.Series:
        """
        获取有效数据掩码

        排除:
        - 眨眼片段
        - 缺失值
        - 极端异常值
        """
        mask = pd.Series(True, index=df.index)

        if 'is_blink' in df.columns:
            mask &= ~df['is_blink']

        if 'is_missing' in df.columns:
            mask &= ~df['is_missing']

        if 'is_extreme_outlier' in df.columns:
            mask &= ~df['is_extreme_outlier']

        return mask

    def _median_filter(self, data: np.ndarray) -> np.ndarray:
        """
        中值滤波

        Args:
            data: 输入数据

        Returns:
            滤波后数据
        """
        window_size = self.config.get('median_filter', {}).get('window_size', 3)

        # scipy.signal.medfilt要求window_size为奇数
        if window_size % 2 == 0:
            window_size += 1

        return medfilt(data, kernel_size=window_size)

    def _savgol_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Savitzky-Golay滤波

        Args:
            data: 输入数据

        Returns:
            滤波后数据
        """
        savgol_config = self.config.get('savgol_filter', {})
        window_size = savgol_config.get('window_size', 5)
        polyorder = savgol_config.get('polyorder', 2)

        # 确保window_size为奇数
        if window_size % 2 == 0:
            window_size += 1

        # 确保window_size > polyorder
        if window_size <= polyorder:
            window_size = polyorder + 2

        # 确保数据点足够
        if len(data) < window_size:
            self.log(f"数据点 {len(data)} < 窗口 {window_size},跳过", level='warning')
            return data

        return savgol_filter(data, window_length=window_size, polyorder=polyorder)
```

---

### 3.6 Stage4: IVT事件检测

**文件**: `stages/ivt_detection.py`

```python
"""
Stage 4: IVT事件检测阶段

使用I-VT算法检测注视和扫视事件
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from .base_stage import BaseStage
from ..events.event_detector import IVTEventDetector
from ..events.event_types import EventType
from ..configs.adaptive_params import get_adaptive_ivt_threshold


class IVTDetectionStage(BaseStage):
    """
    IVT事件检测阶段

    执行:
    1. 速度计算
    2. 注视/扫视分类
    3. 事件过滤和合并
    4. 生成事件序列
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.event_detector = IVTEventDetector(config)

    def process(
        self,
        df: pd.DataFrame,
        metadata: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict, Dict]:
        """
        执行IVT检测

        Returns:
            (添加事件标记的DataFrame, 检测日志, 事件数据)
        """
        self.log("开始IVT事件检测")

        # 自适应调整阈值
        velocity_threshold = self._get_adaptive_threshold(metadata)
        self.event_detector.update_threshold(velocity_threshold)

        # 执行检测
        df_result, events = self.event_detector.detect(df)

        # 生成日志
        detection_log = {
            'velocity_threshold': velocity_threshold,
            'events_detected': {
                'fixations': len([e for e in events if e['type'] == EventType.FIXATION.value]),
                'saccades': len([e for e in events if e['type'] == EventType.SACCADE.value]),
                'blinks': len([e for e in events if e['type'] == EventType.BLINK.value]),
                'total': len(events)
            },
            'fixation_stats': self._compute_fixation_stats(events),
            'saccade_stats': self._compute_saccade_stats(events)
        }

        # 事件数据(用于后续分析)
        events_data = {
            'events': events,
            'event_sequence': [e['type'] for e in events],
            'summary': detection_log
        }

        self.log(f"检测到 {len(events)} 个事件")
        self.log(f"注视: {detection_log['events_detected']['fixations']}, "
                 f"扫视: {detection_log['events_detected']['saccades']}, "
                 f"眨眼: {detection_log['events_detected']['blinks']}")

        return df_result, detection_log, events_data

    def _get_adaptive_threshold(self, metadata: Optional[Dict] = None) -> float:
        """
        获取自适应速度阈值

        考虑:
        - 受试者年龄
        - 任务类型
        """
        base_threshold = self.config.get('velocity_threshold', 30)  # °/s

        if metadata is None:
            return base_threshold

        # 使用自适应函数
        adaptive_threshold = get_adaptive_ivt_threshold(
            age=metadata.get('age'),
            task_type=metadata.get('task_type')
        )

        if adaptive_threshold != base_threshold:
            self.log(f"自适应阈值: {base_threshold} -> {adaptive_threshold} °/s")

        return adaptive_threshold

    def _compute_fixation_stats(self, events: List[Dict]) -> Dict:
        """计算注视统计"""
        fixations = [e for e in events if e['type'] == EventType.FIXATION.value]

        if not fixations:
            return {}

        durations = [f['duration_ms'] for f in fixations]

        return {
            'count': len(fixations),
            'mean_duration_ms': np.mean(durations),
            'median_duration_ms': np.median(durations),
            'min_duration_ms': np.min(durations),
            'max_duration_ms': np.max(durations),
            'total_duration_ms': np.sum(durations)
        }

    def _compute_saccade_stats(self, events: List[Dict]) -> Dict:
        """计算扫视统计"""
        saccades = [e for e in events if e['type'] == EventType.SACCADE.value]

        if not saccades:
            return {}

        amplitudes = [s.get('amplitude', 0) for s in saccades]
        durations = [s['duration_ms'] for s in saccades]

        return {
            'count': len(saccades),
            'mean_amplitude': np.mean(amplitudes),
            'mean_duration_ms': np.mean(durations),
            'max_amplitude': np.max(amplitudes),
            'total_duration_ms': np.sum(durations)
        }
```

---

## 4. API接口设计

### 4.1 新增API端点

在 `api.py` 中新增以下端点:

```python
# ==================== 新增: 保守模式预处理接口 ====================

@m02_bp.route('/preprocessing/modes', methods=['GET'])
@handle_errors
def get_preprocessing_modes():
    """
    获取可用的预处理模式

    Returns:
        模式列表及说明
    """
    modes = [
        {
            'id': 'conservative',
            'name': '保守模式(推荐)',
            'description': '最小干预,仅标记异常,不修改原始数据。适合新研究。',
            'features': [
                '质量评估和眨眼检测',
                '仅标记缺失值和异常值(不插值)',
                '条件噪声降低(默认关闭)',
                'IVT事件检测',
                '完整处理报告'
            ],
            'recommended': True
        },
        {
            'id': 'legacy',
            'name': '兼容模式',
            'description': '保持旧版本行为,用于对比研究。',
            'features': [
                '插值缺失值',
                '高斯平滑滤波',
                '异常值插值处理'
            ],
            'recommended': False
        },
        {
            'id': 'custom',
            'name': '自定义模式',
            'description': '用户自定义配置参数。',
            'features': [
                '完全可配置',
                '基于保守模式扩展'
            ],
            'recommended': False
        }
    ]

    return jsonify({
        'success': True,
        'modes': modes
    })


@m02_bp.route('/preprocessing/config/<mode>', methods=['GET'])
@handle_errors
def get_preprocessing_config(mode: str):
    """
    获取指定模式的配置

    Args:
        mode: 模式ID (conservative | legacy | custom)

    Returns:
        配置对象
    """
    from .configs.conservative_mode import get_conservative_config
    from .configs.legacy_mode import get_legacy_config

    if mode == 'conservative':
        config = get_conservative_config()
    elif mode == 'legacy':
        config = get_legacy_config()
    else:
        return jsonify({
            'success': False,
            'error': f'未知模式: {mode}'
        }), 400

    return jsonify({
        'success': True,
        'mode': mode,
        'config': config
    })


@m02_bp.route('/preprocessing/process', methods=['POST'])
@handle_errors
def process_with_mode():
    """
    使用指定模式处理眼动数据

    Request Body:
    {
        "subject_id": "v2_control_001",
        "input_file": "path/to/raw_data.csv",
        "mode": "conservative",
        "config": {  # 可选: 覆盖默认配置
            ...
        },
        "metadata": {  # 可选: 受试者元数据
            "age": 65,
            "task_type": "reading"
        }
    }

    Returns:
        处理结果和报告
    """
    data = request.get_json()

    subject_id = data.get('subject_id')
    input_file = data.get('input_file')
    mode = data.get('mode', 'conservative')
    custom_config = data.get('config')
    metadata = data.get('metadata')

    if not subject_id or not input_file:
        return jsonify({
            'success': False,
            'error': '缺少必需参数: subject_id, input_file'
        }), 400

    # 验证文件存在
    input_path = Path(input_file)
    if not input_path.exists():
        return jsonify({
            'success': False,
            'error': f'文件不存在: {input_file}'
        }), 404

    # 创建协调器
    try:
        mode_enum = PreprocessingMode(mode)
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'无效模式: {mode}'
        }), 400

    orchestrator = PreprocessingOrchestrator(mode=mode_enum)

    # 更新配置
    if custom_config:
        orchestrator.update_config(custom_config)

    # 设置输出目录
    output_dir = Path(f'data/preprocessing_results/{subject_id}')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 执行处理
    result = orchestrator.process_file(
        input_path=str(input_path),
        output_dir=str(output_dir),
        subject_id=subject_id,
        metadata=metadata
    )

    return jsonify(result)


@m02_bp.route('/preprocessing/batch-process', methods=['POST'])
@handle_errors
def batch_process_with_mode():
    """
    批量处理多个受试者数据

    Request Body:
    {
        "subjects": [
            {
                "subject_id": "v2_control_001",
                "input_file": "path/to/file1.csv",
                "metadata": {...}
            },
            ...
        ],
        "mode": "conservative",
        "config": {...}  # 可选
    }

    Returns:
        批量处理结果
    """
    data = request.get_json()

    subjects = data.get('subjects', [])
    mode = data.get('mode', 'conservative')
    custom_config = data.get('config')

    if not subjects:
        return jsonify({
            'success': False,
            'error': '没有待处理的受试者'
        }), 400

    # 创建协调器
    try:
        mode_enum = PreprocessingMode(mode)
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'无效模式: {mode}'
        }), 400

    orchestrator = PreprocessingOrchestrator(mode=mode_enum)

    if custom_config:
        orchestrator.update_config(custom_config)

    # 批量处理
    results = []
    successful = 0
    failed = 0

    for subject in subjects:
        subject_id = subject.get('subject_id')
        input_file = subject.get('input_file')
        metadata = subject.get('metadata')

        output_dir = Path(f'data/preprocessing_results/{subject_id}')
        output_dir.mkdir(parents=True, exist_ok=True)

        result = orchestrator.process_file(
            input_path=input_file,
            output_dir=str(output_dir),
            subject_id=subject_id,
            metadata=metadata
        )

        results.append(result)

        if result['success']:
            successful += 1
        else:
            failed += 1

    return jsonify({
        'success': True,
        'summary': {
            'total': len(subjects),
            'successful': successful,
            'failed': failed
        },
        'results': results
    })
```

### 4.2 API使用示例

```bash
# 1. 获取可用模式
curl http://localhost:9090/api/m02/preprocessing/modes

# 2. 获取保守模式配置
curl http://localhost:9090/api/m02/preprocessing/config/conservative

# 3. 处理单个文件
curl -X POST http://localhost:9090/api/m02/preprocessing/process \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "v2_control_001",
    "input_file": "data/raw/v2_control_001.csv",
    "mode": "conservative",
    "metadata": {
      "age": 65,
      "task_type": "cognitive_assessment"
    }
  }'

# 4. 批量处理
curl -X POST http://localhost:9090/api/m02/preprocessing/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "subjects": [
      {"subject_id": "v2_control_001", "input_file": "data/raw/v2_control_001.csv"},
      {"subject_id": "v2_control_002", "input_file": "data/raw/v2_control_002.csv"}
    ],
    "mode": "conservative"
  }'
```

---

## 5. 前端界面改造

### 5.1 新增UI组件

在前端添加预处理模式选择器:

```jsx
// frontend/src/components/Module02/PreprocessingModeSelector.jsx

import React, { useState, useEffect } from 'react';
import { Card, Radio, Button, Collapse, Tag, message } from 'antd';
import { CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';

const { Panel } = Collapse;

const PreprocessingModeSelector = ({ onModeChange }) => {
  const [modes, setModes] = useState([]);
  const [selectedMode, setSelectedMode] = useState('conservative');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchModes();
  }, []);

  const fetchModes = async () => {
    try {
      const response = await fetch('/api/m02/preprocessing/modes');
      const data = await response.json();
      if (data.success) {
        setModes(data.modes);
      }
    } catch (error) {
      message.error('加载预处理模式失败');
    }
  };

  const handleModeChange = (e) => {
    const mode = e.target.value;
    setSelectedMode(mode);
    onModeChange && onModeChange(mode);
  };

  return (
    <Card title="预处理模式选择">
      <Radio.Group
        value={selectedMode}
        onChange={handleModeChange}
        style={{ width: '100%' }}
      >
        {modes.map(mode => (
          <Card.Grid
            key={mode.id}
            style={{ width: '33%' }}
            hoverable
          >
            <Radio value={mode.id}>
              <strong>{mode.name}</strong>
              {mode.recommended && (
                <Tag color="green" style={{ marginLeft: 8 }}>
                  推荐
                </Tag>
              )}
            </Radio>
            <p style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              {mode.description}
            </p>
            <Collapse ghost size="small">
              <Panel header="功能特性" key="1">
                <ul style={{ fontSize: 12, paddingLeft: 20 }}>
                  {mode.features.map((feature, idx) => (
                    <li key={idx}>{feature}</li>
                  ))}
                </ul>
              </Panel>
            </Collapse>
          </Card.Grid>
        ))}
      </Radio.Group>
    </Card>
  );
};

export default PreprocessingModeSelector;
```

### 5.2 集成到数据预处理页面

修改 `frontend/src/components/Module02/DataPreprocessing.jsx`:

```jsx
import PreprocessingModeSelector from './PreprocessingModeSelector';

// ... 在组件中添加

const [preprocessingMode, setPreprocessingMode] = useState('conservative');

// ... 在render中添加

<PreprocessingModeSelector
  onModeChange={setPreprocessingMode}
/>

// ... 处理时使用选中的模式

const handleProcess = async () => {
  const requestData = {
    subject_id: selectedSubject,
    input_file: inputFile,
    mode: preprocessingMode,  // 使用选中的模式
    metadata: {
      age: subjectAge,
      task_type: taskType
    }
  };

  const response = await fetch('/api/m02/preprocessing/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
  });

  // ... 处理响应
};
```

---

## 6. 数据库Schema变更(可选)

如果需要将预处理结果存储到数据库:

```sql
-- 新增预处理结果表
CREATE TABLE preprocessing_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT NOT NULL,
    preprocessing_mode TEXT NOT NULL,  -- conservative | legacy | custom
    input_file TEXT NOT NULL,
    output_dir TEXT NOT NULL,
    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 质量指标
    quality_score REAL,
    quality_grade TEXT,
    valid_data_rate REAL,
    blink_count INTEGER,

    -- 事件统计(仅保守模式)
    fixation_count INTEGER,
    saccade_count INTEGER,

    -- 处理报告(JSON)
    full_report TEXT,

    -- 状态
    status TEXT DEFAULT 'completed',  -- completed | failed
    error_message TEXT,

    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- 索引
CREATE INDEX idx_preprocessing_subject ON preprocessing_results(subject_id);
CREATE INDEX idx_preprocessing_mode ON preprocessing_results(preprocessing_mode);
CREATE INDEX idx_preprocessing_date ON preprocessing_results(processing_date);
```

---

## 7. 测试计划

### 7.1 单元测试

```python
# tests/test_quality_assessment.py

import unittest
import pandas as pd
import numpy as np
from src.modules.module02_preprocessing.stages.quality_assessment import QualityAssessmentStage

class TestQualityAssessment(unittest.TestCase):

    def setUp(self):
        # 创建测试数据
        np.random.seed(42)
        self.df = pd.DataFrame({
            'timestamp': np.linspace(0, 10, 600),  # 60Hz, 10秒
            'x': np.random.uniform(0, 1, 600),
            'y': np.random.uniform(0, 1, 600),
            'validity': np.ones(600)
        })

        self.stage = QualityAssessmentStage({
            'expected_sampling_rate': 60,
            'min_valid_data_rate': 0.75
        })

    def test_sampling_rate_check(self):
        """测试采样率检查"""
        df_result, report = self.stage.process(self.df)

        self.assertIn('sampling', report)
        self.assertAlmostEqual(report['sampling']['actual_rate'], 60, delta=1)
        self.assertTrue(report['sampling']['rate_ok'])

    def test_blink_detection(self):
        """测试眨眼检测"""
        # 添加模拟眨眼
        self.df.loc[100:110, 'x'] = np.nan
        self.df.loc[100:110, 'y'] = np.nan

        df_result, report = self.stage.process(self.df)

        self.assertIn('blinks', report)
        self.assertGreater(report['blinks']['blink_count'], 0)
        self.assertIn('is_blink', df_result.columns)

    def test_quality_score_calculation(self):
        """测试质量评分计算"""
        df_result, report = self.stage.process(self.df)

        self.assertIn('quality_score', report)
        self.assertGreaterEqual(report['quality_score'], 0)
        self.assertLessEqual(report['quality_score'], 100)

# ... 更多测试类
```

### 7.2 集成测试

```python
# tests/test_orchestrator.py

import unittest
import pandas as pd
from pathlib import Path
from src.modules.module02_preprocessing.orchestrator import PreprocessingOrchestrator, PreprocessingMode

class TestOrchestrator(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = Path('tests/test_data')
        self.test_data_dir.mkdir(exist_ok=True)

        # 创建测试文件
        self.test_file = self.test_data_dir / 'test_subject.csv'
        df = pd.DataFrame({
            'timestamp': np.linspace(0, 10, 600),
            'x': np.random.uniform(0, 1, 600),
            'y': np.random.uniform(0, 1, 600)
        })
        df.to_csv(self.test_file, index=False)

    def test_conservative_mode_pipeline(self):
        """测试保守模式完整流程"""
        orchestrator = PreprocessingOrchestrator(mode=PreprocessingMode.CONSERVATIVE)

        result = orchestrator.process_file(
            input_path=str(self.test_file),
            output_dir=str(self.test_data_dir / 'output'),
            subject_id='test_subject'
        )

        self.assertTrue(result['success'])
        self.assertIn('output_files', result)
        self.assertIn('processed_data', result['output_files'])
        self.assertIn('events', result['output_files'])
        self.assertIn('report', result['output_files'])

    def test_legacy_mode_compatibility(self):
        """测试兼容模式"""
        orchestrator = PreprocessingOrchestrator(mode=PreprocessingMode.LEGACY)

        result = orchestrator.process_file(
            input_path=str(self.test_file),
            output_dir=str(self.test_data_dir / 'output_legacy'),
            subject_id='test_subject_legacy'
        )

        self.assertTrue(result['success'])

    def tearDown(self):
        # 清理测试文件
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
```

### 7.3 端到端测试

```python
# tests/test_api_preprocessing.py

import unittest
from flask import Flask
from src.web.app import create_app

class TestPreprocessingAPI(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_get_modes(self):
        """测试获取预处理模式API"""
        response = self.client.get('/api/m02/preprocessing/modes')
        data = response.get_json()

        self.assertTrue(data['success'])
        self.assertIn('modes', data)
        self.assertGreater(len(data['modes']), 0)

    def test_process_with_conservative_mode(self):
        """测试保守模式处理API"""
        request_data = {
            'subject_id': 'test_subject',
            'input_file': 'tests/test_data/test_subject.csv',
            'mode': 'conservative'
        }

        response = self.client.post(
            '/api/m02/preprocessing/process',
            json=request_data
        )
        data = response.get_json()

        self.assertTrue(data['success'])
        self.assertIn('output_files', data)
```

---

## 8. 部署与迁移

### 8.1 迁移步骤

```bash
# 1. 备份现有数据
python scripts/backup_preprocessing_data.py

# 2. 安装新依赖
pip install -r requirements.txt

# 3. 运行数据库迁移(如有)
python scripts/migrate_database.py

# 4. 运行测试
pytest tests/test_preprocessing/

# 5. 重启服务
# 停止现有服务
# 启动新服务
python run.py
```

### 8.2 回滚方案

```bash
# 1. 停止服务
kill <pid>

# 2. 恢复代码
git checkout <previous_commit>

# 3. 恢复数据
python scripts/restore_preprocessing_data.py <backup_date>

# 4. 重启服务
python run.py
```

### 8.3 监控指标

- **处理成功率**: successful / total
- **平均处理时间**: mean(processing_time)
- **质量评分分布**: histogram(quality_score)
- **模式使用统计**: count(mode)

---

## 9. 开发时间表

| 阶段 | 任务 | 预估时间 | 责任人 |
|------|------|----------|--------|
| Week 1 | 核心组件开发(Orchestrator, Stages) | 3天 | 开发 |
| Week 1 | 工具函数开发(Blink Detector, Velocity Calculator) | 2天 | 开发 |
| Week 2 | API接口开发 | 2天 | 开发 |
| Week 2 | 前端UI改造 | 2天 | 前端 |
| Week 2 | 单元测试编写 | 1天 | 开发 |
| Week 3 | 集成测试 | 2天 | 测试 |
| Week 3 | 验证研究(10个样本对比) | 3天 | 研究 |
| Week 4 | 文档编写 | 2天 | 开发 |
| Week 4 | 代码审查和优化 | 2天 | 团队 |
| Week 4 | 部署上线 | 1天 | 运维 |

**总计**: 约4周 (20个工作日)

---

## 10. 常见问题FAQ

### Q1: 保守模式会影响后续RQA分析吗?

**A**: 不会。保守模式输出的事件序列(注视点序列)更适合RQA分析,因为:
1. 去除了眨眼干扰
2. 保留了真实的注视-扫视模式
3. 事件序列天然是离散的,符合RQA输入要求

### Q2: 如何选择预处理模式?

**A**:
- **新研究**: 使用保守模式(推荐)
- **对比研究**: 使用兼容模式(与旧数据对比)
- **特殊需求**: 使用自定义模式

### Q3: 处理后的数据文件格式是什么?

**A**:
```
output_dir/
├── {subject_id}_processed.csv    # 处理后的原始数据(带标记列)
├── {subject_id}_events.json      # 事件序列
├── {subject_id}_report.json      # 处理报告
└── {subject_id}_quality.json     # 质量报告
```

### Q4: 如何自定义IVT参数?

**A**:
```python
custom_config = {
    'ivt': {
        'velocity_threshold': 35,  # 调整速度阈值
        'fixation_filter': {
            'min_duration': 80,  # 调整最小注视时长
            'merge_distance': 0.7
        }
    }
}

# 在API调用时传入
request_data = {
    'subject_id': 'xxx',
    'input_file': 'xxx',
    'mode': 'custom',
    'config': custom_config
}
```

### Q5: 保守模式处理速度如何?

**A**:
- 单个受试者(10分钟数据,60Hz): 约5-10秒
- 批量处理100个受试者: 约10-15分钟
- 比兼容模式略慢(+20%),但可接受

---

## 附录: 文件清单

### A. 需要新建的文件

```
new_project/src/modules/module02_preprocessing/
├── orchestrator.py
├── stages/
│   ├── __init__.py
│   ├── base_stage.py
│   ├── quality_assessment.py
│   ├── data_cleaning_conservative.py
│   ├── noise_reduction.py
│   └── ivt_detection.py
├── events/
│   ├── __init__.py
│   ├── event_detector.py
│   └── event_types.py
├── reports/
│   ├── __init__.py
│   ├── quality_report_generator.py
│   └── processing_report_generator.py
├── configs/
│   ├── __init__.py
│   ├── conservative_mode.py
│   ├── legacy_mode.py
│   └── adaptive_params.py
└── utils/
    ├── __init__.py
    ├── velocity_calculator.py
    ├── blink_detector.py
    └── quality_metrics.py
```

### B. 需要修改的文件

```
new_project/src/modules/module02_preprocessing/
├── api.py          # 新增预处理接口
├── pipeline.py     # 集成新协调器
└── __init__.py     # 导出新组件

new_project/frontend/src/components/Module02/
├── PreprocessingModeSelector.jsx  # 新增
└── DataPreprocessing.jsx          # 修改
```

---

**文档版本**: 1.0
**最后更新**: 2025-10-06
**作者**: 技术团队
**审核**: 待审核

---

*本文档为详细的技术实施指南,涵盖了从架构设计到部署上线的完整流程。如有疑问,请联系开发团队。*
