import React from 'react';
import { Typography, Space, Button, Breadcrumb } from 'antd';
import { motion } from 'framer-motion';

const { Title, Text } = Typography;

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  breadcrumb?: Array<{
    title: string;
    href?: string;
  }>;
  extra?: React.ReactNode;
  gradient?: string;
  actions?: Array<{
    text: string;
    onClick: () => void;
    type?: 'primary' | 'default' | 'dashed' | 'link' | 'text';
    icon?: React.ReactNode;
  }>;
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  icon,
  breadcrumb,
  extra,
  gradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  actions
}) => {
  const headerVariants = {
    hidden: { opacity: 0, y: -20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: 'easeOut'
      }
    }
  };

  const titleVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        delay: 0.2,
        duration: 0.5,
        ease: 'easeOut'
      }
    }
  };

  return (
    <motion.div
      variants={headerVariants}
      initial="hidden"
      animate="visible"
      style={{
        background: gradient,
        padding: '24px 32px',
        borderRadius: '12px',
        marginBottom: '24px',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* 装饰性背景元素 */}
      <div style={{
        position: 'absolute',
        top: '-50%',
        right: '-20%',
        width: '200px',
        height: '200px',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '50%',
        filter: 'blur(40px)'
      }} />
      
      <div style={{
        position: 'absolute',
        bottom: '-30%',
        left: '-10%',
        width: '150px',
        height: '150px',
        background: 'rgba(255,255,255,0.08)',
        borderRadius: '50%',
        filter: 'blur(30px)'
      }} />

      <div style={{ position: 'relative', zIndex: 1 }}>
        {breadcrumb && (
          <Breadcrumb style={{ marginBottom: '16px' }}>
            {breadcrumb.map((item, index) => (
              <Breadcrumb.Item key={index} href={item.href}>
                <span style={{ color: 'rgba(255,255,255,0.8)' }}>
                  {item.title}
                </span>
              </Breadcrumb.Item>
            ))}
          </Breadcrumb>
        )}

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          <motion.div variants={titleVariants} style={{ flex: 1 }}>
            <Space align="start" size="middle">
              {icon && (
                <div style={{
                  fontSize: '32px',
                  color: 'rgba(255,255,255,0.9)',
                  marginTop: '4px'
                }}>
                  {icon}
                </div>
              )}
              <div>
                <Title
                  level={1}
                  style={{
                    color: 'white',
                    margin: 0,
                    fontSize: '28px',
                    fontWeight: 'bold',
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}
                >
                  {title}
                </Title>
                {subtitle && (
                  <Text
                    style={{
                      color: 'rgba(255,255,255,0.85)',
                      fontSize: '16px',
                      marginTop: '4px',
                      display: 'block'
                    }}
                  >
                    {subtitle}
                  </Text>
                )}
              </div>
            </Space>
          </motion.div>

          {(extra || actions) && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              {actions && actions.map((action, index) => (
                <Button
                  key={index}
                  type={action.type || 'default'}
                  icon={action.icon}
                  onClick={action.onClick}
                  style={{
                    background: action.type === 'primary' ? 'rgba(255,255,255,0.2)' : 'transparent',
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  {action.text}
                </Button>
              ))}
              {extra}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default PageHeader;
