import React, { useEffect, useState } from 'react';
import { Plus, Receipt, Trash2, Search, Filter } from 'lucide-react';
import { transactionsApi } from '../api/transactions';
import type { Transaction, Category } from '../types';

export const TransactionsView: React.FC = () => {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // Filters
    const [typeFilter, setTypeFilter] = useState<string>('');
    const [categoryFilter, setCategoryFilter] = useState<string>('');

    // Form state
    const [amount, setAmount] = useState('');
    const [type, setType] = useState<'income' | 'expense'>('expense');
    const [categoryId, setCategoryId] = useState<number>(0);
    const [transactionDate, setTransactionDate] = useState(new Date().toISOString().split('T')[0]);
    const [note, setNote] = useState('');

    const loadData = async () => {
        try {
            setLoading(true);
            const [txns, cats] = await Promise.all([
                transactionsApi.list({
                    type: typeFilter ? (typeFilter as 'income' | 'expense') : undefined,
                    category_id: categoryFilter ? Number(categoryFilter) : undefined,
                }),
                transactionsApi.getCategories(),
            ]);
            setTransactions(txns);
            setCategories(cats);
            if (cats.length > 0 && !categoryId) setCategoryId(cats[0].id);
        } catch (error) {
            console.error('Failed to load transactions:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [typeFilter, categoryFilter]);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await transactionsApi.create({
                amount,
                type,
                category_id: categoryId,
                transaction_date: transactionDate,
                note,
            });
            setShowModal(false);
            setAmount('');
            setNote('');
            loadData();
        } catch (error) {
            console.error('Failed to create transaction:', error);
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm('Are you sure you want to delete this transaction?')) {
            await transactionsApi.delete(id);
            loadData();
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white">Transactions</h2>
                    <p className="text-sm text-slate-400">Manage income records and expense entries.</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl font-medium transition-colors"
                >
                    <Plus className="w-4 h-4" /> Add Transaction
                </button>
            </div>

            {/* Filter Toolbar */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <Filter className="w-4 h-4" /> Filters:
                </div>
                <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                >
                    <option value="">All Types</option>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                </select>

                <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                >
                    <option value="">All Categories</option>
                    {categories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
            </div>

            {/* Transactions Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-slate-400">Loading transactions...</div>
                ) : transactions.length === 0 ? (
                    <div className="p-12 text-center text-slate-500">No transactions recorded.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase bg-slate-900/50">
                                    <th className="p-4 font-semibold">Date</th>
                                    <th className="p-4 font-semibold">Type</th>
                                    <th className="p-4 font-semibold">Category</th>
                                    <th className="p-4 font-semibold">Note</th>
                                    <th className="p-4 font-semibold text-right">Amount</th>
                                    <th className="p-4 font-semibold text-center">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800 text-sm">
                                {transactions.map((tx) => (
                                    <tr key={tx.id} className="hover:bg-slate-800/40 transition-colors">
                                        <td className="p-4 text-slate-300 font-mono text-xs">{tx.transaction_date}</td>
                                        <td className="p-4">
                                            <span className={`inline-px px-2.5 py-1 rounded-full text-xs font-medium uppercase ${tx.type === 'income' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                                                }`}>
                                                {tx.type}
                                            </span>
                                        </td>
                                        <td className="p-4 text-white font-medium">{tx.category?.name || 'Uncategorized'}</td>
                                        <td className="p-4 text-slate-400">{tx.note || '—'}</td>
                                        <td className={`p-4 text-right font-bold ${tx.type === 'income' ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {tx.type === 'income' ? '+' : '-'}ZMW {tx.amount}
                                        </td>
                                        <td className="p-4 text-center">
                                            <button
                                                onClick={() => handleDelete(tx.id)}
                                                className="p-2 text-slate-500 hover:text-rose-400 transition-colors"
                                                title="Delete Transaction"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Add Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-6">
                        <h3 className="text-lg font-bold text-white">Add Transaction</h3>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Type</label>
                                <select
                                    value={type}
                                    onChange={(e) => {
                                        const val = e.target.value as 'income' | 'expense';
                                        setType(val);
                                        const filtered = categories.filter(c => c.type === val);
                                        if (filtered.length > 0) setCategoryId(filtered[0].id);
                                    }}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                >
                                    <option value="expense">Expense</option>
                                    <option value="income">Income</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Category</label>
                                <select
                                    value={categoryId}
                                    onChange={(e) => setCategoryId(Number(e.target.value))}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                >
                                    {categories.filter(c => c.type === type).map((c) => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Amount (ZMW)</label>
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

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Date</label>
                                <input
                                    type="date"
                                    required
                                    value={transactionDate}
                                    onChange={(e) => setTransactionDate(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Note (Optional)</label>
                                <input
                                    type="text"
                                    value={note}
                                    onChange={(e) => setNote(e.target.value)}
                                    placeholder="e.g. Grocery shopping"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
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
                                    Save Transaction
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};