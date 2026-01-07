import { useNavigate } from 'react-router-dom';
import { Settings, Bell, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/common';
import { FeedGrid, StatusSummary, ActivityLog, PipelineStatusBanner, ModelStatusIndicator } from '@/components/Dashboard';
import { useStreamStore, useUnacknowledgedCount } from '@/store';
import { cn } from '@/lib/utils';

export function DashboardPage() {
  const navigate = useNavigate();
  const isConnected = useStreamStore((state) => state.isConnected);
  const alertCount = useUnacknowledgedCount();

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-dark-100">Newport Demo</h1>

              {/* Connection Status */}
              <div
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
                  isConnected
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                )}
              >
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4" />
                    <span className="hidden sm:inline">Monitoring</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4" />
                    <span className="hidden sm:inline">Connecting...</span>
                  </>
                )}
              </div>

              {/* AI Model Status */}
              <ModelStatusIndicator />
            </div>

            <div className="flex items-center gap-3">
              {/* Status Summary (Desktop) */}
              <div className="hidden md:block">
                <StatusSummary />
              </div>

              {/* Settings Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/settings')}
              >
                <Settings className="w-4 h-4" />
                <span className="hidden sm:inline">Settings</span>
              </Button>

              {/* Alerts Button */}
              <Button
                variant={alertCount > 0 ? 'danger' : 'ghost'}
                size="sm"
                onClick={() => navigate('/alerts')}
                className="relative"
              >
                <Bell className="w-4 h-4" />
                <span className="hidden sm:inline">Alerts</span>
                {alertCount > 0 && (
                  <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
                    {alertCount}
                  </span>
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Pipeline Status Banner - shows during AI model building */}
        <PipelineStatusBanner />

        {/* Status Summary (Mobile) */}
        <div className="md:hidden mb-6">
          <StatusSummary />
        </div>

        {/* Feed Grid */}
        <section>
          <FeedGrid />
        </section>

        {/* Activity Log */}
        <section className="mt-8">
          <ActivityLog maxItems={8} />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-800 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-center text-sm text-dark-500">
            Newport Demo - AI-Powered Behavioral Monitoring
          </p>
        </div>
      </footer>
    </div>
  );
}
