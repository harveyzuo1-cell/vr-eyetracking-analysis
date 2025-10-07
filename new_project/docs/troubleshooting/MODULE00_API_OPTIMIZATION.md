# Module00 API优化文档
## Module00 API Optimization Documentation

**日期 / Date**: 2025-10-07
**版本 / Version**: 1.1.0

---

## 📋 问题描述 / Problem Description

### 原始问题
用户发现Module00的"扫描所有数据"功能显示的数据统计不正确：
- 显示V2为84个，实际已导入93个
- 显示V1为62个，实际已导入60个

### 根本原因
Module00的`/scan-all` API执行的是**扫描原始数据源目录**的操作，而不是读取**已导入数据的实际统计**。

**核心差异**:
1. **扫描原始数据源** (`/scan-all`):
   - 扫描`data/*_raw/`和`eye_tracking_data/`目录
   - 统计**可导入**的受试者数量
   - 可能与已导入数据不一致

2. **读取已导入数据** (新API `imported-stats`):
   - 读取`subject_metadata.json`
   - 统计**实际已导入**的受试者数量
   - 反映真实的数据状态

---

## 🔧 解决方案 / Solution

### 1. 新增API端点

**端点**: `GET /api/m00/imported-stats`

**功能**: 获取已导入数据的真实统计信息

**响应示例**:
```json
{
    "success": true,
    "v1_data": {
        "control": 20,
        "mci": 20,
        "ad": 20,
        "total": 60
    },
    "v2_data": {
        "control": 77,
        "mci": 8,
        "ad": 8,
        "total": 93
    },
    "summary": {
        "total_subjects": 153,
        "v1_count": 60,
        "v2_count": 93
    }
}
```

### 2. 实现位置

**文件**: [service.py](src/web/modules/module00_data_management/service.py:397-469)

**核心方法**: `get_imported_data_stats()`

**实现逻辑**:
```python
def get_imported_data_stats(self) -> Dict:
    """获取已导入数据的统计信息（从metadata读取）"""

    # 1. 直接读取subject_metadata.json文件
    metadata_file = self.clinical_dir / 'subject_metadata.json'

    with open(metadata_file, 'r', encoding='utf-8') as f:
        all_metadata = json.load(f)

    # 2. 统计V1和V2数据
    v1_stats = {"control": 0, "mci": 0, "ad": 0, "total": 0}
    v2_stats = {"control": 0, "mci": 0, "ad": 0, "total": 0}

    for subject_id, metadata in all_metadata.items():
        data_version = metadata.get("data_version", "")
        group = metadata.get("group", "")

        if data_version == "v1":
            if group in v1_stats:
                v1_stats[group] += 1
            v1_stats["total"] += 1
        elif data_version == "v2":
            if group in v2_stats:
                v2_stats[group] += 1
            v2_stats["total"] += 1

    # 3. 返回统计结果
    return {
        "v1_data": v1_stats,
        "v2_data": v2_stats,
        "summary": {
            "total_subjects": v1_stats["total"] + v2_stats["total"],
            "v1_count": v1_stats["total"],
            "v2_count": v2_stats["total"]
        }
    }
```

---

## 📊 API对比 / API Comparison

### `/scan-all` vs `/imported-stats`

| 特性 | `/scan-all` | `/imported-stats` |
|------|------------|-------------------|
| **用途** | 扫描原始数据源 | 读取已导入数据统计 |
| **数据来源** | 原始目录(`data/*_raw/`, `eye_tracking_data/`) | metadata文件(`subject_metadata.json`) |
| **统计内容** | 可导入的受试者 | 已导入的受试者 |
| **使用场景** | 导入前预览 | 查看已导入数据 |
| **响应速度** | 较慢（需要扫描目录） | 快速（只读JSON文件） |
| **数据准确性** | 可能与已导入不一致 | 100%准确（真实数据） |

### 推荐使用

**导入前预览**:
```javascript
// 扫描可导入的数据
const response = await fetch('/api/m00/scan-all');
const data = await response.json();
```

**查看已导入数据**:
```javascript
// 获取已导入数据的统计
const response = await fetch('/api/m00/imported-stats');
const data = await response.json();
```

---

## 🎯 前端集成 / Frontend Integration

### 建议的UI展示

**数据概览页面**:
```jsx
// 使用imported-stats显示已导入数据
const ImportedDataOverview = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('/api/m00/imported-stats')
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);

  if (!stats) return <Loading />;

  return (
    <Card title="已导入数据统计">
      <Row>
        <Col span={8}>
          <Statistic
            title="V1数据"
            value={stats.v1_data.total}
            suffix={`/ ${stats.summary.v1_count}`}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="V2数据"
            value={stats.v2_data.total}
            suffix={`/ ${stats.summary.v2_count}`}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="总受试者"
            value={stats.summary.total_subjects}
          />
        </Col>
      </Row>
    </Card>
  );
};
```

**数据导入页面**:
```jsx
// 使用scan-all显示可导入数据
const DataImportPreview = () => {
  const [scanResult, setScanResult] = useState(null);

  const handleScan = async () => {
    const response = await fetch('/api/m00/scan-all');
    const data = await response.json();
    setScanResult(data);
  };

  return (
    <Card title="扫描数据源">
      <Button onClick={handleScan}>扫描可导入数据</Button>
      {scanResult && (
        <Descriptions>
          <Descriptions.Item label="Legacy V1">
            {scanResult.legacy_data.total_subjects}
          </Descriptions.Item>
          <Descriptions.Item label="Eye Tracking V2">
            {scanResult.eye_tracking_data.total_subjects}
          </Descriptions.Item>
        </Descriptions>
      )}
    </Card>
  );
};
```

---

## ✅ 验证结果 / Verification Results

### API测试结果

**测试命令**:
```bash
curl http://127.0.0.1:9090/api/m00/imported-stats
```

**响应数据** (2025-10-07):
```json
{
    "success": true,
    "v1_data": {
        "control": 20,
        "mci": 20,
        "ad": 20,
        "total": 60
    },
    "v2_data": {
        "control": 77,
        "mci": 8,
        "ad": 8,
        "total": 93
    },
    "summary": {
        "total_subjects": 153,
        "v1_count": 60,
        "v2_count": 93
    }
}
```

### 数据验证

✅ **V1数据**: 60个受试者
  - Control: 20 ✅
  - MCI: 20 ✅
  - AD: 20 ✅

✅ **V2数据**: 93个受试者
  - Control: 77 ✅
  - MCI: 8 ✅
  - AD: 8 ✅

✅ **总计**: 153个受试者 ✅

---

## 📝 重要提醒 / Important Notes

### 数据规范

1. **V1永远是60个受试者** (Control 20 + MCI 20 + AD 20)
2. **V2有93个受试者** (Control 77 + MCI 8 + AD 8)
3. **总受试者数: 153**

### API使用建议

1. **数据概览/仪表板**:
   - 使用 `/imported-stats` 显示已导入数据
   - 提供准确的数据统计

2. **数据导入页面**:
   - 使用 `/scan-all` 扫描可导入数据
   - 导入前预览数据源

3. **数据验证**:
   - 导入后使用 `/imported-stats` 验证
   - 确保导入成功

---

## 🔄 后续优化 / Future Improvements

### 计划中的功能

1. **实时数据同步**:
   - WebSocket支持，实时更新统计数据
   - 导入过程中的进度推送

2. **缓存机制**:
   - 对 `/imported-stats` 添加缓存
   - 减少重复读取metadata文件

3. **详细统计**:
   - 任务完整性统计
   - MMSE数据覆盖率
   - 数据质量指标

---

## 🎯 总结 / Summary

### 优化成果

✅ **新增API端点** `/imported-stats`
✅ **解决数据统计不准确问题**
✅ **区分"扫描"和"已导入"概念**
✅ **提供准确的数据统计**

### 架构符合性

✅ **符合模块化设计** - 所有修改在Module00内
✅ **符合RESTful规范** - API设计清晰
✅ **符合配置驱动原则** - 使用标准路径配置
✅ **符合数据准确性要求** - 直接读取真实数据

---

**文档作者 / Author**: AI Code Assistant
**最后更新 / Last Updated**: 2025-10-07
**审核状态 / Review Status**: ✅ **已完成 / COMPLETED**
