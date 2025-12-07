"use client";

import React, { useState } from 'react';

export default function AgentSidebar() {
    const [isActive, setIsActive] = useState(false);

    return (
        <aside className="fixed top-0 right-0 h-screen w-[500px] bg-slate-900 border-l border-slate-800 flex flex-col shadow-2xl z-50">
            {/* Header / Agent Status */}
            <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className="text-white font-mono font-bold">AVA [VETERINARY]</span>
                </div>
                <button
                    onClick={() => setIsActive(!isActive)}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-xs uppercase font-bold text-white rounded"
                >
                    {isActive ? 'Disconnect' : 'Connect'}
                </button>
            </div>

            {/* Video Feed Placeholder (Tavus Embed) */}
            <div className="flex-1 bg-black relative flex items-center justify-center overflow-hidden">
                {isActive ? (
                    <div className="text-center">
                        {/* Mock Video Feed */}
                        <div className="w-32 h-32 bg-slate-800 rounded-full mx-auto mb-4 animate-pulse flex items-center justify-center">
                            <span className="text-4xl">🤖</span>
                        </div>
                        <p className="text-green-400 font-mono text-sm">VOICE STREAM ACTIVE</p>
                    </div>
                ) : (
                    <div className="text-slate-500 font-mono text-sm">
                        [SIGNAL LOST]<br />waiting for connection...
                    </div>
                )}

                {/* Overlay UI (always on top of video) */}
                <div className="absolute bottom-10 left-0 right-0 p-6">
                    <div className="bg-black/50 backdrop-blur-md border border-white/10 p-4 rounded-xl text-white text-sm">
                        <p><strong>Ava:</strong> "Hello! I understand you're concerned. Is your pet breathing normally?"</p>
                    </div>
                </div>
            </div>

            {/* Controls / Debug */}
            <div className="p-4 bg-slate-950 border-t border-slate-800">
                <div className="grid grid-cols-2 gap-2">
                    <button className="p-2 bg-slate-800 text-slate-400 hover:text-white text-xs rounded">Mute Mic</button>
                    <button className="p-2 bg-slate-800 text-slate-400 hover:text-white text-xs rounded">Debug Mode</button>
                </div>
            </div>
        </aside>
    );
}
