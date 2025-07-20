import { useState } from 'react';
import { api } from './api';

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
      localStorage.setItem('token', res.data.access_token);
      onLogin(res.data.user);
    } catch (err) {
      console.error(err);
      setError('登录失败');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>登录</h2>
      {error && <div style={{color:'red'}}>{error}</div>}
      <div>
        <input placeholder="用户名" value={username} onChange={e=>setUsername(e.target.value)} />
      </div>
      <div>
        <input type="password" placeholder="密码" value={password} onChange={e=>setPassword(e.target.value)} />
      </div>
      <button type="submit">登录</button>
    </form>
  );
}
