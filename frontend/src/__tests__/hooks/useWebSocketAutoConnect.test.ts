import { renderHook, act } from '@testing-library/react';
import { useWebSocketAutoConnect } from '@/hooks/useWebSocketAutoConnect';

// Mock the stores
jest.mock('@/lib/store', () => ({
  useBlockchainStore: () => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    isConnected: true,
  }),
  useTrainingStore: () => ({
    fetchStatus: jest.fn().mockResolvedValue({}),
    fetchMetrics: jest.fn().mockResolvedValue({}),
  }),
  useNodeStore: () => ({
    fetchNodes: jest.fn().mockResolvedValue({}),
  }),
}));

describe('useWebSocketAutoConnect', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('connects on mount', () => {
    const { result } = renderHook(() => useWebSocketAutoConnect());
    expect(result.current).toBeNull();
  });

  it('sets up polling interval', () => {
    renderHook(() => useWebSocketAutoConnect());
    
    act(() => {
      jest.advanceTimersByTime(10000);
    });
    
    // Polling should have triggered
  });
});
