import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';

const execPromise = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const { url } = await req.json();

        if (!url) {
            return NextResponse.json({ error: 'URL is required' }, { status: 400 });
        }

        // Run client_ingest.py
        const command = `python tools/client_ingest.py "${url}"`;
        const cwd = path.join(process.cwd(), '..');

        // This might take a while (spidering + LLM), so we await it.
        // In a real app, this should be a background job with polling.
        // For this prototype, long-polling is acceptable (Next.js default timeout is high enough usually).
        const { stdout, stderr } = await execPromise(command, { cwd });
        console.log("Ingest Output:", stdout);

        if (stderr) {
            console.warn("Ingest Stderr:", stderr);
        }

        return NextResponse.json({ success: true, logs: stdout });

    } catch (error: any) {
        console.error("API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
