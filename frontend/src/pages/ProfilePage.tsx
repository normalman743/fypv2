import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Upload,
  Avatar,
  Select,
  Switch,
  message,
  Row,
  Col,
  Divider,
  Typography,
  Space,
  Modal,
  Tabs,
  List,
  Tag,
  Progress,
  Statistic,
  Timeline,
  Alert,
  Badge,
  Tooltip
} from 'antd';
import {
  UserOutlined,
  UploadOutlined,
  EditOutlined,
  SaveOutlined,
  LockOutlined,
  BellOutlined,
  HistoryOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import type { UploadProps } from 'antd';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Password } = Input;
const { TabPane } = Tabs;

interface ProfileData {
  email: string;
  name?: string;
  avatar?: string;
  language: string;
  timezone: string;
  bio?: string;
  university?: string;
  major?: string;
  studyYear?: string;
}

interface SecuritySettings {
  twoFactorEnabled: boolean;
  emailNotifications: boolean;
  sessionTimeout: number;
  loginAlerts: boolean;
}

interface ActivityLog {
  id: number;
  action: string;
  timestamp: string;
  ip: string;
  device: string;
  location: string;
}

interface StudyStats {
  totalSessions: number;
  totalTime: number; // minutes
  totalFiles: number;
  averageScore: number;
  completedQuizzes: number;
  studyStreak: number;
  favoriteTopics: string[];
}

const ProfilePage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [securityForm] = Form.useForm();
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [deleteAccountModalVisible, setDeleteAccountModalVisible] = useState(false);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [studyStats, setStudyStats] = useState<StudyStats | null>(null);

  // 模拟数据
  const mockProfile: ProfileData = {
    email: user?.email || 'student@university.edu',
    name: '张三',
    language: user?.language || 'zh-CN',
    timezone: 'Asia/Shanghai',
    bio: '我是一名计算机科学专业的学生，热衷于人工智能和机器学习。',
    university: '清华大学',
    major: '计算机科学与技术',
    studyYear: '大三'
  };

  const mockSecurity: SecuritySettings = {
    twoFactorEnabled: false,
    emailNotifications: true,
    sessionTimeout: 30,
    loginAlerts: true
  };

  const mockActivityLogs: ActivityLog[] = [
    {
      id: 1,
      action: '登录系统',
      timestamp: '2024-01-20 14:30:15',
      ip: '192.168.1.100',
      device: 'Chrome 浏览器',
      location: '北京市'
    },
    {
      id: 2,
      action: '修改个人资料',
      timestamp: '2024-01-20 10:15:30',
      ip: '192.168.1.100',
      device: 'Chrome 浏览器',
      location: '北京市'
    },
    {
      id: 3,
      action: '上传文件',
      timestamp: '2024-01-19 16:45:20',
      ip: '192.168.1.101',
      device: 'Safari 浏览器',
      location: '上海市'
    }
  ];

  const mockStudyStats: StudyStats = {
    totalSessions: 156,
    totalTime: 4320, // 72 hours
    totalFiles: 23,
    averageScore: 87.5,
    completedQuizzes: 45,
    studyStreak: 12,
    favoriteTopics: ['人工智能', '数据结构', '算法设计', '机器学习', '深度学习']
  };

  const [profileData, setProfileData] = useState<ProfileData>(mockProfile);
  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>(mockSecurity);

  useEffect(() => {
    loadProfileData();
    loadActivityLogs();
    loadStudyStats();
  }, []);

  useEffect(() => {
    profileForm.setFieldsValue(profileData);
    securityForm.setFieldsValue(securitySettings);
  }, [profileData, securitySettings, profileForm, securityForm]);

  const loadProfileData = async () => {
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 500));
      setProfileData(mockProfile);
      setSecuritySettings(mockSecurity);
    } catch (error) {
      message.error(t('common.error'));
    }
  };

  const loadActivityLogs = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setActivityLogs(mockActivityLogs);
    } catch (error) {
      message.error(t('common.error'));
    }
  };

  const loadStudyStats = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setStudyStats(mockStudyStats);
    } catch (error) {
      message.error(t('common.error'));
    }
  };

  const handleProfileSave = async (values: ProfileData) => {
    setLoading(true);
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      setProfileData({ ...profileData, ...values });
      
      // 如果语言发生变化，更新 i18n
      if (values.language !== profileData.language) {
        i18n.changeLanguage(values.language);
      }
      
      setEditMode(false);
      message.success(t('profile.updateSuccess'));
    } catch (error) {
      message.error(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: any) => {
    setLoading(true);
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success(t('profile.password.changeSuccess'));
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error) {
      message.error(t('profile.password.changeError'));
    } finally {
      setLoading(false);
    }
  };

  const handleSecuritySave = async (values: SecuritySettings) => {
    setLoading(true);
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSecuritySettings(values);
      message.success(t('profile.security.updateSuccess'));
    } catch (error) {
      message.error(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options;
    
    try {
      // 模拟上传
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 创建预览 URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfileData({
          ...profileData,
          avatar: e.target?.result as string
        });
      };
      reader.readAsDataURL(file as File);
      
      message.success(t('profile.avatar.uploadSuccess'));
      onSuccess?.(file);
    } catch (error) {
      message.error(t('profile.avatar.uploadError'));
      onError?.(error as Error);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success(t('profile.account.deleteSuccess'));
      // 这里应该跳转到登录页面或首页
    } catch (error) {
      message.error(t('common.error'));
    }
  };

  const exportData = () => {
    message.info(t('profile.data.exportStarted'));
    // 实现数据导出逻辑
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}小时${mins}分钟`;
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>{t('profile.title')}</Title>
      
      <Tabs defaultActiveKey="profile">
        <TabPane tab={t('profile.tabs.profile')} key="profile">
          <Row gutter={24}>
            <Col span={8}>
              <Card>
                <div style={{ textAlign: 'center' }}>
                  <Avatar
                    size={120}
                    src={profileData.avatar}
                    icon={<UserOutlined />}
                    style={{ marginBottom: 16 }}
                  />
                  <div>
                    <Upload
                      showUploadList={false}
                      customRequest={handleAvatarUpload}
                      accept="image/*"
                    >
                      <Button icon={<UploadOutlined />}>
                        {t('profile.avatar.change')}
                      </Button>
                    </Upload>
                  </div>
                  <Title level={4} style={{ marginTop: 16 }}>
                    {profileData.name}
                  </Title>
                  <Text type="secondary">{profileData.email}</Text>
                  <div style={{ marginTop: 16 }}>
                    <Tag color="blue">{user?.role === 'admin' ? t('profile.role.admin') : t('profile.role.student')}</Tag>
                    {user?.isVerified && <Tag color="green">{t('profile.verified')}</Tag>}
                  </div>
                </div>
              </Card>
            </Col>
            
            <Col span={16}>
              <Card
                title={t('profile.info.title')}
                extra={
                  <Button
                    type={editMode ? 'primary' : 'default'}
                    icon={editMode ? <SaveOutlined /> : <EditOutlined />}
                    onClick={() => {
                      if (editMode) {
                        profileForm.submit();
                      } else {
                        setEditMode(true);
                      }
                    }}
                    loading={loading}
                  >
                    {editMode ? t('common.save') : t('common.edit')}
                  </Button>
                }
              >
                <Form
                  form={profileForm}
                  layout="vertical"
                  onFinish={handleProfileSave}
                  disabled={!editMode}
                >
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label={t('profile.form.name')}
                        name="name"
                        rules={[{ required: true, message: t('profile.form.nameRequired') }]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label={t('profile.form.email')}
                        name="email"
                      >
                        <Input disabled />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label={t('profile.form.language')}
                        name="language"
                      >
                        <Select>
                          <Option value="zh-CN">简体中文</Option>
                          <Option value="zh-TW">繁體中文</Option>
                          <Option value="en-US">English</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label={t('profile.form.timezone')}
                        name="timezone"
                      >
                        <Select>
                          <Option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</Option>
                          <Option value="America/New_York">America/New_York (UTC-5)</Option>
                          <Option value="Europe/London">Europe/London (UTC+0)</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label={t('profile.form.university')}
                        name="university"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label={t('profile.form.major')}
                        name="major"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Form.Item
                    label={t('profile.form.studyYear')}
                    name="studyYear"
                  >
                    <Select>
                      <Option value="大一">{t('profile.form.year1')}</Option>
                      <Option value="大二">{t('profile.form.year2')}</Option>
                      <Option value="大三">{t('profile.form.year3')}</Option>
                      <Option value="大四">{t('profile.form.year4')}</Option>
                      <Option value="研究生">{t('profile.form.graduate')}</Option>
                      <Option value="博士生">{t('profile.form.phd')}</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item
                    label={t('profile.form.bio')}
                    name="bio"
                  >
                    <Input.TextArea rows={4} />
                  </Form.Item>
                </Form>
              </Card>
            </Col>
          </Row>
        </TabPane>
        
        <TabPane tab={t('profile.tabs.security')} key="security">
          <Row gutter={24}>
            <Col span={12}>
              <Card title={t('profile.security.title')}>
                <Form
                  form={securityForm}
                  layout="vertical"
                  onFinish={handleSecuritySave}
                >
                  <Form.Item
                    label={t('profile.security.twoFactor')}
                    name="twoFactorEnabled"
                    valuePropName="checked"
                    extra={t('profile.security.twoFactorDesc')}
                  >
                    <Switch />
                  </Form.Item>
                  
                  <Form.Item
                    label={t('profile.security.emailNotifications')}
                    name="emailNotifications"
                    valuePropName="checked"
                    extra={t('profile.security.emailNotificationsDesc')}
                  >
                    <Switch />
                  </Form.Item>
                  
                  <Form.Item
                    label={t('profile.security.loginAlerts')}
                    name="loginAlerts"
                    valuePropName="checked"
                    extra={t('profile.security.loginAlertsDesc')}
                  >
                    <Switch />
                  </Form.Item>
                  
                  <Form.Item
                    label={t('profile.security.sessionTimeout')}
                    name="sessionTimeout"
                    extra={t('profile.security.sessionTimeoutDesc')}
                  >
                    <Select>
                      <Option value={15}>15 {t('profile.security.minutes')}</Option>
                      <Option value={30}>30 {t('profile.security.minutes')}</Option>
                      <Option value={60}>1 {t('profile.security.hour')}</Option>
                      <Option value={120}>2 {t('profile.security.hours')}</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item>
                    <Space>
                      <Button type="primary" htmlType="submit" loading={loading}>
                        {t('common.save')}
                      </Button>
                      <Button
                        icon={<LockOutlined />}
                        onClick={() => setPasswordModalVisible(true)}
                      >
                        {t('profile.password.change')}
                      </Button>
                    </Space>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title={t('profile.activity.recent')}>
                <List
                  size="small"
                  dataSource={activityLogs.slice(0, 5)}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        title={item.action}
                        description={
                          <Space direction="vertical" size={0}>
                            <Text type="secondary">{item.timestamp}</Text>
                            <Text type="secondary">{item.device} • {item.location}</Text>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
                <Button type="link" style={{ padding: 0, marginTop: 8 }}>
                  {t('profile.activity.viewAll')}
                </Button>
              </Card>
            </Col>
          </Row>
        </TabPane>
        
        <TabPane tab={t('profile.tabs.stats')} key="stats">
          {studyStats && (
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title={t('profile.stats.totalSessions')}
                    value={studyStats.totalSessions}
                    prefix={<HistoryOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title={t('profile.stats.totalTime')}
                    value={formatTime(studyStats.totalTime)}
                    prefix={<CloseCircleOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title={t('profile.stats.averageScore')}
                    value={studyStats.averageScore}
                    suffix="%"
                    valueStyle={{ color: '#3f8600' }}
                    prefix={<CheckCircleOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title={t('profile.stats.studyStreak')}
                    value={studyStats.studyStreak}
                    suffix={t('profile.stats.days')}
                    valueStyle={{ color: '#ff4d4f' }}
                    prefix={<InfoCircleOutlined />}
                  />
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title={t('profile.stats.progress')}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text>{t('profile.stats.completedQuizzes')}</Text>
                      <Progress percent={Math.round(studyStats.completedQuizzes / 50 * 100)} />
                    </div>
                    <div>
                      <Text>{t('profile.stats.filesUploaded')}</Text>
                      <Progress percent={Math.round(studyStats.totalFiles / 30 * 100)} />
                    </div>
                  </Space>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title={t('profile.stats.favoriteTopics')}>
                  <Space wrap>
                    {studyStats.favoriteTopics.map((topic, index) => (
                      <Tag key={index} color="blue">{topic}</Tag>
                    ))}
                  </Space>
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>
        
        <TabPane tab={t('profile.tabs.data')} key="data">
          <Row gutter={24}>
            <Col span={12}>
              <Card title={t('profile.data.export')}>
                <Paragraph>
                  {t('profile.data.exportDesc')}
                </Paragraph>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={exportData}
                >
                  {t('profile.data.exportButton')}
                </Button>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title={t('profile.data.delete')}>
                <Alert
                  message={t('profile.data.deleteWarning')}
                  type="warning"
                  style={{ marginBottom: 16 }}
                />
                <Paragraph>
                  {t('profile.data.deleteDesc')}
                </Paragraph>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => setDeleteAccountModalVisible(true)}
                >
                  {t('profile.data.deleteButton')}
                </Button>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
      
      {/* 修改密码模态框 */}
      <Modal
        title={t('profile.password.change')}
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={[
          <Button key="cancel" onClick={() => setPasswordModalVisible(false)}>
            {t('common.cancel')}
          </Button>,
          <Button key="submit" type="primary" onClick={() => passwordForm.submit()} loading={loading}>
            {t('common.confirm')}
          </Button>
        ]}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <Form.Item
            label={t('profile.password.current')}
            name="currentPassword"
            rules={[{ required: true, message: t('profile.password.currentRequired') }]}
          >
            <Password />
          </Form.Item>
          
          <Form.Item
            label={t('profile.password.new')}
            name="newPassword"
            rules={[
              { required: true, message: t('profile.password.newRequired') },
              { min: 6, message: t('profile.password.minLength') }
            ]}
          >
            <Password />
          </Form.Item>
          
          <Form.Item
            label={t('profile.password.confirm')}
            name="confirmPassword"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: t('profile.password.confirmRequired') },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error(t('profile.password.mismatch')));
                }
              })
            ]}
          >
            <Password />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 删除账户确认模态框 */}
      <Modal
        title={t('profile.account.deleteTitle')}
        open={deleteAccountModalVisible}
        onCancel={() => setDeleteAccountModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setDeleteAccountModalVisible(false)}>
            {t('common.cancel')}
          </Button>,
          <Button key="delete" type="primary" danger onClick={handleDeleteAccount}>
            {t('profile.account.deleteConfirm')}
          </Button>
        ]}
      >
        <Alert
          message={t('profile.account.deleteWarningTitle')}
          description={t('profile.account.deleteWarningDesc')}
          type="error"
          style={{ marginBottom: 16 }}
        />
        <Paragraph>
          {t('profile.account.deleteConfirmText')}
        </Paragraph>
      </Modal>
    </div>
  );
};

export default ProfilePage;
