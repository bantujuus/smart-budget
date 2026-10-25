import { apiClient } from './client';
import type { Transaction, Category } from '../types';

export interface TransactionFilters {
    type?: 'income' | 'expense';
    category_id?: number;
    start_date?: string;
    end_date?: string;
    search?: string;
}

export const transactionsApi = {
    list: async (filters?: TransactionFilters): Promise<Transaction[]> => {
        const res = await apiClient.get<Transaction[]>('/transactions/', { params: filters });
        return res.data;
    },
    create: async (data: Omit<Transaction, 'id' | 'category'>): Promise<Transaction> => {
        const res = await apiClient.post<Transaction>('/transactions/', data);
        return res.data;
    },
    update: async (id: number, data: Partial<Omit<Transaction, 'id' | 'category'>>): Promise<Transaction> => {
        const res = await apiClient.patch<Transaction>(`/transactions/${id}/`, data);
        return res.data;
    },
    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/transactions/${id}/`);
    },
    getCategories: async (): Promise<Category[]> => {
        const res = await apiClient.get<Category[]>('/categories/');
        return res.data;
    },
};