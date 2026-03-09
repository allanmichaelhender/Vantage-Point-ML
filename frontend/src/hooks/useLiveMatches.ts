// 🎯 Add this import line
import { useState, useEffect } from 'react'; 
import api from '../services/api';

// src/hooks/useLiveMatches.ts
export function useLiveMatches() {
  const [matches, setMatches] = useState<LiveMatch[]>([]);
  const [status, setStatus] = useState<'fresh' | 'revalidating' | 'loading'>('loading');
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchMatches = async () => {
    try {
      const response = await api.get('/matches/today');
      
      // 🎯 Target the new object structure
      setMatches(response.data.matches || []);
      setStatus(response.data.status);
      setLastSync(response.data.last_sync);
      
      setError(null);
    } catch (err: any) {
      setError("Failed to fetch live matches");
    }
  };

  useEffect(() => { fetchMatches(); }, []);

  return { matches, status, lastSync, error, refetch: fetchMatches };
}
