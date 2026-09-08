import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardProvider } from '@/context/DashboardContext';
import { Header } from '@/components/common/Header';
import { DashboardPage } from '@/pages/DashboardPage';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <DashboardProvider>
          <div className="min-h-screen bg-slate-100 font-body flex flex-col w-full">
            {/* Main Full-Width Header */}
            <Header />

            {/* Full-Width Dashboard Content */}
            <main className="flex-1 w-full">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </DashboardProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;

