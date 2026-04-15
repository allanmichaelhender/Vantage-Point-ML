import { useState } from "react";
import { Plus, Zap, RefreshCw } from "lucide-react";
import { PredictModal } from "../components/dashboard/PredictModal";
import { MatchCard } from "../components/dashboard/MatchCard";
import { useLiveMatches } from "../hooks/useLiveMatches";
import api from "../services/api";

export default function DashboardPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { matches, lastSync, error, refetch } = useLiveMatches();
  const [manualPredictions, setManualPredictions] = useState<any[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  const displayedMatches = matches;

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      await api.post("/upcoming/sync/manual");
      await refetch();
    } catch (err) {
      console.error("Manual sync failed:", err);
    } finally {
      setIsSyncing(false);
    }
  };

  const formatLastSync = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    const today = new Date();
    const isToday = date.toDateString() === today.toDateString();

    if (isToday) {
      return `Today at ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
    }
    return date.toLocaleDateString([], {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* 🚀 Top Header Section */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Live Dashboard
            <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full uppercase tracking-widest font-mono">
              v2
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time XGBoost + NN Probabilities
          </p>
        </div>

        <div className="flex items-center gap-3">
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
        </div>
      </header>

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
      {/* 🎾 Featured Matches Grid */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
            Featured Games
          </h2>
        </div>

        {error ? (
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

      {/* 🔄 Sync Button at Bottom Right */}
      <div className="fixed bottom-8 right-8 flex items-center gap-4">
        <span className="text-slate-400 text-sm">
          Lastest sync: {formatLastSync(lastSync)}
        </span>
        <button
          onClick={handleManualSync}
          disabled={isSyncing}
          className="flex items-center gap-2 text-white hover:text-slate-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw size={16} className={isSyncing ? "animate-spin" : ""} />
          <span className="text-sm">Sync</span>
        </button>
      </div>

      <PredictModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onPredictionSuccess={(newMatch) =>
          setManualPredictions([newMatch, ...manualPredictions])
        }
      />
    </div>
  );
}
