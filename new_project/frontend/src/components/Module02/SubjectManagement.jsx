/**
 * 受试者管理组件
 * 功能：受试者信息的增删改查、MMSE数据管理
 */
import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, InputNumber, DatePicker,
  message, Space, Popconfirm, Tag, Upload, Card, Row, Col, Statistic, Collapse, Divider
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, UploadOutlined,
  DownloadOutlined, FileTextOutlined, UserOutlined
} from '@ant-design/icons';
import { subjectService, mmseService } from '../../services/module02Service';
import moment from 'moment';

const { Option } = Select;

const SubjectManagement = () => {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [educationLevels, setEducationLevels] = useState([]);
  const [dataVersionFilter, setDataVersionFilter] = useState('all'); // 'all', 'v1', 'v2'
  const [form] = Form.useForm();

  // 加载数据
  useEffect(() => {
    loadSubjects();
    loadStatistics();
    loadEducationLevels();
  }, [dataVersionFilter]);

  const loadSubjects = async () => {
    setLoading(true);
    try {
      const params = {};
      if (dataVersionFilter !== 'all') {
        params.data_version = dataVersionFilter;
      }
      const response = await subjectService.getAllSubjects(params);
      if (response.success) {
        setSubjects(response.data);
      }
    } catch (error) {
      message.error('加载受试者列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await subjectService.getStatistics();
      if (response.success) {
        setStatistics(response.data);
      }
    } catch (error) {
      console.error('加载统计信息失败', error);
    }
  };

  const loadEducationLevels = async () => {
    try {
      const response = await subjectService.getEducationLevels();
      if (response.success) {
        setEducationLevels(Array.isArray(response.data) ? response.data : []);
      }
    } catch (error) {
      console.error('加载教育程度选项失败', error);
      // 设置默认教育程度选项
      setEducationLevels([
        { value: 'primary', label: '小学' },
        { value: 'junior_high', label: '初中' },
        { value: 'senior_high', label: '高中' },
        { value: 'vocational', label: '中专职高' },
        { value: 'junior_college', label: '大专' },
        { value: 'undergraduate', label: '本科' },
        { value: 'postgraduate', label: '研究生及以上' },
      ]);
    }
  };

  // 打开新增/编辑对话框
  const handleAdd = () => {
    setEditingSubject(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingSubject(record);
    const mmseData = record.mmse || {};
    form.setFieldsValue({
      ...record,
      ...record.demographics,
      mmse_test_date: mmseData.test_date ? moment(mmseData.test_date) : null,
      mmse_total_score: mmseData.total_score,
      // Q1 - 时间定向 (5分)
      q1_year: mmseData.q1_year,
      q1_season: mmseData.q1_season,
      q1_month: mmseData.q1_month,
      q1_weekday: mmseData.q1_weekday,
      // Q2 - 地点定向 (5分)
      q2_province: mmseData.q2_province,
      q2_street: mmseData.q2_street,
      q2_building: mmseData.q2_building,
      q2_floor: mmseData.q2_floor,
      // Q3 - 即刻记忆 (3分)
      q3_immediate: mmseData.q3_immediate,
      // Q4 - 注意力与计算 (5分)
      q4_100_7: mmseData.q4_100_7,
      q4_93_7: mmseData.q4_93_7,
      q4_86_7: mmseData.q4_86_7,
      q4_79_7: mmseData.q4_79_7,
      q4_72_7: mmseData.q4_72_7,
      // Q5 - 延迟回忆 (3分)
      q5_word1: mmseData.q5_word1,
      q5_word2: mmseData.q5_word2,
      q5_word3: mmseData.q5_word3,
    });
    setModalVisible(true);
  };

  // 保存受试者
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      const data = {
        subject_id: values.subject_id,
        group: values.group,
        demographics: {
          gender: values.gender,
          age: values.age,
          education_level: values.education_level,
        },
      };

      // 收集MMSE数据（包括所有子题目）
      const mmseFields = ['q1_year', 'q1_season', 'q1_month', 'q1_weekday',
        'q2_province', 'q2_street', 'q2_building', 'q2_floor',
        'q3_immediate',
        'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
        'q5_word1', 'q5_word2', 'q5_word3'];

      const hasAnyMMSEData = values.mmse_total_score !== undefined ||
                             mmseFields.some(field => values[field] !== undefined);

      if (hasAnyMMSEData) {
        data.mmse = {
          total_score: values.mmse_total_score,
          test_date: values.mmse_test_date?.format('YYYY-MM-DD'),
        };

        // 添加所有子题目分数
        mmseFields.forEach(field => {
          if (values[field] !== undefined) {
            data.mmse[field] = values[field];
          }
        });
      }

      if (editingSubject) {
        await subjectService.updateSubject(editingSubject.subject_id, data);
        message.success('更新成功');
      } else {
        await subjectService.createSubject(data);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadSubjects();
      loadStatistics();
    } catch (error) {
      if (error.response) {
        message.error(error.response.data.message || '保存失败');
      }
    }
  };

  // 删除受试者
  const handleDelete = async (subjectId) => {
    try {
      await subjectService.deleteSubject(subjectId);
      message.success('删除成功');
      loadSubjects();
      loadStatistics();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 下载CSV模板
  const handleDownloadTemplate = () => {
    mmseService.downloadTemplate();
  };

  // 批量导入CSV
  const handleUploadCSV = async (file) => {
    try {
      const response = await mmseService.batchImport(file);
      if (response.success) {
        message.success(`成功导入 ${response.data.updated} 条记录`);
        loadSubjects();
        loadStatistics();
      }
    } catch (error) {
      message.error('导入失败');
    }
    return false; // 阻止自动上传
  };

  // 从Clinical批量导入受试者
  const handleImportFromClinical = async () => {
    setLoading(true);
    try {
      const response = await subjectService.importFromClinical();
      if (response.success) {
        message.success(response.message);
        loadSubjects();
        loadStatistics();
      }
    } catch (error) {
      message.error('批量导入失败');
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '受试者ID',
      dataIndex: 'subject_id',
      key: 'subject_id',
      width: 120,
    },
    {
      title: '组别',
      dataIndex: 'group',
      key: 'group',
      width: 100,
      render: (group) => {
        const groupConfig = {
          control: { color: 'green', label: '对照组' },
          mci: { color: 'orange', label: 'MCI组' },
          ad: { color: 'red', label: 'AD组' }
        };
        const config = groupConfig[group] || { color: 'default', label: group };
        return <Tag color={config.color}>{config.label}</Tag>;
      },
    },
    {
      title: '性别',
      dataIndex: ['demographics', 'gender'],
      key: 'gender',
      width: 80,
      render: (gender) => gender === 'male' ? '男' : '女',
    },
    {
      title: '年龄',
      dataIndex: ['demographics', 'age'],
      key: 'age',
      width: 80,
    },
    {
      title: '教育程度',
      dataIndex: ['demographics', 'education_level'],
      key: 'education_level',
      width: 120,
      render: (level) => {
        const levelMap = {
          primary: '小学',
          junior_high: '初中',
          senior_high: '高中',
          vocational: '中专职高',
          junior_college: '大专',
          undergraduate: '本科',
          postgraduate: '研究生及以上',
        };
        return levelMap[level] || level;
      },
    },
    {
      title: 'MMSE总分',
      dataIndex: ['mmse', 'total_score'],
      key: 'mmse_score',
      width: 100,
      render: (score) => score !== undefined ? `${score}/21` : '-',
    },
    {
      title: '测试日期',
      dataIndex: ['mmse', 'test_date'],
      key: 'test_date',
      width: 120,
    },
    {
      title: '数据版本',
      dataIndex: 'data_version',
      key: 'data_version',
      width: 100,
      render: (version) => {
        const versionConfig = {
          v1: { color: 'blue', label: 'V1' },
          v2: { color: 'green', label: 'V2' }
        };
        const config = versionConfig[version] || { color: 'default', label: version || 'V1' };
        return <Tag color={config.color}>{config.label}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除吗？"
            onConfirm={() => handleDelete(record.subject_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 统计信息 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="受试者总数"
                value={statistics.total_subjects}
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="对照组"
                value={statistics.by_group?.control || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="MCI组"
                value={statistics.by_group?.mci || 0}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="AD组"
                value={statistics.by_group?.ad || 0}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="MMSE已录入"
                value={statistics.mmse_recorded || 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 操作按钮 */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          value={dataVersionFilter}
          onChange={setDataVersionFilter}
          style={{ width: 150 }}
        >
          <Option value="all">全部版本</Option>
          <Option value="v1">仅V1数据</Option>
          <Option value="v2">仅V2数据</Option>
        </Select>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAdd}
        >
          新增受试者
        </Button>
        <Button
          icon={<UploadOutlined />}
          onClick={handleImportFromClinical}
          loading={loading}
        >
          从Clinical批量导入
        </Button>
        <Button
          icon={<DownloadOutlined />}
          onClick={handleDownloadTemplate}
        >
          下载CSV模板
        </Button>
        <Upload
          accept=".csv"
          showUploadList={false}
          beforeUpload={handleUploadCSV}
        >
          <Button icon={<UploadOutlined />}>
            批量导入MMSE
          </Button>
        </Upload>
      </Space>

      {/* 受试者列表 */}
      <Table
        columns={columns}
        dataSource={subjects}
        rowKey="subject_id"
        loading={loading}
        scroll={{ x: 1000 }}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />

      {/* 新增/编辑对话框 */}
      <Modal
        title={editingSubject ? '编辑受试者' : '新增受试者'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="subject_id"
            label="受试者ID"
            rules={[{ required: true, message: '请输入受试者ID' }]}
          >
            <Input disabled={!!editingSubject} />
          </Form.Item>

          <Form.Item
            name="group"
            label="组别"
            rules={[{ required: true, message: '请选择组别' }]}
          >
            <Select>
              <Option value="control">对照组</Option>
              <Option value="mci">MCI组</Option>
              <Option value="ad">AD组</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="gender"
                label="性别"
                rules={[{ required: true, message: '请选择性别' }]}
              >
                <Select>
                  <Option value="male">男</Option>
                  <Option value="female">女</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="age"
                label="年龄"
                rules={[{ required: true, message: '请输入年龄' }]}
              >
                <InputNumber min={0} max={120} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="education_level"
            label="教育程度"
            rules={[{ required: true, message: '请选择教育程度' }]}
          >
            <Select>
              {educationLevels.map(level => (
                <Option key={level.value} value={level.value}>
                  {level.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Divider>MMSE评分（满分21分）</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="mmse_total_score"
                label="MMSE总分"
              >
                <InputNumber min={0} max={21} style={{ width: '100%' }} disabled />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="mmse_test_date"
                label="测试日期"
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Collapse
            ghost
            items={[
              {
                key: '1',
                label: 'Q1 - 时间定向 (5分)',
                children: (
                  <Row gutter={[8, 8]}>
                    <Col span={12}>
                      <Form.Item name="q1_year" label="年份(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q1_season" label="季节(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q1_month" label="月份(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q1_weekday" label="星期(2分)">
                        <InputNumber min={0} max={2} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                )
              },
              {
                key: '2',
                label: 'Q2 - 地点定向 (5分)',
                children: (
                  <Row gutter={[8, 8]}>
                    <Col span={12}>
                      <Form.Item name="q2_province" label="省份(2分)">
                        <InputNumber min={0} max={2} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q2_street" label="街道(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q2_building" label="建筑物(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q2_floor" label="楼层(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                )
              },
              {
                key: '3',
                label: 'Q3 - 即刻记忆 (3分)',
                children: (
                  <Form.Item name="q3_immediate" label="即刻记忆(0-3分)">
                    <InputNumber min={0} max={3} style={{ width: '100%' }} />
                  </Form.Item>
                )
              },
              {
                key: '4',
                label: 'Q4 - 注意力与计算 (5分)',
                children: (
                  <Row gutter={[8, 8]}>
                    <Col span={8}>
                      <Form.Item name="q4_100_7" label="100-7(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="q4_93_7" label="93-7(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="q4_86_7" label="86-7(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q4_79_7" label="79-7(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="q4_72_7" label="72-7(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                )
              },
              {
                key: '5',
                label: 'Q5 - 延迟回忆 (3分)',
                children: (
                  <Row gutter={[8, 8]}>
                    <Col span={8}>
                      <Form.Item name="q5_word1" label="词1(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="q5_word2" label="词2(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="q5_word3" label="词3(1分)">
                        <InputNumber min={0} max={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                )
              }
            ]}
          />
        </Form>
      </Modal>
    </div>
  );
};

export default SubjectManagement;
