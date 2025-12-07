"use client";

import React, { useState } from 'react';

export default function DemoPage() {
    const [url, setUrl] = useState('https://example.com');
    const [targetUrl, setTargetUrl] = useState('https://example.com');

    const handleGo = () => {
        let finalUrl = url;
        if (!finalUrl.startsWith('http')) {
            finalUrl = 'https://' + finalUrl;
        }
        setTargetUrl(finalUrl);
    };

    return (
        <div className="h-screen flex flex-col bg-gray-100">
            {/* Demo Controls */}
            <div className="bg-white border-b p-4 flex gap-4 items-center">
                <span className="font-bold text-slate-700">🖥️ INTERACTIVE DEMO MODE</span>
                <div className="flex-1 flex gap-2">
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        className="flex-1 border border-gray-300 rounded px-3 py-1 text-sm font-mono"
                    />
                    <button
                        onClick={handleGo}
                        className="bg-blue-600 text-white px-4 py-1 rounded text-sm font-bold hover:bg-blue-700"
                    >
                        LOAD URL
                    </button>
                </div>
            </div>

            {/* Iframe Area (Scaled) */}
            <div className="flex-1 overflow-hidden relative bg-gray-200 flex items-center justify-center p-8">

                {/* Device Frame */}
                <div className="w-full h-full max-w-6xl bg-white shadow-2xl rounded-lg overflow-hidden border border-gray-300 relative">
                    {/* Iframe with Scaling as per Protocol v2.0 (0.55 scale fix) */}
                    <div className="w-[181%] h-[181%] origin-top-left transform scale-[0.55]">
                        <iframe
                            src={targetUrl}
                            className="w-full h-full border-none"
                            sandbox="allow-scripts allow-same-origin allow-forms"
                        />
                    </div>

                    {/* Pointer Overlay (Visual Effect) */}
                    <div className="absolute top-10 right-10 pointer-events-none">
                        <div className="bg-red-500/20 w-12 h-12 rounded-full animate-ping"></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
