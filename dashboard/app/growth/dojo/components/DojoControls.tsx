'use client';
import React, { useState, useEffect } from 'react';

interface Props {
    onRun: () => void;
    isRunning: boolean;
    replayMode: boolean;
    setReplayMode: (v: boolean) => void;
    agentId: string;
    setAgentId: (v: string) => void;
    scenarioId: string;
    setScenarioId: (v: string) => void;
}

interface ScenarioOption {
    id: string; // Full path
    name: string;
    group: string;
}

export default function DojoControls({
    onRun, isRunning, replayMode, setReplayMode,
    agentId, setAgentId, scenarioId, setScenarioId
}: Props) {
    const [scenarios, setScenarios] = useState<ScenarioOption[]>([]);

    useEffect(() => {
        fetch('/api/dojo/scenarios')
            .then(res => res.json())
            .then(data => {
                if (data.scenarios) {
                    setScenarios(data.scenarios);
                }
            })
            .catch(console.error);
    }, []);

    // Group scenarios by 'group' field
    const groups: Record<string, ScenarioOption[]> = {};
    scenarios.forEach(s => {
        if (!groups[s.group]) groups[s.group] = [];
        groups[s.group].push(s);
    });

    return (
        <div className="flex items-center gap-4 p-4 bg-gray-800 border-b border-gray-700 sticky top-0 z-10">
            <div className="text-xl font-bold text-white tracking-widest">DOJO</div>

            <select
                value={agentId}
                onChange={e => setAgentId(e.target.value)}
                className="bg-gray-700 text-white rounded px-3 py-1 border border-gray-600 max-w-[200px]"
            >
                <option value="knowles_law_firm">Knowles Law Firm (James)</option>
                <option value="test_build_studio_client">Test Studio Client</option>
            </select>

            <select
                value={scenarioId}
                onChange={e => setScenarioId(e.target.value)}
                className="bg-gray-700 text-white rounded px-3 py-1 border border-gray-600 max-w-[300px]"
            >
                <option value="">Select Scenario...</option>
                {/* Default/Fallback Hardcoded just in case API fails or loading */}
                {!scenarios.length && (
                    <>
                        <option value="tools/evaluation/dojo/scenarios/legal_intake/basic_intake.json">Legal Intake (Basic)</option>
                        <option value="tools/evaluation/dojo/scenarios/legal_intake/level3_adversarial.json">Level 3 (Adversarial)</option>
                    </>
                )}

                {Object.entries(groups).map(([groupName, options]) => (
                    <optgroup key={groupName} label={groupName.replace(/_/g, ' ').toUpperCase()}>
                        {options.map(opt => (
                            <option key={opt.id} value={opt.id}>
                                {opt.name.replace(/_/g, ' ')}
                            </option>
                        ))}
                    </optgroup>
                ))}
            </select>

            <div className="h-6 w-px bg-gray-600 mx-2"></div>

            <button
                onClick={onRun}
                disabled={isRunning}
                className={`px-6 py-1 rounded font-bold uppercase transition-all ${isRunning
                    ? 'bg-gray-600 cursor-not-allowed opacity-50'
                    : 'bg-green-600 hover:bg-green-500 text-white shadow-[0_0_15px_rgba(34,197,94,0.5)]'
                    }`}
            >
                {isRunning ? 'Running...' : 'FIGHT'}
            </button>

            <label className="flex items-center gap-2 cursor-pointer ml-auto text-gray-400 text-sm">
                <input
                    type="checkbox"
                    checked={replayMode}
                    onChange={e => setReplayMode(e.target.checked)}
                    className="form-checkbox bg-gray-700 border-gray-600 text-green-500 rounded"
                />
                <span>Replay Mode</span>
            </label>
        </div>
    );
}
