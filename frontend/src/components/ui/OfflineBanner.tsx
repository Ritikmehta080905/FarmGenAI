import React, { useState, useEffect } from 'react';
import { WifiOff, AlertTriangle } from 'lucide-react';

export default function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-bottom-4">
      <div className="bg-amber-50 border border-amber-200 shadow-lg rounded-xl p-4 pr-12 relative flex items-start gap-3 max-w-sm">
        <div className="p-2 bg-amber-100 rounded-lg shrink-0 mt-0.5">
          <WifiOff size={18} className="text-amber-700" />
        </div>
        <div>
          <h4 className="font-bold text-amber-900 text-sm flex items-center gap-1">
            <AlertTriangle size={14} className="text-amber-600"/> You are offline
          </h4>
          <p className="text-xs text-amber-700 mt-1">
            AgriNegotiator is running in offline mode. New deals cannot be created until connection is restored.
          </p>
        </div>
      </div>
    </div>
  );
}
