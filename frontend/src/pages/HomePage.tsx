import React from 'react';
import { Row, Col, Card, Typography, Button, Space, Statistic, Progress } from 'antd';
import {
  MessageOutlined,
  FileTextOutlined,
  BookOutlined,
  RocketOutlined,
  UserOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  CalendarOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import StatCard from '../components/common/StatCard';
import QuickActionCard from '../components/common/QuickActionCard';
import PageHeader from '../components/common/PageHeader';

const { Title, Paragraph, Text } = Typography;

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useAuth();

  // 模拟统计数据
  const mockStats = {
    totalChats: 12,
    totalFiles: 8,
    studyHours: 24,
    questionsGenerated: 36,
  };

  const quickActions = [
    {
      title: '校园生活询问',
      description: '询问关于校园生活、学习、活动等各种问题',
      icon: <MessageOutlined />,
      action: () => navigate('/chat'),
      color: '#1890ff',
      buttonText: '开始聊天',
      stats: {
        label: '今日咨询',
        value: mockStats.totalChats
      },
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    {
      title: '学习助手',
      description: '文件管理、学习计划、练习测验一站式学习工具',
      icon: <BookOutlined />,
      action: () => navigate('/study'),
      color: '#52c41a',
      buttonText: '进入学习',
      stats: {
        label: '学习时长',
        value: `${mockStats.studyHours}h`
      },
      gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)'
    },
    {
      title: '文件管理',
      description: '上传、管理和分享您的学习资料',
      icon: <FileTextOutlined />,
      action: () => navigate('/files'),
      color: '#fa8c16',
      buttonText: '管理文件',
      stats: {
        label: '文件总数',
        value: mockStats.totalFiles
      },
      gradient: 'linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%)'
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      {/* 优化的页面头部 */}
      <PageHeader
        title={`欢迎回来, ${user?.email?.split('@')[0]}!`}
        subtitle="您的智能校园助手已准备就绪，随时为您提供校园生活和学习支持。"
        icon={<UserOutlined />}
        gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        actions={[
          {
            text: '查看通知',
            icon: <BellOutlined />,
            onClick: () => navigate('/notifications'),
            type: 'default'
          }
        ]}
      />

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
        <Col xs={12} sm={6}>
          <StatCard
            title="校园咨询"
            value={mockStats.totalChats}
            prefix={<MessageOutlined />}
            color="#1890ff"
            trend={{
              value: 12.5,
              isPositive: true
            }}
            description="本周新增咨询"
            onClick={() => navigate('/chat')}
          />
        </Col>
        <Col xs={12} sm={6}>
          <StatCard
            title="学习文件"
            value={mockStats.totalFiles}
            prefix={<FileTextOutlined />}
            color="#52c41a"
            trend={{
              value: 8.3,
              isPositive: true
            }}
            description="最近上传文件"
            onClick={() => navigate('/files')}
          />
        </Col>
        <Col xs={12} sm={6}>
          <StatCard
            title="学习时长"
            value={mockStats.studyHours}
            suffix="小时"
            prefix={<ClockCircleOutlined />}
            color="#faad14"
            trend={{
              value: 15.2,
              isPositive: true
            }}
            description="本周学习总时长"
          />
        </Col>
        <Col xs={12} sm={6}>
          <StatCard
            title="完成测验"
            value={mockStats.questionsGenerated}
            prefix={<TrophyOutlined />}
            color="#722ed1"
            trend={{
              value: 5.7,
              isPositive: false
            }}
            description="本月完成数量"
          />
        </Col>
      </Row>

      {/* 快速操作 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.6 }}
      >
        <Row gutter={[24, 24]} style={{ marginBottom: '32px' }}>
          <Col span={24}>
            <Title level={3}>
              <RocketOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
              快速开始
            </Title>
          </Col>
          {quickActions.map((action, index) => (
            <Col xs={24} md={8} key={index}>
              <QuickActionCard
                title={action.title}
                description={action.description}
                icon={action.icon}
                color={action.color}
                action={action.action}
                buttonText={action.buttonText}
                gradient={action.gradient}
                stats={action.stats}
                badge={index === 0 ? 'NEW' : undefined}
              />
            </Col>
          ))}
        </Row>
      </motion.div>

      {/* 学习进度和最近活动 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            <Card 
              title={
                <Space>
                  <CalendarOutlined style={{ color: '#1890ff' }} />
                  本周学习进度
                </Space>
              }
              extra={<Text type="secondary">68%</Text>}
              style={{
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                color: 'white'
              }}
              headStyle={{ 
                color: 'white', 
                borderBottom: '1px solid rgba(255,255,255,0.2)' 
              }}
              bodyStyle={{ color: 'white' }}
            >
              <Progress 
                percent={68} 
                status="active" 
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                trailColor="rgba(255,255,255,0.3)"
              />
              <div style={{ marginTop: '16px' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text style={{ color: 'rgba(255,255,255,0.9)' }}>完成对话</Text>
                    <Text strong style={{ color: 'white' }}>12/20</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text style={{ color: 'rgba(255,255,255,0.9)' }}>学习时长</Text>
                    <Text strong style={{ color: 'white' }}>24/35 小时</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text style={{ color: 'rgba(255,255,255,0.9)' }}>练习题目</Text>
                    <Text strong style={{ color: 'white' }}>36/50</Text>
                  </div>
                </Space>
              </div>
            </Card>
          </motion.div>
        </Col>

        <Col xs={24} lg={12}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            <Card 
              title={
                <Space>
                  <BellOutlined style={{ color: '#52c41a' }} />
                  最近活动
                </Space>
              }
              extra={<Button type="link" style={{ color: '#52c41a' }}>查看全部</Button>}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <motion.div 
                  style={{ display: 'flex', alignItems: 'center' }}
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                >
                  <div style={{
                    background: '#1890ff15',
                    borderRadius: '50%',
                    width: '40px',
                    height: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginRight: '12px'
                  }}>
                    <MessageOutlined style={{ color: '#1890ff' }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <Text>完成了关于"微积分"的对话</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>2小时前</Text>
                  </div>
                </motion.div>

                <motion.div 
                  style={{ display: 'flex', alignItems: 'center' }}
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                >
                  <div style={{
                    background: '#52c41a15',
                    borderRadius: '50%',
                    width: '40px',
                    height: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginRight: '12px'
                  }}>
                    <FileTextOutlined style={{ color: '#52c41a' }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <Text>上传了"线性代数笔记.pdf"</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>4小时前</Text>
                  </div>
                </motion.div>

                <motion.div 
                  style={{ display: 'flex', alignItems: 'center' }}
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                >
                  <div style={{
                    background: '#faad1415',
                    borderRadius: '50%',
                    width: '40px',
                    height: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginRight: '12px'
                  }}>
                    <BookOutlined style={{ color: '#faad14' }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <Text>生成了10道数学练习题</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>1天前</Text>
                  </div>
                </motion.div>
              </Space>
            </Card>
          </motion.div>
        </Col>
      </Row>
    </motion.div>
  );
};

export default HomePage;
