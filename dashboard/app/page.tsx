"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function Home() {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [deploying, setDeploying] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const fetchOpportunities = async () => {
    try {
      const res = await fetch('/api/scout');
      const data = await res.json();
      setOpportunities(data);
      setLoading(false);
    } catch (e) {
      console.error("Failed to fetch opportunities", e);
      setLoading(false);
    }
  };

  const calculatePipelineScore = () => {
    if (opportunities.length === 0) return 0;
    // Simple average of scores
    const total = opportunities.reduce((acc, curr) => acc + (curr.tam_score || 0), 0);
    return (total / opportunities.length).toFixed(1);
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

  return (
    <div className="p-8">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">🏗️ X AGENT FACTORY</h1>
          <p className="text-slate-500 font-mono">SYSTEM STATUS: ONLINE | PHASE: 4 (INTEGRATION)</p>
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
          <p className="text-4xl font-black text-slate-900 mt-2">{opportunities.length}</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Pipeline Score</h3>
          <p className="text-4xl font-black text-green-600 mt-2">{calculatePipelineScore()}</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Agents Deployed</h3>
          <p className="text-4xl font-black text-blue-600 mt-2">0</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Intelligence Feed */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-slate-700 flex items-center gap-2">
              🔭 MARKET INTELLIGENCE
            </h2>
            <button onClick={() => fetchOpportunities()} className="text-xs text-blue-600 hover:underline">Refresh</button>
          </div>

          <div className="space-y-4">
            {loading ? (
              <div className="text-slate-400 animate-pulse text-sm">Scanning ecosystem...</div>
            ) : (
              opportunities.map((opp, i) => (
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

            {opportunities.length === 0 && !loading && (
              <div className="text-slate-400 text-sm">No opportunities found. Run the Scout.</div>
            )}
          </div>
        </section>

        {/* Factory Floor */}
        <section>
          <h2 className="text-lg font-bold text-slate-700 mb-4">🏭 PRODUCTION LINE</h2>
          <div className="bg-slate-900 rounded-xl p-6 text-white min-h-[300px] flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-mono font-bold text-green-400">ACTIVE BUILD: AVA</h3>
              <span className={`w-2 h-2 rounded-full ${deploying ? 'bg-yellow-500 animate-ping' : 'bg-green-500'}`}></span>
            </div>

            <div className="space-y-2 font-mono text-sm text-slate-400 flex-1 overflow-y-auto max-h-[200px]">
              <p>&gt; System Online.</p>
              {logs.map((log, i) => (
                <p key={i} className="break-words">{log}</p>
              ))}
              {deploying && <p className="animate-pulse">&gt; Processing...</p>}
            </div>

            <div className="mt-8 pt-8 border-t border-slate-700">
              <button
                onClick={() => handleDeploy('Ava')}
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
