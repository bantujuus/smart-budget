import React, { useState } from 'react';
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
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 font-mono">
        Initializing SmartBudget...
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