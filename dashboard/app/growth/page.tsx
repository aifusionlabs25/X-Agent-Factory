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
        if (!confirm(`Generate Agent for ${lead.title}? This will spider: ${lead.href}`)) return;

        setLogs(prev => prev + `\n🚀 Ingesting Client: ${lead.title}...`);

        try {
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: lead.href })
            });
            const data = await res.json();

            if (data.success) {
                setLogs(prev => prev + `\n✅ Agent Knowledge Base Created!\nUser can now deploy.`);
            } else {
                setLogs(prev => prev + `\n❌ Ingest Failed: ${data.error}`);
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n❌ Network Error: ${e.message}`);
        }
    };

    return (
        <div className="p-8">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">📈 GROWTH ENGINE</h1>
                    <p className="text-slate-500 font-mono">PROSPECT SCOUT | LEAD GENERATION</p>
                </div>
                <Link href="/" className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded text-slate-700 text-sm font-bold">
                    ← BACK TO DASHBOARD
                </Link>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Control Panel */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <h3 className="text-sm font-bold text-slate-700 mb-4 uppercase">Target Vertical</h3>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={vertical}
                                onChange={(e) => setVertical(e.target.value)}
                                placeholder="e.g. Plumbers in Austin"
                                className="flex-1 p-3 border border-slate-300 rounded-lg text-sm"
                            />
                            <button
                                onClick={handleHunt}
                                disabled={loading || !vertical}
                                className={`px-4 py-2 rounded-lg font-bold text-white transition-colors ${loading ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500'}`}
                            >
                                {loading ? 'HUNTING...' : 'HUNT'}
                            </button>
                        </div>
                        <p className="text-xs text-slate-400 mt-2">
                            Powered by WebWorker (Search) + Nova (Scoring).
                        </p>
                    </div>

                    {/* Console Output */}
                    <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 min-h-[200px] font-mono text-xs text-green-400 overflow-auto whitespace-pre-wrap">
                        {logs || "> Ready to hunt."}
                    </div>
                </div>

                {/* Results Table */}
                <div className="lg:col-span-2">
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-slate-200 bg-slate-50">
                            <h3 className="text-sm font-bold text-slate-700 uppercase">Qualified Leads (Score &gt; 7)</h3>
                        </div>

                        {leads.length === 0 ? (
                            <div className="p-12 text-center text-slate-400">
                                {loading ? 'Analyzing search results...' : 'No leads found. Try a different vertical.'}
                            </div>
                        ) : (
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th className="p-4">Business / Title</th>
                                        <th className="p-4">Score</th>
                                        <th className="p-4">Reason</th>
                                        <th className="p-4 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {leads.map((lead, i) => (
                                        <tr key={i} className="hover:bg-slate-50 transition-colors">
                                            <td className="p-4">
                                                <div className="font-bold text-slate-800 line-clamp-1">{lead.title}</div>
                                                <a href={lead.href} target="_blank" className="text-xs text-blue-500 hover:underline truncate block max-w-[200px]">{lead.href}</a>
                                            </td>
                                            <td className="p-4">
                                                <span className={`inline-block px-2 py-1 rounded font-bold text-xs ${lead.nova_score >= 9 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                                                    {lead.nova_score}/10
                                                </span>
                                            </td>
                                            <td className="p-4 text-slate-600 text-xs max-w-xs">{lead.nova_reason}</td>
                                            <td className="p-4 text-right">
                                                <button
                                                    onClick={() => handleGenerateAgent(lead)}
                                                    className="px-3 py-1 bg-black text-white text-xs font-bold rounded hover:bg-slate-800"
                                                >
                                                    GENERATE
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
