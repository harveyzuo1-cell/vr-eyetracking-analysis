# VR眼球追踪数据分析平台 - 重构方案

## 📋 项目概述

**创建时间**: 2025-10-01
**当前状态**: 旧项目存在严重的代码组织问题，需要全面重构
**重构目标**: 模块化、可维护、清晰的代码结构

---

## 🔍 现有项目问题分析

### 1. **代码文件过大问题**
- ❌ `visualization/templates/enhanced_index.html`: **19,504行** (包含所有模块的JavaScript)
- ❌ `visualization/enhanced_web_visualizer.py`: **2,577行**
- ❌ `visualization/rqa_pipeline_api.py`: **2,017行**
- ❌ `visualization/ml_prediction_api.py`: **2,021行**

**问题**: 单个HTML文件近2万行，难以维护和调试

### 2. **数据文件命名不一致**
- 原始数据: `ad3q1`, `n1q1`, `m6q1` (不同前缀)
- 处理后数据: `*_preprocessed.csv`, `*_calibrated.csv` (混乱)
- MMSE数据: 中文文件名 `阿尔兹海默症组.csv`

### 3. **模块职责不清**
- 前端和后端混在一起
- API文件既包含业务逻辑又包含路由定义
- 缺少统一的配置管理

### 4. **数据存储混乱**
- 多个数据目录: `*_processed`, `*_calibrated`, `*_raw`, `*_rqa_ready`
- 输出结果散落在各处
- 缺少统一的数据版本管理

---

## 🎯 新项目架构设计

### 目录结构

```
new_project/
├── config/                          # 配置文件
│   ├── __init__.py
│   ├── settings.py                  # 全局配置
│   ├── paths.py                     # 路径配置
│   └── constants.py                 # 常量定义
│
├── data/                            # 数据目录（按阶段组织）
│   ├── 01_raw/                      # 原始数据（只读）
│   │   ├── control/                 # 对照组
│   │   ├── mci/                     # 轻度认知障碍
│   │   ├── ad/                      # 阿尔兹海默症
│   │   └── clinical/                # 临床数据
│   │       ├── mmse_scores.csv      # MMSE评分（统一文件）
│   │       └── participant_info.csv # 受试者信息
│   │
│   ├── 02_preprocessed/             # 预处理数据
│   │   ├── control/
│   │   ├── mci/
│   │   └── ad/
│   │
│   ├── 03_calibrated/               # 校准后数据
│   │   ├── control/
│   │   ├── mci/
│   │   └── ad/
│   │
│   ├── 04_features/                 # 提取的特征
│   │   ├── rqa/                     # RQA特征
│   │   ├── events/                  # 事件分析特征
│   │   └── comprehensive/           # 综合特征
│   │
│   ├── 05_models/                   # 训练好的模型
│   │   ├── checkpoints/             # 模型检查点
│   │   └── production/              # 生产环境模型
│   │
│   └── 06_results/                  # 分析结果
│       ├── visualizations/          # 可视化输出
│       ├── reports/                 # 分析报告
│       └── exports/                 # 导出数据
│
├── src/                             # 源代码
│   ├── __init__.py
│   │
│   ├── core/                        # 核心功能（跨模块共用）
│   │   ├── __init__.py
│   │   ├── data_loader.py           # 数据加载器（200行）
│   │   ├── file_utils.py            # 文件操作（150行）
│   │   └── validators.py            # 数据验证（100行）
│   │
│   ├── modules/                     # 功能模块
│   │   ├── __init__.py
│   │   │
│   │   ├── module01_visualization/  # 模块1：可视化
│   │   │   ├── __init__.py
│   │   │   ├── api.py               # API路由（100行）
│   │   │   ├── service.py           # 业务逻辑（200行）
│   │   │   ├── renderer.py          # 渲染逻辑（150行）
│   │   │   └── static/
│   │   │       └── module1.html     # 前端页面（300行）
│   │   │
│   │   ├── module02_data_import/    # 模块2：数据导入
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── preprocessor.py      # 预处理逻辑
│   │   │   └── static/
│   │   │       └── module2.html
│   │   │
│   │   ├── module03_rqa_analysis/   # 模块3：RQA分析
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── rqa_calculator.py    # RQA计算（GPU优化）
│   │   │   └── static/
│   │   │       └── module3.html
│   │   │
│   │   ├── module04_event_analysis/ # 模块4：事件分析
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── detector.py          # 事件检测
│   │   │   └── static/
│   │   │       └── module4.html
│   │   │
│   │   ├── module05_rqa_pipeline/   # 模块5：RQA批处理
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── batch_processor.py   # 批处理逻辑
│   │   │   ├── gpu_executor.py      # GPU并行执行
│   │   │   └── static/
│   │   │       └── module5.html
│   │   │
│   │   ├── module06_feature_extraction/  # 模块6：特征提取
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── extractors/          # 不同类型的特征提取器
│   │   │   │   ├── rqa_features.py
│   │   │   │   ├── event_features.py
│   │   │   │   └── statistical_features.py
│   │   │   └── static/
│   │   │       └── module6.html
│   │   │
│   │   ├── module07_data_integration/    # 模块7：数据整合
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   └── static/
│   │   │       └── module7.html
│   │   │
│   │   ├── module08_mmse_analysis/  # 模块8：MMSE对比
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── mmse_loader.py       # MMSE数据加载
│   │   │   └── static/
│   │   │       └── module8.html
│   │   │
│   │   ├── module09_ml_prediction/  # 模块9：机器学习预测
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── models/              # 模型定义
│   │   │   │   ├── mlp_model.py
│   │   │   │   └── model_loader.py
│   │   │   └── static/
│   │   │       └── module9.html
│   │   │
│   │   └── module10_eye_index/      # 模块10：Eye-Index综合评估
│   │       ├── __init__.py
│   │       ├── api.py
│   │       ├── service.py
│   │       ├── submodules/
│   │       │   ├── data_preparation.py    # 10A: 数据准备
│   │       │   ├── model_training.py      # 10B: 模型训练
│   │       │   ├── model_service.py       # 10C: 模型服务
│   │       │   ├── performance_eval.py    # 10D: 性能评估
│   │       │   └── correlation_viz.py     # 10E: 关联性可视化
│   │       └── static/
│   │           └── module10.html
│   │
│   ├── web/                         # Web服务
│   │   ├── __init__.py
│   │   ├── app.py                   # Flask应用主入口（150行）
│   │   ├── routes.py                # 路由注册（100行）
│   │   ├── middleware.py            # 中间件（CORS等）
│   │   └── templates/
│   │       ├── base.html            # 基础模板
│   │       └── index.html           # 主页（500行，不含模块JS）
│   │
│   └── utils/                       # 工具函数
│       ├── __init__.py
│       ├── logger.py                # 日志工具
│       ├── timer.py                 # 性能计时
│       └── gpu_utils.py             # GPU工具
│
├── tests/                           # 测试代码
│   ├── __init__.py
│   ├── test_module01/
│   ├── test_module02/
│   └── ...
│
├── docs/                            # 文档
│   ├── API.md                       # API文档
│   ├── ARCHITECTURE.md              # 架构文档
│   ├── MODULES.md                   # 模块说明
│   └── DATA_SPEC.md                 # 数据规范
│
├── scripts/                         # 脚本工具
│   ├── migrate_data.py              # 数据迁移脚本
│   ├── check_data_integrity.py      # 数据完整性检查
│   └── generate_test_data.py        # 生成测试数据
│
├── requirements.txt                 # Python依赖
├── .gitignore
├── README.md
└── start_server.py                  # 启动脚本
```

---

## 📝 数据文件命名规范

### 1. **原始数据命名** (data/01_raw/)
```
<group>_<subject_id>_<task_id>.csv

示例:
- control_s001_q1.csv  (对照组，受试者001，任务Q1)
- mci_s042_q3.csv      (MCI组，受试者042，任务Q3)
- ad_s015_q5.csv       (AD组，受试者015，任务Q5)
```

### 2. **处理后数据命名** (data/02_preprocessed/, data/03_calibrated/)
```
<group>_<subject_id>_<task_id>_<processing_stage>.csv

示例:
- control_s001_q1_preprocessed.csv
- mci_s042_q3_calibrated.csv
```

### 3. **特征文件命名** (data/04_features/)
```
<feature_type>_<group>_<timestamp>.csv

示例:
- rqa_features_all_groups_20251001.csv
- event_features_control_20251001.csv
```

### 4. **临床数据命名** (data/01_raw/clinical/)
```
mmse_scores.csv           # MMSE评分
participant_info.csv      # 受试者信息
group_assignments.csv     # 分组信息
```

**MMSE数据格式**:
```csv
subject_id,group,task_q1_score,task_q1_max,task_q2_score,task_q2_max,...
s001,control,5,5,4,5,3,3,5,5,3,3
s042,mci,4,5,3,5,2,3,3,5,1,3
s015,ad,3,5,2,5,1,3,2,5,0,3
```

### 5. **模型文件命名** (data/05_models/)
```
<model_type>_<version>_<training_date>.pth

示例:
- mlp_classifier_v1.0_20251001.pth
- eye_index_model_v2.3_20251015.pth
```

---

## 🔧 代码组织原则

### 1. **单一职责原则**
- 每个文件不超过 **300行**
- 每个函数不超过 **50行**
- 每个类不超过 **200行**

### 2. **模块独立原则**
- 每个模块有独立的 API、Service、Static
- 模块间通过明确的接口通信
- 避免循环依赖

### 3. **前后端分离**
- HTML文件只包含页面结构和模块专属JS（不超过500行）
- 所有共用JS提取到独立文件
- API和业务逻辑完全分离

### 4. **配置外部化**
- 所有路径、常量、配置集中管理
- 支持环境变量覆盖
- 便于测试和部署

---

## 📂 核心文件说明

### 1. **config/settings.py** - 全局配置
```python
# 示例结构
import os
from pathlib import Path

class Config:
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent

    # 数据目录
    DATA_ROOT = PROJECT_ROOT / "data"
    RAW_DATA_DIR = DATA_ROOT / "01_raw"
    PREPROCESSED_DATA_DIR = DATA_ROOT / "02_preprocessed"

    # 服务器配置
    HOST = "127.0.0.1"
    PORT = 8080
    DEBUG = False

    # GPU配置
    USE_GPU = True
    GPU_BATCH_SIZE = 16
```

### 2. **src/web/app.py** - Flask应用入口
```python
# 示例结构（不超过150行）
from flask import Flask
from src.web.routes import register_routes
from src.web.middleware import setup_cors

def create_app():
    app = Flask(__name__)

    # 加载配置
    app.config.from_object('config.settings.Config')

    # 设置中间件
    setup_cors(app)

    # 注册路由
    register_routes(app)

    return app
```

### 3. **模块API文件** (示例: src/modules/module01_visualization/api.py)
```python
# 每个模块的API文件不超过100行
from flask import Blueprint, request, jsonify
from .service import VisualizationService

bp = Blueprint('module01', __name__, url_prefix='/api/module01')
service = VisualizationService()

@bp.route('/visualize/<group>/<data_id>', methods=['GET'])
def visualize_data(group, data_id):
    """可视化指定数据"""
    params = request.args.to_dict()
    result = service.generate_visualization(group, data_id, params)
    return jsonify(result)
```

### 4. **模块Service文件** (示例: src/modules/module01_visualization/service.py)
```python
# 业务逻辑文件，200行左右
from src.core.data_loader import DataLoader
from .renderer import PlotRenderer

class VisualizationService:
    def __init__(self):
        self.loader = DataLoader()
        self.renderer = PlotRenderer()

    def generate_visualization(self, group, data_id, params):
        """生成可视化图表"""
        # 1. 加载数据（20行）
        data = self.loader.load_calibrated_data(group, data_id)

        # 2. 数据验证（10行）
        if not self._validate_data(data):
            return {'success': False, 'error': '数据格式错误'}

        # 3. 渲染图表（30行）
        plot = self.renderer.render(data, params)

        return {'success': True, 'plot': plot}
```

---

## 🚀 迁移策略

### 阶段1: 基础架构搭建（第1周）
1. ✅ 创建新项目目录结构
2. ⬜ 配置文件系统 (config/)
3. ⬜ 核心工具类 (core/)
4. ⬜ Web框架搭建 (web/app.py)

### 阶段2: 数据层迁移（第2周）
1. ⬜ 数据目录重组
2. ⬜ MMSE数据统一格式
3. ⬜ 数据加载器重写
4. ⬜ 数据完整性检查

### 阶段3: 模块逐个迁移（第3-6周）
**优先级顺序**:
1. **Module 1** (可视化) - 最基础
2. **Module 8** (MMSE) - 提供数据支持
3. **Module 2** (数据导入) - 数据流入口
4. **Module 3** (RQA分析) - 核心功能
5. **Module 4** (事件分析)
6. **Module 5** (RQA批处理) - 包含GPU优化
7. **Module 6** (特征提取)
8. **Module 7** (数据整合)
9. **Module 9** (机器学习)
10. **Module 10** (Eye-Index) - 最复杂

### 阶段4: 测试和优化（第7周）
1. ⬜ 单元测试覆盖
2. ⬜ 集成测试
3. ⬜ 性能优化
4. ⬜ 文档完善

---

## 📊 预期改进效果

| 指标 | 当前状态 | 重构后 | 改进 |
|------|---------|--------|------|
| 主HTML文件行数 | 19,504行 | ~500行 | ⬇️ 97% |
| 单个Python文件最大行数 | 2,577行 | ~300行 | ⬇️ 88% |
| 模块独立性 | 低（耦合严重） | 高（完全独立） | ⬆️ 显著 |
| 代码可维护性 | 差 | 优秀 | ⬆️ 显著 |
| 新功能开发效率 | 低 | 高 | ⬆️ 2-3倍 |
| Bug定位时间 | 长 | 短 | ⬇️ 50% |

---

## 📌 注意事项

1. **向后兼容**: 旧数据格式需要迁移脚本支持
2. **逐步迁移**: 新旧系统并行，逐模块切换
3. **测试优先**: 每个模块迁移后立即测试
4. **文档同步**: 代码和文档同步更新
5. **版本控制**: 使用Git分支管理迁移过程

---

## 下一步行动

1. ✅ 创建 `new_project/` 目录
2. ✅ 编写此重构方案文档
3. ⬜ 创建详细的模块功能清单
4. ⬜ 开始基础架构代码编写
5. ⬜ 数据迁移脚本开发
