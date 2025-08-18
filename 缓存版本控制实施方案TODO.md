# 📋 Module 10-D 缓存版本控制实施方案 TODO List

## 🎯 目标
实现基于文件修改时间的智能缓存机制，确保Module 10-D始终加载最新训练的模型。

---

## ✅ 实施步骤清单

### 第一阶段：准备工作 🔧

- [ ] **1.1 备份现有代码**
  - [ ] 备份 `backend/m10_evaluation/evaluator.py`
  - [ ] 备份 `backend/m10_evaluation/api.py`
  - [ ] 备份 `backend/m10_evaluation/config.py`
  - [ ] 创建备份文件夹：`backup_m10d_$(date)`

- [ ] **1.2 创建测试环境**
  - [ ] 准备测试用的模型文件
  - [ ] 记录当前模型的性能基准
  - [ ] 准备验证脚本

---

### 第二阶段：修改评估器类 📝

- [ ] **2.1 修改 `evaluator.py` - 添加时间戳追踪**
  ```python
  # 在 ModelEvaluator.__init__ 方法中添加
  - [ ] 添加属性：self.cache_timestamps = {}
  - [ ] 添加属性：self.cache_enabled = EVALUATION_CONFIG.get("use_cache", True)
  ```

- [ ] **2.2 实现文件修改时间检查函数**
  ```python
  # 添加新方法
  - [ ] def _check_model_updated(self, cache_key: str, model_path: Path) -> bool
  - [ ] def _get_file_mtime(self, filepath: Path) -> float
  - [ ] def _invalidate_cache_entry(self, cache_key: str) -> None
  ```

- [ ] **2.3 修改 `_load_models_batch` 方法**
  - [ ] 在缓存检查前添加文件时间戳验证
  - [ ] 实现条件缓存清理逻辑
  - [ ] 更新缓存时记录时间戳
  - [ ] 添加详细的日志记录

---

### 第三阶段：添加配置选项 ⚙️

- [ ] **3.1 修改 `config.py`**
  ```python
  EVALUATION_CONFIG = {
      - [ ] 添加 "use_cache": True  # 是否启用缓存
      - [ ] 添加 "cache_check_mtime": True  # 是否检查文件修改时间
      - [ ] 添加 "cache_ttl": 3600  # 缓存过期时间（秒）
      - [ ] 添加 "force_reload": False  # 强制重新加载（调试用）
  }
  ```

- [ ] **3.2 添加环境变量支持**
  - [ ] 支持通过环境变量覆盖配置
  - [ ] `M10D_USE_CACHE=false` 禁用缓存
  - [ ] `M10D_FORCE_RELOAD=true` 强制重新加载

---

### 第四阶段：实现缓存管理API 🔌

- [ ] **4.1 在 `api.py` 中添加缓存管理端点**
  
  - [ ] **清空缓存端点**
    ```python
    @evaluation_bp.route('/cache/clear', methods=['POST'])
    def clear_cache():
        """清空所有缓存"""
    ```
  
  - [ ] **查看缓存状态端点**
    ```python
    @evaluation_bp.route('/cache/status', methods=['GET'])
    def cache_status():
        """返回缓存状态信息"""
    ```
  
  - [ ] **刷新特定模型端点**
    ```python
    @evaluation_bp.route('/cache/refresh/<rqa_sig>', methods=['POST'])
    def refresh_model_cache(rqa_sig):
        """刷新特定配置的模型缓存"""
    ```

---

### 第五阶段：完整实现代码 💻

- [ ] **5.1 创建完整的 evaluator.py 修改**
  ```python
  class ModelEvaluator:
      def __init__(self):
          # 原有代码...
          - [ ] self.cache_timestamps = {}  # 新增
          - [ ] self.cache_enabled = EVALUATION_CONFIG.get("use_cache", True)
          - [ ] self.cache_check_mtime = EVALUATION_CONFIG.get("cache_check_mtime", True)
      
      - [ ] def _check_model_updated(self, cache_key: str, model_path: Path) -> bool:
              """检查模型文件是否更新"""
              if not self.cache_check_mtime:
                  return False
              
              if cache_key not in self.cache_timestamps:
                  return True
              
              try:
                  file_mtime = model_path.stat().st_mtime
                  cached_time = self.cache_timestamps[cache_key]
                  return file_mtime > cached_time
              except:
                  return True
      
      - [ ] def _load_models_batch(self, rqa_sig: str) -> Dict[str, torch.nn.Module]:
              """修改后的批量加载方法"""
              # 实现智能缓存逻辑
  ```

- [ ] **5.2 添加日志增强**
  - [ ] 缓存命中时记录日志
  - [ ] 缓存失效时记录日志
  - [ ] 模型重新加载时记录详细信息

---

### 第六阶段：测试验证 🧪

- [ ] **6.1 单元测试**
  - [ ] 测试缓存命中场景
  - [ ] 测试文件更新后的缓存失效
  - [ ] 测试强制重新加载
  - [ ] 测试缓存禁用模式

- [ ] **6.2 集成测试**
  - [ ] 训练新模型 → 验证自动加载
  - [ ] 多次请求 → 验证缓存效率
  - [ ] API端点测试
  - [ ] 并发请求测试

- [ ] **6.3 性能测试**
  - [ ] 对比缓存开启/关闭的性能差异
  - [ ] 测量文件时间戳检查的开销
  - [ ] 验证内存使用情况

---

### 第七阶段：文档更新 📚

- [ ] **7.1 更新技术文档**
  - [ ] 说明新的缓存机制
  - [ ] 配置参数说明
  - [ ] API端点文档

- [ ] **7.2 创建使用指南**
  - [ ] 开发环境配置建议
  - [ ] 生产环境配置建议
  - [ ] 故障排除指南

- [ ] **7.3 更新CHANGELOG**
  - [ ] 记录版本变更
  - [ ] 说明破坏性更改（如有）

---

### 第八阶段：部署上线 🚀

- [ ] **8.1 预发布检查**
  - [ ] 代码审查
  - [ ] 测试报告确认
  - [ ] 性能基准对比

- [ ] **8.2 分阶段部署**
  - [ ] 在开发环境验证
  - [ ] 在测试环境运行一周
  - [ ] 生产环境灰度发布

- [ ] **8.3 监控与回滚准备**
  - [ ] 设置监控指标
  - [ ] 准备回滚脚本
  - [ ] 记录部署日志

---

## 🎉 完成标准

### 功能要求 ✔️
- [ ] 模型文件更新后自动重新加载
- [ ] 缓存机制可配置（开启/关闭）
- [ ] 提供缓存管理API
- [ ] 保持向后兼容性

### 性能要求 ⚡
- [ ] 缓存命中率 > 90%（未更新模型时）
- [ ] 文件检查开销 < 10ms
- [ ] 内存使用增长 < 5%

### 质量要求 🏆
- [ ] 单元测试覆盖率 > 80%
- [ ] 无破坏性更改
- [ ] 完整的错误处理
- [ ] 详细的日志记录

---

## 📅 时间估算

| 阶段 | 预计时间 | 实际时间 |
|------|----------|----------|
| 准备工作 | 0.5小时 | - |
| 修改评估器类 | 2小时 | - |
| 添加配置选项 | 0.5小时 | - |
| 实现缓存管理API | 1小时 | - |
| 完整实现代码 | 2小时 | - |
| 测试验证 | 2小时 | - |
| 文档更新 | 1小时 | - |
| 部署上线 | 1小时 | - |
| **总计** | **10小时** | - |

---

## 🚨 风险与注意事项

### 潜在风险
1. **并发访问问题**：多个请求同时更新缓存可能导致竞态条件
2. **内存泄漏**：缓存未正确清理可能导致内存增长
3. **文件系统延迟**：网络文件系统可能导致时间戳不准确

### 缓解措施
1. 使用线程锁保护缓存更新操作
2. 实现缓存大小限制和LRU淘汰策略
3. 添加文件系统类型检测和相应的处理逻辑

---

## 📝 备注

- 优先级：**高** 🔴
- 负责人：_____________
- 开始日期：_____________
- 完成日期：_____________
- 审核人：_____________

---

## 🔗 相关资源

- [原始诊断报告](Module10_模型加载问题诊断.md)
- [Module 10 文档](Module10_Complete_Documentation.md)
- [PyTorch 模型加载最佳实践](https://pytorch.org/tutorials/beginner/saving_loading_models.html)

---

**最后更新：** 2024年
**版本：** v1.0