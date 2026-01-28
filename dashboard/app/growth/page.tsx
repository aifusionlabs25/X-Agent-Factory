"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import TaskCard from './components/TaskCard';
import ReportView from './components/ReportView';

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
    // --- G4.0 Engine State ---
    const [activeTab, setActiveTab] = useState<'LEADOPS' | 'MANUAL' | 'TASKS' | 'REPORTS'>('LEADOPS');
    const [engineStats, setEngineStats] = useState<any>(null);
    const [runs, setRuns] = useState<any[]>([]);
    const [opsLoading, setOpsLoading] = useState(false);

    // --- Legacy Scout State ---
    const [atlas, setAtlas] = useState<AtlasEntry[]>([]);
    const [selectedEntry, setSelectedEntry] = useState<AtlasEntry | null>(null);
    const [customQuery, setCustomQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [leads, setLeads] = useState<any[]>([]);
    const [logs, setLogs] = useState<string>('');
    const [toast, setToast] = useState<string | null>(null);

    // --- G6.0 Run Drilldown ---
    const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
    const [runLeads, setRunLeads] = useState<any[]>([]);
    const [detailLoading, setDetailLoading] = useState(false);
    const [statusUpdating, setStatusUpdating] = useState<string | null>(null); // PlaceID being updated
    const [noteModal, setNoteModal] = useState<{ placeId: string, currentNote: string } | null>(null);
    const [filters, setFilters] = useState({ minScore: 0, status: 'all', hasWebsite: false, hasPhone: false });
    const [autoCreateEnabled, setAutoCreateEnabled] = useState(false); // G9.0

    // Auto-Assist Hook
    // Auto-Assist Hook
    useEffect(() => {
        if (autoCreateEnabled && selectedRunId) {
            const runAssist = async () => {
                showToast("✨ Running Auto-Assist...");
                try {
                    const res = await fetch('/api/growth/assist', {
                        method: 'POST',
                        body: JSON.stringify({ runId: selectedRunId })
                    });
                    const data = await res.json();
                    if (data.success && data.tasks_created > 0) {
                        showToast(`✨ Auto-created ${data.tasks_created} tasks!`);
                        // Reload data
                        openRun(selectedRunId);
                        loadTasks();
                    } else {
                        showToast("✨ Auto-Assist: No new tasks needed.");
                    }
                } catch (e) { console.error(e); }
            };
            runAssist();
        }
    }, [selectedRunId, autoCreateEnabled]);

    // Helper: Generate Client-Side Suggestions (Lightweight)
    const getSuggestions = (lead: any) => {
        const suggestions = [];
        if (lead.score >= 8 && lead.status === 'new' && lead.phone) {
            suggestions.push({ label: '📞 Call Priority Lead', action: 'Call' });
        }
        if (lead.status === 'contacted' && (!lead.pending_tasks || lead.pending_tasks === 0)) {
            suggestions.push({ label: '📅 Schedule Follow-up', action: 'Follow Up' });
        }
        return suggestions;
    };

    // --- G7.0 Tasks ---
    const [myTasks, setMyTasks] = useState<any[]>([]);
    const [completedTasks, setCompletedTasks] = useState<any[]>([]); // G7.1
    const [createTaskModal, setCreateTaskModal] = useState<{ placeId: string } | null>(null);
    const [newTaskNote, setNewTaskNote] = useState('');
    const [newTaskDate, setNewTaskDate] = useState('');

    useEffect(() => {
        loadAtlas();
        loadEngineData();
        loadTasks();
    }, []);

    // --- ENGINE OPS (G4.0) ---
    const loadEngineData = async () => {
        try {
            // Load Stats
            const statsRes = await fetch('/api/growth/stats');
            const statsData = await statsRes.json();
            if (statsData.success) setEngineStats(statsData.stats);

            // Load Runs
            const runsRes = await fetch('/api/growth/runs');
            const runsData = await runsRes.json();
            if (runsData.success) setRuns(runsData.runs);
        } catch (e) {
            console.error("Failed to load engine data", e);
        }
    };

    const loadTasks = async () => {
        try {
            // Pending
            const resPending = await fetch('/api/growth/tasks');
            const dataPending = await resPending.json();
            if (dataPending.success) setMyTasks(dataPending.tasks);

            // Completed (G8)
            const resDone = await fetch('/api/growth/tasks?status=done&limit=10');
            const dataDone = await resDone.json();
            if (dataDone.success) setCompletedTasks(dataDone.tasks);
        } catch (e) { console.error(e); }
    };

    const handleOp = async (action: 'orchestrate' | 'ingest') => {
        setOpsLoading(true);
        const startTime = new Date();
        const startStr = startTime.toLocaleTimeString();
        setLogs(prev => prev + `\n\n[${startStr}] ▶ STARTING ${action.toUpperCase()}...\n----------------------------------------`);

        try {
            const res = await fetch(`/api/growth/ops/${action}`, { method: 'POST', body: JSON.stringify({}) });
            const data = await res.json();
            const endTime = new Date();
            const endStr = endTime.toLocaleTimeString();
            const duration = ((endTime.getTime() - startTime.getTime()) / 1000).toFixed(1);

            if (data.success) {
                showToast(`✅ ${action.toUpperCase()} Complete!`);
                setLogs(prev => prev + `\n${data.stdout}\n----------------------------------------\n[${endStr}] ✅ FINISHED (Exit: 0) in ${duration}s`);
                loadEngineData(); // Refresh data
            } else {
                showToast(`❌ ${action.toUpperCase()} Failed`);
                setLogs(prev => prev + `\n${data.error}\n${data.stderr}\n----------------------------------------\n[${endStr}] ❌ FAILED (Exit: 1) in ${duration}s`);
            }
        } catch (e: any) {
            showToast(`❌ Network Error`);
            setLogs(prev => prev + `\n\n❌ Network Error: ${e.message}`);
        } finally {
            setOpsLoading(false);
        }
    };

    // --- MANUAL SCOUT OPS (Legacy) ---
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
        const query = `${entry.sub_vertical} ${entry.vertical}`;
        setCustomQuery(query);
        setLogs(`📋 Selected: ${entry.sub_vertical}\n💡 Pain: ${entry.pain_point}\n🎯 TAM: ${entry.tam_us.toLocaleString()} | MRR: $${entry.deal_size_mrr}\n🔍 Auto-Query: "${query}"`);
    };

    const showToast = (message: string) => {
        setToast(message);
        setTimeout(() => setToast(null), 3000);
    };

    // --- G6/G7 DRILLDOWN LOGIC ---
    const openRun = async (runId: string) => {
        setSelectedRunId(runId);
        setDetailLoading(true);
        try {
            const res = await fetch(`/api/growth/runs/${runId}/leads`);
            const data = await res.json();
            if (data.success) {
                setRunLeads(data.leads);
            } else {
                showToast(`❌ Failed to load leads: ${data.error}`);
            }
        } catch (e) {
            console.error(e);
            showToast("❌ Network error loading leads");
        } finally {
            setDetailLoading(false);
        }
    };

    const updateStatus = async (placeId: string, newStatus: string) => {
        setStatusUpdating(placeId);
        try {
            const res = await fetch(`/api/growth/leads/${placeId}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            const data = await res.json();
            if (data.success) {
                // Optimistic Update
                setRunLeads(prev => prev.map(l => l.place_id === placeId ? { ...l, status: newStatus } : l));
                showToast(`✅ Status updated to ${newStatus}`);
                loadEngineData(); // Refresh main stats
            } else {
                showToast("❌ Update failed");
            }
        } catch (e) {
            showToast("❌ Network error");
        } finally {
            setStatusUpdating(null);
        }
    };

    const saveNote = async () => {
        if (!noteModal) return;
        const { placeId, currentNote } = noteModal;
        setStatusUpdating(placeId);
        try {
            const lead = runLeads.find(l => l.place_id === placeId);
            if (!lead) return;

            const res = await fetch(`/api/growth/leads/${placeId}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: lead.status || 'new', notes: currentNote })
            });
            const data = await res.json();
            if (data.success) {
                setRunLeads(prev => prev.map(l => l.place_id === placeId ? { ...l, outcome_notes: currentNote } : l));
                showToast("✅ Note saved");
            }
        } finally {
            setStatusUpdating(null);
            setNoteModal(null);
        }
    };

    // --- G7 Tasks Logic ---
    const handleCreateTask = async () => {
        if (!createTaskModal || !newTaskNote) return;
        setStatusUpdating(createTaskModal.placeId);
        try {
            // Basic NLP to guess date if empty
            let dueAt = newTaskDate;
            if (!dueAt) {
                // Default to tomorrow 10am
                const d = new Date();
                d.setDate(d.getDate() + 1);
                d.setHours(10, 0, 0, 0);
                dueAt = d.toISOString();
            }

            const res = await fetch('/api/growth/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    placeId: createTaskModal.placeId,
                    notes: newTaskNote,
                    dueAt: dueAt,
                    type: 'follow_up'
                })
            });

            if (res.ok) {
                showToast("✅ Task Created");
                loadTasks();
                // Optimistic logic: update pending_tasks count for lead
                setRunLeads(prev => prev.map(l => l.place_id === createTaskModal.placeId ? { ...l, pending_tasks: (l.pending_tasks || 0) + 1 } : l));
            } else {
                showToast("❌ Failed to create task");
            }
        } catch (e) {
            showToast("❌ Network error");
        } finally {
            setStatusUpdating(null);
            setCreateTaskModal(null);
            setNewTaskNote('');
            setNewTaskDate('');
        }
    }

    const markTaskDone = async (taskId: number) => {
        try {
            const res = await fetch('/api/growth/tasks', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ taskId, status: 'done' })
            });
            if (res.ok) {
                showToast("✅ Task Complete");
                loadTasks(); // Refresh lists from DB
            }
        } catch (e) { showToast("❌ Error marking done"); }
    }

    // Filter Logic
    const filteredLeads = runLeads.filter(l => {
        if (filters.minScore > 0 && (l.score || 0) < filters.minScore) return false;
        if (filters.status !== 'all' && (l.status || 'new') !== filters.status) return false;
        if (filters.hasWebsite && !l.website) return false;
        if (filters.hasPhone && !l.phone) return false;
        return true;
    });

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
                const enrichedLeads = (data.leads || []).map((lead: any) => ({
                    ...lead,
                    suggested_template: selectedEntry?.suggested_template || 'Custom X Agent',
                    buyer_persona: selectedEntry?.buyer_persona || 'Owner',
                    deal_size: selectedEntry?.deal_size_mrr || 1000
                }));
                setLeads(enrichedLeads);
                setLogs(prev => prev + `\n✅ Scout Complete. Found ${enrichedLeads.length} qualified leads.`);

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
                        }
                    } catch (e) { }
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
        if (!confirm(`Generate Demo X Agent for ${lead.title}?`)) return;
        setLogs(prev => prev + `\n\n🚀 generating agent...`);
        let slug = lead.title.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim().replace(/\s+/g, '_').slice(0, 50);

        try {
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: lead.href })
            });
            const data = await res.json();
            if (data.success) {
                const demoLink = `/demo/${slug}`;
                setLogs(prev => prev + `\n✅ Demo Agent Ready: ${demoLink}`);
                setLeads(prev => prev.map(l => l.href === lead.href ? { ...l, demoLink } : l));
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n❌ Error: ${e.message}`);
        }
    };

    const getPainSignal = (reason: string): string => {
        if (!reason) return "Unknown";
        if (reason.toLowerCase().includes("call")) return "📞 Manual Phone";
        return "⚙️ Manual Ops";
    };

    const formatCurrency = (num: number) => {
        if (num >= 1000) return `$${(num / 1000).toFixed(0)}K`;
        return `$${num}`;
    };

    // Render Playbook Badge
    const renderPlaybookAction = (action: string, priority: string) => {
        let color = "bg-slate-700 text-slate-300";
        if (action.includes("Call")) color = "bg-blue-600 text-white";
        if (action.includes("Visit")) color = "bg-purple-600 text-white";
        if (priority === "High") color += " border-2 border-yellow-400";

        return <span className={`px-2 py-1 rounded text-xs font-bold ${color}`}>{action}</span>;
    };

    return (
        <div className="p-8 max-w-[1800px] mx-auto relative min-h-screen bg-slate-50">
            {/* Toast */}
            {toast && (
                <div className="fixed top-4 right-4 z-50 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg animate-pulse">
                    {toast}
                </div>
            )}

            <header className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">📈 GROWTH ENGINE</h1>
                    <p className="text-slate-500 font-mono text-sm">LOCAL LEAD OPs | G7.0</p>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={() => setActiveTab('TASKS')}
                        className={`px-4 py-2 rounded text-sm font-bold flex gap-2 items-center ${activeTab === 'TASKS' ? 'bg-orange-600 text-white' : 'bg-slate-200 text-slate-700'}`}
                    >
                        📝 MY TASKS
                        {myTasks.length > 0 && <span className="bg-white text-orange-600 px-2 rounded-full text-xs">{myTasks.length}</span>}
                    </button>
                    <button
                        onClick={() => setActiveTab('LEADOPS')}
                        className={`px-4 py-2 rounded text-sm font-bold ${activeTab === 'LEADOPS' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'}`}
                    >
                        🏭 ENGINE OPS
                    </button>
                    <button
                        onClick={() => setActiveTab('MANUAL')}
                        className={`px-4 py-2 rounded text-sm font-bold ${activeTab === 'MANUAL' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'}`}
                    >
                        🔍 MANUAL SCOUT
                    </button>
                    <button
                        onClick={() => setActiveTab('REPORTS')}
                        className={`px-4 py-2 rounded text-sm font-bold ${activeTab === 'REPORTS' ? 'bg-purple-600 text-white' : 'bg-slate-200 text-slate-700'}`}
                    >
                        📊 REPORTS
                    </button>
                    <Link href="/" className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded text-slate-700 text-sm font-bold">
                        ← DASHBOARD
                    </Link>
                </div>
            </header>

            {/* === TASKS TAB === */}
            {activeTab === 'TASKS' && (
                <div className="max-w-4xl mx-auto space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-slate-800">My Task Queue</h2>
                            <button
                                onClick={() => showToast("💡 Please select a Lead in Engine Ops to add a task.")}
                                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-bold flex items-center gap-2"
                                title="Select a lead in Engine Ops to attach a task"
                            >
                                ➕ Add Task
                            </button>
                        </div>

                        {myTasks.length === 0 ? (
                            <div className="text-center p-12 text-slate-400">
                                <div className="text-4xl mb-4">✅</div>
                                <p>All caught up! Go to Engine Ops to find new leads.</p>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {/* Overdue */}
                                {myTasks.some(t => new Date(t.due_at) < new Date() && new Date(t.due_at).getDate() !== new Date().getDate()) && (
                                    <div>
                                        <h3 className="text-red-400 font-bold text-xs uppercase mb-2">🔥 Overdue</h3>
                                        <div className="space-y-2">
                                            {myTasks.filter(t => new Date(t.due_at) < new Date() && new Date(t.due_at).getDate() !== new Date().getDate()).map(task => (
                                                <TaskCard key={task.task_id} task={task} markTaskDone={markTaskDone} isOverdue={true} />
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Due Today */}
                                {myTasks.some(t => new Date(t.due_at).toDateString() === new Date().toDateString()) && (
                                    <div>
                                        <h3 className="text-orange-400 font-bold text-xs uppercase mb-2">📅 Due Today</h3>
                                        <div className="space-y-2">
                                            {myTasks.filter(t => new Date(t.due_at).toDateString() === new Date().toDateString()).map(task => (
                                                <TaskCard key={task.task_id} task={task} markTaskDone={markTaskDone} />
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Upcoming */}
                                {myTasks.some(t => new Date(t.due_at) > new Date() && new Date(t.due_at).toDateString() !== new Date().toDateString()) && (
                                    <div>
                                        <h3 className="text-blue-400 font-bold text-xs uppercase mb-2">Upcoming</h3>
                                        <div className="space-y-2">
                                            {myTasks.filter(t => new Date(t.due_at) > new Date() && new Date(t.due_at).toDateString() !== new Date().toDateString()).map(task => (
                                                <TaskCard key={task.task_id} task={task} markTaskDone={markTaskDone} />
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Recently Completed */}
                        {completedTasks.length > 0 && (
                            <div className="mt-8 pt-8 border-t border-slate-100">
                                <h3 className="text-sm font-bold text-slate-400 uppercase mb-4">Recently Completed</h3>
                                <div className="space-y-2 opacity-60">
                                    {completedTasks.map((task) => (
                                        <div key={task.task_id} className="flex items-center gap-4 p-3 bg-slate-50 rounded border border-slate-100">
                                            <span className="text-green-500 font-bold">✔</span>
                                            <span className="text-slate-500 line-through text-sm">{task.notes}</span>
                                            <span className="text-xs text-slate-400 ml-auto">{task.place_name}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
            {activeTab === 'REPORTS' && (
                <ReportView />
            )}

            {activeTab === 'LEADOPS' && (
                <div className="space-y-6">
                    {/* Metrics Cards */}
                    <div className="grid grid-cols-4 gap-4">
                        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-sm">
                            <h3 className="text-xs font-bold text-slate-400 uppercase">Exported</h3>
                            <div className="text-2xl font-bold text-slate-100">{engineStats?.total_exported || 0}</div>
                        </div>
                        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-sm">
                            <h3 className="text-xs font-bold text-slate-400 uppercase">Contacted</h3>
                            <div className="text-2xl font-bold text-blue-400">{engineStats?.total_contacted || 0}</div>
                        </div>
                        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-sm">
                            <h3 className="text-xs font-bold text-slate-400 uppercase">Meetings</h3>
                            <div className="text-2xl font-bold text-purple-400">{engineStats?.meetings || 0}</div>
                        </div>
                        <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-sm">
                            <h3 className="text-xs font-bold text-slate-400 uppercase">Wins</h3>
                            <div className="text-2xl font-bold text-green-400">{engineStats?.won || 0}</div>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-6">
                        {/* Runs Table */}
                        <div className="col-span-2 bg-slate-800 rounded-xl border border-slate-700 shadow-sm overflow-hidden">
                            <div className="p-3 border-b border-slate-700 bg-slate-900 flex justify-between">
                                <h3 className="font-bold text-slate-200">Run History</h3>
                                <button onClick={loadEngineData} className="text-xs text-blue-400 hover:underline">Refresh</button>
                            </div>
                            <table className="w-full text-sm text-left text-slate-300">
                                <thead className="bg-slate-900 text-xs uppercase text-slate-500 font-semibold">
                                    <tr>
                                        <th className="p-3">Run ID</th>
                                        <th className="p-3">Date</th>
                                        <th className="p-3 text-right">Leads</th>
                                        <th className="p-3 text-right">Wins</th>
                                        <th className="p-3 text-right">Cost</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {runs.map((r) => (
                                        <tr key={r.run_id} className="hover:bg-slate-700/50 cursor-pointer" onClick={() => openRun(r.run_id)}>
                                            <td className="p-3 font-mono text-xs text-blue-400 hover:underline">{r.run_id}</td>
                                            <td className="p-3">
                                                {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Invalid Date'}
                                            </td>
                                            <td className="p-3 text-right font-mono text-slate-300">{r.total_exported || 0}</td>
                                            <td className="p-3 text-right font-mono text-green-400">{r.wins_count || 0}</td>
                                            <td className="p-3 text-right font-mono text-slate-400">${(r.cost_estimate_usd || 0).toFixed(2)}</td>
                                        </tr>
                                    ))}
                                    {runs.length === 0 && (
                                        <tr><td colSpan={3} className="p-4 text-center text-slate-500">No runs found</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Ops Panel */}
                        <div className="col-span-1 space-y-4">
                            <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-sm p-4">
                                <h3 className="font-bold text-slate-200 mb-4">⚙️ Operations</h3>
                                <div className="space-y-3">
                                    <button
                                        disabled={opsLoading}
                                        onClick={() => handleOp('orchestrate')}
                                        className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold flex justify-center items-center gap-2 border border-blue-500 shadow-lg"
                                    >
                                        {opsLoading ? 'Running...' : '▶ RUN ORCHESTRATOR'}
                                    </button>
                                    <button
                                        disabled={opsLoading}
                                        onClick={() => handleOp('ingest')}
                                        className="w-full py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-bold flex justify-center items-center gap-2 border border-purple-500 shadow-lg"
                                    >
                                        {opsLoading ? 'Processing...' : '📥 INGEST OUTCOMES'}
                                    </button>
                                </div>
                            </div>

                            {/* Console Log */}
                            <div className="bg-slate-950 p-4 rounded-xl border border-slate-700 min-h-[300px] font-mono text-xs text-green-400 overflow-auto whitespace-pre-wrap">
                                <div className="text-slate-500 mb-2 border-b border-slate-800 pb-2">// OPS CONSOLE</div>
                                {logs || "Ready."}
                            </div>
                        </div>
                    </div>

                </div>
            )}

            {/* Auto-Creation Status (G9) */}
            {
                autoCreateEnabled && (
                    <div className="fixed bottom-4 left-4 bg-purple-900 text-purple-200 px-4 py-2 rounded-full text-xs font-bold border border-purple-700 shadow-lg animate-pulse z-50">
                        ✨ Auto-Assist Active
                    </div>
                )
            }

            {/* DRILLDOWN VIEW */}
            {
                selectedRunId && (
                    <div className="fixed inset-0 bg-slate-900/95 z-50 overflow-auto p-8">
                        <div className="max-w-[1600px] mx-auto bg-slate-800 rounded-xl shadow-2xl border border-slate-700 min-h-screen flex flex-col">
                            {/* Header */}
                            <div className="p-6 border-b border-slate-700 flex justify-between items-center sticky top-0 bg-slate-800 z-10">
                                <div className="flex items-center gap-4">
                                    <button onClick={() => setSelectedRunId(null)} className="text-slate-400 hover:text-white">← Back</button>
                                    <h2 className="text-xl font-bold text-white font-mono">{selectedRunId}</h2>
                                    <span className="bg-blue-900 text-blue-200 px-3 py-1 rounded-full text-xs font-bold">{filteredLeads.length} Leads</span>
                                </div>
                                <div className="flex gap-4 items-center">
                                    <select
                                        className="bg-slate-900 text-slate-300 p-2 rounded border border-slate-700 text-sm"
                                        value={filters.status}
                                        onChange={e => setFilters({ ...filters, status: e.target.value })}
                                    >
                                        <option value="all">All Status</option>
                                        <option value="new">New</option>
                                        <option value="contacted">Contacted</option>
                                        <option value="won">Won</option>
                                        <option value="dead_end">Dead End</option>
                                    </select>
                                    <label className="text-xs text-slate-400 flex items-center gap-2">
                                        <input type="checkbox" checked={filters.hasWebsite} onChange={e => setFilters({ ...filters, hasWebsite: e.target.checked })} />
                                        Has Website
                                    </label>
                                    {/* Refresh Button */}
                                    <button onClick={() => openRun(selectedRunId)} className="p-2 bg-slate-700 rounded hover:bg-slate-600">🔄</button>

                                    {/* Auto-Create Toggle */}
                                    <button
                                        onClick={() => setAutoCreateEnabled(!autoCreateEnabled)}
                                        className={`p-2 rounded border ${autoCreateEnabled ? 'bg-purple-600 border-purple-400 text-white' : 'bg-slate-900 border-slate-700 text-slate-500'}`}
                                        title="Toggle Auto-Task Creation"
                                    >
                                        ✨
                                    </button>
                                </div>
                            </div>

                            {/* Table */}
                            <div className="flex-1 overflow-auto p-6">
                                {detailLoading ? (
                                    <div className="text-center p-20 text-slate-500 animate-pulse">Loading leads...</div>
                                ) : (
                                    <table className="w-full text-left text-sm text-slate-300">
                                        <thead className="bg-slate-900 text-xs uppercase text-slate-500 font-semibold sticky top-0">
                                            <tr>
                                                <th className="p-3">Score & Playbook</th>
                                                <th className="p-3">Business</th>
                                                <th className="p-3">Contact</th>
                                                <th className="p-3">Status</th>
                                                <th className="p-3 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-700">
                                            {filteredLeads.map(lead => (
                                                <tr key={lead.place_id} className="hover:bg-slate-700/30">
                                                    <td className="p-3">
                                                        {/* Score & Playbook (G7) */}
                                                        <div className="flex flex-col gap-1 items-start">
                                                            {/* Playbook Badge */}
                                                            {lead.playbook && renderPlaybookAction(lead.playbook.action, lead.playbook.priority)}

                                                            <div className="flex items-center gap-2 mt-1">
                                                                <div className={`font-bold ${lead.rating > 4.5 ? 'text-green-400' : 'text-slate-400'}`}>
                                                                    {lead.rating || '-'}★
                                                                </div>
                                                                {lead.confidence && (
                                                                    <div className={`w-2 h-2 rounded-full ${lead.confidence === 'High' ? 'bg-green-500' : lead.confidence === 'Medium' ? 'bg-yellow-500' : 'bg-red-500'}`} title={`Confidence: ${lead.confidence}`}></div>
                                                                )}
                                                            </div>

                                                            {/* G9 Suggestions */}
                                                            {getSuggestions(lead).map((s, i) => (
                                                                <div key={i}
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        setCreateTaskModal({ placeId: lead.place_id });
                                                                        setNewTaskNote(s.action + ": " + s.label);
                                                                    }}
                                                                    className="mt-2 text-[10px] bg-purple-900/40 text-purple-200 px-2 py-1 rounded cursor-pointer hover:bg-purple-800 border border-purple-500/30 flex items-center gap-1 w-full"
                                                                    title="Click to Create Task"
                                                                >
                                                                    💡 {s.label}
                                                                </div>
                                                            ))}

                                                            <div className="text-[10px] text-slate-500 cursor-help mt-1" title={lead.score_breakdown?.join('\n')}>
                                                                Score Breakdown ▾
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="p-3">
                                                        <div className="font-bold text-white">{lead.name}</div>
                                                        <div className="text-xs text-slate-500 line-clamp-1">{lead.formatted_address}</div>
                                                        {lead.pending_tasks > 0 && (
                                                            <span className="text-[10px] bg-orange-900 text-orange-200 px-1 rounded border border-orange-700 mt-1 inline-block">
                                                                {lead.pending_tasks} Tasks Pending
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="p-3 space-y-1">
                                                        {lead.phone && <div className="text-xs">📞 {lead.phone}</div>}
                                                        {lead.website && <a href={lead.website} target="_blank" className="text-xs text-blue-400 hover:underline truncate block max-w-[200px]">🌐 {lead.website}</a>}
                                                    </td>
                                                    <td className="p-3">
                                                        <select
                                                            value={lead.status || 'new'}
                                                            onChange={(e) => updateStatus(lead.place_id, e.target.value)}
                                                            disabled={statusUpdating === lead.place_id}
                                                            className={`bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs font-bold
                                                                    ${lead.status === 'won' ? 'text-green-400 border-green-900' : ''}
                                                                    ${lead.status === 'dead_end' ? 'text-red-400 border-red-900' : ''}
                                                                    ${lead.status === 'contacted' ? 'text-blue-400 border-blue-900' : ''}
                                                                `}
                                                        >
                                                            <option value="new">New</option>
                                                            <option value="shortlisted">Shortlisted</option>
                                                            <option value="exported">Exported</option>
                                                            <option value="contacted">Contacted</option>
                                                            <option value="booked_meeting">Meeting</option>
                                                            <option value="won">Won</option>
                                                            <option value="dead_end">Dead End</option>
                                                            <option value="do_not_contact">DNC</option>
                                                        </select>
                                                    </td>
                                                    <td className="p-3 text-right flex gap-2 justify-end">
                                                        <button
                                                            onClick={() => setCreateTaskModal({ placeId: lead.place_id })}
                                                            className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-slate-300"
                                                            title="Create Task"
                                                        >
                                                            📅
                                                        </button>
                                                        <button
                                                            onClick={() => setNoteModal({ placeId: lead.place_id, currentNote: lead.outcome_notes || '' })}
                                                            className="text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-slate-300"
                                                        >
                                                            {lead.outcome_notes ? '📝 Edit' : '+ Note'}
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>

                        {/* Create Task Modal */}
                        {createTaskModal && (
                            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
                                <div className="bg-slate-800 p-6 rounded-xl w-full max-w-md border border-slate-600 shadow-xl">
                                    <h3 className="font-bold text-white mb-4">Create Task</h3>
                                    <input
                                        type="text"
                                        className="w-full bg-slate-900 border border-slate-700 rounded p-3 text-slate-200 mb-3 focus:border-blue-500 outline-none"
                                        placeholder="Task Description (e.g. Call John)"
                                        value={newTaskNote}
                                        onChange={e => setNewTaskNote(e.target.value)}
                                        autoFocus
                                    />
                                    <input
                                        type="datetime-local"
                                        className="w-full bg-slate-900 border border-slate-700 rounded p-3 text-slate-200 mb-3 focus:border-blue-500 outline-none"
                                        value={newTaskDate}
                                        onChange={e => setNewTaskDate(e.target.value)}
                                    />
                                    <div className="flex justify-end gap-3 mt-4">
                                        <button onClick={() => setCreateTaskModal(null)} className="px-4 py-2 text-slate-400 hover:text-white">Cancel</button>
                                        <button onClick={handleCreateTask} className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded font-bold">Create Task</button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Note Modal */}
                        {noteModal && (
                            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
                                <div className="bg-slate-800 p-6 rounded-xl w-full max-w-md border border-slate-600 shadow-xl">
                                    <h3 className="font-bold text-white mb-4">Add Note</h3>
                                    <textarea
                                        className="w-full bg-slate-900 border border-slate-700 rounded p-3 text-slate-200 h-32 focus:border-blue-500 outline-none"
                                        value={noteModal.currentNote}
                                        onChange={e => setNoteModal({ ...noteModal, currentNote: e.target.value })}
                                        placeholder="Call notes, gatekeeper name, objection..."
                                    />
                                    <div className="flex justify-end gap-3 mt-4">
                                        <button onClick={() => setNoteModal(null)} className="px-4 py-2 text-slate-400 hover:text-white">Cancel</button>
                                        <button onClick={saveNote} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold">Save Note</button>
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                )}


            {
                activeTab === 'MANUAL' && (
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
                                                    <th className="p-3">Pain Signal</th>
                                                    <th className="p-3">Template</th>
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
                                                        <td className="p-3 text-xs">{getPainSignal(lead.nova_reason)}</td>
                                                        <td className="p-3">
                                                            <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-mono">{lead.suggested_template}</span>
                                                        </td>
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

                        {/* Console for Manual */}
                        <div className="xl:col-span-1">
                            <div className="bg-slate-900 p-4 rounded-xl border border-slate-700 min-h-[400px] font-mono text-xs text-green-400 overflow-auto whitespace-pre-wrap sticky top-4">
                                <div className="text-slate-500 mb-2 border-b border-slate-700 pb-2">// SCOUT CONSOLE</div>
                                {logs || "> Select a vertical from the Atlas."}
                            </div>
                        </div>
                    </div>
                )
            }
        </div>
    )
}
