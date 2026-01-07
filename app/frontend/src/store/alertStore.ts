import { create } from 'zustand';
import type { Alert } from '@/types';

interface AlertState {
  // Alert data
  alerts: Alert[];

  // Actions
  addAlert: (alert: Alert) => void;
  acknowledgeAlert: (alertId: string) => void;
  resolveAlert: (alertId: string) => void;
  setAlerts: (alerts: Alert[]) => void;
  clearResolved: () => void;
}

export const useAlertStore = create<AlertState>()((set) => ({
  alerts: [],

  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts],
    })),

  acknowledgeAlert: (alertId) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === alertId ? { ...a, acknowledged: true } : a
      ),
    })),

  resolveAlert: (alertId) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === alertId
          ? { ...a, resolved_at: new Date().toISOString() }
          : a
      ),
    })),

  setAlerts: (alerts) => set({ alerts }),

  clearResolved: () =>
    set((state) => ({
      alerts: state.alerts.filter((a) => !a.resolved_at),
    })),
}));

// Selector hooks
export const useActiveAlerts = (): Alert[] =>
  useAlertStore((state) =>
    state.alerts.filter((a) => !a.resolved_at)
  );

export const useCriticalAlerts = (): Alert[] =>
  useAlertStore((state) =>
    state.alerts.filter((a) => a.level === 'critical' && !a.resolved_at)
  );

export const useAlertsByStream = (streamId: string): Alert[] =>
  useAlertStore((state) =>
    state.alerts.filter((a) => a.stream_id === streamId)
  );

export const useUnacknowledgedCount = (): number =>
  useAlertStore((state) =>
    state.alerts.filter((a) => !a.acknowledged && !a.resolved_at).length
  );
