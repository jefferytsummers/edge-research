import { useMemo } from 'react';
import { FeedCard } from './FeedCard';
import { useConfigStore, useStreamStore } from '@/store';
import { cn } from '@/lib/utils';
import type { StreamConfig, Severity } from '@/types';

interface FeedGridProps {
  onFeedClick?: (feed: StreamConfig) => void;
}

// Severity priority for sorting (higher = more urgent, shows first)
const SEVERITY_PRIORITY: Record<Severity, number> = {
  red: 3,
  yellow: 2,
  green: 1,
};

export function FeedGrid({ onFeedClick }: FeedGridProps) {
  const feeds = useConfigStore((state) => state.feeds);
  const statuses = useStreamStore((state) => state.statuses);

  // Sort feeds by severity (RED first, then YELLOW, then GREEN)
  const sortedFeeds = useMemo(() => {
    return [...feeds].sort((a, b) => {
      const severityA = statuses[a.stream_id]?.severity || 'green';
      const severityB = statuses[b.stream_id]?.severity || 'green';
      const priorityA = SEVERITY_PRIORITY[severityA];
      const priorityB = SEVERITY_PRIORITY[severityB];
      // Higher priority first (descending)
      return priorityB - priorityA;
    });
  }, [feeds, statuses]);

  if (feeds.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-dark-400 text-lg">No feeds configured</p>
        <p className="text-dark-500 text-sm mt-2">
          Go to Settings to add camera feeds
        </p>
      </div>
    );
  }

  // Dynamic grid columns based on feed count
  const gridCols = cn(
    'grid gap-6',
    feeds.length === 1 && 'grid-cols-1 max-w-xl mx-auto',
    feeds.length === 2 && 'grid-cols-1 md:grid-cols-2',
    feeds.length === 3 && 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    feeds.length >= 4 && 'grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3',
    feeds.length >= 6 && 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
  );

  return (
    <div className={gridCols}>
      {sortedFeeds.map((feed) => (
        <FeedCard
          key={feed.stream_id}
          feed={feed}
          status={statuses[feed.stream_id]}
          onClick={onFeedClick ? () => onFeedClick(feed) : undefined}
        />
      ))}
    </div>
  );
}
