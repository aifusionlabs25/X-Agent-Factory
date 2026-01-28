import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { agent_id, scenario_id, turns, scratchpad_sys, scratchpad_persona } = body;

        if (!agent_id || !scenario_id) {
            return NextResponse.json({ error: 'Missing agent_id or scenario_id' }, { status: 400 });
        }

        // Generate Run ID Deterministically
        // We do this BEFORE spawning so we can return it immediately.
        // Logic matches dojo_runner: YYYYMMDD_HHMMSS_<scenario_suffix>
        // Extract scenario suffix
        const scenarioName = path.basename(scenario_id, '.json');
        // Sanitize timestamp to avoid collision if run twice same second? Add ms?
        // dojo_runner used HHMMSS. Let's stick to it but maybe check collision?
        // Actually, dojo_runner uses `datetime.now()` inside. If we pass `--run_id`, we control it.

        const now = new Date();
        const timestamp = now.toISOString().replace(/[-:T]/g, '').slice(0, 14); // YYYYMMDDHHMMSS
        // Add seconds? ISO: 2026-01-23T18:00:00.000Z -> 20260123180000
        // Slice(0,15)? 
        // Format: YYYYMMDD_HHMMSS

        // Manual format to match python exactly
        const pad = (n: number) => n.toString().padStart(2, '0');
        const yyyy = now.getFullYear();
        const mm = pad(now.getMonth() + 1);
        const dd = pad(now.getDate());
        const hh = pad(now.getHours());
        const min = pad(now.getMinutes());
        const ss = pad(now.getSeconds());
        const ts = `${yyyy}${mm}${dd}_${hh}${min}${ss}`;

        const runId = `${ts}_${scenarioName}`;

        // Construct Python Command
        const runnerPath = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_runner.py');
        const pythonArgs = [runnerPath, agent_id, scenario_id, '--turns', (turns || 10).toString(), '--run_id', runId];

        // Handle Scratchpad
        if (scratchpad_sys) {
            const tempDir = path.join(FACTORY_ROOT, 'dashboard', 'temp');
            if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });
            const scratchSysPath = path.join(tempDir, `temp_sys_${runId}.txt`);
            fs.writeFileSync(scratchSysPath, scratchpad_sys);
            pythonArgs.push('--scratchpad_sys', scratchSysPath);
        }

        if (scratchpad_persona) {
            const tempDir = path.join(FACTORY_ROOT, 'dashboard', 'temp');
            if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });
            const scratchPersonaPath = path.join(tempDir, `temp_persona_${runId}.txt`);
            fs.writeFileSync(scratchPersonaPath, scratchpad_persona);
            pythonArgs.push('--scratchpad_persona', scratchPersonaPath);
        }

        console.log('[DOJO API] Spawning (Async):', 'python', pythonArgs.join(' '));
        console.log('[DOJO API] Scenario Path:', scenario_id);

        // Spawn Python Process (Detached / Unref)
        const child = spawn('python', pythonArgs, {
            cwd: FACTORY_ROOT,
            detached: true, // Allow running independently?
            stdio: 'ignore' // Ignore IO so we don't hang? Or piped?
            // If we want stdout for debug, we can pipe to a file logic or just let file logging handle it.
            // We implemented file logging in dojo_runner. So we can ignore stdout here.
        });

        child.unref(); // Don't wait for child to exit

        // IMPORTANT: Wait a tiny bit to ensure file creation? 
        // dojo_runner writes header immediately.
        // Child process startup might take 100-500ms.
        // If we return immediately, Frontend polling might 404 once or twice.
        // That's fine, `stream` route can handle retries or Frontend retry logic.
        // But `DojoConsole` needs to be robust. 
        // And `FindLogFile` logic... we know the path!
        // We can return `log_path` constructed here.

        const logPathGuess = path.join('tools', 'evaluation', 'dojo', 'dojo_logs', agent_id, `${runId}.txt`);

        return NextResponse.json({ success: true, run_id: runId, log_path: logPathGuess });

    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
