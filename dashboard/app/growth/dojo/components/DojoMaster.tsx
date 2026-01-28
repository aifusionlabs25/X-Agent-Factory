'use client';
import React, { useState } from 'react';

interface Props {
    runId: string | null;
    score: any;
    snapshots: any;
    onPromote: () => void;
    promoting: boolean;
    onPatchApplied?: (sys: string) => void;
}

export default function DojoMaster({ runId, score, snapshots, onPromote, promoting, onPatchApplied }: Props) {
    const [fixing, setFixing] = useState(false);

    if (!runId) return (
        <div className="bg-gray-800 p-6 rounded-lg text-center text-gray-500 border border-gray-700 h-full flex flex-col justify-center items-center">
            <div className="text-4xl mb-4">🥋</div>
            <div>Ready for Simulation</div>
        </div>
    );

    const verdict = score?.verdict || 'PENDING';
    const points = score?.score; // Can be null

    const isPass = verdict.includes('PASS');
    const isInvalid = verdict.includes('MISMATCH') || verdict.includes('INVALID') || points === null;

    // Show Auto-Fix ONLY if valid FAIL or valid <100 PASS
    // If Invalid (Mismatch), do NOT show Auto-Fix (Troy cannot fix scope).
    const canFix = !isInvalid && (!isPass || (points !== null && points < 100));

    // Color logic
    let verdictColor = 'text-red-500';
    if (isPass) verdictColor = 'text-green-400';
    if (isInvalid) verdictColor = 'text-amber-500'; // Orange for Warn/Invalid

    const handleAutoFix = async () => {
        if (!runId) return;
        setFixing(true);
        try {
            const res = await fetch('/api/dojo/grandmaster', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ run_id: runId })
            });
            const data = await res.json();

            if (data.success) {
                if (onPatchApplied) onPatchApplied(data.patched_system_prompt);
                alert(`Troy Fix Applied!\n${data.message}`);
            } else {
                alert(`Troy Failed:\n${data.message || data.error}\n${data.log || ''}`);
            }
        } catch (e) {
            alert('Auto-Fix Error');
        }
        setFixing(false);
    };

    return (
        <div className="bg-gray-800 p-4 rounded-lg flex flex-col h-full border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">RUN ID: {runId}</div>

            <div className="flex items-center justify-between mb-6">
                <div className={`text-3xl font-black break-words leading-tight max-w-[180px] ${verdictColor}`}>
                    {verdict}
                </div>
                <div className="text-right">
                    <div className="text-5xl font-mono text-white">{points !== null ? points : 'N/A'}</div>
                    <div className="text-xs text-gray-500 uppercase tracking-widest">Score</div>
                </div>
            </div>

            {score?.breakdown && (
                <div className="flex-1 overflow-y-auto mb-4 bg-gray-900 p-3 rounded">
                    <div className="text-xs text-gray-400 mb-2 uppercase font-bold">Breakdown</div>
                    {Object.entries(score.breakdown).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-sm py-1 border-b border-gray-800">
                            <span className="text-gray-300">{k}</span>
                            <span className={String(v).includes('FAIL') || String(v).includes('true') ? 'text-red-400 font-bold' : 'text-gray-500'}>
                                {JSON.stringify(v)}
                            </span>
                        </div>
                    ))}
                </div>
            )}

            <div className="mt-auto grid grid-cols-2 gap-2">
                <button
                    onClick={handleAutoFix}
                    disabled={!canFix || fixing}
                    className={`col-span-2 flex items-center justify-center py-2 rounded text-sm font-bold uppercase transition-colors mb-2 ${!canFix || fixing
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed hidden'
                        : 'bg-amber-600 hover:bg-amber-500 text-white shadow-[0_0_10px_rgba(245,158,11,0.3)]'
                        }`}
                >
                    {fixing ? 'Troy Architect Working...' : '✨ Auto-Fix (Troy)'}
                </button>

                <a
                    href={`/api/dojo/runs/${runId}/export`}
                    target="_blank"
                    className="flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white py-2 rounded text-sm font-bold uppercase transition-colors"
                >
                    Export Winner
                </a>

                <button
                    onClick={onPromote}
                    disabled={!isPass || promoting}
                    className={`flex items-center justify-center py-2 rounded text-sm font-bold uppercase transition-colors ${!isPass || promoting
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'bg-purple-600 hover:bg-purple-500 text-white'
                        }`}
                >
                    {promoting ? 'Promoting...' : 'Promote'}
                </button>
            </div>
        </div>
    );
}
