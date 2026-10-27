import React, { useEffect, useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Wallet, PiggyBank, Coins, Loader2 } from 'lucide-react';
import { reportsApi } from '../api/reports';
import type { DashboardTotals } from '../types';

export const DashboardView: React.FC = () => {
    const [totals, setTotals] = useState<DashboardTotals>({ income_total: '0.00', expense_total: '0.00', net_cash_flow: '0.00' });
    const [loading, setLoading] = useState(true);
    const [barReady, setBarReady] = useState(false);

    // Default filter to current month
    const now = new Date();
    const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];

    useEffect(() => {
        reportsApi.getDashboardTotals(startDate, endDate)
            .then(setTotals)
            .finally(() => setLoading(false));
    }, [startDate, endDate]);

    // Let the spending bar animate from 0 once the data has rendered
    useEffect(() => {
        if (loading) return;
        const t = setTimeout(() => setBarReady(true), 150);
        return () => clearTimeout(t);
    }, [loading]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-pink-500 gap-3">
                <Loader2 className="w-8 h-8 motion-safe:animate-spin" />
                <p className="text-sm font-medium text-slate-500">Loading financial metrics...</p>
            </div>
        );
    }

    const netFlowNum = parseFloat(totals.net_cash_flow);
    const incomeNum = parseFloat(totals.income_total);
    const expenseNum = parseFloat(totals.expense_total);

    const hasIncome = incomeNum > 0;
    const spentPct = hasIncome ? (expenseNum / incomeNum) * 100 : expenseNum > 0 ? 100 : 0;
    const overspent = spentPct > 100;
    const barWidth = barReady ? Math.min(spentPct, 100) : 0;

    const spendingMessage = !hasIncome
        ? expenseNum > 0
            ? 'No income recorded this period, but you have expenses.'
            : 'No income or expenses recorded this period yet.'
        : overspent
            ? `You've spent ${spentPct.toFixed(0)}% of your income, which is more than you earned.`
            : `You've spent ${spentPct.toFixed(0)}% of your income this period.`;

    return (
        <div className="rounded-3xl bg-gradient-to-br from-pink-50 via-white to-fuchsia-50 border border-pink-100 p-6 sm:p-8 space-y-8 motion-safe:animate-rise">
            {/* Header Section */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-pink-100 pb-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-pink-500 via-fuchsia-500 to-rose-500 rounded-2xl shadow-lg shadow-pink-500/30 motion-safe:animate-float">
                        <PiggyBank className="w-7 h-7 text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Financial dashboard</h2>
                        <p className="text-sm text-slate-500 mt-0.5">Overview of your cash flow and active budget performance.</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-pink-700 font-mono bg-white px-3.5 py-2 rounded-xl border border-pink-200 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-pink-500 motion-safe:animate-pulse"></span>
                    <span>Period: {startDate} → {endDate}</span>
                </div>
            </div>

            {/* Summary Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Total Income */}
                <div className="relative overflow-hidden bg-white border border-pink-100 rounded-2xl p-6 shadow-lg shadow-pink-200/40 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-pink-300/40">
                    <div className="absolute -top-8 -right-8 w-28 h-28 rounded-full bg-emerald-300/20 blur-2xl" />
                    <div className="relative flex items-center justify-between mb-4">
                        <span className="text-slate-500 text-sm font-medium">Total income</span>
                        <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
                            <ArrowUpRight className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="relative text-3xl font-extrabold text-slate-900 tracking-tight">
                        <span className="text-sm font-medium text-slate-400 mr-1.5">ZMW</span>
                        {totals.income_total}
                    </p>
                </div>

                {/* Total Expenses */}
                <div className="relative overflow-hidden bg-white border border-pink-100 rounded-2xl p-6 shadow-lg shadow-pink-200/40 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-pink-300/40">
                    <div className="absolute -top-8 -right-8 w-28 h-28 rounded-full bg-rose-300/25 blur-2xl" />
                    <div className="relative flex items-center justify-between mb-4">
                        <span className="text-slate-500 text-sm font-medium">Total expenses</span>
                        <div className="p-2.5 bg-rose-50 text-rose-500 rounded-xl border border-rose-100">
                            <ArrowDownRight className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="relative text-3xl font-extrabold text-slate-900 tracking-tight">
                        <span className="text-sm font-medium text-slate-400 mr-1.5">ZMW</span>
                        {totals.expense_total}
                    </p>
                </div>

                {/* Net Cash Flow */}
                <div className="relative overflow-hidden bg-gradient-to-br from-pink-500 via-fuchsia-600 to-rose-600 rounded-2xl p-6 shadow-lg shadow-pink-500/30 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-pink-500/40">
                    <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/20 blur-2xl" />
                    <div className="relative flex items-center justify-between mb-4">
                        <span className="text-pink-50 text-sm font-medium">Net cash flow</span>
                        <div className="p-2.5 bg-white/20 text-white rounded-xl border border-white/30">
                            <Wallet className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="relative text-3xl font-extrabold text-white tracking-tight">
                        <span className="text-sm font-medium text-pink-100 mr-1.5">ZMW</span>
                        {totals.net_cash_flow}
                    </p>
                    <p className="relative mt-2 text-xs font-medium text-pink-100">
                        {netFlowNum >= 0 ? 'You are in the green this period' : 'You are spending more than you earn'}
                    </p>
                </div>
            </div>

            {/* Spending vs income */}
            <div className="bg-white border border-pink-100 rounded-2xl p-6 shadow-lg shadow-pink-200/40">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-pink-50 text-pink-600 rounded-xl border border-pink-100">
                            <Coins className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-base font-semibold text-slate-900">Spending vs income</h3>
                            <p className="text-sm text-slate-500">{spendingMessage}</p>
                        </div>
                    </div>
                    <span className={`text-2xl font-extrabold ${overspent ? 'text-rose-600' : 'text-pink-600'}`}>
                        {spentPct.toFixed(0)}%
                    </span>
                </div>
                <div
                    className="h-3 w-full bg-pink-100 rounded-full overflow-hidden"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.min(Math.round(spentPct), 100)}
                    aria-label="Share of income spent this period"
                >
                    <div
                        className={`h-full rounded-full transition-all duration-1000 ease-out ${overspent
                            ? 'bg-gradient-to-r from-rose-500 to-red-600'
                            : 'bg-gradient-to-r from-pink-400 via-fuchsia-500 to-rose-500'
                            }`}
                        style={{ width: `${barWidth}%` }}
                    />
                </div>
            </div>
        </div>
    );
};