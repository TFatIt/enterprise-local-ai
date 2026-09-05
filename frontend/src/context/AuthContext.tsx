import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';
import type { User, AuthResponse } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<User>;
  logout: () => void;
  updateCurrentUser: (updatedUser: User) => void;
  isSuperAdmin: boolean;
  isAdmin: boolean;
  isITAdmin: boolean;
  isManager: boolean;
  isDeptManager: boolean;
  isEmployee: boolean;
  canManageDocuments: boolean;
  roleCode: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState<boolean>(() => {
    const hasToken = !!localStorage.getItem('access_token');
    const hasUser = !!localStorage.getItem('user');
    // Only show loading if there is a token to verify and no cached user
    return hasToken && !hasUser;
  });

  useEffect(() => {
    let isMounted = true;
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (!storedToken) {
        if (isMounted) {
          setUser(null);
          setLoading(false);
        }
        return;
      }
      try {
        const resp = await api.get<User>('/auth/me');
        if (isMounted) {
          setUser(resp.data);
          localStorage.setItem('user', JSON.stringify(resp.data));
        }
      } catch {
        if (isMounted) {
          logout();
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    initAuth();
    return () => {
      isMounted = false;
    };
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

  const updateCurrentUser = (updatedUser: User) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  const getRoleCode = (role: any): string => {
    if (!role) return 'EMPLOYEE';
    if (typeof role === 'string') return role;
    return role.code || 'EMPLOYEE';
  };

  const roleCode = getRoleCode(user?.role);
  const isSuperAdmin = roleCode === 'SUPER_ADMIN';
  const isAdmin = roleCode === 'ADMIN' || roleCode === 'SUPER_ADMIN' || roleCode === 'IT_ADMIN';
  const isITAdmin = roleCode === 'IT_ADMIN';
  const isManager = roleCode === 'MANAGER';
  const isDeptManager = roleCode === 'DEPARTMENT_MANAGER';
  const isEmployee = roleCode === 'EMPLOYEE';
  const canManageDocuments = isAdmin || isDeptManager;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        updateCurrentUser,
        isSuperAdmin,
        isAdmin,
        isITAdmin,
        isManager,
        isDeptManager,
        isEmployee,
        canManageDocuments,
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
