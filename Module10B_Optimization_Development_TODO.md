# Module 10-B 优化开发TODO List
## 📋 分任务个性化训练实施方案

---

## 🎯 Phase 1: 配置架构改造
*目标：支持统一配置、智能优化、自定义三种模式*

### 1.1 前端改造 (enhanced_index.html)

#### 1.1.1 配置模式选择器
- [ ] 在第5021行"训练配置"卡片中添加配置模式选择
  ```html
  位置：enhanced_index.html 第5030行后
  - 添加单选按钮组：统一配置 | 智能优化 | 自定义配置
  - 添加模式说明提示文本
  - 绑定切换事件处理函数
  ```

#### 1.1.2 任务特定参数区域
- [ ] 创建动态参数卡片生成函数
  ```javascript
  位置：创建新函数 generateTaskSpecificParams()
  - 根据选中的任务（Q1-Q5）生成独立参数卡片
  - 每个卡片包含完整参数集
  - 支持从统一配置复制参数
  ```

- [ ] 修改现有参数输入区域
  ```html
  位置：第5060-5150行附近
  - 添加div容器 id="task-specific-params-container"
  - 根据模式切换显示/隐藏
  - 保留现有输入作为统一配置
  ```

#### 1.1.3 参数联动和验证
- [ ] 实现批量应用功能
  ```javascript
  - 添加"应用到所有任务"按钮
  - 实现参数复制函数
  - 添加参数验证逻辑
  ```

### 1.2 后端改造

#### 1.2.1 配置管理器 (backend/m10_training/config_manager.py - 新建)
- [ ] 创建TaskConfigManager类
  ```python
  class TaskConfigManager:
      def __init__(self, base_config_path):
          # 加载基础配置
      
      def get_unified_config(self, override_params):
          # 返回统一配置
      
      def get_optimized_config(self, task):
          # 返回任务优化配置
      
      def get_custom_config(self, task, params):
          # 返回自定义配置
      
      def validate_config(self, config):
          # 配置验证
  ```

#### 1.2.2 预设优化配置 (backend/m10_training/optimized_configs.yaml - 新建)
- [ ] 创建任务优化配置文件
  ```yaml
  # 基于R²分析的优化配置
  Q1:
    arch:
      h1: 64
      h2: 32
      activation: "leaky_relu"
    training:
      lr: 0.0005
      batch_size: 16
  
  Q2:
    arch:
      h1: 48
      h2: 24
      activation: "elu"
    # ...
  ```

#### 1.2.3 训练接口升级 (backend/m10_training/api.py)
- [ ] 修改训练API端点（第71-150行）
  ```python
  位置：run_training_job 函数
  - 添加 config_mode 参数解析
  - 根据模式调用不同配置生成器
  - 支持任务特定配置
  ```

- [ ] 添加配置预览API
  ```python
  @m10b_bp.route('/preview-config', methods=['POST'])
  def preview_config():
      # 返回将要使用的配置
  ```

---

## 🏗️ Phase 2: 网络结构灵活性

### 2.1 前端扩展

#### 2.1.1 网络架构配置UI
- [ ] 替换固定隐藏层输入（第5090-5100行）
  ```html
  改造内容：
  - 添加层数选择下拉框（1-5层）
  - 动态生成层参数输入
  - 添加预设结构快速选择
  ```

- [ ] 添加网络结构预览
  ```javascript
  function previewNetworkStructure():
      - 实时显示网络层级
      - 显示参数数量
      - 可视化网络结构
  ```

#### 2.1.2 激活函数选择
- [ ] 添加激活函数下拉选择
  ```html
  位置：在dropout输入后添加
  - 选项：ReLU, LeakyReLU, ELU, Tanh, GELU
  - 添加任务推荐提示
  ```

### 2.2 后端扩展

#### 2.2.1 模型构建优化 (backend/m10_training/model.py)
- [ ] 创建灵活网络构建器
  ```python
  class FlexibleMLP(nn.Module):
      def __init__(self, config):
          # 支持可变层数
          # 支持每层不同配置
  ```

- [ ] 扩展激活函数支持（第60-67行）
  ```python
  添加：
  - GELU激活函数
  - Tanh激活函数
  - Swish激活函数
  ```

#### 2.2.2 更新create_model_from_config (backend/m10_training/model.py)
- [ ] 支持新的配置格式
  ```python
  def create_model_from_config(config):
      if config.get('flexible_arch'):
          return FlexibleMLP(config)
      else:
          return EyeMLP(...)  # 保持向后兼容
  ```

---

## 🔧 Phase 3: 训练策略优化

### 3.1 前端增强

#### 3.1.1 优化器配置
- [ ] 添加优化器选择下拉框
  ```html
  位置：学习率输入附近
  - 选项：Adam, AdamW, SGD, RMSprop
  - 根据选择显示特定参数
  ```

- [ ] 优化器特定参数
  ```javascript
  动态显示：
  - Adam: beta1, beta2, epsilon
  - SGD: momentum, nesterov
  - AdamW: weight_decay
  ```

#### 3.1.2 学习率策略
- [ ] 添加调度器选择
  ```html
  - StepLR: 阶梯下降
  - CosineAnnealingLR: 余弦退火
  - ReduceLROnPlateau: 自适应（当前）
  - ExponentialLR: 指数衰减
  ```

#### 3.1.3 损失函数选择
- [ ] 添加损失函数下拉框
  ```html
  - MSE（默认）
  - MAE
  - Huber
  - SmoothL1
  ```

### 3.2 后端增强

#### 3.2.1 训练循环改造 (backend/m10_training/trainer.py)
- [ ] 扩展优化器创建（第84-88行）
  ```python
  def create_optimizer(model, config):
      optimizer_type = config.get('optimizer', 'adam')
      if optimizer_type == 'adam':
          return torch.optim.Adam(...)
      elif optimizer_type == 'adamw':
          return torch.optim.AdamW(...)
      # ...
  ```

- [ ] 实现多种学习率调度器（第94-103行）
  ```python
  def create_scheduler(optimizer, config):
      scheduler_type = config.get('scheduler_type')
      # 实现各种调度器
  ```

- [ ] 支持不同损失函数（第91行）
  ```python
  def create_criterion(config):
      loss_type = config.get('loss', 'mse')
      # 返回对应损失函数
  ```

---

## 🎨 Phase 4: 预设配置系统

### 4.1 前端快速配置

#### 4.1.1 预设配置选择器
- [ ] 添加快速配置按钮组
  ```html
  位置：配置模式选择器下方
  - 保守配置（稳定但慢）
  - 平衡配置（推荐）
  - 激进配置（快速但可能不稳定）
  - 任务最优（基于历史数据）
  ```

#### 4.1.2 配置对比视图
- [ ] 创建配置对比模态框
  ```javascript
  function showConfigComparison():
      - 显示当前配置 vs 推荐配置
      - 高亮差异
      - 预期性能提升预测
  ```

### 4.2 后端预设管理

#### 4.2.1 预设配置库 (backend/m10_training/presets.py - 新建)
- [ ] 定义预设配置
  ```python
  PRESET_CONFIGS = {
      'conservative': {...},
      'balanced': {...},
      'aggressive': {...},
      'task_optimized': {
          'Q1': {...},
          'Q2': {...},
          # 基于R²分析结果
      }
  }
  ```

#### 4.2.2 配置推荐算法
- [ ] 实现智能推荐
  ```python
  def recommend_config(task, data_stats):
      # 基于任务和数据特征推荐配置
      # 考虑历史训练结果
  ```

---

## 📊 Phase 5: 监控和反馈

### 5.1 前端监控

#### 5.1.1 分任务训练监控
- [ ] 改造训练进度显示
  ```javascript
  位置：训练监控区域
  - 为每个任务创建独立进度条
  - 显示任务特定的损失曲线
  - 添加任务间对比图表
  ```

#### 5.1.2 配置效果分析
- [ ] 添加配置历史记录
  ```javascript
  - 记录每次训练的配置
  - 显示配置-性能关系
  - 推荐最佳配置
  ```

### 5.2 后端日志

#### 5.2.1 训练日志系统 (backend/m10_training/utils/logger.py)
- [ ] 扩展日志记录
  ```python
  class EnhancedTrainingLogger:
      def log_task_config(self, task, config):
          # 记录任务特定配置
      
      def log_comparison(self, tasks_results):
          # 记录任务间对比
  ```

#### 5.2.2 配置-性能映射
- [ ] 创建性能数据库
  ```python
  # 保存历史配置和对应的性能
  def save_config_performance(config, metrics):
      # 保存到JSON或数据库
  ```

---

## 🧪 Phase 6: 特征工程（可选）

### 6.1 前端选项

#### 6.1.1 特征处理选择
- [ ] 添加特征工程选项卡
  ```html
  - 特征标准化方法
  - 特征选择策略
  - 多项式特征
  - 数据增强选项
  ```

### 6.2 后端处理

#### 6.2.1 特征工程管道 (backend/m10_training/feature_engineering.py - 新建)
- [ ] 实现特征处理
  ```python
  class FeatureProcessor:
      def __init__(self, method='standard'):
          # 初始化处理器
      
      def transform(self, X, task=None):
          # 任务特定的特征处理
  ```

---

## ✅ Phase 7: 测试和优化

### 7.1 功能测试

#### 7.1.1 单元测试
- [ ] 创建测试文件 (tests/test_module10b_optimization.py)
  ```python
  - 测试配置管理器
  - 测试模型构建
  - 测试训练流程
  ```

#### 7.1.2 集成测试
- [ ] 测试完整流程
  ```python
  - 测试三种配置模式
  - 测试多任务训练
  - 测试结果一致性
  ```

### 7.2 性能优化

#### 7.2.1 并行训练支持
- [ ] 实现多任务并行训练
  ```python
  def parallel_train_tasks(tasks, configs):
      # 使用多进程或多线程
  ```

#### 7.2.2 配置缓存机制
- [ ] 缓存优化配置
  ```python
  - 缓存常用配置
  - 缓存验证结果
  ```

### 7.3 用户体验

#### 7.3.1 操作提示
- [ ] 添加工具提示
  ```javascript
  - 参数说明提示
  - 推荐值提示
  - 警告提示
  ```

#### 7.3.2 错误处理
- [ ] 完善错误处理
  ```python
  - 配置验证错误
  - 训练失败恢复
  - 友好错误提示
  ```

---

## 🚀 实施计划

### 第一周：核心功能（必做）
1. **Day 1-2**: Phase 1.1 - 前端配置模式选择器
2. **Day 3-4**: Phase 1.2 - 后端配置管理器
3. **Day 5-6**: Phase 2 - 网络结构灵活性
4. **Day 7**: 测试和调试

### 第二周：优化功能（强烈建议）
1. **Day 8-9**: Phase 3 - 训练策略优化
2. **Day 10-11**: Phase 4 - 预设配置系统
3. **Day 12-13**: Phase 5 - 监控和反馈
4. **Day 14**: 集成测试

### 第三周：增强功能（可选）
1. **Day 15-16**: Phase 6 - 特征工程
2. **Day 17-18**: Phase 7 - 性能优化
3. **Day 19-20**: 用户体验优化
4. **Day 21**: 最终测试和文档

---

## 📝 注意事项

### 代码修改原则
1. **保持向后兼容**：所有改动不能破坏现有功能
2. **渐进式改造**：每个Phase独立可运行
3. **配置优先**：通过配置文件控制新功能
4. **充分测试**：每个功能完成后立即测试

### 关键文件位置
- 前端主文件：`visualization/templates/enhanced_index.html`
- 后端训练器：`backend/m10_training/trainer.py`
- 模型定义：`backend/m10_training/model.py`
- API接口：`backend/m10_training/api.py`
- 配置文件：`backend/m10_training/config.yaml`

### 开发建议
1. 先实现统一配置模式，确保不影响现有功能
2. 智能优化模式使用预设配置，降低实现复杂度
3. 自定义模式最后实现，作为高级功能
4. 每个Phase完成后进行代码审查和测试
5. 保持详细的开发日志和注释

---

## 🎯 预期成果

### 功能提升
- ✅ 支持任务个性化配置
- ✅ 灵活的网络结构
- ✅ 多种训练策略
- ✅ 智能配置推荐

### 性能改善
- 📈 Q1 R²: 0.60 → 0.75+
- 📈 Q2 R²: 0.55 → 0.70+
- 📈 Q3 R²: 0.52 → 0.65+
- 📈 Q4 R²: 0.48 → 0.60+
- 📈 Q5 R²: 0.45 → 0.58+

### 用户体验
- 🎨 直观的配置界面
- 📊 实时训练监控
- 💡 智能推荐系统
- ⚡ 快速配置选项

---

*更新时间：2024年*
*版本：v1.0*