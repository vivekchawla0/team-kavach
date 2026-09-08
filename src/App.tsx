import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardProvider } from '@/context/DashboardContext';
import { Sidebar } from '@/components/common/Sidebar';
import { Header } from '@/components/common/Header';
import { DashboardPage } from '@/pages/DashboardPage';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <DashboardProvider>
          <div className="flex min-h-screen bg-slate-100 font-body">
            {/* Left Sidebar */}
            <Sidebar />

            {/* Main Workspace */}
            <div className="flex-1 flex flex-col min-w-0">
              <Header />

              <main className="flex-1">
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </main>
            </div>
          </div>
        </DashboardProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;

