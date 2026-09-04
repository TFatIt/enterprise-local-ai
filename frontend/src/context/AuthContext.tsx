import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';
import type { User, AuthResponse } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<User>;
  logout: () => void;
  isSuperAdmin: boolean;
  isITAdmin: boolean;
  isEmployee: boolean;
  roleCode: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        try {
          const resp = await api.get<User>('/auth/me');
          setUser(resp.data);
          localStorage.setItem('user', JSON.stringify(resp.data));
        } catch {
          logout();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (usernameOrEmail: string, password: string): Promise<User> => {
    const resp = await api.post<AuthResponse>('/auth/login', {
      username_or_email: usernameOrEmail,
      password: password,
    });
    const { access_token, refresh_token, user: loggedUser } = resp.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(loggedUser));

    setToken(access_token);
    setUser(loggedUser);
    return loggedUser;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const getRoleCode = (role: any): string => {
    if (!role) return 'EMPLOYEE';
    if (typeof role === 'string') return role;
    return role.code || 'EMPLOYEE';
  };

  const roleCode = getRoleCode(user?.role);
  const isSuperAdmin = roleCode === 'SUPER_ADMIN';
  const isITAdmin = roleCode === 'IT_ADMIN';
  const isEmployee = roleCode === 'EMPLOYEE';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isSuperAdmin,
        isITAdmin,
        isEmployee,
        roleCode,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
