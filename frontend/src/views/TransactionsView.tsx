import React, { useEffect, useState } from 'react';
import { Plus, Receipt, Trash2, Filter, PiggyBank, Loader2 } from 'lucide-react';
import { transactionsApi } from '../api/transactions';
import type { Transaction, Category } from '../types';

const inputClass =
    'w-full bg-pink-50/60 border border-pink-200 rounded-xl px-4 py-2.5 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-pink-500 focus:ring-4 focus:ring-pink-500/15 transition';
const filterClass =
    'bg-pink-50/60 border border-pink-200 rounded-xl px-3 py-2 text-slate-900 text-sm focus:outline-none focus:bg-white focus:border-pink-500 focus:ring-4 focus:ring-pink-500/15 transition';
const labelClass = 'block text-sm font-medium text-slate-700 mb-1.5';
const primaryBtn =
    'inline-flex items-center justify-center gap-2 bg-gradient-to-r from-pink-500 via-fuchsia-500 to-rose-500 hover:from-pink-600 hover:via-fuchsia-600 hover:to-rose-600 text-white font-semibold rounded-xl shadow-lg shadow-pink-500/30 transition active:scale-[0.98] focus:outline-none focus:ring-4 focus:ring-pink-500/30';
const ghostBtn =
    'px-4 py-2 bg-pink-50 text-pink-700 border border-pink-200 rounded-xl text-sm font-medium hover:bg-pink-100 transition focus:outline-none focus:ring-4 focus:ring-pink-500/15';

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
        <div className="rounded-3xl bg-gradient-to-br from-pink-50 via-white to-fuchsia-50 border border-pink-100 p-6 sm:p-8 space-y-8 motion-safe:animate-rise">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-pink-100 pb-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-pink-500 via-fuchsia-500 to-rose-500 rounded-2xl shadow-lg shadow-pink-500/30">
                        <Receipt className="w-7 h-7 text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Transactions</h2>
                        <p className="text-sm text-slate-500 mt-0.5">Manage income records and expense entries.</p>
                    </div>
                </div>
                <button onClick={() => setShowModal(true)} className={`${primaryBtn} px-5 py-2.5`}>
                    <Plus className="w-4 h-4" /> Add transaction
                </button>
            </div>

            {/* Filter Toolbar */}
            <div className="bg-white border border-pink-100 rounded-2xl p-4 shadow-lg shadow-pink-200/40 flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2 text-pink-600 text-sm font-medium">
                    <Filter className="w-4 h-4" /> Filters
                </div>
                <select
                    aria-label="Filter by type"
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className={filterClass}
                >
                    <option value="">All types</option>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                </select>

                <select
                    aria-label="Filter by category"
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className={filterClass}
                >
                    <option value="">All categories</option>
                    {categories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
            </div>

            {/* Transactions Table */}
            <div className="bg-white border border-pink-100 rounded-2xl shadow-lg shadow-pink-200/40 overflow-hidden">
                {loading ? (
                    <div className="py-14 flex flex-col items-center gap-3 text-pink-500">
                        <Loader2 className="w-8 h-8 motion-safe:animate-spin" />
                        <p className="text-sm font-medium text-slate-500">Loading transactions...</p>
                    </div>
                ) : transactions.length === 0 ? (
                    <div className="py-14 flex flex-col items-center gap-3 text-center text-slate-500">
                        <div className="p-4 bg-pink-50 rounded-full">
                            <PiggyBank className="w-8 h-8 text-pink-500 motion-safe:animate-float" />
                        </div>
                        <p>No transactions recorded.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-pink-100 text-xs text-pink-700 bg-pink-50">
                                    <th className="p-4 font-semibold">Date</th>
                                    <th className="p-4 font-semibold">Type</th>
                                    <th className="p-4 font-semibold">Category</th>
                                    <th className="p-4 font-semibold">Note</th>
                                    <th className="p-4 font-semibold text-right">Amount</th>
                                    <th className="p-4 font-semibold text-center">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-pink-100 text-sm">
                                {transactions.map((tx) => (
                                    <tr key={tx.id} className="hover:bg-pink-50/60 transition-colors">
                                        <td className="p-4 text-slate-500 font-mono text-xs">{tx.transaction_date}</td>
                                        <td className="p-4">
                                            <span
                                                className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize border ${tx.type === 'income'
                                                    ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                                                    : 'bg-rose-50 text-rose-600 border-rose-200'
                                                    }`}
                                            >
                                                {tx.type}
                                            </span>
                                        </td>
                                        <td className="p-4 text-slate-900 font-medium">{tx.category?.name || 'Uncategorized'}</td>
                                        <td className="p-4 text-slate-500">{tx.note || '—'}</td>
                                        <td className={`p-4 text-right font-bold ${tx.type === 'income' ? 'text-emerald-600' : 'text-rose-600'}`}>
                                            {tx.type === 'income' ? '+' : '-'}ZMW {tx.amount}
                                        </td>
                                        <td className="p-4 text-center">
                                            <button
                                                onClick={() => handleDelete(tx.id)}
                                                className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-rose-300"
                                                title="Delete transaction"
                                                aria-label="Delete transaction"
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
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="tx-modal-title"
                        className="bg-white border border-pink-100 rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl shadow-pink-300/40 motion-safe:animate-rise"
                    >
                        <h3 id="tx-modal-title" className="text-lg font-bold text-slate-900">Add transaction</h3>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label htmlFor="tx-type" className={labelClass}>Type</label>
                                <select
                                    id="tx-type"
                                    value={type}
                                    onChange={(e) => {
                                        const val = e.target.value as 'income' | 'expense';
                                        setType(val);
                                        const filtered = categories.filter(c => c.type === val);
                                        if (filtered.length > 0) setCategoryId(filtered[0].id);
                                    }}
                                    className={inputClass}
                                >
                                    <option value="expense">Expense</option>
                                    <option value="income">Income</option>
                                </select>
                            </div>

                            <div>
                                <label htmlFor="tx-category" className={labelClass}>Category</label>
                                <select
                                    id="tx-category"
                                    value={categoryId}
                                    onChange={(e) => setCategoryId(Number(e.target.value))}
                                    className={inputClass}
                                >
                                    {categories.filter(c => c.type === type).map((c) => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label htmlFor="tx-amount" className={labelClass}>Amount (ZMW)</label>
                                <input
                                    id="tx-amount"
                                    type="number"
                                    step="0.01"
                                    required
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    placeholder="0.00"
                                    className={inputClass}
                                />
                            </div>

                            <div>
                                <label htmlFor="tx-date" className={labelClass}>Date</label>
                                <input
                                    id="tx-date"
                                    type="date"
                                    required
                                    value={transactionDate}
                                    onChange={(e) => setTransactionDate(e.target.value)}
                                    className={inputClass}
                                />
                            </div>

                            <div>
                                <label htmlFor="tx-note" className={labelClass}>Note (optional)</label>
                                <input
                                    id="tx-note"
                                    type="text"
                                    value={note}
                                    onChange={(e) => setNote(e.target.value)}
                                    placeholder="e.g. Grocery shopping"
                                    className={inputClass}
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button type="button" onClick={() => setShowModal(false)} className={ghostBtn}>
                                    Cancel
                                </button>
                                <button type="submit" className={`${primaryBtn} px-4 py-2 text-sm`}>
                                    Save transaction
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};