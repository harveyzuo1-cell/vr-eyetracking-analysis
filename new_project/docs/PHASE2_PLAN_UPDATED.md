# 第2阶段计划（更新版）

## 📅 时间：第2周

## 🎯 目标（已调整）

原计划只做数据迁移，现在**增加前端React框架搭建**，为后续模块开发打好基础。

---

## 📋 任务清单

### 2.1 前端框架搭建 ⭐ 新增

#### 2.1.1 创建React项目
- [ ] 使用Vite创建React项目
- [ ] 配置开发环境（ESLint, Prettier）
- [ ] 集成UI组件库（Ant Design）
- [ ] 配置路由系统（React Router）

#### 2.1.2 项目结构规划
```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/          # 可复用组件
│   │   ├── Layout/         # 布局组件
│   │   ├── DataTable/      # 数据表格
│   │   ├── Charts/         # 图表组件
│   │   └── Controls/       # 控制组件
│   ├── pages/              # 页面（10个模块）
│   │   ├── Dashboard/      # 首页
│   │   ├── Module01/       # 数据可视化
│   │   ├── Module02/       # 数据导入
│   │   └── ...
│   ├── services/           # API服务
│   │   ├── api.js         # 基础API配置
│   │   ├── dataService.js # 数据API
│   │   └── rqaService.js  # RQA API
│   ├── utils/              # 工具函数
│   ├── hooks/              # 自定义Hooks
│   ├── store/              # 状态管理
│   ├── App.jsx
│   └── main.jsx
├── package.json
└── vite.config.js
```

#### 2.1.3 基础组件开发
- [ ] Layout布局组件（顶部导航、侧边栏、内容区）
- [ ] API服务封装（Axios配置、统一错误处理）
- [ ] 路由配置（10个模块路由）
- [ ] 全局状态管理（用户设置、数据缓存）

#### 2.1.4 示例页面
- [ ] 首页Dashboard（项目概览）
- [ ] 模块1框架（验证前后端通信）

---

### 2.2 后端API规范 ⭐ 新增

#### 2.2.1 统一API响应格式
```json
// 成功响应
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}

// 失败响应
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}

// 分页响应
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

#### 2.2.2 API端点规划
```
GET    /api/health              # 健康检查
GET    /api/info                # 系统信息

# 数据管理
GET    /api/data/groups         # 获取组别列表
GET    /api/data/subjects       # 获取受试者列表
GET    /api/data/tasks          # 获取任务列表
GET    /api/data/raw            # 获取原始数据
POST   /api/data/import         # 导入数据

# MMSE
GET    /api/mmse/scores         # 获取MMSE分数
GET    /api/mmse/groups         # 按组别获取

# RQA分析
POST   /api/rqa/analyze         # 执行RQA分析
GET    /api/rqa/results         # 获取结果
POST   /api/rqa/batch           # 批量处理

# 机器学习
POST   /api/ml/train            # 训练模型
POST   /api/ml/predict          # 预测
GET    /api/ml/models           # 模型列表
```

---

### 2.3 数据迁移（原计划）

#### 2.3.1 数据迁移脚本
- [ ] 编写 `scripts/migrate_data.py`
- [ ] 重组数据目录（01_raw ~ 06_results）
- [ ] 转换文件命名（统一格式）
- [ ] 合并MMSE数据（3个中文CSV → 1个英文CSV）

#### 2.3.2 数据验证
- [ ] 编写 `scripts/check_data_integrity.py`
- [ ] 验证所有数据文件
- [ ] 检查命名规范
- [ ] 生成数据报告

---

## 🛠️ 技术栈

### 前端
```json
{
  "react": "^18.2.0",
  "vite": "^5.0.0",
  "antd": "^5.12.0",
  "react-router-dom": "^6.20.0",
  "axios": "^1.6.0",
  "recharts": "^2.10.0",
  "plotly.js-dist": "^2.27.0",
  "zustand": "^4.4.0"
}
```

### 后端（已完成）
```python
Flask==2.3.0
flask-cors==4.0.0
pandas==2.0.0
numpy==1.24.0
```

---

## 📈 为什么选择React + Vite？

### React优势
1. **组件化开发** - 每个模块独立开发，易维护
2. **丰富生态** - 大量现成的图表、UI组件
3. **高性能** - Virtual DOM，适合数据密集型应用
4. **TypeScript支持** - 可选的类型安全

### Vite优势
1. **极速启动** - 冷启动 < 1秒
2. **热更新快** - 修改代码立即生效
3. **现代化** - 原生支持ESM、TypeScript
4. **配置简单** - 开箱即用

### Ant Design优势
1. **企业级UI** - 专业的数据展示组件
2. **完整图表** - Table、Chart、Form组件齐全
3. **中文文档** - 学习成本低
4. **主题定制** - 可自定义样式

---

## 🎨 前端组件规划

### 布局组件
```jsx
<MainLayout>
  <Header>
    <Logo />
    <Navigation />
  </Header>
  <Sidebar>
    <ModuleMenu />
  </Sidebar>
  <Content>
    {/* 各模块页面 */}
  </Content>
</MainLayout>
```

### 数据可视化组件
```jsx
// 眼动轨迹图
<GazeTrajectoryChart data={gazeData} />

// RQA递归图
<RecurrencePlot matrix={rqaMatrix} />

// 热力图
<HeatmapChart data={heatmapData} />

// 统计图表
<BarChart data={statistics} />
```

### 数据表格组件
```jsx
<DataTable
  columns={columns}
  data={data}
  pagination
  sortable
  filterable
  exportable
/>
```

---

## 🔄 前后端通信

### API调用示例
```javascript
// services/dataService.js
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:9090/api';

export const dataService = {
  // 获取受试者列表
  async getSubjects(group) {
    const response = await axios.get(`${API_BASE}/data/subjects`, {
      params: { group }
    });
    return response.data;
  },

  // 加载原始数据
  async loadRawData(group, subjectId, taskId) {
    const response = await axios.get(`${API_BASE}/data/raw`, {
      params: { group, subject_id: subjectId, task_id: taskId }
    });
    return response.data;
  }
};
```

### React组件使用
```jsx
// pages/Module01/DataVisualization.jsx
import { useState, useEffect } from 'react';
import { dataService } from '@/services/dataService';

function DataVisualization() {
  const [subjects, setSubjects] = useState([]);

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const result = await dataService.getSubjects('control');
      if (result.success) {
        setSubjects(result.data);
      }
    } catch (error) {
      console.error('加载失败:', error);
    }
  };

  return (
    <div>
      <h1>数据可视化</h1>
      <SubjectSelector subjects={subjects} />
    </div>
  );
}
```

---

## 📦 第2阶段交付物

### 前端
- ✅ React + Vite项目框架
- ✅ 完整的目录结构
- ✅ 布局组件（Header, Sidebar, Content）
- ✅ API服务封装
- ✅ 路由配置（10个模块）
- ✅ 首页Dashboard
- ✅ 模块1示例页面

### 后端
- ✅ 统一API响应格式
- ✅ 基础API端点（数据列表、信息查询）
- ✅ CORS配置（支持前端调用）

### 数据
- ✅ 数据迁移脚本
- ✅ 重组后的数据目录
- ✅ 统一的MMSE数据文件
- ✅ 数据完整性报告

---

## ⏱️ 时间估算

| 任务 | 时间 | 说明 |
|------|------|------|
| React项目搭建 | 0.5天 | Vite快速创建 |
| 目录结构规划 | 0.5天 | 参考最佳实践 |
| 布局组件开发 | 1天 | Header/Sidebar/Content |
| API服务封装 | 0.5天 | Axios配置 |
| 路由配置 | 0.5天 | 10个模块路由 |
| 首页开发 | 1天 | Dashboard |
| 后端API规范 | 0.5天 | 统一响应格式 |
| 数据迁移脚本 | 1.5天 | 完整迁移逻辑 |
| 数据验证 | 0.5天 | 完整性检查 |
| **总计** | **7天** | 约1周 |

---

## 🎯 第3阶段预览

有了React框架后，第3阶段模块迁移会更快：

### 模块开发流程
1. **后端**: 在 `src/modules/moduleXX/` 实现API
2. **前端**: 在 `frontend/src/pages/ModuleXX/` 实现页面
3. **测试**: 前后端联调
4. **部署**: 合并到主分支

### 预计时间
- 每个模块：2-3天
- 10个模块：4周

---

## 🤔 需要确认的问题

### 1. UI组件库选择
- **Ant Design** (推荐) - 企业级，组件全
- **Material-UI** - Google风格，国际化
- **您的偏好？**

### 2. 图表库选择
- **Recharts** - React原生，简单
- **Plotly.js** - 功能强大，交互丰富（旧项目在用）
- **ECharts** - 百度出品，中文文档好
- **您的偏好？**

### 3. 状态管理
- **Zustand** (推荐) - 轻量，易用
- **Redux** - 成熟，生态好，但复杂
- **您的偏好？**

### 4. 开发优先级
- **选项A**: 先完成前端框架 + 数据迁移（第2阶段）
- **选项B**: 先完成数据迁移，再做前端框架
- **您的偏好？**

---

## 📝 下一步

等待您的确认：
1. 是否采用React + Vite方案？
2. UI组件库选择？
3. 图表库选择？
4. 开发优先级？

确认后我将立即开始实施！
