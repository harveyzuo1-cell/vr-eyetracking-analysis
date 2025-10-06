# Project Documentation / 项目文档

## 📚 Documentation Index / 文档索引

### 🎯 Quick Start / 快速开始
- [项目概述](../../项目概述.md) - Project Overview
- [项目迁移安装指南](../../项目迁移安装指南.md) - Installation Guide

### 📋 Coding Standards / 编码规范
- [**前端编码规范**](FRONTEND_CODING_STANDARDS.md) - Frontend Coding Standards
- [**后端编码规范**](BACKEND_CODING_STANDARDS.md) - Backend Coding Standards
- [**代码审查报告**](CODE_REVIEW_REPORT.md) - Code Review Report

### 🏗️ Architecture / 架构文档
- [架构审查](ARCHITECTURE_REVIEW.md) - Architecture Review
- [模块重组计划](MODULE_REORGANIZATION_PLAN.md) - Module Reorganization Plan
- [**国际化架构设计**](I18N_ARCHITECTURE_DESIGN.md) - i18n Architecture Design ⭐NEW
- [**国际化快速参考**](I18N_QUICK_REFERENCE.md) - i18n Quick Reference ⭐NEW
- [**测试架构文档**](TESTING_ARCHITECTURE.md) - Testing Architecture ⭐NEW

### 📝 Development Plans / 开发计划
- [Phase 1 开发计划](PHASE1_DEVELOPMENT_PLAN.md) - Phase 1 Development Plan
- [Phase 2 更新计划](PHASE2_PLAN_UPDATED.md) - Phase 2 Updated Plan
- [**任务扩展系统设计**](TASK_EXTENSION_DESIGN.md) - Task Extension System Design ⭐NEW
- [**任务扩展系统使用指南**](TASK_EXTENSION_README.md) - Task Extension README ⭐NEW
- [**Phase 2 迁移设计文档**](PHASE2_MIGRATION_DESIGN.md) - Phase 2 Migration Design ⭐NEW
- [**Pytest集成指南**](PYTEST_INTEGRATION_GUIDE.md) - Pytest Integration Guide ⭐NEW
- [Module 00 开发计划](MODULE00_DEVELOPMENT_PLAN.md) - Module 00 Development Plan
- [Module 01 开发计划](MODULE01_DEVELOPMENT_PLAN.md) - Module 01 Development Plan
- [**Module 01 数据校正功能设计**](MODULE01_CALIBRATION_FEATURE_DESIGN.md) - Module 01 Calibration Feature Design ⭐NEW
- [**Module 01 V2导入优化方案**](MODULE01_V2_IMPORT_OPTIMIZATION.md) - Module 01 V2 Import Optimization

### 🔧 Optimization Plans / 优化方案
- [**MetadataReader共享化重构方案**](OPTIMIZATION_METADATA_READER_REFACTOR.md) - MetadataReader Refactoring Plan ⭐NEW
- [**数据变更通知机制设计**](OPTIMIZATION_DATA_CHANGE_NOTIFICATION.md) - Data Change Notification Design ⭐NEW

### ✅ Progress Reports / 进度报告
- [Phase 1 完成报告](PHASE1_COMPLETE.md) - Phase 1 Complete
- [Phase 2 前端完成](PHASE2_FRONTEND_COMPLETE.md) - Phase 2 Frontend Complete
- [**Phase 2 任务扩展迁移完成**](PHASE2_MIGRATION_COMPLETE.md) - Phase 2 Task Extension Migration Complete ⭐NEW
- [Module 00 完成报告](MODULE00_COMPLETION_REPORT.md) - Module 00 Completion Report
- [Module 00 进度](MODULE00_PROGRESS.md) - Module 00 Progress
- [前端开发进度](FRONTEND_DEVELOPMENT_PROGRESS.md) - Frontend Development Progress
- [**MetadataReader重构完成报告**](REFACTOR_METADATA_READER_COMPLETION.md) - MetadataReader Refactoring Complete ⭐NEW

### 📚 Documentation Updates / 文档更新
- [文档整合](DOCUMENTATION_CONSOLIDATION.md) - Documentation Consolidation
- [文档更新](DOCUMENTATION_UPDATES.md) - Documentation Updates

### 🛠️ Troubleshooting / 问题排查
- [**问题排查指南**](TROUBLESHOOTING.md) - Troubleshooting Guide ⭐NEW

---

## 🔑 Key Standards / 核心规范

### Frontend Standards Highlights / 前端规范要点

#### 1. React列表Key规范
```javascript
// ❌ 错误：使用可能重复的业务ID
items.map(item => <Item key={item.subject_id} />)

// ✅ 正确：使用复合唯一key
items.map(item => (
  <Item key={`${item.source}_${item.id}_${item.timestamp || index}`} />
))
```

**为什么重要：**
- 避免React渲染错误
- 确保组件正确更新
- 防止数据混乱

**详细内容：** [FRONTEND_CODING_STANDARDS.md](FRONTEND_CODING_STANDARDS.md#react列表渲染规范)

#### 2. 组件设计规范
- 单一职责原则
- Props类型定义
- 使用useMemo优化
- 状态正确管理

**详细内容：** [FRONTEND_CODING_STANDARDS.md](FRONTEND_CODING_STANDARDS.md#组件设计规范)

#### 3. API集成规范
- 统一错误处理
- Loading状态管理
- 用户友好的反馈

**详细内容：** [FRONTEND_CODING_STANDARDS.md](FRONTEND_CODING_STANDARDS.md#api集成规范)

---

### Backend Standards Highlights / 后端规范要点

#### 1. 文件命名规范
```
src/web/modules/
├── module00_data_management/    # snake_case
│   ├── api.py                   # API路由
│   ├── service.py               # 业务逻辑
│   ├── converter.py             # 数据转换
│   └── validator.py             # 数据验证
```

**为什么重要：**
- 代码组织清晰
- 职责分离明确
- 易于维护扩展

**详细内容：** [BACKEND_CODING_STANDARDS.md](BACKEND_CODING_STANDARDS.md#文件命名规范)

#### 2. API响应格式
```python
# 成功响应
{
    "success": True,
    "data": { ... }
}

# 失败响应
{
    "success": False,
    "error": "错误描述"
}
```

**详细内容：** [BACKEND_CODING_STANDARDS.md](BACKEND_CODING_STANDARDS.md#api设计规范)

#### 3. 数据唯一性设计
```python
# 生成复合唯一ID
unique_id = f"{subject_id}_{timestamp}"
```

**详细内容：** [BACKEND_CODING_STANDARDS.md](BACKEND_CODING_STANDARDS.md#数据处理规范)

---

## 📖 Best Practices / 最佳实践

### 1. 数据唯一性问题

**问题场景：**
- Eye Tracking数据中hospital_id重复
- 导致subject_id重复
- React列表渲染错误

**解决方案：**
- **后端：** 生成unique_id字段（`${subject_id}_${timestamp}`）
- **前端：** 使用unique_id作为key
- **预防：** 代码审查检查列表渲染

**相关文档：**
- [Frontend - React列表渲染规范](FRONTEND_CODING_STANDARDS.md#react列表渲染规范)
- [Backend - 数据唯一标识设计](BACKEND_CODING_STANDARDS.md#数据唯一标识设计)

### 2. 多数据源合并

**最佳实践：**
```javascript
// 前端：使用source前缀区分数据源
const uniqueKey = `${source}_${businessId}_${timestamp}`;

// 后端：提供source字段
{
    "unique_id": "eyetrack_control_01_2025-3-27-11-37-22",
    "source": "eye_tracking",
    "subject_id": "control_01"
}
```

### 3. 错误处理

**前端：**
- 所有API调用try-catch
- 显示具体错误信息
- Loading状态管理

**后端：**
- 异常分类处理
- 返回清晰错误描述
- 记录详细日志

---

## 🔍 Code Review Checklist / 代码审查清单

### Frontend Checklist / 前端检查清单

- [ ] **列表渲染**
  - [ ] 所有.map()使用key
  - [ ] Key在列表中唯一
  - [ ] 未使用索引作为动态列表key

- [ ] **组件设计**
  - [ ] 组件职责单一
  - [ ] Props有类型定义
  - [ ] 使用useMemo优化

- [ ] **API集成**
  - [ ] 所有API调用有错误处理
  - [ ] Loading状态正确管理
  - [ ] 用户操作有反馈

### Backend Checklist / 后端检查清单

- [ ] **文件组织**
  - [ ] 使用snake_case命名
  - [ ] 模块结构符合标准
  - [ ] API/Service分离

- [ ] **API设计**
  - [ ] 统一响应格式
  - [ ] RESTful风格路由
  - [ ] 所有端点有文档

- [ ] **数据处理**
  - [ ] 必填字段验证
  - [ ] 空值处理
  - [ ] 生成唯一标识符

---

## 📚 Learning Resources / 学习资源

### 实际案例分析

1. **Module00 SubjectList Key重复问题**
   - 问题：subject_id重复导致React警告
   - 原因：多个受试者使用相同hospital_id
   - 解决：使用timestamp生成唯一key
   - 学习：[Frontend Standards Case 1](FRONTEND_CODING_STANDARDS.md#case-1-module00-subjectlist-key重复问题)

2. **Module00 数据扫描API设计**
   - 问题：需要扫描两个数据源
   - 解决：分离扫描逻辑，统一数据格式
   - 学习：[Backend Standards Case 1](BACKEND_CODING_STANDARDS.md#case-1-module00-数据扫描api设计)

---

## 🚀 Quick Links / 快速链接

- **新手入门：** 先读 [前端编码规范](FRONTEND_CODING_STANDARDS.md) 和 [后端编码规范](BACKEND_CODING_STANDARDS.md)
- **代码审查：** 使用 [代码审查检查点](#code-review-checklist--代码审查清单)
- **问题排查：** 查看 [最佳实践](#best-practices--最佳实践)
- **架构理解：** 阅读 [架构审查](ARCHITECTURE_REVIEW.md)

---

## 📝 Document Maintenance / 文档维护

### 更新日志

| 日期 | 文档 | 更新内容 |
|------|------|---------|
| 2025-10-02 | REFACTOR_METADATA_READER_COMPLETION.md | MetadataReader重构完成报告，Module01减少217行代码 ⭐NEW |
| 2025-10-02 | OPTIMIZATION_METADATA_READER_REFACTOR.md | MetadataReader共享化重构方案设计 ⭐NEW |
| 2025-10-02 | OPTIMIZATION_DATA_CHANGE_NOTIFICATION.md | 数据变更通知机制设计方案 ⭐NEW |
| 2025-10-02 | MODULE01_V2_IMPORT_OPTIMIZATION.md | 创建V2数据导入优化方案，解决hospital_id缺失问题 |
| 2025-10-02 | FRONTEND_CODING_STANDARDS.md | 创建前端编码规范，包含React列表渲染规范 |
| 2025-10-02 | BACKEND_CODING_STANDARDS.md | 创建后端编码规范，包含文件命名和API设计规范 |
| 2025-10-02 | README.md | 创建文档索引和快速参考 |

### 维护责任

- **Frontend Standards:** Frontend Team
- **Backend Standards:** Backend Team
- **Documentation Index:** Tech Lead

### 贡献指南

发现规范问题或有改进建议？
1. 提交Issue描述问题
2. 提供具体案例
3. 建议改进方案

---

**最后更新：** 2025-10-02
**维护团队：** VR Eye Tracking Analysis Platform Team
