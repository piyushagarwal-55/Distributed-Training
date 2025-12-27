import { useEffect, useRef } from 'react';
import { useBlockchainStore, useNodeStore, Node } from '@/lib/store';

/**
 * Hook to automatically connect to WebSocket and fetch initial data
 * Use this in your root layout or _app.tsx
 */
export function useWebSocketAutoConnect() {
  const { connect, disconnect, isConnected } = useBlockchainStore();
  const { setNodes } = useNodeStore();
  const initialized = useRef(false);

  useEffect(() => {
    // Prevent double initialization in React StrictMode
    if (initialized.current) return;
    initialized.current = true;

    console.log('[WebSocket] Initializing connection and data fetching');
    
    // Connect to blockchain (simulated)
    connect();

    // Set initial demo nodes
    const demoNodes: Node[] = [
      {
        id: 'node-1',
        status: 'online',
        health: 'healthy',
        gpu: { model: 'NVIDIA RTX 4090', memory: 24576, utilization: 45 },
        network: { latency: 12, bandwidth: 1000 },
        contribution: 150,
      },
      {
        id: 'node-2',
        status: 'online',
        health: 'healthy',
        gpu: { model: 'NVIDIA RTX 3080', memory: 10240, utilization: 72 },
        network: { latency: 18, bandwidth: 800 },
        contribution: 120,
      },
      {
        id: 'node-3',
        status: 'busy',
        health: 'degraded',
        gpu: { model: 'NVIDIA RTX 3070', memory: 8192, utilization: 95 },
        network: { latency: 25, bandwidth: 600 },
        contribution: 80,
      },
    ];
    setNodes(demoNodes);

    console.log('[WebSocket] Initial data loaded successfully');

    // Cleanup on unmount
    return () => {
      console.log('[WebSocket] Cleaning up connection');
      disconnect();
    };
  }, []);

  return { isConnected };
}
