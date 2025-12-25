import { useEffect } from 'react';
import { useBlockchainStore, useTrainingStore, useNodeStore } from '@/lib/store';
import { DEBUG } from '@/types';

/**
 * Hook to automatically connect to WebSocket and fetch initial data
 * Use this in your root layout or _app.tsx
 */
export function useWebSocketAutoConnect() {
  const { connect, disconnect, isConnected } = useBlockchainStore();
  const { fetchStatus, fetchMetrics } = useTrainingStore();
  const { fetchNodes } = useNodeStore();

  useEffect(() => {
    DEBUG.log('useWebSocketAutoConnect', 'Initializing WebSocket connection and data fetching');
    
    // Connect to WebSocket
    connect();

    // Fetch initial data
    const fetchInitialData = async () => {
      try {
        await Promise.all([
          fetchStatus(),
          fetchMetrics(),
          fetchNodes(),
        ]);
        DEBUG.log('useWebSocketAutoConnect', 'Initial data fetched successfully');
      } catch (error) {
        DEBUG.error('useWebSocketAutoConnect', 'Failed to fetch initial data:', error);
      }
    };

    fetchInitialData();

    // Set up polling for updates every 10 seconds
    const pollInterval = setInterval(() => {
      if (isConnected) {
        fetchStatus();
        fetchMetrics();
        fetchNodes();
      }
    }, 10000);

    // Cleanup on unmount
    return () => {
      DEBUG.log('useWebSocketAutoConnect', 'Cleaning up WebSocket connection');
      clearInterval(pollInterval);
      disconnect();
    };
  }, []); // Empty dependency array = run once on mount

  return null;
}
