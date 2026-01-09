import { useEffect, useRef, useState, useCallback } from 'react';
import { useAppSelector } from './useAppSelector';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (options: UseWebSocketOptions) => {
  const {
    url,
    onMessage,
    onConnect,
    onDisconnect,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);

  const connect = useCallback(() => {
    if (!isAuthenticated) return;

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const token = localStorage.getItem('access_token');
    const wsUrl = `${url}?token=${token}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✓ WebSocket connected:', url);
      setIsConnected(true);
      setReconnectCount(0);
      onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('✗ WebSocket disconnected:', url);
      setIsConnected(false);
      onDisconnect?.();

      // Attempt reconnection
      if (reconnectCount < maxReconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Reconnecting... (${reconnectCount + 1}/${maxReconnectAttempts})`);
          setReconnectCount((prev) => prev + 1);
          connect();
        }, reconnectInterval);
      }
    };

    wsRef.current = ws;
  }, [url, isAuthenticated, reconnectCount, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    }
    return () => disconnect();
  }, [isAuthenticated, connect, disconnect]);

  return { isConnected, sendMessage, reconnectCount, disconnect };
};
