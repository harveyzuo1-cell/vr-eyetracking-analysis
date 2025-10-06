# Module01 V2数据导入优化方案

## 📊 当前问题诊断

### 一、实际vs预期对比

| 项目 | 实际导入 | 用户预期 | 差异 |
|------|---------|---------|------|
| **总受试者** | 13人 | 84人 | -71人 |
| Control | 16人* | 68人 | -52人 |
| MCI | 6人 | 8人 | -2人 |
| AD | 6人 | 8人 | -2人 |
| **总任务数** | 64 tasks | ~420 tasks | -356 tasks |

*注: 实际导入的16人包含了custom/帅哥等测试数据,规范化后应归为Control组

### 二、根本原因分析

#### 🔍 问题1: 误判为"hospital_id缺失则跳过"
**当前逻辑问题:**
```python
# eye_tracking_v2_importer.py (当前)
if not raw_group or not hospital_id:
    skipped += 1
    continue  # ❌ 直接跳过!
```

**实际情况:**
- data_index.json中94个sessions
- **60个有group+hospital_id** → 被导入
- **17个有group但无hospital_id** → 被跳过 ❌
- 17个无group → 正确跳过

**被跳过的17个sessions详情:**
- MCI: 3个 (全部5 levels完整)
- Control(对照组): 12个
- AD(阿尔兹海默): 1个
- custom: 1个
- **其中13个是完整数据(5 levels)**

#### 🔍 问题2: Subject ID生成策略错误
**当前策略:**
```python
subject_id = f"{group}_v2_{hospital_id}"  # ❌ hospital_id缺失则无法生成
```

**问题:**
1. 依赖hospital_id,导致17个sessions无法生成subject_id
2. hospital_id可能重复(不同受试者用了相同ID)
3. 无法区分真正的不同受试者

#### 🔍 问题3: 数据源不完整检查
- data_index.json: 94个sessions
- 实际目录: 101个
- **缺失7个未被索引的sessions**

### 三、数据完整性核查

#### ✅ 可导入数据统计
| 数据源 | Sessions | 状态 |
|--------|----------|------|
| 已导入 | 60 | ✅ 有group+hospital_id |
| 可新增 | 17 | ✅ 有group, 无hospital_id |
| 未索引 | 7 | ❓ 需检查(部分有完整数据) |
| 无group | 17 | ❌ 无法确定分组 |
| **总计** | **101** | **77可用** |

#### 预期可达到的导入量
- **当前**: 60 sessions → 13 subjects (误判重复)
- **修复后**: 77 sessions → **77 subjects** (使用timestamp唯一标识)
- 与预期84人相比,仍差7人(可能在未索引的7个sessions中)

---

## 🎯 完整解决方案

### 方案一: 使用Timestamp作为唯一标识 (推荐)

#### 1. Subject ID生成策略优化
```python
def _generate_subject_id(self, group: str, hospital_id: Optional[str], timestamp: str) -> str:
    """
    生成唯一Subject ID

    优先级:
    1. 如果有hospital_id: {group}_v2_{hospital_id}
    2. 如果无hospital_id: {group}_v2_{timestamp_hash}

    Args:
        group: 组名(control/mci/ad)
        hospital_id: 医院ID(可选)
        timestamp: session时间戳(必有)

    Returns:
        唯一subject_id
    """
    if hospital_id and hospital_id not in ['unknown', '', 'nan']:
        # 有hospital_id,使用它
        return f"{group}_v2_{hospital_id}"
    else:
        # 无hospital_id,使用timestamp的短hash (避免ID过长)
        import hashlib
        ts_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"{group}_v2_{ts_hash}"
```

**优点:**
- 每个session都能生成唯一ID
- 不会因缺少hospital_id而跳过数据
- 避免误判为重复受试者

#### 2. 导入逻辑优化
```python
def load_v2_data(self) -> Dict[str, Dict]:
    # 修改跳过条件
    for session_timestamp, session_data in data_index.items():
        raw_group = session_data.get('group')
        hospital_id = session_data.get('hospital_id')  # 可以为None

        # ❌ 旧逻辑: if not raw_group or not hospital_id: skip

        # ✅ 新逻辑: 只要有group就处理
        if not raw_group:
            skipped += 1
            continue

        # Normalize group
        group = self._normalize_group_name(raw_group)
        if not group:
            skipped += 1
            continue

        # 生成subject_id (hospital_id可选)
        subject_id = self._generate_subject_id(group, hospital_id, session_timestamp)

        # ... 继续处理
```

### 方案二: 扫描式导入(处理未索引sessions)

#### 1. 直接扫描目录,不依赖data_index.json
```python
def scan_directory_import(self):
    """
    扫描eye_tracking_data目录,导入所有可用数据
    不依赖data_index.json
    """
    for session_dir in self.v2_data_dir.iterdir():
        if not session_dir.is_dir():
            continue

        timestamp = session_dir.name

        # 方法1: 从json文件提取metadata
        score_files = list(session_dir.glob('*_score.json'))
        if score_files:
            with open(score_files[0]) as f:
                metadata = json.load(f)
                group = metadata.get('group')
                hospital_id = metadata.get('hospital_id')

        # 方法2: 从文件名/内容推断
        # ...
```

**优点:**
- 可发现data_index遗漏的7个sessions
- 直接从源文件读取,更可靠

---

## 📝 实施步骤

### 阶段1: 立即修复(优先)
1. ✅ 修改`_generate_subject_id()`支持无hospital_id情况
2. ✅ 修改导入条件: `if not group: skip` (移除hospital_id检查)
3. ✅ 重新导入测试

**预期结果:**
- 从13人 → **77人** (60+17)
- MCI: 6→9人 (新增3人)
- Control: 16→28人 (新增12人)
- AD: 6→7人 (新增1人)

### 阶段2: 完善数据源
1. ⏳ 实现扫描式导入(处理未索引的7个sessions)
2. ⏳ 分析无group的17个sessions(手动标注或放弃)
3. ⏳ 验证是否达到84人目标

### 阶段3: 架构优化
1. ⏳ 添加数据版本管理(ROI layout v1 vs v2)
2. ⏳ 统一metadata结构
3. ⏳ 更新Module01前端显示逻辑

---

## 🔧 代码修改清单

### 文件1: `eye_tracking_v2_importer.py`
**修改位置1:** `_convert_subject_id()` → 改名为`_generate_subject_id()`
```python
def _generate_subject_id(self, group: str, hospital_id: Optional[str], timestamp: str) -> str:
    """支持无hospital_id的情况"""
    if hospital_id and hospital_id not in ['unknown', '', 'nan']:
        return f"{group}_v2_{hospital_id}"
    else:
        import hashlib
        ts_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"{group}_v2_{ts_hash}"
```

**修改位置2:** `load_v2_data()` 跳过条件
```python
# 第275行附近
# OLD: if not raw_group or not hospital_id: skipped += 1; continue
# NEW:
if not raw_group:
    skipped += 1
    continue

group = self._normalize_group_name(raw_group)
if not group:
    skipped += 1
    continue

# 使用新方法生成subject_id
subject_id = self._generate_subject_id(group, hospital_id, session_timestamp)
```

### 文件2: `api.py` (Module00)
**无需修改** - API层自动适配新的subject_id生成逻辑

---

## 📈 预期改进效果

### 导入量对比
| 指标 | 修复前 | 修复后(阶段1) | 目标(阶段2) |
|------|--------|--------------|------------|
| 总受试者 | 13 | **77** | 84 |
| Control | 16 | **28** | 68 |
| MCI | 6 | **9** | 8 |
| AD | 6 | **7** | 8 |
| 总任务数 | 64 | **~385** | ~420 |

### MCI组任务缺失修复
- 当前: `mci_v2_01055282` 缺q5
- 修复: 新增3个完整MCI受试者(5 tasks)
- 结果: MCI组从29 tasks → **44 tasks** (9人×5任务-1缺失)

---

## 🏗️ 架构优化建议

### 1. Subject ID规范化
**现状问题:**
- v1: `control_legacy_1` (基于原始文件名)
- v2: `control_v2_000002` (基于hospital_id,不可靠)

**优化方案:**
```
v1: {group}_legacy_{number}      # 不变
v2_有ID: {group}_v2_{hospital_id}  # 保留
v2_无ID: {group}_v2_{ts_hash}     # 新增
```

### 2. Metadata结构扩展
```json
{
  "subject_id": "control_v2_a3f9d2e1",
  "group": "control",
  "data_version": "v2",
  "raw_identifier": "a3f9d2e1",  // timestamp hash
  "original_timestamp": "2025-3-27-11-37-22",
  "has_hospital_id": false,
  "id_source": "timestamp_hash"  // 标识ID来源
}
```

### 3. Module01可视化优化
**前端显示:**
- 添加"ID来源"标签: `[医院ID]` vs `[时间戳]`
- 区分不同ID类型,避免用户误解
- 提供原始timestamp信息供追溯

---

## ✅ 验收标准

### 阶段1完成标准:
- [ ] 导入受试者数: ≥77人
- [ ] MCI组: ≥9人
- [ ] 无因hospital_id缺失而跳过的sessions
- [ ] 所有subject_id唯一且可追溯

### 阶段2完成标准:
- [ ] 导入受试者数: 达到或接近84人
- [ ] 处理完所有未索引sessions
- [ ] 文档化无法导入的数据原因

### 最终验收:
- [ ] 数据完整性: 与Module00统计一致
- [ ] ID唯一性: 无重复subject_id
- [ ] 可追溯性: 每个subject能追溯到原始session
- [ ] 前端展示: 正确显示所有v2数据

---

## 📌 风险与注意事项

### 风险1: Timestamp Hash冲突
- **概率**: 极低(MD5前8位,>40亿组合)
- **缓解**: 添加冲突检测,发生时使用timestamp全文

### 风险2: 与已导入数据的兼容性
- **问题**: 已导入13人可能ID会变化
- **解决**:
  - 选项A: 清空重新导入
  - 选项B: 只导入新数据(增量)

### 风险3: 未索引sessions的group识别
- **问题**: 7个未索引sessions可能无group信息
- **解决**: 手动检查json文件,或根据文件结构推断

---

**文档版本**: v1.0
**创建日期**: 2025-10-02
**作者**: Claude Code
**状态**: 待实施
