# RQA分析功能集成指南

## 📋 概述

本指南介绍如何将RQA（递归量化分析）功能集成到VR眼动数据处理工具中。

## 🏗️ 系统架构

```
VR眼动数据处理工具 + RQA分析模块
├── 前端界面 (enhanced_index.html)
│   ├── 侧边栏导航项
│   ├── 参数配置面板
│   └── 结果展示面板
├── 后端API (rqa_api_extension.py)
│   ├── /api/rqa-analysis
│   ├── /api/rqa-comparison
│   └── /api/rqa-parameters
└── 分析引擎 (analysis/rqa_analyzer.py)
    ├── 数据预处理
    ├── 嵌入空间构建
    ├── 递归矩阵计算
    └── RQA指标提取
```

## 🚀 快速集成

### 1. **安装依赖**

```bash
pip install -r requirements.txt
```

新增依赖：
- `seaborn>=0.11.0` (用于高级可视化)

### 2. **集成到现有后端**

在 `visualization/enhanced_web_visualizer.py` 的 `__init__` 方法末尾添加：

```python
# 在EnhancedWebVisualizer.__init__方法的最后添加
try:
    from rqa_api_extension import setup_rqa_integration
    setup_rqa_integration(self.app, self)
    print("✅ RQA分析功能已启用")
except ImportError as e:
    print(f"⚠️  RQA分析功能不可用: {e}")
```

### 3. **验证集成**

启动服务器后，检查控制台输出：

```
🔬 RQA分析API路由已添加:
  - POST /api/rqa-analysis
  - POST /api/rqa-comparison
  - GET  /api/rqa-parameters
```

## 📊 功能特性

### 🎯 **前端界面**

#### 侧边栏导航
- **图标**: `fas fa-project-diagram`
- **标题**: RQA分析 / RQA Analysis
- **切换函数**: `switchToRQAAnalysis()`

#### 参数配置面板
- **嵌入维度 (m)**: 2-10，默认3
- **时间延迟 (τ)**: 1-20，默认1  
- **递归阈值 (ε)**: 0.01-1.0，默认0.1
- **最小线长 (l_min)**: 2-10，默认2

#### 结果展示面板
- **递归图**: 可视化递归模式
- **RQA指标**: 9项量化指标
- **对比分析**: 组间对比功能

### 🔬 **RQA指标**

| 指标 | 英文名称 | 含义 |
|------|----------|------|
| RR | Recurrence Rate | 递归率 |
| DET | Determinism | 确定性 |
| LAM | Laminarity | 层流性 |
| L | Average Diagonal Line Length | 平均对角线长度 |
| Lmax | Maximum Diagonal Line Length | 最大对角线长度 |
| DIV | Divergence | 发散性 |
| TT | Trapping Time | 平均垂直线长度 |
| Vmax | Maximum Vertical Line Length | 最大垂直线长度 |
| ENTR | Entropy | 熵 |

### 🌐 **API接口**

#### 1. RQA分析
```http
POST /api/rqa-analysis
Content-Type: application/json

{
  "group_type": "control",
  "data_id": "n1q1",
  "parameters": {
    "embedding_dimension": 3,
    "time_delay": 1,
    "recurrence_threshold": 0.1,
    "min_line_length": 2
  }
}
```

**响应**:
```json
{
  "success": true,
  "recurrence_plot": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "metrics": {
    "RR": 0.123456,
    "DET": 0.789012,
    "LAM": 0.456789,
    "L": 12.34,
    "Lmax": 45,
    "DIV": 0.022222,
    "TT": 8.76,
    "Vmax": 23,
    "ENTR": 2.345678
  },
  "parameters": {...},
  "data_info": {
    "total_points": 1000,
    "embedding_points": 998
  }
}
```

#### 2. 组间对比
```http
POST /api/rqa-comparison
Content-Type: application/json

{
  "datasets": [
    {"group_type": "control", "data_id": "n1q1"},
    {"group_type": "mci", "data_id": "m1q1"},
    {"group_type": "ad", "data_id": "ad1q1"}
  ],
  "parameters": {...}
}
```

#### 3. 获取默认参数
```http
GET /api/rqa-parameters
```

## 🛠️ 技术实现

### 数据处理流程

```python
# 1. 数据预处理
x_coords, y_coords = preprocess_data(df)
↓
# 2. 构建嵌入空间  
embedded_data = embed_data(x_coords, y_coords, m, tau)
↓
# 3. 计算递归矩阵
recurrence_matrix = compute_recurrence_matrix(embedded_data, epsilon)
↓
# 4. 生成递归图
recurrence_plot = create_recurrence_plot(recurrence_matrix)
↓
# 5. 计算RQA指标
metrics = compute_rqa_metrics(recurrence_matrix, l_min)
```

### 核心算法

#### 嵌入空间构建
```python
# Takens嵌入定理
for i in range(embedded_points):
    for j in range(embedding_dim):
        delay_idx = i + j * time_delay
        embedded_data[i, j*2] = x_coords[delay_idx]
        embedded_data[i, j*2+1] = y_coords[delay_idx]
```

#### 递归矩阵计算
```python
# 欧几里得距离
distances = squareform(pdist(embedded_data, metric='euclidean'))
# 阈值化
recurrence_matrix = distances <= threshold
```

## 🧪 测试与验证

### 功能测试

1. **参数验证**
   ```bash
   curl -X GET http://localhost:8080/api/rqa-parameters
   ```

2. **单组分析**
   ```bash
   curl -X POST http://localhost:8080/api/rqa-analysis \
        -H "Content-Type: application/json" \
        -d '{"group_type":"control","data_id":"n1q1","parameters":{}}'
   ```

3. **对比分析**
   ```bash
   curl -X POST http://localhost:8080/api/rqa-comparison \
        -H "Content-Type: application/json" \
        -d '{"datasets":[{"group_type":"control","data_id":"n1q1"},{"group_type":"mci","data_id":"m1q1"}]}'
   ```

### 预期结果

- ✅ 递归图正常生成并显示
- ✅ 9项RQA指标正确计算  
- ✅ 界面参数实时更新
- ✅ 多语言本地化正确

## 🔧 故障排除

### 常见问题

1. **RQA分析器不可用**
   ```
   ⚠️ RQA分析器不可用，请确保安装了scipy等依赖包
   ```
   **解决方案**: 运行 `pip install scipy seaborn`

2. **数据文件未找到**
   ```
   未找到数据文件: control/n1q1
   ```
   **解决方案**: 检查数据目录结构和文件命名

3. **嵌入空间构建失败**
   ```
   数据点数量不足以进行嵌入
   ```
   **解决方案**: 减小嵌入维度或时间延迟参数

4. **前端界面显示异常**
   **解决方案**: 检查浏览器控制台，确保JavaScript正确加载

### 调试模式

在开发过程中，可以启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 性能优化

### 计算复杂度

- **嵌入空间**: O(N × m)
- **距离矩阵**: O(N²)
- **递归图生成**: O(N²)
- **指标计算**: O(N²)

### 优化建议

1. **数据量大时** (>5000点)：
   - 增大递归阈值减少计算量
   - 考虑数据抽样

2. **内存优化**：
   - 使用稀疏矩阵存储递归矩阵
   - 分块计算距离矩阵

3. **并行计算**：
   - 多进程计算不同参数组合
   - GPU加速距离计算（需要CUDA）

## 🔮 扩展功能

### 计划中的功能

1. **高级RQA指标**
   - Cross-RQA（交叉递归分析）
   - Joint-RQA（联合递归分析）
   - Multiscale-RQA（多尺度递归分析）

2. **机器学习集成**
   - RQA特征提取
   - 分类模型训练
   - 预测模型构建

3. **实时分析**
   - 流式数据处理
   - 在线参数优化
   - 实时可视化更新

### 贡献指南

欢迎贡献代码和功能建议！

1. Fork项目仓库
2. 创建功能分支
3. 添加测试用例
4. 提交Pull Request

---

**开发团队**: VR眼动数据处理工具开发组  
**最后更新**: 2025年1月28日  
**版本**: v1.0.0 