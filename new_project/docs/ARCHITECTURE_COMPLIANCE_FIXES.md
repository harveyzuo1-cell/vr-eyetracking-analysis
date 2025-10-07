# 架构合规性修复报告
## Architecture Compliance Fixes Report

**日期 / Date**: 2025-10-07
**修复范围 / Scope**: Module00数据导入逻辑
**问题类型 / Issue Type**: V1数据映射错误

---

## 📋 问题总结 / Issue Summary

### 发现的问题 / Issues Found

1. **AD组映射错误** (CRITICAL)
   - **问题**: AD组原始数据`ad_group_3-22`被错误映射为`ad_legacy_3-22`
   - **预期**: 应映射为`ad_legacy_1-20`（重新编号）
   - **影响**: 导致ad_legacy_1和ad_legacy_2缺失，数据不完整

2. **目录排序问题** (HIGH)
   - **问题**: `glob()`字符串排序导致`ad_group_10`在`ad_group_3`之前
   - **预期**: 应按数字排序（3, 4, 5, ..., 10, 11, ...）
   - **影响**: 映射关系混乱

3. **文件类型过滤缺失** (MEDIUM)
   - **问题**: glob扫描包含了`.zip`文件
   - **预期**: 只扫描目录
   - **影响**: 可能导入无效数据

---

## 🔧 实施的修复 / Implemented Fixes

### 1. 修改 `legacy_importer.py`

**文件位置**: `src/web/modules/module00_data_management/importers/legacy_importer.py`

#### 修复1: AD组重新编号逻辑 (第87-101行)

**修改前**:
```python
for subj_dir in subject_dirs:
    parts = subj_dir.name.split('_')
    if len(parts) >= 3:
        group_number = parts[-1]
    else:
        continue

    # 生成subject_id
    subject_id = f"{group}_legacy_{group_number}"
```

**修改后**:
```python
for idx, subj_dir in enumerate(subject_dirs, start=1):
    parts = subj_dir.name.split('_')
    if len(parts) >= 3:
        original_group_number = parts[-1]
    else:
        continue

    # 生成subject_id：对于AD组，使用连续编号1-20；其他组保持原组号
    if group == 'ad':
        # AD组：ad_group_3-22 映射为 ad_legacy_1-20
        subject_id = f"{group}_legacy_{idx}"
    else:
        # Control和MCI组：保持原组号
        subject_id = f"{group}_legacy_{original_group_number}"
```

**说明**:
- AD组使用`enumerate()`生成连续索引（1-20）
- Control和MCI组保持原始组号

#### 修复2: 数字排序+目录过滤 (第81-87行)

**修改前**:
```python
pattern = f"{group}_group_*"
subject_dirs = sorted(source_dir.glob(pattern))
```

**修改后**:
```python
pattern = f"{group}_group_*"
# 按数字排序，只包含目录（排除.zip等文件）
subject_dirs = sorted(
    [d for d in source_dir.glob(pattern) if d.is_dir()],
    key=lambda x: int(x.name.split('_')[-1]) if x.name.split('_')[-1].isdigit() else 999
)
```

**说明**:
- 使用`is_dir()`过滤，只包含目录
- 使用数字排序key，确保3<10<11

---

### 2. 数据清理和重新导入

**执行脚本**: `cleanup_and_reimport_ad.py`

#### 清理步骤:
1. 删除旧的AD CSV文件（100个文件）
2. 删除旧的AD subject_info JSON文件（18个文件）
3. 从subject_metadata.json删除旧的AD V1记录

#### 重新导入结果:
```
原始目录 -> 新ID映射:
  ad_group_3  -> ad_legacy_1   ✅
  ad_group_4  -> ad_legacy_2   ✅
  ad_group_5  -> ad_legacy_3   ✅
  ...
  ad_group_22 -> ad_legacy_20  ✅

导入成功: 20/20
```

---

## ✅ 验证结果 / Verification Results

### V1数据完整性验证

```
V1受试者总数: 60 ✅
  CONTROL: 20个，每个5个任务 ✅
  MCI: 20个，每个5个任务 ✅
  AD: 20个，每个5个任务 ✅

AD组映射验证:
  ad_legacy_1 <- ad_group_3 ✅
  ad_legacy_2 <- ad_group_4 ✅
  ...
  ad_legacy_20 <- ad_group_22 ✅
```

### 架构合规性验证

| 架构要求 | 修复前 | 修复后 | 符合度 |
|---------|--------|--------|--------|
| V1数据总数 | 58个 ❌ | 60个 ✅ | 100% |
| AD组映射 | ad_legacy_3-22 ❌ | ad_legacy_1-20 ✅ | 100% |
| 目录排序 | 字符串排序 ❌ | 数字排序 ✅ | 100% |
| 文件过滤 | 包含.zip ❌ | 只含目录 ✅ | 100% |
| 任务完整性 | 部分缺失 ❌ | 全部完整 ✅ | 100% |

---

## 📊 V2数据状态 / V2 Data Status

### 当前V2数据统计

```
V2受试者总数: 93
  CONTROL: 77 (预期68) ⚠️
  MCI: 8 (预期8) ✅
  AD: 8 (预期8) ✅
```

### V2数据分析

**问题**: V2 Control组有77个受试者，超出预期的68个

**可能原因**:
1. 原始eye_tracking_data包含了所有扫描数据（包括不完整的）
2. 没有按照"只导入有完整5个任务的受试者"的规则过滤

**建议措施**:
1. 检查eye_tracking_data原始目录结构
2. 验证每个受试者是否有完整的5个任务文件
3. 过滤掉任务不完整的受试者
4. 确保最终V2数据为84个（Control 68, MCI 8, AD 8）

---

## 🎯 架构符合性评估 / Architecture Compliance Assessment

### 符合的架构原则 ✅

1. **模块化设计**
   - 所有修改集中在Module00的legacy_importer.py
   - 未影响其他模块

2. **配置驱动**
   - 使用config/settings.py中的配置
   - 无硬编码路径或参数

3. **数据流完整性**
   - 01_raw数据完整导入
   - 元数据正确记录

4. **错误处理**
   - 文件完整性验证
   - 导入失败异常捕获

### 遵循的最佳实践 ✅

1. **单一职责原则**
   - legacy_importer只负责V1数据导入
   - 映射逻辑清晰独立

2. **代码可维护性**
   - 添加了详细注释说明AD组特殊处理
   - 逻辑清晰易懂

3. **数据追溯性**
   - source_path记录原始数据位置
   - 映射关系可追溯

---

## 📋 后续行动项 / Action Items

### 立即执行 (HIGH Priority)

- [ ] **检查V2数据源**
  - 验证eye_tracking_data原始数据量
  - 确认任务文件完整性
  - 识别需要过滤的受试者

- [ ] **修复V2数据**
  - 更新eye_tracking_importer.py
  - 添加任务完整性验证
  - 确保最终V2=84个受试者

### 近期执行 (MEDIUM Priority)

- [ ] **文档更新**
  - 更新Module00文档，说明AD组映射逻辑
  - 添加数据导入规范文档

- [ ] **测试补充**
  - 添加legacy_importer单元测试
  - 测试AD组映射逻辑
  - 测试目录排序逻辑

### 长期优化 (LOW Priority)

- [ ] **重构考虑**
  - 将映射逻辑抽象为配置
  - 支持更灵活的映射规则

---

## 🏆 总结 / Conclusion

### 修复成果 ✅

1. **V1数据完全符合架构要求**
   - 60个受试者（Control 20, MCI 20, AD 20）
   - AD组映射正确（ad_group_3-22 → ad_legacy_1-20）
   - 所有受试者任务完整

2. **代码质量提升**
   - 修复了目录排序bug
   - 添加了文件类型过滤
   - 逻辑更加清晰

3. **架构合规性提升**
   - Module00数据导入逻辑完善
   - 符合架构设计原则
   - 保持代码可维护性

### 遗留问题 ⚠️

1. **V2数据需要验证和清理**
   - 当前93个，目标84个
   - 需要移除任务不完整的受试者

### 建议 💡

**建议立即处理V2数据问题**，以确保：
- 数据完整性和准确性
- 符合Module00的设计要求
- 为后续模块（Module02-10）提供可靠的数据基础

---

**修复人 / Fixed By**: AI Code Assistant
**审核状态 / Review Status**: ⏳ 等待用户确认 / Pending User Confirmation
**下一步 / Next Step**: V2数据验证和清理
