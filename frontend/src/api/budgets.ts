import { apiClient } from './client';
import type { Budget } from '../types';

export const budgetsApi = {
    list: async (): Promise<Budget[]> => {
        const res = await apiClient.get<Budget[]>('/budgets/');
        return res.data;
    },
    create: async (data: { category_id: number; amount: string; start_date: string; end_date: string }): Promise<Budget> => {
        const res = await apiClient.post<Budget>('/budgets/', data);
        return res.data;
    },
    update: async (id: number, data: Partial<{ amount: string; start_date: string; end_date: string }>): Promise<Budget> => {
        const res = await apiClient.patch<Budget>(`/budgets/${id}/`, data);
        return res.data;
    },
    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/budgets/${id}/`);
    },
};