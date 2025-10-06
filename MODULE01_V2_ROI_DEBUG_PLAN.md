# Module01 V2 ROI加载问题排查计划

## 问题描述
- **现象**: Module01选择v2数据版本时，仍然加载v1的ROI信息
- **Console错误**: 404错误 - 无法加载校准数据
  ```
  GET http://127.0.0.1:5173/api/module01/calibration/data?group=control&subject_id=control_v2_000000&task=q3 404
  ```

## 错误分析

### 问题1: ROI数据来源混乱
- **可能原因**:
  1. 前端缓存了旧的ROI数据
  2. 后端返回的ROI数据中version字段不正确
  3. 前端API调用时传递的version参数不正确
  4. ROI文件本身的version字段错误

### 问题2: 404校准数据错误
- **可能原因**:
  1. v2版本的校准数据文件不存在
  2. 校准数据API路径错误（127.0.0.1:5173应该是9090）
  3. 前端proxy配置问题
  4. subject_id命名不匹配（control_v2_000000）

## 排查步骤

### Step 1: 验证后端ROI API返回数据
**目标**: 确认后端返回的ROI数据version字段是否正确

**操作**:
```bash
# 测试v2 Q1的ROI数据
curl -s "http://127.0.0.1:9090/api/data/roi?version=v2&task=q1" | python -m json.tool

# 测试v2 Q3的ROI数据
curl -s "http://127.0.0.1:9090/api/data/roi?version=v2&task=q3" | python -m json.tool
```

**预期结果**:
- `data.version` 应该是 "v2"
- `data.regions` 中每个区域的 `version` 字段应该是 "v2"

**如果失败**: ROI配置文件中的version字段可能是硬编码的v1

---

### Step 2: 检查ROI配置文件内容
**目标**: 验证v2 ROI配置文件中的version字段

**操作**:
```bash
# 检查v2 Q1 ROI文件
cat data/roi_configs/v2/q1_roi.json | python -m json.tool | head -50

# 检查v2 Q3 ROI文件
cat data/roi_configs/v2/q3_roi.json | python -m json.tool | head -50
```

**预期结果**:
- 每个region对象应该有 `"version": "v2"`

**如果失败**: 需要批量修正v2文件夹下所有ROI配置的version字段

---

### Step 3: 检查前端API调用
**目标**: 确认前端传递给后端的version参数

**操作**:
1. 检查Module01组件中传递的version参数
2. 检查roiService中API调用的参数传递
3. 查看浏览器Network面板中实际发送的请求

**文件**:
- `frontend/src/components/Module01/Module01.jsx`
- `frontend/src/services/roiService.js`

**预期结果**:
- 用户选择v2时，所有ROI相关API调用应该带 `version=v2`

---

### Step 4: 检查前端proxy配置
**目标**: 解决404错误 - 确认API请求正确转发到后端

**操作**:
```bash
# 检查vite配置
cat frontend/vite.config.js
```

**预期结果**:
- `/api/*` 应该proxy到 `http://127.0.0.1:9090`
- 不应该出现请求到5173端口的情况

**如果失败**: 修正vite.config.js中的proxy配置

---

### Step 5: 检查v2校准数据文件
**目标**: 解决404错误 - 验证v2校准数据文件是否存在

**操作**:
```bash
# 列出v2校准数据文件
ls -la data/calibrated_data/v2/ 2>/dev/null || echo "v2 folder not found"

# 搜索control_v2开头的文件
find data/calibrated_data -name "*control_v2*" -type f 2>/dev/null
```

**预期结果**:
- 应该存在 `data/calibrated_data/v2/control_v2_000000_q1_calibrated.csv` 等文件

**如果失败**: 需要生成v2版本的校准数据，或修改前端subject_id命名规则

---

### Step 6: 检查Module01状态管理
**目标**: 确认version状态在组件中正确传递

**操作**:
- 检查Module01.jsx中version状态的初始化和更新
- 检查useEffect依赖项中是否包含version
- 添加console.log跟踪version变化

**文件**:
- `frontend/src/components/Module01/Module01.jsx`

---

### Step 7: 检查ROI数据处理逻辑
**目标**: 确认ROI数据在前端的处理和渲染

**操作**:
- 检查ROI数据加载后的处理逻辑
- 检查是否有缓存机制导致使用旧数据
- 检查ROI overlay组件是否正确接收新数据

---

## 修复方案

### 修复1: 批量更新v2 ROI文件的version字段
如果Step 2发现version字段错误，创建脚本批量修正：

```python
# scripts/fix_v2_roi_version.py
import json
from pathlib import Path

def fix_roi_version(roi_file, target_version='v2'):
    """修正ROI文件中的version字段"""
    with open(roi_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 修正所有region的version
    for region_type in ['keywords', 'instructions', 'background']:
        if region_type in data.get('regions', {}):
            for region in data['regions'][region_type]:
                region['version'] = target_version

    with open(roi_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

### 修复2: 修正前端proxy配置
如果Step 4发现proxy问题：

```javascript
// frontend/vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9090',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
```

### 修复3: 创建v2校准数据
如果Step 5发现缺少v2数据：

选项A: 复制v1数据结构到v2
选项B: 修改前端不依赖校准数据
选项C: 生成模拟v2校准数据

### 修复4: 修正后端ROI加载逻辑
确保UnifiedROIService返回数据时保持正确的version：

```python
# src/services/roi_service.py
def get_roi_config(self, version: str, task_id: str):
    # ...加载数据后...

    # 强制设置正确的version
    config_data['version'] = version
    for region_type in ['keywords', 'instructions', 'background']:
        if region_type in config_data.get('regions', {}):
            for region in config_data['regions'][region_type]:
                region['version'] = version
```

## 执行顺序
1. Step 1 → Step 2 (验证数据源)
2. Step 4 (修复proxy - 优先解决404)
3. Step 5 (检查校准数据)
4. Step 3 (检查前端调用)
5. Step 6 → Step 7 (前端状态和渲染)
6. 根据发现的问题应用相应修复方案

## 成功标准
- [ ] 后端API返回的v2 ROI数据version字段正确
- [ ] 前端选择v2时加载的ROI regions全部标记为v2
- [ ] 404错误消失
- [ ] ROI overlay正确显示v2的ROI区域
- [ ] console中没有错误信息
