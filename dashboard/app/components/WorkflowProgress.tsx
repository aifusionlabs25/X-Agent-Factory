'use client';

import { useState, useEffect, useCallback } from 'react';

interface WorkflowProgressProps {
    runId: string | null;
    onComplete?: (success: boolean) => void;
}

interface ProgressData {
    percentage: number;
    completedSteps: number;
    totalSteps: number;
    currentStep: string;
}

interface RunData {
    id: number;
    status: string;
    conclusion: string | null;
    html_url: string;
}

export default function WorkflowProgress({ runId, onComplete }: WorkflowProgressProps) {
    const [progress, setProgress] = useState<ProgressData | null>(null);
    const [run, setRun] = useState<RunData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isPolling, setIsPolling] = useState(false);

    const fetchStatus = useCallback(async () => {
        if (!runId) return;

        try {
            const response = await fetch(`/api/workflow-status?run_id=${runId}`);
            const data = await response.json();

            if (data.success) {
                setRun(data.run);
                setProgress(data.progress);
                setError(null);

                // Check if workflow is complete
                if (data.run.status === 'completed') {
                    setIsPolling(false);
                    if (onComplete) {
                        onComplete(data.run.conclusion === 'success');
                    }
                }
            } else {
                setError(data.error);
            }
        } catch (e: any) {
            setError(e.message);
        }
    }, [runId, onComplete]);

    useEffect(() => {
        if (!runId) return;

        setIsPolling(true);
        fetchStatus();

        // Poll every 3 seconds
        const interval = setInterval(fetchStatus, 3000);

        return () => {
            clearInterval(interval);
            setIsPolling(false);
        };
    }, [runId, fetchStatus]);

    if (!runId) return null;

    const getStatusColor = () => {
        if (!run) return 'bg-gray-600';
        if (run.status === 'completed') {
            return run.conclusion === 'success' ? 'bg-green-500' : 'bg-red-500';
        }
        return 'bg-blue-500';
    };

    const getStatusIcon = () => {
        if (!run) return '⏳';
        if (run.status === 'completed') {
            return run.conclusion === 'success' ? '✅' : '❌';
        }
        if (run.status === 'in_progress') return '🔄';
        return '⏳';
    };

    return (
        <div className="mt-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <span className="text-lg">{getStatusIcon()}</span>
                    <span className="text-sm font-medium text-slate-200">
                        {run?.status === 'completed'
                            ? (run.conclusion === 'success' ? 'Pipeline Complete' : 'Pipeline Failed')
                            : 'Pipeline Running...'
                        }
                    </span>
                </div>
                {run?.html_url && (
                    <a
                        href={run.html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300"
                    >
                        View on GitHub →
                    </a>
                )}
            </div>

            {/* Progress Bar */}
            <div className="relative h-3 bg-slate-700 rounded-full overflow-hidden mb-2">
                <div
                    className={`absolute top-0 left-0 h-full transition-all duration-500 ${getStatusColor()}`}
                    style={{ width: `${progress?.percentage || 0}%` }}
                />
                {isPolling && run?.status !== 'completed' && (
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
                )}
            </div>

            {/* Progress Details */}
            <div className="flex justify-between text-xs text-slate-400">
                <span>
                    {progress?.currentStep || 'Initializing...'}
                </span>
                <span>
                    {progress?.completedSteps || 0}/{progress?.totalSteps || '?'} steps • {progress?.percentage || 0}%
                </span>
            </div>

            {error && (
                <div className="mt-2 text-xs text-red-400">
                    Error: {error}
                </div>
            )}
        </div>
    );
}
