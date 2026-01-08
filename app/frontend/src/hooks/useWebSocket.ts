import { useEffect, useRef, useCallback, useState } from 'react';
import { useStreamStore, useAlertStore } from '@/store';
import type { WSMessage, WSStatusUpdate, WSAlert, WSQueryResponse } from '@/types';

// Audio context for alert sounds
let audioContext: AudioContext | null = null;

/**
 * Play an alert sound for critical alerts using Web Audio API.
 * Creates a distinct two-tone alarm pattern.
 */
function playAlertSound() {
  try {
    // Initialize AudioContext on first use (needs user interaction)
    if (!audioContext) {
      audioContext = new (window.AudioContext || (window as typeof window & { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    }

    // Resume if suspended (browser autoplay policy)
    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }

    const now = audioContext.currentTime;

    // Create oscillator for alarm tone
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Two-tone alarm pattern (high-low-high)
    oscillator.type = 'square';

    // Schedule frequency changes for alarm pattern
    oscillator.frequency.setValueAtTime(880, now);        // High A
    oscillator.frequency.setValueAtTime(660, now + 0.15); // E
    oscillator.frequency.setValueAtTime(880, now + 0.3);  // High A
    oscillator.frequency.setValueAtTime(660, now + 0.45); // E

    // Volume envelope
    gainNode.gain.setValueAtTime(0.3, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.6);

    oscillator.start(now);
    oscillator.stop(now + 0.6);
  } catch (error) {
    console.warn('Failed to play alert sound:', error);
  }
}

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onQueryResponse?: (response: WSQueryResponse) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendQuery: (streamId: string, question: string) => string;
  reconnectAttempts: number;
  pendingQueries: Map<string, { question: string; streamId: string }>;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = `ws://${window.location.host}/ws/live`,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onQueryResponse,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const pendingQueriesRef = useRef<Map<string, { question: string; streamId: string }>>(new Map());

  const { updateStatus, setConnected } = useStreamStore();
  const { addAlert } = useAlertStore();
  const isConnected = useStreamStore((state) => state.isConnected);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'status_update': {
            const status = message as WSStatusUpdate;
            updateStatus({
              stream_id: status.stream_id,
              severity: status.severity,
              icon: status.icon,
              description: status.description,
              confidence: 1.0,
              timestamp: status.timestamp,
            });
            break;
          }

          case 'alert_new': {
            const alertMsg = message as WSAlert;
            addAlert(alertMsg.alert);

            // Play audio cue for critical alerts
            if (alertMsg.alert.level === 'critical') {
              playAlertSound();
            }
            break;
          }

          case 'query_received': {
            // Query acknowledged by server
            console.log('Query received by server:', message);
            break;
          }

          case 'query_response': {
            // Query response from VLM
            const response = message as WSQueryResponse;
            pendingQueriesRef.current.delete(response.request_id);
            onQueryResponse?.(response);
            break;
          }

          case 'pong': {
            // Heartbeat response received
            break;
          }

          default:
            console.log('Unknown WebSocket message type:', message.type);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    },
    [updateStatus, addAlert, onQueryResponse]
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setReconnectAttempts(0);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);

        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1);
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current.onmessage = handleMessage;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [url, reconnectInterval, maxReconnectAttempts, reconnectAttempts, handleMessage, setConnected]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
  }, [setConnected]);

  const sendQuery = useCallback((streamId: string, question: string): string => {
    const requestId = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Track this query
      pendingQueriesRef.current.set(requestId, { question, streamId });

      wsRef.current.send(
        JSON.stringify({
          type: 'query',
          stream_id: streamId,
          question,
          request_id: requestId,
        })
      );
    }

    return requestId;
  }, []);

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [isConnected]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    connect,
    disconnect,
    sendQuery,
    reconnectAttempts,
    pendingQueries: pendingQueriesRef.current,
  };
}
