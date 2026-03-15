import { useState, useEffect } from "react";
import { X, Zap, Loader2, Trophy, Search, User } from "lucide-react";
import api from "../../services/api";

interface Player {
  player_id: string;
  player_name: string;
}

interface PredictionResult {
  p1_prob: number;
  p2_prob: number;
  p1_name: string;
  p2_name: string;
}

interface PredictModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPredictionSuccess: (prediction: any) => void; // 👈 Add this line!
}

export function PredictModal({
  isOpen,
  onClose,
  onPredictionSuccess
}: 
  PredictModalProps
) {
  // Input State
  const [p1Query, setP1Query] = useState("");
  const [p2Query, setP2Query] = useState("");
  const [p1Selected, setP1Selected] = useState<Player | null>(null);
  const [p2Selected, setP2Selected] = useState<Player | null>(null);
  const [surface, setSurface] = useState("Hard");

  // Search Results
  const [p1Results, setP1Results] = useState<Player[]>([]);
  const [p2Results, setP2Results] = useState<Player[]>([]);

  // Status State
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);

  // 🔍 Live Search Logic for Player 1
  useEffect(() => {
    if (p1Query.length < 2 || p1Selected) return setP1Results([]);
    const delayDebounceFn = setTimeout(async () => {
      const res = await api.get(`/players/search?q=${p1Query}`);
      setP1Results(res.data);
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [p1Query, p1Selected]);

  // 🔍 Live Search Logic for Player 2
  useEffect(() => {
    if (p2Query.length < 2 || p2Selected) return setP2Results([]);
    const delayDebounceFn = setTimeout(async () => {
      const res = await api.get(`/players/search?q=${p2Query}`);
      setP2Results(res.data);
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [p2Query, p2Selected]);

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post("/predict/manual-predict", {
        p1_id: p1Selected?.player_id,
        p2_id: p2Selected?.player_id,
        surface: surface,
      });

      // 🎯 Push the result to the Dashboard state
      onPredictionSuccess(response.data);

      // Close the modal immediately so they see the card pop in
      onClose();
      reset();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  const reset = () => {
    setResult(null);
    setP1Selected(null);
    setP2Selected(null);
    setP1Query("");
    setP2Query("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Zap size={18} className="text-blue-400 fill-blue-400" />
            <h3 className="text-xl font-bold text-white font-mono uppercase tracking-tight">
              Manual Analysis
            </h3>
          </div>
          <button
            onClick={reset}
            className="text-slate-500 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="p-8">
          {!result ? (
            <form onSubmit={handlePredict} className="space-y-6">
              {/* Player 1 Search */}
              <div className="relative">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">
                  Player 1
                </label>
                <div className="relative">
                  <Search
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                    size={16}
                  />
                  <input
                    value={p1Selected ? p1Selected.player_name : p1Query}
                    onChange={(e) => {
                      setP1Query(e.target.value);
                      setP1Selected(null);
                    }}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 pl-12 text-white outline-none focus:border-blue-500 transition-all"
                    placeholder="Search Player 1..."
                  />
                </div>
                {p1Results.length > 0 && (
                  <div className="absolute z-10 w-full mt-2 bg-slate-800 border border-slate-700 rounded-xl max-h-48 overflow-y-auto shadow-2xl">
                    {p1Results.map((p) => (
                      <button
                        key={p.player_id}
                        type="button"
                        onClick={() => {
                          setP1Selected(p);
                          setP1Results([]);
                        }}
                        className="w-full px-4 py-3 text-left hover:bg-blue-600 text-sm flex items-center gap-2"
                      >
                        <User size={14} /> {p.player_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Player 2 Search */}
              <div className="relative">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">
                  Player 2
                </label>
                <div className="relative">
                  <Search
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                    size={16}
                  />
                  <input
                    value={p2Selected ? p2Selected.player_name : p2Query}
                    onChange={(e) => {
                      setP2Query(e.target.value);
                      setP2Selected(null);
                    }}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 pl-12 text-white outline-none focus:border-blue-500 transition-all"
                    placeholder="Search Player 2..."
                  />
                </div>
                {p2Results.length > 0 && (
                  <div className="absolute z-10 w-full mt-2 bg-slate-800 border border-slate-700 rounded-xl max-h-48 overflow-y-auto shadow-2xl">
                    {p2Results.map((p) => (
                      <button
                        key={p.player_id}
                        type="button"
                        onClick={() => {
                          setP2Selected(p);
                          setP2Results([]);
                        }}
                        className="w-full px-4 py-3 text-left hover:bg-blue-600 text-sm flex items-center gap-2"
                      >
                        <User size={14} /> {p.player_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">
                  Surface
                </label>
                <select
                  value={surface}
                  onChange={(e) => setSurface(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-white appearance-none"
                >
                  <option>Hard</option>
                  <option>Clay</option>
                  <option>Grass</option>
                </select>
              </div>

              <button
                disabled={loading || !p1Selected || !p2Selected}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3"
              >
                {loading ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  "Run v4 Prediction"
                )}
              </button>
            </form>
          ) : (
            <div className="text-center py-6 animate-in zoom-in-95 duration-300">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-500/10 rounded-full mb-6 border border-blue-500/20">
                <Trophy size={40} className="text-blue-500" />
              </div>
              <h4 className="text-slate-400 text-sm font-medium mb-1">
                {result.p1_name} Win Probability
              </h4>
              <div className="text-7xl font-black text-white tracking-tighter">
                {(result.p1_prob * 100).toFixed(1)}
                <span className="text-2xl text-blue-500">%</span>
              </div>
              <button
                onClick={() => setResult(null)}
                className="mt-10 text-blue-400 hover:text-blue-300 font-bold text-sm uppercase tracking-widest"
              >
                ← New Search
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
