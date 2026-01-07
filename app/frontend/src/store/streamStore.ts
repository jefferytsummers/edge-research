import { create } from 'zustand';
import type { StreamStatus, Severity, StatusHistoryEntry } from '@/types';

interface StreamState {
  // Stream status data
  statuses: Record<string, StreamStatus>;
  history: Record<string, StatusHistoryEntry[]>;

  // Connection status
  isConnected: boolean;

  // Actions
  updateStatus: (status: StreamStatus) => void;
  setStatuses: (statuses: StreamStatus[]) => void;
  addHistoryEntry: (streamId: string, entry: StatusHistoryEntry) => void;
  setConnected: (connected: boolean) => void;
  clearAll: () => void;
}

const MAX_HISTORY_ENTRIES = 50;

export const useStreamStore = create<StreamState>()((set) => ({
  statuses: {},
  history: {},
  isConnected: false,

  updateStatus: (status) =>
    set((state) => {
      const prevStatus = state.statuses[status.stream_id];
      const newHistory = { ...state.history };

      // Add to history if severity changed
      if (prevStatus && prevStatus.severity !== status.severity) {
        const streamHistory = newHistory[status.stream_id] || [];
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

  clearAll: () => set({ statuses: {}, history: {} }),
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
