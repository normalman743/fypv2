import React from 'react';
import { Avatar, Typography } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Text } = Typography;

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: string[];
}

interface ChatMessageProps {
  message: ChatMessage;
  isTyping?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, isTyping = false }) => {
  const isUser = message.role === 'user';
  
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
      y: 20,
      scale: 0.8
    },
    visible: { 
      opacity: 1, 
      y: 0,
      scale: 1,
      transition: {
        duration: 0.4,
        ease: 'easeOut'
      }
    }
  };

  const bubbleVariants = {
    hover: {
      scale: 1.02,
      transition: {
        duration: 0.2
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
        marginBottom: '16px'
      }}
    >
      <div style={{ 
        display: 'flex', 
        alignItems: 'flex-start',
        flexDirection: isUser ? 'row-reverse' : 'row',
        maxWidth: '80%'
      }}>
        <Avatar 
          icon={isUser ? <UserOutlined /> : <RobotOutlined />}
          style={{ 
            backgroundColor: isUser ? '#1890ff' : '#52c41a',
            margin: isUser ? '0 0 0 8px' : '0 8px 0 0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}
        />
        
        <motion.div
          variants={bubbleVariants}
          whileHover="hover"
          style={{
            background: isUser 
              ? 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)' 
              : 'linear-gradient(135deg, #f6f6f6 0%, #ffffff 100%)',
            color: isUser ? 'white' : '#333',
            padding: '12px 16px',
            borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            boxShadow: isUser 
              ? '0 4px 12px rgba(24, 144, 255, 0.3)' 
              : '0 2px 8px rgba(0,0,0,0.1)',
            border: isUser ? 'none' : '1px solid #f0f0f0',
            position: 'relative'
          }}
        >
          {isTyping && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              marginBottom: '8px'
            }}>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <Text type="secondary" style={{ fontSize: '12px', color: isUser ? 'rgba(255,255,255,0.7)' : '#999' }}>
                AI正在思考...
              </Text>
            </div>
          )}
          
          <div>{message.content}</div>
          
          <div style={{ 
            fontSize: '11px', 
            opacity: 0.7, 
            marginTop: '6px',
            textAlign: isUser ? 'left' : 'right',
            color: isUser ? 'rgba(255,255,255,0.8)' : '#999'
          }}>
            {formatTime(message.timestamp)}
          </div>

          {/* 小三角箭头 */}
          <div style={{
            position: 'absolute',
            bottom: '8px',
            [isUser ? 'right' : 'left']: '-6px',
            width: 0,
            height: 0,
            borderStyle: 'solid',
            borderWidth: isUser ? '6px 0 6px 8px' : '6px 8px 6px 0',
            borderColor: isUser 
              ? 'transparent transparent transparent #1890ff' 
              : 'transparent #f6f6f6 transparent transparent'
          }} />
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ChatMessage;
