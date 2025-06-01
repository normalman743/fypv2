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
  Select,
  Dropdown,
  MenuProps,
  Upload,
  message,
} from 'antd';
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  MessageOutlined,
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
  HomeOutlined,
  BookOutlined,
  DashboardOutlined,
  LogoutOutlined,
  SettingOutlined,
  GlobalOutlined,
  PaperClipOutlined,
  FileTextOutlined,
  FileImageOutlined,
  DeleteOutlined as DeleteFileOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import ChatMessageComponent from '../components/chat/ChatMessage';
import WelcomeInterface from '../components/chat/WelcomeInterface';
import PageHeader from '../components/common/PageHeader';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useAuth } from '../context/AuthContext';
import '../components/chat/ChatStyles.css';

const { Text, Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// 消息数据接口 - 支持树状结构
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  parentId?: string; // 父消息ID，用于构建消息树
  children?: string[]; // 子消息ID列表
  isEditing?: boolean; // 是否正在编辑状态
  attachments?: FileAttachment[]; // 附件
}

interface FileAttachment {
  id: string;
  name: string;
  type: 'image' | 'text';
  size: number;
  url: string;
}

interface MessageBranch {
  messageId: string;
  branchIndex: number; // 当前选择的分支索引
  totalBranches: number; // 总分支数
}

interface ChatSession {
  id: string;
  title: string;
  messageCount: number;
  lastUpdated: Date;
  messageTree: { [key: string]: ChatMessage }; // 消息树结构
  currentPath: string[]; // 当前对话路径
}

const ChatPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: '1',
      title: '宿舍网络问题咨询',
      messageCount: 5,
      lastUpdated: new Date(Date.now() - 86400000),
      messageTree: {},
      currentPath: []
    },
    {
      id: '2', 
      title: '图书馆借阅流程',
      messageCount: 3,
      lastUpdated: new Date(Date.now() - 172800000),
      messageTree: {},
      currentPath: []
    },
    {
      id: '3',
      title: '食堂用餐时间',
      messageCount: 2,
      lastUpdated: new Date(Date.now() - 259200000),
      messageTree: {},
      currentPath: []
    }
  ]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null); // 改为null，表示新对话
  const [isLoading, setIsLoading] = useState(false);
  const [sessionSearchTerm, setSessionSearchTerm] = useState('');
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<FileAttachment[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false); // 默认展开侧边栏
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
      // 新对话或其他会话，显示空消息
      setMessages([]);
    }
  }, [selectedSession]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 创建新对话 - 重置到新对话状态
  const createNewSession = () => {
    setSelectedSession(null); // 设置为null表示新对话状态
    setMessages([]);
    setUploadedFiles([]);
  };

  // 文件上传处理
  const handleFileUpload = (file: File) => {
    // 检查文件大小 (10MB = 10 * 1024 * 1024 bytes)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      message.error('文件大小不能超过10MB');
      return false;
    }

    // 检查文件类型
    const isImage = file.type.startsWith('image/');
    const isText = file.type.startsWith('text/') || 
                   file.name.endsWith('.txt') || 
                   file.name.endsWith('.md') || 
                   file.name.endsWith('.doc') || 
                   file.name.endsWith('.docx');

    if (!isImage && !isText) {
      message.error('只支持图片和文本文件');
      return false;
    }

    // 创建文件URL (在实际应用中，这里应该上传到服务器)
    const fileUrl = URL.createObjectURL(file);
    
    const newAttachment: FileAttachment = {
      id: Date.now().toString(),
      name: file.name,
      type: isImage ? 'image' : 'text',
      size: file.size,
      url: fileUrl
    };

    setUploadedFiles(prev => [...prev, newAttachment]);
    message.success(`文件 "${file.name}" 上传成功`);
    return false; // 阻止默认上传行为
  };

  // 删除已上传文件
  const removeUploadedFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const handleSendMessage = async () => {
    if (!currentMessage.trim() && uploadedFiles.length === 0) return;

    let currentSessionId = selectedSession;

    // 如果是新对话状态（selectedSession为null），创建新会话
    if (!selectedSession) {
      const newSessionId = `session_${Date.now()}`;
      const newSession: ChatSession = {
        id: newSessionId,
        title: currentMessage.slice(0, 20) + (currentMessage.length > 20 ? '...' : '') || '新对话',
        messageCount: 0,
        lastUpdated: new Date(),
        messageTree: {},
        currentPath: []
      };
      setSessions(prev => [newSession, ...prev]);
      setSelectedSession(newSessionId);
      currentSessionId = newSessionId;
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: currentMessage,
      timestamp: new Date(),
      attachments: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setUploadedFiles([]); // 清空已上传文件
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

  const handleResendMessage = (messageId: string) => {
    const message = messages.find(m => m.id === messageId);
    if (message && message.role === 'user') {
      setEditingMessageId(messageId);
      setEditingContent(message.content);
    }
  };

  const handleEditConfirm = async () => {
    if (!editingMessageId || !editingContent.trim()) return;

    // 找到要编辑的消息
    const editingMessage = messages.find(m => m.id === editingMessageId);
    if (!editingMessage) return;

    // 找到这个消息在数组中的位置
    const messageIndex = messages.findIndex(m => m.id === editingMessageId);
    if (messageIndex === -1) return;

    // 创建新的分支消息
    const newMessageId = `${editingMessageId}_${Date.now()}`;
    const newUserMessage: ChatMessage = {
      id: newMessageId,
      role: 'user',
      content: editingContent,
      timestamp: new Date(),
      parentId: editingMessage.parentId
    };

    // 移除原消息之后的所有消息（包括AI回复）
    const newMessages = messages.slice(0, messageIndex);
    newMessages.push(newUserMessage);

    setMessages(newMessages);
    setEditingMessageId(null);
    setEditingContent('');
    setIsLoading(true);

    // 模拟AI响应
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `基于您重新编辑的问题："${editingContent}"，我来为您提供更准确的回答。\n\n这是一个重新生成的回复，会根据您修改后的问题内容提供相应的帮助和建议。`,
        timestamp: new Date(),
        parentId: newMessageId
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleEditCancel = () => {
    setEditingMessageId(null);
    setEditingContent('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleLanguageChange = (value: string) => {
    i18n.changeLanguage(value);
    localStorage.setItem('language', value);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // 导航菜单项
  const navigationItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: t('navigation.home'),
      onClick: () => navigate('/'),
    },
    {
      key: 'chat',
      icon: <MessageOutlined />,
      label: '校园生活助手',
      onClick: () => {
        // 重置到新对话状态
        setSelectedSession(null);
        setMessages([]);
        setUploadedFiles([]);
        setSidebarCollapsed(false); // 确保侧边栏是展开的
      },
    },
    {
      key: 'study',
      icon: <BookOutlined />,
      label: t('navigation.studyAssistant'),
      onClick: () => navigate('/study'),
    },
    ...(user?.role === 'admin' ? [{
      key: 'admin',
      icon: <DashboardOutlined />,
      label: t('navigation.admin'),
      onClick: () => navigate('/admin'),
    }] : []),
  ];

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: t('navigation.profile'),
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: t('navigation.settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('auth.logout'),
      onClick: handleLogout,
    },
  ];

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(sessionSearchTerm.toLowerCase())
  );

  // 快速开始对话
  const handleQuickStart = (message: string) => {
    setCurrentMessage(message);
    // 直接发送这个消息
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      backgroundColor: '#f9f9f9'
    }}>
      {/* 左侧边栏 - 类似OpenAI风格 */}
      <div style={{
        width: sidebarCollapsed ? '0px' : '280px',
        backgroundColor: '#000',
        color: '#fff',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #333',
        transition: 'width 0.3s ease',
        overflow: 'hidden'
      }}>
        {/* 新对话按钮 */}
        <div style={{ padding: '16px' }}>
          <Button
            type="default"
            block
            icon={<PlusOutlined />}
            onClick={createNewSession}
            style={{
              backgroundColor: 'transparent',
              borderColor: '#444',
              color: '#fff',
              borderRadius: '8px'
            }}
          >
            新对话
          </Button>
        </div>

        {/* 搜索框 */}
        <div style={{ padding: '0 16px 16px 16px' }}>
          <Input.Search
            placeholder="搜索对话..."
            onChange={(e) => setSessionSearchTerm(e.target.value)}
            style={{
              backgroundColor: '#333',
              borderColor: '#444'
            }}
            className="dark-search"
          />
        </div>

        {/* 对话历史列表 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}>
          {filteredSessions.map((session) => (
            <div
              key={session.id}
              onClick={() => setSelectedSession(session.id)}
              style={{
                padding: '12px 16px',
                margin: '4px 0',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: selectedSession === session.id ? '#2a2a2a' : 'transparent',
                transition: 'all 0.2s ease',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
              onMouseEnter={(e) => {
                if (selectedSession !== session.id) {
                  e.currentTarget.style.backgroundColor = '#1a1a1a';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedSession !== session.id) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: 500,
                  color: '#fff',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {session.title}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: '#888',
                  marginTop: '2px'
                }}>
                  {session.messageCount} 条消息
                </div>
              </div>
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  setSessions(prev => prev.filter(s => s.id !== session.id));
                }}
                style={{
                  color: '#888',
                  border: 'none',
                  padding: '4px'
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* 右侧主聊天区域 */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#fff'
      }}>
        {/* 聊天标题栏 - 融合导航功能 */}
        <div style={{
          padding: '12px 24px',
          borderBottom: '1px solid #e5e5e5',
          backgroundColor: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          {/* 左侧：侧边栏切换按钮和导航菜单 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* 侧边栏切换按钮 */}
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              style={{
                color: '#666',
                border: 'none',
                padding: '6px 8px',
                borderRadius: '6px'
              }}
              title={sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'}
            />
            
            {navigationItems.map((item) => (
              <Button
                key={item.key}
                type="text"
                icon={item.icon}
                onClick={item.onClick}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: '#666',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '6px'
                }}
              >
                {item.label}
              </Button>
            ))}
          </div>

          {/* 中间：AI助手信息 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <RobotOutlined style={{ fontSize: '20px', color: '#10a37f' }} />
            <div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: '#333' }}>
                校园生活AI助手
              </div>
              <div style={{ fontSize: '12px', color: '#888' }}>
                为您解答校园生活中的各种问题
              </div>
            </div>
          </div>

          {/* 右侧：语言选择和用户信息 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* 语言切换 */}
            <Select
              value={i18n.language}
              onChange={handleLanguageChange}
              style={{ width: 120 }}
              size="small"
              suffixIcon={<GlobalOutlined />}
            >
              <Option value="zh-CN">简体中文</Option>
              <Option value="zh-TW">繁體中文</Option>
              <Option value="en-US">English</Option>
            </Select>

            {/* 用户信息 */}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar 
                  size="small" 
                  icon={<UserOutlined />} 
                  style={{ 
                    backgroundColor: user?.role === 'admin' ? '#ff7875' : '#87d068' 
                  }} 
                />
                <Text>{user?.email}</Text>
              </Space>
            </Dropdown>
          </div>
        </div>

        {/* 聊天消息区域 */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0',
          backgroundColor: '#fff',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}>
          {messages.length === 0 ? (
            // 新对话的美观欢迎界面
            <WelcomeInterface onQuickStart={handleQuickStart} />
          ) : (
            // 有消息时的正常聊天界面
            <div style={{
              width: '100%',
              maxWidth: '768px',
              padding: '24px 16px'
            }}>
              {messages.map((message) => (
                <div key={message.id}>
                  {editingMessageId === message.id ? (
                    // 编辑模式
                    <div style={{
                      marginBottom: '24px',
                      padding: '16px',
                      border: '2px solid #0084ff',
                      borderRadius: '12px',
                      backgroundColor: '#f8faff'
                    }}>
                      <div style={{
                        fontSize: '14px',
                        fontWeight: 500,
                        color: '#0084ff',
                        marginBottom: '8px'
                      }}>
                        重新编辑消息
                      </div>
                      <TextArea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        autoSize={{ minRows: 2, maxRows: 6 }}
                        style={{
                          marginBottom: '12px',
                          borderRadius: '8px'
                        }}
                      />
                      <div style={{
                        display: 'flex',
                        gap: '8px',
                        justifyContent: 'flex-end'
                      }}>
                        <Button size="small" onClick={handleEditCancel}>
                          取消
                        </Button>
                        <Button 
                          size="small" 
                          type="primary" 
                          onClick={handleEditConfirm}
                          disabled={!editingContent.trim()}
                        >
                          确认重发
                        </Button>
                      </div>
                    </div>
                  ) : (
                    // 正常显示模式
                    <ChatMessageComponent
                      key={message.id}
                      message={message}
                      onResend={handleResendMessage}
                    />
                  )}
                </div>
              ))}
              {isLoading && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '16px 0',
                  color: '#666'
                }}>
                  <LoadingSpinner size="small" />
                  <span style={{ marginLeft: '12px', fontSize: '14px' }}>
                    AI正在思考中...
                  </span>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 底部输入区域 */}
        <div style={{
          borderTop: '1px solid #e5e5e5',
          backgroundColor: '#fff',
          display: 'flex',
          justifyContent: 'center'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '768px'
          }}>
            {/* 已上传文件显示区域 */}
            {uploadedFiles.length > 0 && (
              <div style={{
                padding: '12px 24px 0',
                borderBottom: '1px solid #f0f0f0'
              }}>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px'
                }}>
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 12px',
                        backgroundColor: '#f5f5f5',
                        borderRadius: '16px',
                        fontSize: '12px',
                        border: '1px solid #e0e0e0'
                      }}
                    >
                      {file.type === 'image' ? (
                        <FileImageOutlined style={{ color: '#52c41a' }} />
                      ) : (
                        <FileTextOutlined style={{ color: '#1890ff' }} />
                      )}
                      <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {file.name}
                      </span>
                      <Button
                        type="text"
                        size="small"
                        icon={<DeleteFileOutlined />}
                        onClick={() => removeUploadedFile(file.id)}
                        style={{
                          padding: 0,
                          minWidth: 'auto',
                          width: '16px',
                          height: '16px',
                          color: '#999'
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* 输入框和按钮区域 */}
            <div style={{
              padding: '16px 24px 24px',
              display: 'flex',
              alignItems: 'flex-end',
              gap: '12px'
            }}>
              <Upload
                beforeUpload={handleFileUpload}
                showUploadList={false}
                multiple={false}
                accept="image/*,.txt,.md,.doc,.docx,text/*"
              >
                <Button
                  icon={<PaperClipOutlined />}
                  style={{
                    borderRadius: '12px',
                    height: '40px',
                    width: '40px',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid #d1d5db'
                  }}
                  title="上传文件（支持图片和文本文件，最大10MB）"
                />
              </Upload>
              
              <TextArea
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onPressEnter={handleKeyPress}
                placeholder="输入您的校园生活问题..."
                autoSize={{ minRows: 1, maxRows: 4 }}
                style={{
                  flex: 1,
                  borderRadius: '12px',
                  border: '1px solid #d1d5db',
                  boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
                  resize: 'none'
                }}
              />
              
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                disabled={(!currentMessage.trim() && uploadedFiles.length === 0) || isLoading}
                style={{
                  borderRadius: '12px',
                  backgroundColor: '#10a37f',
                  borderColor: '#10a37f',
                  height: '40px',
                  width: '40px',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
