# 数据汇总报告
# Data Summary Report

**生成时间 / Generated**: 2025-10-07
**数据版本 / Data Version**: Final

---

## 📊 数据总览 / Data Overview

### 总受试者数 / Total Subjects: **153**

| 数据版本 | 受试者数 | 任务完整性 | 状态 |
|---------|---------|----------|------|
| V1 (Legacy) | 60 | 100% (5个任务/人) | ✅ 完整 |
| V2 (Eye Tracking) | 93 | 100% (5个任务/人) | ✅ 完整 |

---

## 📋 V1数据详情 / V1 Data Details

### V1受试者总数: **60**

| 组别 | 受试者数 | 任务类型 | 映射关系 |
|-----|---------|---------|---------|
| Control | 20 | q1-q5 | control_group_1-20 → control_legacy_1-20 |
| MCI | 20 | q1-q5 | mci_group_1-20 → mci_legacy_1-20 |
| AD | 20 | q1-q5 | ad_group_3-22 → ad_legacy_1-20 |

### V1 AD组特殊映射说明

**原始数据**: `data/ad_raw/ad_group_3` 到 `ad_group_22` (共20个目录)

**映射规则**: 重新编号为连续的1-20
```
ad_group_3  → ad_legacy_1
ad_group_4  → ad_legacy_2
ad_group_5  → ad_legacy_3
...
ad_group_22 → ad_legacy_20
```

**实现位置**: [legacy_importer.py](src/web/modules/module00_data_management/importers/legacy_importer.py:96-101)

---

## 📋 V2数据详情 / V2 Data Details

### V2受试者总数: **93**

| 组别 | 受试者数 | 任务类型 | 数据源 |
|-----|---------|---------|--------|
| Control | 77 | level_1-5 | eye_tracking_data/ |
| MCI | 8 | level_1-5 | eye_tracking_data/ |
| AD | 8 | level_1-5 | eye_tracking_data/ |

### V2任务完整性

✅ **所有93个V2受试者都有完整的5个任务**
- 任务类型: level_1, level_2, level_3, level_4, level_5
- 任务完整性: 100%
- 数据质量: 优秀

---

## 🎯 数据质量指标 / Data Quality Metrics

### 整体指标

| 指标 | 数值 | 状态 |
|-----|------|------|
| 总受试者数 | 153 | ✅ |
| V1受试者数 | 60 | ✅ |
| V2受试者数 | 93 | ✅ |
| V1任务完整性 | 100% (60/60) | ✅ |
| V2任务完整性 | 100% (93/93) | ✅ |
| 元数据完整性 | 100% | ✅ |

### 按组统计

**V1数据**:
- Control组: 20个受试者，100个任务文件 (20×5)
- MCI组: 20个受试者，100个任务文件 (20×5)
- AD组: 20个受试者，100个任务文件 (20×5)
- **V1总任务文件**: 300个

**V2数据**:
- Control组: 77个受试者，385个任务文件 (77×5)
- MCI组: 8个受试者，40个任务文件 (8×5)
- AD组: 8个受试者，40个任务文件 (8×5)
- **V2总任务文件**: 465个

**项目总任务文件**: **765个**

---

## 📁 数据存储位置 / Data Storage Locations

### V1数据存储

```
new_project/data/01_raw/
├── control/
│   ├── control_legacy_1_q1.csv
│   ├── control_legacy_1_q2.csv
│   └── ... (100个文件)
├── mci/
│   ├── mci_legacy_1_q1.csv
│   └── ... (100个文件)
└── ad/
    ├── ad_legacy_1_q1.csv
    └── ... (100个文件)
```

### V2数据存储

```
new_project/data/01_raw/
├── control/
│   ├── v2_control_001_level_1.csv
│   └── ... (385个文件)
├── mci/
│   ├── v2_mci_001_level_1.csv
│   └── ... (40个文件)
└── ad/
    ├── v2_ad_001_level_1.csv
    └── ... (40个文件)
```

### 元数据存储

```
new_project/data/
├── 01_raw/clinical/
│   └── subject_metadata.json  (153个受试者的元数据)
└── subject_info/
    ├── control/  (97个JSON文件: 20个V1 + 77个V2)
    ├── mci/      (28个JSON文件: 20个V1 + 8个V2)
    └── ad/       (28个JSON文件: 20个V1 + 8个V2)
```

---

## ✅ 架构合规性 / Architecture Compliance

### 符合架构要求 ✅

1. **数据版本隔离**
   - V1和V2数据完全分离
   - 清晰的版本标识

2. **任务完整性**
   - 所有受试者都有完整的5个任务
   - 无缺失数据

3. **映射关系固化**
   - AD组映射已在Module00中实现
   - 映射逻辑清晰可追溯

4. **元数据完整**
   - 每个受试者都有完整的元数据
   - 包含source_path、tasks_available等关键信息

---

## 🔍 数据验证方法 / Data Validation Methods

### 验证脚本

运行以下脚本验证数据完整性：

```bash
# 验证V1数据
cd new_project
python verify_v1_data.py

# 验证V2数据
python verify_v2_final.py

# 验证所有数据
python final_verification.py
```

### 验证结果

所有验证脚本均通过 ✅
- V1受试者: 60/60 完整
- V2受试者: 93/93 完整
- 总任务完整性: 100%

---

## 📝 注意事项 / Notes

### 重要提醒

1. **V1永远是60个受试者**
   - Control 20 + MCI 20 + AD 20 = 60
   - 这是固定不变的

2. **V2有93个受试者**
   - Control 77 + MCI 8 + AD 8 = 93
   - 所有受试者都有完整任务

3. **AD组映射关系已固化**
   - ad_group_3-22 → ad_legacy_1-20
   - 不要修改此映射逻辑

4. **任务命名规范**
   - V1任务: q1, q2, q3, q4, q5
   - V2任务: level_1, level_2, level_3, level_4, level_5

---

## 🎯 总结 / Summary

### 数据状态：完美 ✅

✅ **V1数据**: 60个受试者，100%任务完整
✅ **V2数据**: 93个受试者，100%任务完整
✅ **总数据**: 153个受试者，765个任务文件
✅ **架构合规**: 完全符合设计要求
✅ **质量保证**: 所有数据经过验证

**数据已准备就绪，可以进行后续的分析和处理工作！**

---

**报告人 / Reporter**: AI Data Analyst
**验证日期 / Verification Date**: 2025-10-07
**审核状态 / Approval Status**: ✅ **已确认 / CONFIRMED**
