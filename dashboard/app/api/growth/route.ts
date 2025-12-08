import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';

const execPromise = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const { vertical } = await req.json();

        if (!vertical) {
            return NextResponse.json({ error: 'Vertical is required' }, { status: 400 });
        }

        const command = `python tools/prospect_scout.py "${vertical}"`;
        const cwd = path.join(process.cwd(), '..'); // Assuming dashboard is in dashboard/ dir

        // Execute the Python script
        const { stdout, stderr } = await execPromise(command, { cwd });
        console.log("Scout Output:", stdout);

        if (stderr) {
            console.warn("Scout Stderr:", stderr);
        }

        // Read the results file
        const safeVertical = vertical.toLowerCase().replace(/ /g, '_');
        const resultsPath = path.join(cwd, 'intelligence', 'leads', `${safeVertical}_qualified.json`);

        if (fs.existsSync(resultsPath)) {
            const resultsData = fs.readFileSync(resultsPath, 'utf-8');
            const leads = JSON.parse(resultsData);
            return NextResponse.json({ success: true, leads, logs: stdout });
        } else {
            return NextResponse.json({ success: false, error: "Results file not found.", logs: stdout });
        }

    } catch (error: any) {
        console.error("API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}

export async function GET(req: Request) {
    // Optional: List all available lead files
    return NextResponse.json({ message: "Method not implemented yet" });
}
