"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

export default function DemoAgentPage() {
    const params = useParams();
    const slug = params.slug as string;

    // Formatting the slug for display (e.g. veterinary_clinic -> Veterinary Clinic)
    const agentName = slug.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

    const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string }[]>([
        { role: 'assistant', content: `Hello! I am your AI Assistant for ${agentName}. How can I help you today?` }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg, slug })
            });
            const data = await res.json();

            if (data.reply) {
                setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: "⚠️ Error: " + (data.error || "Unknown error") }]);
            }
        } catch (e: any) {
            setMessages(prev => [...prev, { role: 'assistant', content: "⚠️ Network Error: " + e.message }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
                <div className="flex items-center gap-4">
                    <Link href="/growth" className="text-slate-400 hover:text-slate-600 font-bold text-xs uppercase tracking-wider">
                        ← Back to Factory
                    </Link>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
                        {agentName} <span className="text-slate-400 text-sm font-normal">(Demo Mode)</span>
                    </h1>
                </div>
                <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-xs font-bold text-slate-500 uppercase">Live (Local)</span>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 max-w-4xl w-full mx-auto p-6 overflow-y-auto">
                <div className="space-y-6">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] p-4 rounded-xl shadow-sm text-sm ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-none'
                                    : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'
                                }`}>
                                <div className="font-bold text-xs mb-1 opacity-70 uppercase tracking-wider">
                                    {msg.role === 'user' ? 'You' : 'AI Agent'}
                                </div>
                                <div className="leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-white border border-slate-200 p-4 rounded-xl rounded-bl-none shadow-sm flex items-center gap-2">
                                <span className="h-2 w-2 bg-slate-400 rounded-full animate-bounce"></span>
                                <span className="h-2 w-2 bg-slate-400 rounded-full animate-bounce delay-100"></span>
                                <span className="h-2 w-2 bg-slate-400 rounded-full animate-bounce delay-200"></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-slate-200 p-6">
                <div className="max-w-4xl mx-auto relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Type a message to test the agent..."
                        className="w-full pl-6 pr-32 py-4 bg-slate-50 border border-slate-200 rounded-full text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all shadow-inner"
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className={`absolute right-2 top-2 bottom-2 px-6 rounded-full font-bold text-xs uppercase tracking-wider transition-all ${input.trim()
                                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:shadow-xl hover:scale-105'
                                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            }`}
                    >
                        Send
                    </button>
                </div>
                <div className="text-center mt-3 text-xs text-slate-400">
                    Powered by local Llama 3 • Zero Cost Architecture
                </div>
            </div>
        </div>
    );
}
