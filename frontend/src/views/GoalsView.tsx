import React, { useEffect, useState } from 'react';
import { Target, Plus, TrendingUp, CheckCircle, Clock, PiggyBank, Loader2 } from 'lucide-react';
import { goalsApi } from '../api/goals';
import type { SavingsGoal } from '../types';

const inputClass =
    'w-full bg-pink-50/60 border border-pink-200 rounded-xl px-4 py-2.5 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-pink-500 focus:ring-4 focus:ring-pink-500/15 transition';
const labelClass = 'block text-sm font-medium text-slate-700 mb-1.5';
const primaryBtn =
    'inline-flex items-center justify-center gap-2 bg-gradient-to-r from-pink-500 via-fuchsia-500 to-rose-500 hover:from-pink-600 hover:via-fuchsia-600 hover:to-rose-600 text-white font-semibold rounded-xl shadow-lg shadow-pink-500/30 transition active:scale-[0.98] focus:outline-none focus:ring-4 focus:ring-pink-500/30';
const ghostBtn =
    'px-4 py-2 bg-pink-50 text-pink-700 border border-pink-200 rounded-xl text-sm font-medium hover:bg-pink-100 transition focus:outline-none focus:ring-4 focus:ring-pink-500/15';

export const GoalsView: React.FC = () => {
    const [goals, setGoals] = useState<SavingsGoal[]>([]);
    const [loading, setLoading] = useState(true);
    const [barsReady, setBarsReady] = useState(false);

    // Goal modal state
    const [showGoalModal, setShowGoalModal] = useState(false);
    const [goalName, setGoalName] = useState('');
    const [targetAmount, setTargetAmount] = useState('');
    const [targetDate, setTargetDate] = useState('');

    // Contribution modal state
    const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);
    const [contribAmount, setContribAmount] = useState('');
    const [contribDate, setContribDate] = useState(
        new Date().toISOString().split('T')[0]
    );
    const [contribNote, setContribNote] = useState('');

    const loadGoals = async () => {
        try {
            setLoading(true);
            const data = await goalsApi.list();
            setGoals(data);
        } catch (error) {
            console.error('Failed to fetch goals:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadGoals();
    }, []);

    // Let the progress bars animate from 0 once the data has rendered
    useEffect(() => {
        if (loading) return;
        const t = setTimeout(() => setBarsReady(true), 150);
        return () => clearTimeout(t);
    }, [loading]);

    const handleCreateGoal = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await goalsApi.create({
                name: goalName,
                target_amount: targetAmount,
                target_date: targetDate,
            });
            setShowGoalModal(false);
            setGoalName('');
            setTargetAmount('');
            setTargetDate('');
            loadGoals();
        } catch (error) {
            console.error('Failed to create goal:', error);
        }
    };

    const handleAddContribution = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedGoalId) return;
        try {
            await goalsApi.addContribution(selectedGoalId, {
                amount: contribAmount,
                contribution_date: contribDate,
                note: contribNote,
            });
            setSelectedGoalId(null);
            setContribAmount('');
            setContribNote('');
            loadGoals();
        } catch (error) {
            console.error('Failed to add contribution:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-pink-500 gap-3">
                <Loader2 className="w-8 h-8 motion-safe:animate-spin" />
                <p className="text-sm font-medium text-slate-500">Loading savings goals...</p>
            </div>
        );
    }

    return (
        <div className="rounded-3xl bg-gradient-to-br from-pink-50 via-white to-fuchsia-50 border border-pink-100 p-6 sm:p-8 space-y-8 motion-safe:animate-rise">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-pink-100 pb-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-pink-500 via-fuchsia-500 to-rose-500 rounded-2xl shadow-lg shadow-pink-500/30">
                        <Target className="w-7 h-7 text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Savings goals</h2>
                        <p className="text-sm text-slate-500 mt-0.5">Set financial milestones and record progress.</p>
                    </div>
                </div>
                <button onClick={() => setShowGoalModal(true)} className={`${primaryBtn} px-5 py-2.5`}>
                    <Plus className="w-4 h-4" /> New goal
                </button>
            </div>

            {/* Goals Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {goals.map((goal) => {
                    const contributed = parseFloat(goal.goal_contributed || '0.00');
                    const target = parseFloat(goal.target_amount || '1.00');
                    const progress = goal.goal_progress ?? Math.min(Math.round((contributed / target) * 100), 100);
                    const isCompleted = goal.status === 'completed' || progress >= 100;

                    return (
                        <div
                            key={goal.id}
                            className="bg-white border border-pink-100 rounded-2xl p-6 shadow-lg shadow-pink-200/40 flex flex-col justify-between transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-pink-300/40"
                        >
                            <div>
                                <div className="flex items-start justify-between gap-3 mb-5">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2.5 bg-pink-50 text-pink-600 rounded-xl border border-pink-100">
                                            <Target className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-slate-900">{goal.name}</h3>
                                            <p className="text-xs text-slate-500">Target date: {goal.target_date}</p>
                                        </div>
                                    </div>
                                    {isCompleted ? (
                                        <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 font-medium shrink-0">
                                            <CheckCircle className="w-3.5 h-3.5" /> Completed
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-pink-50 text-pink-600 border border-pink-200 font-medium shrink-0">
                                            <Clock className="w-3.5 h-3.5" /> Active
                                        </span>
                                    )}
                                </div>

                                <div className="space-y-2 mb-6">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-500">Saved: ZMW {goal.goal_contributed || '0.00'}</span>
                                        <span className="text-slate-900 font-medium">Target: ZMW {goal.target_amount}</span>
                                    </div>
                                    <div
                                        className="w-full bg-pink-100 rounded-full h-2.5 overflow-hidden"
                                        role="progressbar"
                                        aria-valuemin={0}
                                        aria-valuemax={100}
                                        aria-valuenow={Math.min(progress, 100)}
                                        aria-label={`${goal.name} savings progress`}
                                    >
                                        <div
                                            className={`h-2.5 rounded-full transition-all duration-1000 ease-out ${isCompleted
                                                ? 'bg-gradient-to-r from-emerald-400 to-emerald-500'
                                                : 'bg-gradient-to-r from-pink-400 via-fuchsia-500 to-rose-500'
                                                }`}
                                            style={{ width: `${barsReady ? Math.min(progress, 100) : 0}%` }}
                                        />
                                    </div>
                                    <p className={`text-right text-xs font-semibold ${isCompleted ? 'text-emerald-600' : 'text-pink-600'}`}>
                                        {progress}% saved
                                    </p>
                                </div>
                            </div>

                            <button
                                onClick={() => setSelectedGoalId(goal.id)}
                                className="w-full py-2.5 bg-pink-50 hover:bg-pink-100 text-pink-700 border border-pink-200 rounded-xl text-sm font-semibold transition flex items-center justify-center gap-2 focus:outline-none focus:ring-4 focus:ring-pink-500/15"
                            >
                                <TrendingUp className="w-4 h-4 text-emerald-600" /> Add contribution
                            </button>
                        </div>
                    );
                })}

                {goals.length === 0 && (
                    <div className="col-span-full py-14 flex flex-col items-center gap-3 text-center text-slate-500 bg-white/70 border border-dashed border-pink-200 rounded-2xl">
                        <div className="p-4 bg-pink-50 rounded-full">
                            <PiggyBank className="w-8 h-8 text-pink-500 motion-safe:animate-float" />
                        </div>
                        <p>No savings goals established yet. Click "New goal" to get started.</p>
                    </div>
                )}
            </div>

            {/* New Goal Modal */}
            {showGoalModal && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="goal-modal-title"
                        className="bg-white border border-pink-100 rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl shadow-pink-300/40 motion-safe:animate-rise"
                    >
                        <h3 id="goal-modal-title" className="text-lg font-bold text-slate-900">Create savings goal</h3>
                        <form onSubmit={handleCreateGoal} className="space-y-4">
                            <div>
                                <label htmlFor="goal-name" className={labelClass}>Goal name</label>
                                <input
                                    id="goal-name"
                                    type="text"
                                    required
                                    value={goalName}
                                    onChange={(e) => setGoalName(e.target.value)}
                                    placeholder="e.g. Emergency Fund"
                                    className={inputClass}
                                />
                            </div>

                            <div>
                                <label htmlFor="goal-target" className={labelClass}>Target amount (ZMW)</label>
                                <input
                                    id="goal-target"
                                    type="number"
                                    step="0.01"
                                    required
                                    value={targetAmount}
                                    onChange={(e) => setTargetAmount(e.target.value)}
                                    placeholder="0.00"
                                    className={inputClass}
                                />
                            </div>

                            <div>
                                <label htmlFor="goal-date" className={labelClass}>Target date</label>
                                <input
                                    id="goal-date"
                                    type="date"
                                    required
                                    value={targetDate}
                                    onChange={(e) => setTargetDate(e.target.value)}
                                    className={inputClass}
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button type="button" onClick={() => setShowGoalModal(false)} className={ghostBtn}>
                                    Cancel
                                </button>
                                <button type="submit" className={`${primaryBtn} px-4 py-2 text-sm`}>
                                    Save goal
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Add Contribution Modal */}
            {selectedGoalId !== null && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="contrib-modal-title"
                        className="bg-white border border-pink-100 rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl shadow-pink-300/40 motion-safe:animate-rise"
                    >
                        <h3 id="contrib-modal-title" className="text-lg font-bold text-slate-900">Add goal contribution</h3>
                        <form onSubmit={handleAddContribution} className="space-y-4">
                            <div>
                                <label htmlFor="contrib-amount" className={labelClass}>Contribution amount (ZMW)</label>
                                <input
                                    id="contrib-amount"
                                    type="number"
                                    step="0.01"
                                    required
                                    value={contribAmount}
                                    onChange={(e) => setContribAmount(e.target.value)}
                                    placeholder="0.00"
                                    className={inputClass}
                                />
                            </div>

                            <div>
                                <label htmlFor="contrib-date" className={labelClass}>Date</label>
                                <input
                                    id="contrib-date"
                                    type="date"
                                    required
                                    value={contribDate}
                                    onChange={(e) => setContribDate(e.target.value)}
                                    className={inputClass}
                                />
                            </div>

                            <div>
                                <label htmlFor="contrib-note" className={labelClass}>Note (optional)</label>
                                <input
                                    id="contrib-note"
                                    type="text"
                                    value={contribNote}
                                    onChange={(e) => setContribNote(e.target.value)}
                                    placeholder="e.g. Monthly allocation"
                                    className={inputClass}
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button type="button" onClick={() => setSelectedGoalId(null)} className={ghostBtn}>
                                    Cancel
                                </button>
                                <button type="submit" className={`${primaryBtn} px-4 py-2 text-sm`}>
                                    Submit contribution
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};