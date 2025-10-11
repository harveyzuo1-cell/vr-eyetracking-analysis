import React, { useState } from 'react';
import { Card, Button, Select, Space, Checkbox, Statistic, Row, Col, message, Progress, Alert } from 'antd';
import { DownloadOutlined, RocketOutlined, FileTextOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

/**
 * 批量特征提取面板
 *
 * 功能:
 * - 批量提取所有受试者的特征向量
 * - 支持选择分组（Control/MCI/AD）
 * - 支持选择策略（Strategy A/B）
 * - 导出为 CSV 或 JSON 格式
 */
const BatchExtractionPanel = () => {
  const [groups, setGroups] = useState(['control', 'mci', 'ad']);
  const [strategy, setStrategy] = useState('A');
  const [exportFormat, setExportFormat] = useState('csv');
  const [dataVersion, setDataVersion] = useState('v1');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  // 批量提取
  const handleBatchExtract = async () => {
    if (groups.length === 0) {
      message.warning('请至少选择一个分组！');
      return;
    }

    setLoading(true);
    setResults(null);

    try {
      const response = await axios.post('http://127.0.0.1:9090/api/m06/extract/batch', {
        groups,
        data_version: dataVersion,
        strategy,
        export_format: exportFormat,
      });

      if (response.data.success) {
        setResults(response.data.data);
        message.success(`批量提取完成！成功: ${response.data.data.success_count}/${response.data.data.total_subjects}`);
      } else {
        message.error(`提取失败: ${response.data.error}`);
      }
    } catch (error) {
      message.error(`请求失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 分组选择
  const groupOptions = [
    { label: 'Control (对照组)', value: 'control' },
    { label: 'MCI (轻度认知障碍)', value: 'mci' },
    { label: 'AD (阿尔茨海默症)', value: 'ad' },
  ];

  // 计算进度百分比
  const progressPercent = results
    ? Math.round((results.success_count / results.total_subjects) * 100)
    : 0;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 参数配置区域 */}
      <Card title="提取参数配置">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* 分组选择 */}
          <div>
            <div style={{ marginBottom: 8 }}>
              <strong>选择分组:</strong>
            </div>
            <Checkbox.Group
              options={groupOptions}
              value={groups}
              onChange={setGroups}
            />
          </div>

          {/* 策略选择 */}
          <Row gutter={16}>
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>
                <strong>特征策略:</strong>
              </div>
              <Select value={strategy} onChange={setStrategy} style={{ width: '100%' }}>
                <Option value="A">Strategy A (10维)</Option>
                <Option value="B">Strategy B (69维)</Option>
              </Select>
            </Col>

            <Col span={8}>
              <div style={{ marginBottom: 8 }}>
                <strong>导出格式:</strong>
              </div>
              <Select value={exportFormat} onChange={setExportFormat} style={{ width: '100%' }}>
                <Option value="csv">CSV 格式</Option>
                <Option value="json">JSON 格式</Option>
              </Select>
            </Col>

            <Col span={8}>
              <div style={{ marginBottom: 8 }}>
                <strong>数据版本:</strong>
              </div>
              <Select value={dataVersion} onChange={setDataVersion} style={{ width: '100%' }}>
                <Option value="v1">V1</Option>
                <Option value="v2">V2</Option>
              </Select>
            </Col>
          </Row>

          {/* 执行按钮 */}
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={handleBatchExtract}
            loading={loading}
            block
          >
            {loading ? '正在提取特征向量...' : '开始批量提取'}
          </Button>
        </Space>
      </Card>

      {/* 策略说明 */}
      <Alert
        message="策略说明"
        description={
          <div>
            <p><strong>Strategy A (10维)</strong>: Module04 Top-4 + Module05 Top-6 = 10维特征向量</p>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>特征维度: 10</li>
              <li>样本数量: 300 (60 受试者 × 5 任务)</li>
              <li>样本特征比: 30:1 (优秀)</li>
              <li>适用场景: 通用分类任务，避免过拟合</li>
            </ul>
            <p style={{ marginTop: 12 }}><strong>Strategy B (69维)</strong>: Module04 全部9个 + Module05 Top-10参数×6特征 = 69维特征向量</p>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>特征维度: 69</li>
              <li>样本数量: 300</li>
              <li>样本特征比: 4.3:1 (可接受)</li>
              <li>适用场景: 深度分析，需要更多特征信息</li>
            </ul>
          </div>
        }
        type="info"
        showIcon
      />

      {/* 提取进度和结果 */}
      {loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Progress
              type="circle"
              percent={0}
              status="active"
              format={() => '提取中...'}
            />
            <div style={{ marginTop: 16, color: '#999' }}>
              正在批量提取特征向量，请稍候...
            </div>
          </div>
        </Card>
      )}

      {/* 提取结果 */}
      {results && (
        <>
          <Card title="提取结果">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="总受试者数"
                  value={results.total_subjects}
                  suffix="个"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="成功提取"
                  value={results.success_count}
                  suffix="个"
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="提取失败"
                  value={results.failed_count}
                  suffix="个"
                  valueStyle={{ color: results.failed_count > 0 ? '#cf1322' : '#999' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="特征维度"
                  value={results.dimension}
                  suffix="维"
                />
              </Col>
            </Row>

            <div style={{ marginTop: 24 }}>
              <div style={{ marginBottom: 8 }}>
                <strong>完成进度:</strong>
              </div>
              <Progress
                percent={progressPercent}
                status={results.failed_count > 0 ? 'exception' : 'success'}
              />
            </div>
          </Card>

          {/* 导出文件信息 */}
          <Card title={<span><FileTextOutlined /> 导出文件</span>}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div>
                <strong>文件路径:</strong>
                <div style={{
                  marginTop: 8,
                  padding: 12,
                  background: '#f5f5f5',
                  borderRadius: 4,
                  fontFamily: 'monospace',
                  fontSize: 13,
                  wordBreak: 'break-all',
                }}>
                  {results.export_path}
                </div>
              </div>

              <div>
                <strong>文件格式:</strong> {results.export_format.toUpperCase()}
              </div>

              <div>
                <strong>特征策略:</strong> Strategy {results.strategy} ({results.dimension}维)
              </div>

              {results.failed_count > 0 && (
                <Alert
                  message="部分受试者提取失败"
                  description={
                    <div>
                      <p>失败的受试者ID:</p>
                      <div style={{
                        padding: 8,
                        background: '#fff',
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        maxHeight: 100,
                        overflow: 'auto',
                      }}>
                        {results.failed_subjects.join(', ')}
                      </div>
                    </div>
                  }
                  type="warning"
                  showIcon
                />
              )}

              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => message.info('文件已保存到服务器路径，请手动下载')}
              >
                查看导出文件
              </Button>
            </Space>
          </Card>
        </>
      )}

      {/* 使用提示 */}
      {!results && !loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            请配置提取参数，然后点击"开始批量提取"按钮
          </div>
        </Card>
      )}
    </Space>
  );
};

export default BatchExtractionPanel;
