"use client";

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

interface ClientData {
    business_name: string;
    knowledge_base: string;
    persona_context: string;
    system_prompt: string;
}

export default function DemoPage() {
    const params = useParams();
    const slug = params.slug as string;

    const [clientData, setClientData] = useState<ClientData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [callActive, setCallActive] = useState(false);

    useEffect(() => {
        if (slug) {
            loadClientData();
        }
    }, [slug]);

    const loadClientData = async () => {
        try {
            const res = await fetch(`/api/demo/${slug}`);
            const data = await res.json();

            if (data.error) {
                setError(data.error);
            } else {
                setClientData(data);
            }
        } catch (e: any) {
            setError(`Failed to load demo: ${e.message}`);
        } finally {
            setLoading(false);
        }
    };

    const startDemo = async () => {
        setCallActive(true);
        // In production, this would trigger the Tavus API to start a conversation
        // For now, we show the demo UI
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
                <div className="text-center text-white">
                    <div className="animate-spin text-6xl mb-4">⚙️</div>
                    <p className="text-xl font-mono">Loading your X Agent demo...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900 to-slate-900 flex items-center justify-center">
                <div className="text-center text-white max-w-md">
                    <div className="text-6xl mb-4">⚠️</div>
                    <h1 className="text-2xl font-bold mb-4">Agent Not Built Yet</h1>
                    <p className="text-slate-300 mb-6">{error}</p>
                    <a href="/" className="bg-white text-slate-900 px-6 py-3 rounded-lg font-bold hover:bg-slate-100">
                        Return to Factory
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
            {/* Header */}
            <header className="p-6 border-b border-white/10">
                <div className="max-w-4xl mx-auto flex justify-between items-center">
                    <div>
                        <p className="text-blue-400 text-xs font-mono uppercase tracking-wider">X Agent Factory Demo</p>
                        <h1 className="text-white text-xl font-bold">{clientData?.business_name || slug}</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${callActive ? 'bg-green-500 animate-pulse' : 'bg-slate-500'}`}></span>
                        <span className="text-slate-400 text-sm">{callActive ? 'Live' : 'Standby'}</span>
                    </div>
                </div>
            </header>

            {/* Main Demo Area */}
            <main className="max-w-4xl mx-auto p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Video / Avatar Area */}
                    <div className="bg-black rounded-2xl overflow-hidden aspect-video flex items-center justify-center relative">
                        {callActive ? (
                            <div className="text-center">
                                {/* Placeholder for Tavus embed */}
                                <div className="w-32 h-32 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center animate-pulse">
                                    <span className="text-5xl">🤖</span>
                                </div>
                                <p className="text-green-400 font-mono text-sm">CONNECTED</p>
                                <p className="text-white mt-2">Hi! I'm your dedicated AI assistant.</p>
                            </div>
                        ) : (
                            <div className="text-center p-8">
                                <div className="w-24 h-24 bg-slate-800 rounded-full mx-auto mb-4 flex items-center justify-center">
                                    <span className="text-4xl">🎬</span>
                                </div>
                                <p className="text-slate-400 text-sm">Click "Start Demo" to begin</p>
                            </div>
                        )}

                        {/* Overlay Controls */}
                        <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-4">
                            {!callActive ? (
                                <button
                                    onClick={startDemo}
                                    className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-8 py-3 rounded-full font-bold hover:from-green-400 hover:to-emerald-500 transition-all shadow-lg hover:shadow-xl"
                                >
                                    ▶️ Start Demo
                                </button>
                            ) : (
                                <button
                                    onClick={() => setCallActive(false)}
                                    className="bg-red-500 text-white px-6 py-2 rounded-full font-bold hover:bg-red-400"
                                >
                                    ⏹️ End Call
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Info Panel */}
                    <div className="space-y-6">
                        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
                            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                                <span className="text-2xl">🧠</span> What This Agent Knows
                            </h3>
                            <div className="text-slate-300 text-sm space-y-2 max-h-[200px] overflow-y-auto font-mono">
                                <pre className="whitespace-pre-wrap">{clientData?.knowledge_base?.slice(0, 500) || 'Loading...'}</pre>
                                {(clientData?.knowledge_base?.length || 0) > 500 && (
                                    <p className="text-blue-400">... and more</p>
                                )}
                            </div>
                        </div>

                        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
                            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                                <span className="text-2xl">✨</span> Agent Capabilities
                            </h3>
                            <ul className="text-slate-300 text-sm space-y-2">
                                <li className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span> Answer questions about your business
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span> Schedule appointments 24/7
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span> Qualify leads automatically
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span> Handle emergency triage
                                </li>
                            </ul>
                        </div>

                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
                            <h3 className="font-bold mb-2">Ready to Launch Your Own Agent?</h3>
                            <p className="text-sm text-white/80 mb-4">This is a demo built specifically for your business. Get the full version with custom training.</p>
                            <a href="mailto:hello@aifusionlabs.com" className="inline-block bg-white text-blue-600 px-6 py-2 rounded-lg font-bold hover:bg-slate-100 transition-colors">
                                Contact Sales
                            </a>
                        </div>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="p-6 text-center text-slate-500 text-xs mt-12">
                Powered by X Agent Factory | AI Fusion Labs
            </footer>
        </div>
    );
}
