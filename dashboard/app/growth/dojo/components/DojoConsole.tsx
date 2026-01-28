'use client';
import React, { useEffect, useRef } from 'react';

// Props: transcript string
export default function DojoConsole({ transcript }: { transcript: string }) {
    const bottomRef = useRef<HTMLDivElement>(null);

    // Extract Metadata from first few lines
    const getMeta = (key: string) => {
        const regex = new RegExp(`${key}: (.*)`);
        const match = transcript.match(regex);
        return match ? match[1] : null;
    };

    const scenarioPath = getMeta('Scenario Path');
    const topics = getMeta('Topics');
    const role = getMeta('Opponent Role');

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcript]);

    return (
        <div className="bg-gray-900 text-green-400 font-mono rounded-lg h-full flex flex-col border border-gray-700 shadow-inner relative">
            {/* Metadata Header */}
            {(scenarioPath || role) && (
                <div className="bg-gray-800 p-2 text-xs border-b border-gray-700 text-gray-400 flex flex-col gap-1 sticky top-0 z-10 opacity-90 backdrop-blur">
                    {scenarioPath && <div><span className="font-bold text-gray-300">PATH:</span> {scenarioPath}</div>}
                    {role && <div><span className="font-bold text-gray-300">ROLE:</span> {role}</div>}
                    {topics && <div><span className="font-bold text-gray-300">TAGS:</span> {topics}</div>}
                </div>
            )}

            <div className="p-4 overflow-y-auto flex-1">
                <pre className="whitespace-pre-wrap text-sm">{transcript || "Waiting for simulation..."}</pre>
                <div ref={bottomRef} />
            </div>
        </div>
    );
}
