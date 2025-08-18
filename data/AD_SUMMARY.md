# 阿尔兹海默症组(AD Group)数据概览
生成时间: 2025-07-24 19:09:02
提取自: C:\Users\asino\entropy\ip\mci-dataprocessing\trans_ad

## 数据概况
- **总组数**: 21 个AD组
- **原始文件**: 100 个.txt文件
- **预处理文件**: 100 个.csv文件
- **有原始数据的组**: 20 个
- **有预处理数据的组**: 20 个

## 目录结构
```
data/
├── ad_raw/                   # AD组原始数据
│   ├── ad_group_1/           # AD第1组数据
│   │   ├── 1.txt             # 任务1原始数据
│   │   ├── 2.txt             # 任务2原始数据
│   │   ├── 3.txt             # 任务3原始数据
│   │   ├── 4.txt             # 任务4原始数据
│   │   └── 5.txt             # 任务5原始数据
│   └── ...
├── ad_processed/             # AD组预处理数据
│   ├── ad_group_1/           # AD第1组处理结果
│   │   ├── ad1q1_preprocessed.csv  # 任务1预处理结果
│   │   ├── ad1q2_preprocessed.csv  # 任务2预处理结果
│   │   ├── ad1q3_preprocessed.csv  # 任务3预处理结果
│   │   ├── ad1q4_preprocessed.csv  # 任务4预处理结果
│   │   └── ad1q5_preprocessed.csv  # 任务5预处理结果
│   └── ...
└── ad_calibrated/            # AD组校准数据
    ├── ad_group_1/           # AD第1组校准结果
    │   ├── ad1q1_preprocessed_calibrated.csv
    │   ├── ad1q2_preprocessed_calibrated.csv
    │   ├── ad1q3_preprocessed_calibrated.csv
    │   ├── ad1q4_preprocessed_calibrated.csv
    │   └── ad1q5_preprocessed_calibrated.csv
    └── ...
```

## 文件命名规范
- **原始数据**: `1.txt`, `2.txt`, `3.txt`, `4.txt`, `5.txt`
- **预处理数据**: `ad{组号}q{任务编号}_preprocessed.csv`
- **校准数据**: `ad{组号}q{任务编号}_preprocessed_calibrated.csv`
- **组名格式**: `ad_group_{组号}`

## 数据完整性
### 有原始数据的组
- ad_group_10
- ad_group_11
- ad_group_12
- ad_group_13
- ad_group_14
- ad_group_15
- ad_group_16
- ad_group_17
- ad_group_18
- ad_group_19
- ad_group_20
- ad_group_21
- ad_group_22
- ad_group_3
- ad_group_4
- ad_group_5
- ad_group_6
- ad_group_7
- ad_group_8
- ad_group_9

### 有预处理数据的组
- ad_group_10
- ad_group_11
- ad_group_12
- ad_group_13
- ad_group_14
- ad_group_15
- ad_group_16
- ad_group_17
- ad_group_18
- ad_group_19
- ad_group_20
- ad_group_21
- ad_group_22
- ad_group_3
- ad_group_4
- ad_group_5
- ad_group_6
- ad_group_7
- ad_group_8
- ad_group_9

### 缺失数据的组
- ad_group_1 ⚠️

## 与其他组的对比
| 数据组 | 组数 | 原始文件 | 预处理文件 | 命名前缀 |
|--------|------|----------|------------|----------|
| Control Group | 20 | ~95 | 100 | n | 
| MCI Group | 21 | ~105 | 105 | m |
| AD Group | 20 | 100 | 100 | ad |

## 研究意义
- **对照组**: 健康对照
- **MCI组**: 轻度认知障碍
- **AD组**: 阿尔兹海默症患者
- **研究价值**: 支持认知障碍疾病进展的眼球追踪对比研究
