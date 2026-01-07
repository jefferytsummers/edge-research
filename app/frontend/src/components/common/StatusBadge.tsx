import { cn } from '@/lib/utils';
import type { Severity } from '@/types';
import { SEVERITY_LABELS } from '@/types';

interface StatusBadgeProps {
  severity: Severity;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  pulse?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'h-2 w-2',
  md: 'h-3 w-3',
  lg: 'h-4 w-4',
};

const labelSizeClasses = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
};

const severityClasses: Record<Severity, string> = {
  green: 'bg-status-green',
  yellow: 'bg-status-yellow',
  red: 'bg-status-red',
};

const labelColorClasses: Record<Severity, string> = {
  green: 'text-status-green',
  yellow: 'text-status-yellow',
  red: 'text-status-red',
};

export function StatusBadge({
  severity,
  size = 'md',
  showLabel = false,
  pulse = false,
  className,
}: StatusBadgeProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span
        className={cn(
          'rounded-full',
          sizeClasses[size],
          severityClasses[severity],
          pulse && severity === 'red' && 'animate-alert-pulse',
          pulse && severity === 'yellow' && 'animate-pulse-slow'
        )}
      />
      {showLabel && (
        <span
          className={cn(
            'font-medium',
            labelSizeClasses[size],
            labelColorClasses[severity],
            severity === 'red' && 'uppercase font-bold'
          )}
        >
          {SEVERITY_LABELS[severity]}
        </span>
      )}
    </div>
  );
}

interface StatusPillProps {
  severity: Severity;
  className?: string;
}

export function StatusPill({ severity, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium',
        severity === 'green' && 'bg-green-500/20 text-green-400',
        severity === 'yellow' && 'bg-yellow-500/20 text-yellow-400',
        severity === 'red' && 'bg-red-500/20 text-red-400',
        severity === 'red' && 'animate-alert-pulse',
        className
      )}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 rounded-full',
          severityClasses[severity]
        )}
      />
      {SEVERITY_LABELS[severity]}
    </span>
  );
}
