import { create } from 'zustand';
import type { StreamStatus, Severity, StatusHistoryEntry } from '@/types';

// Time in ms after which a stream is considered stale (no updates received)
const STALE_THRESHOLD_MS = 30000; // 30 seconds

interface StreamState {
  // Stream status data
  statuses: Record<string, StreamStatus>;
  history: Record<string, StatusHistoryEntry[]>;
  lastUpdateTime: Record<string, number>; // Track when each stream was last updated

  // Connection status
  isConnected: boolean;

  // Actions
  updateStatus: (status: StreamStatus) => void;
  setStatuses: (statuses: StreamStatus[]) => void;
  addHistoryEntry: (streamId: string, entry: StatusHistoryEntry) => void;
  setConnected: (connected: boolean) => void;
  markStreamStale: (streamId: string) => void;
  clearAll: () => void;
}

const MAX_HISTORY_ENTRIES = 50;

export const useStreamStore = create<StreamState>()((set) => ({
  statuses: {},
  history: {},
  lastUpdateTime: {},
  isConnected: false,

  updateStatus: (status) =>
    set((state) => {
      const prevStatus = state.statuses[status.stream_id];
      const newHistory = { ...state.history };
      const streamHistory = newHistory[status.stream_id] || [];

      // Determine if we should add to history:
      // 1. Severity changed (important event)
      // 2. No previous status (first update)
      // 3. Description significantly changed (new observation)
      const severityChanged = !prevStatus || prevStatus.severity !== status.severity;
      const descriptionChanged = !prevStatus || prevStatus.description !== status.description;
      const isNewStream = !prevStatus;

      // Always record severity changes; also record description changes but throttle
      // to avoid flooding history with minor updates
      const shouldRecord = severityChanged || isNewStream ||
        (descriptionChanged && streamHistory.length === 0);

      if (shouldRecord) {
        newHistory[status.stream_id] = [
          {
            severity: status.severity,
            description: status.description,
            timestamp: status.timestamp,
          },
          ...streamHistory,
        ].slice(0, MAX_HISTORY_ENTRIES);
      }

      return {
        statuses: {
          ...state.statuses,
          [status.stream_id]: status,
        },
        history: newHistory,
        lastUpdateTime: {
          ...state.lastUpdateTime,
          [status.stream_id]: Date.now(),
        },
      };
    }),

  setStatuses: (statuses) =>
    set(() => ({
      statuses: statuses.reduce(
        (acc, status) => {
          acc[status.stream_id] = status;
          return acc;
        },
        {} as Record<string, StreamStatus>
      ),
    })),

  addHistoryEntry: (streamId, entry) =>
    set((state) => ({
      history: {
        ...state.history,
        [streamId]: [entry, ...(state.history[streamId] || [])].slice(
          0,
          MAX_HISTORY_ENTRIES
        ),
      },
    })),

  setConnected: (connected) => set({ isConnected: connected }),

  markStreamStale: (streamId) =>
    set((state) => {
      const currentStatus = state.statuses[streamId];
      if (!currentStatus) return state;

      // Only mark as stale if not already showing a problem
      if (currentStatus.severity === 'red') return state;

      return {
        statuses: {
          ...state.statuses,
          [streamId]: {
            ...currentStatus,
            severity: 'yellow' as Severity,
            description: 'Stream connection timeout - no recent updates',
            icon: '\u26A0\uFE0F', // Warning emoji
          },
        },
      };
    }),

  clearAll: () => set({ statuses: {}, history: {}, lastUpdateTime: {} }),
}));

// Selector hooks for common use cases
export const useStreamStatus = (streamId: string): StreamStatus | undefined =>
  useStreamStore((state) => state.statuses[streamId]);

export const useAllStatuses = (): StreamStatus[] =>
  useStreamStore((state) => Object.values(state.statuses));

export const useStreamHistory = (streamId: string): StatusHistoryEntry[] =>
  useStreamStore((state) => state.history[streamId] || []);

export const useSeverityCounts = (): Record<Severity, number> =>
  useStreamStore((state) => {
    const counts: Record<Severity, number> = { green: 0, yellow: 0, red: 0 };
    Object.values(state.statuses).forEach((status) => {
      counts[status.severity]++;
    });
    return counts;
  });

export const useLastUpdateTime = (streamId: string): number | undefined =>
  useStreamStore((state) => state.lastUpdateTime[streamId]);

// Export threshold for use in stale detection hooks
export { STALE_THRESHOLD_MS };
