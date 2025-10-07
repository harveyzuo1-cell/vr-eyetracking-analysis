# ModuleEX2: 数据导出与固化模块

## 📋 模块概述

ModuleEX2是数据固化和导出工具模块，负责将Module00(数据管理)、Module01(数据可视化)、Module02(数据预处理)、ModuleEX(ROI配置)处理后的数据进行固化存储和导出。

### 定位

- **类型**: 辅助工具模块 (EX = Extension)
- **作用**: 数据固化、归档、导出
- **对应架构**: 第6阶段数据流 - 结果输出 (`data/06_results/exports/`)

## 🎯 核心功能

### 1. 校准眼动数据导出
- 从 `data/02_processed/` 读取校准后的眼动数据
- 支持按受试者ID筛选
- 支持V1/V2数据版本
- 输出格式: CSV, Excel

### 2. ROI配置导出
- 从 `data/roi_configs/` 读取ROI配置
- 支持V1/V2版本分离
- 输出格式: JSON (完整结构), CSV (表格化)

### 3. 受试者信息+MMSE导出
- 从 `data/subject_info/` 读取受试者数据
- 包含完整MMSE评分（19题，21分）
  - Q1: 时间定向 (5分, q1_weekday 2分)
  - Q2: 地点定向 (5分, q2_province 2分)
  - Q3: 即刻记忆 (3分, 单题可变分值)
  - Q4: 注意力与计算 (5分)
  - Q5: 延迟回忆 (3分)
- 支持详细子题目展开
- 输出格式: CSV

### 4. 统一打包导出
- 一键导出所有数据（眼动+ROI+受试者）
- 自动生成ZIP压缩包
- 包含元数据 (export_metadata.json)

### 5. 导出历史管理
- 列出所有历史导出文件
- 提供下载接口
- 显示文件大小、创建时间

## 🏗️ 架构设计

### 符合6阶段数据流

根据项目架构文档 (`docs/ARCHITECTURE_REVIEW.md`)，数据流经6个阶段：

```
01_raw → 02_preprocessed → 03_calibrated → 04_features → 05_models → 06_results
```

**ModuleEX2的定位**：
- **输入**: 读取阶段2-4的处理结果
- **输出**: 存储到阶段6 (`data/06_results/exports/`)
- **作用**: 数据固化归档，便于长期存储和分享

### 目录结构

```
data/06_results/exports/
├── calibrated_eyetracking_v1_20250107_123456.csv       # 校准眼动数据
├── calibrated_eyetracking_v1_20250107_123456.xlsx     # Excel版本
├── roi_configs_v1_20250107_123456.json                # ROI配置(JSON)
├── roi_configs_v1_20250107_123456.csv                 # ROI配置(CSV)
├── subjects_with_mmse_v1_20250107_123456.csv          # 受试者+MMSE
├── export_all_v1_20250107_123456.zip                  # 统一打包
└── export_all_v1_20250107_123456/                     # 解压后内容
    ├── eyetracking_data.csv
    ├── roi_configs.json
    ├── subjects_mmse.csv
    └── export_metadata.json
```

## 🔧 API端点

### 后端API

| 端点 | 方法 | 功能 | 参数 |
|------|------|------|------|
| `/api/ex2/export/eyetracking` | POST | 导出眼动数据 | subject_ids, data_version, output_format |
| `/api/ex2/export/roi` | POST | 导出ROI配置 | data_version, output_format |
| `/api/ex2/export/subjects` | POST | 导出受试者+MMSE | data_version, include_mmse_details |
| `/api/ex2/export/all` | POST | 统一打包导出 | data_version, subject_ids |
| `/api/ex2/exports` | GET | 列出导出历史 | - |
| `/api/ex2/download/<filename>` | GET | 下载导出文件 | filename |
| `/api/ex2/health` | GET | 健康检查 | - |

### 前端路由

- **路径**: `/moduleEX2`
- **组件**: `frontend/src/pages/ModuleEX2/ModuleEX2.jsx`
- **菜单**: "ModuleEX2: 数据导出"

## 💾 数据格式

### 1. 校准眼动数据 (CSV)

```csv
subject_id,group,data_version,task_id,x,y,z,abs_datetime,milliseconds,...
sub_001,control,v1,task1,100.5,200.3,0,2025-01-07 12:34:56,1234,...
```

- **来源**: `data/02_processed/{group}/{subject_id}_task{n}_calibrated.csv`
- **元数据列**: subject_id, group, data_version, task_id (新增)
- **眼动列**: x, y, z, abs_datetime, milliseconds, velocity_deg_s等

### 2. ROI配置 (JSON)

```json
{
  "version": "v1",
  "task_id": "task1",
  "background_image": "task1.png",
  "regions": {
    "keywords": [...],
    "instructions": [...],
    "background": [...]
  },
  "last_modified": "2025-01-07T12:34:56"
}
```

### 3. 受试者+MMSE (CSV)

```csv
subject_id,group,data_version,birth_year,gender,education_level,mmse_total_score,mmse_test_date,q1_year,q1_season,...,q5_word3
sub_001,control,v1,1960,male,bachelor,21,2025-01-01,1,1,...,1
```

- **基础信息**: subject_id, group, data_version, birth_year等
- **MMSE总分**: mmse_total_score (0-21分)
- **MMSE明细**: 19个子题目 (可选)

### 4. 统一导出元数据 (JSON)

```json
{
  "export_time": "2025-01-07T12:34:56",
  "data_version": "v1",
  "module_version": "1.0.0",
  "exported_subjects": 60,
  "exported_tasks": 5,
  "files": {
    "eyetracking": "eyetracking_data.csv",
    "roi": "roi_configs.json",
    "subjects": "subjects_mmse.csv"
  }
}
```

## 📊 使用场景

### 场景1: 数据备份归档
**用途**: 定期备份处理后的数据
**操作**: 使用"统一打包导出" → 下载ZIP → 存档

### 场景2: 数据分享
**用途**: 与合作者分享研究数据
**操作**: 导出指定受试者 → 下载CSV → 发送

### 场景3: 外部分析
**用途**: 使用其他工具(SPSS, R, Python)分析
**操作**: 导出CSV格式 → 导入分析软件

### 场景4: 论文附件
**用途**: 准备论文补充材料
**操作**: 导出Excel/CSV → 整理格式 → 上传期刊

## 🔄 与其他模块的关系

```
Module00 (数据管理)
    ↓ 导入原始数据
Module01 (数据可视化)
    ↓ 校准眼动数据
Module02 (数据预处理)
    ↓ 生成受试者信息+MMSE
ModuleEX (ROI配置)
    ↓ 定义ROI区域
    ↓
ModuleEX2 (数据导出) ← 当前模块
    ↓ 固化到 data/06_results/exports/
    ↓
用户下载/外部分析
```

## 🚀 快速开始

### 后端启动

```bash
cd new_project
python run.py
# 后端运行在 http://127.0.0.1:9090
```

### 前端启动

```bash
cd new_project/frontend
npm run dev
# 前端运行在 http://localhost:5173
# 访问 http://localhost:5173/moduleEX2
```

### API测试

```bash
# 健康检查
curl http://127.0.0.1:9090/api/ex2/health

# 导出V1校准眼动数据
curl -X POST http://127.0.0.1:9090/api/ex2/export/eyetracking \
  -H "Content-Type: application/json" \
  -d '{"data_version": "v1", "output_format": "csv"}'

# 列出导出历史
curl http://127.0.0.1:9090/api/ex2/exports
```

## 📝 开发日志

### v1.0.0 (2025-01-07)
- ✅ 初始开发完成
- ✅ 后端API实现 (service.py 670行, api.py 290行)
- ✅ 前端组件实现 (6个组件)
- ✅ Pytest测试通过
- ✅ 架构优化：存储路径改为 `data/06_results/exports/`
- ✅ MMSE Q3计分修复 (3题1分)

## 🎯 未来计划

### 短期 (v1.1)
- [ ] 添加导出进度条
- [ ] 支持导出任务取消
- [ ] 增加导出文件预览

### 中期 (v1.2)
- [ ] 支持增量导出（只导出新数据）
- [ ] 添加导出模板自定义
- [ ] 集成数据压缩选项

### 长期 (v2.0)
- [ ] 云存储集成（S3, OSS）
- [ ] 自动定时导出
- [ ] 导出审计日志

## 📚 参考文档

- [项目概述](../../../README.md)
- [架构审查报告](../../../docs/ARCHITECTURE_REVIEW.md)
- [架构合规性报告](../../../docs/ARCHITECTURE_COMPLIANCE_REPORT.md)
- [MMSE评分规则](../../modules/module02_preprocessing/README.md)

## 👥 维护团队

**开发**: VR眼动数据分析系统开发团队
**版本**: 1.0.0
**最后更新**: 2025-01-07
