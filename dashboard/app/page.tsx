import Link from "next/link";

// Mock Data (In production, this would read from intelligence/daily_opportunities.json)
const OPPORTUNITIES = [
  { vertical: "Veterinary", score: 9.9, status: "BUILD", agent: "Ava" },
  { vertical: "Home Services", score: 9.3, status: "BUILD", agent: "Pending" },
  { vertical: "Dental", score: 7.6, status: "WAIT", agent: "-" },
];

export default function Home() {
  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800 tracking-tight">🏗️ X AGENT FACTORY</h1>
        <p className="text-slate-500 font-mono">SYSTEM STATUS: ONLINE | PHASE: 3 (UI)</p>
      </header>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Active Verticals</h3>
          <p className="text-4xl font-black text-slate-900 mt-2">1</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Pipeline Score</h3>
          <p className="text-4xl font-black text-green-600 mt-2">9.9</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Agents Deployed</h3>
          <p className="text-4xl font-black text-blue-600 mt-2">0</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Intelligence Feed */}
        <section>
          <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
            🔭 MARKET INTELLIGENCE
          </h2>
          <div className="space-y-4">
            {OPPORTUNITIES.map((opp, i) => (
              <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 flex justify-between items-center group hover:border-blue-400 transition-colors">
                <div>
                  <h3 className="font-bold text-slate-800">{opp.vertical}</h3>
                  <div className="flex gap-2 text-xs mt-1">
                    <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">Score: {opp.score}</span>
                    <span className={`px-2 py-0.5 rounded font-bold ${opp.status === 'BUILD' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {opp.status}
                    </span>
                  </div>
                </div>
                {opp.agent !== "-" && (
                  <Link href="/demo" className="text-xs bg-black text-white px-3 py-1.5 rounded font-bold hover:bg-slate-800">
                    LAUNCH DEMO
                  </Link>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Factory Floor */}
        <section>
          <h2 className="text-lg font-bold text-slate-700 mb-4">🏭 PRODUCTION LINE</h2>
          <div className="bg-slate-900 rounded-xl p-6 text-white min-h-[300px]">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-mono font-bold text-green-400">ACTIVE BUILD: AVA</h3>
              <span className="animate-pulse w-2 h-2 bg-green-500 rounded-full"></span>
            </div>

            <div className="space-y-2 font-mono text-sm text-slate-400">
              <p>&gt; Initializing Identity... [DONE]</p>
              <p>&gt; Ingesting Knowledge Base (v2)... [DONE]</p>
              <p>&gt; Synthesizing Voice Model (Tavus)... [PENDING]</p>
              <p>&gt; Calibrating UI Interface... [IN PROGRESS]</p>
            </div>

            <div className="mt-8 pt-8 border-t border-slate-700">
              <button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded flex items-center justify-center gap-2">
                <span>🚀 DEPLOY TO STAGING</span>
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
