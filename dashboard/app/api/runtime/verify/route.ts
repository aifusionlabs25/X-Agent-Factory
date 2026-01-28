import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';

const execPromise = util.promisify(exec);

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const client = searchParams.get('client');

    if (!client) {
        return NextResponse.json({ error: 'Client slug required' }, { status: 400 });
    }

    try {
        // Run the verification tool
        const rootDir = path.join(process.cwd(), '..');
        const command = `python tools/verify_runtime_profile.py --client ${client}`;

        // We expect success (exit 0) or failure (exit 1)
        // execPromise throws on non-zero exit
        await execPromise(command, { cwd: rootDir });

        return NextResponse.json({
            success: true,
            output: "Runtime Verification Passed."
        });

    } catch (error: any) {
        // If tool fails, capture stderr/stdout
        const output = error.stdout || error.stderr || error.message;
        return NextResponse.json({
            success: false,
            output: output
        }, { status: 200 }); // Return 200 so UI can display the failure message nicely
    }
}
