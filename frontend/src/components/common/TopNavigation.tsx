import React, { useState } from 'react';
import { Button, Avatar, Select, Typography } from 'antd';
import {
  HomeOutlined,
  MessageOutlined,
  BookOutlined,
  DashboardOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  GlobalOutlined,
  DownOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';

const { Text } = Typography;
const { Option } = Select;

interface TopNavigationProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
}

const TopNavigation: React.FC<TopNavigationProps> = ({ title, subtitle, icon }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { i18n } = useTranslation();
  const { user, logout } = useAuth();
  const [userMenuVisible, setUserMenuVisible] = useState(false);

  const handleLanguageChange = (value: string) => {
    i18n.changeLanguage(value);
    localStorage.setItem('language', value);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // 导航菜单
  const navigationItems = [
    {
      key: '/',
      label: '首页',
      icon: <HomeOutlined />,
      active: location.pathname === '/'
    },
    {
      key: '/chat',
      label: '校园生活Q&A',
      icon: <MessageOutlined />,
      active: location.pathname === '/chat'
    },
    {
      key: '/study',
      label: 'Study Assistant',
      icon: <BookOutlined />,
      active: location.pathname === '/study'
    },
    ...(user?.role === 'admin' ? [{
      key: '/admin',
      label: '管理',
      icon: <DashboardOutlined />,
      active: location.pathname === '/admin'
    }] : []),
  ];

  return (
    <div 
      style={{
        padding: '16px 24px',
        borderBottom: '1px solid #e5e5e5',
        backgroundColor: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 1px 4px rgba(0,21,41,.08)',
        position: 'relative',
      }}
    >
      {/* 左侧：导航链接 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        {navigationItems.map((item) => (
          <Button
            key={item.key}
            type={item.active ? 'primary' : 'text'}
            icon={item.icon}
            onClick={() => navigate(item.key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              border: 'none',
              backgroundColor: item.active ? '#0084ff' : 'transparent',
              color: item.active ? '#fff' : '#666',
              fontWeight: item.active ? 500 : 400
            }}
          >
            {item.label}
          </Button>
        ))}
      </div>

      {/* 中央：页面标题 */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '12px',
        flex: 1,
        justifyContent: 'center'
      }}>
        {icon && <span style={{ fontSize: '20px', color: '#10a37f' }}>{icon}</span>}
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '16px', fontWeight: 600, color: '#333' }}>
            {title}
          </div>
          {subtitle && (
            <div style={{ fontSize: '12px', color: '#888' }}>
              {subtitle}
            </div>
          )}
        </div>
      </div>

      {/* 右侧：用户信息 */}
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

        {/* 用户信息 - 简单的原生下拉菜单 */}
        <div style={{ position: 'relative' }}>
          <div
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: '6px',
              backgroundColor: userMenuVisible ? '#f5f5f5' : 'transparent'
            }}
            onClick={() => setUserMenuVisible(!userMenuVisible)}
          >
            <Avatar 
              size="small" 
              icon={<UserOutlined />} 
              style={{ 
                backgroundColor: user?.role === 'admin' ? '#ff7875' : '#87d068' 
              }} 
            />
            <Text>{user?.email}</Text>
            <DownOutlined style={{ fontSize: '12px', color: '#999' }} />
          </div>

          {/* 简单的下拉菜单 */}
          {userMenuVisible && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '4px',
                backgroundColor: 'white',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                boxShadow: '0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
                minWidth: '160px',
                zIndex: 1000,
              }}
            >
              <div
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                onClick={() => {
                  navigate('/profile');
                  setUserMenuVisible(false);
                }}
              >
                <UserOutlined />
                个人资料
              </div>
              <div
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                onClick={() => {
                  navigate('/profile');
                  setUserMenuVisible(false);
                }}
              >
                <SettingOutlined />
                设置
              </div>
              <div style={{ borderTop: '1px solid #f0f0f0', margin: '4px 0' }} />
              <div
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: '#ff4d4f'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                onClick={() => {
                  handleLogout();
                  setUserMenuVisible(false);
                }}
              >
                <LogoutOutlined />
                退出登录
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 点击其他地方关闭菜单 */}
      {userMenuVisible && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 999,
          }}
          onClick={() => setUserMenuVisible(false)}
        />
      )}
    </div>
  );
};

export default TopNavigation;
