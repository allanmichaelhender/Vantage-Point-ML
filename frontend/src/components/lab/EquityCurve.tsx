import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { useState, useEffect } from "react";
import type { ModelType, LabData } from "../../types/lab";

interface Props {
  data: LabData;
  globalModel: ModelType;
}

const mergeData = (
  nnHybrid: any[],
  base: any[],
  nnScout: any[],
  legacy: any[],
) => {
  const baseMap = new Map(
    (base || []).map((item) => [item.date, item.balance]),
  );
  const scoutMap = new Map(
    (nnScout || []).map((item) => [item.date, item.balance]),
  );
  const legacyMap = new Map(
    (legacy || []).map((item) => [item.date, item.balance]),
  );

  return (nnHybrid || []).map((point) => ({
    date: point.date,
    nn_balance: point.balance,
    base_balance: baseMap.get(point.date) ?? null,
    scout_balance: scoutMap.get(point.date) ?? null,
    legacy_balance: legacyMap.get(point.date) ?? null, // 🎯 The fourth line
  }));
};

export function EquityCurve({ data, globalModel }: Props) {
  // 🎯 1. Local state (defaults to global, but can be 'both')
  const [viewMode, setViewMode] = useState<ModelType | "both">(globalModel);

  useEffect(() => {
    setViewMode(globalModel);
  }, [globalModel]);

  const chartData =
    viewMode === "both"
      ? mergeData(
          data.xgboost_nn.equity_curve,
          data.xgboost.equity_curve,
          data.nn.equity_curve,
          data.logistic.equity_curve,
        )
      : data[viewMode].equity_curve;

    return (
    <div className="group relative bg-slate-900 border border-slate-800 p-6 rounded-xl h-[450px] w-full">
      {/* --- 1. HEADER & CONTROLS (Isolated in its own row) --- */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest">
            Performance Trajectory (GBP)
          </h3>
          <p className="text-slate-500 text-[10px] mt-1 italic">
            {viewMode === "both"
              ? "Comparison Mode"
              : viewMode === "xgboost_nn"
              ? "Neural Hybrid Active"
              : viewMode === "xgboost"
              ? "Baseline Active"
              : viewMode === "nn"
              ? "Neural Scout Active"
              : "Legacy Model Active"}
          </p>
        </div>

        <div className="flex bg-slate-950/50 p-1 rounded-lg border border-slate-800 opacity-0 group-hover:opacity-100 transition-opacity">
          {["xgboost_nn", "xgboost", "nn", "logistic", "both"].map((mode) => {
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

      {/* --- 2. THE CHART (Direct child of the 450px container) --- */}
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorNN" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorBase" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorScout" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorLegacy" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />

          <XAxis
            dataKey="date"
            stroke="#475569"
            fontSize={10}
            tickFormatter={(str) => str.split("-").slice(1).join("/")}
          />

          <YAxis
            stroke="#475569"
            fontSize={10}
            domain={["dataMin - 50", "dataMax + 50"]}
            tickFormatter={(val) => `£${Math.round(val)}`}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
            }}
            formatter={(value: any, name: string, props: any) => {
              const formattedValue = `£${Number(value).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`;

              const displayName =
                props.name ||
                (name === "nn_balance" ? "Hybrid" : 
                 name === "base_balance" ? "Baseline" : 
                 name === "scout_balance" ? "Scout" : 
                 name === "legacy_balance" ? "Legacy" : "Model");

              return [formattedValue, displayName];
            }}
          />

          {/* Hybrid Area */}
          {(viewMode === "xgboost_nn" || viewMode === "both") && (
            <Area
              type="monotone"
              dataKey={viewMode === "both" ? "nn_balance" : "balance"}
              name="Hybrid"
              stroke="#6366f1"
              fill="url(#colorNN)"
              strokeWidth={2}
              connectNulls
            />
          )}

          {/* Baseline Area */}
          {(viewMode === "xgboost" || viewMode === "both") && (
            <Area
              type="monotone"
              dataKey={viewMode === "both" ? "base_balance" : "balance"}
              name="Baseline"
              stroke="#22c55e"
              fill="url(#colorBase)"
              strokeWidth={2}
              connectNulls
            />
          )}

          {/* Scout Area */}
          {(viewMode === "nn" || viewMode === "both") && (
            <Area
              type="monotone"
              dataKey={viewMode === "both" ? "scout_balance" : "balance"}
              name="Scout"
              stroke="#f59e0b"
              fill="url(#colorScout)"
              strokeWidth={2}
              connectNulls
            />
          )}

          {/* Legacy Area */}
          {(viewMode === "logistic" || viewMode === "both") && (
            <Area
              type="monotone"
              dataKey={viewMode === "both" ? "legacy_balance" : "balance"}
              name="Legacy"
              stroke="#06b6d4"
              fill="url(#colorLegacy)"
              strokeWidth={2}
              connectNulls
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );

}
