# Module01与ModuleEX ROI数据互通集成设计文档

## 📋 文档信息
- **文档版本**: v1.0
- **创建日期**: 2025-10-03
- **作者**: VR Eye-Tracking Analysis Team
- **状态**: 设计阶段

---

## 1. 问题分析

### 1.1 当前问题

#### 问题1: ROI数据存储位置不统一
- **Module01 (数据可视化)**:
  - 读取路径: `config/roi_v1.json`, `config/roi_v2.json`
  - 格式: 旧的扁平化JSON格式
  - Task命名: `q1`, `q2`, `q3`, `q4`, `q5`

- **ModuleEX (ROI配置管理)**:
  - 读取路径: `data/roi_configs/v1/*.json`, `data/roi_configs/v2/*.json`
  - 格式: 新的分层JSON格式 (keywords/instructions/background)
  - Task命名: `task1`, `task2`, `task3`, `task4`, `task5`

#### 问题2: API端点不完整
- Module01调用 `POST /api/data/roi-stats` 时返回404
- 该端点在Module01的api.py中已定义，但实现可能有问题
- ModuleEX的配置数据无法被Module01的ROI统计功能使用

#### 问题3: 数据格式不兼容
- **旧格式** (config/roi_v1.json):
  ```json
  {
    "version": "v1",
    "layout": "legacy",
    "regions": [
      {"id": "KW_q1_1", "task": "q1", "type": "KW", "coords": [x, y, w, h]}
    ]
  }
  ```

- **新格式** (data/roi_configs/v2/task1_roi.json):
  ```json
  {
    "version": "v2",
    "task_id": "task1",
    "regions": {
      "keywords": [
        {"id": "KW_task1_1", "type": "KW", "normalized_coords": [x, y, w, h]}
      ],
      "instructions": [...],
      "background": [...]
    }
  }
  ```

---

## 2. 架构设计原则

### 2.1 符合项目架构
遵循 `ARCHITECTURE_REVIEW.md` 中的设计原则：
- ✅ **配置驱动**: 使用 `Config.DATA_ROOT` 统一数据路径
- ✅ **前后端分离**: API层与业务逻辑层解耦
- ✅ **模块独立**: 各模块通过标准API交互
- ✅ **统一日志**: 使用 `setup_logger()` 记录操作

### 2.2 数据统一原则
- **单一数据源**: ROI配置统一存储在 `data/roi_configs/{version}/` 目录
- **格式标准化**: 采用新的分层JSON格式（keywords/instructions/background）
- **向后兼容**: 保留旧数据读取能力，提供格式转换工具
- **版本隔离**: v1和v2数据完全独立存储

---

## 3. 解决方案设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     统一ROI数据层                              │
│                 (data/roi_configs/)                           │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   v1/            │         │   v2/            │          │
│  │   - q1_roi.json  │         │   - task1_roi.json│         │
│  │   - q2_roi.json  │         │   - task2_roi.json│         │
│  │   - ...          │         │   - ...          │          │
│  └──────────────────┘         └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                          ↑                    ↑
                          │                    │
         ┌────────────────┴──────────┬─────────┴──────────────┐
         │                           │                        │
    ┌────▼─────┐              ┌──────▼──────┐         ┌──────▼──────┐
    │ Module01 │              │  ModuleEX   │         │  ROI共享    │
    │   API    │              │    API      │         │  Service    │
    │          │              │             │         │             │
    │ GET /roi │              │ GET /config │         │ 格式转换器   │
    │ POST     │              │ POST /save  │         │ 数据验证器   │
    │ /roi-stat│              │             │         │             │
    └──────────┘              └─────────────┘         └─────────────┘
```

### 3.2 关键组件设计

#### 3.2.1 统一ROI服务层 (src/services/roi_service.py)

**功能职责:**
- 提供统一的ROI配置读取接口
- 处理旧格式到新格式的转换
- 统一Task ID映射 (q1 ↔ task1)
- 缓存ROI配置以提升性能

**核心接口:**
```python
class UnifiedROIService:
    """统一ROI配置服务"""

    def get_roi_config(version: str, task: str) -> Dict:
        """
        获取ROI配置（统一接口）

        Args:
            version: v1/v2
            task: q1-q5 或 task1-task5（自动转换）

        Returns:
            标准化的ROI配置数据
        """

    def get_roi_config_by_path(version: str, task: str) -> str:
        """获取ROI配置文件路径"""

    def convert_legacy_to_new(legacy_config: Dict) -> Dict:
        """将旧格式转换为新格式"""

    def normalize_task_id(task: str) -> Tuple[str, str]:
        """
        任务ID标准化

        Returns:
            (legacy_task_id, new_task_id)
            例: ("q1", "task1")
        """
```

#### 3.2.2 数据迁移工具 (scripts/migrate_roi_configs.py)

**功能:**
- 将 `config/roi_v1.json` 拆分为 `data/roi_configs/v1/q{1-5}_roi.json`
- 将 `config/roi_v2.json` 拆分为 `data/roi_configs/v2/q{1-5}_roi.json`
- 转换旧格式到新格式（分层结构）
- 保留原始文件作为备份

**执行流程:**
```
1. 读取 config/roi_v1.json
2. 按task分组regions
3. 转换为新格式（keywords/instructions/background分层）
4. 保存到 data/roi_configs/v1/q{1-5}_roi.json
5. 对roi_v2.json重复上述步骤
6. 验证迁移结果
```

#### 3.2.3 Task ID映射器

**映射关系:**
```python
TASK_ID_MAPPING = {
    # Legacy ID -> New ID
    "q1": "task1",
    "q2": "task2",
    "q3": "task3",
    "q4": "task4",
    "q5": "task5",
    # New ID -> Legacy ID
    "task1": "q1",
    "task2": "q2",
    "task3": "q3",
    "task4": "q4",
    "task5": "q5"
}
```

---

## 4. 实施步骤

### 阶段1: 创建统一ROI服务层 (1-2小时)

**任务清单:**
- [ ] 创建 `src/services/roi_service.py`
- [ ] 实现 `UnifiedROIService` 类
- [ ] 实现Task ID双向映射
- [ ] 实现格式转换器 (legacy ↔ new)
- [ ] 添加单元测试

**文件结构:**
```
src/services/
├── __init__.py
└── roi_service.py          # 新增：统一ROI服务
```

### 阶段2: 数据迁移 (30分钟)

**任务清单:**
- [ ] 创建 `scripts/migrate_roi_configs.py`
- [ ] 备份现有配置文件
- [ ] 执行迁移：config/*.json → data/roi_configs/
- [ ] 验证迁移后的数据完整性
- [ ] 创建v1的ROI配置文件（从roi_v1.json拆分）

**迁移命令:**
```bash
python scripts/migrate_roi_configs.py --backup --validate
```

### 阶段3: 更新Module01 (1小时)

**任务清单:**
- [ ] 修改 `module01_data_visualization/service.py`
  - 使用 `UnifiedROIService` 替代直接读取config文件
  - 更新 `get_roi_config()` 方法
  - 更新 `get_roi_config_enhanced()` 方法
  - 修复 `calculate_roi_stats()` 实现

- [ ] 修改 `module01_data_visualization/api.py`
  - 确保 `/api/data/roi-stats` 端点正常工作
  - 添加错误处理和日志记录

- [ ] 测试v1和v2数据可视化功能

### 阶段4: 更新ModuleEX (30分钟)

**任务清单:**
- [ ] 修改 `moduleEX_roi_config/service.py`
  - 使用统一的Task ID命名 (支持q1-q5和task1-task5)
  - 确保保存的配置与Module01兼容

- [ ] 修改 `moduleEX_roi_config/api.py`
  - 添加Task ID自动转换
  - 统一返回格式

- [ ] 测试ROI配置的保存和加载

### 阶段5: 前端适配 (30分钟)

**任务清单:**
- [ ] 更新 `frontend/src/services/roiService.js`
  - 确保API调用路径正确
  - 添加Task ID转换逻辑

- [ ] 更新 `Module01.jsx`
  - 确保v2数据加载正常
  - 修复ROI统计功能

- [ ] 更新 `ModuleEX/index.jsx`
  - 支持加载v1配置
  - 显示Task ID映射关系

### 阶段6: 测试与验证 (1小时)

**测试用例:**
1. ✅ Module01加载v1数据并显示ROI
2. ✅ Module01加载v2数据并显示ROI
3. ✅ Module01计算v2数据的ROI统计
4. ✅ ModuleEX加载v1的ROI配置
5. ✅ ModuleEX加载v2的ROI配置
6. ✅ ModuleEX保存的配置能被Module01读取
7. ✅ ModuleEX修改v1配置后Module01能正确显示

---

## 5. API接口设计

### 5.1 统一ROI配置接口

#### GET /api/data/roi
**功能**: 获取ROI配置（兼容旧格式）

**请求参数:**
```
version: v1 | v2
task: q1 | q2 | q3 | q4 | q5 | task1 | task2 | task3 | task4 | task5
```

**响应:**
```json
{
  "success": true,
  "data": {
    "version": "v1",
    "task_id": "q1",
    "task_id_new": "task1",
    "regions": {
      "keywords": [...],
      "instructions": [...],
      "background": [...]
    }
  }
}
```

#### GET /api/data/roi-enhanced
**功能**: 获取增强ROI配置（新格式）

**请求参数:**
```
version: v1 | v2
task: q1-q5 或 task1-task5（自动转换）
```

**响应:**
```json
{
  "success": true,
  "data": {
    "version": "v1",
    "task_id": "q1",
    "task_name": "时间定向",
    "background_image": "/static/background_images/v1/Q1.jpg",
    "regions": {
      "keywords": [...],
      "instructions": [...],
      "background": [...]
    }
  }
}
```

#### POST /api/data/roi-stats
**功能**: 计算ROI统计信息

**请求Body:**
```json
{
  "version": "v1",
  "task": "q1",
  "gaze_data": [
    {"x": 0.5, "y": 0.5, "timestamp": 0.0},
    ...
  ]
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "stats": {
      "KW_q1_1": {
        "fixation_time": 2.5,
        "entry_count": 3,
        "regression_count": 2
      }
    },
    "summary": {
      "total_fixation_time": 10.5,
      "keywords_fixation_time": 5.2
    }
  }
}
```

### 5.2 ModuleEX配置接口

#### GET /api/config/roi-configs
**功能**: 获取ROI配置列表

**请求参数:**
```
version: v1 | v2
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "filename": "q1_roi.json",
      "task_id": "q1",
      "task_id_new": "task1",
      "version": "v1",
      "modified_time": "2025-10-03T14:00:00"
    }
  ]
}
```

#### POST /api/config/roi-configs
**功能**: 保存ROI配置

**请求Body:**
```json
{
  "version": "v2",
  "task_id": "task1",  // 自动转换为q1
  "regions": {
    "keywords": [...],
    "instructions": [...],
    "background": [...]
  }
}
```

---

## 6. 数据格式标准

### 6.1 统一ROI配置格式

```json
{
  "version": "v1|v2",
  "task_id": "q1|task1",
  "task_name": "时间定向",
  "background_image": "q1.png|task1.png",
  "regions": {
    "keywords": [
      {
        "id": "KW_q1_1",
        "type": "KW",
        "normalized_coords": [x, y, w, h],
        "task_id": "q1",
        "version": "v1"
      }
    ],
    "instructions": [
      {
        "id": "INST_q1_1",
        "type": "INST",
        "normalized_coords": [x, y, w, h],
        "task_id": "q1",
        "version": "v1"
      }
    ],
    "background": [
      {
        "id": "BG_q1",
        "type": "BG",
        "normalized_coords": [0, 0, 1, 1],
        "task_id": "q1",
        "version": "v1"
      }
    ]
  },
  "last_modified": "2025-10-03T14:00:00"
}
```

### 6.2 Task ID标准化规则

| 版本 | Module01使用 | ModuleEX使用 | 文件命名 | ROI ID前缀 |
|------|-------------|-------------|---------|-----------|
| v1   | q1-q5       | q1-q5       | q{1-5}_roi.json | KW_q1_1 |
| v2   | q1-q5       | task1-task5 | q{1-5}_roi.json | KW_q1_1 |

**说明:**
- 内部统一使用 `q1-q5` 作为Task ID
- ModuleEX前端显示可以用 `task1-task5`
- 文件名统一使用 `q{1-5}_roi.json`
- ROI区域ID保持 `KW_q1_1` 格式

---

## 7. 风险与注意事项

### 7.1 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 数据迁移失败 | 高 | 低 | 1. 迁移前备份<br>2. 分步验证<br>3. 回滚方案 |
| 格式转换错误 | 中 | 中 | 1. 单元测试<br>2. 数据验证<br>3. 人工检查 |
| API兼容性问题 | 高 | 低 | 1. 向后兼容设计<br>2. 版本控制<br>3. 渐进式迁移 |
| 性能下降 | 低 | 低 | 1. 配置缓存<br>2. 延迟加载<br>3. 性能监控 |

### 7.2 注意事项

1. **数据备份**: 在迁移前必须备份 `config/roi_v1.json` 和 `config/roi_v2.json`
2. **渐进式迁移**: 先支持读取旧格式，再逐步迁移到新格式
3. **兼容性测试**: 确保所有现有功能在迁移后仍正常工作
4. **文档更新**: 更新API文档和用户手册

---

## 8. 验收标准

### 8.1 功能验收

- [ ] Module01能加载v1的ROI配置并正常显示
- [ ] Module01能加载v2的ROI配置并正常显示
- [ ] Module01能计算v1和v2的ROI统计数据
- [ ] ModuleEX能加载v1的ROI配置进行编辑
- [ ] ModuleEX能加载v2的ROI配置进行编辑
- [ ] ModuleEX保存的配置能被Module01正确读取
- [ ] Task ID在两个模块间正确映射（q1↔task1）

### 8.2 性能验收

- [ ] ROI配置加载时间 < 500ms
- [ ] ROI统计计算时间 < 1s（1000个数据点）
- [ ] 配置保存响应时间 < 300ms

### 8.3 质量验收

- [ ] 代码通过单元测试（覆盖率>80%）
- [ ] 代码符合项目架构规范
- [ ] 日志记录完整（Info/Error/Debug）
- [ ] API返回格式统一

---

## 9. 开发时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 1 | 创建统一ROI服务层 | 1-2小时 |
| 2 | 数据迁移脚本 | 30分钟 |
| 3 | 更新Module01 | 1小时 |
| 4 | 更新ModuleEX | 30分钟 |
| 5 | 前端适配 | 30分钟 |
| 6 | 测试与验证 | 1小时 |
| **总计** | | **4.5-5.5小时** |

---

## 10. 后续优化建议

1. **ROI配置版本控制**: 实现配置历史记录和回滚功能
2. **批量操作**: 支持批量导入/导出ROI配置
3. **可视化预览**: ModuleEX中预览Module01的显示效果
4. **智能推荐**: 基于v1配置自动生成v2配置建议
5. **配置模板**: 提供常用ROI配置模板库

---

## 附录

### A. 文件路径对照表

| 数据类型 | 旧路径 | 新路径 |
|---------|--------|--------|
| v1 ROI配置 | `config/roi_v1.json` | `data/roi_configs/v1/q{1-5}_roi.json` |
| v2 ROI配置 | `config/roi_v2.json` | `data/roi_configs/v2/q{1-5}_roi.json` |
| v1 背景图片 | `data/background_images/v1/Q{1-5}.jpg` | 保持不变 |
| v2 背景图片 | `data/background_images/v2/task{1-5}.png` | 保持不变 |

### B. 相关文档

- [Module01 ROI增强设计](MODULE01_ROI_ENHANCEMENT_PLAN.md)
- [Module01 ROI可视化设计](MODULE01_ROI_VISUALIZATION_DESIGN.md)
- [架构设计评审](ARCHITECTURE_REVIEW.md)

---

**文档状态**: 待评审
**下一步行动**: 评审通过后开始阶段1开发
