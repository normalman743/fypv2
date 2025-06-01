import React from 'react';
import { RobotOutlined, MessageOutlined, BookOutlined, HomeOutlined } from '@ant-design/icons';
import { Button } from 'antd';

interface WelcomeInterfaceProps {
  onQuickStart: (message: string) => void;
}

const WelcomeInterface: React.FC<WelcomeInterfaceProps> = ({ onQuickStart }) => {
  const quickStartMessages = [
    "宿舍网络连接有问题怎么办？",
    "图书馆的开放时间是什么时候？",
    "食堂有哪些美食推荐？",
    "如何申请课程选修？"
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      width: '100%',
      padding: '40px 24px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* 背景装饰 */}
      <div style={{
        position: 'absolute',
        top: '-50%',
        left: '-50%',
        width: '200%',
        height: '200%',
        background: 'radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px)',
        backgroundSize: '50px 50px',
        animation: 'float 20s ease-in-out infinite',
        pointerEvents: 'none'
      }} />

      {/* 主要内容 */}
      <div style={{
        textAlign: 'center',
        zIndex: 1,
        maxWidth: '600px'
      }}>
        {/* AI助手图标和标题 */}
        <div style={{
          marginBottom: '32px'
        }}>
          <div style={{
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            background: 'linear-gradient(45deg, #10a37f, #1a73e8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 24px',
            boxShadow: '0 20px 40px rgba(16, 163, 127, 0.3)',
            animation: 'pulse 2s ease-in-out infinite'
          }}>
            <RobotOutlined style={{ 
              fontSize: '48px', 
              color: '#fff'
            }} />
          </div>
          
          <h1 style={{
            fontSize: '42px',
            fontWeight: 700,
            color: '#fff',
            margin: '0 0 16px 0',
            textShadow: '0 2px 4px rgba(0,0,0,0.1)',
            letterSpacing: '-0.5px'
          }}>
            校园生活AI助手
          </h1>
          
          <p style={{
            fontSize: '18px',
            color: 'rgba(255,255,255,0.9)',
            margin: '0 0 40px 0',
            lineHeight: '1.6',
            fontWeight: 300
          }}>
            您的智能校园伙伴，为您解答宿舍、食堂、图书馆、课程等各种校园生活问题
          </p>
        </div>

        {/* 快速开始按钮 */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '16px',
          marginBottom: '40px'
        }}>
          {quickStartMessages.map((message, index) => (
            <Button
              key={index}
              size="large"
              onClick={() => onQuickStart(message)}
              style={{
                height: '60px',
                borderRadius: '16px',
                border: '2px solid rgba(255,255,255,0.2)',
                background: 'rgba(255,255,255,0.1)',
                color: '#fff',
                fontSize: '15px',
                fontWeight: 500,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '0 20px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              {message}
            </Button>
          ))}
        </div>

        {/* 特性介绍 */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '40px',
          flexWrap: 'wrap'
        }}>
          {[
            { icon: <MessageOutlined />, title: '智能问答', desc: '24/7在线服务' },
            { icon: <BookOutlined />, title: '学习助手', desc: '课程与学术支持' },
            { icon: <HomeOutlined />, title: '生活指南', desc: '校园生活全方位' }
          ].map((feature, index) => (
            <div
              key={index}
              style={{
                textAlign: 'center',
                color: 'rgba(255,255,255,0.9)'
              }}
            >
              <div style={{
                fontSize: '24px',
                marginBottom: '8px'
              }}>
                {feature.icon}
              </div>
              <div style={{
                fontSize: '16px',
                fontWeight: 600,
                marginBottom: '4px'
              }}>
                {feature.title}
              </div>
              <div style={{
                fontSize: '14px',
                opacity: 0.8
              }}>
                {feature.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CSS动画样式 */}
      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
        
        @keyframes float {
          0% { transform: translate(0px, 0px) rotate(0deg); }
          33% { transform: translate(30px, -30px) rotate(120deg); }
          66% { transform: translate(-20px, 20px) rotate(240deg); }
          100% { transform: translate(0px, 0px) rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default WelcomeInterface;
