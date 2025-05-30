import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import zhTW from 'antd/locale/zh_TW';
import enUS from 'antd/locale/en_US';
import { useTranslation } from 'react-i18next';

// Context Providers
import { AuthProvider } from './context/AuthContext';

// Components
import Layout from './components/common/Layout';
import ProtectedRoute from './components/common/ProtectedRoute';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatPage from './pages/ChatPage';
import FilesPage from './pages/FilesPage';
import StudyPage from './pages/StudyPage';
import AdminPage from './pages/AdminPage';
import ProfilePage from './pages/ProfilePage';

// Styles
import './App.css';
import './styles/enhanced.css';
import './i18n';

// Ant Design locale mapping
const getAntdLocale = (language: string) => {
  switch (language) {
    case 'zh-CN':
      return zhCN;
    case 'zh-TW':
      return zhTW;
    case 'en-US':
      return enUS;
    default:
      return zhCN;
  }
};

function App() {
  const { i18n } = useTranslation();
  const antdLocale = getAntdLocale(i18n.language);

  return (
    <ConfigProvider locale={antdLocale}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout>
                    <HomePage />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/chat" element={
                <ProtectedRoute>
                  <Layout>
                    <ChatPage />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/study" element={
                <ProtectedRoute>
                  <Layout>
                    <StudyPage />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/admin" element={
                <ProtectedRoute requireAdmin>
                  <Layout>
                    <AdminPage />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/profile" element={
                <ProtectedRoute>
                  <Layout>
                    <ProfilePage />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Redirect any unknown routes to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  );
}

export default App;
