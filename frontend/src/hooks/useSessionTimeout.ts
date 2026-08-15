import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Enterprise Hook: Tracks user inactivity and auto-expires the session.
 * 
 * @param {number} timeoutMinutes - Number of minutes before auto-logout (default 30).
 */
export function useSessionTimeout(timeoutMinutes = 30) {
  const { isAuthenticated, triggerSessionExpired } = useAuth();
  const timeoutMs = timeoutMinutes * 60 * 1000;
  const timerRef = useRef(null);

  const resetTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (isAuthenticated) {
      timerRef.current = setTimeout(() => {
        triggerSessionExpired();
      }, timeoutMs);
    }
  }, [isAuthenticated, triggerSessionExpired, timeoutMs]);

  useEffect(() => {
    if (!isAuthenticated) return;

    // Standard DOM events to track "activity"
    const events = ['mousemove', 'keydown', 'scroll', 'click'];
    
    events.forEach(event => window.addEventListener(event, resetTimer));
    resetTimer(); // Start timer immediately on mount

    return () => {
      events.forEach(event => window.removeEventListener(event, resetTimer));
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isAuthenticated, resetTimer]);
}
