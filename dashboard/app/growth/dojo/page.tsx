'use client';

import React, { useState, useEffect, useRef } from 'react';
import DojoControls from './components/DojoControls';
import DojoConsole from './components/DojoConsole';
import DojoMaster from './components/DojoMaster';
import DojoScratchpad from './components/DojoScratchpad';

export default function DojoPage() {
    const [isRunning, setIsRunning] = useState(false);
    const [replayMode, setReplayMode] = useState(false);

    const [agentId, setAgentId] = useState('knowles_law_firm');
    const [scenarioId, setScenarioId] = useState('tools/evaluation/dojo/scenarios/legal_intake/basic_intake.json');

    const [runId, setRunId] = useState<string | null>(null);
    const [transcript, setTranscript] = useState('');
    const [score, setScore] = useState<any>(null);
    const [snapshots, setSnapshots] = useState<any>({});

    const [scratchSys, setScratchSys] = useState('');
    const [scratchPersona, setScratchPersona] = useState('');

    const [runs, setRuns] = useState<any[]>([]);
    const [promoting, setPromoting] = useState(false);

    // Load Runs Helper
    const loadRuns = async () => {
        try {
            const res = await fetch('/api/dojo/runs');
            const data = await res.json();
            if (data.runs) setRuns(data.runs);
        } catch (e) {
            console.error('Failed to load runs');
        }
    };

    // Initial Load
    useEffect(() => { loadRuns(); }, []);

    // Run Handler
    const handleRun = async () => {
        if (isRunning) return;
        setIsRunning(true);
        setTranscript('Initializing simulation...');
        setScore(null);

        try {
            if (replayMode) {
                setTranscript('Replay Mode: Select a run from history to replay.');
                setIsRunning(false);
                return;
            }

            const res = await fetch('/api/dojo/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent_id: agentId,
                    scenario_id: scenarioId,
                    turns: 10,
                    scratchpad_sys: scratchSys || undefined,
                    scratchpad_persona: scratchPersona || undefined
                })
            });

            const data = await res.json();
            if (data.success) {
                setRunId(data.run_id);
                // Start Stream
                startStream(data.run_id);
            } else {
                setTranscript(`Error: ${data.error}\n${data.stderr || ''}`);
                setIsRunning(false);
            }
        } catch (e) {
            setTranscript('Request failed.');
            setIsRunning(false);
        }
    };

    const startStream = (id: string) => {
        const eventSource = new EventSource(`/api/dojo/runs/${id}/stream`);

        eventSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.chunk) {
                setTranscript(prev => prev + data.chunk);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            setIsRunning(false);
            // Refresh details to get score
            loadRunDetails(id);
            loadRuns(); // Refresh history
        };

        eventSource.addEventListener('close', () => {
            eventSource.close();
            setIsRunning(false);
            loadRunDetails(id);
            loadRuns();
        });
    };

    const loadRunDetails = async (id: string) => {
        const res = await fetch(`/api/dojo/runs/${id}`);
        const data = await res.json();
        if (data.transcript) {
            setTranscript(data.transcript);
            setScore(data.score);
            setSnapshots(data.snapshots || {});
        }
    };

    const handleHistoryClick = (id: string) => {
        setRunId(id);
        loadRunDetails(id);
    };

    const handlePromote = async () => {
        if (!runId) return;
        setPromoting(true);
        try {
            const res = await fetch(`/api/dojo/runs/${runId}/promote`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: agentId })
            });
            const data = await res.json();
            if (data.success) {
                alert('Promoted Successfully!');
            } else {
                alert(`Promotion Failed: ${data.error}\n${data.output}`);
            }
        } catch (e) {
            alert('Promotion Error');
        }
        setPromoting(false);
    };

    return (
        <div className="flex flex-col h-screen bg-gray-950 text-white overflow-hidden">
            <DojoControls
                onRun={handleRun}
                isRunning={isRunning}
                replayMode={replayMode}
                setReplayMode={setReplayMode}
                agentId={agentId} setAgentId={setAgentId}
                scenarioId={scenarioId} setScenarioId={setScenarioId}
            />

            <div className="flex flex-1 overflow-hidden">
                {/* LEFT: History */}
                <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
                    <div className="p-4 font-bold text-gray-500 text-xs uppercase tracking-wider">Recent Matches</div>
                    <div className="flex-1 overflow-y-auto">
                        {runs.map(r => (
                            <div
                                key={r.run_id}
                                onClick={() => handleHistoryClick(r.run_id)}
                                className={`p-3 border-b border-gray-800 cursor-pointer hover:bg-gray-800 ${runId === r.run_id ? 'bg-gray-800 border-l-4 border-green-500' : ''}`}
                            >
                                <div className="flex justify-between items-center mb-1">
                                    <span className={`text-xs font-bold px-1 rounded ${r.verdict.includes('PASS') ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-500'}`}>
                                        {r.verdict === 'PASS' ? 'PASS' : 'FAIL'}
                                    </span>
                                    <span className="text-xs text-gray-500 font-mono">{r.score}</span>
                                </div>
                                <div className="text-xs text-gray-400 truncate">{r.run_id}</div>
                                <div className="text-[10px] text-gray-600">{new Date(r.timestamp).toLocaleString()}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* CENTER: Console */}
                <div className="flex-1 flex flex-col p-4 gap-4 max-w-4xl mx-auto w-full overflow-hidden">
                    <div className="flex-[2] min-h-0">
                        <DojoConsole transcript={transcript} />
                    </div>

                    {/* Scratchpad (Bottom Half) */}
                    <div className="flex-1 min-h-[200px] min-w-0">
                        <DojoScratchpad
                            snapshots={snapshots}
                            onChange={(s, p) => { setScratchSys(s); setScratchPersona(p); }}
                        />
                    </div>
                </div>

                {/* RIGHT: Master */}
                <div className="w-80 bg-gray-900 border-l border-gray-800 p-4">
                    <DojoMaster
                        runId={runId}
                        score={score}
                        snapshots={snapshots}
                        onPromote={handlePromote}
                        promoting={promoting}
                        onPatchApplied={(sys: string) => {
                            setScratchSys(sys);
                            setSnapshots((prev: any) => ({ ...prev, system_prompt: sys }));
                        }}
                    />
                </div>
            </div>
        </div>
    );
}
