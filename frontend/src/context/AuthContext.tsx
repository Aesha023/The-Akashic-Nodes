import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, role?: UserRole, token?: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('pravahx_auth_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return null;
      }
    }
    // Default active user for quick review
    return {
      id: 'usr_lead_hydro_01',
      username: 'dr_sharma',
      email: 'a.sharma@pravahx.internal',
      role: 'hydrologist',
      mfa_enabled: true,
      token: 'jwt_mock_valid_token_pravahx',
    };
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('pravahx_auth_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('pravahx_auth_user');
    }
  }, [user]);

  const login = (username: string, role: UserRole = 'hydrologist', token: string = 'token_auth_ok') => {
    const newUser: User = {
      id: 'usr_' + Date.now(),
      username,
      email: `${username}@pravahx.internal`,
      role,
      token,
      mfa_enabled: true,
    };
    setUser(newUser);
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
