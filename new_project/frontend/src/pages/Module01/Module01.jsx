/**
 * 模块1: 数据可视化
 *
 * 功能：
 * - 选择数据（组别、受试者、任务）
 * - 加载眼动数据
 * - 显示眼动轨迹图
 * - 显示热力图
 * - 数据统计信息
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Select, Button, Space, Alert, Statistic, Row, Col, message, Tag, Descriptions, Tabs, Modal, Progress, Collapse } from 'antd';
import { LineChartOutlined, ReloadOutlined, HeatMapOutlined, DotChartOutlined, CheckCircleOutlined, CloseCircleOutlined, AuditOutlined, WarningOutlined } from '@ant-design/icons';
import { dataService } from '../../services/dataService';
import { roiService } from '../../services/roiService';
import GazeTrajectoryChart from '../../components/Charts/GazeTrajectoryChart';
import GazeTrajectoryChartEnhanced from '../../components/Charts/GazeTrajectoryChartEnhanced';
import HeatmapChart from '../../components/Charts/HeatmapChart';
import ROIStatsPanel from '../../components/Charts/ROIStatsPanel';

const { Option } = Select;

const Module01 = () => {
  // 状态管理
  const [groups, setGroups] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [tasks, setTasks] = useState([]);

  const [selectedGroup, setSelectedGroup] = useState(null);
  const [selectedVersion, setSelectedVersion] = useState('all'); // 数据版本筛选
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);

  const [gazeData, setGazeData] = useState(null);
  const [stats, setStats] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [roiConfig, setRoiConfig] = useState(null); // ROI配置 (简单版)
  const [roiConfigEnhanced, setRoiConfigEnhanced] = useState(null); // ROI配置 (增强版)
  const [roiStats, setRoiStats] = useState(null); // ROI统计信息

  const [loadingGroups, setLoadingGroups] = useState(false);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [loadingData, setLoadingData] = useState(false);

  // 校正完成度验证状态
  const [calibrationModalVisible, setCalibrationModalVisible] = useState(false);
  const [calibrationCheckVersion, setCalibrationCheckVersion] = useState('v1');
  const [calibrationData, setCalibrationData] = useState(null);
  const [loadingCalibration, setLoadingCalibration] = useState(false);

  // 组件加载时获取组别列表
  useEffect(() => {
    loadGroups();
  }, []);

  // 当版本变化时，重新加载组别统计信息
  useEffect(() => {
    loadGroups(selectedVersion);
  }, [selectedVersion]);

  // 当组别或版本变化时，加载受试者列表
  useEffect(() => {
    if (selectedGroup) {
      loadSubjects(selectedGroup, selectedVersion);
      // 重置受试者和任务选择
      setSelectedSubject(null);
      setSelectedTask(null);
      setTasks([]);
      setGazeData(null);
    }
  }, [selectedGroup, selectedVersion]);

  // 当受试者变化时，加载任务列表
  useEffect(() => {
    if (selectedGroup && selectedSubject) {
      loadTasks(selectedGroup, selectedSubject);
      // 重置任务选择
      setSelectedTask(null);
      setGazeData(null);
    }
  }, [selectedSubject]);

  // 加载组别列表
  const loadGroups = async (version = 'all') => {
    try {
      setLoadingGroups(true);
      const result = await dataService.getGroups(version);
      setGroups(result.data || []);

      // 默认选择第一个组别（仅在首次加载时）
      if (!selectedGroup && result.data && result.data.length > 0) {
        setSelectedGroup(result.data[0].id);
      }
    } catch (error) {
      console.error('加载组别列表失败:', error);
      message.error('加载组别列表失败');
    } finally {
      setLoadingGroups(false);
    }
  };

  // 加载受试者列表
  const loadSubjects = async (group, version = 'all') => {
    try {
      setLoadingSubjects(true);
      const result = await dataService.getSubjects(group, version);
      setSubjects(result.data || []);

      // 默认选择第一个受试者
      if (result.data && result.data.length > 0) {
        setSelectedSubject(result.data[0].id);
      }
    } catch (error) {
      console.error('加载受试者列表失败:', error);
      message.error('加载受试者列表失败');
    } finally {
      setLoadingSubjects(false);
    }
  };

  // 加载任务列表
  const loadTasks = async (group, subjectId) => {
    try {
      setLoadingTasks(true);
      const result = await dataService.getTasks(group, subjectId);
      setTasks(result.data || []);

      // 默认选择第一个任务
      if (result.data && result.data.length > 0) {
        setSelectedTask(result.data[0]);
      }
    } catch (error) {
      console.error('加载任务列表失败:', error);
      message.error('加载任务列表失败');
    } finally {
      setLoadingTasks(false);
    }
  };

  // 加载眼动数据
  const loadGazeData = async () => {
    if (!selectedGroup || !selectedSubject || !selectedTask) {
      message.warning('请先选择组别、受试者和任务');
      return;
    }

    try {
      setLoadingData(true);

      let result;
      if (selectedTask === 'all') {
        // 加载全部任务数据
        result = await dataService.loadAllTasksData(
          selectedGroup,
          selectedSubject
        );
        message.success(`成功加载全部任务 ${result.data.length} 个数据点`);
      } else {
        // 加载单个任务数据
        result = await dataService.loadRawData(
          selectedGroup,
          selectedSubject,
          selectedTask
        );
        message.success(`成功加载 ${result.data.length} 个数据点`);
      }

      setGazeData(result.data);
      setStats(result.stats);
      setMetadata(result.metadata);

      // 加载ROI配置（V1和V2都支持）
      // 使用用户选择的版本，而不是metadata中的版本（修复v2 ROI加载问题）
      const dataVersionFromSubject = selectedSubject ? (selectedSubject.includes('_v2_') ? 'v2' : 'v1') : 'v1';
      const dataVersion = selectedVersion === 'all' ? dataVersionFromSubject : selectedVersion;

      // 加载简单版ROI配置（用于兼容）
      const roiResult = await roiService.getROIConfig(dataVersion, selectedTask);
      if (roiResult.success) {
        setRoiConfig(roiResult.data);
      } else {
        console.warn('加载ROI配置失败:', roiResult.error);
        setRoiConfig(null);
      }

      // 加载增强版ROI配置（多层ROI + 背景图片）
      const roiEnhancedResult = await roiService.getROIConfigEnhanced(dataVersion, selectedTask);
      if (roiEnhancedResult.success) {
        setRoiConfigEnhanced(roiEnhancedResult.data);

        // ROI统计信息将在GazeTrajectoryChartEnhanced组件加载displayData后自动计算
        // 这样可以确保使用矫正后的数据（如果存在）
      } else {
        console.warn('加载增强版ROI配置失败:', roiEnhancedResult.error);
        setRoiConfigEnhanced(null);
        setRoiStats(null);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败: ' + (error.message || '未知错误'));
    } finally {
      setLoadingData(false);
    }
  };

  // 当显示的数据变化时（如校正后数据加载），重新计算ROI统计
  const handleDisplayDataChange = useCallback(async (displayData) => {
    if (!roiConfigEnhanced || !selectedTask || !displayData || displayData.length === 0) {
      return;
    }

    try {
      const dataVersion = metadata?.data_version || 'v1';
      const roiStatsResult = await roiService.calculateROIStats(
        dataVersion,
        selectedTask,
        displayData
      );
      if (roiStatsResult.success) {
        setRoiStats(roiStatsResult.data);
      } else {
        console.warn('重新计算ROI统计失败:', roiStatsResult.error);
      }
    } catch (error) {
      console.error('重新计算ROI统计错误:', error);
    }
  }, [roiConfigEnhanced, selectedTask, metadata]);

  // 检查校正完成度
  const checkCalibrationCompleteness = async () => {
    try {
      setLoadingCalibration(true);
      const result = await dataService.checkCalibrationCompleteness(calibrationCheckVersion);

      if (result.success) {
        setCalibrationData(result.data);
        setCalibrationModalVisible(true);
      } else {
        message.error('检查校正完成度失败');
      }
    } catch (error) {
      console.error('检查校正完成度错误:', error);
      message.error('检查校正完成度失败: ' + (error.message || '未知错误'));
    } finally {
      setLoadingCalibration(false);
    }
  };

  return (
    <div>
      {/* 页面标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h2 style={{ marginBottom: 8 }}>
              <LineChartOutlined style={{ marginRight: 8 }} />
              模块1: 数据可视化
            </h2>
            <p style={{ color: '#666', marginBottom: 0 }}>
              可视化眼球追踪数据，包括轨迹图、热力图等
            </p>
          </Col>
          <Col>
            <Space>
              <Select
                value={calibrationCheckVersion}
                onChange={setCalibrationCheckVersion}
                style={{ width: 140 }}
              >
                <Option value="v1">V1 (旧数据)</Option>
                <Option value="v2">V2 (新数据)</Option>
              </Select>
              <Button
                type="primary"
                icon={<AuditOutlined />}
                onClick={checkCalibrationCompleteness}
                loading={loadingCalibration}
              >
                验证校正完成度
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 数据选择 */}
      <Card title="数据选择" style={{ marginBottom: 24 }}>
        <Space size="large" wrap>
          <div>
            <label style={{ marginRight: 8 }}>数据版本:</label>
            <Select
              value={selectedVersion}
              onChange={setSelectedVersion}
              style={{ width: 150 }}
            >
              <Option value="all">全部版本</Option>
              <Option value="v1">V1 (旧数据)</Option>
              <Option value="v2">V2 (新数据)</Option>
            </Select>
          </div>

          <div>
            <label style={{ marginRight: 8 }}>研究组别:</label>
            <Select
              value={selectedGroup}
              onChange={setSelectedGroup}
              style={{ width: 180 }}
              loading={loadingGroups}
            >
              {groups.map(g => (
                <Option key={g.id} value={g.id}>
                  {g.name} ({g.count}人)
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <label style={{ marginRight: 8 }}>受试者:</label>
            <Select
              value={selectedSubject}
              onChange={setSelectedSubject}
              placeholder="选择受试者"
              style={{ width: 280 }}
              loading={loadingSubjects}
              disabled={!selectedGroup}
            >
              {subjects.map(s => (
                <Option key={s.id} value={s.id}>
                  <Space>
                    <span>{s.id}</span>
                    <Tag color={s.data_version === 'v2' ? 'blue' : 'green'} style={{ margin: 0 }}>
                      {s.data_version || 'v1'}
                    </Tag>
                    {s.has_mmse && (
                      <Tag color="orange" style={{ margin: 0 }}>MMSE</Tag>
                    )}
                    <span style={{ color: '#999' }}>({s.task_count}个任务)</span>
                  </Space>
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <label style={{ marginRight: 8 }}>任务:</label>
            <Select
              value={selectedTask}
              onChange={setSelectedTask}
              placeholder="选择任务"
              style={{ width: 140 }}
              loading={loadingTasks}
              disabled={!selectedSubject}
            >
              <Option value="all">全部任务</Option>
              {tasks.map(t => (
                <Option key={t} value={t}>
                  {t.toUpperCase()}
                </Option>
              ))}
            </Select>
          </div>

          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={loadGazeData}
            loading={loadingData}
            disabled={!selectedGroup || !selectedSubject || !selectedTask}
          >
            加载数据
          </Button>
        </Space>
      </Card>

      {/* 数据统计 */}
      {stats && (
        <Card title="数据统计" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="数据点数"
                value={stats.total_points}
                suffix="个"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="持续时间"
                value={stats.duration}
                precision={2}
                suffix="秒"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="X坐标范围"
                value={`${stats.x_range[0].toFixed(3)} - ${stats.x_range[1].toFixed(3)}`}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Y坐标范围"
                value={`${stats.y_range[0].toFixed(3)} - ${stats.y_range[1].toFixed(3)}`}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 元数据信息 */}
      {metadata && (
        <Card title="数据信息" style={{ marginBottom: 24 }}>
          <Descriptions column={3} size="small">
            <Descriptions.Item label="受试者ID">
              {metadata.subject_id}
            </Descriptions.Item>
            <Descriptions.Item label="组别">
              {metadata.group}
            </Descriptions.Item>
            <Descriptions.Item label="任务">
              {metadata.task === 'all' ? '全部任务(Q1-Q5)' : metadata.task.toUpperCase()}
            </Descriptions.Item>
            <Descriptions.Item label="数据版本">
              <Tag color={metadata.data_version === 'v2' ? 'blue' : 'green'}>
                {metadata.data_version || 'v1'}
              </Tag>
              <span style={{ marginLeft: 8, color: '#999' }}>
                ({metadata.source_type === 'legacy' ? '原始数据' : '眼动仪v2'})
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="ROI布局">
              {metadata.roi_layout || 'v1'}
            </Descriptions.Item>
            <Descriptions.Item label="MMSE评分">
              {metadata.has_mmse ? (
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  <span>已有</span>
                </Space>
              ) : (
                <Space>
                  <CloseCircleOutlined style={{ color: '#999' }} />
                  <span style={{ color: '#999' }}>暂无</span>
                </Space>
              )}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* 提示信息 */}
      {!gazeData && (
        <Alert
          message="使用说明"
          description={
            <div>
              <p>1. 选择研究组别（对照组/MCI组/AD组）</p>
              <p>2. 选择受试者ID</p>
              <p>3. 选择任务（Q1-Q5）</p>
              <p>4. 点击"加载数据"按钮</p>
              <p>5. 查看眼动轨迹图和热力图</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 可视化图表 */}
      <Card title="数据可视化">
        {gazeData ? (
          <Tabs
            defaultActiveKey="trajectory"
            items={[
              {
                key: 'trajectory',
                label: (
                  <span>
                    <DotChartOutlined />
                    眼动轨迹图
                  </span>
                ),
                children: (
                  <Row gutter={16}>
                    <Col span={14}>
                      <GazeTrajectoryChartEnhanced
                        data={gazeData}
                        roiConfig={roiConfigEnhanced}
                        loading={loadingData}
                        title=""
                        enableCalibration={true}
                        group={selectedGroup}
                        subjectId={selectedSubject}
                        task={selectedTask}
                        onDataChange={handleDisplayDataChange}
                      />
                    </Col>
                    <Col span={10}>
                      <ROIStatsPanel
                        roiStats={roiStats}
                        roiConfig={roiConfigEnhanced}
                      />
                    </Col>
                  </Row>
                )
              },
              {
                key: 'heatmap',
                label: (
                  <span>
                    <HeatMapOutlined />
                    热力图
                  </span>
                ),
                children: (
                  <HeatmapChart
                    data={gazeData}
                    loading={loadingData}
                    title=""
                    gridSize={50}
                  />
                )
              }
            ]}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '100px 0' }}>
            <p>请加载数据后查看可视化图表</p>
          </div>
        )}
      </Card>

      {/* 校正完成度Modal */}
      <Modal
        title={
          <span>
            <AuditOutlined style={{ marginRight: 8 }} />
            校正完成度检查结果
          </span>
        }
        open={calibrationModalVisible}
        onCancel={() => setCalibrationModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setCalibrationModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {calibrationData && (
          <div>
            {/* 总体统计 */}
            <Card size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="数据版本"
                    value={calibrationData.summary.data_version.toUpperCase()}
                    valueStyle={{ color: calibrationData.summary.data_version === 'v1' ? '#52c41a' : '#1890ff' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="总受试者数"
                    value={calibrationData.summary.total_subjects}
                    suffix="人"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="总任务数"
                    value={calibrationData.summary.total_tasks}
                    suffix="个"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="完成率"
                    value={calibrationData.summary.completion_rate}
                    suffix="%"
                    valueStyle={{
                      color: calibrationData.summary.completion_rate === 100 ? '#52c41a' :
                             calibrationData.summary.completion_rate > 50 ? '#faad14' : '#ff4d4f'
                    }}
                    prefix={
                      calibrationData.summary.completion_rate === 100 ?
                      <CheckCircleOutlined /> :
                      <WarningOutlined />
                    }
                  />
                </Col>
              </Row>
              <div style={{ marginTop: 16 }}>
                <Progress
                  percent={calibrationData.summary.completion_rate}
                  status={calibrationData.summary.completion_rate === 100 ? 'success' : 'active'}
                  strokeColor={
                    calibrationData.summary.completion_rate === 100 ? '#52c41a' :
                    calibrationData.summary.completion_rate > 50 ? '#faad14' : '#ff4d4f'
                  }
                />
                <div style={{ marginTop: 8, fontSize: 14, color: '#666' }}>
                  已校正: {calibrationData.summary.calibrated_tasks} /
                  未校正: {calibrationData.summary.missing_tasks}
                </div>
              </div>
            </Card>

            {/* 分组统计 */}
            <Card size="small" title="各组完成度" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                {Object.entries(calibrationData.by_group).map(([groupName, groupData]) => (
                  <Col span={8} key={groupName}>
                    <Card size="small" style={{ marginBottom: 8 }}>
                      <h4>{groupName === 'control' ? '对照组' : groupName === 'mci' ? 'MCI组' : 'AD组'}</h4>
                      <Progress
                        percent={groupData.completion_rate}
                        size="small"
                        status={groupData.completion_rate === 100 ? 'success' : 'active'}
                      />
                      <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                        受试者: {groupData.subjects}人 |
                        已校正: {groupData.calibrated}/{groupData.total_tasks}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>

            {/* 缺失详情 */}
            {calibrationData.missing_details && calibrationData.missing_details.length > 0 ? (
              <Card size="small" title={
                <span>
                  <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />
                  缺失校正详情 ({calibrationData.missing_details.length}个受试者)
                </span>
              }>
                <Collapse
                  size="small"
                  items={calibrationData.missing_details.map((item, index) => ({
                    key: index,
                    label: (
                      <Space>
                        <Tag color={item.group === 'control' ? 'green' : item.group === 'mci' ? 'orange' : 'red'}>
                          {item.group.toUpperCase()}
                        </Tag>
                        <span style={{ fontWeight: 500 }}>{item.subject_id}</span>
                        <span style={{ color: '#999' }}>
                          缺失 {item.missing_count}/{item.total_tasks} 个任务
                        </span>
                      </Space>
                    ),
                    children: (
                      <div>
                        <p style={{ marginBottom: 8, color: '#666' }}>缺失的任务:</p>
                        <Space wrap>
                          {item.missing_tasks.map(task => (
                            <Tag key={task} color="error">{task.toUpperCase()}</Tag>
                          ))}
                        </Space>
                      </div>
                    )
                  }))}
                />
              </Card>
            ) : (
              <Alert
                message="所有受试者的所有任务都已完成校正"
                type="success"
                showIcon
                icon={<CheckCircleOutlined />}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Module01;
