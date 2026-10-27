import React, { useEffect, useState } from 'react';
import { BarChart2, PieChart, TrendingUp, AlertTriangle, Loader2 } from 'lucide-react';
import { reportsApi } from '../api/reports';
import type { CategorySummary, CategoryInsight } from '../types';

export const ReportsView: React.FC = () => {
    const [summary, setSummary] = useState<CategorySummary[]>([]);
    const [insights, setInsights] = useState<{ category_changes: CategoryInsight[]; overspent_count: number } | null>(null);
    const [loading, setLoading] = useState(true);
    const [barsReady, setBarsReady] = useState(false);

    const now = new Date();
    const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];

    useEffect(() => {
        Promise.all([
            reportsApi.getCategorySummary(startDate, endDate),
            reportsApi.getInsights(),
        ])
            .then(([summaryData, insightsData]) => {
                setSummary(summaryData);
                setInsights(insightsData);
            })
            .finally(() => setLoading(false));
    }, [startDate, endDate]);

    // Let the share bars animate from 0 once the data has rendered
    useEffect(() => {
        if (loading) return;
        const t = setTimeout(() => setBarsReady(true), 150);
        return () => clearTimeout(t);
    }, [loading]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-pink-500 gap-3">
                <Loader2 className="w-8 h-8 motion-safe:animate-spin" />
                <p className="text-sm font-medium text-slate-500">Loading reports and analytics...</p>
            </div>
        );
    }

    const overspent = insights?.overspent_count ?? 0;

    return (
        <div className="rounded-3xl bg-gradient-to-br from-pink-50 via-white to-fuchsia-50 border border-pink-100 p-6 sm:p-8 space-y-8 motion-safe:animate-rise">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-pink-100 pb-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-pink-500 via-fuchsia-500 to-rose-500 rounded-2xl shadow-lg shadow-pink-500/30">
                        <BarChart2 className="w-7 h-7 text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Reports & insights</h2>
                        <p className="text-sm text-slate-500 mt-0.5">Analyze spending shares and financial patterns.</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-pink-700 font-mono bg-white px-3.5 py-2 rounded-xl border border-pink-200 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-pink-500 motion-safe:animate-pulse"></span>
                    <span>Period: {startDate} to {endDate}</span>
                </div>
            </div>

            {/* Insights Banner */}
            {insights && overspent > 0 && (
                <div role="alert" className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-center gap-3 text-rose-600">
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                    <p className="text-sm">
                        You currently have <strong>{overspent}</strong> overspent budget {overspent === 1 ? 'category' : 'categories'} requiring attention.
                    </p>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Share Breakdown */}
                <div className="bg-white border border-pink-100 rounded-2xl p-6 shadow-lg shadow-pink-200/40 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-pink-50 text-pink-600 rounded-xl border border-pink-100">
                            <PieChart className="w-5 h-5" />
                        </div>
                        <h3 className="font-bold text-slate-900">Spending by category</h3>
                    </div>

                    <div className="space-y-4 pt-2">
                        {summary.map((item) => (
                            <div key={item.category_id} className="space-y-1.5">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-900 font-medium">{item.category_name}</span>
                                    <span className="text-slate-500">ZMW {item.total_amount} ({item.percentage_share}%)</span>
                                </div>
                                <div
                                    className="w-full bg-pink-100 rounded-full h-2.5 overflow-hidden"
                                    role="progressbar"
                                    aria-valuemin={0}
                                    aria-valuemax={100}
                                    aria-valuenow={Math.min(item.percentage_share, 100)}
                                    aria-label={`${item.category_name} share of spending`}
                                >
                                    <div
                                        className="bg-gradient-to-r from-pink-400 via-fuchsia-500 to-rose-500 h-2.5 rounded-full transition-all duration-1000 ease-out"
                                        style={{ width: `${barsReady ? Math.min(item.percentage_share, 100) : 0}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                        {summary.length === 0 && (
                            <p className="text-center text-slate-500 py-6">No category summary data available for this period.</p>
                        )}
                    </div>
                </div>

                {/* Period Trend Comparisons */}
                <div className="bg-white border border-pink-100 rounded-2xl p-6 shadow-lg shadow-pink-200/40 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-fuchsia-50 text-fuchsia-600 rounded-xl border border-fuchsia-100">
                            <TrendingUp className="w-5 h-5" />
                        </div>
                        <h3 className="font-bold text-slate-900">Period comparisons</h3>
                    </div>

                    <div className="space-y-3 pt-2">
                        {insights?.category_changes?.map((change, idx) => (
                            <div key={idx} className="flex items-center justify-between gap-3 p-3.5 bg-pink-50/60 border border-pink-100 rounded-xl">
                                <div>
                                    <p className="font-medium text-slate-900 text-sm">{change.category_name}</p>
                                    <p className="text-xs text-slate-500">Current: ZMW {change.current_period} | Previous: ZMW {change.previous_period}</p>
                                </div>
                                <span
                                    className={`text-xs font-semibold px-2.5 py-1 rounded-full border shrink-0 ${change.percentage_change >= 0
                                        ? 'bg-rose-50 text-rose-600 border-rose-200'
                                        : 'bg-emerald-50 text-emerald-600 border-emerald-200'
                                        }`}
                                >
                                    {change.percentage_change >= 0 ? `+${change.percentage_change}%` : `${change.percentage_change}%`}
                                </span>
                            </div>
                        ))}
                        {(!insights?.category_changes || insights.category_changes.length === 0) && (
                            <p className="text-center text-slate-500 py-6">No historical comparison data available.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};