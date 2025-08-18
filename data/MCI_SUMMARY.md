# MCI（轻度认知障碍）数据概览

## 数据说明
- **MCI**: Mild Cognitive Impairment（轻度认知障碍）
- **数据类型**: VR眼球追踪数据
- **对比组**: Control Group（对照组）vs MCI Group（认知障碍组）

## 文件夹结构
```
data/
├── mci_raw/              # MCI原始txt文件
│   ├── mci_group_XX/     # MCI第XX组数据
│   └── ...
├── mci_processed/        # MCI预处理csv文件
│   ├── mci_group_XX/     # MCI第XX组处理结果
│   └── ...
└── mci_calibrated/       # MCI校准csv文件
    ├── mci_group_XX/     # MCI第XX组校准结果
    └── ...
```

## 数据统计
- **MCI组数**: 21 组
- **原始文件**: 105 个txt文件
- **处理后文件**: 105 个csv文件

## 数据对比
| 数据类型 | Control Group | MCI Group |
|---------|---------------|----------|
| 位置 | data/raw/, data/processed/, data/calibrated/ | data/mci_raw/, data/mci_processed/, data/mci_calibrated/ |
| 命名格式 | control_group_{组号} | mci_group_{组号} |
| 用途 | 健康对照组 | 认知障碍对比组 |

## 校准建议
- **Control Group**: 使用标准校准参数
- **MCI Group**: 可能需要个体化校准参数
- **个体差异**: 建议为不同个体设置不同的校准偏移量

### MCI原始数据统计
- mci_group_1: 5 个txt文件
- mci_group_10: 5 个txt文件
- mci_group_11: 5 个txt文件
- mci_group_12: 5 个txt文件
- mci_group_13: 5 个txt文件
- mci_group_14: 5 个txt文件
- mci_group_15: 5 个txt文件
- mci_group_16: 5 个txt文件
- mci_group_17: 5 个txt文件
- mci_group_18: 5 个txt文件
- mci_group_19: 5 个txt文件
- mci_group_2: 5 个txt文件
- mci_group_20: 5 个txt文件
- mci_group_3: 5 个txt文件
- mci_group_4: 5 个txt文件
- mci_group_5: 5 个txt文件
- mci_group_6: 5 个txt文件
- mci_group_7: 5 个txt文件
- mci_group_8: 5 个txt文件
- mci_group_9: 5 个txt文件
- mci_group_jojo: 5 个txt文件

### MCI处理后数据统计
- mci_group_1: 5 个csv文件
- mci_group_10: 5 个csv文件
- mci_group_11: 5 个csv文件
- mci_group_12: 5 个csv文件
- mci_group_13: 5 个csv文件
- mci_group_14: 5 个csv文件
- mci_group_15: 5 个csv文件
- mci_group_16: 5 个csv文件
- mci_group_17: 5 个csv文件
- mci_group_18: 5 个csv文件
- mci_group_19: 5 个csv文件
- mci_group_2: 5 个csv文件
- mci_group_20: 5 个csv文件
- mci_group_3: 5 个csv文件
- mci_group_4: 5 个csv文件
- mci_group_5: 5 个csv文件
- mci_group_6: 5 个csv文件
- mci_group_7: 5 个csv文件
- mci_group_8: 5 个csv文件
- mci_group_9: 5 个csv文件
- mci_group_jojo: 5 个csv文件
