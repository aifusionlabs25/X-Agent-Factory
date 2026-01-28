import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');
const LOGS_DIR = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_logs');

// Helper to find log file by ID
function findLogFile(runId: string) {
    if (!fs.existsSync(LOGS_DIR)) return null;

    // Search all clients
    const clients = fs.readdirSync(LOGS_DIR).filter(f => fs.statSync(path.join(LOGS_DIR, f)).isDirectory());
    for (const client of clients) {
        const potentialPath = path.join(LOGS_DIR, client, `${runId}.txt`);
        if (fs.existsSync(potentialPath)) {
            return { path: potentialPath, client };
        }
    }
    return null;
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const { id: runId } = await params;
    const logInfo = findLogFile(runId);

    if (!logInfo) {
        return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }

    const baseDir = path.dirname(logInfo.path);
    const scoreFile = path.join(baseDir, `${runId}.score.json`);
    const sysFile = path.join(baseDir, `${runId}.system_prompt.txt`);
    const personaFile = path.join(baseDir, `${runId}.persona_context.txt`);

    // Read Content
    let transcript = '';
    try { transcript = fs.readFileSync(logInfo.path, 'utf-8'); } catch (e) { }

    let scoreData = null;
    if (fs.existsSync(scoreFile)) {
        try { scoreData = JSON.parse(fs.readFileSync(scoreFile, 'utf-8')); } catch (e) { }
    }

    let system_prompt = null;
    if (fs.existsSync(sysFile)) {
        system_prompt = fs.readFileSync(sysFile, 'utf-8');
    }

    let persona_context = null;
    if (fs.existsSync(personaFile)) {
        persona_context = fs.readFileSync(personaFile, 'utf-8');
    }

    return NextResponse.json({
        run_id: runId,
        client: logInfo.client,
        transcript,
        score: scoreData,
        snapshots: {
            system_prompt,
            persona_context
        }
    });
}
