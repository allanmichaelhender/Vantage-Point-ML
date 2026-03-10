// 🎯 Add this import line
import { useState, useEffect, useRef } from 'react'; 
import api from '../services/api';

export interface LiveMatch {
  id: string;
  player1: string;
  player2: string;
  p1_prob: number;
  p2_prob: number;
  commence_time: string;
}


export function useLiveMatches() {
  const [matches, setMatches] = useState<LiveMatch[]>([]);
  const [status, setStatus] = useState<'fresh' | 'revalidating' | 'loading'>('loading');
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const pollingRef = useRef<any>(null);
  const hasFetched = useRef(false); // 🎯 Add this ref

  const fetchMatches = async () => {
    try {
      const response = await api.get('/upcoming/sync');
      setMatches(response.data.matches || []);
      setStatus(response.data.status);
      setLastSync(response.data.last_sync);
      setError(null);
    } catch (err: any) {
      setError("Failed to fetch live matches");
    }
  };

  useEffect(() => {
    // 🎯 Move the manual call inside this check
    if (!hasFetched.current) {
      fetchMatches();
      hasFetched.current = true;
    }

    if (status === 'revalidating' && !pollingRef.current) {
      console.log("🚀 Starting single poll instance");
      pollingRef.current = setInterval(() => {
        fetchMatches();
      }, 3000);
    }

    if (status === 'fresh' && pollingRef.current) {
      console.log("🛑 Killing poll - Data is fresh");
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    return () => {
      // Logic for cleanup...
    };
  }, [status]);

  return { matches, status, lastSync, error, refetch: fetchMatches };
}
