import { useStreamHistory } from '@/store';
import { formatTimestamp } from '@/lib/utils';
import { cn } from '@/lib/utils';
import type { Severity } from '@/types';

interface StatusHistoryProps {
  streamId: string;
  maxItems?: number;
}

const severityStyles: Record<Severity, { dot: string; text: string }> = {
  green: {
    dot: 'bg-green-400',
    text: 'text-green-400',
  },
  yellow: {
    dot: 'bg-yellow-400',
    text: 'text-yellow-400',
  },
  red: {
    dot: 'bg-red-400',
    text: 'text-red-400',
  },
};

export function StatusHistory({ streamId, maxItems = 10 }: StatusHistoryProps) {
  const history = useStreamHistory(streamId);
  const displayHistory = history.slice(0, maxItems);

  if (displayHistory.length === 0) {
    return (
      <div>
        <h3 className="text-sm font-medium text-dark-300 mb-3">Status History</h3>
        <p className="text-sm text-dark-500">No history available</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-medium text-dark-300 mb-3">Status History</h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-[5px] top-2 bottom-2 w-0.5 bg-dark-700" />

        <div className="space-y-3">
          {displayHistory.map((entry, index) => {
            const styles = severityStyles[entry.severity];

            return (
              <div key={index} className="flex items-start gap-3 relative">
                {/* Timeline dot */}
                <div
                  className={cn(
                    'w-3 h-3 rounded-full flex-shrink-0 mt-0.5 z-10',
                    styles.dot
                  )}
                />

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-dark-500">
                      {formatTimestamp(entry.timestamp)}
                    </span>
                    <span className={cn('text-xs font-medium', styles.text)}>
                      {entry.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-dark-300 truncate">
                    {entry.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
