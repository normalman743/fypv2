import React from 'react';
import { Card, Space, Typography, Button } from 'antd';
import { motion } from 'framer-motion';

const { Title, Text } = Typography;

interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  color?: string;
  action?: () => void;
  onClick?: () => void;
  buttonText?: string;
  gradient?: string;
  badge?: string;
  stats?: {
    label: string;
    value: string | number;
  };
}

const QuickActionCard: React.FC<QuickActionCardProps> = ({
  title,
  description,
  icon,
  color,
  action,
  onClick,
  buttonText = '立即开始',
  gradient,
  badge,
  stats
}) => {
  const handleClick = onClick || action;
  const cardVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.5,
        ease: 'easeOut'
      }
    },
    hover: {
      y: -8,
      boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    },
    tap: {
      scale: 0.95
    }
  };

  const iconVariants = {
    hover: {
      scale: 1.1,
      rotate: 5,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    }
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      whileTap="tap"
      style={{ height: '100%' }}
    >
      <Card
        hoverable
        style={{
          height: '100%',
          background: gradient || `linear-gradient(135deg, ${color}10 0%, ${color}25 100%)`,
          border: `1px solid ${color}30`,
          borderRadius: '12px',
          overflow: 'hidden',
          position: 'relative'
        }}
        bodyStyle={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          padding: '24px'
        }}
      >
        {badge && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            background: color,
            color: 'white',
            padding: '4px 8px',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            {badge}
          </div>
        )}

        <Space direction="vertical" style={{ width: '100%', textAlign: 'center', flex: 1 }}>
          <motion.div
            variants={iconVariants}
            style={{
              background: `${color}15`,
              borderRadius: '50%',
              width: '80px',
              height: '80px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              fontSize: '32px',
              color: color
            }}
          >
            {icon}
          </motion.div>

          <Title level={4} style={{ marginBottom: '8px', color: '#333' }}>
            {title}
          </Title>

          <Text type="secondary" style={{ marginBottom: '16px', lineHeight: '1.5' }}>
            {description}
          </Text>

          {stats && (
            <div style={{
              background: 'rgba(255,255,255,0.5)',
              padding: '8px 12px',
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                {stats.label}:
              </Text>
              <Text strong style={{ marginLeft: '4px', color: color }}>
                {stats.value}
              </Text>
            </div>
          )}

          <Button
            type="primary"
            size="large"
            style={{
              marginTop: 'auto',
              background: color,
              borderColor: color,
              borderRadius: '8px',
              fontWeight: 'bold',
              boxShadow: `0 4px 15px ${color}40`
            }}
            onClick={handleClick}
          >
            {buttonText}
          </Button>
        </Space>
      </Card>
    </motion.div>
  );
};

export default QuickActionCard;
