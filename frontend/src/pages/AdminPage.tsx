import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  Select,
  Input,
  Modal,
  Form,
  message,
  DatePicker,
  Tabs,
  Badge,
  Avatar,
  Typography,
  Switch,
  Popconfirm,
  Progress,
  Timeline,
  Alert,
  Divider
} from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  MessageOutlined,
  SettingOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  ReloadOutlined,
  DownloadOutlined,
  UploadOutlined,
  SearchOutlined,
  FilterOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

interface UserData {
  id: number;
  email: string;
  role: 'student' | 'admin';
  isVerified: boolean;
  isActive: boolean;
  language: string;
  createdAt: string;
  lastLogin: string;
  totalSessions: number;
  totalFiles: number;
}

interface SystemStats {
  totalUsers: number;
  activeUsers: number;
  totalSessions: number;
  totalFiles: number;
  storageUsed: number;
  storageLimit: number;
  dailyActiveUsers: number;
  weeklyActiveUsers: number;
  monthlyActiveUsers: number;
}

interface SystemLog {
  id: number;
  type: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
  user?: string;
  ip?: string;
}

const AdminPage: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<UserData[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [systemLogs, setSystemLogs] = useState<SystemLog[]>([]);
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<UserData | null>(null);
  const [userModalVisible, setUserModalVisible] = useState(false);
  const [editForm] = Form.useForm();

  // 模拟数据
  const mockStats: SystemStats = {
    totalUsers: 1245,
    activeUsers: 892,
    totalSessions: 15432,
    totalFiles: 8765,
    storageUsed: 15.6, // GB
    storageLimit: 100, // GB
    dailyActiveUsers: 234,
    weeklyActiveUsers: 567,
    monthlyActiveUsers: 892
  };

  const mockUsers: UserData[] = [
    {
      id: 1,
      email: 'student1@university.edu',
      role: 'student',
      isVerified: true,
      isActive: true,
      language: 'zh-CN',
      createdAt: '2024-01-15',
      lastLogin: '2024-01-20 14:30',
      totalSessions: 45,
      totalFiles: 12
    },
    {
      id: 2,
      email: 'admin@university.edu',
      role: 'admin',
      isVerified: true,
      isActive: true,
      language: 'en-US',
      createdAt: '2024-01-10',
      lastLogin: '2024-01-20 15:45',
      totalSessions: 120,
      totalFiles: 5
    },
    {
      id: 3,
      email: 'student2@university.edu',
      role: 'student',
      isVerified: false,
      isActive: false,
      language: 'zh-TW',
      createdAt: '2024-01-18',
      lastLogin: '2024-01-19 09:15',
      totalSessions: 8,
      totalFiles: 3
    }
  ];

  const mockLogs: SystemLog[] = [
    {
      id: 1,
      type: 'info',
      message: '用户 student1@university.edu 登录系统',
      timestamp: '2024-01-20 14:30:15',
      user: 'student1@university.edu',
      ip: '192.168.1.100'
    },
    {
      id: 2,
      type: 'warning',
      message: '存储空间使用率超过 80%',
      timestamp: '2024-01-20 14:25:00'
    },
    {
      id: 3,
      type: 'error',
      message: 'AI 服务连接失败',
      timestamp: '2024-01-20 14:20:30'
    }
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      setUsers(mockUsers);
      setSystemStats(mockStats);
      setSystemLogs(mockLogs);
    } catch (error) {
      message.error(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchText.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'active' && user.isActive) ||
      (statusFilter === 'inactive' && !user.isActive) ||
      (statusFilter === 'verified' && user.isVerified) ||
      (statusFilter === 'unverified' && !user.isVerified);
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  const userColumns: ColumnsType<UserData> = [
    {
      title: t('admin.user.email'),
      dataIndex: 'email',
      key: 'email',
      render: (email: string, record: UserData) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          <span>{email}</span>
          {!record.isVerified && <Badge status="warning" />}
        </Space>
      )
    },
    {
      title: t('admin.user.role'),
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'red' : 'blue'}>
          {t(`admin.user.roles.${role}`)}
        </Tag>
      )
    },
    {
      title: t('admin.user.status'),
      key: 'status',
      render: (_, record: UserData) => (
        <Space direction="vertical" size="small">
          <Tag color={record.isActive ? 'green' : 'default'}>
            {record.isActive ? t('admin.user.active') : t('admin.user.inactive')}
          </Tag>
          <Tag color={record.isVerified ? 'blue' : 'orange'}>
            {record.isVerified ? t('admin.user.verified') : t('admin.user.unverified')}
          </Tag>
        </Space>
      )
    },
    {
      title: t('admin.user.lastLogin'),
      dataIndex: 'lastLogin',
      key: 'lastLogin'
    },
    {
      title: t('admin.user.statistics'),
      key: 'statistics',
      render: (_, record: UserData) => (
        <Space direction="vertical" size="small">
          <Text type="secondary">{t('admin.user.sessions')}: {record.totalSessions}</Text>
          <Text type="secondary">{t('admin.user.files')}: {record.totalFiles}</Text>
        </Space>
      )
    },
    {
      title: t('admin.user.actions'),
      key: 'actions',
      render: (_, record: UserData) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => viewUser(record)}
          >
            {t('common.view')}
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => editUser(record)}
          >
            {t('common.edit')}
          </Button>
          <Popconfirm
            title={t('admin.user.deleteConfirm')}
            onConfirm={() => deleteUser(record.id)}
            okText={t('common.confirm')}
            cancelText={t('common.cancel')}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              {t('common.delete')}
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const logColumns: ColumnsType<SystemLog> = [
    {
      title: t('admin.logs.type'),
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const config = {
          info: { color: 'blue', icon: <CheckCircleOutlined /> },
          warning: { color: 'orange', icon: <ExclamationCircleOutlined /> },
          error: { color: 'red', icon: <ClockCircleOutlined /> }
        };
        return (
          <Tag color={config[type as keyof typeof config].color} icon={config[type as keyof typeof config].icon}>
            {t(`admin.logs.types.${type}`)}
          </Tag>
        );
      }
    },
    {
      title: t('admin.logs.message'),
      dataIndex: 'message',
      key: 'message'
    },
    {
      title: t('admin.logs.timestamp'),
      dataIndex: 'timestamp',
      key: 'timestamp'
    },
    {
      title: t('admin.logs.user'),
      dataIndex: 'user',
      key: 'user',
      render: (user: string) => user || '-'
    }
  ];

  const viewUser = (user: UserData) => {
    setSelectedUser(user);
    setUserModalVisible(true);
  };

  const editUser = (user: UserData) => {
    setSelectedUser(user);
    editForm.setFieldsValue(user);
    setUserModalVisible(true);
  };

  const deleteUser = async (userId: number) => {
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 500));
      setUsers(users.filter(user => user.id !== userId));
      message.success(t('admin.user.deleteSuccess'));
    } catch (error) {
      message.error(t('common.error'));
    }
  };

  const handleUserSave = async (values: any) => {
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (selectedUser) {
        setUsers(users.map(user => 
          user.id === selectedUser.id ? { ...user, ...values } : user
        ));
        message.success(t('admin.user.updateSuccess'));
      }
      
      setUserModalVisible(false);
      setSelectedUser(null);
      editForm.resetFields();
    } catch (error) {
      message.error(t('common.error'));
    }
  };

  const exportData = () => {
    message.info(t('admin.export.starting'));
    // 这里实现数据导出逻辑
  };

  const refreshData = () => {
    loadData();
  };

  // 权限检查
  if (!user || user.role !== 'admin') {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Alert
          message={t('admin.accessDenied')}
          description={t('admin.accessDeniedDesc')}
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>{t('admin.title')}</Title>
      
      <Tabs defaultActiveKey="overview">
        <TabPane tab={t('admin.tabs.overview')} key="overview">
          {/* 系统统计 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title={t('admin.stats.totalUsers')}
                  value={systemStats?.totalUsers || 0}
                  prefix={<UserOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title={t('admin.stats.activeUsers')}
                  value={systemStats?.activeUsers || 0}
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<UserOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title={t('admin.stats.totalSessions')}
                  value={systemStats?.totalSessions || 0}
                  prefix={<MessageOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title={t('admin.stats.totalFiles')}
                  value={systemStats?.totalFiles || 0}
                  prefix={<FileTextOutlined />}
                />
              </Card>
            </Col>
          </Row>

          {/* 存储使用情况 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={12}>
              <Card title={t('admin.storage.title')}>
                <Progress
                  type="circle"
                  percent={Math.round((systemStats?.storageUsed || 0) / (systemStats?.storageLimit || 1) * 100)}
                  format={(percent) => `${systemStats?.storageUsed || 0}GB / ${systemStats?.storageLimit || 0}GB`}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card title={t('admin.activity.title')}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text>{t('admin.activity.daily')}: </Text>
                    <Text strong>{systemStats?.dailyActiveUsers || 0}</Text>
                  </div>
                  <div>
                    <Text>{t('admin.activity.weekly')}: </Text>
                    <Text strong>{systemStats?.weeklyActiveUsers || 0}</Text>
                  </div>
                  <div>
                    <Text>{t('admin.activity.monthly')}: </Text>
                    <Text strong>{systemStats?.monthlyActiveUsers || 0}</Text>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab={t('admin.tabs.users')} key="users">
          {/* 用户管理 */}
          <Card
            title={t('admin.user.management')}
            extra={
              <Space>
                <Button icon={<DownloadOutlined />} onClick={exportData}>
                  {t('admin.export.users')}
                </Button>
                <Button icon={<ReloadOutlined />} onClick={refreshData}>
                  {t('common.refresh')}
                </Button>
              </Space>
            }
          >
            {/* 搜索和过滤 */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Input
                  placeholder={t('admin.user.searchPlaceholder')}
                  prefix={<SearchOutlined />}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                />
              </Col>
              <Col span={4}>
                <Select
                  style={{ width: '100%' }}
                  placeholder={t('admin.user.filterRole')}
                  value={roleFilter}
                  onChange={setRoleFilter}
                >
                  <Option value="all">{t('admin.filter.all')}</Option>
                  <Option value="student">{t('admin.user.roles.student')}</Option>
                  <Option value="admin">{t('admin.user.roles.admin')}</Option>
                </Select>
              </Col>
              <Col span={4}>
                <Select
                  style={{ width: '100%' }}
                  placeholder={t('admin.user.filterStatus')}
                  value={statusFilter}
                  onChange={setStatusFilter}
                >
                  <Option value="all">{t('admin.filter.all')}</Option>
                  <Option value="active">{t('admin.user.active')}</Option>
                  <Option value="inactive">{t('admin.user.inactive')}</Option>
                  <Option value="verified">{t('admin.user.verified')}</Option>
                  <Option value="unverified">{t('admin.user.unverified')}</Option>
                </Select>
              </Col>
            </Row>

            <Table
              columns={userColumns}
              dataSource={filteredUsers}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => t('admin.pagination.total', { total })
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab={t('admin.tabs.logs')} key="logs">
          {/* 系统日志 */}
          <Card title={t('admin.logs.title')}>
            <Table
              columns={logColumns}
              dataSource={systemLogs}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showQuickJumper: true
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab={t('admin.tabs.settings')} key="settings">
          {/* 系统设置 */}
          <Row gutter={16}>
            <Col span={12}>
              <Card title={t('admin.settings.system')}>
                <Form layout="vertical">
                  <Form.Item label={t('admin.settings.maintenanceMode')}>
                    <Switch />
                    <Paragraph type="secondary" style={{ marginTop: 8 }}>
                      {t('admin.settings.maintenanceModeDesc')}
                    </Paragraph>
                  </Form.Item>
                  
                  <Form.Item label={t('admin.settings.registrationEnabled')}>
                    <Switch defaultChecked />
                    <Paragraph type="secondary" style={{ marginTop: 8 }}>
                      {t('admin.settings.registrationEnabledDesc')}
                    </Paragraph>
                  </Form.Item>
                  
                  <Form.Item label={t('admin.settings.emailVerificationRequired')}>
                    <Switch defaultChecked />
                    <Paragraph type="secondary" style={{ marginTop: 8 }}>
                      {t('admin.settings.emailVerificationRequiredDesc')}
                    </Paragraph>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={12}>
              <Card title={t('admin.settings.ai')}>
                <Form layout="vertical">
                  <Form.Item label={t('admin.settings.aiModel')}>
                    <Select defaultValue="gpt-4" style={{ width: '100%' }}>
                      <Option value="gpt-4">GPT-4</Option>
                      <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item label={t('admin.settings.maxTokens')}>
                    <Input type="number" defaultValue="4000" />
                  </Form.Item>
                  
                  <Form.Item label={t('admin.settings.temperature')}>
                    <Input type="number" step="0.1" min="0" max="2" defaultValue="0.7" />
                  </Form.Item>
                </Form>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* 用户详情/编辑模态框 */}
      <Modal
        title={selectedUser ? t('admin.user.editTitle') : t('admin.user.viewTitle')}
        open={userModalVisible}
        onCancel={() => {
          setUserModalVisible(false);
          setSelectedUser(null);
          editForm.resetFields();
        }}
        footer={[
          <Button key="cancel" onClick={() => setUserModalVisible(false)}>
            {t('common.cancel')}
          </Button>,
          <Button key="save" type="primary" onClick={() => editForm.submit()}>
            {t('common.save')}
          </Button>
        ]}
      >
        {selectedUser && (
          <Form
            form={editForm}
            layout="vertical"
            onFinish={handleUserSave}
          >
            <Form.Item label={t('admin.user.email')} name="email">
              <Input disabled />
            </Form.Item>
            
            <Form.Item label={t('admin.user.role')} name="role">
              <Select>
                <Option value="student">{t('admin.user.roles.student')}</Option>
                <Option value="admin">{t('admin.user.roles.admin')}</Option>
              </Select>
            </Form.Item>
            
            <Form.Item label={t('admin.user.language')} name="language">
              <Select>
                <Option value="zh-CN">简体中文</Option>
                <Option value="zh-TW">繁體中文</Option>
                <Option value="en-US">English</Option>
              </Select>
            </Form.Item>
            
            <Form.Item label={t('admin.user.status')} valuePropName="checked" name="isActive">
              <Switch />
            </Form.Item>
            
            <Form.Item label={t('admin.user.verified')} valuePropName="checked" name="isVerified">
              <Switch />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
};

export default AdminPage;
