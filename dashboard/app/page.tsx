"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

interface Opportunity {
  vertical: string;
  tam_score: number;
  recommendation: string;
}

interface FactoryState {
  active_verticals: number;
  pipeline_score: number;
  agents_deployed: number;
  agents_total: number;
  last_run_timestamp: string | null;
  qualified_leads: number;
  opportunities: Opportunity[];
}

export default function Home() {
  const [state, setState] = useState<FactoryState | null>(null);
  const [loading, setLoading] = useState(true);
  const [deploying, setDeploying] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    fetchState();
  }, []);

  const fetchState = async () => {
    try {
      const res = await fetch('/api/state');
      const data = await res.json();
      setState(data);
      setLoading(false);
    } catch (e) {
      console.error("Failed to fetch factory state", e);
      setLoading(false);
    }
  };

  const handleDeploy = async (agentName: string) => {
    setDeploying(true);
    addLog(`Initiating deployment for ${agentName}...`);

    try {
      const res = await fetch('/api/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentName })
      });
      const data = await res.json();

      if (data.success) {
        addLog(`✅ Deployment Successful!`);
        addLog(data.logs);
      } else {
        addLog(`❌ Deployment Failed: ${data.error}`);
      }
    } catch (e: any) {
      addLog(`❌ Error: ${e.message}`);
    } finally {
      setDeploying(false);
    }
  };

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `> ${msg}`]);
  };

  const formatLastUpdated = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <div className="p-8">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">🏗️ X AGENT FACTORY</h1>
          <p className="text-slate-500 font-mono">
            SYSTEM STATUS: ONLINE | LAST UPDATED: {formatLastUpdated(state?.last_run_timestamp || null)}
          </p>
        </div>
        <div className="flex gap-3">
          <Link href="/admin/usage" className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm">
            ⚙️ System Status
          </Link>
          <Link href="/growth" className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-bold transition-colors">
            🚀 LAUNCH HUNTER
          </Link>
        </div>
      </header>


      {/* KPIs */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Active Verticals</h3>
          <p className="text-4xl font-black text-slate-900 mt-2">
            {loading ? '—' : state?.active_verticals || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Pipeline Score</h3>
          <p className="text-4xl font-black text-green-600 mt-2">
            {loading ? '—' : state?.pipeline_score || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Agents Deployed</h3>
          <p className="text-4xl font-black text-blue-600 mt-2">
            {loading ? '—' : state?.agents_deployed || 0}
          </p>
          {state?.agents_total && state.agents_total > 0 && (
            <p className="text-xs text-slate-400 mt-1">of {state.agents_total} built</p>
          )}
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Qualified Leads</h3>
          <p className="text-4xl font-black text-purple-600 mt-2">
            {loading ? '—' : state?.qualified_leads || 0}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Intelligence Feed */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-slate-700 flex items-center gap-2">
              🔭 MARKET INTELLIGENCE
            </h2>
            <button onClick={() => fetchState()} className="text-xs text-blue-600 hover:underline">Refresh</button>
          </div>

          <div className="space-y-4">
            {loading ? (
              <div className="text-slate-400 animate-pulse text-sm">Scanning ecosystem...</div>
            ) : (
              state?.opportunities?.map((opp, i) => (
                <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 flex justify-between items-center group hover:border-blue-400 transition-colors">
                  <div>
                    <h3 className="font-bold text-slate-800">{opp.vertical}</h3>
                    <div className="flex gap-2 text-xs mt-1">
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">Score: {opp.tam_score}</span>
                      <span className={`px-2 py-0.5 rounded font-bold ${opp.recommendation === 'BUILD' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                        {opp.recommendation}
                      </span>
                    </div>
                  </div>
                  {opp.recommendation === "BUILD" && (
                    <div className="flex gap-2">
                      <Link href="/demo" className="text-xs bg-black text-white px-3 py-1.5 rounded font-bold hover:bg-slate-800">
                        DEMO
                      </Link>
                    </div>
                  )}
                </div>
              ))
            )}

            {!loading && (!state?.opportunities || state.opportunities.length === 0) && (
              <div className="text-slate-400 text-sm">No opportunities found. Run the Scout.</div>
            )}
          </div>
        </section>

        {/* Factory Floor */}
        <section>
          <h2 className="text-lg font-bold text-slate-700 mb-4">🏭 PRODUCTION LINE</h2>
          <div className="bg-slate-900 rounded-xl p-6 text-white min-h-[300px] flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-mono font-bold text-green-400">FACTORY CONSOLE</h3>
              <span className={`w-2 h-2 rounded-full ${deploying ? 'bg-yellow-500 animate-ping' : 'bg-green-500'}`}></span>
            </div>

            <div className="space-y-2 font-mono text-sm text-slate-400 flex-1 overflow-y-auto max-h-[200px]">
              <p>&gt; System Online.</p>
              <p>&gt; Agents: {state?.agents_total || 0} built, {state?.agents_deployed || 0} deployed</p>
              <p>&gt; Verticals: {state?.active_verticals || 0} active</p>
              {logs.map((log, i) => (
                <p key={i} className="break-words">{log}</p>
              ))}
              {deploying && <p className="animate-pulse">&gt; Processing...</p>}
            </div>

            <div className="mt-8 pt-8 border-t border-slate-700">
              <button
                onClick={() => handleDeploy('NewAgent')}
                disabled={deploying}
                className={`w-full font-bold py-3 rounded flex items-center justify-center gap-2 transition-colors ${deploying ? 'bg-slate-700 cursor-not-allowed text-slate-400' : 'bg-blue-600 hover:bg-blue-500 text-white'}`}
              >
                {deploying ? '🚀 DEPLOYING...' : '🚀 DEPLOY TO STAGING'}
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

