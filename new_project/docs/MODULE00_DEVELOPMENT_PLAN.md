# Module 00: 数据管理中心 - 完整开发文档 v2.0

**创建日期**: 2025-10-02
**文档版本**: v2.0
**状态**: 开发中

---

## 📋 目录

1. [需求分析](#需求分析)
2. [数据源结构](#数据源结构)
3. [架构设计](#架构设计)
4. [后端开发文档](#后端开发文档)
5. [前端开发文档](#前端开发文档)
6. [数据存储设计](#数据存储设计)
7. [开发计划](#开发计划)
8. [测试方案](#测试方案)

---

## 需求分析

### 业务背景

VR眼球追踪数据分析平台存在两套历史数据:
1. **旧版数据** (v1): 2025年1月采集,共65个受试者,使用ROI v1布局
2. **新版数据** (v2): 2025年3-4月采集,共94个受试者,使用ROI v2布局

Module 00需要实现统一的数据导入管理,支持两种数据源的批量导入,并为后续模块提供数据版本标识。

---

## 数据源结构

### 数据源1: 旧版数据 (Legacy Data v1)

**位置**: `data/*_raw/`

**结构**:
```
data/
├── control_raw/  (22个受试者)
│   ├── control_group_1/
│   │   ├── 1.txt  # Q1任务
│   │   ├── 2.txt  # Q2任务
│   │   ├── 3.txt  # Q3任务
│   │   ├── 4.txt  # Q4任务
│   │   └── 5.txt  # Q5任务
│   ├── control_group_2/
│   └── ...
├── mci_raw/      (22个受试者)
│   └── mci_group_X/
└── ad_raw/       (21个受试者)
    └── ad_group_X/
```

**特征**:
- 时间戳: 2025-01-23
- 命名规则: `{group}_group_{序号}`
- 文件格式: TXT (与新版相同格式)
- ROI版本: v1
- 元数据: 无,需手动生成

**统计**:
- Control: 22个受试者
- MCI: 22个受试者
- AD: 21个受试者
- **总计: 65个受试者**

---

### 数据源2: 新版数据 (Eye Tracking Data v2)

**位置**: `eye_tracking_data/`

**结构**:
```
eye_tracking_data/
├── data_index.json              # 元数据索引
├── 2025-3-27-11-22-56/          # 时间戳目录
│   ├── level_1.txt              # Q1眼动数据
│   ├── level_2.txt              # Q2眼动数据
│   ├── level_3.txt              # Q3眼动数据
│   ├── level_4.txt              # Q4眼动数据
│   ├── level_5.txt              # Q5眼动数据
│   ├── level_1_score.json       # Q1评分
│   ├── level_1_time.json        # Q1时间
│   └── ...
├── 2025-3-27-11-37-22/
└── ... (101个时间戳目录)
```

**data_index.json 结构**:
```json
{
  "2025-3-27-11-37-22": {
    "timestamp": "2025-3-27-11-37-22",
    "patient_name": "黄鹤鸣",
    "hospital_id": "000000",
    "group": "对照组",
    "levels": {
      "1": {"txt_file": "level_1.txt", "plot_file": "level_1.png"},
      "2": {"txt_file": "level_2.txt", "plot_file": "level_2.png"},
      "3": {"txt_file": "level_3.txt", "plot_file": "level_3.png"},
      "4": {"txt_file": "level_4.txt", "plot_file": "level_4.png"},
      "5": {"txt_file": "level_5.txt", "plot_file": "level_5.png"}
    }
  }
}
```

**特征**:
- 时间戳: 2025-03-27 ~ 2025-04-15
- 命名规则: 时间戳目录
- 文件格式: TXT
- ROI版本: v2
- 元数据: data_index.json提供

**统计**:
- 总目录数: 101个
- data_index.json记录: 94条
- 完整数据(level_1~5都存在): 约87个
- **有效受试者: ~87-94个**

---

### 眼动数据格式 (通用)

**TXT格式** (level_X.txt 或 X.txt):
```
x:0.296941y:0.769334z:0.000000/2025-3-27-11-37-31-522----
x:0.296761y:0.769074z:0.000000/2025-3-27-11-37-31-527----
...
```

**格式说明**:
- `x:{float}` - 归一化X坐标 (0.0-1.0)
- `y:{float}` - 归一化Y坐标 (0.0-1.0)
- `z:0.000000` - Z坐标(固定为0)
- `/{timestamp}` - 时间戳: 年-月-日-时-分-秒-毫秒
- `----` - 分隔符

**转换为CSV格式**:
```csv
timestamp,x,y
2025-03-27 11:37:31.522,0.296941,0.769334
2025-03-27 11:37:31.527,0.296761,0.769074
...
```

---

## 架构设计

### 数据流设计

```
┌─────────────────────┐
│ 数据源1: Legacy     │
│ data/*_raw/         │ (v1, 65个受试者)
│ ├─ control_raw/     │
│ ├─ mci_raw/         │
│ └─ ad_raw/          │
└─────────────────────┘
          ↓
          ↓ LegacyImporter
          ↓
┌─────────────────────┐
│ 数据源2: EyeTracking│
│ eye_tracking_data/  │ (v2, 94个受试者)
│ ├─ data_index.json  │
│ └─ timestamp_dirs/  │
└─────────────────────┘
          ↓
          ↓ EyeTrackingImporter
          ↓
┌─────────────────────┐
│ Module 00:          │
│ 统一数据导入管理     │
│ ├─ 扫描识别         │
│ ├─ 格式转换         │
│ ├─ 元数据生成       │
│ └─ 版本标识         │
└─────────────────────┘
          ↓
          ↓ 标准化输出
          ↓
┌─────────────────────────────────────┐
│ new_project/data/01_raw/            │
│ ├─ control/                         │
│ │   ├─ control_legacy_1_q1.csv  (v1)│
│ │   ├─ control_000000_q1.csv    (v2)│
│ │   └─ ...                           │
│ ├─ mci/                             │
│ ├─ ad/                              │
│ └─ clinical/                        │
│     ├─ subject_metadata.json        │
│     └─ import_history.json          │
└─────────────────────────────────────┘
```

---

### 模块架构

```
src/web/modules/module00_data_management/
├── __init__.py
├── api.py                          # API路由 (120行)
├── service.py                      # 业务逻辑 (300行)
│
├── importers/                      # 导入器目录
│   ├── __init__.py
│   ├── legacy_importer.py          # 旧版数据导入 (150行)
│   └── eye_tracking_importer.py    # 新版数据导入 (180行)
│
├── scanner.py                      # 数据扫描器 (200行)
├── converter.py                    # 格式转换器 (120行)
├── validator.py                    # 数据验证器 (100行)
└── metadata_manager.py             # 元数据管理 (120行)
```

---

## 后端开发文档

### 文件1: importers/legacy_importer.py

**职责**: 导入旧版 data/*_raw/ 数据

**核心类**:
```python
class LegacyDataImporter:
    """导入旧版data/*_raw/数据"""

    def __init__(self, config):
        self.source_dirs = {
            "control": Path("data/control_raw"),
            "mci": Path("data/mci_raw"),
            "ad": Path("data/ad_raw")
        }
        self.target_dir = Path("new_project/data/01_raw")
        self.converter = EyeTrackingDataConverter()

    def scan_legacy_data(self) -> Dict:
        """扫描旧版数据目录"""

    def import_single_subject(self, subject_info: Dict) -> Dict:
        """导入单个旧版受试者数据"""

    def import_all(self) -> Dict:
        """批量导入所有旧版数据"""
```

**关键方法**:

#### `scan_legacy_data()`
```python
def scan_legacy_data(self) -> Dict:
    """
    扫描旧版数据目录

    Returns:
        {
            "control": [
                {
                    "subject_dir": Path,
                    "subject_id": "control_legacy_1",
                    "group": "control",
                    "data_version": "v1",
                    "roi_layout": "v1",
                    "source_type": "legacy"
                },
                ...
            ],
            "mci": [...],
            "ad": [...]
        }
    """
    result = {}
    for group, source_dir in self.source_dirs.items():
        subjects = list(source_dir.glob(f"{group}_group_*"))
        result[group] = [
            {
                "subject_dir": subj,
                "subject_id": f"{group}_legacy_{subj.name.split('_')[-1]}",
                "group": group,
                "data_version": "v1",
                "roi_layout": "v1",
                "source_type": "legacy"
            }
            for subj in subjects
        ]
    return result
```

#### `import_single_subject(subject_info)`
```python
def import_single_subject(self, subject_info: Dict) -> Dict:
    """
    导入单个旧版受试者数据

    Args:
        subject_info: {
            "subject_dir": Path("data/control_raw/control_group_1"),
            "subject_id": "control_legacy_1",
            "group": "control",
            ...
        }

    Returns:
        metadata: {
            "subject_id": "control_legacy_1",
            "group": "control",
            "data_version": "v1",
            "roi_layout": "v1",
            "source_type": "legacy",
            "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
            ...
        }
    """
    subject_dir = subject_info["subject_dir"]
    subject_id = subject_info["subject_id"]
    group = subject_info["group"]

    # 1. 验证文件完整性
    required_files = ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
    if not all((subject_dir / f).exists() for f in required_files):
        raise ValueError(f"Incomplete data for {subject_id}")

    # 2. 输出目录
    output_dir = self.target_dir / group
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. 转换5个任务
    for i in range(1, 6):
        txt_path = subject_dir / f"{i}.txt"
        csv_path = output_dir / f"{subject_id}_q{i}.csv"
        self.converter.convert_txt_to_csv(txt_path, csv_path)

    # 4. 生成元数据
    metadata = {
        "subject_id": subject_id,
        "group": group,
        "data_version": "v1",
        "roi_layout": "v1",
        "source_type": "legacy",
        "source_path": str(subject_dir),
        "import_date": datetime.now().isoformat(),
        "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
        "has_mmse": False
    }

    return metadata
```

---

### 文件2: importers/eye_tracking_importer.py

**职责**: 导入新版 eye_tracking_data/ 数据

**核心类**:
```python
class EyeTrackingDataImporter:
    """导入新版eye_tracking_data数据"""

    def __init__(self, config):
        self.source_dir = Path("eye_tracking_data")
        self.data_index_path = self.source_dir / "data_index.json"
        self.target_dir = Path("new_project/data/01_raw")
        self.scanner = EyeTrackingDataScanner(...)
        self.converter = EyeTrackingDataConverter()

    def load_data_index(self) -> Dict:
        """加载data_index.json"""

    def import_single(self, timestamp: str, metadata: Dict) -> Dict:
        """导入单个时间戳的数据"""

    def import_all_new(self) -> Dict:
        """批量导入所有新数据"""
```

**关键方法**:

#### `import_single(timestamp, metadata)`
```python
def import_single(self, timestamp: str, metadata: Dict) -> Dict:
    """
    导入单个时间戳的数据

    Args:
        timestamp: "2025-3-27-11-37-22"
        metadata: {
            "patient_name": "黄鹤鸣",
            "hospital_id": "000000",
            "group": "对照组",
            "levels": {...}
        }

    Returns:
        metadata: {
            "subject_id": "control_000000",
            "patient_name": "黄鹤鸣",
            "data_version": "v2",
            "roi_layout": "v2",
            ...
        }
    """
    timestamp_dir = self.source_dir / timestamp

    # 1. 组别映射
    GROUP_MAPPING = {
        "对照组": "control",
        "轻度认知障碍组": "mci",
        "阿尔兹海默症组": "ad",
        "custom": "custom"
    }
    group_code = GROUP_MAPPING[metadata["group"]]

    # 2. 生成subject_id
    hospital_id = metadata["hospital_id"]
    subject_id = f"{group_code}_{hospital_id}"

    # 3. 输出目录
    output_dir = self.target_dir / group_code
    output_dir.mkdir(parents=True, exist_ok=True)

    # 4. 转换全部5个任务
    for i in range(1, 6):
        txt_path = timestamp_dir / f"level_{i}.txt"
        csv_path = output_dir / f"{subject_id}_q{i}.csv"
        self.converter.convert_txt_to_csv(txt_path, csv_path)

    # 5. 生成元数据
    metadata_result = {
        "subject_id": subject_id,
        "patient_name": metadata["patient_name"],
        "hospital_id": hospital_id,
        "group": group_code,
        "data_version": "v2",           # 新版数据标记
        "roi_layout": "v2",             # 新版ROI
        "source_type": "eye_tracking",  # 数据来源
        "source_timestamp": timestamp,
        "import_date": datetime.now().isoformat(),
        "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
        "has_mmse": False
    }

    return metadata_result
```

---

### 文件3: converter.py

**职责**: TXT格式转换为CSV格式

**核心类**:
```python
class EyeTrackingDataConverter:
    """转换原始TXT格式到标准CSV"""

    @staticmethod
    def parse_line(line: str) -> Dict:
        """解析单行数据"""

    def convert_txt_to_csv(self, txt_path: Path, csv_path: Path):
        """转换单个TXT文件到CSV"""
```

**关键方法**:

#### `parse_line(line)`
```python
@staticmethod
def parse_line(line: str) -> Dict:
    """
    解析单行数据

    Input:
        x:0.296941y:0.769334z:0.000000/2025-3-27-11-37-31-522----

    Output:
        {
            'x': 0.296941,
            'y': 0.769334,
            'timestamp': '2025-03-27 11:37:31.522'
        }
    """
    # 正则匹配: x:(float) y:(float) z:(float) / (timestamp)
    pattern = r'x:([\d.]+)y:([\d.]+)z:([\d.]+)/([\d-]+)'
    match = re.match(pattern, line)

    if not match:
        return None

    x, y, z, timestamp_str = match.groups()

    # 时间戳转换: 2025-3-27-11-37-31-522 → 2025-03-27 11:37:31.522
    parts = timestamp_str.split('-')
    year, month, day, hour, minute, second, ms = parts

    timestamp_formatted = (
        f"{year}-{month.zfill(2)}-{day.zfill(2)} "
        f"{hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}.{ms}"
    )

    return {
        'x': float(x),
        'y': float(y),
        'timestamp': timestamp_formatted
    }
```

#### `convert_txt_to_csv(txt_path, csv_path)`
```python
def convert_txt_to_csv(self, txt_path: Path, csv_path: Path):
    """
    转换单个TXT文件到CSV

    Args:
        txt_path: data/control_raw/control_group_1/1.txt
        csv_path: new_project/data/01_raw/control/control_legacy_1_q1.csv
    """
    import csv

    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按 ---- 分割数据点
    data_points = [point.strip() for point in content.split('----') if point.strip()]

    # 解析每个数据点
    parsed_data = []
    for point in data_points:
        parsed = self.parse_line(point)
        if parsed:
            parsed_data.append(parsed)

    # 写入CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'x', 'y'])
        writer.writeheader()
        writer.writerows(parsed_data)
```

---

### 文件4: service.py

**职责**: 业务逻辑协调层

**核心类**:
```python
class DataManagementService:
    """Module 00核心业务逻辑"""

    def __init__(self):
        self.legacy_importer = LegacyDataImporter(config.settings)
        self.eye_tracking_importer = EyeTrackingDataImporter(config.settings)
        self.metadata_manager = MetadataManager()

    def scan_all_sources(self) -> Dict:
        """API: /api/m00/scan-all"""

    def preview_importable_data(self, source: str = "all") -> Dict:
        """API: /api/m00/preview"""

    def batch_import(self, source: str = "all", subjects: List = None,
                    overwrite: bool = False) -> Dict:
        """API: POST /api/m00/import"""

    def get_subjects(self, data_version: str = "all") -> Dict:
        """API: GET /api/m00/subjects"""
```

---

### 文件5: api.py

**职责**: Flask API路由定义

**API端点**:

```python
from flask import Blueprint, request, jsonify
from .service import DataManagementService

bp = Blueprint('module00', __name__, url_prefix='/api/m00')
service = DataManagementService()

@bp.route('/scan-all', methods=['GET'])
def scan_all():
    """扫描所有数据源"""
    result = service.scan_all_sources()
    return jsonify(result)

@bp.route('/preview', methods=['GET'])
def preview():
    """预览待导入数据"""
    source = request.args.get('source', 'all')
    result = service.preview_importable_data(source)
    return jsonify(result)

@bp.route('/import', methods=['POST'])
def batch_import():
    """批量导入数据"""
    data = request.json
    source = data.get('source', 'all')
    subjects = data.get('subjects', None)
    overwrite = data.get('overwrite', False)

    result = service.batch_import(source, subjects, overwrite)
    return jsonify(result)

@bp.route('/subjects', methods=['GET'])
def get_subjects():
    """查看受试者列表"""
    data_version = request.args.get('data_version', 'all')
    result = service.get_subjects(data_version)
    return jsonify(result)

@bp.route('/import-history', methods=['GET'])
def get_import_history():
    """查看导入历史"""
    result = service.metadata_manager.load_import_history()
    return jsonify({"success": True, "history": result})
```

---

## 数据存储设计

### 1. subject_metadata.json

**位置**: `new_project/data/01_raw/clinical/subject_metadata.json`

**结构**:
```json
{
    "control_legacy_1": {
        "subject_id": "control_legacy_1",
        "group": "control",
        "data_version": "v1",
        "roi_layout": "v1",
        "source_type": "legacy",
        "source_path": "data/control_raw/control_group_1",
        "import_date": "2025-10-02T15:30:00",
        "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
        "has_mmse": false,
        "mmse_scores": null
    },
    "control_000000": {
        "subject_id": "control_000000",
        "patient_name": "黄鹤鸣",
        "hospital_id": "000000",
        "group": "control",
        "data_version": "v2",
        "roi_layout": "v2",
        "source_type": "eye_tracking",
        "source_timestamp": "2025-3-27-11-37-22",
        "import_date": "2025-10-02T15:35:00",
        "tasks_available": ["q1", "q2", "q3", "q4", "q5"],
        "has_mmse": false,
        "mmse_scores": null
    }
}
```

---

### 2. import_history.json

**位置**: `new_project/data/01_raw/clinical/import_history.json`

**结构**:
```json
{
    "last_import_time": "2025-10-02T15:35:00",
    "import_logs": [
        {
            "timestamp": "2025-10-02T15:30:00",
            "source": "legacy",
            "imported_count": 65,
            "subjects": [
                "control_legacy_1",
                "control_legacy_2",
                "..."
            ]
        },
        {
            "timestamp": "2025-10-02T15:35:00",
            "source": "eye_tracking",
            "imported_count": 94,
            "source_timestamps": [
                "2025-3-27-11-37-22",
                "2025-3-27-11-53-9",
                "..."
            ]
        }
    ]
}
```

---

### 3. 输出CSV文件

**位置**: `new_project/data/01_raw/<group>/<subject_id>_qX.csv`

**格式**:
```csv
timestamp,x,y
2025-03-27 11:37:31.522,0.296941,0.769334
2025-03-27 11:37:31.527,0.296761,0.769074
2025-03-27 11:37:31.541,0.296831,0.768151
...
```

---

## 开发计划

### 阶段1: 后端核心功能 (3天)

**Day 1: 导入器开发**
- [x] 数据源结构分析
- [ ] converter.py - 格式转换器
- [ ] legacy_importer.py - 旧版数据导入
- [ ] eye_tracking_importer.py - 新版数据导入

**Day 2: 服务层开发**
- [ ] scanner.py - 数据扫描器
- [ ] validator.py - 数据验证器
- [ ] metadata_manager.py - 元数据管理
- [ ] service.py - 业务逻辑

**Day 3: API与测试**
- [ ] api.py - API路由
- [ ] 单元测试编写
- [ ] 集成测试

---

### 阶段2: 前端开发 (2天)

**Day 4: 基础组件**
- [ ] DataSourceOverview.jsx - 数据源概览
- [ ] DataScanner.jsx - 扫描面板
- [ ] ImportPreview.jsx - 预览表格

**Day 5: 主页面整合**
- [ ] SubjectList.jsx - 受试者列表
- [ ] Module00.jsx - 主页面
- [ ] API服务层扩展

---

### 阶段3: 测试与文档 (1天)

**Day 6: 完整测试**
- [ ] 旧版数据导入测试
- [ ] 新版数据导入测试
- [ ] 双源混合导入测试
- [ ] 版本筛选功能测试
- [ ] 更新项目文档

---

## 测试方案

### 单元测试

**测试文件**: `tests/test_module00/`

```python
# test_legacy_importer.py
def test_scan_legacy_data():
    """测试旧版数据扫描"""

def test_import_single_subject():
    """测试单个受试者导入"""

# test_eye_tracking_importer.py
def test_load_data_index():
    """测试data_index.json加载"""

def test_import_single_timestamp():
    """测试单个时间戳导入"""

# test_converter.py
def test_parse_line():
    """测试数据行解析"""

def test_convert_txt_to_csv():
    """测试TXT转CSV"""
```

---

### 集成测试

**测试场景**:

1. **场景1: 完整导入旧版数据**
   - 扫描 data/*_raw/ 目录
   - 导入全部65个受试者
   - 验证CSV文件生成
   - 验证元数据正确性

2. **场景2: 完整导入新版数据**
   - 加载 data_index.json
   - 导入全部94个受试者
   - 验证CSV文件生成
   - 验证元数据正确性

3. **场景3: 混合导入**
   - 先导入旧版数据
   - 再导入新版数据
   - 验证159个受试者数据
   - 验证版本标识正确

4. **场景4: 增量导入**
   - 导入部分数据
   - 模拟新增数据
   - 增量导入新数据
   - 验证导入历史

---

## 附录

### A. 组别映射表

```python
GROUP_MAPPING = {
    "对照组": "control",
    "轻度认知障碍组": "mci",
    "阿尔兹海默症组": "ad",
    "custom": "custom"
}
```

---

### B. 数据版本说明

| 版本 | 时间 | 受试者数 | ROI布局 | 数据来源 |
|-----|------|---------|---------|---------|
| v1  | 2025-01 | 65 | ROI v1 | data/*_raw/ |
| v2  | 2025-03+ | 94 | ROI v2 | eye_tracking_data/ |

---

### C. Subject ID生成规则

**旧版数据**:
```python
subject_id = f"{group}_legacy_{group_number}"
# 例如: control_legacy_1, mci_legacy_15
```

**新版数据**:
```python
subject_id = f"{group_code}_{hospital_id}"
# 例如: control_000000, mci_000123
```

---

**文档状态**: ✅ 待开发
**负责人**: Claude AI
**最后更新**: 2025-10-02
