"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface ServiceStatus {
    status: string;
    latency?: number;
    model?: string;
    minutes_used?: number;
    minutes_remaining?: number;
    characters_used?: number;
    characters_limit?: number;
    voice?: string;
}

interface StatusData {
    timestamp: string;
    services: {
        ollama: ServiceStatus;
        gemini: ServiceStatus;
        tavus: ServiceStatus;
        elevenlabs: ServiceStatus;
    };
}

export default function UsagePage() {
    const [status, setStatus] = useState<StatusData | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const fetchStatus = async () => {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            setStatus(data);
            setLastUpdate(new Date());
        } catch (e) {
            console.error("Failed to fetch status", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 60000); // Auto-refresh every 60s
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'online': return 'bg-green-500';
            case 'offline': return 'bg-red-500';
            case 'error': return 'bg-red-500';
            case 'timeout': return 'bg-yellow-500';
            case 'no_key': return 'bg-slate-500';
            default: return 'bg-slate-400';
        }
    };

    const getStatusEmoji = (status: string) => {
        switch (status) {
            case 'online': return '🟢';
            case 'offline': return '🔴';
            case 'error': return '🔴';
            case 'timeout': return '🟡';
            case 'no_key': return '⚪';
            default: return '⚪';
        }
    };

    const getHealthLevel = (used: number, total: number) => {
        const pct = (used / total) * 100;
        if (pct >= 90) return { color: 'bg-red-500', label: 'CRITICAL', emoji: '🔴' };
        if (pct >= 70) return { color: 'bg-yellow-500', label: 'LOW', emoji: '🟡' };
        return { color: 'bg-green-500', label: 'OK', emoji: '🟢' };
    };

    const CircularGauge = ({ used, total, label, color }: { used: number; total: number; label: string; color: string }) => {
        const pct = Math.min((used / total) * 100, 100);
        const circumference = 2 * Math.PI * 45;
        const offset = circumference - (pct / 100) * circumference;

        return (
            <div className="relative w-32 h-32">
                <svg className="transform -rotate-90 w-32 h-32">
                    <circle
                        cx="64"
                        cy="64"
                        r="45"
                        stroke="currentColor"
                        strokeWidth="10"
                        fill="transparent"
                        className="text-slate-700"
                    />
                    <circle
                        cx="64"
                        cy="64"
                        r="45"
                        stroke="currentColor"
                        strokeWidth="10"
                        fill="transparent"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        className={color.replace('bg-', 'text-')}
                        strokeLinecap="round"
                    />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold text-white">{Math.round(pct)}%</span>
                    <span className="text-xs text-slate-400">{label}</span>
                </div>
            </div>
        );
    };

    const ProgressBar = ({ used, total, label }: { used: number; total: number; label: string }) => {
        const pct = Math.min((used / total) * 100, 100);
        const health = getHealthLevel(used, total);

        return (
            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span className="text-slate-400">{label}</span>
                    <span className="text-white font-mono">{used.toLocaleString()} / {total.toLocaleString()}</span>
                </div>
                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${health.color} transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                    />
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
            <header className="mb-8 flex justify-between items-center max-w-6xl mx-auto">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">⚙️ SYSTEM STATUS</h1>
                    <p className="text-slate-400 font-mono text-sm">
                        API HEALTH | USAGE MONITORING | AUTO-REFRESH: 60s
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={fetchStatus}
                        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-bold"
                    >
                        🔄 Refresh
                    </button>
                    <Link href="/" className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-bold">
                        ← Dashboard
                    </Link>
                </div>
            </header>

            {loading ? (
                <div className="text-center text-white py-20">
                    <div className="animate-spin text-6xl mb-4">⚙️</div>
                    <p>Checking system status...</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-6xl mx-auto">
                    {/* Ollama (Local) */}
                    <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                🦙 Ollama (Local)
                            </h2>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getStatusColor(status?.services.ollama.status || 'unknown')}`}>
                                {getStatusEmoji(status?.services.ollama.status || 'unknown')} {status?.services.ollama.status?.toUpperCase()}
                            </span>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Endpoint</span>
                                <span className="text-white font-mono">localhost:11434</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Model</span>
                                <span className="text-white font-mono">{status?.services.ollama.model || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Latency</span>
                                <span className="text-green-400 font-mono">{status?.services.ollama.latency || 0}ms</span>
                            </div>
                        </div>
                    </div>

                    {/* Gemini */}
                    <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                ✨ Google Gemini
                            </h2>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getStatusColor(status?.services.gemini.status || 'unknown')}`}>
                                {getStatusEmoji(status?.services.gemini.status || 'unknown')} {status?.services.gemini.status?.toUpperCase()}
                            </span>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Model</span>
                                <span className="text-white font-mono">gemini-2.0-flash-exp</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">API Latency</span>
                                <span className="text-green-400 font-mono">{status?.services.gemini.latency || 0}ms</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Est. MTD Cost</span>
                                <span className="text-yellow-400 font-mono">~$2.50</span>
                            </div>
                        </div>
                    </div>

                    {/* Tavus */}
                    <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                🎬 Tavus
                            </h2>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getStatusColor(status?.services.tavus.status || 'unknown')}`}>
                                {getStatusEmoji(status?.services.tavus.status || 'unknown')} {status?.services.tavus.status?.toUpperCase()}
                            </span>
                        </div>
                        <div className="flex items-center gap-6">
                            <CircularGauge
                                used={status?.services.tavus.minutes_used || 0}
                                total={(status?.services.tavus.minutes_used || 0) + (status?.services.tavus.minutes_remaining || 1000)}
                                label="Used"
                                color={getHealthLevel(
                                    status?.services.tavus.minutes_used || 0,
                                    (status?.services.tavus.minutes_used || 0) + (status?.services.tavus.minutes_remaining || 1000)
                                ).color}
                            />
                            <div className="flex-1 space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-400">Minutes Used</span>
                                    <span className="text-white font-mono">{status?.services.tavus.minutes_used || 0}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-400">Remaining</span>
                                    <span className="text-green-400 font-mono">{status?.services.tavus.minutes_remaining || 0}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ElevenLabs */}
                    <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                🎙️ ElevenLabs
                            </h2>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getStatusColor(status?.services.elevenlabs.status || 'unknown')}`}>
                                {getStatusEmoji(status?.services.elevenlabs.status || 'unknown')} {status?.services.elevenlabs.status?.toUpperCase()}
                            </span>
                        </div>
                        <div className="space-y-4">
                            <ProgressBar
                                used={status?.services.elevenlabs.characters_used || 0}
                                total={status?.services.elevenlabs.characters_limit || 10000}
                                label="Characters"
                            />
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Active Voice</span>
                                <span className="text-white font-mono">{status?.services.elevenlabs.voice || 'Rachel'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Footer */}
            <footer className="text-center text-slate-500 text-xs mt-12">
                Last updated: {lastUpdate?.toLocaleTimeString() || 'Never'} | Auto-refresh in 60s
            </footer>
        </div>
    );
}
