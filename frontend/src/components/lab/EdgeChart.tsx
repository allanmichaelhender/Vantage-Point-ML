import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import type { LabData, ModelType } from "../../types/lab";

interface Props {
  data: LabData;
  globalModel: ModelType;
}

const mergeEdgeData = (
  nn_hybrid: any[],
  base: any[],
  nn_scout: any[],
  legacy: any[],
) => {
  return nn_hybrid.map((item, i) => ({
    bucket: item.bucket,
    // Hybrid
    nn_roi: item.roi,
    nn_matches: item.match_count,
    // Baseline
    base_roi: base[i]?.roi ?? 0,
    base_matches: base[i]?.match_count ?? 0,
    // Neural Scout
    scout_roi: nn_scout[i]?.roi ?? 0,
    scout_matches: nn_scout[i]?.match_count ?? 0,
    // Legacy (Logistic) 🎯 NEW
    legacy_roi: legacy[i]?.roi ?? 0,
    legacy_matches: legacy[i]?.match_count ?? 0,
  }));
};

export function EdgeChart({ data, globalModel }: Props) {
  const [viewMode, setViewMode] = useState<ModelType | "both">(globalModel);

  useEffect(() => {
    setViewMode(globalModel);
  }, [globalModel]);

  const chartData =
    viewMode === "both"
      ? mergeEdgeData(
          data.xgboost_nn.edge_analysis,
          data.xgboost.edge_analysis,
          data.nn.edge_analysis,
          data.logistic.edge_analysis, // 🎯 Add fourth arg
        )
      : data[viewMode].edge_analysis;

  return (
    <div className="group relative bg-slate-900 border border-slate-800 p-6 rounded-xl h-[450px] w-full">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest">
            ROI by Edge Size
          </h3>
          <p className="text-slate-500 text-[10px] mt-1 italic">
            Visualising profit yield across different "value" buckets
          </p>
        </div>

        {/* 🎯 Updated Local Controls Container */}
        <div className="flex bg-slate-950/50 p-1 rounded-lg border border-slate-800 opacity-0 group-hover:opacity-100 transition-opacity">
          {["xgboost_nn", "xgboost", "nn", "logistic", "both"].map((mode) => {
            // 🧠 Mapping object keeps the ternary mess out of your JSX
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
                className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase transition-all ${
                  viewMode === mode
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/40"
                }`}
              >
                {labels[mode]}
              </button>
            );
          })}
        </div>
      </div>

      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={chartData as any[]} barGap={8}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#1e293b"
            vertical={false}
          />
          <XAxis
            dataKey="bucket"
            stroke="#475569"
            fontSize={10}
            tickFormatter={(val) => val.split(" ")[0]}
          />
          <YAxis
            stroke="#475569"
            fontSize={10}
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
          />
          <ReferenceLine y={0} stroke="#475569" />

          <Tooltip
            cursor={{ fill: "#ffffff", opacity: 0.05 }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg shadow-2xl space-y-2">
                    <p className="text-[10px] text-slate-500 font-bold uppercase border-b border-slate-800 pb-1">
                      {payload[0].payload.bucket} Edge
                    </p>
                    {payload.map((entry: any) => {
                      const isNN = entry.dataKey.includes("nn");
                      const roi = Number(entry.value) * 100;
                      const matches = isNN
                        ? entry.payload.nn_matches
                        : entry.payload.base_matches ||
                          entry.payload.match_count;
                      return (
                        <div key={entry.dataKey} className="space-y-1">
                          <p className="text-[10px] text-indigo-400 font-bold">
                            {isNN ? "Neural DNA" : "Baseline"}
                          </p>
                          <div className="flex justify-between gap-4">
                            <span
                              className="text-xs font-bold"
                              style={{
                                color: roi >= 0 ? "#22c55e" : "#ef4444",
                              }}
                            >
                              {roi.toFixed(2)}% ROI
                            </span>
                            <span className="text-[10px] text-slate-500">
                              {matches} Matches
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              }
              return null;
            }}
          />

          {/* 🎯 Neural Bar */}
          {(viewMode === "xgboost_nn" || viewMode === "both") && (
            <Bar
              dataKey={viewMode === "both" ? "nn_roi" : "roi"}
              name="Neural DNA"
            >
              {chartData.map((entry: any, index: number) => (
                <Cell
                  key={`nn-${index}`}
                  fill={
                    viewMode === "both"
                      ? "#6366f1"
                      : entry.roi >= 0
                        ? "#22c55e"
                        : "#ef4444"
                  }
                />
              ))}
            </Bar>
          )}

          {/* 🎯 Baseline Bar */}
          {(viewMode === "xgboost" || viewMode === "both") && (
            <Bar
              dataKey={viewMode === "both" ? "base_roi" : "roi"}
              name="Baseline"
            >
              {chartData.map((entry: any, index: number) => (
                <Cell
                  key={`base-${index}`}
                  fill={
                    viewMode === "both"
                      ? "#22c55e"
                      : entry.roi >= 0
                        ? "#22c55e"
                        : "#ef4444"
                  }
                />
              ))}
            </Bar>
          )}

          {/* 🎯 Neural Scout Bar (Amber) */}
          {(viewMode === "nn" || viewMode === "both") && (
            <Bar
              dataKey={viewMode === "both" ? "scout_roi" : "roi"}
              name="Neural Scout"
            >
              {chartData.map((entry: any, index: number) => (
                <Cell
                  key={`scout-${index}`}
                  fill={
                    viewMode === "both"
                      ? "#f59e0b"
                      : entry.roi >= 0
                        ? "#22c55e"
                        : "#ef4444"
                  }
                />
              ))}
            </Bar>
          )}

          {(viewMode === "logistic" || viewMode === "both") && (
            <Bar
              dataKey={viewMode === "both" ? "legacy_roi" : "roi"}
              name="Legacy"
            >
              {chartData.map((entry: any, index: number) => (
                <Cell
                  key={`legacy-${index}`}
                  fill={
                    viewMode === "both"
                      ? "#06b6d4"
                      : entry.roi >= 0
                        ? "#22c55e"
                        : "#ef4444"
                  }
                />
              ))}
            </Bar>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
