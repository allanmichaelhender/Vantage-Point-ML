import { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { LabData, ModelType } from "../../types/lab";

interface Props {
  data: LabData;
  globalModel: ModelType;
}

const mergeCalibration = (nn: any[], base: any[]) => {
  return nn.map((item, i) => ({
    prob_bucket: item.prob_bucket,
    // Neural Data
    nn_actual: item.actual_win_rate,
    nn_predicted: item.avg_predicted, // 🎯 Keep the blue line data
    nn_matches: item.match_count,
    // Baseline Data
    base_actual: base[i]?.actual_win_rate ?? 0,
    base_predicted: base[i]?.avg_predicted ?? 0, // 🎯 Keep the blue line data
    base_matches: base[i]?.match_count ?? 0,
  }));
};


export function CalibrationChart({ data, globalModel }: Props) {
  const [viewMode, setViewMode] = useState<ModelType | "both">(globalModel);

  useEffect(() => {
    setViewMode(globalModel);
  }, [globalModel]);

  const chartData =
    viewMode === "both"
      ? mergeCalibration(
          data.xgboost_nn.calibration_data,
          data.xgboost.calibration_data,
        )
      : data[viewMode].calibration_data;

  return (
  <div className="group relative bg-slate-900 border border-slate-800 p-6 rounded-xl h-[450px] w-full">
    <div className="flex justify-between items-start mb-6">
      <div>
        <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest">
          Model Calibration (Reliability)
        </h3>
        <p className="text-slate-500 text-[10px] mt-1 italic">
          {viewMode === 'both' ? 'Neural vs Baseline Comparison' : 'Ideal: Actual Win Rate should track with Confidence'}
        </p>
      </div>

      {/* 🎯 Local Controls */}
      <div className="flex bg-slate-950/50 p-1 rounded-lg border border-slate-800 opacity-0 group-hover:opacity-100 transition-opacity">
        {["xgboost_nn", "xgboost", "both"].map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode as any)}
            className={`px-3 py-1 rounded text-[10px] font-bold uppercase transition-colors ${
              viewMode === mode
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {mode === "xgboost_nn" ? "Neural" : mode === "xgboost" ? "Base" : "Vs"}
          </button>
        ))}
      </div>
    </div>

    <ResponsiveContainer width="100%" height="85%">
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis dataKey="prob_bucket" stroke="#475569" fontSize={10} tickMargin={10} />
        <YAxis 
          stroke="#475569" 
          fontSize={10} 
          domain={[0.45, 1]} 
          tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} 
        />

        <Tooltip
          contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px" }}
          labelStyle={{ color: "#94a3b8", fontWeight: "bold", marginBottom: "4px" }}
          formatter={(value: any, name: any, props: any) => {
            const { payload, dataKey } = props;
            let displayName = "Win Rate";
            let matches = payload.match_count || 0;

            if (dataKey === "nn_actual") {
              displayName = "Neural DNA Win Rate";
              matches = payload.nn_matches;
            } else if (dataKey === "base_actual") {
              displayName = "Baseline Win Rate";
              matches = payload.base_matches;
            } else if (dataKey.includes("predicted")) {
              return [`${(Number(value) * 100).toFixed(1)}%`, "Expected (Confidence)"];
            }

            return [`${(Number(value) * 100).toFixed(1)}%`, `${displayName} (${matches} matches)`];
          }}
        />

        {/* 🎯 Neural Model (Indigo) */}
        {(viewMode === "xgboost_nn" || viewMode === "both") && (
          <>
            <Area
              name="nn_actual"
              type="monotone"
              dataKey={viewMode === "both" ? "nn_actual" : "actual_win_rate"}
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.1}
              strokeWidth={3}
            />
            {/* Dashed line for Neural Predicted Confidence */}
            <Area
              dataKey={viewMode === "both" ? "nn_predicted" : "avg_predicted"}
              stroke="#6366f1"
              fill="none"
              strokeDasharray="5 5"
              strokeWidth={1}
              connectNulls
            />
          </>
        )}

        {/* 🎯 Baseline Model (Green) */}
        {(viewMode === "xgboost" || viewMode === "both") && (
          <>
            <Area
              name="base_actual"
              type="monotone"
              dataKey={viewMode === "both" ? "base_actual" : "actual_win_rate"}
              stroke="#22c55e"
              fill="#22c55e"
              fillOpacity={0.1}
              strokeWidth={3}
            />
            {/* Dashed line for Baseline Predicted Confidence */}
            <Area
              dataKey={viewMode === "both" ? "base_predicted" : "avg_predicted"}
              stroke="#22c55e"
              fill="none"
              strokeDasharray="5 5"
              strokeWidth={1}
              connectNulls
            />
          </>
        )}
      </AreaChart>
    </ResponsiveContainer>
  </div>
);

}
