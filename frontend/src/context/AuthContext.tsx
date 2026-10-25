import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types';
import { authApi } from '../api/auth';

interface AuthContextType {
    user: User | null;
    token: string | null;
    loading: boolean;
    login: (token: string, user: User) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('smart_budget_token'));
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const initAuth = async () => {
            if (token) {
                try {
                    const profile = await authApi.getProfile();
                    setUser(profile);
                } catch (error) {
                    console.error('Failed to restore session:', error);
                    localStorage.removeItem('smart_budget_token');
                    setToken(null);
                }
            }
            setLoading(false);
        };
        initAuth();
    }, [token]);

    const login = (newToken: string, newUser: User) => {
        localStorage.setItem('smart_budget_token', newToken);
        setToken(newToken);
        setUser(newUser);
    };

    const logout = () => {
        localStorage.removeItem('smart_budget_token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within an AuthProvider');
    return context;
};