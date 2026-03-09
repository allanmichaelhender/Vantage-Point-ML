import type { PerformanceSummary } from '../../types/lab';

export function StatCards({ summary }: { summary: PerformanceSummary }) {
  const items = [
    { label: 'Total ROI', value: `${(summary.roi * 100).toFixed(2)}%`, color: summary.roi >= 0 ? 'text-green-400' : 'text-red-400' },
    { label: 'Brier Score', value: summary.brier_score.toFixed(4), color: 'text-blue-400' },
    { label: 'Win Rate', value: `${(summary.win_rate * 100).toFixed(1)}%`, color: 'text-slate-100' },
    { label: 'Profit', value: `£${summary.total_profit.toFixed(2)}`, color: summary.total_profit >= 0 ? 'text-green-400' : 'text-red-400' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {items.map((item) => (
        <div key={item.label} className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-sm">
          <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">{item.label}</p>
          <p className={`text-2xl font-mono mt-1 ${item.color}`}>{item.value}</p>
        </div>
      ))}
    </div>
  );
}
