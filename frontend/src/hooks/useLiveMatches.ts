// 🎯 Add this import line
import { useState, useEffect } from "react";
import api from "../services/api";

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
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchMatches = async () => {
    try {
      const response = await api.get("/upcoming/sync");
      const fetchedMatches = response.data.matches || [];

      setMatches(fetchedMatches);
      setLastSync(response.data.last_sync);
      setError(null);
    } catch (err: any) {
      setError("Failed to fetch live matches");
    }
  };

  useEffect(() => {
    // Initial fetch on mount
    fetchMatches();
  }, []);

  return { matches, lastSync, error, refetch: fetchMatches };
}
