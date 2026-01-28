"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import WorkflowProgress from "./components/WorkflowProgress";

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

interface Agent {
  slug: string;
  name: string;
  deployed: boolean;
  deployment_date?: string;
  expert_mode?: boolean;
}

interface WorkflowStatus {
  id: number;
  status: string;
  html_url: string;
}

interface GrowthProspect {
  id: string;
  name: string;
  source: 'X' | 'WEB' | 'GBP' | 'x' | 'web' | 'gbp' | 'manual';
  score: number;
  moment_score: number;
  b2b_confidence: number;
  bucket: 'BUILD_SPEC' | 'WATCH' | 'IGNORE';
  prospect_key: string;
  domain: string | null;
  domain_quality?: 'good' | 'low';
  expanded_urls?: string[];
  x_handle: string | null;
  x_profile_url: string | null;
  // G1.4: Gate fields
  context_gate?: 'PASS' | 'FAIL';
  vendor_pitch_gate?: 'PASS' | 'FAIL';
  // G1.5: Enrichment fields
  site_type?: 'BUSINESS' | 'VENDOR' | 'BLOG' | 'LINKHUB' | 'UNKNOWN';
  enrichment?: {
    page_title?: string;
    has_phone?: boolean;
    has_email?: boolean;
    has_contact_page?: boolean;
    has_address?: boolean;
    industry_hint?: string;
    location_hint?: string;
    services_detected?: string[];
  };
  // G1.6: Persona & ICP fields
  persona_type?: 'BUYER' | 'AGENCY' | 'VENDOR' | 'CREATOR' | 'UNKNOWN';
  icp_lane?: string;
  evidence_signals?: string[];
  penalties?: string[];
  b2b_boost_reasons?: string[];
  // G1.7: GBP-specific fields
  gbp_data?: {
    phone?: string;
    address?: string;
    category?: string;
    rating?: number;
    review_count?: number;
    maps_url?: string;
  };
  evidence: {
    type: string;
    text: string;
    url: string;
    created_at: string;
    query: string;
  }[];
  why_this_lead: string;
  recommended_action: 'BUILD_SPEC' | 'WATCH' | 'IGNORE';
  tags: string[];
  discovered_at: string;
  // Legacy fields
  prospect_name?: string;
  url?: string;
  signals?: string[];
}

interface GrowthData {
  generated_at: string | null;
  total_found: number;
  weekly_target: number;
  top_build_spec: GrowthProspect[];
  watchlist: GrowthProspect[];
  ignored_count: number;
  // Legacy
  prospects?: GrowthProspect[];
  top_count?: number;
}

export default function Home() {
  const [state, setState] = useState<FactoryState | null>(null);
  const [loading, setLoading] = useState(true);
  const [deploying, setDeploying] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  // Agent list state
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [deployWorkflow, setDeployWorkflow] = useState<WorkflowStatus | null>(null);

  // New Prospect state
  const [prospectUrl, setProspectUrl] = useState('');
  const [prospectProcessing, setProspectProcessing] = useState(false);
  const [prospectStatus, setProspectStatus] = useState<string | null>(null);
  const [workflowInfo, setWorkflowInfo] = useState<WorkflowStatus | null>(null);
  const [deployToStaging, setDeployToStaging] = useState(false);
  const [expertMode, setExpertMode] = useState(false);
  const [buildKb, setBuildKb] = useState(true);

  // Growth Radar state
  const [growthData, setGrowthData] = useState<GrowthData | null>(null);
  const [growthLoading, setGrowthLoading] = useState(true);
  const [growthTab, setGrowthTab] = useState<'build_spec' | 'watchlist'>('build_spec');

  // Delete Agent State
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchState();
    fetchAgents();
    fetchGrowthOpportunities();
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

  const fetchAgents = async () => {
    try {
      const res = await fetch('/api/agents');
      const data = await res.json();
      if (data.success && data.agents) {
        setAgents(data.agents);
        // Auto-select the most recent undeployed agent if available
        const pending = data.agents.filter((a: Agent) => !a.deployed);
        if (pending.length > 0) {
          setSelectedAgent(pending[0].slug);
        } else if (data.agents.length > 0) {
          setSelectedAgent(data.agents[0].slug);
        }
      }
    } catch (e) {
      console.error('Failed to fetch agents', e);
    }
  };

  const fetchGrowthOpportunities = async () => {
    try {
      setGrowthLoading(true);
      const res = await fetch('/api/growth/opportunities');
      const data = await res.json();
      setGrowthData(data);
    } catch (e) {
      console.error('Failed to fetch growth opportunities', e);
    } finally {
      setGrowthLoading(false);
    }
  };

  const handleNewProspect = async () => {
    if (!prospectUrl.trim()) {
      setProspectStatus('Please enter a URL');
      return;
    }

    setProspectProcessing(true);
    setProspectStatus('Triggering workflow...');
    setWorkflowInfo(null);
    addLog(`🎯 New Prospect: ${prospectUrl}`);

    try {
      const res = await fetch('/api/new-prospect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: prospectUrl,
          deployEnv: deployToStaging ? 'staging' : 'off',
          expertMode: expertMode,
          buildKb: buildKb,
        }),
      });
      const data = await res.json();

      if (data.success) {
        setProspectStatus('Workflow started!');
        addLog(`✅ Workflow triggered`);
        if (data.workflow) {
          setWorkflowInfo(data.workflow);
          addLog(`📋 Run ID: ${data.workflow.id}`);
        }
        // Clear input after success
        setProspectUrl('');
        // Refresh state after a delay
        setTimeout(fetchState, 5000);
      } else {
        setProspectStatus(`Error: ${data.error}`);
        addLog(`❌ Error: ${data.error}`);
      }
    } catch (e: any) {
      setProspectStatus(`Error: ${e.message}`);
      addLog(`❌ Error: ${e.message}`);
    } finally {
      setProspectProcessing(false);
    }
  };

  const handleDeploy = async () => {
    if (!selectedAgent) {
      addLog('❌ Please select an agent first');
      return;
    }

    setDeploying(true);
    setDeployWorkflow(null);
    addLog(`🚀 Dispatching deploy workflow for: ${selectedAgent}...`);

    try {
      const res = await fetch('/api/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slug: selectedAgent, env: 'staging' })
      });
      const data = await res.json();

      if (data.success) {
        addLog(`✅ Deploy workflow queued!`);
        if (data.workflow) {
          setDeployWorkflow(data.workflow);
          addLog(`📋 Run ID: ${data.workflow.id}`);
        }
        // Refresh agents list after a delay
        setTimeout(() => {
          fetchAgents();
          fetchState();
        }, 5000);
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

  const handleOpenFolder = async (slug?: string) => {
    try {
      const path = slug ? `agents/${slug}` : 'agents';
      const res = await fetch('/api/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });
      const data = await res.json();
      if (data.success) {
        addLog(`📂 Opened folder: ${path}`);
      } else {
        addLog(`❌ Failed to open folder: ${data.error}`);
      }
    } catch (e: any) {
      addLog(`❌ Error opening folder: ${e.message}`);
    }
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

  const handleDeleteAgent = async () => {
    if (!agentToDelete) return;

    setIsDeleting(true);
    addLog(`🗑️ Deleting agent: ${agentToDelete}...`);

    try {
      const res = await fetch(`/api/agents/${agentToDelete}`, {
        method: 'DELETE',
      });
      const data = await res.json();

      if (res.ok) {
        addLog(`✅ Agent ${agentToDelete} deleted successfully.`);
        // Reset selection if we deleted the selected agent
        if (selectedAgent === agentToDelete) {
          setSelectedAgent('');
        }
        await fetchAgents();
        await fetchState();
      } else {
        addLog(`❌ Failed to delete agent: ${data.error}`);
      }
    } catch (e: any) {
      addLog(`❌ Delete error: ${e.message}`);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
      setAgentToDelete(null);
    }
  };

  return (
    <div className="p-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-red-600 truncate">
              🏭 X AGENT FACTORY
            </h1>
            <span className="bg-slate-800 text-slate-400 text-xs px-2 py-1 rounded border border-slate-700">v2.1</span>
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            SYSTEM STATUS: <span className="text-green-500">ONLINE</span> | LAST UPDATED: {formatLastUpdated(state?.last_run_timestamp || null)}
          </p>
        </div>
        <div className="flex gap-4">
          <Link href="/api/state" target="_blank">
            <button className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded text-sm font-bold transition-colors">
              ⚙️ System Status
            </button>
          </Link>
          <Link href="/build">
            <button className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded text-sm font-bold transition-colors shadow-lg shadow-purple-900/20">
              🏗️ BUILD STUDIO
            </button>
          </Link>
          <a href="https://github.com/aifusionlabs25/X-Agent-Factory/actions" target="_blank" rel="noopener noreferrer">
            <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm font-bold transition-colors shadow-lg shadow-blue-900/20">
              🚀 LAUNCH HUNTER
            </button>
          </a>
        </div>
      </header>

      {/* NEW PROSPECT CARD */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 mb-8 text-white relative">
        <h2 className="text-lg font-bold mb-4">✨ NEW PROSPECT</h2>
        {/* Progress Indicator Overlay */}
        {prospectProcessing && (
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-xl">
            <div className="text-center">
              <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
              <p className="text-white font-bold animate-pulse">Initializing Agent Pipeline...</p>
              <p className="text-xs text-slate-400 mt-1">Check Factory Console for logs</p>
            </div>
          </div>
        )}

        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="text-xs font-bold uppercase opacity-80 block mb-2">Prospect Website URL</label>
            <input
              type="url"
              value={prospectUrl}
              onChange={(e) => setProspectUrl(e.target.value)}
              placeholder="https://example.com"
              disabled={prospectProcessing}
              className="w-full p-3 rounded-lg text-slate-800 text-sm font-mono disabled:opacity-50"
            />
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm cursor-pointer border-r border-white/20 pr-4">
              <input
                type="checkbox"
                checked={expertMode}
                onChange={(e) => setExpertMode(e.target.checked)}
                disabled={prospectProcessing}
                className="w-4 h-4 accent-yellow-400"
              />
              <span className="font-bold text-yellow-300">⚡ Expert Mode</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer border-r border-white/20 pr-4">
              <input
                type="checkbox"
                checked={buildKb}
                onChange={(e) => setBuildKb(e.target.checked)}
                disabled={prospectProcessing}
                className="w-4 h-4 accent-green-400"
              />
              <span className="font-bold text-green-300">📚 Build KB</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={deployToStaging}
                onChange={(e) => setDeployToStaging(e.target.checked)}
                disabled={prospectProcessing}
                className="w-4 h-4"
              />
              Deploy to Staging
            </label>
            <button
              onClick={handleNewProspect}
              disabled={prospectProcessing || !prospectUrl.trim()}
              className={`px-6 py-3 rounded-lg font-bold transition-all ${prospectProcessing || !prospectUrl.trim()
                ? 'bg-white/30 cursor-not-allowed'
                : 'bg-white text-purple-600 hover:bg-purple-100'
                }`}
            >
              {prospectProcessing ? '⏳ Processing...' : '🚀 Create Agent'}
            </button>
          </div>
        </div>
        {prospectStatus && (
          <div className="mt-3 text-sm font-mono opacity-90">
            {prospectStatus}
          </div>
        )}
        {/* Workflow Progress Bar */}
        {workflowInfo && (
          <WorkflowProgress
            runId={workflowInfo.id.toString()}
            onComplete={(success) => {
              if (success) {
                addLog('✅ Pipeline completed successfully!');
                fetchAgents();
                fetchState();
              } else {
                addLog('❌ Pipeline failed. Check GitHub for details.');
              }
            }}
          />
        )}
      </div>

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

      {/* GROWTH RADAR CARD */}
      <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl p-6 mb-8 text-white">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold flex items-center gap-2">
            📈 GROWTH RADAR
            <span className="bg-white/20 text-xs px-2 py-1 rounded">G1.3</span>
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => fetchGrowthOpportunities()}
              className="text-xs bg-white/20 hover:bg-white/30 px-3 py-1 rounded transition-colors"
            >
              Refresh
            </button>
            <a
              href="https://github.com/aifusionlabs25/X-Agent-Factory/actions/workflows/growth_radar.yml"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs bg-white/20 hover:bg-white/30 px-3 py-1 rounded transition-colors"
            >
              🔭 Run Hunt
            </a>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setGrowthTab('build_spec')}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${growthTab === 'build_spec'
              ? 'bg-yellow-400 text-black'
              : 'bg-white/20 hover:bg-white/30'
              }`}
          >
            🎯 Build Spec ({growthData?.top_build_spec?.length || 0})
          </button>
          <button
            onClick={() => setGrowthTab('watchlist')}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${growthTab === 'watchlist'
              ? 'bg-blue-400 text-black'
              : 'bg-white/20 hover:bg-white/30'
              }`}
          >
            👁️ Watchlist ({growthData?.watchlist?.length || 0})
          </button>
        </div>

        {growthLoading ? (
          <div className="text-center py-8 opacity-70">Loading opportunities...</div>
        ) : growthData ? (
          <div className="space-y-3">
            {(growthTab === 'build_spec' ? growthData.top_build_spec : growthData.watchlist)?.map((prospect, idx) => (
              <div key={prospect.id || idx} className={`rounded-lg p-4 ${growthTab === 'build_spec' ? 'bg-yellow-400/20' : 'bg-blue-400/20'
                }`}>
                {/* Header: Name + Source + Domain */}
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold">{prospect.name || prospect.prospect_name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${prospect.source?.toUpperCase() === 'X' ? 'bg-blue-400/30' : 'bg-green-400/30'
                        }`}>
                        {prospect.source?.toUpperCase()}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded ${prospect.bucket === 'BUILD_SPEC' ? 'bg-yellow-400/50 text-black' : 'bg-blue-400/50'
                        }`}>
                        {prospect.bucket?.replace('_', ' ')}
                      </span>
                      {prospect.domain && (
                        <a
                          href={`https://${prospect.domain}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-yellow-300 hover:underline"
                        >
                          🌐 {prospect.domain}
                        </a>
                      )}
                      {prospect.x_handle && (
                        <a
                          href={prospect.x_profile_url || `https://x.com/${prospect.x_handle}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-300 hover:underline"
                        >
                          @{prospect.x_handle}
                        </a>
                      )}
                    </div>
                  </div>
                  {/* Scores */}
                  <div className="text-right ml-4">
                    <div className={`text-2xl font-black ${prospect.b2b_confidence >= 6 ? 'text-yellow-300' : 'text-white/70'
                      }`}>
                      B2B: {prospect.b2b_confidence || 0}
                    </div>
                    <div className="text-xs opacity-70">
                      Moment: {prospect.moment_score || 0}
                    </div>
                  </div>
                </div>
                {/* Evidence Snippet */}
                {prospect.evidence && prospect.evidence[0] && (
                  <div className="text-xs opacity-80 bg-black/20 rounded p-2 mt-2">
                    <span className="opacity-50">Evidence:</span> "{prospect.evidence[0].text?.slice(0, 150)}..."
                    {prospect.evidence[0].url && (
                      <a
                        href={prospect.evidence[0].url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-blue-300 hover:underline"
                      >
                        View
                      </a>
                    )}
                  </div>
                )}
                {/* Why This Lead */}
                {prospect.why_this_lead && (
                  <div className="text-xs opacity-60 mt-2 italic">
                    {prospect.why_this_lead}
                  </div>
                )}
              </div>
            ))}
            {((growthTab === 'build_spec' ? growthData.top_build_spec : growthData.watchlist)?.length || 0) === 0 && (
              <div className="text-center py-4 opacity-70">
                No {growthTab === 'build_spec' ? 'Build Spec' : 'Watchlist'} prospects found.
              </div>
            )}
            <div className="text-xs text-center opacity-70 pt-2">
              Total found: {growthData.total_found} | BUILD_SPEC: {growthData.top_build_spec?.length || 0} | WATCH: {growthData.watchlist?.length || 0}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="opacity-80 mb-2">No prospects yet.</p>
            <p className="text-xs opacity-60">Run the Growth Radar workflow to discover opportunities.</p>
          </div>
        )}
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
              <span className={`w-2 h-2 rounded-full ${deploying || prospectProcessing ? 'bg-yellow-500 animate-ping' : 'bg-green-500'}`}></span>
            </div>

            <div className="space-y-2 font-mono text-sm text-slate-400 flex-1 overflow-y-auto max-h-[200px]">
              <p>&gt; System Online.</p>
              <p>&gt; Agents: {state?.agents_total || 0} built, {state?.agents_deployed || 0} deployed</p>
              <p>&gt; Verticals: {state?.active_verticals || 0} active</p>
              {logs.map((log, i) => (
                <p key={i} className="break-words">{log}</p>
              ))}
              {(deploying || prospectProcessing) && <p className="animate-pulse">&gt; Processing...</p>}
            </div>

            <div className="mt-8 pt-8 border-t border-slate-700">
              {/* Agent Selector */}
              <div className="mb-4">
                <label className="text-xs font-bold text-slate-400 uppercase block mb-2">Select Agent</label>
                <div className="flex gap-2">
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    disabled={deploying || agents.length === 0}
                    className="flex-1 p-2 rounded bg-slate-800 text-white border border-slate-600 text-sm"
                  >
                    {agents.length === 0 ? (
                      <option value="">No agents available</option>
                    ) : (
                      agents.map((agent) => (
                        <option key={agent.slug} value={agent.slug}>
                          {agent.expert_mode ? '⚡ ' : ''}{agent.name || agent.slug} {agent.deployed ? '✅' : '⏳'}
                        </option>
                      ))
                    )}
                  </select>
                  <button
                    onClick={() => {
                      if (selectedAgent) {
                        setAgentToDelete(selectedAgent);
                        setShowDeleteConfirm(true);
                      }
                    }}
                    disabled={!selectedAgent || deploying}
                    className="bg-red-900/50 hover:bg-red-900 text-red-200 p-2 rounded border border-red-800 transition-colors disabled:opacity-50"
                    title="Delete Agent"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              <button
                onClick={handleDeploy}
                disabled={deploying || !selectedAgent}
                className={`w-full font-bold py-3 rounded flex items-center justify-center gap-2 transition-colors ${deploying || !selectedAgent ? 'bg-slate-700 cursor-not-allowed text-slate-400' : 'bg-blue-600 hover:bg-blue-500 text-white'}`}
              >
                {deploying ? '🚀 DEPLOYING...' : '🚀 DEPLOY TO STAGING'}
              </button>

              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => handleOpenFolder(selectedAgent)}
                  disabled={!selectedAgent}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs py-2 rounded font-mono transition-colors disabled:opacity-50"
                >
                  📂 OPEN AGENT FOLDER
                </button>
                <button
                  onClick={() => handleOpenFolder()}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs py-2 rounded font-mono transition-colors border border-slate-700"
                >
                  📂 ALL AGENTS
                </button>
              </div>

              {deployWorkflow && (
                <a
                  href={deployWorkflow.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block mt-2 text-center text-xs text-blue-400 hover:underline"
                >
                  View deploy workflow →
                </a>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-red-600 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              ⚠️ Confirm Deletion
            </h3>
            <p className="text-slate-300 mb-6">
              Are you sure you want to delete <span className="font-mono text-white bg-slate-800 px-1 rounded">{agentToDelete}</span>?
              <br /><br />
              This will permanently remove the agent files. This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="px-4 py-2 rounded text-slate-300 hover:bg-slate-800 transition-colors font-bold"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAgent}
                disabled={isDeleting}
                className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded font-bold transition-colors flex items-center gap-2"
              >
                {isDeleting ? 'Deleting...' : '🗑️ Yes, Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


