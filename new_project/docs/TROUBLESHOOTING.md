# Troubleshooting Guide / 问题排查指南

## Table of Contents / 目录

1. [React版本兼容性问题](#react版本兼容性问题)
2. [列表渲染Key重复问题](#列表渲染key重复问题)
3. [API调用问题](#api调用问题)
4. [开发服务器问题](#开发服务器问题)

---

## React版本兼容性问题

### 问题描述 / Problem Description

**症状 / Symptoms:**
```
Warning: [antd: compatible] antd v5 support React is 16 ~ 18.
see https://u.ant.design/v5-for-19 for compatible.
```

**出现时间 / When it occurs:**
- 浏览器控制台显示警告
- 使用Ant Design组件时触发

### 原因分析 / Root Cause

**版本冲突：**
- React 19.x 与 Ant Design v5 不兼容
- Ant Design v5 官方支持 React 16-18
- package.json中React版本过高

**相关代码：**
```json
// ❌ 问题版本
{
  "react": "^19.1.1",
  "react-dom": "^19.1.1"
}
```

### 解决方案 / Solution

#### 方案1: 降级到React 18 (推荐)

**步骤：**

1. **修改package.json**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0"
  }
}
```

2. **清理并重新安装**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

3. **重启开发服务器**
```bash
npm run dev
```

**为什么选择这个方案：**
- ✅ React 18是成熟稳定的版本
- ✅ Ant Design v5完全支持
- ✅ 避免兼容性问题
- ✅ 生产环境可靠

#### 方案2: 使用Ant Design的React 19兼容包 (不推荐)

**仅在必须使用React 19时考虑此方案**

```bash
npm install @ant-design/compatible
```

**缺点：**
- ⚠️ 可能不稳定
- ⚠️ 部分功能可能有限制
- ⚠️ 官方不完全支持

### 验证修复 / Verification

**检查步骤：**

1. 打开浏览器控制台
2. 访问应用页面
3. 确认没有Ant Design兼容性警告
4. 测试所有组件功能正常

**预期结果：**
- ✅ 无警告信息
- ✅ 所有组件渲染正常
- ✅ 交互功能正常

### 预防措施 / Prevention

**依赖管理规范：**

1. **检查版本兼容性**
   - 安装新依赖前检查与现有包的兼容性
   - 查看官方文档的版本支持说明

2. **锁定主要版本**
   ```json
   {
     "react": "~18.2.0",  // 使用~而非^，锁定次版本
     "antd": "~5.27.0"
   }
   ```

3. **定期审查依赖**
   ```bash
   npm outdated
   npm audit
   ```

---

## 列表渲染Key重复问题

### 问题描述 / Problem Description

**症状 / Symptoms:**
```
Warning: Encountered two children with the same key, `control_111`.
Keys should be unique so that components maintain their identity across updates.
```

**影响：**
- React列表渲染错误
- 组件更新异常
- 下拉菜单/筛选器无法正常工作

### 原因分析 / Root Cause

**数据重复：**
- 多个受试者使用相同的business ID
- Eye Tracking数据中hospital_id重复
- 生成的subject_id不唯一

**问题代码：**
```javascript
// ❌ 错误：使用可能重复的ID作为key
{items.map(item => (
  <Item key={item.subject_id} />  // subject_id会重复
))}
```

### 解决方案 / Solution

#### 使用复合唯一Key

**修复方案：**
```javascript
// ✅ 正确：使用复合key
eyeTrackingData.forEach((subject, index) => {
  const uniqueKey = subject.timestamp
    ? `eyetrack_${subject.subject_id}_${subject.timestamp}`
    : `eyetrack_${subject.subject_id}_${index}`;

  subjects.push({
    key: uniqueKey,  // 确保唯一
    subject_id: subject.subject_id,
    ...
  });
});
```

**Key生成策略：**
| 场景 | 推荐方式 | 示例 |
|------|---------|------|
| 有timestamp | `${source}_${id}_${timestamp}` | `eyetrack_001_2025-3-27-11-37-22` |
| 有UUID | 直接使用UUID | `550e8400-e29b-41d4-a716-446655440000` |
| 无唯一标识 | `${source}_${id}_${index}` | `legacy_001_0` |

### 验证修复 / Verification

**检查步骤：**
1. 打开浏览器控制台
2. 渲染包含列表的组件
3. 确认无key重复警告
4. 测试筛选和排序功能

**预期结果：**
- ✅ 无key重复警告
- ✅ 列表渲染正确
- ✅ 筛选功能正常

### 预防措施 / Prevention

**代码规范：**

1. **永远使用唯一key**
   - 不使用可能重复的业务ID
   - 不使用数组索引（动态列表）

2. **后端提供unique_id**
   ```python
   # 后端生成唯一ID
   entry["unique_id"] = f"{subject_id}_{timestamp}"
   ```

3. **代码审查检查点**
   - [ ] 所有.map()使用key
   - [ ] Key值确保唯一
   - [ ] 多数据源使用前缀区分

---

## API调用问题

### 问题：API返回数据为空或错误

**症状：**
- API响应success: false
- 数据字段为空
- 网络请求失败

**排查步骤：**

1. **检查后端服务**
   ```bash
   # 检查Flask服务是否运行
   curl http://127.0.0.1:9090/api/health
   ```

2. **检查API端点**
   ```bash
   # 测试具体API
   curl http://127.0.0.1:9090/api/m00/scan-all
   ```

3. **检查CORS配置**
   ```python
   # backend/run.py
   CORS(app, resources={
       r"/api/*": {
           "origins": ["http://localhost:5173", "http://localhost:5174"]
       }
   })
   ```

4. **检查响应格式**
   ```javascript
   // 确认响应格式
   {
     "success": true/false,
     "data": {...},
     "error": "..."
   }
   ```

### 解决方案：

**统一错误处理：**
```javascript
const handleApiCall = async () => {
  try {
    const response = await axios.get('/api/endpoint');

    if (response.data.success) {
      // 成功处理
      message.success('操作成功');
    } else {
      // 失败处理
      message.error(`操作失败: ${response.data.error}`);
    }
  } catch (error) {
    // 网络错误
    message.error(`请求失败: ${error.message}`);
  }
};
```

---

## 开发服务器问题

### 问题：端口被占用

**症状：**
```
Port 5173 is in use, trying another one...
VITE ready in XXX ms
Local: http://localhost:5174/
```

**解决方案：**

1. **方案1: 停止占用进程**
   ```bash
   # Windows
   netstat -ano | findstr :5173
   taskkill /PID <PID> /F

   # Linux/Mac
   lsof -i :5173
   kill -9 <PID>
   ```

2. **方案2: 使用新端口**
   - Vite会自动选择下一个可用端口
   - 更新前端访问地址

3. **方案3: 配置固定端口**
   ```javascript
   // vite.config.js
   export default {
     server: {
       port: 5173,
       strictPort: false  // 端口占用时尝试下一个
     }
   }
   ```

### 问题：HMR（热更新）不工作

**症状：**
- 修改代码后页面不自动刷新
- 需要手动刷新浏览器

**解决方案：**

1. **检查WebSocket连接**
   ```javascript
   // vite.config.js
   export default {
     server: {
       hmr: {
         overlay: true
       }
     }
   }
   ```

2. **重启开发服务器**
   ```bash
   # Ctrl+C 停止
   npm run dev
   ```

3. **清除缓存**
   ```bash
   rm -rf node_modules/.vite
   npm run dev
   ```

---

## 常见错误代码对照表

| 错误代码 | 含义 | 解决方案 |
|---------|------|---------|
| CORS Error | 跨域请求被阻止 | 检查后端CORS配置 |
| 404 Not Found | API端点不存在 | 检查路由注册 |
| 500 Server Error | 后端逻辑错误 | 查看后端日志 |
| Network Error | 网络连接失败 | 检查后端服务状态 |
| ECONNREFUSED | 连接被拒绝 | 确认后端服务运行 |

---

## 调试工具和命令

### Frontend 前端调试

```bash
# 检查依赖版本
npm list react react-dom antd

# 查看过时的包
npm outdated

# 清理缓存
npm cache clean --force

# 完全重装
rm -rf node_modules package-lock.json
npm install
```

### Backend 后端调试

```bash
# 检查Python包
pip list | grep Flask

# 查看端口占用
netstat -ano | findstr :9090  # Windows
lsof -i :9090                 # Linux/Mac

# 测试API
curl -X GET http://127.0.0.1:9090/api/m00/scan-all
curl -X POST http://127.0.0.1:9090/api/m00/import \
  -H "Content-Type: application/json" \
  -d '{"source":"all","overwrite":false}'
```

### 浏览器调试

1. **React DevTools** - 检查组件状态
2. **Network Tab** - 查看API请求
3. **Console** - 查看错误和警告
4. **Performance** - 分析性能问题

---

## 快速诊断清单

**前端问题：**
- [ ] 检查浏览器控制台是否有错误
- [ ] 确认React和Ant Design版本兼容
- [ ] 验证API请求地址正确
- [ ] 检查网络请求是否成功
- [ ] 确认数据格式符合预期

**后端问题：**
- [ ] 确认Flask服务运行中
- [ ] 检查API端点是否注册
- [ ] 验证数据源路径正确
- [ ] 查看后端日志输出
- [ ] 确认CORS配置正确

**环境问题：**
- [ ] Node.js版本符合要求
- [ ] Python版本符合要求
- [ ] 依赖包正确安装
- [ ] 端口没有被占用
- [ ] 文件路径正确

---

**文档版本 / Version:** 1.0
**最后更新 / Last Updated:** 2025-10-02
**维护者 / Maintainer:** VR Eye Tracking Analysis Platform Team
