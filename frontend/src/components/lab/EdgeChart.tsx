import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import type { EdgeBucket } from '../../types/lab';

export function EdgeChart({ data }: { data: EdgeBucket[] }) {
  // 🎯 Guard Clause: Prevent crash if data is loading or empty
  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl h-[400px] flex items-center justify-center">
        <p className="text-slate-500 animate-pulse text-xs uppercase tracking-widest font-bold">
          Analyzing Edge Data...
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl h-[400px]">
      <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-6">
        ROI by Edge Size
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          
          {/* 🎯 Use 'bucket' key for X-Axis labels */}
          <XAxis 
            dataKey="bucket" 
            stroke="#475569" 
            fontSize={10} 
            interval={0}
            tickFormatter={(value) => value.split(' ')[0]} // e.g., "15%+" instead of full text
          />
          
          {/* 🎯 Convert decimal ROI to % for Y-Axis */}
          <YAxis 
            stroke="#475569" 
            fontSize={12} 
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} 
          />
          
          <Tooltip 
            cursor={{ fill: '#ffffff', opacity: 0.4 }}
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
            formatter={(value: number) => [`${(value * 100).toFixed(2)}%`, 'ROI']}
          />
          
          <ReferenceLine y={0} stroke="#475569" />
          
          <Bar dataKey="roi">
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                // 🎯 Dynamic coloring: Green for profit, Red for loss
                fill={entry.roi >= 0 ? '#22c55e' : '#ef4444'} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
