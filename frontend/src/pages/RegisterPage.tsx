import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space, Divider, Steps } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, SafetyOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Select } from 'antd';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;
const { Step } = Steps;

const RegisterPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [email, setEmail] = useState('');
  const { register, verify, isAuthenticated } = useAuth();
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

  const onRegisterFinish = async (values: { email: string; password: string; confirmPassword: string }) => {
    setLoading(true);
    setError(null);

    try {
      await register(values.email, values.password);
      setEmail(values.email);
      setSuccess(t('auth.registerSuccess'));
      setCurrentStep(1);
    } catch (err) {
      setError('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onVerifyFinish = async (values: { verificationCode: string }) => {
    setLoading(true);
    setError(null);

    try {
      await verify(email, values.verificationCode);
      navigate('/');
    } catch (err) {
      setError('Invalid verification code. Please try again.');
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
          maxWidth: '450px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: '8px' }}>
            AI Assistant
          </Title>
          <Text type="secondary">
            {t('auth.register')}
          </Text>
        </div>

        {/* 语言选择 */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Select
            value={i18n.language}
            onChange={handleLanguageChange}
            style={{ width: 150 }}
          >
            <Option value="zh-CN">简体中文</Option>
            <Option value="zh-TW">繁體中文</Option>
            <Option value="en-US">English</Option>
          </Select>
        </div>

        {/* 步骤指示器 */}
        <Steps current={currentStep} style={{ marginBottom: '24px' }}>
          <Step title={t('auth.register')} icon={<UserOutlined />} />
          <Step title={t('auth.verificationCode')} icon={<SafetyOutlined />} />
        </Steps>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: '16px' }}
          />
        )}

        {success && (
          <Alert
            message={success}
            type="success"
            showIcon
            style={{ marginBottom: '16px' }}
          />
        )}

        {currentStep === 0 && (
          <Form
            name="register"
            onFinish={onRegisterFinish}
            layout="vertical"
            requiredMark={false}
          >
            <Form.Item
              name="email"
              label={t('auth.email')}
              rules={[
                { required: true, message: t('auth.emailRequired') },
                { type: 'email', message: t('auth.emailFormat') }
              ]}
            >
              <Input
                prefix={<MailOutlined />}
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

            <Form.Item
              name="confirmPassword"
              label={t('auth.confirmPassword')}
              dependencies={['password']}
              rules={[
                { required: true, message: t('auth.passwordRequired') },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error(t('auth.passwordsNotMatch')));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder={t('auth.confirmPassword')}
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
                {t('auth.register')}
              </Button>
            </Form.Item>
          </Form>
        )}

        {currentStep === 1 && (
          <Form
            name="verify"
            onFinish={onVerifyFinish}
            layout="vertical"
            requiredMark={false}
          >
            <div style={{ textAlign: 'center', marginBottom: '16px' }}>
              <Text>
                验证码已发送到: <strong>{email}</strong>
              </Text>
            </div>

            <Form.Item
              name="verificationCode"
              label={t('auth.verificationCode')}
              rules={[
                { required: true, message: t('auth.verificationCodeRequired') }
              ]}
            >
              <Input
                prefix={<SafetyOutlined />}
                placeholder={t('auth.verificationCode')}
                size="large"
                maxLength={6}
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
                {t('common.confirm')}
              </Button>
            </Form.Item>

            <div style={{ textAlign: 'center' }}>
              <Button type="link" onClick={() => setCurrentStep(0)}>
                {t('common.back')}
              </Button>
            </div>
          </Form>
        )}

        <Divider />

        <div style={{ textAlign: 'center' }}>
          <Text>
            已有账户?{' '}
            <Link to="/login">{t('auth.login')}</Link>
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default RegisterPage;
