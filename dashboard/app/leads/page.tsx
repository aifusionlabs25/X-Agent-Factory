'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

export default function LeadsPage() {
    const [leads, setLeads] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedRows, setExpandedRows] = useState<number[]>([]);

    const toggleRow = (id: number) => {
        setExpandedRows(prev =>
            prev.includes(id) ? prev.filter(rowId => rowId !== id) : [...prev, id]
        );
    };

    const fetchLeads = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/leads');
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            setLeads(data.leads || []);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLeads();
    }, []);

    const deleteLead = async (id: number) => {
        if (!confirm('Are you sure you want to delete this lead?')) return;
        try {
            await fetch(`/api/leads?id=${id}`, { method: 'DELETE' });
            setLeads(leads.filter(l => l.id !== id));
        } catch (err) {
            alert('Failed to delete');
        }
    };

    const updateStatus = async (id: number, newStatus: string) => {
        try {
            await fetch('/api/leads', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, status: newStatus })
            });
            setLeads(leads.map(l => l.id === id ? { ...l, status: newStatus } : l));
        } catch (err) {
            alert('Failed to update status');
        }
    };

    const exportCSV = () => {
        const headers = ['Business', 'URL', 'Vertical', 'Score', 'Status', 'Email'];
        const csvContent = [
            headers.join(','),
            ...leads.map(l => [
                `"${l.business_name}"`,
                l.url,
                l.vertical,
                l.nova_score,
                l.status,
                l.contact_data ? JSON.parse(l.contact_data).email || '' : ''
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `leads_export_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    return (
        <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
            {/* Header */}
            <div className="max-w-7xl mx-auto mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                        🏭 Factory Intelligence
                    </h1>
                    <p className="text-slate-400 mt-2">Database Viewer • {leads.length} Records</p>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={exportCSV}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium border border-slate-700 transition"
                    >
                        📥 Export CSV
                    </button>
                    <Link
                        href="/growth"
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition shadow-lg shadow-blue-900/50"
                    >
                        🎯 Hunter Mode
                    </Link>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto">
                {error && (
                    <div className="mb-6 p-4 bg-red-900/50 border border-red-800 rounded-xl text-red-200">
                        ⚠️ {error}
                    </div>
                )}

                <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden backdrop-blur-sm">
                    <table className="w-full text-left">
                        <thead className="bg-slate-900/50 border-b border-slate-700">
                            <tr>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Business</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Vertical</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Score</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/50">
                            {loading ? (
                                <tr><td colSpan={5} className="p-8 text-center text-slate-500">Loading factory Data...</td></tr>
                            ) : leads.map((lead) => {
                                const intel = lead.sales_intel ? JSON.parse(lead.sales_intel) : {};
                                const isExpanded = expandedRows.includes(lead.id);
                                return (
                                    <React.Fragment key={lead.id}>
                                        <tr className="hover:bg-slate-700/30 transition">
                                            <td className="p-4">
                                                <div className="font-medium text-slate-200">{lead.business_name}</div>
                                                <a href={lead.url} target="_blank" className="text-xs text-blue-400 hover:underline truncate block max-w-[200px]">
                                                    {lead.url}
                                                </a>
                                            </td>
                                            <td className="p-4 text-sm text-slate-300">
                                                <span className="px-2 py-1 bg-slate-800 rounded text-xs border border-slate-700">
                                                    {lead.vertical || 'Unknown'}
                                                </span>
                                            </td>
                                            <td className="p-4">
                                                <div className={`
                      inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm
                      ${lead.nova_score >= 8 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                                        lead.nova_score >= 6 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                                                            'bg-red-500/20 text-red-400 border border-red-500/30'}
                    `}>
                                                    {lead.nova_score}
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <select
                                                    value={lead.status}
                                                    onChange={(e) => updateStatus(lead.id, e.target.value)}
                                                    className="bg-transparent text-sm text-slate-300 focus:outline-none cursor-pointer hover:text-white"
                                                >
                                                    <option value="new">🆕 New</option>
                                                    <option value="contacted">📧 Contacted</option>
                                                    <option value="closed">✅ Closed</option>
                                                    <option value="rejected">❌ Rejected</option>
                                                </select>
                                            </td>
                                            <td className="p-4 text-right space-x-2">
                                                <button
                                                    onClick={() => toggleRow(lead.id)}
                                                    className={`px-3 py-1 text-xs font-bold rounded transition ${isExpanded ? 'bg-purple-600 text-white' : 'bg-slate-800 text-purple-400 hover:bg-slate-700'}`}
                                                >
                                                    {isExpanded ? '🔽 INTEL' : '💡 INTEL'}
                                                </button>
                                                <button
                                                    onClick={() => deleteLead(lead.id)}
                                                    className="text-slate-500 hover:text-red-400 transition"
                                                    title="Delete"
                                                >
                                                    🗑️
                                                </button>
                                            </td>
                                        </tr>
                                        {isExpanded && (
                                            <tr className="bg-slate-800/40 border-l-4 border-l-purple-500">
                                                <td colSpan={5} className="p-4">
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                                        <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700">
                                                            <div className="text-xs font-bold text-slate-500 uppercase mb-1">🎣 The Hook</div>
                                                            <div className="text-slate-200 italic">"{intel.hook || 'Not analyzed'}"</div>
                                                        </div>
                                                        <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700">
                                                            <div className="text-xs font-bold text-slate-500 uppercase mb-1">🩹 Pain Point</div>
                                                            <div className="text-red-400">{intel.pain_point || 'Unknown'}</div>
                                                        </div>
                                                        <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700">
                                                            <div className="text-xs font-bold text-slate-500 uppercase mb-1">📐 Sales Angle</div>
                                                            <div className="text-blue-400">{intel.sales_angle || 'Generic'}</div>
                                                        </div>
                                                        <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700">
                                                            <div className="text-xs font-bold text-slate-500 uppercase mb-1">👤 Decision Maker</div>
                                                            <div className="text-emerald-400 font-bold">{intel.decision_maker || 'Owner'}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                );
                            })}
                        </tbody>
                    </table>

                    {!loading && leads.length === 0 && (
                        <div className="p-12 text-center text-slate-500">
                            <div className="text-4xl mb-4">🕸️</div>
                            <p>No leads found in database.</p>
                            <Link href="/growth" className="text-blue-400 hover:underline mt-2 inline-block">
                                Start a Hunt
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
