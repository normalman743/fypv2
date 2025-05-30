import React from 'react';
import { Card, Statistic, Typography } from 'antd';
import { motion } from 'framer-motion';

const { Text } = Typography;

interface StatCardProps {
  title: string;
  value: string | number;
  prefix?: React.ReactNode;
  suffix?: string;
  icon?: React.ReactNode;
  valueStyle?: React.CSSProperties;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  description?: string;
  color?: string;
  loading?: boolean;
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  prefix,
  suffix,
  icon,
  valueStyle,
  trend,
  description,
  color = '#1890ff',
  loading = false,
  onClick
}) => {
  const cardVariants = {
    hover: {
      scale: 1.02,
      boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    },
    tap: {
      scale: 0.98
    }
  };

  return (
    <motion.div
      variants={cardVariants}
      whileHover="hover"
      whileTap={onClick ? "tap" : undefined}
      style={{ height: '100%' }}
    >
      <Card
        hoverable={!!onClick}
        loading={loading}
        onClick={onClick}
        style={{
          height: '100%',
          borderLeft: `4px solid ${color}`,
          cursor: onClick ? 'pointer' : 'default'
        }}
        bodyStyle={{
          padding: '20px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ flex: 1 }}>
            <Statistic
              title={title}
              value={value}
              prefix={prefix}
              suffix={suffix}
              valueStyle={{
                color: color,
                fontSize: '24px',
                fontWeight: 'bold',
                ...valueStyle
              }}
            />
          </div>
          {icon && (
            <div style={{
              fontSize: '32px',
              color: color,
              opacity: 0.8,
              marginLeft: '16px'
            }}>
              {icon}
            </div>
          )}
        </div>
        
        {trend && (
          <div style={{ marginTop: '8px' }}>
            <Text 
              type={trend.isPositive ? 'success' : 'danger'}
              style={{ fontSize: '12px' }}
            >
              {trend.isPositive ? '↗' : '↘'} {Math.abs(trend.value)}%
            </Text>
            <Text type="secondary" style={{ fontSize: '12px', marginLeft: '4px' }}>
              较上周
            </Text>
          </div>
        )}
        
        {description && (
          <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '4px' }}>
            {description}
          </Text>
        )}
      </Card>
    </motion.div>
  );
};

export default StatCard;
