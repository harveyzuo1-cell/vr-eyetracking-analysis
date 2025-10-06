# Backend Coding Standards
# 后端编码规范

## Table of Contents / 目录

1. [文件命名规范](#文件命名规范)
2. [模块架构规范](#模块架构规范)
3. [API设计规范](#api设计规范)
4. [数据处理规范](#数据处理规范)
5. [错误处理规范](#错误处理规范)
6. [代码审查检查点](#代码审查检查点)

---

## 文件命名规范

### 1. 文件命名规则

**核心原则：** 所有Python文件使用`snake_case`命名

| 文件类型 | 命名规则 | 示例 |
|---------|---------|------|
| API路由 | `api.py` | `module00_data_management/api.py` |
| 业务逻辑 | `service.py` | `module00_data_management/service.py` |
| 数据转换 | `converter.py` | `module00_data_management/converter.py` |
| 数据验证 | `validator.py` | `module00_data_management/validator.py` |
| 工具函数 | `utils.py` | `module00_data_management/utils.py` |
| 配置文件 | `config.py` | `module00_data_management/config.py` |

### 2. 目录结构规范

```
src/web/modules/
├── module00_data_management/    # 模块根目录（snake_case）
│   ├── __init__.py
│   ├── api.py                   # API路由定义
│   ├── service.py               # 核心业务逻辑
│   ├── converter.py             # 数据格式转换
│   ├── validator.py             # 数据验证
│   ├── metadata_manager.py      # 元数据管理
│   └── importers/               # 子模块
│       ├── __init__.py
│       ├── legacy_importer.py
│       └── eye_tracking_importer.py
```

---

## 模块架构规范

### 1. 标准模块结构

每个模块必须包含以下核心文件：

```python
# api.py - API路由层
from flask import Blueprint, request, jsonify
from .service import ModuleService

bp = Blueprint('module_name', __name__, url_prefix='/api/module')
service = ModuleService()

@bp.route('/endpoint', methods=['GET'])
def endpoint():
    """API端点描述"""
    try:
        result = service.method()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
```

```python
# service.py - 业务逻辑层
class ModuleService:
    """模块业务逻辑"""

    def __init__(self):
        self.validator = Validator()
        self.converter = Converter()

    def method(self):
        """业务方法"""
        # 1. 验证
        # 2. 处理
        # 3. 转换
        # 4. 返回
        pass
```

### 2. 层级职责划分

| 层级 | 文件 | 职责 | 依赖方向 |
|------|------|------|---------|
| API层 | `api.py` | 路由定义、请求响应 | → Service层 |
| Service层 | `service.py` | 业务逻辑、流程控制 | → Converter/Validator |
| Converter层 | `converter.py` | 数据格式转换 | → 无 |
| Validator层 | `validator.py` | 数据验证 | → 无 |

**依赖原则：**
- API层只依赖Service层
- Service层可依赖Converter、Validator
- Converter和Validator层不依赖其他层

---

## API设计规范

### 1. RESTful API规范

```python
# ✅ 正确的API设计
@bp.route('/subjects', methods=['GET'])
def get_subjects():
    """获取受试者列表"""
    pass

@bp.route('/subjects/<subject_id>', methods=['GET'])
def get_subject(subject_id):
    """获取单个受试者"""
    pass

@bp.route('/scan-all', methods=['GET'])
def scan_all():
    """扫描所有数据源"""
    pass

@bp.route('/import', methods=['POST'])
def import_data():
    """导入数据"""
    pass
```

### 2. 统一响应格式

**成功响应：**
```python
{
    "success": True,
    "data": {
        # 业务数据
    },
    "message": "操作成功"  # 可选
}
```

**失败响应：**
```python
{
    "success": False,
    "error": "错误描述",
    "code": "ERROR_CODE"  # 可选
}
```

**实现示例：**
```python
def success_response(data, message=None):
    """成功响应"""
    response = {"success": True, "data": data}
    if message:
        response["message"] = message
    return jsonify(response)

def error_response(error, code=None):
    """错误响应"""
    response = {"success": False, "error": str(error)}
    if code:
        response["code"] = code
    return jsonify(response)

# 使用
@bp.route('/endpoint')
def endpoint():
    try:
        result = service.method()
        return success_response(result)
    except ValueError as e:
        return error_response(e, "VALIDATION_ERROR")
    except Exception as e:
        return error_response(e)
```

### 3. 数据唯一标识设计

**问题：** 业务ID可能重复，需要生成真正唯一的标识符

**解决方案：**
```python
# ✅ 在扫描API中生成唯一ID
def scan_eye_tracking_data(self):
    """扫描Eye Tracking数据"""
    valid_entries = []

    for entry in raw_entries:
        # 生成复合唯一ID
        unique_id = f"{entry['subject_id']}_{entry['timestamp']}"

        valid_entries.append({
            "unique_id": unique_id,          # 真正唯一的ID
            "subject_id": entry["subject_id"], # 业务ID
            "timestamp": entry["timestamp"],
            # ... 其他字段
        })

    return valid_entries
```

---

## 数据处理规范

### 1. 数据验证

```python
class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_subject_data(data):
        """验证受试者数据"""
        required_fields = ['subject_id', 'group']

        # 检查必填字段
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填字段: {field}")

        # 检查数据类型
        if not isinstance(data['subject_id'], str):
            raise ValueError("subject_id必须是字符串")

        # 检查值范围
        valid_groups = ['control', 'mci', 'ad']
        if data['group'] not in valid_groups:
            raise ValueError(f"无效的分组: {data['group']}")

        return True
```

### 2. 数据转换

```python
class DataConverter:
    """数据转换器"""

    @staticmethod
    def normalize_group(raw_group):
        """标准化分组名称"""
        group_mapping = {
            'MCI': 'mci',
            '阿尔兹海默': 'ad',
            '对照组': 'control',
            'custom': 'control',  # 默认映射
        }

        # 空值处理
        if not raw_group:
            return 'control'

        # 查找映射
        return group_mapping.get(raw_group, 'control')

    @staticmethod
    def format_subject_data(raw_data):
        """格式化受试者数据"""
        return {
            "subject_id": raw_data.get("subject_id"),
            "group": DataConverter.normalize_group(raw_data.get("group")),
            "hospital_id": raw_data.get("hospital_id") or "N/A",
            "patient_name": raw_data.get("patient_name"),
            "data_version": raw_data.get("data_version", "v2"),
        }
```

### 3. 数据过滤

```python
def filter_incomplete_data(entries):
    """过滤不完整数据"""
    valid_entries = []
    incomplete_count = 0

    for entry in entries:
        # 检查完整性
        if not entry.get('level_file'):
            incomplete_count += 1
            continue

        # 检查必填字段
        if not entry.get('subject_id'):
            incomplete_count += 1
            continue

        valid_entries.append(entry)

    return {
        "valid_entries": valid_entries,
        "incomplete_count": incomplete_count,
        "total": len(entries)
    }
```

---

## 错误处理规范

### 1. 异常分类处理

```python
from flask import jsonify

@bp.route('/import', methods=['POST'])
def import_data():
    """导入数据"""
    try:
        data = request.json

        # 业务逻辑
        result = service.import_data(data)

        return jsonify({
            "success": True,
            "imported_count": result["count"],
            "data": result
        })

    except ValueError as e:
        # 验证错误 - 400
        return jsonify({
            "success": False,
            "error": f"数据验证失败: {str(e)}"
        }), 400

    except FileNotFoundError as e:
        # 文件不存在 - 404
        return jsonify({
            "success": False,
            "error": f"文件未找到: {str(e)}"
        }), 404

    except PermissionError as e:
        # 权限错误 - 403
        return jsonify({
            "success": False,
            "error": f"权限不足: {str(e)}"
        }), 403

    except Exception as e:
        # 未知错误 - 500
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500
```

### 2. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

class ModuleService:
    def process_data(self, data):
        """处理数据"""
        logger.info(f"开始处理数据，数量: {len(data)}")

        try:
            result = self._process(data)
            logger.info(f"数据处理成功，结果数量: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"数据处理失败: {str(e)}", exc_info=True)
            raise
```

---

## 代码审查检查点

### 1. 文件组织检查

- [ ] 所有Python文件使用snake_case命名
- [ ] 模块目录结构符合标准
- [ ] 每个模块有`__init__.py`
- [ ] API、Service、Converter、Validator分离

### 2. API设计检查

- [ ] 使用统一的响应格式（success + data/error）
- [ ] 路由命名清晰（RESTful风格）
- [ ] HTTP方法使用正确（GET/POST/PUT/DELETE）
- [ ] 所有端点有文档字符串

### 3. 数据处理检查

- [ ] 必填字段验证
- [ ] 数据类型检查
- [ ] 空值/None值处理
- [ ] 数据转换有映射表（如group映射）
- [ ] 生成唯一标识符（unique_id）

### 4. 错误处理检查

- [ ] 所有API端点有try-except
- [ ] 异常分类处理（ValueError、FileNotFoundError等）
- [ ] 错误信息清晰且具体
- [ ] 关键操作有日志记录

### 5. 性能检查

- [ ] 大量数据处理使用生成器
- [ ] 避免重复计算（使用缓存）
- [ ] 文件操作使用上下文管理器
- [ ] 数据库查询优化

---

## 实际案例总结

### Case 1: Module00 数据扫描API设计

**需求：** 扫描Legacy和Eye Tracking两个数据源，返回统计信息

**实现要点：**
1. 分离扫描逻辑（两个独立的方法）
2. 统一数据格式（标准化group字段）
3. 生成唯一标识（使用timestamp）
4. 过滤不完整数据

**代码示例：**
```python
class Module00Service:
    def scan_all(self):
        """扫描所有数据源"""
        # 1. 扫描Legacy数据
        legacy_data = self._scan_legacy()

        # 2. 扫描Eye Tracking数据
        eye_tracking_data = self._scan_eye_tracking()

        # 3. 生成统计摘要
        summary = {
            "total_subjects": legacy_data["total"] + eye_tracking_data["total"],
            "legacy_count": legacy_data["total"],
            "eye_tracking_count": eye_tracking_data["total"],
        }

        return {
            "legacy_data": legacy_data,
            "eye_tracking_data": eye_tracking_data,
            "summary": summary
        }
```

### Case 2: 数据唯一性问题

**问题：** Eye Tracking数据中hospital_id重复，导致subject_id重复

**解决方案：**
```python
# ✅ 使用timestamp生成唯一ID
for entry in entries:
    unique_id = f"{entry['subject_id']}_{entry['timestamp']}"

    formatted_entry = {
        "unique_id": unique_id,  # 前端使用此字段作为key
        "subject_id": entry["subject_id"],
        "timestamp": entry["timestamp"],
        # ...
    }
```

**教训：**
1. 业务ID ≠ 唯一ID
2. 前端需要真正唯一的标识符
3. 后端应该提供unique_id字段

---

## 附录：常用工具函数

### 路径处理

```python
import os
from pathlib import Path

def get_data_path(relative_path):
    """获取数据文件路径"""
    base_dir = Path(__file__).parent.parent.parent
    return base_dir / relative_path

def ensure_directory(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
```

### JSON处理

```python
import json

def safe_json_load(file_path, default=None):
    """安全加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default or {}
```

### 数据标准化

```python
def normalize_string(s):
    """标准化字符串"""
    if not s:
        return "N/A"
    return str(s).strip()

def safe_int(value, default=0):
    """安全转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
```

---

**文档版本：** v1.0
**最后更新：** 2025-10-02
**维护者：** Backend Team
