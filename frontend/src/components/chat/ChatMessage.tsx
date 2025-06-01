import React, { useState } from 'react';
import { Avatar, Typography, Button, Tooltip, Image } from 'antd';
import { UserOutlined, RobotOutlined, RedoOutlined, FileTextOutlined, FileImageOutlined } from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Text } = Typography;

interface FileAttachment {
  id: string;
  name: string;
  type: 'image' | 'text';
  size: number;
  url: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: FileAttachment[];
}

interface ChatMessageProps {
  message: ChatMessage;
  isTyping?: boolean;
  onResend?: (messageId: string, content: string) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, isTyping = false, onResend }) => {
  const isUser = message.role === 'user';
  const [isHovered, setIsHovered] = useState(false);
  
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

  const messageVariants = {
    hidden: { 
      opacity: 0, 
      y: 10
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    }
  };

  return (
    <motion.div
      variants={messageVariants}
      initial="hidden"
      animate="visible"
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '24px',
        width: '100%'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        maxWidth: '85%',
        gap: '12px'
      }}>
        {/* 头像 */}
        <Avatar
          size={40}
          icon={isUser ? <UserOutlined /> : <RobotOutlined />}
          style={{
            backgroundColor: isUser ? '#1890ff' : '#10a37f',
            flexShrink: 0,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #fff'
          }}
        />

        {/* 消息内容区域 */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
          gap: '4px',
          maxWidth: 'calc(100% - 52px)'
        }}>
          {/* 消息气泡 */}
          <div
            style={{
              background: isUser 
                ? 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)' 
                : 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
              color: isUser ? '#fff' : '#333',
              padding: '16px 20px',
              borderRadius: isUser ? '20px 20px 6px 20px' : '20px 20px 20px 6px',
              boxShadow: isUser 
                ? '0 4px 12px rgba(24, 144, 255, 0.3)' 
                : '0 4px 12px rgba(0, 0, 0, 0.1)',
              border: isUser ? 'none' : '1px solid #e0e0e0',
              position: 'relative',
              transition: 'all 0.3s ease',
              transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
              maxWidth: '100%',
              wordBreak: 'break-word'
            }}
          >
            {/* 消息文本内容 */}
            <Text 
              style={{ 
                color: isUser ? '#fff' : '#333',
                fontSize: '15px',
                lineHeight: '1.6',
                fontWeight: 400,
                whiteSpace: 'pre-wrap'
              }}
            >
              {message.content}
            </Text>

            {/* 附件显示 */}
            {message.attachments && message.attachments.length > 0 && (
              <div style={{ 
                marginTop: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {message.attachments.map((attachment) => (
                  <div
                    key={attachment.id}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: isUser ? 'rgba(255,255,255,0.2)' : '#f5f5f5',
                      borderRadius: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      border: isUser ? '1px solid rgba(255,255,255,0.3)' : '1px solid #e0e0e0'
                    }}
                  >
                    {attachment.type === 'image' ? (
                      <>
                        <FileImageOutlined style={{ 
                          color: isUser ? '#fff' : '#52c41a',
                          fontSize: '16px'
                        }} />
                        <Image
                          src={attachment.url}
                          alt={attachment.name}
                          style={{ 
                            maxWidth: '200px', 
                            maxHeight: '150px',
                            borderRadius: '8px'
                          }}
                          preview={{
                            mask: <span style={{ color: '#fff' }}>预览</span>
                          }}
                        />
                      </>
                    ) : (
                      <>
                        <FileTextOutlined style={{ 
                          color: isUser ? '#fff' : '#1890ff',
                          fontSize: '16px'
                        }} />
                        <span style={{
                          color: isUser ? '#fff' : '#333',
                          fontSize: '14px',
                          maxWidth: '150px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {attachment.name}
                        </span>
                        <span style={{
                          color: isUser ? 'rgba(255,255,255,0.7)' : '#999',
                          fontSize: '12px'
                        }}>
                          ({(attachment.size / 1024).toFixed(1)}KB)
                        </span>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 时间戳和操作按钮 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            opacity: isHovered ? 1 : 0.6,
            transition: 'opacity 0.3s ease',
            marginTop: '4px'
          }}>
            <Text 
              style={{ 
                fontSize: '12px', 
                color: '#999',
                fontWeight: 400
              }}
            >
              {formatTime(message.timestamp)}
            </Text>
            
            {/* 重发按钮 - 只对用户消息显示 */}
            {isUser && onResend && (
              <Tooltip title="重新发送">
                <Button
                  type="text"
                  size="small"
                  icon={<RedoOutlined />}
                  onClick={() => onResend(message.id, message.content)}
                  style={{
                    color: '#999',
                    border: 'none',
                    padding: '2px 4px',
                    height: '24px',
                    borderRadius: '6px',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#1890ff';
                    e.currentTarget.style.backgroundColor = '#f0f8ff';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = '#999';
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                />
              </Tooltip>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ChatMessage;
