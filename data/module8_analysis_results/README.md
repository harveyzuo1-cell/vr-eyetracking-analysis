# 模块8分析结果目录

> **目录用途**: 存储模块8（眼动系数与MMSE对比分析）相关的CSV和JSON文件  
> **创建日期**: 2025年1月

---

## 📁 **目录结构**

```
module8_analysis_results/
├── README.md                           # 本说明文件
├── individual_comparisons/             # 个人层面对比结果
├── group_comparisons/                  # 群体层面对比结果
├── sub_question_analysis/              # 子问题详细分析
└── exported_reports/                   # 用户导出的报告文件
```

## 📊 **文件类型说明**

### **JSON文件**
- **命名格式**: `module8_comparison_{detail_mode}_{view_mode}_{date}.json`
- **内容**: 完整的分析结果，包括原始数据、统计信息和元数据
- **用途**: 数据交换、备份、进一步分析

### **CSV文件**
- **命名格式**: `module8_comparison_{detail_mode}_{view_mode}_{date}.csv`
- **内容**: 当前视图的表格数据，便于在Excel等工具中打开
- **用途**: 数据可视化、统计分析、报告制作

## 🔧 **detail_mode参数说明**

- **main**: 主问题模式（Q1-Q5大类问题）
- **subQuestion**: 子问题模式（17个具体子问题）

## 👥 **view_mode参数说明**

- **individual**: 个人视图（每个受试者的详细数据）
- **group**: 群体视图（各组的统计汇总数据）

## 📈 **数据内容说明**

### **主问题个人视图** (main_individual)
| 字段 | 说明 |
|-----|-----|
| subject_id | 受试者ID |
| task_id | 任务ID (Q1-Q5) |
| group_type | 组别 (control/mci/ad) |
| eye_movement_coefficient | 眼动系数 |
| mmse_score | MMSE分数 |
| mmse_max_score | MMSE满分 |
| performance_ratio | 完成率 |

### **子问题个人视图** (subQuestion_individual)
| 字段 | 说明 |
|-----|-----|
| subject_id | 受试者ID |
| task_id | 任务ID |
| sub_question_id | 子问题ID (Q1-1到Q5-3) |
| sub_question_name | 子问题名称 |
| group_type | 组别 |
| eye_movement_coefficient | 眼动系数 |
| sub_question_score | 子问题得分 |
| sub_question_max_score | 子问题满分 |
| sub_question_performance_ratio | 子问题完成率 |

### **群体视图** (group)
包含各组的平均值、相关系数、标准差等统计信息。

## ⚠️ **注意事项**

1. **MMSE分数修正**:
   - Q1满分: 5分 (年份1分 + 季节1分 + 月份1分 + 星期2分)
   - Q2满分: 5分 (省市区2分 + 街道1分 + 建筑1分 + 楼层1分)
   - Q3满分: 3分 (即刻记忆3分)
   - Q4满分: 5分 (100-7系列每题1分)
   - Q5满分: 3分 (词汇回忆每个1分)

2. **文件管理**:
   - 定期清理过期的临时文件
   - 重要分析结果建议备份到其他位置
   - 大文件可以压缩存储

3. **数据隐私**:
   - 导出的文件可能包含受试者信息
   - 请遵守数据保护相关规定
   - 分享数据前请进行脱敏处理

---

**📝 使用说明**: 
此目录由模块8自动管理，用户通过"导出对比报告"功能生成的文件将保存在相应的子目录中。