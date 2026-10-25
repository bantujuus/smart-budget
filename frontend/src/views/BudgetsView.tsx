import React, { useEffect, useState } from 'react';
import { PieChart, Plus, AlertCircle } from 'lucide-react';
import { budgetsApi } from '../api/budgets';
import { transactionsApi } from '../api/transactions';
import type { Budget, Category } from '../types';

export const BudgetsView: React.FC = () => {
    const [budgets, setBudgets] = useState<Budget[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

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

    if (loading) return <div className="p-8 text-center text-slate-400">Loading Budgets...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">Category Budgets</h2>
                    <p className="text-sm text-slate-400">Track spending limits and monitor overages.</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl font-medium transition-colors"
                >
                    <Plus className="w-4 h-4" /> Add Budget
                </button>
            </div>

            {/* Budgets Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {budgets.map((budget) => {
                    const usedPct = budget.used_pct || 0;
                    const isOver = budget.is_over;
                    return (
                        <div key={budget.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between">
                            {isOver && (
                                <div className="absolute top-0 right-0 bg-rose-500/10 text-rose-400 border-b border-l border-rose-500/20 px-3 py-1 rounded-bl-xl text-xs font-semibold flex items-center gap-1">
                                    <AlertCircle className="w-3.5 h-3.5" /> Overspent
                                </div>
                            )}

                            <div>
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="p-2 bg-slate-800 rounded-xl text-indigo-400">
                                        <PieChart className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-white">{budget.category?.name || 'Category'}</h3>
                                        <p className="text-xs text-slate-400">{budget.start_date} to {budget.end_date}</p>
                                    </div>
                                </div>

                                <div className="space-y-2 mb-4">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Spent: ZMW {budget.used || '0.00'}</span>
                                        <span className="text-white font-medium">Limit: ZMW {budget.amount}</span>
                                    </div>
                                    <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                                        <div
                                            className={`h-2.5 rounded-full transition-all ${isOver ? 'bg-rose-500' : 'bg-indigo-600'}`}
                                            style={{ width: `${Math.min(usedPct, 100)}%` }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-slate-800/60 text-xs">
                                <span className={isOver ? 'text-rose-400 font-medium' : 'text-slate-400'}>
                                    {isOver ? `Over by ZMW ${Math.abs(parseFloat(budget.remaining || '0'))}` : `ZMW ${budget.remaining || '0.00'} remaining`}
                                </span>
                                <button
                                    onClick={() => handleDelete(budget.id)}
                                    className="text-slate-500 hover:text-rose-400 transition-colors"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    );
                })}

                {budgets.length === 0 && (
                    <div className="col-span-full py-12 text-center text-slate-500 bg-slate-900/50 border border-slate-800 rounded-2xl">
                        No budgets configured yet. Click "Add Budget" to get started.
                    </div>
                )}
            </div>

            {/* Add Budget Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-6">
                        <h3 className="text-lg font-bold text-white">Create New Budget</h3>
                        <form onSubmit={handleCreateBudget} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Category</label>
                                <select
                                    value={categoryId}
                                    onChange={(e) => setCategoryId(Number(e.target.value))}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                >
                                    {categories.map((c) => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Limit Amount (ZMW)</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    required
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    placeholder="0.00"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1">Start Date</label>
                                    <input
                                        type="date"
                                        required
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1">End Date</label>
                                    <input
                                        type="date"
                                        required
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-sm font-medium hover:bg-slate-700"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-500"
                                >
                                    Save Budget
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};