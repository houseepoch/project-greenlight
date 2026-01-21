import { useRef, useCallback, useEffect } from 'react';

interface UsePollingOptions {
  interval?: number;
  maxAttempts?: number;
  onMaxAttemptsReached?: () => void;
}

/**
 * Custom hook for polling with proper cleanup
 * Automatically stops polling when component unmounts
 */
export function usePolling(options: UsePollingOptions = {}) {
  const {
    interval = 1000,
    maxAttempts = 600, // ~10 minutes at 1s interval
    onMaxAttemptsReached
  } = options;

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const attemptCountRef = useRef(0);
  const isActiveRef = useRef(false);
  const pollFnRef = useRef<(() => Promise<boolean>) | null>(null);

  // Clear any existing timeout
  const clearPolling = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    isActiveRef.current = false;
    attemptCountRef.current = 0;
  }, []);

  // Start polling with a callback that returns true when done
  const startPolling = useCallback((pollFn: () => Promise<boolean>) => {
    // Clear any existing polling
    clearPolling();

    isActiveRef.current = true;
    attemptCountRef.current = 0;
    pollFnRef.current = pollFn;

    const poll = async () => {
      // Check if polling was stopped
      if (!isActiveRef.current) return;

      // Check max attempts
      attemptCountRef.current++;
      if (attemptCountRef.current > maxAttempts) {
        isActiveRef.current = false;
        onMaxAttemptsReached?.();
        return;
      }

      try {
        const isDone = await pollFn();
        if (isDone) {
          isActiveRef.current = false;
          return;
        }
      } catch (error) {
        // On error, still continue polling unless stopped
        console.error('Polling error:', error);
      }

      // Schedule next poll if still active
      if (isActiveRef.current) {
        timeoutRef.current = setTimeout(poll, interval);
      }
    };

    // Start immediately
    poll();
  }, [interval, maxAttempts, onMaxAttemptsReached, clearPolling]);

  // Stop polling
  const stopPolling = useCallback(() => {
    clearPolling();
  }, [clearPolling]);

  // Check if currently polling
  const isPolling = useCallback(() => {
    return isActiveRef.current;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearPolling();
    };
  }, [clearPolling]);

  return {
    startPolling,
    stopPolling,
    isPolling,
    clearPolling,
  };
}
