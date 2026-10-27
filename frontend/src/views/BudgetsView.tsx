import React, { useEffect, useState } from 'react';
import { PieChart, Plus, AlertCircle, PiggyBank, Loader2 } from 'lucide-react';
import { budgetsApi } from '../api/budgets';
import { transactionsApi } from '../api/transactions';
import type { Budget, Category } from '../types';

const inputClass =
    'w-full bg-pink-50/60 border border-pink-200 rounded-xl px-4 py-2.5 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-pink-500 focus:ring-4 focus:ring-pink-500/15 transition';
const labelClass = 'block text-sm font-medium text-slate-700 mb-1.5';
const primaryBtn =
    'inline-flex items-center justify-center gap-2 bg-gradient-to-r from-pink-500 via-fuchsia-500 to-rose-500 hover:from-pink-600 hover:via-fuchsia-600 hover:to-rose-600 text-white font-semibold rounded-xl shadow-lg shadow-pink-500/30 transition active:scale-[0.98] focus:outline-none focus:ring-4 focus:ring-pink-500/30';
const ghostBtn =
    'px-4 py-2 bg-pink-50 text-pink-700 border border-pink-200 rounded-xl text-sm font-medium hover:bg-pink-100 transition focus:outline-none focus:ring-4 focus:ring-pink-500/15';

export const BudgetsView: React.FC = () => {
    const [budgets, setBudgets] = useState<Budget[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [barsReady, setBarsReady] = useState(false);

    // Form state
    const [categoryId, setCategoryId] = useState<number>(0);
    const [amount, setAmount] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const loadData = async () => {
        try {
            setLoading(true);
            const [budgetsData, catsData] = await Promise.all([
                budgetsApi.list(),
                transactionsApi.getCategories(),
            ]);
            setBudgets(budgetsData);
            setCategories(catsData.filter(c => c.type === 'expense'));
            if (catsData.length > 0) setCategoryId(catsData[0].id);
        } catch (error) {
            console.error('Failed to load budgets:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    // Let the progress bars animate from 0 once the data has rendered
    useEffect(() => {
        if (loading) return;
        const t = setTimeout(() => setBarsReady(true), 150);
        return () => clearTimeout(t);
    }, [loading]);

    const handleCreateBudget = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await budgetsApi.create({
                category_id: categoryId,
                amount,
                start_date: startDate,
                end_date: endDate,
            });
            setShowModal(false);
            setAmount('');
            loadData();
        } catch (error) {
            console.error('Failed to create budget:', error);
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm('Are you sure you want to delete this budget?')) {
            await budgetsApi.delete(id);
            loadData();
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-pink-500 gap-3">
                <Loader2 className="w-8 h-8 motion-safe:animate-spin" />
                <p className="text-sm font-medium text-slate-500">Loading budgets...</p>
            </div>
        );
    }

    return (
        <div className="rounded-3xl bg-gradient-to-br from-pink-50 via-white to-fuchsia-50 border border-pink-100 p-6 sm:p-8 space-y-8 motion-safe:animate-rise">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-pink-100 pb-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-pink-500 via-fuchsia-500 to-rose-500 rounded-2xl shadow-lg shadow-pink-500/30">
                        <PieChart className="w-7 h-7 text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Category budgets</h2>
                        <p className="text-sm text-slate-500 mt-0.5">Track spending limits and monitor overages.</p>
                    </div>
                </div>
                <button onClick={() => setShowModal(true)} className={`${primaryBtn} px-5 py-2.5`}>
                    <Plus className="w-4 h-4" /> Add budget
                </button>
            </div>

            {/* Budgets Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {budgets.map((budget) => {
                    const usedPct = budget.used_pct || 0;
                    const isOver = budget.is_over;
                    return (
                        <div
                            key={budget.id}
                            className="relative overflow-hidden bg-white border border-pink-100 rounded-2xl p-6 shadow-lg shadow-pink-200/40 flex flex-col justify-between transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-pink-300/40"
                        >
                            {isOver && (
                                <div className="absolute top-0 right-0 bg-rose-50 text-rose-600 border-b border-l border-rose-200 px-3 py-1 rounded-bl-xl text-xs font-semibold flex items-center gap-1">
                                    <AlertCircle className="w-3.5 h-3.5" /> Overspent
                                </div>
                            )}

                            <div>
                                <div className="flex items-center gap-3 mb-5">
                                    <div className="p-2.5 bg-pink-50 text-pink-600 rounded-xl border border-pink-100">
                                        <PieChart className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-slate-900">{budget.category?.name || 'Category'}</h3>
                                        <p className="text-xs text-slate-500">{budget.start_date} to {budget.end_date}</p>
                                    </div>
                                </div>

                                <div className="space-y-2 mb-4">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-500">Spent: ZMW {budget.used || '0.00'}</span>
                                        <span className="text-slate-900 font-medium">Limit: ZMW {budget.amount}</span>
                                    </div>
                                    <div
                                        className="w-full bg-pink-100 rounded-full h-2.5 overflow-hidden"
                                        role="progressbar"
                                        aria-valuemin={0}
                                        aria-valuemax={100}
                                        aria-valuenow={Math.min(Math.round(usedPct), 100)}
                                        aria-label={`${budget.category?.name || 'Category'} budget used`}
                                    >
                                        <div
                                            className={`h-2.5 rounded-full transition-all duration-1000 ease-out ${isOver
                                                ? 'bg-gradient-to-r from-rose-500 to-red-600'
                                                : 'bg-gradient-to-r from-pink-400 via-fuchsia-500 to-rose-500'
                                                }`}
                                            style={{ width: `${barsReady ? Math.min(usedPct, 100) : 0}%` }}
                                        />
                                    </div>
                                    <p className={`text-right text-xs font-semibold ${isOver ? 'text-rose-600' : 'text-pink-600'}`}>
                                        {Math.round(usedPct)}% used
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-pink-100 text-xs">
                                <span className={isOver ? 'text-rose-600 font-medium' : 'text-slate-500'}>
                                    {isOver ? `Over by ZMW ${Math.abs(parseFloat(budget.remaining || '0'))}` : `ZMW ${budget.remaining || '0.00'} remaining`}
                                </span>
                                <button
                                    onClick={() => handleDelete(budget.id)}
                                    className="text-slate-400 hover:text-rose-500 font-medium transition-colors focus:outline-none focus:underline"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    );
                })}

                {budgets.length === 0 && (
                    <div className="col-span-full py-14 flex flex-col items-center gap-3 text-center text-slate-500 bg-white/70 border border-dashed border-pink-200 rounded-2xl">
                        <div className="p-4 bg-pink-50 rounded-full">
                            <PiggyBank className="w-8 h-8 text-pink-500 motion-safe:animate-float" />
                        </div>
                        <p>No budgets configured yet. Click "Add budget" to get started.</p>
                    </div>
                )}
            </div>

            {/* Add Budget Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="budget-modal-title"
                        className="bg-white border border-pink-100 rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl shadow-pink-300/40 motion-safe:animate-rise"
                    >
                        <h3 id="budget-modal-title" className="text-lg font-bold text-slate-900">Create new budget</h3>
                        <form onSubmit={handleCreateBudget} className="space-y-4">
                            <div>
                                <label htmlFor="budget-category" className={labelClass}>Category</label>
                                <select
                                    id="budget-category"
                                    value={categoryId}
                                    onChange={(e) => setCategoryId(Number(e.target.value))}
                                    className={inputClass}
                                >
                                    {categories.map((c) => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label htmlFor="budget-amount" className={labelClass}>Limit amount (ZMW)</label>
                                <input
                                    id="budget-amount"
                                    type="number"
                                    step="0.01"
                                    required
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    placeholder="0.00"
                                    className={inputClass}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label htmlFor="budget-start" className={labelClass}>Start date</label>
                                    <input
                                        id="budget-start"
                                        type="date"
                                        required
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        className={inputClass}
                                    />
                                </div>
                                <div>
                                    <label htmlFor="budget-end" className={labelClass}>End date</label>
                                    <input
                                        id="budget-end"
                                        type="date"
                                        required
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        className={inputClass}
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button type="button" onClick={() => setShowModal(false)} className={ghostBtn}>
                                    Cancel
                                </button>
                                <button type="submit" className={`${primaryBtn} px-4 py-2 text-sm`}>
                                    Save budget
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};