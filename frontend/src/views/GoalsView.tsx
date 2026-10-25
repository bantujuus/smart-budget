import React, { useEffect, useState } from 'react';
import { Target, Plus, TrendingUp, CheckCircle, Clock } from 'lucide-react';
import { goalsApi } from '../api/goals';
import type { SavingsGoal } from '../types';

export const GoalsView: React.FC = () => {
    const [goals, setGoals] = useState<SavingsGoal[]>([]);
    const [loading, setLoading] = useState(true);

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

    if (loading) return <div className="p-8 text-center text-slate-400">Loading Savings Goals...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">Savings Goals</h2>
                    <p className="text-sm text-slate-400">Set financial milestones and record progress.</p>
                </div>
                <button
                    onClick={() => setShowGoalModal(true)}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl font-medium transition-colors"
                >
                    <Plus className="w-4 h-4" /> New Goal
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
                        <div key={goal.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
                            <div>
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                                            <Target className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-white">{goal.name}</h3>
                                            <p className="text-xs text-slate-400">Target Date: {goal.target_date}</p>
                                        </div>
                                    </div>
                                    {isCompleted ? (
                                        <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                                            <CheckCircle className="w-3.5 h-3.5" /> Completed
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                                            <Clock className="w-3.5 h-3.5" /> Active
                                        </span>
                                    )}
                                </div>

                                <div className="space-y-2 mb-6">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Saved: ZMW {goal.goal_contributed || '0.00'}</span>
                                        <span className="text-white font-medium">Target: ZMW {goal.target_amount}</span>
                                    </div>
                                    <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                                        <div
                                            className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                                            style={{ width: `${Math.min(progress, 100)}%` }}
                                        />
                                    </div>
                                    <p className="text-right text-xs font-semibold text-indigo-400">{progress}% Saved</p>
                                </div>
                            </div>

                            <button
                                onClick={() => setSelectedGoalId(goal.id)}
                                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
                            >
                                <TrendingUp className="w-4 h-4 text-emerald-400" /> Add Contribution
                            </button>
                        </div>
                    );
                })}

                {goals.length === 0 && (
                    <div className="col-span-full py-12 text-center text-slate-500 bg-slate-900/50 border border-slate-800 rounded-2xl">
                        No savings goals established yet. Click "New Goal" to get started.
                    </div>
                )}
            </div>

            {/* New Goal Modal */}
            {showGoalModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-6">
                        <h3 className="text-lg font-bold text-white">Create Savings Goal</h3>
                        <form onSubmit={handleCreateGoal} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Goal Name</label>
                                <input
                                    type="text"
                                    required
                                    value={goalName}
                                    onChange={(e) => setGoalName(e.target.value)}
                                    placeholder="e.g. Emergency Fund"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Target Amount (ZMW)</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    required
                                    value={targetAmount}
                                    onChange={(e) => setTargetAmount(e.target.value)}
                                    placeholder="0.00"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Target Date</label>
                                <input
                                    type="date"
                                    required
                                    value={targetDate}
                                    onChange={(e) => setTargetDate(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowGoalModal(false)}
                                    className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-sm font-medium hover:bg-slate-700"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-500"
                                >
                                    Save Goal
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Add Contribution Modal */}
            {selectedGoalId !== null && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-6">
                        <h3 className="text-lg font-bold text-white">Add Goal Contribution</h3>
                        <form onSubmit={handleAddContribution} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Contribution Amount (ZMW)</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    required
                                    value={contribAmount}
                                    onChange={(e) => setContribAmount(e.target.value)}
                                    placeholder="0.00"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Date</label>
                                <input
                                    type="date"
                                    required
                                    value={contribDate}
                                    onChange={(e) => setContribDate(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Note (Optional)</label>
                                <input
                                    type="text"
                                    value={contribNote}
                                    onChange={(e) => setContribNote(e.target.value)}
                                    placeholder="e.g. Monthly allocation"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setSelectedGoalId(null)}
                                    className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-sm font-medium hover:bg-slate-700"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-500"
                                >
                                    Submit Contribution
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};
