import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execPromise = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { vertical } = body;

        if (!vertical) {
            return NextResponse.json({ error: "Vertical name required" }, { status: 400 });
        }

        // Resolve paths
        const factoryRoot = path.resolve(process.cwd(), '..');
        const scriptPath = path.join(factoryRoot, 'tools', 'kb_generator.py');

        console.log(`🏗️ Running Architect for ${vertical}: python "${scriptPath}"`);

        // Execute Python script
        // Note: kb_generator.py takes the vertical name as an argument
        const { stdout, stderr } = await execPromise(`python "${scriptPath}" "${vertical}"`, {
            cwd: factoryRoot
        });

        if (stderr) {
            console.warn('Architect Stderr:', stderr);
        }

        return NextResponse.json({ success: true, logs: stdout });

    } catch (error: any) {
        console.error('Architect Error:', error);
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
