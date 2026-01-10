'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
    Globe, Heart, DollarSign, Scale, Palette, Sparkles,
    Hammer, Database, ClipboardCheck, Shield, Zap,
    Send, Bot, User, FileJson, Terminal, History, Trash2, FolderOpen, Pencil, Check, X
} from 'lucide-react';

// Council Roster Config
const COUNCIL = [
    { name: 'Nova', role: 'The Scout', icon: Globe, color: 'text-blue-400', desc: 'Market Intelligence' },
    { name: 'Eve', role: 'The Empath', icon: Heart, color: 'text-pink-400', desc: 'Psychological Hooks' },
    { name: 'Fin', role: 'The Closer', icon: DollarSign, color: 'text-green-400', desc: 'Sales Strategy' },
    { name: 'Marcus', role: 'The Guardrail', icon: Scale, color: 'text-red-400', desc: 'Legal & Compliance' },
    { name: 'Sasha', role: 'The Creative', icon: Palette, color: 'text-purple-400', desc: 'Visuals & Vibe' },
    { name: 'Sparkle', role: 'The Writer', icon: Sparkles, color: 'text-yellow-400', desc: 'Outreach Copy' },
    { name: 'Troy', role: 'The Architect', icon: Hammer, color: 'text-orange-400', desc: 'System Prompts' },
    { name: 'WebWorker', role: 'The Hands', icon: Database, color: 'text-cyan-400', desc: 'Data Extraction' },
    { name: 'Quinn', role: 'The Evaluator', icon: ClipboardCheck, color: 'text-teal-400', desc: 'QA & Scoring' },
    { name: 'Nia', role: 'The Shield', icon: Shield, color: 'text-indigo-400', desc: 'Security & Red Team' },
    { name: 'Rhea', role: 'The Integrator', icon: Zap, color: 'text-amber-400', desc: 'Tools & APIs' },
];

export default function StrategyPage() {
    const [activePersona, setActivePersona] = useState(COUNCIL[0]);
    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [factoryMode, setFactoryMode] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [sessions, setSessions] = useState<any[]>([]);
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [editContent, setEditContent] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (showHistory) {
            loadSessions();
        }
    }, [showHistory]);

    const [participatingAgents, setParticipatingAgents] = useState<string[]>([]);
    const [roundtableMode, setRoundtableMode] = useState(false);

    const loadSessions = async () => {
        try {
            const res = await fetch('/api/strategy/history');
            const data = await res.json();
            if (data.sessions) {
                setSessions(data.sessions);
            }
        } catch (e) {
            console.error(e);
        }
    };

    // Calculate active participants whenever messages change
    useEffect(() => {
        const participants = Array.from(new Set(
            messages
                .filter(m => m.role === 'assistant' && m.persona)
                .map(m => m.persona)
        ));
        setParticipatingAgents(participants);
    }, [messages]);

    const loadSession = async (filename: string) => {
        if (messages.length > 0 && !confirm("Load this session? Current chat will be replaced.")) return;

        try {
            const res = await fetch('/api/strategy/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });
            const data = await res.json();
            if (data.success) {
                setMessages(data.messages);
                setShowHistory(false);
            }
        } catch (e) {
            alert("Failed to load session");
        }
    };

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch('/api/strategy/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg.content,
                    persona: activePersona.name,
                    history: messages,
                    factoryMode: factoryMode,
                    roundtable: roundtableMode
                })
            });

            const data = await res.json();
            if (data.error) throw new Error(data.error);

            if (data.roundtable && data.replies) {
                // Handle multiple replies
                data.replies.forEach((reply: any, index: number) => {
                    setTimeout(() => {
                        setMessages(prev => [...prev, {
                            role: 'assistant',
                            content: reply.content,
                            persona: reply.persona
                        }]);
                    }, index * 1000); // Stagger bubbles for effect
                });
            } else {
                // Handle single reply
                setMessages(prev => [...prev, { role: 'assistant', content: data.reply, persona: activePersona.name }]);
            }

        } catch (err: any) {
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}`, isError: true }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-screen bg-slate-950 text-slate-100 font-sans flex overflow-hidden">

            {/* SIDEBAR: The Council */}
            <div className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col relative z-20">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                    <div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
                            THE WAR ROOM
                        </h1>
                        <p className="text-xs text-slate-500 mt-1">Strategic Command Center</p>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-2">

                    {/* Mode Toggles */}
                    <div className="flex gap-2 mb-4">
                        <button
                            onClick={() => {
                                setRoundtableMode(!roundtableMode);
                                if (factoryMode && !roundtableMode) setFactoryMode(false); // mutually exclusive? optional
                            }}
                            className={`flex-1 py-2 rounded-lg text-xs font-bold border flex items-center justify-center gap-2 transition-all ${roundtableMode
                                ? 'bg-amber-500 border-amber-600 text-slate-900 animate-pulse'
                                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
                                }`}
                        >
                            <Zap size={14} className={roundtableMode ? "fill-current" : ""} />
                            {roundtableMode ? 'ROUNDTABLE ACTIVE' : 'ROUNDTABLE'}
                        </button>

                        <button
                            onClick={() => setShowHistory(!showHistory)}
                            className={`flex-1 py-2 rounded-lg text-xs font-bold border flex items-center justify-center gap-2 transition-all ${showHistory
                                ? 'bg-blue-600 border-blue-500 text-white'
                                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
                                }`}
                        >
                            {showHistory ? <FolderOpen size={14} /> : <History size={14} />}
                            {showHistory ? 'MISSIONS' : 'HISTORY'}
                        </button>
                    </div>

                    {showHistory ? (
                        <div className="space-y-2 animate-in fade-in slide-in-from-left-4 duration-200">
                            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest pl-2 mb-2">Saved Missions</h2>
                            {sessions.length === 0 && <p className="text-xs text-slate-600 pl-2">No saved missions found.</p>}
                            {sessions.map((s) => (
                                <button
                                    key={s.filename}
                                    onClick={() => loadSession(s.filename)}
                                    className="w-full text-left p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-all group"
                                >
                                    <div className="text-xs font-bold text-slate-300 truncate group-hover:text-white">{s.name}</div>
                                    <div className="text-[10px] text-slate-600 mt-1">{new Date(s.date).toLocaleDateString()}</div>
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-200 space-y-2">
                            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest pl-2 mb-2">The Council</h2>
                            {COUNCIL.map((c) => (
                                <button
                                    key={c.name}
                                    onClick={() => setActivePersona(c)}
                                    className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all border ${activePersona.name === c.name
                                        ? 'bg-slate-800 border-slate-700 shadow-lg'
                                        : 'bg-transparent border-transparent hover:bg-slate-800/50 hover:border-slate-800'
                                        }`}
                                >
                                    <div className={`p-2 rounded-lg bg-slate-900 ${c.color} border border-slate-800`}>
                                        <c.icon size={20} />
                                    </div>
                                    <div className="text-left w-full overflow-hidden">
                                        <div className={`font-medium truncate flex items-center gap-2 ${activePersona.name === c.name ? 'text-white' : 'text-slate-300'}`}>
                                            {c.name}
                                            {participatingAgents.includes(c.name) && (
                                                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" title="Active in Session" />
                                            )}
                                        </div>
                                        <div className="text-xs text-slate-500 truncate">{c.role}</div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* BOTTOM CONTROLS */}
                <div className="p-4 border-t border-slate-800">
                    <div className="flex items-center justify-between p-3 bg-slate-900 rounded-lg border border-slate-800 mb-4">
                        <div className="flex items-center gap-2">
                            <Terminal size={16} className={factoryMode ? 'text-green-400' : 'text-slate-500'} />
                            <span className="text-sm font-medium">Factory Mode</span>
                        </div>
                        <button
                            onClick={() => setFactoryMode(!factoryMode)}
                            className={`w-10 h-5 rounded-full transition-colors relative ${factoryMode ? 'bg-green-500' : 'bg-slate-700'}`}
                        >
                            <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${factoryMode ? 'left-6' : 'left-1'}`} />
                        </button>
                    </div>
                    <Link href="/growth" className="block w-full text-center py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-300 transition-colors">
                        &larr; Back to Dashboard
                    </Link>
                </div>
            </div>

            {/* MAIN CHAT AREA */}
            <div className="flex-1 flex flex-col bg-[url('/grid.svg')] bg-repeat opacity-95 relative z-10">

                {/* HEADER */}
                <div className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md flex items-center px-6 justify-between sticky top-0 z-10">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${activePersona.color} bg-current animate-pulse`} />
                            <span className="font-semibold text-lg">{activePersona.name}</span>
                            <span className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">{activePersona.role}</span>
                        </div>

                        {participatingAgents.length > 0 && (
                            <div className="flex items-center gap-2 pl-6 border-l border-slate-800">
                                <div className="flex -space-x-2">
                                    {participatingAgents.slice(0, 3).map((agent, i) => {
                                        const p = COUNCIL.find(c => c.name === agent);
                                        return (
                                            <div key={i} className={`w-6 h-6 rounded-full border-2 border-slate-950 bg-slate-800 flex items-center justify-center ${p?.color || 'text-slate-500'}`} title={agent}>
                                                {p?.icon ? <p.icon size={12} /> : agent[0]}
                                            </div>
                                        );
                                    })}
                                    {participatingAgents.length > 3 && (
                                        <div className="w-6 h-6 rounded-full border-2 border-slate-950 bg-slate-800 flex items-center justify-center text-[8px] font-bold text-slate-400">
                                            +{participatingAgents.length - 3}
                                        </div>
                                    )}
                                </div>
                                <span className="text-xs text-slate-500 font-medium">
                                    {participatingAgents.length} Active
                                </span>
                            </div>
                        )}
                    </div>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={async () => {
                                const name = prompt("Name this mission (e.g., 'Dental-Campaign-v1'):");
                                if (!name) return;
                                try {
                                    const res = await fetch('/api/strategy/save', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ messages, sessionName: name })
                                    });
                                    const data = await res.json();
                                    if (data.success) {
                                        alert(`Mission Saved to intelligence/missions/${data.filename}`);
                                    } else {
                                        alert(`Save Failed: ${data.error}`);
                                    }
                                } catch (e: any) {
                                    alert(`Error: ${e.message}`);
                                }
                            }}
                            disabled={messages.length === 0}
                            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded text-slate-300 text-xs font-bold border border-slate-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                        >
                            <FolderOpen size={14} /> SAVE
                        </button>

                        <button
                            onClick={() => {
                                if (confirm("Clear chat history?")) setMessages([]);
                            }}
                            disabled={messages.length === 0}
                            className="px-3 py-1.5 bg-slate-800 hover:bg-red-900/50 rounded text-slate-300 hover:text-red-200 text-xs font-bold border border-slate-700 hover:border-red-800 transition-colors disabled:opacity-50 flex items-center gap-2"
                        >
                            <Trash2 size={14} /> CLEAR
                        </button>

                        <Link href="/growth" className="px-4 py-2 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 rounded text-white text-xs font-bold shadow-lg shadow-red-900/50 flex items-center gap-2 transition-all ml-4">
                            🚀 DEPLOY HUNTER
                        </Link>
                    </div>
                </div>

                {/* MESSAGES */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-slate-600 opacity-50">
                            <activePersona.icon size={64} className="mb-4 text-slate-700" />
                            <p className="text-lg font-medium">Select a Council Member.</p>
                            <p className="text-sm mt-2 max-w-md text-center">Switching personas preserves context, allowing for a multi-agent roundtable discussion.</p>
                            {factoryMode && <p className="text-xs font-mono text-green-500 mt-4">[[FACTORY MODE ACTIVE]]</p>}
                        </div>
                    )}

                    {messages.map((m, i) => (
                        <div key={i} className={`flex gap-4 max-w-4xl mx-auto ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {m.role === 'assistant' && (
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 bg-slate-800 border border-slate-700`}>
                                    <Bot size={16} className="text-slate-400" />
                                </div>
                            )}

                            <div className={`rounded-2xl p-4 shadow-xl border max-w-[80%] group relative ${m.role === 'user'
                                ? 'bg-blue-600 text-white border-blue-500 rounded-tr-sm'
                                : 'bg-slate-900 border-slate-800 text-slate-200 rounded-tl-sm'
                                }`}>
                                {/* Persona Label for Assistant */}
                                {m.role === 'assistant' && m.persona && (
                                    <div className="text-xs font-bold text-slate-500 mb-2 uppercase tracking-wide flex items-center justify-between">
                                        <span>{m.persona}</span>
                                        <button className="hover:text-white" title="Copy"><FileJson size={12} /></button>
                                    </div>
                                )}

                                {/* Edit Mode for User Messages */}
                                {m.role === 'user' && editingIndex === i ? (
                                    <div className="flex flex-col gap-2">
                                        <textarea
                                            value={editContent}
                                            onChange={(e) => setEditContent(e.target.value)}
                                            className="w-full bg-blue-700 border border-blue-400 rounded p-2 text-white text-sm resize-none min-h-[60px] focus:outline-none"
                                            autoFocus
                                        />
                                        <div className="flex gap-2 justify-end">
                                            <button
                                                onClick={() => {
                                                    const updated = [...messages];
                                                    updated[i].content = editContent;
                                                    setMessages(updated);
                                                    setEditingIndex(null);
                                                }}
                                                className="p-1.5 bg-green-500 hover:bg-green-400 rounded text-white"
                                                title="Save"
                                            >
                                                <Check size={14} />
                                            </button>
                                            <button
                                                onClick={() => setEditingIndex(null)}
                                                className="p-1.5 bg-red-500 hover:bg-red-400 rounded text-white"
                                                title="Cancel"
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="prose prose-invert prose-sm whitespace-pre-wrap font-sans leading-relaxed">
                                        {m.content}
                                    </div>
                                )}

                                {/* Edit Button (User Only) */}
                                {m.role === 'user' && editingIndex !== i && (
                                    <button
                                        onClick={() => {
                                            setEditingIndex(i);
                                            setEditContent(m.content);
                                        }}
                                        className="absolute -left-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1.5 bg-slate-700 hover:bg-slate-600 rounded text-slate-300 transition-opacity"
                                        title="Edit"
                                    >
                                        <Pencil size={12} />
                                    </button>
                                )}
                            </div>

                            {m.role === 'user' && (
                                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0 mt-1">
                                    <User size={16} className="text-slate-300" />
                                </div>
                            )}
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* INPUT */}
                <div className="p-6 bg-slate-950 border-t border-slate-800">
                    <div className="max-w-4xl mx-auto relative">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder={`Ask ${activePersona.name} about ${activePersona.desc.toLowerCase()}...`}
                            className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 pr-14 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none min-h-[60px] shadow-inner font-mono text-sm"
                        />
                        <button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="absolute right-3 bottom-3 p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send size={18} />}
                        </button>
                    </div>
                    <div className="max-w-4xl mx-auto mt-2 text-center">
                        <p className="text-[10px] text-slate-600">
                            POWERED BY OLLAMA (RTX 5080) • ZERO LATENCY • FACTORY PROTOCOL v2.1
                        </p>
                    </div>
                </div>

            </div>
        </div>
    );
}
