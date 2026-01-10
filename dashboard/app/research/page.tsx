"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface Agent {
    agent_id: string;
    agent_name: string;
    vertical: string;
    status: string;
}

interface ResearchJob {
    id: string;
    agent: string;
    query: string;
    sources: string[];
    status: 'pending' | 'running' | 'complete' | 'error';
    progress: number;
    documentsFound: number;
    startedAt: string;
    completedAt?: string;
}

export default function ResearchPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<string>('');
    const [researchQuery, setResearchQuery] = useState('');
    const [sources, setSources] = useState<string[]>([
        'Veterinary symptom databases',
        'Pet triage protocols',
        'ASPCA poison control',
        'Emergency vet guidelines'
    ]);
    const [customSource, setCustomSource] = useState('');
    const [loading, setLoading] = useState(false);
    const [jobs, setJobs] = useState<ResearchJob[]>([]);
    const [logs, setLogs] = useState<string>('> Research Lab initialized.\n> Select an agent and configure research parameters.');
    const [toast, setToast] = useState<string | null>(null);

    // Load agents on mount
    useEffect(() => {
        loadAgents();
        loadJobs();
    }, []);

    const loadAgents = async () => {
        try {
            const res = await fetch('/api/research/agents');
            const data = await res.json();
            if (data.agents) {
                setAgents(data.agents);
            }
        } catch (e) {
            console.error("Failed to load agents", e);
            // Fallback with Luna
            setAgents([
                { agent_id: 'luna_veterinary', agent_name: 'Dr. Luna', vertical: 'Veterinary', status: 'deployed_testing' }
            ]);
        }
    };

    const loadJobs = async () => {
        try {
            const res = await fetch('/api/research/jobs');
            const data = await res.json();
            if (data.jobs) {
                setJobs(data.jobs);
            }
        } catch (e) {
            console.error("Failed to load jobs", e);
        }
    };

    const showToast = (message: string) => {
        setToast(message);
        setTimeout(() => setToast(null), 5000);
    };

    const addSource = () => {
        if (customSource.trim() && !sources.includes(customSource.trim())) {
            setSources([...sources, customSource.trim()]);
            setCustomSource('');
        }
    };

    const removeSource = (source: string) => {
        setSources(sources.filter(s => s !== source));
    };

    const handleStartResearch = async () => {
        if (!selectedAgent || !researchQuery.trim()) {
            showToast('⚠️ Select an agent and enter a research query');
            return;
        }

        setLoading(true);
        setLogs(prev => prev + `\n\n🚀 INITIATING DEEP RESEARCH`);
        setLogs(prev => prev + `\n   > Agent: ${selectedAgent}`);
        setLogs(prev => prev + `\n   > Query: "${researchQuery}"`);
        setLogs(prev => prev + `\n   > Sources: ${sources.length}`);

        try {
            const res = await fetch('/api/research/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent_id: selectedAgent,
                    query: researchQuery,
                    sources: sources,
                    max_depth: 3,
                    max_pages: 100
                })
            });

            const data = await res.json();

            if (data.success) {
                setLogs(prev => prev + `\n✅ Research job started: ${data.job_id}`);
                setLogs(prev => prev + `\n   > Estimated time: ${data.estimated_time || 'varies'}`);
                showToast(`🔬 Research job started! ID: ${data.job_id}`);

                // Add to jobs list
                const newJob: ResearchJob = {
                    id: data.job_id,
                    agent: selectedAgent,
                    query: researchQuery,
                    sources: sources,
                    status: 'running',
                    progress: 0,
                    documentsFound: 0,
                    startedAt: new Date().toISOString()
                };
                setJobs(prev => [newJob, ...prev]);

                // Start polling for updates
                pollJobStatus(data.job_id);
            } else {
                setLogs(prev => prev + `\n❌ Failed to start: ${data.error}`);
                showToast(`❌ ${data.error}`);
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n❌ Network error: ${e.message}`);
            showToast(`❌ Network error`);
        } finally {
            setLoading(false);
        }
    };

    const pollJobStatus = async (jobId: string) => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/research/status/${jobId}`);
                const data = await res.json();

                if (data.job) {
                    setJobs(prev => prev.map(j =>
                        j.id === jobId ? { ...j, ...data.job } : j
                    ));

                    setLogs(prev => prev + `\n   📊 Progress: ${data.job.progress}% | Docs: ${data.job.documentsFound}`);

                    if (data.job.status === 'complete' || data.job.status === 'error') {
                        clearInterval(interval);
                        if (data.job.status === 'complete') {
                            setLogs(prev => prev + `\n\n✅ RESEARCH COMPLETE!`);
                            setLogs(prev => prev + `\n   📄 Documents collected: ${data.job.documentsFound}`);
                            setLogs(prev => prev + `\n   📁 Ready for KB export`);
                            showToast(`✅ Research complete! ${data.job.documentsFound} documents`);
                        } else {
                            setLogs(prev => prev + `\n❌ Research failed: ${data.job.error}`);
                        }
                    }
                }
            } catch (e) {
                console.error('Poll error:', e);
            }
        }, 5000);
    };

    const handleExportToKB = async (jobId: string) => {
        setLogs(prev => prev + `\n\n📦 EXPORTING TO KNOWLEDGE BASE...`);
        try {
            const res = await fetch('/api/research/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_id: jobId })
            });

            const data = await res.json();
            if (data.success) {
                setLogs(prev => prev + `\n✅ Exported to: ${data.output_path}`);
                setLogs(prev => prev + `\n   > ${data.files_created} KB files created`);
                showToast(`✅ Exported ${data.files_created} KB files!`);
            } else {
                setLogs(prev => prev + `\n❌ Export failed: ${data.error}`);
            }
        } catch (e: any) {
            setLogs(prev => prev + `\n❌ Export error: ${e.message}`);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'running': return 'bg-blue-500 animate-pulse';
            case 'complete': return 'bg-green-500';
            case 'error': return 'bg-red-500';
            default: return 'bg-slate-500';
        }
    };

    return (
        <div className="p-8 max-w-[1800px] mx-auto relative">
            {/* Toast */}
            {toast && (
                <div className="fixed top-4 right-4 z-50 bg-purple-600 text-white px-6 py-3 rounded-lg shadow-lg">
                    {toast}
                </div>
            )}

            {/* Header */}
            <header className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">🔬 RESEARCH LAB</h1>
                    <p className="text-slate-500 font-mono text-sm">DEEP SCRAPER | KB GENERATOR | GPU ACCELERATED</p>
                </div>
                <div className="flex gap-3">
                    <Link href="/growth" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white text-sm font-bold">
                        📈 GROWTH
                    </Link>
                    <Link href="/strategy" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-white text-sm font-bold">
                        ⚔️ WAR ROOM
                    </Link>
                    <Link href="/" className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded text-slate-700 text-sm font-bold">
                        ← DASHBOARD
                    </Link>
                </div>
            </header>

            <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
                {/* Config Panel - Left */}
                <div className="xl:col-span-2 space-y-4">
                    {/* Agent Selector */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white">
                            <h3 className="text-xs font-bold uppercase">🎯 Target Agent</h3>
                            <p className="text-xs text-white/70">Select agent to build KB for</p>
                        </div>
                        <div className="p-4">
                            <select
                                value={selectedAgent}
                                onChange={(e) => {
                                    setSelectedAgent(e.target.value);
                                    const agent = agents.find(a => a.agent_id === e.target.value);
                                    if (agent) {
                                        setResearchQuery(`${agent.vertical} triage protocols symptoms emergency care`);
                                    }
                                }}
                                className="w-full p-3 border border-slate-300 rounded-lg text-sm text-slate-800"
                            >
                                <option value="">Select an agent...</option>
                                {agents.map(agent => (
                                    <option key={agent.agent_id} value={agent.agent_id}>
                                        {agent.agent_name} ({agent.vertical})
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Research Query */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white">
                            <h3 className="text-xs font-bold uppercase">🔍 Research Query</h3>
                            <p className="text-xs text-white/70">What knowledge to gather</p>
                        </div>
                        <div className="p-4">
                            <textarea
                                value={researchQuery}
                                onChange={(e) => setResearchQuery(e.target.value)}
                                placeholder="e.g., veterinary pet triage symptoms emergency protocols..."
                                rows={3}
                                className="w-full p-3 border border-slate-300 rounded-lg text-sm text-slate-800 resize-none"
                            />
                        </div>
                    </div>

                    {/* Sources */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-3 bg-gradient-to-r from-green-600 to-teal-600 text-white">
                            <h3 className="text-xs font-bold uppercase">🌐 Data Sources</h3>
                            <p className="text-xs text-white/70">Websites and databases to scrape</p>
                        </div>
                        <div className="p-4 space-y-3">
                            <div className="flex flex-wrap gap-2">
                                {sources.map((source, i) => (
                                    <span
                                        key={i}
                                        className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs flex items-center gap-2"
                                    >
                                        {source}
                                        <button
                                            onClick={() => removeSource(source)}
                                            className="text-slate-400 hover:text-red-500"
                                        >
                                            ×
                                        </button>
                                    </span>
                                ))}
                            </div>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={customSource}
                                    onChange={(e) => setCustomSource(e.target.value)}
                                    placeholder="Add custom source..."
                                    className="flex-1 p-2 border border-slate-300 rounded text-sm text-slate-800"
                                    onKeyPress={(e) => e.key === 'Enter' && addSource()}
                                />
                                <button
                                    onClick={addSource}
                                    className="px-3 py-2 bg-green-500 text-white rounded text-sm font-bold hover:bg-green-400"
                                >
                                    + Add
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Launch Button */}
                    <button
                        onClick={handleStartResearch}
                        disabled={loading || !selectedAgent || !researchQuery.trim()}
                        className={`w-full py-4 rounded-xl font-bold text-white text-lg transition-all ${loading || !selectedAgent || !researchQuery.trim()
                                ? 'bg-slate-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 shadow-lg hover:shadow-xl'
                            }`}
                    >
                        {loading ? '🔄 RESEARCHING...' : '🚀 START DEEP RESEARCH'}
                    </button>
                </div>

                {/* Jobs Panel - Center */}
                <div className="xl:col-span-2 space-y-4">
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="p-3 border-b border-slate-200 bg-gradient-to-r from-slate-900 to-slate-800 text-white flex justify-between items-center">
                            <h3 className="text-sm font-bold uppercase">📋 Research Jobs</h3>
                            <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded">
                                {jobs.filter(j => j.status === 'running').length} running
                            </span>
                        </div>

                        {jobs.length === 0 ? (
                            <div className="p-12 text-center text-slate-400">
                                <div className="text-4xl mb-4">🔬</div>
                                <p>No research jobs yet.<br />Configure and start a deep search.</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-slate-100 max-h-[500px] overflow-y-auto">
                                {jobs.map(job => (
                                    <div key={job.id} className="p-4 hover:bg-slate-50">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <span className="font-bold text-slate-800">{job.agent}</span>
                                                <p className="text-xs text-slate-500 truncate max-w-[200px]">{job.query}</p>
                                            </div>
                                            <span className={`px-2 py-1 rounded text-xs text-white font-bold ${getStatusColor(job.status)}`}>
                                                {job.status.toUpperCase()}
                                            </span>
                                        </div>

                                        {/* Progress bar */}
                                        <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                                            <div
                                                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                                                style={{ width: `${job.progress}%` }}
                                            />
                                        </div>

                                        <div className="flex justify-between text-xs text-slate-500">
                                            <span>📄 {job.documentsFound} docs</span>
                                            <span>{job.progress}%</span>
                                        </div>

                                        {job.status === 'complete' && (
                                            <button
                                                onClick={() => handleExportToKB(job.id)}
                                                className="mt-3 w-full py-2 bg-green-500 hover:bg-green-400 text-white rounded text-sm font-bold"
                                            >
                                                📦 EXPORT TO KB
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Console - Right */}
                <div className="xl:col-span-1">
                    <div className="bg-slate-900 p-4 rounded-xl border border-slate-700 min-h-[600px] font-mono text-xs text-green-400 overflow-auto whitespace-pre-wrap sticky top-4">
                        <div className="text-slate-500 mb-2 border-b border-slate-700 pb-2">// RESEARCH LAB CONSOLE</div>
                        {logs}
                    </div>
                </div>
            </div>
        </div>
    );
}
