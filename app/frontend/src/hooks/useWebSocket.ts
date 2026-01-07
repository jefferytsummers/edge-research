import { useEffect, useRef, useCallback, useState } from 'react';
import { useStreamStore, useAlertStore } from '@/store';
import type { WSMessage, WSStatusUpdate, WSAlert } from '@/types';

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendQuery: (streamId: string, question: string) => string;
  reconnectAttempts: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = `ws://${window.location.host}/ws/live`,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

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
    [updateStatus, addAlert]
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
  };
}
