import { useEffect, useState } from 'react';
import { Loader2, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConfigResponse {
  model_ready: boolean;
  pipeline_status: string;
  pipeline_message: string;
}

export function ModelStatusIndicator() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);

  useEffect(() => {
    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    const fetchConfig = async () => {
      try {
        const res = await fetch('/config');
        if (res.ok && mounted) {
          const data = await res.json();
          setConfig(data);

          // Continue polling if model is NOT ready (to catch when it becomes ready)
          if (!data.model_ready && mounted) {
            timeoutId = setTimeout(fetchConfig, 3000);
          }
        }
      } catch {
        if (mounted) {
          timeoutId = setTimeout(fetchConfig, 3000);
        }
      }
    };

    fetchConfig();

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
    };
  }, []);

  if (!config) {
    return null;
  }

  const isBuilding = config.pipeline_status === 'building_engine' || config.pipeline_status === 'initializing';
  const isError = config.pipeline_status === 'error';

  if (config.model_ready) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
          'bg-green-500/20 text-green-400'
        )}
        title="AI model is loaded and ready"
      >
        <CheckCircle2 className="w-4 h-4" />
        <span className="hidden sm:inline">AI Ready</span>
      </div>
    );
  }

  if (isBuilding) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
          'bg-blue-500/20 text-blue-400'
        )}
        title="AI model is loading..."
      >
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="hidden sm:inline">AI Loading</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
          'bg-red-500/20 text-red-400'
        )}
        title={config.pipeline_message || 'Pipeline error'}
      >
        <AlertCircle className="w-4 h-4" />
        <span className="hidden sm:inline">AI Error</span>
      </div>
    );
  }

  // Offline state
  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
        'bg-dark-700 text-dark-400'
      )}
      title="AI pipeline not running"
    >
      <Cpu className="w-4 h-4" />
      <span className="hidden sm:inline">AI Offline</span>
    </div>
  );
}
