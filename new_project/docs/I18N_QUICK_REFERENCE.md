# i18n Quick Reference Guide
# 国际化快速参考指南

## 🚀 快速开始

### 前端使用

```javascript
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t, i18n } = useTranslation(['namespace']);

  return (
    <div>
      {/* 基础翻译 */}
      <h1>{t('key')}</h1>

      {/* 命名空间翻译 */}
      <p>{t('namespace:key')}</p>

      {/* 带参数翻译 */}
      <span>{t('key', { count: 10, name: 'John' })}</span>

      {/* 切换语言 */}
      <button onClick={() => i18n.changeLanguage('en-US')}>
        English
      </button>
    </div>
  );
};
```

### 后端使用

```python
from flask_babel import gettext as _

@app.route('/api/data')
def get_data():
    return jsonify({
        "message": _("操作成功"),
        "count": _("共%(count)d条记录", count=100)
    })
```

---

## 📁 文件组织

### 前端翻译文件

```
frontend/src/locales/
├── zh-CN/
│   ├── common.json      # 通用：导航、按钮、状态
│   ├── module00.json    # 模块00
│   ├── module01.json    # 模块01
│   ├── charts.json      # 图表
│   └── errors.json      # 错误消息
├── en-US/
│   └── ...
└── ms-MY/
    └── ...
```

### 后端翻译文件

```
src/web/translations/
├── zh_CN/LC_MESSAGES/messages.po
├── en_US/LC_MESSAGES/messages.po
└── ms_MY/LC_MESSAGES/messages.po
```

---

## 🔑 翻译Key命名规范

### ✅ 推荐

```json
{
  "module00": {
    "title": "数据管理中心",
    "scanner": {
      "button": "扫描所有数据源",
      "scanning": "扫描中...",
      "success": "扫描完成"
    },
    "table": {
      "columns": {
        "id": "ID",
        "name": "名称"
      }
    }
  }
}
```

使用：`t('module00:scanner.button')`

### ❌ 避免

```json
{
  "btn1": "按钮",
  "text1": "文字",
  "label": "标签"
}
```

---

## 🌍 语言切换

### 前端

```javascript
// 获取当前语言
i18n.language // 'zh-CN'

// 切换语言
i18n.changeLanguage('en-US')

// 语言切换组件
<Select
  value={i18n.language}
  onChange={(lang) => i18n.changeLanguage(lang)}
>
  <Option value="zh-CN">🇨🇳 简体中文</Option>
  <Option value="en-US">🇬🇧 English</Option>
  <Option value="ms-MY">🇲🇾 Bahasa Melayu</Option>
</Select>
```

### 后端

```python
# 从请求头获取语言
@babel.localeselector
def get_locale():
    return request.headers.get('Accept-Language', 'zh_CN')

# 设置响应语言
response.headers['Content-Language'] = get_locale()
```

---

## 📊 图表国际化

### Plotly示例

```javascript
import { useTranslation } from 'react-i18next';

const Chart = () => {
  const { t } = useTranslation('charts');

  const layout = {
    title: { text: t('gazeTrajectory.title') },
    xaxis: { title: { text: t('gazeTrajectory.xaxis') } },
    yaxis: { title: { text: t('gazeTrajectory.yaxis') } }
  };

  return <Plot data={data} layout={layout} />;
};
```

**翻译文件：**
```json
{
  "gazeTrajectory": {
    "title": "注视轨迹图 / Gaze Trajectory / Trajektori Pandangan",
    "xaxis": "X坐标 / X Axis / Paksi X",
    "yaxis": "Y坐标 / Y Axis / Paksi Y"
  }
}
```

---

## 📄 常用翻译

### 通用操作

| 中文 | English | Bahasa Melayu | Key |
|------|---------|---------------|-----|
| 提交 | Submit | Hantar | `actions.submit` |
| 取消 | Cancel | Batal | `actions.cancel` |
| 保存 | Save | Simpan | `actions.save` |
| 删除 | Delete | Padam | `actions.delete` |
| 编辑 | Edit | Edit | `actions.edit` |
| 搜索 | Search | Cari | `actions.search` |
| 导出 | Export | Eksport | `actions.export` |
| 导入 | Import | Import | `actions.import` |

### 状态消息

| 中文 | English | Bahasa Melayu | Key |
|------|---------|---------------|-----|
| 加载中... | Loading... | Memuatkan... | `status.loading` |
| 操作成功 | Success | Berjaya | `status.success` |
| 操作失败 | Error | Ralat | `status.error` |
| 暂无数据 | No Data | Tiada Data | `status.noData` |

### Module00专用

| 中文 | English | Bahasa Melayu | Key |
|------|---------|---------------|-----|
| 数据管理中心 | Data Management Center | Pusat Pengurusan Data | `module00:title` |
| 扫描所有数据源 | Scan All Data Sources | Imbas Semua Sumber Data | `module00:scanner.button` |
| 导入成功 | Import Successful | Import Berjaya | `module00:importer.success` |
| 对照组 | Control Group | Kumpulan Kawalan | `module00:dataSource.control` |
| MCI组 | MCI Group | Kumpulan MCI | `module00:dataSource.mci` |
| AD组 | AD Group | Kumpulan AD | `module00:dataSource.ad` |

---

## 🛠️ 开发工具

### VSCode扩展

**i18n Ally** - 必装！
```bash
code --install-extension Lokalise.i18n-ally
```

功能：
- ✅ 翻译文件自动补全
- ✅ 内联显示翻译
- ✅ 缺失翻译检测
- ✅ 翻译进度统计

### 命令行工具

**提取新翻译：**
```bash
# 前端
npm run i18n:extract

# 后端
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d src/web/translations
```

**编译翻译：**
```bash
# 后端
pybabel compile -d src/web/translations
```

---

## ✅ 检查清单

### 添加新功能时

- [ ] 所有UI文字使用`t()`函数
- [ ] 创建对应的翻译key
- [ ] 翻译为三种语言
- [ ] 图表标题、坐标轴使用翻译
- [ ] API响应消息使用`_()`函数
- [ ] 测试三种语言显示

### 代码审查

- [ ] 无硬编码文字
- [ ] 翻译key语义化
- [ ] 三语翻译完整
- [ ] 参数化翻译正确
- [ ] 字体支持检查

---

## ⚠️ 常见陷阱与最佳实践

### 🚨 陷阱1: 变量名与翻译函数冲突

**问题描述：**
使用 `useTranslation()` 返回的 `t` 函数时，在回调函数中使用相同的变量名会导致命名冲突。

**❌ 错误示例：**
```javascript
const { t } = useTranslation(['module01']);

// ❌ 错误：map回调中的参数t覆盖了翻译函数t
const data = time.map((t, i) => `${t('label')}: ${t.toFixed(2)}`);
//                      ↑ 这个t是数字，不是翻译函数！
```

**错误信息：**
```
Uncaught TypeError: t is not a function
```

**✅ 正确示例：**
```javascript
const { t } = useTranslation(['module01']);

// ✅ 正确：使用不同的变量名
const data = time.map((timeValue, i) => `${t('label')}: ${timeValue.toFixed(2)}`);
//                      ↑ 使用语义化的变量名

// ✅ 其他推荐的变量名
time.map((timestamp, i) => ...)
data.map((item, idx) => ...)
values.map((value, index) => ...)
```

**最佳实践：**
1. **避免使用单字母变量名**，尤其是 `t`, `i`, `e` 等常用名称
2. **使用描述性变量名**：`timeValue`, `item`, `element`, `entry` 等
3. **在useMemo依赖中包含t**：确保翻译函数变化时重新计算

```javascript
const plotData = useMemo(() => {
  // ... 使用 t() 的代码
}, [data, t]); // ← 重要：将 t 添加到依赖数组
```

### 🚨 陷阱2: 字符串拼接而非参数化

**❌ 错误示例：**
```javascript
// 难以翻译和维护
const msg = '共导入 ' + count + ' 名受试者';
```

**✅ 正确示例：**
```javascript
// 翻译文件
{
  "importSuccess": "共导入 {{count}} 名受试者"
}

// 使用
t('importSuccess', { count })
```

### 🚨 陷阱3: 在循环或条件中定义useTranslation

**❌ 错误示例：**
```javascript
if (condition) {
  const { t } = useTranslation(); // ❌ Hook只能在顶层调用
}
```

**✅ 正确示例：**
```javascript
const { t } = useTranslation(); // ✅ 在组件顶层调用

if (condition) {
  return <div>{t('key')}</div>;
}
```

### 🚨 陷阱4: 图表配置对象未使用useMemo包裹

**问题描述：**
图表配置对象（layout、config等）如果包含翻译函数调用，但没有使用useMemo包裹，会导致语言切换时不更新。

**❌ 错误示例：**
```javascript
const { t } = useTranslation(['module01']);

// ❌ 错误：layout是普通对象，不会响应语言变化
const layout = {
  xaxis: { title: t('xAxis') },
  yaxis: { title: t('yAxis') }
};
// 语言切换时，layout不会重新计算，仍然显示旧语言！
```

**✅ 正确示例：**
```javascript
const { t } = useTranslation(['module01']);

// ✅ 正确：使用useMemo并添加t依赖
const layout = useMemo(() => ({
  xaxis: { title: t('xAxis') },
  yaxis: { title: t('yAxis') }
}), [t]); // ← t作为依赖，语言切换时会重新计算
```

**完整示例（图表组件）：**
```javascript
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

const MyChart = ({ data }) => {
  const { t } = useTranslation(['charts']);

  // ✅ plotData使用useMemo，包含t依赖
  const plotData = useMemo(() => {
    return [{
      x: data.x,
      y: data.y,
      name: t('dataSeriesName'),
      text: data.x.map((val, i) => `${t('point')} ${i}`)
    }];
  }, [data, t]); // ← 重要：包含t

  // ✅ layout使用useMemo，包含t依赖
  const layout = useMemo(() => ({
    title: t('chartTitle'),
    xaxis: { title: t('xAxisLabel') },
    yaxis: { title: t('yAxisLabel') }
  }), [t]); // ← 重要：包含t

  return <Plot data={plotData} layout={layout} />;
};
```

---

## 🐛 常见问题

### Q: 翻译不生效？

**A:** 检查以下几点：
1. 确认翻译文件已正确导入
2. 检查翻译key是否正确
3. 确认当前语言设置
4. 查看浏览器控制台错误
5. **检查是否有变量名冲突**（特别是 `t` 变量）

```javascript
// 调试语言设置
console.log(i18n.language); // 当前语言
console.log(i18n.options.resources); // 加载的翻译资源
console.log(typeof t); // 应该是 'function'
```

### Q: 参数化翻译如何使用？

**A:** 使用`{{}}`包裹参数：

```javascript
// 翻译文件
{
  "message": "共导入 {{count}} 名受试者"
}

// 使用
t('message', { count: 10 })
// 输出: "共导入 10 名受试者"
```

### Q: 复数形式如何处理？

**A:** 使用`_plural`后缀：

```json
{
  "item": "项目",
  "item_plural": "项目"
}
```

```javascript
t('item', { count: 1 })  // "1 项目"
t('item', { count: 5 })  // "5 项目"
```

---

## 📚 完整示例

### Module00 完整国际化

**组件代码：**
```javascript
import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Button, message } from 'antd';

const DataScanner = () => {
  const { t } = useTranslation('module00');
  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    setScanning(true);
    try {
      const result = await api.scanAll();
      message.success(t('scanner.success'));
    } catch (error) {
      message.error(t('scanner.error'));
    } finally {
      setScanning(false);
    }
  };

  return (
    <Card title={t('scanner.title')}>
      <Button
        type="primary"
        onClick={handleScan}
        loading={scanning}
      >
        {scanning ? t('scanner.scanning') : t('scanner.button')}
      </Button>
    </Card>
  );
};
```

**翻译文件 (zh-CN/module00.json):**
```json
{
  "scanner": {
    "title": "数据扫描",
    "button": "扫描所有数据源",
    "scanning": "扫描中...",
    "success": "扫描完成！",
    "error": "扫描失败"
  }
}
```

---

**快速参考完成！** 🎉

查看完整文档：[I18N_ARCHITECTURE_DESIGN.md](I18N_ARCHITECTURE_DESIGN.md)
