import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

export function MonthlyBreakdown({ data }: { data: any[] }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl h-[400px]">
      <h3 className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-6">
        Monthly Profit & Loss (GBP)
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="month" stroke="#475569" fontSize={12} tickMargin={10} />
          <YAxis stroke="#475569" fontSize={12} tickFormatter={(val) => `$${val}`} />
          <Tooltip 
            cursor={{ fill: '#1e293b', opacity: 0.4 }}
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
          />
          <ReferenceLine y={0} stroke="#475569" />
          <Bar dataKey="profit" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.profit >= 0 ? '#22c55e' : '#ef4444'} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
