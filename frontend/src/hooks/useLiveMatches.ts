// 🎯 Add this import line
import { useState, useEffect, useRef } from "react";
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
  const [status, setStatus] = useState<"fresh" | "revalidating" | "loading">(
    "loading",
  );
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 🎯 Use Refs for values that shouldn't trigger re-renders
  const retryCountRef = useRef(0);
  const MAX_RETRIES = 3;

  const fetchMatches = async () => {
    try {
      const response = await api.get("/upcoming/sync");
      const fetchedMatches = response.data.matches || [];
      const newStatus = response.data.status;

      setMatches(fetchedMatches);
      setLastSync(response.data.last_sync);
      setError(null);

      // 🎯 Logic: If no matches and still revalidating, increment retry
      if (newStatus === "revalidating" && fetchedMatches.length === 0) {
        retryCountRef.current += 1;
        console.log(
          `Sync attempt ${retryCountRef.current}/${MAX_RETRIES} failed to find matches.`,
        );
      } else {
        retryCountRef.current = 0; // Reset if we found matches or it's finished
      }

      // 🎯 Kill-switch: Force status to 'fresh' if we hit the limit
      if (retryCountRef.current >= MAX_RETRIES) {
        console.log("🛑 Max retries reached. Stopping sync loop.");
        setStatus("fresh");
      } else {
        setStatus(newStatus);
      }
    } catch (err: any) {
      setError("Failed to fetch live matches");
      setStatus("fresh"); // Stop polling on error
    }
  };

  useEffect(() => {
    // Initial fetch on mount
    fetchMatches();

    let intervalId: any = null;

    // Only start the interval if we are in 'revalidating' state
    if (status === "revalidating") {
      intervalId = setInterval(fetchMatches, 10000);
    }

    // 🎯 CLEANUP: This is critical to stop the loop
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [status]); // The loop restarts only when status actually changes

  return { matches, status, lastSync, error, refetch: fetchMatches };
}
