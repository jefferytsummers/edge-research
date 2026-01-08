import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { useStreamStore } from '@/store';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
  className?: string;
  showLabel?: boolean;
}

export function ConnectionStatus({ className, showLabel = true }: ConnectionStatusProps) {
  const isConnected = useStreamStore((state) => state.isConnected);

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-2 py-1 rounded-md text-xs',
        isConnected
          ? 'bg-green-500/10 text-green-400'
          : 'bg-yellow-500/10 text-yellow-400',
        className
      )}
    >
      {isConnected ? (
        <>
          <Wifi className="w-3 h-3" />
          {showLabel && <span>Connected</span>}
        </>
      ) : (
        <>
          <WifiOff className="w-3 h-3" />
          {showLabel && <span>Reconnecting...</span>}
          <RefreshCw className="w-3 h-3 animate-spin" />
        </>
      )}
    </div>
  );
}

// Floating toast-style notification for connection changes
interface ConnectionToastProps {
  show: boolean;
  isConnected: boolean;
}

export function ConnectionToast({ show, isConnected }: ConnectionToastProps) {
  if (!show) return null;

  return (
    <div
      className={cn(
        'fixed bottom-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg',
        'flex items-center gap-2 text-sm font-medium',
        'animate-in fade-in slide-in-from-bottom-2 duration-300',
        isConnected
          ? 'bg-green-600 text-white'
          : 'bg-yellow-600 text-white'
      )}
    >
      {isConnected ? (
        <>
          <Wifi className="w-4 h-4" />
          <span>Connection restored</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4" />
          <span>Connection lost - reconnecting...</span>
        </>
      )}
    </div>
  );
}
