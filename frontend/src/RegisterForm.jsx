import { useState } from 'react';
import { api } from './api';

export default function RegisterForm({ onRegister }) {
  const [form, setForm] = useState({ email:'', username:'', password:'', invite_code:'' });
  const [error, setError] = useState(null);
  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify(form)
      });
      onRegister();
    } catch (err) {
      console.error(err);
      setError('注册失败');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>注册</h2>
      {error && <div style={{color:'red'}}>{error}</div>}
      <input name="email" placeholder="邮箱" value={form.email} onChange={handleChange} />
      <input name="username" placeholder="用户名" value={form.username} onChange={handleChange} />
      <input type="password" name="password" placeholder="密码" value={form.password} onChange={handleChange} />
      <input name="invite_code" placeholder="邀请码" value={form.invite_code} onChange={handleChange} />
      <button type="submit">注册</button>
    </form>
  );
}
