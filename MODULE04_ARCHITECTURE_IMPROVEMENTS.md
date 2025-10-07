# Module04 架构改进清单

**基于**: MODULE01_ARCHITECTURE_COMPLIANCE_REVIEW.md, MODULE02_ARCHITECTURE_COMPLIANCE_REPORT.md
**日期**: 2025-10-07
**优先级**: 🔴 高 | 🟡 中 | 🟢 低

---

## 📋 需要改进的项目

### 🔴 高优先级改进

#### 1. Service实例化方式不符合最佳实践

**当前代码** (`api.py:15`):
```python
# 模块级全局实例
service = EventAnalysisService()
```

**问题**:
- 违反单一职责原则
- 难以进行单元测试和Mock
- 无法控制生命周期
- 不支持依赖注入

**Module01参考实现** (`src/web/modules/module01_data_visualization/api.py`):
```python
# Module01也使用了模块级实例,但两个模块都应该改进
service = DataVisualizationService()
```

**Module02参考实现** (`src/web/modules/module02_preprocessing/api.py`):
```python
# Module02使用装饰器和全局实例,也不是最佳实践
subject_manager = SubjectManager(subject_info_dir)
```

**推荐改进方案**:
```python
# 方案1: 懒加载单例模式
_service_instance = None

def get_service():
    """获取Service单例实例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = EventAnalysisService()
    return _service_instance

@m04_bp.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    service = get_service()  # 使用函数获取
    ...
```

**或方案2: Flask应用上下文 (更优)**:
```python
def init_service(app):
    """在app初始化时注册Service"""
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    app.extensions['m04_service'] = EventAnalysisService()

def get_service():
    """从Flask应用上下文获取Service"""
    from flask import current_app
    return current_app.extensions.get('m04_service')
```

**收益**:
- ✅ 更好的测试性（可以Mock get_service）
- ✅ 生命周期可控
- ✅ 支持配置注入
- ✅ 符合Flask最佳实践

---

#### 2. 缺少错误处理装饰器

**当前状态**: 每个API端点都有重复的try-except代码

**当前代码** (重复7次):
```python
@m04_bp.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    try:
        ...
        return jsonify(result)
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Module02参考实现**:
```python
# Module02使用了统一的错误处理装饰器
def handle_errors(f):
    """统一错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except FileNotFoundError as e:
            return jsonify({'success': False, 'message': str(e)}), 404
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)}), 500
    return decorated_function

@m02_bp.route('/subjects', methods=['GET'])
@handle_errors
def get_subjects():
    # 无需try-except,装饰器自动处理
    result = subject_manager.list_subjects(...)
    return jsonify(result)
```

**推荐改进**:

在 `api.py` 顶部添加:
```python
from functools import wraps

def handle_api_errors(f):
    """
    统一API错误处理装饰器

    自动捕获异常并返回统一格式的错误响应
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            # 参数错误
            logger.warning(f"参数错误 in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except FileNotFoundError as e:
            # 文件不存在
            logger.warning(f"文件未找到 in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': '数据文件不存在'
            }), 404
        except Exception as e:
            # 其他未预期错误
            logger.error(f"未预期错误 in {f.__name__}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return decorated_function
```

然后简化所有端点:
```python
@m04_bp.route('/analyze/batch', methods=['POST'])
@handle_api_errors
def analyze_batch():
    data = request.get_json() or {}
    service = get_service()

    result = service.analyze_batch(
        group=data.get('group'),
        data_version=data.get('data_version', 'v1'),
        ...
    )

    return jsonify(result)  # 无需try-except
```

**收益**:
- ✅ 减少代码重复（从200行减少到50行）
- ✅ 错误处理统一
- ✅ 更好的可维护性
- ✅ 符合DRY原则

---

#### 3. 缺少参数验证工具

**当前状态**: 手动验证参数

**当前代码**:
```python
if not all([subject_id, group, task_id]):
    return jsonify({
        'success': False,
        'error': '缺少必要参数: subject_id, group, task_id'
    }), 400
```

**问题**:
- 重复代码
- 错误消息不一致
- 无法复用
- 难以扩展（如类型检查、范围检查）

**推荐改进**:

创建 `validators.py`:
```python
"""
Module04 参数验证工具
"""
from typing import Dict, List, Any, Optional
from functools import wraps
from flask import request, jsonify


class ValidationError(ValueError):
    """参数验证错误"""
    pass


def validate_required_params(*param_names):
    """
    验证必需参数装饰器

    用法:
        @validate_required_params('subject_id', 'group', 'task_id')
        def analyze_single():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}
            missing = [p for p in param_names if not data.get(p)]

            if missing:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要参数: {", ".join(missing)}'
                }), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_params_schema(schema: Dict[str, Dict]):
    """
    验证参数类型和约束

    用法:
        @validate_params_schema({
            'velocity_threshold': {'type': float, 'min': 0, 'max': 1000},
            'min_fixation_duration': {'type': int, 'min': 0}
        })
        def analyze_batch():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}

            for param, rules in schema.items():
                if param in data:
                    value = data[param]

                    # 类型检查
                    if 'type' in rules and not isinstance(value, rules['type']):
                        return jsonify({
                            'success': False,
                            'error': f'参数 {param} 类型错误，应为 {rules["type"].__name__}'
                        }), 400

                    # 范围检查
                    if 'min' in rules and value < rules['min']:
                        return jsonify({
                            'success': False,
                            'error': f'参数 {param} 不能小于 {rules["min"]}'
                        }), 400

                    if 'max' in rules and value > rules['max']:
                        return jsonify({
                            'success': False,
                            'error': f'参数 {param} 不能大于 {rules["max"]}'
                        }), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator
```

**使用示例**:
```python
from .validators import validate_required_params, validate_params_schema

@m04_bp.route('/analyze/single', methods=['POST'])
@handle_api_errors
@validate_required_params('subject_id', 'group', 'task_id')
def analyze_single():
    # 参数已验证，直接使用
    data = request.get_json()
    service = get_service()
    result = service.analyze_single_file(...)
    return jsonify(result)


@m04_bp.route('/analyze/batch', methods=['POST'])
@handle_api_errors
@validate_params_schema({
    'velocity_threshold': {'type': float, 'min': 0, 'max': 1000},
    'min_fixation_duration': {'type': int, 'min': 0, 'max': 10000}
})
def analyze_batch():
    # 参数类型和范围已验证
    ...
```

**收益**:
- ✅ 代码更简洁
- ✅ 验证逻辑可复用
- ✅ 错误消息统一
- ✅ 易于扩展新的验证规则

---

### 🟡 中优先级改进

#### 4. API文档缺失

**当前状态**: 只有docstring，缺少OpenAPI/Swagger文档

**Module01/02状态**: 同样缺少OpenAPI文档

**推荐改进**: 使用Flask-RESTX或flasgger

**安装**:
```bash
pip install flask-restx
```

**改进示例**:
```python
from flask_restx import Namespace, Resource, fields

api = Namespace('m04', description='眼动事件分析模块')

# 定义数据模型
analyze_batch_model = api.model('AnalyzeBatch', {
    'group': fields.String(description='组别 (可选)'),
    'data_version': fields.String(required=True, description='数据版本 (v1/v2)', default='v1'),
    'velocity_threshold': fields.Float(description='IVT速度阈值', default=40.0),
    'min_fixation_duration': fields.Integer(description='最小注视时长(ms)', default=100)
})

@api.route('/analyze/batch')
class AnalyzeBatch(Resource):
    @api.expect(analyze_batch_model)
    @api.doc(responses={
        200: 'Success',
        400: 'Validation Error',
        500: 'Internal Server Error'
    })
    def post(self):
        """批量分析眼动事件"""
        ...
```

**收益**:
- ✅ 自动生成Swagger UI文档
- ✅ 前端开发更方便
- ✅ 参数验证自动化
- ✅ 测试更容易

**优先级**: 中（可以延后，但长期有益）

---

#### 5. 缺少单元测试

**当前状态**: 无测试文件

**Module01/02状态**: 同样缺少系统化测试

**推荐结构**:
```
tests/
└── module04/
    ├── __init__.py
    ├── test_api.py              # API端点测试
    ├── test_service.py          # Service层测试
    ├── test_event_analyzer.py   # IVT算法测试
    └── fixtures/                # 测试数据
        ├── sample_gaze_data.csv
        └── sample_roi_config.json
```

**测试示例** (`test_api.py`):
```python
import pytest
from flask import Flask
from src.modules.module04_event_analysis.api import m04_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(m04_bp)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """测试健康检查端点"""
    response = client.get('/api/m04/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'

def test_analyze_batch_missing_params(client):
    """测试批量分析缺少参数"""
    response = client.post('/api/m04/analyze/batch', json={})
    # 应该返回参数验证错误
    assert response.status_code in [200, 400]

def test_cache_endpoint(client):
    """测试缓存端点"""
    response = client.get('/api/m04/cache')
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data
```

**Service层测试示例** (`test_service.py`):
```python
import pytest
from pathlib import Path
from src.modules.module04_event_analysis.service import EventAnalysisService

@pytest.fixture
def service():
    return EventAnalysisService()

def test_service_initialization(service):
    """测试Service初始化"""
    assert service.data_root.exists()
    assert service.processed_dir.exists()
    assert service.cache_dir.exists()

def test_load_cache_no_file(service):
    """测试加载不存在的缓存"""
    # 确保缓存不存在
    cache_file = service.cache_dir / 'latest_analysis.json'
    if cache_file.exists():
        cache_file.unlink()

    result = service.load_cache()
    assert result is None
```

**收益**:
- ✅ 提高代码质量
- ✅ 防止回归bug
- ✅ 重构更安全
- ✅ 作为文档使用

**优先级**: 中（建议尽快添加）

---

#### 6. Service层日志过于详细

**当前代码** (`service.py`):
```python
logger.info(f"逐帧分析法: 检查文件 {calibrated_file}, exists={calibrated_file.exists()}")
logger.info(f"逐帧分析法: 读取校准数据 {len(gaze_df)} 行")
logger.info(f"逐帧分析法: ROI配置获取结果 success={roi_result.get('success')}")
logger.info(f"逐帧分析法: ROI summary = {roi_summary}")
```

**问题**:
- 生产环境日志量过大
- 包含过多调试信息
- 应该用DEBUG级别

**推荐改进**:
```python
# 调试信息用DEBUG
logger.debug(f"逐帧分析法: 检查文件 {calibrated_file}, exists={calibrated_file.exists()}")
logger.debug(f"逐帧分析法: 读取校准数据 {len(gaze_df)} 行")

# 关键节点用INFO
logger.info(f"开始分析: {full_subject_id}_{task_id}")

# 结果摘要用INFO
if bg_ratio_frame + inst_ratio_frame + kw_ratio_frame > 0:
    logger.info(f"逐帧分析完成: {full_subject_id}_{task_id} - "
                f"BG:{bg_ratio_frame:.2f}% INST:{inst_ratio_frame:.2f}% KW:{kw_ratio_frame:.2f}%")
```

**收益**:
- ✅ 生产环境日志更清洁
- ✅ 性能提升（减少I/O）
- ✅ 便于问题定位

---

### 🟢 低优先级改进

#### 7. 模块位置不一致

**当前位置**: `src/modules/module04_event_analysis/`

**Module01位置**: `src/web/modules/module01_data_visualization/`

**Module02位置**:
- API: `src/web/modules/module02_preprocessing/api.py`
- Service: `src/modules/module02_preprocessing/`

**建议**: 统一所有模块位置

**方案1: 都放在 `src/modules/`**:
```
src/modules/
├── module01_data_visualization/
├── module02_preprocessing/
├── module04_event_analysis/      # 已经在这里
└── ...
```

**方案2: 都放在 `src/web/modules/`**:
```
src/web/modules/
├── module01_data_visualization/  # 已经在这里
├── module02_preprocessing/
├── module04_event_analysis/      # 需要移动
└── ...
```

**推荐**: 方案1（纯业务逻辑模块放src/modules，Web特定的放src/web/modules）

**影响**: 需要更新导入路径和配置

---

#### 8. 前端错误处理可以更友好

**当前代码** (`Module04.jsx`):
```jsx
try {
    const response = await axios.post('/api/m04/features', payload);
    setFeaturesData(response.data.features);
} catch (error) {
    message.error('分析失败');
    console.error(error);
}
```

**推荐改进**:
```jsx
try {
    const response = await axios.post('/api/m04/features', payload);

    if (!response.data.success) {
        message.error(`分析失败: ${response.data.error}`);
        return;
    }

    setFeaturesData(response.data.features);
    message.success('分析完成');

} catch (error) {
    const errorMsg = error.response?.data?.error || error.message || '未知错误';
    message.error(`分析失败: ${errorMsg}`);
    console.error('Analysis error:', error);
}
```

**收益**:
- ✅ 用户看到具体错误原因
- ✅ 更好的调试体验

---

#### 9. 缺少性能监控

**建议**: 添加性能日志

**示例**:
```python
import time

def analyze_batch(self, ...):
    start_time = time.time()

    # 执行分析
    result = ...

    elapsed = time.time() - start_time
    logger.info(f"批量分析完成: {len(results)}个任务, 耗时{elapsed:.2f}秒")

    return result
```

---

## 📊 改进优先级总结

| 改进项 | 优先级 | 预计工作量 | 收益 | 推荐顺序 |
|--------|--------|------------|------|----------|
| 1. Service实例化方式 | 🔴 高 | 1小时 | 高 | 1 |
| 2. 错误处理装饰器 | 🔴 高 | 2小时 | 高 | 2 |
| 3. 参数验证工具 | 🔴 高 | 3小时 | 高 | 3 |
| 4. API文档 | 🟡 中 | 4小时 | 中 | 5 |
| 5. 单元测试 | 🟡 中 | 8小时 | 高 | 4 |
| 6. 日志级别优化 | 🟡 中 | 1小时 | 中 | 6 |
| 7. 模块位置统一 | 🟢 低 | 2小时 | 低 | 8 |
| 8. 前端错误处理 | 🟢 低 | 1小时 | 中 | 7 |
| 9. 性能监控 | 🟢 低 | 1小时 | 低 | 9 |

**总计工作量**: 约23小时
**第一阶段（高优先级）**: 约6小时
**第二阶段（中优先级）**: 约13小时
**第三阶段（低优先级）**: 约4小时

---

## 🎯 实施建议

### 第一阶段：立即改进（本周）

1. **Service实例化** - 改为懒加载模式
2. **错误处理装饰器** - 统一API错误处理
3. **参数验证** - 添加验证装饰器

### 第二阶段：短期改进（本月）

4. **单元测试** - 至少覆盖核心功能
5. **API文档** - 添加Swagger文档
6. **日志优化** - DEBUG/INFO级别分离

### 第三阶段：长期优化（下季度）

7. **前端优化** - 更好的错误提示
8. **模块重组** - 统一目录结构
9. **性能监控** - 添加性能日志

---

## 📝 参考资料

- **Module01架构审查**: `MODULE01_ARCHITECTURE_COMPLIANCE_REVIEW.md`
- **Module02架构审查**: `MODULE02_ARCHITECTURE_COMPLIANCE_REPORT.md`
- **Flask最佳实践**: https://flask.palletsprojects.com/patterns/
- **Python装饰器**: https://realpython.com/primer-on-python-decorators/
- **Flask-RESTX文档**: https://flask-restx.readthedocs.io/

---

**文档版本**: 1.0
**最后更新**: 2025-10-07
**维护者**: Architecture Team
