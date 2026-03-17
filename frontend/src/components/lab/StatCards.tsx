import type { LabData, ModelType } from "../../types/lab";

interface Props {
  data: LabData;
  globalModel: ModelType;
}

export function StatCards({ data, globalModel }: Props) {
  // 🎯 Extract the summary for the currently active global model
  const summary = data[globalModel].summary;

  const items = [
    {
      label: "Total ROI",
      value: `${(summary.roi * 100).toFixed(2)}%`,
      color: summary.roi >= 0 ? "text-green-400" : "text-red-400",
    },
    {
      label: "Brier Score",
      value: summary.brier_score.toFixed(4),
      color: "text-indigo-400", // 🧠 Changed to Indigo to match your NN theme
    },
    {
      label: "Win Rate",
      value: `${(summary.win_rate * 100).toFixed(1)}%`,
      color: "text-slate-100",
    },
    {
      label: "Profit",
      value: `£${summary.total_profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      color: summary.total_profit >= 0 ? "text-green-400" : "text-red-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {items.map((item) => (
        <div
          key={item.label}
          className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-sm transition-all duration-300"
        >
          <div className="flex justify-between items-center">
            <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">
              {item.label}
            </p>
            {/* 🎯 Small indicator of which model is providing the stats */}
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500 font-mono uppercase">
              {globalModel === "xgboost_nn"
                ? "Hybrid"
                : globalModel === "nn"
                  ? "Scout"
                  : globalModel === "logistic"
                    ? "Legacy"
                    : "Base"}
            </span>
          </div>
          <p className={`text-2xl font-mono mt-2 ${item.color}`}>
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}
