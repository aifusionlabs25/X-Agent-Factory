
import React, { useState, useEffect } from 'react';

export default function ReportView() {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>(null);
    const [genLoading, setGenLoading] = useState(false);
    const [lastReport, setLastReport] = useState<string | null>(null);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/growth/reports/stats');
            const data = await res.json();
            if (data.success) {
                setStats(data.data);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const generateReport = async () => {
        setGenLoading(true);
        try {
            const res = await fetch('/api/growth/reports/generate', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                setLastReport(data.path);
            }
        } finally {
            setGenLoading(false);
        }
    };

    if (loading) return <div className="p-12 text-center text-slate-400 animate-pulse">Running Analysis Engine...</div>;
    if (!stats) return <div className="p-12 text-center text-red-400">Failed to load reports. Check logs.</div>;

    const { weekly, operator } = stats;

    return (
        <div className="space-y-6">
            {/* Operator Health */}
            <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-xs font-bold text-slate-400 uppercase mb-2">Tasks Done (7d)</h3>
                    <div className="text-3xl font-bold text-green-400">{operator.tasks_last_7d}</div>
                </div>
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-xs font-bold text-slate-400 uppercase mb-2">Avg Tasks / Day</h3>
                    <div className="text-3xl font-bold text-blue-400">{operator.avg_tasks_per_day}</div>
                </div>
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-xs font-bold text-slate-400 uppercase mb-2">Backlog Overdue</h3>
                    <div className="text-3xl font-bold text-red-400">{operator.backlog_overdue}</div>
                </div>
            </div>

            {/* Actions */}
            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                    <h3 className="font-bold text-slate-300">Report Generator</h3>
                    <p className="text-xs text-slate-500">Create snapshot files for external review</p>
                </div>
                <div className="flex gap-4 items-center">
                    {lastReport && <span className="text-xs text-green-400 bg-green-900/30 px-3 py-1 rounded border border-green-800">✅ Saved: {lastReport.split('\\').pop()}</span>}
                    <button
                        onClick={generateReport}
                        disabled={genLoading}
                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-lg disabled:opacity-50"
                    >
                        {genLoading ? 'Generating...' : '📄 Generate Weekly Report'}
                    </button>
                </div>
            </div>

            {/* Weekly Table */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <div className="p-4 bg-slate-900 border-b border-slate-700">
                    <h3 className="font-bold text-slate-200">Weekly Performance</h3>
                </div>
                <table className="w-full text-sm text-left text-slate-300">
                    <thead className="bg-slate-900 text-xs uppercase text-slate-500 font-semibold">
                        <tr>
                            <th className="p-3">Week</th>
                            <th className="p-3 text-right">Runs</th>
                            <th className="p-3 text-right">Exported</th>
                            <th className="p-3 text-right">Contacted</th>
                            <th className="p-3 text-right">Win Rate</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                        {weekly.map((w: any) => (
                            <tr key={w.week} className="hover:bg-slate-700/50">
                                <td className="p-3 font-mono text-blue-400">{w.week}</td>
                                <td className="p-3 text-right font-mono">{w.total_runs}</td>
                                <td className="p-3 text-right font-mono">{w.exported}</td>
                                <td className="p-3 text-right font-mono">
                                    {w.contacted} <span className="text-xs text-slate-500">({w.contact_rate.toFixed(1)}%)</span>
                                </td>
                                <td className="p-3 text-right font-mono text-green-400">{w.win_rate.toFixed(1)}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
