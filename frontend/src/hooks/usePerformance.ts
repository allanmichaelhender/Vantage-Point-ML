import { useState, useEffect } from 'react';
import api from '../services/api';
import type { ModelPerformanceResponse, CalibrationPoint, EdgeBucket } from '../types/lab';

export function usePerformance() {
  const [data, setData] = useState<ModelPerformanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      
      // 🎯 Fire all three backend calls at the same time
      const [perfRes, calRes, edgeRes] = await Promise.all([
        api.get('/lab/model-performance'),
        api.get('/lab/calibration'),
        api.get('/lab/edge-analysis')
      ]);

      // 🧩 Merge the three responses into one state object
      setData({
        ...perfRes.data,
        calibration_data: calRes.data,
        edge_analysis: edgeRes.data
      });
      
      setError(null);
    } catch (err: any) {
      console.error("Data fetch failed:", err);
      setError(err.response?.data?.detail || "Failed to sync Lab data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  return { data, loading, error, refetch: fetchAllData };
}
