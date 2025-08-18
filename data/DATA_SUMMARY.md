# VR眼球追踪数据概览 (统一命名)
更新时间: C:\Users\asino\Downloads\az

## 统一命名说明
- **命名规则**: 统一使用 `{组类型}_{数据阶段}` 格式
- **Control Group**: control_raw, control_processed, control_calibrated
- **MCI Group**: mci_raw, mci_processed, mci_calibrated
- **优势**: 命名一致、清晰明确、避免误解

## 优化后的目录结构
```
data/
├── control_raw/              # 对照组原始数据
│   ├── control_group_1/      # 第1组对照数据
│   ├── control_group_2/      # 第2组对照数据
│   └── ...                   # 第3-20组
├── control_processed/        # 对照组预处理数据
│   ├── control_group_1/      # 第1组处理结果
│   └── ...                   # 其他组处理结果
├── control_calibrated/       # 对照组校准数据
│   ├── control_group_1/      # 第1组校准结果
│   └── ...                   # 其他组校准结果
├── mci_raw/                  # MCI组原始数据
│   ├── mci_group_XX/         # MCI第XX组数据
│   └── ...
├── mci_processed/            # MCI组预处理数据
│   ├── mci_group_XX/         # MCI第XX组处理结果
│   └── ...
└── mci_calibrated/           # MCI组校准数据
    ├── mci_group_XX/         # MCI第XX组校准结果
    └── ...
```

## 命名优化前后对比
| 数据类型 | 优化前 | 优化后 |
|---------|--------|--------|
| 对照组原始 | raw/ | control_raw/ |
| 对照组处理 | processed/ | control_processed/ |
| 对照组校准 | calibrated/ | control_calibrated/ |
| MCI组原始 | mci_raw/ | mci_raw/ (保持) |
| MCI组处理 | mci_processed/ | mci_processed/ (保持) |
| MCI组校准 | mci_calibrated/ | mci_calibrated/ (保持) |

## 使用建议
1. **清晰识别**: 一眼区分对照组vs认知障碍组数据
2. **批量操作**: 便于使用通配符进行批量处理
3. **脚本兼容**: 所有处理脚本已自动更新路径
4. **扩展性好**: 便于未来添加新的数据组类型

### CONTROL Group数据统计
- **raw**: 19组, 95个文件
- **processed**: 20组, 100个文件
- **calibrated**: 0组, 0个文件

### MCI Group数据统计
- **raw**: 21组, 105个文件
- **processed**: 21组, 105个文件
- **calibrated**: 21组, 105个文件
