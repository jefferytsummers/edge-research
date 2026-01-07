import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { StreamConfig, ProtocolRules, AppConfig } from '@/types';
import { generateId } from '@/lib/utils';

interface ConfigState {
  // Configuration data
  feeds: StreamConfig[];
  protocols: ProtocolRules;
  isConfigured: boolean;

  // Actions
  addFeed: (feed: Omit<StreamConfig, 'stream_id' | 'enabled'>) => void;
  removeFeed: (streamId: string) => void;
  updateFeed: (streamId: string, updates: Partial<StreamConfig>) => void;
  setProtocols: (protocols: ProtocolRules) => void;
  setConfig: (config: AppConfig) => void;
  resetConfig: () => void;
  markConfigured: () => void;
}

const defaultProtocols: ProtocolRules = {
  green_rules:
    'Reading, watching TV, sleeping normally in bed, eating meals, sitting calmly, exercising normally',
  yellow_rules:
    'Out of camera view, crouching in corners, minor injuries, pacing erratically, signs of distress',
  red_rules:
    'Unconscious on ground, severe injury, room is empty/resident has left, self-harm behavior, medical emergency',
};

export const useConfigStore = create<ConfigState>()(
  persist(
    (set) => ({
      feeds: [],
      protocols: defaultProtocols,
      isConfigured: false,

      addFeed: (feed) =>
        set((state) => ({
          feeds: [
            ...state.feeds,
            {
              ...feed,
              stream_id: generateId(),
              enabled: true,
            },
          ],
        })),

      removeFeed: (streamId) =>
        set((state) => ({
          feeds: state.feeds.filter((f) => f.stream_id !== streamId),
        })),

      updateFeed: (streamId, updates) =>
        set((state) => ({
          feeds: state.feeds.map((f) =>
            f.stream_id === streamId ? { ...f, ...updates } : f
          ),
        })),

      setProtocols: (protocols) => set({ protocols }),

      setConfig: (config) =>
        set({
          feeds: config.feeds,
          protocols: config.protocols,
          isConfigured: true,
        }),

      resetConfig: () =>
        set({
          feeds: [],
          protocols: defaultProtocols,
          isConfigured: false,
        }),

      markConfigured: () => set({ isConfigured: true }),
    }),
    {
      name: 'newport-config',
    }
  )
);
