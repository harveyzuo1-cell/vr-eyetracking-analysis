"""
眼动事件分析器 - IVT算法实现

基于速度阈值的I-VT (Velocity-Threshold Identification)算法进行注视和扫视检测
"""

import math
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# IVT算法参数
IVT_VELOCITY_THRESHOLD = 40.0  # 速度阈值 (deg/s)
IVT_MIN_FIXATION_DURATION = 100  # 最小注视时长 (ms)
VELOCITY_MAX_LIMIT = 1000.0  # 速度上限 (deg/s)


class EventAnalyzer:
    """眼动事件分析器"""

    def __init__(self, velocity_threshold: float = IVT_VELOCITY_THRESHOLD,
                 min_fixation_duration: float = IVT_MIN_FIXATION_DURATION):
        """
        初始化事件分析器

        Args:
            velocity_threshold: 速度阈值 (deg/s)
            min_fixation_duration: 最小注视时长 (ms)
        """
        self.velocity_threshold = velocity_threshold
        self.min_fixation_duration = min_fixation_duration

        logger.info(f"事件分析器初始化: velocity_threshold={velocity_threshold}, "
                   f"min_fixation_duration={min_fixation_duration}")

    def compute_velocity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算眼动速度

        Args:
            df: 眼动数据DataFrame (包含x, y, milliseconds列)

        Returns:
            添加速度列的DataFrame (velocity_deg_s, x_deg, y_deg)
        """
        df = df.copy().sort_values("milliseconds").reset_index(drop=True)

        # 计算时间差
        df["time_diff"] = df["milliseconds"].diff()
        df = df[df["time_diff"] > 0].copy().reset_index(drop=True)

        if len(df) < 2:
            logger.warning("数据点太少，无法计算速度")
            return df

        # 转换为角度 (假设视角60度)
        x_deg = (df["x"] - 0.5) * 60.0
        y_deg = (df["y"] - 0.5) * 60.0
        df["x_deg"] = x_deg
        df["y_deg"] = y_deg

        # 计算速度
        velo = np.zeros(len(df))
        for i in range(1, len(df)):
            dt = df.at[i, "time_diff"]
            dx = df.at[i, "x_deg"] - df.at[i-1, "x_deg"]
            dy = df.at[i, "y_deg"] - df.at[i-1, "y_deg"]
            dist = math.sqrt(dx*dx + dy*dy)
            velo[i] = (dist / dt) * 1000.0  # 转换为 deg/s

        df["velocity_deg_s"] = velo

        # 过滤异常值
        df = df[df["velocity_deg_s"] < VELOCITY_MAX_LIMIT].copy().reset_index(drop=True)

        if len(df) < 2:
            logger.warning("速度过滤后数据点太少")
            return df

        # Z-score过滤 (去除3个标准差以外的点)
        try:
            zv = np.abs(stats.zscore(df["velocity_deg_s"], nan_policy='omit'))
            df = df[zv < 3].copy().reset_index(drop=True)
        except Exception as e:
            logger.warning(f"Z-score过滤失败: {e}")

        return df

    def ivt_segmentation(self, df: pd.DataFrame) -> Tuple[List[Tuple], List[Tuple]]:
        """
        IVT分段算法 - 基于速度阈值检测注视和扫视

        Args:
            df: 包含velocity_deg_s和milliseconds的DataFrame

        Returns:
            (fixations, saccades) 元组
            - fixations: [(start_idx, end_idx, duration_ms), ...]
            - saccades: [(start_idx, end_idx, duration_ms), ...]
        """
        if len(df) < 2:
            return [], []

        events = []
        state = "saccade"  # 初始状态
        st_i = 0  # 当前段起始索引

        for i in range(len(df)):
            v_ = df.at[i, "velocity_deg_s"]

            if v_ < self.velocity_threshold:
                # 低速 -> 注视
                if state == "saccade":
                    # 状态切换: saccade -> fixation
                    ed_i = i - 1
                    if ed_i >= st_i:
                        dur = df.at[ed_i, "milliseconds"] - df.at[st_i, "milliseconds"]
                        events.append(("saccade", st_i, ed_i, dur))
                    state = "fixation"
                    st_i = i
            else:
                # 高速 -> 扫视
                if state == "fixation":
                    # 状态切换: fixation -> saccade
                    ed_i = i - 1
                    if ed_i >= st_i:
                        dur = df.at[ed_i, "milliseconds"] - df.at[st_i, "milliseconds"]
                        if dur >= self.min_fixation_duration:
                            events.append(("fixation", st_i, ed_i, dur))
                        else:
                            # 时长不足，归类为saccade
                            events.append(("saccade", st_i, ed_i, dur))
                    state = "saccade"
                    st_i = i

        # 处理最后一段
        if st_i < len(df):
            ed_i = len(df) - 1
            dur = df.at[ed_i, "milliseconds"] - df.at[st_i, "milliseconds"]
            if state == "fixation" and dur >= self.min_fixation_duration:
                events.append(("fixation", st_i, ed_i, dur))
            else:
                events.append(("saccade", st_i, ed_i, dur))

        # 分离fixation和saccade
        fixations = [(st, ed, dur) for (etype, st, ed, dur) in events if etype == "fixation"]
        saccades = [(st, ed, dur) for (etype, st, ed, dur) in events if etype == "saccade"]

        logger.debug(f"IVT分段完成: {len(fixations)} fixations, {len(saccades)} saccades")

        return fixations, saccades

    def calc_saccade_features(self, df: pd.DataFrame, st_i: int, ed_i: int) -> Dict:
        """
        计算扫视特征

        Args:
            df: 眼动数据DataFrame
            st_i: 起始索引
            ed_i: 结束索引

        Returns:
            扫视特征字典
        """
        seg = df.iloc[st_i:ed_i+1]
        if seg.empty:
            return {
                "max_velocity": 0,
                "mean_velocity": 0,
                "amplitude": 0
            }

        max_v = seg["velocity_deg_s"].max()
        mean_v = seg["velocity_deg_s"].mean()

        # 计算幅度 (起点到终点的距离)
        x1, y1 = df.at[st_i, "x_deg"], df.at[st_i, "y_deg"]
        x2, y2 = df.at[ed_i, "x_deg"], df.at[ed_i, "y_deg"]
        amplitude = math.sqrt((x2-x1)**2 + (y2-y1)**2)

        return {
            "max_velocity": float(max_v),
            "mean_velocity": float(mean_v),
            "amplitude": float(amplitude)
        }

    def calc_fixation_features(self, df: pd.DataFrame, st_i: int, ed_i: int) -> Dict:
        """
        计算注视特征

        Args:
            df: 眼动数据DataFrame
            st_i: 起始索引
            ed_i: 结束索引

        Returns:
            注视特征字典
        """
        seg = df.iloc[st_i:ed_i+1]
        if seg.empty:
            return {
                "centroid_x": 0,
                "centroid_y": 0,
                "dispersion": 0
            }

        # 质心位置
        centroid_x = seg["x"].mean()
        centroid_y = seg["y"].mean()

        # 离散度 (标准差)
        dispersion_x = seg["x"].std()
        dispersion_y = seg["y"].std()
        dispersion = math.sqrt(dispersion_x**2 + dispersion_y**2)

        return {
            "centroid_x": float(centroid_x),
            "centroid_y": float(centroid_y),
            "dispersion": float(dispersion)
        }

    def find_roi_for_point(self, x: float, y: float, roi_regions: Dict) -> Optional[str]:
        """
        判断坐标点属于哪个ROI区域

        Args:
            x: 归一化x坐标 (0-1)
            y: 归一化y坐标 (0-1)
            roi_regions: ROI区域定义 (来自ROI配置JSON)

        Returns:
            ROI区域ID，不在任何ROI内则返回None
        """
        # 优先级: keywords > instructions > background
        for priority in ["keywords", "instructions", "background"]:
            if priority not in roi_regions:
                continue

            for region in roi_regions[priority]:
                coords = region.get("normalized_coords", [])
                if len(coords) != 4:
                    continue

                x_min, y_min, width, height = coords
                x_max = x_min + width
                y_max = y_min + height

                if x_min <= x <= x_max and y_min <= y <= y_max:
                    return region.get("id", region.get("name", "unknown"))

        return None

    def analyze_file(self, file_path: Path, roi_regions: Optional[Dict] = None) -> Dict:
        """
        分析单个眼动数据文件

        Args:
            file_path: 眼动数据文件路径
            roi_regions: ROI区域定义 (可选)

        Returns:
            分析结果字典
        """
        try:
            # 读取数据
            df = pd.read_csv(file_path)

            # 检查必要列 (兼容 timestamp 或 milliseconds)
            required_cols = ['x', 'y']
            time_col = None

            if 'milliseconds' in df.columns:
                time_col = 'milliseconds'
            elif 'timestamp' in df.columns:
                time_col = 'timestamp'
                # 将timestamp (Unix时间戳，秒) 转换为相对时间 (毫秒)
                df['milliseconds'] = (df['timestamp'] - df['timestamp'].iloc[0]) * 1000

            if time_col is None or not all(col in df.columns for col in required_cols):
                raise ValueError(f"缺少必要列: {required_cols + ['milliseconds或timestamp']}")

            # 计算速度
            df = self.compute_velocity(df)

            if len(df) < 2:
                return {
                    'success': False,
                    'error': '有效数据点不足'
                }

            # IVT分段
            fixations, saccades = self.ivt_segmentation(df)

            # 整理注视事件
            fixation_events = []
            for (st_i, ed_i, dur) in fixations:
                features = self.calc_fixation_features(df, st_i, ed_i)

                # ROI标注
                roi_label = None
                if roi_regions:
                    roi_label = self.find_roi_for_point(
                        features['centroid_x'],
                        features['centroid_y'],
                        roi_regions
                    )

                fixation_events.append({
                    'event_type': 'fixation',
                    'start_idx': int(st_i),
                    'end_idx': int(ed_i),
                    'duration_ms': float(dur),
                    'centroid_x': features['centroid_x'],
                    'centroid_y': features['centroid_y'],
                    'dispersion': features['dispersion'],
                    'roi': roi_label
                })

            # 整理扫视事件
            saccade_events = []
            for (st_i, ed_i, dur) in saccades:
                features = self.calc_saccade_features(df, st_i, ed_i)

                saccade_events.append({
                    'event_type': 'saccade',
                    'start_idx': int(st_i),
                    'end_idx': int(ed_i),
                    'duration_ms': float(dur),
                    'amplitude': features['amplitude'],
                    'max_velocity': features['max_velocity'],
                    'mean_velocity': features['mean_velocity']
                })

            return {
                'success': True,
                'file_path': str(file_path),
                'data_points': len(df),
                'fixations': fixation_events,
                'saccades': saccade_events,
                'summary': {
                    'total_fixations': len(fixations),
                    'total_saccades': len(saccades),
                    'total_fixation_duration': sum([dur for (_, _, dur) in fixations]),
                    'total_saccade_duration': sum([dur for (_, _, dur) in saccades])
                }
            }

        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
