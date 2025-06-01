import React from 'react';
import { Button, Dropdown, Avatar, Space, Select, Typography, MenuProps } from 'antd';
import {
  HomeOutlined,
  MessageOutlined,
  BookOutlined,
  DashboardOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  GlobalOutlined,
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
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();

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

  return (
    <div style={{
      padding: '16px 24px',
      borderBottom: '1px solid #e5e5e5',
      backgroundColor: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      boxShadow: '0 1px 4px rgba(0,21,41,.08)'
    }}>
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
  );
};

export default TopNavigation;
