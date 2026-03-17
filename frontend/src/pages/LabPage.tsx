import { useState } from "react"; // 🎯 Added missing useState
import { usePerformance } from "../hooks/usePerformance";
import { StatCards } from "../components/lab/StatCards";
import { EquityCurve } from "../components/lab/EquityCurve"; // 🎯 Named consistently
import { MonthlyBreakdown } from "../components/lab/MonthlyBreakdown";
import { CalibrationChart } from "../components/lab/CalibrationChart";
import { EdgeChart } from "../components/lab/EdgeChart";
import type { ModelType } from "../types/lab"; // 🎯 Pull in your type

export default function LabPage() {
  const { data, loading, error } = usePerformance();
  const [globalModel, setGlobalModel] = useState<ModelType>("xgboost_nn");

  if (loading)
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <p className="text-slate-400 animate-pulse font-mono uppercase tracking-tighter">
          Loading Lab Intelligence...
        </p>
      </div>
    );

  if (error)
    return (
      <div className="p-8 text-red-400 bg-slate-950 min-h-screen">
        Error: {error}
      </div>
    );
  if (!data) return null;

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-slate-100 pb-20">
      <header className="flex flex-col md:flex-row justify-between items-end mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-black tracking-tight text-white">
            Model Lab
          </h1>
          <p className="text-slate-500 mt-1 font-medium">
            Backtesting from Jan 2025 onwards
          </p>
        </div>

        {/* 🎯 THE MASTER TOGGLE UI - Updated to include NN & Legacy */}
        <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 shadow-xl">
          {(["xgboost_nn", "xgboost", "nn", "logistic"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setGlobalModel(m)}
              className={`px-6 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${
                globalModel === m
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {m === "xgboost_nn"
                ? "Neural Hybrid"
                : m === "xgboost"
                  ? "Baseline"
                  : m === "nn"
                    ? "Neural Scout"
                    : "Legacy"}{" "}
              {/* 🎯 User sees 'Legacy' for Logistic */}
            </button>
          ))}
        </div>
      </header>

      {/* 🎯 Top Stats Row - Automatically follows globalModel */}
      <StatCards data={data} globalModel={globalModel} />

      {/* 🎯 The Main Analysis Grid */}
      <div className="grid grid-cols-1 gap-8 mt-8">

        {/* Comparison Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <CalibrationChart data={data} globalModel={globalModel} />
          <EdgeChart data={data} globalModel={globalModel} />
        <EquityCurve data={data} globalModel={globalModel} />

        </div>

        {/* Monthly Breakdown (Full Width) */}
        <MonthlyBreakdown data={data} globalModel={globalModel} />
      </div>
    </div>
  );
}
