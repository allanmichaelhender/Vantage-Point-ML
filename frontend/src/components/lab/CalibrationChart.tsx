import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Line 
} from 'recharts';
import type { CalibrationPoint } from '../../types/lab';

export function CalibrationChart({ data }: { data: CalibrationPoint[] }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl h-[400px] w-full">
      <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-6">
        Model Calibration (Reliability)
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis 
            dataKey="prob_bucket" 
            stroke="#475569" 
            fontSize={12} 
            tickMargin={10} 
          />
          <YAxis 
            stroke="#475569" 
            fontSize={12} 
            domain={[0, 1]} 
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} 
          />
          
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
            }}
            labelStyle={{ color: "#94a3b8", fontWeight: "bold", marginBottom: "4px" }}
            itemStyle={{ fontSize: "12px" }}
            // 🎯 The Fix: Cast to 'any' to bypass TS strictness and show 3 fields
            formatter={(value: any, name: any, props: any) => {
              const { payload } = props;
              if (name === "avg_predicted") {
                return [`${(Number(value) * 100).toFixed(1)}%`, "Model Confidence"];
              }
              if (name === "actual_win_rate") {
                return [
                  `${(Number(value) * 100).toFixed(1)}%`, 
                  `Actual Win Rate (${payload.match_count} matches)`
                ];
              }
              return [value, name];
            }}
          />

          {/* 🎯 Actual Performance Area */}
          <Area
            name="actual_win_rate"
            type="monotone"
            dataKey="actual_win_rate"
            stroke="#22c55e"
            fill="#22c55e"
            fillOpacity={0.1}
            strokeWidth={3}
          />
          
          <Area
            name="avg_predicted"
            type="monotone"
            dataKey="avg_predicted"
            stroke="#3b82f6"
            fill="none"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
