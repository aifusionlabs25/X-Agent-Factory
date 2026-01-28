import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(req: Request) {
    const { params } = await req.json(); // Expect generic params if needed, mostly just action trigger
    const rootDir = path.resolve(process.cwd(), '..');

    // Command mapping
    const command = `python tools/run_orchestrator.py --queue growth/runs/run_queue.yaml`;

    return new Promise((resolve) => {
        exec(command, { cwd: rootDir }, (error, stdout, stderr) => {
            if (error) {
                resolve(NextResponse.json({ success: false, error: error.message, stderr }));
            } else {
                resolve(NextResponse.json({ success: true, stdout }));
            }
        });
    });
}
