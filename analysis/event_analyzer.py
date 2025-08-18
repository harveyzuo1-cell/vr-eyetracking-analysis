#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
眼动事件分析模块
基于用户提供的参考代码实现IVT分段算法和ROI统计
"""

import os
import math
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any
import re

###############################################################################
# ROI 定义 (基于用户提供的代码)
###############################################################################
USER_DEFINED_ROI = {
    "n2q1": {
        "keywords": [
            ("KW_n2q1_1", 0.01, 0.5886, 0.39, 0.4164),
            ("KW_n2q1_2", 0.39, 0.5886, 0.668, 0.4164),
            ("KW_n2q1_3", 0.01, 0.3494, 0.49, 0.1716),
            ("KW_n2q1_4", 0.49, 0.3494, 0.915, 0.1716),
        ],
        "instructions": [
            ("INST_n2q1_1", 0.01, 0.8250, 0.355, 0.6500)
        ],
        "background": [
            ("BG_n2q1", 0, 0, 1, 1)
        ]
    },
    "n2q2": {
        "keywords": [
            ("KW_n2q2_1", 0.01, 0.5896, 0.466, 0.4104),
            ("KW_n2q2_2", 0.466, 0.5886, 0.95, 0.4164),
            ("KW_n2q2_3", 0.01, 0.3494, 0.49, 0.1716),
            ("KW_n2q2_4", 0.49, 0.3494, 0.999, 0.1716),
        ],
        "instructions": [
            ("INST_n2q2_1", 0.01, 0.8250, 0.754, 0.6500)
        ],
        "background": [
            ("BG_n2q2", 0, 0, 1, 1)
        ]
    },
    "n2q3": {
        "keywords": [
            ("KW_n2q3_1", 0.01, 0.5688, 0.18, 0.4152),
            ("KW_n2q3_2", 0.18, 0.5688, 0.34, 0.4152),
            ("KW_n2q3_3", 0.34, 0.5688, 0.51, 0.4152),
        ],
        "instructions": [
            ("INST_n2q3_1", 0.01, 0.8373, 0.788, 0.6757),
            ("INST_n2q3_2", 0.01, 0.3050, 0.999, 0.1450),
        ],
        "background": [
            ("BG_n2q3", 0, 0, 1, 1)
        ]
    },
    "n2q4": {
        "keywords": [
            ("KW_n2q4_1", 0.42, 0.9273, 0.76, 0.5757),
        ],
        "instructions": [
            ("INST_n2q4_1", 0.01, 0.8373, 0.42, 0.6757),
            ("INST_n2q4_2a", 0.01, 0.54, 0.999, 0.38),
            ("INST_n2q4_2b", 0.01, 0.2525, 0.788, 0.0845),
        ],
        "background": [
            ("BG_n2q4", 0, 0, 1, 1)
        ]
    },
    "n2q5": {
        "keywords": [],
        "instructions": [
            ("INST_n2q5_1a", 0.01, 0.8250, 0.428, 0.6500),
            ("INST_n2q5_1b", 0.01, 0.5886, 0.523, 0.4164),
            ("INST_n2q5_1c", 0.01, 0.3494, 0.77, 0.1716)
        ],
        "background": [
            ("BG_n2q5", 0, 0, 1, 1)
        ]
    }
}

# 常量设置
TIME_CUT = {
    "n2q1": (0, 0), "n2q2": (0, 0), "n2q3": (0, 0), 
    "n2q4": (0, 0), "n2q5": (0, 0)
}

IVT_VELOCITY_THRESHOLD = 40.0
IVT_MIN_FIXATION_DURATION = 100
VELOCITY_MAX_LIMIT = 1000.0


class EventAnalyzer:
    """眼动事件分析器"""
    
    def __init__(self):
        self.roi_definitions = USER_DEFINED_ROI
        
    def map_to_n2q(self, adq_id: str) -> str:
        """将 nXqY 映射到 n2qY，以复用同一套 ROI"""
        if "q" not in adq_id:
            return adq_id
        parts = adq_id.split("q")
        if len(parts) < 2:
            return adq_id
        qnum = parts[-1]
        return f"n2q{qnum}"
    
    def normalize_roi(self, roi_list):
        """修正ROI坐标"""
        new_list = []
        for (rn, xmn, ymn, xmx, ymy) in roi_list:
            if xmn > xmx:
                xmn, xmx = xmx, xmn
            if ymn > ymy:
                ymn, ymy = ymy, ymn
            new_list.append((rn, xmn, ymn, xmx, ymy))
        return new_list
    
    def get_roi_def(self, adq_id):
        """获取ROI定义"""
        real_id = self.map_to_n2q(adq_id)
        roi_def = self.roi_definitions.get(real_id, {})
        kw = self.normalize_roi(roi_def.get("keywords", []))
        inst = self.normalize_roi(roi_def.get("instructions", []))
        bg = self.normalize_roi(roi_def.get("background", []))
        return kw, inst, bg
    
    def find_roi_label_for_point(self, x_n, y_n, roi_kw, roi_inst, roi_bg):
        """为坐标点找到ROI标签"""
        # 优先级: instructions => keywords => background
        for (rn, xmn, ymn, xmx, ymy) in roi_inst:
            if xmn <= x_n <= xmx and ymn <= y_n <= ymy:
                return rn
        for (rn, xmn, ymn, xmx, ymy) in roi_kw:
            if xmn <= x_n <= xmx and ymn <= y_n <= ymy:
                return rn
        for (rn, xmn, ymn, xmx, ymy) in roi_bg:
            if xmn <= x_n <= xmx and ymn <= y_n <= ymy:
                return rn
        return None
    
    def compute_velocity(self, df: pd.DataFrame):
        """计算速度（基于用户代码）"""
        df = df.copy().sort_values("milliseconds").reset_index(drop=True)
        df["time_diff"] = df["milliseconds"].diff()
        df = df[df["time_diff"] > 0].copy().reset_index(drop=True)
        
        if len(df) < 2:
            return df
        
        # 转换为度
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
            velo[i] = (dist / dt) * 1000.0
        
        df["velocity_deg_s"] = velo
        
        # 限速过滤
        df = df[df["velocity_deg_s"] < VELOCITY_MAX_LIMIT].copy().reset_index(drop=True)
        if len(df) < 2:
            return df
        
        # Z-score过滤
        try:
            zv = np.abs(stats.zscore(df["velocity_deg_s"], nan_policy='omit'))
            df = df[zv < 3].copy().reset_index(drop=True)
        except:
            pass  # 如果计算失败，跳过Z-score过滤
        
        return df
    
    def ivt_segmentation(self, df: pd.DataFrame):
        """IVT分段算法（基于用户代码）"""
        if len(df) < 2:
            return [], []
        
        events = []
        state = "saccade"
        st_i = 0
        
        for i in range(len(df)):
            v_ = df.at[i, "velocity_deg_s"]
            if v_ < IVT_VELOCITY_THRESHOLD:
                if state == "saccade":
                    ed_i = i - 1
                    if ed_i >= st_i:
                        dur = df.at[ed_i, "milliseconds"] - df.at[st_i, "milliseconds"]
                        events.append(("saccade", st_i, ed_i, dur))
                    state = "fixation"
                    st_i = i
            else:
                if state == "fixation":
                    ed_i = i - 1
                    if ed_i >= st_i:
                        dur = df.at[ed_i, "milliseconds"] - df.at[st_i, "milliseconds"]
                        if dur >= IVT_MIN_FIXATION_DURATION:
                            events.append(("fixation", st_i, ed_i, dur))
                        else:
                            events.append(("saccade", st_i, ed_i, dur))
                    state = "saccade"
                    st_i = i
        
        # 处理最后一段
        if st_i < len(df):
            ed_i = len(df) - 1
            dur = df.at[ed_i, "milliseconds"] - df.at[st_i, "milliseconds"]
            if state == "fixation" and dur >= IVT_MIN_FIXATION_DURATION:
                events.append(("fixation", st_i, ed_i, dur))
            else:
                events.append(("saccade", st_i, ed_i, dur))
        
        # 分离fixation和saccade
        fix_, sacc_ = [], []
        for (etype, st, ed, dur) in events:
            if etype == "fixation":
                fix_.append((st, ed, dur))
            else:
                sacc_.append((st, ed, dur))
        
        return fix_, sacc_
    
    def calc_saccade_feature(self, df, st_i, ed_i):
        """计算saccade特征"""
        seg = df.iloc[st_i:ed_i+1]
        if seg.empty:
            return 0, 0, 0
        
        mxv = seg["velocity_deg_s"].max()
        mmv = seg["velocity_deg_s"].mean()
        x1, y1 = df.at[st_i, "x_deg"], df.at[st_i, "y_deg"]
        x2, y2 = df.at[ed_i, "x_deg"], df.at[ed_i, "y_deg"]
        amp = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        return amp, mxv, mmv
    
    def calc_fixation_feature(self, df, st_i, ed_i):
        """计算fixation特征"""
        if st_i > ed_i:
            return 0
        x1, y1 = df.at[st_i, "x_deg"], df.at[st_i, "y_deg"]
        x2, y2 = df.at[ed_i, "x_deg"], df.at[ed_i, "y_deg"]
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
    def majority_roi_for_event(self, df, st_i, ed_i, roi_kw, roi_inst, roi_bg):
        """为事件找到主要ROI"""
        sub = df.iloc[st_i:ed_i+1]
        rc = {}
        for _, row in sub.iterrows():
            lb = self.find_roi_label_for_point(row["x"], row["y"], roi_kw, roi_inst, roi_bg)
            if lb:
                rc[lb] = rc.get(lb, 0) + 1
        if not rc:
            return None
        return max(rc, key=rc.get)
    
    def build_event_df(self, adq_id, df, fixs, saccs, roi_kw, roi_inst, roi_bg):
        """构建事件DataFrame"""
        rows = []
        
        # 处理fixations
        for (st, ed, dur) in fixs:
            amp = self.calc_fixation_feature(df, st, ed)
            r_ = self.majority_roi_for_event(df, st, ed, roi_kw, roi_inst, roi_bg)
            rows.append({
                "ADQ_ID": adq_id,
                "EventType": "fixation",
                "StartIndex": st,
                "EndIndex": ed,
                "Duration_ms": dur,
                "Amplitude_deg": amp,
                "MaxVel": None,
                "MeanVel": None,
                "ROI": r_
            })
        
        # 处理saccades
        for (st, ed, dur) in saccs:
            amp, mxv, mmv = self.calc_saccade_feature(df, st, ed)
            rows.append({
                "ADQ_ID": adq_id,
                "EventType": "saccade",
                "StartIndex": st,
                "EndIndex": ed,
                "Duration_ms": dur,
                "Amplitude_deg": amp,
                "MaxVel": mxv,
                "MeanVel": mmv,
                "ROI": None
            })
        
        return pd.DataFrame(rows)
    
    def sample_based_roi_stats(self, df, roi_kw, roi_inst, roi_bg, debug=False):
        """逐帧ROI统计（基于用户代码）"""
        name_set = set()
        for (rn, *_) in roi_bg:
            name_set.add(rn)
        for (rn, *_) in roi_inst:
            name_set.add(rn)
        for (rn, *_) in roi_kw:
            name_set.add(rn)
        
        stat = {}
        for nm in name_set:
            stat[nm] = {"FixTime": 0.0, "EnterCount": 0, "RegressionCount": 0}
        
        if len(df) < 1:
            return stat
        
        prev_roi = None
        for i in range(len(df)):
            dt = df.at[i, "time_diff"]
            if pd.isna(dt) or dt < 0:
                dt = 0
            lb = self.find_roi_label_for_point(df.at[i, "x"], df.at[i, "y"], roi_kw, roi_inst, roi_bg)
            if lb:
                stat[lb]["FixTime"] += dt / 1000.0
                if lb != prev_roi:
                    stat[lb]["EnterCount"] += 1
                prev_roi = lb
            else:
                prev_roi = None
        
        # 计算回归次数
        for lb, st_ in stat.items():
            c = st_["EnterCount"]
            st_["RegressionCount"] = c - 1 if c > 1 else 0
        
        if debug:
            print("[sample_based_roi_stats Debug] =>")
            for lb, st_ in stat.items():
                print(f"  ROI={lb}, FixTime={st_['FixTime']:.2f}, Enter={st_['EnterCount']}, Regress={st_['RegressionCount']}")
        
        return stat
    
    def extract_adq_id_from_filename(self, filename: str) -> str:
        """从文件名提取ADQ_ID"""
        # 匹配模式: nXXqY, mXXqY, adXXqY
        match = re.search(r'([a-z]*\d+q\d+)', filename.lower())
        if match:
            return match.group(1)
        return filename.replace('_preprocessed_calibrated.csv', '').replace('_preprocessed.csv', '')
    
    def process_single_file(self, file_path: str, debug=False):
        """处理单个数据文件"""
        try:
            # 从文件名提取ADQ_ID
            filename = os.path.basename(file_path)
            adq_id = self.extract_adq_id_from_filename(filename)
            
            if debug:
                print(f"\n=== 处理文件: {filename} (ADQ_ID: {adq_id}) ===")
            
            # 读取数据
            df = pd.read_csv(file_path)
            
            # 确保必要的列存在
            if 'milliseconds' not in df.columns:
                if 'timestamp' in df.columns:
                    df['milliseconds'] = df['timestamp'] * 1000
                else:
                    df['milliseconds'] = df.index * 16.67  # 假设60Hz
            
            if 'x' not in df.columns or 'y' not in df.columns:
                print(f"  ⚠️ 跳过: 缺少x或y列")
                return None, None
            
            # 时间裁剪
            real_id = self.map_to_n2q(adq_id)
            fc, bc = TIME_CUT.get(real_id, (0, 0))
            if fc > 0 or bc > 0:
                msmin = df["milliseconds"].min() + fc
                msmax = df["milliseconds"].max() - bc
                df = df[(df["milliseconds"] >= msmin) & (df["milliseconds"] <= msmax)].copy()
                df.reset_index(drop=True, inplace=True)
            
            if len(df) < 2:
                print(f"  ⚠️ 跳过: 数据点不足")
                return None, None
            
            # 计算速度
            df = self.compute_velocity(df)
            if len(df) < 2:
                print(f"  ⚠️ 跳过: 速度过滤后数据不足")
                return None, None
            
            # 获取ROI定义
            roi_kw, roi_inst, roi_bg = self.get_roi_def(adq_id)
            
            # IVT分段
            fixs, saccs = self.ivt_segmentation(df)
            
            # 构建事件DataFrame
            evt_df = self.build_event_df(adq_id, df, fixs, saccs, roi_kw, roi_inst, roi_bg)
            
            # ROI统计
            roi_stats = self.sample_based_roi_stats(df, roi_kw, roi_inst, roi_bg, debug=debug)
            roi_rows = []
            for lb, st_ in roi_stats.items():
                roi_rows.append({
                    "ADQ_ID": adq_id,
                    "ROI": lb,
                    "FixTime": st_["FixTime"],
                    "EnterCount": st_["EnterCount"],
                    "RegressionCount": st_["RegressionCount"]
                })
            roi_df = pd.DataFrame(roi_rows)
            
            if debug:
                print(f"  ✅ 成功: {len(evt_df)} 个事件, {len(roi_df)} 个ROI统计")
            
            return evt_df, roi_df
            
        except Exception as e:
            print(f"  ❌ 处理失败: {str(e)}")
            return None, None
    
    def analyze_group_data(self, group_type: str, debug=False):
        """分析整个组的数据"""
        print(f"\n🔍 分析 {group_type} 组数据...")
        
        # 确定数据目录
        data_dir = f"data/{group_type}_calibrated"
        if not os.path.exists(data_dir):
            print(f"  ❌ 目录不存在: {data_dir}")
            return None, None
        
        all_events = []
        all_roi_stats = []
        processed_count = 0
        
        # 遍历所有子目录
        for group_dir in os.listdir(data_dir):
            group_dir_path = os.path.join(data_dir, group_dir)
            if not os.path.isdir(group_dir_path):
                continue
            
            if debug:
                print(f"  📂 处理目录: {group_dir}")
            
            # 处理该目录下的所有CSV文件
            csv_files = [f for f in os.listdir(group_dir_path) if f.endswith('.csv')]
            for csv_file in csv_files:
                file_path = os.path.join(group_dir_path, csv_file)
                evt_df, roi_df = self.process_single_file(file_path, debug=False)
                
                if evt_df is not None and not evt_df.empty:
                    all_events.append(evt_df)
                    processed_count += 1
                
                if roi_df is not None and not roi_df.empty:
                    all_roi_stats.append(roi_df)
        
        # 合并结果
        if all_events:
            events_df = pd.concat(all_events, ignore_index=True)
        else:
            events_df = pd.DataFrame()
        
        if all_roi_stats:
            roi_stats_df = pd.concat(all_roi_stats, ignore_index=True)
        else:
            roi_stats_df = pd.DataFrame()
        
        print(f"  ✅ 完成: 处理了 {processed_count} 个文件")
        print(f"    📊 事件总数: {len(events_df)}")
        print(f"    🎯 ROI统计: {len(roi_stats_df)}")
        
        return events_df, roi_stats_df


def create_event_analyzer():
    """创建事件分析器实例"""
    return EventAnalyzer()


# 测试函数
if __name__ == "__main__":
    analyzer = create_event_analyzer()
    
    # 测试单个组
    events_df, roi_df = analyzer.analyze_group_data("control", debug=True)
    
    if events_df is not None and not events_df.empty:
        print(f"\n📊 事件分析结果预览:")
        print(events_df.head())
        
        print(f"\n🎯 ROI统计结果预览:")
        print(roi_df.head()) 