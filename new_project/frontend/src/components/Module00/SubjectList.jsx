import React, { useState, useMemo } from 'react';
import { Card, Table, Tag, Select, Space } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Option } = Select;

const SubjectList = ({ scanData }) => {
  const { t } = useTranslation('module00');
  const [dataVersion, setDataVersion] = useState('all');
  const [groupFilter, setGroupFilter] = useState('all');

  // 合并两个数据源的受试者列表
  const allSubjects = useMemo(() => {
    if (!scanData) return [];

    const subjects = [];

    // Legacy数据
    const legacyData = scanData.legacy_data?.details || {};
    Object.entries(legacyData).forEach(([group, subjectList]) => {
      subjectList.forEach((subject, index) => {
        subjects.push({
          key: `legacy_${subject.subject_id}_${index}`, // 使用复合key确保唯一性
          subject_id: subject.subject_id,
          group: subject.group,
          data_version: 'v1',
          source_type: 'legacy',
          hospital_id: 'N/A',
        });
      });
    });

    // Eye Tracking数据
    const eyeTrackingData = scanData.eye_tracking_data?.details?.valid_entries || [];
    eyeTrackingData.forEach((subject, index) => {
      // 使用timestamp作为唯一标识，如果没有则使用index
      const uniqueKey = subject.timestamp
        ? `eyetrack_${subject.subject_id}_${subject.timestamp}`
        : `eyetrack_${subject.subject_id}_${index}`;

      subjects.push({
        key: uniqueKey,
        subject_id: subject.subject_id,
        group: subject.group_code,
        data_version: 'v2',
        source_type: 'eye_tracking',
        hospital_id: subject.hospital_id,
        patient_name: subject.patient_name,
        timestamp: subject.timestamp,
      });
    });

    return subjects;
  }, [scanData]);

  // 过滤受试者
  const filteredSubjects = useMemo(() => {
    return allSubjects.filter((subject) => {
      if (dataVersion !== 'all' && subject.data_version !== dataVersion) return false;
      if (groupFilter !== 'all' && subject.group !== groupFilter) return false;
      return true;
    });
  }, [allSubjects, dataVersion, groupFilter]);

  const columns = [
    {
      title: 'Subject ID',
      dataIndex: 'subject_id',
      key: 'subject_id',
      width: 180,
    },
    {
      title: '姓名',
      dataIndex: 'patient_name',
      key: 'patient_name',
      render: (name) => name || '-',
      width: 100,
    },
    {
      title: 'Hospital ID',
      dataIndex: 'hospital_id',
      key: 'hospital_id',
      width: 120,
    },
    {
      title: '分组',
      dataIndex: 'group',
      key: 'group',
      width: 100,
      render: (group) => {
        const colorMap = {
          control: 'blue',
          mci: 'orange',
          ad: 'red',
        };
        return <Tag color={colorMap[group]}>{group.toUpperCase()}</Tag>;
      },
    },
    {
      title: '数据版本',
      dataIndex: 'data_version',
      key: 'data_version',
      width: 100,
      render: (version) => (
        <Tag color={version === 'v1' ? 'green' : 'blue'}>{version}</Tag>
      ),
    },
    {
      title: '数据源',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 120,
      render: (type) => (
        <Tag>{type === 'legacy' ? 'Legacy' : 'Eye Tracking'}</Tag>
      ),
    },
    {
      title: '时间戳',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp) => timestamp || '-',
    },
  ];

  return (
    <Card
      title={
        <span>
          <UserOutlined /> {t('subjectList.title')} {t('subjectList.count', { count: filteredSubjects.length })}
        </span>
      }
      extra={
        <Space>
          <Select
            value={dataVersion}
            onChange={setDataVersion}
            style={{ width: 120 }}
          >
            <Option value="all">全部版本</Option>
            <Option value="v1">Legacy v1</Option>
            <Option value="v2">Eye Tracking v2</Option>
          </Select>
          <Select
            value={groupFilter}
            onChange={setGroupFilter}
            style={{ width: 120 }}
          >
            <Option value="all">全部分组</Option>
            <Option value="control">Control</Option>
            <Option value="mci">MCI</Option>
            <Option value="ad">AD</Option>
          </Select>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={filteredSubjects}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        size="middle"
      />
    </Card>
  );
};

export default SubjectList;
