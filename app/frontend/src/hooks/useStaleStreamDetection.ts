import { useEffect, useRef } from 'react';
import { useStreamStore, STALE_THRESHOLD_MS } from '@/store';

/**
 * Hook that monitors stream updates and marks streams as stale
 * if they haven't received an update within the threshold period.
 *
 * This handles RTSP stream timeout scenarios where the backend
 * stops sending updates due to connection issues.
 */
export function useStaleStreamDetection() {
  const lastUpdateTime = useStreamStore((state) => state.lastUpdateTime);
  const markStreamStale = useStreamStore((state) => state.markStreamStale);
  const isConnected = useStreamStore((state) => state.isConnected);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    // Only check for stale streams when connected
    if (!isConnected) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
      return;
    }

    // Check for stale streams every 10 seconds
    const checkStaleStreams = () => {
      const now = Date.now();

      Object.entries(lastUpdateTime).forEach(([streamId, lastUpdate]) => {
        const timeSinceUpdate = now - lastUpdate;

        if (timeSinceUpdate > STALE_THRESHOLD_MS) {
          markStreamStale(streamId);
        }
      });
    };

    // Initial check
    checkStaleStreams();

    // Set up interval
    intervalRef.current = setInterval(checkStaleStreams, 10000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isConnected, lastUpdateTime, markStreamStale]);
}
