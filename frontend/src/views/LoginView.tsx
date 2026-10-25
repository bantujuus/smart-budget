import React, { useState } from 'react';
import { Wallet, LogIn, ArrowRight } from 'lucide-react';
import { authApi } from '../api/auth';
import { useAuth } from '../context/AuthContext';

interface LoginViewProps {
    onSwitchToRegister: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onSwitchToRegister }) => {
    const { login } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await authApi.login({ username, password });
            login(data.token, data.user);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Invalid username or password.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
                <div className="flex items-center gap-3 mb-8">
                    <div className="p-3 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-600/30">
                        <Wallet className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">SmartBudget</h1>
                        <p className="text-xs text-slate-400">Sign in to your financial dashboard</p>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Username</label>
                        <input
                            type="text"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500"
                            placeholder="Enter your username"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Password</label>
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500"
                            placeholder="••••••••"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50"
                    >
                        {loading ? 'Signing in...' : 'Sign In'} <LogIn className="w-4 h-4" />
                    </button>
                </form>

                <div className="mt-6 pt-6 border-t border-slate-800 text-center">
                    <p className="text-sm text-slate-400">
                        Don't have an account?{' '}
                        <button
                            onClick={onSwitchToRegister}
                            className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
                        >
                            Register here <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};