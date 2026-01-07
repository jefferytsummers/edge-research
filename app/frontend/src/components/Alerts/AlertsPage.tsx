import { useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Bell, History } from 'lucide-react';
import { Button, Card } from '@/components/common';
import { AlertCard } from './AlertCard';
import { useAlertStore, useActiveAlerts, useCriticalAlerts } from '@/store';
import { cn } from '@/lib/utils';

export function AlertsPage() {
  const navigate = useNavigate();
  const alerts = useAlertStore((state) => state.alerts);
  const activeAlerts = useActiveAlerts();
  const criticalAlerts = useCriticalAlerts();

  const resolvedAlerts = alerts.filter((a) => a.resolved_at);
  const warningAlerts = activeAlerts.filter((a) => a.level === 'warning');

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Grid
              </Button>
              <h1 className="text-xl font-bold text-dark-100 flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Alerts
              </h1>
            </div>
            {criticalAlerts.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <span className="text-sm font-medium text-red-400">
                  {criticalAlerts.length} Critical Alert
                  {criticalAlerts.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 py-6">
        {/* No alerts state */}
        {alerts.length === 0 && (
          <Card className="text-center py-16">
            <Bell className="w-12 h-12 text-dark-600 mx-auto mb-4" />
            <h2 className="text-lg font-medium text-dark-300 mb-2">
              No Alerts
            </h2>
            <p className="text-dark-500">
              All feeds are operating normally. Alerts will appear here when
              detected.
            </p>
          </Card>
        )}

        {/* Critical Alerts */}
        {criticalAlerts.length > 0 && (
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h2 className="text-lg font-semibold text-red-300">
                Active Critical Alerts ({criticalAlerts.length})
              </h2>
            </div>
            <div className="space-y-4">
              {criticalAlerts.map((alert) => (
                <AlertCard
                  key={alert.id || alert.timestamp}
                  alert={alert}
                  expanded
                />
              ))}
            </div>
          </section>
        )}

        {/* Warning Alerts */}
        {warningAlerts.length > 0 && (
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Bell className="w-5 h-5 text-yellow-400" />
              <h2 className="text-lg font-semibold text-yellow-300">
                Attention Needed ({warningAlerts.length})
              </h2>
            </div>
            <div className="space-y-3">
              {warningAlerts.map((alert) => (
                <AlertCard
                  key={alert.id || alert.timestamp}
                  alert={alert}
                />
              ))}
            </div>
          </section>
        )}

        {/* Alert History */}
        {resolvedAlerts.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-4">
              <History className="w-5 h-5 text-dark-400" />
              <h2 className="text-lg font-semibold text-dark-300">
                Alert History (Today)
              </h2>
            </div>
            <Card variant="outlined" padding="sm">
              <div className="space-y-2">
                {resolvedAlerts.slice(0, 10).map((alert) => (
                  <AlertHistoryItem
                    key={alert.id || alert.timestamp}
                    alert={alert}
                  />
                ))}
              </div>
            </Card>
          </section>
        )}
      </main>
    </div>
  );
}

interface AlertHistoryItemProps {
  alert: {
    stream_id: string;
    severity: string;
    title: string;
    resolved_at?: string;
    timestamp: string;
  };
}

function AlertHistoryItem({ alert }: AlertHistoryItemProps) {
  const navigate = useNavigate();

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded hover:bg-dark-800/50 transition-colors">
      <span className="text-xs text-dark-500 w-12 flex-shrink-0">
        {formatTime(alert.resolved_at || alert.timestamp)}
      </span>
      <span className="text-sm text-dark-300 flex-1 truncate">
        {alert.stream_id} -{' '}
        <span
          className={cn(
            alert.severity === 'red' && 'text-red-400',
            alert.severity === 'yellow' && 'text-yellow-400'
          )}
        >
          {alert.severity.toUpperCase()}
        </span>{' '}
        resolved ({alert.title})
      </span>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate(`/feed/${alert.stream_id}`)}
        className="text-xs"
      >
        View Feed
      </Button>
    </div>
  );
}
