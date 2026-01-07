import { useNavigate } from 'react-router-dom';
import { AlertTriangle, CheckCircle, Eye, Clock, XCircle } from 'lucide-react';
import { Button, Card, StatusPill } from '@/components/common';
import { useAlertStore, useConfigStore } from '@/store';
import { useAlertsApi } from '@/hooks';
import { cn, formatTimestamp, formatDuration } from '@/lib/utils';
import type { Alert, AlertLevel } from '@/types';

interface AlertCardProps {
  alert: Alert;
  expanded?: boolean;
}

const levelConfig: Record<
  AlertLevel,
  { icon: typeof AlertTriangle; bgClass: string; borderClass: string }
> = {
  critical: {
    icon: AlertTriangle,
    bgClass: 'bg-red-950/50',
    borderClass: 'border-red-500/50',
  },
  warning: {
    icon: Clock,
    bgClass: 'bg-yellow-950/30',
    borderClass: 'border-yellow-500/30',
  },
  info: {
    icon: CheckCircle,
    bgClass: 'bg-dark-800',
    borderClass: 'border-dark-700',
  },
};

export function AlertCard({ alert, expanded = false }: AlertCardProps) {
  const navigate = useNavigate();
  const feeds = useConfigStore((state) => state.feeds);
  const { acknowledgeAlert: ackAlertStore, resolveAlert: resolveAlertStore } =
    useAlertStore();
  const { acknowledgeAlert, resolveAlert, loading } = useAlertsApi();

  const feed = feeds.find((f) => f.stream_id === alert.stream_id);
  const config = levelConfig[alert.level];
  const Icon = config.icon;

  const handleAcknowledge = async () => {
    if (!alert.id) return;
    const success = await acknowledgeAlert(alert.id);
    if (success) {
      ackAlertStore(alert.id);
    }
  };

  const handleResolve = async () => {
    if (!alert.id) return;
    const success = await resolveAlert(alert.id);
    if (success) {
      resolveAlertStore(alert.id);
    }
  };

  const handleViewFeed = () => {
    navigate(`/feed/${alert.stream_id}`);
  };

  const isCritical = alert.level === 'critical';
  const isResolved = !!alert.resolved_at;

  return (
    <Card
      className={cn(
        'border transition-all',
        config.bgClass,
        config.borderClass,
        isCritical && !isResolved && 'animate-alert-pulse',
        isResolved && 'opacity-60'
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div
          className={cn(
            'p-2 rounded-lg',
            isCritical ? 'bg-red-500/20 text-red-400' : 'bg-dark-700 text-dark-400'
          )}
        >
          <Icon className="w-6 h-6" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <h3
              className={cn(
                'font-semibold',
                isCritical ? 'text-red-300' : 'text-dark-100'
              )}
            >
              {feed?.name || alert.stream_id} - {alert.title}
            </h3>
            <StatusPill severity={alert.severity} />
          </div>

          {/* Timestamp info */}
          <div className="flex items-center gap-4 text-sm text-dark-400 mb-3">
            <span>Detected: {formatTimestamp(alert.timestamp)}</span>
            {!isResolved && (
              <span>Duration: {formatDuration(alert.timestamp)}</span>
            )}
            {isResolved && alert.resolved_at && (
              <span className="text-green-400">
                Resolved: {formatTimestamp(alert.resolved_at)}
              </span>
            )}
          </div>

          {/* Message */}
          {expanded && (
            <div className="mb-4">
              <p className="text-sm font-medium text-dark-300 mb-1">
                AI Assessment:
              </p>
              <p className="text-sm text-dark-400">{alert.message}</p>
            </div>
          )}

          {/* Actions */}
          {!isResolved && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleViewFeed}
              >
                <Eye className="w-4 h-4" />
                View Live Feed
              </Button>
              {!alert.acknowledged && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleAcknowledge}
                  disabled={loading}
                >
                  <CheckCircle className="w-4 h-4" />
                  Acknowledge
                </Button>
              )}
              {isCritical && (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => {
                    // In production, this would trigger emergency response
                    window.alert('Emergency help requested');
                  }}
                >
                  <AlertTriangle className="w-4 h-4" />
                  Request Emergency Help
                </Button>
              )}
            </div>
          )}

          {/* Resolve button for acknowledged alerts */}
          {!isResolved && alert.acknowledged && (
            <div className="mt-3 pt-3 border-t border-dark-700">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResolve}
                disabled={loading}
                className="text-green-400 hover:text-green-300"
              >
                <XCircle className="w-4 h-4" />
                Mark as Resolved
              </Button>
            </div>
          )}
        </div>

        {/* Acknowledged indicator */}
        {alert.acknowledged && !isResolved && (
          <div className="flex-shrink-0">
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-dark-700 text-dark-400 text-xs">
              <CheckCircle className="w-3 h-3" />
              Acknowledged
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
