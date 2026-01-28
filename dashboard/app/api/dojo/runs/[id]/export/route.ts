import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');
const LOGS_DIR = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_logs');

// Helper to find log file by ID
function findLogFile(runId: string) {
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

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const { id: runId } = await params;
    const logInfo = findLogFile(runId);

    if (!logInfo) {
        return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }

    // --- SANITIZER GATE ---
    // Block export if "DOJO_MODE" artifact exists or "MANDATORY" spam > 2.
    const artifacts = ['system_prompt.txt', 'persona_context.md', 'persona_context.txt'];
    for (const art of artifacts) {
        const artPath = path.join(path.dirname(logInfo.path), `${runId}.${art}`);
        if (fs.existsSync(artPath)) {
            const content = fs.readFileSync(artPath, 'utf-8');

            if (content.includes("DOJO_MODE")) {
                return NextResponse.json({ error: `Sanitizer Blocked: DOJO_MODE artifact found in ${art}` }, { status: 400 });
            }

            const mandatoryCount = (content.match(/MANDATORY/g) || []).length;
            if (mandatoryCount > 2) {
                return NextResponse.json({ error: `Sanitizer Blocked: Robotic Repetition in ${art}` }, { status: 400 });
            }
        }
    }
    // ----------------------

    // Call dojo_reporter.py to ensure zip exists
    const reporterPath = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_reporter.py');
    const exportDir = path.join(FACTORY_ROOT, 'dashboard', 'public', 'dojo_export'); // Serve via public? Or stream?
    // User requested "Download Zip". Next.js can stream files.
    // Let's output to a temp location then stream.

    // Check if zip already exists from previous export? 
    // dojo_reporter puts it in --out dir.
    // Let's pick a stable location: `tools/evaluation/dojo/dojo_export` might be better or `dashboard/.temp`.
    // Let's use `dashboard/temp_exports`.

    const tempExportDir = path.join(FACTORY_ROOT, 'dashboard', 'temp_exports');
    if (!fs.existsSync(tempExportDir)) fs.mkdirSync(tempExportDir, { recursive: true });

    const zipName = `winner_package_${runId}.zip`;
    const zipPath = path.join(tempExportDir, zipName);

    // If zip exists, delete it? Or reuse? Use reuse if immutable. Runs are immutable.
    if (!fs.existsSync(zipPath)) {
        // Run Reporter
        console.log('[API] Generating Export for', runId);

        const child = spawn('python', [reporterPath, logInfo.path, '--out', tempExportDir], { cwd: FACTORY_ROOT });

        await new Promise((resolve, reject) => {
            child.on('close', (code) => {
                if (code === 0) resolve(true);
                else reject(new Error('Reporter failed'));
            });
        });
    }

    if (fs.existsSync(zipPath)) {
        // Stream back
        const fileBuffer = fs.readFileSync(zipPath);
        return new NextResponse(fileBuffer, {
            headers: {
                'Content-Type': 'application/zip',
                'Content-Disposition': `attachment; filename="${zipName}"`
            }
        });
    } else {
        return NextResponse.json({ error: 'Export failed generation' }, { status: 500 });
    }
}
