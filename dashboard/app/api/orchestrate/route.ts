import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

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

        // Run the orchestrator
        const { stdout, stderr } = await execAsync(
            `python tools/factory_orchestrator.py --file "${filePath}"`,
            {
                cwd: projectRoot,
                timeout: 120000, // 2 minute timeout
                env: { ...process.env }
            }
        );

        console.log('Orchestrator output:', stdout);
        if (stderr) console.error('Orchestrator stderr:', stderr);

        // Check if email was sent
        const emailSent = stdout.includes('Email sent');

        return NextResponse.json({
            success: true,
            filename: filename,
            output: stdout,
            emailSent: emailSent,
            message: emailSent
                ? 'Report generated and emailed!'
                : 'Report generated (email may be pending)'
        });

    } catch (error: any) {
        console.error('Orchestrator error:', error);
        return NextResponse.json({
            success: false,
            error: error.message,
            stderr: error.stderr
        }, { status: 500 });
    }
}
