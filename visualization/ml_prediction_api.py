"""
模块9：机器学习预测API
实现基于眼动特征的MMSE子分数预测
"""

import os
import pandas as pd
import numpy as np
import joblib
from flask import Blueprint, request, jsonify
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import json
from datetime import datetime
import traceback

# 机器学习相关导入
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
    print("✅ TensorFlow已加载成功")
except ImportError as e:
    TENSORFLOW_AVAILABLE = False
    print(f"⚠️ TensorFlow不可用: {e}")
    print("💡 如需使用MLP训练功能，请安装: pip install tensorflow")

# 创建蓝图
ml_prediction_bp = Blueprint('ml_prediction', __name__)

class MLDataProcessor:
    """机器学习数据处理器"""
    
    def __init__(self):
        self.base_path = os.path.join(os.path.dirname(__file__), '..')
        self.module8_results_path = os.path.join(self.base_path, 'data', 'module8_analysis_results')
        self.mmse_data_path = os.path.join(self.base_path, 'data', 'MMSE_Score')
        self.module9_path = os.path.join(self.base_path, 'data', 'module9_ml_results')
        
        # 确保模块9目录存在
        os.makedirs(self.module9_path, exist_ok=True)
        
        # 特征方向配置
        self.feature_direction_config = None
        self.load_feature_direction_config()
        
        print("✅ ML数据处理器初始化完成")
    
    def load_feature_direction_config(self):
        """加载特征方向配置文件"""
        config_path = os.path.join(self.module9_path, 'feature_direction_config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.feature_direction_config = json.load(f)
                print("✅ 成功加载特征方向配置文件")
        else:
            print(f"⚠️ 未找到特征方向配置文件: {config_path}")
            # 返回默认配置
            self.feature_direction_config = {
                "feature_transforms": {
                    "game_duration": {"transform": "reciprocal"},
                    "KW_ROI_time": {"transform": "negate"},
                    "INST_ROI_time": {"transform": "negate"},
                    "BG_ROI_time": {"transform": "negate"},
                    "RR_1D": {"transform": "identity"},
                    "DET_1D": {"transform": "identity"},
                    "ENT_1D": {"transform": "identity"},
                    "RR_2D": {"transform": "identity"},
                    "DET_2D": {"transform": "identity"},
                    "ENT_2D": {"transform": "identity"}
                }
            }
    
    def apply_feature_transform(self, series, transform_method, epsilon=1e-6, outlier_percentile=(1, 99)):
        """
        应用特征变换，统一方向为"数值越高=认知越好"
        
        Args:
            series: pandas Series，特征数据
            transform_method: str，变换方法 ('negate', 'reciprocal', 'identity')
            epsilon: float，避免除零的小常数
            outlier_percentile: tuple，异常值截断的分位数范围 (下界, 上界)
        
        Returns:
            pandas Series，变换后的特征数据
        """
        if transform_method == "negate":
            return -series
        elif transform_method == "reciprocal":
            # 专家建议：在倒数变换前进行异常值截断，防止极端值
            if outlier_percentile:
                lower_bound = series.quantile(outlier_percentile[0] / 100.0)
                upper_bound = series.quantile(outlier_percentile[1] / 100.0)
                clipped_series = series.clip(lower=lower_bound, upper=upper_bound)
            else:
                clipped_series = series
            
            # 使用倒数变换，添加小常数避免除零
            return 1.0 / (clipped_series + epsilon)
        elif transform_method == "identity":
            return series
        else:
            print(f"⚠️ 未知的变换方法: {transform_method}，使用identity")
            return series
    
    def validate_feature_directions(self, df, feature_cols, mmse_cols):
        """
        验证特征方向一致性 - 所有特征与MMSE总分应正相关
        
        Args:
            df: DataFrame，包含特征和MMSE数据
            feature_cols: list，特征列名
            mmse_cols: list，MMSE子分数列名
        
        Returns:
            dict，验证结果
        """
        # 计算MMSE总分
        mmse_total = df[mmse_cols].sum(axis=1)
        
        # 计算每个特征与MMSE总分的相关性
        correlations = {}
        negative_features = []
        
        for col in feature_cols:
            if col in df.columns:
                corr = df[col].corr(mmse_total)
                correlations[col] = corr
                if corr < 0:
                    negative_features.append(col)
        
        validation_result = {
            'correlations': correlations,
            'negative_features': negative_features,
            'all_positive': len(negative_features) == 0,
            'mmse_total_stats': {
                'mean': float(mmse_total.mean()),
                'std': float(mmse_total.std()),
                'min': float(mmse_total.min()),
                'max': float(mmse_total.max())
            }
        }
        
        return validation_result
    
    def get_available_rqa_configs(self):
        """获取可用的RQA配置列表"""
        try:
            if not os.path.exists(self.module8_results_path):
                return []
            
            configs = []
            for config_dir in os.listdir(self.module8_results_path):
                config_path = os.path.join(self.module8_results_path, config_dir)
                if os.path.isdir(config_path):
                    # 检查是否有个人对比文件
                    individual_files = [f for f in os.listdir(config_path) 
                                      if f.startswith('individual_comparison_')]
                    if individual_files:
                        configs.append({
                            'id': config_dir,
                            'display_name': self._format_config_display_name(config_dir),
                            'file_count': len(individual_files)
                        })
            
            return sorted(configs, key=lambda x: x['id'])
            
        except Exception as e:
            print(f"❌ 获取RQA配置失败: {str(e)}")
            return []
    
    def _format_config_display_name(self, config_id):
        """格式化配置显示名称"""
        try:
            # 解析类似 m2_tau1_eps0.055_lmin2 的格式
            parts = config_id.split('_')
            display_parts = []
            
            for part in parts:
                if part.startswith('m'):
                    display_parts.append(f"m={part[1:]}")
                elif part.startswith('tau'):
                    display_parts.append(f"τ={part[3:]}")
                elif part.startswith('eps'):
                    display_parts.append(f"ε={part[3:]}")
                elif part.startswith('lmin'):
                    display_parts.append(f"l_min={part[4:]}")
            
            return ", ".join(display_parts)
        except:
            return config_id
    
    def load_eye_movement_data(self, rqa_config):
        """加载模块8的眼动特征数据"""
        try:
            config_path = os.path.join(self.module8_results_path, rqa_config)
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"RQA配置目录不存在: {rqa_config}")
            
            # 查找最新的individual_comparison文件
            individual_files = [f for f in os.listdir(config_path) 
                              if f.startswith('individual_comparison_')]
            
            if not individual_files:
                raise FileNotFoundError(f"未找到个人对比数据文件")
            
            # 选择最新的文件
            latest_file = sorted(individual_files)[-1]
            file_path = os.path.join(config_path, latest_file)
            
            print(f"📂 加载眼动数据文件: {latest_file}")
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 检查必要的列
            required_columns = ['Subject_ID', 'Task_ID', 'Group_Type', 'Eye_Movement_Coefficient']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"缺少必要的列: {missing_columns}")
            
            print(f"✅ 成功加载眼动数据: {len(df)} 条记录")
            print(f"📊 数据列: {list(df.columns)}")
            
            return df, latest_file
            
        except Exception as e:
            print(f"❌ 加载眼动数据失败: {str(e)}")
            raise e
    
    def load_mmse_data(self):
        """加载MMSE子分数数据"""
        try:
            mmse_files = {
                'control': '控制组.csv',
                'mci': '轻度认知障碍组.csv', 
                'ad': '阿尔兹海默症组.csv'
            }
            
            all_mmse_data = []
            
            for group_type, filename in mmse_files.items():
                file_path = os.path.join(self.mmse_data_path, filename)
                
                if not os.path.exists(file_path):
                    print(f"⚠️ MMSE文件不存在: {filename}")
                    continue
                
                df = pd.read_csv(file_path)
                print(f"📂 加载MMSE数据: {filename}, 记录数: {len(df)}")
                
                # 添加组别标识(保持与眼动数据一致的小写格式)
                df['Group_Type'] = group_type.lower()
                
                # 处理受试者ID列（可能是'试者'或'受试者'）
                subject_col = None
                for col in ['试者', '受试者', 'Subject_ID']:
                    if col in df.columns:
                        subject_col = col
                        break
                
                if subject_col:
                    df['Subject_ID'] = df[subject_col]
                else:
                    raise ValueError(f"在{filename}中未找到受试者ID列")
                
                all_mmse_data.append(df)
            
            if not all_mmse_data:
                raise FileNotFoundError("未找到任何MMSE数据文件")
            
            # 合并所有组的数据
            combined_mmse = pd.concat(all_mmse_data, ignore_index=True)
            
            print(f"✅ 成功加载MMSE数据: {len(combined_mmse)} 条记录")
            print(f"📊 数据列: {list(combined_mmse.columns)}")
            
            return combined_mmse
            
        except Exception as e:
            print(f"❌ 加载MMSE数据失败: {str(e)}")
            raise e
    
    def extract_mmse_subscores(self, mmse_df):
        """提取MMSE五个子分数"""
        try:
            # 定义MMSE子分数的列映射和权重
            subscore_mapping = {
                'Q1': {  # 时间定向 (5分总计)
                    '年份': 1, '季节': 1, '月份': 1, '星期': 2
                },
                'Q2': {  # 空间定向 (5分总计) 
                    '省市区': 2, '街道': 1, '建筑': 1, '楼层': 1
                },
                'Q3': {  # 即刻记忆 (3分)
                    '即刻记忆': 3
                },
                'Q4': {  # 注意力与计算 (5分)
                    '100-7': 1, '93-7': 1, '86-7': 1, '79-7': 1, '72-7': 1
                },
                'Q5': {  # 延迟回忆 (3分)
                    '词1': 1, '词2': 1, '词3': 1
                }
            }
            
            # 为每个受试者计算子分数
            processed_data = []
            
            for _, row in mmse_df.iterrows():
                subject_data = {
                    'Subject_ID': row['Subject_ID'],
                    'Group_Type': row['Group_Type']
                }
                
                # 计算每个子分数(按权重)
                for task_id, column_weights in subscore_mapping.items():
                    subscore = 0
                    for col, weight in column_weights.items():
                        if col in mmse_df.columns:
                            subscore += row.get(col, 0) * weight
                    subject_data[f'{task_id}_subscore'] = subscore
                
                processed_data.append(subject_data)
            
            result_df = pd.DataFrame(processed_data)
            
            print(f"✅ 成功提取MMSE子分数")
            print(f"📊 子分数列: {[col for col in result_df.columns if 'subscore' in col]}")
            print(f"📋 MMSE Subject_ID 示例: {result_df['Subject_ID'].head().tolist()}")
            
            return result_df
            
        except Exception as e:
            print(f"❌ 提取MMSE子分数失败: {str(e)}")
            raise e
    
    def create_subject_aggregated_features(self, eye_movement_df):
        """创建受试者级别的聚合眼动特征（支持缺失任务容错）"""
        try:
            # 专家建议：增强缺失任务容错处理
            expected_tasks = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
            
            # 检测缺失任务
            missing_task_info = []
            for subject_id in eye_movement_df['Subject_ID'].unique():
                subject_data = eye_movement_df[eye_movement_df['Subject_ID'] == subject_id]
                actual_tasks = set(subject_data['Task_ID'].unique())
                missing_tasks = set(expected_tasks) - actual_tasks
                
                if missing_tasks:
                    missing_task_info.append({
                        'Subject_ID': subject_id,
                        'missing_tasks': list(missing_tasks),
                        'missing_count': len(missing_tasks)
                    })
            
            if missing_task_info:
                print(f"⚠️ 发现 {len(missing_task_info)} 个受试者有缺失任务:")
                for info in missing_task_info[:5]:  # 只显示前5个
                    print(f"  {info['Subject_ID']}: 缺失 {info['missing_tasks']}")
                if len(missing_task_info) > 5:
                    print(f"  ... 还有 {len(missing_task_info) - 5} 个")
            
            # 按受试者聚合特征（仅使用现有任务）
            subject_features = eye_movement_df.groupby(['Subject_ID', 'Group_Type']).agg({
                'Eye_Movement_Coefficient': ['mean', 'std', 'min', 'max']
            }).reset_index()
            
            # 展平列名
            subject_features.columns = ['Subject_ID', 'Group_Type', 
                                      'eye_coeff_mean', 'eye_coeff_std', 
                                      'eye_coeff_min', 'eye_coeff_max']
            
            # 填充NaN值（如果只有一个任务的话，std会是NaN）
            subject_features['eye_coeff_std'] = subject_features['eye_coeff_std'].fillna(0)
            
            # 添加任务计数特征
            task_counts = eye_movement_df.groupby('Subject_ID')['Task_ID'].nunique().reset_index()
            task_counts.columns = ['Subject_ID', 'task_count']
            
            subject_features = subject_features.merge(task_counts, on='Subject_ID')
            
            # 专家建议：添加缺失任务标志特征
            missing_task_flags = pd.DataFrame(missing_task_info) if missing_task_info else pd.DataFrame(columns=['Subject_ID', 'missing_count'])
            if not missing_task_flags.empty:
                missing_task_flags = missing_task_flags[['Subject_ID', 'missing_count']]
            else:
                # 为所有受试者创建缺失计数为0的记录
                missing_task_flags = pd.DataFrame({
                    'Subject_ID': subject_features['Subject_ID'],
                    'missing_count': 0
                })
            
            subject_features = subject_features.merge(missing_task_flags, on='Subject_ID', how='left')
            subject_features['missing_count'] = subject_features['missing_count'].fillna(0)
            
            # 添加缺失任务标志（二进制特征）
            subject_features['flag_missing_task'] = (subject_features['missing_count'] > 0).astype(int)
            
            # 计算更多聚合特征
            task_features = eye_movement_df.pivot_table(
                index=['Subject_ID', 'Group_Type'], 
                columns='Task_ID', 
                values='Eye_Movement_Coefficient',
                fill_value=0  # 缺失任务用0填充
            ).reset_index()
            
            # 重命名任务特征列
            task_feature_cols = {}
            for col in task_features.columns:
                if col not in ['Subject_ID', 'Group_Type']:
                    task_feature_cols[col] = f'eye_coeff_{col.lower()}'
            
            task_features = task_features.rename(columns=task_feature_cols)
            
            # 合并所有特征
            final_features = subject_features.merge(task_features, on=['Subject_ID', 'Group_Type'])
            
            print(f"✅ 成功创建受试者聚合特征")
            print(f"📊 特征数量: {len(final_features.columns) - 2}")  # 减去ID和Group列
            print(f"👥 受试者数量: {len(final_features)}")
            print(f"📋 眼动数据 Subject_ID 示例: {final_features['Subject_ID'].head().tolist()}")
            
            # 详细的受试者分布统计
            group_distribution = final_features['Group_Type'].value_counts()
            print(f"📊 受试者组别分布:")
            for group, count in group_distribution.items():
                print(f"  {group}: {count} 受试者")
            
            # 缺失任务统计
            if missing_task_info:
                print(f"⚠️ 缺失任务统计:")
                print(f"  有缺失任务的受试者: {len(missing_task_info)}")
                print(f"  完整任务的受试者: {len(final_features) - len(missing_task_info)}")
                missing_counts = final_features['missing_count'].value_counts().sort_index()
                for count, num_subjects in missing_counts.items():
                    if count > 0:
                        print(f"  缺失{count}个任务: {num_subjects}名受试者")
                        
            # 检查是否有重复数据导致的样本减少
            print(f"⚠️ 数据聚合说明: 原始眼动数据按Subject_ID聚合为受试者级别特征")
            print(f"   每个受试者可能有多个任务记录，聚合后变为1个受试者1条记录")
            print(f"   缺失任务通过0填充和标志变量进行处理")
            
            return final_features
            
        except Exception as e:
            print(f"❌ 创建聚合特征失败: {str(e)}")
            raise e
    
    def convert_eye_movement_id_to_mmse_id(self, subject_id, group_type):
        """将眼动数据的Subject_ID转换为MMSE数据格式"""
        try:
            # 去掉可能的'q'后缀
            base_id = subject_id
            if base_id.endswith('q'):
                base_id = base_id[:-1]
            
            if group_type.lower() == 'control':
                # n1 -> n01, n2 -> n02, ..., n20 -> n20
                if base_id.startswith('n'):
                    num = int(base_id[1:])
                    if 1 <= num <= 20:
                        return f"n{num:02d}"
                    else:
                        print(f"⚠️ Control组ID超出范围: {subject_id} (期望1-20)")
                        return None
            elif group_type.lower() == 'mci':
                # m1 -> M01, m2 -> M02, ..., m20 -> M20 (注意大写M)
                if base_id.startswith('m'):
                    num = int(base_id[1:])
                    if 1 <= num <= 20:
                        return f"M{num:02d}"
                    else:
                        print(f"⚠️ MCI组ID超出范围: {subject_id} (期望1-20)")
                        return None
            elif group_type.lower() == 'ad':
                # ad3 -> ad01, ad4 -> ad02, ..., ad22 -> ad20 (眼动数据从3开始到22，MMSE从1开始到20，offset=-2)
                if base_id.startswith('ad'):
                    num = int(base_id[2:])
                    if 3 <= num <= 22:
                        mmse_num = num - 2  # ad3->ad01, ad4->ad02, ..., ad22->ad20
                        return f"ad{mmse_num:02d}"
                    else:
                        print(f"⚠️ AD组ID超出范围: {subject_id} (期望3-22)")
                        return None
            
            print(f"⚠️ 无法识别的ID格式: {subject_id} ({group_type})")
            return None
        except Exception as e:
            print(f"⚠️ ID转换失败: {subject_id} -> {str(e)}")
            return None
    
    def merge_eye_movement_and_mmse(self, eye_features_df, mmse_subscores_df):
        """合并眼动特征和MMSE子分数"""
        try:
            # 转换眼动数据的Subject_ID格式以匹配MMSE数据
            eye_features_df_copy = eye_features_df.copy()
            eye_features_df_copy['MMSE_Subject_ID'] = eye_features_df_copy.apply(
                lambda row: self.convert_eye_movement_id_to_mmse_id(row['Subject_ID'], row['Group_Type']), 
                axis=1
            )
            
            print(f"📋 ID转换示例:")
            for i in range(min(10, len(eye_features_df_copy))):
                row = eye_features_df_copy.iloc[i]
                print(f"  {row['Subject_ID']} ({row['Group_Type']}) -> {row['MMSE_Subject_ID']}")
            
            # 过滤掉转换失败的记录（MMSE_Subject_ID为None）
            valid_conversions = eye_features_df_copy['MMSE_Subject_ID'].notna()
            eye_features_valid = eye_features_df_copy[valid_conversions]
            
            print(f"📊 转换统计:")
            print(f"  总眼动记录: {len(eye_features_df_copy)}")
            print(f"  成功转换: {len(eye_features_valid)}")
            print(f"  转换失败: {len(eye_features_df_copy) - len(eye_features_valid)}")
            
            if len(eye_features_valid) == 0:
                print("❌ 没有任何眼动数据ID能够转换为MMSE格式")
                return pd.DataFrame()
            
            # 显示待合并的数据样本
            print(f"📋 待合并的眼动数据样本 (MMSE_Subject_ID):")
            sample_eye_ids = eye_features_valid['MMSE_Subject_ID'].unique()[:10]
            for group in ['control', 'mci', 'ad']:
                group_sample = eye_features_valid[eye_features_valid['Group_Type'] == group]['MMSE_Subject_ID'].unique()[:5]
                print(f"  {group}: {list(group_sample)}")
            
            print(f"📋 MMSE数据样本 (Subject_ID):")
            for group in ['control', 'mci', 'ad']:
                group_sample = mmse_subscores_df[mmse_subscores_df['Group_Type'] == group]['Subject_ID'].unique()[:5]
                print(f"  {group}: {list(group_sample)}")
            
            # 基于转换后的Subject_ID和Group_Type合并数据
            merged_df = eye_features_valid.merge(
                mmse_subscores_df, 
                left_on=['MMSE_Subject_ID', 'Group_Type'],
                right_on=['Subject_ID', 'Group_Type'],
                how='inner'
            )
            
            # 保留原始的Subject_ID（眼动数据格式）
            if len(merged_df) > 0:
                merged_df['Subject_ID'] = merged_df['Subject_ID_x']
                merged_df = merged_df.drop(['Subject_ID_x', 'Subject_ID_y', 'MMSE_Subject_ID'], axis=1)
            
            print(f"✅ 成功合并眼动特征和MMSE数据")
            print(f"👥 合并后受试者数量: {len(merged_df)}")
            print(f"📊 总列数: {len(merged_df.columns)}")
            
            # 验证数据完整性
            missing_data = merged_df.isnull().sum()
            if missing_data.any():
                print("⚠️ 发现缺失数据:")
                for col, count in missing_data[missing_data > 0].items():
                    print(f"  {col}: {count} 缺失值")
            
            return merged_df
            
        except Exception as e:
            print(f"❌ 合并数据失败: {str(e)}")
            raise e
    
    def prepare_ml_dataset(self, merged_df):
        """准备机器学习数据集"""
        try:
            # 分离特征和目标变量
            feature_columns = [col for col in merged_df.columns 
                             if col not in ['Subject_ID', 'Group_Type'] 
                             and not col.endswith('_subscore')]
            
            target_columns = [col for col in merged_df.columns if col.endswith('_subscore')]
            
            print(f"📊 特征列 ({len(feature_columns)}): {feature_columns}")
            print(f"🎯 目标列 ({len(target_columns)}): {target_columns}")
            
            # 提取特征和目标
            X = merged_df[feature_columns].copy()
            y = merged_df[target_columns].copy()
            
            # 检查并处理无限值和缺失值
            X = X.replace([np.inf, -np.inf], np.nan)
            X = X.fillna(X.mean())
            
            y = y.replace([np.inf, -np.inf], np.nan)
            y = y.fillna(y.mean())
            
            # 应用特征方向一致性校正
            print(f"🔄 开始特征方向一致性校正...")
            X_transformed = X.copy()
            
            if self.feature_direction_config and 'feature_transforms' in self.feature_direction_config:
                transforms = self.feature_direction_config['feature_transforms']
                applied_transforms = []
                
                for feature_col in feature_columns:
                    if feature_col in transforms:
                        transform_method = transforms[feature_col]['transform']
                        original_values = X_transformed[feature_col].copy()
                        
                        # 应用变换
                        X_transformed[feature_col] = self.apply_feature_transform(
                            X_transformed[feature_col], transform_method
                        )
                        
                        # 记录变换信息
                        applied_transforms.append({
                            'feature': feature_col,
                            'method': transform_method,
                            'original_mean': float(original_values.mean()),
                            'transformed_mean': float(X_transformed[feature_col].mean()),
                            'original_std': float(original_values.std()),
                            'transformed_std': float(X_transformed[feature_col].std())
                        })
                        
                        print(f"  ✅ {feature_col}: {transform_method} 变换")
                    else:
                        print(f"  ⚠️ {feature_col}: 未配置变换方法，使用identity")
                
                print(f"✅ 特征方向校正完成，共处理 {len(applied_transforms)} 个特征")
            else:
                print(f"⚠️ 未加载特征方向配置，跳过方向校正")
                applied_transforms = []
            
            # 标准化特征 (使用变换后的特征)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_transformed)
            X_scaled_df = pd.DataFrame(X_scaled, columns=feature_columns, index=X.index)
            
            print(f"✅ 特征标准化完成")
            print(f"📈 特征范围: {X_scaled.min():.3f} 到 {X_scaled.max():.3f}")
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled_df, y, 
                test_size=0.2, 
                random_state=42,
                stratify=merged_df['Group_Type']  # 按组别分层抽样
            )
            
            # 专家建议：只用训练集做方向验证（避免测试集信息泄漏）
            validation_result = None
            if self.feature_direction_config and 'feature_transforms' in self.feature_direction_config:
                # 在训练集上验证特征方向一致性
                print(f"🔍 特征方向验证（仅基于训练集）:")
                validation_result = self.validate_feature_directions(
                    pd.concat([X_train, y_train], axis=1), 
                    feature_columns, 
                    [col for col in y_train.columns]
                )
                
                if validation_result['all_positive']:
                    print(f"  ✅ 所有特征与MMSE总分正相关")
                else:
                    print(f"  ⚠️ 发现负相关特征: {validation_result['negative_features']}")
                
                # 显示相关性信息
                for feature, corr in validation_result['correlations'].items():
                    status = "✅" if corr >= 0 else "❌"
                    print(f"    {status} {feature}: {corr:.3f}")
            else:
                validation_result = None
            
            print(f"✅ 数据集划分完成")
            print(f"🚂 训练集: {len(X_train)} 样本")
            print(f"🧪 测试集: {len(X_test)} 样本")
            
            # 详细的特征和目标信息
            print(f"🔍 特征标准化情况:")
            print(f"  特征数量: {len(feature_columns)}")
            print(f"  标准化方法: Z-score (StandardScaler)")
            print(f"  标准化后特征范围: [{X_scaled.min():.3f}, {X_scaled.max():.3f}]")
            
            print(f"🎯 MMSE子分数详情:")
            max_scores = {'Q1_subscore': 5, 'Q2_subscore': 5, 'Q3_subscore': 3, 'Q4_subscore': 5, 'Q5_subscore': 3}
            for i, col in enumerate(target_columns, 1):
                subscore_info = {
                    'Q1_subscore': '时间定向(Q1) [年份1+季节1+月份1+星期2=5分]',
                    'Q2_subscore': '空间定向(Q2) [省市区2+街道1+建筑1+楼层1=5分]', 
                    'Q3_subscore': '即时记忆(Q3) [即刻记忆3分]',
                    'Q4_subscore': '注意/计算(Q4) [连续减法5×1=5分]',
                    'Q5_subscore': '延迟回忆(Q5) [词汇回忆3×1=3分]'
                }.get(col, col)
                max_score = max_scores.get(col, '?')
                print(f"  {subscore_info}")
                print(f"    实际: 均值={y[col].mean():.2f}, 标准差={y[col].std():.2f}, 范围=[{y[col].min():.0f}, {y[col].max():.0f}], 满分={max_score}")
            
            # 计算数据集统计信息
            dataset_stats = {
                'total_samples': len(merged_df),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': len(feature_columns),
                'target_count': len(target_columns),
                'group_distribution': merged_df['Group_Type'].value_counts().to_dict(),
                'feature_names': feature_columns,
                'target_names': target_columns,
                'target_stats': {
                    col: {
                        'mean': float(y[col].mean()),
                        'std': float(y[col].std()),
                        'min': float(y[col].min()),
                        'max': float(y[col].max())
                    } for col in target_columns
                }
            }
            
            return {
                'X_train': X_train,
                'X_test': X_test,
                'y_train': y_train,
                'y_test': y_test,
                'scaler': scaler,
                'merged_data': merged_df,
                'stats': dataset_stats,
                'applied_transforms': applied_transforms if 'applied_transforms' in locals() else [],
                'validation_result': validation_result if 'validation_result' in locals() else None
            }
            
        except Exception as e:
            print(f"❌ 准备ML数据集失败: {str(e)}")
            raise e
    
    def save_preprocessed_data(self, dataset, rqa_config):
        """保存预处理后的数据"""
        try:
            # 创建配置专用目录
            config_dir = os.path.join(self.module9_path, rqa_config)
            os.makedirs(config_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存训练集和测试集
            train_data = pd.concat([dataset['X_train'], dataset['y_train']], axis=1)
            test_data = pd.concat([dataset['X_test'], dataset['y_test']], axis=1)
            
            train_file = os.path.join(config_dir, f'train_dataset_{timestamp}.csv')
            test_file = os.path.join(config_dir, f'test_dataset_{timestamp}.csv')
            merged_file = os.path.join(config_dir, f'merged_dataset_{timestamp}.csv')
            stats_file = os.path.join(config_dir, f'dataset_stats_{timestamp}.json')
            
            train_data.to_csv(train_file, index=False)
            test_data.to_csv(test_file, index=False)
            dataset['merged_data'].to_csv(merged_file, index=False)
            
            # 保存增强的统计信息
            stats_data = dataset['stats'].copy()
            
            # 添加特征变换和验证信息
            if 'applied_transforms' in dataset and dataset['applied_transforms']:
                stats_data['feature_transforms'] = dataset['applied_transforms']
            
            if 'validation_result' in dataset and dataset['validation_result']:
                stats_data['direction_validation'] = dataset['validation_result']
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
            
            # 保存StandardScaler
            scaler_file = os.path.join(config_dir, f'scaler_{timestamp}.pkl')
            joblib.dump(dataset['scaler'], scaler_file)
            
            # 保存特征方向配置文件副本
            config_copy_file = os.path.join(config_dir, f'feature_direction_config_{timestamp}.json')
            if self.feature_direction_config:
                with open(config_copy_file, 'w', encoding='utf-8') as f:
                    json.dump(self.feature_direction_config, f, indent=2, ensure_ascii=False)
            
            # 创建最新文件的副本（用于训练）
            latest_scaler = os.path.join(config_dir, 'latest_scaler.pkl')
            latest_config = os.path.join(config_dir, 'latest_feature_config.json')
            
            try:
                # 删除旧的文件
                if os.path.exists(latest_scaler):
                    os.remove(latest_scaler)
                if os.path.exists(latest_config):
                    os.remove(latest_config)
                
                # 复制最新文件
                import shutil
                shutil.copy2(scaler_file, latest_scaler)
                if self.feature_direction_config:
                    shutil.copy2(config_copy_file, latest_config)
                
            except Exception as e:
                print(f"⚠️ 创建最新文件副本失败: {e}")
            
            print(f"💾 数据保存完成:")
            print(f"  训练集: {train_file}")
            print(f"  测试集: {test_file}")
            print(f"  合并数据: {merged_file}")
            print(f"  统计信息: {stats_file}")
            print(f"  标准化器: {scaler_file}")
            print(f"  特征配置: {config_copy_file}")
            
            return {
                'train_file': train_file,
                'test_file': test_file,
                'merged_file': merged_file,
                'stats_file': stats_file,
                'scaler_file': scaler_file,
                'config_file': config_copy_file,
                'latest_scaler': latest_scaler,
                'latest_config': latest_config
            }
            
        except Exception as e:
            print(f"❌ 保存预处理数据失败: {str(e)}")
            raise e

# 创建全局处理器实例
ml_processor = MLDataProcessor()

@ml_prediction_bp.route('/api/ml/available-configs', methods=['GET'])
def get_available_configs():
    """获取可用的RQA配置"""
    try:
        configs = ml_processor.get_available_rqa_configs()
        return jsonify({
            'success': True,
            'configs': configs,
            'count': len(configs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ml_prediction_bp.route('/api/ml/preprocess-data', methods=['POST'])
def preprocess_data():
    """执行数据预处理（子模块9.1）"""
    try:
        data = request.get_json()
        rqa_config = data.get('rqa_config')
        enable_direction_correction = data.get('enable_direction_correction', True)  # 默认启用
        
        if not rqa_config:
            return jsonify({
                'success': False,
                'error': '请提供RQA配置参数'
            }), 400
        
        print(f"🚀 开始执行模块9.1数据预处理，RQA配置: {rqa_config}")
        
        # 步骤1: 加载眼动数据
        print("📂 步骤1: 加载眼动数据")
        eye_movement_df, eye_file = ml_processor.load_eye_movement_data(rqa_config)
        
        # 步骤2: 加载MMSE数据
        print("📂 步骤2: 加载MMSE数据")
        mmse_df = ml_processor.load_mmse_data()
        
        # 步骤3: 提取MMSE子分数
        print("🔢 步骤3: 提取MMSE子分数")
        mmse_subscores_df = ml_processor.extract_mmse_subscores(mmse_df)
        
        # 步骤4: 创建受试者级别的眼动特征
        print("🧮 步骤4: 创建受试者级别眼动特征")
        eye_features_df = ml_processor.create_subject_aggregated_features(eye_movement_df)
        
        # 步骤5: 合并眼动特征和MMSE数据
        print("🔗 步骤5: 合并眼动特征和MMSE数据")
        merged_df = ml_processor.merge_eye_movement_and_mmse(eye_features_df, mmse_subscores_df)
        
        # 步骤6: 准备机器学习数据集
        print("⚙️ 步骤6: 准备机器学习数据集")
        dataset = ml_processor.prepare_ml_dataset(merged_df)
        
        # 步骤7: 保存预处理后的数据
        print("💾 步骤7: 保存预处理数据")
        saved_files = ml_processor.save_preprocessed_data(dataset, rqa_config)
        
        print(f"✅ 模块9.1数据预处理完成！")
        
        return jsonify({
            'success': True,
            'message': '数据预处理完成',
            'stats': dataset['stats'],
            'files': saved_files,
            'source_file': eye_file
        })
        
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        print(f"❌ 数据预处理失败: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

class CVMLPTrainer:
    """5-fold交叉验证MLP模型训练器（专家优化版 + 标签归一化）"""
    
    def __init__(self, config_name):
        self.config_name = config_name
        self.model_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'module9_ml_results', config_name)
        os.makedirs(self.model_dir, exist_ok=True)
        
        # CV专用目录
        self.cv_models_dir = os.path.join(self.model_dir, 'cv_models')
        self.cv_histories_dir = os.path.join(self.model_dir, 'cv_histories')
        os.makedirs(self.cv_models_dir, exist_ok=True)
        os.makedirs(self.cv_histories_dir, exist_ok=True)
        
        # 专家建议的优化参数
        self.cv_params = {
            'n_splits': 5,
            'shuffle': True,
            'random_state': 42,
            'epochs': 200,
            'batch_size': 8,
            'patience': 10,
            'dropout': 0.35,  # 专家建议
            'l2_reg': 1e-3,   # 专家建议
            'hidden_layers': [32],  # 简单结构避免过拟合
            'activation': 'relu',
            'optimizer': 'adam',
            'loss': 'mse',
            'metrics': ['mae']
        }
        
        # 标签归一化：MMSE子分数满分向量 [Q1, Q2, Q3, Q4, Q5]
        self.MAX_SCORES = np.array([5, 5, 3, 5, 3], dtype=np.float32)
        print(f"🎯 标签归一化启用：MAX_SCORES = {self.MAX_SCORES}")
    
    def build_model(self, input_dim=10, output_dim=5):
        """构建单个CV折叠的模型"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow不可用，无法创建MLP模型")
        
        l2_reg = keras.regularizers.l2(self.cv_params['l2_reg'])
        
        model = keras.Sequential([
            layers.Dense(
                self.cv_params['hidden_layers'][0], 
                activation=self.cv_params['activation'],
                input_shape=(input_dim,),
                kernel_regularizer=l2_reg,
                kernel_initializer='he_normal',
                name='hidden_1'
            ),
            layers.Dropout(self.cv_params['dropout'], name='dropout_1'),
            layers.Dense(output_dim, activation='linear', name='output')
        ])
        
        model.compile(
            optimizer=self.cv_params['optimizer'],
            loss=self.cv_params['loss'],
            metrics=self.cv_params['metrics']
        )
        
        return model
    
    def train_cv_models(self, X_train, y_train_raw, X_test, y_test_raw):
        """执行5-fold交叉验证训练"""
        try:
            print(f"🚀 开始5-fold交叉验证训练（标签归一化优化版）")
            print(f"📊 训练样本: {len(X_train)}, 测试样本: {len(X_test)}")
            print(f"🎯 原始标签范围: y_train ∈ [{y_train_raw.min():.1f}, {y_train_raw.max():.1f}]")
            
            # 标签归一化: y ∈ [0,1]
            y_train = y_train_raw / self.MAX_SCORES
            y_test = y_test_raw / self.MAX_SCORES
            print(f"✅ 标签归一化完成: y_norm ∈ [{y_train.min():.3f}, {y_train.max():.3f}]")
            
            # 导入sklearn
            from sklearn.model_selection import KFold
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            
            # 初始化
            kf = KFold(
                n_splits=self.cv_params['n_splits'],
                shuffle=self.cv_params['shuffle'],
                random_state=self.cv_params['random_state']
            )
            
            fold_predictions = []
            fold_metrics = []
            fold_histories = []
            
            # 5-fold训练循环
            for fold, (train_idx, val_idx) in enumerate(kf.split(X_train)):
                print(f"\n📂 训练 Fold {fold + 1}/{self.cv_params['n_splits']}")
                
                # 划分当前折叠的训练/验证集
                X_fold_train, X_fold_val = X_train[train_idx], X_train[val_idx]
                y_fold_train, y_fold_val = y_train[train_idx], y_train[val_idx]
                
                print(f"  训练样本: {len(X_fold_train)}, 验证样本: {len(X_fold_val)}")
                
                # 构建模型 - 动态获取输入维度（专家建议：10个核心特征）
                input_dim = X_fold_train.shape[1]
                output_dim = y_fold_train.shape[1]
                print(f"  🔧 模型维度: 输入={input_dim}特征, 输出={output_dim}子分数")
                if input_dim == 10:
                    print(f"  ✅ 特征维度符合专家建议 (10个核心眼动特征)")
                else:
                    print(f"  ⚠️ 特征维度异常: 期望10个，实际{input_dim}个")
                model = self.build_model(input_dim=input_dim, output_dim=output_dim)
                
                # 早停回调
                early_stopping = keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=self.cv_params['patience'],
                    restore_best_weights=True,
                    verbose=1
                )
                
                # 训练模型
                history = model.fit(
                    X_fold_train, y_fold_train,
                    validation_data=(X_fold_val, y_fold_val),
                    epochs=self.cv_params['epochs'],
                    batch_size=self.cv_params['batch_size'],
                    verbose=0,
                    callbacks=[early_stopping]
                )
                
                # 保存模型
                model_path = os.path.join(self.cv_models_dir, f'fold{fold}.keras')
                model.save(model_path)
                print(f"  ✅ 模型已保存: fold{fold}.keras")
                
                # 保存训练历史
                history_path = os.path.join(self.cv_histories_dir, f'cv_history_fold{fold}.json')
                with open(history_path, 'w') as f:
                    import json
                    history_dict = {}
                    for key, values in history.history.items():
                        history_dict[key] = [float(v) for v in values]
                    json.dump(history_dict, f, indent=2)
                
                # 验证集预测和指标（标签归一化版）
                y_val_pred_norm = model.predict(X_fold_val, verbose=0)  # 预测归一化标签
                y_val_pred_raw = y_val_pred_norm * self.MAX_SCORES      # 乘回满分进行评估
                
                # 获取原始验证标签（从索引中提取）
                y_fold_val_raw = y_train_raw[val_idx]
                
                # 计算原始量纲的指标
                val_mse = mean_squared_error(y_fold_val_raw, y_val_pred_raw)
                val_rmse = np.sqrt(val_mse)  # 兼容老版本sklearn
                val_mae = mean_absolute_error(y_fold_val_raw, y_val_pred_raw)
                val_r2 = r2_score(y_fold_val_raw, y_val_pred_raw)
                best_epoch = len(history.history['loss'])
                
                fold_metrics.append({
                    'fold': fold,
                    'val_rmse': float(val_rmse),
                    'val_mae': float(val_mae),
                    'val_r2': float(val_r2),
                    'best_epoch': best_epoch,
                    'final_train_loss': float(history.history['loss'][-1]),
                    'final_val_loss': float(history.history['val_loss'][-1])
                })
                
                # 测试集预测（用于后续集成，保存归一化版本）
                y_test_pred_norm = model.predict(X_test, verbose=0)  # 归一化预测
                fold_predictions.append(y_test_pred_norm)            # 保存归一化版本用于集成
                
                print(f"  📊 验证 RMSE: {val_rmse:.4f}, MAE: {val_mae:.4f}, R²: {val_r2:.4f}")
                print(f"  🏁 最佳轮次: {best_epoch}")
            
            # 集成预测（标签归一化版）
            print(f"\n🔄 计算集成预测...")
            y_pred_ensemble_norm = np.mean(fold_predictions, axis=0)  # 归一化集成预测
            y_pred_ensemble_raw = y_pred_ensemble_norm * self.MAX_SCORES  # 乘回满分
            
            print(f"📊 集成预测范围: norm ∈ [{y_pred_ensemble_norm.min():.3f}, {y_pred_ensemble_norm.max():.3f}]")
            print(f"📊 集成预测范围: raw ∈ [{y_pred_ensemble_raw.min():.1f}, {y_pred_ensemble_raw.max():.1f}]")
            
            # 集成评估（使用原始量纲）
            ensemble_mse = mean_squared_error(y_test_raw, y_pred_ensemble_raw)
            ensemble_rmse = np.sqrt(ensemble_mse)  # 兼容老版本sklearn
            ensemble_mae = mean_absolute_error(y_test_raw, y_pred_ensemble_raw)
            ensemble_r2 = r2_score(y_test_raw, y_pred_ensemble_raw)
            
            # 每个子分数的详细评估
            detailed_metrics = {}
            target_names = ['Q1_subscore', 'Q2_subscore', 'Q3_subscore', 'Q4_subscore', 'Q5_subscore']
            
            for i, target in enumerate(target_names):
                y_true_col = y_test_raw[:, i]         # 使用原始量纲
                y_pred_col = y_pred_ensemble_raw[:, i] # 使用原始量纲
                
                mse_val = mean_squared_error(y_true_col, y_pred_col)
                detailed_metrics[target] = {
                    'mse': float(mse_val),
                    'rmse': float(np.sqrt(mse_val)),  # 兼容老版本sklearn
                    'mae': float(mean_absolute_error(y_true_col, y_pred_col)),
                    'r2': float(r2_score(y_true_col, y_pred_col)),
                    'max_score': float(self.MAX_SCORES[i])  # 添加满分信息
                }
            
            # 保存集成预测结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 创建预测结果DataFrame（原始量纲）
            predictions_df = pd.DataFrame({
                'Subject_ID': range(len(y_test_raw)),  # 临时ID，实际使用时应传入真实ID
                **{f'y_true_{target}': y_test_raw[:, i] for i, target in enumerate(target_names)},
                **{f'y_pred_{target}': y_pred_ensemble_raw[:, i] for i, target in enumerate(target_names)},
                # 额外添加归一化版本用于调试
                **{f'y_pred_norm_{target}': y_pred_ensemble_norm[:, i] for i, target in enumerate(target_names)}
            })
            
            predictions_path = os.path.join(self.model_dir, f'ensemble_test_predictions_{timestamp}.csv')
            predictions_df.to_csv(predictions_path, index=False)
            
            # 保存CV指标（包含标签归一化和特征选择信息）
            cv_metrics = {
                'fold_stats': fold_metrics,
                'ensemble': {
                    'mse': float(ensemble_mse),
                    'rmse': float(ensemble_rmse),
                    'mae': float(ensemble_mae),
                    'r2': float(ensemble_r2)
                },
                'detailed_metrics': detailed_metrics,
                'cv_params': self.cv_params,
                'label_normalization': {
                    'enabled': True,
                    'max_scores': self.MAX_SCORES.tolist(),
                    'description': 'Labels normalized to [0,1] during training, scaled back for evaluation'
                },
                'feature_selection': {
                    'enabled': True,
                    'total_features': len(X_train[0]),
                    'expected_features': [
                        'game_duration', 'KW_ROI_time', 'INST_ROI_time', 'BG_ROI_time',
                        'RR_1D', 'DET_1D', 'ENT_1D', 'RR_2D', 'DET_2D', 'ENT_2D'
                    ],
                    'actual_features': feature_columns,
                    'description': 'Expert-recommended 10 core eye-movement features: 4 basic + 6 RQA parameters'
                },
                'timestamp': timestamp
            }
            
            metrics_path = os.path.join(self.model_dir, f'cv_metrics_{timestamp}.json')
            with open(metrics_path, 'w') as f:
                json.dump(cv_metrics, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ 5-fold交叉验证完成!")
            print(f"📊 集成结果:")
            print(f"  🎯 RMSE: {ensemble_rmse:.4f}")
            print(f"  📏 MAE: {ensemble_mae:.4f}")
            print(f"  📈 R²: {ensemble_r2:.4f}")
            
            # 计算CV统计
            fold_rmses = [m['val_rmse'] for m in fold_metrics]
            cv_rmse_mean = np.mean(fold_rmses)
            cv_rmse_std = np.std(fold_rmses)
            
            print(f"  📊 CV RMSE: {cv_rmse_mean:.4f} ± {cv_rmse_std:.4f}")
            
            return {
                'success': True,
                'ensemble_metrics': {
                    'rmse': ensemble_rmse,
                    'mae': ensemble_mae,
                    'r2': ensemble_r2,
                    'mse': ensemble_mse
                },
                'fold_metrics': fold_metrics,
                'detailed_metrics': detailed_metrics,
                'cv_stats': {
                    'cv_rmse_mean': float(cv_rmse_mean),
                    'cv_rmse_std': float(cv_rmse_std),
                    'best_fold': min(fold_metrics, key=lambda x: x['val_rmse'])['fold']
                },
                'files': {
                    'predictions': predictions_path,
                    'metrics': metrics_path,
                    'models_dir': self.cv_models_dir,
                    'histories_dir': self.cv_histories_dir
                }
            }
            
        except Exception as e:
            print(f"❌ CV训练失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def load_ensemble_models(self):
        """加载所有CV模型用于集成预测"""
        try:
            import glob
            model_paths = glob.glob(os.path.join(self.cv_models_dir, 'fold*.keras'))
            if len(model_paths) != self.cv_params['n_splits']:
                raise FileNotFoundError(f"期望{self.cv_params['n_splits']}个模型，实际找到{len(model_paths)}个")
            
            models = []
            for path in sorted(model_paths):
                model = keras.models.load_model(path)
                models.append(model)
            
            return models
        except Exception as e:
            print(f"❌ 加载集成模型失败: {str(e)}")
            return None
    
    def predict_ensemble(self, X_input, models=None, return_raw_scale=True):
        """使用集成模型进行预测（支持标签归一化）"""
        if models is None:
            models = self.load_ensemble_models()
            if models is None:
                raise RuntimeError("无法加载集成模型")
        
        # 获取所有模型的预测（归一化版本）
        predictions_norm = []
        for model in models:
            pred_norm = model.predict(X_input, verbose=0)
            predictions_norm.append(pred_norm)
        
        # 计算平均预测（归一化版本）
        ensemble_prediction_norm = np.mean(predictions_norm, axis=0)
        
        if return_raw_scale:
            # 乘回满分得到原始量纲
            ensemble_prediction_raw = ensemble_prediction_norm * self.MAX_SCORES
            individual_predictions_raw = [pred * self.MAX_SCORES for pred in predictions_norm]
            return ensemble_prediction_raw, individual_predictions_raw
        else:
            # 返回归一化版本
            return ensemble_prediction_norm, predictions_norm

class MLPTrainer:
    """MLP模型训练器（单模型版本）"""
    
    def __init__(self, config_name):
        self.config_name = config_name
        self.model_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'module9_ml_results', config_name)
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 默认模型参数 - 针对小样本过拟合优化
        self.default_params = {
            'model_type': 'simple',  # 'simple', 'moderate', 'complex'
            'hidden_layers': [32],   # 简化网络结构，单隐藏层32神经元
            'activation': 'relu',
            'output_activation': 'linear',
            'optimizer': 'adam',
            'loss': 'mse',
            'metrics': ['mse', 'mae'],
            'epochs': 100,
            'batch_size': 8,  # 专家建议：8更适合48个训练样本
            'validation_split': 0.2,  # 专家建议：0.2更合理
            'early_stopping_patience': 15,
            'learning_rate': 0.001,
            # 正则化参数
            'use_dropout': True,
            'dropout_rate': 0.3,
            'use_l2_regularization': True,
            'l2_lambda': 0.01,
            'use_batch_normalization': False  # 小数据集不建议使用
        }
    
    def get_model_presets(self):
        """获取预设模型配置"""
        return {
            'simple': {
                'hidden_layers': [32],
                'description': '单隐藏层32神经元 - 适合小样本，防过拟合'
            },
            'moderate': {
                'hidden_layers': [64, 32],
                'description': '双隐藏层64+32神经元 - 中等复杂度'
            },
            'complex': {
                'hidden_layers': [64, 32, 16],
                'description': '三隐藏层64+32+16神经元 - 复杂模型，需大样本'
            }
        }

    def create_mlp_model(self, input_dim=10, output_dim=5, params=None):
        """创建优化的MLP模型，针对小样本过拟合问题"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow不可用，无法创建MLP模型")
        
        if params is None:
            params = self.default_params
        
        model = keras.Sequential()
        
        # L2正则化配置
        l2_reg = keras.regularizers.l2(params.get('l2_lambda', 0.01)) if params.get('use_l2_regularization', False) else None
        
        # 输入层和第一个隐藏层
        model.add(layers.Dense(
            params['hidden_layers'][0], 
            input_dim=input_dim,
            activation=params['activation'],
            kernel_initializer='he_normal',
            kernel_regularizer=l2_reg,
            name='hidden_layer_1'
        ))
        
        # 第一层后的Dropout
        if params.get('use_dropout', False):
            model.add(layers.Dropout(params.get('dropout_rate', 0.3), name='dropout_1'))
        
        # 批归一化（如果启用）
        if params.get('use_batch_normalization', False):
            model.add(layers.BatchNormalization(name='batch_norm_1'))
        
        # 额外的隐藏层
        for i, units in enumerate(params['hidden_layers'][1:], 2):
            model.add(layers.Dense(
                units,
                activation=params['activation'],
                kernel_initializer='he_normal',
                kernel_regularizer=l2_reg,
                name=f'hidden_layer_{i}'
            ))
            
            # 每层后添加Dropout
            if params.get('use_dropout', False):
                model.add(layers.Dropout(params.get('dropout_rate', 0.3), name=f'dropout_{i}'))
            
            # 批归一化（如果启用）
            if params.get('use_batch_normalization', False):
                model.add(layers.BatchNormalization(name=f'batch_norm_{i}'))
        
        # 输出层（无正则化）
        model.add(layers.Dense(
            output_dim,
            activation=params['output_activation'],
            name='output_layer'
        ))
        
        # 详细模型信息
        regularization_info = []
        if params.get('use_dropout', False):
            regularization_info.append(f"Dropout({params.get('dropout_rate', 0.3)})")
        if params.get('use_l2_regularization', False):
            regularization_info.append(f"L2({params.get('l2_lambda', 0.01)})")
        if params.get('use_batch_normalization', False):
            regularization_info.append("BatchNorm")
        
        reg_str = f" + {'+'.join(regularization_info)}" if regularization_info else ""
        
        print(f"🧠 创建优化MLP模型: {input_dim}维输入 -> {params['hidden_layers']} -> {output_dim}维输出{reg_str}")
        print(f"📊 模型复杂度: {params.get('model_type', 'custom')}级别")
        
        return model
    
    def compile_model(self, model, params=None):
        """编译模型"""
        if params is None:
            params = self.default_params
        
        # 创建优化器
        if params.get('learning_rate'):
            optimizer = keras.optimizers.Adam(learning_rate=params['learning_rate'])
        else:
            optimizer = params['optimizer']
        
        model.compile(
            optimizer=optimizer,
            loss=params['loss'],
            metrics=params['metrics']
        )
        
        print(f"⚙️ 模型编译完成: {params['optimizer']}, 损失函数: {params['loss']}")
        
        return model
    
    def train_model(self, X_train, y_train, X_test=None, y_test=None, params=None):
        """训练MLP模型"""
        try:
            if params is None:
                params = self.default_params
            
            print(f"🚀 开始MLP模型训练")
            print(f"📊 训练数据: {X_train.shape[0]} 样本, {X_train.shape[1]} 特征")
            print(f"🎯 目标数据: {y_train.shape[0]} 样本, {y_train.shape[1]} 输出")
            
            # 创建和编译模型
            model = self.create_mlp_model(
                input_dim=X_train.shape[1],
                output_dim=y_train.shape[1],
                params=params
            )
            
            model = self.compile_model(model, params)
            
            # 显示模型摘要
            print("📋 模型结构:")
            model.summary(print_fn=lambda x: print(f"  {x}"))
            
            # 准备回调函数
            callbacks = []
            
            # 早停回调
            if params.get('early_stopping_patience'):
                early_stop = EarlyStopping(
                    monitor='val_loss',
                    patience=params['early_stopping_patience'],
                    restore_best_weights=True,
                    verbose=1
                )
                callbacks.append(early_stop)
                print(f"📌 早停策略: 验证损失{params['early_stopping_patience']}轮未改善即停止")
            
            # 模型检查点
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_path = os.path.join(self.model_dir, f'best_model_{timestamp}.h5')
            checkpoint = ModelCheckpoint(
                checkpoint_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            )
            callbacks.append(checkpoint)
            
            # 开始训练
            print(f"🎓 开始训练: {params['epochs']} epochs, batch_size={params['batch_size']}")
            
            history = model.fit(
                X_train, y_train,
                epochs=params['epochs'],
                batch_size=params['batch_size'],
                validation_split=params['validation_split'],
                callbacks=callbacks,
                verbose=1
            )
            
            # 训练完成后的评估
            print(f"✅ 训练完成!")
            
            # 在测试集上评估
            if X_test is not None and y_test is not None:
                print(f"🧪 测试集评估:")
                test_loss = model.evaluate(X_test, y_test, verbose=0)
                print(f"  测试损失(MSE): {test_loss[0]:.4f}")
                if len(test_loss) > 1:
                    print(f"  测试MAE: {test_loss[2]:.4f}")
                
                # 详细测试集性能分析
                print(f"📊 详细测试集性能分析:")
                
                # 获取预测结果
                from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
                y_pred = model.predict(X_test, verbose=0)
                
                # 整体性能指标
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                rmse = mse ** 0.5
                r2 = r2_score(y_test, y_pred)
                
                print(f"🎯 整体测试集性能:")
                print(f"  TEST MSE: {mse:.4f}")
                print(f"  TEST RMSE: {rmse:.4f}")
                print(f"  TEST MAE: {mae:.4f}")
                print(f"  TEST R²: {r2:.4f}")
                
                # 每个MMSE子分数的详细分析
                print(f"📋 各子分数详细性能:")
                subscore_names = ["时间定向(Q1)", "空间定向(Q2)", "即时记忆(Q3)", "注意/计算(Q4)", "延迟回忆(Q5)"]
                max_scores = [5, 5, 3, 5, 3]  # 各子分数的满分
                
                subscore_results = []
                for i, (name, max_score) in enumerate(zip(subscore_names, max_scores)):
                    sub_mae = mean_absolute_error(y_test[:, i], y_pred[:, i])
                    sub_r2 = r2_score(y_test[:, i], y_pred[:, i])
                    sub_mse = mean_squared_error(y_test[:, i], y_pred[:, i])
                    sub_rmse = sub_mse ** 0.5
                    
                    # 计算相对误差 (MAE/满分)
                    relative_error = (sub_mae / max_score) * 100
                    
                    print(f"  {name}:")
                    print(f"    MAE: {sub_mae:.3f} (相对误差: {relative_error:.1f}%)")
                    print(f"    RMSE: {sub_rmse:.3f}")
                    print(f"    R²: {sub_r2:.3f}")
                    print(f"    满分: {max_score}")
                    
                    subscore_results.append({
                        'name': name,
                        'mae': sub_mae,
                        'rmse': sub_rmse,
                        'r2': sub_r2,
                        'relative_error': relative_error,
                        'max_score': max_score
                    })
                
                # 性能分级评估
                print(f"🏆 性能分级评估:")
                avg_relative_error = sum([r['relative_error'] for r in subscore_results]) / len(subscore_results)
                avg_r2 = sum([r['r2'] for r in subscore_results]) / len(subscore_results)
                
                if avg_relative_error < 15 and avg_r2 > 0.7:
                    performance_grade = "优秀"
                    grade_emoji = "🏆"
                elif avg_relative_error < 25 and avg_r2 > 0.5:
                    performance_grade = "良好"  
                    grade_emoji = "🥈"
                elif avg_relative_error < 35 and avg_r2 > 0.3:
                    performance_grade = "中等"
                    grade_emoji = "🥉"
                else:
                    performance_grade = "需改进"
                    grade_emoji = "⚠️"
                
                print(f"  {grade_emoji} 综合评级: {performance_grade}")
                print(f"  平均相对误差: {avg_relative_error:.1f}%")
                print(f"  平均R²: {avg_r2:.3f}")
                
                # 训练vs验证vs测试对比
                print(f"📊 模型泛化分析:")
                final_train_loss = history.history['loss'][-1]
                final_val_loss = history.history['val_loss'][-1]
                best_val_loss = min(history.history['val_loss'])
                
                # 过拟合检测
                overfitting_ratio = final_val_loss / final_train_loss
                generalization_gap = abs(mse - final_val_loss)
                
                print(f"  最终训练损失: {final_train_loss:.4f}")
                print(f"  最终验证损失: {final_val_loss:.4f}")
                print(f"  最佳验证损失: {best_val_loss:.4f}")
                print(f"  测试集损失: {mse:.4f}")
                print(f"  过拟合比率: {overfitting_ratio:.2f}")
                print(f"  泛化差距: {generalization_gap:.4f}")
                
                if overfitting_ratio > 2.0:
                    print(f"⚠️  检测到过拟合! 建议:")
                    print(f"   - 增加Dropout率 (当前: {params.get('dropout_rate', 0.3)})")
                    print(f"   - 增加L2正则化 (当前: {params.get('l2_lambda', 0.01)})")
                    print(f"   - 简化网络结构")
                    print(f"   - 增加训练数据")
                elif overfitting_ratio < 1.2:
                    print(f"✅ 模型泛化良好")
                else:
                    print(f"📈 轻微过拟合，在可接受范围内")
                
                # 保存详细评估结果到训练历史
                detailed_evaluation = {
                    'overall': {
                        'mse': float(mse),
                        'mae': float(mae),
                        'rmse': float(rmse),
                        'r2': float(r2)
                    },
                    'subscore_results': subscore_results,
                    'performance_grade': performance_grade,
                    'avg_relative_error': float(avg_relative_error),
                    'avg_r2': float(avg_r2),
                    'overfitting_ratio': float(overfitting_ratio),
                    'generalization_gap': float(generalization_gap)
                }
            
            # 保存最终模型 - 使用有意义的文件名
            # 构建文件名: RQA参数_模型类型_隐藏层_正则化_时间戳
            model_type = params.get('model_type', 'simple')
            hidden_layers_str = '_'.join(map(str, params.get('hidden_layers', [32])))
            dropout_str = f"dropout{params.get('dropout_rate', 0.3)}" if params.get('use_dropout', False) else "nodropout"
            l2_str = f"l2{params.get('l2_lambda', 0.01)}" if params.get('use_l2_regularization', False) else "nol2"
            
            model_filename = f"{self.config_name}_{model_type}_{hidden_layers_str}_{dropout_str}_{l2_str}_{timestamp}.h5"
            final_model_path = os.path.join(self.model_dir, model_filename)
            model.save(final_model_path)
            
            # 同时保存最佳模型的副本（如果存在）
            best_model_path = os.path.join(self.model_dir, f'best_model_{timestamp}.h5')
            if os.path.exists(best_model_path):
                best_model_filename = f"{self.config_name}_{model_type}_{hidden_layers_str}_{dropout_str}_{l2_str}_best_{timestamp}.h5"
                best_model_final_path = os.path.join(self.model_dir, best_model_filename)
                try:
                    import shutil
                    shutil.copy2(best_model_path, best_model_final_path)
                    print(f"💾 最佳模型已保存: {best_model_filename}")
                except Exception as e:
                    print(f"⚠️ 复制最佳模型失败: {e}")
            
            # 保存训练历史（包含详细评估结果）
            history_path = os.path.join(self.model_dir, f'training_history_{timestamp}.json')
            history_data = {
                'loss': [float(x) for x in history.history['loss']],
                'val_loss': [float(x) for x in history.history['val_loss']],
                'mse': [float(x) for x in history.history.get('mse', [])],
                'val_mse': [float(x) for x in history.history.get('val_mse', [])],
                'mae': [float(x) for x in history.history.get('mae', [])],
                'val_mae': [float(x) for x in history.history.get('val_mae', [])],
                'epochs_trained': len(history.history['loss']),
                'best_val_loss': float(min(history.history['val_loss'])),
                'final_train_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1])
            }
            
            # 添加详细测试集评估结果
            if X_test is not None and y_test is not None and 'detailed_evaluation' in locals():
                history_data['detailed_test_evaluation'] = detailed_evaluation
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            # 保存训练结果摘要
            model_files_info = {
                'final_model': final_model_path,
                'final_model_filename': model_filename,
                'best_checkpoint': checkpoint_path,
                'training_history': history_path
            }
            
            # 如果最佳模型存在，添加到文件信息中
            if 'best_model_final_path' in locals():
                model_files_info['best_model'] = best_model_final_path
                model_files_info['best_model_filename'] = best_model_filename
            
            training_summary = {
                'config_name': self.config_name,
                'timestamp': timestamp,
                'model_params': params,
                'training_stats': history_data,
                'model_files': model_files_info,
                'data_info': {
                    'train_samples': X_train.shape[0],
                    'test_samples': X_test.shape[0] if X_test is not None else 0,
                    'input_features': X_train.shape[1],
                    'output_targets': y_train.shape[1]
                }
            }
            
            print(f"💾 最终模型已保存: {model_filename}")
            print(f"📋 训练历史已保存: training_history_{timestamp}.json")
            print(f"📁 保存目录: {self.model_dir}")
            
            # 准备返回结果，包含详细评估
            result = {
                'success': True,
                'model': model,
                'history': history_data,
                'summary': training_summary,
                'files': training_summary['model_files']
            }
            
            # 如果有详细评估结果，添加到返回值
            if X_test is not None and y_test is not None and 'detailed_evaluation' in locals():
                result['detailed_evaluation'] = detailed_evaluation
            
            return result
            
        except Exception as e:
            print(f"❌ 模型训练失败: {str(e)}")
            raise e

@ml_prediction_bp.route('/api/ml/train-model', methods=['POST'])
def train_mlp_model():
    """训练MLP模型"""
    try:
        if not TENSORFLOW_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'TensorFlow不可用，请安装tensorflow库'
            }), 500
        
        data = request.get_json()
        config_name = data.get('config_name')
        model_params = data.get('model_params', {})
        
        if not config_name:
            return jsonify({
                'success': False,
                'error': '请提供RQA配置名称'
            }), 400
        
        print(f"🚀 开始训练MLP模型，配置: {config_name}")
        
        # 加载预处理后的数据
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'module9_ml_results', config_name)
        
        # 查找最新的数据文件
        train_files = [f for f in os.listdir(config_dir) if f.startswith('train_dataset_')]
        test_files = [f for f in os.listdir(config_dir) if f.startswith('test_dataset_')]
        
        if not train_files or not test_files:
            return jsonify({
                'success': False,
                'error': f'未找到{config_name}的预处理数据，请先运行数据预处理'
            }), 400
        
        # 使用最新的数据文件
        latest_train = sorted(train_files)[-1]
        latest_test = sorted(test_files)[-1]
        
        train_path = os.path.join(config_dir, latest_train)
        test_path = os.path.join(config_dir, latest_test)
        
        print(f"📂 加载训练数据: {latest_train}")
        print(f"📂 加载测试数据: {latest_test}")
        
        # 加载数据
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        # 分离特征和标签
        feature_columns = [col for col in train_df.columns 
                          if col not in ['Subject_ID', 'Group_Type'] 
                          and not col.endswith('_subscore')]
        target_columns = [col for col in train_df.columns if col.endswith('_subscore')]
        
        X_train = train_df[feature_columns].values
        y_train = train_df[target_columns].values
        X_test = test_df[feature_columns].values  
        y_test = test_df[target_columns].values
        
        print(f"📊 训练特征: {X_train.shape}")
        print(f"🎯 训练标签: {y_train.shape}")
        print(f"📊 测试特征: {X_test.shape}")
        print(f"🎯 测试标签: {y_test.shape}")
        
        # 创建训练器并训练模型
        trainer = MLPTrainer(config_name)
        
        # 合并用户参数和默认参数
        final_params = trainer.default_params.copy()
        final_params.update(model_params)
        
        print(f"⚙️ 训练参数: {final_params}")
        
        # 训练模型
        result = trainer.train_model(X_train, y_train, X_test, y_test, final_params)
        
        if result['success']:
            print(f"✅ MLP模型训练完成!")
            
            # 提取detailed_evaluation以便前端访问
            detailed_eval = None
            if 'detailed_evaluation' in result:
                detailed_eval = result['detailed_evaluation']
            elif 'history' in result and 'detailed_test_evaluation' in result['history']:
                detailed_eval = result['history']['detailed_test_evaluation']
            
            return jsonify({
                'success': True,
                'message': 'MLP模型训练完成',
                'training_stats': result['history'],
                'detailed_evaluation': detailed_eval,
                'summary': result['summary'],
                'files': result['files']
            })
        else:
            return jsonify({
                'success': False,
                'error': '模型训练失败'
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        print(f"❌ MLP训练失败: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@ml_prediction_bp.route('/api/ml/cv-train', methods=['POST'])
def cv_train_model():
    """执行5-fold交叉验证训练（专家优化版）"""
    try:
        data = request.get_json()
        config_name = data.get('config_name')
        cv_params = data.get('cv_params', {})
        
        if not config_name:
            return jsonify({
                'success': False,
                'error': '请提供RQA配置名称'
            }), 400
        
        print(f"🚀 开始CV训练，配置: {config_name}")
        
        # 加载预处理数据
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'module9_ml_results', config_name)
        
        # 查找最新的训练和测试数据
        import glob
        train_files = glob.glob(os.path.join(config_dir, 'train_dataset_*.csv'))
        test_files = glob.glob(os.path.join(config_dir, 'test_dataset_*.csv'))
        
        if not train_files or not test_files:
            return jsonify({
                'success': False,
                'error': '未找到预处理数据，请先执行数据预处理'
            }), 400
        
        # 使用最新的数据文件
        train_file = sorted(train_files)[-1]
        test_file = sorted(test_files)[-1]
        
        # 加载数据
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        # 专家建议：精选10个核心眼动特征
        expected_10_features = [
            'game_duration', 'KW_ROI_time', 'INST_ROI_time', 'BG_ROI_time',  # 4个基础眼动指标
            'RR_1D', 'DET_1D', 'ENT_1D', 'RR_2D', 'DET_2D', 'ENT_2D'        # 6个RQA参数
        ]
        
        # 检查数据中实际存在的特征
        available_cols = list(train_df.columns)
        target_columns = [col for col in train_df.columns if col.endswith('_subscore')]
        
        # 找出实际存在的10个核心特征
        feature_columns = []
        missing_features = []
        for feature in expected_10_features:
            if feature in available_cols:
                feature_columns.append(feature)
            else:
                missing_features.append(feature)
        
        # 如果10个核心特征不全，从可用列中补充（排除ID和标签列）
        if len(feature_columns) < 10:
            exclude_cols = ['Subject_ID', 'Group_Type'] + target_columns + ['task_count', 'missing_count']
            additional_cols = [col for col in available_cols if col not in exclude_cols + feature_columns]
            needed = 10 - len(feature_columns)
            feature_columns.extend(additional_cols[:needed])
        
        print(f"🎯 专家10特征筛选:")
        print(f"  期望特征: {expected_10_features}")
        print(f"  实际特征: {feature_columns}")
        print(f"  特征维度: {len(feature_columns)}")
        if missing_features:
            print(f"  ⚠️ 缺失特征: {missing_features}")
        if len(feature_columns) == 10:
            print(f"  ✅ 成功获得10个核心特征")
        
        # 重新提取特征数据
        X_train_raw = train_df[feature_columns].values
        y_train = train_df[target_columns].values
        X_test_raw = test_df[feature_columns].values
        y_test = test_df[target_columns].values
        
        # 重新fit scaler（专家建议：基于精选特征重新标准化）
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train_raw)
        X_test = scaler.transform(X_test_raw)
        
        # 保存更新的scaler
        scaler_path = os.path.join(config_dir, 'scaler_10features.pkl')
        joblib.dump(scaler, scaler_path)
        print(f"✅ 10特征scaler已保存: {scaler_path}")
        
        print(f"📊 数据加载完成:")
        print(f"  训练集: {X_train.shape}")
        print(f"  测试集: {X_test.shape}")
        print(f"  特征数: {len(feature_columns)} (实际维度: {X_train.shape[1]})")
        print(f"  目标数: {len(target_columns)} (实际维度: {y_train.shape[1]})")
        print(f"  特征列表: {feature_columns}")
        
        # 创建CV训练器
        cv_trainer = CVMLPTrainer(config_name)
        
        # 如果有自定义参数，更新CV参数
        if cv_params:
            cv_trainer.cv_params.update(cv_params)
            print(f"🔧 使用自定义参数: {cv_params}")
        
        # 执行CV训练（传递原始标签，由CV训练器内部归一化）
        result = cv_trainer.train_cv_models(X_train, y_train, X_test, y_test)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '5-fold交叉验证训练完成',
                'ensemble_metrics': result['ensemble_metrics'],
                'fold_metrics': result['fold_metrics'],
                'cv_stats': result['cv_stats'],
                'detailed_metrics': result['detailed_metrics'],
                'files': result['files']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        import traceback
        traceback.print_exc()
        print(f"❌ CV训练失败: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@ml_prediction_bp.route('/api/ml/ensemble-predict', methods=['POST'])
def ensemble_predict():
    """使用集成模型进行预测"""
    try:
        data = request.get_json()
        config_name = data.get('config_name')
        features = data.get('features')  # 原始特征字典或数组
        
        if not config_name or not features:
            return jsonify({
                'success': False,
                'error': '请提供配置名称和特征数据'
            }), 400
        
        # 加载CV训练器
        cv_trainer = CVMLPTrainer(config_name)
        
        # 如果features是字典，需要转换为数组
        if isinstance(features, dict):
            # 加载特征方向配置和scaler
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'module9_ml_results', config_name)
            
            try:
                # 加载特征配置
                import glob
                config_files = glob.glob(os.path.join(config_dir, 'latest_feature_config.json'))
                if config_files:
                    with open(config_files[0], 'r') as f:
                        feature_config = json.load(f)
                else:
                    feature_config = None
                
                # 加载scaler（优先使用10特征版本）
                scaler_10_files = glob.glob(os.path.join(config_dir, 'scaler_10features.pkl'))
                scaler_files = glob.glob(os.path.join(config_dir, 'latest_scaler.pkl'))
                
                if scaler_10_files:
                    scaler = joblib.load(scaler_10_files[0])
                    print(f"✅ 使用10特征专用scaler: {scaler_10_files[0]}")
                elif scaler_files:
                    scaler = joblib.load(scaler_files[0])
                    print(f"⚠️ 使用通用scaler: {scaler_files[0]}")
                else:
                    return jsonify({
                        'success': False,
                        'error': '未找到特征标准化器'
                    }), 400
                
                # 预处理特征
                feature_array = []
                for feature_name in sorted(features.keys()):
                    value = features[feature_name]
                    
                    # 应用特征变换
                    if feature_config and feature_name in feature_config.get('feature_transforms', {}):
                        transform = feature_config['feature_transforms'][feature_name]['transform']
                        if transform == 'negate':
                            value = -value
                        elif transform == 'reciprocal':
                            value = 1.0 / (value + 1e-6)
                    
                    feature_array.append(value)
                
                # 标准化
                X_input = scaler.transform(np.array(feature_array).reshape(1, -1))
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'特征预处理失败: {str(e)}'
                }), 400
        else:
            # 假设features已经是预处理后的数组
            X_input = np.array(features).reshape(1, -1)
        
        # 执行集成预测（返回原始量纲）
        ensemble_pred, individual_preds = cv_trainer.predict_ensemble(X_input, return_raw_scale=True)
        
        # 格式化结果
        target_names = ['Q1_subscore', 'Q2_subscore', 'Q3_subscore', 'Q4_subscore', 'Q5_subscore']
        
        result = {
            'ensemble_prediction': {
                target_names[i]: float(ensemble_pred[0][i]) for i in range(len(target_names))
            },
            'individual_predictions': [
                {target_names[i]: float(pred[0][i]) for i in range(len(target_names))}
                for pred in individual_preds
            ],
            'prediction_stats': {
                'mean': {target_names[i]: float(np.mean([pred[0][i] for pred in individual_preds])) 
                        for i in range(len(target_names))},
                'std': {target_names[i]: float(np.std([pred[0][i] for pred in individual_preds])) 
                       for i in range(len(target_names))}
            }
        }
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        error_msg = str(e)
        import traceback
        traceback.print_exc()
        print(f"❌ 集成预测失败: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

def register_ml_prediction_routes(app):
    """注册机器学习预测路由"""
    app.register_blueprint(ml_prediction_bp)
    print("✅ 机器学习预测API路由已注册")