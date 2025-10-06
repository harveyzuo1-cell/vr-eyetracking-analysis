# Frontend Coding Standards
# 前端编码规范

## Table of Contents / 目录

1. [React列表渲染规范](#react列表渲染规范)
2. [组件设计规范](#组件设计规范)
3. [数据处理规范](#数据处理规范)
4. [API集成规范](#api集成规范)
5. [错误处理规范](#错误处理规范)
6. [代码审查检查点](#代码审查检查点)

---

## React列表渲染规范

### 1. Key的唯一性要求

**核心原则：** React列表中的`key`必须在整个列表中保持唯一性，用于标识元素身份。

#### ❌ 错误示例

```javascript
// 错误1：使用可能重复的业务ID
items.map(item => <Item key={item.subject_id} />)

// 错误2：使用数组索引（在动态列表中）
items.map((item, index) => <Item key={index} />)

// 错误3：未添加key
items.map(item => <Item />)
```

**问题：**
- 业务ID可能重复（如`subject_id`、`hospital_id`）
- 数组索引在增删改时会导致渲染错误
- 缺少key会导致React警告和性能问题

#### ✅ 正确示例

```javascript
// 方案1：使用后端提供的唯一ID
items.map(item => (
  <Item key={item.unique_id} />
))

// 方案2：使用复合key（source + id + timestamp）
items.map(item => (
  <Item key={`${item.source}_${item.id}_${item.timestamp}`} />
))

// 方案3：合并多数据源时使用前缀 + 唯一标识
legacyData.map((item, index) => (
  <Item key={`legacy_${item.id}_${index}`} />
))
eyeTrackingData.map(item => (
  <Item key={`eyetrack_${item.id}_${item.timestamp}`} />
))
```

### 2. 实际案例：Module00 SubjectList

**问题场景：**
```javascript
// 原始代码 - 导致key重复错误
eyeTrackingData.forEach((subject) => {
  subjects.push({
    key: subject.subject_id,  // ❌ 会重复
    subject_id: subject.subject_id,
    ...
  });
});
```

**错误信息：**
```
Encountered two children with the same key, `control_111`.
Keys should be unique so that components maintain their identity across updates.
```

**修复方案：**
```javascript
// 修复后的代码
eyeTrackingData.forEach((subject, index) => {
  // 优先使用timestamp，其次使用index
  const uniqueKey = subject.timestamp
    ? `eyetrack_${subject.subject_id}_${subject.timestamp}`
    : `eyetrack_${subject.subject_id}_${index}`;

  subjects.push({
    key: uniqueKey,  // ✅ 确保唯一
    subject_id: subject.subject_id,
    timestamp: subject.timestamp,
    ...
  });
});
```

### 3. 推荐的Key生成策略

| 场景 | 推荐策略 | 示例 |
|------|---------|------|
| 单一数据源 | `source_${uniqueId}` | `legacy_${subject_id}_${index}` |
| 多数据源合并 | `${source}_${id}_${timestamp}` | `eyetrack_control_01_2025-3-27-11-37-22` |
| 有UUID | 直接使用UUID | `550e8400-e29b-41d4-a716-446655440000` |
| 有timestamp | `${id}_${timestamp}` | `subject_123_1709123456789` |
| 静态列表 | 可使用索引 | `index` (仅当列表不变时) |

---

## 组件设计规范

### 1. 组件文件结构

```javascript
/**
 * 组件描述
 * Component Description
 */
import React, { useState, useMemo, useCallback } from 'react';
import { Card, Button } from 'antd';
import PropTypes from 'prop-types';

const ComponentName = ({ prop1, prop2 }) => {
  // 1. State定义
  const [state, setState] = useState(initialValue);

  // 2. Memoized计算
  const memoizedValue = useMemo(() => {
    // 计算逻辑
  }, [dependencies]);

  // 3. 事件处理函数
  const handleEvent = useCallback(() => {
    // 处理逻辑
  }, [dependencies]);

  // 4. JSX渲染
  return (
    <div>
      {/* 组件内容 */}
    </div>
  );
};

// PropTypes定义
ComponentName.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.func,
};

export default ComponentName;
```

### 2. 组件命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 组件文件 | PascalCase | `DataScanner.jsx`, `SubjectList.jsx` |
| 组件名称 | PascalCase | `const DataScanner = () => {}` |
| Props | camelCase | `scanData`, `onScanComplete` |
| State变量 | camelCase | `loading`, `dataVersion` |
| 事件处理 | handle前缀 | `handleScan`, `handleImportComplete` |
| Callback props | on前缀 | `onScanComplete`, `onImportComplete` |

### 3. 组件目录结构

```
frontend/src/
├── components/          # 可复用组件
│   └── Module00/       # 模块专用组件
│       ├── DataScanner.jsx
│       ├── DataImporter.jsx
│       └── SubjectList.jsx
├── pages/              # 页面组件
│   └── Module00/
│       └── index.jsx
└── utils/              # 工具函数
```

---

## 数据处理规范

### 1. 数据合并规范

当合并多个数据源时，必须确保生成唯一标识：

```javascript
// ✅ 正确：为每个数据源添加唯一前缀
const allSubjects = useMemo(() => {
  const subjects = [];

  // Legacy数据
  legacyData.forEach((subject, index) => {
    subjects.push({
      key: `legacy_${subject.subject_id}_${index}`,
      source: 'legacy',
      data_version: 'v1',
      ...subject
    });
  });

  // Eye Tracking数据
  eyeTrackingData.forEach((subject, index) => {
    subjects.push({
      key: `eyetrack_${subject.subject_id}_${subject.timestamp || index}`,
      source: 'eye_tracking',
      data_version: 'v2',
      ...subject
    });
  });

  return subjects;
}, [legacyData, eyeTrackingData]);
```

### 2. 数据过滤规范

使用`useMemo`优化过滤性能：

```javascript
const filteredData = useMemo(() => {
  return allData.filter(item => {
    if (filter1 !== 'all' && item.field1 !== filter1) return false;
    if (filter2 !== 'all' && item.field2 !== filter2) return false;
    return true;
  });
}, [allData, filter1, filter2]);
```

### 3. 数据转换规范

```javascript
// ❌ 错误：直接修改原数据
items.forEach(item => {
  item.newField = processData(item);
});

// ✅ 正确：创建新对象
const processedItems = items.map(item => ({
  ...item,
  newField: processData(item)
}));
```

---

## API集成规范

### 1. API调用封装

```javascript
import axios from 'axios';
import { message } from 'antd';

const apiCall = async (endpoint, options = {}) => {
  try {
    const response = await axios({
      url: `/api/${endpoint}`,
      ...options
    });

    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.error || '请求失败');
    }
  } catch (error) {
    message.error(`API错误: ${error.message}`);
    throw error;
  }
};
```

### 2. 组件中的API调用

```javascript
const handleAction = async () => {
  setLoading(true);

  try {
    const response = await axios.get('/api/endpoint');

    if (response.data.success) {
      message.success('操作成功');
      onComplete?.(response.data);
    } else {
      message.error('操作失败：' + response.data.error);
    }
  } catch (error) {
    message.error('操作失败：' + error.message);
  } finally {
    setLoading(false);
  }
};
```

---

## 错误处理规范

### 1. 用户友好的错误提示

```javascript
// ✅ 提供具体的错误信息
if (!scanData) {
  return (
    <Alert
      message="请先扫描数据源"
      description="点击上方扫描按钮开始扫描"
      type="info"
      showIcon
    />
  );
}

// ✅ 处理API错误
try {
  await apiCall();
} catch (error) {
  Modal.error({
    title: '导入失败',
    content: error.message || '未知错误，请重试',
  });
}
```

### 2. Loading状态处理

```javascript
const [loading, setLoading] = useState(false);

const handleAction = async () => {
  setLoading(true);
  try {
    // 操作逻辑
  } finally {
    setLoading(false);  // 确保loading状态被重置
  }
};

// UI中的loading状态
<Button loading={loading} onClick={handleAction}>
  {loading ? '处理中...' : '开始处理'}
</Button>
```

---

## 代码审查检查点

### 1. React列表渲染检查

- [ ] 所有`.map()`渲染都使用了`key`
- [ ] Key在整个列表中唯一（不会重复）
- [ ] 合并多数据源时使用了前缀区分
- [ ] 没有使用数组索引作为动态列表的key

### 2. 组件设计检查

- [ ] 组件职责单一，功能明确
- [ ] Props有明确的类型定义
- [ ] 使用`useMemo`优化昂贵计算
- [ ] 使用`useCallback`优化事件处理函数
- [ ] State提升到合适的层级

### 3. 数据处理检查

- [ ] 没有直接修改原数据（保持不可变性）
- [ ] 过滤和转换使用了`useMemo`
- [ ] 数据合并时生成了唯一标识

### 4. API集成检查

- [ ] 所有API调用都有错误处理
- [ ] Loading状态正确管理（开始和结束）
- [ ] 用户操作有明确的反馈（成功/失败）
- [ ] 异步操作使用了`try...finally`确保状态重置

### 5. 用户体验检查

- [ ] 空状态有友好提示
- [ ] 错误信息具体且可操作
- [ ] 操作有确认对话框（危险操作）
- [ ] Loading期间禁用操作按钮

---

## 实际案例总结

### Case 1: Module00 SubjectList Key重复问题

**问题：** Eye Tracking数据中，多个受试者使用相同的`hospital_id`，导致生成的`subject_id`重复。

**教训：**
1. 业务ID不等于唯一ID
2. 合并数据源时必须确保key唯一
3. 优先使用timestamp等不可变标识符

**解决方案：**
```javascript
// 使用复合key
const uniqueKey = subject.timestamp
  ? `eyetrack_${subject.subject_id}_${subject.timestamp}`
  : `eyetrack_${subject.subject_id}_${index}`;
```

**预防措施：**
1. 代码审查时检查所有列表渲染
2. 测试时检查控制台是否有React警告
3. 多数据源合并时必须使用前缀区分

---

## 附录：常用工具函数

### 生成唯一Key

```javascript
// 生成复合唯一key
export const generateUniqueKey = (source, id, identifier) => {
  return `${source}_${id}_${identifier || Date.now()}`;
};

// 使用示例
const key = generateUniqueKey('legacy', subject.id, subject.timestamp);
```

### 安全的数据访问

```javascript
// 安全访问嵌套属性
export const safeGet = (obj, path, defaultValue = undefined) => {
  const keys = path.split('.');
  let result = obj;

  for (const key of keys) {
    if (result === null || result === undefined) {
      return defaultValue;
    }
    result = result[key];
  }

  return result !== undefined ? result : defaultValue;
};

// 使用示例
const count = safeGet(scanData, 'legacy_data.total_subjects', 0);
```

---

**文档版本：** v1.0
**最后更新：** 2025-10-02
**维护者：** Frontend Team
