import { apiClient } from './client';
import type { SavingsGoal, GoalContribution } from '../types';

export const goalsApi = {
    list: async (): Promise<SavingsGoal[]> => {
        const res = await apiClient.get<SavingsGoal[]>('/goals/');
        return res.data;
    },
    create: async (data: { name: string; target_amount: string; target_date: string }): Promise<SavingsGoal> => {
        const res = await apiClient.post<SavingsGoal>('/goals/', data);
        return res.data;
    },
    update: async (id: number, data: Partial<{ name: string; target_amount: string; target_date: string; status: string }>): Promise<SavingsGoal> => {
        const res = await apiClient.patch<SavingsGoal>(`/goals/${id}/`, data);
        return res.data;
    },
    addContribution: async (goalId: number, data: { amount: string; contribution_date: string; note?: string }): Promise<GoalContribution> => {
        const res = await apiClient.post<GoalContribution>(`/goals/${goalId}/contributions/`, data);
        return res.data;
    },
    listContributions: async (goalId: number): Promise<GoalContribution[]> => {
        const res = await apiClient.get<GoalContribution[]>(`/goals/${goalId}/contributions/`);
        return res.data;
    },
};