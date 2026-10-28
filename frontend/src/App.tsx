import React, { useState } from 'react';
import { PiggyBank } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { LoginView } from './views/LoginView';
import { RegisterView } from './views/RegisterView';
import { DashboardView } from './views/DashboardView';
import { TransactionsView } from './views/TransactionsView';
import { BudgetsView } from './views/BudgetsView';
import { GoalsView } from './views/GoalsView';
import { ReportsView } from './views/ReportsView';

const MainRouter: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentView, setCurrentView] = useState('dashboard');
  const [authView, setAuthView] = useState<'login' | 'register'>('login');

  if (loading) {
    return (
      <div
        role="status"
        className="min-h-screen relative overflow-hidden bg-gradient-to-br from-pink-500 via-fuchsia-600 to-rose-600 flex flex-col items-center justify-center gap-5 text-white"
      >
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-pink-300/30 blur-3xl" />
        <div className="absolute -bottom-32 -right-20 w-96 h-96 rounded-full bg-rose-300/30 blur-3xl" />

        <div className="relative p-5 bg-white/20 backdrop-blur rounded-3xl border border-white/30 shadow-2xl shadow-pink-900/20 motion-safe:animate-float">
          <PiggyBank className="w-12 h-12 text-white" />
        </div>
        <div className="relative text-center">
          <p className="text-xl font-bold">SmartBudget</p>
          <p className="text-sm text-pink-100 mt-1">Initializing SmartBudget...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return authView === 'login' ? (
      <LoginView onSwitchToRegister={() => setAuthView('register')} />
    ) : (
      <RegisterView onSwitchToLogin={() => setAuthView('login')} />
    );
  }

  return (
    <AppLayout currentView={currentView} onNavigate={setCurrentView}>
      {currentView === 'dashboard' && <DashboardView />}
      {currentView === 'transactions' && <TransactionsView />}
      {currentView === 'budgets' && <BudgetsView />}
      {currentView === 'goals' && <GoalsView />}
      {currentView === 'reports' && <ReportsView />}
    </AppLayout>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainRouter />
    </AuthProvider>
  );
}