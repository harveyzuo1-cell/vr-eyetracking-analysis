# Internationalization (i18n) Architecture Design
# 国际化架构设计

**支持语言 / Supported Languages:**
- 🇨🇳 简体中文 (zh-CN)
- 🇬🇧 English (en-US)
- 🇲🇾 Bahasa Melayu (ms-MY)

---

## Table of Contents / 目录

1. [架构概览](#架构概览)
2. [前端国际化方案](#前端国际化方案)
3. [后端国际化方案](#后端国际化方案)
4. [图表国际化方案](#图表国际化方案)
5. [报表国际化方案](#报表国际化方案)
6. [实施计划](#实施计划)

---

## 架构概览

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面 / User Interface             │
│                  (语言切换 / Language Switcher)          │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌──────▼──────────┐
│  Frontend i18n │  │  Backend i18n   │
│  (react-i18next)│  │  (Flask-Babel)  │
└───────┬────────┘  └──────┬──────────┘
        │                   │
        │     ┌─────────────┴─────────────┐
        │     │                           │
┌───────▼─────▼──────┐        ┌──────────▼─────────┐
│  Chart i18n        │        │  Report i18n       │
│  (Plotly/Recharts) │        │  (PDF/Excel)       │
└────────────────────┘        └────────────────────┘
```

### 技术栈选择

| 层级 | 技术方案 | 理由 |
|------|---------|------|
| **Frontend** | react-i18next | React生态最成熟的i18n方案 |
| **Backend** | Flask-Babel | Flask官方推荐的国际化扩展 |
| **Chart** | 自定义翻译函数 | 与前端i18n集成 |
| **Report** | 模板 + 翻译字典 | 灵活支持多格式导出 |

---

## 前端国际化方案

### 1. 技术方案：react-i18next

**安装依赖：**
```bash
npm install react-i18next i18next i18next-browser-languagedetector
```

### 2. 目录结构

```
frontend/src/
├── locales/                    # 翻译文件目录
│   ├── zh-CN/                 # 简体中文
│   │   ├── common.json        # 通用翻译
│   │   ├── module00.json      # 模块00翻译
│   │   ├── module01.json      # 模块01翻译
│   │   └── errors.json        # 错误信息
│   ├── en-US/                 # 英文
│   │   ├── common.json
│   │   ├── module00.json
│   │   └── ...
│   └── ms-MY/                 # 马来文
│       ├── common.json
│       ├── module00.json
│       └── ...
├── i18n/                      # i18n配置
│   └── config.js              # i18n初始化配置
└── components/
    └── LanguageSwitcher/      # 语言切换器组件
        └── index.jsx
```

### 3. 配置文件

**i18n/config.js:**
```javascript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 导入翻译文件
import zhCN_common from '../locales/zh-CN/common.json';
import zhCN_module00 from '../locales/zh-CN/module00.json';
import enUS_common from '../locales/en-US/common.json';
import enUS_module00 from '../locales/en-US/module00.json';
import msMY_common from '../locales/ms-MY/common.json';
import msMY_module00 from '../locales/ms-MY/module00.json';

const resources = {
  'zh-CN': {
    common: zhCN_common,
    module00: zhCN_module00,
  },
  'en-US': {
    common: enUS_common,
    module00: enUS_module00,
  },
  'ms-MY': {
    common: msMY_common,
    module00: msMY_module00,
  },
};

i18n
  .use(LanguageDetector) // 自动检测用户语言
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'zh-CN', // 默认语言
    defaultNS: 'common',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'], // 优先从localStorage读取
      caches: ['localStorage'],
    },
  });

export default i18n;
```

### 4. 翻译文件示例

**locales/zh-CN/common.json:**
```json
{
  "app": {
    "title": "VR眼球追踪数据分析平台",
    "subtitle": "VR Eye Tracking Data Analysis Platform"
  },
  "nav": {
    "dashboard": "仪表盘",
    "module00": "数据管理",
    "module01": "数据上传"
  },
  "actions": {
    "submit": "提交",
    "cancel": "取消",
    "save": "保存",
    "delete": "删除",
    "edit": "编辑",
    "search": "搜索",
    "export": "导出",
    "import": "导入"
  },
  "status": {
    "loading": "加载中...",
    "success": "操作成功",
    "error": "操作失败",
    "noData": "暂无数据"
  }
}
```

**locales/en-US/common.json:**
```json
{
  "app": {
    "title": "VR Eye Tracking Data Analysis Platform",
    "subtitle": "VR Eye Tracking Data Analysis Platform"
  },
  "nav": {
    "dashboard": "Dashboard",
    "module00": "Data Management",
    "module01": "Data Upload"
  },
  "actions": {
    "submit": "Submit",
    "cancel": "Cancel",
    "save": "Save",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "export": "Export",
    "import": "Import"
  },
  "status": {
    "loading": "Loading...",
    "success": "Success",
    "error": "Error",
    "noData": "No Data"
  }
}
```

**locales/ms-MY/common.json:**
```json
{
  "app": {
    "title": "Platform Analisis Data Penjejakan Mata VR",
    "subtitle": "VR Eye Tracking Data Analysis Platform"
  },
  "nav": {
    "dashboard": "Papan Pemuka",
    "module00": "Pengurusan Data",
    "module01": "Muat Naik Data"
  },
  "actions": {
    "submit": "Hantar",
    "cancel": "Batal",
    "save": "Simpan",
    "delete": "Padam",
    "edit": "Edit",
    "search": "Cari",
    "export": "Eksport",
    "import": "Import"
  },
  "status": {
    "loading": "Memuatkan...",
    "success": "Berjaya",
    "error": "Ralat",
    "noData": "Tiada Data"
  }
}
```

### 5. Module00 翻译示例

**locales/zh-CN/module00.json:**
```json
{
  "title": "数据管理中心",
  "subtitle": "双数据源统一管理",
  "dataSource": {
    "title": "数据源概览",
    "legacy": "Legacy数据 (v1)",
    "eyeTracking": "Eye Tracking数据 (v2)",
    "total": "总受试者数",
    "control": "对照组",
    "mci": "MCI组",
    "ad": "AD组"
  },
  "scanner": {
    "title": "数据扫描",
    "button": "扫描所有数据源",
    "scanning": "扫描中...",
    "success": "扫描完成！",
    "error": "扫描失败"
  },
  "importer": {
    "title": "数据导入",
    "selectSource": "选择数据源",
    "all": "全部导入",
    "legacyOnly": "仅Legacy (v1)",
    "eyeTrackingOnly": "仅Eye Tracking (v2)",
    "overwrite": "覆盖已存在数据",
    "button": "开始导入",
    "importing": "导入中...",
    "success": "导入成功！共导入 {{count}} 名受试者",
    "error": "导入失败"
  },
  "subjectList": {
    "title": "受试者列表",
    "count": "{{count}}名",
    "filters": {
      "version": {
        "all": "全部版本",
        "v1": "Legacy v1",
        "v2": "Eye Tracking v2"
      },
      "group": {
        "all": "全部分组",
        "control": "Control",
        "mci": "MCI",
        "ad": "AD"
      }
    },
    "columns": {
      "subjectId": "Subject ID",
      "name": "姓名",
      "hospitalId": "Hospital ID",
      "group": "分组",
      "version": "数据版本",
      "source": "数据源",
      "timestamp": "时间戳"
    }
  }
}
```

**locales/en-US/module00.json:**
```json
{
  "title": "Data Management Center",
  "subtitle": "Dual Data Source Management",
  "dataSource": {
    "title": "Data Source Overview",
    "legacy": "Legacy Data (v1)",
    "eyeTracking": "Eye Tracking Data (v2)",
    "total": "Total Subjects",
    "control": "Control Group",
    "mci": "MCI Group",
    "ad": "AD Group"
  },
  "scanner": {
    "title": "Data Scanning",
    "button": "Scan All Data Sources",
    "scanning": "Scanning...",
    "success": "Scan completed!",
    "error": "Scan failed"
  },
  "importer": {
    "title": "Data Import",
    "selectSource": "Select Data Source",
    "all": "Import All",
    "legacyOnly": "Legacy Only (v1)",
    "eyeTrackingOnly": "Eye Tracking Only (v2)",
    "overwrite": "Overwrite Existing Data",
    "button": "Start Import",
    "importing": "Importing...",
    "success": "Import successful! {{count}} subjects imported",
    "error": "Import failed"
  },
  "subjectList": {
    "title": "Subject List",
    "count": "{{count}} subjects",
    "filters": {
      "version": {
        "all": "All Versions",
        "v1": "Legacy v1",
        "v2": "Eye Tracking v2"
      },
      "group": {
        "all": "All Groups",
        "control": "Control",
        "mci": "MCI",
        "ad": "AD"
      }
    },
    "columns": {
      "subjectId": "Subject ID",
      "name": "Name",
      "hospitalId": "Hospital ID",
      "group": "Group",
      "version": "Data Version",
      "source": "Data Source",
      "timestamp": "Timestamp"
    }
  }
}
```

**locales/ms-MY/module00.json:**
```json
{
  "title": "Pusat Pengurusan Data",
  "subtitle": "Pengurusan Sumber Data Dwi",
  "dataSource": {
    "title": "Gambaran Sumber Data",
    "legacy": "Data Legacy (v1)",
    "eyeTracking": "Data Penjejakan Mata (v2)",
    "total": "Jumlah Subjek",
    "control": "Kumpulan Kawalan",
    "mci": "Kumpulan MCI",
    "ad": "Kumpulan AD"
  },
  "scanner": {
    "title": "Pengimbasan Data",
    "button": "Imbas Semua Sumber Data",
    "scanning": "Mengimbas...",
    "success": "Pengimbasan selesai!",
    "error": "Pengimbasan gagal"
  },
  "importer": {
    "title": "Import Data",
    "selectSource": "Pilih Sumber Data",
    "all": "Import Semua",
    "legacyOnly": "Legacy Sahaja (v1)",
    "eyeTrackingOnly": "Penjejakan Mata Sahaja (v2)",
    "overwrite": "Tulis Ganti Data Sedia Ada",
    "button": "Mula Import",
    "importing": "Mengimport...",
    "success": "Import berjaya! {{count}} subjek diimport",
    "error": "Import gagal"
  },
  "subjectList": {
    "title": "Senarai Subjek",
    "count": "{{count}} subjek",
    "filters": {
      "version": {
        "all": "Semua Versi",
        "v1": "Legacy v1",
        "v2": "Penjejakan Mata v2"
      },
      "group": {
        "all": "Semua Kumpulan",
        "control": "Kawalan",
        "mci": "MCI",
        "ad": "AD"
      }
    },
    "columns": {
      "subjectId": "ID Subjek",
      "name": "Nama",
      "hospitalId": "ID Hospital",
      "group": "Kumpulan",
      "version": "Versi Data",
      "source": "Sumber Data",
      "timestamp": "Cap Masa"
    }
  }
}
```

### 6. 组件使用示例

**LanguageSwitcher组件:**
```javascript
import React from 'react';
import { Select } from 'antd';
import { useTranslation } from 'react-i18next';
import { GlobalOutlined } from '@ant-design/icons';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();

  const languages = [
    { value: 'zh-CN', label: '简体中文', flag: '🇨🇳' },
    { value: 'en-US', label: 'English', flag: '🇬🇧' },
    { value: 'ms-MY', label: 'Bahasa Melayu', flag: '🇲🇾' },
  ];

  const handleChange = (value) => {
    i18n.changeLanguage(value);
  };

  return (
    <Select
      value={i18n.language}
      onChange={handleChange}
      style={{ width: 180 }}
      suffixIcon={<GlobalOutlined />}
    >
      {languages.map(lang => (
        <Select.Option key={lang.value} value={lang.value}>
          <span>{lang.flag} {lang.label}</span>
        </Select.Option>
      ))}
    </Select>
  );
};

export default LanguageSwitcher;
```

**在Module00中使用:**
```javascript
import React from 'react';
import { useTranslation } from 'react-i18next';

const Module00 = () => {
  const { t } = useTranslation(['module00', 'common']);

  return (
    <div>
      <h1>{t('module00:title')}</h1>
      <p>{t('module00:subtitle')}</p>

      <Button onClick={handleScan}>
        {scanning ? t('module00:scanner.scanning') : t('module00:scanner.button')}
      </Button>

      {/* 带参数的翻译 */}
      <span>{t('module00:subjectList.count', { count: subjects.length })}</span>
    </div>
  );
};
```

---

## 后端国际化方案

### 1. 技术方案：Flask-Babel

**安装依赖：**
```bash
pip install Flask-Babel
```

### 2. 目录结构

```
new_project/
├── src/
│   └── web/
│       ├── translations/           # 翻译文件目录
│       │   ├── zh_CN/
│       │   │   └── LC_MESSAGES/
│       │   │       └── messages.po
│       │   ├── en_US/
│       │   │   └── LC_MESSAGES/
│       │   │       └── messages.po
│       │   └── ms_MY/
│       │       └── LC_MESSAGES/
│       │           └── messages.po
│       └── i18n/
│           └── config.py           # Babel配置
└── babel.cfg                       # Babel配置文件
```

### 3. 配置文件

**run.py (添加Babel):**
```python
from flask import Flask, request
from flask_babel import Babel, gettext as _
from flask_cors import CORS

app = Flask(__name__)

# Babel配置
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
app.config['BABEL_SUPPORTED_LOCALES'] = ['zh_CN', 'en_US', 'ms_MY']

babel = Babel(app)

@babel.localeselector
def get_locale():
    """自动检测语言"""
    # 1. 从请求头获取
    lang = request.headers.get('Accept-Language')
    if lang:
        return lang.split(',')[0].replace('-', '_')

    # 2. 从URL参数获取
    lang = request.args.get('lang')
    if lang:
        return lang.replace('-', '_')

    # 3. 默认语言
    return 'zh_CN'

# CORS配置
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "expose_headers": ["Content-Language"]
    }
})
```

### 4. API响应国际化

**api.py (使用翻译):**
```python
from flask import Blueprint, jsonify, request
from flask_babel import gettext as _

m00_bp = Blueprint('module00', __name__, url_prefix='/api/m00')

@m00_bp.route('/scan-all', methods=['GET'])
def scan_all():
    """扫描所有数据源"""
    try:
        result = data_service.scan_all_sources()
        return jsonify({
            "success": True,
            "message": _("扫描完成"),  # 自动翻译
            **result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": _("扫描失败: %(error)s", error=str(e))
        }), 500

@m00_bp.route('/import', methods=['POST'])
def import_data():
    """导入数据"""
    try:
        data = request.json
        result = data_service.import_data(data)

        return jsonify({
            "success": True,
            "message": _("导入成功！共导入 %(count)d 名受试者",
                        count=result['imported_count']),
            **result
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": _("数据验证失败: %(error)s", error=str(e))
        }), 400
```

### 5. 翻译文件管理

**提取翻译字符串：**
```bash
# 提取所有翻译字符串
pybabel extract -F babel.cfg -o messages.pot .

# 初始化语言
pybabel init -i messages.pot -d src/web/translations -l zh_CN
pybabel init -i messages.pot -d src/web/translations -l en_US
pybabel init -i messages.pot -d src/web/translations -l ms_MY

# 编译翻译
pybabel compile -d src/web/translations
```

**messages.po示例 (zh_CN):**
```po
msgid "扫描完成"
msgstr "扫描完成"

msgid "扫描失败: %(error)s"
msgstr "扫描失败: %(error)s"

msgid "导入成功！共导入 %(count)d 名受试者"
msgstr "导入成功！共导入 %(count)d 名受试者"
```

**messages.po示例 (en_US):**
```po
msgid "扫描完成"
msgstr "Scan completed"

msgid "扫描失败: %(error)s"
msgstr "Scan failed: %(error)s"

msgid "导入成功！共导入 %(count)d 名受试者"
msgstr "Import successful! %(count)d subjects imported"
```

**messages.po示例 (ms_MY):**
```po
msgid "扫描完成"
msgstr "Pengimbasan selesai"

msgid "扫描失败: %(error)s"
msgstr "Pengimbasan gagal: %(error)s"

msgid "导入成功！共导入 %(count)d 名受试者"
msgstr "Import berjaya! %(count)d subjek diimport"
```

---

## 图表国际化方案

### 1. Plotly图表国际化

**创建翻译辅助函数:**
```javascript
// utils/chartI18n.js
import i18n from '../i18n/config';

export const getChartTranslations = (namespace = 'charts') => {
  return {
    title: i18n.t(`${namespace}:title`),
    xaxis: i18n.t(`${namespace}:xaxis`),
    yaxis: i18n.t(`${namespace}:yaxis`),
    legend: i18n.t(`${namespace}:legend`),
  };
};

export const createLocalizedLayout = (baseLayout, translationKey) => {
  const { t } = i18n;

  return {
    ...baseLayout,
    title: {
      text: t(`${translationKey}.title`),
      font: { size: 16 }
    },
    xaxis: {
      ...baseLayout.xaxis,
      title: { text: t(`${translationKey}.xaxis`) }
    },
    yaxis: {
      ...baseLayout.yaxis,
      title: { text: t(`${translationKey}.yaxis`) }
    },
    legend: {
      ...baseLayout.legend,
      title: { text: t(`${translationKey}.legend`) }
    }
  };
};
```

**翻译文件 (charts.json):**
```json
// locales/zh-CN/charts.json
{
  "gazeTrajectory": {
    "title": "注视轨迹图",
    "xaxis": "X坐标",
    "yaxis": "Y坐标",
    "legend": "受试者"
  },
  "heatmap": {
    "title": "热力图",
    "xaxis": "X坐标",
    "yaxis": "Y坐标",
    "legend": "注视密度"
  }
}

// locales/en-US/charts.json
{
  "gazeTrajectory": {
    "title": "Gaze Trajectory",
    "xaxis": "X Coordinate",
    "yaxis": "Y Coordinate",
    "legend": "Subject"
  },
  "heatmap": {
    "title": "Heatmap",
    "xaxis": "X Coordinate",
    "yaxis": "Y Coordinate",
    "legend": "Gaze Density"
  }
}

// locales/ms-MY/charts.json
{
  "gazeTrajectory": {
    "title": "Trajektori Pandangan",
    "xaxis": "Koordinat X",
    "yaxis": "Koordinat Y",
    "legend": "Subjek"
  },
  "heatmap": {
    "title": "Peta Haba",
    "xaxis": "Koordinat X",
    "yaxis": "Koordinat Y",
    "legend": "Ketumpatan Pandangan"
  }
}
```

**使用示例:**
```javascript
import React from 'react';
import Plot from 'react-plotly.js';
import { useTranslation } from 'react-i18next';
import { createLocalizedLayout } from '../utils/chartI18n';

const GazeTrajectoryChart = ({ data }) => {
  const { i18n } = useTranslation();

  const baseLayout = {
    width: 800,
    height: 600,
    xaxis: { range: [0, 1920] },
    yaxis: { range: [0, 1080] },
  };

  const layout = createLocalizedLayout(baseLayout, 'charts:gazeTrajectory');

  return <Plot data={data} layout={layout} />;
};
```

### 2. 后端生成图表国际化

**Python图表生成:**
```python
from flask_babel import gettext as _
import plotly.graph_objects as go

def create_localized_chart(data, chart_type='trajectory'):
    """创建本地化图表"""

    if chart_type == 'trajectory':
        fig = go.Figure(data=[
            go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='lines+markers',
                name=_('受试者轨迹')
            )
        ])

        fig.update_layout(
            title=_('注视轨迹图'),
            xaxis_title=_('X坐标'),
            yaxis_title=_('Y坐标'),
            font=dict(
                family="Arial, sans-serif",
                size=12
            )
        )

    return fig

# 导出为图片
def export_chart_image(fig, filename, lang='zh_CN'):
    """导出图表为图片"""
    # 根据语言选择字体
    font_family = {
        'zh_CN': 'Microsoft YaHei, SimHei, Arial',
        'en_US': 'Arial, Helvetica, sans-serif',
        'ms_MY': 'Arial, Helvetica, sans-serif'
    }.get(lang, 'Arial')

    fig.update_layout(font_family=font_family)
    fig.write_image(filename)
```

---

## 报表国际化方案

### 1. PDF报表

**使用reportlab + 翻译模板:**
```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask_babel import gettext as _

# 注册中文字体
pdfmetrics.registerFont(TTFont('SimHei', 'SimHei.ttf'))

def generate_report_pdf(data, lang='zh_CN'):
    """生成PDF报告"""
    filename = f"report_{lang}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)

    # 设置字体
    font = 'SimHei' if lang == 'zh_CN' else 'Helvetica'
    c.setFont(font, 16)

    # 标题
    c.drawString(100, 800, _('VR眼球追踪数据分析报告'))

    c.setFont(font, 12)
    c.drawString(100, 770, _('受试者: %(subject)s', subject=data['subject_id']))
    c.drawString(100, 750, _('分组: %(group)s', group=data['group']))
    c.drawString(100, 730, _('分析日期: %(date)s', date=data['date']))

    # 分析结果
    y = 700
    c.drawString(100, y, _('分析结果:'))
    for key, value in data['results'].items():
        y -= 20
        c.drawString(120, y, f"{_(key)}: {value}")

    c.save()
    return filename
```

### 2. Excel报表

**使用openpyxl + 翻译:**
```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from flask_babel import gettext as _

def generate_report_excel(data, lang='zh_CN'):
    """生成Excel报告"""
    wb = Workbook()
    ws = wb.active
    ws.title = _('分析报告')

    # 标题行
    headers = [
        _('受试者ID'),
        _('分组'),
        _('数据版本'),
        _('分析指标1'),
        _('分析指标2'),
    ]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # 数据行
    for row, item in enumerate(data, start=2):
        ws.cell(row=row, column=1, value=item['subject_id'])
        ws.cell(row=row, column=2, value=_(item['group']))
        ws.cell(row=row, column=3, value=item['version'])
        ws.cell(row=row, column=4, value=item['metric1'])
        ws.cell(row=row, column=5, value=item['metric2'])

    filename = f"report_{lang}.xlsx"
    wb.save(filename)
    return filename
```

---

## 实施计划

### Phase 1: 前端基础国际化 (Week 1-2)

**任务清单：**
- [ ] 安装react-i18next依赖
- [ ] 创建i18n配置文件
- [ ] 创建翻译文件目录结构
- [ ] 翻译common.json (通用文字)
- [ ] 翻译module00.json (Module00)
- [ ] 创建LanguageSwitcher组件
- [ ] 集成到MainLayout

**交付物：**
- ✅ 前端UI支持三语切换
- ✅ Module00完全国际化
- ✅ 语言设置持久化

### Phase 2: 后端API国际化 (Week 3)

**任务清单：**
- [ ] 安装Flask-Babel
- [ ] 配置Babel
- [ ] 提取翻译字符串
- [ ] 创建.po翻译文件
- [ ] 翻译API响应消息
- [ ] 翻译错误信息

**交付物：**
- ✅ API响应支持多语言
- ✅ 错误消息本地化

### Phase 3: 图表国际化 (Week 4)

**任务清单：**
- [ ] 创建图表翻译文件
- [ ] 创建图表i18n工具函数
- [ ] 更新Plotly图表
- [ ] 更新Recharts图表
- [ ] 后端图表生成国际化

**交付物：**
- ✅ 所有图表支持多语言
- ✅ 图片导出包含翻译

### Phase 4: 报表国际化 (Week 5)

**任务清单：**
- [ ] PDF报表模板国际化
- [ ] Excel报表国际化
- [ ] 字体支持优化
- [ ] 测试三语报表生成

**交付物：**
- ✅ PDF/Excel报表支持三语
- ✅ 中文字体正确显示

### Phase 5: 全面测试 (Week 6)

**测试清单：**
- [ ] 功能测试（每个语言）
- [ ] UI显示测试
- [ ] 图表渲染测试
- [ ] 报表生成测试
- [ ] 性能测试
- [ ] 兼容性测试

---

## 最佳实践

### 1. 翻译管理

✅ **推荐做法：**
- 使用命名空间组织翻译（common, module00, errors等）
- 翻译key使用语义化命名（`scanner.button`而非`btn1`）
- 保持翻译文件结构一致
- 使用参数化翻译（`{{count}}`）

❌ **避免：**
- 硬编码文字
- 翻译key过于简单（`title`, `button`）
- 不同语言文件结构不一致

### 2. 性能优化

**懒加载翻译文件：**
```javascript
// 动态导入翻译文件
const loadTranslations = async (lang, namespace) => {
  const translations = await import(`./locales/${lang}/${namespace}.json`);
  i18n.addResourceBundle(lang, namespace, translations.default);
};
```

**缓存翻译：**
```javascript
// localStorage缓存
i18n.init({
  backend: {
    loadPath: '/locales/{{lng}}/{{ns}}.json',
    addPath: '/locales/add/{{lng}}/{{ns}}',
  },
  cache: {
    enabled: true,
    prefix: 'i18next_res_',
    expirationTime: 7 * 24 * 60 * 60 * 1000, // 7天
  },
});
```

### 3. 字体支持

**多语言字体配置：**
```css
/* 全局字体 */
body {
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    'PingFang SC',        /* 中文 */
    'Hiragino Sans GB',   /* 中文 */
    'Microsoft YaHei',    /* 中文 */
    'Noto Sans CJK',      /* 中日韩 */
    'Noto Sans',          /* 通用 */
    Arial,
    sans-serif;
}
```

---

## 附录

### A. 语言代码映射

| 语言 | ISO 639-1 | Locale Code | 显示名称 |
|------|-----------|-------------|---------|
| 简体中文 | zh | zh-CN / zh_CN | 简体中文 |
| 英文 | en | en-US / en_US | English |
| 马来文 | ms | ms-MY / ms_MY | Bahasa Melayu |

### B. 参考资源

**文档：**
- [react-i18next](https://react.i18next.com/)
- [Flask-Babel](https://python-babel.github.io/flask-babel/)
- [ICU Message Format](https://unicode-org.github.io/icu/userguide/format_parse/messages/)

**工具：**
- [i18n Ally](https://marketplace.visualstudio.com/items?itemName=Lokalise.i18n-ally) - VSCode扩展
- [POEdit](https://poedit.net/) - .po文件编辑器
- [Google Translate API](https://cloud.google.com/translate) - 自动翻译

---

**文档版本 / Version:** 1.0
**创建日期 / Created:** 2025-10-02
**维护者 / Maintainer:** Development Team
