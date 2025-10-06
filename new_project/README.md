# VR眼球追踪数据分析平台 - 重构项目

## 📚 文档索引

本目录包含了完整的项目重构方案文档：

### 1. [REFACTOR_PLAN.md](./REFACTOR_PLAN.md) - 重构方案总览
**必读文档！** 包含：
- ❌ 现有项目的主要问题分析
- ✅ 新项目的目录结构设计
- 📝 数据文件命名规范
- 🔧 代码组织原则
- 🚀 分阶段迁移策略
- 📊 预期改进效果对比

**关键发现**:
- 主HTML文件 **19,504行** → 重构后 **~500行** (减少97%)
- Python文件最大 **2,577行** → 重构后 **~300行** (减少88%)

---

### 2. [MODULES_INVENTORY.md](./MODULES_INVENTORY.md) - 模块功能清单
**详细分析文档！** 包含：
- 📋 模块1-10的完整功能清单
- 📂 每个模块的当前实现位置
- 🔄 数据流向和依赖关系
- 💡 具体的重构建议
- ⚠️ 技术债务清单

**每个模块包含**:
- 核心功能描述
- 当前代码位置
- 数据输入/输出
- API端点列表
- 重构后的文件拆分建议

---

## 🎯 重构的核心目标

### 问题 → 解决方案

| 现有问题 | 重构解决方案 |
|---------|-------------|
| 单文件近2万行代码 | 拆分为独立模块，每个文件<300行 |
| 数据命名混乱 | 统一命名规范 `<group>_<subject>_<task>.csv` |
| 前后端耦合 | 完全分离，独立API层 |
| 配置硬编码 | 集中配置管理 `config/` |
| 无数据版本管理 | 按阶段组织数据目录 `data/01_raw/` ~ `06_results/` |
| 维护困难、Bug多 | 模块化、单元测试、清晰文档 |

---

## 📊 项目现状分析

### 代码规模统计
```
可视化主页面:  19,504 行  (visualization/templates/enhanced_index.html)
后端主文件:     2,577 行  (visualization/enhanced_web_visualizer.py)
RQA批处理:      2,017 行  (visualization/rqa_pipeline_api.py)
ML预测API:      2,021 行  (visualization/ml_prediction_api.py)
```

### 数据组织现状
```
data/
├── control_raw/          # 原始数据
├── control_processed/    # 预处理数据
├── control_calibrated/   # 校准数据
├── mci_raw/
├── mci_processed/
├── mci_calibrated/
├── ad_raw/
├── ad_processed/
├── ad_calibrated/
├── MMSE_Score/           # MMSE评分（3个中文文件）
├── rqa_results/          # RQA结果
├── event_analysis_results/
├── module7_integrated_results/
├── module8_analysis_results/
├── module9_ml_results/
├── module10_datasets/
└── ...（更多）
```

**问题**: 目录分散、命名不统一、难以追踪数据流

---

## 🏗️ 新项目架构

### 目录结构（简化版）
```
new_project/
├── config/              # 配置管理
├── data/                # 数据（按流程阶段组织）
│   ├── 01_raw/
│   ├── 02_preprocessed/
│   ├── 03_calibrated/
│   ├── 04_features/
│   ├── 05_models/
│   └── 06_results/
├── src/
│   ├── core/            # 核心工具
│   ├── modules/         # 10个功能模块
│   │   ├── module01_visualization/
│   │   ├── module02_data_import/
│   │   ├── module03_rqa_analysis/
│   │   ├── ...
│   │   └── module10_eye_index/
│   ├── web/             # Flask应用
│   └── utils/           # 工具函数
├── tests/               # 测试代码
├── docs/                # 文档
└── scripts/             # 脚本工具
```

### 模块结构（标准模板）
```python
src/modules/module0X_xxx/
├── __init__.py
├── api.py              # API路由 (~100行)
├── service.py          # 业务逻辑 (~200行)
├── [specific].py       # 特定功能 (~200行)
└── static/
    └── moduleX.html    # 前端页面 (~300行)
```

---

## 📋 数据命名规范

### 原始数据
```
格式: <group>_<subject_id>_<task_id>.csv

示例:
- control_s001_q1.csv   # 对照组，受试者001，任务Q1
- mci_s042_q3.csv       # MCI组，受试者042，任务Q3
- ad_s015_q5.csv        # AD组，受试者015，任务Q5
```

### 处理后数据
```
格式: <group>_<subject_id>_<task_id>_<stage>.csv

示例:
- control_s001_q1_preprocessed.csv
- mci_s042_q3_calibrated.csv
```

### MMSE临床数据
```
统一文件: data/01_raw/clinical/mmse_scores.csv

格式:
subject_id,group,q1_score,q1_max,q2_score,q2_max,...,total_score
s001,control,5,5,4,5,3,3,5,5,3,3,20
s042,mci,4,5,3,5,2,3,3,5,1,3,16
s015,ad,3,5,2,5,1,3,2,5,0,3,11
```

---

## 🚀 迁移计划

### 第1阶段: 基础架构（1周）✅ **已完成**
- [x] 创建新项目目录
- [x] 编写重构方案文档
- [x] 编写模块清单文档
- [x] 创建配置文件系统 (288行)
- [x] 实现核心工具类 (865行)
- [x] 搭建Flask应用骨架 (211行 + 模板)
- [x] 应用启动测试通过

**成果**: 23个文件，~2,400行代码，完整的基础架构

### 第2阶段: 数据迁移（1周）
- [ ] 重组数据目录结构
- [ ] 统一MMSE数据格式
- [ ] 编写数据迁移脚本
- [ ] 数据完整性验证

### 第3阶段: 模块迁移（4周）
**优先级顺序**:
1. Module 1 (可视化) - 最基础
2. Module 8 (MMSE) - 数据支持
3. Module 2 (数据导入) - 数据入口
4. Module 3 (RQA分析)
5. Module 4 (事件分析)
6. Module 5 (RQA批处理) - 含GPU优化
7. Module 6 (特征提取)
8. Module 7 (数据整合)
9. Module 9 (机器学习)
10. Module 10 (Eye-Index)

### 第4阶段: 测试优化（1周）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档完善

---

## 💡 重构原则

### 代码组织
1. **单一职责**: 每个文件只负责一件事
2. **行数限制**:
   - Python文件 < 300行
   - HTML文件 < 500行
   - 函数 < 50行
3. **模块独立**: 模块间通过API通信
4. **配置外部化**: 无硬编码路径

### 数据管理
1. **阶段化存储**: 按处理阶段组织
2. **统一命名**: 严格遵循命名规范
3. **版本控制**: 结果包含元数据
4. **只读原则**: 原始数据不可修改

### 开发规范
1. **测试先行**: 每个功能必有测试
2. **文档同步**: 代码与文档同步更新
3. **渐进式迁移**: 新旧系统并行
4. **向后兼容**: 提供迁移脚本

---

## 📈 预期收益

### 开发效率
- ✅ 新功能开发时间减少 **50%**
- ✅ Bug定位时间减少 **70%**
- ✅ 代码审查效率提升 **3倍**

### 维护性
- ✅ 代码可读性: 差 → 优秀
- ✅ 模块复用性: 低 → 高
- ✅ 团队协作: 困难 → 顺畅

### 稳定性
- ✅ Bug数量减少 **60%**
- ✅ 测试覆盖率: 0% → 80%
- ✅ 系统可靠性大幅提升

---

## 🔄 下一步行动

### 立即开始
1. ✅ 阅读 [REFACTOR_PLAN.md](./REFACTOR_PLAN.md)
2. ✅ 阅读 [MODULES_INVENTORY.md](./MODULES_INVENTORY.md)
3. ⬜ 讨论并确认重构方案
4. ⬜ 开始第1阶段: 基础架构搭建

### 本周目标
- [ ] 完成配置系统
- [ ] 完成核心工具类
- [ ] 完成数据迁移脚本
- [ ] 开始模块1重构

---

## 📞 联系与反馈

如有任何问题或建议，请：
1. 查看相关文档
2. 提出具体问题
3. 讨论解决方案

**记住**:
> 重构不是推倒重来，而是**渐进式改进**。我们将保持旧系统运行，同步逐模块迁移到新架构。

---

**创建日期**: 2025-10-01
**最后更新**: 2025-10-01
**状态**: ✅ 第1阶段完成，进入第2阶段

---

## 📖 详细文档

- [PHASE1_COMPLETE.md](./docs/PHASE1_COMPLETE.md) - 第1阶段完成报告（包含代码统计、使用示例、测试指南）
