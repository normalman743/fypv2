import React, { useState, useRef, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Input, 
  Button, 
  Space, 
  Typography, 
  Modal,
  Upload,
  message,
  Badge,
  Tooltip,
  Avatar,
} from 'antd';
import {
  SendOutlined,
  PaperClipOutlined,
  UploadOutlined,
  PlusOutlined,
  DeleteOutlined,
  UserOutlined,
  RobotOutlined,
  MessageOutlined,
  BulbOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import ChatMessageComponent from '../components/chat/ChatMessage';
import SessionList from '../components/chat/SessionList';
import PageHeader from '../components/common/PageHeader';
import LoadingSpinner from '../components/common/LoadingSpinner';
import '../components/chat/ChatStyles.css';

const { Text, Title } = Typography;
const { TextArea } = Input;

interface ChatMessageType {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: string[];
}

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

const ChatPage: React.FC = () => {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: '1',
      title: '校园选课咨询',
      lastMessage: '请推荐一些计算机专业的核心课程',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      messageCount: 8,
    },
    {
      id: '2',
      title: '图书馆使用指南',
      lastMessage: '图书馆的预约系统怎么使用？',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
      messageCount: 12,
    },
  ]);
  
  const [currentSession, setCurrentSession] = useState<string>('1');
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      id: '1',
      role: 'user',
      content: '请推荐一些计算机专业的核心课程',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
    },
    {
      id: '2',
      role: 'assistant',
      content: '根据计算机专业的培养目标，我为您推荐以下核心课程：\n\n**基础课程：**\n• 数据结构与算法 - 编程基础，必修\n• 计算机组成原理 - 了解硬件架构\n• 操作系统 - 系统级编程基础\n• 计算机网络 - 网络编程必备\n\n**进阶课程：**\n• 数据库系统 - 数据管理核心技能\n• 软件工程 - 大型项目开发方法\n• 机器学习 - 当前热门方向\n• Web开发技术 - 实用性强\n\n建议按照基础→进阶的顺序选课，每学期选择2-3门专业课，避免课业负担过重。需要具体的选课建议吗？',
      timestamp: new Date(Date.now() - 1000 * 60 * 25),
    },
  ]);
  
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const newMessage: ChatMessageType = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsLoading(true);

    // 模拟AI回复
    setTimeout(() => {
      const aiMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '这是一个模拟的AI回复。在实际应用中，这里会连接到OpenAI API或其他AI服务来生成真实的回复。',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: '新对话',
      lastMessage: '',
      timestamp: new Date(),
      messageCount: 0,
    };
    
    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession.id);
    setMessages([]);
  };

  const handleDeleteSession = (sessionId: string) => {
    Modal.confirm({
      title: '删除对话',
      content: '确定要删除这个对话吗？此操作不可恢复。',
      onOk() {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (currentSession === sessionId) {
          const remaining = sessions.filter(s => s.id !== sessionId);
          setCurrentSession(remaining.length > 0 ? remaining[0].id : '');
          setMessages([]);
        }
      },
    });
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
  };

  return (
    <div style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
      <PageHeader
        title="AI智能助手"
        subtitle="校园生活问答助手，为您提供全方位的校园信息咨询服务"
        icon={<MessageOutlined />}
        gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        actions={[
          {
            text: '新对话',
            icon: <PlusOutlined />,
            onClick: handleNewSession,
            type: 'primary'
          }
        ]}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
          {/* 左侧会话列表 */}
          <Col xs={24} md={8} lg={6}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Card 
                className="session-card"
                style={{ 
                  height: 'calc(100vh - 200px)',
                  borderRadius: '12px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  border: '1px solid rgba(102, 126, 234, 0.1)'
                }}
                bodyStyle={{ padding: 0, height: 'calc(100% - 57px)', overflow: 'hidden' }}
              >
                <div style={{ 
                  padding: '16px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white'
                }}>
                  <Space>
                    <MessageOutlined />
                    <Typography.Text strong style={{ color: 'white' }}>
                      对话历史
                    </Typography.Text>
                    <Badge count={sessions.length} style={{ backgroundColor: 'rgba(255,255,255,0.3)' }} />
                  </Space>
                </div>
                
                <SessionList
                  sessions={sessions}
                  currentSession={currentSession}
                  onSessionSelect={setCurrentSession}
                  onSessionDelete={handleDeleteSession}
                  onNewSession={handleNewSession}
                  title="对话历史"
                />
              </Card>
            </motion.div>
          </Col>

          {/* 右侧聊天区域 */}
          <Col xs={24} md={16} lg={18}>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card 
                className="chat-card"
                style={{ 
                  height: 'calc(100vh - 200px)',
                  borderRadius: '12px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  border: '1px solid rgba(102, 126, 234, 0.1)',
                  display: 'flex',
                  flexDirection: 'column'
                }}
                bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}
              >
                {/* 聊天头部 */}
                <div style={{ 
                  padding: '16px 24px', 
                  borderBottom: '1px solid #f0f0f0',
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <Typography.Title level={4} style={{ margin: 0, color: '#667eea' }}>
                        {sessions.find(s => s.id === currentSession)?.title || '校园AI助手'}
                      </Typography.Title>
                      <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                        <BulbOutlined style={{ marginRight: '4px' }} />
                        智能解答您的校园生活问题
                      </Typography.Text>
                    </div>
                    <Space>
                      <Tooltip title="上传文档">
                        <Button 
                          icon={<PaperClipOutlined />} 
                          onClick={() => setUploadModalVisible(true)}
                          style={{ borderColor: '#667eea', color: '#667eea' }}
                        >
                          上传文档
                        </Button>
                      </Tooltip>
                    </Space>
                  </div>
                </div>

                {/* 消息列表 */}
                <div style={{ 
                  flex: 1, 
                  padding: '16px 24px', 
                  overflow: 'auto',
                  background: '#fff'
                }}>
                  {messages.length === 0 ? (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.5 }}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100%',
                        textAlign: 'center'
                      }}
                    >
                      <div style={{
                        width: '80px',
                        height: '80px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: '24px'
                      }}>
                        <MessageOutlined style={{ fontSize: '32px', color: 'white' }} />
                      </div>
                      <Typography.Title level={3} style={{ color: '#667eea', marginBottom: '8px' }}>
                        开始新对话
                      </Typography.Title>
                      <Typography.Text type="secondary" style={{ marginBottom: '24px' }}>
                        选择下方问题开始，或直接输入您的问题
                      </Typography.Text>
                    </motion.div>
                  ) : (
                    messages.map((msg, index) => (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                      >
                        <ChatMessageComponent message={msg} />
                      </motion.div>
                    ))
                  )}
                  
                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                        <Avatar 
                          icon={<RobotOutlined />}
                          style={{ backgroundColor: '#52c41a', marginRight: '8px' }}
                        />
                        <div style={{
                          background: '#f6f6f6',
                          padding: '12px 16px',
                          borderRadius: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}>
                          <LoadingSpinner size="small" />
                          <Typography.Text type="secondary" className="typing-animation">
                            AI正在思考中...
                          </Typography.Text>
                        </div>
                      </div>
                    </motion.div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>

                {/* 输入区域 */}
                <div style={{ 
                  padding: '16px 24px', 
                  borderTop: '1px solid #f0f0f0',
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%)'
                }}>
                  {/* 常见问题快捷按钮 */}
                  {messages.length === 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.3 }}
                      style={{ marginBottom: '16px' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                        <QuestionCircleOutlined style={{ color: '#667eea', marginRight: '8px' }} />
                        <Typography.Text type="secondary">
                          热门问题推荐：
                        </Typography.Text>
                      </div>
                      <Space wrap>
                        {[
                          '图书馆的开放时间是什么？',
                          '如何申请宿舍？',
                          '学校有哪些社团可以加入？',
                          '选课系统怎么使用？',
                          '食堂都有什么好吃的？'
                        ].map((question, index) => (
                          <motion.div
                            key={question}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.3, delay: 0.4 + index * 0.1 }}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            <Button 
                              size="small" 
                              onClick={() => setInputValue(question)}
                              style={{
                                borderColor: '#667eea',
                                color: '#667eea',
                                borderRadius: '16px'
                              }}
                              className="quick-question-btn"
                            >
                              {question.replace('？', '').replace('?', '')}
                            </Button>
                          </motion.div>
                        ))}
                      </Space>
                    </motion.div>
                  )}
                  
                  <Space.Compact style={{ width: '100%' }}>
                    <Input.TextArea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="请输入您关于校园生活的问题..."
                      autoSize={{ minRows: 1, maxRows: 4 }}
                      onPressEnter={(e) => {
                        if (!e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      style={{ 
                        resize: 'none',
                        borderRadius: '8px 0 0 8px',
                        borderColor: '#667eea'
                      }}
                      className="chat-input"
                    />
                    <Button 
                      type="primary" 
                      icon={<SendOutlined />}
                      onClick={handleSendMessage}
                      loading={isLoading}
                      disabled={!inputValue.trim()}
                      style={{ 
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 'none',
                        borderRadius: '0 8px 8px 0',
                        height: 'auto'
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
      </motion.div>

      {/* 文件上传模态框 */}
      <Modal
        title={
          <Space>
            <UploadOutlined style={{ color: '#667eea' }} />
            <span>上传文档</span>
          </Space>
        }
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        style={{ borderRadius: '12px' }}
      >
        <Upload.Dragger
          multiple
          beforeUpload={() => false}
          onChange={(info) => {
            message.success(`${info.file.name} 文件上传成功`);
            setUploadModalVisible(false);
          }}
          style={{ borderColor: '#667eea', borderRadius: '8px' }}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ color: '#667eea' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 PDF、DOC、DOCX、TXT 格式，文件大小不超过 10MB
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  );
};

export default ChatPage;
