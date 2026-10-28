import React, { useState } from 'react';
import { LayoutDashboard, Receipt, PieChart, Target, BarChart2, LogOut, Menu, X, PiggyBank, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface AppLayoutProps {
    currentView: string;
    onNavigate: (view: string) => void;
    children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ currentView, onNavigate, children }) => {
    const { user, logout } = useAuth();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'transactions', label: 'Transactions', icon: Receipt },
        { id: 'budgets', label: 'Budgets', icon: PieChart },
        { id: 'goals', label: 'Savings goals', icon: Target },
        { id: 'reports', label: 'Reports', icon: BarChart2 },
    ];

    const current = navItems.find((item) => item.id === currentView);
    const CurrentIcon = current?.icon ?? LayoutDashboard;
    const initial = (user?.username?.[0] ?? '?').toUpperCase();

    return (
        <div className="min-h-screen bg-pink-50 text-slate-900 flex">
            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`fixed inset-y-0 left-0 lg:sticky lg:top-0 lg:h-screen z-50 w-64 overflow-hidden bg-gradient-to-b from-white via-white to-pink-50 border-r border-pink-100 shadow-xl shadow-pink-200/40 flex flex-col transform transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                    }`}
            >
                {/* Twinkling sparkles */}
                <Sparkles aria-hidden="true" className="pointer-events-none absolute top-24 right-4 w-3.5 h-3.5 text-pink-300 motion-safe:animate-twinkle" />
                <Sparkles aria-hidden="true" className="pointer-events-none absolute top-1/2 left-3 w-3 h-3 text-fuchsia-300 motion-safe:animate-twinkle" style={{ animationDelay: '-1s' }} />
                <Sparkles aria-hidden="true" className="pointer-events-none absolute bottom-48 right-6 w-3 h-3 text-rose-300 motion-safe:animate-twinkle" style={{ animationDelay: '-1.8s' }} />

                <div className="relative p-6 border-b border-pink-100 flex items-center justify-between">
                    <div className="group flex items-center gap-3 cursor-default">
                        <div className="p-2.5 bg-gradient-to-br from-pink-500 via-fuchsia-500 to-rose-500 rounded-xl shadow-lg shadow-pink-500/30 motion-safe:group-hover:animate-wiggle">
                            <PiggyBank className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="font-bold text-lg text-slate-900">SmartBudget</h1>
                            <p className="text-xs text-pink-600">Financial manager</p>
                        </div>
                    </div>
                    <button
                        className="lg:hidden p-1 text-slate-400 hover:text-pink-600 transition-colors"
                        onClick={() => setSidebarOpen(false)}
                        aria-label="Close menu"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <nav className="relative flex-1 p-4 space-y-1.5">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const active = currentView === item.id;
                        return (
                            <button
                                key={item.id}
                                onClick={() => { onNavigate(item.id); setSidebarOpen(false); }}
                                aria-current={active ? 'page' : undefined}
                                className={`group relative overflow-hidden w-full flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-pink-500/20 ${active
                                    ? 'bg-gradient-to-r from-pink-500 via-fuchsia-500 to-rose-500 text-white shadow-lg shadow-pink-500/30'
                                    : 'text-slate-500 hover:bg-pink-50 hover:text-pink-700 hover:translate-x-1'
                                    }`}
                            >
                                {active && (
                                    <span
                                        aria-hidden="true"
                                        className="pointer-events-none absolute inset-y-0 -left-1/2 w-1/2 bg-gradient-to-r from-transparent via-white/30 to-transparent motion-safe:animate-shimmer"
                                    />
                                )}
                                <Icon className="relative w-5 h-5 transition-transform duration-200 group-hover:scale-110 group-hover:-rotate-6" />
                                <span className="relative">{item.label}</span>
                            </button>
                        );
                    })}
                </nav>

                <div className="relative p-4 space-y-3 border-t border-pink-100">
                    {/* Encouragement card */}
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-pink-100 to-fuchsia-100 border border-pink-200">
                        <PiggyBank className="w-6 h-6 shrink-0 text-pink-600 motion-safe:animate-float" />
                        <p className="text-xs font-medium text-pink-800">Small savings add up. Keep going!</p>
                    </div>

                    <div className="flex items-center justify-between gap-2 p-3 bg-white border border-pink-100 rounded-xl shadow-sm">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="w-9 h-9 shrink-0 rounded-full bg-gradient-to-br from-pink-500 to-fuchsia-600 text-white text-sm font-bold flex items-center justify-center shadow-md shadow-pink-500/30">
                                {initial}
                            </div>
                            <div className="truncate">
                                <p className="text-sm font-semibold text-slate-900 truncate">{user?.username}</p>
                                <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                            </div>
                        </div>
                        <button
                            onClick={logout}
                            className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-rose-300"
                            title="Sign out"
                            aria-label="Sign out"
                        >
                            <LogOut className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-16 bg-white/70 backdrop-blur-md border-b border-pink-100 flex items-center justify-between px-6 sticky top-0 z-30">
                    <div className="flex items-center gap-3">
                        <button
                            className="lg:hidden p-2 -ml-2 text-slate-500 hover:text-pink-600 transition-colors"
                            onClick={() => setSidebarOpen(true)}
                            aria-label="Open menu"
                        >
                            <Menu className="w-6 h-6" />
                        </button>
                        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                            <CurrentIcon className="w-4 h-4 text-pink-500" />
                            {current?.label ?? currentView} overview
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="hidden sm:inline text-sm text-slate-500">
                            Hi, <span className="font-semibold text-pink-600">{user?.username}</span>
                        </span>
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-600 border border-emerald-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 motion-safe:animate-pulse" /> Live backend
                        </span>
                    </div>
                </header>

                <main className="flex-1 p-4 sm:p-6 overflow-y-auto">
                    {children}
                </main>
            </div>
        </div>
    );
};