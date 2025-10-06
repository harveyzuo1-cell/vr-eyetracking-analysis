# 数据变更通知机制设计方案
# Data Change Notification Mechanism Design

**文档版本**: v1.0
**创建日期**: 2025-10-02
**状态**: 📋 待实施
**优先级**: 🟢 低（未来优化）

---

## 📋 目录

1. [背景与目标](#背景与目标)
2. [问题场景](#问题场景)
3. [技术方案对比](#技术方案对比)
4. [推荐方案详解](#推荐方案详解)
5. [实施步骤](#实施步骤)
6. [代码示例](#代码示例)
7. [性能分析](#性能分析)
8. [测试计划](#测试计划)
9. [未来扩展](#未来扩展)
10. [实施建议](#实施建议)

---

## 🎯 背景与目标

### 当前问题

**场景**: 用户通过Module00导入新的眼动数据
```
1. 用户访问Module00前端页面
2. 点击"导入v2数据"按钮
3. Module00后端处理导入（需要5-10秒）
4. 导入成功，新增68个受试者
5. 用户切换到Module01页面
6. ❓ Module01如何知道数据已更新？
```

**问题**:
- Module01的MetadataReader在初始化时加载元数据，并**缓存**在内存中
- Module00导入新数据后，Module01的缓存**不会自动刷新**
- 用户需要**手动刷新浏览器**才能看到新数据

### 优化目标

实现**自动数据同步机制**，当Module00更新数据时：
- ✅ Module01等模块自动感知变更
- ✅ 自动刷新缓存数据
- ✅ 前端UI自动更新
- ✅ 用户无需手动刷新

---

## 🔍 问题场景

### 场景1：Module00导入新数据

**流程**:
```
1. Module00 POST /api/m00/import-v2
   ↓ 导入68个新受试者
   ↓ 更新subject_metadata.json
   ↓
2. Module01前端定期调用 GET /api/data/groups
   ↓ Module01后端从缓存返回旧数据（不知道已更新）
   ↓
3. 前端显示旧数据 ❌
```

**期望流程**:
```
1. Module00 POST /api/m00/import-v2
   ↓ 导入68个新受试者
   ↓ 更新subject_metadata.json
   ↓ 发送"数据变更通知"
   ↓
2. Module01收到通知
   ↓ 刷新MetadataReader缓存
   ↓
3. 前端调用 GET /api/data/groups
   ↓ 返回最新数据 ✅
   ↓
4. 前端自动更新UI ✅
```

---

### 场景2：Module00删除/修改数据

**流程**:
```
1. Module00删除某个受试者
   ↓ 更新subject_metadata.json
   ↓ 发送"数据变更通知"
   ↓
2. Module01收到通知并刷新
3. Module02-10同时收到通知并刷新
```

---

### 场景3：MMSE数据更新

**流程**:
```
1. Module00导入MMSE评分
   ↓ 更新mmse_scores.json
   ↓ 发送"MMSE变更通知"
   ↓
2. Module01刷新MMSE缓存
3. Module08（MMSE分析模块）刷新缓存
```

---

## 🛠️ 技术方案对比

### 方案A：前端轮询（简单，推荐）

**原理**: 前端定期调用API检查数据版本

**实现**:
```javascript
// 前端每30秒检查一次数据版本
setInterval(async () => {
  const response = await fetch('/api/data/version');
  const { version } = await response.json();

  if (version > currentVersion) {
    // 数据已更新，刷新页面数据
    await refreshData();
    currentVersion = version;
  }
}, 30000); // 30秒
```

**优点**:
- ✅ 实现简单，不需要WebSocket
- ✅ 兼容性好，适用所有浏览器
- ✅ 易于调试和维护

**缺点**:
- ⚠️ 实时性差（30秒延迟）
- ⚠️ 有一定网络开销（每30秒一次请求）

**适用场景**:
- ✅ 数据更新频率低（每天/每小时）
- ✅ 对实时性要求不高（30秒延迟可接受）

---

### 方案B：WebSocket推送（复杂，未来可选）

**原理**: 后端通过WebSocket主动推送变更通知

**实现**:
```python
# 后端
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to server'})

# Module00导入完成后发送通知
def notify_data_change(change_type, metadata):
    socketio.emit('data_changed', {
        'type': change_type,
        'metadata': metadata,
        'timestamp': datetime.now().isoformat()
    })
```

```javascript
// 前端
import io from 'socket.io-client';

const socket = io('http://127.0.0.1:9090');

socket.on('data_changed', (event) => {
  console.log('Data changed:', event);
  refreshData();
});
```

**优点**:
- ✅ 实时性强（秒级响应）
- ✅ 网络开销小（仅在变更时推送）
- ✅ 支持双向通信

**缺点**:
- ❌ 实现复杂（需要Socket.IO库）
- ❌ 需要维护长连接
- ❌ 增加服务器负担
- ❌ 调试复杂

**适用场景**:
- ✅ 数据更新频繁（每分钟）
- ✅ 对实时性要求高（秒级响应）

---

### 方案C：服务端事件（SSE, Server-Sent Events）

**原理**: 服务器单向推送事件流

**实现**:
```python
# 后端
from flask import Response

@app.route('/api/events/stream')
def event_stream():
    def generate():
        while True:
            # 检查是否有变更
            if data_changed:
                yield f"data: {json.dumps({'type': 'data_change'})}\n\n"
            time.sleep(5)

    return Response(generate(), mimetype='text/event-stream')
```

```javascript
// 前端
const eventSource = new EventSource('/api/events/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'data_change') {
    refreshData();
  }
};
```

**优点**:
- ✅ 原生浏览器支持，无需额外库
- ✅ 实现相对简单
- ✅ 适合单向推送

**缺点**:
- ⚠️ 只支持服务器→客户端（不支持双向）
- ⚠️ 需要维护长连接

**适用场景**:
- ✅ 单向通知场景
- ✅ 对实时性有一定要求（5秒级）

---

### 方案D：基于文件监听（仅后端）

**原理**: 后端监听元数据文件变化，自动刷新缓存

**实现**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MetadataFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('subject_metadata.json'):
            # 刷新所有模块的MetadataReader缓存
            reload_all_metadata_readers()

observer = Observer()
observer.schedule(MetadataFileHandler(), path='data/01_raw/clinical', recursive=False)
observer.start()
```

**优点**:
- ✅ 自动检测文件变化
- ✅ 无需前端配合

**缺点**:
- ⚠️ 前端仍需轮询或WebSocket通知
- ⚠️ 增加系统复杂度

**适用场景**:
- ✅ 配合方案A/B/C使用

---

### 方案对比总结

| 方案 | 实时性 | 实现复杂度 | 网络开销 | 推荐度 | 适用场景 |
|------|--------|-----------|---------|--------|---------|
| A. 前端轮询 | ⭐⭐⭐ (30秒) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **当前项目** |
| B. WebSocket | ⭐⭐⭐⭐⭐ (秒级) | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 高频更新场景 |
| C. SSE | ⭐⭐⭐⭐ (5秒) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 单向通知场景 |
| D. 文件监听 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | - | ⭐⭐⭐ | 后端辅助方案 |

**推荐**: **方案A（前端轮询）+ 方案D（文件监听）组合**

---

## 📖 推荐方案详解

### 组合方案：前端轮询 + 后端文件监听

**架构图**:
```
┌─────────────────────────────────────┐
│  前端 (React)                       │
│                                     │
│  useEffect(() => {                 │
│    setInterval(() => {             │
│      checkDataVersion()  ←─────────┼─── 每30秒轮询
│    }, 30000)                       │
│  }, [])                            │
└─────────────────────────────────────┘
              ↓ GET /api/data/version
┌─────────────────────────────────────┐
│  后端 Module01 API                  │
│                                     │
│  @app.route('/api/data/version')   │
│  def get_data_version():           │
│    return metadata_reader.version  │
└─────────────────────────────────────┘
              ↑ 自动刷新缓存
┌─────────────────────────────────────┐
│  MetadataReader                     │
│                                     │
│  - version: int (时间戳)            │
│  - reload() 刷新缓存                │
└─────────────────────────────────────┘
              ↑ 文件变更触发
┌─────────────────────────────────────┐
│  文件监听器 (watchdog)               │
│                                     │
│  监听: subject_metadata.json        │
│  事件: on_modified → reload()       │
└─────────────────────────────────────┘
```

---

### 关键设计

#### 1. 数据版本号管理

```python
# src/core/metadata_reader.py

class MetadataReader:
    """共享元数据读取器（带版本号）"""

    def __init__(self, clinical_data_dir: Optional[str] = None):
        # ... 现有代码 ...

        # ⭐ 新增：数据版本号（使用文件修改时间戳）
        self.version = self._get_current_version()

    def _get_current_version(self) -> int:
        """
        获取当前数据版本号

        使用subject_metadata.json的最后修改时间作为版本号

        Returns:
            Unix时间戳（秒）
        """
        if self.subject_metadata_file.exists():
            return int(self.subject_metadata_file.stat().st_mtime)
        return 0

    def reload(self):
        """重新加载元数据并更新版本号"""
        self._load_metadata()
        self.version = self._get_current_version()
        logger.info(f"MetadataReader reloaded, new version: {self.version}")
```

---

#### 2. 后端API：获取数据版本

```python
# src/web/modules/module01_data_visualization/api.py

@data_bp.route('/version', methods=['GET'])
def get_data_version():
    """
    获取当前数据版本号

    用于前端检测数据是否已更新

    Returns:
        {
            "version": 1696234567,  # Unix时间戳
            "last_modified": "2025-10-02 15:30:00"
        }
    """
    try:
        version = service.metadata_reader.version

        return jsonify({
            "success": True,
            "version": version,
            "last_modified": datetime.fromtimestamp(version).isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get data version: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "version": 0
        }), 500
```

---

#### 3. 后端：文件监听器

```python
# src/utils/metadata_watcher.py (新文件)
"""
元数据文件监听器
Metadata File Watcher

监听subject_metadata.json和mmse_scores.json的变化，
自动刷新所有MetadataReader实例
"""
import logging
from pathlib import Path
from typing import List, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)


class MetadataFileWatcher(FileSystemEventHandler):
    """元数据文件变更处理器"""

    def __init__(self, callbacks: List[Callable] = None):
        """
        初始化文件监听器

        Args:
            callbacks: 文件变更时的回调函数列表
        """
        self.callbacks = callbacks or []
        self.monitored_files = [
            'subject_metadata.json',
            'mmse_scores.json'
        ]

    def on_modified(self, event: FileModifiedEvent):
        """文件修改事件处理"""
        if event.is_directory:
            return

        file_name = Path(event.src_path).name

        if file_name in self.monitored_files:
            logger.info(f"Detected metadata file change: {file_name}")

            # 调用所有回调函数
            for callback in self.callbacks:
                try:
                    callback(file_name)
                except Exception as e:
                    logger.error(f"Callback failed: {e}", exc_info=True)


class MetadataWatcherService:
    """元数据监听服务"""

    def __init__(self, clinical_data_dir: str):
        """
        初始化监听服务

        Args:
            clinical_data_dir: 临床数据目录路径
        """
        self.clinical_data_dir = Path(clinical_data_dir)
        self.observer = Observer()
        self.callbacks = []

    def register_callback(self, callback: Callable):
        """
        注册回调函数

        Args:
            callback: 文件变更时调用的函数
        """
        self.callbacks.append(callback)
        logger.info(f"Registered metadata watcher callback: {callback.__name__}")

    def start(self):
        """启动文件监听"""
        handler = MetadataFileWatcher(callbacks=self.callbacks)

        self.observer.schedule(
            handler,
            path=str(self.clinical_data_dir),
            recursive=False
        )

        self.observer.start()
        logger.info(f"Metadata watcher started: {self.clinical_data_dir}")

    def stop(self):
        """停止文件监听"""
        self.observer.stop()
        self.observer.join()
        logger.info("Metadata watcher stopped")
```

---

#### 4. Flask应用启动时初始化监听器

```python
# src/web/app.py

from src.utils.metadata_watcher import MetadataWatcherService
from pathlib import Path

def create_app():
    """Flask应用工厂"""
    app = Flask(__name__)

    # ... 现有代码 ...

    # ⭐ 新增：启动元数据文件监听
    clinical_data_dir = Path(__file__).parent.parent.parent / "data" / "01_raw" / "clinical"
    metadata_watcher = MetadataWatcherService(str(clinical_data_dir))

    # 注册回调：刷新所有模块的MetadataReader
    def on_metadata_changed(filename):
        logger.info(f"Metadata changed: {filename}, reloading all MetadataReaders...")
        # 这里可以触发所有模块的reload()
        # 实际实现可能需要维护全局的MetadataReader实例列表
        pass

    metadata_watcher.register_callback(on_metadata_changed)
    metadata_watcher.start()

    # 应用关闭时停止监听
    import atexit
    atexit.register(metadata_watcher.stop)

    return app
```

---

#### 5. 前端：定期检查版本

```javascript
// frontend/src/hooks/useDataVersion.js
import { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * 自定义Hook：监听数据版本变化
 *
 * @param {number} interval - 检查间隔（毫秒），默认30秒
 * @param {function} onDataChanged - 数据变更时的回调函数
 */
export const useDataVersion = (interval = 30000, onDataChanged) => {
  const [version, setVersion] = useState(0);
  const [lastCheck, setLastCheck] = useState(new Date());

  useEffect(() => {
    const checkVersion = async () => {
      try {
        const response = await axios.get('/api/data/version');
        const { version: newVersion } = response.data;

        if (newVersion > version && version !== 0) {
          console.log(`Data version changed: ${version} → ${newVersion}`);

          // 触发回调函数
          if (onDataChanged) {
            onDataChanged(newVersion, version);
          }
        }

        setVersion(newVersion);
        setLastCheck(new Date());
      } catch (error) {
        console.error('Failed to check data version:', error);
      }
    };

    // 立即检查一次
    checkVersion();

    // 定期检查
    const timer = setInterval(checkVersion, interval);

    return () => clearInterval(timer);
  }, [version, interval, onDataChanged]);

  return { version, lastCheck };
};
```

---

#### 6. 前端：Module01使用Hook

```javascript
// frontend/src/pages/Module01/Module01.jsx
import React, { useState, useCallback } from 'react';
import { useDataVersion } from '../../hooks/useDataVersion';
import { dataService } from '../../services/dataService';

const Module01 = () => {
  const [groups, setGroups] = useState([]);
  const [subjects, setSubjects] = useState([]);

  // 加载组别列表
  const loadGroups = useCallback(async () => {
    const response = await dataService.getGroups();
    setGroups(response.data);
  }, []);

  // 数据变更回调
  const handleDataChanged = useCallback((newVersion, oldVersion) => {
    console.log('Data updated, refreshing...');

    // 重新加载数据
    loadGroups();

    // 显示通知（可选）
    alert('数据已更新，已自动刷新！');
  }, [loadGroups]);

  // ⭐ 使用数据版本监听Hook
  const { version, lastCheck } = useDataVersion(30000, handleDataChanged);

  // 初次加载
  useEffect(() => {
    loadGroups();
  }, [loadGroups]);

  return (
    <div>
      <h1>Module 01: 数据可视化</h1>

      {/* 显示数据版本信息（可选） */}
      <div style={{ fontSize: '12px', color: '#999' }}>
        数据版本: {version} | 最后检查: {lastCheck.toLocaleTimeString()}
      </div>

      {/* ... 其他UI组件 ... */}
    </div>
  );
};
```

---

## 📝 实施步骤

### Phase 1: 后端基础（1小时）

#### 步骤1.1：MetadataReader添加版本号支持
```python
# 修改 src/core/metadata_reader.py
# 添加 version 属性和 _get_current_version() 方法
```

#### 步骤1.2：添加版本查询API
```python
# 修改 src/web/modules/module01_data_visualization/api.py
# 添加 GET /api/data/version 端点
```

#### 步骤1.3：测试版本API
```bash
curl http://127.0.0.1:9090/api/data/version
# 预期: {"success": true, "version": 1696234567, ...}
```

---

### Phase 2: 文件监听（1小时）

#### 步骤2.1：安装watchdog库
```bash
pip install watchdog
echo "watchdog==3.0.0" >> requirements.txt
```

#### 步骤2.2：创建文件监听器
```python
# 创建 src/utils/metadata_watcher.py
```

#### 步骤2.3：集成到Flask应用
```python
# 修改 src/web/app.py
# 启动时初始化 MetadataWatcherService
```

---

### Phase 3: 前端实现（1小时）

#### 步骤3.1：创建useDataVersion Hook
```javascript
// 创建 frontend/src/hooks/useDataVersion.js
```

#### 步骤3.2：Module01使用Hook
```javascript
// 修改 frontend/src/pages/Module01/Module01.jsx
```

#### 步骤3.3：测试前端轮询
```bash
# 启动前端
cd frontend
npm run dev

# 观察浏览器控制台，应该每30秒打印一次版本检查日志
```

---

### Phase 4: 测试验证（30分钟）

#### 步骤4.1：端到端测试
```bash
# 1. 启动后端和前端
# 2. 访问Module01页面
# 3. 在另一个终端导入新数据
curl -X POST http://127.0.0.1:9090/api/m00/import-v2
# 4. 等待30秒，观察Module01是否自动刷新
```

#### 步骤4.2：文件监听测试
```bash
# 手动修改元数据文件
echo '{}' >> data/01_raw/clinical/subject_metadata.json
# 观察后端日志，应该打印 "Detected metadata file change"
```

---

## 💻 代码示例

### 完整示例：Module02使用数据变更通知

```python
# src/web/modules/module02_data_import/service.py

from src.core.metadata_reader import MetadataReader

class DataImportService:
    """数据导入服务"""

    def __init__(self):
        self.metadata_reader = MetadataReader()

        # 订阅数据变更通知（通过全局Watcher）
        # 当元数据文件变化时，自动刷新
        # （实际订阅逻辑在app.py中统一管理）

    def get_import_candidates(self):
        """获取待导入的受试者候选列表"""
        # 使用最新的元数据
        existing_subjects = self.metadata_reader.get_all_subjects()

        # ... 业务逻辑 ...

        return candidates
```

---

## 📊 性能分析

### 网络开销分析

**前端轮询（30秒间隔）**:
```
请求频率: 120次/小时 = 2,880次/天
请求大小: ~100字节（JSON响应）
总流量: 288KB/天 ≈ 可忽略
```

**结论**: ✅ 网络开销极小

---

### 服务器负载分析

**文件监听（watchdog）**:
```
CPU占用: <0.1%（idle时）
内存占用: ~5MB
```

**前端轮询API**:
```
单次请求处理时间: <5ms（读取文件修改时间）
QPS: ~0.03（假设100个用户，每30秒一次）
```

**结论**: ✅ 服务器负载极小

---

## 🧪 测试计划

### 单元测试

```python
# tests/utils/test_metadata_watcher.py

def test_file_watcher_detects_change():
    """测试文件监听器能检测到文件变化"""
    callback_called = [False]

    def callback(filename):
        callback_called[0] = True

    watcher = MetadataWatcherService('/path/to/clinical')
    watcher.register_callback(callback)
    watcher.start()

    # 修改文件
    Path('/path/to/clinical/subject_metadata.json').touch()

    # 等待监听器响应
    time.sleep(1)

    assert callback_called[0], "Callback should be called"

    watcher.stop()
```

---

### 集成测试

```bash
# 测试脚本: tests/integration/test_data_change_notification.sh

# 1. 启动服务
python run.py &
BACKEND_PID=$!

# 2. 获取初始版本
INITIAL_VERSION=$(curl -s http://127.0.0.1:9090/api/data/version | jq .version)

# 3. 导入新数据
curl -X POST http://127.0.0.1:9090/api/m00/import-v2

# 4. 等待2秒（文件监听器响应）
sleep 2

# 5. 获取新版本
NEW_VERSION=$(curl -s http://127.0.0.1:9090/api/data/version | jq .version)

# 6. 验证版本已更新
if [ "$NEW_VERSION" -gt "$INITIAL_VERSION" ]; then
    echo "✅ Data version updated successfully"
else
    echo "❌ Data version not updated"
    exit 1
fi

# 7. 清理
kill $BACKEND_PID
```

---

## 🚀 未来扩展

### 扩展1：WebSocket实时推送（可选）

如果未来需要更强的实时性，可以升级为WebSocket方案：

```python
# src/web/app.py
from flask_socketio import SocketIO

socketio = SocketIO(app, cors_allowed_origins="*")

# MetadataWatcher回调函数改为发送WebSocket消息
def on_metadata_changed(filename):
    socketio.emit('data_changed', {
        'type': 'metadata',
        'filename': filename,
        'version': metadata_reader.version
    })
```

---

### 扩展2：细粒度通知

区分不同类型的数据变更：

```python
# 通知类型
NOTIFICATION_TYPES = {
    'SUBJECT_ADDED': 'subject_added',      # 新增受试者
    'SUBJECT_REMOVED': 'subject_removed',  # 删除受试者
    'MMSE_UPDATED': 'mmse_updated',        # MMSE更新
    'METADATA_CHANGED': 'metadata_changed' # 元数据变更
}

# 前端可以根据通知类型做不同处理
```

---

### 扩展3：增量更新

仅传输变更的数据，而非全量刷新：

```javascript
// 增量更新示例
const handleDataChanged = (changeEvent) => {
  if (changeEvent.type === 'SUBJECT_ADDED') {
    // 仅添加新受试者，不重新加载全部
    addSubject(changeEvent.data);
  }
};
```

---

## 💡 实施建议

### 实施优先级

**🟢 建议延后实施**

**原因**:
1. 当前数据更新频率低（每天/每周导入一次）
2. 用户手动刷新浏览器可以解决问题
3. 不影响核心功能

**建议时机**:
- 如果数据更新频率提高（每小时/每分钟）
- 如果用户反馈"需要手动刷新"是重大痛点
- 如果Module02-10都已开发完成，有余力优化

---

### 分阶段实施建议

**阶段1（最小可行方案）**: 仅实现前端轮询
- 工作量：1小时
- 收益：中等
- 实现版本查询API和前端Hook

**阶段2（增强方案）**: 添加文件监听
- 工作量：1小时
- 收益：高
- 后端自动刷新缓存

**阶段3（完整方案）**: WebSocket实时推送
- 工作量：3小时
- 收益：高（如果需要实时性）
- 升级为WebSocket架构

---

## 📞 总结

### 推荐方案
**✅ 方案A（前端轮询30秒）+ 方案D（后端文件监听）**

### 实施时机
**🟢 建议延后** - 当前优先级低，可在Module02-10开发完成后实施

### 预期收益
- ✅ 用户体验提升：无需手动刷新浏览器
- ✅ 数据一致性：确保前端始终显示最新数据
- ✅ 易于维护：轮询方案实现简单，调试容易

### 工作量估算
- Phase 1-3: 3小时（核心功能）
- Phase 4: 0.5小时（测试）
- **总计: 3.5小时**

---

**文档维护者**: AI Assistant
**创建日期**: 2025-10-02
**下次审查**: Module02开发前

---

**附录**: 实施Checklist（见下页）

---

## 📋 实施Checklist

### Phase 1: 后端基础
- [ ] MetadataReader添加version属性
- [ ] MetadataReader添加_get_current_version()方法
- [ ] 添加GET /api/data/version API端点
- [ ] 测试版本API

### Phase 2: 文件监听
- [ ] 安装watchdog依赖
- [ ] 创建MetadataWatcher类
- [ ] 创建MetadataWatcherService
- [ ] 集成到Flask应用启动
- [ ] 测试文件监听功能

### Phase 3: 前端实现
- [ ] 创建useDataVersion Hook
- [ ] Module01使用Hook
- [ ] 测试前端轮询逻辑

### Phase 4: 测试
- [ ] 单元测试
- [ ] 集成测试
- [ ] 端到端测试
- [ ] 性能测试

### Phase 5: 文档
- [ ] 更新架构文档
- [ ] 编写使用指南
- [ ] 更新README

---

**文档结束**
