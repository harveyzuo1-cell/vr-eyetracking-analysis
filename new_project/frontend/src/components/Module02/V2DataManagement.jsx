/**
 * V2DataManagement: V2受试者数据管理
 *
 * 功能：
 * - 显示scan_result_v2.json中的所有v2受试者
 * - 批量导入v2受试者基础信息
 * - 为v2受试者批量录入MMSE数据
 */
import React, { useState, useEffect } from 'react';
import { Table, Button, message, Tag, Space, Modal, Form, InputNumber, Input, DatePicker, Collapse, Upload, Checkbox, Descriptions } from 'antd';
import { DownloadOutlined, PlusOutlined, UploadOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';

const V2DataManagement = () => {
  const [v2Subjects, setV2Subjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();

  // ID规范化相关状态
  const [enableNormalization, setEnableNormalization] = useState(true);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [idMapping, setIdMapping] = useState({});
  const [importResult, setImportResult] = useState(null);
  const [resultModalVisible, setResultModalVisible] = useState(false);

  // 加载v2受试者列表
  const loadV2Subjects = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/m02/subjects/get-v2-subjects');
      if (response.data.success) {
        setV2Subjects(response.data.data.subjects);
      } else {
        message.error(response.data.message || '加载失败');
      }
    } catch (error) {
      message.error('加载v2受试者列表失败：' + error.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadV2Subjects();
  }, []);

  // 预览ID规范化映射
  const handlePreviewNormalization = async () => {
    try {
      // 获取未导入的V2受试者
      const unimportedSubjects = v2Subjects
        .filter(s => !s.exists_in_system)
        .map(s => ({
          subject_id: s.subject_id,
          group: s.group,
          patient_name: s.patient_name,
          hospital_id: s.hospital_id
        }));

      if (unimportedSubjects.length === 0) {
        message.info('没有需要导入的V2受试者');
        return;
      }

      const response = await axios.post('/api/m02/v2/normalize-preview', {
        subjects: unimportedSubjects
      });

      if (response.data.success) {
        setIdMapping(response.data.id_mapping);
        setPreviewModalVisible(true);
      } else {
        message.error(response.data.message || '预览失败');
      }
    } catch (error) {
      message.error('预览ID映射失败：' + error.message);
    }
  };

  // 规范化现有V2受试者ID
  const handleNormalizeExisting = async () => {
    Modal.confirm({
      title: '确认规范化现有V2受试者ID',
      content: '这将把所有现有V2受试者ID统一规范为 v2_{分组}_{序号} 格式，原始ID会保留在metadata中。是否继续？',
      okText: '确认规范化',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 先预览
          const previewResponse = await axios.post('/api/m02/v2/normalize-existing', {
            dry_run: true
          });

          if (previewResponse.data.success) {
            const mapping = previewResponse.data.id_mapping;
            const count = Object.keys(mapping).filter(k => k !== mapping[k]).length;

            if (count === 0) {
              message.info('所有V2受试者ID已经是规范化格式');
              return;
            }

            // 显示预览，确认后执行
            Modal.confirm({
              title: `将规范化 ${count} 个受试者ID`,
              content: (
                <div>
                  <p>预览ID映射关系（部分）：</p>
                  <ul style={{ maxHeight: 200, overflow: 'auto' }}>
                    {Object.entries(mapping).slice(0, 10).map(([oldId, newId]) => (
                      oldId !== newId && <li key={oldId}>{oldId} → {newId}</li>
                    ))}
                  </ul>
                  {Object.keys(mapping).length > 10 && <p>...还有 {Object.keys(mapping).length - 10} 个</p>}
                </div>
              ),
              okText: '执行规范化',
              cancelText: '取消',
              onOk: async () => {
                const response = await axios.post('/api/m02/v2/normalize-existing', {
                  dry_run: false
                });

                if (response.data.success) {
                  message.success(response.data.message);
                  setImportResult(response.data);
                  setResultModalVisible(true);
                  loadV2Subjects(); // 重新加载
                } else {
                  message.error(response.data.message || '规范化失败');
                }
              }
            });
          }
        } catch (error) {
          message.error('规范化失败：' + error.message);
        }
      }
    });
  };

  // 批量导入v2受试者基础信息
  const handleBulkImport = async () => {
    setImporting(true);
    try {
      // 获取未导入的V2受试者
      const unimportedSubjects = v2Subjects
        .filter(s => !s.exists_in_system)
        .map(s => ({
          subject_id: s.subject_id,
          group: s.group,
          patient_name: s.patient_name,
          hospital_id: s.hospital_id,
          timestamp: s.timestamp
        }));

      // 检查是否有需要导入的受试者
      if (unimportedSubjects.length === 0) {
        message.info('所有V2受试者已经导入系统，无需重复导入');
        setImporting(false);
        return;
      }

      const response = await axios.post('/api/m02/v2/batch-import', {
        subjects: unimportedSubjects,
        rename: enableNormalization
      });

      if (response.data.success) {
        const result = response.data;
        setImportResult(result);
        setResultModalVisible(true);

        message.success(`导入成功：${result.imported} 个受试者`);

        loadV2Subjects(); // 重新加载列表
      } else {
        message.error(response.data.message || '导入失败');
      }
    } catch (error) {
      message.error('批量导入失败：' + error.message);
    }
    setImporting(false);
  };

  // 计算MMSE总分
  const calculateTotalScore = (values) => {
    const mmseFields = ['q1_year', 'q1_season', 'q1_month', 'q1_weekday',
      'q2_province', 'q2_street', 'q2_building', 'q2_floor',
      'q3_immediate',
      'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
      'q5_word1', 'q5_word2', 'q5_word3'];

    let total = 0;
    mmseFields.forEach(field => {
      if (values[field] !== undefined && values[field] !== null) {
        total += values[field];
      }
    });
    return total;
  };

  // 表单值变化时自动计算总分
  const handleFormValuesChange = (changedValues, allValues) => {
    const totalScore = calculateTotalScore(allValues);
    form.setFieldsValue({ mmse_total_score: totalScore });
  };

  // 为单个受试者添加MMSE数据
  const handleAddMMSE = (record) => {
    setEditingSubject(record);
    form.resetFields();
    setModalVisible(true);
  };

  // 保存MMSE数据
  const handleSaveMMSE = async () => {
    try {
      const values = await form.validateFields();

      // 收集MMSE数据
      const mmseFields = ['q1_year', 'q1_season', 'q1_month', 'q1_weekday',
        'q2_province', 'q2_street', 'q2_building', 'q2_floor',
        'q3_immediate',
        'q4_100_7', 'q4_93_7', 'q4_86_7', 'q4_79_7', 'q4_72_7',
        'q5_word1', 'q5_word2', 'q5_word3'];

      const mmseData = {};
      mmseFields.forEach(field => {
        if (values[field] !== undefined) {
          mmseData[field] = values[field];
        }
      });

      // 添加总分（总分已经自动计算）
      mmseData.total_score = values.mmse_total_score;

      // 收集人口学信息
      const demographics = {};
      ['name', 'hospital_id', 'age', 'gender', 'education_level'].forEach(field => {
        if (values[field] !== undefined && values[field] !== '') {
          demographics[field] = values[field];
        }
      });

      // 调用更新API
      const response = await axios.put(`/api/m02/subjects/${editingSubject.subject_id}`, {
        mmse: mmseData,
        demographics: Object.keys(demographics).length > 0 ? demographics : undefined
      });

      if (response.data.success) {
        message.success('MMSE数据保存成功');
        setModalVisible(false);
        loadV2Subjects(); // 重新加载列表
      } else {
        message.error(response.data.message || '保存失败');
      }
    } catch (error) {
      if (error.errorFields) {
        message.error('请检查表单填写');
      } else {
        message.error('保存失败：' + error.message);
      }
    }
  };

  // 下载MMSE批量导入模板
  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get('/api/m02/mmse/batch-template', {
        params: {
          include_data: 'true',
          data_version: 'v2'
        },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'mmse_batch_template_v2.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      message.success('模板下载成功');
    } catch (error) {
      message.error('下载模板失败：' + error.message);
    }
  };

  // 批量上传MMSE配置
  const uploadProps = {
    name: 'file',
    accept: '.csv',
    showUploadList: false,
    beforeUpload: (file) => {
      const isCsv = file.name.endsWith('.csv');
      if (!isCsv) {
        message.error('只能上传CSV文件');
      }
      return isCsv;
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post('/api/m02/mmse/batch-import', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        if (response.data.success) {
          message.success(`批量导入完成：成功 ${response.data.data.success} 个，失败 ${response.data.data.failed} 个`);
          if (response.data.data.errors && response.data.data.errors.length > 0) {
            console.error('导入错误详情：', response.data.data.errors);
          }
          onSuccess();
          loadV2Subjects();
          setUploadModalVisible(false);
        } else {
          message.error(response.data.message || '导入失败');
          onError();
        }
      } catch (error) {
        message.error('上传失败：' + error.message);
        onError(error);
      } finally {
        setUploading(false);
      }
    },
  };

  const columns = [
    {
      title: '受试者ID',
      dataIndex: 'subject_id',
      key: 'subject_id',
      width: 200,
    },
    {
      title: '分组',
      dataIndex: 'group',
      key: 'group',
      width: 100,
      render: (group) => {
        const colorMap = {
          control: 'green',
          mci: 'orange',
          ad: 'red',
        };
        return <Tag color={colorMap[group] || 'blue'}>{group.toUpperCase()}</Tag>;
      },
    },
    {
      title: '患者姓名',
      dataIndex: 'patient_name',
      key: 'patient_name',
      width: 120,
    },
    {
      title: '医院ID',
      dataIndex: 'hospital_id',
      key: 'hospital_id',
      width: 120,
    },
    {
      title: '年龄',
      dataIndex: 'age',
      key: 'age',
      width: 80,
      render: (age) => age || <span style={{ color: '#999' }}>-</span>,
    },
    {
      title: '受教育程度',
      dataIndex: 'education_level',
      key: 'education_level',
      width: 120,
      render: (edu) => edu || <span style={{ color: '#999' }}>-</span>,
    },
    {
      title: '时间戳',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
    },
    {
      title: '系统状态',
      key: 'system_status',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.exists_in_system ? (
            <Tag color="blue">已导入</Tag>
          ) : (
            <Tag color="default">未导入</Tag>
          )}
          {record.has_mmse ? (
            <Tag color="green">有MMSE</Tag>
          ) : (
            <Tag color="warning">无MMSE</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.exists_in_system && !record.has_mmse && (
            <Button
              type="link"
              size="small"
              onClick={() => handleAddMMSE(record)}
            >
              录入MMSE
            </Button>
          )}
          {record.exists_in_system && record.has_mmse && (
            <Button
              type="link"
              size="small"
              onClick={() => handleAddMMSE(record)}
            >
              编辑MMSE
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const stats = {
    total: v2Subjects.length,
    imported: v2Subjects.filter(s => s.exists_in_system).length,
    hasMMSE: v2Subjects.filter(s => s.has_mmse).length,
    needsMMSE: v2Subjects.filter(s => s.exists_in_system && !s.has_mmse).length,
  };

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 统计信息 */}
        <div style={{ background: '#f0f2f5', padding: '16px', borderRadius: '8px' }}>
          <Space size="large">
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                {stats.total}
              </div>
              <div>V2受试者总数</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                {stats.imported}
              </div>
              <div>已导入系统</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
                {stats.hasMMSE}
              </div>
              <div>已有MMSE数据</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff4d4f' }}>
                {stats.needsMMSE}
              </div>
              <div>待录入MMSE</div>
            </div>
          </Space>
        </div>

        {/* 操作按钮 */}
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space wrap>
            <Checkbox
              checked={enableNormalization}
              onChange={(e) => setEnableNormalization(e.target.checked)}
            >
              启用ID规范化（格式：v2_分组_序号）
            </Checkbox>
            {enableNormalization && (
              <Button
                icon={<EyeOutlined />}
                onClick={handlePreviewNormalization}
                size="small"
              >
                预览ID映射
              </Button>
            )}
          </Space>

          <Space wrap>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleBulkImport}
              loading={importing}
            >
              批量导入V2受试者基础信息
            </Button>
            <Button
              danger
              onClick={handleNormalizeExisting}
            >
              规范化现有V2受试者ID
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleDownloadTemplate}
            >
              下载MMSE批量导入模板
            </Button>
            <Button
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              批量导入MMSE数据
            </Button>
            <Button onClick={loadV2Subjects} loading={loading}>
              刷新列表
            </Button>
          </Space>
        </Space>

        {/* V2受试者列表 */}
        <Table
          columns={columns}
          dataSource={v2Subjects}
          rowKey={(record) => `${record.subject_id}_${record.timestamp}`}
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Space>

      {/* MMSE数据录入Modal */}
      <Modal
        title={`为 ${editingSubject?.subject_id} 录入MMSE数据`}
        open={modalVisible}
        onOk={handleSaveMMSE}
        onCancel={() => setModalVisible(false)}
        width={900}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" onValuesChange={handleFormValuesChange}>
          {/* 人口学信息 */}
          <div style={{ marginBottom: 16, padding: 12, background: '#f0f2f5', borderRadius: 4 }}>
            <h4 style={{ marginBottom: 12 }}>基本信息（可选）</h4>
            <Space wrap style={{ width: '100%' }}>
              <Form.Item name="name" label="姓名" style={{ marginBottom: 0, width: 150 }}>
                <Input placeholder="患者姓名" />
              </Form.Item>
              <Form.Item name="hospital_id" label="医院ID" style={{ marginBottom: 0, width: 150 }}>
                <Input placeholder="医院ID" />
              </Form.Item>
              <Form.Item name="age" label="年龄" style={{ marginBottom: 0, width: 100 }}>
                <InputNumber min={0} max={120} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="gender" label="性别" style={{ marginBottom: 0, width: 100 }}>
                <Input placeholder="性别" />
              </Form.Item>
              <Form.Item name="education_level" label="学历" style={{ marginBottom: 0, width: 150 }}>
                <Input placeholder="教育程度" />
              </Form.Item>
            </Space>
          </div>

          {/* MMSE总分 - 自动计算 */}
          <Form.Item name="mmse_total_score" label="MMSE总分（自动计算，满分21）">
            <InputNumber min={0} max={21} style={{ width: '100%' }} disabled />
          </Form.Item>

          <Collapse
            ghost
            items={[
              {
                key: '1',
                label: 'Q1 - 时间定向 (5分)',
                children: (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="q1_year" label="年份(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q1_season" label="季节(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q1_month" label="月份(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q1_weekday" label="星期(2分)">
                      <InputNumber min={0} max={2} style={{ width: '100%' }} />
                    </Form.Item>
                  </Space>
                )
              },
              {
                key: '2',
                label: 'Q2 - 地点定向 (5分)',
                children: (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="q2_province" label="省份(2分)">
                      <InputNumber min={0} max={2} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q2_street" label="街道(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q2_building" label="楼层/建筑(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q2_floor" label="房间号(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                  </Space>
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
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="q4_100_7" label="100-7(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q4_93_7" label="93-7(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q4_86_7" label="86-7(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q4_79_7" label="79-7(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q4_72_7" label="72-7(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                  </Space>
                )
              },
              {
                key: '5',
                label: 'Q5 - 延迟回忆 (3分)',
                children: (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="q5_word1" label="词1(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q5_word2" label="词2(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="q5_word3" label="词3(1分)">
                      <InputNumber min={0} max={1} style={{ width: '100%' }} />
                    </Form.Item>
                  </Space>
                )
              }
            ]}
          />
        </Form>
      </Modal>

      {/* 批量上传MMSE数据Modal */}
      <Modal
        title="批量导入MMSE数据"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <h4>使用说明：</h4>
            <ol>
              <li>点击"下载MMSE批量导入模板"按钮下载CSV模板文件</li>
              <li>在模板中填写受试者的MMSE数据（subject_id列必须与系统中已导入的v2受试者ID完全一致）</li>
              <li>保存CSV文件后，点击下方上传按钮选择文件进行批量导入</li>
              <li>系统会自动验证数据并显示导入结果</li>
            </ol>
          </div>

          <Upload {...uploadProps}>
            <Button
              icon={<UploadOutlined />}
              loading={uploading}
              type="primary"
              block
            >
              {uploading ? '上传中...' : '选择CSV文件上传'}
            </Button>
          </Upload>

          <div style={{ color: '#999', fontSize: '12px' }}>
            提示：CSV文件必须包含subject_id列和至少一个MMSE字段（如total_score、test_date等）
          </div>
        </Space>
      </Modal>

      {/* ID映射预览Modal */}
      <Modal
        title="ID规范化映射预览"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <div style={{ marginBottom: 16 }}>
          <p>以下是将要应用的ID映射关系（共 {Object.keys(idMapping).length} 个）：</p>
        </div>
        <Table
          dataSource={Object.entries(idMapping).map(([oldId, newId]) => ({
            oldId,
            newId,
            key: oldId
          }))}
          columns={[
            {
              title: '原始ID',
              dataIndex: 'oldId',
              key: 'oldId',
              width: '40%'
            },
            {
              title: '→',
              key: 'arrow',
              width: '10%',
              align: 'center',
              render: () => '→'
            },
            {
              title: '规范化后ID',
              dataIndex: 'newId',
              key: 'newId',
              width: '50%',
              render: (text) => <strong style={{ color: '#1890ff' }}>{text}</strong>
            }
          ]}
          pagination={false}
          scroll={{ y: 400 }}
          size="small"
        />
      </Modal>

      {/* 导入结果Modal */}
      <Modal
        title="批量导入结果"
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        footer={[
          <Button key="close" type="primary" onClick={() => setResultModalVisible(false)}>
            确定
          </Button>
        ]}
        width={800}
      >
        {importResult && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="成功导入" span={1}>
                <span style={{ color: '#52c41a', fontSize: '18px', fontWeight: 'bold' }}>
                  {importResult.imported || importResult.updated || 0}
                </span> 个
              </Descriptions.Item>
              <Descriptions.Item label="失败" span={1}>
                <span style={{ color: '#ff4d4f', fontSize: '18px', fontWeight: 'bold' }}>
                  {importResult.failed || (importResult.errors && importResult.errors.length) || 0}
                </span> 个
              </Descriptions.Item>
            </Descriptions>

            {importResult.id_mapping && Object.keys(importResult.id_mapping).length > 0 && (
              <div>
                <h4>ID映射关系：</h4>
                <Table
                  dataSource={Object.entries(importResult.id_mapping).map(([oldId, newId]) => ({
                    oldId,
                    newId,
                    key: oldId
                  }))}
                  columns={[
                    {
                      title: '原始ID',
                      dataIndex: 'oldId',
                      key: 'oldId',
                      width: '45%'
                    },
                    {
                      title: '规范化后ID',
                      dataIndex: 'newId',
                      key: 'newId',
                      width: '55%',
                      render: (text) => <Tag color="blue">{text}</Tag>
                    }
                  ]}
                  pagination={false}
                  scroll={{ y: 300 }}
                  size="small"
                />
              </div>
            )}

            {importResult.errors && importResult.errors.length > 0 && (
              <div>
                <h4 style={{ color: '#ff4d4f' }}>错误信息：</h4>
                <ul>
                  {importResult.errors.map((error, index) => (
                    <li key={index} style={{ color: '#ff4d4f' }}>
                      {error.subject_id}: {error.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default V2DataManagement;
