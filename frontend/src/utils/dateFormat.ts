/**
 * Client-side only date formatting utilities
 * Prevents hydration errors by returning placeholder on server
 */

import { useEffect, useState } from 'react';

export const formatTime = (date: Date | string | null | undefined): string => {
  if (typeof window === 'undefined') {
    // Server-side: return empty string to prevent hydration mismatch
    return '';
  }
  
  if (!date) return 'N/A';
  
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit',
      hour12: false // Use 24-hour format to avoid am/pm inconsistencies
    });
  } catch {
    return 'Invalid Date';
  }
};

export const formatNumber = (num: number | null | undefined, fallback: string = '0'): string => {
  if (typeof window === 'undefined') {
    // Server-side: return fallback to prevent hydration mismatch
    return fallback;
  }
  
  if (num === null || num === undefined) return fallback;
  
  return num.toLocaleString('en-US');
};

/**
 * Hook to safely format numbers client-side only
 * Returns fallback during SSR and initial render, then formatted number after mount
 */
export const useFormattedNumber = (num: number | null | undefined, fallback: string = '0'): string => {
  const [isMounted, setIsMounted] = useState(false);
  
  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  if (!isMounted || num === null || num === undefined) {
    return fallback;
  }
  
  return num.toLocaleString('en-US');
};
