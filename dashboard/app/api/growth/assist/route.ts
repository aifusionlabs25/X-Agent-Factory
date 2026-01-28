import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';
import { GrowthDB } from '../../../../../../tools/growth_db.py'; // Pseudo-import logic, we will reimplement or wrap python? 
// Actually Next.js can't import python. We need to implement the logic in TS or call python script.
// Given "Local Only" and "Lightweight", I will implement simple logic in TS for the API route or call a new python script.
// The user "DELIVERABLES" section implied "growth_db.py" changes, which suggests Python backend is primary for logic.
// So I should stick to the pattern: TS API calls Python Script (like run_orchestrator).

// WAIT. growth_db.py is used by Python tools. The Dashboard uses direct SQLite.
// So I must implement logic in TS or call Python.
// Calling Python `tools/run_assist.py` seems cleaner and reuses the `SuggestionEngine` I just wrote (which is Python).
// So I will create `tools/run_assist.py` and call it from this API.

export async function POST(request: Request) {
    const { runId } = await request.json();

    // Call Python script
    const { exec } = require('child_process');
    const scriptPath = path.join(process.cwd(), '../tools/run_assist.py');
    const cmd = `python "${scriptPath}" --run_id "${runId}"`;

    return new Promise((resolve) => {
        exec(cmd, (error: any, stdout: string, stderr: string) => {
            if (error) {
                resolve(NextResponse.json({ success: false, error: stderr }, { status: 500 }));
            } else {
                try {
                    const result = JSON.parse(stdout.trim());
                    resolve(NextResponse.json({ success: true, ...result }));
                } catch (e) {
                    resolve(NextResponse.json({ success: true, raw: stdout }));
                }
            }
        });
    });
}
