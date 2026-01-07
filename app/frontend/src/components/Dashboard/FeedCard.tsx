import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, AlertTriangle, ExternalLink } from 'lucide-react';
import { StatusPill } from '@/components/common';
import { cn, formatTimestamp } from '@/lib/utils';
import type { StreamStatus, StreamConfig, Severity } from '@/types';

interface FeedCardProps {
  feed: StreamConfig;
  status?: StreamStatus;
  onClick?: () => void;
}

const severityBorderColors: Record<Severity, string> = {
  green: 'border-green-500/30 hover:border-green-500/50',
  yellow: 'border-yellow-500/30 hover:border-yellow-500/50',
  red: 'border-red-500/50 hover:border-red-500/70',
};

const severityBgColors: Record<Severity, string> = {
  green: 'bg-dark-800',
  yellow: 'bg-dark-800',
  red: 'bg-red-950/30',
};

export function FeedCard({ feed, status, onClick }: FeedCardProps) {
  const navigate = useNavigate();
  const [imageError] = useState(false);

  const severity = status?.severity || 'green';
  const isRed = severity === 'red';

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/feed/${feed.stream_id}`);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={cn(
        'rounded-xl border-2 overflow-hidden cursor-pointer transition-all duration-200',
        'hover:shadow-lg hover:scale-[1.02]',
        severityBorderColors[severity],
        severityBgColors[severity],
        isRed && 'animate-pulse shadow-red-500/20 shadow-lg'
      )}
    >
      {/* Video Preview Area */}
      <div className="aspect-video bg-dark-900 relative">
        {imageError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-dark-500">
            <Video className="w-12 h-12 mb-2" />
            <span className="text-sm">{feed.name}</span>
          </div>
        ) : (
          <>
            {/* Placeholder for actual video feed - in production this would be an <img> or <video> */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-dark-500">
              <Video className="w-12 h-12 mb-2" />
              <span className="text-sm">Live Feed</span>
            </div>

            {/* Status overlay for RED alerts */}
            {isRed && (
              <div className="absolute inset-0 bg-red-900/30 flex items-center justify-center">
                <div className="bg-red-600 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 animate-alert-pulse">
                  <AlertTriangle className="w-5 h-5" />
                  ALERT
                </div>
              </div>
            )}
          </>
        )}

        {/* Feed name overlay */}
        <div className="absolute top-2 left-2 bg-dark-900/80 px-2 py-1 rounded text-xs font-medium text-dark-200">
          {feed.name}
        </div>

        {/* Live indicator */}
        <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-dark-900/80 px-2 py-1 rounded">
          <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-xs text-dark-300">LIVE</span>
        </div>
      </div>

      {/* Status Info */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <span className="text-2xl" role="img" aria-label="status">
            {status?.icon || '\uD83D\uDFE2'}
          </span>

          {/* Description */}
          <div className="flex-1 min-w-0">
            <p
              className={cn(
                'font-medium truncate',
                isRed ? 'text-red-300' : 'text-dark-100'
              )}
            >
              {status?.description || 'Initializing...'}
            </p>

            <div className="flex items-center gap-2 mt-1">
              <StatusPill severity={severity} />
              {status?.timestamp && (
                <span className="text-xs text-dark-500">
                  {formatTimestamp(status.timestamp)}
                </span>
              )}
            </div>
          </div>

          {/* Expand indicator */}
          <ExternalLink className="w-4 h-4 text-dark-500" />
        </div>

        {/* Alert action for RED status */}
        {isRed && (
          <div className="mt-3 pt-3 border-t border-red-500/30">
            <button
              className="text-sm text-red-400 hover:text-red-300 font-medium flex items-center gap-1"
              onClick={(e) => {
                e.stopPropagation();
                navigate('/alerts');
              }}
            >
              Click to View Alert
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
