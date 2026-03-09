import { usePerformance } from "../hooks/usePerformance";
import { StatCards } from "../components/lab/StatCards";
import { EquityChart } from "../components/lab/EquityChart";
import { MonthlyBreakdown } from "../components/lab/MonthlyBreakdown";
import { CalibrationChart } from "../components/lab/CalibrationChart";
import { EdgeChart } from "../components/lab/EdgeChart";

export default function LabPage() {
  const { data, loading, error } = usePerformance();

  if (loading)
    return (
      <div className="p-8 text-slate-400 animate-pulse">
        Loading Lab Intelligence...
      </div>
    );
  if (error) return <div className="p-8 text-red-400">Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Model Lab</h1>
        <p className="text-slate-400">XGBoost Performance Audit</p>
      </header>

      <StatCards summary={data.summary} />

      <div className="grid grid-cols-1 gap-6">
        <EquityChart data={data.equity_curve} />
        <MonthlyBreakdown data={data.monthly_breakdown} />
        <CalibrationChart data={data.calibration_data} />
        <EdgeChart data={data.edge_analysis} />
      </div>
    </div>
  );
}
("");
