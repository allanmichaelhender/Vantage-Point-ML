export function MatchCard({ match, isManual = false }: { match: any; isManual?: boolean }) {
  // 🎯 UNIVERSAL MAPPING: Handle both API formats
  const p1Name = isManual ? match.p1_stats.player_name : match.p1_name;
  const p2Name = isManual ? match.p2_stats.player_name : match.p2_name;
  const modelProb = match.p1_prob; 
  
  // Odds/Edge logic (Only for Featured Games)
  const bookieProb = match.pin_p1 ? (1 / match.pin_p1) : null;
  const edge = (bookieProb && modelProb) ? (modelProb - bookieProb) * 100 : 0;

  return (
    <div className={`bg-slate-900 border transition-all p-5 rounded-2xl ${
      isManual ? 'border-blue-500/40 bg-blue-500/5 shadow-lg shadow-blue-500/10' : 
      edge > 3 ? 'border-green-500/30 shadow-lg shadow-green-500/5' : 'border-slate-800'
    }`}>
      
      {/* 🏷️ TOP TAGS */}
      <div className="flex justify-between items-start mb-4">
        <span className="text-[10px] font-bold bg-slate-800 text-slate-400 px-2 py-1 rounded uppercase tracking-tight">
          {match.surface} • {isManual ? 'v4 Manual Analysis' : match.tournament}
        </span>
        {!isManual && edge > 2 && (
          <span className="text-[10px] font-bold text-green-400 bg-green-400/10 px-2 py-1 rounded border border-green-400/20">
            +{edge.toFixed(1)}% EDGE
          </span>
        )}
      </div>

      {/* 📊 PROBABILITY SECTION */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="font-semibold text-slate-100">{p1Name}</span>
          <span className="text-sm font-mono text-blue-400">{(modelProb * 100).toFixed(1)}%</span>
        </div>
        <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-blue-500 transition-all duration-700" style={{ width: `${modelProb * 100}%` }} />
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500">{p2Name}</span>
          <span className="text-sm font-mono text-slate-600">{((1 - modelProb) * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* 🚀 DEEP STATS (Only for Manual Runs) */}
      {isManual && (
        <div className="mt-4 pt-4 border-t border-slate-800/50 grid grid-cols-2 gap-4">
          <div className="space-y-1">
             <p className="text-[9px] text-slate-500 font-bold uppercase">Elo: {match.p1_stats.current_elo.toFixed(0)}</p>
             <p className="text-[10px] text-slate-400">Aces/G: <span className="text-white">{match.p1_stats.rolling_ace_per_game.toFixed(2)}</span></p>
             <p className="text-[10px] text-slate-400">BP Save: <span className="text-white">{(match.p1_stats.rolling_bp_save_pct * 100).toFixed(0)}%</span></p>
          </div>
          <div className="space-y-1 border-l border-slate-800 pl-4">
             <p className="text-[9px] text-slate-500 font-bold uppercase">Elo: {match.p2_stats.current_elo.toFixed(0)}</p>
             <p className="text-[10px] text-slate-400">Aces/G: <span className="text-white">{match.p2_stats.rolling_ace_per_game.toFixed(2)}</span></p>
             <p className="text-[10px] text-slate-400">BP Save: <span className="text-white">{(match.p2_stats.rolling_bp_save_pct * 100).toFixed(0)}%</span></p>
          </div>
        </div>
      )}
      
      {/* 📅 FOOTER */}
      <div className="mt-4 pt-4 border-t border-slate-800 flex justify-between text-[10px] text-slate-500 font-medium">
        {bookieProb ? (
          <span>Bookie Implied: {(bookieProb * 100).toFixed(0)}%</span>
        ) : (
          <span className="text-blue-500/50">XGBOOST V4 ENGINE</span>
        )}
        <span className="text-slate-400 italic">v4.2.1 Stable</span>
      </div>
    </div>
  );
}
