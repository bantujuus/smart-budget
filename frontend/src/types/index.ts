export interface User {
    id: number;
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
}

export interface Category {
    id: number;
    name: string;
    type: 'income' | 'expense';
    is_default?: boolean;
}

export interface Transaction {
    id: number;
    amount: string;
    type: 'income' | 'expense';
    category: Category;
    category_id: number;
    transaction_date: string;
    note?: string;
    created_at?: string;
}

export interface Budget {
    id: number;
    category: Category;
    category_id: number;
    amount: string;
    start_date: string;
    end_date: string;
    used: string;
    remaining: string;
    used_pct: number;
    is_over: boolean;
}

export interface SavingsGoal {
    id: number;
    name: string;
    target_amount: string;
    target_date: string;
    status: 'active' | 'completed' | 'abandoned';
    goal_contributed: string;
    goal_progress: number; // Capped at 100
}

export interface GoalContribution {
    id: number;
    goal: number;
    amount: string;
    contribution_date: string;
    note?: string;
}

export interface DashboardTotals {
    income_total: string;
    expense_total: string;
    net_cash_flow: string;
}

export interface CategorySummary {
    category_id: number;
    category_name: string;
    type: 'income' | 'expense';
    total_amount: string;
    percentage_share: number;
}

export interface CashFlowTrendItem {
    period: string; // e.g., "2026-10" or "2026-10-25"
    income: string;
    expense: string;
    net: string;
}

export interface CategoryInsight {
    category_name: string;
    current_period: string;
    previous_period: string;
    difference: string;
    percentage_change: number;
}