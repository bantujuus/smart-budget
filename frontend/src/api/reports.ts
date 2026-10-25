import { apiClient } from './client';
import type { DashboardTotals, CategorySummary, CashFlowTrendItem, CategoryInsight } from '../types';

export const reportsApi = {
    getDashboardTotals: async (start_date: string, end_date: string): Promise<DashboardTotals> => {
        const res = await apiClient.get<DashboardTotals>('/dashboard/', { params: { start_date, end_date } });
        return res.data;
    },
    getCategorySummary: async (start_date: string, end_date: string): Promise<CategorySummary[]> => {
        const res = await apiClient.get<CategorySummary[]>('/reports/summary/', { params: { start_date, end_date } });
        return res.data;
    },
    getCashFlowTrend: async (start_date: string, end_date: string, group_by: 'day' | 'week' | 'month' = 'month'): Promise<CashFlowTrendItem[]> => {
        const res = await apiClient.get<CashFlowTrendItem[]>('/reports/trend/', { params: { start_date, end_date, group_by } });
        return res.data;
    },
    getInsights: async (): Promise<{ category_changes: CategoryInsight[]; overspent_count: number }> => {
        const res = await apiClient.get('/insights/');
        return res.data;
    },
};