import React, { useState, useRef, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Input, 
  Button, 
  List,
  Typography, 
  Avatar,
  Space,
} from 'antd';
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  MessageOutlined,
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import ChatMessageComponent from '../components/chat/ChatMessage';
import PageHeader from '../components/common/PageHeader';
import LoadingSpinner from '../components/common/LoadingSpinner';
import '../components/chat/ChatStyles.css';

const { Text, Title } = Typography;
const { TextArea } = Input;

// 简化的数据接口
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatSession {
  id: string;
  title: string;
  messageCount: number;
  lastUpdated: Date;
}

const ChatPage: React.FC = () => {
  const { t } = useTranslation();
  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: '1',
      title: '宿舍网络问题咨询',
      messageCount: 5,
      lastUpdated: new Date(Date.now() - 86400000)
    },
    {
      id: '2', 
      title: '图书馆借阅流程',
      messageCount: 3,
      lastUpdated: new Date(Date.now() - 172800000)
    },
    {
      id: '3',
      title: '食堂用餐时间',
      messageCount: 2,
      lastUpdated: new Date(Date.now() - 259200000)
    }
  ]);
  const [selectedSession, setSelectedSession] = useState<string>('1');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionSearchTerm, setSessionSearchTerm] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 初始化当前会话的消息
  useEffect(() => {
    if (selectedSession === '1') {
      setMessages([
        {
          id: '1',
          role: 'user',
          content: '宿舍的网络连接有问题，总是断断续续的，该怎么办？',
          timestamp: new Date(Date.now() - 3600000)
        },
        {
          id: '2',
          role: 'assistant',
          content: '关于宿舍网络问题，建议您采取以下步骤：\n\n1. 首先检查网线连接是否松动\n2. 重启路由器和电脑网络适配器\n3. 如果问题依然存在，可以联系宿舍管理员或网络中心\n4. 网络中心电话：123-456-7890\n5. 工作时间：周一至周五 9:00-17:00\n\n您也可以尝试使用手机热点作为临时解决方案。',
          timestamp: new Date(Date.now() - 3500000)
        }
      ]);
    } else {
      setMessages([]);
    }
  }, [selectedSession]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!currentMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: currentMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    // 模拟AI响应
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `感谢您的提问："${currentMessage}"。我正在为您查询相关的校园生活信息，请稍等片刻。\n\n这是一个模拟回复，实际的AI助手将会根据您的问题提供详细的校园生活指导和建议。`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: '新对话',
      messageCount: 0,
      lastUpdated: new Date()
    };
    setSessions(prev => [newSession, ...prev]);
    setSelectedSession(newSession.id);
    setMessages([]);
  };

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(sessionSearchTerm.toLowerCase())
  );

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '24px 0'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
        <PageHeader
          title={t('navigation.campusChat')}
          subtitle="校园生活AI助手 - 为您解答校园生活中的各种问题"
        />

        <Row gutter={[24, 24]}>
          {/* 左侧 - 对话历史 */}
          <Col xs={24} md={8}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Card
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MessageOutlined style={{ color: '#667eea' }} />
                    对话历史
                  </div>
                }
                extra={
                  <Button
                    type="primary"
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={createNewSession}
                  >
                    新对话
                  </Button>
                }
                style={{
                  borderRadius: '12px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                  border: 'none'
                }}
              >
                <Input.Search
                  placeholder="搜索对话..."
                  style={{ marginBottom: 16 }}
                  onChange={(e) => setSessionSearchTerm(e.target.value)}
                  prefix={<SearchOutlined />}
                />
                <List
                  size="small"
                  dataSource={filteredSessions}
                  renderItem={(session) => (
                    <List.Item
                      style={{
                        cursor: 'pointer',
                        borderRadius: '8px',
                        marginBottom: '8px',
                        padding: '12px',
                        backgroundColor: selectedSession === session.id ? '#f0f7ff' : 'transparent',
                        border: selectedSession === session.id ? '2px solid #667eea' : '1px solid #f0f0f0'
                      }}
                      onClick={() => setSelectedSession(session.id)}
                      actions={[
                        <Button
                          type="text"
                          size="small"
                          icon={<DeleteOutlined />}
                          danger
                          onClick={(e) => {
                            e.stopPropagation();
                            setSessions(prev => prev.filter(s => s.id !== session.id));
                          }}
                        />
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Text strong style={{ fontSize: '14px' }}>
                            {session.title}
                          </Text>
                        }
                        description={
                          <Space direction="vertical" size={0}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {session.messageCount} 条消息
                            </Text>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {session.lastUpdated.toLocaleDateString()}
                            </Text>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </motion.div>
          </Col>

          {/* 右侧 - 聊天界面 */}
          <Col xs={24} md={16}>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <RobotOutlined style={{ color: '#667eea' }} />
                    AI助手对话
                  </div>
                }
                style={{
                  borderRadius: '12px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                  border: 'none',
                  height: '600px',
                  display: 'flex',
                  flexDirection: 'column'
                }}
                bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}
              >
                {/* 聊天消息区域 */}
                <div
                  style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '16px',
                    background: '#fafafa',
                    borderRadius: '8px 8px 0 0'
                  }}
                >
                  {messages.length === 0 ? (
                    <div style={{
                      textAlign: 'center',
                      paddingTop: '100px',
                      color: '#999'
                    }}>
                      <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                      <div>开始与AI助手对话吧！</div>
                      <div style={{ fontSize: '12px', marginTop: '8px' }}>
                        您可以询问关于宿舍、食堂、图书馆、课程等校园生活问题
                      </div>
                    </div>
                  ) : (
                    <>
                      {messages.map((message) => (
                        <ChatMessageComponent
                          key={message.id}
                          message={message}
                        />
                      ))}
                      {isLoading && (
                        <div style={{ textAlign: 'center', padding: '20px' }}>
                          <LoadingSpinner size="small" />
                          <Text type="secondary" style={{ marginLeft: '8px' }}>
                            AI正在思考中...
                          </Text>
                        </div>
                      )}
                    </>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* 输入区域 */}
                <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0' }}>
                  <Space.Compact style={{ width: '100%' }}>
                    <TextArea
                      value={currentMessage}
                      onChange={(e) => setCurrentMessage(e.target.value)}
                      onPressEnter={handleKeyPress}
                      placeholder="输入您的校园生活问题..."
                      autoSize={{ minRows: 1, maxRows: 3 }}
                      style={{ resize: 'none' }}
                    />
                    <Button
                      type="primary"
                      icon={<SendOutlined />}
                      onClick={handleSendMessage}
                      disabled={!currentMessage.trim() || isLoading}
                      style={{
                        height: 'auto',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 'none'
                      }}
                    >
                      发送
                    </Button>
                  </Space.Compact>
                </div>
              </Card>
            </motion.div>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default ChatPage;
