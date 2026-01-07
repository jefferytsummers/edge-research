import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SetupWizard } from '@/components/SetupWizard';
import { ExpandedFeed } from '@/components/FeedView';
import { AlertsPage } from '@/components/Alerts';
import { DashboardPage, SettingsPage } from '@/pages';
import { useConfigStore } from '@/store';
import { useWebSocket } from '@/hooks';

function AppContent() {
  const isConfigured = useConfigStore((state) => state.isConfigured);
  const markConfigured = useConfigStore((state) => state.markConfigured);

  // Initialize WebSocket connection
  useWebSocket({ autoConnect: isConfigured });

  const handleSetupComplete = () => {
    markConfigured();
  };

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
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
