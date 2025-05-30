import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space, Divider } from 'antd';
import { UserOutlined, LockOutlined, GlobalOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Select } from 'antd';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login, isAuthenticated } = useAuth();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  // 如果已经登录，重定向到首页
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleLanguageChange = (value: string) => {
    i18n.changeLanguage(value);
    localStorage.setItem('language', value);
  };

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    setError(null);

    try {
      await login(values.email, values.password);
      navigate('/');
    } catch (err) {
      setError(t('auth.invalidCredentials'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: '400px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: '8px' }}>
            AI Assistant
          </Title>
          <Text type="secondary">
            {t('auth.login')}
          </Text>
        </div>

        {/* 语言选择 */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Select
            value={i18n.language}
            onChange={handleLanguageChange}
            style={{ width: 150 }}
            suffixIcon={<GlobalOutlined />}
          >
            <Option value="zh-CN">简体中文</Option>
            <Option value="zh-TW">繁體中文</Option>
            <Option value="en-US">English</Option>
          </Select>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
        >
          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              style={{ marginBottom: '16px' }}
            />
          )}

          {/* 测试账户信息 */}
          <Alert
            message={t('auth.testAccounts')}
            description={
              <div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>{t('auth.adminAccount')}:</strong>
                  <br />
                  {t('auth.email')}: admin@university.edu
                  <br />
                  {t('auth.password')}: admin123
                </div>
                <div>
                  <strong>{t('auth.studentAccount')}:</strong>
                  <br />
                  {t('auth.email')}: student@university.edu
                  <br />
                  {t('auth.password')}: student123
                </div>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: '16px' }}
          />

          <Form.Item
            name="email"
            label={t('auth.email')}
            rules={[
              { required: true, message: t('auth.emailRequired') },
              { type: 'email', message: t('auth.emailFormat') }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder={t('auth.email')}
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label={t('auth.password')}
            rules={[
              { required: true, message: t('auth.passwordRequired') },
              { min: 6, message: t('auth.passwordLength') }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={t('auth.password')}
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              size="large"
              block
            >
              {t('auth.login')}
            </Button>
          </Form.Item>
        </Form>

        <Divider />

        <div style={{ textAlign: 'center' }}>
          <Space direction="vertical">
            <Text>
              {t('auth.register')}?{' '}
              <Link to="/register">{t('auth.register')}</Link>
            </Text>
            <Link to="/forgot-password">
              <Text type="secondary">{t('auth.forgotPassword')}</Text>
            </Link>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
