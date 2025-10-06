# Module02 V2数据管理优化方案

## 📋 需求概述

### 核心需求
1. **受试者筛选功能** - 按数据版本（v1/v2/全部）筛选
2. **V1数据管理** - 新增V1数据导入和管理功能
3. **V2受试者ID规范化** - 批量导入后自动重命名为标准格式
4. **MMSE模板自动填充** - 下载模板时包含已有的V2受试者信息
5. **MMSE录入优化** - 简化录入流程，自动计算总分，补充人口学信息
6. **列表字段扩充** - 增加年龄、受教育程度显示

---

## 🎯 优化方案设计

### 1. 受试者筛选功能

#### 1.1 前端设计

**位置**: `SubjectManagement.jsx` 顶部筛选区

**UI组件**:
```jsx
<Select
  value={dataVersionFilter}
  onChange={setDataVersionFilter}
  style={{ width: 200 }}
>
  <Option value="all">全部受试者</Option>
  <Option value="v1">仅V1受试者</Option>
  <Option value="v2">仅V2受试者</Option>
</Select>
```

**筛选逻辑**:
```javascript
const filteredSubjects = subjects.filter(subject => {
  // 版本筛选
  if (dataVersionFilter === 'v1' && subject.data_version !== 'v1') return false;
  if (dataVersionFilter === 'v2' && subject.data_version !== 'v2') return false;

  // 组别筛选
  if (groupFilter !== 'all' && subject.group !== groupFilter) return false;

  return true;
});
```

#### 1.2 后端支持

**API**: `GET /api/m02/subjects?data_version=v1|v2|all`

**修改文件**: `src/modules/module02_preprocessing/subject_manager.py`

```python
def get_all_subjects(
    self,
    group: Optional[str] = None,
    with_mmse: bool = False,
    data_version: Optional[str] = None  # 新增参数
) -> List[Dict]:
    """
    获取所有受试者

    Args:
        data_version: 'v1', 'v2', 或 None(全部)
    """
    subjects = []
    # ... 现有逻辑 ...

    # 版本过滤
    if data_version:
        subjects = [s for s in subjects if s.get('data_version') == data_version]

    return subjects
```

---

### 2. V1数据管理功能

#### 2.1 架构设计

**模块结构**:
```
src/modules/module02_preprocessing/
├── v1_data_manager.py          # 新增: V1数据管理器
├── v2_data_manager.py          # 现有: V2数据管理器
└── subject_manager.py          # 统一受试者管理
```

**职责划分**:
- `v1_data_manager.py`: 处理V1格式数据导入、扫描
- `v2_data_manager.py`: 处理V2格式数据导入、扫描、ID规范化
- `subject_manager.py`: 统一管理所有受试者，不关心数据来源

#### 2.2 V1数据管理器实现

**文件**: `src/modules/module02_preprocessing/v1_data_manager.py`

```python
class V1DataManager:
    """V1格式眼动数据管理器"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.v1_scan_dir = data_dir / 'v1_raw_data'  # V1原始数据目录

    def scan_v1_subjects(self) -> List[Dict]:
        """
        扫描V1目录下的受试者数据

        V1目录结构示例:
        v1_raw_data/
        ├── control/
        │   ├── control_001/
        │   │   └── task_data.txt
        │   └── control_002/
        └── mci/
            └── mci_001/

        Returns:
            [
                {
                    'subject_id': 'control_001',
                    'group': 'control',
                    'name': '',
                    'hospital_id': '',
                    'timestamp': '2024-01-01',
                    'data_version': 'v1',
                    'file_count': 5
                },
                ...
            ]
        """
        v1_subjects = []

        for group in ['control', 'mci', 'ad']:
            group_dir = self.v1_scan_dir / group
            if not group_dir.exists():
                continue

            for subject_dir in group_dir.iterdir():
                if not subject_dir.is_dir():
                    continue

                subject_id = subject_dir.name

                # 统计数据文件
                data_files = list(subject_dir.glob('*.txt')) + \
                             list(subject_dir.glob('*.csv'))

                v1_subjects.append({
                    'subject_id': subject_id,
                    'group': group,
                    'name': '',  # V1通常没有姓名
                    'hospital_id': '',
                    'timestamp': self._get_earliest_file_time(data_files),
                    'data_version': 'v1',
                    'file_count': len(data_files),
                    'status': 'available'
                })

        return v1_subjects

    def import_v1_subject(
        self,
        subject_id: str,
        demographics: Dict,
        subject_manager: 'SubjectManager'
    ) -> Dict:
        """
        导入V1受试者到subject_manager

        Args:
            subject_id: V1受试者ID
            demographics: 人口学信息 {'age': 65, 'gender': 'male', ...}
            subject_manager: SubjectManager实例

        Returns:
            创建的受试者信息
        """
        # 从扫描结果获取V1受试者
        v1_subjects = self.scan_v1_subjects()
        v1_subject = next((s for s in v1_subjects if s['subject_id'] == subject_id), None)

        if not v1_subject:
            raise ValueError(f"V1受试者不存在: {subject_id}")

        # 创建受试者记录
        subject = subject_manager.create_subject(
            subject_id=subject_id,
            group=v1_subject['group'],
            demographics=demographics,
            mmse=None,  # V1初始无MMSE
            data_version='v1'
        )

        return subject
```

#### 2.3 前端V1数据管理组件

**文件**: `frontend/src/pages/Module02/V1DataManagement.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message } from 'antd';
import { getV1Subjects, importV1Subject } from '@/services/module02Service';

const V1DataManagement = () => {
  const [v1Subjects, setV1Subjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState(null);

  const columns = [
    { title: '受试者ID', dataIndex: 'subject_id', key: 'subject_id' },
    { title: '分组', dataIndex: 'group', key: 'group' },
    { title: '时间戳', dataIndex: 'timestamp', key: 'timestamp' },
    { title: '文件数量', dataIndex: 'file_count', key: 'file_count' },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status) => status === 'imported' ? '已导入' : '待导入'
    },
    { title: '操作', key: 'action',
      render: (_, record) => (
        <Button
          type="primary"
          size="small"
          disabled={record.status === 'imported'}
          onClick={() => handleImport(record)}
        >
          导入
        </Button>
      )
    }
  ];

  const handleImport = (subject) => {
    setSelectedSubject(subject);
    setImportModalVisible(true);
  };

  const handleImportSubmit = async (values) => {
    try {
      await importV1Subject(selectedSubject.subject_id, values);
      message.success('导入成功');
      setImportModalVisible(false);
      loadV1Subjects();
    } catch (error) {
      message.error('导入失败: ' + error.message);
    }
  };

  return (
    <div>
      <h3>V1数据管理</h3>
      <Table
        columns={columns}
        dataSource={v1Subjects}
        loading={loading}
        rowKey="subject_id"
      />

      <Modal
        title="导入V1受试者"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={null}
      >
        <Form onFinish={handleImportSubmit}>
          <Form.Item label="受试者ID" name="subject_id"
            initialValue={selectedSubject?.subject_id}>
            <Input disabled />
          </Form.Item>
          <Form.Item label="年龄" name="age" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item label="性别" name="gender" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="male">男</Select.Option>
              <Select.Option value="female">女</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="受教育程度" name="education_level" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="primary">小学</Select.Option>
              <Select.Option value="junior_high">初中</Select.Option>
              <Select.Option value="senior_high">高中</Select.Option>
              <Select.Option value="undergraduate">本科</Select.Option>
              <Select.Option value="postgraduate">研究生</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">确定导入</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default V1DataManagement;
```

---

### 3. V2受试者ID规范化

#### 3.1 ID命名规范

**格式**: `v2_{group}_{序号}`

**示例**:
- `v2_control_001`
- `v2_mci_002`
- `v2_ad_003`

**序号规则**:
1. **按组别独立编号**: control、mci、ad 各自从001开始
2. **避免冲突**: 查找当前组别最大序号+1
3. **补零对齐**: 使用3位数字（001-999）

#### 3.2 ID规范化逻辑

**文件**: `src/modules/module02_preprocessing/v2_data_manager.py`

```python
class V2DataManager:
    """V2格式眼动数据管理器"""

    def __init__(self, data_dir: Path, subject_manager: 'SubjectManager'):
        self.data_dir = data_dir
        self.subject_manager = subject_manager

    def normalize_v2_subject_ids(self, v2_subjects: List[Dict]) -> Dict[str, str]:
        """
        为V2受试者生成规范ID

        Args:
            v2_subjects: 扫描到的V2受试者列表

        Returns:
            ID映射字典 {旧ID: 新ID}
            例: {'N_01': 'v2_control_001', 'M_03': 'v2_mci_001'}
        """
        # 获取已存在的V2受试者，统计每组最大序号
        existing_subjects = self.subject_manager.get_all_subjects(data_version='v2')

        max_seq = {'control': 0, 'mci': 0, 'ad': 0}

        for subject in existing_subjects:
            # 解析已有ID，提取序号
            # v2_control_005 -> group=control, seq=5
            match = re.match(r'v2_(\w+)_(\d+)', subject['subject_id'])
            if match:
                group, seq = match.groups()
                max_seq[group] = max(max_seq[group], int(seq))

        # 为新导入的V2受试者分配ID
        id_mapping = {}
        group_counters = max_seq.copy()

        for v2_subject in v2_subjects:
            old_id = v2_subject['subject_id']
            group = v2_subject['group']

            # 递增序号
            group_counters[group] += 1
            seq = group_counters[group]

            # 生成新ID
            new_id = f"v2_{group}_{seq:03d}"
            id_mapping[old_id] = new_id

        return id_mapping

    def batch_import_v2_subjects(
        self,
        v2_subjects: List[Dict],
        rename: bool = True
    ) -> Dict:
        """
        批量导入V2受试者

        Args:
            v2_subjects: V2受试者列表
            rename: 是否自动重命名为规范ID

        Returns:
            {
                'imported': 10,
                'failed': 0,
                'id_mapping': {'N_01': 'v2_control_001', ...}
            }
        """
        results = {
            'imported': 0,
            'failed': 0,
            'id_mapping': {},
            'errors': []
        }

        # 生成ID映射
        if rename:
            results['id_mapping'] = self.normalize_v2_subject_ids(v2_subjects)

        # 逐个导入
        for v2_subject in v2_subjects:
            old_id = v2_subject['subject_id']
            new_id = results['id_mapping'].get(old_id, old_id)

            try:
                self.subject_manager.create_subject(
                    subject_id=new_id,
                    group=v2_subject['group'],
                    demographics={
                        'name': v2_subject.get('name', ''),
                        'hospital_id': v2_subject.get('hospital_id', ''),
                        'age': None,  # 待补充
                        'gender': None,
                        'education_level': None
                    },
                    mmse=None,
                    data_version='v2',
                    metadata={
                        'original_id': old_id,
                        'timestamp': v2_subject.get('timestamp'),
                        'v2_import_date': datetime.now().isoformat()
                    }
                )
                results['imported'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'subject_id': old_id,
                    'error': str(e)
                })

        return results
```

#### 3.3 前端批量导入UI

**修改**: `frontend/src/pages/Module02/V2DataManagement.jsx`

```jsx
const V2DataManagement = () => {
  const [renameEnabled, setRenameEnabled] = useState(true);  // 新增

  const handleBatchImport = async () => {
    try {
      const selectedSubjects = v2Subjects.filter(s =>
        selectedRowKeys.includes(s.subject_id)
      );

      const result = await batchImportV2Subjects(
        selectedSubjects,
        renameEnabled  // 传递重命名选项
      );

      // 显示ID映射结果
      if (renameEnabled && result.id_mapping) {
        Modal.info({
          title: 'ID重命名映射',
          content: (
            <div>
              <p>已导入 {result.imported} 个受试者</p>
              <Table
                size="small"
                dataSource={Object.entries(result.id_mapping).map(([old, new_]) => ({
                  old_id: old,
                  new_id: new_
                }))}
                columns={[
                  { title: '原ID', dataIndex: 'old_id' },
                  { title: '新ID', dataIndex: 'new_id' }
                ]}
              />
            </div>
          )
        });
      }

      message.success(`成功导入 ${result.imported} 个受试者`);

    } catch (error) {
      message.error('批量导入失败: ' + error.message);
    }
  };

  return (
    <div>
      <Checkbox
        checked={renameEnabled}
        onChange={(e) => setRenameEnabled(e.target.checked)}
      >
        自动规范化受试者ID（推荐）
      </Checkbox>

      <Button onClick={handleBatchImport}>批量导入</Button>

      {/* ... 其他UI ... */}
    </div>
  );
};
```

---

### 4. MMSE模板自动填充

#### 4.1 后端模板生成

**API**: `GET /api/m02/mmse/template?include_v2_data=true`

**修改文件**: `src/modules/module02_preprocessing/mmse_manager.py`

```python
def generate_batch_import_template(
    self,
    include_v2_data: bool = True,
    data_version: str = 'all'  # 'v1', 'v2', 'all'
) -> bytes:
    """
    生成MMSE批量导入模板（包含已有V2受试者信息）

    Args:
        include_v2_data: 是否包含V2受试者的已有信息
        data_version: 包含哪些版本的受试者

    Returns:
        CSV文件内容（bytes）
    """
    import io
    import csv

    # CSV列定义
    columns = [
        'subject_id',      # 受试者ID（不可修改）
        'group',           # 分组
        'name',            # 患者姓名
        'hospital_id',     # 医院ID
        'age',             # 年龄
        'gender',          # 性别
        'education_level', # 受教育程度
        'timestamp',       # 时间戳（不可修改）
        'q1_year', 'q1_season', 'q1_month', 'q1_weekday',
        'q2_province', 'q2_floor',
        'q3_immediate',
        # ... 其他MMSE项目
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()

    if include_v2_data:
        # 获取所有V2受试者（或根据data_version筛选）
        subjects = self.subject_manager.get_all_subjects(data_version=data_version)

        for subject in subjects:
            row = {
                'subject_id': subject['subject_id'],
                'group': subject['group'],
                'name': subject.get('demographics', {}).get('name', ''),
                'hospital_id': subject.get('demographics', {}).get('hospital_id', ''),
                'age': subject.get('demographics', {}).get('age', ''),
                'gender': subject.get('demographics', {}).get('gender', ''),
                'education_level': subject.get('demographics', {}).get('education_level', ''),
                'timestamp': subject.get('metadata', {}).get('timestamp', ''),
            }

            # 如果已有MMSE数据，也填充进去
            if subject.get('mmse'):
                for key, value in subject['mmse'].items():
                    if key in columns:
                        row[key] = value

            writer.writerow(row)
    else:
        # 空模板，只有表头
        pass

    csv_content = output.getvalue()
    return csv_content.encode('utf-8-sig')  # BOM for Excel
```

#### 4.2 批量导入更新逻辑

**修改**: `mmse_manager.py::batch_import_clinical_data()`

```python
def batch_import_clinical_data(self, csv_file_path: Path) -> Dict:
    """
    批量导入MMSE临床数据（支持更新已有受试者）

    导入规则:
    1. subject_id和timestamp不可修改（作为查找依据）
    2. 其他字段可更新（demographics和mmse）
    3. 如果subject_id不存在，报错（必须先导入V2数据）

    Returns:
        {
            'updated': 10,
            'errors': []
        }
    """
    import csv

    results = {'updated': 0, 'created': 0, 'errors': []}

    with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            subject_id = row['subject_id']

            # 检查受试者是否存在
            existing_subject = self.subject_manager.get_subject(subject_id)

            if not existing_subject:
                results['errors'].append({
                    'row': row_num,
                    'subject_id': subject_id,
                    'error': '受试者不存在，请先导入V2数据'
                })
                continue

            try:
                # 准备更新数据
                demographics_update = {}
                if row.get('name'):
                    demographics_update['name'] = row['name']
                if row.get('hospital_id'):
                    demographics_update['hospital_id'] = row['hospital_id']
                if row.get('age'):
                    demographics_update['age'] = int(row['age'])
                if row.get('gender'):
                    demographics_update['gender'] = row['gender']
                if row.get('education_level'):
                    demographics_update['education_level'] = row['education_level']

                # 准备MMSE数据
                mmse_update = {}
                mmse_fields = ['q1_year', 'q1_season', 'q1_month', 'q1_weekday',
                               'q2_province', 'q2_floor', 'q3_immediate']

                for field in mmse_fields:
                    if row.get(field):
                        mmse_update[field] = int(row[field])

                # 计算总分
                if mmse_update:
                    mmse_update['total_score'] = self._calculate_total_score(mmse_update)

                # 更新受试者
                self.subject_manager.update_subject(
                    subject_id=subject_id,
                    demographics=demographics_update if demographics_update else None,
                    mmse=mmse_update if mmse_update else None
                )

                results['updated'] += 1

            except Exception as e:
                results['errors'].append({
                    'row': row_num,
                    'subject_id': subject_id,
                    'error': str(e)
                })

    return results
```

---

### 5. MMSE录入优化

#### 5.1 后端API优化

**新增API**: `POST /api/m02/mmse/submit`

```python
@m02_bp.route('/mmse/submit', methods=['POST'])
@handle_errors
def submit_mmse_data():
    """
    提交MMSE数据（包含人口学信息）

    Request Body:
    {
        "subject_id": "v2_control_001",
        "demographics": {  # 可选，补充人口学信息
            "age": 65,
            "gender": "male",
            "education_level": "undergraduate",
            "name": "张三",
            "hospital_id": "H001"
        },
        "mmse": {
            "q1_year": 1,
            "q1_season": 1,
            "q1_month": 1,
            "q1_weekday": 2,
            "q2_province": 2,
            "q2_floor": 1,
            "q3_immediate": 3
            // 注意: 不需要传total_score和test_date
        }
    }

    Returns:
    {
        "subject": {...},  # 更新后的受试者信息
        "mmse_total_score": 10  # 自动计算的总分
    }
    """
    data = request.get_json()
    subject_id = data['subject_id']

    # 验证受试者存在
    subject = subject_manager.get_subject(subject_id)
    if not subject:
        return {'error': '受试者不存在'}, 404

    # 自动计算MMSE总分
    mmse_data = data.get('mmse', {})
    if mmse_data:
        mmse_data['total_score'] = mmse_manager._calculate_total_score(mmse_data)

    # 更新受试者
    updated_subject = subject_manager.update_subject(
        subject_id=subject_id,
        demographics=data.get('demographics'),
        mmse=mmse_data if mmse_data else None
    )

    return {
        'subject': updated_subject,
        'mmse_total_score': mmse_data.get('total_score')
    }
```

#### 5.2 前端MMSE录入表单优化

**修改**: `frontend/src/pages/Module02/components/MMSEInputModal.jsx`

```jsx
const MMSEInputModal = ({ visible, subject, onClose, onSuccess }) => {
  const [form] = Form.useForm();
  const [totalScore, setTotalScore] = useState(0);

  // 自动计算总分
  const calculateTotalScore = (values) => {
    const score =
      (values.q1_year || 0) +
      (values.q1_season || 0) +
      (values.q1_month || 0) +
      (values.q1_weekday || 0) +
      (values.q2_province || 0) +
      (values.q2_floor || 0) +
      (values.q3_immediate || 0);

    setTotalScore(score);
    return score;
  };

  const handleValuesChange = (changedValues, allValues) => {
    calculateTotalScore(allValues.mmse || {});
  };

  const handleSubmit = async (values) => {
    try {
      const payload = {
        subject_id: subject.subject_id,
        demographics: {
          age: values.age,
          gender: values.gender,
          education_level: values.education_level,
          name: values.name,
          hospital_id: values.hospital_id
        },
        mmse: values.mmse
        // 注意: 不传total_score，后端自动计算
      };

      await submitMMSEData(payload);
      message.success('MMSE数据提交成功');
      onSuccess();
      onClose();
    } catch (error) {
      message.error('提交失败: ' + error.message);
    }
  };

  return (
    <Modal
      title="录入MMSE数据"
      open={visible}
      onCancel={onClose}
      width={800}
      footer={null}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        onValuesChange={handleValuesChange}
        initialValues={{
          subject_id: subject?.subject_id,
          name: subject?.demographics?.name,
          hospital_id: subject?.demographics?.hospital_id,
          age: subject?.demographics?.age,
          gender: subject?.demographics?.gender,
          education_level: subject?.demographics?.education_level
        }}
      >
        {/* 基本信息区 */}
        <h4>基本信息</h4>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="受试者ID" name="subject_id">
              <Input disabled />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="分组">
              <Input value={subject?.group} disabled />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item label="姓名" name="name">
              <Input />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="医院ID" name="hospital_id">
              <Input />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="时间戳">
              <Input value={subject?.metadata?.timestamp} disabled />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              label="年龄"
              name="age"
              rules={[{ required: true, message: '请输入年龄' }]}
            >
              <InputNumber min={0} max={120} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              label="性别"
              name="gender"
              rules={[{ required: true, message: '请选择性别' }]}
            >
              <Select>
                <Select.Option value="male">男</Select.Option>
                <Select.Option value="female">女</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              label="受教育程度"
              name="education_level"
              rules={[{ required: true, message: '请选择受教育程度' }]}
            >
              <Select>
                <Select.Option value="primary">小学</Select.Option>
                <Select.Option value="junior_high">初中</Select.Option>
                <Select.Option value="senior_high">高中</Select.Option>
                <Select.Option value="undergraduate">本科</Select.Option>
                <Select.Option value="postgraduate">研究生</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Divider />

        {/* MMSE评分区 */}
        <h4>MMSE评分</h4>
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item label="Q1: 年份" name={['mmse', 'q1_year']}>
              <Select>
                <Select.Option value={0}>0分</Select.Option>
                <Select.Option value={1}>1分</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label="Q1: 季节" name={['mmse', 'q1_season']}>
              <Select>
                <Select.Option value={0}>0分</Select.Option>
                <Select.Option value={1}>1分</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label="Q1: 月份" name={['mmse', 'q1_month']}>
              <Select>
                <Select.Option value={0}>0分</Select.Option>
                <Select.Option value={1}>1分</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label="Q1: 星期" name={['mmse', 'q1_weekday']}>
              <Select>
                <Select.Option value={0}>0分</Select.Option>
                <Select.Option value={2}>2分</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={6}>
            <Form.Item label="Q2: 省份" name={['mmse', 'q2_province']}>
              <Select>
                <Select.Option value={0}>0分</Select.Option>
                <Select.Option value={2}>2分</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label="Q2: 楼层" name={['mmse', 'q2_floor']}>
              <Select>
                <Select.Option value={0}>0分</Select.Option>
                <Select.Option value={1}>1分</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item label="Q3: 即时回忆" name={['mmse', 'q3_immediate']}>
              <Select>
                <Select.Option value={0}>0分</Select.Option>
                <Select.Option value={1}>1分</Select.Option>
                <Select.Option value={2}>2分</Select.Option>
                <Select.Option value={3}>3分</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        {/* 总分显示 */}
        <Alert
          message={`当前总分: ${totalScore} / 21`}
          type={totalScore >= 18 ? 'success' : totalScore >= 10 ? 'warning' : 'error'}
          showIcon
        />

        <Form.Item style={{ marginTop: 24 }}>
          <Button type="primary" htmlType="submit" block>
            提交MMSE数据
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
};
```

---

### 6. 列表字段扩充

#### 6.1 前端表格列定义

**修改**: `SubjectManagement.jsx`

```jsx
const columns = [
  {
    title: '受试者ID',
    dataIndex: 'subject_id',
    key: 'subject_id',
    width: 180,
    fixed: 'left'
  },
  {
    title: '分组',
    dataIndex: 'group',
    key: 'group',
    width: 100,
    render: (group) => {
      const colorMap = { control: 'green', mci: 'orange', ad: 'red' };
      return <Tag color={colorMap[group]}>{group.toUpperCase()}</Tag>;
    }
  },
  {
    title: '患者姓名',
    dataIndex: ['demographics', 'name'],
    key: 'name',
    width: 120
  },
  {
    title: '年龄',
    dataIndex: ['demographics', 'age'],
    key: 'age',
    width: 80,
    render: (age) => age || '-'
  },
  {
    title: '受教育程度',
    dataIndex: ['demographics', 'education_level'],
    key: 'education_level',
    width: 120,
    render: (level) => {
      const levelMap = {
        'primary': '小学',
        'junior_high': '初中',
        'senior_high': '高中',
        'undergraduate': '本科',
        'postgraduate': '研究生'
      };
      return levelMap[level] || '-';
    }
  },
  {
    title: '医院ID',
    dataIndex: ['demographics', 'hospital_id'],
    key: 'hospital_id',
    width: 120
  },
  {
    title: '时间戳',
    dataIndex: ['metadata', 'timestamp'],
    key: 'timestamp',
    width: 150
  },
  {
    title: '系统状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    render: (status) => {
      const statusMap = {
        'complete': { text: '完整', color: 'success' },
        'partial': { text: '部分', color: 'warning' },
        'empty': { text: '待补充', color: 'default' }
      };
      const s = statusMap[status] || statusMap['empty'];
      return <Badge status={s.color} text={s.text} />;
    }
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right',
    render: (_, record) => (
      <Space>
        <Button size="small" onClick={() => handleViewDetail(record)}>
          查看
        </Button>
        <Button size="small" onClick={() => handleEditMMSE(record)}>
          录入MMSE
        </Button>
        <Button size="small" danger onClick={() => handleDelete(record)}>
          删除
        </Button>
      </Space>
    )
  }
];
```

---

## 📂 文件结构调整

### 后端新增/修改文件

```
src/modules/module02_preprocessing/
├── __init__.py
├── subject_manager.py           # 修改: 增加data_version参数支持
├── mmse_manager.py              # 修改: 优化模板生成、批量导入
├── v1_data_manager.py           # 新增: V1数据管理
├── v2_data_manager.py           # 新增: V2数据管理、ID规范化
└── pipeline.py

src/web/modules/module02_preprocessing/
├── api.py                        # 修改: 新增V1/V2数据管理API
└── api_docs.py                   # 修改: 更新OpenAPI文档

tests/
├── test_v1_data_manager.py      # 新增: V1管理器测试
├── test_v2_data_manager.py      # 新增: V2管理器测试
└── test_subject_manager_extended.py  # 修改: 增加筛选测试
```

### 前端新增/修改文件

```
frontend/src/pages/Module02/
├── index.jsx                     # 修改: 添加V1数据管理Tab
├── SubjectManagement.jsx         # 修改: 增加版本筛选、列扩展
├── V1DataManagement.jsx          # 新增: V1数据管理组件
├── V2DataManagement.jsx          # 修改: ID规范化功能
└── components/
    └── MMSEInputModal.jsx        # 修改: 优化录入表单

frontend/src/services/
└── module02Service.js            # 修改: 新增API调用函数

frontend/src/locales/zh-CN/
└── module02.json                 # 修改: 新增翻译条目
```

---

## 🗺️ API接口清单

### 新增API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/m02/v1/subjects` | 获取V1受试者列表 |
| POST | `/api/m02/v1/import` | 导入V1受试者 |
| POST | `/api/m02/v2/batch-import` | 批量导入V2受试者(含ID规范化) |
| POST | `/api/m02/mmse/submit` | 提交MMSE数据(含人口学信息) |
| GET | `/api/m02/mmse/template?include_v2=true&version=v2` | 生成MMSE模板(含已有数据) |

### 修改API

| 方法 | 路径 | 新增参数 | 说明 |
|------|------|----------|------|
| GET | `/api/m02/subjects` | `?data_version=v1\|v2\|all` | 按版本筛选受试者 |

---

## 🧪 测试策略

### 单元测试

1. **V1数据管理器测试** (`test_v1_data_manager.py`)
   - 扫描V1目录
   - 导入V1受试者
   - 错误处理

2. **V2数据管理器测试** (`test_v2_data_manager.py`)
   - ID规范化逻辑
   - 避免序号冲突
   - 批量导入

3. **Subject Manager扩展测试**
   - 版本筛选功能
   - 混合V1/V2数据

### 集成测试

1. **完整导入流程**
   - V2批量导入 → ID规范化 → 下载模板 → 批量上传MMSE → 验证数据

2. **数据一致性**
   - 确保ID映射正确
   - 确保人口学信息不丢失

---

## 📅 开发计划

### Phase 1: 核心功能 (3-4天)
- ✅ Day 1: V1/V2数据管理器开发
- ✅ Day 2: ID规范化逻辑实现
- ✅ Day 3: MMSE模板优化、录入表单改进
- ✅ Day 4: 前端筛选、列扩展

### Phase 2: 集成测试 (2天)
- ✅ Day 5: 单元测试编写
- ✅ Day 6: 集成测试、Bug修复

### Phase 3: 文档和部署 (1天)
- ✅ Day 7: API文档更新、用户手册

---

## 🎯 质量目标

| 指标 | 目标 |
|------|------|
| 代码覆盖率 | ≥ 85% |
| API响应时间 | < 500ms |
| 批量导入性能 | 100条/秒 |
| UI交互响应 | < 200ms |
| 错误处理完整性 | 100% |

---

## 📝 注意事项

### 数据迁移

1. **现有V2数据处理**
   - 已导入的V2受试者需要执行ID规范化迁移脚本
   - 保留`original_id`在metadata中

2. **向后兼容**
   - 旧的V2 ID仍可查询（通过metadata.original_id）
   - 提供ID映射查询API

### 用户体验

1. **ID规范化提示**
   - 批量导入前显示ID映射预览
   - 允许用户选择是否启用规范化

2. **错误提示优化**
   - 批量导入失败时显示详细错误列表
   - 提供CSV错误行号定位

---

**文档版本**: v1.0
**撰写日期**: 2025-10-06
**状态**: 待审核
**预计开发周期**: 7天
