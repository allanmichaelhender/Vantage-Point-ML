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

// 🎯 Helper to merge edge buckets by name
const mergeEdgeData = (nn: any[], base: any[]) => {
  return nn.map((item, i) => ({
    bucket: item.bucket,
    nn_roi: item.roi,
    nn_matches: item.match_count,
    base_roi: base[i]?.roi ?? 0,
    base_matches: base[i]?.match_count ?? 0,
  }));
};

export function EdgeChart({ data, globalModel }: Props) {
  const [viewMode, setViewMode] = useState<ModelType | 'both'>(globalModel);

  useEffect(() => {
    setViewMode(globalModel);
  }, [globalModel]);

  const chartData = viewMode === 'both' 
    ? mergeEdgeData(data.xgboost_nn.edge_analysis, data.xgboost.edge_analysis)
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
        <BarChart data={chartData} barGap={8}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="bucket" stroke="#475569" fontSize={10} tickFormatter={(val) => val.split(" ")[0]} />
          <YAxis stroke="#475569" fontSize={10} tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
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
                      const isNN = entry.dataKey.includes('nn');
                      const roi = Number(entry.value) * 100;
                      const matches = isNN ? entry.payload.nn_matches : (entry.payload.base_matches || entry.payload.match_count);
                      return (
                        <div key={entry.dataKey} className="space-y-1">
                          <p className="text-[10px] text-indigo-400 font-bold">
                            {isNN ? 'Neural DNA' : 'Baseline'}
                          </p>
                          <div className="flex justify-between gap-4">
                            <span className="text-xs font-bold" style={{ color: roi >= 0 ? "#22c55e" : "#ef4444" }}>
                              {roi.toFixed(2)}% ROI
                            </span>
                            <span className="text-[10px] text-slate-500">{matches} Matches</span>
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
            <Bar dataKey={viewMode === 'both' ? "nn_roi" : "roi"} name="Neural DNA">
              {chartData.map((entry: any, index: number) => (
                <Cell 
                  key={`nn-${index}`} 
                  fill={viewMode === 'both' ? "#6366f1" : (entry.roi >= 0 ? "#22c55e" : "#ef4444")} 
                />
              ))}
            </Bar>
          )}

          {/* 🎯 Baseline Bar */}
          {(viewMode === 'xgboost' || viewMode === 'both') && (
            <Bar dataKey={viewMode === 'both' ? "base_roi" : "roi"} name="Baseline">
              {chartData.map((entry: any, index: number) => (
                <Cell 
                  key={`base-${index}`} 
                  fill={viewMode === 'both' ? "#22c55e" : (entry.roi >= 0 ? "#22c55e" : "#ef4444")} 
                />
              ))}
            </Bar>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
