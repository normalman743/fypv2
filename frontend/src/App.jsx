import { useEffect, useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import Dashboard from './Dashboard';
import { api } from './api';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [showRegister, setShowRegister] = useState(false);

  useEffect(() => {
    async function fetchUser() {
      try {
        const res = await api('/auth/me');
        setUser(res.data);
      } catch {
        // not logged in
      }
    }
    fetchUser();
  }, []);

  if (!user) {
    return (
      <div className="auth-container">
        {showRegister ? (
          <RegisterForm onRegister={() => setShowRegister(false)} />
        ) : (
          <LoginForm onLogin={setUser} />
        )}
        <button onClick={() => setShowRegister(!showRegister)}>
          {showRegister ? '已有账号? 登录' : '没有账号? 注册'}
        </button>
      </div>
    );
  }

  return <Dashboard user={user} />;
}

export default App;
