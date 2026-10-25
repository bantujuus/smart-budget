import React, { useEffect, useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Wallet, TrendingUp, Loader2 } from 'lucide-react';
import { reportsApi } from '../api/reports';
import type { DashboardTotals } from '../types';

export const DashboardView: React.FC = () => {
    const [totals, setTotals] = useState<DashboardTotals>({ income_total: '0.00', expense_total: '0.00', net_cash_flow: '0.00' });
    const [loading, setLoading] = useState(true);

    // Default filter to current month
    const now = new Date();
    const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];

    useEffect(() => {
        reportsApi.getDashboardTotals(startDate, endDate)
            .then(setTotals)
            .finally(() => setLoading(false));
    }, [startDate, endDate]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400 gap-3">
                <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
                <p className="text-sm font-medium">Loading financial metrics...</p>
            </div>
        );
    }

    const netFlowNum = parseFloat(totals.net_cash_flow);

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header Section */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <TrendingUp className="w-6 h-6 text-cyan-400" />
                        Financial Dashboard
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">Overview of your cash flow and active budget performance.</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-300 font-mono bg-slate-900/90 px-3.5 py-2 rounded-xl border border-slate-800 shadow-inner">
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                    <span>Period: {startDate} → {endDate}</span>
                </div>
            </div>

            {/* Summary Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Total Income */}
                <div className="relative group bg-slate-900/80 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 shadow-lg shadow-cyan-950/10 transition-all duration-300 hover:border-slate-700 hover:shadow-cyan-900/20">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-all"></div>
                    <div className="flex items-center justify-between mb-4 relative z-10">
                        <span className="text-slate-400 text-xs font-semibold tracking-wider uppercase">Total Income</span>
                        <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                            <ArrowUpRight className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-extrabold text-white tracking-tight relative z-10">
                        <span className="text-sm font-medium text-slate-400 mr-1.5">ZMW</span>
                        {totals.income_total}
                    </p>
                </div>

                {/* Total Expenses */}
                <div className="relative group bg-slate-900/80 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 shadow-lg shadow-rose-950/10 transition-all duration-300 hover:border-slate-700 hover:shadow-rose-900/20">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/5 rounded-full blur-2xl group-hover:bg-rose-500/10 transition-all"></div>
                    <div className="flex items-center justify-between mb-4 relative z-10">
                        <span className="text-slate-400 text-xs font-semibold tracking-wider uppercase">Total Expenses</span>
                        <div className="p-2.5 bg-rose-500/10 text-rose-400 rounded-xl border border-rose-500/20">
                            <ArrowDownRight className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-extrabold text-white tracking-tight relative z-10">
                        <span className="text-sm font-medium text-slate-400 mr-1.5">ZMW</span>
                        {totals.expense_total}
                    </p>
                </div>

                {/* Net Cash Flow */}
                <div className="relative group bg-slate-900/80 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 shadow-lg shadow-indigo-950/10 transition-all duration-300 hover:border-slate-700 hover:shadow-indigo-900/20">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-all"></div>
                    <div className="flex items-center justify-between mb-4 relative z-10">
                        <span className="text-slate-400 text-xs font-semibold tracking-wider uppercase">Net Cash Flow</span>
                        <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
                            <Wallet className="w-5 h-5" />
                        </div>
                    </div>
                    <p className={`text-3xl font-extrabold tracking-tight relative z-10 ${netFlowNum >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        <span className="text-sm font-medium text-slate-400 mr-1.5">ZMW</span>
                        {totals.net_cash_flow}
                    </p>
                </div>
            </div>
        </div>
    );
};