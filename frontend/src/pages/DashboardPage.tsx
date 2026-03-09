import { useState } from "react";
import { Plus, Zap, Filter, TrendingUp, Info } from "lucide-react";
import { PredictModal } from "../components/dashboard/PredictModal";
import { MatchCard } from "../components/dashboard/MatchCard";
import { useLiveMatches } from "../hooks/useLiveMatches";

export default function DashboardPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showOnlyValue, setShowOnlyValue] = useState(false);
  const { matches, status, lastSync, error } = useLiveMatches();
  const [manualPredictions, setManualPredictions] = useState<any[]>([]);



  // Filter logic for "Edge" (Value Bets)
  const displayedMatches = showOnlyValue
    ? matches.filter((m) => (m.model_prob - m.bookie_prob) * 100 > 3)
    : matches.slice(0, 20);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* 🚀 Top Header Section */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Live Dashboard
            <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full uppercase tracking-widest font-mono">
              v1
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time XGBoost Probabilities
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-blue-900/40 active:scale-95 group"
        >
          <Plus
            size={18}
            className="group-hover:rotate-90 transition-transform"
          />
          <span>Predict Custom Match</span>
        </button>
      </header>

      {/* 📊 Summary Banner (Quick Context) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-2 bg-green-500/10 rounded-lg text-green-400">
            <TrendingUp size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-bold uppercase">
              Today's Avg Edge
            </p>
            <p className="text-lg font-mono text-white">+4.2%</p>
          </div>
        </div>
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
            <Zap size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-bold uppercase">
              Active Models
            </p>
            <p className="text-lg font-mono text-white">XGB v4, CatBoost v1</p>
          </div>
        </div>
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-2 bg-slate-800 rounded-lg text-slate-400">
            <Info size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-bold uppercase">
              Model Confidence
            </p>
            <p className="text-lg font-mono text-white">94.1% (High)</p>
          </div>
        </div>
      </div>

      {manualPredictions.length > 0 && (
        <section className="mb-12 animate-in slide-in-from-top duration-500">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-blue-400 flex items-center gap-2">
              <Zap size={18} className="fill-blue-400" />
              Your Custom Predictions
            </h2>
            <button
              onClick={() => setManualPredictions([])}
              className="text-slate-500 hover:text-red-400 text-xs font-bold uppercase tracking-widest"
            >
              Clear All
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {manualPredictions.map((match, i) => (
              <MatchCard key={`manual-${i}`} match={match} isManual={true} />
            ))}
          </div>
          <div className="mt-8 border-b border-slate-800/50" />
        </section>
      )}


 {/* 🕒 Revalidating Banner */}
    {status === 'loading' && (
      <div className="mb-6 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-between animate-in fade-in slide-in-from-top-2">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
          <p className="text-xs font-bold text-blue-400 uppercase tracking-widest">
            Syncing Today's Odds...
          </p>
        </div>
        {lastSync && (
          <span className="text-[10px] text-slate-500 font-mono">
            Showing Cache from: {new Date(lastSync).toLocaleTimeString()}
          </span>
        )}
      </div>
    )}
      {/* 🎾 Featured Matches Grid */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
            Featured Games
          </h2>
         </div> 

        {status === 'loading' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="h-52 bg-slate-900/40 animate-pulse rounded-2xl border border-slate-800"
              />
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl text-center">
            Failed to load live match feed: {error}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedMatches.map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        )}
      </section>

      {/* 🛠️ Modals */}
       <PredictModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onPredictionSuccess={(newMatch) => setManualPredictions([newMatch, ...manualPredictions])}
      />
    </div>
  );
}
