import { useState } from 'react';
import LabPage from './pages/LabPage';
import DashboardPage from './pages/DashboardPage'; // 🎯 Import the new page
import { LayoutDashboard, Beaker, Zap } from 'lucide-react';

function App() {
  // 🧭 Simple state-based routing
  const [activePage, setActivePage] = useState<'dashboard' | 'lab'>('dashboard');

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* 📟 Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-8 sticky top-0 h-screen">
        <div className="flex items-center gap-3 px-2">
          <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-900/20">
            <Zap size={20} className="fill-current text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight">TENNIS.AI</span>
        </div>

        <nav className="flex flex-col gap-2">
          <button 
            onClick={() => setActivePage('dashboard')}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activePage === 'dashboard' 
                ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 shadow-inner' 
                : 'hover:bg-slate-800/50 text-slate-400'
            }`}
          >
            <LayoutDashboard size={18} />
            <span className="font-semibold text-sm">Live Dashboard</span>
          </button>

          <button 
            onClick={() => setActivePage('lab')}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activePage === 'lab' 
                ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 shadow-inner' 
                : 'hover:bg-slate-800/50 text-slate-400'
            }`}
          >
            <Beaker size={18} />
            <span className="font-semibold text-sm">Model Lab</span>
          </button>
        </nav>

        <div className="mt-auto p-4 bg-slate-800/30 rounded-2xl border border-slate-700/30">
          <p className="text-[10px] text-slate-500 uppercase font-black tracking-[0.2em]">Engine Status</p>
          <div className="flex items-center gap-2 mt-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
            <p className="text-xs font-mono text-slate-300">v1</p>
          </div>
        </div>
      </aside>

      {/* 🚀 Dynamic Content Area */}
      <main className="flex-1 overflow-y-auto bg-slate-950">
        {activePage === 'dashboard' ? <DashboardPage /> : <LabPage />}
      </main>
    </div>
  );
}

export default App;
