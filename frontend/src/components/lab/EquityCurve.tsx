import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { useState, useEffect } from 'react';
import type { ModelType, LabData } from '../../types/lab';


interface Props {
  data: LabData;
  globalModel: ModelType;
}

const mergeData = (nnCurve: any[], baseCurve: any[]) => {
  const merged: any[] = [];
  
  // Create a map of the second curve for easy lookup
  const baseMap = new Map(baseCurve.map(item => [item.date, item.balance]));

  nnCurve.forEach(nnPoint => {
    const baseBalance = baseMap.get(nnPoint.date);
    
    merged.push({
      date: nnPoint.date,
      nn_balance: nnPoint.balance,
      // If the dates don't perfectly match, we fallback to the previous point or null
      base_balance: baseBalance ?? null 
    });
  });

  return merged;
};

export function EquityCurve({ data, globalModel }: Props) {
  // 🎯 1. Local state (defaults to global, but can be 'both')
  const [viewMode, setViewMode] = useState<ModelType | 'both'>(globalModel);

  // 🎯 2. Sync with Master Button
  // When you click the master button, every chart "snaps" to that model
  useEffect(() => {
    setViewMode(globalModel);
  }, [globalModel]);

  // 🎯 3. Logic to prepare the chart data
  const chartData = viewMode === 'both' 
    ? mergeData(data.xgboost_nn.equity_curve, data.xgboost.equity_curve)
    : data[viewMode].equity_curve;

  return (
  <div className="group relative bg-slate-900 border border-slate-800 p-6 rounded-xl h-[450px] w-full">
    {/* --- HEADER & LOCAL CONTROLS --- */}
    <div className="flex justify-between items-start mb-6">
      <div>
        <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest">
          Performance Trajectory (GBP)
        </h3>
        <p className="text-slate-500 text-[10px] mt-1 italic">
          {viewMode === 'both' ? 'Comparison Mode' : `${viewMode === 'xgboost_nn' ? 'Neural Hybrid' : 'Baseline Stats'} Active`}
        </p>
      </div>

      {/* 🎯 Local Toggle (Visible on Hover via 'group') */}
      <div className="flex bg-slate-950/50 p-1 rounded-lg border border-slate-800 opacity-0 group-hover:opacity-100 transition-opacity">
        {['xgboost_nn', 'xgboost', 'both'].map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode as any)}
            className={`px-3 py-1 rounded text-[10px] font-bold uppercase transition-colors ${
              viewMode === mode ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {mode === 'xgboost_nn' ? 'Neural' : mode === 'xgboost' ? 'Base' : 'Vs'}
          </button>
        ))}
      </div>
    </div>

    {/* --- CHART --- */}
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
          domain={['dataMin - 50', 'dataMax + 50']}
          tickFormatter={(val) => `£${Math.round(val)}`}
        />

        <Tooltip
  contentStyle={{
    backgroundColor: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: "8px",
  }}
  // 🎯 Use (value, name, props) to get access to the full payload
  formatter={(value: any, name: string, props: any) => {
    // 1. Format the money value
    const formattedValue = `£${Number(value).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;

    // 2. Map the display name based on the dataKey or name prop
    // This ensures 'nn_balance' shows as 'Neural DNA' in the popup
    const displayName = props.name || (name === 'nn_balance' ? 'Neural DNA' : 'Baseline Stats');

    return [formattedValue, displayName];
  }}
/>

        {/* 🎯 Dynamic Rendering: Show NN if active or 'both' */}
        {(viewMode === 'xgboost_nn' || viewMode === 'both') && (
          <Area
            type="monotone"
            dataKey={viewMode === 'both' ? "nn_balance" : "balance"}
            name="Neural DNA"
            stroke="#6366f1"
            fill="url(#colorNN)"
            strokeWidth={2}
          />
        )}

        {/* 🎯 Dynamic Rendering: Show Baseline if active or 'both' */}
        {(viewMode === 'xgboost' || viewMode === 'both') && (
          <Area
            type="monotone"
            dataKey={viewMode === 'both' ? "base_balance" : "balance"}
            name="Baseline"
            stroke="#22c55e"
            fill="url(#colorBase)"
            strokeWidth={2}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  </div>
);

}
