import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine
} from "recharts";
import type { LabData, ModelType } from '../../types/lab';

interface Props {
  data: LabData;
  globalModel: ModelType;
}

// 🎯 Helper to merge monthly stats
const mergeMonthlyData = (nn: any[], base: any[]) => {
  return nn.map((item, i) => ({
    month: item.month,
    nn_profit: item.profit,
    nn_roi: item.roi,
    base_profit: base[i]?.profit ?? 0,
    base_roi: base[i]?.roi ?? 0,
  }));
};

export function MonthlyBreakdown({ data, globalModel }: Props) {
  const [viewMode, setViewMode] = useState<ModelType | 'both'>(globalModel);

  useEffect(() => {
    setViewMode(globalModel);
  }, [globalModel]);

  const chartData = viewMode === 'both' 
    ? mergeMonthlyData(data.xgboost_nn.monthly_breakdown, data.xgboost.monthly_breakdown)
    : data[viewMode].monthly_breakdown;

  return (
    <div className="group relative bg-slate-900 border border-slate-800 p-6 rounded-xl h-[450px] w-full">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest">
            Monthly Profit & Loss (GBP)
          </h3>
          <p className="text-slate-500 text-[10px] mt-1 italic">
            Performance breakdown by calendar month
          </p>
        </div>

        {/* 🎯 Local Controls */}
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

      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={chartData} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="month" stroke="#475569" fontSize={10} tickMargin={10} />
          <YAxis 
            stroke="#475569" 
            fontSize={10} 
            tickFormatter={(val) => `£${Math.round(val)}`} 
          />
          <ReferenceLine y={0} stroke="#475569" />

          <Tooltip
            cursor={{ fill: "#ffffff", opacity: 0.05 }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg shadow-2xl space-y-3">
                    <p className="text-[10px] text-slate-500 font-bold uppercase border-b border-slate-800 pb-1">
                      {payload[0].payload.month} Results
                    </p>
                    {payload.map((entry: any) => {
                      const isNN = entry.dataKey.includes('nn');
                      const profit = Number(entry.value);
                      const roi = isNN ? entry.payload.nn_roi : (entry.payload.base_roi || entry.payload.roi);
                      
                      return (
                        <div key={entry.dataKey} className="space-y-0.5">
                          <p className="text-[9px] text-slate-500 font-bold uppercase">
                            {isNN ? 'Neural DNA' : 'Baseline'}
                          </p>
                          <div className="flex justify-between gap-6">
                            <span className="text-sm font-bold font-mono" style={{ color: profit >= 0 ? "#22c55e" : "#ef4444" }}>
                              £{profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              {(roi * 100).toFixed(1)}% ROI
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
          {(viewMode === 'xgboost_nn' || viewMode === 'both') && (
            <Bar dataKey={viewMode === 'both' ? "nn_profit" : "profit"} radius={[2, 2, 0, 0]}>
              {chartData.map((entry: any, index: number) => (
                <Cell 
                  key={`nn-${index}`} 
                  fill={viewMode === 'both' ? "#6366f1" : (entry.profit >= 0 ? "#22c55e" : "#ef4444")} 
                />
              ))}
            </Bar>
          )}

          {/* 🎯 Baseline Bar */}
          {(viewMode === 'xgboost' || viewMode === 'both') && (
            <Bar dataKey={viewMode === 'both' ? "base_profit" : "profit"} radius={[2, 2, 0, 0]}>
              {chartData.map((entry: any, index: number) => (
                <Cell 
                  key={`base-${index}`} 
                  fill={viewMode === 'both' ? "#22c55e" : (entry.profit >= 0 ? "#22c55e" : "#ef4444")} 
                />
              ))}
            </Bar>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
