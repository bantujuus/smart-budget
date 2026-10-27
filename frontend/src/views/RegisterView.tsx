import React, { useState } from 'react';
import { Wallet, UserPlus, ArrowLeft, Eye, EyeOff, Coins, TrendingUp, ShieldCheck } from 'lucide-react';
import { authApi } from '../api/auth';
import { useAuth } from '../context/AuthContext';

interface RegisterViewProps {
    onSwitchToLogin: () => void;
}

const BARS = [40, 62, 48, 78, 58, 94];

const PiggyBankIllustration: React.FC = () => (
    <svg viewBox="0 0 240 210" className="w-64 h-auto drop-shadow-2xl" role="img" aria-label="Piggy bank collecting coins">
        {/* Falling coins (drawn first so they disappear behind the body) */}
        {[0, 1.2, 2.4].map((delay) => (
            <g
                key={delay}
                className="motion-safe:animate-coin-drop"
                style={{ animationDelay: `${delay}s`, opacity: 0 }}
            >
                <circle cx="120" cy="20" r="11" fill="#fde047" stroke="#f59e0b" strokeWidth="2.5" />
                <circle cx="120" cy="20" r="6" fill="none" stroke="#f59e0b" strokeWidth="1.5" />
            </g>
        ))}

        {/* Tail */}
        <path d="M42 100 C26 92 24 112 36 112 C28 118 40 126 46 116" fill="none" stroke="#f472b6" strokeWidth="5" strokeLinecap="round" />
        {/* Legs */}
        <rect x="68" y="152" width="22" height="34" rx="9" fill="#ec4899" />
        <rect x="150" y="152" width="22" height="34" rx="9" fill="#ec4899" />
        {/* Ears */}
        <path d="M150 62 L166 34 L184 66 Z" fill="#f472b6" />
        <path d="M156 60 L166 42 L177 63 Z" fill="#fbcfe8" />
        {/* Body */}
        <ellipse cx="116" cy="110" rx="82" ry="60" fill="#f9a8d4" />
        <ellipse cx="100" cy="88" rx="46" ry="22" fill="#fbcfe8" opacity="0.55" />
        {/* Snout */}
        <ellipse cx="200" cy="116" rx="22" ry="17" fill="#f472b6" />
        <circle cx="194" cy="116" r="3.2" fill="#be185d" />
        <circle cx="206" cy="116" r="3.2" fill="#be185d" />
        {/* Eye */}
        <circle cx="168" cy="94" r="5" fill="#500724" />
        <circle cx="169.5" cy="92.5" r="1.6" fill="#fff" />
        {/* Cheek */}
        <circle cx="176" cy="108" r="7" fill="#fb7185" opacity="0.5" />
        {/* Coin slot */}
        <rect x="94" y="52" width="46" height="7" rx="3.5" fill="#9d174d" />
    </svg>
);

const inputClass =
    'w-full bg-pink-50/60 border border-pink-200 rounded-xl px-4 py-3 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-pink-500 focus:ring-4 focus:ring-pink-500/15 transition';

export const RegisterView: React.FC<RegisterViewProps> = ({ onSwitchToLogin }) => {
    const { login } = useAuth();
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await authApi.register({ username, email, password });
            login(data.token, data.user);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed. Please check your inputs.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex bg-pink-50">
            <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-pink-500 via-fuchsia-600 to-rose-600 p-12 flex-col justify-between">
                <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-pink-300/30 blur-3xl" />
                <div className="absolute top-1/3 -right-20 w-80 h-80 rounded-full bg-fuchsia-300/30 blur-3xl" />
                <div className="absolute -bottom-32 left-1/4 w-96 h-96 rounded-full bg-rose-300/30 blur-3xl" />

                <div className="relative flex items-center gap-3">
                    <div className="p-3 bg-white/20 backdrop-blur rounded-xl border border-white/30">
                        <Wallet className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xl font-bold text-white">SmartBudget</span>
                </div>

                <div className="relative">
                    <h2 className="text-4xl font-bold text-white leading-tight max-w-md">
                        Start building better money habits today.
                    </h2>
                    <p className="mt-4 text-pink-100 max-w-sm">
                        Create your free account and set your first budget in minutes.
                    </p>
                </div>

                {/* Illustration */}
                <div className="relative mx-auto w-full max-w-md h-72">
                    {/* Piggy bank */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="motion-safe:animate-float">
                            <PiggyBankIllustration />
                        </div>
                    </div>

                    {/* Bar chart card */}
                    <div
                        className="absolute top-0 right-0 w-44 p-4 rounded-2xl bg-white/15 backdrop-blur-md border border-white/30 shadow-xl motion-safe:animate-float"
                        style={{ animationDelay: '-2s' }}
                    >
                        <p className="text-xs font-medium text-pink-50 mb-3">Monthly spending</p>
                        <div className="flex items-end gap-1.5 h-14">
                            {BARS.map((h, i) => (
                                <div
                                    key={i}
                                    className="flex-1 rounded-t bg-white/85 origin-bottom motion-safe:animate-grow"
                                    style={{ height: `${h}%`, animationDelay: `${0.3 + i * 0.12}s` }}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Line chart card */}
                    <div
                        className="absolute bottom-0 left-0 w-44 p-4 rounded-2xl bg-white/15 backdrop-blur-md border border-white/30 shadow-xl motion-safe:animate-float"
                        style={{ animationDelay: '-4s' }}
                    >
                        <div className="flex items-center justify-between mb-2">
                            <p className="text-xs font-medium text-pink-50">Savings growth</p>
                            <TrendingUp className="w-4 h-4 text-white" />
                        </div>
                        <svg viewBox="0 0 120 40" className="w-full h-10" aria-hidden="true">
                            <polyline
                                points="0,34 20,28 40,30 60,18 80,20 100,8 120,4"
                                fill="none"
                                stroke="#fff"
                                strokeWidth="2.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                pathLength={1}
                                strokeDasharray={1}
                                className="motion-safe:animate-draw"
                            />
                        </svg>
                    </div>

                    {/* Floating coin badge */}
                    <div
                        className="absolute top-6 left-2 p-3 rounded-full bg-yellow-300/90 shadow-lg shadow-yellow-500/30 motion-safe:animate-float"
                        style={{ animationDelay: '-1s' }}
                    >
                        <Coins className="w-5 h-5 text-amber-700" />
                    </div>
                </div>

                <p className="relative text-xs text-pink-100/80 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Your financial data stays private to you
                </p>
            </div>

            {/* Form panel */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8">
                <div className="max-w-md w-full bg-white border border-pink-100 rounded-2xl p-8 shadow-xl shadow-pink-200/50 motion-safe:animate-rise">
                    <div className="flex items-center gap-3 mb-8 lg:hidden">
                        <div className="p-3 bg-gradient-to-br from-pink-500 to-fuchsia-600 rounded-xl shadow-lg shadow-pink-500/30">
                            <Wallet className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-xl font-bold text-slate-900">SmartBudget</span>
                    </div>

                    <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
                    <p className="text-sm text-slate-500 mt-1 mb-8">Join SmartBudget today</p>

                    {error && (
                        <div
                            role="alert"
                            className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-600 text-sm rounded-xl"
                        >
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-slate-700 mb-1.5">
                                Username
                            </label>
                            <input
                                id="username"
                                type="text"
                                required
                                autoComplete="username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className={inputClass}
                                placeholder="Choose a username"
                            />
                        </div>

                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
                                Email address
                            </label>
                            <input
                                id="email"
                                type="email"
                                required
                                autoComplete="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className={inputClass}
                                placeholder="you@example.com"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    required
                                    autoComplete="new-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className={`${inputClass} pr-12`}
                                    placeholder="••••••••"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword((v) => !v)}
                                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-pink-600 focus:outline-none focus:text-pink-600"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-pink-500 via-fuchsia-500 to-rose-500 hover:from-pink-600 hover:via-fuchsia-600 hover:to-rose-600 text-white font-semibold py-3 rounded-xl transition active:scale-[0.98] flex items-center justify-center gap-2 shadow-lg shadow-pink-500/30 focus:outline-none focus:ring-4 focus:ring-pink-500/30 disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Creating account...' : 'Create account'} <UserPlus className="w-4 h-4" />
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-pink-100 text-center">
                        <button
                            type="button"
                            onClick={onSwitchToLogin}
                            className="text-sm text-slate-500 hover:text-pink-600 font-medium inline-flex items-center gap-1.5 focus:outline-none focus:underline"
                        >
                            <ArrowLeft className="w-4 h-4" /> Back to sign in
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};