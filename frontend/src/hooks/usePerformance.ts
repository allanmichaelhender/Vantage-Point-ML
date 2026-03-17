// 📂 src/hooks/usePerformance.ts

import { useState, useEffect } from "react";
// 🎯 Ensure your api helper points to your FastAPI base URL
import api from "../services/api";

// 🎯 Pull in the 'Master' response type and the 'ModelType' literal
import type { LabData } from "../types/lab";

export function usePerformance() {
  const [data, setData] = useState<LabData | null>(null);

  // 🎯 1. Add "logistic" to the allowed active models
  const [activeModel, setActiveModel] = useState<
    "xgboost_nn" | "xgboost" | "nn" | "logistic"
  >("xgboost_nn");

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

      // 🎯 2. Map all 4 models from the API response
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
        nn: {
          ...perfRes.data.nn,
          calibration_data: calRes.data.nn,
          edge_analysis: edgeRes.data.nn,
        },
        logistic: {
          ...perfRes.data.logistic, // 👈 New Legacy model
          calibration_data: calRes.data.logistic,
          edge_analysis: edgeRes.data.logistic,
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
