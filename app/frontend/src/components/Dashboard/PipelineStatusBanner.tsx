import { useEffect, useState } from 'react';
import { Loader2, Cpu, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConfigResponse {
  model_ready: boolean;
  pipeline_status: string;
  pipeline_message: string;
  pipeline_progress?: number;
}

interface PipelineStatusBannerProps {
  pollInterval?: number;
}

export function PipelineStatusBanner({ pollInterval = 3000 }: PipelineStatusBannerProps) {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReadyBanner, setShowReadyBanner] = useState(false);
  const [wasBuilding, setWasBuilding] = useState(false);

  useEffect(() => {
    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    const fetchConfig = async () => {
      try {
        const res = await fetch('/config');
        if (res.ok && mounted) {
          const data = await res.json();

          // Track if we were building before
          const isBuilding = data.pipeline_status === 'building_engine' || data.pipeline_status === 'initializing';
          if (isBuilding) {
            setWasBuilding(true);
          }

          // Show "ready" banner if we just transitioned from building to ready
          if (wasBuilding && data.model_ready && !showReadyBanner) {
            setShowReadyBanner(true);
            // Hide after 5 seconds
            setTimeout(() => {
              if (mounted) setShowReadyBanner(false);
            }, 5000);
          }

          setConfig(data);
          setLoading(false);

          // Continue polling if model is NOT ready
          if (!data.model_ready && mounted) {
            timeoutId = setTimeout(fetchConfig, pollInterval);
          }
        }
      } catch {
        if (mounted) {
          timeoutId = setTimeout(fetchConfig, pollInterval);
        }
      }
    };

    fetchConfig();

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
    };
  }, [pollInterval, wasBuilding, showReadyBanner]);

  // Don't show anything while loading initial state
  if (loading || !config) {
    return null;
  }

  // Show "Model Ready" banner briefly after transitioning from building
  if (showReadyBanner && config.model_ready) {
    return (
      <div
        className={cn(
          'rounded-xl border p-4 mb-6 transition-all duration-500',
          'bg-green-500/10 border-green-500/30'
        )}
      >
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">
            <CheckCircle2 className="w-8 h-8 text-green-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-green-400">AI Model Ready</h3>
            <p className="text-sm text-dark-300 mt-0.5">
              The model has been loaded and is ready for inference.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Model is ready and we've shown the ready banner (or didn't need to) - hide
  if (config.model_ready) {
    return null;
  }

  const isBuilding = config.pipeline_status === 'building_engine' || config.pipeline_status === 'initializing';

  // Only show loading banner for building states
  if (!isBuilding) {
    return null;
  }

  const progress = config.pipeline_progress ?? 0;

  return (
    <div
      className={cn(
        'rounded-xl border p-4 mb-6 transition-all duration-300',
        'bg-blue-500/10 border-blue-500/30'
      )}
    >
      <div className="flex items-center gap-4">
        <div className="flex-shrink-0 relative">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
          <Cpu className="w-4 h-4 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-blue-400" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-blue-400">AI Model Loading</h3>
            {progress > 0 && (
              <span className="text-sm font-medium text-blue-400">{progress}%</span>
            )}
          </div>
          <p className="text-sm text-dark-300 mt-0.5">
            {config.pipeline_message || 'Initializing AI model...'}
          </p>
          {progress > 0 && (
            <div className="mt-3">
              <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
          <p className="text-xs text-dark-400 mt-2">
            First-time setup takes ~4 minutes. The model will be cached for future runs.
          </p>
        </div>
      </div>
    </div>
  );
}
