import React, { useEffect, useState } from 'react';
import { BarChart2, PieChart, TrendingUp, AlertTriangle } from 'lucide-react';
import { reportsApi } from '../api/reports';
import type { CategorySummary, CategoryInsight } from '../types';

export const ReportsView: React.FC = () => {
    const [summary, setSummary] = useState<CategorySummary[]>([]);
    const [insights, setInsights] = useState<{ category_changes: CategoryInsight[]; overspent_count: number } | null>(null);
    const [loading, setLoading] = useState(true);

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

    if (loading) return <div className="p-8 text-center text-slate-400">Loading Reports & Analytics...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">Reports & Insights</h2>
                    <p className="text-sm text-slate-400">Analyze spending shares and financial patterns.</p>
                </div>
                <span className="text-xs text-slate-400 font-mono bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
                    Period: {startDate} to {endDate}
                </span>
            </div>

            {/* Insights Banner */}
            {insights && insights.overspent_count > 0 && (
                <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-4 flex items-center gap-3 text-rose-400">
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                    <p className="text-sm">You currently have <strong>{insights.overspent_count}</strong> overspent budget category requiring attention.</p>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Share Breakdown */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                            <PieChart className="w-5 h-5" />
                        </div>
                        <h3 className="font-bold text-white">Spending by Category</h3>
                    </div>

                    <div className="space-y-3 pt-2">
                        {summary.map((item) => (
                            <div key={item.category_id} className="space-y-1">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-300 font-medium">{item.category_name}</span>
                                    <span className="text-slate-400">ZMW {item.total_amount} ({item.percentage_share}%)</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-indigo-600 h-2 rounded-full"
                                        style={{ width: `${Math.min(item.percentage_share, 100)}%` }}
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
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl">
                            <TrendingUp className="w-5 h-5" />
                        </div>
                        <h3 className="font-bold text-white">Period Comparisons</h3>
                    </div>

                    <div className="space-y-3 pt-2">
                        {insights?.category_changes?.map((change, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-slate-800/40 rounded-xl">
                                <div>
                                    <p className="font-medium text-white text-sm">{change.category_name}</p>
                                    <p className="text-xs text-slate-400">Current: ZMW {change.current_period} | Previous: ZMW {change.previous_period}</p>
                                </div>
                                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${change.percentage_change >= 0 ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'
                                    }`}>
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