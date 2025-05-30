import React from 'react';
import { Spin, Space, Typography } from 'antd';
import { motion } from 'framer-motion';

const { Text } = Typography;

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large';
  text?: string;
  fullscreen?: boolean;
  delay?: number;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'default',
  text = '加载中...',
  fullscreen = false,
  delay = 200
}) => {
  const spinnerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: {
        delay: delay / 1000,
        duration: 0.3
      }
    }
  };

  const containerStyle: React.CSSProperties = fullscreen ? {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(255, 255, 255, 0.9)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    backdropFilter: 'blur(4px)'
  } : {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 20px'
  };

  return (
    <motion.div
      variants={spinnerVariants}
      initial="hidden"
      animate="visible"
      style={containerStyle}
    >
      <Space direction="vertical" align="center" size="large">
        <Spin size={size} />
        {text && (
          <Text type="secondary" style={{ fontSize: '14px' }}>
            {text}
          </Text>
        )}
      </Space>
    </motion.div>
  );
};

export default LoadingSpinner;
