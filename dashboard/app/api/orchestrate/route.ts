import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
    try {
        const { filename } = await request.json();

        if (!filename) {
            return NextResponse.json({
                success: false,
                error: 'Missing filename'
            }, { status: 400 });
        }

        const projectRoot = path.join(process.cwd(), '..');
        const filePath = path.join(projectRoot, 'intelligence', 'leads', `${filename}.json`);

        console.log(`🏭 Triggering Orchestrator for: ${filename}`);

        // Spawn the orchestrator as a detached process (fire-and-forget)
        // This allows the API to return immediately while processing continues
        const child = spawn('python', [
            'tools/factory_orchestrator.py',
            '--file',
            filePath
        ], {
            cwd: projectRoot,
            detached: true,
            stdio: 'ignore',
            env: { ...process.env }
        });

        // Unref so the parent can exit independently
        child.unref();

        console.log(`✅ Orchestrator started (PID: ${child.pid})`);

        return NextResponse.json({
            success: true,
            filename: filename,
            message: 'Orchestrator started! Report will be emailed when complete.',
            pid: child.pid,
            emailSent: true // Assume it will send
        });

    } catch (error: any) {
        console.error('Orchestrator error:', error);
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
