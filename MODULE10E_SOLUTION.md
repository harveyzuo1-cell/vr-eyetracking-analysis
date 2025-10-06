# 模块10-E 解决方案说明

## 问题描述
子模块10-E: MMSE预测关联性深度可视化中，"Select Model Configuration"无法找到60位成员模拟数据的选项。

## 解决方案

### 1. 创建了60位成员模拟数据集
- 文件: `create_60_member_dataset.py`
- 生成的数据保存在: `data/simulated_60_members/`
- 包含60位参与者（各20位对照组、MCI、AD）
- MMSE分数严格按照临床标准分布

### 2. 更新了后端API
- 文件: `backend/m10e_correlation/correlation_analyzer.py`
  - 添加了`get_available_models()`方法
  - 添加了`_analyze_simulated_dataset()`方法处理60位成员数据
  - 改进了`_generate_mock_roc()`支持多分类ROC曲线

- 文件: `backend/m10e_correlation/api.py`
  - 添加了`/model-configs`端点返回可用模型列表
  - 更新了`/correlation-analysis`端点支持dataset_id参数

### 3. 更新了前端代码
- 文件: `visualization/templates/enhanced_index.html`
  - 修改了API调用端点为`/api/m10e/model-configs`
  - 确保前端正确加载60位成员数据集选项

## 使用方法

### 启动服务器
```bash
cd "C:\Users\asino\Downloads\az - 副本 (11)"
python visualization/enhanced_web_visualizer.py
```

### 在浏览器中操作
1. 打开 http://localhost:5000
2. 导航到模块10-E
3. 在"Select Model Configuration"下拉框中，应该能看到:
   - **60 Member Dataset (English)** - 60位成员模拟数据
   - Default Mock Dataset - 默认模拟数据

4. 选择"60 Member Dataset (English)"
5. 点击"开始分析"按钮
6. 查看生成的可视化结果

## 测试验证

### 运行API测试
```bash
python test_api_module10e.py
```

### 运行数据加载测试
```bash
python test_module10e.py
```

## 数据集特点

### 60位成员数据集
- **对照组(Control)**: 20人，MMSE 27-30分
- **MCI组**: 20人，MMSE 21-26分  
- **AD组**: 20人，MMSE 10-20分
- 包含完整的认知评分（MoCA、CDR-SB、ADAS-Cog）
- 包含眼动追踪特征数据
- 每个任务(Q1-Q5)都有对应的预测值

## 可视化功能

### 支持的分析类型
1. **散点图矩阵**: 真实值 vs 预测值对比
2. **Bland-Altman分析**: 评估预测一致性
3. **ROC曲线**: 
   - 二分类ROC（阈值20、24）
   - 多分类ROC（Control vs All、MCI vs All、AD vs All）
4. **相关性矩阵**: 特征与认知评分的相关性
5. **3D散点图**: 可选的三维可视化

## 注意事项
1. 确保Flask服务器正在运行
2. 确保所有依赖包已安装
3. 数据集文件必须存在于`data/simulated_60_members/`目录
4. API端点已注册在`/api/m10e/`前缀下

## 故障排查
如果仍然看不到60位成员数据集选项：
1. 检查浏览器控制台是否有错误信息
2. 确认API端点是否正常响应: `http://localhost:5000/api/m10e/model-configs`
3. 清除浏览器缓存并刷新页面
4. 检查`data/simulated_60_members/`目录是否存在数据文件