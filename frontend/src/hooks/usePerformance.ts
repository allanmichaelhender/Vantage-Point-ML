// 📂 src/hooks/usePerformance.ts

import { useState, useEffect } from "react";
// 🎯 Ensure your api helper points to your FastAPI base URL
import api from "../services/api";

// 🎯 Pull in the 'Master' response type and the 'ModelType' literal
import type { LabData } from "../types/lab";

export function usePerformance() {
  const [data, setData] = useState<LabData | null>(null);
  // 🎯 Add a state to toggle between the two brains
  const [activeModel, setActiveModel] = useState<"xgboost_nn" | "xgboost">(
    "xgboost_nn",
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllData = async () => {
    try {
      setLoading(true);

      const [perfRes, calRes, edgeRes] = await Promise.all([
        api.get("/lab/model-performance"),
        api.get("/lab/calibration"),
        api.get("/lab/edge-analysis"),
      ]);

      // 🧩 We "stitch" the calibration and edge data into the specific model profiles
      setData({
        xgboost_nn: {
          ...perfRes.data.xgboost_nn,
          calibration_data: calRes.data.xgboost_nn,
          edge_analysis: edgeRes.data.xgboost_nn,
        },
        xgboost: {
          ...perfRes.data.xgboost,
          calibration_data: calRes.data.xgboost,
          edge_analysis: edgeRes.data.xgboost,
        },
      });

      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to sync Lab data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  // 🎯 Helper to pull the "Active" data for your charts/stats
  const selectedProfile = data ? data[activeModel] : null;

  return {
    data,
    selectedProfile, // 👈 Use this in your UI components
    activeModel,
    setActiveModel,
    loading,
    error,
    refetch: fetchAllData,
  };
}
