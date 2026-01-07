import { useStreamStore, useConfigStore } from '@/store';
import { Card } from '@/components/common';
import { formatTimestamp } from '@/lib/utils';
import type { StatusHistoryEntry, Severity } from '@/types';

interface ActivityLogProps {
  maxItems?: number;
}

interface LogEntry extends StatusHistoryEntry {
  streamId: string;
  streamName: string;
}

export function ActivityLog({ maxItems = 10 }: ActivityLogProps) {
  const history = useStreamStore((state) => state.history);
  const feeds = useConfigStore((state) => state.feeds);

  // Create a name lookup map
  const feedNames = feeds.reduce(
    (acc, feed) => {
      acc[feed.stream_id] = feed.name;
      return acc;
    },
    {} as Record<string, string>
  );

  // Flatten and sort all history entries
  const allEntries: LogEntry[] = Object.entries(history)
    .flatMap(([streamId, entries]) =>
      entries.map((entry) => ({
        ...entry,
        streamId,
        streamName: feedNames[streamId] || streamId,
      }))
    )
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
    .slice(0, maxItems);

  if (allEntries.length === 0) {
    return null;
  }

  return (
    <Card variant="outlined" padding="sm">
      <h3 className="text-sm font-medium text-dark-300 px-2 mb-2">
        Recent Activity
      </h3>
      <div className="space-y-1">
        {allEntries.map((entry, index) => (
          <ActivityLogItem key={`${entry.streamId}-${index}`} entry={entry} />
        ))}
      </div>
    </Card>
  );
}

interface ActivityLogItemProps {
  entry: LogEntry;
}

function ActivityLogItem({ entry }: ActivityLogItemProps) {
  const getSeverityLabel = (severity: Severity): string => {
    switch (severity) {
      case 'green':
        return 'GREEN';
      case 'yellow':
        return 'YELLOW';
      case 'red':
        return 'RED';
    }
  };

  return (
    <div className="flex items-center gap-3 px-2 py-1.5 rounded hover:bg-dark-800/50 transition-colors">
      <span className="text-xs text-dark-500 w-16 flex-shrink-0">
        {formatTimestamp(entry.timestamp)}
      </span>
      <span className="text-sm text-dark-300 flex-shrink-0">
        {entry.streamName}:
      </span>
      <span className="text-sm text-dark-400 flex-1 truncate">
        Status changed to{' '}
        <span
          className={
            entry.severity === 'green'
              ? 'text-green-400'
              : entry.severity === 'yellow'
                ? 'text-yellow-400'
                : 'text-red-400 font-medium'
          }
        >
          {getSeverityLabel(entry.severity)}
        </span>
      </span>
    </div>
  );
}
