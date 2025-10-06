# Module02 V2数据管理优化 - 开发进度报告

## 📅 更新时间
2025-10-06

## ✅ 已完成功能 (4/11 - 36%)

### 1. ✅ V1数据管理器 (`v1_data_manager.py`)

**文件**: `new_project/src/modules/module02_preprocessing/v1_data_manager.py` (226行)

**核心功能**:
- ✅ `scan_v1_subjects()` - 扫描V1目录，支持control/mci/ad分组
- ✅ `import_v1_subject()` - 导入单个V1受试者
- ✅ `batch_import_v1_subjects()` - 批量导入V1受试者
- ✅ `get_v1_subject_detail()` - 获取V1受试者详情（含文件列表）
- ✅ `_read_v1_metadata()` - 读取V1元数据（metadata.json）
- ✅ `_get_earliest_file_time()` - 获取最早文件时间作为timestamp

**目录结构支持**:
```
v1_raw_data/
├── control/
│   ├── control_001/
│   │   ├── task_data.txt
│   │   └── metadata.json
│   └── control_002/
├── mci/
└── ad/
```

---

### 2. ✅ V2数据管理器 (`v2_data_manager.py`)

**文件**: `new_project/src/modules/module02_preprocessing/v2_data_manager.py` (354行)

**核心功能**:
- ✅ `normalize_v2_subject_ids()` - **ID规范化核心逻辑**
  - 格式: `v2_{group}_{序号}` (如 `v2_control_001`)
  - 智能序号分配: 查找当前最大序号+1，避免冲突
  - 支持预览模式(`preview_only=True`)

- ✅ `batch_import_v2_subjects()` - 批量导入V2受试者
  - 支持ID规范化选项(`rename=True/False`)
  - 试运行模式(`dry_run=True`)仅返回ID映射
  - 返回详细导入结果和ID映射表

- ✅ `scan_v2_subjects_from_directory()` - 扫描V2目录
  - 读取info.json获取受试者信息
  - 支持自定义扫描目录

- ✅ `get_id_mapping_by_original_id()` - 通过原始ID查找新ID

- ✅ `migrate_existing_v2_ids()` - 迁移已有数据到规范格式
  - 重命名文件
  - 保留original_id在metadata中
  - 更新索引

**ID规范化示例**:
```python
# 输入: N_01, N_02, M_03, A_01
# 输出:
{
  'N_01': 'v2_control_001',
  'N_02': 'v2_control_002',
  'M_03': 'v2_mci_001',
  'A_01': 'v2_ad_001'
}
```

---

### 3. ✅ SubjectManager扩展

**文件**: `new_project/src/modules/module02_preprocessing/subject_manager.py` (修改)

**新增功能**:
- ✅ `get_all_subjects(data_version='v1'|'v2'|None)` - 按版本筛选
- ✅ `create_subject(data_version='v1'|'v2', metadata={})` - 支持版本和元数据
- ✅ 返回结果包含`metadata`字段（timestamp、data_path等）

**代码变更**:
```python
# 新增参数
def get_all_subjects(
    self,
    group: Optional[str] = None,
    with_mmse: bool = False,
    data_version: Optional[str] = None  # 新增
) -> List[Dict]:
    # ...
    # 版本筛选
    if data_version:
        subjects = [s for s in subjects if s.get('data_version') == data_version]
    return subjects

# 新增参数
def create_subject(
    self,
    subject_id: str,
    group: str,
    demographics: Dict,
    mmse: Optional[Dict] = None,
    data_version: str = 'v1',  # 新增
    metadata: Optional[Dict] = None  # 新增
) -> Dict:
    subject_data = {
        # ...
        'data_version': data_version,
        'metadata': metadata or {}
    }
```

---

### 4. ✅ MMSEManager优化

**文件**: `new_project/src/modules/module02_preprocessing/mmse_manager.py` (新增180行)

**新增功能**:
- ✅ `generate_batch_import_template()` - **自动填充V2数据的模板生成**
  - 包含已导入V2受试者的所有信息
  - 支持按`data_version`筛选
  - 自动填充: subject_id, group, name, hospital_id, age, gender, education_level, timestamp
  - 已有MMSE数据也自动填充
  - 返回Excel兼容的CSV(UTF-8 BOM)

- ✅ `batch_import_clinical_data()` - **批量导入MMSE数据**
  - 支持更新已有受试者（demographics + mmse）
  - subject_id和timestamp不可修改
  - 自动计算total_score
  - 详细错误报告（行号、受试者ID、错误原因）

**CSV模板格式**:
```csv
subject_id,group,name,hospital_id,age,gender,education_level,timestamp,q1_year,q1_season,q1_month,q1_weekday,q2_province,q2_floor,q3_immediate
v2_control_001,control,张三,H001,65,male,undergraduate,2024-01-01 10:30:00,1,1,1,2,2,1,3
v2_mci_001,mci,李四,H002,70,female,senior_high,2024-01-02 11:00:00,,,,,,,
```

**导入结果示例**:
```python
{
  'updated': 10,
  'skipped': 0,
  'errors': [
    {
      'row': 5,
      'subject_id': 'invalid_id',
      'error': '受试者不存在，请先导入V2数据'
    }
  ]
}
```

---

## 🔄 进行中任务 (1/11 - 9%)

### 5. ⏳ 添加V1/V2数据管理API接口

**计划**:
- `GET /api/m02/v1/subjects` - 获取V1受试者列表
- `POST /api/m02/v1/import` - 导入V1受试者
- `POST /api/m02/v2/batch-import` - 批量导入V2受试者(含ID规范化)
- `POST /api/m02/v2/normalize-preview` - 预览ID规范化映射
- `POST /api/m02/mmse/submit` - 提交MMSE数据(含人口学信息)
- `GET /api/m02/mmse/template?include_v2=true&version=v2` - 生成MMSE模板

---

## ⏸️ 待开发任务 (6/11 - 55%)

### 6. ⏸️ 前端V1数据管理组件
- V1DataManagement.jsx - 扫描、导入V1数据
- 表格显示V1受试者列表
- 导入表单（年龄、性别、学历）

### 7. ⏸️ 前端V2数据管理优化
- 批量导入时ID规范化选项
- 显示ID映射预览
- 导入结果展示

### 8. ⏸️ 前端MMSE录入表单优化
- 移除测试日期输入
- 自动计算总分（实时显示）
- 补充人口学信息录入

### 9. ⏸️ 前端受试者列表扩展
- 版本筛选下拉框（v1/v2/全部）
- 新增列：年龄、受教育程度
- 优化系统状态显示

### 10. ⏸️ API文档和i18n更新
- 更新OpenAPI规范
- 新增中英马来语翻译

### 11. ⏸️ 测试用例
- V1/V2管理器单元测试
- API集成测试
- 前端E2E测试

---

## 📊 开发统计

### 代码量
| 模块 | 新增行数 | 修改行数 | 文件数 |
|------|---------|---------|--------|
| V1数据管理器 | 226 | 0 | 1 (新) |
| V2数据管理器 | 354 | 0 | 1 (新) |
| SubjectManager | 0 | ~15 | 1 (修改) |
| MMSEManager | 180 | 0 | 1 (修改) |
| **合计** | **760** | **15** | **4** |

### 功能完成度
```
后端核心模块:  ████████░░ 40% (4/10)
API接口开发:   ░░░░░░░░░░  0% (0/6)
前端组件开发:  ░░░░░░░░░░  0% (0/4)
测试验证:      ░░░░░░░░░░  0% (0/3)

总体进度:      ███░░░░░░░ 36% (4/11)
```

---

## 🎯 核心亮点

### 1. **智能ID规范化** ⭐⭐⭐⭐⭐
```python
# 自动分配序号，避免冲突
normalize_v2_subject_ids([
  {'subject_id': 'N_01', 'group': 'control'},
  {'subject_id': 'N_02', 'group': 'control'}
])
# 输出: {'N_01': 'v2_control_001', 'N_02': 'v2_control_002'}

# 已存在v2_control_001，新导入自动从002开始
```

### 2. **MMSE模板自动填充** ⭐⭐⭐⭐⭐
```python
# 下载模板时自动包含所有V2受试者信息
mmse_manager.generate_batch_import_template(
  subject_manager,
  include_existing_data=True,  # 自动填充
  data_version='v2'            # 仅V2受试者
)
# 模板包含: 姓名、医院ID、年龄、性别、学历、已有MMSE分数等
```

### 3. **版本筛选支持** ⭐⭐⭐⭐
```python
# 获取所有V2受试者
subjects = subject_manager.get_all_subjects(data_version='v2')

# 获取V1的MCI组受试者
subjects = subject_manager.get_all_subjects(group='mci', data_version='v1')
```

### 4. **数据迁移功能** ⭐⭐⭐⭐
```python
# 将旧的V2 ID迁移到规范格式
v2_manager.migrate_existing_v2_ids()
# 自动重命名文件、更新索引、保留原始ID
```

---

## 📁 文件结构

### 后端新增文件
```
new_project/src/modules/module02_preprocessing/
├── v1_data_manager.py          ✅ 新增 (226行)
├── v2_data_manager.py          ✅ 新增 (354行)
├── subject_manager.py          ✅ 修改 (+15行)
└── mmse_manager.py             ✅ 修改 (+180行)
```

### 待开发文件
```
new_project/src/web/modules/module02_preprocessing/
└── api.py                       ⏳ 待修改 (新增API)

new_project/frontend/src/pages/Module02/
├── V1DataManagement.jsx         ⏸️ 待新增
├── V2DataManagement.jsx         ⏸️ 待修改
├── SubjectManagement.jsx        ⏸️ 待修改
└── components/
    └── MMSEInputModal.jsx       ⏸️ 待修改

new_project/tests/
├── test_v1_data_manager.py      ⏸️ 待新增
└── test_v2_data_manager.py      ⏸️ 待新增
```

---

## 🚀 下一步计划

### 立即执行 (优先级高)
1. ⏳ **完成API接口开发** (预计2小时)
   - V1/V2数据管理6个API
   - MMSE优化API

2. ⏸️ **前端V2数据管理优化** (预计1小时)
   - ID规范化UI
   - 映射表预览

3. ⏸️ **前端MMSE录入优化** (预计1小时)
   - 自动计算总分
   - 人口学信息录入

### 短期完成 (本周)
4. ⏸️ **前端受试者列表扩展** (预计0.5小时)
5. ⏸️ **前端V1数据管理** (预计1小时)
6. ⏸️ **API文档和i18n更新** (预计0.5小时)

### 中期完成 (本月)
7. ⏸️ **测试用例编写** (预计2小时)
8. ⏸️ **端到端测试验证** (预计1小时)

---

## 📝 技术要点

### ID规范化算法
```python
# 伪代码
def normalize_v2_subject_ids(v2_subjects):
    # 1. 获取已有V2受试者，统计各组最大序号
    max_seq = {'control': 0, 'mci': 0, 'ad': 0}
    for subject in existing_v2_subjects:
        match = re.match(r'v2_(\w+)_(\d+)', subject_id)
        if match:
            group, seq = match.groups()
            max_seq[group] = max(max_seq[group], int(seq))

    # 2. 为新受试者分配递增序号
    id_mapping = {}
    for v2_subject in v2_subjects:
        max_seq[group] += 1
        new_id = f"v2_{group}_{max_seq[group]:03d}"
        id_mapping[old_id] = new_id

    return id_mapping
```

### MMSE模板自动填充逻辑
```python
# 伪代码
def generate_batch_import_template(subject_manager, data_version):
    # 1. 获取指定版本的所有受试者
    subjects = subject_manager.get_all_subjects(
        data_version=data_version,
        with_mmse=True
    )

    # 2. 填充CSV行
    for subject in subjects:
        row = {
            'subject_id': subject['subject_id'],  # 从subject
            'group': subject['group'],
            'name': subject.demographics.name,    # 从demographics
            'age': subject.demographics.age,
            'q1_year': subject.mmse.q1_year if mmse else '',  # 从mmse
            ...
        }
        csv_writer.writerow(row)
```

---

## ✅ 质量检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 代码规范 | ✅ | 符合PEP8，类型注解完整 |
| 错误处理 | ✅ | 完整的异常捕获和错误报告 |
| 日志记录 | ✅ | 关键操作有logger记录 |
| 文档注释 | ✅ | 所有函数有docstring |
| 边界情况 | ✅ | 处理空数据、重复ID等 |
| 向后兼容 | ✅ | 保留original_id，支持迁移 |

---

**报告撰写**: ✅
**撰写时间**: 2025-10-06
**进度**: 36% (4/11 任务完成)
**预计完成**: 7天 (按原计划)
**当前状态**: ✅ 核心后端模块已完成，进入API和前端开发阶段
