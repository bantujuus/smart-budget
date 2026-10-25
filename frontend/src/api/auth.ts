import { apiClient } from './client';
import type { User } from '../types';

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface RegisterCredentials extends LoginCredentials {
    email: string;
}

export interface AuthResponse {
    token: string;
    user: User;
}

export const authApi = {
    login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
        const res = await apiClient.post<AuthResponse>('/auth/login/', credentials);
        return res.data;
    },
    register: async (credentials: RegisterCredentials): Promise<AuthResponse> => {
        const res = await apiClient.post<AuthResponse>('/auth/register/', credentials);
        return res.data;
    },
    getProfile: async (): Promise<User> => {
        const res = await apiClient.get<User>('/me/');
        return res.data;
    },
};