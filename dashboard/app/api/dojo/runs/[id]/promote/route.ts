import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');

// Helper to find log file by ID (Duplicated logic, should be lib but okay for MVP)
function findLogFile(runId: string) {
    const LOGS_DIR = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_logs');
    if (!fs.existsSync(LOGS_DIR)) return null;
    const clients = fs.readdirSync(LOGS_DIR).filter(f => fs.statSync(path.join(LOGS_DIR, f)).isDirectory());
    for (const client of clients) {
        const potentialPath = path.join(LOGS_DIR, client, `${runId}.txt`);
        if (fs.existsSync(potentialPath)) {
            return { path: potentialPath, client };
        }
    }
    return null;
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const { id: runId } = await params;

    // Parse body for agent_id and force
    let body;
    try { body = await req.json(); } catch (e) { return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 }); }

    const { agent_id, force } = body; // Front end sends agent_id for verification?

    // We need agent_id for promoter command
    if (!agent_id) return NextResponse.json({ error: 'agent_id required' }, { status: 400 });

    const promoterPath = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_promoter.py');
    const args = [promoterPath, runId, '--agent', agent_id];
    if (force) args.push('--force');

    console.log('[API] Promoting', runId, 'for', agent_id);

    // --- SANITIZER GATE ---
    // User Requirement: Block if "DOJO_MODE" artifact exists or "MANDATORY" spam > 2.
    const logInfo = findLogFile(runId);
    if (logInfo) {
        const artifacts = ['system_prompt.txt', 'persona_context.md', 'persona_context.txt'];
        for (const art of artifacts) {
            const artPath = path.join(path.dirname(logInfo.path), `${runId}.${art}`);
            if (fs.existsSync(artPath)) {
                const content = fs.readFileSync(artPath, 'utf-8');

                // Check 1: DOJO_MODE
                if (content.includes("DOJO_MODE")) {
                    return NextResponse.json({
                        success: false,
                        error: `Sanitizer Blocked: DOJO_MODE artifact found in ${art}`,
                        output: "Clean the scratchpad before promoting."
                    }, { status: 400 });
                }

                // Check 2: Repetition (MANDATORY spam)
                const mandatoryCount = (content.match(/MANDATORY/g) || []).length;
                if (mandatoryCount > 2) {
                    return NextResponse.json({
                        success: false,
                        error: `Sanitizer Blocked: Robotic Repetition in ${art}`,
                        output: `Found 'MANDATORY' ${mandatoryCount} times. Max 2 allowed.`
                    }, { status: 400 });
                }
            }
        }
    }
    // ----------------------

    try {
        const child = spawn('python', args, { cwd: FACTORY_ROOT });

        let stdout = '';
        let stderr = '';

        child.stdout.on('data', d => stdout += d.toString());
        child.stderr.on('data', d => stderr += d.toString());

        return new Promise((resolve) => {
            child.on('close', (code) => {
                if (code === 0) {
                    resolve(NextResponse.json({ success: true, message: 'Promoted successfully', output: stdout }));
                } else {
                    // Parse block reason from stdout? 
                    // Promoter prints "[BLOCK] ..." on sys.exit(1) usually?
                    // Or stderr?
                    // Promoter uses print() so mostly stdout.
                    resolve(NextResponse.json({ success: false, error: 'Promotion Blocked', output: stdout + stderr }, { status: 400 }));
                }
            });
        });
    } catch (e) {
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
