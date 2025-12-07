import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execPromise = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { agentName } = body;

        if (!agentName) {
            return NextResponse.json({ error: "Agent Name required" }, { status: 400 });
        }

        // Resolve paths
        const factoryRoot = path.resolve(process.cwd(), '..');
        const scriptPath = path.join(factoryRoot, 'tools', 'deploy_agent.py');

        console.log(`🚀 Deploying ${agentName}: python "${scriptPath}"`);

        // Execute Python script
        const { stdout, stderr } = await execPromise(`python "${scriptPath}" "${agentName}"`, {
            cwd: factoryRoot
        });

        if (stderr) {
            console.warn('Deploy Stderr:', stderr);
        }

        return NextResponse.json({ success: true, logs: stdout });

    } catch (error: any) {
        console.error('Deploy Error:', error);
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
