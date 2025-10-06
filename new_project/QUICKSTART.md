# 快速开始指南

## 🚀 5分钟启动新平台

### 前置要求

- Python 3.8+
- pip (Python包管理器)

### 步骤1: 安装依赖

```bash
cd new_project
pip install -r requirements.txt
```

**可选**: 如果有NVIDIA GPU且想使用GPU加速:
```bash
pip install cupy-cuda12x
```

### 步骤2: 启动应用

```bash
python run.py
```

### 步骤3: 访问平台

打开浏览器访问: http://127.0.0.1:8080/

---

## ✅ 验证安装

### 检查API健康状态

浏览器访问: http://127.0.0.1:8080/api/health

预期响应:
```json
{
  "success": true,
  "status": "healthy",
  "version": "2.0.0"
}
```

### 检查系统信息

浏览器访问: http://127.0.0.1:8080/api/info

预期响应:
```json
{
  "success": true,
  "data": {
    "project_name": "VR Eye-Tracking Analysis Platform",
    "version": "2.0.0",
    "environment": "development"
  }
}
```

---

## 📂 项目结构导览

### 核心配置
```
config/settings.py  - 所有配置参数集中管理
```

### 核心工具
```
src/core/
├── data_loader.py   - 数据加载（支持所有数据类型）
├── file_utils.py    - 文件操作工具
└── validators.py    - 数据验证器
```

### Web应用
```
src/web/
├── app.py          - Flask应用工厂
├── routes.py       - 路由注册
├── middleware.py   - 中间件
└── templates/      - HTML模板
```

### 应用入口
```
run.py              - 启动脚本
```

---

## 💡 使用示例

### 示例1: 使用配置系统

```python
from config.settings import Config

# 获取数据路径
path = Config.get_data_path(
    group='control',
    subject_id='s001',
    task_id='q1',
    stage='raw'
)
print(path)
# 输出: .../data/01_raw/control/control_s001_q1.csv
```

### 示例2: 加载数据

```python
from src.core import DataLoader

loader = DataLoader()

# 加载原始眼动数据
df = loader.load_raw_data('control', 's001', 'q1')
print(f"数据形状: {df.shape}")

# 列出所有受试者
subjects = loader.list_subjects('control', stage='raw')
print(f"控制组受试者: {subjects}")
```

### 示例3: 验证数据

```python
from src.core import DataValidator

validator = DataValidator()

# 验证眼动数据
is_valid, errors = validator.validate_eyetracking_data(df)
if not is_valid:
    for error in errors:
        print(f"错误: {error}")
```

### 示例4: 文件操作

```python
from src.core import FileUtils
from pathlib import Path

# 读取JSON文件
data = FileUtils.read_json(Path('data/meta.json'))

# 备份文件
backup_path = FileUtils.backup_file(Path('important.csv'))
print(f"备份到: {backup_path}")
```

### 示例5: 计时器

```python
from src.utils import Timer

with Timer("数据处理"):
    # 执行耗时操作
    result = process_data()
# 自动输出: [数据处理] 耗时: 3.45 s
```

### 示例6: GPU检测

```python
from src.utils import GPUUtils

if GPUUtils.is_gpu_available():
    print("GPU可用!")
    GPUUtils.log_gpu_status()
else:
    print("GPU不可用，使用CPU模式")
```

---

## 🐛 常见问题

### 问题1: 启动失败 - ModuleNotFoundError

**原因**: 缺少依赖包

**解决**:
```bash
pip install -r requirements.txt
```

### 问题2: 端口被占用

**错误信息**: `Address already in use`

**解决**:
1. 修改 `config/settings.py` 中的 `PORT` 参数
2. 或者关闭占用8080端口的程序

### 问题3: 中文乱码

**原因**: 控制台编码问题

**解决**:
```bash
# Windows
chcp 65001

# 或在代码中设置
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 问题4: 找不到模板文件

**错误信息**: `TemplateNotFound`

**原因**: 工作目录不正确

**解决**:
```bash
# 确保在new_project目录下执行
cd new_project
python run.py
```

---

## 📚 下一步

### 开发模式

当前已是开发模式，支持:
- 自动重载
- 详细日志
- 调试信息

### 生产部署

修改环境变量:
```bash
export FLASK_ENV=production
python run.py
```

或使用WSGI服务器（如gunicorn）:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 "src.web:create_app()"
```

### 添加新模块

1. 在 `src/modules/` 创建模块目录
2. 实现 `api.py` 和 `service.py`
3. 在 `src/web/routes.py` 注册路由

参考文档: [REFACTOR_PLAN.md](REFACTOR_PLAN.md)

---

## 📖 完整文档

- [README.md](README.md) - 项目概述
- [REFACTOR_PLAN.md](REFACTOR_PLAN.md) - 重构方案
- [MODULES_INVENTORY.md](MODULES_INVENTORY.md) - 模块清单
- [docs/PHASE1_COMPLETE.md](docs/PHASE1_COMPLETE.md) - 第1阶段完成报告

---

## 💬 获取帮助

遇到问题？
1. 查看日志文件: `logs/app.log`
2. 阅读文档
3. 检查代码注释（所有函数都有详细docstring）

---

**祝使用愉快！** 🎉
