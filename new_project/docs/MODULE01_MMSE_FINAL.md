# Module01 MMSE数据集成方案（最终版）
# Module01 MMSE Data Integration - Final Version

**文档版本：** v2.0 - 最终优化版
**创建日期：** 2025-10-02
**最后更新：** 2025-10-02
**状态：** 📋 待用户确认

---

## 📊 MMSE数据现状分析（修正版）

### 实际数据情况

**Legacy数据 (v1) - 60/65人有MMSE：**
- ✅ 控制组：20/22人有MMSE (n01-n20)，**缺失2人 (n21-n22)**
- ✅ MCI组：20/22人有MMSE (M01-M20)，**缺失2人 (M21-M22)**
- ✅ AD组：20/21人有MMSE (ad01-ad20)，**缺失1人 (ad21)**
- **总计：60人有MMSE，5人缺失MMSE**

**Eye Tracking数据 (v2) - 待确认：**
- 🔍 需要确认v2数据是否有MMSE评分
- 🔍 如有，需要定义导入格式

### 数据存储位置

```
老项目/data/MMSE_Score/
├── 控制组.csv          (20人: n01-n20 + 统计行)
├── 轻度认知障碍组.csv   (20人: M01-M20 + 统计行)
└── 阿尔兹海默症组.csv   (20人: ad01-ad20 + 统计行)
```

---

## 🎯 核心问题：MMSE管理功能应该放在哪个模块？

### 方案对比分析

#### 方案1：放在Module00 - 数据管理中心 ⭐ **推荐**

**理由：**
1. ✅ **职责清晰** - Module00负责所有数据的导入和管理，MMSE属于临床数据
2. ✅ **统一管理** - 眼动数据、ROI配置、MMSE评分统一在Module00管理
3. ✅ **数据完整性** - 导入受试者时就应该关联MMSE，保证数据完整性
4. ✅ **可追溯性** - 在`subject_metadata.json`中记录MMSE来源和导入时间
5. ✅ **避免耦合** - Module01只负责可视化，不涉及数据管理

**功能设计：**
- 📁 MMSE数据导入（Excel/CSV上传）
- 📝 MMSE数据录入（手动填写表单）
- 📊 MMSE数据查看和编辑
- 🔗 自动关联到受试者metadata

**优点：**
- 符合模块职责划分原则
- 便于后续扩展其他临床数据（年龄、性别、病史等）
- Module01保持纯粹的可视化功能

**缺点：**
- Module00功能会变得更丰富（但这是合理的）

---

#### 方案2：放在Module01 - 数据可视化

**理由：**
- Module01需要展示MMSE评分
- 可视化时顺便录入MMSE

**缺点：**
- ❌ 职责不清 - Module01应专注可视化，不应管理数据
- ❌ 数据分散 - MMSE数据管理和眼动数据管理分离
- ❌ 逻辑混乱 - 用户可能期望在数据管理模块修改MMSE

---

#### 方案3：创建新模块 - Module0X: 临床数据管理

**理由：**
- 专门管理临床数据（MMSE、人口统计学信息等）

**缺点：**
- ❌ 过度设计 - 当前只有MMSE一种临床数据，单独模块过于复杂
- ❌ 分散注意力 - Module00已经是数据管理中心，再分一个模块容易混淆

---

### 🏆 最终推荐：**方案1 - 扩展Module00**

将MMSE管理功能整合到Module00数据管理中心，具体设计如下：

---

## 🔧 Module00 MMSE功能设计

### 1. 功能模块结构

```
Module00 - 数据管理中心
├── 眼动数据管理
│   ├── 数据扫描
│   ├── 数据导入
│   └── 受试者列表
└── MMSE数据管理（新增）⭐
    ├── MMSE批量导入（Excel/CSV）
    ├── MMSE单条录入（表单）
    ├── MMSE查看和编辑
    └── MMSE缺失统计
```

### 2. 后端架构设计

#### 新增文件结构

```
src/web/modules/module00_data_management/
├── api.py                      # 现有
├── service.py                  # 现有
├── mmse/                       # 新增MMSE子模块 ⭐
│   ├── __init__.py
│   ├── mmse_loader.py         # MMSE读取器
│   ├── mmse_importer.py       # MMSE导入器
│   ├── mmse_validator.py      # MMSE验证器
│   └── mmse_storage.py        # MMSE存储管理
└── importers/                  # 现有
    ├── legacy_importer.py
    └── eye_tracking_importer.py
```

#### 新增API端点

```python
# Module00 扩展API

# 1. 获取MMSE数据
GET /api/m00/mmse/{subject_id}
Response:
{
  "success": true,
  "data": {
    "subject_id": "control_legacy_1",
    "has_mmse": true,
    "mmse_scores": {...},
    "source": "legacy_csv",  // legacy_csv | manual_input | excel_import
    "last_updated": "2025-10-02T10:00:00"
  }
}

# 2. 批量导入MMSE（Excel/CSV）
POST /api/m00/mmse/import
Request:
{
  "file": <multipart file>,
  "group": "control",  // control | mci | ad
  "overwrite": false
}
Response:
{
  "success": true,
  "imported_count": 15,
  "updated_count": 3,
  "errors": []
}

# 3. 单条录入MMSE
POST /api/m00/mmse/{subject_id}
Request:
{
  "q1_time_orientation": {...},
  "q2_place_orientation": {...},
  "q3_immediate_memory": 3,
  "q4_attention": {...},
  "q5_recall": {...},
  "total_score": 28
}

# 4. 更新MMSE
PUT /api/m00/mmse/{subject_id}

# 5. 删除MMSE
DELETE /api/m00/mmse/{subject_id}

# 6. 获取MMSE缺失列表
GET /api/m00/mmse/missing
Response:
{
  "success": true,
  "missing": [
    {"subject_id": "control_legacy_21", "group": "control"},
    {"subject_id": "control_legacy_22", "group": "control"},
    ...
  ],
  "total_missing": 5,
  "total_subjects": 138
}
```

### 3. 数据存储设计

#### MMSE数据存储位置

```
new_project/data/01_raw/clinical/
├── subject_metadata.json       # 现有 - 受试者元数据
├── import_history.json         # 现有 - 导入历史
└── mmse_scores.json           # 新增 - MMSE评分存储 ⭐
```

#### mmse_scores.json结构

```json
{
  "control_legacy_1": {
    "subject_id": "control_legacy_1",
    "group": "control",
    "q1_time_orientation": {
      "year": 1,
      "season": 1,
      "month": 1,
      "weekday": 2,
      "subtotal": 5
    },
    "q2_place_orientation": {
      "province": 2,
      "street": 1,
      "building": 1,
      "floor": 1,
      "subtotal": 5
    },
    "q3_immediate_memory": 3,
    "q4_attention": {
      "step1": 1,
      "step2": 1,
      "step3": 1,
      "step4": 1,
      "step5": 1,
      "subtotal": 5
    },
    "q5_recall": {
      "word1": 1,
      "word2": 1,
      "word3": 1,
      "subtotal": 3
    },
    "total_score": 21,
    "source": "legacy_csv",           // 数据来源
    "import_date": "2025-10-02T01:07:50.655133",
    "last_updated": "2025-10-02T10:00:00",
    "updated_by": "admin"
  },
  "control_legacy_21": null,  // 无MMSE数据
  "mci_eyetrack_s005": {
    "subject_id": "mci_eyetrack_s005",
    "group": "mci",
    "q1_time_orientation": {...},
    ...
    "total_score": 26,
    "source": "manual_input",         // 手动录入
    "import_date": "2025-10-02T11:00:00",
    "last_updated": "2025-10-02T11:00:00",
    "updated_by": "admin"
  }
}
```

### 4. 前端功能设计

#### Module00页面新增Tab

```jsx
<Tabs>
  <TabPane tab="眼动数据管理" key="eyetracking">
    <DataScanner />
    <DataImporter />
    <SubjectList />
  </TabPane>

  <TabPane tab="MMSE数据管理" key="mmse">  {/* 新增 ⭐ */}
    <MMSEDataOverview />      {/* MMSE统计概览 */}
    <MMSEBatchImport />       {/* 批量导入 */}
    <MMSEManualEntry />       {/* 手动录入 */}
    <MMSEMissingList />       {/* 缺失列表 */}
  </TabPane>
</Tabs>
```

#### 新增组件设计

**1. MMSEDataOverview - MMSE统计概览**

```jsx
const MMSEDataOverview = () => {
  return (
    <Card title="MMSE数据概览">
      <Row gutter={16}>
        <Col span={6}>
          <Statistic title="总受试者数" value={138} />
        </Col>
        <Col span={6}>
          <Statistic
            title="有MMSE评分"
            value={133}
            valueStyle={{ color: '#3f8600' }}
            suffix="/ 138"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="缺失MMSE"
            value={5}
            valueStyle={{ color: '#cf1322' }}
          />
        </Col>
        <Col span={6}>
          <Statistic title="完整率" value="96.4%" precision={1} />
        </Col>
      </Row>

      {/* 按组别统计 */}
      <Table
        dataSource={[
          { group: 'Control', total: 54, has_mmse: 52, missing: 2 },
          { group: 'MCI', total: 42, has_mmse: 40, missing: 2 },
          { group: 'AD', total: 42, has_mmse: 41, missing: 1 }
        ]}
        columns={[...]}
      />
    </Card>
  );
};
```

**2. MMSEBatchImport - 批量导入**

```jsx
const MMSEBatchImport = () => {
  const [fileList, setFileList] = useState([]);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', fileList[0]);
    formData.append('group', selectedGroup);

    const response = await axios.post('/api/m00/mmse/import', formData);
    // ...
  };

  return (
    <Card title="MMSE批量导入">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert
          message="支持的文件格式"
          description={
            <div>
              <p>✅ Excel文件（.xlsx, .xls）</p>
              <p>✅ CSV文件（.csv，UTF-8编码）</p>
              <p>📋 <a href="/templates/mmse_template.xlsx">下载MMSE导入模板</a></p>
            </div>
          }
          type="info"
        />

        <Select placeholder="选择组别" onChange={setSelectedGroup}>
          <Option value="control">控制组</Option>
          <Option value="mci">MCI组</Option>
          <Option value="ad">AD组</Option>
        </Select>

        <Upload.Dragger
          fileList={fileList}
          beforeUpload={(file) => {
            setFileList([file]);
            return false;
          }}
          accept=".xlsx,.xls,.csv"
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        </Upload.Dragger>

        <Button
          type="primary"
          onClick={handleUpload}
          disabled={!fileList.length}
        >
          开始导入
        </Button>
      </Space>
    </Card>
  );
};
```

**3. MMSEManualEntry - 手动录入**

```jsx
const MMSEManualEntry = () => {
  const [form] = Form.useForm();

  return (
    <Card title="MMSE手动录入">
      <Form form={form} onFinish={handleSubmit}>
        <Form.Item label="受试者ID" name="subject_id" required>
          <Select placeholder="选择受试者">
            {missingSubjects.map(s => (
              <Option key={s.id} value={s.id}>
                {s.id} ({s.group})
              </Option>
            ))}
          </Select>
        </Form.Item>

        {/* Q1: 时间定向 */}
        <Card title="Q1: 时间定向 (满分4分)" size="small">
          <Form.Item label="年份" name={['q1', 'year']}>
            <Radio.Group>
              <Radio value={1}>正确 (1分)</Radio>
              <Radio value={0}>错误 (0分)</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item label="季节" name={['q1', 'season']}>
            <Radio.Group>
              <Radio value={1}>正确 (1分)</Radio>
              <Radio value={0}>错误 (0分)</Radio>
            </Radio.Group>
          </Form.Item>
          {/* 月份、星期 */}
        </Card>

        {/* Q2-Q5类似 */}

        <Form.Item>
          <Button type="primary" htmlType="submit">提交MMSE评分</Button>
        </Form.Item>
      </Form>
    </Card>
  );
};
```

**4. MMSEMissingList - 缺失列表**

```jsx
const MMSEMissingList = () => {
  return (
    <Card title="MMSE缺失列表">
      <Table
        dataSource={missingSubjects}
        columns={[
          { title: '受试者ID', dataIndex: 'subject_id' },
          { title: '组别', dataIndex: 'group' },
          { title: '数据版本', dataIndex: 'data_version' },
          {
            title: '操作',
            render: (_, record) => (
              <Space>
                <Button onClick={() => openEntryForm(record)}>
                  录入MMSE
                </Button>
                <Button onClick={() => openImportDialog(record)}>
                  上传文件
                </Button>
              </Space>
            )
          }
        ]}
      />
    </Card>
  );
};
```

---

## 📄 MMSE导入文件格式规范

### Excel/CSV模板格式

#### 控制组模板 (control_mmse_template.xlsx)

| 受试者 | 年份 | 季节 | 月份 | 星期 | 省市区 | 街道 | 建筑 | 楼层 | 即刻记忆 | 100-7 | 93-7 | 86-7 | 79-7 | 72-7 | 词1 | 词2 | 词3 | 总分 |
|--------|------|------|------|------|--------|------|------|------|----------|-------|------|------|------|------|-----|-----|-----|------|
| control_legacy_21 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 21 |
| control_legacy_22 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 20 |

**字段说明：**
- **受试者**：必须与系统中的subject_id完全一致
- **评分字段**：所有字段只能填0或1（省市区可以填0-2）
- **总分**：系统会自动验证总分是否正确（可不填，自动计算）

#### Eye Tracking数据模板 (eyetracking_mmse_template.xlsx)

**支持两种格式：**

**格式1：完整格式（与Legacy相同）**
```
受试者,年份,季节,月份,星期,省市区,街道,建筑,楼层,即刻记忆,100-7,93-7,86-7,79-7,72-7,词1,词2,词3,总分
mci_eyetrack_s001,1,1,1,2,2,1,1,1,3,1,1,1,0,0,1,0,0,18
```

**格式2：简化格式（仅总分）**
```
受试者,总分
mci_eyetrack_s001,18
```

**注意事项：**
1. ✅ 受试者ID必须完全匹配系统中的ID
2. ✅ 支持UTF-8和GBK编码
3. ✅ 第一行必须是表头
4. ✅ 可包含空行（自动跳过）
5. ⚠️ 总分必须在0-30之间
6. ⚠️ 重复导入时需要选择"覆盖"或"跳过"策略

---

## 🔄 Module01如何使用MMSE数据

### 职责分工

**Module00职责：**
- ✅ MMSE数据的导入、录入、编辑、删除
- ✅ 维护 `mmse_scores.json`
- ✅ 在 `subject_metadata.json` 中标记 `has_mmse`

**Module01职责：**
- ✅ 从Module00读取MMSE数据（只读）
- ✅ 在可视化界面显示MMSE评分
- ✅ 根据MMSE分数过滤受试者
- ❌ 不负责MMSE数据的修改

### Module01读取MMSE的方式

```python
# Module01 Service

class DataVisualizationService:
    def __init__(self):
        # 读取Module00维护的MMSE数据
        self.mmse_data = self._load_mmse_from_module00()

    def _load_mmse_from_module00(self):
        """从Module00的mmse_scores.json读取MMSE数据"""
        mmse_file = self.data_root / "01_raw" / "clinical" / "mmse_scores.json"
        if mmse_file.exists():
            with open(mmse_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_mmse_score(self, subject_id: str):
        """获取MMSE评分（只读）"""
        return self.mmse_data.get(subject_id)
```

---

## ✅ 任务清单更新

### Module00新增任务（MMSE管理功能）

#### Phase 0: MMSE基础架构（优先级P0）

**Task 0.1: 创建MMSE子模块结构**
- 工作量：0.5小时
- 创建 `mmse/` 目录和基础文件

**Task 0.2: 实现MMSELoader（读取Legacy MMSE）**
- 工作量：1小时
- 读取老项目的MMSE CSV文件
- ID映射 (n01→control_legacy_1)
- 转换为标准JSON格式
- 保存到 `mmse_scores.json`

**Task 0.3: 实现MMSEStorage（MMSE存储管理）**
- 工作量：1小时
- 创建/读取/更新/删除MMSE数据
- 维护 `mmse_scores.json`
- 同步更新 `subject_metadata.json` 的 `has_mmse` 字段

#### Phase 1: MMSE导入功能（优先级P1）

**Task 1.1: 实现MMSEImporter（批量导入）**
- 工作量：2小时
- 支持Excel/CSV文件解析
- 数据验证（字段范围、总分校验）
- 批量写入 `mmse_scores.json`

**Task 1.2: 实现MMSEValidator（数据验证）**
- 工作量：1小时
- 验证subject_id存在性
- 验证评分范围（0-1，省市区0-2）
- 验证总分计算正确性

**Task 1.3: API端点实现**
- 工作量：1.5小时
- GET /api/m00/mmse/{subject_id}
- POST /api/m00/mmse/import
- POST /api/m00/mmse/{subject_id}
- PUT /api/m00/mmse/{subject_id}
- GET /api/m00/mmse/missing

#### Phase 2: MMSE前端功能（优先级P1）

**Task 2.1: MMSEDataOverview组件**
- 工作量：1小时
- 统计概览卡片
- 按组别统计表格

**Task 2.2: MMSEBatchImport组件**
- 工作量：1.5小时
- 文件上传界面
- 导入进度显示
- 错误提示

**Task 2.3: MMSEManualEntry组件**
- 工作量：2小时
- MMSE评分表单（Q1-Q5）
- 实时总分计算
- 提交验证

**Task 2.4: MMSEMissingList组件**
- 工作量：0.5小时
- 缺失列表表格
- 快捷录入入口

#### Phase 3: 集成测试（优先级P0）

**Task 3.1: MMSE功能测试**
- 工作量：1.5小时
- 测试Legacy MMSE读取
- 测试批量导入
- 测试手动录入
- 测试数据验证

---

### Module01任务调整

**原Task 1.4: 创建MMSE加载器** - ❌ 删除
- 改为：从Module00读取MMSE数据

**原Task 1.5: 集成MMSE到Service** - ✅ 简化
- 工作量：从0.5h降低到0.2h
- 仅读取Module00的 `mmse_scores.json`

---

## 📊 工作量汇总

### Module00 MMSE功能开发

| 阶段 | 任务数 | 工作量 | 优先级 |
|------|--------|--------|--------|
| Phase 0: 基础架构 | 3项 | 2.5h | P0 |
| Phase 1: 导入功能 | 3项 | 4.5h | P1 |
| Phase 2: 前端界面 | 4项 | 5h | P1 |
| Phase 3: 测试 | 1项 | 1.5h | P0 |
| **总计** | **11项** | **13.5h** | - |

### Module01数据可视化开发（调整后）

| 阶段 | 任务数 | 原工时 | 新工时 | 变化 |
|------|--------|--------|--------|------|
| P0核心 | 4项 | 7h | 5.2h | -1.8h ⬇️ |
| P1增强 | 6项 | 4h | 4h | - |
| P2优化 | 4项 | 3.5h | 3.5h | - |
| **总计** | **14项** | **14.5h** | **12.7h** | **-1.8h** |

### 总体工作量

| 模块 | 工作量 | 交付时间 |
|------|--------|----------|
| Module00 MMSE功能 | 13.5h | 2天 |
| Module01 数据可视化 | 12.7h | 2天 |
| **总计** | **26.2h** | **约3-4个工作日**（可并行开发）|

---

## 📝 开发优先级建议

### 阶段1：Module01核心功能（优先）⭐

**目标：** 让Module01能正确读取Module00导入的真实数据

**任务：**
1. Module01 Task 1.1-1.3（数据对接）- 3.5h
2. Module00 Task 0.2（读取Legacy MMSE）- 1h
3. Module00 Task 0.3（MMSE存储）- 1h
4. Module01 Task 5.1（Backend测试）- 1.5h

**总计：** 7小时（1个工作日）

**交付成果：**
- ✅ Module01能读取真实眼动数据
- ✅ Module01能显示60个Legacy受试者的MMSE评分
- ✅ 5个缺失MMSE的受试者显示"无MMSE"状态

---

### 阶段2：Module00 MMSE管理（次优先）

**目标：** 补充缺失的5个MMSE评分

**任务：**
1. Module00 Phase 1（导入功能）- 4.5h
2. Module00 Phase 2（前端界面）- 5h
3. Module00 Phase 3（测试）- 1.5h

**总计：** 11小时（1.5个工作日）

**交付成果：**
- ✅ 可批量导入Eye Tracking MMSE数据
- ✅ 可手动录入缺失的5个Legacy MMSE
- ✅ MMSE完整率从60/65提升到65/65（v1）

---

### 阶段3：Module01功能增强（最后）

**目标：** 完善Module01的用户体验

**任务：**
1. Module01 P1增强 - 4h
2. Module01 P2优化 - 3.5h

**总计：** 7.5小时（1个工作日）

**交付成果：**
- ✅ 显示v1/v2数据版本徽章
- ✅ 显示受试者详细信息
- ✅ 数据版本过滤器
- ✅ i18n三语支持

---

## 🎯 最终方案总结

### 核心决策

1. **MMSE管理功能放在Module00** ⭐
   - Module00负责所有数据管理（眼动+MMSE）
   - Module01只负责数据可视化（只读MMSE）

2. **数据存储位置**
   - MMSE统一存储在：`data/01_raw/clinical/mmse_scores.json`
   - Legacy MMSE：从老项目CSV迁移过来
   - Eye Tracking MMSE：通过批量导入或手动录入

3. **开发优先级**
   - 第一阶段：Module01数据对接（让可视化能用）
   - 第二阶段：Module00 MMSE管理（补充缺失数据）
   - 第三阶段：Module01功能增强（优化体验）

### 关键文件

**Backend:**
- `src/web/modules/module00_data_management/mmse/mmse_loader.py`
- `src/web/modules/module00_data_management/mmse/mmse_storage.py`
- `src/web/modules/module00_data_management/mmse/mmse_importer.py`
- `data/01_raw/clinical/mmse_scores.json`

**Frontend:**
- `frontend/src/pages/Module00/components/MMSEDataOverview.jsx`
- `frontend/src/pages/Module00/components/MMSEBatchImport.jsx`
- `frontend/src/pages/Module00/components/MMSEManualEntry.jsx`
- `frontend/templates/mmse_template.xlsx`

---

## ⚠️ 重要注意事项

### 1. 数据一致性

- ✅ `mmse_scores.json` 是MMSE的唯一数据源
- ✅ 所有模块读取MMSE都从此文件读取
- ✅ 只有Module00能修改此文件

### 2. subject_id映射

- ✅ 必须维护准确的ID映射表
- ✅ 导入时验证subject_id存在性
- ⚠️ Legacy: n{N} → {group}_legacy_{N}
- ⚠️ Eye Tracking: 需要定义映射规则

### 3. 数据验证

- ✅ 每个字段只能是0或1（省市区0-2）
- ✅ 总分必须等于各项之和
- ✅ 总分范围0-30

### 4. 错误处理

- ✅ 导入时遇到无效ID → 跳过并记录错误
- ✅ 评分超出范围 → 拒绝并提示
- ✅ 文件格式错误 → 详细错误提示

---

## 📚 相关文档

- [Module00开发文档](./MODULE00_DEVELOPMENT_LOG.md)
- [Module01开发规划](./MODULE01_DEVELOPMENT_PLAN.md)
- [Frontend编码规范](./FRONTEND_CODING_STANDARDS.md)
- [Backend编码规范](./BACKEND_CODING_STANDARDS.md)

---

**文档状态：** ✅ 最终优化版，待用户确认
**核心建议：** MMSE管理功能放在Module00，Module01只负责可视化
**预计总工时：** 26.2小时（约3-4个工作日）

---

**下一步行动：**
1. ✅ 用户确认MMSE功能放在Module00
2. ✅ 用户确认Eye Tracking MMSE导入格式
3. ✅ 开始实施阶段1：Module01数据对接
4. ✅ 实施阶段2：Module00 MMSE管理
5. ✅ 实施阶段3：Module01功能增强
