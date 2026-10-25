import React, { useState } from 'react';
import { LayoutDashboard, Receipt, PieChart, Target, BarChart2, LogOut, Menu, X, Wallet } from 'lucide-react';
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
        { id: 'goals', label: 'Savings Goals', icon: Target },
        { id: 'reports', label: 'Reports', icon: BarChart2 },
    ];

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex">
            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
            )}

            {/* Sidebar */}
            <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 flex flex-col transform transition-transform duration-200 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
                <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-600 rounded-xl">
                            <Wallet className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="font-bold text-lg text-white">SmartBudget</h1>
                            <p className="text-xs text-slate-400">Financial Manager</p>
                        </div>
                    </div>
                    <button className="lg:hidden text-slate-400 hover:text-white" onClick={() => setSidebarOpen(false)}>
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const active = currentView === item.id;
                        return (
                            <button
                                key={item.id}
                                onClick={() => { onNavigate(item.id); setSidebarOpen(false); }}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${active ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                                    }`}
                            >
                                <Icon className="w-5 h-5" />
                                {item.label}
                            </button>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-slate-800">
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                        <div className="truncate">
                            <p className="text-sm font-semibold text-white truncate">{user?.username}</p>
                            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                        </div>
                        <button onClick={logout} className="p-2 text-slate-400 hover:text-rose-400 transition-colors" title="Sign Out">
                            <LogOut className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-16 bg-slate-900/50 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-30">
                    <button className="lg:hidden p-2 text-slate-400 hover:text-white" onClick={() => setSidebarOpen(true)}>
                        <Menu className="w-6 h-6" />
                    </button>
                    <div className="text-sm font-medium text-slate-400 capitalize">
                        {currentView} Overview
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Live Backend
                        </span>
                    </div>
                </header>

                <main className="flex-1 p-6 overflow-y-auto">
                    {children}
                </main>
            </div>
        </div>
    );
};