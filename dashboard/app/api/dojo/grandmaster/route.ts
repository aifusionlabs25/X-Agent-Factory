import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');
const LOGS_DIR = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_logs');
const GM_INPUTS = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'grandmaster', 'inputs');

// Helper to find log file by ID
function findLogFile(runId: string) {
    if (!fs.existsSync(LOGS_DIR)) return null;
    const clients = fs.readdirSync(LOGS_DIR).filter(f => fs.statSync(path.join(LOGS_DIR, f)).isDirectory());
    for (const client of clients) {
        const potentialPath = path.join(LOGS_DIR, client, `${runId}.txt`);
        if (fs.existsSync(potentialPath)) {
            return { path: potentialPath, client, dir: path.join(LOGS_DIR, client) };
        }
    }
    return null;
}

export async function POST(req: NextRequest) {
    try {
        const { run_id } = await req.json();
        if (!run_id) return NextResponse.json({ error: 'Missing run_id' }, { status: 400 });

        const logInfo = findLogFile(run_id);
        if (!logInfo) return NextResponse.json({ error: 'Run not found' }, { status: 404 });

        // 1. Setup Input Directory
        const inputDir = path.join(GM_INPUTS, run_id);
        if (!fs.existsSync(inputDir)) fs.mkdirSync(inputDir, { recursive: true });

        // Copy Artifacts
        const filesToCopy = [
            { src: `${run_id}.txt`, dest: 'transcript.txt' },
            { src: `${run_id}.score.json`, dest: 'score.json' },
            { src: `${run_id}.system_prompt.txt`, dest: 'system_prompt.txt' }, // Snapshot
            // persona might be .txt or .md depending on runner version? Runner usually outputs .txt for snapshot
            { src: `${run_id}.persona_context.txt`, dest: 'persona_context.txt' }
        ];

        for (const file of filesToCopy) {
            const srcPath = path.join(logInfo.dir, file.src);
            const destPath = path.join(inputDir, file.dest);
            if (fs.existsSync(srcPath)) {
                fs.copyFileSync(srcPath, destPath);
            } else {
                console.warn(`[GM API] Missing source file: ${srcPath}`);
            }
        }

        // 2. Run Troy Architect
        const architectScript = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'grandmaster', 'troy_architect.py');
        console.log('[GM API] Running Troy...');

        // We need to capture the output path from stdout? Or just know it?
        // troy_architect.py prints "[TROY] Generated Change Order: ..."

        const troyProcess = spawn('python', [architectScript, run_id], { cwd: FACTORY_ROOT });
        let troyOutput = '';

        await new Promise((resolve) => {
            troyProcess.stdout.on('data', d => troyOutput += d);
            troyProcess.on('close', resolve);
        });

        // Check if CO generated
        const match = troyOutput.match(/Generated Change Order: (.*)/);
        if (!match) {
            return NextResponse.json({ success: false, message: 'Troy found no improvements.', log: troyOutput });
        }
        const coPath = match[1].trim();

        // 3. Apply Patch
        const utilsScript = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'grandmaster', 'grandmaster_utils.py');
        console.log('[GM API] Applying Patch...');

        const applyProcess = spawn('python', [utilsScript, 'apply', coPath, inputDir], { cwd: FACTORY_ROOT });
        let applyOutput = '';

        const exitCode = await new Promise((resolve) => {
            applyProcess.stdout.on('data', d => applyOutput += d);
            applyProcess.on('close', resolve);
        });

        if (exitCode !== 0) {
            return NextResponse.json({ success: false, error: 'Patch Application Failed', log: applyOutput });
        }

        // 4. Return Success + Content of Patched File (for UI Scratchpad Update)
        // Read the patched system_prompt from inputs dir
        const patchedSysPath = path.join(inputDir, 'system_prompt.txt');
        let patchedSys = '';
        if (fs.existsSync(patchedSysPath)) {
            patchedSys = fs.readFileSync(patchedSysPath, 'utf-8');
        }

        return NextResponse.json({
            success: true,
            message: 'Grandmaster Patch Applied',
            patch_log: applyOutput,
            patched_system_prompt: patchedSys
        });

    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
