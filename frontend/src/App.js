import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { DemoModeProvider } from './contexts/DemoModeContext';
import AuthCallback from './components/AuthCallback';
import Sidebar from './components/Sidebar';
import DemoModeBanner from './components/DemoModeBanner';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProgramsPage from './pages/ProgramsPage';
import FarmersPage from './pages/FarmersPage';
import ClaimsPage from './pages/ClaimsPage';
import LedgerPage from './pages/LedgerPage';
import ExportPage from './pages/ExportPage';
import './App.css';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8]">
        <div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-[#FDFCF8]">
      <DemoModeBanner />
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <main className={`transition-all duration-300 ${collapsed ? 'ml-[68px]' : 'ml-[240px]'}`}>
        <div className="max-w-7xl mx-auto p-8">
          <Routes>
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="programs" element={<ProgramsPage />} />
            <Route path="farmers" element={<FarmersPage />} />
            <Route path="claims" element={<ClaimsPage />} />
            <Route path="ledger" element={<LedgerPage />} />
            <Route path="exports" element={<ExportPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function AppRouter() {
  const location = useLocation();

  // Check URL fragment for session_id synchronously (prevents race conditions)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <DemoModeProvider>
          <AppRouter />
          <Toaster
            position="top-right"
            toastOptions={{
              style: { fontFamily: 'Inter, sans-serif', fontSize: '14px' },
            }}
          />
        </DemoModeProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
