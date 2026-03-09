import { ComposedChart, Line, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export function CalibrationChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) return <div className="h-[400px] flex items-center justify-center text-slate-500 italic">No Calibration Data</div>;

  return (
    <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl h-[400px]">
      <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-6">Reliability Diagram (Calibration)</h3>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          
          {/* 🎯 Using avg_predicted for X-Axis */}
          <XAxis 
            dataKey="avg_predicted" 
            type="number" 
            domain={[0.5, 1]} 
            stroke="#475569" 
            fontSize={12} 
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
          />
          
          {/* 🎯 Using actual_win_rate for Y-Axis */}
          <YAxis 
            type="number" 
            domain={[0.5, 1]} 
            stroke="#475569" 
            fontSize={12} 
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
          />
          
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }} 
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
            formatter={(val: number) => [`${(val * 100).toFixed(1)}%`]}
          />
          
          {/* The Perfect Calibration Line (Diagonal) */}
          <ReferenceLine segment={[{ x: 0.5, y: 0.5 }, { x: 1, y: 1 }]} stroke="#475569" strokeDasharray="5 5" />
          
          {/* 🎯 Mapping to actual_win_rate */}
          <Scatter name="Actual Results" dataKey="actual_win_rate" fill="#3b82f6" />
          <Line type="monotone" dataKey="actual_win_rate" stroke="#3b82f6" dot={false} strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
