import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  id: number;
  email: string;
  role: 'student' | 'admin';
  isVerified: boolean;
  language: string;
  createdAt: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  verify: (email: string, code: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化时检查本地存储的认证信息
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Invalid stored user data:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      // 模拟登录验证 - 测试账户
      const testAccounts = [
        {
          email: 'admin@university.edu',
          password: 'admin123',
          user: {
            id: 1,
            email: 'admin@university.edu',
            role: 'admin' as const,
            isVerified: true,
            language: 'zh-CN',
            createdAt: '2024-01-01T00:00:00Z'
          }
        },
        {
          email: 'student@university.edu',
          password: 'student123',
          user: {
            id: 2,
            email: 'student@university.edu',
            role: 'student' as const,
            isVerified: true,
            language: 'zh-CN',
            createdAt: '2024-01-15T00:00:00Z'
          }
        },
        {
          email: 'student2@university.edu',
          password: 'student123',
          user: {
            id: 3,
            email: 'student2@university.edu',
            role: 'student' as const,
            isVerified: false,
            language: 'zh-CN',
            createdAt: '2024-01-18T00:00:00Z'
          }
        }
      ];

      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 1000));

      const account = testAccounts.find(acc => acc.email === email && acc.password === password);
      
      if (!account) {
        throw new Error('Invalid email or password');
      }

      const token = `mock_token_${account.user.id}_${Date.now()}`;
      
      setToken(token);
      setUser(account.user);
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(account.user));
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const verify = async (email: string, code: string): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, code }),
      });

      if (!response.ok) {
        throw new Error('Verification failed');
      }

      const data = await response.json();
      
      setToken(data.token);
      setUser(data.user);
      
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    verify,
    logout,
    isLoading,
    isAuthenticated: !!user && !!token,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
