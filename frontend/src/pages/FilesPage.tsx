import React, { useState } from 'react';
import {
  Row,
  Col,
  Card,
  Upload,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Progress,
  Modal,
  message,
  Tooltip,
  Divider,
  Badge,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  EyeOutlined,
  FolderOutlined,
  CloudUploadOutlined,
  PlusOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import type { ColumnsType } from 'antd/es/table';
import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import QuickActionCard from '../components/common/QuickActionCard';
import LoadingSpinner from '../components/common/LoadingSpinner';

const { Title, Text } = Typography;
const { Dragger } = Upload;

interface FileItem {
  id: string;
  filename: string;
  originalName: string;
  fileSize: number;
  fileType: string;
  uploadTime: Date;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  purpose: string;
}

const FilesPage: React.FC = () => {
  const { t } = useTranslation();
  const [files, setFiles] = useState<FileItem[]>([
    {
      id: '1',
      filename: 'calculus_notes.pdf',
      originalName: '微积分笔记.pdf',
      fileSize: 2048576, // 2MB
      fileType: 'pdf',
      uploadTime: new Date(Date.now() - 1000 * 60 * 60 * 2),
      status: 'completed',
      purpose: 'study',
    },
    {
      id: '2',
      filename: 'linear_algebra.docx',
      originalName: '线性代数教材.docx',
      fileSize: 1536000, // 1.5MB
      fileType: 'docx',
      uploadTime: new Date(Date.now() - 1000 * 60 * 60 * 4),
      status: 'processing',
      purpose: 'reference',
    },
    {
      id: '3',
      filename: 'homework_solutions.txt',
      originalName: '作业解答.txt',
      fileSize: 512000, // 500KB
      fileType: 'txt',
      uploadTime: new Date(Date.now() - 1000 * 60 * 60 * 24),
      status: 'completed',
      purpose: 'homework',
    },
  ]);

  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType: string) => {
    const iconStyle = { fontSize: '18px' };
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return (
          <div className="file-icon-wrapper file-icon-pdf">
            <FilePdfOutlined style={{ color: '#ff4d4f', ...iconStyle }} />
          </div>
        );
      case 'doc':
      case 'docx':
        return (
          <div className="file-icon-wrapper file-icon-doc">
            <FileWordOutlined style={{ color: '#1890ff', ...iconStyle }} />
          </div>
        );
      case 'txt':
      case 'md':
        return (
          <div className="file-icon-wrapper file-icon-txt">
            <FileTextOutlined style={{ color: '#52c41a', ...iconStyle }} />
          </div>
        );
      default:
        return (
          <div className="file-icon-wrapper file-icon-default">
            <FileTextOutlined style={{ color: '#8c8c8c', ...iconStyle }} />
          </div>
        );
    }
  };

  const getStatusTag = (status: string) => {
    const statusConfig = {
      pending: { color: 'orange', text: t('files.pending') },
      processing: { color: 'blue', text: t('files.processing') },
      completed: { color: 'green', text: t('files.completed') },
      failed: { color: 'red', text: t('files.failed') },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const handleFileUpload = (file: File) => {
    const newFile: FileItem = {
      id: Date.now().toString(),
      filename: file.name,
      originalName: file.name,
      fileSize: file.size,
      fileType: file.name.split('.').pop() || '',
      uploadTime: new Date(),
      status: 'pending',
      purpose: 'other',
    };

    setFiles(prev => [newFile, ...prev]);
    message.success(t('files.uploadSuccess'));

    // 模拟文件处理过程
    setTimeout(() => {
      setFiles(prev => prev.map(f => 
        f.id === newFile.id ? { ...f, status: 'processing' } : f
      ));
    }, 1000);

    setTimeout(() => {
      setFiles(prev => prev.map(f => 
        f.id === newFile.id ? { ...f, status: 'completed' } : f
      ));
    }, 3000);

    return false; // 阻止默认上传行为
  };

  const handleDeleteFile = (fileId: string) => {
    Modal.confirm({
      title: '删除文件',
      content: '确定要删除这个文件吗？此操作不可恢复。',
      onOk() {
        setFiles(prev => prev.filter(f => f.id !== fileId));
        message.success('文件删除成功');
      },
    });
  };

  const handlePreviewFile = (file: FileItem) => {
    setSelectedFile(file);
    setPreviewModalVisible(true);
  };

  const columns: ColumnsType<FileItem> = [
    {
      title: t('files.fileName'),
      dataIndex: 'originalName',
      key: 'originalName',
      render: (text, record) => (
        <Space align="center">
          {getFileIcon(record.fileType)}
          <div>
            <div style={{ fontWeight: 500, color: '#262626' }}>{text}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.filename}
            </Text>
          </div>
        </Space>
      ),
      width: 280,
    },
    {
      title: t('files.fileSize'),
      dataIndex: 'fileSize',
      key: 'fileSize',
      render: (size) => (
        <Text style={{ fontWeight: 500 }}>{formatFileSize(size)}</Text>
      ),
      sorter: (a, b) => a.fileSize - b.fileSize,
      width: 120,
    },
    {
      title: t('files.fileType'),
      dataIndex: 'fileType',
      key: 'fileType',
      render: (type) => (
        <Tag 
          color="blue" 
          style={{ borderRadius: '6px', fontWeight: 500 }}
        >
          {type.toUpperCase()}
        </Tag>
      ),
      width: 100,
    },
    {
      title: t('files.processStatus'),
      dataIndex: 'status',
      key: 'status',
      render: (status, record) => (
        <div className={status === 'processing' ? 'file-processing' : ''}>
          {getStatusTag(status)}
        </div>
      ),
      filters: [
        { text: t('files.pending'), value: 'pending' },
        { text: t('files.processing'), value: 'processing' },
        { text: t('files.completed'), value: 'completed' },
        { text: t('files.failed'), value: 'failed' },
      ],
      onFilter: (value, record) => record.status === value,
      width: 120,
    },
    {
      title: t('files.uploadTime'),
      dataIndex: 'uploadTime',
      key: 'uploadTime',
      render: (date) => (
        <div>
          <div style={{ fontWeight: 500 }}>
            {date.toLocaleDateString('zh-CN')}
          </div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {date.toLocaleTimeString('zh-CN', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </Text>
        </div>
      ),
      sorter: (a, b) => a.uploadTime.getTime() - b.uploadTime.getTime(),
      width: 140,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="预览">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => handlePreviewFile(record)}
              style={{ color: '#667eea' }}
            />
          </Tooltip>
          <Tooltip title={t('files.downloadFile')}>
            <Button 
              type="text" 
              icon={<DownloadOutlined />}
              onClick={() => message.info('下载功能将在后端实现后启用')}
              style={{ color: '#52c41a' }}
            />
          </Tooltip>
          <Tooltip title={t('files.deleteFile')}>
            <Button 
              type="text" 
              icon={<DeleteOutlined />} 
              danger
              onClick={() => handleDeleteFile(record.id)}
            />
          </Tooltip>
        </Space>
      ),
      width: 120,
      fixed: 'right',
    },
  ];

  const completedFiles = files.filter(f => f.status === 'completed').length;
  const totalSize = files.reduce((sum, file) => sum + file.fileSize, 0);

  return (
    <div style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
      <PageHeader
        title="文件管理中心"
        subtitle="智能文件管理与处理平台，支持多种格式文件上传、预览和RAG知识库构建"
        icon={<FolderOutlined />}
        gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        actions={[
          {
            text: '批量上传',
            icon: <CloudUploadOutlined />,
            onClick: () => setUploadModalVisible(true),
            type: 'primary'
          }
        ]}
      />

      {/* 统计卡片 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{ marginBottom: '24px' }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="总文件数"
              value={files.length}
              icon={<FileTextOutlined />}
              color="#1890ff"
              trend={{ value: 12, isPositive: true }}
              description="本周新增"
              onClick={() => message.info('查看文件详情')}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="已处理完成"
              value={completedFiles}
              icon={<SyncOutlined />}
              color="#52c41a"
              trend={{ value: 8, isPositive: true }}
              description={`处理成功率 ${files.length ? Math.round(completedFiles / files.length * 100) : 0}%`}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="总存储空间"
              value={formatFileSize(totalSize)}
              icon={<CloudUploadOutlined />}
              color="#faad14"
              description="已使用空间"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="处理中文件"
              value={files.filter(f => f.status === 'processing').length}
              icon={<SyncOutlined />}
              color="#722ed1"
              description="正在处理中"
            />
          </Col>
        </Row>
      </motion.div>

      {/* 快速操作卡片 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        style={{ marginBottom: '24px' }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8}>
            <QuickActionCard
              title="文件上传"
              description="上传学习资料和文档文件"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
              gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
              stats={{ label: "支持格式", value: "PDF/DOC/TXT" }}
              badge="HOT"
            />
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <QuickActionCard
              title="文件管理"
              description="查看和管理已上传文件"
              icon={<FolderOutlined />}
              onClick={() => message.info('文件管理功能')}
              gradient="linear-gradient(135deg, #52c41a 0%, #389e0d 100%)"
              stats={{ label: "已处理", value: `${completedFiles}个` }}
            />
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <QuickActionCard
              title="知识库构建"
              description="基于文件构建RAG知识库"
              icon={<FileTextOutlined />}
              onClick={() => message.info('知识库构建功能即将推出')}
              gradient="linear-gradient(135deg, #fa8c16 0%, #d46b08 100%)"
              stats={{ label: "知识条目", value: "128个" }}
              badge="NEW"
            />
          </Col>
        </Row>
      </motion.div>

      {/* 文件列表 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <Card 
          title={
            <Space>
              <FileTextOutlined style={{ color: '#1890ff' }} />
              {t('files.fileList')}
            </Space>
          }
          extra={
            <Space>
              <Button 
                icon={<SyncOutlined />} 
                onClick={() => message.info('刷新文件列表')}
              >
                刷新
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => setUploadModalVisible(true)}
              >
                上传文件
              </Button>
            </Space>
          }
          style={{ 
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            border: '1px solid rgba(102, 126, 234, 0.1)'
          }}
        >
          <Table
            columns={columns}
            dataSource={files}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
            scroll={{ x: 1000 }}
            bordered
          />
        </Card>
      </motion.div>

      {/* 文件上传模态框 */}
      <Modal
        title={
          <Space>
            <CloudUploadOutlined style={{ color: '#667eea' }} />
            上传文件
          </Space>
        }
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={700}
        style={{ top: 50 }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Dragger
            multiple
            beforeUpload={handleFileUpload}
            accept=".pdf,.doc,.docx,.txt,.md"
            style={{ 
              marginBottom: '24px',
              borderRadius: '12px',
              border: '2px dashed #667eea',
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)'
            }}
            className="enhanced-upload-dragger"
          >
            <p className="ant-upload-drag-icon">
              <CloudUploadOutlined style={{ color: '#667eea', fontSize: '48px' }} />
            </p>
            <p className="ant-upload-text" style={{ color: '#667eea', fontSize: '18px', fontWeight: 'bold' }}>
              点击或拖拽文件到此区域上传
            </p>
            <p className="ant-upload-hint" style={{ color: '#8c8c8c' }}>
              {t('files.supportedFormats')}
              <br />
              {t('files.fileSizeLimit')}
            </p>
          </Dragger>
          
          <Card 
            size="small" 
            title={
              <Space>
                <FileTextOutlined style={{ color: '#52c41a' }} />
                文件用途说明
              </Space>
            }
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.05) 0%, rgba(56, 158, 13, 0.05) 100%)'
            }}
          >
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Space direction="vertical" size="small">
                  <div>
                    <Badge status="processing" />
                    <Text strong>学习材料：</Text>课程笔记、教材章节
                  </div>
                  <div>
                    <Badge status="success" />
                    <Text strong>作业文档：</Text>作业题目、解答等
                  </div>
                </Space>
              </Col>
              <Col span={12}>
                <Space direction="vertical" size="small">
                  <div>
                    <Badge status="warning" />
                    <Text strong>参考资料：</Text>补充文献和材料
                  </div>
                  <div>
                    <Badge status="default" />
                    <Text strong>其他：</Text>其他类型文档
                  </div>
                </Space>
              </Col>
            </Row>
          </Card>
        </motion.div>
      </Modal>

      {/* 文件预览模态框 */}
      <Modal
        title={
          <Space>
            <EyeOutlined style={{ color: '#667eea' }} />
            预览: {selectedFile?.originalName}
          </Space>
        }
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button 
            key="download" 
            icon={<DownloadOutlined />}
            style={{ borderColor: '#667eea', color: '#667eea' }}
          >
            下载
          </Button>,
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={900}
        style={{ top: 30 }}
      >
        {selectedFile && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Card 
              size="small" 
              style={{ 
                marginBottom: '16px',
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)'
              }}
            >
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text type="secondary">文件名:</Text>
                      <Text strong>{selectedFile.originalName}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text type="secondary">文件类型:</Text>
                      <Tag color="blue">{selectedFile.fileType.toUpperCase()}</Tag>
                    </div>
                  </Space>
                </Col>
                <Col span={12}>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text type="secondary">文件大小:</Text>
                      <Text strong>{formatFileSize(selectedFile.fileSize)}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text type="secondary">处理状态:</Text>
                      {getStatusTag(selectedFile.status)}
                    </div>
                  </Space>
                </Col>
              </Row>
              <Divider style={{ margin: '12px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text type="secondary">上传时间:</Text>
                <Text>{selectedFile.uploadTime.toLocaleString('zh-CN')}</Text>
              </div>
            </Card>
            
            <Card 
              style={{ 
                height: '420px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, rgba(245, 245, 245, 0.8) 0%, rgba(250, 250, 250, 0.8) 100%)',
                border: '2px dashed #d9d9d9',
                borderRadius: '12px'
              }}
            >
              <motion.div 
                style={{ textAlign: 'center' }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <div style={{ fontSize: '64px', marginBottom: '16px' }}>
                  {getFileIcon(selectedFile.fileType)}
                </div>
                <Title level={4} type="secondary">
                  {selectedFile.originalName}
                </Title>
                <Text type="secondary" style={{ fontSize: '16px' }}>
                  文件预览功能将在后续版本中实现
                </Text>
                <br />
                <Text type="secondary">
                  支持在线预览 PDF、Word、文本等多种格式
                </Text>
              </motion.div>
            </Card>
          </motion.div>
        )}
      </Modal>
    </div>
  );
};

export default FilesPage;
