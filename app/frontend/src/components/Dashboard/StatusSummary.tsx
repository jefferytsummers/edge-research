import { useSeverityCounts } from '@/store';
import { cn } from '@/lib/utils';
import type { Severity } from '@/types';

interface StatusSummaryProps {
  className?: string;
}

const severityConfig: Record<Severity, { label: string; bgClass: string; textClass: string }> = {
  green: {
    label: 'Safe',
    bgClass: 'bg-green-500/20',
    textClass: 'text-green-400',
  },
  yellow: {
    label: 'Attention',
    bgClass: 'bg-yellow-500/20',
    textClass: 'text-yellow-400',
  },
  red: {
    label: 'Critical',
    bgClass: 'bg-red-500/20',
    textClass: 'text-red-400',
  },
};

export function StatusSummary({ className }: StatusSummaryProps) {
  const counts = useSeverityCounts();
  const total = counts.green + counts.yellow + counts.red;

  if (total === 0) {
    return null;
  }

  return (
    <div className={cn('flex items-center gap-4', className)}>
      {(['green', 'yellow', 'red'] as Severity[]).map((severity) => {
        const config = severityConfig[severity];
        const count = counts[severity];

        if (count === 0) return null;

        return (
          <div
            key={severity}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg',
              config.bgClass
            )}
          >
            <span className={cn('font-bold text-lg', config.textClass)}>
              {count}
            </span>
            <span className={cn('text-sm', config.textClass)}>
              {config.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
