"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function GrowthPage() {
    const [vertical, setVertical] = useState('');
    const [loading, setLoading] = useState(false);
    const [leads, setLeads] = useState<any[]>([]);
    const [logs, setLogs] = useState<string>('');

    const handleHunt = async () => {
        if (!vertical) return;
        setLoading(true);
        setLogs(`🚀 Initiating Prospect Scout for: ${vertical}...`);
        setLeads([]);

        try {
            const res = await fetch('/api/growth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vertical })
            });
            const data = await res.json();

            if (data.success) {
                setLeads(data.leads || []);
                setLogs(prev => prev + `\n✅ Scout Complete. Found ${data.leads?.length} qualified leads.`);
            } else {
                setLogs(prev => prev + `\n❌ Error: ${data.error || 'Unknown error'}`);
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n❌ Network Error: ${e.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateAgent = async (lead: any) => {
        if (!confirm(`Generate Demo X Agent for ${lead.title}?\n\nThis will:\n1. Spider their website\n2. Build a custom Knowledge Base\n3. Generate a shareable demo link`)) return;

        setLogs(prev => prev + `\n🚀 Ingesting Client: ${lead.title}...`);

        try {
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: lead.href })
            });
            const data = await res.json();

            if (data.success) {
                setLogs(prev => prev + `\n✅ Demo Agent Ready! Knowledge Base Created.`);
            } else {
                setLogs(prev => prev + `\n❌ Ingest Failed: ${data.error}`);
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n❌ Network Error: ${e.message}`);
        }
    };

    // Estimate opportunity value based on score
    const getOpportunitySize = (score: number): string => {
        if (score >= 9) return "$2,500+/mo";
        if (score >= 7) return "$1,000-$2,500/mo";
        return "$500-$1,000/mo";
    };

    // Derive pain signal from reason
    const getPainSignal = (reason: string): string => {
        if (!reason) return "Unknown";
        if (reason.toLowerCase().includes("call")) return "📞 Manual Phone Intake";
        if (reason.toLowerCase().includes("schedule") || reason.toLowerCase().includes("book")) return "📅 No Online Booking";
        if (reason.toLowerCase().includes("website") || reason.toLowerCase().includes("old")) return "🌐 Outdated Website";
        if (reason.toLowerCase().includes("small") || reason.toLowerCase().includes("local")) return "🏠 Small Local Biz";
        return "⚙️ Manual Operations";
    };

    // Suggest X Agent type based on vertical
    const getAgentType = (): string => {
        const v = vertical.toLowerCase();
        if (v.includes("hvac") || v.includes("plumb") || v.includes("home")) return "Noah (Dispatch)";
        if (v.includes("vet") || v.includes("pet") || v.includes("animal")) return "Ava (Triage)";
        if (v.includes("legal") || v.includes("law") || v.includes("attorney")) return "Liam (Intake)";
        if (v.includes("dental") || v.includes("dentist")) return "Sage (Scheduler)";
        return "Custom X Agent";
    };

    return (
        <div className="p-8 max-w-[1600px] mx-auto">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">📈 GROWTH ENGINE</h1>
                    <p className="text-slate-500 font-mono">PROSPECT SCOUT | LEAD GENERATION | DEMO AGENT BUILDER</p>
                </div>
                <Link href="/" className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded text-slate-700 text-sm font-bold">
                    ← BACK TO DASHBOARD
                </Link>
            </header>

            {/* Control Panel - Horizontal */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-8">
                <div className="flex gap-4 items-end">
                    <div className="flex-1">
                        <label className="text-sm font-bold text-slate-700 mb-2 block uppercase">Target Vertical</label>
                        <input
                            type="text"
                            value={vertical}
                            onChange={(e) => setVertical(e.target.value)}
                            placeholder="e.g. HVAC in Phoenix, Plumbers in Austin, Veterinary Clinics in Denver"
                            className="w-full p-3 border border-slate-300 rounded-lg text-sm text-slate-800"
                        />
                    </div>
                    <button
                        onClick={handleHunt}
                        disabled={loading || !vertical}
                        className={`px-8 py-3 rounded-lg font-bold text-white transition-colors ${loading ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500'}`}
                    >
                        {loading ? '🔍 HUNTING...' : '🎯 HUNT LEADS'}
                    </button>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                    Powered by WebWorker (DuckDuckGo) + Nova (Lead Scoring) + Troy (Agent Builder). Suggested Agent: <strong className="text-blue-600">{getAgentType()}</strong>
                </p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                {/* Results Table - Takes most space */}
                <div className="xl:col-span-3">
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-slate-900 to-slate-800 text-white">
                            <div className="flex justify-between items-center">
                                <h3 className="text-sm font-bold uppercase">🎯 Qualified Leads ({leads.length})</h3>
                                <span className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded">Score ≥ 4 | Ready for Demo Agent</span>
                            </div>
                        </div>

                        {leads.length === 0 ? (
                            <div className="p-16 text-center text-slate-400">
                                {loading ? (
                                    <div className="animate-pulse">
                                        <div className="text-4xl mb-4">🔍</div>
                                        <p>Searching the web for {vertical}...</p>
                                        <p className="text-xs mt-2">Nova is scoring each lead for automation potential.</p>
                                    </div>
                                ) : (
                                    <div>
                                        <div className="text-4xl mb-4">📊</div>
                                        <p>No leads found yet. Enter a vertical above and click HUNT.</p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 text-xs uppercase">
                                        <tr>
                                            <th className="p-4">Business</th>
                                            <th className="p-4">Nova Score</th>
                                            <th className="p-4">Pain Signal</th>
                                            <th className="p-4">Opportunity</th>
                                            <th className="p-4">X Agent</th>
                                            <th className="p-4 text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {leads.map((lead, i) => (
                                            <tr key={i} className="hover:bg-blue-50/50 transition-colors">
                                                <td className="p-4">
                                                    <div className="font-bold text-slate-800 line-clamp-1 max-w-[250px]">{lead.title}</div>
                                                    <a href={lead.href} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline truncate block max-w-[250px]">{lead.href}</a>
                                                </td>
                                                <td className="p-4">
                                                    <span className={`inline-block px-3 py-1 rounded-full font-bold text-xs ${lead.nova_score >= 8 ? 'bg-green-100 text-green-700' : lead.nova_score >= 6 ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                                        {lead.nova_score}/10
                                                    </span>
                                                </td>
                                                <td className="p-4 text-slate-600 text-sm">
                                                    {getPainSignal(lead.nova_reason)}
                                                </td>
                                                <td className="p-4">
                                                    <span className="font-bold text-green-600">{getOpportunitySize(lead.nova_score)}</span>
                                                </td>
                                                <td className="p-4">
                                                    <span className="bg-slate-100 px-2 py-1 rounded text-xs font-mono">{getAgentType()}</span>
                                                </td>
                                                <td className="p-4 text-right">
                                                    <button
                                                        onClick={() => handleGenerateAgent(lead)}
                                                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-bold rounded-lg hover:from-blue-500 hover:to-purple-500 transition-all shadow-md hover:shadow-lg"
                                                    >
                                                        🚀 BUILD DEMO
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                {/* Console / Activity Log */}
                <div className="xl:col-span-1">
                    <div className="bg-slate-900 p-4 rounded-xl border border-slate-700 min-h-[400px] font-mono text-xs text-green-400 overflow-auto whitespace-pre-wrap sticky top-4">
                        <div className="text-slate-500 mb-2 border-b border-slate-700 pb-2">// FACTORY CONSOLE</div>
                        {logs || "> Ready to hunt.\n> Enter a vertical and click HUNT."}
                    </div>

                    {/* Quick Stats */}
                    {leads.length > 0 && (
                        <div className="mt-4 bg-white p-4 rounded-xl border border-slate-200 space-y-3">
                            <h4 className="text-xs font-bold text-slate-500 uppercase">Pipeline Summary</h4>
                            <div className="flex justify-between">
                                <span className="text-slate-600">Total Leads</span>
                                <span className="font-bold">{leads.length}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-600">High-Value (8+)</span>
                                <span className="font-bold text-green-600">{leads.filter(l => l.nova_score >= 8).length}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-600">Est. Monthly Rev</span>
                                <span className="font-bold text-blue-600">${leads.length * 1000}-${leads.length * 2000}</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
