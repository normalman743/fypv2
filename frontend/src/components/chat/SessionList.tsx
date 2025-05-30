import React from 'react';
import { Card, List, Button, Typography, Space } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Text } = Typography;

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

interface SessionListProps {
  sessions: ChatSession[];
  currentSession: string;
  onSessionSelect: (sessionId: string) => void;
  onSessionDelete: (sessionId: string) => void;
  onNewSession: () => void;
  title: string;
}

const SessionList: React.FC<SessionListProps> = ({
  sessions,
  currentSession,
  onSessionSelect,
  onSessionDelete,
  onNewSession,
  title
}) => {
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

  const listVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    }
  };

  return (
    <Card 
      title={title}
      extra={
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={onNewSession}
          size="small"
          style={{
            borderRadius: '6px',
            boxShadow: '0 2px 4px rgba(24, 144, 255, 0.3)'
          }}
        >
          新对话
        </Button>
      }
      style={{ 
        height: '100%',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        borderRadius: '12px'
      }}
      bodyStyle={{ 
        padding: 0, 
        height: 'calc(100% - 57px)', 
        overflow: 'auto'
      }}
    >
      <motion.div
        variants={listVariants}
        initial="hidden"
        animate="visible"
      >
        <List
          dataSource={sessions}
          renderItem={(session, index) => (
            <motion.div
              key={session.id}
              variants={itemVariants}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <List.Item
                className={`session-item ${currentSession === session.id ? 'active' : ''}`}
                onClick={() => onSessionSelect(session.id)}
                style={{
                  cursor: 'pointer',
                  padding: '12px 16px',
                  backgroundColor: currentSession === session.id ? '#f0f9ff' : 'transparent',
                  borderLeft: currentSession === session.id ? '3px solid #1890ff' : '3px solid transparent',
                  transition: 'all 0.3s ease'
                }}
                actions={[
                  <Button
                    type="text"
                    icon={<DeleteOutlined />}
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSessionDelete(session.id);
                    }}
                    danger
                    style={{
                      opacity: 0.6,
                      transition: 'opacity 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.opacity = '1';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.opacity = '0.6';
                    }}
                  />
                ]}
              >
                <List.Item.Meta
                  title={
                    <Text 
                      ellipsis 
                      style={{ 
                        fontSize: '14px', 
                        fontWeight: currentSession === session.id ? 600 : 500,
                        color: currentSession === session.id ? '#1890ff' : '#333'
                      }}
                    >
                      {session.title}
                    </Text>
                  }
                  description={
                    <div>
                      <Text 
                        ellipsis 
                        type="secondary" 
                        style={{ 
                          fontSize: '12px',
                          display: 'block',
                          marginBottom: '4px'
                        }}
                      >
                        {session.lastMessage || '暂无消息'}
                      </Text>
                      <Space size="small">
                        <Text type="secondary" style={{ fontSize: '11px' }}>
                          {formatTime(session.timestamp)}
                        </Text>
                        <Text type="secondary" style={{ fontSize: '11px' }}>
                          {session.messageCount}条消息
                        </Text>
                      </Space>
                    </div>
                  }
                />
              </List.Item>
            </motion.div>
          )}
        />
      </motion.div>
    </Card>
  );
};

export default SessionList;
