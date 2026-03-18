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

const mergeCalibration = (
  nn_hybrid: any[] = [],
  base: any[] = [],
  nn_scout: any[] = [],
  legacy: any[] = [],
) => {
  return (nn_hybrid || []).map((item, i) => ({
    prob_bucket: item.prob_bucket,
    nn_actual: item.actual_win_rate,
    nn_predicted: item.avg_predicted,
    nn_matches: item.match_count,
    base_actual: base?.[i]?.actual_win_rate ?? 0,
    base_predicted: base?.[i]?.avg_predicted ?? 0,
    base_matches: base?.[i]?.match_count ?? 0,
    scout_actual: nn_scout?.[i]?.actual_win_rate ?? 0,
    scout_predicted: nn_scout?.[i]?.avg_predicted ?? 0,
    scout_matches: nn_scout?.[i]?.match_count ?? 0,
    legacy_actual: legacy?.[i]?.actual_win_rate ?? 0,
    legacy_predicted: legacy?.[i]?.avg_predicted ?? 0,
    legacy_matches: legacy?.[i]?.match_count ?? 0,
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
          data.nn.calibration_data,
          data.logistic.calibration_data,
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
            {viewMode === "both"
              ? "Neural vs Baseline Comparison"
              : "Ideal: Actual Win Rate should track with Confidence"}
          </p>
        </div>
        {/* 🎯 Local Controls */}
        <div className="flex bg-slate-950/50 p-1 rounded-lg border border-slate-800 opacity-0 group-hover:opacity-100 transition-opacity">
          {["xgboost_nn", "xgboost", "nn", "logistic", "both"].map((mode) => {
            // 🎯 Map the technical key to the Display Name
            const labels: Record<string, string> = {
              xgboost_nn: "Hybrid",
              xgboost: "Base",
              nn: "Scout",
              logistic: "Legacy",
              both: "Vs",
            };

            return (
              <button
                key={mode}
                onClick={() => setViewMode(mode as any)}
                className={`px-3 py-1 rounded text-[10px] font-bold uppercase transition-colors ${
                  viewMode === mode
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {labels[mode]}
              </button>
            );
          })}
        </div>
      </div>
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart
          data={chartData as any[]}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#1e293b"
            vertical={false}
          />
          <XAxis
            dataKey="prob_bucket"
            stroke="#475569"
            fontSize={10}
            tickMargin={10}
          />
          <YAxis
            stroke="#475569"
            fontSize={10}
            domain={[0.45, 1]}
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
            }}
            labelStyle={{
              color: "#94a3b8",
              fontWeight: "bold",
              marginBottom: "4px",
            }}
            formatter={(value: any, name: any, props: any) => {
              const { dataKey, payload } = props;
              const isPercent = (val: any) =>
                `${(Number(val) * 100).toFixed(1)}%`;

              // 1. Model: Hybrid (Indigo)
              if (dataKey === "nn_predicted")
                return [isPercent(value), "Hybrid Expected"];
              if (dataKey === "nn_actual") {
                return [
                  isPercent(value),
                  `Actual (${payload.nn_matches || payload.match_count} matches)`,
                ];
              }
              // 2. Model: Baseline (Green)
              if (dataKey === "base_predicted")
                return [isPercent(value), "Baseline Expected"];
              if (dataKey === "base_actual") {
                return [
                  isPercent(value),
                  `Actual (${payload.base_matches || payload.match_count} matches)`,
                ];
              }
              // 3. Model: Neural Scout (Amber)
              if (dataKey === "scout_predicted")
                return [isPercent(value), "NN Scout Expected"];
              if (dataKey === "scout_actual") {
                return [
                  isPercent(value),
                  `Actual (${payload.scout_matches || payload.match_count} matches)`,
                ];
              }
              // 4. Model: Legacy (Cyan)
              if (dataKey === "legacy_predicted")
                return [isPercent(value), "Legacy Expected"];
              if (dataKey === "legacy_actual") {
                return [
                  isPercent(value),
                  `Actual (${payload.scout_matches || payload.match_count} matches)`,
                ];
              }
              // Fallback for single-view mode
              if (dataKey === "avg_predicted")
                return [isPercent(value), "Model Expected"];
              if (dataKey === "actual_win_rate")
                return [isPercent(value), "Actual"];

              return [value, name];
            }}
          />
          {/* 🎯 Neural Model (Indigo) */}
          {(viewMode === "xgboost_nn" || viewMode === "both") && (
            <>
              {/* Dashed line for Neural Predicted Confidence */}
              <Area
                dataKey={viewMode === "both" ? "nn_predicted" : "avg_predicted"}
                stroke="#6366f1"
                fill="none"
                strokeDasharray="5 5"
                strokeWidth={1}
                connectNulls
              />
              <Area
                name="nn_actual"
                type="monotone"
                dataKey={viewMode === "both" ? "nn_actual" : "actual_win_rate"}
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.1}
                strokeWidth={3}
              />
            </>
          )}
          {/* 🎯 Baseline Model (Green) */}
          {(viewMode === "xgboost" || viewMode === "both") && (
            <>
              {/* Dashed line for Baseline Predicted Confidence */}
              <Area
                dataKey={
                  viewMode === "both" ? "base_predicted" : "avg_predicted"
                }
                stroke="#22c55e"
                fill="none"
                strokeDasharray="5 5"
                strokeWidth={1}
                connectNulls
              />
              <Area
                name="base_actual"
                type="monotone"
                dataKey={
                  viewMode === "both" ? "base_actual" : "actual_win_rate"
                }
                stroke="#22c55e"
                fill="#22c55e"
                fillOpacity={0.1}
                strokeWidth={3}
              />
            </>
          )}

          {/* 🎯 Neural Scout (Amber) */}
          {(viewMode === "nn" || viewMode === "both") && (
            <>
              <Area
                dataKey={
                  viewMode === "both" ? "scout_predicted" : "avg_predicted"
                }
                stroke="#f59e0b"
                fill="none"
                strokeDasharray="5 5"
                strokeWidth={1}
                connectNulls
              />
              <Area
                name="scout_actual"
                type="monotone"
                dataKey={
                  viewMode === "both" ? "scout_actual" : "actual_win_rate"
                }
                stroke="#f59e0b" // Amber color
                fill="#f59e0b"
                fillOpacity={0.1}
                strokeWidth={3}
              />
            </>
          )}

          {(viewMode === "logistic" || viewMode === "both") && (
            <>
              <Area
                dataKey={
                  viewMode === "both" ? "legacy_predicted" : "avg_predicted"
                }
                stroke="#06b6d4" // Cyan
                fill="none"
                strokeDasharray="5 5"
                strokeWidth={1}
                connectNulls
              />
              <Area
                name="legacy_actual"
                type="monotone"
                dataKey={
                  viewMode === "both" ? "legacy_actual" : "actual_win_rate"
                }
                stroke="#06b6d4"
                fill="#06b6d4"
                fillOpacity={0.1}
                strokeWidth={3}
              />
            </>
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
