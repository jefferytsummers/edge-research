import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SetupWizard } from '@/components/SetupWizard';
import { ExpandedFeed } from '@/components/FeedView';
import { AlertsPage } from '@/components/Alerts';
import { DashboardPage, SettingsPage } from '@/pages';
import { ErrorBoundary } from '@/components/common';
import { useConfigStore } from '@/store';
import { useWebSocket, useConfigApi, useStaleStreamDetection } from '@/hooks';

function AppContent() {
  const isConfigured = useConfigStore((state) => state.isConfigured);
  const setConfig = useConfigStore((state) => state.setConfig);
  const markConfigured = useConfigStore((state) => state.markConfigured);
  const { getConfig } = useConfigApi();
  const [isLoading, setIsLoading] = useState(true);

  // Load configuration from backend on mount
  useEffect(() => {
    async function loadConfig() {
      try {
        const config = await getConfig();
        if (config && config.feeds && config.feeds.length > 0) {
          setConfig(config);
        }
      } catch (error) {
        console.error('Failed to load config from backend:', error);
      } finally {
        setIsLoading(false);
      }
    }
    loadConfig();
  }, [getConfig, setConfig]);

  // Initialize WebSocket connection
  useWebSocket({ autoConnect: isConfigured });

  // Monitor for stale streams (no updates received)
  useStaleStreamDetection();

  const handleSetupComplete = () => {
    markConfigured();
  };

  // Show loading state while checking backend
  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mx-auto mb-4" />
          <p className="text-dark-400">Loading configuration...</p>
        </div>
      </div>
    );
  }

  // Redirect based on configuration state
  if (!isConfigured) {
    return <SetupWizard onComplete={handleSetupComplete} />;
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/feed/:streamId" element={<ExpandedFeed />} />
      <Route path="/alerts" element={<AlertsPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/setup" element={<SetupWizard onComplete={handleSetupComplete} />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
