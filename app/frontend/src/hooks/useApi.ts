import { useState, useCallback } from 'react';
import type {
  AppConfig,
  StreamConfig,
  ProtocolRules,
  Alert,
  StreamStatus,
  ConnectionTestResult,
  HealthStatus,
} from '@/types';

const API_BASE = '/api';

interface ApiError {
  message: string;
  status?: number;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error: ApiError = {
      message: `API error: ${response.statusText}`,
      status: response.status,
    };
    throw error;
  }

  return response.json();
}

// Configuration API hooks
export function useConfigApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getConfig = useCallback(async (): Promise<AppConfig | null> => {
    setLoading(true);
    setError(null);
    try {
      return await fetchApi<AppConfig>('/config');
    } catch (err) {
      setError((err as ApiError).message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const addFeed = useCallback(
    async (feed: { name: string; source_uri: string }): Promise<StreamConfig | null> => {
      setLoading(true);
      setError(null);
      try {
        return await fetchApi<StreamConfig>('/config/feeds', {
          method: 'POST',
          body: JSON.stringify(feed),
        });
      } catch (err) {
        setError((err as ApiError).message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const removeFeed = useCallback(async (feedId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      await fetchApi(`/config/feeds/${feedId}`, { method: 'DELETE' });
      return true;
    } catch (err) {
      setError((err as ApiError).message);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const testConnection = useCallback(
    async (sourceUri: string): Promise<ConnectionTestResult | null> => {
      setLoading(true);
      setError(null);
      try {
        return await fetchApi<ConnectionTestResult>('/config/feeds/test', {
          method: 'POST',
          body: JSON.stringify({ source_url: sourceUri }),
        });
      } catch (err) {
        setError((err as ApiError).message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const saveProtocols = useCallback(
    async (protocols: ProtocolRules): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        await fetchApi('/config/protocols', {
          method: 'POST',
          body: JSON.stringify(protocols),
        });
        return true;
      } catch (err) {
        setError((err as ApiError).message);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    loading,
    error,
    getConfig,
    addFeed,
    removeFeed,
    testConnection,
    saveProtocols,
  };
}

// Status API hooks
export function useStatusApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getStatus = useCallback(async (): Promise<{
    streams: StreamStatus[];
    active_alerts: number;
  } | null> => {
    setLoading(true);
    setError(null);
    try {
      return await fetchApi('/status');
    } catch (err) {
      setError((err as ApiError).message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, getStatus };
}

// Alerts API hooks
export function useAlertsApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAlerts = useCallback(async (): Promise<Alert[] | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchApi<{ alerts: Alert[] }>('/alerts');
      return response.alerts;
    } catch (err) {
      setError((err as ApiError).message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const acknowledgeAlert = useCallback(async (alertId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      await fetchApi(`/alerts/${alertId}/acknowledge`, { method: 'POST' });
      return true;
    } catch (err) {
      setError((err as ApiError).message);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const resolveAlert = useCallback(async (alertId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      await fetchApi(`/alerts/${alertId}/resolve`, { method: 'POST' });
      return true;
    } catch (err) {
      setError((err as ApiError).message);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, getAlerts, acknowledgeAlert, resolveAlert };
}

// Health API hooks
export function useHealthApi() {
  const checkHealth = useCallback(async (): Promise<HealthStatus | null> => {
    try {
      return await fetchApi<HealthStatus>('/health');
    } catch {
      return null;
    }
  }, []);

  return { checkHealth };
}

// Pipeline Status types
export interface PipelineStatus {
  status: 'initializing' | 'building_engine' | 'running' | 'stopped' | 'error' | 'offline' | 'unknown';
  message: string;
  stream_id: string;
  progress?: number;
  timestamp: number;
}

// Pipeline Status API hooks
export function usePipelineStatusApi() {
  const getPipelineStatus = useCallback(
    async (streamId: string = 'stream_0'): Promise<PipelineStatus | null> => {
      try {
        return await fetchApi<PipelineStatus>(`/pipeline/status?stream_id=${streamId}`);
      } catch {
        return null;
      }
    },
    []
  );

  return { getPipelineStatus };
}
