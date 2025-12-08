"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface AtlasEntry {
    category: string;
    vertical: string;
    sub_vertical: string;
    use_case: string;
    pain_point: string;
    buyer_persona: string;
    tam_us: number;
    deal_size_mrr: number;
    complexity: number;
    outreach_hook: string;
    roi_potential: number;
    suggested_template: string;
}

export default function GrowthPage() {
    const [atlas, setAtlas] = useState<AtlasEntry[]>([]);
    const [selectedEntry, setSelectedEntry] = useState<AtlasEntry | null>(null);
    const [customQuery, setCustomQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [leads, setLeads] = useState<any[]>([]);
    const [logs, setLogs] = useState<string>('');

    useEffect(() => {
        loadAtlas();
    }, []);

    const loadAtlas = async () => {
        try {
            const res = await fetch('/api/atlas');
            const data = await res.json();
            if (Array.isArray(data)) {
                setAtlas(data);
            }
        } catch (e) {
            console.error("Failed to load atlas", e);
        }
    };

    const handleEntrySelect = (entry: AtlasEntry) => {
        setSelectedEntry(entry);
        // Auto-generate search query from use_case + pain_point
        const query = `${entry.sub_vertical} ${entry.vertical}`;
        setCustomQuery(query);
        setLogs(`📋 Selected: ${entry.sub_vertical}\n💡 Pain: ${entry.pain_point}\n🎯 TAM: ${entry.tam_us.toLocaleString()} | MRR: $${entry.deal_size_mrr}\n🔍 Auto-Query: "${query}"`);
    };

    const [toast, setToast] = useState<string | null>(null);

    const showToast = (message: string) => {
        setToast(message);
        setTimeout(() => setToast(null), 5000);
    };

    const handleHunt = async () => {
        if (!customQuery && !selectedEntry) return;
        setLoading(true);
        const searchQuery = customQuery || `${selectedEntry?.sub_vertical} ${selectedEntry?.vertical}`;
        setLogs(prev => prev + `\n\n🚀 Initiating Prospect Scout for: ${searchQuery}...`);
        setLeads([]);

        try {
            const res = await fetch('/api/growth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vertical: searchQuery })
            });
            const data = await res.json();

            if (data.success) {
                // Enrich leads with atlas data
                const enrichedLeads = (data.leads || []).map((lead: any) => ({
                    ...lead,
                    suggested_template: selectedEntry?.suggested_template || 'Custom X Agent',
                    buyer_persona: selectedEntry?.buyer_persona || 'Owner',
                    deal_size: selectedEntry?.deal_size_mrr || 1000
                }));
                setLeads(enrichedLeads);
                setLogs(prev => prev + `\n✅ Scout Complete. Found ${enrichedLeads.length} qualified leads.`);

                // AUTO-SAVE: Save results to JSON + CSV
                if (enrichedLeads.length > 0) {
                    setLogs(prev => prev + `\n💾 Saving results...`);
                    try {
                        const saveRes = await fetch('/api/save-hunt', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                vertical: searchQuery,
                                leads: enrichedLeads
                            })
                        });
                        const saveData = await saveRes.json();

                        if (saveData.success) {
                            setLogs(prev => prev + `\n✅ Saved to: ${saveData.jsonPath}`);
                            showToast(`📁 Saved ${saveData.leadCount} leads to ${saveData.filename}`);

                            // PHASE 2: Trigger Orchestrator → Email Report
                            setLogs(prev => prev + `\n\n🏭 TRIGGERING ORCHESTRATOR...`);
                            setLogs(prev => prev + `\n   > Processing leads...`);
                            setLogs(prev => prev + `\n   > Generating report...`);
                            setLogs(prev => prev + `\n   > Sending email to aifusionlabs@gmail.com...`);

                            try {
                                const orchRes = await fetch('/api/orchestrate', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ filename: saveData.filename })
                                });
                                const orchData = await orchRes.json();

                                if (orchData.success) {
                                    if (orchData.emailSent) {
                                        setLogs(prev => prev + `\n✅ REPORT EMAILED TO ALPHA!`);
                                        showToast(`📧 Report emailed to aifusionlabs@gmail.com!`);
                                    } else {
                                        setLogs(prev => prev + `\n✅ Report generated (check inbox)`);
                                    }
                                } else {
                                    setLogs(prev => prev + `\n⚠️ Orchestrator: ${orchData.error}`);
                                }
                            } catch (orchErr: any) {
                                setLogs(prev => prev + `\n⚠️ Orchestrator error: ${orchErr.message}`);
                            }
                        } else {
                            setLogs(prev => prev + `\n⚠️ Save failed: ${saveData.error}`);
                        }
                    } catch (saveErr: any) {
                        setLogs(prev => prev + `\n⚠️ Save error: ${saveErr.message}`);
                    }
                }
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
        if (!confirm(`Generate Demo X Agent for ${lead.title}?\n\nTemplate: ${lead.suggested_template}\nThis will:\n1. Enrich lead (WebWorker + Nova + Fin + Sparkle)\n2. Spider their website\n3. Build a custom demo`)) return;

        let slug = lead.title.toLowerCase();
        slug = slug.replace(/[^a-z0-9\s]/g, '').trim().replace(/\s+/g, '_').slice(0, 50);

        // STAGE 1: ENRICHMENT
        setLogs(prev => prev + `\n\n🔬 ENRICHMENT PIPELINE STARTED`);
        setLogs(prev => prev + `\n   > 🕷️ WebWorker: Spidering...`);

        try {
            const enrichRes = await fetch('/api/enrich', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: lead.href,
                    title: lead.title,
                    pain: selectedEntry?.pain_point || '',
                    demo: ''
                })
            });
            const enrichData = await enrichRes.json();

            if (enrichData.success && enrichData.enriched) {
                const e = enrichData.enriched;
                setLogs(prev => prev + `\n   > 💠 Nova: Priority ${e.nova?.final_priority || 'N/A'}`);
                setLogs(prev => prev + `\n   > 💼 Fin: ${e.fin?.recommended_approach || 'N/A'}`);
                setLogs(prev => prev + `\n   > ✨ Sparkle: "${e.sparkle?.email_subject || 'Copy ready'}"`);

                // Update lead with enriched data
                setLeads(prevLeads => prevLeads.map(l =>
                    l.href === lead.href ? {
                        ...l,
                        enriched: e,
                        priority: e.nova?.final_priority,
                        approach: e.fin?.recommended_approach
                    } : l
                ));
            } else {
                setLogs(prev => prev + `\n   ⚠️ Enrichment partial: ${enrichData.message || 'Check logs'}`);
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n   ⚠️ Enrichment error: ${e.message}`);
        }

        // STAGE 2: INGEST
        setLogs(prev => prev + `\n\n🚀 INGESTING CLIENT: ${lead.title}...`);

        try {
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: lead.href })
            });
            const data = await res.json();

            if (data.success) {
                const demoLink = `/demo/${slug}`;
                setLogs(prev => prev + `\n✅ Demo Agent Ready!\n📎 Demo Link: ${window.location.origin}${demoLink}`);
                setLeads(prevLeads => prevLeads.map(l =>
                    l.href === lead.href ? { ...l, demoLink } : l
                ));
            } else {
                setLogs(prev => prev + `\n❌ Ingest Failed: ${data.error}`);
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n❌ Network Error: ${e.message}`);
        }
    };

    const getPainSignal = (reason: string): string => {
        if (!reason) return "Unknown";
        if (reason.toLowerCase().includes("call")) return "📞 Manual Phone";
        if (reason.toLowerCase().includes("schedule") || reason.toLowerCase().includes("book")) return "📅 No Booking";
        if (reason.toLowerCase().includes("website") || reason.toLowerCase().includes("old")) return "🌐 Outdated Site";
        if (reason.toLowerCase().includes("small") || reason.toLowerCase().includes("local")) return "🏠 Small Biz";
        return "⚙️ Manual Ops";
    };

    const downloadCSV = () => {
        if (leads.length === 0) return;

        const headers = [
            'Business Name',
            'URL',
            'Nova Score',
            'Pain Signal',
            'Suggested Template',
            'Deal Size MRR',
            'Priority',
            'Approach',
            'Demo Link',
            'Email Subject',
            'Outreach Hook'
        ];

        const rows = leads.map(lead => [
            lead.title || '',
            lead.href || '',
            lead.nova_score || '',
            getPainSignal(lead.nova_reason),
            lead.suggested_template || '',
            lead.deal_size || '',
            lead.enriched?.nova?.final_priority || '',
            lead.enriched?.fin?.recommended_approach || '',
            lead.demoLink ? `${window.location.origin}${lead.demoLink}` : '',
            lead.enriched?.sparkle?.email_subject || '',
            selectedEntry?.outreach_hook || ''
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
        ].join('\n');

        // Build filename from hunt terms
        const huntTerms = customQuery || selectedEntry?.sub_vertical || 'export';
        const sanitizedName = huntTerms
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, '')
            .trim()
            .replace(/\s+/g, '_')
            .slice(0, 50);
        const dateStr = new Date().toISOString().split('T')[0];
        const filename = `hunt_${sanitizedName}_${dateStr}.csv`;

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        setLogs(prev => prev + `\n📥 Exported ${leads.length} leads to: ${filename}`);
    };



    const formatCurrency = (num: number) => {
        if (num >= 1000000000) return `$${(num / 1000000000).toFixed(1)}B`;
        if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `$${(num / 1000).toFixed(0)}K`;
        return `$${num}`;
    };

    return (
        <div className="p-8 max-w-[1800px] mx-auto relative">
            {/* Toast Notification */}
            {toast && (
                <div className="fixed top-4 right-4 z-50 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg animate-pulse">
                    {toast}
                </div>
            )}

            <header className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">📈 GROWTH ENGINE</h1>
                    <p className="text-slate-500 font-mono text-sm">GUIDED HUNT | MARKET ATLAS POWERED | {atlas.length} VERTICALS LOADED</p>
                </div>

                <div className="flex gap-3">
                    {leads.length > 0 && (
                        <button
                            onClick={downloadCSV}
                            className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded text-white text-sm font-bold"
                        >
                            📥 Download CSV ({leads.length})
                        </button>
                    )}
                    <Link href="/" className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded text-slate-700 text-sm font-bold">
                        ← DASHBOARD
                    </Link>
                </div>
            </header>


            <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
                {/* Atlas Selector - Left Panel */}
                <div className="xl:col-span-1 space-y-4">
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white">
                            <h3 className="text-xs font-bold uppercase">🗺️ Market Atlas</h3>
                            <p className="text-xs text-white/70">Sorted by ROI Potential</p>
                        </div>
                        <div className="max-h-[500px] overflow-y-auto">
                            {atlas.map((entry, i) => (
                                <div
                                    key={i}
                                    onClick={() => handleEntrySelect(entry)}
                                    className={`p-3 border-b border-slate-100 cursor-pointer hover:bg-blue-50 transition-colors ${selectedEntry === entry ? 'bg-blue-100 border-l-4 border-l-blue-600' : ''}`}
                                >
                                    <div className="font-bold text-slate-800 text-sm">{entry.sub_vertical}</div>
                                    <div className="text-xs text-slate-500">{entry.vertical}</div>
                                    <div className="flex justify-between mt-1 text-xs">
                                        <span className="text-green-600 font-bold">${entry.deal_size_mrr}/mo</span>
                                        <span className="text-slate-400">{formatCurrency(entry.roi_potential)} TAM</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Main Content */}
                <div className="xl:col-span-3 space-y-4">
                    {/* Search Bar */}
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex gap-3 items-end">
                            <div className="flex-1">
                                <label className="text-xs font-bold text-slate-700 mb-1 block uppercase">Search Query</label>
                                <input
                                    type="text"
                                    value={customQuery}
                                    onChange={(e) => setCustomQuery(e.target.value)}
                                    placeholder="Select from Atlas or type custom query..."
                                    className="w-full p-3 border border-slate-300 rounded-lg text-sm text-slate-800"
                                />
                            </div>
                            <button
                                onClick={handleHunt}
                                disabled={loading || (!customQuery && !selectedEntry)}
                                className={`px-6 py-3 rounded-lg font-bold text-white transition-colors ${loading ? 'bg-slate-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500'}`}
                            >
                                {loading ? '🔍 HUNTING...' : '🎯 HUNT'}
                            </button>
                        </div>
                        {selectedEntry && (
                            <div className="mt-3 p-3 bg-slate-50 rounded-lg text-xs">
                                <div className="flex gap-4">
                                    <div><strong>💡 Pain:</strong> {selectedEntry.pain_point}</div>
                                    <div><strong>🎯 Buyer:</strong> {selectedEntry.buyer_persona}</div>
                                    <div><strong>📦 Template:</strong> {selectedEntry.suggested_template}</div>
                                </div>
                                <div className="mt-2 text-blue-600 italic">"{selectedEntry.outreach_hook}"</div>
                            </div>
                        )}
                    </div>

                    {/* Results Table */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-3 border-b border-slate-200 bg-gradient-to-r from-slate-900 to-slate-800 text-white flex justify-between items-center">
                            <h3 className="text-sm font-bold uppercase">🎯 Qualified Leads ({leads.length})</h3>
                            {leads.length > 0 && (
                                <span className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded">
                                    Est. MRR: ${(leads.length * (selectedEntry?.deal_size_mrr || 1000)).toLocaleString()}
                                </span>
                            )}
                        </div>

                        {leads.length === 0 ? (
                            <div className="p-12 text-center text-slate-400">
                                {loading ? (
                                    <div className="animate-pulse">
                                        <div className="text-4xl mb-4">🔍</div>
                                        <p>Hunting leads with Atlas intelligence...</p>
                                    </div>
                                ) : (
                                    <div>
                                        <div className="text-4xl mb-4">🗺️</div>
                                        <p>Select a vertical from the Atlas to begin.</p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 text-xs uppercase">
                                        <tr>
                                            <th className="p-3">Business</th>
                                            <th className="p-3">Score</th>
                                            <th className="p-3">Pain Signal</th>
                                            <th className="p-3">Template</th>
                                            <th className="p-3">MRR</th>
                                            <th className="p-3 text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {leads.map((lead, i) => (
                                            <tr key={i} className="hover:bg-blue-50/50 transition-colors">
                                                <td className="p-3">
                                                    <div className="font-bold text-slate-800 text-sm line-clamp-1 max-w-[200px]">{lead.title}</div>
                                                    <a href={lead.href} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline truncate block max-w-[200px]">{lead.href}</a>
                                                </td>
                                                <td className="p-3">
                                                    <span className={`inline-block px-2 py-1 rounded-full font-bold text-xs ${lead.nova_score >= 8 ? 'bg-green-100 text-green-700' : lead.nova_score >= 6 ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                                        {lead.nova_score}/10
                                                    </span>
                                                </td>
                                                <td className="p-3 text-xs">{getPainSignal(lead.nova_reason)}</td>
                                                <td className="p-3">
                                                    <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-mono">{lead.suggested_template}</span>
                                                </td>
                                                <td className="p-3 font-bold text-green-600">${lead.deal_size}</td>
                                                <td className="p-3 text-right">
                                                    {lead.demoLink ? (
                                                        <a href={lead.demoLink} target="_blank" className="px-3 py-1 bg-green-500 text-white text-xs font-bold rounded hover:bg-green-400">
                                                            VIEW DEMO
                                                        </a>
                                                    ) : (
                                                        <button
                                                            onClick={() => handleGenerateAgent(lead)}
                                                            className="px-3 py-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-bold rounded hover:from-blue-500 hover:to-purple-500"
                                                        >
                                                            🚀 BUILD
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                {/* Console */}
                <div className="xl:col-span-1">
                    <div className="bg-slate-900 p-4 rounded-xl border border-slate-700 min-h-[400px] font-mono text-xs text-green-400 overflow-auto whitespace-pre-wrap sticky top-4">
                        <div className="text-slate-500 mb-2 border-b border-slate-700 pb-2">// FACTORY CONSOLE</div>
                        {logs || "> Select a vertical from the Atlas.\n> Click HUNT to find prospects."}
                    </div>

                    {leads.length > 0 && (
                        <div className="mt-4 bg-white p-4 rounded-xl border border-slate-200 space-y-2">
                            <h4 className="text-xs font-bold text-slate-500 uppercase">Pipeline</h4>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Leads</span>
                                <span className="font-bold">{leads.length}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-600">High-Value</span>
                                <span className="font-bold text-green-600">{leads.filter(l => l.nova_score >= 8).length}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Est. MRR</span>
                                <span className="font-bold text-blue-600">${(leads.length * (selectedEntry?.deal_size_mrr || 1000)).toLocaleString()}</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
