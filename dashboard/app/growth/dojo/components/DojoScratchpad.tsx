'use client';
import React, { useState, useEffect } from 'react';

interface Props {
    snapshots: { system_prompt: string | null; persona_context: string | null };
    onChange: (sys: string, persona: string) => void;
}

export default function DojoScratchpad({ snapshots, onChange }: Props) {
    const [activeTab, setActiveTab] = useState<'system' | 'persona'>('system');
    const [sys, setSys] = useState(snapshots.system_prompt || '');
    const [persona, setPersona] = useState(snapshots.persona_context || '');

    // Update internal state if snapshots change (e.g. on run complete)
    useEffect(() => {
        if (snapshots.system_prompt) setSys(snapshots.system_prompt);
        if (snapshots.persona_context) setPersona(snapshots.persona_context);
    }, [snapshots]);

    // Propagate changes
    useEffect(() => {
        onChange(sys, persona);
    }, [sys, persona, onChange]);

    return (
        <div className="flex flex-col h-full bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
            <div className="flex border-b border-gray-700 bg-gray-800">
                <button
                    onClick={() => setActiveTab('system')}
                    className={`px-4 py-2 text-sm font-bold ${activeTab === 'system' ? 'text-white bg-gray-700' : 'text-gray-400 hover:text-white'}`}
                >
                    System Prompt
                </button>
                <button
                    onClick={() => setActiveTab('persona')}
                    className={`px-4 py-2 text-sm font-bold ${activeTab === 'persona' ? 'text-white bg-gray-700' : 'text-gray-400 hover:text-white'}`}
                >
                    Persona Context
                </button>
                <div className="ml-auto px-4 py-2 text-xs text-yellow-500 flex items-center">
                    <span>⚠️ Scratchpad Mode</span>
                </div>
            </div>

            <div className="flex-1 relative">
                {activeTab === 'system' ? (
                    <textarea
                        className="w-full h-full bg-gray-900 text-gray-300 p-4 font-mono text-xs focus:outline-none resize-none"
                        value={sys}
                        onChange={e => setSys(e.target.value)}
                        spellCheck={false}
                    />
                ) : (
                    <textarea
                        className="w-full h-full bg-gray-900 text-gray-300 p-4 font-mono text-xs focus:outline-none resize-none"
                        value={persona}
                        onChange={e => setPersona(e.target.value)}
                        spellCheck={false}
                    />
                )}
            </div>
        </div>
    );
}
