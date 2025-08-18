# Module 10 模型加载问题诊断报告

## 问题描述
用户在Module 10-B重新训练模型后，Module 10-D的评估结果没有变化，怀疑D模块没有加载最新的模型。

## 核心发现 🔍

### 🚨 **根本原因：模型缓存机制导致旧模型被重复使用**

Module 10-D使用了模型缓存机制，一旦模型被加载到缓存中，后续请求会直接使用缓存的模型，而不会重新从磁盘加载最新的模型文件。

---

## 详细分析

### 1. Module 10-B 模型保存路径

**位置：** `backend/m10_training/trainer.py` 第70-73行

```python
self.save_root = Path(config.get("save_root", "models"))
self.model_dir = self.save_root / rqa_sig
# 最终保存路径: models/{rqa_sig}/{task}_best.pt
```

**保存机制：** `callbacks.py` 第151-152行
```python
checkpoint_path = str(self.model_dir / f"{self.q_tag}_best.pt")
```

✅ **结论：** Module 10-B正确保存模型到 `models/{rqa_sig}/{Q1-Q5}_best.pt`

### 2. Module 10-D 模型加载路径

**位置：** `backend/m10_evaluation/config.py` 第36-38行

```python
def get_model_path(rqa_sig: str, task: str) -> Path:
    """获取模型文件路径"""
    return MODELS_ROOT / rqa_sig / f"{task}_best.pt"
```

✅ **结论：** Module 10-D从相同路径加载模型

### 3. 🔴 **问题核心：缓存机制**

**位置：** `backend/m10_evaluation/evaluator.py` 第116-126行

```python
def _load_models_batch(self, rqa_sig: str) -> Dict[str, torch.nn.Module]:
    """批量加载模型"""
    models_dict = {}
    
    for task in self.tasks:
        cache_key = f"{rqa_sig}_{task}"
        
        # 🚨 问题在这里：如果缓存中存在，直接返回缓存的模型
        if cache_key in self.model_cache:
            models_dict[task] = self.model_cache[cache_key]
            continue  # 跳过加载新模型！
        
        # 只有缓存中不存在时才从磁盘加载
        model_path = get_model_path(rqa_sig, task)
        # ... 加载模型代码
```

**缓存设置：** 第189-191行
```python
# 缓存模型
if len(self.model_cache) < EVALUATION_CONFIG["model_cache_size"]:
    self.model_cache[cache_key] = model
```

### 4. 🔴 **全局评估器实例问题**

**位置：** `backend/m10_evaluation/api.py` 第17-18行

```python
# 全局评估器实例
evaluator = ModelEvaluator()
```

这个全局实例在服务启动时创建，并在整个服务生命周期内保持不变。这意味着：
- 模型缓存永远不会被清空
- 重新训练的模型不会被加载，除非重启服务

---

## 实际存储的模型文件

通过文件系统检查，发现以下模型文件：
```
models/
├── m2_tau1_eps0.055_lmin2/
│   ├── Q1_best.pt
│   ├── Q2_best.pt
│   ├── Q3_best.pt
│   ├── Q4_best.pt
│   └── Q5_best.pt
├── m2_tau1_eps0.06_lmin2/
│   └── ...
└── m2_tau1_eps0.08_lmin2/
    └── ...
```

---

## 解决方案

### 方案1：重启服务（临时解决）
```bash
# 重启Python服务，清空缓存
# 重新运行 start_server.py
```

### 方案2：清空缓存API（推荐）
添加一个清空缓存的API端点：

```python
# 在 backend/m10_evaluation/api.py 中添加
@evaluation_bp.route('/clear-cache', methods=['POST'])
def clear_model_cache():
    """清空模型缓存，强制重新加载"""
    global evaluator
    evaluator.model_cache.clear()
    evaluator.data_cache.clear()
    logger.info("模型缓存已清空")
    return jsonify({"success": True, "message": "缓存已清空"})
```

### 方案3：添加缓存版本控制（长期方案）
修改缓存机制，检查模型文件的修改时间：

```python
# 修改 evaluator.py 的 _load_models_batch 方法
def _load_models_batch(self, rqa_sig: str) -> Dict[str, torch.nn.Module]:
    models_dict = {}
    
    for task in self.tasks:
        cache_key = f"{rqa_sig}_{task}"
        model_path = get_model_path(rqa_sig, task)
        
        # 检查文件修改时间
        if cache_key in self.model_cache:
            cached_time = self.cache_timestamps.get(cache_key, 0)
            file_mtime = model_path.stat().st_mtime
            
            # 如果文件更新了，清除缓存
            if file_mtime > cached_time:
                logger.info(f"检测到模型更新: {task}")
                del self.model_cache[cache_key]
            else:
                models_dict[task] = self.model_cache[cache_key]
                continue
        
        # 加载新模型
        # ... 原有加载代码
        
        # 记录时间戳
        self.cache_timestamps[cache_key] = model_path.stat().st_mtime
```

### 方案4：禁用缓存（开发环境）
```python
# 在 config.py 中添加配置
EVALUATION_CONFIG = {
    "use_cache": False,  # 开发环境设为False
    # ...
}

# 在 evaluator.py 中检查配置
if EVALUATION_CONFIG.get("use_cache", True) and cache_key in self.model_cache:
    # 使用缓存
else:
    # 强制重新加载
```

---

## 立即可用的快速修复

### 方法1：重启服务
```bash
# Windows
taskkill /F /IM python.exe
python start_server.py

# 或者直接重启整个服务
启动服务器.bat
```

### 方法2：手动清理缓存（Python控制台）
```python
import requests

# 如果你添加了清空缓存的API
response = requests.post("http://localhost:5000/api/m10d/clear-cache")
print(response.json())
```

### 方法3：修改缓存大小为0（临时禁用缓存）
编辑 `backend/m10_evaluation/config.py`:
```python
EVALUATION_CONFIG = {
    "model_cache_size": 0,  # 设为0禁用缓存
    # ...
}
```

---

## 验证步骤

1. **检查模型文件时间戳**
   ```bash
   dir "models\m2_tau1_eps0.055_lmin2\*.pt" /T:W
   ```

2. **确认B模块保存成功**
   - 查看训练日志确认模型已保存
   - 检查 `{task}_best.pt` 文件更新时间

3. **测试D模块加载**
   - 清空缓存或重启服务
   - 重新调用D模块API
   - 检查返回结果是否更新

---

## 总结

**问题原因：** Module 10-D使用了模型缓存机制，且缓存没有版本控制或过期机制，导致重新训练的模型不会被加载。

**快速解决：** 重启服务或清空缓存

**长期方案：** 实现基于文件修改时间的缓存版本控制，或在开发环境禁用缓存。

---

**生成时间：** 2024年
**诊断版本：** v1.0