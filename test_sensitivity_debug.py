"""
调试参数敏感性分析
"""
import pandas as pd
from pathlib import Path

# 读取一个enriched_features.csv文件
csv_path = Path(r"c:\Users\asino\Downloads\az - 副本 (11)\new_project\data\05_rqa_analysis\results\m1_tau1_eps0.05_lmin2\step3_feature_enrichment\enriched_features.csv")

df = pd.read_csv(csv_path)

print("原始列名:")
print(list(df.columns))
print()

# 标准化列名
df.columns = df.columns.str.lower()
print("小写后列名:")
print(list(df.columns))
print()

# 标准化group列的值
if 'group' in df.columns:
    df['group'] = df['group'].str.lower()
    print("Group值 (唯一):", df['group'].unique())
print()

# 识别RQA特征
rqa_prefixes = ['rr-', 'det-', 'ent-', 'lam-', 'x_', 'y_', 'combined_', 'rqa_']
rqa_keywords = ['symmetry', 'diff', 'complexity']

rqa_features = []
for col in df.columns:
    col_lower = col.lower()
    if any(col_lower.startswith(prefix) for prefix in rqa_prefixes):
        rqa_features.append(col)
    elif any(keyword in col_lower for keyword in rqa_keywords):
        rqa_features.append(col)

print(f"识别到 {len(rqa_features)} 个RQA特征:")
print(rqa_features)
print()

# 测试第一个特征
if len(rqa_features) > 0:
    feature = rqa_features[0]
    print(f"测试特征: {feature}")
    print(f"数据统计: {df[feature].describe()}")
    print()

    # 测试跨任务分析
    for task in ['q1', 'q2', 'q3', 'q4', 'q5']:
        task_df = df[df['task_id'] == task]
        print(f"  任务 {task}: {len(task_df)} 行")

        # 按组别分组
        groups = []
        for group in ['control', 'mci', 'ad']:
            group_data = task_df[task_df['group'] == group][feature].dropna()
            print(f"    {group}: {len(group_data)} 个样本")
            if len(group_data) > 0:
                groups.append(group_data)

        print(f"    可用组数: {len(groups)}")
        if len(groups) >= 2:
            from scipy import stats
            f_stat, p_val = stats.f_oneway(*groups)
            print(f"    F统计量: {f_stat:.4f}, p值: {p_val:.4f}")
    print()

